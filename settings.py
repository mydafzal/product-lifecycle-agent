"""
Central settings and configuration for the IMS (Intelligent Management System).
Defines paths, thresholds, and runtime parameters.
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Thresholds (can be updated from frontend)
UNDERPERF_PCT = float(os.getenv("UNDERPERF_PCT", "0.10"))  # 10% default
MAX_PRICE_CHANGE = float(os.getenv("MAX_PRICE_CHANGE", "0.20"))  # 20% guardrail
MIN_INVENTORY = int(os.getenv("MIN_INVENTORY", "10"))
LABOR_COST_CAP = float(os.getenv("LABOR_COST_CAP", "200.0"))  # per store/day

# Input files
SALES_INPUT = INPUT_DIR / "get_sales.csv"
INVENTORY_INPUT = INPUT_DIR / "get_inventory.csv"
PRICE_OPTIMIZER_INPUT = INPUT_DIR / "price_optimizer.csv"
MARKETING_PLANNER_INPUT = INPUT_DIR / "marketing_planner.csv"
LABOR_SIMULATOR_INPUT = INPUT_DIR / "labor_simulator.csv"

# Output files
FLAGGED_SKUS = OUTPUT_DIR / "flagged_skus.csv"
CHOICE_SETS = OUTPUT_DIR / "choice_sets.json"
PRICE_SCENARIOS = OUTPUT_DIR / "price_scenarios.csv"
CAMPAIGN_SCENARIOS = OUTPUT_DIR / "campaign_scenarios.csv"
LABOR_ESTIMATES = OUTPUT_DIR / "labor_cost_estimates.csv"
RANKED_PLAN = OUTPUT_DIR / "ranked_action_plan.csv"
FINAL_ACTIONS = OUTPUT_DIR / "finalized_actions.csv"

# Logs
AUDIT_LOG = LOGS_DIR / "audit_log.csv"
APP_LOG = LOGS_DIR / "app.log"

# MCP Server URLs (for future use)
SALES_SERVER_URL = os.getenv("SALES_SERVER_URL", "http://localhost:8001")
INVENTORY_SERVER_URL = os.getenv("INVENTORY_SERVER_URL", "http://localhost:8002")
PRICE_OPTIMIZER_SERVER_URL = os.getenv("PRICE_OPTIMIZER_SERVER_URL", "http://localhost:8003")
