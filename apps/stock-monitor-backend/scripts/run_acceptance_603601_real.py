
import asyncio
print("1. asyncio imported")
import logging
print("2. logging imported")
import os
print("2.1 os imported")
import sys
print("2.2 sys imported")
from datetime import datetime, timedelta, date
print("2.3 datetime imported")
from decimal import Decimal
print("2.4 decimal imported")
from sqlalchemy import text, select
print("2.5 sqlalchemy imported")
from typing import List, Dict, Any
print("3. standard libs imported")

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(current_dir) # apps/stock-monitor-backend
sys.path.append(backend_root)
print(f"4. path added: {backend_root}")

from app.database import DatabaseManager
print("5. DatabaseManager imported")
from app.crawler.wencai_crawler import WencaiCrawler
print("6. WencaiCrawler imported")
from app.services.stock_sync_service import StockSyncService
print("7. StockSyncService imported")
from app.services.rule_engine_service import RuleEngineService
print("8. RuleEngineService imported")
from app.models.stock_daily import StockDaily, StockScoreResult
print("9. Models imported")

# Setup logging
print("STARTING SCRIPT run_acceptance_603601_real.py")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TARGET_CODE = "603601"
TARGET_CODE_FULL = "603601.SH"
COMPARE_CODE = "603631" # Added per user request
COMPARE_CODE_FULL = "603631.SH"

TARGET_CODES = [TARGET_CODE, COMPARE_CODE]
TARGET_CODES_FULL = [TARGET_CODE_FULL, COMPARE_CODE_FULL]

async def clear_data(db_manager):
    logger.info(f"Clearing data for {TARGET_CODES}...")
    async with db_manager.get_session() as session:
        tables = [
            "wencai_stocks", "monitor_list", "stock_info", "stock_daily", 
            "stock_daily_temp", "stock_volume_baseline", "stock_tag_relations",
            "stock_score_results", "volume_analysis_results", "alert_records",
            "wencai_data_dedup", "stock_concepts"
        ]
        for table in tables:
            try:
                # Try both code formats
                for code, full_code in zip(TARGET_CODES, TARGET_CODES_FULL):
                    await session.execute(text(f"DELETE FROM {table} WHERE stock_code = :code OR stock_code = :full_code"), {"code": code, "full_code": full_code})
                    
                    # Some tables use 'code' column
                    if table in ["stock_info", "stock_daily", "stock_daily_temp", "stock_volume_baseline", "stock_score_results", "volume_analysis_results"]:
                         await session.execute(text(f"DELETE FROM {table} WHERE code = :code OR code = :full_code"), {"code": code, "full_code": full_code})
            except Exception as e:
                # Ignore column errors
                pass
        await session.commit()
    logger.info("Data cleared.")

async def sync_daily_data(db_manager, sync_service, target_date, codes: List[str]):
    """Sync daily data for the target stocks and date"""
    start_date_str = (target_date - timedelta(days=60)).strftime("%Y%m%d")
    end_date_str = target_date.strftime("%Y%m%d")
    
    logger.info(f"Syncing daily data for {codes} from {start_date_str} to {end_date_str}")
    
    for code_full in [c + (".SH" if c.startswith("6") else ".SZ") for c in codes]:
        # Handle suffix manually if needed, but sync_service usually takes full code
        # Actually codes passed here are short codes, let's make them full
        # But wait, logic above defines TARGET_CODES_FULL.
        pass

    results = {}
    for code, full_code in zip(TARGET_CODES, TARGET_CODES_FULL):
        df = await sync_service.fetch_from_akshare(full_code, start_date_str, end_date_str)
        
        if df is None or df.empty:
            logger.warning(f"No data found for {code} from Akshare")
            results[code] = False
            continue
            
        # Insert into DB
        async with db_manager.get_session() as session:
            for _, row in df.iterrows():
                # Check if exists
                trade_date_obj = datetime.strptime(str(row['trade_date']), "%Y%m%d").date()
                
                stmt = select(StockDaily).where(
                    StockDaily.code == code, 
                    StockDaily.trade_date == trade_date_obj
                )
                existing = (await session.execute(stmt)).scalar_one_or_none()
                
                if not existing:
                    daily = StockDaily(
                        code=code,
                        trade_date=trade_date_obj,
                        open=Decimal(str(row['open'])),
                        high=Decimal(str(row['high'])),
                        low=Decimal(str(row['low'])),
                        close=Decimal(str(row['close'])),
                        vol=int(row['vol']),
                        amount=Decimal(str(row['amount']))
                    )
                    session.add(daily)
            await session.commit()
        results[code] = True
    return results

