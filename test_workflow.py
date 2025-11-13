"""
Test Workflow Runner
Runs the complete agent workflow and saves outputs to test run folders.

Usage:
    python test_workflow.py
    
    # With custom thresholds:
    python test_workflow.py --underperf 0.15 --max-price-change 0.25
"""
import argparse
import json
import sys
import shutil
from datetime import datetime
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import settings
from crew import run_workflow


def get_next_test_run_number():
    """Get the next test run number by checking existing test folders"""
    output_dir = settings.OUTPUT_DIR
    test_folders = [d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith("test_")]
    
    if not test_folders:
        return 1
    
    # Extract numbers from folder names
    numbers = []
    for folder in test_folders:
        try:
            num = int(folder.name.split("_")[1])
            numbers.append(num)
        except (IndexError, ValueError):
            continue
    
    return max(numbers) + 1 if numbers else 1


def setup_test_run_folder():
    """Create a new test run folder and update settings to use it"""
    test_num = get_next_test_run_number()
    test_folder = settings.OUTPUT_DIR / f"test_{test_num}"
    test_folder.mkdir(parents=True, exist_ok=True)
    
    # Update settings to point to test folder
    settings.OUTPUT_DIR = test_folder
    settings.FLAGGED_SKUS = test_folder / "flagged_skus.csv"
    settings.CHOICE_SETS = test_folder / "choice_sets.json"
    settings.PRICE_SCENARIOS = test_folder / "price_scenarios.csv"
    settings.CAMPAIGN_SCENARIOS = test_folder / "campaign_scenarios.csv"
    settings.LABOR_ESTIMATES = test_folder / "labor_cost_estimates.csv"
    settings.RANKED_PLAN = test_folder / "ranked_action_plan.csv"
    settings.PRODUCT_FEEDBACK = test_folder / "product_feedback.csv"
    settings.FINAL_ACTIONS = test_folder / "finalized_actions.csv"
    
    return test_num, test_folder


def print_separator(title="", char="=", width=80):
    """Print a formatted separator"""
    if title:
        padding = (width - len(title) - 2) // 2
        print(f"\n{char * padding} {title} {char * padding}")
    else:
        print(f"\n{char * width}")


def display_results():
    """Display the results from the workflow outputs"""
    print_separator("WORKFLOW RESULTS", "=")
    
    # Display flagged SKUs
    if settings.FLAGGED_SKUS.exists():
        print_separator("1. Flagged SKUs (TriggerAgent)", "-")
        flagged = pd.read_csv(settings.FLAGGED_SKUS)
        print(f"\nTotal flagged SKUs: {len(flagged)}")
        print("\nTop 5 underperformers:")
        print(flagged.head(5).to_string(index=False))
        if len(flagged) > 5:
            print(f"\n... and {len(flagged) - 5} more SKUs")
    
    # Display price scenarios
    if settings.PRICE_SCENARIOS.exists():
        print_separator("2. Price Scenarios (PricingAgent)", "-")
        scenarios = pd.read_csv(settings.PRICE_SCENARIOS)
        print(f"\nTotal price scenarios: {len(scenarios)}")
        print("\nTop 5 scenarios by expected lift:")
        top_scenarios = scenarios.nlargest(5, 'expected_lift_units')
        print(top_scenarios[['sku_id', 'current_price', 'proposed_price', 
                            'delta_pct', 'expected_lift_units']].to_string(index=False))
    
    # Display campaign scenarios
    if settings.CAMPAIGN_SCENARIOS.exists():
        print_separator("3. Campaign Scenarios (MarketingAgent)", "-")
        campaigns = pd.read_csv(settings.CAMPAIGN_SCENARIOS)
        print(f"\nTotal campaign scenarios: {len(campaigns)}")
        print(f"Total marketing spend: ${campaigns['total_spend'].sum():,.2f}")
        print("\nTop 5 campaigns by expected lift:")
        top_campaigns = campaigns.nlargest(5, 'expected_lift_units')
        print(top_campaigns[['sku_id', 'channels', 'total_spend', 'expected_lift_units']].to_string(index=False))
    
    # Display labor estimates
    if settings.LABOR_ESTIMATES.exists():
        print_separator("4. Labor Estimates (LaborAgent)", "-")
        labor = pd.read_csv(settings.LABOR_ESTIMATES)
        print(f"\nTotal labor estimates: {len(labor)}")
        print(f"Total labor cost: ${labor['total_cost'].sum():,.2f}")
        print(f"SKUs with incremental labor: {len(labor[labor['incremental_cost'] > 0])}")
    
    # Display ranked action plan
    if settings.RANKED_PLAN.exists():
        print_separator("5. Ranked Action Plan (FinanceAgent)", "-")
        ranked = pd.read_csv(settings.RANKED_PLAN)
        print(f"\nTotal scenarios ranked: {len(ranked)}")
        print(f"Total expected ROI: ${ranked['roi'].sum():,.2f}")
        print(f"Scenarios with positive ROI: {len(ranked[ranked['roi'] > 0])}")
        print("\nTop 5 by ROI:")
        print(ranked.head(5)[['sku_id', 'rank', 'roi', 'incremental_revenue', 'total_costs']].to_string(index=False))
    
    # Display product feedback
    if settings.PRODUCT_FEEDBACK.exists():
        print_separator("6. Product Feedback (ProductAgent)", "-")
        product = pd.read_csv(settings.PRODUCT_FEEDBACK)
        print(f"\nTotal scenarios validated: {len(product)}")
        print(f"Accepted: {len(product[product['decision'] == 'accept'])}")
        print(f"Needs review: {len(product[product['decision'] == 'review'])}")
        print(f"Rejected: {len(product[product['decision'] == 'reject'])}")
    
    # Display finalized actions
    if settings.FINAL_ACTIONS.exists():
        print_separator("7. Finalized Actions (GovernanceAgent)", "-")
        final = pd.read_csv(settings.FINAL_ACTIONS)
        print(f"\nTotal actions evaluated: {len(final)}")
        print(f"Auto-approved: {len(final[final['decision'] == 'auto-approved'])}")
        print(f"Manual review required: {len(final[final['decision'] == 'manual-review'])}")
        print(f"Rejected: {len(final[final['decision'] == 'rejected'])}")
        print("\nTop 5 auto-approved actions:")
        auto_approved = final[final['decision'] == 'auto-approved'].head(5)
        if len(auto_approved) > 0:
            print(auto_approved[['sku_id', 'rank', 'decision', 'roi']].to_string(index=False))
    
    print_separator()


