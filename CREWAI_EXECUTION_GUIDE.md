# 🚀 CrewAI Execution Guide

## What Changed & Why

### ❌ **Before (WRONG)**
Your workflow was calling agent **functions directly**, bypassing CrewAI entirely:
```python
# This was NOT using CrewAI framework!
def run_workflow():
    trigger_result = run_trigger()      # Direct function call
    pricing_result = run_pricing()      # Direct function call
    marketing_result = run_marketing()  # Direct function call
    # ... etc
```

**Problem:** This doesn't show how CrewAI agents work, how they execute tasks, or how they use tools/MCP server.

---

### ✅ **After (CORRECT)**
Now your workflow uses **CrewAI's kickoff mechanism** to properly execute agents:
```python
def run_crew_workflow(underperf_threshold=None, max_price_change=None):
    # Create the crew with all agents and tasks
    crew = create_crew(underperf_threshold, max_price_change)
    
    # Kickoff the crew - this runs all agents through CrewAI framework
    result = crew.kickoff()
    
    return result
```

**Benefit:** You can now see:
- ✅ How CrewAI agents execute tasks
- ✅ How agents use callbacks to run deterministic logic
- ✅ How the framework orchestrates sequential execution
- ✅ Verbose logging from CrewAI showing agent thinking
- ✅ Task execution flow and results

---

## 📋 What You'll See Now

### When Running `python crew.py`:

```
================================================================================
STARTING CREWAI INTELLIGENT MANAGEMENT SYSTEM
================================================================================
Underperformance threshold: default
Max price change: default
================================================================================

🚀 Kicking off CrewAI workflow...

[CrewAI] Starting Crew execution...

> Entering new CrewAgentExecutor chain...

[Trigger Agent] Executing task: Flag underperformers and write flagged_skus.csv & choice_sets.json
[Trigger Agent] Using callback to execute deterministic logic...
============================================================
TRIGGER AGENT - Starting execution
============================================================
Using underperformance threshold: 10.0%
Fetching sales data...
Loaded 15 SKU records
Found 5 underperforming SKUs (threshold: 10.0%)
✅ TriggerAgent completed successfully
   - Flagged SKUs: 5
   - Average gap: 15.2%
   - Max gap: 22.0%
   - Output: data/output/flagged_skus.csv
   - Output: data/output/choice_sets.json

[Pricing Agent] Executing task: Generate price_scenarios.csv
[Pricing Agent] Using callback to execute deterministic logic...
============================================================
PRICING AGENT - Starting execution
============================================================
Using max price change guardrail: 20.0%
Reading flagged SKUs from TriggerAgent...
Loaded 5 flagged SKUs
Fetching price optimizer data...
✅ PricingAgent completed successfully
   - Price scenarios: 5
   - Average price delta: 5.2%
   - Total expected lift: 125 units
   - Output: data/output/price_scenarios.csv

[Marketing Agent] Executing task: Generate campaign_scenarios.csv
...

[Labor Agent] Executing task: Generate labor_cost_estimates.csv
...

[Finance Agent] Executing task: Generate ranked_action_plan.csv
...

[Product Agent] Executing task: Generate product_feedback.csv
...

[Governance Agent] Executing task: Generate finalized_actions.csv
...

================================================================================
CREWAI WORKFLOW COMPLETED
================================================================================
```

---

## 🧪 Testing with test_workflow.py

### Run the test:
```bash
python test_workflow.py
```

### What you'll see:
```
================================================================================
INTELLIGENT MANAGEMENT SYSTEM - TEST WORKFLOW
================================================================================

🧪 Test Run #3
Execution started at: 2025-11-14 08:20:15

Configuration:
  - Underperformance threshold: 10.0%
  - Max price change: 20.0%
  - Min inventory: 10
  - Labor cost cap: $200.0

Directories:
  - Input: data/input
  - Output: data/output/test_3
  - Logs: logs

================================================================================
RUNNING CREWAI WORKFLOW
================================================================================

🚀 Starting CrewAI agents execution...
   This will show you how agents work, execute tasks, and use MCP server

[Full CrewAI execution with verbose logging...]

================================================================================
CREWAI EXECUTION COMPLETED
================================================================================

[Crew output showing all task results]

================================================================================
EXECUTION COMPLETE
================================================================================

✅ CrewAI workflow completed successfully!

📁 All outputs saved to: data/output/test_3

Generated files:
  1. flagged_skus.csv - Underperforming SKUs
  2. choice_sets.json - Choice sets
  3. price_scenarios.csv - Price recommendations
  4. campaign_scenarios.csv - Marketing campaigns
  5. labor_cost_estimates.csv - Labor cost estimates
  6. ranked_action_plan.csv - ROI-ranked actions
  7. product_feedback.csv - Product validation
  8. finalized_actions.csv - Governance decisions
  9. summary_report.json - Summary report

📋 Logs: logs/app.log

💡 Review the logs to see how CrewAI agents executed tasks and used MCP server
```

