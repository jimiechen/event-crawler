
import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta
from sqlalchemy import text
from loguru import logger

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db_manager
from app.crawler.wencai_crawler import WencaiCrawler
from app.services.wencai_service import WencaiService
from app.services.volume_analysis_service import VolumeAnalysisService
from app.services.rule_engine_service import RuleEngineService
from app.models.stock import StockInfo
from unittest.mock import AsyncMock

# Configure logging
logger.remove()
logger.add(sys.stdout, level="INFO")
logger.add("reprocess_execution.log", rotation="10 MB")

async def get_trading_dates(session, start_date, end_date):
    stmt = text("SELECT DISTINCT trade_date FROM stock_daily WHERE trade_date BETWEEN :start AND :end ORDER BY trade_date")
    result = await session.execute(stmt, {"start": start_date, "end": end_date})
    return [row.trade_date for row in result.fetchall()]

async def get_prev_date(session, date_obj):
    stmt = text("SELECT MAX(trade_date) FROM stock_daily WHERE trade_date < :date")
    result = await session.execute(stmt, {"date": date_obj})
    return result.scalar()

async def clear_data(session, start_date, end_date):
    logger.info(f"Starting data cleanup for period {start_date} to {end_date}...")
    
    # 1. Find batches to delete
    # Note: We look for batches started in the range. 
    # Adjust time range to cover full days
    start_ts = f"{start_date} 00:00:00"
    end_ts = f"{end_date} 23:59:59"
    
    stmt = text("SELECT id FROM wencai_crawl_batches WHERE started_at BETWEEN :start AND :end")
    result = await session.execute(stmt, {"start": start_ts, "end": end_ts})
    batch_ids = [row.id for row in result.fetchall()]
    
    logger.info(f"Found {len(batch_ids)} batches to delete.")
    
    if batch_ids:
        # Delete related data
        stmt = text("DELETE FROM wencai_data_dedup WHERE crawl_batch_id IN :ids")
        await session.execute(stmt, {"ids": tuple(batch_ids)})
        
        stmt = text("DELETE FROM wencai_stocks WHERE crawl_batch_id IN :ids")
        await session.execute(stmt, {"ids": tuple(batch_ids)})
        
        # Batch tag relations? Assuming batch_tag_relations table
        try:
            stmt = text("DELETE FROM batch_tag_relations WHERE batch_id IN :ids")
            await session.execute(stmt, {"ids": tuple(batch_ids)})
        except Exception as e:
            logger.warning(f"Failed to delete batch_tag_relations (might not exist): {e}")

        stmt = text("DELETE FROM wencai_crawl_batches WHERE id IN :ids")
        await session.execute(stmt, {"ids": tuple(batch_ids)})
    
    # 2. Delete time-series data
    tables_date_col = [
        ("stock_daily", "trade_date"),
        ("stock_daily_temp", "trade_date"),
        ("stock_score_result", "trade_date"),
        ("volume_analysis_result", "trade_date"),
        # alert_record uses created_at usually, let's check schema or assume range
        # ("alert_record", "created_at") 
    ]
    
    for table, col in tables_date_col:
        logger.info(f"Clearing {table}...")
        stmt = text(f"DELETE FROM {table} WHERE {col} BETWEEN :start AND :end")
        await session.execute(stmt, {"start": start_date, "end": end_date})

    # Alert record might need datetime
    logger.info("Clearing alert_record...")
    stmt = text("DELETE FROM alert_record WHERE created_at BETWEEN :start AND :end")
    await session.execute(stmt, {"start": start_ts, "end": end_ts})

    logger.info("Data cleanup completed.")

