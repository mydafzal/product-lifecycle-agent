"""
ProductAgent - Digital twin validator for SKU constraints.

This agent:
1. Reads ranked action plan from FinanceAgent
2. Validates against product constraints (inventory, lead time)
3. Provides accept/reject feedback for each SKU
4. Writes product_feedback.csv
"""
import pandas as pd
import json
from datetime import datetime
import settings
from tools.data_tools import get_inventory_data, write_csv
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


def run_product():
    """
    Main product validation logic - deterministic constraint checking.
    
    Returns:
        dict: Summary of product feedback
    """
    logger.info("=" * 60)
    logger.info("PRODUCT AGENT - Starting execution")
    logger.info("=" * 60)
    
    try:
        # Read ranked action plan
        logger.info("Reading ranked action plan from FinanceAgent...")
        if not settings.RANKED_PLAN.exists():
            logger.error("❌ ranked_action_plan.csv not found. Run FinanceAgent first!")
            return {"status": "error", "error": "ranked_action_plan.csv not found"}
        
        ranked_plan = pd.read_csv(settings.RANKED_PLAN)
        logger.info(f"Loaded {len(ranked_plan)} ranked scenarios")
        
        if len(ranked_plan) == 0:
            logger.warning("No ranked scenarios to validate!")
            write_csv(pd.DataFrame(columns=["sku_id", "rank", "decision", 
                                           "risk_level", "feedback", "constraints"]), 
                     settings.PRODUCT_FEEDBACK)
            return {"scenario_count": 0, "status": "success"}
        
        # Get inventory data for validation
        logger.info("Fetching inventory data for validation...")
        inventory_data = get_inventory_data()
        logger.info(f"Loaded inventory data for {len(inventory_data)} SKUs")
        
        # Merge ranked plan with inventory
        df = ranked_plan[["sku_id", "rank", "roi", "expected_lift_units"]].merge(
            inventory_data, on="sku_id", how="left"
        )
        
        # Validate against constraints
        def validate_sku(row):
            decision = "accept"
            risk_level = "low"
            feedback_parts = []
            constraints = []
            
            # Check inventory constraint
            if pd.notna(row["inventory"]):
                if row["inventory"] < settings.MIN_INVENTORY:
                    decision = "reject"
                    risk_level = "high"
                    feedback_parts.append(f"Low inventory ({row['inventory']} units)")
                    constraints.append(f"inventory<{settings.MIN_INVENTORY}")
                elif row["inventory"] < row["expected_lift_units"]:
                    risk_level = "medium"
                    feedback_parts.append(f"Inventory may not cover expected lift")
                    constraints.append("inventory_risk")
            
            # Check lead time constraint
            if pd.notna(row["lead_time"]):
                if row["lead_time"] > 14:  # Long lead time threshold
                    if decision != "reject":
                        decision = "review"
                    risk_level = "medium" if risk_level == "low" else risk_level
                    feedback_parts.append(f"Long lead time ({row['lead_time']} days)")
                    constraints.append("long_lead_time")
            
            # Check ROI (negative ROI should be flagged)
            if row["roi"] < 0:
                if decision == "accept":
                    decision = "review"
                risk_level = "high"
                feedback_parts.append(f"Negative ROI (${row['roi']:,.2f})")
                constraints.append("negative_roi")
            
            # If no issues found
            if not feedback_parts:
                feedback_parts.append("All constraints satisfied")
            
            feedback = " | ".join(feedback_parts)
            constraint_str = ", ".join(constraints) if constraints else "none"
            
            return pd.Series({
                "decision": decision,
                "risk_level": risk_level,
                "feedback": feedback,
                "constraints": constraint_str
            })
        
        df[["decision", "risk_level", "feedback", "constraints"]] = df.apply(
            validate_sku, axis=1
        )
        
        # Write output
        output_cols = ["sku_id", "rank", "decision", "risk_level", "feedback", "constraints"]
        write_csv(df[output_cols], settings.PRODUCT_FEEDBACK)
        
        # Log summary
        accepted_count = len(df[df["decision"] == "accept"])
        review_count = len(df[df["decision"] == "review"])
        rejected_count = len(df[df["decision"] == "reject"])
        high_risk_count = len(df[df["risk_level"] == "high"])
        
        logger.info(f"✅ ProductAgent completed successfully")
        logger.info(f"   - Total scenarios validated: {len(df)}")
        logger.info(f"   - Accepted: {accepted_count}")
        logger.info(f"   - Needs review: {review_count}")
        logger.info(f"   - Rejected: {rejected_count}")
        logger.info(f"   - High risk scenarios: {high_risk_count}")
        logger.info(f"   - Output: {settings.PRODUCT_FEEDBACK}")
        
        return {
            "scenario_count": len(df),
            "accepted_count": accepted_count,
            "review_count": review_count,
            "rejected_count": rejected_count,
            "high_risk_count": high_risk_count,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ ProductAgent failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Test the agent standalone
    result = run_product()
    print(json.dumps(result, indent=2))
