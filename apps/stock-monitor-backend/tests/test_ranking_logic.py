
import asyncio
from datetime import date, timedelta
from sqlalchemy import select, desc, and_, func
from app.database import db_manager
from app.models.stock import WencaiStock
from app.models.stock_daily import StockScoreResult

async def test_ranking_logic():
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        # Define a date range (e.g. last 30 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        print(f"Testing ranking from {start_date} to {end_date}")
        
        conditions = [
            StockScoreResult.trade_date >= start_date,
            StockScoreResult.trade_date <= end_date
        ]
        
        # The query from RankingService
        stmt = select(
            WencaiStock.stock_code.label('code'),
            WencaiStock.stock_name.label('name'),
            func.coalesce(func.sum(StockScoreResult.daily_score), 0).label('growth'),
        ).outerjoin(
            StockScoreResult, and_(
                WencaiStock.stock_code == StockScoreResult.code,
                *conditions
            )
        ).group_by(
            WencaiStock.stock_code,
            WencaiStock.stock_name
        ).order_by(
            desc('growth')
        ).limit(20)
        
        result = await session.execute(stmt)
        rows = result.all()
        
        print(f"Top 20 results:")
        for row in rows:
            print(f"Code: {row.code}, Name: {row.name}, Growth: {row.growth}")
            
        # Check if we have mixed positive and zero values
        growths = [row.growth for row in rows]
        has_positive = any(g > 0 for g in growths)
        has_zero = any(g == 0 for g in growths)
        
        print(f"Has positive growth: {has_positive}")
        print(f"Has zero growth: {has_zero}")
        
        if has_positive and has_zero:
             # Verify order
             sorted_growths = sorted(growths, reverse=True)
             is_sorted = (list(growths) == sorted_growths)
             print(f"Is sorted correctly: {is_sorted}")

if __name__ == "__main__":
    asyncio.run(test_ranking_logic())
