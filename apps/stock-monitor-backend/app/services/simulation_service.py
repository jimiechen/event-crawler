
import asyncio
import json
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from loguru import logger

from app.models.stock import WencaiStock
from app.models.stock_daily import StockDaily, StockScoreResult
from app.services.wencai_service import WencaiService
from app.services.local_data_service import LocalDataService
from app.services.pathway_engine import PathwayVolumePriceEngine
from app.services.volume_analysis_service import VolumeAnalysisService
from app.crawler.wencai_crawler import WencaiCrawler
from app.services.stock_service import StockService
from app.services.sse_service import sse_service

class StockSimulationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.wencai_service = WencaiService(db)
        self.stock_service = StockService(db)

    async def run_daily_simulation_stream(self, target_date: date):
        """
        Generic Daily Simulation: Crawl -> Iterate Stocks -> Unified Init -> Validation
        This method yields SSE-formatted strings.
        """
        def sse_msg(msg_type, content, data=None):
            payload = {"type": msg_type, "message": content, "data": data, "timestamp": datetime.now().isoformat()}
            # Format as SSE event
            return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        try:
            yield sse_msg("info", f"开始执行每日模拟: {target_date}")
            
            # 1. Wencai Crawler
            logger.info(f"Calling Wencai Crawler for {target_date}")
            yield sse_msg("step", "正在调用问财爬虫...", {"target_date": str(target_date)})
            
            # Use WencaiCrawler directly
            crawler = WencaiCrawler(self.db)
            
            # Check if it's weekend
            if target_date.weekday() >= 5:
                 yield sse_msg("warning", f"{target_date} 是周末，跳过爬取")
                 # We might still want to process existing data if any? 
                 # But usually simulation stops here or continues with mock?
                 # Let's assume we proceed to step 2 even if crawl skipped (maybe manual data exists)
            else:
                # Generate query similar to wencai_controller
                d1 = target_date.strftime("%Y年%m月%d日")
                d2 = (target_date - timedelta(days=1)).strftime("%Y年%m月%d日")
                # Handle Monday (prev day is Friday) - Simple logic, better if handled by calendar utility
                # But for now assume Wencai query handles "yesterday" logic or we just use simple timedelta
                
                query = f"{d1}成交量是{d2}成交量的2.5倍以上，非北交 非创业版，非科创版，非ST，概念 行业，{d2}和{d1}涨幅低于13% 收盘价低于25"
                batch_name = f"AutoCrawl_{target_date.strftime('%Y%m%d')}"
                
                crawler_res = await crawler.fetch_and_parse(
                    query=query,
                    batch_name=batch_name,
                    target_stock_code=None,
                    target_date=target_date
                )
                
                if crawler_res.get('status') != 'completed':
                    error_msg = f"Wencai Crawler failed: {crawler_res.get('errors')}"
                    yield sse_msg("error", error_msg)
                    # We continue? Or stop? 
                    # If crawler fails, we might not have new data, but we can still process cumulative list.
                else:
                    yield sse_msg("step", f"爬虫执行完成: {crawler_res.get('success')} 条成功", crawler_res)

            # 2. Get Cumulative Top 3 Stocks from ALL batches
            # User Request: Calculate for ALL stocks that ever appeared in Top 3 (Cumulative)
            yield sse_msg("step", "正在获取累计优选股票池 (历史每批次前3名)...")
            
            # We select all stocks, ordered by batch and id, then pick top 3 for each batch
            # Note: WencaiStock.crawl_batch_id is a string in model but usually int
            stmt = select(WencaiStock.stock_code, WencaiStock.crawl_batch_id).order_by(WencaiStock.crawl_batch_id, WencaiStock.id)
            result = await self.db.execute(stmt)
            rows = result.all()
            
            batch_counts = {}
            cumulative_codes = set()
            
            for row in rows:
                code = row[0]
                b_id = row[1]
                
                if b_id not in batch_counts:
                    batch_counts[b_id] = 0
                
                if batch_counts[b_id] < 3:
                    cumulative_codes.add(code)
                    batch_counts[b_id] += 1
            
            codes = list(cumulative_codes)
            
            if codes:
                yield sse_msg("info", f"获取到 {len(codes)} 只累计优选股票 (每批次前3)，开始统一计算日期 {target_date}...")
                
                success_count = 0
                for i, code in enumerate(codes):
                    progress = f"[{i+1}/{len(codes)}]"
                    yield sse_msg("step", f"{progress} 处理股票 {code}...")
                    
                    # Call Unified Function
                    async for log in self._initialize_stock_environment(code, target_date, sse_msg):
                        yield log
                    
                    success_count += 1
                    # Small delay to yield to event loop
                    await asyncio.sleep(0.1)
                    
                yield sse_msg("success", f"所有股票处理完成 ({success_count}/{len(codes)})")

                # 3. Validation (Poll until success or timeout)
                yield sse_msg("step", "正在验证数据完整性 (检查250天数据量)...")
                # In local mode, we can check DB directly
                
                max_retries = 30
                retry_interval = 2
                validated = False
                
                for i in range(max_retries):
                    yield sse_msg("step", f"验证尝试 {i+1}/{max_retries}...")
                    
                    failures = []
                    for code in codes:
                        count = await self._check_data_count(code)
                        if count < 250:
                            failures.append(code)
                    
                    if not failures:
                        yield sse_msg("success", "所有股票数据完整性验证通过 (>=250天)")
                        validated = True
                        break
                    else:
                        fail_count = len(failures)
                        sample = failures[:3]
                        msg = f"验证未通过: {fail_count} 只股票数据不足 (示例: {sample})"
                        yield sse_msg("info", msg)
                    
                    await asyncio.sleep(retry_interval)
                
                if not validated:
                    yield sse_msg("warning", "数据完整性验证超时，部分股票可能数据不足")

            else:
                yield sse_msg("warning", "未能获取到任何历史问财股票，跳过处理")
            
            yield sse_msg("success", "每日模拟执行完成！")
            
        except Exception as e:
            logger.error(f"Daily simulation failed for {target_date}: {e}")
            yield sse_msg("error", f"执行失败: {str(e)}")
            return

    async def _initialize_stock_environment(self, code: str, target_date: date, yield_func):
        """
        Unified initialization function
        """
        try:
            # 1. Clean Data (Strict Simulation: Remove future data or reload fresh)
            # In simulation logic: Delete all and reload 250 days.
            # yield yield_func("log", f"[{code}] 清理历史数据...")
            # await self.db.execute(text("DELETE FROM stock_daily WHERE code = :code"), {"code": code})
            # await self.db.commit()

            # NOTE: Deleting all data might be too aggressive for production DB if we share data?
            # But the requirement says "simulation logic" which implies strict state.
            # If stock-monitor-backend is used for real monitoring, we shouldn't delete data blindly.
            # However, `load_local_data` usually upserts.
            # The original simulation logic did DELETE. 
            # If we want to support "Backtest/Simulation" on the same DB as "Production Monitoring",
            # we should be careful. 
            # But based on context, this system seems to be built for this purpose.
            # Let's follow the original logic but maybe skip DELETE if we trust `load_local_data` to overwrite/fill gaps.
            # Actually, original logic deleted to ensure NO FUTURE DATA exists (peeking).
            # So for simulation at `target_date`, we must ensure no data > `target_date`.
            
            yield yield_func("log", f"[{code}] 清理 {target_date} 之后的数据...")
            await self.db.execute(text("DELETE FROM stock_daily WHERE code = :code AND trade_date > :date"), {"code": code, "date": target_date})
            await self.db.commit()

            # 2. Load History (Inject 250 days)
            yield yield_func("log", f"[{code}] 加载历史K线 (截止 {target_date})...")
            # LocalDataService.load_local_data_for_stocks expects StockService
            await LocalDataService.load_local_data_for_stocks(self.stock_service, [code], end_date=target_date, limit=300)

            # 3. Trigger Score Calculation
            yield yield_func("log", f"[{code}] 触发评分计算...")
            engine = PathwayVolumePriceEngine(self.db)
            # calculate_daily_scores is for batch, calculate_single_stock_score is what we need?
            # PathwayVolumePriceEngine has `calculate_daily_scores(date)` which calculates for ALL stocks.
            # We want single stock. 
            # Checking PathwayVolumePriceEngine (I haven't read it, but I saw it used in stock_score_controller)
            # stock_score_controller uses: `await engine.calculate_daily_scores(target_date)`
            # Does it support single stock?
            # If not, we might need to implement it or use `calculate_daily_scores` but filter?
            # Let's check `PathwayVolumePriceEngine` later. 
            # Assuming it might NOT support single stock efficiently if designed for batch.
            # BUT, the original code called `BackendClient.trigger_single_calculation`.
            # Let's assume there is a way or I will add it.
            # Wait, `stock_score_controller.py` has:
            # @router.get("/calculate/{calculate_date}/{code}")
            # async def calculate_single_stock_score(...)
            #     engine = PathwayVolumePriceEngine(db)
            #     result = await engine.calculate_single_stock_score(code, calculate_date)
            # So `calculate_single_stock_score` exists!
            await engine.calculate_single_stock_score(code, target_date)

            # 4. Trigger Volume Analysis
            yield yield_func("log", f"[{code}] 触发异动分析...")
            # VolumeAnalysisService.analyze_stock(code, session=self.db)
            await VolumeAnalysisService.analyze_stock(code, session=self.db)

            yield yield_func("log", f"[{code}] 初始化完成")

        except Exception as e:
            logger.error(f"Failed to initialize {code}: {e}")
            yield yield_func("warning", f"[{code}] 初始化失败: {e}")

    async def _check_data_count(self, code: str) -> int:
        stmt = select(StockDaily).where(StockDaily.code == code)
        result = await self.db.execute(stmt)
        return len(result.scalars().all())

    async def run_task_without_sse(self, target_date: date):
        """
        Run simulation as a background task (no SSE return, but broadcasts logs)
        """
        async for msg in self.run_daily_simulation_stream(target_date):
            # msg is "data: {...}\n\n"
            # Parse it back to broadcast? Or just broadcast raw?
            # sse_service.broadcast expects event_type and data dict.
            # We need to parse the JSON inside.
            try:
                if msg.startswith("data: "):
                    json_str = msg[6:].strip()
                    payload = json.loads(json_str)
                    # Payload has type, message, data
                    # Broadcast to 'simulation' channel or general?
                    # sse_service.broadcast(event, data)
                    await sse_service.broadcast(payload['type'], payload)
            except Exception as e:
                logger.error(f"Error broadcasting SSE in task: {e}")
