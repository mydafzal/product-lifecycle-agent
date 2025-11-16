"""
ReportAgent - Generates final transparency report showing the journey of each SKU.

This agent:
1. Reads all workflow outputs (flagged SKUs, pricing, marketing, labor, finance, product, governance)
ReportAgent: Generates comprehensive transparency report
Consolidates all workflow outputs into a single SKU journey report
Uses LLM to generate human-readable markdown report
"""
import pandas as pd
from pathlib import Path
import json
from datetime import datetime
import logging
import settings
from tools.data_tools import write_csv
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.APP_LOG),
        logging.StreamHandler()
    ]
)


def generate_markdown_report(report_df: pd.DataFrame, summary: dict) -> str:
    """
    Use OpenAI to generate a human-readable markdown report from the SKU journey data.
    
    Args:
        report_df: DataFrame containing complete SKU journey
        summary: Dictionary with summary metrics
    
    Returns:
        Markdown-formatted report as string
    """
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Prepare data summary for LLM (limit to top 10 SKUs to avoid token limits)
        top_skus = report_df.head(10)
        
        # Create a concise data summary
        sku_summaries = []
        for idx, row in top_skus.iterrows():
            sku_summary = f"""
SKU {row.get('sku_id', 'N/A')} (Rank #{row.get('rank', 'N/A')}):
- Trigger: {row.get('trigger_reason', 'N/A')}
- Price: ${row.get('price_current', 0):.2f} → ${row.get('price_proposed', 0):.2f} ({row.get('price_change_pct', 0)*100:.1f}% change)
- Marketing: {row.get('marketing_channels', 'N/A')} (${row.get('marketing_spend', 0):,.0f})
- Labor: {row.get('labor_hours', 0):.1f} hours (${row.get('labor_cost', 0):,.0f})
- ROI: ${row.get('roi', 0):,.0f}
- Decision: {row.get('final_decision', 'N/A')} - {row.get('governance_reason', 'N/A')}
"""
            sku_summaries.append(sku_summary)
        
        # Create prompt for LLM
        prompt = f"""
You are a business intelligence analyst. Generate a comprehensive transparency report in markdown format about SKU performance analysis.

WORKFLOW DATA:
- Total SKUs Analyzed: {summary.get('total_skus_flagged', 0)}
- Total ROI: ${summary.get('total_roi', 0):,.2f}
- Total Marketing Spend: ${summary.get('total_marketing_spend', 0):,.2f}
- Total Labor Cost: ${summary.get('total_labor_cost', 0):,.2f}

DECISIONS:
{json.dumps(summary.get('by_final_decision', {}), indent=2)}

TOP SKU DETAILS:
{''.join(sku_summaries)}

Generate a professional markdown report with these sections:

# SKU Performance Transparency Report

## Executive Summary
[Brief overview of the analysis and key outcomes]

## Workflow Overview
[Explain the 8-stage process: Trigger → Pricing → Marketing → Labor → Finance → Product → Governance → Report]

## Key Findings
[Highlight top performers, concerns, and patterns]

## Decision Analysis
[Breakdown of approvals, rejections, manual reviews]

## Financial Impact
[ROI analysis and cost breakdown]

## Individual SKU Stories
[Tell the story of top 3-5 SKUs with their complete journey]

## Recommendations
[Actionable insights for business leaders]

## Next Steps
[Required actions and implementation plan]

Make it engaging, professional, and focused on business insights. Use proper markdown formatting.
"""
        
        # Call OpenAI API
        logger.info("Calling OpenAI to generate markdown report...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a business intelligence analyst who creates comprehensive, professional reports."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=3000
        )
        
        markdown_report = response.choices[0].message.content
        logger.info("✅ Markdown report generated successfully")
        return markdown_report
        
    except Exception as e:
        logger.error(f"❌ Failed to generate markdown report: {str(e)}")
        # Return a simple fallback report
        return f"""# SKU Performance Transparency Report

## Executive Summary
Analysis of {summary.get('total_skus_flagged', 0)} SKUs completed with total ROI of ${summary.get('total_roi', 0):,.2f}.

## Error
Failed to generate detailed report: {str(e)}

## Raw Data Summary
- Total Marketing Spend: ${summary.get('total_marketing_spend', 0):,.2f}
- Total Labor Cost: ${summary.get('total_labor_cost', 0):,.2f}
- Decisions: {summary.get('by_final_decision', {})}
"""


