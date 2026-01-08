
import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta, date
from decimal import Decimal
from sqlalchemy import text

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db_manager
from app.models.base import Base
# Import models to ensure they are registered in Base.metadata
from app.models import stock, stock_daily, tag_management
from app.services.local_data_service import LocalDataService
from app.services.stock_service import StockService
from app.crawler.wencai_crawler import WencaiCrawler
from app.services.rule_engine_service import RuleEngineService
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stdout, level="INFO")

async def ensure_tables():
    logger.info("Ensuring tables exist...")
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def clear_data(session):
    logger.info("Clearing existing data...")
    tables = [
        "stock_score_result",
        "stock_daily",
        "task_execution_log",
        "wencai_stocks",
        "wencai_crawl_batches",
        "stock_tag_relations",
        "stock_info"
    ]
    
    for table in tables:
        try:
            await session.execute(text(f"TRUNCATE TABLE {table}"))
            logger.info(f"Truncated {table}")
        except Exception as e:
            logger.warning(f"Failed to truncate {table}: {e}")
            try:
                await session.execute(text(f"DELETE FROM {table}"))
                logger.info(f"Deleted from {table}")
            except Exception as e2:
                logger.error(f"Failed to delete {table}: {e2}")
    
    await session.commit()

async def main():
    logger.info("Starting Rebuild and Verify Process (Optimized)")
    
    await db_manager.initialize()
    await ensure_tables()
    
    async with db_manager.get_session() as session:
        await clear_data(session)
        stock_service = StockService(session)
    
    # 3. Iterate Dates
    start_date = date(2025, 11, 20)
    end_date = date(2025, 12, 10)
    current_date = start_date
    
    rule_service = RuleEngineService(db_manager)
    
    results_603601 = []
    
    while current_date <= end_date:
        d1_str = current_date.strftime("%Y年%m月%d日")
        prev_date = current_date - timedelta(days=1)
        d2_str = prev_date.strftime("%Y年%m月%d日")
        
        # CORRECTED QUERY: Use "非创业板" instead of "非创业版", "非北交所" instead of "非北交"
        query = f"{d1_str}成交量是{d2_str}成交量的2.5倍以上，非北交所 非创业板 非科创板 非ST，概念 行业，{d2_str}和{d1_str}涨幅低于13% 收盘价低于25"
        
        logger.info(f"Processing date: {current_date}")
        
        # Run Crawler
        batch_id = None
        async with db_manager.get_session() as session:
            crawler = WencaiCrawler(session)
            await asyncio.sleep(2) # Small delay
            
            try:
                result = await crawler.fetch_and_parse(
                    query=query,
                    batch_name=f"Verify_{current_date.strftime('%Y%m%d')}"
                )
                
                if result.get("status") == "completed":
                    batch_id = result.get("batch_id")
                    count = result.get("total", 0)
                    logger.info(f"Crawler found {count} stocks for {current_date} (Batch {batch_id})")
                else:
                    logger.warning(f"Crawler failed for {current_date}: {result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Error processing {current_date}: {e}")
        
        # If stocks found, load data and score
        if batch_id:
            async with db_manager.get_session() as session:
                # Get codes from wencai_stocks
                res = await session.execute(
                    text("SELECT stock_code FROM wencai_stocks WHERE crawl_batch_id = :bid"),
                    {"bid": str(batch_id)} # WencaiStock.crawl_batch_id is string
                )
                codes = [r[0] for r in res.fetchall()]
                
                if codes:
                    logger.info(f"Loading local data for {len(codes)} stocks...")
                    stock_service = StockService(session)
                    
                    # Load basics first (since we cleared stock_info)
                    await LocalDataService.load_stock_basics_for_stocks(stock_service, codes)
                    
                    # Load data for these stocks
                    await LocalDataService.load_local_data_for_stocks(stock_service, codes)
                    
                    # Calculate scores
                    logger.info(f"Calculating scores for {current_date}")
                    # Note: rule_service manages its own session/db access usually
                    score_res = await rule_service.calculate_daily_scores(target_date=current_date, force=True)
                    logger.info(f"Scoring result: {score_res}")
        
        # Check 603601
        async with db_manager.get_session() as session:
            res = await session.execute(
                text("SELECT total_score, ranking FROM stock_score_result WHERE code = '603601' AND trade_date = :date"),
                {"date": current_date}
            )
            row = res.fetchone()
            if row:
                results_603601.append({
                    "date": current_date,
                    "score": row[0],
                    "rank": row[1]
                })
                logger.info(f"603601 on {current_date}: Score={row[0]}, Rank={row[1]}")
            else:
                # Maybe 603601 wasn't in the list?
                # Check if it was in the crawler list
                if batch_id:
                     res_check = await session.execute(
                        text("SELECT count(*) FROM wencai_stocks WHERE crawl_batch_id = :bid AND stock_code LIKE '603601%'"),
                        {"bid": str(batch_id)}
                     )
                     in_list = res_check.scalar() > 0
                     logger.info(f"603601 on {current_date}: No Score (In List: {in_list})")
                else:
                     logger.info(f"603601 on {current_date}: No Score (No Batch)")

        current_date += timedelta(days=1)
        
    # Final Report
    logger.info("\n=== Final Report ===")
    logger.info("603601 Performance (2025-11-20 to 2025-12-10):")
    for r in results_603601:
        logger.info(f"Date: {r['date']}, Score: {r['score']}, Rank: {r['rank']}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Main execution error: {e}")
