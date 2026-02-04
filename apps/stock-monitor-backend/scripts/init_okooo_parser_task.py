#!/usr/bin/env python3
"""
初始化Okooo解析定时任务
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.database import db_manager
from app.services.generic_task_service import GenericTaskService


async def init_okooo_parser_task():
    """初始化Okooo解析定时任务"""

    async with db_manager.get_session() as session:
        service = GenericTaskService(session)

        # 检查是否已存在
        tasks = await service.get_all_generic_tasks()
        existing = [t for t in tasks if "okooo" in t.name.lower()]

        if existing:
            print(f"✅ Okooo解析任务已存在:")
            for task in existing:
                print(f"   - {task.name} (ID: {task.id}, 启用: {task.is_active})")
            return

        # 创建新任务
        task_data = {
            "name": "每日Okooo比赛数据解析",
            "task_category": "crawler",
            "api_method": "POST",
            "api_endpoint": "/api/v1/okooo/parse/daily",
            "request_params": {"date": "auto"},  # auto = 当天日期
            "cron_expression": "0 14 * * *",  # 每天14:00
            "is_active": True,
            "timeout": 1800,  # 30分钟
            "max_retries": 2,
            "priority": 5,
            "description": "自动解析当天日期的所有Okooo比赛数据，输出到 processed/{日期}/",
            "notify_on_failure": True,
            "notify_channels": "desktop,log"
        }

        task = await service.create_generic_task(task_data)
        print(f"✅ 创建成功!")
        print(f"   任务名称: {task.name}")
        print(f"   任务ID: {task.id}")
        print(f"   调度规则: {task.cron_expression} (每天14:00)")
        print(f"   API端点: {task.api_endpoint}")
        print(f"   输出目录: data/okooo/processed/{日期}/")
        print(f"   状态: {'启用' if task.is_active else '禁用'}")


if __name__ == "__main__":
    print("🚀 初始化Okooo解析定时任务...")
    asyncio.run(init_okooo_parser_task())