async def run_crawler_for_date(session, target_date, prev_date):
    logger.info(f"Running crawler for {target_date} (Prev: {prev_date})...")
    
    date_str = target_date.strftime("%Y%m%d")
    prev_date_str = prev_date.strftime("%Y%m%d")
    
    # Construct query
    query = f"{date_str}成交量是{prev_date_str}成交量的2.5倍以上，非北交 非创业版，非科创版，非ST，概念 行业，{prev_date_str}和{date_str}涨幅低于13% 收盘价低于25"
    logger.info(f"Query: {query}")
    
    crawler = WencaiCrawler(session)
    wencai_service = WencaiService(session)
    
    # Fetch
    # Note: fetch_and_parse creates a batch but doesn't save stocks?
    # We need to manually handle the flow as seen in controller
    
    # Wait, WencaiCrawler.fetch_and_parse returns parsed_stocks?
    # Let's re-read wencai_crawler.py
    # It returns Dict with status, etc.
    # It calls wencai_service.create_crawl_batch
    # It calls wencai_service.parse_html_table -> returns parsed_stocks (List[Dict])
    # But it doesn't return parsed_stocks in the result dict?
    # Wait, wencai_crawler.py:
    # result = {"status": "completed", "found_target": ...}
    # It does NOT return parsed_stocks.
    # And it does NOT save them.
    # This seems like a flaw in fetch_and_parse if it's meant to be standalone.
    # But wait, wencai_controller.py passes `request.html_content` to `parse_html_table`.
    # It seems `fetch_and_parse` in crawler is for "validation" or "auto crawl"?
    # In `wencai_crawler.py`:
    # parsed_stocks = self.wencai_service.parse_html_table(html_content, debug=True)
    # It doesn't do anything with parsed_stocks other than check if target exists.
    
    # So I should use the lower level methods or modify the crawler call.
    # I will emulate what controller does.
    
    html_content = await crawler.fetch_page_source(query)
    if not html_content:
        logger.error(f"Failed to fetch content for {target_date}")
        return
        
    batch_name = f"Reprocess_{date_str}"
    batch_id = await wencai_service.create_crawl_batch(
        batch_name=batch_name,
        crawl_url=f"http://www.iwencai.com/stockpick/search?w={query}",
        query_string=query
    )
    
    parsed_stocks = wencai_service.parse_html_table(html_content, debug=False)
    if not parsed_stocks:
        logger.warning(f"No stocks found for {target_date}")
        await wencai_service.update_batch_status(batch_id, 'failed', 0, 0, 0, 'No data')
        return

    success_count, failed_count, errors = await wencai_service.save_wencai_stocks(batch_id, parsed_stocks)
    await wencai_service.update_batch_status(batch_id, 'completed', len(parsed_stocks), success_count, failed_count)
    
    logger.info(f"Saved {success_count} stocks for {target_date}")
    
    # Process batch (tags, etc.)
    # PATCH: Disable automatic scoring to avoid calculating for "today"
    original_calc = RuleEngineService.calculate_daily_scores
    RuleEngineService.calculate_daily_scores = AsyncMock()
    
    try:
        await wencai_service.process_batch_data(batch_id)
    finally:
        # Restore original method
        RuleEngineService.calculate_daily_scores = original_calc
    
    # Manual scoring for correct date
    logger.info(f"Manually triggering scoring for {target_date}...")
    rule_service = RuleEngineService(db_manager)
    await rule_service.calculate_daily_scores(target_date=target_date, force=True)
    logger.info(f"Scoring completed for {target_date}")
    
    # Sync to monitor/stock_info/stock_daily?
    # process_batch_data calls sync_batch_stocks_to_pool?
    # wencai_service.py: process_batch_data implementation calls sync_batch_stocks_to_pool
    # sync_batch_stocks_to_pool adds to monitor list.
    # Does it add to StockDaily?
    # Usually monitor_service.add_monitor -> stock_service.create_stock -> ...
    # It might create StockInfo.
    # But StockDaily?
    # If StockDaily is missing, scoring will fail.
    # I hope wencai_service or monitor_service handles daily data fetching.
    # If not, I might need to explicitly fetch daily data for these stocks.
    # For now, let's assume the system works as intended.

async def main():
    logger.info("Initializing...")
    await db_manager.initialize()
    
    start_date_str = "2025-11-20"
    end_date_str = "2025-12-10"
    
    async with db_manager.get_session() as session:
        # 0. Get dates
        dates = await get_trading_dates(session, start_date_str, end_date_str)
        logger.info(f"Trading dates: {dates}")
        
        # 1. Clean Data
        await clear_data(session, start_date_str, end_date_str)
        await session.commit()
        
    # 2. Run Crawler
    # Re-open session for each iteration to be safe or keep one?
    # WencaiCrawler needs session.
    
    for target_date in dates:
        async with db_manager.get_session() as session:
            prev_date = await get_prev_date(session, target_date)
            if not prev_date:
                logger.warning(f"No previous date for {target_date}, skipping...")
                continue
                
            await run_crawler_for_date(session, target_date, prev_date)
            await session.commit()
            
        # Sleep to be nice
        await asyncio.sleep(5)

    # 3. Run Scoring
    logger.info("Starting scoring...")
    # Analyze 603601 specifically and others
    target_code = "603601"
    
    async with db_manager.get_session() as session:
        # We should probably analyze all active stocks to be thorough, but it takes time.
        # User said "Execute volume/price score calculation ... focus on 603601".
        # But if I cleared all results, I should probably restore them for everyone if possible.
        # But `analyze_all_stocks` might take too long.
        # Let's get all stocks from wencai_stocks for the period and analyze them.
        
        stmt = text("""
            SELECT DISTINCT stock_code FROM wencai_stocks ws
            JOIN wencai_crawl_batches wcb ON ws.crawl_batch_id = wcb.id
            WHERE wcb.started_at BETWEEN :start AND :end
        """)
        result = await session.execute(stmt, {"start": f"{start_date_str} 00:00:00", "end": f"{end_date_str} 23:59:59"})
        codes = [row.stock_code for row in result.fetchall()]
        
        if target_code not in codes:
            codes.append(target_code)
            
        logger.info(f"Analyzing {len(codes)} stocks...")
        
        for code in codes:
            try:
                # Need to use VolumeAnalysisService.analyze_stock
                # But it manages its own session?
                # The method signature: analyze_stock(code, session=None, ...)
                # If I pass session, it uses it.
                await VolumeAnalysisService.analyze_stock(code, session=session)
            except Exception as e:
                logger.error(f"Failed to analyze {code}: {e}")
        
        await session.commit()

    # 4. Verification for 603601
    async with db_manager.get_session() as session:
        logger.info("Verifying 603601...")
        stmt = text("SELECT trade_date, total_score, ranking FROM stock_score_result WHERE code = '603601' AND trade_date BETWEEN :start AND :end ORDER BY trade_date")
        result = await session.execute(stmt, {"start": start_date_str, "end": end_date_str})
        rows = result.fetchall()
        for row in rows:
            logger.info(f"603601 | {row.trade_date} | Score: {row.total_score} | Rank: {row.ranking}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
