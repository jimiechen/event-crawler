
import asyncio
import os
import sys
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from datetime import date

# Load environment variables
load_dotenv('/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/.env')

# Add app directory to path
sys.path.append('/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend')

from app.models.stock import StockInfo
from app.models.stock_daily import StockScoreResult

async def check_data():
    db_url = f"mysql+aiomysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_DATABASE')}"
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("--- StockInfo Stats ---")
        # Count total
        total_stocks = await session.execute(select(func.count()).select_from(StockInfo))
        print(f"Total stocks: {total_stocks.scalar()}")
        
        # Count wencai source
        wencai_source = await session.execute(select(func.count()).select_from(StockInfo).where(StockInfo.source == 'wencai'))
        print(f"Stocks with source='wencai': {wencai_source.scalar()}")
        
        # Count active
        active_stocks = await session.execute(select(func.count()).select_from(StockInfo).where(StockInfo.is_active == True))
        print(f"Active stocks: {active_stocks.scalar()}")

        print("\n--- StockScoreResult Stats (2026-01-16) ---")
        target_date = date(2026, 1, 16)
        
        # Total scores
        total_scores = await session.execute(select(func.count()).select_from(StockScoreResult).where(StockScoreResult.trade_date == target_date))
        print(f"Total scores on {target_date}: {total_scores.scalar()}")
        
        # Scores for wencai stocks
        stmt_wencai_scores = select(func.count()).select_from(StockScoreResult).join(
            StockInfo, StockScoreResult.code == StockInfo.code
        ).where(
            StockScoreResult.trade_date == target_date,
            (StockInfo.source == 'wencai') | (StockScoreResult.pool_type == 'wencai')
        )
        wencai_scores = await session.execute(stmt_wencai_scores)
        print(f"Scores for Wencai stocks on {target_date}: {wencai_scores.scalar()}")

        print("\n--- Top 5 Wencai Scores (2026-01-16) ---")
        stmt_top = select(StockScoreResult.code, StockScoreResult.daily_score).join(
            StockInfo, StockScoreResult.code == StockInfo.code
        ).where(
            StockScoreResult.trade_date == target_date,
            (StockInfo.source == 'wencai') | (StockScoreResult.pool_type == 'wencai')
        ).order_by(StockScoreResult.daily_score.desc()).limit(10)
        
        result_top = await session.execute(stmt_top)
        for row in result_top:
            print(f"{row.code}: {row.daily_score}")

    await engine.dispose()

asyncio.run(check_data())
