from pathlib import Path



# Base directory
BASE_DRECTORY = Path(__file__)
DATA_DIRECTORY = BASE_DRECTORY / "data"
INPUT_DIRECTORY = DATA_DIRECTORY / "input"
OUTPUT_DIRECTORY = DATA_DIRECTORY / "output"

# Input Data Path 
SALES_CSV = INPUT_DIRECTORY / "get_sales.csv"
PRICE_OPTIMIZER_CSV = INPUT_DIRECTORY / "price_optimizer.csv"

# MCP Server
MCP_PORT = 8001  
