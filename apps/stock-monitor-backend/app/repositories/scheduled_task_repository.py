#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务仓储层
"""

from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models.scheduled_task import ScheduledTask
from app.database import DatabaseManager

class ScheduledTaskRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def get_all_tasks(self) -> List[ScheduledTask]:
        async with self.db_manager.get_session() as session:
            stmt = select(ScheduledTask)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_task_by_type(self, task_type: str) -> Optional[ScheduledTask]:
        async with self.db_manager.get_session() as session:
            stmt = select(ScheduledTask).where(ScheduledTask.task_type == task_type)
            result = await session.execute(stmt)
            return result.scalars().first()
            
    async def get_task_by_id(self, task_id: int) -> Optional[ScheduledTask]:
        async with self.db_manager.get_session() as session:
            stmt = select(ScheduledTask).where(ScheduledTask.id == task_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def create_task(self, task: ScheduledTask) -> ScheduledTask:
        async with self.db_manager.get_session() as session:
            session.add(task)
            await session.commit()
            await session.refresh(task)
            return task

    async def update_task_status(self, task_id: int, status: str, last_run_at: datetime = None, next_run_at: datetime = None):
        async with self.db_manager.get_session() as session:
            stmt = update(ScheduledTask).where(ScheduledTask.id == task_id).values(
                last_run_status=status
            )
            if last_run_at:
                stmt = stmt.values(last_run_at=last_run_at)
            if next_run_at:
                stmt = stmt.values(next_run_at=next_run_at)
                
            await session.execute(stmt)
            await session.commit()
            
    async def update_task_config(self, task_id: int, cron_expression: str = None, is_active: bool = None):
        async with self.db_manager.get_session() as session:
            stmt = update(ScheduledTask).where(ScheduledTask.id == task_id)
            if cron_expression is not None:
                stmt = stmt.values(cron_expression=cron_expression)
            if is_active is not None:
                stmt = stmt.values(is_active=is_active)
            
            await session.execute(stmt)
            await session.commit()
