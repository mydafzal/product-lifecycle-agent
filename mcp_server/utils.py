import json
import pandas as pd
import os
import settings
import logging

logger = logging.get_logger(__name__)


def get_sales(params: Optional):
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
        logger.info("Starting the internal tool of MCP")
        file_path = settings.SALES_CSV
        sku_id = params.get("sku_id", "")
        df = pd.read_csv(file_path)

        if not sku:
            return {"data": df.to_json(orient_record=True), "status": True}
    except Exception as e:
        return {"error": e, "status": "error"}

    sales = df[df["sku_id"] == sku_id]
    return {"data": sales.to_json(orient_record=True), "status": True}


def get_price_optimizer_data(params):
    pass