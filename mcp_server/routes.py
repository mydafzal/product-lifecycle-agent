import utils.session
from mcp import MCPServer, MCPTool,MCPRequest, MCPResponse
import pandas as pd 
import json 
import logging
import settings

logger = logging.get_logger(__name__)


server = MCPServer(name="Price Marketing Server")

server.register_tool(MCPTool(name="Sales Data Extractor", description="Extracts sales forecast data from the csv", func=get_sales))
server.register_tool(MCPTool(name="Price Optimizer Data Extractor", description="Extracts price optimizer data from the csv", func=get_price_optimizer_data))


@app.route("/invoke", methods=["POST"])
def invoke(request: MCPRequest):
    logger.info("MCP Server is called.")
    tool_name = request.tool_name
    params = request.get("params", {})

    if tool_name not in server.tools:
        return MCPResponse(error="Tool not found")

    tool = server.tools[tool_name]
    try:
        tool_response = tool.handler(params)
        return MCPResponse(result=tool_response)
    except Exception as e:
        return MCPResponse(error=str(e))



if __name__ == "__main__":
    server.run("0.0.0.0", PORT=settings.MCP_PORT)