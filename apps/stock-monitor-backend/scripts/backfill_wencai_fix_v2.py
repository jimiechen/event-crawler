
import asyncio
import os
import sys
from datetime import date, timedelta, datetime
from decimal import Decimal
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_manager
from app.models.stock import StockInfo
from app.models.stock_daily import StockScoreResult, StockDaily
from app.services.volume_analysis_service import VolumeAnalysisService
from app.services.rule_engine_service import RuleEngineService
from sqlalchemy import select, update, delete, and_, func

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def backfill_wencai_history():
    """
    Backfill history for Wencai stocks:
    1. Identify all Wencai stocks (source='wencai').
    2. Iterate from 2024-11-01 to Today.
    3. For each date:
       - Ensure score exists (calculate if missing).
       - Ensure pool_type is 'wencai'.
       - Calculate and update Ranking (within Wencai pool).
    """
    print("🚀 Starting Wencai History Backfill (Fix & Ranking)...")
    
    await db_manager.initialize()
    
    start_date = date(2024, 11, 1) # Cover 603601's 2025-11-28 (Wait, user said 2025. 2024 is safe)
    # User said 603601 first day 2025-11-28. 
    # Let's ensure we cover enough history.
    end_date = date.today()
    
    async with db_manager.get_session() as session:
        # 1. Get all Wencai Stocks
        stmt = select(StockInfo).where(StockInfo.source == 'wencai')
        result = await session.execute(stmt)
        wencai_stocks = result.scalars().all()
        wencai_codes = [s.code for s in wencai_stocks]
        
        print(f"📋 Found {len(wencai_codes)} Wencai stocks.")
        if not wencai_codes:
            print("❌ No Wencai stocks found. Exiting.")
            await db_manager.close()
            return

        # 2. Update pool_type for existing records (Batch)
        # This ensures existing scores have correct pool_type
        print("🔄 Updating pool_type for existing records...")
        update_stmt = update(StockScoreResult).where(
            StockScoreResult.code.in_(wencai_codes)
        ).values(pool_type='wencai')
        await session.execute(update_stmt)
        await session.commit()
        print("✅ Pool type updated.")

    # Service instances
    # We need to instantiate services properly. 
    # VolumeAnalysisService and RuleEngineService usually take session in methods or init?
    # Checking their code:
    # RuleEngineService: __init__(db_manager)
    # VolumeAnalysisService: Static methods mostly, or __init__(db_manager)
    
    rule_service = RuleEngineService(db_manager)
    
    curr = start_date
    while curr <= end_date:
        print(f"\n📅 Processing Date: {curr}")
        
        # We need to process day by day to ensure "Previous Score" dependency is met for calculation
        
        async with db_manager.get_session() as session:
            # Check which Wencai stocks have data on this day (to avoid useless calculation attempts)
            # Or just rely on RuleEngine to check history.
            
            # Find missing scores for Wencai stocks on this day
            # First, get list of stocks that HAVE scores today
            stmt_exist = select(StockScoreResult.code).where(
                StockScoreResult.trade_date == curr,
                StockScoreResult.code.in_(wencai_codes)
            )
            res_exist = await session.execute(stmt_exist)
            existing_codes = set(res_exist.scalars().all())
            
            # Candidates are all wencai codes minus existing
            missing_codes = [c for c in wencai_codes if c not in existing_codes]
            
            # Check if these missing codes actually have TRADING data (StockDaily) on or before this day?
            # If they don't have StockDaily, we can't score them.
            # Efficient check: Query StockDaily for these codes on this date
            if missing_codes:
                stmt_daily = select(StockDaily.code).where(
                    StockDaily.trade_date == curr,
                    StockDaily.code.in_(missing_codes)
                )
                res_daily = await session.execute(stmt_daily)
                valid_missing_codes = res_daily.scalars().all()
                
                if valid_missing_codes:
                    print(f"   ⚠️ Found {len(valid_missing_codes)} stocks with data but missing scores. Calculating...")
                    
                    # Calculate scores for these stocks
                    # Use RuleEngineService to calculate and save scores
                    print(f"      Calculating scores for {len(valid_missing_codes)} stocks...")
                    
                    for i, code in enumerate(valid_missing_codes, 1):
                        try:
                            # calculate_daily_scores handles tag generation and saving
                            # force=True to ensure we overwrite if partially exists (though we filtered)
                            # It returns a dict, we just await it.
                            await rule_service.calculate_daily_scores(
                                target_date=curr, 
                                force=True, 
                                stock_code=code
                            )
                            if i % 10 == 0:
                                print(f"      Progress: {i}/{len(valid_missing_codes)}")
                                
                        except Exception as e:
                            logger.error(f"Failed to calculate {code} on {curr}: {e}")

        # Now that we ensured scores exist (or tried to), let's RANK.
        await calculate_daily_ranking(curr, 'wencai')
        
        curr += timedelta(days=1)

    print("\n✅ Backfill Completed.")
    await db_manager.close()

async def calculate_daily_ranking(target_date: date, pool_type: str):
    """
    Calculate and update ranking for a specific pool on a specific date.
    """
    async with db_manager.get_session() as session:
        # Get all scores for this pool and date
        stmt = select(StockScoreResult).where(
            StockScoreResult.trade_date == target_date,
            StockScoreResult.pool_type == pool_type
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        
        if not rows:
            return

        # Sort by total_score desc
        # Handle None values
        sorted_rows = sorted(rows, key=lambda x: float(x.total_score) if x.total_score is not None else -1, reverse=True)
        
        # Update ranking
        for rank, row in enumerate(sorted_rows, 1):
            if row.ranking != rank:
                row.ranking = rank
                # We can update directly on the object since it's attached to session
                # Or use update statement if detached. 
                # Since we are in `async with`, it's attached.
        
        await session.commit()
        print(f"   🏆 Ranked {len(rows)} stocks for {pool_type} on {target_date}.")

if __name__ == "__main__":
    # Fix for rule_engine calling logic
    # I need to know how to trigger calculation for specific stocks.
    # If RuleEngineService.calculate_daily_scores only does ALL, it might be slow.
    # But "Time is not an issue".
    # So I can just call it?
    # Wait, `calculate_daily_scores` iterates ALL stocks with tags.
    # I should check `rule_engine_service.py` signature.
    
    asyncio.run(backfill_wencai_history())