def run_report():
    """
    Generate final transparency report showing the complete journey of each SKU.
    
    Returns:
        dict: Summary of report generation
    """
    logger.info("=" * 60)
    logger.info("REPORT AGENT - Starting execution")
    logger.info("=" * 60)
    
    try:
        # Read all workflow outputs
        logger.info("Reading workflow outputs...")
        
        # Start with flagged SKUs (the origin)
        if not settings.FLAGGED_SKUS.exists():
            logger.error("❌ flagged_skus.csv not found. Cannot generate report!")
            return {"status": "error", "error": "flagged_skus.csv not found"}
        
        report = pd.read_csv(settings.FLAGGED_SKUS)
        logger.info(f"Loaded {len(report)} flagged SKUs")
        
        # Rename trigger columns for clarity
        report.rename(columns={
            "reason": "trigger_reason"
        }, inplace=True)
        
        # Add pricing information
        if settings.PRICE_SCENARIOS.exists():
            pricing = pd.read_csv(settings.PRICE_SCENARIOS)
            pricing_cols = ["sku_id", "current_price", "proposed_price", "delta_pct", "expected_lift_units"]
            available_pricing_cols = ["sku_id"] + [col for col in pricing_cols[1:] if col in pricing.columns]
            report = report.merge(
                pricing[available_pricing_cols],
                on="sku_id",
                how="left"
            )
            report.rename(columns={
                "current_price": "price_current",
                "proposed_price": "price_proposed",
                "delta_pct": "price_change_pct",
                "expected_lift_units": "price_expected_lift"
            }, inplace=True)
        
        # Add marketing information
        if settings.CAMPAIGN_SCENARIOS.exists():
            marketing = pd.read_csv(settings.CAMPAIGN_SCENARIOS)
            marketing_cols = ["sku_id", "channels", "total_spend", "expected_lift_units"]
            available_marketing_cols = ["sku_id"] + [col for col in marketing_cols[1:] if col in marketing.columns]
            report = report.merge(
                marketing[available_marketing_cols],
                on="sku_id",
                how="left",
                suffixes=('', '_marketing')
            )
            report.rename(columns={
                "channels": "marketing_channels",
                "total_spend": "marketing_spend",
                "expected_lift_units_marketing": "marketing_expected_lift"
            }, inplace=True)
        
        # Add labor information
        if settings.LABOR_ESTIMATES.exists():
            labor = pd.read_csv(settings.LABOR_ESTIMATES)
            # Use actual column names from the file
            labor_merge_cols = ["sku_id"]
            rename_map = {}
            
            if "total_labor_hours" in labor.columns:
                labor_merge_cols.append("total_labor_hours")
                rename_map["total_labor_hours"] = "labor_hours"
            
            if "total_cost" in labor.columns:
                labor_merge_cols.append("total_cost")
                rename_map["total_cost"] = "labor_cost"
            
            report = report.merge(
                labor[labor_merge_cols],
                on="sku_id",
                how="left",
                suffixes=('', '_labor')
            )
            
            if rename_map:
                report.rename(columns=rename_map, inplace=True)
        
        # Add finance/ranking information
        if settings.RANKED_PLAN.exists():
            finance = pd.read_csv(settings.RANKED_PLAN)
            # Use actual column names from the file
            finance_merge_cols = ["sku_id"]
            rename_map = {}
            
            for col in ["roi", "rank", "incremental_revenue"]:
                if col in finance.columns:
                    finance_merge_cols.append(col)
            
            if "total_costs" in finance.columns:
                finance_merge_cols.append("total_costs")
                rename_map["total_costs"] = "total_action_cost"
            
            report = report.merge(
                finance[finance_merge_cols],
                on="sku_id",
                how="left",
                suffixes=('', '_finance')
            )
            
            if rename_map:
                report.rename(columns=rename_map, inplace=True)
        
        # Add product feedback
        if settings.PRODUCT_FEEDBACK.exists():
            product = pd.read_csv(settings.PRODUCT_FEEDBACK)
            product_cols = ["sku_id", "decision", "risk_level", "feedback"]
            available_product_cols = ["sku_id"] + [col for col in product_cols[1:] if col in product.columns]
            report = report.merge(
                product[available_product_cols],
                on="sku_id",
                how="left",
                suffixes=('', '_product')
            )
            report.rename(columns={
                "decision": "product_decision",
                "risk_level": "product_risk",
                "feedback": "product_feedback"
            }, inplace=True)
        
        # Add final governance decision
        if settings.FINAL_ACTIONS.exists():
            governance = pd.read_csv(settings.FINAL_ACTIONS)
            governance_cols = ["sku_id", "decision", "reason"]
            available_governance_cols = ["sku_id"] + [col for col in governance_cols[1:] if col in governance.columns]
            report = report.merge(
                governance[available_governance_cols],
                on="sku_id",
                how="left",
                suffixes=('', '_governance')
            )
            report.rename(columns={
                "decision": "final_decision",
                "reason": "governance_reason"
            }, inplace=True)
        
        # Add human approval status (will be updated after human review)
        report["human_decision"] = "pending"
        report["human_notes"] = ""
        
        # Sort by rank (most important first)
        if "rank" in report.columns:
            report = report.sort_values("rank")
        
        # Save the transparency report
        transparency_report_path = settings.OUTPUT_DIR / "transparency_report.csv"
        write_csv(report, transparency_report_path)
        
        # Create a summary JSON for easy consumption
        summary = {
            "report_generated": datetime.now().isoformat(),
            "total_skus_flagged": len(report),
            "by_final_decision": report["final_decision"].value_counts().to_dict() if "final_decision" in report.columns else {},
            "by_product_risk": report["product_risk"].value_counts().to_dict() if "product_risk" in report.columns else {},
            "total_roi": float(report["roi"].sum()) if "roi" in report.columns else 0,
            "total_marketing_spend": float(report["marketing_spend"].sum()) if "marketing_spend" in report.columns else 0,
            "total_labor_cost": float(report["labor_cost"].sum()) if "labor_cost" in report.columns else 0
        }
        
        summary_path = settings.OUTPUT_DIR / "transparency_report_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Generate LLM-based markdown report
        logger.info("Generating human-readable markdown report using LLM...")
        markdown_report = generate_markdown_report(report, summary)
        
        # Save markdown report
        markdown_path = settings.OUTPUT_DIR / "transparency_report.md"
        with open(markdown_path, 'w') as f:
            f.write(markdown_report)
        
        logger.info(f"✅ ReportAgent completed successfully")
        logger.info(f"   - Total SKUs in report: {len(report)}")
        logger.info(f"   - CSV report: {transparency_report_path}")
        logger.info(f"   - Markdown report: {markdown_path}")
        logger.info(f"   - Summary: {summary_path}")
        
        return {
            "status": "success",
            "total_skus": len(report),
            "summary": summary,
            "markdown_report": markdown_report,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ ReportAgent failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Test the agent standalone
    result = run_report()
    print(json.dumps(result, indent=2))
