# Intelligent Management System (IMS)

An AI-powered system for managing product lifecycle with sequential agent workflows.

## Overview

This system implements a multi-agent workflow for intelligent product management:
- **TriggerAgent**: Detects underperforming SKUs
- **PricingAgent**: Proposes optimal price adjustments
- *(Future)* Marketing, Labor, Finance, Governance, and Product agents

## Project Structure

```
Marketing_Life_Item_Agent/
├── agents/                      # Agent implementations
│   ├── trigger_agent.py        # Detects underperformers
│   └── pricing_agent.py        # Proposes prices
├── tools/                       # Data access layer
│   └── data_tools.py           # Unified data access (MCP or CSV)
├── mcp_servers/                 # MCP servers for data services
│   ├── sales_server.py         # Port 8001
│   ├── inventory_server.py     # Port 8002
│   └── price_optimizer_server.py # Port 8003
├── data/
│   ├── input/                  # Input CSV files
│   └── output/                 # Generated outputs
├── logs/                        # Application logs
├── settings.py                  # Configuration
├── crew.py                      # CrewAI workflow orchestration
├── test_workflow.py             # Test runner
├── start_mcp_servers.sh         # Start all MCP servers
├── stop_mcp_servers.sh          # Stop all MCP servers
└── MCP_ARCHITECTURE.md          # Detailed MCP documentation
```

## Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure settings** (optional):
Create a `.env` file to override defaults:
```env
UNDERPERF_PCT=0.15          # 15% underperformance threshold
MAX_PRICE_CHANGE=0.20       # 20% max price change
MIN_INVENTORY=10
```

## Usage

### Quick Start (Direct CSV Mode - Default)

```bash
# Run the complete workflow
python test_workflow.py
```

### Run with Custom Thresholds

```bash
python test_workflow.py --underperf 0.15 --max-price-change 0.25
```

### Run Individual Agents

```bash
# Test TriggerAgent only
python agents/trigger_agent.py

# Test PricingAgent only (requires TriggerAgent output)
python agents/pricing_agent.py
```

### Using MCP Servers (Production Mode)

MCP servers provide a centralized data access layer for both agents and frontend.

**1. Start all MCP servers:**
```bash
./start_mcp_servers.sh
```

**2. Enable MCP mode in `tools/data_tools.py`:**
```python
USE_MCP_SERVERS = True  # Change from False to True
```

**3. Run workflow:**
```bash
python test_workflow.py
```

**4. Stop servers when done:**
```bash
./stop_mcp_servers.sh
```

**Why use MCP servers?**
- Same servers can be used by frontend
- Easy to switch from CSV to database later
- Centralized filtering and business logic
- See `MCP_ARCHITECTURE.md` for details

## Input Data

Place your CSV files in `data/input/`:

- **get_sales.csv**: `sku_id, sales, forecast, plan`
- **get_inventory.csv**: `sku_id, inventory, lead_time`
- **price_optimizer.csv**: `sku_id, optimal_price, elasticity`

## Output Files

The workflow generates:

- **data/output/flagged_skus.csv**: Underperforming SKUs
- **data/output/choice_sets.json**: Choice sets for downstream processing
- **data/output/price_scenarios.csv**: Proposed price adjustments
- **logs/app.log**: Detailed execution logs
- **data/output/workflow_summary_*.json**: Execution summary

## Configuration

### Thresholds (in `settings.py`)

- `UNDERPERF_PCT`: Underperformance threshold (default: 10%)
- `MAX_PRICE_CHANGE`: Maximum allowed price change (default: 20%)
- `MIN_INVENTORY`: Minimum inventory threshold (default: 10 units)
- `LABOR_COST_CAP`: Labor cost cap per store/day (default: $200)

### Future Frontend Integration

The system is designed to accept parameters from a frontend:
- CSV file uploads
- Dynamic threshold configuration
- Real-time workflow monitoring
- Results visualization

## Agent Details

### TriggerAgent
- **Input**: Sales data (actual vs forecast)
- **Logic**: Flags SKUs where `actual < forecast` by threshold %
- **Output**: `flagged_skus.csv`, `choice_sets.json`
- **Deterministic**: Yes (no LLM required)

### PricingAgent
- **Input**: Flagged SKUs, price optimizer data
- **Logic**: Proposes optimal prices using elasticity, respects guardrails
- **Output**: `price_scenarios.csv`
- **Deterministic**: Yes (no LLM required)

## Logs

All execution logs are saved to:
- **logs/app.log**: Detailed agent execution logs
- Console output with real-time progress

## Future Enhancements

- Marketing Agent (campaign recommendations)
- Labor Agent (operational impact)
- Finance Agent (ROI ranking)
- Governance Agent (approval workflows)
- Product Agent (digital twin validation)
- Frontend UI for workflow management
- Real-time MCP server integration

## Development

### Adding New Agents

1. Create agent file in `agents/`
2. Implement `run_<agent>()` function
3. Add to workflow in `crew.py`
4. Update `test_workflow.py` to include new agent

### Testing

```bash
# Run full workflow test
python test_workflow.py

# Run with verbose logging
python test_workflow.py --no-display
```

## License

Proprietary - Crixent Job Project
