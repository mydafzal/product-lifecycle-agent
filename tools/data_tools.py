"""
Data tools for agents to access data via MCP servers.
All data access goes through MCP servers for centralized logic and future scalability.
"""
import pandas as pd
import json
from pathlib import Path
import settings
import logging
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)

# Flag to enable/disable MCP server usage
USE_MCP_SERVER = False  # Set to True to use MCP server, False to use direct CSV access

# Helper function to run async MCP calls
def _run_mcp_tool(tool_name: str, params: dict = None) -> dict:
    """
    Execute an MCP tool call synchronously.
    
    Args:
        tool_name: Name of the MCP tool to call
        params: Parameters to pass to the tool
    
    Returns:
        Dict with the tool result
    """
    async def _call():
        async with streamablehttp_client(settings.MCP_SERVER_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, params or {})
                return result
    
    return asyncio.run(_call())

def get_sales_data(sku_id=None):
    """
    Fetch sales data from MCP server or CSV file.
    
    Args:
        sku_id: Optional SKU ID to filter data
    
    Returns:
        DataFrame with sku_id, sales, forecast, plan
    """
    if USE_MCP_SERVER:
        try:
            params = {"sku_id": sku_id} if sku_id else {}
            result = _run_mcp_tool("get_sales_tool", params)
            
            # Extract data from MCP result
            if hasattr(result, 'content') and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    data = json.loads(content.text)
                    if data.get("status") == "success":
                        return pd.DataFrame(data["data"])
                    else:
                        logger.error(f"MCP tool error: {data.get('error')}")
                        raise Exception(data.get("error", "Unknown error"))
            
            raise Exception("Unexpected response format from MCP server")
        except Exception as e:
            logger.warning(f"MCP server failed, falling back to direct CSV: {e}")
            # Fall through to direct CSV access
    
    # Direct CSV access (fallback or default)
    df = pd.read_csv(settings.SALES_INPUT)
    if sku_id:
        df = df[df["sku_id"] == sku_id]
    return df

def get_inventory_data(sku_id=None):
    """
    Fetch inventory data from MCP server or CSV file.
    
    Args:
        sku_id: Optional SKU ID to filter data
    
    Returns:
        DataFrame with sku_id, inventory, lead_time
    """
    if USE_MCP_SERVER:
        try:
            params = {"sku_id": sku_id} if sku_id else {}
            result = _run_mcp_tool("get_inventory_tool", params)
            
            # Extract data from MCP result
            if hasattr(result, 'content') and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    data = json.loads(content.text)
                    if data.get("status") == "success":
                        return pd.DataFrame(data["data"])
                    else:
                        logger.error(f"MCP tool error: {data.get('error')}")
                        raise Exception(data.get("error", "Unknown error"))
            
            raise Exception("Unexpected response format from MCP server")
        except Exception as e:
            logger.warning(f"MCP server failed, falling back to direct CSV: {e}")
            # Fall through to direct CSV access
    
    # Direct CSV access (fallback or default)
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
    if USE_MCP_SERVER:
        try:
            params = {"sku_id": sku_id} if sku_id else {}
            result = _run_mcp_tool("price_optimizer_tool", params)
            
            # Extract data from MCP result
            if hasattr(result, 'content') and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    data = json.loads(content.text)
                    if data.get("status") == "success":
                        return pd.DataFrame(data["data"])
                    else:
                        logger.error(f"MCP tool error: {data.get('error')}")
                        raise Exception(data.get("error", "Unknown error"))
            
            raise Exception("Unexpected response format from MCP server")
        except Exception as e:
            logger.warning(f"MCP server failed, falling back to direct CSV: {e}")
            # Fall through to direct CSV access
    
    # Direct CSV access (fallback or default)
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
    Returns marketing channels, spend, lift per SKU as DataFrame.
    
    Args:
        sku_id: Optional SKU filter
    
    Returns:
        DataFrame with sku_id, channels, spend, lift
    """
    if USE_MCP_SERVER:
        try:
            params = {"sku_id": sku_id} if sku_id else {}
            result = _run_mcp_tool("marketing_planner_tool", params)
            
            # Extract data from MCP result
            if hasattr(result, 'content') and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    data = json.loads(content.text)
                    if data.get("status") == "success":
                        return pd.DataFrame(data["data"])
                    else:
                        logger.error(f"MCP tool error: {data.get('error')}")
                        raise Exception(data.get("error", "Unknown error"))
            
            raise Exception("Unexpected response format from MCP server")
        except Exception as e:
            logger.warning(f"MCP server failed, falling back to direct CSV: {e}")
            # Fall through to direct CSV access
    
    # Direct CSV access (fallback or default)
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
    if USE_MCP_SERVER:
        try:
            params = {"sku_id": sku_id} if sku_id else {}
            result = _run_mcp_tool("labor_simulator_tool", params)
            
            # Extract data from MCP result
            if hasattr(result, 'content') and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    data = json.loads(content.text)
                    if data.get("status") == "success":
                        return pd.DataFrame(data["data"])
                    else:
                        logger.error(f"MCP tool error: {data.get('error')}")
                        raise Exception(data.get("error", "Unknown error"))
            
            raise Exception("Unexpected response format from MCP server")
        except Exception as e:
            logger.warning(f"MCP server failed, falling back to direct CSV: {e}")
            # Fall through to direct CSV access
    
    # Direct CSV access (fallback or default)
    df = pd.read_csv(settings.LABOR_SIMULATOR_INPUT)
    if sku_id:
        df = df[df["sku_id"] == sku_id]
    return df
