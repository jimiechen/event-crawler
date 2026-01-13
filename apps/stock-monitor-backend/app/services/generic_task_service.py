from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime
from loguru import logger
from croniter import croniter

from app.models.generic_task import GenericTask

class GenericTaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_generic_task(self, task_data: Dict[str, Any]) -> GenericTask:
        """创建通用任务"""
        task = GenericTask(**task_data)
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_all_generic_tasks(self) -> List[GenericTask]:
        """获取所有通用任务"""
        stmt = select(GenericTask).order_by(GenericTask.priority, GenericTask.id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_generic_task_by_id(self, task_id: int) -> Optional[GenericTask]:
        """根据ID获取任务"""
        stmt = select(GenericTask).where(GenericTask.id == task_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_generic_task(self, task_id: int, task_data: Dict[str, Any]) -> Optional[GenericTask]:
        """更新通用任务"""
        task = await self.get_generic_task_by_id(task_id)
        if not task:
            return None
        
        for key, value in task_data.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def delete_generic_task(self, task_id: int) -> bool:
        """删除通用任务"""
        stmt = delete(GenericTask).where(GenericTask.id == task_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def toggle_generic_task(self, task_id: int, enabled: bool) -> Optional[GenericTask]:
        """启用/禁用通用任务"""
        return await self.update_generic_task(task_id, {"is_active": enabled})

    async def batch_create_generic_tasks(self, tasks_data: List[Dict[str, Any]]) -> List[GenericTask]:
        """批量创建通用任务"""
        tasks = [GenericTask(**data) for data in tasks_data]
        self.db.add_all(tasks)
        await self.db.commit()
        for task in tasks:
            await self.db.refresh(task)
        return tasks

    async def batch_toggle_generic_tasks(self, task_ids: List[int], enabled: bool) -> List[int]:
        """批量启用/禁用通用任务"""
        stmt = update(GenericTask).where(GenericTask.id.in_(task_ids)).values(is_active=enabled)
        await self.db.execute(stmt)
        await self.db.commit()
        return task_ids

    async def get_active_tasks(self) -> List[GenericTask]:
        """获取所有启用的任务"""
        stmt = select(GenericTask).where(GenericTask.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_next_run_time(self, cron_expression: str) -> datetime:
        """获取下次运行时间"""
        iter = croniter(cron_expression, datetime.now())
        return iter.get_next(datetime)
