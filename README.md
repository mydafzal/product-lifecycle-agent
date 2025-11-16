# Intelligent Management System (IMS)

An AI-powered system for managing product lifecycle with sequential agent workflows and human-in-the-loop governance.

## Overview

This system implements a complete 7-agent workflow for intelligent product management:
- **TriggerAgent**: Detects underperforming SKUs
- **PricingAgent**: Proposes optimal price adjustments  
- **MarketingAgent**: Creates targeted marketing campaigns
- **LaborAgent**: Estimates operational labor costs
- **FinanceAgent**: Ranks actions by ROI and financial impact
- **ProductAgent**: Validates feasibility and inventory constraints
- **GovernanceAgent**: Makes approval decisions with human oversight
- **ReportAgent**: Generates comprehensive transparency reports

## Project Structure

```
Marketing_Life_Item_Agent/
├── agents/                      # Complete agent implementations
│   ├── trigger_agent.py        # Detects underperforming SKUs
│   ├── pricing_agent.py        # Proposes optimal prices
│   ├── marketing_agent.py      # Creates marketing campaigns
│   ├── labor_agent.py          # Estimates labor costs
│   ├── finance_agent.py        # ROI analysis and ranking
│   ├── product_agent.py        # Product feasibility validation
│   ├── governance_agent.py     # Approval decisions
│   └── report_agent.py         # Transparency reporting
├── tools/                       # Data access layer
│   └── data_tools.py           # Unified data access
├── mcp_servers/                 # MCP server for data services
│   ├── server.py               # Centralized MCP server (Port 8000)
│   └── data_functions.py       # Data access functions
├── webapp/                      # Flask web application
│   ├── app.py                  # Main Flask application
│   ├── templates/              # HTML templates
│   │   └── index.html          # Main UI
│   └── static/                 # Frontend assets
│       ├── css/style.css       # UI styling
│       └── js/main.js          # Frontend JavaScript
├── data/
│   ├── input/                  # Input CSV files
│   ├── output/                 # Generated outputs (test_XX folders)
│   └── uploads/                # Web upload storage
├── logs/                        # Application logs
├── settings.py                  # Central configuration
├── crew.py                      # CrewAI workflow orchestration
├── test_workflow.py             # Command-line test runner
├── run_webapp.py                # Web application launcher
├── start_mcp_server.sh          # Start MCP server
├── stop_mcp_servers.sh          # Stop MCP server
└── README.md                    # This file
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

### Web Application (Recommended)

1. **Start the Flask web application**:
```bash
python run_webapp.py
```

2. **Open browser** and navigate to `http://localhost:5000`

3. **Upload CSV files** in the Upload Data section

4. **Run workflow** and monitor progress in real-time

5. **Review governance decisions** - approve/reject SKUs requiring manual review

6. **Download results** including transparency reports

### Command Line Testing

```bash
# Run the complete 7-agent workflow
python test_workflow.py

# Run with custom thresholds
python test_workflow.py --underperf 0.15 --max-price-change 0.25

# Skip result display (just run workflow)
python test_workflow.py --no-display
```

### Using MCP Servers (Production Mode)

MCP servers provide a centralized data access layer for both agents and frontend.

**1. Start MCP server:**
```bash
./start_mcp_server.sh
```

**2. Enable MCP mode in `tools/data_tools.py`:**
```python
USE_MCP_SERVERS = True  # Change from False to True
```

**3. Run workflow:**
```bash
python test_workflow.py
```

**4. Stop server when done:**
```bash
./stop_mcp_servers.sh
```

**Why use MCP servers?**
- Same server can be used by frontend and agents
- Easy to switch from CSV to database later
- Centralized filtering and business logic
- Better performance for multiple agent calls

## Input Data

Place your CSV files in `data/input/`:

- **get_sales.csv**: `sku_id, sales, forecast, plan`
- **get_inventory.csv**: `sku_id, inventory, lead_time`
- **price_optimizer.csv**: `sku_id, optimal_price, elasticity`

## Output Files

Each workflow run creates a unique `test_XX` folder in `data/output/` containing:

**Agent Outputs:**
- **flagged_skus.csv**: Underperforming SKUs (TriggerAgent)
- **choice_sets.json**: Choice sets for processing (TriggerAgent)
- **price_scenarios.csv**: Price recommendations (PricingAgent)
- **campaign_scenarios.csv**: Marketing campaigns (MarketingAgent)
- **labor_cost_estimates.csv**: Labor cost analysis (LaborAgent)
- **ranked_action_plan.csv**: ROI-ranked actions (FinanceAgent)
- **product_feedback.csv**: Feasibility validation (ProductAgent)
- **finalized_actions.csv**: Governance decisions (GovernanceAgent)

