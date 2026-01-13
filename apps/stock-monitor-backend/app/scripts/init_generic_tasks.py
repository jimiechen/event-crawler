import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到 python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import db_manager
from app.services.generic_task_service import GenericTaskService
from app.models.generic_task import GenericTask

async def init_tasks():
    print("开始初始化通用定时任务...")
    
    async with db_manager.get_session() as session:
        service = GenericTaskService(session)
        
        # 定义默认任务
        default_tasks = [
            {
                "name": "盘中问财实时抓取",
                "task_category": "crawler",
                "api_method": "POST",
                "api_endpoint": "/api/v1/wencai/crawl/realtime",
                "request_params": {"query": "量比大于2，涨幅大于3%，涨幅小于7%，非ST"},
                "cron_expression": "*/30 9-14 * * 1-5",  # 周一至周五 9:00-14:59 每30分钟
                "description": "盘中每30分钟抓取一次符合条件的股票",
                "priority": 8
            },
            {
                "name": "盘后 Pathway 积分计算",
                "task_category": "calculation",
                "api_method": "POST",
                "api_endpoint": "/api/v1/scores/calculate/{today}",  # {today} 需要在 Executor 中处理吗？目前不支持动态参数
                # 注意：TaskExecutor 目前不支持 {today} 动态替换。
                # 我们可以让 Controller 的 calculate 接口支持 "today" 作为参数，或者不传日期默认为当天。
                # 让我们检查一下 Controller。
                # Controller: date_str: str = Path(...)
                # 我们需要修改 Controller 允许 "today" 关键字，或者修改 TaskExecutor 支持动态变量。
                # 为了简单，修改 Controller 最容易。
                "request_params": {},
                "cron_expression": "30 15 * * 1-5",  # 周一至周五 15:30
                "description": "盘后自动计算当日股票积分",
                "priority": 9
            },
            {
                "name": "每日问财复盘抓取",
                "task_category": "crawler",
                "api_method": "POST",
                "api_endpoint": "/api/v1/wencai/crawl/realtime",
                "request_params": {"query": "量比大于1.5，涨幅大于0%，非ST"}, # 稍微放宽条件
                "cron_expression": "0 17 * * 1-5",  # 周一至周五 17:00
                "description": "每日收盘后进行一次全量复盘抓取",
                "priority": 7
            }
        ]
        
        existing_tasks = await service.get_all_generic_tasks()
        existing_names = {t.name for t in existing_tasks}
        
        for task_data in default_tasks:
            if task_data["name"] in existing_names:
                print(f"任务已存在: {task_data['name']}")
                continue
                
            # 特殊处理 api_endpoint 中的动态参数
            # 由于目前 TaskExecutor 不支持动态参数替换，我们需要修改 Controller
            # 这里的 endpoint 保持为 "/api/v1/scores/calculate/today"
            if "{today}" in task_data["api_endpoint"]:
                task_data["api_endpoint"] = task_data["api_endpoint"].replace("{today}", "today")
            
            await service.create_generic_task(task_data)
            print(f"创建任务: {task_data['name']}")
            
    print("初始化完成!")

if __name__ == "__main__":
    asyncio.run(init_tasks())
