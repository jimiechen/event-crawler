import asyncio
import os
import sys
from sqlalchemy import select, text

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db_manager
from app.models.stock_daily import StockDaily

async def inspect_data():
    await db_manager.initialize()
    async with db_manager.get_session() as session:
        # Check 002735 records
        code = '002735.SZ' # Or 002735
        print(f"Checking data for {code}...")
        
        # Try both formats
        stmt = select(StockDaily).where(StockDaily.code == code).order_by(StockDaily.trade_date.desc()).limit(10)
        result = await session.execute(stmt)
        records = result.scalars().all()
        
        if not records:
            code = '002735'
            print(f"Trying {code}...")
            stmt = select(StockDaily).where(StockDaily.code == code).order_by(StockDaily.trade_date.desc()).limit(10)
            result = await session.execute(stmt)
            records = result.scalars().all()
            
        print(f"Found {len(records)} records.")
        for r in records:
            print(f"Date: {r.trade_date}, Close: {r.close}, AdjFactor: {r.adj_factor}")
            
        # Check max adj_factor
        stmt_max = select(StockDaily.adj_factor).where(StockDaily.code == code).order_by(StockDaily.adj_factor.desc()).limit(1)
        res_max = await session.execute(stmt_max)
        max_factor = res_max.scalar()
        print(f"Max Adj Factor in DB: {max_factor}")

        # Check latest adj_factor (by date)
        stmt_latest = select(StockDaily.adj_factor).where(StockDaily.code == code).order_by(StockDaily.trade_date.desc()).limit(1)
        res_latest = await session.execute(stmt_latest)
        latest_factor = res_latest.scalar()
        print(f"Latest Adj Factor (by date) in DB: {latest_factor}")

if __name__ == "__main__":
    asyncio.run(inspect_data())
