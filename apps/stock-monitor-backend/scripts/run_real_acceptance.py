import asyncio
import logging
import sys
import os
import json
from datetime import datetime, timedelta, date
from decimal import Decimal
import pandas as pd
from sqlalchemy import select, desc, text
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure app is in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Import reset_db
try:
    from reset_db import reset_db
except ImportError:
    # If running from different context, try relative import or assume it's available
    try:
        from scripts.reset_db import reset_db
    except ImportError:
        pass

from app.database import db_manager
from app.services.pattern_analysis_service import PatternAnalysisService
from app.services.stock_sync_service import StockSyncService
from app.crawler.wencai_crawler import WencaiCrawler
from app.services.wencai_service import WencaiService
from app.services.tag_management_service import TagManagementService
from app.api.tag_schemas import TagCreate
from app.models.pattern_config import PatternStockPool
from app.models.stock import WencaiStock
from app.config.settings import get_settings

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("real_acceptance.log")
    ]
)
logger = logging.getLogger(__name__)

async def get_trading_days(start_date_str: str, end_date_str: str):
    dates = []
    start = datetime.strptime(start_date_str, "%Y-%m-%d")
    end = datetime.strptime(end_date_str, "%Y-%m-%d")
    current = start
    while current <= end:
        if current.weekday() < 5: # Mon-Fri
            dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return dates

async def run_daily_process(date_str: str, stock_sync_service: StockSyncService):
    logger.info(f"=== Starting Real Process for {date_str} ===")
    
    async with db_manager.get_session() as session:
        # Initialize Services
        crawler = WencaiCrawler(session)
        wencai_service = WencaiService(session)
        pattern_service = PatternAnalysisService(session, stock_sync_service)
        tag_service = TagManagementService(session)
        
        # 1. Real Wencai Crawl
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        # Calculate prev_date (T-1)
        prev_date_obj = date_obj - timedelta(days=1)
        while prev_date_obj.weekday() >= 5: # Skip weekends
             prev_date_obj -= timedelta(days=1)
        
        query_date = date_obj.strftime("%Y年%m月%d日")
        prev_date_str = prev_date_obj.strftime("%Y年%m月%d日")
        
        # Query: {T}成交量是{T-1}成交量的2.5倍以上...
        query = f"{query_date}成交量是{prev_date_str}成交量的2.9倍以上，非北交，非创业板，非科创版，非ST，概念，行业，{prev_date_str}和{query_date}涨幅低于13%，收盘价低于25"
        
        batch_name = f"Real_{date_str.replace('-', '')}"
        logger.info(f"[{date_str}] Crawling Wencai with query: {query}")
        
        crawl_result = await crawler.fetch_and_parse(query, batch_name=batch_name)
        
        if crawl_result.get("status") != "completed" and crawl_result.get("success", 0) == 0:
             logger.warning(f"No stocks found for {date_str}")
             return {
                 "processed": 0,
                 "passed": 0,
                 "failed": 0,
                 "errors": ["No stocks found"],
                 "stats_603601": None
             }

        batch_id = crawl_result.get("batch_id")
        if not batch_id:
             batch = await wencai_service.get_batch_by_name(batch_name)
             if not batch:
                 logger.error(f"[{date_str}] Batch {batch_name} not found.")
                 return None
             batch_id = batch.id

        logger.info(f"[{date_str}] Batch ID: {batch_id}")
        
        # 2. Sync to Temp
        stocks = await wencai_service.get_stocks_by_batch(batch_id)
        logger.info(f"[{date_str}] Found {len(stocks)} stocks in batch.")
        
        temp_data = []
        for s in stocks:
            # Enforce Filtering: No BSE (8xx, 4xx, 92xx), No ChiNext (30xx), No STAR (688xx), No ST
            # Handle both object and dict access for compatibility
            if isinstance(s, dict):
                code = s.get('stock_code')
                name = s.get('stock_name')
                current_price = s.get('current_price')
                volume = s.get('volume')
                industry = s.get('industry')
                concept = s.get('concept')
            else:
                code = s.stock_code
                name = s.stock_name
                current_price = s.current_price
                volume = s.volume
                industry = s.industry
                concept = s.concept
            
            if not code:
                continue

            if code.startswith(('8', '4', '92')): # BSE
                logger.info(f"Skipping BSE stock: {code} {name}")
                continue
            if code.startswith('30'): # ChiNext
                logger.info(f"Skipping ChiNext stock: {code} {name}")
                continue
            if code.startswith('688'): # STAR
                logger.info(f"Skipping STAR stock: {code} {name}")
                continue
            if 'ST' in name or 'st' in name:
                logger.info(f"Skipping ST stock: {code} {name}")
                continue

            temp_data.append({
                "code": code,
                "trade_date": date_obj,
                "open": current_price,
                "close": current_price,
                "high": current_price,
                "low": current_price,
                "volume": volume,
                "amount": 0,
                "industry": industry,
                "concept": concept
            })
            
        await pattern_service.save_temp_data(temp_data)
        logger.info(f"[{date_str}] Saved {len(temp_data)} to Temp Pool.")
        
        # 3. Screening
        # Pass date_obj.date() to perform_screening
        screening_stats = await pattern_service.perform_screening(analysis_date=date_obj.date())
        logger.info(f"[{date_str}] Screening stats: {screening_stats}")
        
        # 4. Tag Sync (Optional but requested implicitly by 'report')
        stmt = select(PatternStockPool).where(PatternStockPool.status.in_(['core', 'observation']))
        pool_stocks = (await session.execute(stmt)).scalars().all()
        
        for stock in pool_stocks:
            if not stock.patterns: continue
            tags_to_add = []
            tags_to_add.append(TagCreate(name="缠论选股", tag_type="strategy", score=0))
            
            p_list = stock.patterns
            if isinstance(p_list, str):
                try:
                    p_list = json.loads(p_list)
                except:
                    p_list = []
            
            if isinstance(p_list, list):
                for p_str in p_list:
                    p_name = p_str.split('(')[0]
                    tags_to_add.append(TagCreate(name=p_name, tag_type="pattern", score=stock.score))
            
            if tags_to_add:
                await tag_service.add_tags_to_stock(stock.stock_code, tags_to_add, operator="system_real")

        await session.commit()
        
        # 5. Check 603601
        stats_603601 = None
        stmt = select(PatternStockPool).where(PatternStockPool.stock_code.like('603601%'))
        stock_603601 = (await session.execute(stmt)).scalar_one_or_none()
        
        if stock_603601:
             stmt_all = select(PatternStockPool).order_by(desc(PatternStockPool.score))
             all_s = (await session.execute(stmt_all)).scalars().all()
             rank = -1
             for i, s in enumerate(all_s):
                 if s.stock_code.startswith('603601'):
                     rank = i + 1
                     break
             stats_603601 = {
                 "date": date_str,
                 "score": float(stock_603601.score),
                 "rank": rank,
                 "status": stock_603601.status,
                 "patterns": stock_603601.patterns
             }
        else:
             stats_603601 = {
                 "date": date_str,
                 "score": 0,
                 "rank": -1,
                 "status": "Not in Pool",
                 "patterns": None
             }
        
        if screening_stats:
            screening_stats["stats_603601"] = stats_603601
            
        return screening_stats

