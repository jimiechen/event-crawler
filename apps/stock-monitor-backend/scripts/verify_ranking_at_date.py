import asyncio
import sys
import os
from datetime import date, timedelta
from sqlalchemy import select, func, and_, desc

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_manager
from app.models.stock_daily import StockScoreResult
from app.services.ranking_service import RankingService
from app.models.stock import StockInfo

async def verify_ranking():
    target_date = date(2025, 12, 5)
    start_date = target_date - timedelta(days=250)
    
    print(f"=== Verifying Ranking for Date: {target_date} ===")
    print(f"Window: {start_date} to {target_date}")
    
    async with db_manager.get_session() as session:
        ranking_service = RankingService(session)
        
        # 1. Get Official Ranking
        top_stocks = await ranking_service.get_total_score_ranking(target_date, limit=20)
        
        print("\n--- Top 5 Official Ranking ---")
        for i, stock in enumerate(top_stocks[:5], 1):
            print(f"Rank {i}: {stock['code']} - {stock['name']} : {stock['score']}")
            
        # 2. Check 603601 specifically
        # We manually calculate to verify the service logic
        stmt = select(func.sum(StockScoreResult.total_score))\
            .where(
                and_(
                    StockScoreResult.code == "603601",
                    StockScoreResult.trade_date <= target_date,
                    StockScoreResult.trade_date > start_date
                )
            )
        score_603601 = await session.scalar(stmt) or 0.0
        
        print(f"\n--- 603601 Score Verification ---")
        print(f"Manual Sum (Window {start_date}~{target_date}): {score_603601}")
        
        # Check if it appears in the top list
        found_rank = None
        for i, stock in enumerate(top_stocks, 1):
            if stock['code'] == "603601":
                found_rank = i
                break
        
        if found_rank:
            print(f"603601 Rank in Top 20: #{found_rank}")
        else:
            print(f"603601 NOT in Top 20 (Score: {score_603601})")
            if top_stocks:
                print(f"Lowest Top 20 Score: {top_stocks[-1]['score']}")
            
        # 3. Check for "Future Data" Leakage
        # See if 603601 has scores AFTER 2025-12-05
        stmt_future = select(func.count(), func.sum(StockScoreResult.total_score))\
            .where(
                and_(
                    StockScoreResult.code == "603601",
                    StockScoreResult.trade_date > target_date
                )
            )
        future_result = await session.execute(stmt_future)
        future_count, future_sum = future_result.one()
        
        print(f"\n--- Future Data Check (After {target_date}) ---")
        print(f"Records found: {future_count}")
        print(f"Sum of future scores: {future_sum or 0}")
        
        if future_sum and (score_603601 + float(future_sum or 0) > score_603601):
             print(f"CRITICAL: If future data were included, score would be: {score_603601 + float(future_sum)}")

if __name__ == "__main__":
    asyncio.run(verify_ranking())
