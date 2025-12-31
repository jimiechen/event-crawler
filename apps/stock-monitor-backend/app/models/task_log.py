#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务执行日志模型
用于记录单只股票任务的创建、执行状态和结果
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

class TaskExecutionLog(BaseModel):
    """任务执行日志表"""
    
    __tablename__ = "batch_task_execution_log"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="日志ID")
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="任务类型: csv_sync, tushare_sync, calculate")
    task_url: Mapped[str] = mapped_column(String(500), nullable=False, comment="执行URL")
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False, comment="股票代码")
    
    status: Mapped[str] = mapped_column(String(20), default="pending", comment="状态: pending, running, success, failed")
    result_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="执行结果信息")
    
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="执行时间")

    def __repr__(self):
        return f"<TaskExecutionLog(id={self.id}, code={self.stock_code}, type={self.task_type}, status={self.status})>"
