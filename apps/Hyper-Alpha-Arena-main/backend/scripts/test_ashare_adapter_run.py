
import asyncio
import os
import sys
from pprint import pprint

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from adapters.ashare_adapter import AShareDataAdapter

async def test_adapter():
    # Use the local stock monitor database
    db_url = "mysql+aiomysql://stock_user:stock123456@localhost:3306/stock_monitor?charset=utf8mb4"
    adapter = AShareDataAdapter(db_url=db_url)
    
    print(f"Connecting to {db_url}...")
    
    try:
        # Test getting context for a stock (using one from our mock data)
        symbol = "000001"
        print(f"\nFetching context for {symbol}...")
        context = await adapter.get_stock_context(symbol)
        
        if context:
            print("Successfully fetched context:")
            pprint(context.model_dump())
        else:
            print(f"Stock {symbol} not found.")
            
        # Test fetching multiple
        symbols = ["000001", "600519"]
        print(f"\nFetching multiple stocks: {symbols}")
        results = await adapter.get_multiple_stocks(symbols)
        for s, ctx in results.items():
            print(f"{s}: {'Found' if ctx else 'Not Found'}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await adapter.close()

if __name__ == "__main__":
    asyncio.run(test_adapter())
