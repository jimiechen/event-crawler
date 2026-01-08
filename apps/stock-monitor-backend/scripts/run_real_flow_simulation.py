import asyncio
import os
import sys
import logging
import datetime
from decimal import Decimal
from typing import List, Dict, Any

import pandas as pd
import akshare as ak
from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_manager
from app.models.base import Base
from app.models.stock import WencaiStock, StockInfo
from app.models.stock_daily import StockDailyTemp
from app.models.pattern_config import PatternStockPool, PatternConfig
from app.services.pattern_analysis_service import PatternAnalysisService
from app.services.tag_management_service import TagManagementService
from app.api.tag_schemas import TagCreate

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("real_flow_simulation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
DB_URL = "sqlite+aiosqlite:///./stock_monitor_simulation.db"  # Use separate DB for simulation
TARGET_STOCKS = ["600519", "000001", "000858", "601318", "002594", "300750", "600036", "002415", "600276", "600030",
                 "000725", "601166", "601398", "601288", "601939", "601988", "600000", "600016", "600019", "600028",
                 "600048", "600050", "600104", "600585", "600690", "600887", "601088", "601186", "601328", "601601",
                 "601628", "601668", "601688", "601800", "601818", "601857", "601888", "601899", "601998", "603288",
                 "000002", "000333", "000538", "000625", "000651", "000776", "002027", "002304", "002475", "002714"]

async def init_db(engine):
    """Initialize Database Tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized.")

async def mock_wencai_crawl(session: AsyncSession, date_str: str, stock_codes: List[str]) -> str:
    """
    Mock Wencai Crawl: Fetch history from AkShare and insert into wencai_stocks
    Returns: batch_id
    """
    batch_id = f"mock_batch_{date_str.replace('-', '')}"
    logger.info(f"[{date_str}] Starting mock Wencai crawl for batch {batch_id}...")
    
    tasks = []
    for code in stock_codes:
        tasks.append(fetch_stock_day_data(code, date_str))
    
    results = await asyncio.gather(*tasks)
    
    wencai_entries = []
    for res in results:
        if res:
            # Mock some Wencai-specific fields
            wencai_entry = WencaiStock(
                stock_code=res['code'],
                stock_name=res['name'],
                current_price=Decimal(str(res['close'])),
                volume=int(res['volume']),
                crawl_batch_id=batch_id,
                concept="TestConcept",
                industry="TestIndustry",
                raw_data="{}"
            )
            session.add(wencai_entry)
            wencai_entries.append(wencai_entry)
            
            # Ensure StockInfo exists (required for TagManagement)
            stmt = select(StockInfo).where(StockInfo.code == res['code'])
            existing_info = (await session.execute(stmt)).scalar_one_or_none()
            if not existing_info:
                info = StockInfo(
                    code=res['code'],
                    name=res['name'],
                    market="sh" if res['code'].startswith("6") else "sz",
                    source="wencai"
                )
                session.add(info)
    
    await session.commit()
    logger.info(f"[{date_str}] Mock crawl finished. Inserted {len(wencai_entries)} records into wencai_stocks.")
    return batch_id

async def fetch_stock_day_data(code: str, date_str: str) -> Dict[str, Any]:
    """Fetch single day data from AkShare (Helper)"""
    try:
        symbol = code
        # Fetch a small window around the date to ensure we get data
        # AkShare history format: YYYYMMDD
        target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        start_date = (target_date - datetime.timedelta(days=10)).strftime("%Y%m%d")
        end_date = target_date.strftime("%Y%m%d")
        
        df = await asyncio.to_thread(
            ak.stock_zh_a_hist, 
            symbol=symbol, 
            period="daily", 
            start_date=start_date, 
            end_date=end_date, 
            adjust="qfq"
        )
        
        if df.empty:
            return None
            
        # Get exact date or nearest previous date (simulation logic)
        df['日期'] = pd.to_datetime(df['日期'])
        mask = df['日期'] <= target_date
        df_filtered = df[mask]
        
        if df_filtered.empty:
            return None
            
        row = df_filtered.iloc[-1]
        
        # Check if it's too old (e.g. suspension)
        if (target_date - row['日期']).days > 5:
            return None
            
        return {
            "code": code,
            "name": f"Stock-{code}", # Akshare hist doesn't return name easily here, using mock
            "close": row['收盘'],
            "open": row['开盘'],
            "high": row['最高'],
            "low": row['最低'],
            "volume": row['成交量'],
            "turnover": row['成交额'] if '成交额' in row else 0,
            "turnover_rate": row['换手率'] if '换手率' in row else 0,
            "date": row['日期'].date()
        }
    except Exception as e:
        logger.warning(f"Failed to fetch {code}: {e}")
        return None

async def sync_wencai_to_temp_pool(session: AsyncSession, batch_id: str, pattern_service: PatternAnalysisService):
    """
    Step 2: Transform wencai_stocks to stock_daily_temp (Integration Logic)
    """
    stmt = select(WencaiStock).where(WencaiStock.crawl_batch_id == batch_id)
    wencai_stocks = (await session.execute(stmt)).scalars().all()
    
    if not wencai_stocks:
        logger.warning(f"No stocks found for batch {batch_id}")
        return

    temp_data_list = []
    for ws in wencai_stocks:
        # Note: WencaiStock only has current snapshot. 
        # For PatternAnalysis, we actually need HISTORY.
        # In the real system, 'save_temp_data' usually triggers a history fetch or assumes history exists.
        # Here, PatternAnalysisService.perform_screening() -> analyze_history_and_score() -> fetch_history()
        # So we just need to put the 'trigger' data into stock_daily_temp.
        
        # We need to map WencaiStock fields to StockDailyTemp
        # Since WencaiStock lacks O/H/L for the specific day in our simple model (it has them but we need to ensure types),
        # we will trust what we put in (which came from AkShare).
        
        # Wait, PatternAnalysisService.save_temp_data expects a list of dicts.
        temp_data = {
            "code": ws.stock_code,
            "trade_date": datetime.date.today(), # Placeholder, will be ignored by fetch_history likely, but important for record
            "open": float(ws.current_price or 0), # Approx
            "close": float(ws.current_price or 0),
            "high": float(ws.current_price or 0),
            "low": float(ws.current_price or 0),
            "volume": float(ws.volume or 0),
            "amount": 0.0,
            "turnover": 0.0,
            "industry": ws.industry,
            "concept": ws.concept
        }
        temp_data_list.append(temp_data)
    
    # Use the service method to save (it handles clearing old data)
    await pattern_service.save_temp_data(temp_data_list, source=f"wencai_batch_{batch_id}")
    logger.info(f"Synced {len(temp_data_list)} stocks from Wencai batch {batch_id} to Temp Pool.")

async def sqlite_compatible_save_temp_data(self, data_list: List[Dict[str, Any]], source: str = "wencai") -> int:
    """
    SQLite compatible version of save_temp_data for simulation
    """
    if not data_list:
        return 0

    try:
        # Simple Delete then Insert for SQLite
        codes = [item.get("code") for item in data_list]
        stmt = delete(StockDailyTemp).where(StockDailyTemp.code.in_(codes))
        await self.db.execute(stmt)
        
        # Insert
        for item in data_list:
            record = StockDailyTemp(
                code=item.get("code"),
                trade_date=item.get("trade_date") or datetime.date.today(),
                open=item.get("open"),
                close=item.get("close"),
                high=item.get("high"),
                low=item.get("low"),
                vol=item.get("volume"),
                amount=item.get("amount"),
                turnover_rate=item.get("turnover"),
                industry=item.get("industry"),
                concept=item.get("concept"),
                source=source,
                status="pending",
                created_at=datetime.datetime.now()
            )
            self.db.add(record)
        
        await self.db.commit()
        return len(data_list)

    except Exception as e:
        await self.db.rollback()
        logger.error(f"Error saving temp data (SQLite): {e}")
        raise e

async def run_daily_process(session: AsyncSession, date_str: str, stock_codes: List[str]):
    """Execute Full Daily Flow"""
    logger.info(f"=== Starting Process for {date_str} ===")
    
    pattern_service = PatternAnalysisService(session)
    # PATCH: Override save_temp_data for SQLite compatibility
    pattern_service.save_temp_data = lambda data, source="wencai": sqlite_compatible_save_temp_data(pattern_service, data, source)
    
    tag_service = TagManagementService(session)

    
    # 1. Mock Wencai Crawl (Data Source)
    batch_id = await mock_wencai_crawl(session, date_str, stock_codes)
    
    # 2. Sync to Temp Pool (Data Preparation)
    await sync_wencai_to_temp_pool(session, batch_id, pattern_service)
    
    # 3. Pattern Analysis (Core Logic)
    # Note: perform_screening will fetch history internally. 
    # To make it "simulate" the past, we need to hack the "today" in perform_screening?
    # Actually, perform_screening calls analyze_history_and_score.
    # We need to ensure analyze_history_and_score fetches data UP TO date_str.
    # The current implementation of fetch_history in PatternAnalysisService likely fetches "latest".
    # For simulation, we rely on the fact that we can't easily change the service code to accept "sim_date" without modifying it.
    # BUT, we can rely on our "mock_wencai_crawl" to set the scene.
    # However, PatternAnalysisService.analyze_history_and_score calls `ak.stock_zh_a_hist` directly.
    # We MUST patch it to return data only up to date_str.
    
    # We will use unittest.mock inside this function scope!
    from unittest.mock import patch
    
    # Prepare the mock for ak.stock_zh_a_hist to respect the simulation date
    original_ak_hist = ak.stock_zh_a_hist
    
    def mock_hist_func(symbol, period="daily", start_date=None, end_date=None, adjust="qfq"):
        # We ignore requested dates and enforce our simulation window
        # End date = date_str
        sim_end_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        real_end_date_str = sim_end_date.strftime("%Y%m%d")
        # Start date = 1 year ago
        real_start_date_str = (sim_end_date - datetime.timedelta(days=365)).strftime("%Y%m%d")
        
        return original_ak_hist(symbol=symbol, period=period, start_date=real_start_date_str, end_date=real_end_date_str, adjust=adjust)
    
    with patch('app.services.pattern_analysis_service.ak.stock_zh_a_hist', side_effect=mock_hist_func):
        screening_stats = await pattern_service.perform_screening()
    
    logger.info(f"[{date_str}] Screening stats: {screening_stats}")
    
    # 4. Tag Synchronization (New Requirement)
    # Fetch the actual results from PatternStockPool (or StockDailyTemp)
    # We want to tag stocks that PASSED screening TODAY.
    # We can check PatternStockPool where updated_at is recent, or query StockDailyTemp where status='passed'.
    # But StockDailyTemp might contain passed stocks from previous runs if not cleaned? 
    # Actually save_temp_data cleans/upserts based on what we passed.
    # Let's query StockDailyTemp where status='passed' AND trade_date matches (approx).
    # Better: Query PatternStockPool for stocks that were just updated.
    
    # Since we are in a simulation loop, PatternStockPool contains the "survivors".
    # But we want to tag the specific patterns found TODAY.
    # PatternStockPool.patterns stores the latest patterns.
    
    # Let's query PatternStockPool.
    stmt = select(PatternStockPool)
    all_pool = (await session.execute(stmt)).scalars().all()
    
    passed_today = []
    
    for stock in all_pool:
        # We assume if it's in the pool, it has valid patterns.
        # In a real daily run, we might filter by updated_at.
        # For simulation, we tag everyone in the pool (refresh tags).
        
        stock_code = stock.stock_code
        patterns = stock.patterns # dict or list? Model says JSON.
        if isinstance(patterns, str):
            import json
            try:
                patterns = json.loads(patterns)
            except:
                patterns = {}
        
        # If patterns is a list (old format) or dict (new format)
        # The service saves it as dict: {"pattern_code": score} or similar?
        # Let's check PatternAnalysisService._update_stock_pool.
        # It passes `patterns` from `analyze_history_and_score`.
        # `analyze_history_and_score` returns `patterns` as dict: {name: score}.
        
        if not patterns:
            continue
            
        tags_to_add = []
        
        # Add "Pattern Selected" tag
        tags_to_add.append(TagCreate(name="缠论选股", tag_type="strategy", score=0))
        
        # Add specific pattern tags
        if isinstance(patterns, dict):
            for p_name, p_score in patterns.items():
                # e.g. "底分型"
                clean_name = p_name.split('(')[0]
                tags_to_add.append(TagCreate(name=clean_name, tag_type="pattern", score=float(p_score)))
        elif isinstance(patterns, list):
             for p_str in patterns:
                 clean_name = p_str.split('(')[0]
                 tags_to_add.append(TagCreate(name=clean_name, tag_type="pattern", score=0)) # Score unknown if list
        
        if tags_to_add:
            await tag_service.add_tags_to_stock(stock_code, tags_to_add, operator="simulation")
            passed_today.append(stock_code)
            
    logger.info(f"[{date_str}] Synced tags for {len(passed_today)} stocks.")

    # 5. Pool Management
    await pattern_service._manage_pool_size()
    
    # 6. Snapshot for Report
    stmt = select(PatternStockPool).where(PatternStockPool.status == 'core')
    core_stocks = (await session.execute(stmt)).scalars().all()
    logger.info(f"[{date_str}] Core Pool Size: {len(core_stocks)}")
    
    return {
        "date": date_str,
        "processed": len(stock_codes),
        "passed": screening_stats["passed"],
        "pool_size": len(core_stocks),
        "top_stocks": ", ".join([f"{s.stock_code}({s.score})" for s in core_stocks[:5]])
    }

async def main():
    logger.info("Starting Real Flow Simulation...")
    
    engine = create_async_engine(DB_URL, echo=False)
    await init_db(engine)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    # Simulation Dates (Last 7 weekdays)
    today = datetime.date.today()
    dates = []
    curr = today
    while len(dates) < 7:
        if curr.weekday() < 5: # Mon-Fri
            dates.append(curr)
        curr -= datetime.timedelta(days=1)
    dates.reverse() # Oldest first
    
    daily_reports = []
    
    async with async_session() as session:
        # Init Configs
        service = PatternAnalysisService(session)
        await service.init_configs()
        
        for d in dates:
            date_str = d.strftime("%Y-%m-%d")
            report = await run_daily_process(session, date_str, TARGET_STOCKS)
            daily_reports.append(report)
            
        # Generate Report
        final_report = generate_markdown_report(daily_reports, session)
        with open("real_flow_report.md", "w") as f:
            f.write(final_report)
            
    await engine.dispose()
    logger.info("Simulation Completed. Report generated: real_flow_report.md")

def generate_markdown_report(daily_reports, session):
    # (Simplified report generation)
    md = "# 真实流程仿真报告 (Real Flow Simulation)\n\n"
    md += "本次仿真模拟了完整的业务链路：\n"
    md += "1. **问财抓取 (Mock)**: 模拟每日从问财获取股票列表。\n"
    md += "2. **数据清洗**: 存入临时表 `stock_daily_temp`。\n"
    md += "3. **深度分析**: 结合历史K线进行缠论量价分析。\n"
    md += "4. **标签同步**: 将分析结果（如底分型）写入系统标签库。\n"
    md += "5. **优胜劣汰**: 动态管理股票池。\n\n"
    
    md += "## 每日执行概览\n\n"
    md += "| 日期 | 处理数量 | 命中形态 | 核心池大小 | Top 5 股票 |\n"
    md += "|---|---|---|---|---|\n"
    for r in daily_reports:
        md += f"| {r['date']} | {r['processed']} | {r['passed']} | {r['pool_size']} | {r['top_stocks']} |\n"
        
    return md

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
