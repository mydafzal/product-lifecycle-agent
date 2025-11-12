#!/bin/bash
# Stop all MCP servers

echo "Stopping MCP Servers..."
pkill -f 'python mcp_servers'
echo "✅ All MCP servers stopped!"
