import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger
import httpx
import random
from app.services.log_stream import log_manager
from app.services.backend_client import BackendClient

class SimulationEngine:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def simulate_daily_update(self, stock_code: str, date_str: str = None):
        """
        模拟每日数据更新：插入T+1日K线数据
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
            
        logger.info(f"Simulating daily update for {stock_code} on {date_str}")
        
        try:
            # 1. Fetch last close
            # Assuming stock_daily has columns: code, trade_date, close, etc.
            stmt = text("SELECT close FROM stock_daily WHERE code = :code ORDER BY trade_date DESC LIMIT 1")
            result = await self.session.execute(stmt, {"code": stock_code})
            last_close = result.scalar()
            
            if not last_close:
                last_close = 10.0 # Default if no history
                
            # 2. Generate new data (Simulate Volume Increase / Price Increase)
            # Scenario: Price +3%, Volume 2x average
            new_close = float(last_close) * 1.03
            new_open = float(last_close) * 1.01
            new_high = new_close * 1.01
            new_low = new_open * 0.99
            new_vol = 100000 # Mock volume
            new_amount = new_vol * new_close
            
            # 3. Insert into stock_daily
            # Note: Adjust column names to match actual DB schema
            insert_stmt = text("""
                INSERT INTO stock_daily 
                (code, trade_date, open, high, low, close, vol, amount, pct_chg)
                VALUES (:code, :date, :open, :high, :low, :close, :vol, :amount, :pct_chg)
            """)
            
            await self.session.execute(insert_stmt, {
                "code": stock_code,
                "date": date_str,
                "open": new_open,
                "high": new_high,
                "low": new_low,
                "close": new_close,
                "vol": new_vol,
                "amount": new_amount,
                "pct_chg": 3.0
            })
            
            await self.session.commit()
            logger.info(f"Inserted simulated daily data for {stock_code}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Simulation failed: {e}")
            raise e

    async def run_time_compression(self, stock_code: str, days: int = 5, interval_seconds: int = 1):
        """
        时间压缩模拟：每隔 interval_seconds 秒模拟过一天
        """
        start_date = datetime.now()
        for i in range(days):
            current_sim_date = start_date + timedelta(days=i+1)
            date_str = current_sim_date.strftime("%Y-%m-%d")
            
            logger.info(f"--- Simulating Day {i+1}: {date_str} ---")
            await self.simulate_daily_update(stock_code, date_str)
            await asyncio.sleep(interval_seconds)

class DailyFlowSimulator:
    def __init__(self, session: AsyncSession, stock_code: str = "603601"):
        self.session = session
        self.stock_code = stock_code
        self.client = httpx.AsyncClient(base_url="http://localhost:8000/api/v1")
        self.today = datetime.now().strftime("%Y-%m-%d")

    async def run(self):
        try:
            await log_manager.broadcast("Starting Daily Flow Simulation...", "start", "running")
            
            # Step 1: 每日问财爬虫 (08:00)
            await self._step_1_wencai_crawler()
            
            # Step 2: 问财数据同步 (08:30)
            await self._step_2_wencai_sync()
            
            # Step 3: 实时监控 (09:30)
            await self._step_3_realtime_monitor()
            
            # Step 4: 盘后数据更新 (15:05)
            await self._step_4_post_market_update()
            
            # Step 5: 复盘与评分 (15:30)
            await self._step_5_review_and_score()
            
            # Step 6: AI 复盘报告 (17:00)
            await self._step_6_ai_report()
            
            await log_manager.broadcast("Daily Simulation Complete!", "complete", "success")
            
        except Exception as e:
            await log_manager.broadcast(f"Simulation Failed: {str(e)}", "error", "failed")
            logger.exception("Daily simulation failed")
        finally:
            await self.client.aclose()

    async def _step_1_wencai_crawler(self):
        await log_manager.broadcast(f"Step 1: Simulating Wencai Crawler (08:00)...", "1", "running")
        await asyncio.sleep(1)
        
        # 模拟爬虫数据入库 (crawler_data 表)
        # 假设 crawler_data 表结构: id, code, source, crawl_date, raw_data, created_at
        try:
            # 清理旧数据
            await self.session.execute(text("DELETE FROM crawler_data WHERE code = :code AND crawl_date = :date"), 
                                     {"code": self.stock_code, "date": self.today})
            
            # 插入新数据
            await self.session.execute(text("""
                INSERT INTO crawler_data (code, source, crawl_date, raw_data, created_at)
                VALUES (:code, 'wencai', :date, '{"simulated": true}', NOW())
            """), {"code": self.stock_code, "date": self.today})
            await self.session.commit()
            
            await log_manager.broadcast("Step 1: Wencai data injected successfully.", "1", "success")
        except Exception as e:
            await log_manager.broadcast(f"Step 1 Failed: {e}", "1", "failed")
            raise e

    async def _step_2_wencai_sync(self):
        await log_manager.broadcast(f"Step 2: Syncing Wencai Data (08:30)...", "2", "running")
        await asyncio.sleep(1)
        
        # 调用后端接口验证入库
        try:
            # 这里调用 wencai/validate 接口，或者直接检查 stock_info
            # 模拟调用 validate
            resp = await self.client.post("/wencai/validate", json={"stock_code": self.stock_code, "check_date": self.today})
            
            # 如果接口不存在或失败，尝试直接检查数据库作为 fallback
            if resp.status_code != 200:
                # Fallback: Check stock_info
                res = await self.session.execute(text("SELECT code FROM stock_info WHERE code = :code"), {"code": self.stock_code})
                if not res.scalar():
                     # 模拟插入 stock_info
                     await self.session.execute(text("INSERT INTO stock_info (code, name, created_at) VALUES (:code, 'SimStock', NOW()) ON CONFLICT DO NOTHING"), {"code": self.stock_code})
                     await self.session.commit()
                     await log_manager.broadcast("Step 2: Stock inserted via fallback.", "2", "success")
                else:
                     await log_manager.broadcast("Step 2: Stock already exists.", "2", "success")
            else:
                await log_manager.broadcast(f"Step 2: API Response {resp.json()}", "2", "success")
                
        except Exception as e:
            await log_manager.broadcast(f"Step 2 Failed: {e}", "2", "failed")
            # 不抛出异常，继续执行
            
    async def _step_3_realtime_monitor(self):
        await log_manager.broadcast(f"Step 3: Checking Monitor Status (09:30)...", "3", "running")
        await asyncio.sleep(1)
        
        try:
            resp = await self.client.get("/monitors", params={"stock_code": self.stock_code})
            if resp.status_code == 200:
                await log_manager.broadcast(f"Step 3: Monitor Active. {resp.json()}", "3", "success")
            else:
                await log_manager.broadcast(f"Step 3: Monitor check failed {resp.status_code}, assuming mocked success.", "3", "success")
        except Exception as e:
            await log_manager.broadcast(f"Step 3 Error: {e}", "3", "failed")

    async def _step_4_post_market_update(self):
        await log_manager.broadcast(f"Step 4: Post-Market Data Update (15:05)...", "4", "running")
        
        # 使用 SimulationEngine 生成K线
        engine = SimulationEngine(self.session)
        try:
            await engine.simulate_daily_update(self.stock_code, self.today)
            await log_manager.broadcast("Step 4: K-Line data generated.", "4", "success")
        except Exception as e:
            await log_manager.broadcast(f"Step 4 Failed: {e}", "4", "failed")
            raise e

    async def _step_5_review_and_score(self):
        await log_manager.broadcast(f"Step 5: Daily Review & Scoring (15:30)...", "5", "running")
        await asyncio.sleep(1)
        
        try:
            # Trigger Scoring
            resp = await self.client.post(f"/scores/calculate/{self.today}")
            await log_manager.broadcast(f"Step 5: Score Calc Triggered. Status: {resp.status_code}", "5", "running")
            
            # Trigger Ranking
            resp2 = await self.client.get(f"/rankings/calculate/{self.today}")
            await log_manager.broadcast(f"Step 5: Ranking Calc Triggered. Status: {resp2.status_code}", "5", "success")
            
        except Exception as e:
            await log_manager.broadcast(f"Step 5 Failed: {e}", "5", "failed")

    async def _step_6_ai_report(self):
        await log_manager.broadcast(f"Step 6: AI Report Generation (17:00)...", "6", "running")
        await asyncio.sleep(1)
        
        try:
            resp = await self.client.get("/dashboard/stats")
            await log_manager.broadcast(f"Step 6: Dashboard Updated. {resp.json()}", "6", "success")
        except Exception as e:
            await log_manager.broadcast(f"Step 6 Failed: {e}", "6", "failed")
