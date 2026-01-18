from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, insert
from loguru import logger

class SimulationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute_step1_20251119(self):
        """
        Step 1: 2025-11-19
        - Inject 603601 into wencai_stocks
        - Inject score result for 603601 (Total: 37800, Rank: 1)
        """
        logger.info("Executing Step 1 (2025-11-19)...")
        
        target_date = date(2025, 11, 19)
        stock_code = "603601"
        stock_name = "再升科技"
        
        try:
            # 1. Insert into wencai_stocks
            # Ensure no duplicates first (though clear_all should have handled it)
            await self.session.execute(text("DELETE FROM wencai_stocks WHERE stock_code = :code"), {"code": stock_code})
            
            stmt_wencai = text("""
                INSERT INTO wencai_stocks (stock_code, stock_name, created_at, is_active, source)
                VALUES (:code, :name, :date, true, 'wencai')
            """)
            await self.session.execute(stmt_wencai, {
                "code": stock_code,
                "name": stock_name,
                "date": datetime(2025, 11, 19, 9, 30) # Morning
            })
            
            # 2. Insert into stock_score_result
            await self.session.execute(text("DELETE FROM stock_score_result WHERE code = :code AND trade_date = :date"), {"code": stock_code, "date": target_date})
            
            stmt_score = text("""
                INSERT INTO stock_score_result 
                (code, trade_date, daily_score, total_score, accumulated_score, ranking, pool_type, rule_scores)
                VALUES (:code, :date, :daily, :total, :acc, :rank, 'wencai', :rules)
            """)
            await self.session.execute(stmt_score, {
                "code": stock_code,
                "date": target_date,
                "daily": 50.00,
                "total": 37800.00,
                "acc": 37800.00,
                "rank": 1,
                "rules": '{"base": 37750, "daily": 50}'
            })
            
            # 3. Ensure stock_info exists (for frontend list)
            await self.session.execute(text("DELETE FROM stock_info WHERE code = :code"), {"code": stock_code})
            stmt_info = text("""
                INSERT INTO stock_info (code, name, is_active, created_at)
                VALUES (:code, :name, true, :date)
            """)
            await self.session.execute(stmt_info, {
                "code": stock_code,
                "name": stock_name,
                "date": datetime(2025, 11, 19)
            })

            # 4. Mock Stock Daily for the day (optional but good for completeness)
            await self.session.execute(text("DELETE FROM stock_daily WHERE code = :code AND trade_date = :date"), {"code": stock_code, "date": target_date})
            # Insert dummy daily data
            stmt_daily = text("""
                INSERT INTO stock_daily (code, trade_date, open, close, high, low, vol, amount)
                VALUES (:code, :date, 10.0, 10.5, 10.5, 9.8, 10000, 100000)
            """)
            await self.session.execute(stmt_daily, {
                "code": stock_code,
                "date": target_date
            })
            
            await self.session.commit()
            logger.info("Step 1 completed successfully.")
            return {"status": "success", "message": "Step 1 (2025-11-19) executed: 603601 added with score 37800."}
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Step 1 failed: {e}")
            raise e

    async def execute_step2_20251120(self):
        """
        Step 2: 2025-11-20
        - Add 11 other stocks
        - Update scores: 603601 (Rank 12), Others (Rank 1-11)
        """
        logger.info("Executing Step 2 (2025-11-20)...")
        
        target_date = date(2025, 11, 20)
        stock_603601 = "603601"
        
        try:
            # 1. Add 11 other stocks
            other_stocks = []
            for i in range(1, 12):
                code = f"0000{i:02d}"
                name = f"模拟股{i}"
                other_stocks.append({"code": code, "name": name})
                
                # Insert into wencai_stocks
                await self.session.execute(text("DELETE FROM wencai_stocks WHERE stock_code = :code"), {"code": code})
                await self.session.execute(text("""
                    INSERT INTO wencai_stocks (stock_code, stock_name, created_at, is_active, source)
                    VALUES (:code, :name, :date, true, 'wencai')
                """), {"code": code, "name": name, "date": datetime(2025, 11, 20, 9, 30)})
                
                # Insert into stock_info
                await self.session.execute(text("DELETE FROM stock_info WHERE code = :code"), {"code": code})
                await self.session.execute(text("""
                    INSERT INTO stock_info (code, name, is_active, created_at)
                    VALUES (:code, :name, true, :date)
                """), {"code": code, "name": name, "date": datetime(2025, 11, 20)})

                # Insert Score (Rank 1-11, Score > 37800)
                score = 40000 + (12 - i) * 100 # Rank 1 gets highest score
                rank = i
                
                await self.session.execute(text("""
                    INSERT INTO stock_score_result 
                    (code, trade_date, daily_score, total_score, accumulated_score, ranking, pool_type, rule_scores)
                    VALUES (:code, :date, :daily, :total, :acc, :rank, 'wencai', :rules)
                """), {
                    "code": code,
                    "date": target_date,
                    "daily": 100.00,
                    "total": score,
                    "acc": score,
                    "rank": rank,
                    "rules": '{"base": 39900, "daily": 100}'
                })

                # Mock Daily
                await self.session.execute(text("DELETE FROM stock_daily WHERE code = :code AND trade_date = :date"), {"code": code, "date": target_date})
                await self.session.execute(text("""
                    INSERT INTO stock_daily (code, trade_date, open, close, high, low, vol, amount)
                    VALUES (:code, :date, 20.0, 22.0, 22.0, 19.8, 50000, 1000000)
                """), {"code": code, "date": target_date})

            # 2. Update 603601 for 2025-11-20
            # Rank 12, Score 37800 (unchanged total, 0 daily)
            await self.session.execute(text("DELETE FROM stock_score_result WHERE code = :code AND trade_date = :date"), {"code": stock_603601, "date": target_date})
            
            await self.session.execute(text("""
                INSERT INTO stock_score_result 
                (code, trade_date, daily_score, total_score, accumulated_score, ranking, pool_type, rule_scores)
                VALUES (:code, :date, :daily, :total, :acc, :rank, 'wencai', :rules)
            """), {
                "code": stock_603601,
                "date": target_date,
                "daily": 0.00,
                "total": 37800.00,
                "acc": 37800.00,
                "rank": 12,
                "rules": '{"base": 37800, "daily": 0}'
            })

            # Mock Daily for 603601 (no limit up)
            await self.session.execute(text("DELETE FROM stock_daily WHERE code = :code AND trade_date = :date"), {"code": stock_603601, "date": target_date})
            await self.session.execute(text("""
                INSERT INTO stock_daily (code, trade_date, open, close, high, low, vol, amount)
                VALUES (:code, :date, 10.5, 10.6, 10.7, 10.4, 8000, 80000)
            """), {"code": stock_603601, "date": target_date})

            await self.session.commit()
            logger.info("Step 2 completed successfully.")
            return {"status": "success", "message": "Step 2 (2025-11-20) executed: 12 stocks total, 603601 rank 12."}

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Step 2 failed: {e}")
            raise e
