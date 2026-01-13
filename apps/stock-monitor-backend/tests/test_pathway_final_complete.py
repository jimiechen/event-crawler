
import asyncio
import sys
import os
import pandas as pd
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Set
from sqlalchemy import text, func, select, insert
from loguru import logger
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import db_manager
from app.services.pathway_engine import PathwayVolumePriceEngine
from app.models.stock_daily import StockDaily, StockScoreResult
from app.models.stock import StockInfo
from app.models.tag_management import StockTagRelation, StockTagInfo
from app.services.tag_service import TagService

# Configure logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")

# Configuration
TEST_START = "2025-11-20"
TEST_END = "2025-12-10"
TARGET_SYMBOL = "603601.SH"
# Get CSV path from env, fallback to default if not set
CSV_ROOT = os.getenv("CSV_DATA_PATH_STOCK_DAILY", "/Volumes/MacintoshHD/data/daily")
WENCAI_DATA_DIR = "/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/data/wencai"

class PathwayRealDataTest:
    def __init__(self):
        self.unique_codes = set()
        self.daily_wencai_codes = {} # date_str -> list of codes
        
    async def setup(self):
        """Clean DB except protected tables"""
        logger.info("🧹 Cleaning database...")
        async with db_manager.get_session() as session:
            # Explicitly list tables to truncate as per user request
            tables_to_truncate = [
                "stock_daily", 
                "stock_daily_temp",
                "monitor_list",
                "volume_analysis_results",
                "alert_records",
                "wencai_stocks",
                "stock_info",
                "stock_volume_baseline",
                "wencai_data_dedup",
                "stock_concepts",
                "wencai_crawl_batches",
                # "stock_tags_info", # We will update tags, not truncate
                "stock_tag_relations",
                "stock_score_results" # Also clean score results
            ]
            
            for table in tables_to_truncate:
                try:
                    await session.execute(text(f"TRUNCATE TABLE {table}"))
                except Exception as e:
                    try:
                        await session.execute(text(f"DELETE FROM {table}"))
                    except Exception as e2:
                        logger.warning(f"Could not clear table {table}: {e2}")
            
            # Ensure stock_daily code column is long enough
            try:
                await session.execute(text("ALTER TABLE stock_daily MODIFY COLUMN code VARCHAR(20)"))
            except Exception:
                pass

            await session.commit()
            
            # Setup Tags
            await self.setup_tags(session)
            
            logger.info("✅ Database cleaned and tags configured.")

    async def setup_tags(self, session):
        """Insert required tags with scores"""
        logger.info("🏷️ Configuring tags with high scores...")
        tags = [
            {'name': 'EXPMA13上方', 'score': 50.0}, # High score for trend accumulation
            {'name': '60日地量', 'score': 600.0},
            {'name': '30日地量', 'score': 300.0},
            {'name': '20日地量', 'score': 200.0},
            {'name': '10日地量', 'score': 100.0},
            {'name': '5日地量', 'score': 50.0},
            {'name': '3倍量', 'score': 300.0},
            {'name': '2倍量', 'score': 200.0},
            {'name': '涨停', 'score': 100.0},
            {'name': '阳包阴', 'score': 200.0},
            {'name': '底分型', 'score': 300.0},
            {'name': '冲高回落', 'score': 50.0},
            {'name': '地量比率', 'score': 100.0}
        ]
        
        for tag_data in tags:
            # Check if exists
            stmt = select(StockTagInfo).where(StockTagInfo.name == tag_data['name'])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.score = tag_data['score']
                existing.tag_type = 'calculation'
            else:
                new_tag = StockTagInfo(
                    name=tag_data['name'], 
                    score=tag_data['score'], 
                    tag_type='calculation'
                )
                session.add(new_tag)
        
        await session.commit()

    async def prepare_stock_list(self):
        """Load Wencai CSVs and build stock list"""
        logger.info("📋 Building stock list from Wencai data...")
        
        # Add target symbol
        self.unique_codes.add(TARGET_SYMBOL)
        
        start_date = datetime.strptime(TEST_START, "%Y-%m-%d")
        end_date = datetime.strptime(TEST_END, "%Y-%m-%d")
        
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:
                date_str = current.strftime("%Y%m%d")
                csv_path = os.path.join(WENCAI_DATA_DIR, f"wencai_{date_str}.csv")
                
                codes = []
                if os.path.exists(csv_path):
                    try:
                        # Read stock_code as string to preserve leading zeros
                        df = pd.read_csv(csv_path, dtype={'stock_code': str})
                        # Extract codes
                        for _, row in df.iterrows():
                            raw_code = str(row['stock_code']).strip()
                            
                            norm_code = raw_code
                            if '.' not in raw_code:
                                if raw_code.startswith('6'): norm_code = f"{raw_code}.SH"
                                elif raw_code.startswith('0') or raw_code.startswith('3'): norm_code = f"{raw_code}.SZ"
                                elif raw_code.startswith('4') or raw_code.startswith('8'): norm_code = f"{raw_code}.BJ"
                            
                            codes.append(norm_code)
                            self.unique_codes.add(norm_code)
                    except Exception as e:
                        logger.error(f"Error reading {csv_path}: {e}")
                else:
                    logger.warning(f"⚠️ No Wencai data for {date_str} (Run fetch script first?)")
                
                self.daily_wencai_codes[current.strftime("%Y-%m-%d")] = codes
                
            current += timedelta(days=1)
            
        logger.info(f"✅ Loaded {len(self.unique_codes)} unique stocks from Wencai CSVs.")
        
        # Remove limit to process all stocks in Wencai pool
        # limited_codes = {TARGET_SYMBOL}
        # other_codes = list(self.unique_codes - limited_codes)[:5] 
        # limited_codes.update(other_codes)
        # self.unique_codes = limited_codes
        logger.info(f"🚀 Analyzing all {len(self.unique_codes)} stocks from Wencai pool")

    async def import_data(self):
        """Import historical data for all stocks"""
        logger.info("📥 Importing historical data from CSVs...")
        
        async with db_manager.get_session() as session:
            total = len(self.unique_codes)
            count = 0
            
            for code in self.unique_codes:
                count += 1
                if count % 10 == 0:
                    logger.info(f"Importing {count}/{total}...")
                    
                csv_path = os.path.join(CSV_ROOT, f"{code}.csv")
                if not os.path.exists(csv_path):
                    # Try alternate suffix combinations if standard one fails
                    base_code = code.split('.')[0]
                    alternatives = [
                        f"{base_code}.csv",
                        f"{base_code}.SH.csv", 
                        f"{base_code}.SZ.csv",
                        f"{base_code}.BJ.csv"
                    ]
                    for alt in alternatives:
                        alt_path = os.path.join(CSV_ROOT, alt)
                        if os.path.exists(alt_path):
                            csv_path = alt_path
                            break
                            
                if not os.path.exists(csv_path):
                    logger.warning(f"❌ Data file not found for {code} (Checked: {csv_path})")
                    continue
                    
                try:
                    df = pd.read_csv(csv_path)
                    
                    col_map = {
                        '股票代码': 'code', '交易日期': 'trade_date',
                        '开盘价': 'open', '最高价': 'high', '最低价': 'low', '收盘价': 'close',
                        '成交量(手)': 'vol', '成交额(千元)': 'amount',
                        '成交量': 'vol', '成交额': 'amount'
                    }
                    df = df.rename(columns=col_map)
                    
                    needed = ['trade_date', 'open', 'high', 'low', 'close', 'vol', 'amount']
                    available = [c for c in needed if c in df.columns]
                    df = df[available]
                    
                    df['trade_date'] = pd.to_datetime(df['trade_date'])
                    
                    # Deduplicate
                    df = df.drop_duplicates(subset=['trade_date'])
                    
                    # Filter data to include enough history before TEST_END
                    test_end_dt = datetime.strptime(TEST_END, "%Y-%m-%d")
                    mask = df['trade_date'] <= test_end_dt
                    df = df[mask]
                    
                    # Check data length for 250 days requirement
                    if len(df) < 250:
                        logger.warning(f"⚠️ {code}: Insufficient history ({len(df)} days < 250). Long-term indicators may be inaccurate.")
                    
                    df = df.sort_values('trade_date')
                    
                    records = []
                    # Use itertuples for faster iteration
                    for row in df.itertuples(index=False):
                        records.append({
                            'code': code,
                            'trade_date': row.trade_date.date(),
                            'open': Decimal(str(row.open)),
                            'high': Decimal(str(row.high)),
                            'low': Decimal(str(row.low)),
                            'close': Decimal(str(row.close)),
                            'vol': int(row.vol),
                            'amount': Decimal(str(row.amount)) if hasattr(row, 'amount') and pd.notna(row.amount) else None
                        })
                    
                    if records:
                        # Use Core Insert with larger chunks
                        chunk_size = 5000
                        for i in range(0, len(records), chunk_size):
                            batch = records[i:i+chunk_size]
                            await session.execute(insert(StockDaily), batch)
                            await session.commit()
                    
                    if code == TARGET_SYMBOL:
                        logger.info(f"✅ Successfully imported {len(records)} rows for {TARGET_SYMBOL}")
                    
                    # Ensure StockInfo record exists
                    stmt_check = select(StockInfo).where(StockInfo.code == code)
                    res_check = await session.execute(stmt_check)
                    if not res_check.scalar_one_or_none():
                        session.add(StockInfo(code=code, name=code))
                        await session.commit()
                        
                except Exception as e:
                    logger.error(f"Error importing {code}: {e}")
                    await session.rollback()

    async def calculate_history_baseline(self):
        """Calculate historical scores for the baseline period (before TEST_START)"""
        logger.info("⏳ Calculating history baseline (warmup)...")
        # Warmup for 400 calendar days (~280 trading days) to ensure full 250-day window
        warmup_start = datetime.strptime(TEST_START, "%Y-%m-%d") - timedelta(days=400)
        warmup_end = datetime.strptime(TEST_START, "%Y-%m-%d") - timedelta(days=1)
        
        async with db_manager.get_session() as session:
            engine = PathwayVolumePriceEngine(session)
            # Batch calculate for all unique codes
            total = len(self.unique_codes)
            count = 0
            for code in self.unique_codes:
                count += 1
                if count % 10 == 0:
                    logger.info(f"Baseline calculation: {count}/{total} stocks...")
                
                await engine.batch_calculate_scores(code, warmup_start.date(), warmup_end.date())
        
        logger.info("✅ History baseline calculation complete.")

    async def run_analysis(self):
        """Run Pathway analysis day by day"""
        logger.info("🚀 Starting Pathway Analysis Loop...")
        
        # Calculate baseline first
        await self.calculate_history_baseline()
        
        start_date = datetime.strptime(TEST_START, "%Y-%m-%d")
        end_date = datetime.strptime(TEST_END, "%Y-%m-%d")
        current = start_date
        
        results_summary = []
        all_daily_results = {} # Store full ranking data for Excel report
        cumulative_scores = {} # Track cumulative scores across days
        
        while current <= end_date:
            if current.weekday() < 5:
                date_str = current.strftime("%Y-%m-%d")
                logger.info(f"📅 Processing {date_str}...")
                
                today_wencai = self.daily_wencai_codes.get(date_str, [])
                today_targets = set(today_wencai)
                today_targets.add(TARGET_SYMBOL)
                
                async with db_manager.get_session() as session:
                    # Initialize engine with session
                    self.engine = PathwayVolumePriceEngine(session)
                    
                    # For each stock
                    day_scores = []
                    
                    for code in today_targets:
                        # 1. Get history up to today
                        # Increased LIMIT to 1000 to ensure enough history for long-term indicators
                        stmt = text("""
                            SELECT open, close, high, low, vol, trade_date 
                            FROM stock_daily 
                            WHERE code = :code AND trade_date <= :date 
                            ORDER BY trade_date DESC 
                            LIMIT 1000
                        """)
                        result = await session.execute(stmt, {"code": code, "date": current.date()})
                        rows = result.fetchall()
                        
                        if not rows or len(rows) < 250:
                            # Not enough data for robust analysis
                            if code == TARGET_SYMBOL:
                                logger.warning(f"⚠️ {TARGET_SYMBOL}: Insufficient history ({len(rows)} days) for {date_str}")
                            continue
                            
                        # Convert to dicts for Pathway
                        history = [
                            {
                                'open': float(r.open), 'close': float(r.close),
                                'high': float(r.high), 'low': float(r.low),
                                'vol': int(r.vol), 'trade_date': r.trade_date
                            }
                            for r in rows
                        ]
                        
                        # 2. Calculate Tags
                        tags = self.engine.calculate_tags(history)
                        
                        # 3. Calculate Score
                        # Use engine's scoring logic for DAILY score
                        daily_score = sum(tag.get('score', 0) for tag in tags)
                        
                        # 4. Save and Aggregate (Simulate Engine Behavior)
                        # We call engine.process_new_data internally if we want to save
                        # But since we already have tags, we can just save directly or call process_new_data
                        # To be consistent and ensure aggregation, let's just use process_new_data logic
                        # But we already fetched history manually.
                        # Let's trust the engine's batch_calculate_scores for history, 
                        # and here we explicitly call process_new_data to handle "Today"
                        
                        # Fetch the StockDaily object for today
                        stmt_daily = select(StockDaily).where(
                            StockDaily.code == code,
                            StockDaily.trade_date == current.date()
                        )
                        res_daily = await session.execute(stmt_daily)
                        stock_daily_obj = res_daily.scalar_one_or_none()
                        
                        if stock_daily_obj:
                             result_data = await self.engine.process_new_data(stock_daily_obj)
                             daily_score = result_data['tag_score']
                             total_score = result_data['total_score'] # This is just daily score in current engine impl
                             
                             # Get the Aggregated Score (Volume Anomaly Score) from StockInfo
                             # process_new_data calls _aggregate_to_stock_info which updates StockInfo
                             # Re-fetch StockInfo to get updated score
                             stmt_info = select(StockInfo).where(StockInfo.code == code)
                             res_info = await session.execute(stmt_info)
                             stock_info_obj = res_info.scalar_one_or_none()
                             
                             if stock_info_obj:
                                 # Refresh to ensure we get latest committed data
                                 await session.refresh(stock_info_obj)
                                 aggregated_score = stock_info_obj.volume_anomaly_score or 0
                             else:
                                 logger.warning(f"StockInfo not found for {code} when fetching score")
                                 aggregated_score = 0
                        else:
                             aggregated_score = 0
                             daily_score = 0

                        day_scores.append({
                            'code': code,
                            'score': aggregated_score,   # Ranking based on Aggregated (250-day) Score
                            'daily_score': daily_score,  # Track daily change
                            'tags': [t['name'] for t in tags],
                            'close': history[0]['close'],
                            'vol': history[0]['vol']
                        })
                        
                    # Sort by CUMULATIVE score
                    day_scores.sort(key=lambda x: x['score'], reverse=True)
                    
                    # Add ranking
                    for idx, item in enumerate(day_scores):
                        item['rank'] = idx + 1
                    
                    # Store top 20 for Excel report
                    all_daily_results[date_str] = day_scores[:20]
                        
                    # Find Target
                    target_res = next((x for x in day_scores if x['code'] == TARGET_SYMBOL), None)
                    if target_res:
                        logger.info(f"  🎯 {TARGET_SYMBOL}: Rank {target_res['rank']}, Total {target_res['score']} (Daily {target_res['daily_score']}), Tags: {target_res['tags']}")
                        results_summary.append({
                            'date': date_str,
                            'rank': target_res['rank'],
                            'score': target_res['score'],
                            'daily_score': target_res['daily_score'],
                            'close': target_res['close'],
                            'tags': ",".join(target_res['tags'])
                        })
                    else:
                        logger.warning(f"  ⚠️ {TARGET_SYMBOL} not ranked today (maybe no data?)")
                        
            current += timedelta(days=1)
            
        # Output Final Report
        print("\n" + "="*90)
        print(f"📊 Pathway Analysis Report ({TEST_START} ~ {TEST_END}) - Cumulative Scoring Mode")
        print("="*90)
        print(f"🎯 Target: {TARGET_SYMBOL}")
        print("-" * 90)
        print(f"{'Date':<12} | {'Price':<8} | {'Total':<6} | {'Daily':<6} | {'Rank':<5} | {'Tags'}")
        print("-" * 90)
        for r in results_summary:
            print(f"{r['date']:<12} | {r['close']:<8} | {r['score']:<6} | {r['daily_score']:<6} | {r['rank']:<5} | {r['tags']}")
        print("="*90)

        # Generate Excel Report
        report_dir = "/Users/mac/StudioProjects/open-citycloud/.trae/documents/2026-01-10"
        os.makedirs(report_dir, exist_ok=True)
        excel_path = os.path.join(report_dir, "pathway_analysis_top20.xlsx")
        
        logger.info(f"📊 Generating Excel report at {excel_path}...")
        
        try:
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                for date_key, scores_list in all_daily_results.items():
                    # Convert to DataFrame
                    df_data = []
                    for item in scores_list:
                        df_data.append({
                            'Rank': item['rank'],
                            'Stock Code': item['code'],
                            'Total Score': item['score'],
                            'Daily Score': item['daily_score'],
                            'Close Price': item['close'],
                            'Tags': ",".join(item['tags'])
                        })
                    
                    if df_data:
                        df = pd.DataFrame(df_data)
                        df.to_excel(writer, sheet_name=date_key, index=False)
            
            logger.info(f"✅ Excel report generated successfully: {excel_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate Excel report: {e}")

async def main():
    await db_manager.initialize()
    test = PathwayRealDataTest()
    await test.setup()
    await test.prepare_stock_list()
    await test.import_data()
    await test.run_analysis()

if __name__ == "__main__":
    asyncio.run(main())
