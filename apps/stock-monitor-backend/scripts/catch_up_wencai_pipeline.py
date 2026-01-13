import asyncio
import sys
import os
import pandas as pd
from datetime import datetime, timedelta, date
from loguru import logger
from sqlalchemy import select, text

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db_manager
from app.crawler.wencai_crawler import WencaiCrawler
from app.services.wencai_service import WencaiService
from app.services.cookie_service import CookieService
from app.services.rule_engine_service import RuleEngineService
from app.services.pathway_engine import PathwayVolumePriceEngine
from app.models.stock import StockInfo

class FixedWencaiCrawler(WencaiCrawler):
    """
    Temporary fix for abstract method instantiation error.
    WencaiCrawler inherits from CrawlerBase but doesn't implement crawl().
    """
    async def crawl(self, *args, **kwargs):
        pass

OUTPUT_DIR = "/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/data/wencai"

# Configure logging
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{message}</level>")
logger.add("pipeline.log", rotation="10 MB")

async def run_pipeline():
    logger.info("🚀 Starting Catch-up Pipeline...")
    await db_manager.initialize()
    
    # 1. Determine Date Range
    # User said "already crawled up to 20251211", so start from 20251212
    start_date = datetime(2025, 12, 12) 
    end_date = datetime.now()
    
    logger.info(f"📅 Date Range: {start_date.date()} -> {end_date.date()}")
    
    # 2. Crawl & Save & Ingest
    current = start_date
    while current <= end_date:
        if current.weekday() >= 5: # Skip Sat/Sun
            logger.info(f"⏭️ Skipping weekend: {current.date()}")
            current += timedelta(days=1)
            continue
            
        await process_date(current)
        current += timedelta(days=1)
        
    # 3. Pathway Engine Calculation (250 days)
    logger.info("🧠 Starting Pathway Engine Calculation (250 days)...")
    await run_pathway_calculation(days=250)
    
    # 4. End-to-End Verification
    await verify_results()
    logger.info("✨ Pipeline Completed!")

async def process_date(target_date: datetime):
    date_str = target_date.strftime("%Y%m%d")
    query_date_str = target_date.strftime("%Y年%m月%d日")
    
    # Calc Prev Date (Workday)
    prev_date = target_date - timedelta(days=1)
    while prev_date.weekday() >= 5:
        prev_date -= timedelta(days=1)
    prev_date_str = prev_date.strftime("%Y年%m月%d日")
    
    query = f"{query_date_str}成交量是{prev_date_str}成交量的2.5倍以上，非北交，非创业板，非科创版，非ST，概念，行业，{prev_date_str}和{query_date_str}涨幅低于13%，收盘价低于25"
    
    logger.info(f"📥 Processing {date_str}...")
    
    async with db_manager.get_session() as session:
        crawler = FixedWencaiCrawler(session)
        wencai_service = WencaiService(session)
        cookie_service = CookieService(session)
        
        # Check cookies
        cookies = await cookie_service.get_cookies("iwencai.com")
        if not cookies:
             cookies = await cookie_service.get_cookies("10jqka.com.cn")
        if not cookies:
            logger.error("❌ No cookies found. Please update cookies.")
            # return # Don't return, try anyway? No, crawler needs cookies.
            # Actually FixedWencaiCrawler uses Playwright which might need cookies.
            # But let's let it try, maybe default session works?
            # Or log error and skip
            return

        # A. Crawl
        # We use fetch_page_source + parse_html_table manually to control flow
        try:
            html = await crawler.fetch_page_source(query)
            if not html:
                logger.error(f"❌ Failed to fetch HTML for {date_str}")
                return

            stocks = wencai_service.parse_html_table(html)
            if not stocks:
                logger.warning(f"⚠️ No stocks found for {date_str}")
                # We still continue to ensure we don't block pipeline, but maybe mark as empty
                return
                
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
                batch_name=f"CatchUp_{date_str}",
                crawl_url="manual_script",
                query_string=query
            )
            
            success, failed, errors = await wencai_service.save_wencai_stocks(batch_id, stocks)
            await wencai_service.update_batch_status(batch_id, 'completed', len(stocks), success, failed)
            
            # D. Process Batch (Tags)
            # This maps tags and updates stock_info
            await wencai_service.process_batch_data(batch_id)
            
        except Exception as e:
            logger.error(f"❌ Error processing {date_str}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
        # Sleep a bit to avoid rate limiting
        await asyncio.sleep(5)

async def run_pathway_calculation(days=250):
    async with db_manager.get_session() as session:
        # Get all active stocks
        result = await session.execute(select(StockInfo.code))
        codes = result.scalars().all()
        
        logger.info(f"📊 Calculating Pathway scores for {len(codes)} stocks...")
        
        engine = PathwayVolumePriceEngine(session)
        
        # Define range
        end_d = date.today()
        start_d = end_d - timedelta(days=days)
        
        chunk_size = 20
        total_processed = 0
        
        for i in range(0, len(codes), chunk_size):
            chunk = codes[i:i+chunk_size]
            tasks = []
            
            for code in chunk:
                # We can run these in parallel
                tasks.append(engine.batch_calculate_scores(code, start_d, end_d))
                
            # Run chunk
            await asyncio.gather(*tasks)
            # await session.commit() # batch_calculate_scores might not commit, so we should commit here if needed
            # But PathwayVolumePriceEngine.batch_calculate_scores calls process_new_data which calls _save_score_result
            # Let's see if _save_score_result commits.
            # If not, we should commit.
            # Assuming we need to commit.
            await session.commit()
            
            total_processed += len(chunk)
            if total_processed % 100 == 0:
                logger.info(f"Processed {total_processed}/{len(codes)} stocks")

async def verify_results():
    logger.info("🔍 Verifying results...")
    # Check if CSV exists for today (if weekday)
    today = datetime.now()
    if today.weekday() < 5:
        date_str = today.strftime("%Y%m%d")
        csv_path = os.path.join(OUTPUT_DIR, f"wencai_{date_str}.csv")
        if os.path.exists(csv_path):
            logger.info(f"✅ CSV for today ({date_str}) exists.")
        else:
            logger.warning(f"⚠️ CSV for today ({date_str}) missing (could be empty result).")
            
    # Check DB
    async with db_manager.get_session() as session:
        # Check StockInfo score
        stmt = select(StockInfo).where(StockInfo.volume_anomaly_score != 0).limit(5)
        res = await session.execute(stmt)
        stocks = res.scalars().all()
        if stocks:
            logger.info(f"✅ Found {len(stocks)} stocks with calculated scores.")
            for s in stocks:
                logger.info(f"   - {s.code}: {s.volume_anomaly_score}")
        else:
            logger.warning("⚠️ No stocks found with calculated scores (volume_anomaly_score != 0).")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
