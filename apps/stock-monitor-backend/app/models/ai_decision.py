#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Decision Result Model
"""

from datetime import datetime, date
from typing import Dict, Any, Optional
from sqlalchemy import String, Integer, DateTime, Text, JSON, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

class AIDecisionResult(BaseModel):
    """AI决策结果表"""
    __tablename__ = "ai_decision_results"
    __table_args__ = (
        {"comment": "AI决策结果表"}
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(20), index=True, nullable=False, comment="股票代码")
    trade_date: Mapped[date] = mapped_column(Date, index=True, nullable=False, comment="交易日期")
    
    # Decision content
    decision_json: Mapped[Dict[str, Any]] = mapped_column(JSON, comment="完整决策JSON")
    
    # Metadata
    model_name: Mapped[str] = mapped_column(String(50), comment="模型名称")
    template_name: Mapped[str] = mapped_column(String(50), nullable=True, comment="模板名称")
    
    # Summary fields for easy querying
    primary_operation: Mapped[str] = mapped_column(String(20), nullable=True, comment="主要操作(buy/sell/hold)")
    primary_reason: Mapped[str] = mapped_column(Text, nullable=True, comment="主要理由")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
