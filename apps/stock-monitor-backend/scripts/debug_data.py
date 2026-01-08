
import asyncio
import sys
import os
from sqlalchemy import text
from loguru import logger

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db_manager

async def check_data():
    await db_manager.initialize()
    
    start_date = "2025-11-20"
    end_date = "2025-12-10"
    target_code = "603601"
    other_code = "603193"
    
    async with db_manager.get_session() as session:
        # Check StockDaily
        logger.info(f"Checking StockDaily for {target_code} and {other_code} ({start_date} to {end_date})...")
        stmt = text("SELECT code, trade_date, close FROM stock_daily WHERE code IN (:c1, :c2) AND trade_date BETWEEN :start AND :end ORDER BY code, trade_date")
        result = await session.execute(stmt, {"c1": target_code, "c2": other_code, "start": start_date, "end": end_date})
        rows = result.fetchall()
        for row in rows:
            logger.info(f"Daily: {row.code} | {row.trade_date} | {row.close}")
            
        if not rows:
            logger.warning("No daily data found!")
            
        # Check Score Result
        logger.info(f"Checking Score Result...")
        stmt = text("SELECT code, trade_date, total_score FROM stock_score_result WHERE code IN (:c1, :c2) AND trade_date BETWEEN :start AND :end ORDER BY code, trade_date")
        result = await session.execute(stmt, {"c1": target_code, "c2": other_code, "start": start_date, "end": end_date})
        rows = result.fetchall()
        for row in rows:
            logger.info(f"Score: {row.code} | {row.trade_date} | {row.total_score}")

if __name__ == "__main__":
    asyncio.run(check_data())
