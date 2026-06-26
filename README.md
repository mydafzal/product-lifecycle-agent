# Product Lifecycle Agent

Product Lifecycle Agent is an AI-assisted operations workflow for identifying underperforming SKUs, proposing commercial actions, validating feasibility, and producing transparent decision reports.

The system uses a sequential multi-agent pipeline with human-in-the-loop governance. It is built to show how agentic workflows can support product, pricing, marketing, labor, finance, and governance decisions from structured business data.

## Highlights

- Seven-stage agent workflow for product lifecycle decisions
- Deterministic business-rule agents for pricing, labor, finance, product, and governance checks
- LLM-powered report generation for human-readable transparency reports
- Flask web app for CSV upload, configuration, workflow execution, approvals, and downloads
- MCP server layer for centralized data access and future database-backed execution
- Audit-oriented outputs for every stage of the decision process
- Command-line workflow runner for repeatable tests

## Agent Workflow

```text
TriggerAgent
  -> PricingAgent
  -> MarketingAgent
  -> LaborAgent
  -> FinanceAgent
  -> ProductAgent
  -> GovernanceAgent
  -> ReportAgent
```

Each agent writes its output to disk so the full reasoning path can be inspected, reviewed, and audited.

## Tech Stack

- Python
- Flask
- CrewAI
- MCP
- Pandas
- Pydantic
- OpenAI
- CSV-based data layer with MCP migration path

## Project Structure

```text
agents/          trigger, pricing, marketing, labor, finance, product, governance, report agents
tools/           shared data access helpers
mcp_servers/     MCP server and data functions
webapp/          Flask UI for uploads, workflow execution, and governance review
data/input/      source CSV files
data/output/     generated workflow results
crew.py          workflow orchestration
test_workflow.py command-line runner
```

## Local Development

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the web app:

```bash
python run_webapp.py
```

Run the workflow from the command line:

```bash
python test_workflow.py
```

Optional MCP mode:

```bash
./start_mcp_server.sh
python test_workflow.py
./stop_mcp_servers.sh
```

## Input Files

Place CSV inputs in `data/input/`:

- `get_sales.csv`
- `get_inventory.csv`
- `price_optimizer.csv`

## Security

Do not commit `.env`, logs, generated output folders, customer data, or real operational exports.

