import sys
import os
sys.path.append(os.getcwd())

import asyncio
from sqlalchemy import select
from app.database import db_manager
from app.models.stock_daily import StockDaily

from app.models.stock import StockInfo

from sqlalchemy import text

async def check_daily():
    await db_manager.initialize()
    async with db_manager.session_factory() as session:
        # Check specific stock 600724
        print("Checking 600724 data range...")
        
        # 1. Check 600724
        stmt = select(StockDaily.trade_date).where(StockDaily.code == "600724").order_by(StockDaily.trade_date.desc()).limit(5)
        res = await session.execute(stmt)
        dates = res.scalars().all()
        print(f"Code '600724' latest dates: {dates}")
        
        # 2. Check 600724.SH
        stmt = select(StockDaily.trade_date).where(StockDaily.code == "600724.SH").order_by(StockDaily.trade_date.desc()).limit(5)
        res = await session.execute(stmt)
        dates = res.scalars().all()
        print(f"Code '600724.SH' latest dates: {dates}")
        
        # 3. Fuzzy Search for 600724
        stmt = select(StockDaily.code, StockDaily.trade_date).where(StockDaily.code.like("%600724%")).order_by(StockDaily.trade_date.desc()).limit(5)
        res = await session.execute(stmt)
        rows = res.all()
        print(f"Fuzzy '%600724%' latest rows: {rows}")

if __name__ == "__main__":
    asyncio.run(check_daily())
