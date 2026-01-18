import csv
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger
from .backend_client import BackendClient

class SimulationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _load_csv_data(self, code: str, end_date: date, days: int = 250):
        """
        从CSV加载真实数据并插入 stock_daily
        CSV路径: /Users/mac/StudioProjects/open-citycloud/603601.SH.csv
        """
        csv_path = "/Users/mac/StudioProjects/open-citycloud/603601.SH.csv"
        logger.info(f"Loading real data from {csv_path} for {code} ending {end_date}")
        
        data_list = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                all_rows = list(reader)
                
                # Sort by date just in case
                all_rows.sort(key=lambda x: x['交易日期'])
                
                # Filter rows <= end_date
                target_rows = []
                for row in all_rows:
                    row_date = datetime.strptime(row['交易日期'], "%Y-%m-%d").date()
                    if row_date <= end_date:
                        target_rows.append(row)
                
                # Take last N days
                if len(target_rows) > days:
                    target_rows = target_rows[-days:]
                
                for row in target_rows:
                    # CSV columns: 股票代码,交易日期,开盘价,最高价,最低价,收盘价,昨收价,涨跌额,涨跌幅,成交量(手),成交额(千元)
                    trade_date = datetime.strptime(row['交易日期'], "%Y-%m-%d").date()
                    
                    data_list.append({
                        "code": code,
                        "trade_date": trade_date,
                        "open": float(row['开盘价']),
                        "close": float(row['收盘价']),
                        "high": float(row['最高价']),
                        "low": float(row['最低价']),
                        "vol": float(row['成交量(手)']),
                        "amount": float(row['成交额(千元)'])
                    })
            
            if data_list:
                logger.info(f"Loaded {len(data_list)} records from CSV. Last date: {data_list[-1]['trade_date']}")
                stmt = text("""
                    INSERT INTO stock_daily (code, trade_date, open, close, high, low, vol, amount)
                    VALUES (:code, :trade_date, :open, :close, :high, :low, :vol, :amount)
                """)
                await self.session.execute(stmt, data_list)
            else:
                logger.warning("No data found in CSV for the specified range")
                
        except Exception as e:
            logger.error(f"Failed to load CSV data: {e}")
            raise e

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

            # stock_info (Deprecated, removed per user instruction)
            # await self.session.execute(text("DELETE FROM stock_info WHERE code = :code"), {"code": code})
            # await self.session.execute(text("""
            #    INSERT INTO stock_info (code, name, is_active, created_at)
            #    VALUES (:code, :name, true, :date)
            # """), {"code": code, "name": name, "date": datetime(2025, 11, 19)})

            # 2. Load Real History
            # Clear daily first
            await self.session.execute(text("DELETE FROM stock_daily WHERE code = :code"), {"code": code})
            
            # Use CSV data instead of mock
            # await self._generate_mock_daily_data(code, target_date, days=255) 
            await self._load_csv_data(code, target_date, days=255)
            
            await self.session.commit()
            
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
        - 爬虫自动计算基础分
        - 更新 603601 历史数据
        - 计算所有股票的当日评分
        """
        import json
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
                error_msg = f"Wencai Crawler failed: {crawler_res.get('message')}"
                yield sse_msg("error", error_msg)
                raise Exception(error_msg)
            
            yield sse_msg("step", f"爬虫执行完成: {crawler_res.get('message')}", crawler_res)
            logger.info(f"Wencai Crawler completed: {crawler_res}")
            
            # 2. 更新 603601 历史数据（添加2025-11-20一天）
            yield sse_msg("step", "正在更新 603601 历史数据...")
            code_603601 = "603601"
            await self.session.execute(text("""
                DELETE FROM stock_daily 
                WHERE code = :code AND trade_date = :date
            """), {"code": code_603601, "date": target_date})
            
            # Load real data for this specific day from 603601.SH.csv
            await self._load_csv_data(code_603601, target_date, days=1)
            
            await self.session.commit()
            yield sse_msg("step", "603601 历史数据更新完成")
            
            # 3. 计算所有股票的当日评分(2025-11-20)
            yield sse_msg("step", "正在触发全量评分计算...")
            logger.info(f"Triggering batch calculation for {target_date}")
            res = await BackendClient.trigger_calculation(target_date.strftime("%Y-%m-%d"), 0)
            
            yield sse_msg("step", f"评分计算完成: {res.get('message')}", res)
            
            yield sse_msg("success", "Step 2 执行成功！")
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Step 2 failed: {e}")
            yield sse_msg("error", f"执行失败: {str(e)}")
            # Don't raise, just end stream with error
            return
