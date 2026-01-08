import asyncio
import os
import sys
from datetime import date, datetime, timedelta
from sqlalchemy import select, delete
import pandas as pd

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db_manager
from app.services.volume_analysis_service import VolumeAnalysisService
from app.services.ranking_service import RankingService
from app.models.stock_daily import StockDaily, StockScoreResult
from app.models.tag_management import StockTagInfo, StockTagRelation

async def verify_603601_full_history():
    stock_code = "603601"
    
    print(f"\n====== Full History Verification for {stock_code} ======")
    
    async with db_manager.get_session() as session:
        # 1. Ensure "Price Double Breakout" tag exists (Critical for high scores)
        print("\n[1] Checking Score Configuration...")
        stmt = select(StockTagInfo).where(StockTagInfo.name == "价格双重突破")
        res = await session.execute(stmt)
        tag = res.scalar_one_or_none()
        if not tag:
            print("⚠️ '价格双重突破' tag missing! Creating it...")
            tag = StockTagInfo(
                name="价格双重突破",
                tag_type="calculation",
                score=50, # Assumption: High score for breakout
            )
            session.add(tag)
            await session.commit()
            print("✅ Created '价格双重突破' with score 50")
        else:
            print(f"✅ '价格双重突破' tag exists with score {tag.score}")

        # 2. Data Backfill (Akshare)
        print("\n[2] Backfilling 1 Year of Data...")
        end_date_str = "20251210"
        start_date_str = "20250101" # Approx 1 year
        
        try:
            import akshare as ak
            print("   Fetching from Akshare...")
            stock_df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date_str, end_date=end_date_str, adjust="qfq")
            
            # Get existing dates to avoid duplicates
            existing_stmt = select(StockDaily.trade_date).where(
                StockDaily.code == stock_code,
                StockDaily.trade_date >= date(2025, 1, 1)
            )
            existing_res = await session.execute(existing_stmt)
            existing_dates = set(existing_res.scalars().all())
            
            new_records = []
            for _, row in stock_df.iterrows():
                d_date = datetime.strptime(str(row['日期']), "%Y-%m-%d").date()
                if d_date in existing_dates:
                    continue
                    
                record = StockDaily(
                    code=stock_code,
                    trade_date=d_date,
                    open=float(row['开盘']),
                    high=float(row['最高']),
                    low=float(row['最低']),
                    close=float(row['收盘']),
                    vol=float(row['成交量']),
                    amount=float(row['成交额'])
                )
                new_records.append(record)
            
            if new_records:
                session.add_all(new_records)
                await session.commit()
                print(f"✅ Inserted {len(new_records)} new records.")
            else:
                print("✅ Data already up to date.")
                
        except Exception as e:
            print(f"❌ Data fetch failed: {e}")
            return

    # 3. Run Full History Analysis
    print("\n[3] Running VolumeAnalysisService.analyze_stock (Full History)...")
    
    # FORCE RECALCULATION: Delete existing scores to bypass "already up to date" check
    async with db_manager.get_session() as session:
        print("   Clearing old score records to force recalculation...")
        del_stmt = delete(StockScoreResult).where(StockScoreResult.code == stock_code)
        await session.execute(del_stmt)
        await session.commit()
        print("   Old scores deleted.")

    try:
        # We need to run this in a loop or ensuring it covers the whole period.
        # VolumeAnalysisService._calculate_stock_internal fetches 400 days and calculates for all of them.
        # So running it once for the latest date (or just generic call) should cover history.
        # But wait, _calculate_stock_internal logic:
        # It iterates `range(1, len(daily_data))` -> lines 349
        # So it recalculates everything!
        
        await VolumeAnalysisService.analyze_stock(stock_code)
        print("✅ Analysis Complete.")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return

    # 4. Check Results
    print("\n[4] Checking Results...")
    async with db_manager.get_session() as session:
        # A. Check Total Score for Ranking
        ranking_service = RankingService(session)
        target_rank_date = date(2025, 12, 5)
        
        # DEBUG: Check ALL score records
        print("\n   [DEBUG] Checking all score records for 603601:")
        all_scores_stmt = select(StockScoreResult).where(StockScoreResult.code == stock_code).order_by(StockScoreResult.trade_date)
        all_scores_res = await session.execute(all_scores_stmt)
        all_scores = all_scores_res.scalars().all()
        print(f"   Found {len(all_scores)} score records.")
        non_zero = [s for s in all_scores if s.total_score > 0]
        print(f"   Found {len(non_zero)} non-zero score records.")
        total_sum = sum([s.total_score for s in non_zero])
        print(f"   Total Score (Sum of all records): {total_sum}")
        
        if non_zero:
            print("   Sample non-zero scores:")
            for s in non_zero[:5]:
                print(f"     {s.trade_date}: {s.total_score} (Rules: {s.rule_scores})")

        # B. Ranking
        rankings = await ranking_service.get_total_score_ranking(target_date=target_rank_date, limit=50)
        my_entry = next((x for x in rankings if x['code'] == stock_code), None)
        
        if my_entry:
            print(f"✅ Rank: {my_entry.get('ranking')} | Score: {my_entry.get('score')}")
        else:
            print("❌ Not in Top 50")
            if rankings:
                print(f"   Top 1 Score: {rankings[0]['score']}")

if __name__ == "__main__":
    asyncio.run(verify_603601_full_history())
