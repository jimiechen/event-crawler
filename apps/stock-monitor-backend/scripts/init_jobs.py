import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from app.database import db_manager
from app.models.generic_task import GenericTask
from app.services.generic_task_service import GenericTaskService
from loguru import logger

async def init_jobs():
    logger.info("Initializing Generic Tasks for Job Migration...")
    
    tasks_to_create = [
        {
            "name": "盘后积分更新",
            "task_category": "calculation",
            "api_method": "POST",
            "api_endpoint": "/api/v1/jobs/post-market-update",
            "cron_expression": "30 15 * * *",
            "is_active": True,
            "timeout": 3600,
            "description": "盘后数据同步、积分计算与排名更新"
        },
        {
            "name": "每日验收测试",
            "task_category": "monitor",
            "api_method": "POST",
            "api_endpoint": "/api/v1/jobs/daily-acceptance",
            "cron_expression": "0 16 * * *",
            "is_active": True,
            "timeout": 600,
            "description": "每日系统功能验收测试"
        },
        {
            "name": "盘中实时监控检查",
            "task_category": "monitor",
            "api_method": "POST",
            "api_endpoint": "/api/v1/jobs/realtime-monitor",
            "cron_expression": "*/5 14 * * 1-5",
            "is_active": True,
            "timeout": 60,
            "description": "盘中实时监控数据检查"
        },
        {
            "name": "每日AI复盘",
            "task_category": "analysis",
            "api_method": "POST",
            "api_endpoint": "/api/v1/jobs/daily-ai-review",
            "cron_expression": "40 15 * * *",
            "is_active": True,
            "timeout": 3600,
            "description": "每日AI复盘分析"
        },
        {
            "name": "每日问财爬虫",
            "task_category": "crawler",
            "api_method": "POST",
            "api_endpoint": "/api/v1/jobs/wencai-daily-crawler",
            "cron_expression": "30 16 * * *",
            "is_active": True,
            "timeout": 3600,
            "description": "每日问财数据爬取"
        },
        {
            "name": "问财数据同步与评分",
            "task_category": "data_sync",
            "api_method": "POST",
            "api_endpoint": "/api/v1/jobs/wencai-data-sync",
            "cron_expression": "0 17 * * *",
            "is_active": True,
            "timeout": 3600,
            "description": "问财数据同步到本地并进行评分"
        }
    ]

    async with db_manager.get_session() as session:
        service = GenericTaskService(session)
        existing_tasks = await service.get_all_generic_tasks()
        existing_map = {t.name: t for t in existing_tasks}
        
        for task_data in tasks_to_create:
            task_name = task_data["name"]
            if task_name in existing_map:
                logger.info(f"Updating existing task: {task_name}")
                task = existing_map[task_name]
                await service.update_generic_task(task.id, task_data)
            else:
                logger.info(f"Creating new task: {task_name}")
                await service.create_generic_task(task_data)
        
        logger.info("Job initialization completed.")

if __name__ == "__main__":
    asyncio.run(init_jobs())
