#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步任务日志仓储层
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import db_manager
from app.models.sync_log import SyncTaskLog, SyncTaskType, SyncTaskStatus

class SyncLogRepository:
    """同步任务日志仓储"""
    
    def __init__(self, db_manager=db_manager):
        self.db_manager = db_manager

    async def create_log(self, 
                         task_type: SyncTaskType, 
                         batch_id: Optional[int] = None, 
                         start_time: Optional[Any] = None) -> SyncTaskLog:
        """创建日志"""
        async with self.db_manager.get_session() as session:
            log = SyncTaskLog(
                task_type=task_type.value,
                batch_id=batch_id,
                status=SyncTaskStatus.RUNNING.value,
                start_time=start_time if start_time else datetime.now(),
                processed_count=0,
                inserted_count=0,
                error_count=0
            )
            session.add(log)
            await session.commit()
            await session.refresh(log)
            return log

    async def update_log(self, 
                         log_id: int, 
                         status: SyncTaskStatus, 
                         end_time: Optional[Any] = None,
                         message: Optional[str] = None,
                         processed_count: Optional[int] = None,
                         inserted_count: Optional[int] = None,
                         error_count: Optional[int] = None) -> Optional[SyncTaskLog]:
        """更新日志"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(select(SyncTaskLog).where(SyncTaskLog.id == log_id))
            log = result.scalar_one_or_none()
            
            if log:
                log.status = status.value
                if end_time:
                    log.end_time = end_time
                if message is not None:
                    log.message = message
                if processed_count is not None:
                    log.processed_count = processed_count
                if inserted_count is not None:
                    log.inserted_count = inserted_count
                if error_count is not None:
                    log.error_count = error_count
                
                await session.commit()
                await session.refresh(log)
                return log
            return None

    async def get_logs(self, 
                       limit: int = 50, 
                       offset: int = 0, 
                       task_type: Optional[str] = None,
                       batch_id: Optional[int] = None) -> List[SyncTaskLog]:
        """查询日志"""
        async with self.db_manager.get_session() as session:
            stmt = select(SyncTaskLog).order_by(desc(SyncTaskLog.start_time))
            
            if task_type:
                stmt = stmt.where(SyncTaskLog.task_type == task_type)
            if batch_id:
                stmt = stmt.where(SyncTaskLog.batch_id == batch_id)
                
            stmt = stmt.limit(limit).offset(offset)
            
            result = await session.execute(stmt)
            return result.scalars().all()
