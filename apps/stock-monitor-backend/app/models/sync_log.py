#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步任务日志模型
"""

from enum import Enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

class SyncTaskType(str, Enum):
    CSV_FULL = "csv_full"
    TUSHARE_INCREMENT = "tushare_increment"
    DAILY_INCREMENT = "daily_increment"

class SyncTaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

class SyncTaskLog(BaseModel):
    """同步任务日志表"""
    
    __tablename__ = "sync_task_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="日志ID")
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="任务类型")
    batch_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="关联批次ID")
    status: Mapped[str] = mapped_column(String(20), default=SyncTaskStatus.PENDING.value, comment="任务状态")
    
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="开始时间")
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="结束时间")
    
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="日志详情/错误信息")
    processed_count: Mapped[int] = mapped_column(Integer, default=0, comment="处理数量")
    inserted_count: Mapped[int] = mapped_column(Integer, default=0, comment="插入数量")
    error_count: Mapped[int] = mapped_column(Integer, default=0, comment="错误数量")

    def __repr__(self):
        return f"<SyncTaskLog(id={self.id}, type={self.task_type}, status={self.status})>"
