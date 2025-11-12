"""
MCP Server for Price Optimizer Data
Exposes price_optimizer endpoint to retrieve optimal prices and elasticity data.
"""
from fastapi import FastAPI, Request
import pandas as pd
import json
from pathlib import Path

app = FastAPI(title="Price Optimizer MCP Server")

# Path to price optimizer data
DATA_PATH = Path(__file__).parent.parent / "data" / "input" / "price_optimizer.csv"

@app.post("/price_optimizer")
async def price_optimizer(request: Request):
    """
    Retrieve price optimization data for SKUs.
    
    Request body:
        {
            "sku_id": "SKU_0001" (optional - filter by specific SKU)
        }
    
    Returns:
        List of price records with sku_id, optimal_price, elasticity
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
    return {"status": "healthy", "service": "price_optimizer_server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