**Reports:**
- **transparency_report.csv**: Complete SKU journey data (ReportAgent)
- **transparency_report.md**: Human-readable markdown report (ReportAgent)
- **transparency_report_summary.json**: Summary statistics (ReportAgent)
- **final_approved_actions.csv**: Actions approved by human reviewers
- **governance_decisions.json**: Detailed governance decisions

**Logs:**
- **logs/app.log**: Detailed execution logs
- **workflow_summary_*.json**: Execution summary

## Configuration

### Thresholds (in `settings.py`)

- `UNDERPERF_PCT`: Underperformance threshold (default: 10%)
- `MAX_PRICE_CHANGE`: Maximum allowed price change (default: 20%)
- `MIN_INVENTORY`: Minimum inventory threshold (default: 10 units)
- `LABOR_COST_CAP`: Labor cost cap per store/day (default: $200)

### Web Interface Features

The Flask web application provides:
- **CSV file uploads** with validation
- **Dynamic threshold configuration** via UI
- **Real-time workflow monitoring** with live logs
- **Interactive governance decisions** with approval/rejection
- **Results visualization** and download
- **Transparency reports** with markdown display

## Agent Details

### 1. TriggerAgent
- **Input**: Sales data (actual vs forecast)
- **Logic**: Flags SKUs where `actual < forecast` by threshold %
- **Output**: `flagged_skus.csv`, `choice_sets.json`
- **Deterministic**: Yes (no LLM required)

### 2. PricingAgent
- **Input**: Flagged SKUs, price optimizer data
- **Logic**: Proposes optimal prices using elasticity, respects guardrails
- **Output**: `price_scenarios.csv`
- **Deterministic**: Yes (no LLM required)

### 3. MarketingAgent
- **Input**: Price scenarios, marketing channel data
- **Logic**: Creates targeted campaigns, estimates spend and lift
- **Output**: `campaign_scenarios.csv`
- **Deterministic**: Yes (rule-based channel selection)

### 4. LaborAgent
- **Input**: Campaign scenarios, labor rate data
- **Logic**: Estimates operational labor costs for implementation
- **Output**: `labor_cost_estimates.csv`
- **Deterministic**: Yes (cost calculation based on rules)

### 5. FinanceAgent
- **Input**: All previous agent outputs
- **Logic**: Calculates ROI, ranks actions by financial impact
- **Output**: `ranked_action_plan.csv`
- **Deterministic**: Yes (financial calculations)

### 6. ProductAgent
- **Input**: Ranked actions, inventory data
- **Logic**: Validates feasibility, checks inventory constraints
- **Output**: `product_feedback.csv`
- **Deterministic**: Yes (constraint validation)

### 7. GovernanceAgent
- **Input**: Product feedback, governance rules
- **Logic**: Makes approval decisions, flags manual review cases
- **Output**: `finalized_actions.csv`, `governance_decisions.json`
- **Deterministic**: Yes (rule-based approval logic)

### 8. ReportAgent
- **Input**: All agent outputs, human decisions
- **Logic**: Generates comprehensive transparency reports using LLM
- **Output**: `transparency_report.csv`, `transparency_report.md`
- **Uses LLM**: Yes (for human-readable markdown generation)

## Logs

All execution logs are saved to:
- **logs/app.log**: Detailed agent execution logs
- Console output with real-time progress

## Human-in-the-Loop Governance

The system includes sophisticated governance workflows:

1. **Automatic Approval**: SKUs meeting all criteria are auto-approved
2. **Manual Review**: SKUs with risks (high costs, low ROI, inventory issues) require human review
3. **Interactive UI**: Web interface shows governance popup for manual review decisions
4. **Transparency**: All decisions (automatic and human) are tracked in reports
5. **Audit Trail**: Complete decision history with timestamps and reasons

## Development

### Testing the System

```bash
# Test complete workflow via command line
python test_workflow.py

# Test with custom parameters
python test_workflow.py --underperf 0.15 --max-price-change 0.25

# Test via web interface (recommended)
python run_webapp.py
# Then open http://localhost:5000
```

### Key Features Implemented

- ✅ **Complete 8-agent workflow** (Trigger → Pricing → Marketing → Labor → Finance → Product → Governance → Report)
- ✅ **Web-based UI** with real-time monitoring
- ✅ **Human-in-the-loop governance** with approval/rejection interface  
- ✅ **Transparency reporting** with LLM-generated markdown
- ✅ **Dynamic output folders** (test_XX) for each run
- ✅ **MCP server integration** for scalable data access
- ✅ **Comprehensive logging** and audit trails

## License

Proprietary - Crixent Job Project
