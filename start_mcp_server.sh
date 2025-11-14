#!/bin/bash

# Start MCP Server for Intelligent Management System
# This script starts the centralized MCP server on port 8000

echo "🚀 Starting IMS MCP Server..."
echo "📍 Server will be available at: http://localhost:8000"
echo ""

cd "$(dirname "$0")/mcp_servers"

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "❌ Error: uvicorn is not installed"
    echo "Please install it with: pip install uvicorn"
    exit 1
fi

# Start the server
python server.py
