
import asyncio
import os
import sys
import logging
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import select
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import DatabaseManager
from app.config.settings import get_settings
from app.services.wencai_service import WencaiService
from app.services.stock_sync_service import StockSyncService
from app.services.rule_engine_service import RuleEngineService
from app.models.crawler import CrawlerTarget
from app.crawler.wencai_crawler import WencaiCrawler

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

OUTPUT_DIR = "/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/data/wencai"

async def main():
    # 1. Initialize Database
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    # 2. Initialize Services
    wencai_service = WencaiService(db_manager)
    stock_sync_service = StockSyncService(db_manager)
    rule_engine_service = RuleEngineService(db_manager)
    
    # 3. Define Missing Dates
    missing_dates = [
        "2026-01-13"
    ]
    
    logger.info(f"Starting backfill for dates: {missing_dates}")
    
    # 4. Get Crawler Target (assuming ID 1 or the first active one with 'wencai' platform)
    async with db_manager.get_session() as session:
        stmt = select(CrawlerTarget).where(CrawlerTarget.platform == 'wencai', CrawlerTarget.is_active == True).limit(1)
        result = await session.execute(stmt)
        target = result.scalar_one_or_none()
        
        if not target:
            logger.error("No enabled wencai crawler target found!")
            return
        
        target_query = target.url
        logger.info(f"Using Crawler Target ID {target.id}: {target_query}")

    for date_str in missing_dates:
        logger.info(f"=== Processing {date_str} ===")
        
        try:
            current_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            prev_date = current_date - timedelta(days=1)
            # Find previous trading day (simple logic, assuming missing_dates are valid trading days)
            # Better logic: if prev_date is weekend, go back
            while prev_date.weekday() >= 5:
                prev_date -= timedelta(days=1)
            
            prev_date_str = prev_date.strftime("%Y%m%d")
            query_date_str = current_date.strftime("%Y%m%d")
            
            # Dynamic Parameter Replacement
            final_query = target_query.replace("{query_date}", query_date_str).replace("{prev_date_str}", prev_date_str)
            logger.info(f"Query: {final_query}")
            
            # A. Run Crawler
            logger.info("Running Wencai Crawler...")
            async with db_manager.get_session() as session:
                crawler = WencaiCrawler(session)
                crawl_result = await crawler.fetch_and_parse(
                    query=final_query,
                    target_date=current_date
                )
            
            batch_id = crawl_result.get("batch_id")
            count = crawl_result.get("count", 0)
            stocks = crawl_result.get("stocks", [])
            
            if batch_id:
                logger.info(f"✅ Crawl success. Batch ID: {batch_id}, Stocks found: {count}")
                
                # B. Save to CSV
                if stocks:
                    try:
                        if not os.path.exists(OUTPUT_DIR):
                            os.makedirs(OUTPUT_DIR)
                        
                        df = pd.DataFrame(stocks)
                        output_path = os.path.join(OUTPUT_DIR, f"wencai_{query_date_str}.csv")
                        df.to_csv(output_path, index=False, encoding='utf-8-sig')
                        logger.info(f"✅ Saved wencai data to {output_path}")
                    except Exception as e:
                        logger.error(f"❌ Failed to save CSV: {e}")
                else:
                     logger.warning("No stocks data returned to save CSV.")

                # C. Sync Stock Data (Tushare/Akshare)
                logger.info("Syncing Stock Data (History & CSV)...")
                # We want to sync up to current_date
                # sync_tushare_increment uses batch_id to find stocks.
                # It syncs from start_date_str. We should probably specify it to ensure coverage.
                # Or let it default. If default is settings based, it might be too old or too new.
                # Let's specify start_date_str as current_date to ensure we get at least that day, 
                # but maybe we need history if it's a new stock.
                # Let's set start_date_str to "2025-12-10" to be safe for this backfill period, 
                # or just the specific date if we trust history is there.
                # Given the prompt says "ensure stock pool data includes ... up to today", 
                # and "补全tushare+akshare补全csv历史数据", safer to go back a bit or just rely on the service to fetch missing.
                # sync_tushare_single fetches range.
                
                # Let's try to sync from the missing date.
                sync_result = await stock_sync_service.sync_tushare_increment(
                    batch_id=batch_id,
                    start_date_str=date_str 
                )
                logger.info(f"Sync Result: {sync_result}")
                
                # Verify CSV for a sample stock if any
                if stocks:
                    sample_code = stocks[0].get('code')
                    if sample_code:
                        csv_path = stock_sync_service._find_csv_path(sample_code)
                        if csv_path and os.path.exists(csv_path):
                            logger.info(f"✅ Verified CSV exists for {sample_code}: {csv_path}")
                            # Optionally check last line date
                            try:
                                df_check = pd.read_csv(csv_path)
                                last_date = df_check['trade_date'].max()
                                logger.info(f"   Last date in CSV: {last_date}")
                            except:
                                pass
                        else:
                            logger.warning(f"❌ CSV not found for {sample_code} at expected path")

                # D. Calculate Basic Scores
                logger.info("Calculating Basic Scores...")
                score_result = await rule_engine_service.calculate_daily_scores(
                    target_date=current_date,
                    force=True
                )
                logger.info(f"Score Result: {score_result}")
                
            else:
                logger.error(f"❌ Crawl failed or no batch ID: {crawl_result}")
        
        except Exception as e:
            logger.error(f"❌ Error processing {date_str}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
