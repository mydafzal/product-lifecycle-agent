# MCP Server Architecture

## Overview

The system uses **MCP (Model Context Protocol) Servers** as a centralized data access layer. This architecture provides flexibility, scalability, and separation of concerns.

## Architecture Diagram

```
┌─────────────┐
│  Frontend   │ (Future)
│   (React)   │
└──────┬──────┘
       │
       │ HTTP Requests
       │
       ▼
┌──────────────────────────────────────────────────────┐
│         Centralized MCP Server (:8000)               │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  MCP Framework (Model Context Protocol)    │    │
│  │  - Tool Registration                       │    │
│  │  - stdio transport (for MCP clients)       │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  HTTP Wrapper (Starlette)                  │    │
│  │  - POST /tool/{tool_name}                  │    │
│  │  - GET /tools                              │    │
│  │  - GET /health                             │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  Tool Handlers (tool_handlers.py)          │    │
│  │  - fetch_sales_data()                      │    │
│  │  - fetch_inventory_data()                  │    │
│  │  - fetch_price_optimizer_data()            │    │
│  │  - fetch_marketing_planner_data()          │    │
│  │  - fetch_labor_simulator_data()            │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  Data Sources (data_sources.py)            │    │
│  │  - Core CSV reading logic                  │    │
│  │  - Data filtering and transformation       │    │
│  └────────────────────────────────────────────┘    │
└──────────────┬───────────────────────────────────────┘
               │
               │ Read Data
               ▼
        ┌─────────────┐
        │   CSV Files │
        │ (data/input)│
        └─────────────┘

┌─────────────┐
│   Agents    │
│  (CrewAI)   │
└──────┬──────┘
       │
       │ Function Calls
       ▼
┌─────────────┐
│ data_tools  │
│   .py       │
└──────┬──────┘
       │
       │ HTTP POST (if USE_MCP_SERVERS=True)
       │ OR Direct CSV (if USE_MCP_SERVERS=False)
       ▼
   [MCP Server HTTP endpoint]
```

## Why MCP Servers?

### 1. **Single Source of Truth**
- All data access logic in one place
- Consistent filtering, validation, and business rules
- Easy to audit and debug

### 2. **Flexibility**
- Switch between CSV, Database, or External APIs without changing agent code
- Add caching, rate limiting, authentication at the server level

### 3. **Scalability**
- MCP servers can run on separate machines
- Load balancing and horizontal scaling
- Independent deployment and versioning

### 4. **Frontend Integration**
- Same servers serve both agents AND frontend
- Consistent API contracts
- Real-time data access for UI

### 5. **Future-Proofing**
- Easy to add new data sources (Supabase, PostgreSQL, etc.)
- Can add GraphQL layer on top
- Microservices-ready architecture

## Current Implementation

### Centralized MCP Server

Located in `mcp_servers/` (Port 8000):

**Files:**
1. **`server.py`** - Main MCP server with HTTP wrapper
   - MCP Framework: Tool registration and stdio transport
   - HTTP Wrapper: Starlette app for HTTP access
   - Endpoints:
     - `POST /tool/get_sales` - Get sales data
     - `POST /tool/get_inventory` - Get inventory data
     - `POST /tool/price_optimizer` - Get price optimization data
     - `POST /tool/marketing_planner` - Get marketing data
     - `POST /tool/labor_simulator` - Get labor data
     - `GET /tools` - List all available tools
     - `GET /health` - Health check

2. **`tool_handlers.py`** - Tool handler functions
   - Wrapper functions for each data source
   - Logging and error handling
   - Separates tool registration from implementation

3. **`data_sources.py`** - Core data access logic
   - CSV reading and filtering
   - Data transformation
   - Standardized response format

### Data Tools

`tools/data_tools.py` provides a **unified interface** with:

- **`USE_MCP_SERVERS` flag**: Toggle between MCP servers and direct CSV
- **Automatic fallback**: If MCP server fails, falls back to CSV
- **Filtering support**: Pass `sku_id` parameter to filter data

## Usage Modes

### Mode 1: Direct CSV (Current Default)

**When to use:**
- Quick testing
- Single-machine deployment
- No frontend yet

**Setup:**
```python
# In tools/data_tools.py
USE_MCP_SERVERS = False
```

**Run:**
```bash
python test_workflow.py
```

### Mode 2: With MCP Server (Production)

**When to use:**
- Frontend integration needed
- Multiple services accessing data
- Need caching, authentication, or advanced features
- Centralized logging and monitoring

**Setup:**

1. Start MCP server:
```bash
./start_mcp_server.sh
# OR
python mcp_servers/server.py
```

