
import asyncio
from sqlalchemy import select
from app.database import db_manager
from app.models.stock_daily import StockScoreResult
import sys
import os
import json

sys.path.append(os.getcwd())

async def check_score_details():
    async with db_manager.get_session() as session:
        print("--- Checking StockScoreResult for 000881 ---")
        # Get the latest score or sum
        stmt = select(StockScoreResult).where(StockScoreResult.code == "000881").order_by(StockScoreResult.trade_date.desc())
        result = await session.execute(stmt)
        scores = result.scalars().all()
        
        total_score = 0
        score_breakdown = {}
        
        print(f"Found {len(scores)} score records.")
        
        for s in scores:
            total_score += float(s.total_score)
            details = s.rule_scores  # This is a dict
            if details:
                for k, v in details.items():
                    score_breakdown[k] = score_breakdown.get(k, 0) + v
        
        print(f"Total Score (Sum of all days): {total_score}")
        print("Score Breakdown by Rule:")
        for k, v in score_breakdown.items():
            print(f"  {k}: {v}")

if __name__ == "__main__":
    asyncio.run(check_score_details())
