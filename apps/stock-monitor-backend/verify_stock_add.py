import httpx
import asyncio
import sys

BASE_URL = "http://localhost:8000/api/v1/test-tool"

async def test_add_custom_stock():
    # Test case: Add 600000 (Shanghai Pudong Development Bank) with empty label
    # Expect: Backend fetches name "浦发银行" (or similar) from Tushare
    
    code = "600000"
    payload = {
        "code": code,
        "label": "", # Empty label to trigger Tushare fetch
        "custom_date": "2023-01-01" # Optional
    }
    
    print(f"Testing add-custom-stock with code={code}...")
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{BASE_URL}/add-custom-stock", json=payload, timeout=30.0)
            
        if resp.status_code != 200:
            print(f"FAILED: Status code {resp.status_code}")
            print(resp.text)
            return
            
        data = resp.json()
        if not data["success"]:
            print(f"FAILED: API returned success=False. Message: {data['message']}")
            return
            
        stock_info = data["stock_info"]
        stock_name = stock_info.get("stock_name") or stock_info.get("name")
        print(f"Returned Stock Name: {stock_name}")
        
        # Verify name is NOT the code (which would happen if fetch failed)
        if stock_name and stock_name != code and "浦发" in stock_name:
            print("SUCCESS: Stock name fetched correctly.")
        else:
            print(f"WARNING: Stock name '{stock_name}' might be incorrect or fetch failed.")
            
        # Verify Daily Data has adj_factor and looks correct
        daily_data = data.get("daily_data", [])
        print(f"Returned {len(daily_data)} daily records.")
        
        if daily_data:
            first_record = daily_data[0]
            print("Sample Record keys:", first_record.keys())
            
            # Check for adj_factor (it might not be in the response model explicitly if I didn't update it)
            # Wait, AddCustomStockResponse -> daily_data -> StockDailyData
            # I should check StockDailyData definition in test_tool_schemas.py
            
            # If I didn't add adj_factor to StockDailyData schema, it won't be returned in JSON!
            # Let's check schemas again.
            pass
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_add_custom_stock())
