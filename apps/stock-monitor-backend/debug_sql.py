
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select, func, desc, and_, text
from sqlalchemy.dialects import postgresql
from app.models.stock_daily import StockScoreResult
from app.models.stock import WencaiStock
from app.database import db_manager
from datetime import date

async def debug():
    # 1. Print SQL
    print("\n=== DEBUG: SQL GENERATION ===")
    
    # Construct the Total Ranking SQL
    target_date = date(2025, 12, 25)
    limit = 100
    window_days = 250
    from datetime import timedelta
    start_date = target_date - timedelta(days=window_days)
    
    conditions = [
        StockScoreResult.trade_date > start_date,
        StockScoreResult.trade_date <= target_date
    ]
    
    stmt_total = select(
        WencaiStock.stock_code.label('code'),
        WencaiStock.stock_name.label('name'),
        func.coalesce(func.sum(StockScoreResult.daily_score), 0).label('total_score')
    ).outerjoin(
        StockScoreResult, and_(
            WencaiStock.stock_code == StockScoreResult.code,
            *conditions
        )
    ).group_by(
        WencaiStock.stock_code,
        WencaiStock.stock_name
    ).order_by(
        desc('total_score')
    ).limit(limit)
    
    print("\n--- TOTAL RANKING SQL (Target Date: 2025-12-25) ---")
    print(stmt_total.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))

    # Construct the Growth Ranking SQL
    growth_date = date(2026, 1, 2) # User's example
    conditions_growth = [
        StockScoreResult.trade_date >= growth_date,
        StockScoreResult.trade_date <= growth_date
    ]
    
    stmt_growth = select(
        WencaiStock.stock_code.label('code'),
        WencaiStock.stock_name.label('name'),
        func.coalesce(func.sum(StockScoreResult.daily_score), 0).label('growth')
    ).outerjoin(
        StockScoreResult, and_(
            WencaiStock.stock_code == StockScoreResult.code,
            *conditions_growth
        )
    ).group_by(
        WencaiStock.stock_code,
        WencaiStock.stock_name
    ).order_by(
        desc('growth')
    ).limit(limit)

    print("\n--- GROWTH RANKING SQL (Date: 2026-01-02) ---")
    print(stmt_growth.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))

    # 2. Check Data
    print("\n=== DEBUG: DATA CHECK ===")
    await db_manager.initialize()
    
    async with db_manager.session_factory() as session:
        # Check Total Count in WencaiStock
        res = await session.execute(select(func.count(WencaiStock.id)))
        wencai_count = res.scalar()
        print(f"Total Stocks in WencaiStock table: {wencai_count}")
        
        # Check Total Distinct Stocks in StockScoreResult
        res = await session.execute(select(func.count(func.distinct(StockScoreResult.code))))
        score_stock_count = res.scalar()
        print(f"Total Distinct Stocks in StockScoreResult table: {score_stock_count}")
        
        # Check Stocks with Score > 0 on 2025-12-25
        res = await session.execute(select(func.count(StockScoreResult.id)).where(
            StockScoreResult.trade_date == date(2025, 12, 25),
            StockScoreResult.daily_score > 0
        ))
        count_2025_12_25 = res.scalar()
        print(f"Stocks with Score > 0 on 2025-12-25: {count_2025_12_25}")
        
        if count_2025_12_25 < 10:
            print("  -> Details of stocks with score > 0 on 2025-12-25:")
            res = await session.execute(select(StockScoreResult.code, StockScoreResult.daily_score).where(
                StockScoreResult.trade_date == date(2025, 12, 25),
                StockScoreResult.daily_score > 0
            ))
            for row in res.all():
                print(f"     {row.code}: {row.daily_score}")

        # Check Stocks with Score > 0 on 2026-01-05
    res = await session.execute(select(func.count(StockScoreResult.id)).where(
        StockScoreResult.trade_date == date(2026, 1, 5),
        StockScoreResult.daily_score > 0
    ))
    count_2026_01_05 = res.scalar()
    print(f"Stocks with Score > 0 on 2026-01-05: {count_2026_01_05}")
    
    if count_2026_01_05 > 0:
        print("  -> Details for 2026-01-05:")
        res = await session.execute(select(StockScoreResult.code, StockScoreResult.daily_score).where(
            StockScoreResult.trade_date == date(2026, 1, 5),
            StockScoreResult.daily_score > 0
        ))
        for row in res.all():
            print(f"     {row.code}: {row.daily_score}")

if __name__ == "__main__":
    asyncio.run(debug())
