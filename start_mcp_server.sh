echo "Starting MCP Server..."
echo "MCP Server is listening at 8001"

py -3.10 mcp_server/routes.py

echo "Server Started Successfully..."
echo "You can kill the server using command -> pkill -f py -3.10 mcp_server/routes.py"