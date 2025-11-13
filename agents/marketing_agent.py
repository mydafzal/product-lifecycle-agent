"""
MarketingAgent - Recommends marketing campaigns for underperforming SKUs.

This agent:
1. Reads flagged SKUs and price scenarios
2. Reads marketing planner data (channels, spend, lift)
3. Proposes campaign recommendations with expected lift
4. Writes campaign_scenarios.csv
"""
import pandas as pd
import json
from datetime import datetime
import settings
from tools.data_tools import get_marketing_planner_data, write_csv
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


def run_marketing():
    """
    Main marketing logic - deterministic, no LLM needed.
    
    Returns:
        dict: Summary of campaign scenarios
    """
    logger.info("=" * 60)
    logger.info("MARKETING AGENT - Starting execution")
    logger.info("=" * 60)
    
    try:
        # Read flagged SKUs
        logger.info("Reading flagged SKUs from TriggerAgent...")
        if not settings.FLAGGED_SKUS.exists():
            logger.error("❌ flagged_skus.csv not found. Run TriggerAgent first!")
            return {"status": "error", "error": "flagged_skus.csv not found"}
        
        flagged = pd.read_csv(settings.FLAGGED_SKUS)
        logger.info(f"Loaded {len(flagged)} flagged SKUs")
        
        if len(flagged) == 0:
            logger.warning("No flagged SKUs to process!")
            write_csv(pd.DataFrame(columns=["sku_id", "channels", "total_spend", 
                                           "expected_lift_units", "notes"]), 
                     settings.CAMPAIGN_SCENARIOS)
            return {"scenario_count": 0, "status": "success"}
        
        # Read price scenarios (optional - for combined lift estimation)
        price_lift = pd.DataFrame(columns=["sku_id", "expected_lift_units"])
        if settings.PRICE_SCENARIOS.exists():
            logger.info("Reading price scenarios for combined lift estimation...")
            price_scenarios = pd.read_csv(settings.PRICE_SCENARIOS)
            price_lift = price_scenarios[["sku_id", "expected_lift_units"]].rename(
                columns={"expected_lift_units": "price_lift"}
            )
        
        # Get marketing planner data
        logger.info("Fetching marketing planner data...")
        marketing_data = get_marketing_planner_data()
        logger.info(f"Loaded marketing data for {len(marketing_data)} SKUs")
        
        # Merge flagged SKUs with marketing data
        df = flagged[["sku_id", "sales", "forecast", "gap_pct"]].merge(
            marketing_data, on="sku_id", how="left"
        )
        
        # Merge with price lift if available
        if not price_lift.empty:
            df = df.merge(price_lift, on="sku_id", how="left")
            df["price_lift"] = df["price_lift"].fillna(0)
        else:
            df["price_lift"] = 0
        
        # Calculate expected lift from marketing
        # Lift is a percentage, so apply to current sales
        df["marketing_lift_units"] = (df["lift"] * df["sales"]).fillna(0)
        
        # Combined expected lift (price + marketing)
        df["expected_lift_units"] = df["marketing_lift_units"] + df["price_lift"]
        
        # Add notes
        def generate_notes(row):
            if pd.isna(row["channels"]) or pd.isna(row["spend"]):
                return "No marketing data available"
            
            notes = f"Channels: {row['channels']}"
            if row["price_lift"] > 0:
                notes += f" | Combined with pricing lift: {row['price_lift']:.0f} units"
            return notes
        
        df["notes"] = df.apply(generate_notes, axis=1)
        
        # Handle NaN values
        df["channels"] = df["channels"].fillna("No channels")
        df["spend"] = df["spend"].fillna(0)
        df["expected_lift_units"] = df["expected_lift_units"].fillna(0)
        
        # Write output
        output_cols = ["sku_id", "channels", "spend", "expected_lift_units", "notes"]
        output_df = df[output_cols].rename(columns={"spend": "total_spend"})
        write_csv(output_df, settings.CAMPAIGN_SCENARIOS)
        
        # Log summary
        total_spend = df["spend"].sum()
        total_lift = df["expected_lift_units"].sum()
        avg_lift_pct = df["lift"].mean()
        scenarios_with_campaigns = len(df[df["spend"] > 0])
        
        logger.info(f"✅ MarketingAgent completed successfully")
        logger.info(f"   - Campaign scenarios: {len(df)}")
        logger.info(f"   - Scenarios with campaigns: {scenarios_with_campaigns}")
        logger.info(f"   - Total marketing spend: ${total_spend:,.2f}")
        logger.info(f"   - Average lift %: {avg_lift_pct:.1%}")
        logger.info(f"   - Total expected lift: {total_lift:.0f} units")
        logger.info(f"   - Output: {settings.CAMPAIGN_SCENARIOS}")
        
        return {
            "scenario_count": len(df),
            "scenarios_with_campaigns": scenarios_with_campaigns,
            "total_spend": float(total_spend),
            "avg_lift_pct": float(avg_lift_pct),
            "total_expected_lift": float(total_lift),
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ MarketingAgent failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Test the agent standalone
    result = run_marketing()
    print(json.dumps(result, indent=2))
