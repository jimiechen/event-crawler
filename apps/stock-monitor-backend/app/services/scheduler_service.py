#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务调度服务
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from datetime import datetime

from app.services.tushare_service import TushareService
from app.services.rule_engine_service import RuleEngineService
from app.services.local_data_service import LocalDataService
from app.services.volume_analysis_service import VolumeAnalysisService
from app.services.stock_service import StockService
from app.repositories.tag_repository import TagRepository
from app.repositories.sync_log_repository import SyncLogRepository
from app.repositories.scheduled_task_repository import ScheduledTaskRepository
from app.models.sync_log import SyncTaskType, SyncTaskStatus
from app.models.scheduled_task import ScheduledTask
from app.database import DatabaseManager, db_manager

class SchedulerService:
    def __init__(self, db_manager: DatabaseManager):
        self.scheduler = AsyncIOScheduler()
        self.db_manager = db_manager
        self.repo = ScheduledTaskRepository(db_manager)
        self.stock_service = StockService(db_manager)
        self.tushare_service = TushareService(db_manager)
        self.rule_engine_service = RuleEngineService(db_manager)
        self.log_repository = SyncLogRepository(db_manager)

    def start(self):
        """启动调度器"""
        # 使用 create_task 异步初始化任务
        import asyncio
        asyncio.create_task(self._init_and_load_jobs())
        
        self.scheduler.start()
        logger.info("定时任务调度器已启动")

    async def _init_and_load_jobs(self):
        """初始化默认任务并加载到调度器"""
        try:
            await self._init_default_tasks()
            await self._load_jobs()
        except Exception as e:
            logger.error(f"Failed to init/load scheduled jobs: {e}")

    async def _init_default_tasks(self):
        """初始化默认定时任务"""
        defaults = [
            {
                "name": "每日数据同步",
                "task_type": "daily_sync",
                "cron_expression": "30 15 * * *",
                "description": "每日15:30同步Tushare数据"
            },
            {
                "name": "每日评分计算",
                "task_type": "daily_score",
                "cron_expression": "0 16 * * *",
                "description": "每日16:00计算股票评分"
            },
            {
                "name": "CSV数据健康检查",
                "task_type": "csv_health_check",
                "cron_expression": "0 8 * * *",
                "description": "每日08:00检查CSV文件格式和数据质量"
            }
        ]
        
        for task_info in defaults:
            existing = await self.repo.get_task_by_type(task_info["task_type"])
            if not existing:
                new_task = ScheduledTask(
                    name=task_info["name"],
                    task_type=task_info["task_type"],
                    cron_expression=task_info["cron_expression"],
                    description=task_info["description"],
                    is_active=True
                )
                await self.repo.create_task(new_task)
                logger.info(f"Initialized default scheduled task: {task_info['name']}")

    async def _load_jobs(self):
        """从数据库加载任务到调度器"""
        self.scheduler.remove_all_jobs()
        tasks = await self.repo.get_all_tasks()
        
        for task in tasks:
            if task.is_active:
                try:
                    self.add_job_to_scheduler(task)
                except Exception as e:
                    logger.error(f"Failed to schedule task {task.name}: {e}")
        
        logger.info(f"Loaded {len(self.scheduler.get_jobs())} scheduled jobs")

    def add_job_to_scheduler(self, task: ScheduledTask):
        """添加单个任务到调度器"""
        try:
            trigger = CronTrigger.from_crontab(task.cron_expression)
            self.scheduler.add_job(
                self.execute_task_wrapper,
                trigger,
                id=str(task.id),
                name=task.name,
                args=[task.id, task.task_type],
                replace_existing=True
            )
            logger.info(f"Scheduled job: {task.name} ({task.cron_expression})")
        except Exception as e:
            logger.error(f"Invalid cron expression for {task.name}: {task.cron_expression}")
            raise e

    async def execute_task_wrapper(self, task_id: int, task_type: str):
        """任务执行包装器 (处理状态更新)"""
        logger.info(f"Executing scheduled task: {task_type} (ID: {task_id})")
        start_time = datetime.now()
        
        try:
            # Execute actual logic
            if task_type == 'daily_sync':
                await self.run_daily_sync()
            elif task_type == 'daily_score':
                await self.run_daily_score()
            elif task_type == 'csv_health_check':
                await self.run_csv_health_check()
            else:
                logger.warning(f"Unknown task type: {task_type}")
                return

            # Update success status
            await self.repo.update_task_status(task_id, 'success', last_run_at=start_time)
            logger.info(f"Scheduled task {task_type} completed successfully")
            
        except Exception as e:
            logger.error(f"Scheduled task {task_type} failed: {e}")
            # Update failed status
            await self.repo.update_task_status(task_id, 'failed', last_run_at=start_time)

    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()
        logger.info("定时任务调度器已关闭")

    async def run_daily_sync(self):
        """执行每日数据同步"""
        logger.info("定时任务: 开始每日数据同步")
        
        # Create Log
        from datetime import datetime
        log = await self.log_repository.create_log(
            task_type=SyncTaskType.DAILY_INCREMENT
        )

        try:
            # 1. 同步股票池 (构建 StockPool 表)
            logger.info("正在同步股票池...")
            result = await self.tushare_service.refresh_stock_pool()
            pool_stats = result.get("stats", {})
            logger.info(f"股票池同步完成: {pool_stats}")
            
            tagged_codes = []
            
            # 1.5 加载本地历史数据 (优先级最高，只加载股票池内的本地CSV数据)
            # 获取股票池代码
            target_codes = await self.tushare_service.repository.get_target_stocks()
            logger.info(f"正在加载本地历史数据 (针对 {len(target_codes)} 只池内股票)...")
            
            # Initialize tagged_codes with target_codes to ensure analysis runs for all pool stocks
            tagged_codes = target_codes
            
            if target_codes:
                async with self.db_manager.get_session() as session:
                    stock_service = StockService(session)
                    # Load basics
                    await LocalDataService.load_stock_basics_for_stocks(stock_service, target_codes)
                    # Load daily
                    await LocalDataService.load_local_data_for_stocks(stock_service, target_codes)

            # 2. 同步问财股票数据 (优先)
            logger.info("正在同步问财股票数据...")
            wencai_res = await self.tushare_service.sync_wencai_stocks()

            # 3. 同步所有股票日线数据 (增量)
            logger.info("正在同步所有股票日线数据...")
            daily_res = await self.tushare_service.sync_daily_data(mode="incremental")
            
            # 4. 标签股票后续处理: 异动分析 & 评分计算
            if tagged_codes:
                logger.info(f"开始对 {len(tagged_codes)} 只标签股票进行异动分析...")
                processed_vol = 0
                for code in tagged_codes:
                    try:
                        # Analyze stock volume anomalies
                        await VolumeAnalysisService.analyze_stock(code)
                        processed_vol += 1
                        if processed_vol % 10 == 0:
                            logger.info(f"异动分析进度: {processed_vol}/{len(tagged_codes)}")
                    except Exception as e:
                        logger.error(f"Failed to analyze volume for {code}: {e}")
                logger.info("标签股票异动分析完成")
                
                # Calculate scores (Global calculation, but now with updated data for tagged stocks)
                logger.info("开始执行评分计算...")
                await self.rule_engine_service.calculate_daily_scores()
                logger.info("评分计算完成")
                
            logger.info("定时任务: 每日数据同步完成")
            
            # Update Log Success
            processed = daily_res.get("processed", 0) if isinstance(daily_res, dict) else 0
            
            await self.log_repository.update_log(
                log_id=log.id,
                status=SyncTaskStatus.SUCCESS,
                end_time=datetime.now(),
                processed_count=processed,
                message=f"Pool: {pool_stats}, Daily: {daily_res.get('status')}"
            )
            
        except Exception as e:
            logger.error(f"定时任务执行失败: {e}")
            await self.log_repository.update_log(
                log_id=log.id,
                status=SyncTaskStatus.FAILED,
                end_time=datetime.now(),
                message=str(e)
            )

    async def run_csv_health_check(self):
        """执行CSV健康检查"""
        logger.info("定时任务: 开始CSV健康检查")
        
        from app.services.stock_sync_service import StockSyncService
        
        # StockSyncService takes only db_manager in __init__
        sync_service = StockSyncService(self.db_manager)
        
        try:
            result = await sync_service.check_csv_health()
            
            if result['success']:
                if result['error_count'] > 0:
                    logger.warning(f"CSV Health Check Found Issues: {result['error_count']} files. Details: {result['errors']}")
                else:
                    logger.info("CSV Health Check Passed: No issues found.")
            else:
                logger.error(f"CSV Health Check Failed: {result.get('message')}")
        except Exception as e:
            logger.error(f"CSV Health Check Exception: {e}")

    async def run_daily_score(self):
        """执行每日评分计算"""
        logger.info("定时任务: 开始每日评分计算")
        await self.rule_engine_service.calculate_daily_scores()
        logger.info("定时任务: 每日评分计算完成")

# Global instance
scheduler_service = SchedulerService(db_manager)
