"""
FinanceAgent - Calculates ROI and ranks action plans.

This agent:
1. Reads price scenarios, campaign scenarios, and labor estimates
2. Calculates incremental revenue and total costs
3. Computes ROI for each SKU
4. Ranks SKUs by ROI
5. Writes ranked_action_plan.csv
"""
import pandas as pd
import json
from datetime import datetime
import settings
from tools.data_tools import write_csv
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.APP_LOG),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Assumed unit price for revenue calculation (can be overridden)
ASSUMED_UNIT_PRICE = 50.0


def run_finance():
    """
    Main finance logic - deterministic ROI calculation and ranking.
    
    Returns:
        dict: Summary of ranked action plan
    """
    logger.info("=" * 60)
    logger.info("FINANCE AGENT - Starting execution")
    logger.info("=" * 60)
    
    try:
        # Read price scenarios
        logger.info("Reading price scenarios from PricingAgent...")
        if not settings.PRICE_SCENARIOS.exists():
            logger.error("❌ price_scenarios.csv not found. Run PricingAgent first!")
            return {"status": "error", "error": "price_scenarios.csv not found"}
        
        price_scenarios = pd.read_csv(settings.PRICE_SCENARIOS)
        logger.info(f"Loaded {len(price_scenarios)} price scenarios")
        
        # Read campaign scenarios
        logger.info("Reading campaign scenarios from MarketingAgent...")
        if not settings.CAMPAIGN_SCENARIOS.exists():
            logger.error("❌ campaign_scenarios.csv not found. Run MarketingAgent first!")
            return {"status": "error", "error": "campaign_scenarios.csv not found"}
        
        campaigns = pd.read_csv(settings.CAMPAIGN_SCENARIOS)
        logger.info(f"Loaded {len(campaigns)} campaign scenarios")
        
        # Read labor estimates
        logger.info("Reading labor estimates from LaborAgent...")
        if not settings.LABOR_ESTIMATES.exists():
            logger.error("❌ labor_cost_estimates.csv not found. Run LaborAgent first!")
            return {"status": "error", "error": "labor_cost_estimates.csv not found"}
        
        labor_estimates = pd.read_csv(settings.LABOR_ESTIMATES)
        logger.info(f"Loaded {len(labor_estimates)} labor estimates")
        
        # Merge all data
        df = price_scenarios[["sku_id", "proposed_price", "expected_lift_units"]].rename(
            columns={"expected_lift_units": "price_lift"}
        )
        
        df = df.merge(
            campaigns[["sku_id", "total_spend", "expected_lift_units"]].rename(
                columns={"expected_lift_units": "marketing_lift"}
            ),
            on="sku_id",
            how="outer"
        )
        
        df = df.merge(
            labor_estimates[["sku_id", "total_cost"]].rename(
                columns={"total_cost": "labor_cost"}
            ),
            on="sku_id",
            how="left"
        )
        
        # Handle NaN values
        df["price_lift"] = df["price_lift"].fillna(0)
        df["marketing_lift"] = df["marketing_lift"].fillna(0)
        df["total_spend"] = df["total_spend"].fillna(0)
        df["labor_cost"] = df["labor_cost"].fillna(0)
        df["proposed_price"] = df["proposed_price"].fillna(ASSUMED_UNIT_PRICE)
        
        # Calculate combined expected lift (max of price and marketing lift)
        df["expected_lift_units"] = df[["price_lift", "marketing_lift"]].max(axis=1)
        
        # Calculate incremental revenue
        # Revenue = expected_lift_units * proposed_price
        df["incremental_revenue"] = df["expected_lift_units"] * df["proposed_price"]
        
        # Calculate total costs
        # Costs = marketing_spend + labor_cost
        df["total_costs"] = df["total_spend"] + df["labor_cost"]
        
        # Calculate ROI
        # ROI = incremental_revenue - total_costs
        df["roi"] = df["incremental_revenue"] - df["total_costs"]
        
        # Calculate ROI percentage
        df["roi_pct"] = (df["roi"] / df["total_costs"]).replace([float('inf'), -float('inf')], 0)
        df["roi_pct"] = df["roi_pct"].fillna(0)
        
        # Rank by ROI (highest first)
        df = df.sort_values("roi", ascending=False).reset_index(drop=True)
        df["rank"] = range(1, len(df) + 1)
        
        # Add rationale
        def generate_rationale(row):
            if row["roi"] > 0:
                return f"Positive ROI: ${row['roi']:,.2f} (Revenue: ${row['incremental_revenue']:,.2f}, Costs: ${row['total_costs']:,.2f})"
            elif row["roi"] == 0:
                return "Break-even scenario"
            else:
                return f"Negative ROI: ${row['roi']:,.2f} - Consider rejecting"
        
        df["rationale"] = df.apply(generate_rationale, axis=1)
        
        # Write output
        output_cols = ["sku_id", "rank", "roi", "roi_pct", "incremental_revenue", 
                      "total_costs", "expected_lift_units", "rationale"]
        write_csv(df[output_cols], settings.RANKED_PLAN)
        
        # Log summary
        positive_roi_count = len(df[df["roi"] > 0])
        total_roi = df["roi"].sum()
        avg_roi = df["roi"].mean()
        total_revenue = df["incremental_revenue"].sum()
        total_costs = df["total_costs"].sum()
        
        logger.info(f"✅ FinanceAgent completed successfully")
        logger.info(f"   - Ranked scenarios: {len(df)}")
        logger.info(f"   - Scenarios with positive ROI: {positive_roi_count}")
        logger.info(f"   - Total expected ROI: ${total_roi:,.2f}")
        logger.info(f"   - Average ROI: ${avg_roi:,.2f}")
        logger.info(f"   - Total incremental revenue: ${total_revenue:,.2f}")
        logger.info(f"   - Total costs: ${total_costs:,.2f}")
        logger.info(f"   - Output: {settings.RANKED_PLAN}")
        
        return {
            "scenario_count": len(df),
            "positive_roi_count": positive_roi_count,
            "total_roi": float(total_roi),
            "avg_roi": float(avg_roi),
            "total_revenue": float(total_revenue),
            "total_costs": float(total_costs),
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ FinanceAgent failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Test the agent standalone
    result = run_finance()
    print(json.dumps(result, indent=2))
