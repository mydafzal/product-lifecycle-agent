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
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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


def create_marketing_task(agent):
    """Create task for MarketingAgent"""
    return Task(
        description=(
            "For each flagged SKU, recommend marketing campaigns. "
            "Allocate budget across channels to maximize lift. "
            "Ensure campaigns stay within spend limits."
        ),
        agent=agent,
        expected_output=(
            "A CSV file of campaign scenarios with channel mix, "
            "spend allocation, and expected lift."
        ),
        callback=lambda _: run_marketing()
    )


def create_labor_task(agent):
    """Create task for LaborAgent"""
    return Task(
        description=(
            "Estimate labor costs and operational feasibility. "
            "Calculate labor hours needed for volume increases. "
            "Ensure labor costs stay within cap."
        ),
        agent=agent,
        expected_output=(
            "A CSV file of labor cost estimates with hours, "
            "costs, and feasibility flags."
        ),
        callback=lambda _: run_labor()
    )


def create_finance_task(agent):
    """Create task for FinanceAgent"""
    return Task(
        description=(
            "Calculate ROI and rank action plans by financial impact. "
            "Compute incremental revenue, costs, and net profit. "
            "Prioritize the most profitable actions."
        ),
        agent=agent,
        expected_output=(
            "A CSV file of ranked action plans with ROI, "
            "incremental revenue, and costs."
        ),
        callback=lambda _: run_finance()
    )


def create_product_task(agent):
    """Create task for ProductAgent"""
    return Task(
        description=(
            "Validate SKU constraints and provide product feedback. "
            "Check inventory levels, lead times, and product constraints. "
            "Flag any issues or concerns."
        ),
        agent=agent,
        expected_output=(
            "A CSV file of product feedback with validation results, "
            "inventory status, and recommendations."
        ),
        callback=lambda _: run_product()
    )


def create_governance_task(agent):
    """Create task for GovernanceAgent"""
    return Task(
        description=(
            "Apply guardrails and make final approval decisions. "
            "Ensure all actions comply with business rules. "
            "Generate final approved action list."
        ),
        agent=agent,
        expected_output=(
            "A CSV file of finalized actions with approval status, "
            "compliance flags, and final recommendations."
        ),
        callback=lambda _: run_governance()
    )


def create_crew(underperf_threshold=None, max_price_change=None):
    """
    Create and configure the CrewAI crew with all 7 agents and tasks.
    
    Args:
        underperf_threshold: Override default underperformance threshold
        max_price_change: Override default max price change guardrail
    
    Returns:
        Crew: Configured CrewAI crew with complete workflow
    """
    # Create all 7 agents
    trigger_agent = create_trigger_agent()
    pricing_agent = create_pricing_agent()
    marketing_agent = create_marketing_agent()
    labor_agent = create_labor_agent()
    finance_agent = create_finance_agent()
    product_agent = create_product_agent()
    governance_agent = create_governance_agent()
    
    # Create all 7 tasks
    trigger_task = create_trigger_task(trigger_agent, underperf_threshold)
    pricing_task = create_pricing_task(pricing_agent, max_price_change)
    marketing_task = create_marketing_task(marketing_agent)
    labor_task = create_labor_task(labor_agent)
    finance_task = create_finance_task(finance_agent)
    product_task = create_product_task(product_agent)
    governance_task = create_governance_task(governance_agent)
    
    # Create crew with sequential process (all 7 agents in workflow order)
    crew = Crew(
        agents=[
            trigger_agent,
            pricing_agent,
            marketing_agent,
            labor_agent,
            finance_agent,
            product_agent,
            governance_agent
        ],
        tasks=[
            trigger_task,
            pricing_task,
            marketing_task,
            labor_task,
            finance_task,
            product_task,
            governance_task
        ],
        process=Process.sequential,  # Run tasks in order: Trigger -> Pricing -> Marketing -> Labor -> Finance -> Product -> Governance
        verbose=True
    )
    
    return crew


def run_crew_workflow(underperf_threshold=None, max_price_change=None):
    """
    Run the complete workflow using CrewAI framework.
    This actually executes agents through CrewAI, not direct function calls.
    
    Args:
        underperf_threshold: Override default underperformance threshold
        max_price_change: Override default max price change guardrail
    
    Returns:
        CrewOutput: Results from the CrewAI execution
    """
    logger.info("=" * 80)
    logger.info("STARTING CREWAI INTELLIGENT MANAGEMENT SYSTEM")
    logger.info("=" * 80)
    logger.info(f"Underperformance threshold: {underperf_threshold or 'default'}")
    logger.info(f"Max price change: {max_price_change or 'default'}")
    logger.info("=" * 80)
    
    # Create the crew with all agents and tasks
    crew = create_crew(underperf_threshold, max_price_change)
    
    # Kickoff the crew - this runs all agents sequentially through CrewAI
    logger.info("\n🚀 Kicking off CrewAI workflow...\n")
    result = crew.kickoff()
    
    logger.info("\n" + "=" * 80)
    logger.info("CREWAI WORKFLOW COMPLETED")
    logger.info("=" * 80)
    
    return result


if __name__ == "__main__":
    # Run the crew using CrewAI framework
    print("\n" + "=" * 80)
    print("TESTING CREWAI WORKFLOW")
    print("=" * 80)
    
    result = run_crew_workflow()
    
    print("\n" + "=" * 80)
    print("CREW EXECUTION RESULT")
    print("=" * 80)
    print(result)
