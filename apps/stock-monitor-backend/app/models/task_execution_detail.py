from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Integer, DateTime, Text, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from .base import Base

class TaskExecutionDetail(Base):
    """任务执行详细记录"""
    __tablename__ = "task_execution_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(Integer, index=True, comment="通用任务ID")
    
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="开始时间")
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="结束时间")
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="执行耗时(秒)")
    
    status: Mapped[str] = mapped_column(String(20), default="running", index=True, comment="状态: success/failed/timeout/running")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="错误消息")
    retry_count: Mapped[int] = mapped_column(Integer, default=0, comment="重试次数")
    
    response_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="HTTP响应码")
    response_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="响应数据(部分)")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<TaskExecutionDetail(id={self.id}, task_id={self.task_id}, status='{self.status}')>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
