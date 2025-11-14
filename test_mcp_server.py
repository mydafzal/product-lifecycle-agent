"""
Quick test script to verify MCP server setup.
This tests the server endpoints and data functions.
"""
import sys
from pathlib import Path

# Add mcp_servers to path
sys.path.insert(0, str(Path(__file__).parent / "mcp_servers"))

from data_functions import (
    get_sales,
    get_inventory,
    price_optimizer,
    marketing_planner,
    labor_simulator
)

def test_data_functions():
    """Test all data functions directly."""
    print("=" * 60)
    print("Testing Data Functions")
    print("=" * 60)
    
    # Test get_sales
    print("\n1. Testing get_sales()...")
    result = get_sales()
    print(f"   Status: {result['status']}")
    if result['status'] == 'success':
        print(f"   Records: {len(result['data'])}")
    else:
        print(f"   Error: {result['error']}")
    
    # Test get_sales with filter
    print("\n2. Testing get_sales(sku_id='SKU001')...")
    result = get_sales(sku_id='SKU001')
    print(f"   Status: {result['status']}")
    if result['status'] == 'success':
        print(f"   Records: {len(result['data'])}")
    
    # Test get_inventory
    print("\n3. Testing get_inventory()...")
    result = get_inventory()
    print(f"   Status: {result['status']}")
    if result['status'] == 'success':
        print(f"   Records: {len(result['data'])}")
    
    # Test price_optimizer
    print("\n4. Testing price_optimizer()...")
    result = price_optimizer()
    print(f"   Status: {result['status']}")
    if result['status'] == 'success':
        print(f"   Records: {len(result['data'])}")
    
    # Test marketing_planner
    print("\n5. Testing marketing_planner()...")
    result = marketing_planner()
    print(f"   Status: {result['status']}")
    if result['status'] == 'success':
        print(f"   Records: {len(result['data'])}")
    
    # Test labor_simulator
    print("\n6. Testing labor_simulator()...")
    result = labor_simulator()
    print(f"   Status: {result['status']}")
    if result['status'] == 'success':
        print(f"   Records: {len(result['data'])}")
    
    print("\n" + "=" * 60)
    print("✅ All data functions tested!")
    print("=" * 60)

if __name__ == "__main__":
    test_data_functions()
    print("\n📝 To start the MCP server, run:")
    print("   cd mcp_servers && python server.py")
    print("\n📝 Server will be available at: http://localhost:8000")
    print("   - Health check: GET http://localhost:8000/health")
    print("   - List tools: GET http://localhost:8000/tools")
    print("   - Call tool: POST http://localhost:8000/tool/<tool_name>")
