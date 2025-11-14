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
    Returns sales, forecast, plan per SKU as DataFrame.
    
    Args:
        sku_id: Optional SKU filter
    
    Returns:
        DataFrame with sku_id, sales, forecast, plan
    """
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
        logger.error(f"Failed to get sales data from MCP server: {e}")
        raise

def get_inventory_data(sku_id=None):
    """
    Returns inventory and lead_time per SKU as DataFrame.
    
    Args:
        sku_id: Optional SKU filter
    
    Returns:
        DataFrame with sku_id, inventory, lead_time
    """
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
        logger.error(f"Failed to get inventory data from MCP server: {e}")
        raise

def get_price_optimizer_data(sku_id=None):
    """
    Returns optimal_price and elasticity per SKU as DataFrame.
    
    Args:
        sku_id: Optional SKU filter
    
    Returns:
        DataFrame with sku_id, optimal_price, elasticity
    """
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
        logger.error(f"Failed to get price optimizer data from MCP server: {e}")
        raise

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
        logger.error(f"Failed to get marketing planner data from MCP server: {e}")
        raise

def get_labor_simulator_data(sku_id=None):
    """
    Returns labor hours and cost per SKU as DataFrame.
    
    Args:
        sku_id: Optional SKU filter
    
    Returns:
        DataFrame with sku_id, labor_hours, cost
    """
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
        logger.error(f"Failed to get labor simulator data from MCP server: {e}")
        raise
