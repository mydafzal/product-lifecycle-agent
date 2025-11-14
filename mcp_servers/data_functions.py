"""
Data source functions for MCP server.
Each function fetches data from CSV files and can filter based on optional parameters.
These functions are registered as tools in the MCP server.
"""
import pandas as pd
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Base data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "input"


def get_sales(sku_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve sales data for SKUs.
    
    Args:
        sku_id: Optional SKU filter
    
    Returns:
        Dict with status and data (list of sales records with sku_id, sales, forecast, plan)
    """
    try:
        data_path = DATA_DIR / "get_sales.csv"
        df = pd.read_csv(data_path)
        
        if sku_id:
            df = df[df["sku_id"] == sku_id]
        
        return {
            "status": "success",
            "data": json.loads(df.to_json(orient="records"))
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def get_inventory(sku_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve inventory data for SKUs.
    
    Args:
        sku_id: Optional SKU filter
    
    Returns:
        Dict with status and data (list of inventory records with sku_id, inventory, lead_time)
    """
    try:
        data_path = DATA_DIR / "get_inventory.csv"
        df = pd.read_csv(data_path)
        
        if sku_id:
            df = df[df["sku_id"] == sku_id]
        
        return {
            "status": "success",
            "data": json.loads(df.to_json(orient="records"))
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def price_optimizer(sku_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve price optimization data for SKUs.
    
    Args:
        sku_id: Optional SKU filter
    
    Returns:
        Dict with status and data (list of price records with sku_id, optimal_price, elasticity)
    """
    try:
        data_path = DATA_DIR / "price_optimizer.csv"
        df = pd.read_csv(data_path)
        
        if sku_id:
            df = df[df["sku_id"] == sku_id]
        
        return {
            "status": "success",
            "data": json.loads(df.to_json(orient="records"))
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def marketing_planner(sku_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve marketing planner data for SKUs.
    
    Args:
        sku_id: Optional SKU filter
    
    Returns:
        Dict with status and data (list of marketing records with sku_id, channels, spend, lift)
    """
    try:
        data_path = DATA_DIR / "marketing_planner.csv"
        df = pd.read_csv(data_path)
        
        if sku_id:
            df = df[df["sku_id"] == sku_id]
        
        return {
            "status": "success",
            "data": json.loads(df.to_json(orient="records"))
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def labor_simulator(sku_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve labor simulator data for SKUs.
    
    Args:
        sku_id: Optional SKU filter
    
    Returns:
        Dict with status and data (list of labor records with sku_id, labor_hours, cost)
    """
    try:
        data_path = DATA_DIR / "labor_simulator.csv"
        df = pd.read_csv(data_path)
        
        if sku_id:
            df = df[df["sku_id"] == sku_id]
        
        return {
            "status": "success",
            "data": json.loads(df.to_json(orient="records"))
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
