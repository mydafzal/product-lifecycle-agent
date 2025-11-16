"""
Central settings and configuration for the IMS (Intelligent Management System).
Defines paths, thresholds, and runtime parameters.
All paths are relative to the project root for cross-platform compatibility.
"""
import os
from pathlib import Path

# Base directories - always relative to project root
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
UPLOADS_DIR = DATA_DIR / "uploads"

# Ensure directories exist
for directory in [INPUT_DIR, OUTPUT_DIR, LOGS_DIR, UPLOADS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Business thresholds (can be overridden via environment variables)
UNDERPERF_PCT = float(os.getenv("UNDERPERF_PCT", "0.10"))  # 10% underperformance threshold
MAX_PRICE_CHANGE = float(os.getenv("MAX_PRICE_CHANGE", "0.20"))  # 20% max price change
MIN_INVENTORY = int(os.getenv("MIN_INVENTORY", "10"))  # Minimum inventory units
LABOR_COST_CAP = float(os.getenv("LABOR_COST_CAP", "200.0"))  # Labor cost cap per store/day

# Input file paths
SALES_INPUT = INPUT_DIR / "get_sales.csv"
INVENTORY_INPUT = INPUT_DIR / "get_inventory.csv"
PRICE_OPTIMIZER_INPUT = INPUT_DIR / "price_optimizer.csv"
MARKETING_PLANNER_INPUT = INPUT_DIR / "marketing_planner.csv"
LABOR_SIMULATOR_INPUT = INPUT_DIR / "labor_simulator.csv"

# Output file paths (these will be updated dynamically for test runs)
FLAGGED_SKUS = OUTPUT_DIR / "flagged_skus.csv"
CHOICE_SETS = OUTPUT_DIR / "choice_sets.json"
PRICE_SCENARIOS = OUTPUT_DIR / "price_scenarios.csv"
CAMPAIGN_SCENARIOS = OUTPUT_DIR / "campaign_scenarios.csv"
LABOR_ESTIMATES = OUTPUT_DIR / "labor_cost_estimates.csv"
RANKED_PLAN = OUTPUT_DIR / "ranked_action_plan.csv"
PRODUCT_FEEDBACK = OUTPUT_DIR / "product_feedback.csv"
FINAL_ACTIONS = OUTPUT_DIR / "finalized_actions.csv"

# Log file paths
AUDIT_LOG = LOGS_DIR / "audit_log.csv"
APP_LOG = LOGS_DIR / "app.log"

# MCP Server configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8000"))

# Flask configuration
FLASK_HOST = os.getenv("FLASK_HOST", "localhost")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
