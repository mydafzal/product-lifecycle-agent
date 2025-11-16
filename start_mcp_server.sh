#!/bin/bash

# Start MCP Server for Intelligent Management System
# This script starts the centralized MCP server on port 8000

echo "🚀 Starting IMS MCP Server..."
echo "📍 Server will be available at: http://localhost:8000"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/mcp_servers"

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Error: python is not installed or not in PATH"
    exit 1
fi

# Check if server.py exists
if [ ! -f "server.py" ]; then
    echo "❌ Error: server.py not found in mcp_servers directory"
    exit 1
fi

echo "Starting MCP server..."
python server.py