async def main():
    # 0. Reset DB
    logger.info("Resetting Database...")
    await reset_db()
    
    stock_sync_service = StockSyncService(db_manager)
    
    # 1. Get Dates
    # User said: start from 2025-11-20 to 2025-12-10
    days = await get_trading_days("2025-11-20", "2025-12-10")
    logger.info(f"Target Dates: {days}")
    
    report_data = []
    
    for d in days:
        try:
            stats = await run_daily_process(d, stock_sync_service)
            report_data.append({"date": d, "stats": stats})
        except Exception as e:
            logger.error(f"Failed processing {d}: {e}", exc_info=True)
            report_data.append({"date": d, "stats": None, "error": str(e)})

    # Generate Report
    try:
        with open("real_acceptance_report.md", "w") as f:
            f.write("# Real Acceptance Report\n\n")
            
            # General Stats
            f.write("## Daily Processing Stats\n\n")
            f.write("| Date | Processed | Passed | Failed | Errors |\n")
            f.write("|---|---|---|---|---|\n")
            for item in report_data:
                s = item.get("stats")
                if s:
                    f.write(f"| {item['date']} | {s.get('processed')} | {s.get('passed')} | {s.get('failed')} | {s.get('errors')} |\n")
                else:
                    err = item.get("error", "Unknown")
                    f.write(f"| {item['date']} | N/A | N/A | N/A | {err} |\n")
            
            # 603601 Verification
            f.write("\n## 603601 Verification\n\n")
            f.write("| Date | Score | Rank | Status | Patterns |\n")
            f.write("|---|---|---|---|---|\n")
            for item in report_data:
                s = item.get("stats")
                if s and s.get("stats_603601"):
                    st = s["stats_603601"]
                    f.write(f"| {st['date']} | {st['score']} | {st['rank']} | {st['status']} | {st['patterns']} |\n")
                else:
                    f.write(f"| {item['date']} | N/A | N/A | N/A | N/A |\n")
                    
    except Exception as e:
        logger.error(f"Failed to write report: {e}")

    # Cleanup
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
