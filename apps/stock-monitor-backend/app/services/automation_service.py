from typing import List, Optional, Dict, Any
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import json

from app.models.automation import AutomationConfig, AutomationTask, AutomationLog
from app.repositories.base import BaseRepository

class AutomationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.config_repo = BaseRepository(AutomationConfig, db)
        self.task_repo = BaseRepository(AutomationTask, db)
        self.log_repo = BaseRepository(AutomationLog, db)

    async def get_config(self, device_model: str, resolution: str, app_version: str) -> Optional[AutomationConfig]:
        """根据设备信息获取配置"""
        query = select(AutomationConfig).where(
            AutomationConfig.device_model == device_model,
            AutomationConfig.resolution == resolution,
            AutomationConfig.app_version == app_version,
            AutomationConfig.is_active == True
        ).order_by(desc(AutomationConfig.updated_at))
        
        result = await self.db.execute(query)
        return result.scalars().first()

    async def save_config(self, config_data: Dict[str, Any]) -> AutomationConfig:
        """保存或更新配置"""
        # 查找是否存在现有配置
        existing = await self.get_config(
            config_data["device_model"],
            config_data["resolution"],
            config_data["app_version"]
        )
        
        if existing:
            existing.config_data = config_data["config_data"]
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            new_config = AutomationConfig(
                device_model=config_data["device_model"],
                resolution=config_data["resolution"],
                app_version=config_data["app_version"],
                config_data=config_data["config_data"]
            )
            self.db.add(new_config)
            await self.db.commit()
            await self.db.refresh(new_config)
            return new_config

    async def create_task(self, task_data: Dict[str, Any]) -> AutomationTask:
        """创建新任务"""
        task = AutomationTask(**task_data)
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def update_task_status(self, task_id: int, status: str, result: Optional[Dict[str, Any]] = None) -> Optional[AutomationTask]:
        """更新任务状态"""
        task = await self.task_repo.get(task_id)
        if task:
            task.status = status
            if result:
                task.result_data = result
            await self.db.commit()
            await self.db.refresh(task)
        return task

    async def log_event(self, log_data: Dict[str, Any]) -> AutomationLog:
        """记录日志"""
        log = AutomationLog(**log_data)
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log
