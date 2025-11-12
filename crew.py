"""
CrewAI Crew Configuration
Wires together TriggerAgent and PricingAgent for the workflow.
"""
from crewai import Agent, Task, Crew, Process
from agents.trigger_agent import run_trigger
from agents.pricing_agent import run_pricing
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
    Run the complete workflow: Trigger -> Pricing
    
    Args:
        underperf_threshold: Override default underperformance threshold
        max_price_change: Override default max price change guardrail
    
    Returns:
        dict: Results from the workflow
    """
    logger.info("=" * 80)
    logger.info("STARTING INTELLIGENT MANAGEMENT SYSTEM WORKFLOW")
    logger.info("=" * 80)
    
    try:
        # For now, we'll run agents directly without CrewAI orchestration
        # This gives us more control and clearer logging
        
        # Step 1: Run TriggerAgent
        logger.info("\n[STEP 1/2] Running TriggerAgent...")
        trigger_result = run_trigger(underperf_threshold)
        
        if trigger_result["status"] != "success":
            logger.error("TriggerAgent failed. Stopping workflow.")
            return {"status": "error", "step": "trigger", "error": trigger_result.get("error")}
        
        # Step 2: Run PricingAgent
        logger.info("\n[STEP 2/2] Running PricingAgent...")
        pricing_result = run_pricing(max_price_change)
        
        if pricing_result["status"] != "success":
            logger.error("PricingAgent failed. Stopping workflow.")
            return {"status": "error", "step": "pricing", "error": pricing_result.get("error")}
        
        logger.info("\n" + "=" * 80)
        logger.info("WORKFLOW COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        
        return {
            "status": "success",
            "trigger_result": trigger_result,
            "pricing_result": pricing_result
        }
        
    except Exception as e:
        logger.error(f"Workflow failed with error: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    # Test the crew
    result = run_workflow()
    
    import json
    print("\n" + "=" * 80)
    print("WORKFLOW SUMMARY")
    print("=" * 80)
    print(json.dumps(result, indent=2))
