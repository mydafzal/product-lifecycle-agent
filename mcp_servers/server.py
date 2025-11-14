import logging
from starlette.applications import Starlette
from starlette.routing import Mount

# Official MCP SDK import (not the third-party 'fastmcp' module)
from mcp.server.fastmcp import FastMCP

# Your CSV-backed functions
from .data_functions import (
    get_sales,
    get_inventory,
    price_optimizer,
    marketing_planner,
    labor_simulator,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataSourcesServer")

# Create the MCP server; configure Streamable HTTP path as /mcp
mcp = FastMCP(name="DataSourcesServer", streamable_http_path="/mcp")

# === Register tools by decorating simple wrappers around your functions ===

@mcp.tool()
def get_sales_tool(sku_id: str | None = None) -> dict:
    """Fetch sales data from CSV (optionally filter by sku_id)."""
    return get_sales(sku_id=sku_id)

@mcp.tool()
def get_inventory_tool(sku_id: str | None = None) -> dict:
    """Fetch inventory data from CSV (optionally filter by sku_id)."""
    return get_inventory(sku_id=sku_id)

@mcp.tool()
def price_optimizer_tool(sku_id: str | None = None) -> dict:
    """Fetch price optimizer data from CSV (optionally filter by sku_id)."""
    return price_optimizer(sku_id=sku_id)

@mcp.tool()
def marketing_planner_tool(sku_id: str | None = None) -> dict:
    """Fetch marketing planner data from CSV (optionally filter by sku_id)."""
    return marketing_planner(sku_id=sku_id)

@mcp.tool()
def labor_simulator_tool(sku_id: str | None = None) -> dict:
    """Fetch labor simulator data from CSV (optionally filter by sku_id)."""
    return labor_simulator(sku_id=sku_id)

logger.info("✅ Registered MCP tools")

# Expose the MCP server over Streamable HTTP at /mcp
app = Starlette(routes=[Mount("/", app=mcp.streamable_http_app())])

if __name__ == "__main__":
    logger.info("🚀 Starting MCP DataSourcesServer at http://localhost:8000/mcp")
    import uvicorn
    uvicorn.run("mcp_servers.server:app", host="0.0.0.0", port=8000, reload=False)
