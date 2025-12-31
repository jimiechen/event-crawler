
import asyncio
from sqlalchemy import select, func
from app.database import db_manager
from app.models.stock_daily import StockScoreResult
from app.models.stock import StockInfo
from sqlalchemy import select, func
import asyncio

from app.models.task_log import TaskExecutionLog
from app.models.scheduled_task import ScheduledTask

from app.models.stock_daily import StockDaily

from app.models.tag_management import StockTagInfo

async def check_scores():
    await db_manager.initialize()
    async with db_manager.get_session() as db:
        # Check Tag Config
        tag_query = select(StockTagInfo).where(StockTagInfo.tag_type == 'calculation')
        result = await db.execute(tag_query)
        tags = result.scalars().all()
        print("Calculation Tags:")
        if not tags:
            print("  No calculation tags found!")
        for tag in tags:
            print(f"  {tag.name}: {tag.score}")

        # Check latest daily data
        daily_query = select(StockDaily.trade_date).order_by(StockDaily.trade_date.desc()).limit(1)
        result = await db.execute(daily_query)
        latest_date = result.scalar()
        print(f"Latest Stock Daily Data Date: {latest_date}")

        # Check scheduled tasks
        task_query = select(ScheduledTask)
        result = await db.execute(task_query)
        tasks = result.scalars().all()
        print("Scheduled Tasks Status:")
        for task in tasks:
            print(f"  {task.name} ({task.task_type}): Last Run: {task.last_run_at} Status: {task.last_run_status}")

        # Check execution logs
        log_query = select(TaskExecutionLog).order_by(TaskExecutionLog.executed_at.desc()).limit(10)
        result = await db.execute(log_query)
        logs = result.scalars().all()
        print("\nRecent Task Execution Logs:")
        for log in logs:
            print(f"  {log.task_type} for {log.stock_code} - {log.status} - {log.executed_at} - URL: {log.task_url}")

        # Check total count
        count_query = select(func.count(StockScoreResult.id))
        result = await db.execute(count_query)
        count = result.scalar()
        print(f"Total rows in stock_score_result: {count}")

        # Check latest dates
        date_query = select(StockScoreResult.trade_date, func.count(StockScoreResult.id)).group_by(StockScoreResult.trade_date).order_by(StockScoreResult.trade_date.desc()).limit(5)
        result = await db.execute(date_query)
        dates = result.all()
        print("Latest dates in stock_score_result:")
        for d, c in dates:
            print(f"  {d}: {c} records")

        # Check a sample record
        if count > 0:
            sample_query = select(StockScoreResult).limit(1)
            result = await db.execute(sample_query)
            sample = result.scalar()
            print(f"Sample record: code={sample.code}, date={sample.trade_date}, total_score={sample.total_score}")

if __name__ == "__main__":
    asyncio.run(check_scores())
