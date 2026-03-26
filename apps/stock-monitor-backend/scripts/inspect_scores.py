
import asyncio
from datetime import date
from sqlalchemy import select, and_
from app.database import DatabaseManager
from app.models.stock_daily import StockScoreResult

from app.models.stock import WencaiStock

async def inspect_rule_scores():
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        # Check 603601 on 2025-11-28 in StockScoreResult
        print("--- StockScoreResult ---")
        stmt = select(StockScoreResult).where(
            and_(
                StockScoreResult.code == '603601',
                StockScoreResult.trade_date == date(2025, 11, 28)
            )
        )
        result = await session.execute(stmt)
        record = result.scalar()
        
        if record:
            print(f"Date: {record.trade_date}")
            print(f"Daily Score: {record.daily_score}")
            print(f"Ranking: {record.ranking}")
            print(f"Rule Scores: {record.rule_scores}")
        else:
            print("No record found for 603601 on 2025-11-28 in StockScoreResult")

        # Check WencaiStock
        print("\n--- WencaiStock ---")
        stmt_w = select(WencaiStock).where(WencaiStock.stock_code == '603601')
        result_w = await session.execute(stmt_w)
        w_record = result_w.first() # fetchone/first
        
        if w_record:
            print(f"Found in WencaiStock: {w_record[0].stock_code} - {w_record[0].stock_name}")
        else:
            print("Not found in WencaiStock")


if __name__ == "__main__":
    asyncio.run(inspect_rule_scores())
