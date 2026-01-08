
import asyncio
import sys
import os

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import db_manager
from app.crawler.wencai_crawler import WencaiCrawler
from datetime import datetime

async def main():
    await db_manager.initialize()
    
    date = "2025-11-28"
    prev_date = "2025-11-27"
    
    query = f"{date}成交量是{prev_date}成交量的2.5倍以上，非北交所 非创业板 非科创板 非ST，概念 行业，{prev_date}和{date}涨幅低于13% 收盘价低于25"
    
    print(f"Executing Query: {query}")
    
    async with db_manager.get_session() as session:
        crawler = WencaiCrawler(session)
        # Use target_stock_code to force check logs
        result = await crawler.fetch_and_parse(query=query, batch_name="DEBUG_TEST", target_stock_code="603601")
        
        print("\n--- Result Summary ---")
        print(f"Status: {result.get('status')}")
        print(f"Total Found: {result.get('total')}")
        print(f"Target Found: {result.get('found_target')}")
        
        if result.get('stocks'):
            print("\nFirst 5 stocks:")
            for s in result['stocks'][:5]:
                print(f"  {s.get('stock_code')} {s.get('stock_name')}")
                
            # Check 603601 specifically in list
            target = next((s for s in result['stocks'] if '603601' in s.get('stock_code', '')), None)
            if target:
                print(f"\nFOUND 603601: {target}")
            else:
                print(f"\n603601 NOT in parsed list.")
                
        else:
            print("No stocks parsed.")

if __name__ == "__main__":
    asyncio.run(main())
