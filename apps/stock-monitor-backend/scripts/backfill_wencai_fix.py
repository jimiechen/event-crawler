import sys
import os
print("Script loaded")

import asyncio
from datetime import date, timedelta, datetime
import time
print("Importing sqlalchemy...")
from sqlalchemy import select
print("Importing pandas...")
import pandas as pd

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUTPUT_DIR = "/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/data/wencai"

print("Importing app modules...")
from app.database import db_manager
print("Imported db_manager")
from app.crawler.wencai_crawler import WencaiCrawler
print("Imported WencaiCrawler")
from app.services.stock_sync_service import StockSyncService
print("Imported StockSyncService")
from app.services.rule_engine_service import RuleEngineService
print("Imported RuleEngineService")
from app.models.crawler import CrawlerTarget
print("Imported CrawlerTarget")
from loguru import logger
print("Imports done")

async def main():
    logger.info("Initializing database...")
    print("Initializing database (stdout)...")
    await db_manager.initialize()
    
    # Range: 2025-12-11 to 2026-01-16
    start_date = date(2025, 12, 11)
    end_date = date(2026, 1, 16)
    
    logger.info(f"Starting backfill from {start_date} to {end_date}")
    
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() >= 5: # Skip Sat/Sun
            logger.info(f"Skipping weekend: {current_date}")
            current_date += timedelta(days=1)
            continue
            
        logger.info(f"========== Processing date: {current_date} ==========")
        
        try:
            async with db_manager.get_session() as session:
                # 1. Get Crawler Target
                stmt = select(CrawlerTarget).where(
                    CrawlerTarget.is_active == True,
                    CrawlerTarget.platform == 'wencai'
                )
                result = await session.execute(stmt)
                targets = result.scalars().all()
                
                # Initialize services
                # WencaiCrawler needs a session
                crawler = WencaiCrawler(session)
                
                # These services manage their own sessions via db_manager
                sync_service = StockSyncService(db_manager) 
                rule_service = RuleEngineService(db_manager)
                
                batch_ids = []
                
                # Default query template if no target found
                query_template = "{date}成交量是{prev_date}成交量的2.9倍以上，非北交，非创业板，非科创版，非ST，概念，行业，{prev_date}和{date}涨幅低于13%，收盘价低于25"
                
                queries_to_run = []
                
                if targets:
                    for t in targets:
                        # Use target name for logging
                        logger.info(f"Found target: {t.name} (ID: {t.id})")
                        queries_to_run.append(t.url)
                else:
                    logger.warning("No enabled targets found, using default template")
                    queries_to_run.append(query_template)
                
                # Calculate dates for query replacement
                prev_date = current_date - timedelta(days=1)
                while prev_date.weekday() >= 5:
                     prev_date -= timedelta(days=1)
                     
                date_str = current_date.strftime("%Y年%m月%d日")
                prev_date_str = prev_date.strftime("%Y年%m月%d日")
                
                for q_tmpl in queries_to_run:
                    # Format query
                    query = q_tmpl
                    try:
                        # Replace various placeholder formats to be safe
                        query = query.replace("{query_date}", date_str)
                        query = query.replace("{prev_date_str}", prev_date_str)
                        query = query.replace("{date}", date_str)
                        query = query.replace("{prev_date}", prev_date_str)
                    except Exception as e:
                        logger.warning(f"Query format error: {e}")
                        
                    logger.info(f"Running crawler with query: {query}")
                    
                    # Run Crawler
                    # Note: crawler uses the session passed in __init__
                    crawl_result = await crawler.fetch_and_parse(
                        query=query,
                        batch_name=f"Backfill_{current_date.strftime('%Y%m%d')}",
                        target_date=current_date
                    )
                    
                    if crawl_result.get("status") == "completed":
                        bid = crawl_result.get("batch_id")
                        count = crawl_result.get("total", 0)
                        if bid:
                            batch_ids.append(bid)
                            logger.info(f"✅ Crawl success. Batch ID: {bid}, Stocks found: {count}")
                            
                            # Save to CSV
                            stocks = crawl_result.get("stocks", [])
                            if stocks:
                                try:
                                    if not os.path.exists(OUTPUT_DIR):
                                        os.makedirs(OUTPUT_DIR)
                                    
                                    df = pd.DataFrame(stocks)
                                    output_path = os.path.join(OUTPUT_DIR, f"wencai_{current_date.strftime('%Y%m%d')}.csv")
                                    df.to_csv(output_path, index=False, encoding='utf-8-sig')
                                    logger.info(f"Saved wencai data to {output_path}")
                                except Exception as e:
                                    logger.error(f"Failed to save CSV: {e}")
                        else:
                            logger.warning(f"Crawl completed but no batch ID returned. Result: {crawl_result}")
                    else:
                        logger.error(f"❌ Crawl failed for {current_date}: {crawl_result.get('error')}")

                # Commit any changes made by crawler using the session
                # (Although fetch_and_parse usually handles its own commits via wencai_service, 
                # but it's good practice to ensure session is clean before next steps)
                await session.commit()

            # 2. Sync Data (Outside of crawler session context to avoid conflicts if service uses db_manager)
            # sync_service uses db_manager internally
            if batch_ids:
                for bid in batch_ids:
                    logger.info(f"Starting data sync for Batch {bid}...")
                    # sync_tushare_increment fetches from start_date to TODAY
                    sync_res = await sync_service.sync_tushare_increment(
                        batch_id=bid,
                        start_date_str=current_date.strftime("%Y-%m-%d")
                    )
                    logger.info(f"Sync result: {sync_res}")
            else:
                logger.info("No batches to sync for this date.")
            
            # 3. Calculate Scores
            logger.info(f"Calculating scores for {current_date}...")
            # rule_service uses db_manager internally
            try:
                await rule_service.calculate_daily_scores(target_date=current_date)
                logger.info(f"✅ Scoring completed for {current_date}")
            except Exception as e:
                logger.error(f"❌ Scoring failed for {current_date}: {e}")
                
        except Exception as e:
            logger.error(f"❌ Critical error processing {current_date}: {e}")
            import traceback
            traceback.print_exc()
            
        current_date += timedelta(days=1)
        # Sleep to be nice to APIs
        await asyncio.sleep(3)

    logger.info("Backfill process completed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
    except Exception as e:
        logger.error(f"Process crashed: {e}")
