#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务日志仓库
"""

from typing import List, Optional, Any, Dict
from datetime import datetime, timedelta
from sqlalchemy import select, update, desc, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task_log import TaskExecutionLog
from app.repositories.base import BaseRepository
from app.database import DatabaseManager

class TaskExecutionLogRepository(BaseRepository[TaskExecutionLog]):
    def __init__(self, db_manager: DatabaseManager):
        # 注意: BaseRepository 需要 session，但这里的 BaseRepository 设计可能需要调整或我们在方法里获取 session
        # 观察 BaseRepository 实现，它接收 session。
        # 但为了方便 Service 调用，通常 Repository 可能会自己管理 session 或者由 Service 传入。
        # 现有的 StockDailyRepository 接收 db_manager，我们保持一致。
        self.db_manager = db_manager
        # self.model = TaskExecutionLog # BaseRepository needs this but we can't call super().__init__ easily if we don't have session yet.
        # Let's override methods or use a context manager pattern like other repos likely do.
        pass

    async def create_log(self, task_type: str, task_url: str, stock_code: str) -> TaskExecutionLog:
        async with self.db_manager.get_session() as session:
            log = TaskExecutionLog(
                task_type=task_type,
                task_url=task_url,
                stock_code=stock_code,
                status="pending",
                created_at=datetime.now()
            )
            session.add(log)
            await session.commit()
            await session.refresh(log)
            return log

    async def batch_create_logs(self, logs_data: List[Dict[str, Any]]) -> int:
        """批量创建日志"""
        async with self.db_manager.get_session() as session:
            try:
                # 转换 dict 为 model 对象
                logs = [TaskExecutionLog(**data, status="pending", created_at=datetime.now()) for data in logs_data]
                session.add_all(logs)
                await session.commit()
                return len(logs)
            except Exception as e:
                await session.rollback()
                raise e

    async def update_status(self, log_id: int, status: str, result_message: str = None):
        async with self.db_manager.get_session() as session:
            stmt = update(TaskExecutionLog).where(TaskExecutionLog.id == log_id).values(
                status=status,
                result_message=result_message,
                executed_at=datetime.now() if status in ["success", "failed"] else None
            )
            await session.execute(stmt)
            await session.commit()

    async def get_log_by_id(self, log_id: int) -> Optional[TaskExecutionLog]:
        async with self.db_manager.get_session() as session:
            query = select(TaskExecutionLog).where(TaskExecutionLog.id == log_id)
            result = await session.execute(query)
            return result.scalars().first()

    async def get_logs(
        self, 
        skip: int = 0, 
        limit: int = 50, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        stock_code: Optional[str] = None,
        status: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> tuple[List[TaskExecutionLog], int]:
        async with self.db_manager.get_session() as session:
            query = select(TaskExecutionLog)
            
            conditions = []
            if start_date:
                # 假设 created_at 是 DateTime
                conditions.append(TaskExecutionLog.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
            if end_date:
                conditions.append(TaskExecutionLog.created_at < datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))
            if stock_code:
                conditions.append(TaskExecutionLog.stock_code.like(f"%{stock_code}%"))
            if status:
                conditions.append(TaskExecutionLog.status == status)
            if task_type:
                conditions.append(TaskExecutionLog.task_type == task_type)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Count
            count_query = select(func.count()).select_from(TaskExecutionLog)
            if conditions:
                count_query = count_query.where(and_(*conditions))
            
            total = (await session.execute(count_query)).scalar() or 0
            
            # Paging
            query = query.order_by(desc(TaskExecutionLog.id)).offset(skip).limit(limit)
            
            result = await session.execute(query)
            return result.scalars().all(), total

    async def get_pending_tasks(self, limit: int = 10) -> List[TaskExecutionLog]:
        """获取待执行任务"""
        async with self.db_manager.get_session() as session:
            query = select(TaskExecutionLog).where(TaskExecutionLog.status == "pending").limit(limit)
            result = await session.execute(query)
            return result.scalars().all()
