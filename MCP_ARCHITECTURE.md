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
┌─────────────────────────────────────────┐
│         MCP Servers (FastAPI)           │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Sales   │ │Inventory │ │  Price   │ │
│  │ :8001   │ │  :8002   │ │Optimizer │ │
│  │         │ │          │ │  :8003   │ │
│  └─────────┘ └──────────┘ └──────────┘ │
└──────────────┬──────────────────────────┘
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
       │ HTTP Requests (if USE_MCP_SERVERS=True)
       │ OR Direct CSV (if USE_MCP_SERVERS=False)
       ▼
   [Same as above]
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

### MCP Servers

Located in `mcp_servers/`:

1. **`sales_server.py`** (Port 8001)
   - Endpoint: `POST /get_sales`
   - Returns: `sku_id, sales, forecast, plan`

2. **`inventory_server.py`** (Port 8002)
   - Endpoint: `POST /get_inventory`
   - Returns: `sku_id, inventory, lead_time`

3. **`price_optimizer_server.py`** (Port 8003)
   - Endpoint: `POST /price_optimizer`
   - Returns: `sku_id, optimal_price, elasticity`

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

### Mode 2: With MCP Servers (Production)

**When to use:**
- Frontend integration needed
- Multiple services accessing data
- Need caching, authentication, or advanced features

**Setup:**

1. Start MCP servers:
```bash
./start_mcp_servers.sh
```

2. Enable MCP mode:
```python
# In tools/data_tools.py
USE_MCP_SERVERS = True
```

3. Run workflow:
```bash
python test_workflow.py
```

4. Stop servers when done:
```bash
./stop_mcp_servers.sh
```

## Adding Business Logic to MCP Servers

### Example: Add Threshold Filtering

When frontend sends threshold parameters, MCP servers can apply filters:

```python
# In mcp_servers/sales_server.py
@app.post("/get_sales")
async def get_sales(request: Request):
    body = await request.json()
    sku_filter = body.get("sku_id")
    min_sales = body.get("min_sales", 0)  # NEW: threshold from frontend
    
    df = pd.read_csv(DATA_PATH)
    
    if sku_filter:
        df = df[df["sku_id"] == sku_filter]
    
    # NEW: Apply threshold filter
    if min_sales > 0:
        df = df[df["sales"] >= min_sales]
    
    return {"data": df.to_json(orient="records"), "status": "success"}
```

### Example: Switch to Database

```python
# In mcp_servers/sales_server.py
import psycopg2

@app.post("/get_sales")
async def get_sales(request: Request):
    body = await request.json()
    
    # Connect to database instead of CSV
    conn = psycopg2.connect(DATABASE_URL)
    query = "SELECT sku_id, sales, forecast, plan FROM sales_data"
    
    if body.get("sku_id"):
        query += f" WHERE sku_id = '{body['sku_id']}'"
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    return {"data": df.to_json(orient="records"), "status": "success"}
```

**Agent code doesn't change at all!** ✨

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

// Fetch results from MCP servers
const getSalesData = async () => {
  const response = await fetch('http://localhost:8001/get_sales', {
    method: 'POST',
    body: JSON.stringify({})
  });
  return response.json();
};
```

## Testing MCP Servers

### Test Individual Server

```bash
# Start server
python mcp_servers/sales_server.py

# In another terminal, test with curl
curl -X POST http://localhost:8001/get_sales \
  -H "Content-Type: application/json" \
  -d '{"sku_id": "SKU_0001"}'

# Health check
curl http://localhost:8001/health
```

### Test All Servers

```bash
# Start all servers
./start_mcp_servers.sh

# Run workflow with MCP servers enabled
# (Set USE_MCP_SERVERS=True in data_tools.py first)
python test_workflow.py

# Stop all servers
./stop_mcp_servers.sh
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
