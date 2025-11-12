"""
MCP Server for Sales Data
Exposes get_sales endpoint to retrieve sales, forecast, and plan data.
"""
from fastapi import FastAPI, Request
import pandas as pd
import json
from pathlib import Path

app = FastAPI(title="Sales MCP Server")

# Path to sales data
DATA_PATH = Path(__file__).parent.parent / "data" / "input" / "get_sales.csv"

@app.post("/get_sales")
async def get_sales(request: Request):
    """
    Retrieve sales data for SKUs.
    
    Request body:
        {
            "sku_id": "SKU_0001" (optional - filter by specific SKU)
        }
    
    Returns:
        List of sales records with sku_id, sales, forecast, plan
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
    return {"status": "healthy", "service": "sales_server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