---

## 🔍 How CrewAI Agents Work Now

### 1. **Agent Creation**
Each agent is created with:
- **Role**: "Trigger Agent", "Pricing Agent", etc.
- **Goal**: What the agent aims to achieve
- **Backstory**: Context for the agent
- **Verbose**: `True` to see execution details
- **Allow delegation**: `False` for deterministic execution

### 2. **Task Creation**
Each task has:
- **Description**: What needs to be done
- **Agent**: Which agent executes it
- **Expected output**: What the task should produce
- **Callback**: Function that executes deterministic logic

### 3. **Task Execution via Callback**
```python
Task(
    description="Analyze sales data and identify underperforming SKUs",
    agent=trigger_agent,
    expected_output="flagged_skus.csv and choice_sets.json",
    callback=lambda _: run_trigger(underperf_threshold)  # ← Deterministic logic
)
```

When CrewAI executes this task:
1. Agent receives the task description
2. CrewAI calls the callback function
3. Callback executes `run_trigger()` which:
   - Calls MCP server to get sales data
   - Performs deterministic calculations
   - Writes output files
4. Task completes and returns result

### 4. **Sequential Execution**
```python
crew = Crew(
    agents=[...],
    tasks=[...],
    process=Process.sequential,  # ← Tasks run in order
    verbose=True                 # ← Show execution details
)
```

CrewAI executes tasks one by one:
1. Trigger → 2. Pricing → 3. Marketing → 4. Labor → 5. Finance → 6. Product → 7. Governance

---

## 🛠️ How Agents Use MCP Server

### Flow:
```
CrewAI Agent
    ↓
Task Callback (run_trigger, run_pricing, etc.)
    ↓
Data Tools (get_sales_data, get_price_optimizer_data, etc.)
    ↓
HTTP POST to MCP Server (/invoke endpoint)
    ↓
MCP Server routes to registered tool
    ↓
Data Function (get_sales, get_inventory, etc.)
    ↓
Reads CSV from data/input/
    ↓
Returns JSON response
    ↓
Data Tool converts to DataFrame
    ↓
Agent function uses data for calculations
    ↓
Writes output to data/output/
```

### Example:
```python
# In TriggerAgent callback:
def run_trigger(underperf_threshold):
    # This calls data_tools.get_sales_data()
    sales = get_sales_data()
    
    # Which makes HTTP request:
    # POST http://localhost:8000/invoke
    # Body: {"tool": "get_sales", "params": {}}
    
    # MCP server executes get_sales() function
    # Returns: {"status": "success", "data": [...]}
    
    # Data tool converts to DataFrame
    # Agent performs calculations
    # Writes flagged_skus.csv
```

---

## 📊 Logs to Review

### 1. **Console Output**
Shows CrewAI execution flow, agent thinking, and task results

### 2. **logs/app.log**
Detailed logging from each agent:
- Data fetching
- Calculations
- Output writing
- Errors (if any)

### 3. **Output Files**
All generated CSV/JSON files in `data/output/test_X/`

---

## 🎯 For Frontend Integration

When integrating with frontend, you'll use:

```python
from crew import run_crew_workflow

# Frontend calls this with user-provided thresholds
result = run_crew_workflow(
    underperf_threshold=0.15,  # From UI input
    max_price_change=0.25      # From UI input
)

# result contains CrewAI execution output
# All files are written to data/output/
# Frontend can read and display them
```

This gives you:
- ✅ Full CrewAI agent orchestration
- ✅ Verbose logging for debugging
- ✅ MCP server integration
- ✅ Sequential task execution
- ✅ Deterministic results
- ✅ Error handling

---

## 🚀 Quick Start

### 1. Start MCP Server (optional, has fallback):
```bash
cd mcp_servers
python server.py
# Server runs on http://localhost:8000
```

### 2. Run CrewAI Workflow:
```bash
# Simple test
python crew.py

# Full test with results display
python test_workflow.py

# With custom thresholds
python test_workflow.py --underperf 0.15 --max-price-change 0.25
```

### 3. Review Results:
- Check console output for CrewAI execution flow
- Review `logs/app.log` for detailed agent logs
- Inspect output files in `data/output/test_X/`

---

## ✅ Summary

**Now you have:**
- ✅ Proper CrewAI agent execution (not direct function calls)
- ✅ Visible agent workflow and task execution
- ✅ MCP server integration with data tools
- ✅ Sequential task orchestration
- ✅ Verbose logging showing how agents work
- ✅ Test script that demonstrates complete flow
- ✅ Ready for frontend integration

**Perfect for:**
- Testing agent behavior
- Debugging workflow issues
- Demonstrating to stakeholders
- Frontend integration
- Production deployment

🎉 **Your agents are now properly running through CrewAI!**
