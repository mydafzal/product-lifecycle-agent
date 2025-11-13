"""
GovernanceAgent - Applies guardrails and final approval decisions.

This agent:
1. Reads ranked action plan and product feedback
2. Applies governance guardrails (price change limits, labor cost caps)
3. Makes final approval decisions (auto-approve, manual review, reject)
4. Writes finalized_actions.csv and audit_log.csv
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


def run_governance():
    """
    Main governance logic - deterministic guardrail application.
    
    Returns:
        dict: Summary of governance decisions
    """
    logger.info("=" * 60)
    logger.info("GOVERNANCE AGENT - Starting execution")
    logger.info("=" * 60)
    
    try:
        # Read ranked action plan
        logger.info("Reading ranked action plan from FinanceAgent...")
        if not settings.RANKED_PLAN.exists():
            logger.error("❌ ranked_action_plan.csv not found. Run FinanceAgent first!")
            return {"status": "error", "error": "ranked_action_plan.csv not found"}
        
        ranked_plan = pd.read_csv(settings.RANKED_PLAN)
        logger.info(f"Loaded {len(ranked_plan)} ranked scenarios")
        
        # Read product feedback
        product_feedback = pd.DataFrame(columns=["sku_id", "decision", "risk_level", "feedback"])
        if settings.PRODUCT_FEEDBACK.exists():
            logger.info("Reading product feedback from ProductAgent...")
            product_feedback = pd.read_csv(settings.PRODUCT_FEEDBACK)
            logger.info(f"Loaded product feedback for {len(product_feedback)} SKUs")
        
        # Read price scenarios for guardrail checks
        price_scenarios = pd.DataFrame(columns=["sku_id", "delta_pct"])
        if settings.PRICE_SCENARIOS.exists():
            price_scenarios = pd.read_csv(settings.PRICE_SCENARIOS)[["sku_id", "delta_pct"]]
        
        # Read labor estimates for cost cap checks
        labor_estimates = pd.DataFrame(columns=["sku_id", "total_cost"])
        if settings.LABOR_ESTIMATES.exists():
            labor_estimates = pd.read_csv(settings.LABOR_ESTIMATES)[["sku_id", "total_cost"]]
        
        # Merge all data
        df = ranked_plan.copy()
        
        if not product_feedback.empty:
            df = df.merge(
                product_feedback[["sku_id", "decision", "risk_level", "feedback"]].rename(
                    columns={"decision": "product_decision", "feedback": "product_feedback"}
                ),
                on="sku_id",
                how="left"
            )
        else:
            df["product_decision"] = "accept"
            df["risk_level"] = "low"
            df["product_feedback"] = "No product validation"
        
        if not price_scenarios.empty:
            df = df.merge(price_scenarios, on="sku_id", how="left")
        else:
            df["delta_pct"] = 0
        
        if not labor_estimates.empty:
            df = df.merge(
                labor_estimates.rename(columns={"total_cost": "labor_cost"}),
                on="sku_id",
                how="left"
            )
        else:
            df["labor_cost"] = 0
        
        # Apply governance guardrails
        def apply_guardrails(row):
            decision = "auto-approved"
            action_type = "price+marketing"
            reasons = []
            
            # Check product decision first
            if row.get("product_decision") == "reject":
                decision = "rejected"
                reasons.append(f"Product rejected: {row.get('product_feedback', 'N/A')}")
                return pd.Series({
                    "action_type": action_type,
                    "decision": decision,
                    "reason": " | ".join(reasons)
                })
            
            # Check price change guardrail
            if abs(row.get("delta_pct", 0)) > settings.MAX_PRICE_CHANGE:
                decision = "manual-review"
                reasons.append(f"Price change ({row['delta_pct']:.1%}) exceeds {settings.MAX_PRICE_CHANGE:.1%} limit")
            
            # Check labor cost cap
            if row.get("labor_cost", 0) > settings.LABOR_COST_CAP:
                if decision == "auto-approved":
                    decision = "manual-review"
                reasons.append(f"Labor cost (${row['labor_cost']:.2f}) exceeds ${settings.LABOR_COST_CAP} cap")
            
            # Check negative ROI
            if row.get("roi", 0) < 0:
                decision = "rejected"
                reasons.append(f"Negative ROI (${row['roi']:,.2f})")
            
            # Check product risk level
            if row.get("risk_level") == "high" and decision == "auto-approved":
                decision = "manual-review"
                reasons.append(f"High risk: {row.get('product_feedback', 'N/A')}")
            
            # Check product review recommendation
            if row.get("product_decision") == "review" and decision == "auto-approved":
                decision = "manual-review"
                reasons.append(f"Product review needed: {row.get('product_feedback', 'N/A')}")
            
            # If no issues
            if not reasons:
                reasons.append("All guardrails satisfied")
            
            return pd.Series({
                "action_type": action_type,
                "decision": decision,
                "reason": " | ".join(reasons)
            })
        
        df[["action_type", "decision", "reason"]] = df.apply(apply_guardrails, axis=1)
        
        # Write finalized actions
        output_cols = ["sku_id", "rank", "action_type", "decision", "reason", "roi"]
        write_csv(df[output_cols], settings.FINAL_ACTIONS)
        
        # Create audit log
        audit_entries = []
        for _, row in df.iterrows():
            audit_entries.append({
                "timestamp": datetime.now().isoformat(),
                "sku_id": row["sku_id"],
                "agent": "GovernanceAgent",
                "action_type": row["action_type"],
                "decision": row["decision"],
                "reason": row["reason"],
                "roi": row["roi"]
            })
        
        audit_df = pd.DataFrame(audit_entries)
        write_csv(audit_df, settings.AUDIT_LOG)
        
        # Log summary
        auto_approved = len(df[df["decision"] == "auto-approved"])
        manual_review = len(df[df["decision"] == "manual-review"])
        rejected = len(df[df["decision"] == "rejected"])
        
        logger.info(f"✅ GovernanceAgent completed successfully")
        logger.info(f"   - Total scenarios evaluated: {len(df)}")
        logger.info(f"   - Auto-approved: {auto_approved}")
        logger.info(f"   - Manual review required: {manual_review}")
        logger.info(f"   - Rejected: {rejected}")
        logger.info(f"   - Output: {settings.FINAL_ACTIONS}")
        logger.info(f"   - Audit log: {settings.AUDIT_LOG}")
        
        return {
            "scenario_count": len(df),
            "auto_approved": auto_approved,
            "manual_review": manual_review,
            "rejected": rejected,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ GovernanceAgent failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Test the agent standalone
    result = run_governance()
    print(json.dumps(result, indent=2))
