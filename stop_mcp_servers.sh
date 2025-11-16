#!/bin/bash
# Stop MCP Server

echo "🛑 Stopping IMS MCP Server..."

# Kill any Python processes running server.py from mcp_servers directory
pkill -f "python.*mcp_servers/server.py"
pkill -f "python.*server.py"

echo "✅ MCP server stopped!"