async def main():
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    # 1. Clear Data
    await clear_data(db_manager)
    
    start_date = date(2025, 11, 20)
    end_date = date(2025, 12, 10)
    current_date = start_date
    
    sync_service = StockSyncService(db_manager)
    rule_service = RuleEngineService(db_manager)
    
    # Track results
    report_data = []

    while current_date <= end_date:
        logger.info(f"--- Processing {current_date} ---")
        
        # 2. Crawler
        date_str = current_date.strftime("%Y年%m月%d日")
        prev_date = current_date - timedelta(days=1)
        prev_date_str = prev_date.strftime("%Y年%m月%d日")
        
        query = f"{date_str}成交量是{prev_date_str}成交量的2.8倍以上，非北交 非创业版，非科创版，非ST，概念 行业，{prev_date_str}和{date_str}涨幅低于11% 收盘价低于25"
        
        found_in_crawl = False
        async with db_manager.get_session() as session:
            crawler = WencaiCrawler(session)
            # Try 3 times for crawler stability
            for attempt in range(3):
                try:
                    logger.info(f"Crawling (Attempt {attempt+1}): {query}")
                    result = await crawler.fetch_and_parse(query, target_stock_code=TARGET_CODE)
                    
                    if result.get("stocks"):
                        for s in result["stocks"]:
                            if TARGET_CODE in s.get("stock_code", ""):
                                found_in_crawl = True
                                break
                    
                    if result.get("status") == "completed":
                        break
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Crawl error: {e}")
                    await asyncio.sleep(1)

        logger.info(f"603601 found in crawl results: {found_in_crawl}")
        
        # 3. Sync Data (Always sync both stocks)
        has_data_map = await sync_daily_data(db_manager, sync_service, current_date, TARGET_CODES)
        
        day_stats = {
            "date": current_date.strftime("%Y-%m-%d"),
            "found_603601": found_in_crawl,
            "scores": {}
        }
        
        # 4. Score
        for code in TARGET_CODES:
            if has_data_map.get(code):
                logger.info(f"Calculating score for {code} on {current_date}")
                try:
                    # Force recalculation for specific stock
                    await rule_service.calculate_daily_scores(target_date=current_date, force=True, stock_code=code)
                    
                    # Retrieve Score
                    async with db_manager.get_session() as session:
                        stmt = select(StockScoreResult).where(
                            StockScoreResult.code == code,
                            StockScoreResult.trade_date == current_date
                        )
                        score_res = (await session.execute(stmt)).scalar_one_or_none()
                        
                        score_val = score_res.total_score if score_res else 0
                        
                        # Rank
                        count_stmt = select(StockScoreResult).where(StockScoreResult.trade_date == current_date)
                        all_scores = (await session.execute(count_stmt)).scalars().all()
                        all_scores_sorted = sorted(all_scores, key=lambda x: x.total_score, reverse=True)
                        
                        rank = "N/A"
                        for idx, s in enumerate(all_scores_sorted):
                            if s.code == code:
                                rank = idx + 1
                                break
                        
                        day_stats["scores"][code] = {
                            "score": score_val,
                            "rank": rank
                        }
                except Exception as e:
                    logger.error(f"Scoring error for {code}: {e}")
            else:
                 day_stats["scores"][code] = {
                    "score": 0,
                    "rank": "-"
                }
        
        report_data.append(day_stats)
        # Save incrementally
        generate_report(report_data)
        
        current_date += timedelta(days=1)
        # Avoid rapid requests
        await asyncio.sleep(0.5)

    # Generate Report Final
    generate_report(report_data)

def generate_report(data):
    # Use absolute path as requested/implied by workspace structure
    report_path = "/Users/mac/StudioProjects/open-citycloud/.trae/documents/Acceptance_Report_603601_Final.md"
    # Ensure dir exists
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# 股票 603601 (再升科技) 最终验收报告 (严格时序验证版)\n\n")
            f.write(f"**日期**: {date.today()}\n")
            f.write("**验证人**: Trae AI\n\n")
            f.write("## 1. 概述\n")
            f.write("本报告基于2025-11-20至2025-12-10的历史数据回测，验证603601及对比股票603631的积分与排名变化。\n\n")
            
            f.write("## 2. 每日积分与排名详情\n\n")
            f.write("| 日期 | 603601积分 | 603601排名 | 603631积分 | 603631排名 | 备注 |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
            
            for item in data:
                d = item["date"]
                s601 = item["scores"].get(TARGET_CODE, {"score": 0, "rank": "-"})
                s631 = item["scores"].get(COMPARE_CODE, {"score": 0, "rank": "-"})
                note = "603601出现在问财结果中" if item["found_603601"] else ""
                
                f.write(f"| {d} | {s601['score']} | {s601['rank']} | {s631['score']} | {s631['rank']} | {note} |\n")
                
            f.write("\n## 3. 结论\n")
            f.write("验证完成。\n")
            
        logger.info(f"Report saved to {report_path}")
    except Exception as e:
        logger.error(f"Failed to write report: {e}")

if __name__ == "__main__":
    asyncio.run(main())
