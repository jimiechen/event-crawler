
import sys
import os
import asyncio
import pandas as pd
from datetime import datetime, timedelta, date
from sqlalchemy import text
from loguru import logger

# Add project root to sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(backend_root)

from app.database import db_manager
from app.crawler.wencai_crawler import WencaiCrawler
from app.services.stock_data_manager import StockDataManager

# Configuration
START_DATE = date(2025, 11, 20)
END_DATE = date(2025, 12, 10)
REPORT_FILE = os.path.abspath(os.path.join(backend_root, "../../../../.trae/documents/Acceptance_Report_603601_Final.md"))

# Scoring Rules
TAG_SCORES = {
    '涨停': -100,
    '3倍量': 300,
    '2倍量': 200,
    '60日地量': 600,
    '30日地量': 300,
    '20日地量': 200,
    '10日地量': 100,
    '5日地量': 50
}

TABLES_TO_CLEAR = [
    "wencai_stocks", "monitor_list", "stock_info", "stock_daily",
    "stock_daily_temp", "stock_volume_baseline", "stock_tag_relations",
    "stock_score_results", "volume_analysis_results", "alert_records",
    "wencai_data_dedup", "stock_concepts"
]

class MemoryScorer:
    def __init__(self, stock_data_manager):
        self.data_manager = stock_data_manager
        self.cache = {}  # code -> dataframe

    async def load_data(self, code):
        if code in self.cache:
            return self.cache[code]
        
        # Check if local file exists and has enough data
        csv_path = self.data_manager._get_csv_path(code)
        need_sync = True
        
        if os.path.exists(csv_path):
             try:
                 # Read first few lines to check
                 df = pd.read_csv(csv_path)
                 if len(df) > 250:
                     need_sync = False
             except:
                 pass
        
        if need_sync:
             logger.info(f"Syncing data for {code}...")
             # Fetch history starting from 2024 to ensure coverage for 250-day window in late 2025
             await self.data_manager.get_stock_data(code, start_date=date(2024, 1, 1), end_date=END_DATE, sync_if_missing=True)
        
        # Now load
        df = self.data_manager._load_local_data(code)
        if df.empty:
            logger.warning(f"Data for {code} is empty after sync attempt!")
            return None
        else:
            if code == '603601':
                logger.info(f"Loaded {len(df)} rows for 603601. Date range: {df['trade_date'].min()} to {df['trade_date'].max()}")
            
        # Ensure date column and types
        if 'trade_date' in df.columns:
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.date
        
        # Ensure numeric columns
        cols = ['vol', 'close', 'high', 'low', 'open']
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Sort
        df = df.sort_values('trade_date')
        self.cache[code] = df
        return df

    def calculate_score(self, df, target_date):
        """
        Calculate 250-day cumulative score for target_date.
        """
        if df is None or df.empty:
            return 0
            
        # Filter data up to target_date
        mask = df['trade_date'] <= target_date
        valid_df = df[mask]
        
        if valid_df.empty:
            return 0
            
        # We need enough history to calculate tags (max lookback 60) for the 250-day window
        # Window = last 250 rows of valid_df
        # Calculation Base = Window + 60 rows before
        
        window_size = 250
        lookback = 65 # 60 + margin
        
        required_len = window_size + lookback
        
        if len(valid_df) < 2:
            return 0
            
        calc_df = valid_df.tail(required_len).copy()
        
        # Prepare shifts
        calc_df['prev_vol'] = calc_df['vol'].shift(1)
        calc_df['prev_close'] = calc_df['close'].shift(1)
        
        # Initialize scores series
        scores = pd.Series(0.0, index=calc_df.index)
        
        # 1. Volume Multiplier
        # Avoid division by zero
        mask_valid_vol = (calc_df['prev_vol'] > 0)
        vol_ratio = pd.Series(0.0, index=calc_df.index)
        vol_ratio[mask_valid_vol] = calc_df.loc[mask_valid_vol, 'vol'] / calc_df.loc[mask_valid_vol, 'prev_vol']
        
        scores[vol_ratio >= 3.0] += TAG_SCORES['3倍量']
        scores[(vol_ratio >= 2.0) & (vol_ratio < 3.0)] += TAG_SCORES['2倍量']
        
        # 2. Limit Up
        mask_valid_close = (calc_df['prev_close'] > 0)
        pct_chg = pd.Series(0.0, index=calc_df.index)
        pct_chg[mask_valid_close] = (calc_df.loc[mask_valid_close, 'close'] - calc_df.loc[mask_valid_close, 'prev_close']) / calc_df.loc[mask_valid_close, 'prev_close']
        
        scores[pct_chg > 0.095] += TAG_SCORES['涨停']
        
        # 3. Low Volume
        # Logic: 60 > 30 > 20 > 10 > 5
        
        # Logic adapted from VolumeAnalysisService.calculate_scores_batch
        # Calculate rolling minimums on PREVIOUS volume
        min_60 = calc_df['prev_vol'].rolling(window=60).min()
        min_30 = calc_df['prev_vol'].rolling(window=30).min()
        min_20 = calc_df['prev_vol'].rolling(window=20).min()
        min_10 = calc_df['prev_vol'].rolling(window=10).min()
        min_5  = calc_df['prev_vol'].rolling(window=5).min()
        
        # Create masks
        mask_60 = (calc_df['vol'] <= min_60) & (calc_df['vol'] > 0)
        mask_30 = (calc_df['vol'] <= min_30) & (~mask_60) & (calc_df['vol'] > 0)
        mask_20 = (calc_df['vol'] <= min_20) & (~mask_60) & (~mask_30) & (calc_df['vol'] > 0)
        mask_10 = (calc_df['vol'] <= min_10) & (~mask_60) & (~mask_30) & (~mask_20) & (calc_df['vol'] > 0)
        mask_5  = (calc_df['vol'] <= min_5) & (~mask_60) & (~mask_30) & (~mask_20) & (~mask_10) & (calc_df['vol'] > 0)
        
        # Debug for 603601
        if code == '603601':
            logger.info(f"DEBUG {code} {current_date}: Vol={calc_df['vol'].iloc[-1]}, Min60={min_60.iloc[-1]}, Min5={min_5.iloc[-1]}")
            logger.info(f"DEBUG {code} Masks: 60={mask_60.iloc[-1]}, 30={mask_30.iloc[-1]}, 5={mask_5.iloc[-1]}")
        
        scores[mask_60] += TAG_SCORES['60日地量']
        scores[mask_30] += TAG_SCORES['30日地量']
        scores[mask_20] += TAG_SCORES['20日地量']
        scores[mask_10] += TAG_SCORES['10日地量']
        scores[mask_5]  += TAG_SCORES['5日地量']
        
        # Sum only the last 250 days (or fewer if not enough data)
        window_scores = scores.tail(window_size)
        
        return window_scores.sum()

