
import asyncio
import sys
import os
import pandas as pd
from datetime import datetime, timedelta, date
from loguru import logger
from sqlalchemy import select, text
import json
from decimal import Decimal

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db_manager
from app.crawler.wencai_crawler import WencaiCrawler
from app.services.wencai_service import WencaiService
from app.services.cookie_service import CookieService
from app.services.rule_engine_service import RuleEngineService
from app.models.stock import StockInfo

class FixedWencaiCrawler(WencaiCrawler):
    """
    Temporary fix for abstract method instantiation error.
    WencaiCrawler inherits from CrawlerBase but doesn't implement crawl().
    """
    async def crawl(self, *args, **kwargs):
        pass

OUTPUT_DIR = "/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/data/wencai_backfill"

# Configure logging
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{message}</level>")
logger.add("backfill_20251121_20260116.log", rotation="10 MB")

async def run_pipeline():
    logger.info("🚀 Starting Acceptance Backfill Pipeline (2025-11-21 to 2026-01-16)...")
    await db_manager.initialize()
    
    # 1. Determine Date Range
    start_date = datetime(2025, 11, 21) 
    end_date = datetime(2026, 1, 16)
    
    logger.info(f"📅 Date Range: {start_date.date()} -> {end_date.date()}")
    
    # 2. Loop
    current = start_date
    while current <= end_date:
        if current.weekday() >= 5: # Skip Sat/Sun
            logger.info(f"⏭️ Skipping weekend: {current.date()}")
            current += timedelta(days=1)
            continue
            
        await process_date(current)
        current += timedelta(days=1)
        
    logger.info("✨ Backfill Pipeline Completed!")

async def process_date(target_date: datetime):
    date_str = target_date.strftime("%Y%m%d")
    query_date_str = target_date.strftime("%Y年%m月%d日")
    
    # Calc Prev Date (Workday)
    prev_date = target_date - timedelta(days=1)
    while prev_date.weekday() >= 5:
        prev_date -= timedelta(days=1)
    prev_date_str = prev_date.strftime("%Y年%m月%d日")
    
    # Query matching user's requirement (2.5x volume, etc.)
    query = f"{query_date_str}成交量是{prev_date_str}成交量的2.5倍以上，非北交，非创业板，非科创版，非ST，概念，行业，{prev_date_str}和{query_date_str}涨幅低于13%，收盘价低于25"
    
    logger.info(f"📥 Processing {date_str}...")
    
    async with db_manager.get_session() as session:
        crawler = FixedWencaiCrawler(session)
        wencai_service = WencaiService(session)
        cookie_service = CookieService(session)
        rule_service = RuleEngineService(db_manager)
        
        # Check cookies
        cookies = await cookie_service.get_cookies("iwencai.com")
        if not cookies:
             cookies = await cookie_service.get_cookies("10jqka.com.cn")
        if not cookies:
            logger.error("❌ No cookies found. Please update cookies.")
            # return # Try to continue, maybe session works
        
        # A. Crawl
        try:
            logger.info(f"🕷️ Crawling query: {query}")
            html = await crawler.fetch_page_source(query)
            if not html:
                logger.error(f"❌ Failed to fetch HTML for {date_str}")
                return

            stocks = wencai_service.parse_html_table(html)
            
            # Handle empty results gracefully
            if not stocks:
                logger.warning(f"⚠️ No stocks found for {date_str}")
                # We still proceed to calculate scores (maybe for other stocks)
            else:
                logger.info(f"✅ Found {len(stocks)} stocks.")
                
                # B. Save CSV
                if not os.path.exists(OUTPUT_DIR):
                    os.makedirs(OUTPUT_DIR)
                
                df = pd.DataFrame(stocks)
                csv_path = os.path.join(OUTPUT_DIR, f"wencai_{date_str}.csv")
                df.to_csv(csv_path, index=False)
                logger.info(f"💾 Saved CSV: {csv_path}")
                
                # C. Ingest to DB
                batch_id = await wencai_service.create_crawl_batch(
                    batch_name=f"Backfill_{date_str}",
                    crawl_url="manual_backfill",
                    query_string=query
                )
                
                success, failed, errors = await wencai_service.save_wencai_stocks(batch_id, stocks)
                await wencai_service.update_batch_status(batch_id, 'completed', len(stocks), success, failed)
                
                # D. Process Batch (Tags & StockInfo)
                # This maps tags (Date Tag + 3x Vol Tag) and updates stock_info
                await wencai_service.process_batch_data(batch_id)
                logger.info(f"🏷️ Batch processed and tags applied for {date_str}")

        except Exception as e:
            logger.error(f"❌ Error crawling/saving {date_str}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
        # E. Calculate Daily Scores (Step 2)
        try:
            logger.info(f"🧮 Calculating Daily Scores for {date_str}...")
            # Use run_in_executor if needed, but calculate_daily_scores is async
            # We convert datetime to date object
            target_date_obj = target_date.date()
            
            # We need to make sure calculate_daily_scores is called correctly
            # It uses db_manager internally
            await rule_service.calculate_daily_scores(target_date_obj, force=True)
            logger.info(f"✅ Daily Scores calculated for {date_str}")
            
        except Exception as e:
            logger.error(f"❌ Error calculating scores for {date_str}: {e}")
            import traceback
            logger.error(traceback.format_exc())

        # Sleep a bit to avoid rate limiting
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(run_pipeline())
