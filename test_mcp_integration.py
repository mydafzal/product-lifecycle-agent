"""
Test script to verify MCP server integration with data_tools.py
This script tests that the MCP server can be called from data_tools.py
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tools import data_tools
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_mcp_integration():
    """Test MCP server integration with data_tools.py"""
    
    print("=" * 80)
    print("MCP SERVER INTEGRATION TEST")
    print("=" * 80)
    print()
    
    # Check MCP server mode
    print(f"📊 MCP Server Mode: {'ENABLED' if data_tools.USE_MCP_SERVERS else 'DISABLED'}")
    print()
    
    if not data_tools.USE_MCP_SERVERS:
        print("⚠️  MCP servers are disabled. Set USE_MCP_SERVERS = True in tools/data_tools.py")
        print("   Running tests with direct CSV access...")
        print()
    
    # Test 1: Get Sales Data
    print("Test 1: Get Sales Data")
    print("-" * 40)
    try:
        df = data_tools.get_sales_data()
        print(f"✅ Success! Retrieved {len(df)} sales records")
        print(f"   Columns: {list(df.columns)}")
        if len(df) > 0:
            print(f"   Sample: {df.iloc[0].to_dict()}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    print()
    
    # Test 2: Get Inventory Data
    print("Test 2: Get Inventory Data")
    print("-" * 40)
    try:
        df = data_tools.get_inventory_data()
        print(f"✅ Success! Retrieved {len(df)} inventory records")
        print(f"   Columns: {list(df.columns)}")
        if len(df) > 0:
            print(f"   Sample: {df.iloc[0].to_dict()}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    print()
    
    # Test 3: Get Price Optimizer Data
    print("Test 3: Get Price Optimizer Data")
    print("-" * 40)
    try:
        df = data_tools.get_price_optimizer_data()
        print(f"✅ Success! Retrieved {len(df)} price records")
        print(f"   Columns: {list(df.columns)}")
        if len(df) > 0:
            print(f"   Sample: {df.iloc[0].to_dict()}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    print()
    
    # Test 4: Get Marketing Planner Data
    print("Test 4: Get Marketing Planner Data")
    print("-" * 40)
    try:
        df = data_tools.get_marketing_planner_data()
        print(f"✅ Success! Retrieved {len(df)} marketing records")
        print(f"   Columns: {list(df.columns)}")
        if len(df) > 0:
            print(f"   Sample: {df.iloc[0].to_dict()}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    print()
    
    # Test 5: Get Labor Simulator Data
    print("Test 5: Get Labor Simulator Data")
    print("-" * 40)
    try:
        df = data_tools.get_labor_simulator_data()
        print(f"✅ Success! Retrieved {len(df)} labor records")
        print(f"   Columns: {list(df.columns)}")
        if len(df) > 0:
            print(f"   Sample: {df.iloc[0].to_dict()}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    print()
    
    # Test 6: Filter by SKU
    print("Test 6: Filter by SKU (get_sales_data with sku_id)")
    print("-" * 40)
    try:
        df = data_tools.get_sales_data(sku_id="SKU_0001")
        print(f"✅ Success! Retrieved {len(df)} filtered records")
        if len(df) > 0:
            print(f"   Data: {df.iloc[0].to_dict()}")
        else:
            print("   No records found for SKU_0001")
    except Exception as e:
        print(f"❌ Failed: {e}")
    print()
    
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    
    if data_tools.USE_MCP_SERVERS:
        print()
        print("💡 Tips:")
        print("   - Make sure MCP server is running: python mcp_servers/server.py")
        print("   - Check server health: curl http://localhost:8000/health")
        print("   - List tools: curl http://localhost:8000/tools")


if __name__ == "__main__":
    test_mcp_integration()