async def main():
    logger.add("acceptance_final.log", rotation="10 MB")
    
    # Init DB
    await db_manager.initialize()
    
    # 2. Init components
    stock_data_manager = StockDataManager(db_manager)

    # 1. Clear Data
    logger.info("Clearing data...")
    try:
        async with db_manager.session_factory() as session:
            # Disable foreign key checks for MySQL/MariaDB
            await session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            
            for table in TABLES_TO_CLEAR:
                try:
                    await session.execute(text(f"TRUNCATE TABLE {table}"))
                    logger.info(f"Truncated {table}")
                except Exception as e:
                    logger.warning(f"Failed to truncate {table}, trying delete: {e}")
                    try:
                        await session.execute(text(f"DELETE FROM {table}"))
                    except Exception as e2:
                        logger.error(f"Failed to delete {table}: {e2}")
            
            await session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            await session.commit()

        # Clear CSVs for targets to force fresh sync
        for code in ['603601']:
            csv_path = stock_data_manager._get_csv_path(code)
            if os.path.exists(csv_path):
                os.remove(csv_path)
                logger.info(f"Deleted CSV for {code}")

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        
    logger.info("Data cleared.")
    
    # WencaiCrawler needs a session
    async with db_manager.session_factory() as session:
        crawler = WencaiCrawler(session)
        scorer = MemoryScorer(stock_data_manager)
        
        report_lines = []
        report_lines.append("# 603601 验收报告 (Final)")
        report_lines.append(f"生成时间: {datetime.now()}")
        report_lines.append("")
        report_lines.append("| 日期 | 603601积分 | 603601排名 |")
        report_lines.append("|---|---|---|")
        
        os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
        
        # 3. Loop Dates
        current_date = START_DATE
        while current_date <= END_DATE:
            date_str = current_date.strftime("%Y-%m-%d")
            logger.info(f"Processing {date_str}...")
            
            prev_date = current_date - timedelta(days=1)
            query = (
                f"{current_date.year}年{current_date.month}月{current_date.day}日成交量是"
                f"{prev_date.year}年{prev_date.month}月{prev_date.day}日成交量的2.8倍以上，"
                f"非北交 非创业版，非科创版，非ST，概念 行业，"
                f"{prev_date.year}年{prev_date.month}月{prev_date.day}日和"
                f"{current_date.year}年{current_date.month}月{current_date.day}日涨幅低于11% 收盘价低于25"
            )
            
            # logger.info(f"Query: {query}")
            
            stocks = []
            try:
                # Use fetch_and_parse with timeout
                logger.info(f"Crawling Wencai for {date_str}...")
                try:
                    result = await asyncio.wait_for(crawler.fetch_and_parse(query), timeout=60.0)
                    stocks = result.get('stocks', [])
                    logger.info(f"Crawled {len(stocks)} stocks.")
                except asyncio.TimeoutError:
                    logger.error(f"Crawler timed out for {date_str}")
            except Exception as e:
                logger.error(f"Crawler failed for {date_str}: {e}")
                
            stock_codes = [s.get('stock_code') or s.get('code') for s in stocks if s.get('stock_code') or s.get('code')]
            
            # Add targets
            targets = ['603601']
            all_codes = list(set(stock_codes + targets))
            
            # Calculate scores
            scores = []
            for i, code in enumerate(all_codes):
                if i % 50 == 0:
                    logger.info(f"Scoring {i}/{len(all_codes)}...")
                try:
                    df = await scorer.load_data(code)
                    score = scorer.calculate_score(df, current_date)
                    scores.append({'code': code, 'score': score})
                except Exception as e:
                    # logger.error(f"Error scoring {code}: {e}")
                    scores.append({'code': code, 'score': 0})
            
            # Sort
            scores.sort(key=lambda x: x['score'], reverse=True)
            
            # Find ranks
            rank_603601 = "-"
            score_603601 = 0
            
            for idx, item in enumerate(scores):
                if item['code'] == '603601':
                    rank_603601 = idx + 1
                    score_603601 = item['score']
            
            line = f"| {date_str} | {score_603601} | {rank_603601} |"
            report_lines.append(line)
            logger.info(f"Report Line: {line}")
            
            # Incremental Save
            with open(REPORT_FILE, 'w') as f:
                f.write('\n'.join(report_lines))
                
            current_date += timedelta(days=1)
            await asyncio.sleep(3)

    logger.info("Done!")

if __name__ == "__main__":
    asyncio.run(main())
