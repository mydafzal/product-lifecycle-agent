"""
MCP Server for Inventory Data
Exposes get_inventory endpoint to retrieve inventory and lead_time data.
"""
from fastapi import FastAPI, Request
import pandas as pd
import json
from pathlib import Path

app = FastAPI(title="Inventory MCP Server")

# Path to inventory data
DATA_PATH = Path(__file__).parent.parent / "data" / "input" / "get_inventory.csv"

@app.post("/get_inventory")
async def get_inventory(request: Request):
    """
    Retrieve inventory data for SKUs.
    
    Request body:
        {
            "sku_id": "SKU_0001" (optional - filter by specific SKU)
        }
    
    Returns:
        List of inventory records with sku_id, inventory, lead_time
    """
    try:
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}
        sku_filter = body.get("sku_id")

        # Read from CSV
        df = pd.read_csv(DATA_PATH)

        if sku_filter:
            df = df[df["sku_id"] == sku_filter]

        return {"data": json.loads(df.to_json(orient="records")), "status": "success"}
    except Exception as e:
        return {"error": str(e), "status": "error"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "inventory_server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
