
import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db_manager
from app.crawler.wencai_crawler import WencaiCrawler
from app.services.pattern_analysis_service import PatternAnalysisService
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_wencai_flow():
    """
    Test the full flow of Wencai Crawler -> Database -> Pattern Analysis
    """
    logger.info("Initializing Database...")
    await db_manager.initialize()
    # Ensure tables are created
    await db_manager.create_tables()
    
    async with db_manager.get_session() as session:
        crawler = WencaiCrawler(session)
        pattern_service = PatternAnalysisService(session)
        
        # 1. Define a test query
        # Use a simple query that is likely to return results but not too many
        query = "成交量大于500万，非ST，非科创板，涨幅小于5%"
        logger.info(f"Running Wencai Crawler with query: {query}")
        
        # 2. Run Crawler
        result = await crawler.fetch_and_parse(query, batch_name="Test_Flow_Batch")
        
        if result.get("status") != "completed":
            logger.error(f"Crawler failed: {result}")
            return
            
        logger.info(f"Crawler success! Fetched {result.get('success')} records.")
        batch_id = result.get("batch_id")
        
        # 3. Verify WencaiStocks
        logger.info("Verifying wencai_stocks table...")
        stmt = text("SELECT count(*) FROM wencai_stocks WHERE crawl_batch_id = :batch_id")
        count_res = await session.execute(stmt, {"batch_id": batch_id})
        count = count_res.scalar()
        logger.info(f"Found {count} records in wencai_stocks for batch {batch_id}")
        
        if count == 0:
            logger.error("No records found in wencai_stocks!")
            return

        # 4. Verify StockDailyTemp (should be auto-synced)
        logger.info("Verifying stock_daily_temp table (should be auto-synced)...")
        # We check for data created today
        stmt = text("""
            SELECT count(*) FROM stock_daily_temp 
            WHERE source = 'wencai_crawl' 
            AND created_at >= CURDATE()
        """)
        temp_count_res = await session.execute(stmt)
        temp_count = temp_count_res.scalar()
        logger.info(f"Found {temp_count} records in stock_daily_temp created today")
        
        if temp_count == 0:
             logger.warning("No records in stock_daily_temp! Sync might have failed or condition not met.")
        
        # 5. Verify Cookie Sync
        logger.info("Verifying Cookie Sync...")
        stmt = text("SELECT count(*) FROM chrome_cookies WHERE domain LIKE '%iwencai%'")
        cookie_res = await session.execute(stmt)
        cookie_count = cookie_res.scalar()
        logger.info(f"Found {cookie_count} cookies for iwencai in database.")
        
        # 6. Test Pattern Screening (Optional)
        logger.info("Running Pattern Screening on Temp Data...")
        screen_result = await pattern_service.perform_screening()
        logger.info(f"Screening Result: {screen_result}")
        
    logger.info("Test Flow Completed.")

if __name__ == "__main__":
    try:
        asyncio.run(test_wencai_flow())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
