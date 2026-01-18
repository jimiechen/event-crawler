import asyncio
import sys
import os
from datetime import datetime, date
from sqlalchemy import select, func, and_

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import DatabaseManager
from app.models.task_log import TaskExecutionLog
from app.config.settings import settings

async def main():
    db = DatabaseManager()
    await db.initialize()
    
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    
    print(f"Checking tasks for date: {today}")
    
    async with db.get_session() as session:
        # Summary query
        stmt = select(
            TaskExecutionLog.task_type,
            TaskExecutionLog.status,
            func.count(TaskExecutionLog.id)
        ).where(
            TaskExecutionLog.created_at >= start_of_day
        ).group_by(
            TaskExecutionLog.task_type,
            TaskExecutionLog.status
        )
        
        result = await session.execute(stmt)
        rows = result.fetchall()
        
        print("\n--- Daily Task Summary ---")
        if not rows:
            print("No tasks found for today.")
        
        summary = {}
        for task_type, status, count in rows:
            print(f"Type: {task_type}, Status: {status}, Count: {count}")
            if task_type not in summary:
                summary[task_type] = {"total": 0, "success": 0, "failed": 0, "pending": 0, "running": 0}
            summary[task_type]["total"] += count
            if status in summary[task_type]:
                summary[task_type][status] += count
                
        # Check failures
        print("\n--- Failures ---")
        fail_stmt = select(TaskExecutionLog).where(
            and_(
                TaskExecutionLog.created_at >= start_of_day,
                TaskExecutionLog.status == 'failed'
            )
        ).limit(10)
        
        fail_result = await session.execute(fail_stmt)
        failures = fail_result.scalars().all()
        
        if not failures:
            print("No failures found.")
        else:
            for fail in failures:
                print(f"ID: {fail.id}, Type: {fail.task_type}, Code: {fail.stock_code}, Error: {fail.result_message}")

if __name__ == "__main__":
    asyncio.run(main())
