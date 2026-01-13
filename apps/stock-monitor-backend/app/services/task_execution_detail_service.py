from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from datetime import datetime, date
from loguru import logger

from app.models.task_execution_detail import TaskExecutionDetail

class TaskExecutionDetailService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_execution_detail(self, detail_data: Dict[str, Any]) -> int:
        """创建执行详细记录，返回ID"""
        detail = TaskExecutionDetail(**detail_data)
        self.db.add(detail)
        await self.db.commit()
        await self.db.refresh(detail)
        return detail.id

    async def update_execution_detail(self, detail_id: int, detail_data: Dict[str, Any]) -> bool:
        """更新执行详细记录"""
        stmt = select(TaskExecutionDetail).where(TaskExecutionDetail.id == detail_id)
        result = await self.db.execute(stmt)
        detail = result.scalar_one_or_none()
        
        if not detail:
            return False
            
        for key, value in detail_data.items():
            if hasattr(detail, key):
                setattr(detail, key, value)
        
        await self.db.commit()
        return True

    async def get_execution_details_by_task_id(
        self, 
        task_id: int, 
        limit: int = 50
    ) -> List[TaskExecutionDetail]:
        """获取任务的所有执行详细记录"""
        stmt = select(TaskExecutionDetail)\
            .where(TaskExecutionDetail.task_id == task_id)\
            .order_by(TaskExecutionDetail.start_time.desc())\
            .limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
