# Quick Start Guide - MCP Server

## 🚀 Start MCP Server

```bash
# Option 1: Using script
./start_mcp_server.sh

# Option 2: Direct command
python mcp_servers/server.py
```

Server runs on: **http://localhost:8000**

## ✅ Test Server

```bash
# Health check
curl http://localhost:8000/health

# List all tools
curl http://localhost:8000/tools

# Test a tool
curl -X POST http://localhost:8000/tool/get_sales \
  -H "Content-Type: application/json" \
  -d '{"sku_id": "SKU_0001"}'
```

## 🧪 Run Integration Test

```bash
python test_mcp_integration.py
```

## 🤖 Run Agent Workflow

```bash
python test_workflow.py
```

## 📁 File Structure

```
mcp_servers/
├── server.py           # MCP server + HTTP wrapper
├── tool_handlers.py    # Tool handler functions
├── data_sources.py     # Core data access
└── README.md          # Full documentation

tools/
└── data_tools.py      # Agent data access (calls MCP server)
```

## 🔧 Configuration

**Enable/Disable MCP Server:**
```python
# In tools/data_tools.py
USE_MCP_SERVERS = True   # Use MCP server
USE_MCP_SERVERS = False  # Use direct CSV
```

**Server URL:**
```python
# In settings.py
MCP_SERVER_URL = "http://localhost:8000"
```

## 📊 Available Tools

1. **get_sales** - Sales, forecast, plan data
2. **get_inventory** - Inventory, lead time data
3. **price_optimizer** - Optimal price, elasticity data
4. **marketing_planner** - Marketing channels, spend, lift data
5. **labor_simulator** - Labor hours, cost data

## 🛠️ Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Start MCP server
python mcp_servers/server.py

# Test integration
python test_mcp_integration.py

# Run workflow
python test_workflow.py

# Stop server
# Press Ctrl+C in server terminal
```

## 📖 More Documentation

- **Full Architecture**: See `MCP_ARCHITECTURE.md`
- **Implementation Details**: See `IMPLEMENTATION_SUMMARY.md`
- **MCP Server Details**: See `mcp_servers/README.md`

## 🎯 Quick Troubleshooting

**Server won't start:**
- Check if port 8000 is in use
- Install dependencies: `pip install -r requirements.txt`

**Can't connect to server:**
- Verify server is running
- Check `MCP_SERVER_URL` in `settings.py`
- Server auto-falls back to CSV if unavailable

**Tools return errors:**
- Check CSV files exist in `data/input/`
- View server logs for details
