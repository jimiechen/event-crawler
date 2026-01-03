import sys
import os
sys.path.append(os.getcwd())

import asyncio
from sqlalchemy import select
from app.database import db_manager
from app.models.stock import StockInfo
from app.models.stock_daily import StockDaily

async def check_mismatch():
    await db_manager.initialize()
    async with db_manager.session_factory() as session:
        # Get first 5 active stocks
        stmt = select(StockInfo).where(StockInfo.is_active == True).limit(5)
        result = await session.execute(stmt)
        stocks = result.scalars().all()
        
        for stock in stocks:
            print(f"StockInfo Code: {stock.code}, Name: {stock.name}")
            
            # Check Daily with exact match
            stmt_d = select(StockDaily).where(StockDaily.code == stock.code).order_by(StockDaily.trade_date.desc()).limit(1)
            res_d = await session.execute(stmt_d)
            daily = res_d.scalars().first()
            if daily:
                print(f"  Exact Match Daily: Found, Date: {daily.trade_date}")
            else:
                print(f"  Exact Match Daily: NOT FOUND")
                
            # Check Daily with suffix if not present
            if "." not in stock.code:
                suffix_code = f"{stock.code}.SH" if stock.code.startswith('6') else f"{stock.code}.SZ"
                stmt_s = select(StockDaily).where(StockDaily.code == suffix_code).order_by(StockDaily.trade_date.desc()).limit(1)
                res_s = await session.execute(stmt_s)
                daily_s = res_s.scalars().first()
                if daily_s:
                     print(f"  Suffix Match ({suffix_code}) Daily: Found, Date: {daily_s.trade_date}")

if __name__ == "__main__":
    asyncio.run(check_mismatch())
