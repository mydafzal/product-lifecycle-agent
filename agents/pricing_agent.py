"""
PricingAgent - Proposes optimal prices using elasticity data.

This agent:
1. Reads flagged SKUs from TriggerAgent
2. Reads price optimizer data (optimal_price, elasticity)
3. Proposes prices within guardrails (max price change %)
4. Calculates expected lift based on elasticity
5. Writes price_scenarios.csv
"""
import pandas as pd
import json
import math
from datetime import datetime
import settings
from tools.data_tools import get_price_optimizer_data, write_csv, read_json
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


def run_pricing(max_price_change=None, baseline_price_multiplier=50.0):
    """
    Main pricing logic - deterministic, no LLM needed.
    
    Args:
        max_price_change: Override default max price change guardrail
        baseline_price_multiplier: Multiplier to estimate baseline price from optimal
    
    Returns:
        dict: Summary of pricing scenarios
    """
    logger.info("=" * 60)
    logger.info("PRICING AGENT - Starting execution")
    logger.info("=" * 60)
    
    max_change = max_price_change or settings.MAX_PRICE_CHANGE
    logger.info(f"Using max price change guardrail: {max_change * 100}%")
    
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
            write_csv(pd.DataFrame(columns=["sku_id", "current_price", "proposed_price", 
                                           "delta_pct", "expected_lift_units", "notes"]), 
                     settings.PRICE_SCENARIOS)
            return {"scenario_count": 0, "status": "success"}
        
        # Get price optimizer data
        logger.info("Fetching price optimizer data...")
        price_data = get_price_optimizer_data()
        logger.info(f"Loaded price data for {len(price_data)} SKUs")
        
        # Merge flagged SKUs with price data
        df = flagged[["sku_id", "sales", "forecast"]].merge(
            price_data, on="sku_id", how="left"
        )
        
        # Estimate current price (in real scenario, this would come from a baseline_prices.csv)
        # For demo, we'll use optimal_price as a baseline with some variation
        df["current_price"] = df["optimal_price"] * 0.95  # Assume current is 5% below optimal
        
        # Calculate proposed price with guardrails
        def calculate_proposed_price(row):
            target = row["optimal_price"]
            current = row["current_price"]
            
            if pd.isna(target) or pd.isna(current) or current == 0:
                return current, 0.0, "No price data available"
            
            delta = (target - current) / current
            
            # Apply guardrail
            if abs(delta) > max_change:
                # Cap to guardrail
                capped_target = current * (1 + math.copysign(max_change, delta))
                note = f"Capped at {max_change * 100}% guardrail (optimal would be {delta:.1%})"
                return capped_target, math.copysign(max_change, delta), note
            else:
                note = f"Within guardrails (change: {delta:.1%})"
                return target, delta, note
        
        df[["proposed_price", "delta_pct", "notes"]] = df.apply(
            lambda row: pd.Series(calculate_proposed_price(row)), axis=1
        )
        
        # Calculate expected lift using elasticity
        # Lift formula: % change in quantity = elasticity * % change in price
        # Since elasticity is negative, price decrease leads to quantity increase
        df["expected_lift_units"] = (
            df["delta_pct"] * df["elasticity"] * df["sales"]
        ).abs()
        
        # Handle NaN values
        df["expected_lift_units"] = df["expected_lift_units"].fillna(0)
        df["proposed_price"] = df["proposed_price"].fillna(df["current_price"])
        df["delta_pct"] = df["delta_pct"].fillna(0)
        
        # Write output
        output_cols = ["sku_id", "current_price", "proposed_price", "delta_pct", 
                      "expected_lift_units", "notes"]
        write_csv(df[output_cols], settings.PRICE_SCENARIOS)
        
        # Log summary
        avg_delta = df["delta_pct"].mean()
        total_lift = df["expected_lift_units"].sum()
        scenarios_with_change = len(df[df["delta_pct"] != 0])
        
        logger.info(f"✅ PricingAgent completed successfully")
        logger.info(f"   - Price scenarios: {len(df)}")
        logger.info(f"   - Scenarios with price change: {scenarios_with_change}")
        logger.info(f"   - Average price delta: {avg_delta:.1%}")
        logger.info(f"   - Total expected lift: {total_lift:.0f} units")
        logger.info(f"   - Output: {settings.PRICE_SCENARIOS}")
        
        return {
            "scenario_count": len(df),
            "scenarios_with_change": scenarios_with_change,
            "avg_delta": float(avg_delta),
            "total_expected_lift": float(total_lift),
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ PricingAgent failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Test the agent standalone
    result = run_pricing()
    print(json.dumps(result, indent=2))
