"""
Test Workflow Runner
Runs the Trigger and Pricing agent workflow and saves outputs for inspection.

Usage:
    python test_workflow.py
    
    # With custom thresholds:
    python test_workflow.py --underperf 0.15 --max-price-change 0.25
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import settings
from crew import run_workflow


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
        print_separator("Flagged SKUs", "-")
        flagged = pd.read_csv(settings.FLAGGED_SKUS)
        print(f"\nTotal flagged SKUs: {len(flagged)}")
        print("\nTop 10 underperformers:")
        print(flagged.head(10).to_string(index=False))
        
        if len(flagged) > 10:
            print(f"\n... and {len(flagged) - 10} more SKUs")
    
    # Display choice sets
    if settings.CHOICE_SETS.exists():
        print_separator("Choice Sets", "-")
        with open(settings.CHOICE_SETS, 'r') as f:
            choice_sets = json.load(f)
        print(f"\nTotal choice sets: {len(choice_sets)}")
        if choice_sets:
            print("\nFirst 3 choice sets:")
            for cs in choice_sets[:3]:
                print(f"  - {cs['set_id']}: {cs['rationale']}")
    
    # Display price scenarios
    if settings.PRICE_SCENARIOS.exists():
        print_separator("Price Scenarios", "-")
        scenarios = pd.read_csv(settings.PRICE_SCENARIOS)
        print(f"\nTotal price scenarios: {len(scenarios)}")
        print("\nTop 10 scenarios by expected lift:")
        top_scenarios = scenarios.nlargest(10, 'expected_lift_units')
        print(top_scenarios[['sku_id', 'current_price', 'proposed_price', 
                            'delta_pct', 'expected_lift_units']].to_string(index=False))
        
        print(f"\n\nSummary Statistics:")
        print(f"  - Average price change: {scenarios['delta_pct'].mean():.2%}")
        print(f"  - Total expected lift: {scenarios['expected_lift_units'].sum():.0f} units")
        print(f"  - Scenarios with price increase: {len(scenarios[scenarios['delta_pct'] > 0])}")
        print(f"  - Scenarios with price decrease: {len(scenarios[scenarios['delta_pct'] < 0])}")
    
    print_separator()


def save_summary_report(workflow_result):
    """Save a summary report of the workflow execution"""
    report_path = settings.OUTPUT_DIR / f"workflow_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    summary = {
        "execution_time": datetime.now().isoformat(),
        "status": workflow_result.get("status"),
        "workflow_result": workflow_result,
        "output_files": {
            "flagged_skus": str(settings.FLAGGED_SKUS),
            "choice_sets": str(settings.CHOICE_SETS),
            "price_scenarios": str(settings.PRICE_SCENARIOS)
        }
    }
    
    with open(report_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📄 Summary report saved to: {report_path}")
    return report_path


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(
        description="Run the Trigger and Pricing agent workflow"
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
    
    print_separator("INTELLIGENT MANAGEMENT SYSTEM - TEST WORKFLOW", "=")
    print(f"\nExecution started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nConfiguration:")
    print(f"  - Underperformance threshold: {args.underperf or settings.UNDERPERF_PCT:.1%}")
    print(f"  - Max price change: {args.max_price_change or settings.MAX_PRICE_CHANGE:.1%}")
    print(f"  - Input directory: {settings.INPUT_DIR}")
    print(f"  - Output directory: {settings.OUTPUT_DIR}")
    print(f"  - Logs directory: {settings.LOGS_DIR}")
    
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
    report_path = save_summary_report(workflow_result)
    
    # Final status
    print_separator("EXECUTION COMPLETE", "=")
    if workflow_result.get("status") == "success":
        print("\n✅ Workflow completed successfully!")
        print(f"\nOutputs generated:")
        print(f"  - {settings.FLAGGED_SKUS}")
        print(f"  - {settings.CHOICE_SETS}")
        print(f"  - {settings.PRICE_SCENARIOS}")
        print(f"  - {settings.APP_LOG}")
        print(f"  - {report_path}")
        return 0
    else:
        print("\n❌ Workflow failed!")
        print(f"Error: {workflow_result.get('error', 'Unknown error')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
