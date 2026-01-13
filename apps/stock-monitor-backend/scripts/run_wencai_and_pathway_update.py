
import asyncio
import sys
import os
from datetime import datetime, timedelta, date
from typing import List, Set

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import db_manager
from app.crawler.wencai_crawler import WencaiCrawler
from app.services.wencai_service import WencaiService
from app.services.pathway_engine import PathwayVolumePriceEngine
from app.services.stock_sync_service import StockSyncService
from app.models.stock import StockInfo
from loguru import logger
from sqlalchemy import select

# Configure logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")

START_DATE_STR = "2025-12-11"
END_DATE_STR = "2026-01-12"

async def get_trading_dates(start_str: str, end_str: str) -> List[date]:
    """Simple trading date generator (skips weekends)"""
    s = datetime.strptime(start_str, "%Y-%m-%d").date()
    e = datetime.strptime(end_str, "%Y-%m-%d").date()
    dates = []
    curr = s
    while curr <= e:
        if curr.weekday() < 5: # Mon-Fri
            dates.append(curr)
        curr += timedelta(days=1)
    return dates

async def crawl_wencai_daily(session, target_date: date):
    """Crawl wencai for a specific date"""
    date_str = target_date.strftime("%Y年%m月%d日")
    
    # Calculate prev trading day (simple logic)
    prev_date = target_date - timedelta(days=1)
    while prev_date.weekday() >= 5:
        prev_date -= timedelta(days=1)
    prev_date_str = prev_date.strftime("%Y年%m月%d日")
    
    query = (
        f"{date_str}成交量是{prev_date_str}成交量的2.5倍以上，"
        f"非北交 非创业版，非科创版，非ST，概念 行业，"
        f"{prev_date_str}和{date_str}涨幅低于13% 收盘价低于25"
    )
    
    logger.info(f"🕷️ Crawling {target_date} with query: {query}")
    
    crawler = WencaiCrawler(session)
    # batch_name is important for tracking
    batch_name = f"CatchUp_{target_date.strftime('%Y%m%d')}"
    
    result = await crawler.fetch_and_parse(query, batch_name=batch_name)
    
    if result.get('status') == 'completed':
        count = result.get('total', 0)
        logger.info(f"✅ Crawled {count} stocks for {target_date}")
        
        # Return list of stock codes found
        stocks = result.get('stocks', []) # This might be None depending on implementation
        # Wait, fetch_and_parse in wencai_crawler.py returns a dict summary, 
        # but does it return the stock list?
        # Looking at wencai_crawler.py code snippet earlier: 
        # It calls wencai_service.save_wencai_stocks but might not return them in the dict.
        # Let's assume we need to query them or WencaiService saves them to DB.
        # We can query wencai_stocks table for this batch or date.
        return stocks
    else:
        logger.error(f"❌ Crawl failed for {target_date}: {result.get('message')}")
        return []

async def main():
    logger.info("🚀 Starting Wencai Catch-up & Pathway Calculation...")
    
    await db_manager.initialize()
    
    dates = await get_trading_dates(START_DATE_STR, END_DATE_STR)
    logger.info(f"📅 Target dates: {[d.strftime('%Y-%m-%d') for d in dates]}")
    
    affected_stocks: Set[str] = set()
    
    # 1. Crawl Loop
    for d in dates:
        async with db_manager.get_session() as session:
            stocks = await crawl_wencai_daily(session, d)
            
            # If stocks list is empty from return, we might need to query DB
            # But let's check if we can get them. 
            # If not, we can query `wencai_stocks` table for `query_date == d`.
            
            # For now, let's also just accumulate all active stocks or query DB after crawl
            # Query DB for stocks crawled on this date
            from app.models.crawler import WencaiStock
            stmt = select(WencaiStock.stock_code).where(WencaiStock.query_date == d)
            result = await session.execute(stmt)
            codes = result.scalars().all()
            
            for code in codes:
                affected_stocks.add(code)
                
            await session.commit()
            
        # Sleep to avoid rate limits
        await asyncio.sleep(2)

    logger.info(f"📊 Total affected stocks: {len(affected_stocks)}")
    
    if not affected_stocks:
        logger.warning("⚠️ No stocks found in the period. Exiting.")
        return

    # 2. Pathway Calculation
    logger.info("🧮 Starting Pathway Engine Calculation...")
    
    async with db_manager.get_session() as session:
        engine = PathwayVolumePriceEngine(session)
        
        total = len(affected_stocks)
        count = 0
        
        for code in affected_stocks:
            count += 1
            if count % 10 == 0:
                logger.info(f"Processing {count}/{total} stocks...")
                
            # Run batch calculation for the catch-up period
            # We assume history before 2025-12-11 exists.
            # We calculate from START_DATE to END_DATE.
            # Note: start_date should be date object
            s_date = datetime.strptime(START_DATE_STR, "%Y-%m-%d").date()
            e_date = datetime.strptime(END_DATE_STR, "%Y-%m-%d").date()
            
            await engine.batch_calculate_scores(code, s_date, e_date)
            
        await session.commit()
        
    logger.info("✅ All done!")

if __name__ == "__main__":
    asyncio.run(main())
