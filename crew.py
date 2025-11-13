"""
CrewAI Crew Configuration
Wires together all agents for the complete workflow.
"""
from crewai import Agent, Task, Crew, Process
from agents.trigger_agent import run_trigger
from agents.pricing_agent import run_pricing
from agents.marketing_agent import run_marketing
from agents.labor_agent import run_labor
from agents.finance_agent import run_finance
from agents.product_agent import run_product
from agents.governance_agent import run_governance
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_trigger_agent():
    """Create TriggerAgent with CrewAI"""
    return Agent(
        role="Trigger Agent",
        goal="Detect underperforming SKUs and flag them for action",
        backstory=(
            "You are an expert at analyzing sales performance data. "
            "You compare actual sales against forecasts and identify SKUs "
            "that are underperforming and need intervention."
        ),
        verbose=True,
        allow_delegation=False
    )


def create_pricing_agent():
    """Create PricingAgent with CrewAI"""
    return Agent(
        role="Pricing Agent",
        goal="Propose optimal price adjustments using elasticity data",
        backstory=(
            "You are a pricing strategist who uses elasticity models "
            "to recommend price changes that maximize revenue while "
            "respecting business guardrails."
        ),
        verbose=True,
        allow_delegation=False
    )


def create_marketing_agent():
    """Create MarketingAgent with CrewAI"""
    return Agent(
        role="Marketing Agent",
        goal="Recommend marketing campaigns with optimal channel mix",
        backstory=(
            "You are a marketing strategist who allocates budget across "
            "channels to maximize lift while staying within spend limits."
        ),
        verbose=True,
        allow_delegation=False
    )


def create_labor_agent():
    """Create LaborAgent with CrewAI"""
    return Agent(
        role="Labor Agent",
        goal="Estimate labor costs and operational feasibility",
        backstory=(
            "You are an operations expert who estimates labor requirements "
            "and costs to ensure store operations can handle volume increases."
        ),
        verbose=True,
        allow_delegation=False
    )


def create_finance_agent():
    """Create FinanceAgent with CrewAI"""
    return Agent(
        role="Finance Agent",
        goal="Calculate ROI and rank action plans by financial impact",
        backstory=(
            "You are a financial analyst who computes incremental revenue, "
            "costs, and ROI to prioritize the most profitable actions."
        ),
        verbose=True,
        allow_delegation=False
    )


def create_product_agent():
    """Create ProductAgent with CrewAI"""
    return Agent(
        role="Product Agent",
        goal="Validate SKU constraints and provide product feedback",
        backstory=(
            "You are a product manager who acts as a digital twin, "
            "validating inventory, lead times, and product constraints."
        ),
        verbose=True,
        allow_delegation=False
    )


def create_governance_agent():
    """Create GovernanceAgent with CrewAI"""
    return Agent(
        role="Governance Agent",
        goal="Apply guardrails and make final approval decisions",
        backstory=(
            "You are a governance officer who ensures all actions comply "
            "with business rules and makes final approval decisions."
        ),
        verbose=True,
        allow_delegation=False
    )


def create_trigger_task(agent, underperf_threshold=None):
    """Create task for TriggerAgent"""
    return Task(
        description=(
            "Analyze sales data and identify underperforming SKUs. "
            "Flag SKUs where actual sales are significantly below forecast. "
            "Generate choice sets for downstream processing."
        ),
        agent=agent,
        expected_output=(
            "A CSV file of flagged SKUs with gap percentages and reasons, "
            "plus a JSON file of choice sets for further analysis."
        ),
        # Use callback to execute deterministic logic
        callback=lambda _: run_trigger(underperf_threshold)
    )


def create_pricing_task(agent, max_price_change=None):
    """Create task for PricingAgent"""
    return Task(
        description=(
            "For each flagged SKU, propose optimal price adjustments. "
            "Use elasticity data to calculate expected lift. "
            "Respect guardrails on maximum price changes."
        ),
        agent=agent,
        expected_output=(
            "A CSV file of price scenarios with proposed prices, "
            "price deltas, and expected lift in units."
        ),
        # Use callback to execute deterministic logic
        callback=lambda _: run_pricing(max_price_change)
    )


