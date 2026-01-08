
import asyncio
import os
import sys
from datetime import date
from sqlalchemy import text, select, func

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(current_dir) # apps/stock-monitor-backend
sys.path.append(backend_root)

from app.database import DatabaseManager
from app.models.stock_daily import StockScoreResult

async def main():
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        # Check latest date for 603601
        result = await session.execute(
            select(func.max(StockScoreResult.trade_date))
            .where(StockScoreResult.code == '603601')
        )
        max_date = result.scalar()
        print(f"Latest score date for 603601: {max_date}")
        
        # Check count
        result = await session.execute(
            select(func.count(StockScoreResult.id))
            .where(StockScoreResult.code == '603601')
            .where(StockScoreResult.trade_date >= date(2025, 11, 20))
        )
        count = result.scalar()
        print(f"Count of scores since 2025-11-20: {count}")

if __name__ == "__main__":
    asyncio.run(main())