def save_summary_report(workflow_result, test_num):
    """Save a summary report of the workflow execution"""
    report_path = settings.OUTPUT_DIR / f"workflow_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    summary = {
        "test_run": test_num,
        "execution_time": datetime.now().isoformat(),
        "status": workflow_result.get("status"),
        "workflow_result": workflow_result,
        "output_folder": str(settings.OUTPUT_DIR),
        "output_files": {
            "flagged_skus": str(settings.FLAGGED_SKUS),
            "choice_sets": str(settings.CHOICE_SETS),
            "price_scenarios": str(settings.PRICE_SCENARIOS),
            "campaign_scenarios": str(settings.CAMPAIGN_SCENARIOS),
            "labor_estimates": str(settings.LABOR_ESTIMATES),
            "ranked_plan": str(settings.RANKED_PLAN),
            "product_feedback": str(settings.PRODUCT_FEEDBACK),
            "final_actions": str(settings.FINAL_ACTIONS)
        }
    }
    
    with open(report_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📄 Summary report saved to: {report_path}")
    return report_path


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(
        description="Run the complete agent workflow with all 7 agents"
    )
    parser.add_argument(
        '--underperf',
        type=float,
        default=None,
        help=f'Underperformance threshold (default: {settings.UNDERPERF_PCT})'
    )
    parser.add_argument(
        '--max-price-change',
        type=float,
        default=None,
        help=f'Max price change guardrail (default: {settings.MAX_PRICE_CHANGE})'
    )
    parser.add_argument(
        '--no-display',
        action='store_true',
        help='Skip displaying results (just run workflow)'
    )
    
    args = parser.parse_args()
    
    # Setup test run folder
    test_num, test_folder = setup_test_run_folder()
    
    print_separator("INTELLIGENT MANAGEMENT SYSTEM - TEST WORKFLOW", "=")
    print(f"\n🧪 Test Run #{test_num}")
    print(f"Execution started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nConfiguration:")
    print(f"  - Underperformance threshold: {args.underperf or settings.UNDERPERF_PCT:.1%}")
    print(f"  - Max price change: {args.max_price_change or settings.MAX_PRICE_CHANGE:.1%}")
    print(f"  - Min inventory: {settings.MIN_INVENTORY}")
    print(f"  - Labor cost cap: ${settings.LABOR_COST_CAP}")
    print(f"\nDirectories:")
    print(f"  - Input: {settings.INPUT_DIR}")
    print(f"  - Output: {test_folder}")
    print(f"  - Logs: {settings.LOGS_DIR}")
    
    # Run the workflow
    print_separator("RUNNING WORKFLOW", "=")
    workflow_result = run_workflow(
        underperf_threshold=args.underperf,
        max_price_change=args.max_price_change
    )
    
    # Display results
    if not args.no_display and workflow_result.get("status") == "success":
        display_results()
    
    # Save summary report
    report_path = save_summary_report(workflow_result, test_num)
    
    # Final status
    print_separator("EXECUTION COMPLETE", "=")
    if workflow_result.get("status") == "success":
        print("\n✅ Workflow completed successfully!")
        print(f"\n📁 All outputs saved to: {test_folder}")
        print(f"\nGenerated files:")
        print(f"  1. {settings.FLAGGED_SKUS.name} - Underperforming SKUs")
        print(f"  2. {settings.CHOICE_SETS.name} - Choice sets")
        print(f"  3. {settings.PRICE_SCENARIOS.name} - Price recommendations")
        print(f"  4. {settings.CAMPAIGN_SCENARIOS.name} - Marketing campaigns")
        print(f"  5. {settings.LABOR_ESTIMATES.name} - Labor cost estimates")
        print(f"  6. {settings.RANKED_PLAN.name} - ROI-ranked actions")
        print(f"  7. {settings.PRODUCT_FEEDBACK.name} - Product validation")
        print(f"  8. {settings.FINAL_ACTIONS.name} - Governance decisions")
        print(f"  9. {report_path.name} - Summary report")
        print(f"\n📋 Logs: {settings.APP_LOG}")
        return 0
    else:
        print("\n❌ Workflow failed!")
        print(f"Error at step: {workflow_result.get('step', 'unknown')}")
        print(f"Error: {workflow_result.get('error', 'Unknown error')}")
        print(f"\n📁 Partial outputs saved to: {test_folder}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
