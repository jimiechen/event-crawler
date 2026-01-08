
import asyncio
import sys
import os
from datetime import date, timedelta
from sqlalchemy import text
from loguru import logger

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db_manager
from app.services.rule_engine_service import RuleEngineService

# Configure logging
logger.remove()
logger.add(sys.stdout, level="INFO")
logger.add("historical_scoring.log", rotation="10 MB")

async def get_trading_dates(session, start_date, end_date):
    stmt = text("SELECT DISTINCT trade_date FROM stock_daily WHERE trade_date BETWEEN :start AND :end ORDER BY trade_date")
    result = await session.execute(stmt, {"start": start_date, "end": end_date})
    return [row.trade_date for row in result.fetchall()]

async def main():
    logger.info("Initializing historical scoring...")
    await db_manager.initialize()
    
    start_date_str = "2025-11-20"
    end_date_str = "2025-12-10"
    
    async with db_manager.get_session() as session:
        dates = await get_trading_dates(session, start_date_str, end_date_str)
        logger.info(f"Trading dates to score: {dates}")
    
    rule_service = RuleEngineService(db_manager)
    
    for target_date in dates:
        logger.info(f"Calculating scores for {target_date}...")
        try:
            await rule_service.calculate_daily_scores(target_date=target_date, force=True)
            logger.info(f"Completed scoring for {target_date}")
        except Exception as e:
            logger.error(f"Failed to calculate for {target_date}: {e}")
            
    logger.info("All scoring completed.")

if __name__ == "__main__":
    asyncio.run(main())
