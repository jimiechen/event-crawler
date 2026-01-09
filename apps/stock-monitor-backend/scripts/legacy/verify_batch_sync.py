import sys
import os
import asyncio
from sqlalchemy import select, func, text
sys.path.append(os.getcwd())

from app.database import db_manager
from app.models.task_log import TaskExecutionLog
from app.models.stock_daily import StockDaily

async def verify():
    await db_manager.initialize()
    async with db_manager.session_factory() as session:
        # 1. Check Task Logs
        print("Checking Task Logs...")
        stmt = select(func.count(TaskExecutionLog.id)).where(
            TaskExecutionLog.task_type == "tushare_sync",
            TaskExecutionLog.status == "success"
        )
        success_count = (await session.execute(stmt)).scalar()
        
        stmt = select(func.count(TaskExecutionLog.id)).where(
            TaskExecutionLog.task_type == "tushare_sync"
        )
        total_count = (await session.execute(stmt)).scalar()
        
        print(f"Total Tushare Sync Tasks: {total_count}")
        print(f"Successful Tasks: {success_count}")
        
        # 2. Check Stock Daily Data
        print("\nChecking Stock Daily Data...")
        # Check how many distinct codes have data
        stmt = select(func.count(func.distinct(StockDaily.code)))
        stock_count = (await session.execute(stmt)).scalar()
        print(f"Total Stocks in StockDaily: {stock_count}")
        
        if success_count > 0:
            ratio = stock_count / success_count
            print(f"Ratio (Stocks/Tasks): {ratio:.2f}")
        
        if success_count != stock_count:
            print(f"\n[INFO] Mismatch: Success Tasks ({success_count}) != Stocks with Data ({stock_count})")
            print("Note: Some stocks might have no data (suspended/delisted) even if task succeeded.")
        else:
            print(f"\n[OK] Match: Success Tasks ({success_count}) == Stocks with Data ({stock_count})")

if __name__ == "__main__":
    asyncio.run(verify())
