
import asyncio
import os
import sys
import pandas as pd
from datetime import datetime, date
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Project Modules
from app.database import db_manager
from app.models.stock_daily import StockDaily
from app.models.stock import StockInfo
from app.services.pathway_vectorized_engine import PathwayVectorizedEngine

# Load Environment
load_dotenv()

# Configure Pandas display
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

class PathwayOptimizer:
    def __init__(self):
        # self.engine = create_async_engine(DATABASE_URL, echo=False)
        # self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        self.pathway_engine = PathwayVectorizedEngine() # Will attach session later
        
        # Target Date Range
        self.start_date = date(2025, 11, 20)
        self.end_date = date(2025, 12, 10)
        
        # Buffer for indicators (need history for MA, Volume, etc.)
        # 400 days buffer to ensure 250-day rolling score is accurate
        self.history_start_date = date(2024, 1, 1) 

    async def get_target_stocks(self):
        """Load target stocks from Wencai CSVs"""
        # Use correct path from previous test
        csv_dir = "/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/data/wencai"
        unique_codes = set()
        
        if not os.path.exists(csv_dir):
            logger.error(f"CSV Directory not found: {csv_dir}")
            return []

        for f in os.listdir(csv_dir):
            if f.endswith(".csv"):
                try:
                    # Try UTF-8 first, then GBK
                    path = os.path.join(csv_dir, f)
                    try:
                        df = pd.read_csv(path, encoding='utf-8')
                    except UnicodeDecodeError:
                        df = pd.read_csv(path, encoding='gbk')
                    
                    # Debug columns
                    # logger.info(f"File {f} columns: {df.columns.tolist()}")
                    
                    # Check for stock code column
                    code_col = None
                    for col in df.columns:
                        if '股票代码' in col or 'code' in col.lower():
                            code_col = col
                            break
                    
                    if code_col:
                        for raw in df[code_col].astype(str):
                            raw = raw.strip()
                            if not raw or raw == 'nan': continue
                            
                            if '.' not in raw:
                                if raw.startswith('6'): raw += '.SH'
                                elif raw.startswith('0') or raw.startswith('3'): raw += '.SZ'
                                elif raw.startswith('4') or raw.startswith('8'): raw += '.BJ'
                            unique_codes.add(raw)
                    else:
                        logger.warning(f"No stock code column found in {f}")

                except Exception as e:
                    logger.error(f"Error reading {f}: {e}")
        
        logger.info(f"Found {len(unique_codes)} unique stocks in CSVs")
        return list(unique_codes)

    async def load_stock_data(self, session, codes):
        """Load ALL daily data for these stocks into a DataFrame"""
        logger.info(f"Loading history for {len(codes)} stocks from {self.history_start_date}...")
        
        # Chunking if too many codes
        chunk_size = 50
        all_dfs = []
        
        for i in range(0, len(codes), chunk_size):
            chunk = codes[i:i+chunk_size]
            stmt = select(
                StockDaily.code, 
                StockDaily.trade_date, 
                StockDaily.open, 
                StockDaily.close, 
                StockDaily.high, 
                StockDaily.low, 
                StockDaily.vol
            ).where(
                StockDaily.code.in_(chunk),
                StockDaily.trade_date >= self.history_start_date
            ).order_by(StockDaily.trade_date.asc())
            
            result = await session.execute(stmt)
            rows = result.fetchall()
            if rows:
                df = pd.DataFrame(rows, columns=['code', 'trade_date', 'open', 'close', 'high', 'low', 'vol'])
                all_dfs.append(df)
            
            logger.info(f"Loaded chunk {i//chunk_size + 1}/{(len(codes)-1)//chunk_size + 1}")

        if not all_dfs:
            return pd.DataFrame()
            
        return pd.concat(all_dfs, ignore_index=True)

    async def run(self):
        async with db_manager.get_session() as session:
            self.pathway_engine.db_session = session
            await self.pathway_engine._ensure_tag_scores()
            
            # 1. Get Stocks
            stocks = await self.get_target_stocks()
            if not stocks:
                logger.warning("No stocks found in Wencai CSVs")
                return

            # 2. Load Data (One BIG Query/Chunks)
            df_all = await self.load_stock_data(session, stocks)
            if df_all.empty:
                logger.error("No data found in DB")
                return

            # 3. Vectorized Calculation
            logger.info("Starting Vectorized Calculation...")
            
            final_results = {} # Date -> List of dicts
            
            # Group by Stock Code
            grouped = df_all.groupby('code')
            
            count = 0
            for code, df_stock in grouped:
                # Calculate for this stock
                df_res = self.pathway_engine.calculate_batch(df_stock)
                
                # Filter for target date range
                mask_range = (df_res['trade_date'] >= self.start_date) & (df_res['trade_date'] <= self.end_date)
                df_target = df_res.loc[mask_range]
                
                for _, row in df_target.iterrows():
                    d_str = row['trade_date'].strftime('%Y-%m-%d')
                    if d_str not in final_results:
                        final_results[d_str] = []
                    
                    final_results[d_str].append({
                        'code': code,
                        'score': row['total_score'],
                        'daily_score': row['daily_score'],
                        'close': row['close'],
                        'tags': row['tags_str']
                    })
                
                count += 1
                if count % 10 == 0:
                    logger.info(f"Processed {count} stocks")

            # 4. Generate Report
            self.generate_report(final_results)

    def generate_report(self, daily_results):
        report_dir = "/Users/mac/StudioProjects/open-citycloud/.trae/documents/2026-01-10"
        os.makedirs(report_dir, exist_ok=True)
        excel_path = os.path.join(report_dir, "pathway_optimized_top20.xlsx")
        
        logger.info(f"Generating Excel at {excel_path}")
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Sort keys (dates)
            sorted_dates = sorted(daily_results.keys())
            
            for d_str in sorted_dates:
                items = daily_results[d_str]
                # Sort by Total Score Desc
                items.sort(key=lambda x: x['score'], reverse=True)
                
                # Top 20
                top20 = items[:20]
                
                # Add Rank
                for idx, item in enumerate(top20):
                    item['rank'] = idx + 1
                
                df = pd.DataFrame(top20)
                # Rename cols for display
                df = df.rename(columns={
                    'rank': 'Rank',
                    'code': 'Stock Code',
                    'score': 'Total Score',
                    'daily_score': 'Daily Score',
                    'close': 'Close Price',
                    'tags': 'Tags'
                })
                
                df.to_excel(writer, sheet_name=d_str, index=False)
                
        logger.info("✅ Report Generated Successfully!")

if __name__ == "__main__":
    runner = PathwayOptimizer()
    try:
        asyncio.run(runner.run())
    except KeyboardInterrupt:
        pass