def create_crew(underperf_threshold=None, max_price_change=None):
    """
    Create and configure the CrewAI crew with agents and tasks.
    
    Args:
        underperf_threshold: Override default underperformance threshold
        max_price_change: Override default max price change guardrail
    
    Returns:
        Crew: Configured CrewAI crew
    """
    # Create agents
    trigger_agent = create_trigger_agent()
    pricing_agent = create_pricing_agent()
    
    # Create tasks
    trigger_task = create_trigger_task(trigger_agent, underperf_threshold)
    pricing_task = create_pricing_task(pricing_agent, max_price_change)
    
    # Create crew with sequential process
    crew = Crew(
        agents=[trigger_agent, pricing_agent],
        tasks=[trigger_task, pricing_task],
        process=Process.sequential,  # Run tasks in order
        verbose=True
    )
    
    return crew


def run_workflow(underperf_threshold=None, max_price_change=None):
    """
    Run the complete workflow: Trigger -> Pricing -> Marketing -> Labor -> Finance -> Product -> Governance
    
    Args:
        underperf_threshold: Override default underperformance threshold
        max_price_change: Override default max price change guardrail
    
    Returns:
        dict: Results from the workflow
    """
    logger.info("=" * 80)
    logger.info("STARTING INTELLIGENT MANAGEMENT SYSTEM WORKFLOW")
    logger.info("=" * 80)
    
    results = {}
    
    try:
        # Step 1: Run TriggerAgent
        logger.info("\n[STEP 1/7] Running TriggerAgent...")
        trigger_result = run_trigger(underperf_threshold)
        results["trigger"] = trigger_result
        
        if trigger_result["status"] != "success":
            logger.error("TriggerAgent failed. Stopping workflow.")
            return {"status": "error", "step": "trigger", "error": trigger_result.get("error"), "results": results}
        
        # Step 2: Run PricingAgent
        logger.info("\n[STEP 2/7] Running PricingAgent...")
        pricing_result = run_pricing(max_price_change)
        results["pricing"] = pricing_result
        
        if pricing_result["status"] != "success":
            logger.error("PricingAgent failed. Stopping workflow.")
            return {"status": "error", "step": "pricing", "error": pricing_result.get("error"), "results": results}
        
        # Step 3: Run MarketingAgent
        logger.info("\n[STEP 3/7] Running MarketingAgent...")
        marketing_result = run_marketing()
        results["marketing"] = marketing_result
        
        if marketing_result["status"] != "success":
            logger.error("MarketingAgent failed. Stopping workflow.")
            return {"status": "error", "step": "marketing", "error": marketing_result.get("error"), "results": results}
        
        # Step 4: Run LaborAgent
        logger.info("\n[STEP 4/7] Running LaborAgent...")
        labor_result = run_labor()
        results["labor"] = labor_result
        
        if labor_result["status"] != "success":
            logger.error("LaborAgent failed. Stopping workflow.")
            return {"status": "error", "step": "labor", "error": labor_result.get("error"), "results": results}
        
        # Step 5: Run FinanceAgent
        logger.info("\n[STEP 5/7] Running FinanceAgent...")
        finance_result = run_finance()
        results["finance"] = finance_result
        
        if finance_result["status"] != "success":
            logger.error("FinanceAgent failed. Stopping workflow.")
            return {"status": "error", "step": "finance", "error": finance_result.get("error"), "results": results}
        
        # Step 6: Run ProductAgent
        logger.info("\n[STEP 6/7] Running ProductAgent...")
        product_result = run_product()
        results["product"] = product_result
        
        if product_result["status"] != "success":
            logger.error("ProductAgent failed. Stopping workflow.")
            return {"status": "error", "step": "product", "error": product_result.get("error"), "results": results}
        
        # Step 7: Run GovernanceAgent
        logger.info("\n[STEP 7/7] Running GovernanceAgent...")
        governance_result = run_governance()
        results["governance"] = governance_result
        
        if governance_result["status"] != "success":
            logger.error("GovernanceAgent failed. Stopping workflow.")
            return {"status": "error", "step": "governance", "error": governance_result.get("error"), "results": results}
        
        logger.info("\n" + "=" * 80)
        logger.info("WORKFLOW COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        
        return {
            "status": "success",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Workflow failed with error: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e), "results": results}


if __name__ == "__main__":
    # Test the crew
    result = run_workflow()
    
    import json
    print("\n" + "=" * 80)
    print("WORKFLOW SUMMARY")
    print("=" * 80)
    print(json.dumps(result, indent=2))
