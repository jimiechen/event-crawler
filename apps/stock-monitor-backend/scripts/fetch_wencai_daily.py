
import asyncio
import sys
import os
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import db_manager
from app.crawler.wencai_crawler import WencaiCrawler
from app.services.cookie_service import CookieService

# Configure logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{message}</level>")

OUTPUT_DIR = "/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/data/wencai"

async def fetch_daily_wencai():
    """
    Fetch Wencai data for the period 2025-11-20 to 2025-12-10.
    Save daily results to CSV.
    Check for 603601.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    start_date = datetime(2025, 11, 20)
    end_date = datetime(2025, 12, 10)
    
    target_code = "603601"
    
    logger.info(f"Starting Wencai fetch from {start_date.date()} to {end_date.date()}")
    
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        crawler = WencaiCrawler(session)
        cookie_service = CookieService(session)
        
        # Check cookies first
        cookies = await cookie_service.get_cookies("iwencai.com")
        if not cookies:
             cookies = await cookie_service.get_cookies("10jqka.com.cn")
             
        if not cookies:
            logger.error("❌ No cookies found for iwencai.com or 10jqka.com.cn. Please update cookies in database.")
            logger.info("Tip: You can use the Chrome Extension or manually insert cookies into 'cookies' table.")
            return

        current_date = start_date
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() >= 5:
                logger.info(f"Skipping weekend: {current_date.date()}")
                current_date += timedelta(days=1)
                continue
                
            date_str = current_date.strftime("%Y%m%d")
            query_date_str = current_date.strftime("%Y年%m月%d日")
            
            # Calculate prev date for query logic (T-1)
            prev_date = current_date - timedelta(days=1)
            while prev_date.weekday() >= 5:
                prev_date -= timedelta(days=1)
            prev_date_str = prev_date.strftime("%Y年%m月%d日")
            
            # Query construction
            # "2025年11月20日成交量是2025年11月19日成交量的2.5倍以上，..."
            query = f"{query_date_str}成交量是{prev_date_str}成交量的2.5倍以上，非北交，非创业板，非科创版，非ST，概念，行业，{prev_date_str}和{query_date_str}涨幅低于13%，收盘价低于25"
            
            logger.info(f"Fetching for {date_str}...")
            logger.info(f"Query: {query}")
            
            try:
                # Use a unique batch name
                batch_name = f"FETCH_{date_str}"
                
                # Fetch
                result = await crawler.fetch_and_parse(query=query, batch_name=batch_name)
                
                if result.get('status') == 'error':
                     logger.error(f"❌ Fetch failed for {date_str}: {result.get('message')}")
                     # If login failed, it might return error or empty.
                     # WencaiCrawler usually logs errors.
                
                stocks = result.get('stocks', [])
                logger.info(f"Found {len(stocks)} stocks for {date_str}")
                
                if stocks:
                    # Convert to DataFrame
                    df = pd.DataFrame(stocks)
                    
                    # Ensure columns exist
                    cols = ['stock_code', 'stock_name']
                    # Add other columns if available
                    for k in stocks[0].keys():
                        if k not in cols:
                            cols.append(k)
                            
                    df = df[cols]
                    
                    # Save to CSV
                    csv_path = os.path.join(OUTPUT_DIR, f"wencai_{date_str}.csv")
                    df.to_csv(csv_path, index=False)
                    logger.info(f"✅ Saved to {csv_path}")
                    
                    # Check for 603601
                    # Handle full code (603601.SH) or short code (603601)
                    found_target = False
                    for s in stocks:
                        c = s.get('stock_code', '')
                        if target_code in c:
                            found_target = True
                            logger.success(f"🎯 FOUND {target_code} in {date_str} results!")
                            break
                    
                    if not found_target:
                        logger.warning(f"Target {target_code} NOT found in {date_str} results.")
                        
                else:
                    logger.warning(f"No stocks found for {date_str}")
                    
            except Exception as e:
                logger.error(f"❌ Exception fetching {date_str}: {e}")
                import traceback
                traceback.print_exc()
            
            # Sleep to avoid rate limiting
            await asyncio.sleep(5)
            current_date += timedelta(days=1)

if __name__ == "__main__":
    asyncio.run(fetch_daily_wencai())
