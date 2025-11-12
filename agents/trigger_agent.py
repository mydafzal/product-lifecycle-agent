"""
TriggerAgent - Detects underperforming SKUs and generates choice sets.

This agent:
1. Reads sales data (actual vs forecast)
2. Flags SKUs where actual < forecast by threshold %
3. Generates choice sets for downstream agents
4. Writes flagged_skus.csv and choice_sets.json
"""
import pandas as pd
import json
from datetime import datetime
import settings
from tools.data_tools import get_sales_data, write_csv, write_json
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


def run_trigger(underperf_threshold=None):
    """
    Main trigger logic - deterministic, no LLM needed.
    
    Args:
        underperf_threshold: Override default underperformance threshold
    
    Returns:
        dict: Summary of flagged SKUs
    """
    logger.info("=" * 60)
    logger.info("TRIGGER AGENT - Starting execution")
    logger.info("=" * 60)
    
    threshold = underperf_threshold or settings.UNDERPERF_PCT
    logger.info(f"Using underperformance threshold: {threshold * 100}%")
    
    try:
        # Get sales data
        logger.info("Fetching sales data...")
        sales = get_sales_data()
        logger.info(f"Loaded {len(sales)} SKU records")
        
        # Calculate gap percentage
        sales["gap_pct"] = (sales["forecast"] - sales["sales"]) / sales["forecast"]
        
        # Flag underperformers
        flagged = sales[sales["gap_pct"] >= threshold].copy()
        logger.info(f"Found {len(flagged)} underperforming SKUs (threshold: {threshold * 100}%)")
        
        if len(flagged) == 0:
            logger.warning("No underperforming SKUs found!")
            # Write empty files
            write_csv(pd.DataFrame(columns=["sku_id", "sales", "forecast", "plan", "gap_pct", "reason"]), 
                     settings.FLAGGED_SKUS)
            write_json([], settings.CHOICE_SETS)
            return {"flagged_count": 0, "status": "success"}
        
        # Add reason column
        flagged["reason"] = flagged["gap_pct"].apply(
            lambda x: f"Underperforming by {x:.1%} (sales < forecast)"
        )
        
        # Write flagged SKUs
        output_cols = ["sku_id", "sales", "forecast", "plan", "gap_pct", "reason"]
        write_csv(flagged[output_cols], settings.FLAGGED_SKUS)
        
        # Generate choice sets (one per SKU for v1, can extend to clusters later)
        choice_sets = []
        for _, row in flagged.iterrows():
            choice_sets.append({
                "set_id": row["sku_id"],
                "skus": [row["sku_id"]],
                "rationale": row["reason"],
                "gap_pct": float(row["gap_pct"]),
                "sales": int(row["sales"]),
                "forecast": int(row["forecast"])
            })
        
        write_json(choice_sets, settings.CHOICE_SETS)
        
        # Log summary
        logger.info(f"✅ TriggerAgent completed successfully")
        logger.info(f"   - Flagged SKUs: {len(flagged)}")
        logger.info(f"   - Average gap: {flagged['gap_pct'].mean():.1%}")
        logger.info(f"   - Max gap: {flagged['gap_pct'].max():.1%}")
        logger.info(f"   - Output: {settings.FLAGGED_SKUS}")
        logger.info(f"   - Output: {settings.CHOICE_SETS}")
        
        return {
            "flagged_count": len(flagged),
            "avg_gap": float(flagged["gap_pct"].mean()),
            "max_gap": float(flagged["gap_pct"].max()),
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ TriggerAgent failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Test the agent standalone
    result = run_trigger()
    print(json.dumps(result, indent=2))
