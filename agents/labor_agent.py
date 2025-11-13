"""
LaborAgent - Estimates labor costs for expected volume lift.

This agent:
1. Reads campaign scenarios with expected lift
2. Reads labor simulator data (baseline hours and cost)
3. Estimates incremental labor needs based on volume lift
4. Writes labor_cost_estimates.csv
"""
import pandas as pd
import json
from datetime import datetime
import settings
from tools.data_tools import get_labor_simulator_data, write_csv
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


def run_labor():
    """
    Main labor estimation logic - deterministic, no LLM needed.
    
    Returns:
        dict: Summary of labor cost estimates
    """
    logger.info("=" * 60)
    logger.info("LABOR AGENT - Starting execution")
    logger.info("=" * 60)
    
    try:
        # Read campaign scenarios
        logger.info("Reading campaign scenarios from MarketingAgent...")
        if not settings.CAMPAIGN_SCENARIOS.exists():
            logger.error("❌ campaign_scenarios.csv not found. Run MarketingAgent first!")
            return {"status": "error", "error": "campaign_scenarios.csv not found"}
        
        campaigns = pd.read_csv(settings.CAMPAIGN_SCENARIOS)
        logger.info(f"Loaded {len(campaigns)} campaign scenarios")
        
        if len(campaigns) == 0:
            logger.warning("No campaign scenarios to process!")
            write_csv(pd.DataFrame(columns=["sku_id", "baseline_labor_hours", 
                                           "incremental_labor_hours", "total_labor_hours",
                                           "baseline_cost", "incremental_cost", "total_cost", "notes"]), 
                     settings.LABOR_ESTIMATES)
            return {"scenario_count": 0, "status": "success"}
        
        # Get labor simulator data
        logger.info("Fetching labor simulator data...")
        labor_data = get_labor_simulator_data()
        logger.info(f"Loaded labor data for {len(labor_data)} SKUs")
        
        # Merge campaigns with labor data
        df = campaigns[["sku_id", "expected_lift_units"]].merge(
            labor_data, on="sku_id", how="left"
        )
        
        # Rename baseline columns
        df = df.rename(columns={
            "labor_hours": "baseline_labor_hours",
            "cost": "baseline_cost"
        })
        
        # Calculate incremental labor based on expected lift
        # Simple model: if lift > threshold (50 units), add 10% labor
        # For more sophisticated: scale proportionally to lift
        LIFT_THRESHOLD = 50
        LABOR_SCALING_FACTOR = 0.10  # 10% more labor for significant lift
        
        df["lift_significant"] = df["expected_lift_units"] > LIFT_THRESHOLD
        df["incremental_labor_hours"] = (
            df["baseline_labor_hours"] * LABOR_SCALING_FACTOR * df["lift_significant"]
        ).fillna(0)
        
        df["incremental_cost"] = (
            df["baseline_cost"] * LABOR_SCALING_FACTOR * df["lift_significant"]
        ).fillna(0)
        
        # Total labor
        df["total_labor_hours"] = df["baseline_labor_hours"] + df["incremental_labor_hours"]
        df["total_cost"] = df["baseline_cost"] + df["incremental_cost"]
        
        # Add notes
        def generate_notes(row):
            if pd.isna(row["baseline_labor_hours"]):
                return "No labor data available"
            
            if row["lift_significant"]:
                return f"Incremental labor needed for {row['expected_lift_units']:.0f} unit lift"
            else:
                return "No incremental labor needed (low lift)"
        
        df["notes"] = df.apply(generate_notes, axis=1)
        
        # Handle NaN values
        df["baseline_labor_hours"] = df["baseline_labor_hours"].fillna(0)
        df["baseline_cost"] = df["baseline_cost"].fillna(0)
        df["incremental_labor_hours"] = df["incremental_labor_hours"].fillna(0)
        df["incremental_cost"] = df["incremental_cost"].fillna(0)
        df["total_labor_hours"] = df["total_labor_hours"].fillna(0)
        df["total_cost"] = df["total_cost"].fillna(0)
        
        # Write output
        output_cols = ["sku_id", "baseline_labor_hours", "incremental_labor_hours", 
                      "total_labor_hours", "baseline_cost", "incremental_cost", 
                      "total_cost", "notes"]
        write_csv(df[output_cols], settings.LABOR_ESTIMATES)
        
        # Log summary
        total_baseline_cost = df["baseline_cost"].sum()
        total_incremental_cost = df["incremental_cost"].sum()
        total_cost = df["total_cost"].sum()
        skus_with_incremental = len(df[df["incremental_cost"] > 0])
        
        logger.info(f"✅ LaborAgent completed successfully")
        logger.info(f"   - Labor estimates: {len(df)}")
        logger.info(f"   - SKUs with incremental labor: {skus_with_incremental}")
        logger.info(f"   - Total baseline cost: ${total_baseline_cost:,.2f}")
        logger.info(f"   - Total incremental cost: ${total_incremental_cost:,.2f}")
        logger.info(f"   - Total labor cost: ${total_cost:,.2f}")
        logger.info(f"   - Output: {settings.LABOR_ESTIMATES}")
        
        return {
            "estimate_count": len(df),
            "skus_with_incremental": skus_with_incremental,
            "total_baseline_cost": float(total_baseline_cost),
            "total_incremental_cost": float(total_incremental_cost),
            "total_cost": float(total_cost),
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ LaborAgent failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Test the agent standalone
    result = run_labor()
    print(json.dumps(result, indent=2))
