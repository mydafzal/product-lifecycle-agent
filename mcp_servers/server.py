from fastmcp import MCPServer, MCPTool, MCPRequest, MCPResponse
import logging
from data_functions import (
    get_sales,
    get_inventory,
    price_optimizer,
    marketing_planner,
    labor_simulator
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = MCPServer(name="DataSourcesServer")

# Register tools
server.register_tool(MCPTool(
    name="get_sales",
    description="Fetches sales data",
    handler=get_sales
))

server.register_tool(MCPTool(
    name="get_inventory",
    description="Fetches inventory data",
    handler=get_inventory
))

server.register_tool(MCPTool(
    name="price_optimizer",
    description="Fetches price optimizer data",
    handler=price_optimizer
))

server.register_tool(MCPTool(
    name="marketing_planner",
    description="Fetches marketing planner data",
    handler=marketing_planner
))

server.register_tool(MCPTool(
    name="labor_simulator",
    description="Fetches labor simulator data",
    handler=labor_simulator
))

logger.info("Registered MCP tools...")


@server.route("/invoke", methods=["POST"])
def invoke(request: MCPRequest):
    tool_name = request.tool
    params = request.params or {}

    if tool_name not in server.tools:
        return MCPResponse(error=f"Unknown tool: {tool_name}")

    try:
        tool = server.tools[tool_name]
        result = tool.handler(params)
        return MCPResponse(result=result)
    except Exception as e:
        return MCPResponse(error=str(e))


if __name__ == "__main__":
    logger.info("🚀 Starting MCP Data Sources Server at http://localhost:8000")
    server.run("0.0.0.0", 8000)
