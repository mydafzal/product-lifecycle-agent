#!/bin/bash
# Start all MCP servers in the background

echo "Starting MCP Servers..."

# Start sales server
echo "Starting Sales Server on port 8001..."
python mcp_servers/sales_server.py &
SALES_PID=$!

# Start inventory server
echo "Starting Inventory Server on port 8002..."
python mcp_servers/inventory_server.py &
INVENTORY_PID=$!

# Start price optimizer server
echo "Starting Price Optimizer Server on port 8003..."
python mcp_servers/price_optimizer_server.py &
PRICE_PID=$!

echo ""
echo "✅ All MCP servers started!"
echo "   - Sales Server (PID: $SALES_PID) - http://localhost:8001"
echo "   - Inventory Server (PID: $INVENTORY_PID) - http://localhost:8002"
echo "   - Price Optimizer Server (PID: $PRICE_PID) - http://localhost:8003"
echo ""
echo "To stop all servers, run: kill $SALES_PID $INVENTORY_PID $PRICE_PID"
echo "Or use: pkill -f 'python mcp_servers'"
echo ""
echo "To enable MCP servers in agents, set USE_MCP_SERVERS=True in tools/data_tools.py"
