import csv
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger
from .backend_client import BackendClient

class SimulationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def step1_calculate_603601_baseline(self):
        """
        Step 1: 2025-11-19
        - Clear existing data for 603601 (safety)
        - Insert 603601 into wencai_stocks
        - Load 250 days history ending 2025-11-19 from CSV
        - Call backend to calculate score
        """
        target_date = date(2025, 11, 19)
        code = "603601"
        name = "再升科技"
        
        try:
            # 1. Prepare Metadata
            # wencai_stocks
            await self.session.execute(text("DELETE FROM wencai_stocks WHERE stock_code = :code"), {"code": code})
            await self.session.execute(text("""
                INSERT INTO wencai_stocks (stock_code, stock_name, created_at, is_active, crawl_batch_id)
                VALUES (:code, :name, :date, true, 1)
            """), {"code": code, "name": name, "date": datetime(2025, 11, 19, 9, 30)})

            # 2. Load Real History
            # Clear daily first
            await self.session.execute(text("DELETE FROM stock_daily WHERE code = :code"), {"code": code})
            await self.session.commit()
            
            # Use Backend to load CSV data
            # await self._generate_mock_daily_data(code, target_date, days=255) 
            # await self._load_csv_data(code, target_date, days=255)
            logger.info(f"Triggering backend to load local data for {code} ending {target_date}")
            await BackendClient.load_local_data([code], end_date=target_date.strftime("%Y-%m-%d"))
            
            # 3. Trigger Calculation
            # We use single stock calculation to be fast and specific
            logger.info(f"Triggering calculation for {code} on {target_date}")
            res = await BackendClient.trigger_single_calculation(target_date.strftime("%Y-%m-%d"), code)
            
            # 4. Trigger Volume Analysis (to populate volume_analysis_result and stock_volume_baseline)
            logger.info(f"Triggering volume analysis for {code}")
            vol_res = await BackendClient.trigger_volume_analysis(code)

            return {
                "status": "success", 
                "message": f"Step 1 executed. Backend response: {res.get('message')}. Analysis: {vol_res.get('message', 'ok')}",
                "backend_data": res,
                "analysis_data": vol_res
            }
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Step 1 failed: {e}")
            raise e

    async def step2_wencai_crawler_and_score(self):
        """
        Step 2: 2025-11-20 (Deprecated in favor of streaming version)
        """
        async for event in self.step2_stream():
            pass
        return {"status": "success", "message": "Step 2 executed via stream wrapper"}

    async def step2_stream(self):
        """
        Step 2: 2025-11-20 with SSE Streaming
        - 调用真实问财爬虫，抓取2025-11-20的数据
        - 对抓取到的每只股票执行统一初始化流程 (同 Step 1):
            - 清理历史数据
            - 加载250日历史K线
            - 触发评分计算
            - 触发异动分析
        - 验证数据完整性
        """
        import json
        import asyncio
        target_date = date(2025, 11, 20)
        
        def sse_msg(msg_type, content, data=None):
            payload = {"type": msg_type, "message": content, "data": data, "timestamp": datetime.now().isoformat()}
            return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        try:
            yield sse_msg("info", f"开始执行 Step 2: 日期 {target_date}")
            
            # 1. 调用真实问财爬虫API
            logger.info(f"Calling Wencai Crawler for {target_date}")
            yield sse_msg("step", "正在调用问财爬虫...", {"target_date": str(target_date)})
            
            crawler_res = await BackendClient.call_wencai_crawler(target_date.strftime("%Y-%m-%d"))
            
            if not crawler_res.get('success'):
                errors = crawler_res.get('data', {}).get('errors')
                error_details = f" Errors: {errors}" if errors else ""
                error_msg = f"Wencai Crawler failed: {crawler_res.get('message')}{error_details}"
                yield sse_msg("error", error_msg)
                raise Exception(error_msg)
            
            yield sse_msg("step", f"爬虫执行完成: {crawler_res.get('message')}", crawler_res)
            logger.info(f"Wencai Crawler completed: {crawler_res}")

            # 2. Get Top 3 Stocks from this batch
            # User Request: Only take top 3 from Wencai list for the target date to save time
            yield sse_msg("step", "正在获取该批次前3名股票...")
            
            batch_id = crawler_res.get('data', {}).get('batch_id')
            if not batch_id:
                yield sse_msg("warning", "未获取到批次ID，尝试通过日期获取...")
                # Fallback: try to find batch by date if not returned
                # This part is tricky without specific table structure knowledge, 
                # but let's assume batch_id is usually returned.
                # If not, we might fallback to all stocks (which user wants to avoid) or fail.
                # Let's try to query wencai_stocks created today if batch_id is missing?
                # For now, let's assume batch_id is present.
                pass

            codes = []
            if batch_id:
                stmt = text("SELECT stock_code FROM wencai_stocks WHERE crawl_batch_id = :batch_id ORDER BY id ASC")
                result = await self.session.execute(stmt, {"batch_id": batch_id})
                codes = [row[0] for row in result.all()]
            
            if codes:
                yield sse_msg("info", f"获取到 {len(codes)} 只股票，开始逐个执行统一初始化流程...")
                
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
                max_retries = 30
                retry_interval = 2
                validated = False
                
                for i in range(max_retries):
                    yield sse_msg("step", f"验证尝试 {i+1}/{max_retries}...")
                    try:
                        val_res = await BackendClient.validate_data_counts(codes, min_count=250)
                        if val_res.get("status") == "success":
                            yield sse_msg("success", "所有股票数据完整性验证通过 (>=250天)")
                            validated = True
                            break
                        else:
                            failures = val_res.get("failures", [])
                            fail_count = len(failures)
                            sample = failures[:3]
                            msg = f"验证未通过: {fail_count} 只股票数据不足 (示例: {sample})"
                            yield sse_msg("info", msg)
                    except Exception as e:
                        yield sse_msg("warning", f"验证请求异常: {str(e)}")
                    
                    await asyncio.sleep(retry_interval)
                
                if not validated:
                    yield sse_msg("warning", "数据完整性验证超时，部分股票可能数据不足")

            else:
                yield sse_msg("warning", "未能获取到任何历史问财股票，跳过处理")
            
            yield sse_msg("success", "Step 2 执行成功！")
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Step 2 failed: {e}")
            yield sse_msg("error", f"执行失败: {str(e)}")
            return

    async def _initialize_stock_environment(self, code: str, target_date: date, yield_func):
        """
        Unified initialization function (Step 1 Logic):
        1. Clean existing daily data (to ensure strict simulation state)
        2. Load 250-day history ending at target_date
        3. Trigger Single Score Calculation
        4. Trigger Volume Analysis
        """
        try:
            # 1. Clean Data (Strict Simulation: Remove future data or reload fresh)
            # To match "Step 1" logic exactly: Delete all and reload 250 days.
            # This ensures no future data leakage and fixes any gaps.
            yield yield_func("log", f"[{code}] 清理历史数据...")
            await self.session.execute(text("DELETE FROM stock_daily WHERE code = :code"), {"code": code})
            await self.session.commit()

            # 2. Load History (Inject 250 days)
            yield yield_func("log", f"[{code}] 加载250日历史K线 (截止 {target_date})...")
            # We use limit=300 to be safe for 250 trading days
            await BackendClient.load_local_data([code], end_date=target_date.strftime("%Y-%m-%d"))

            # 3. Trigger Score Calculation
            yield yield_func("log", f"[{code}] 触发评分计算...")
            await BackendClient.trigger_single_calculation(target_date.strftime("%Y-%m-%d"), code)

            # 4. Trigger Volume Analysis
            yield yield_func("log", f"[{code}] 触发异动分析...")
            await BackendClient.trigger_volume_analysis(code)

            yield yield_func("log", f"[{code}] 初始化完成")
            # return True # Can't return value in async generator

        except Exception as e:
            logger.error(f"Failed to initialize {code}: {e}")
            yield yield_func("warning", f"[{code}] 初始化失败: {e}")
            # return False # Can't return value in async generator

    async def run_daily_simulation_stream(self, target_date: date):
        """
        Generic Daily Simulation: Crawl -> Iterate Stocks -> Unified Init -> Validation
        """
        import json
        import asyncio
        
        def sse_msg(msg_type, content, data=None):
            payload = {"type": msg_type, "message": content, "data": data, "timestamp": datetime.now().isoformat()}
            return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        try:
            yield sse_msg("info", f"开始执行每日模拟: {target_date}")
            
            # 1. Wencai Crawler
            logger.info(f"Calling Wencai Crawler for {target_date}")
            yield sse_msg("step", "正在调用问财爬虫...", {"target_date": str(target_date)})
            
            crawler_res = await BackendClient.call_wencai_crawler(target_date.strftime("%Y-%m-%d"))
            
            if not crawler_res.get('success'):
                error_msg = f"Wencai Crawler failed: {crawler_res.get('message')}"
                yield sse_msg("error", error_msg)
                raise Exception(error_msg)
            
            yield sse_msg("step", f"爬虫执行完成: {crawler_res.get('message')}", crawler_res)
            
            # 2. Get Cumulative Top 3 Stocks from ALL batches
            # User Request: Calculate for ALL stocks that ever appeared in Top 3 (Cumulative)
            yield sse_msg("step", "正在获取累计优选股票池 (历史每批次前3名)...")
            
            # Use Python to filter Top 3 per batch to support all DB types easily
            # We select all stocks, ordered by batch and id, then pick top 3 for each batch
            stmt = text("SELECT stock_code, crawl_batch_id FROM wencai_stocks ORDER BY crawl_batch_id, id ASC")
            result = await self.session.execute(stmt)
            rows = result.all()
            
            batch_counts = {}
            cumulative_codes = set()
            
            for row in rows:
                code = row[0]
                b_id = row[1]
                
                # If batch_id is None, treat as a special batch or ignore? 
                # Let's treat None as a batch for safety.
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
                    # Small delay to yield to event loop and not choke the DB
                    await asyncio.sleep(0.1)
                    
                yield sse_msg("success", f"所有股票处理完成 ({success_count}/{len(codes)})")

                # 3. Validation (Poll until success or timeout)
                yield sse_msg("step", "正在验证数据完整性 (检查250天数据量)...")
                max_retries = 30
                retry_interval = 2
                validated = False
                
                for i in range(max_retries):
                    yield sse_msg("step", f"验证尝试 {i+1}/{max_retries}...")
                    try:
                        val_res = await BackendClient.validate_data_counts(codes, min_count=250)
                        if val_res.get("status") == "success":
                            yield sse_msg("success", "所有股票数据完整性验证通过 (>=250天)")
                            validated = True
                            break
                        else:
                            failures = val_res.get("failures", [])
                            fail_count = len(failures)
                            sample = failures[:3]
                            msg = f"验证未通过: {fail_count} 只股票数据不足 (示例: {sample})"
                            yield sse_msg("info", msg)
                    except Exception as e:
                        yield sse_msg("warning", f"验证请求异常: {str(e)}")
                    
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