2. Enable MCP mode (already enabled by default):
```python
# In tools/data_tools.py
USE_MCP_SERVERS = True  # Already set to True
```

3. Run workflow:
```bash
python test_workflow.py
```

4. Test integration:
```bash
python test_mcp_integration.py
```

5. Stop server when done (Ctrl+C in the server terminal)

## Adding Business Logic to MCP Servers

### Example: Add Threshold Filtering

When frontend sends threshold parameters, MCP servers can apply filters:

```python
# In mcp_servers/data_sources.py
def get_sales_data(sku_id: Optional[str] = None, min_sales: float = 0) -> Dict[str, Any]:
    """
    Retrieve sales data for SKUs.
    
    Args:
        sku_id: Optional SKU filter
        min_sales: Minimum sales threshold (NEW)
    
    Returns:
        Dict with status and data
    """
    try:
        data_path = DATA_DIR / "get_sales.csv"
        df = pd.read_csv(data_path)
        
        if sku_id:
            df = df[df["sku_id"] == sku_id]
        
        # NEW: Apply threshold filter
        if min_sales > 0:
            df = df[df["sales"] >= min_sales]
        
        return {
            "status": "success",
            "data": json.loads(df.to_json(orient="records"))
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
```

### Example: Switch to Database

```python
# In mcp_servers/data_sources.py
import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/ims_db")

def get_sales_data(sku_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve sales data from PostgreSQL database.
    """
    try:
        # Connect to database instead of CSV
        conn = psycopg2.connect(DATABASE_URL)
        query = "SELECT sku_id, sales, forecast, plan FROM sales_data"
        
        if sku_id:
            query += f" WHERE sku_id = '{sku_id}'"
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        return {
            "status": "success",
            "data": json.loads(df.to_json(orient="records"))
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
```

**Agent code and tool_handlers.py don't change at all!** ✨

## Frontend Integration

When you build the frontend, it will use the same MCP servers:

```javascript
// Frontend React code
const uploadCSV = async (file) => {
  // Upload CSV to server
  await uploadFile(file);
  
  // Trigger workflow
  const response = await fetch('/api/run-workflow', {
    method: 'POST',
    body: JSON.stringify({
      underperf_threshold: 0.15,
      max_price_change: 0.20
    })
  });
};

// Fetch results from MCP server
const getSalesData = async () => {
  const response = await fetch('http://localhost:8000/tool/get_sales', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  });
  return response.json();
};
```

## Testing MCP Server

### Test Server Endpoints

```bash
# Start server
python mcp_servers/server.py

# In another terminal, test with curl

# Health check
curl http://localhost:8000/health

# List all tools
curl http://localhost:8000/tools

# Test get_sales tool
curl -X POST http://localhost:8000/tool/get_sales \
  -H "Content-Type: application/json" \
  -d '{"sku_id": "SKU_0001"}'

# Test get_inventory tool
curl -X POST http://localhost:8000/tool/get_inventory \
  -H "Content-Type: application/json" \
  -d '{}'

# Test price_optimizer tool
curl -X POST http://localhost:8000/tool/price_optimizer \
  -H "Content-Type: application/json" \
  -d '{"sku_id": "SKU_0002"}'
```

### Test Integration with Agents

```bash
# Start MCP server
./start_mcp_server.sh

# Run integration test
python test_mcp_integration.py

# Run workflow with MCP server enabled
# (USE_MCP_SERVERS=True is already set by default)
python test_workflow.py
```

## Migration Path

### Phase 1: Current (Direct CSV) ✅
- Agents read CSV directly
- Fast development, simple testing

### Phase 2: MCP Servers (Optional)
- Start MCP servers
- Toggle `USE_MCP_SERVERS=True`
- Same functionality, better architecture

### Phase 3: Frontend Integration
- Frontend uses MCP servers
- Agents use MCP servers
- Unified data access layer

### Phase 4: Database Backend
- Update MCP servers to use database
- No changes to agents or frontend
- Production-ready scalability

## Best Practices

1. **Keep MCP servers stateless** - No session data, pure data access
2. **Add validation** - Validate inputs in MCP servers
3. **Error handling** - Return proper error codes and messages
4. **Logging** - Log all requests for debugging
5. **Versioning** - Use API versioning (`/v1/get_sales`) for breaking changes
6. **Documentation** - Use FastAPI's auto-generated docs at `/docs`

## Summary

**MCP Servers = Future-Proof Data Layer**

- ✅ Works now with CSV
- ✅ Easy to switch to database later
- ✅ Frontend can use same servers
- ✅ Agents don't need to change
- ✅ Centralized business logic
- ✅ Production-ready architecture

The `USE_MCP_SERVERS` flag gives you the best of both worlds: simple testing now, scalable architecture later!
