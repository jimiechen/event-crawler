
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缠论量价分析配置与股票池模型
"""

from datetime import datetime
from sqlalchemy import Integer, String, Boolean, JSON, DECIMAL, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel

class PatternConfig(BaseModel):
    """形态评分配置表"""
    __tablename__ = "pattern_configs"
    __table_args__ = (
        Index("idx_pattern_code", "pattern_code", unique=True),
        {"comment": "形态评分配置表"}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pattern_code: Mapped[str] = mapped_column(String(50), nullable=False, comment="形态代码")
    pattern_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="形态名称")
    description: Mapped[str] = mapped_column(Text, nullable=True, comment="描述")
    score: Mapped[int] = mapped_column(Integer, default=0, comment="分值")
    days: Mapped[int] = mapped_column(Integer, default=1, comment="形态天数(1/2/3)")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    priority: Mapped[int] = mapped_column(Integer, default=1, comment="优先级")
    conflict_rule: Mapped[str] = mapped_column(String(20), default="add", comment="冲突处理: add(叠加)/replace(覆盖)")

class PatternStockPool(BaseModel):
    """缠论量价股票池"""
    __tablename__ = "pattern_stock_pool"
    __table_args__ = (
        Index("idx_pool_code", "stock_code", unique=True),
        Index("idx_pool_status", "status"),
        Index("idx_pool_score", "score"),
        {"comment": "缠论量价股票池"}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False, comment="股票代码")
    stock_name: Mapped[str] = mapped_column(String(50), nullable=True, comment="股票名称")
    
    score: Mapped[int] = mapped_column(Integer, default=0, comment="当前评分")
    patterns: Mapped[dict] = mapped_column(JSON, nullable=True, comment="命中的形态列表")
    
    industry: Mapped[str] = mapped_column(String(50), nullable=True, comment="行业")
    concept: Mapped[str] = mapped_column(Text, nullable=True, comment="概念")
    
    status: Mapped[str] = mapped_column(String(20), default="watch", comment="状态: core(核心)/watch(观察)/rejected(淘汰)")
    
    last_analyzed_at: Mapped[datetime] = mapped_column(nullable=True, comment="最后分析时间")
