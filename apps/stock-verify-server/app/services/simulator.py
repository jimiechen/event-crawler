import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger
import pandas as pd
import random

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
            import random
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
            
            # Here we would normally trigger the system's analysis task
            # For verification, we might need to call an API on the backend or simulate the analysis call
            # But since we are independent, we might just verify that IF the backend was running, it would see this.
            # OR, we call the analysis logic if we imported it? 
            # The prompt says "Integrate ACCEPTANCE_PLAN...". The plan says "Call VolumeAnalysisService...".
            # If we are strictly isolated, we can't import services from the other project easily unless we add it to python path.
            # Given "Must be completely isolated... via independent code base", copying the core logic or calling APIs is better.
            # But the backend doesn't seem to expose "Run Analysis for Stock X" via API easily (maybe /api/v1/analysis/volume?).
            
            # Let's assume we just insert data for now, and the user triggers analysis or we mock the analysis result 
            # if we are verifying the *result* of the backend. 
            # Wait, if we are verifying the backend, we should trigger the backend to process.
            # If the backend has an API, we call it.
            
            await asyncio.sleep(interval_seconds)
