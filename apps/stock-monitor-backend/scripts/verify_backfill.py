import asyncio
import sys
import os
from sqlalchemy import select, func
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import DatabaseManager
from app.models.stock_daily import StockDaily, StockScoreResult

async def verify():
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    dates = [
        "2025-12-12",
        "2025-12-24",
        "2025-12-25",
        "2025-12-26",
        "2026-01-05",
        "2026-01-13",
        "2026-01-14"
    ]
    
    async with db_manager.get_session() as session:
        for date_str in dates:
            # Check StockDaily count
            stmt_daily = select(func.count(StockDaily.id)).where(StockDaily.trade_date == date_str)
            res_daily = await session.execute(stmt_daily)
            count_daily = res_daily.scalar()
            
            # Check StockScoreResult count
            stmt_score = select(func.count(StockScoreResult.id)).where(StockScoreResult.trade_date == date_str)
            res_score = await session.execute(stmt_score)
            count_score = res_score.scalar()
            
            logger.info(f"Date {date_str}: StockDaily Count = {count_daily}, Score Count = {count_score}")

if __name__ == "__main__":
    asyncio.run(verify())
