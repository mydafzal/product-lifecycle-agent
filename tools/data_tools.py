"""
Data tools for agents to access data via MCP servers.
All data access goes through MCP servers for centralized logic and future scalability.
"""
import pandas as pd
import json
from pathlib import Path
import requests
import settings
import logging

logger = logging.getLogger(__name__)

# Flag to switch between MCP servers and direct CSV access
USE_MCP_SERVERS = False  # Set to True when MCP servers are running

def get_sales_data(sku_id=None):
    """
    Returns sales, forecast, plan per SKU as DataFrame.
    
    Args:
        sku_id: Optional SKU filter
    
    Returns:
        DataFrame with sku_id, sales, forecast, plan
    """
    if USE_MCP_SERVERS:
        try:
            response = requests.post(
                f"{settings.SALES_SERVER_URL}/get_sales",
                json={"sku_id": sku_id} if sku_id else {},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                return pd.DataFrame(data["data"])
            else:
                logger.error(f"MCP server error: {data.get('error')}")
                raise Exception(data.get("error", "Unknown error"))
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to sales MCP server: {e}")
            logger.info("Falling back to direct CSV access")
            # Fallback to CSV
            df = pd.read_csv(settings.SALES_INPUT)
            if sku_id:
                df = df[df["sku_id"] == sku_id]
            return df
    else:
        # Direct CSV access
        df = pd.read_csv(settings.SALES_INPUT)
        if sku_id:
            df = df[df["sku_id"] == sku_id]
        return df

def get_inventory_data(sku_id=None):
    """
    Returns inventory and lead_time per SKU as DataFrame.
    
    Args:
        sku_id: Optional SKU filter
    
    Returns:
        DataFrame with sku_id, inventory, lead_time
    """
    if USE_MCP_SERVERS:
        try:
            response = requests.post(
                f"{settings.INVENTORY_SERVER_URL}/get_inventory",
                json={"sku_id": sku_id} if sku_id else {},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                return pd.DataFrame(data["data"])
            else:
                logger.error(f"MCP server error: {data.get('error')}")
                raise Exception(data.get("error", "Unknown error"))
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to inventory MCP server: {e}")
            logger.info("Falling back to direct CSV access")
            # Fallback to CSV
            df = pd.read_csv(settings.INVENTORY_INPUT)
            if sku_id:
                df = df[df["sku_id"] == sku_id]
            return df
    else:
        # Direct CSV access
        df = pd.read_csv(settings.INVENTORY_INPUT)
        if sku_id:
            df = df[df["sku_id"] == sku_id]
        return df

def get_price_optimizer_data(sku_id=None):
    """
    Returns optimal_price and elasticity per SKU as DataFrame.
    
    Args:
        sku_id: Optional SKU filter
    
    Returns:
        DataFrame with sku_id, optimal_price, elasticity
    """
    if USE_MCP_SERVERS:
        try:
            response = requests.post(
                f"{settings.PRICE_OPTIMIZER_SERVER_URL}/price_optimizer",
                json={"sku_id": sku_id} if sku_id else {},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                return pd.DataFrame(data["data"])
            else:
                logger.error(f"MCP server error: {data.get('error')}")
                raise Exception(data.get("error", "Unknown error"))
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to price optimizer MCP server: {e}")
            logger.info("Falling back to direct CSV access")
            # Fallback to CSV
            df = pd.read_csv(settings.PRICE_OPTIMIZER_INPUT)
            if sku_id:
                df = df[df["sku_id"] == sku_id]
            return df
    else:
        # Direct CSV access
        df = pd.read_csv(settings.PRICE_OPTIMIZER_INPUT)
        if sku_id:
            df = df[df["sku_id"] == sku_id]
        return df

def write_csv(df, path):
    """
    Write DataFrame to CSV file.
    """
    df.to_csv(path, index=False)
    print(f"✅ Written: {path}")

def write_json(obj, path):
    """
    Write object to JSON file.
    """
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
    print(f"✅ Written: {path}")

def read_json(path):
    """
    Read JSON file.
    """
    with open(path, "r") as f:
        return json.load(f)

def get_marketing_planner_data(sku_id=None):
    """
    Returns marketing channels, spend, and lift per SKU as DataFrame.
    
    Args:
        sku_id: Optional SKU filter
    
    Returns:
        DataFrame with sku_id, channels, spend, lift
    """
    if USE_MCP_SERVERS:
        try:
            response = requests.post(
                f"{settings.MARKETING_PLANNER_SERVER_URL}/marketing_planner",
                json={"sku_id": sku_id} if sku_id else {},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                return pd.DataFrame(data["data"])
            else:
                logger.error(f"MCP server error: {data.get('error')}")
                raise Exception(data.get("error", "Unknown error"))
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to marketing planner MCP server: {e}")
            logger.info("Falling back to direct CSV access")
            df = pd.read_csv(settings.MARKETING_PLANNER_INPUT)
            if sku_id:
                df = df[df["sku_id"] == sku_id]
            return df
    else:
        # Direct CSV access
        df = pd.read_csv(settings.MARKETING_PLANNER_INPUT)
        if sku_id:
            df = df[df["sku_id"] == sku_id]
        return df

def get_labor_simulator_data(sku_id=None):
    """
    Returns labor hours and cost per SKU as DataFrame.
    
    Args:
        sku_id: Optional SKU filter
    
    Returns:
        DataFrame with sku_id, labor_hours, cost
    """
    if USE_MCP_SERVERS:
        try:
            response = requests.post(
                f"{settings.LABOR_SIMULATOR_SERVER_URL}/labor_simulator",
                json={"sku_id": sku_id} if sku_id else {},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                return pd.DataFrame(data["data"])
            else:
                logger.error(f"MCP server error: {data.get('error')}")
                raise Exception(data.get("error", "Unknown error"))
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to labor simulator MCP server: {e}")
            logger.info("Falling back to direct CSV access")
            df = pd.read_csv(settings.LABOR_SIMULATOR_INPUT)
            if sku_id:
                df = df[df["sku_id"] == sku_id]
            return df
    else:
        # Direct CSV access
        df = pd.read_csv(settings.LABOR_SIMULATOR_INPUT)
        if sku_id:
            df = df[df["sku_id"] == sku_id]
        return df
