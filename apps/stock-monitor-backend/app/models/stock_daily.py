#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务相关数据模型
包含日线数据、评分结果、任务日志等
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Integer, String, Date, DateTime, DECIMAL, Text, JSON,
    Index, UniqueConstraint, BigInteger
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel

class StockDaily(BaseModel):
    """股票日线数据表"""
    __tablename__ = "stock_daily"
    __table_args__ = (
        UniqueConstraint("code", "trade_date", name="uk_stock_daily_code_date"),
        Index("idx_stock_daily_date", "trade_date"),
        Index("idx_stock_daily_code", "code"),
        {"comment": "股票日线数据表"}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, comment="股票代码")
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, comment="交易日期")
    
    open: Mapped[Decimal] = mapped_column(DECIMAL(10, 3), nullable=True, comment="开盘价")
    close: Mapped[Decimal] = mapped_column(DECIMAL(10, 3), nullable=True, comment="收盘价")
    high: Mapped[Decimal] = mapped_column(DECIMAL(10, 3), nullable=True, comment="最高价")
    low: Mapped[Decimal] = mapped_column(DECIMAL(10, 3), nullable=True, comment="最低价")
    vol: Mapped[int] = mapped_column(BigInteger, nullable=True, comment="成交量(手)")
    amount: Mapped[Decimal] = mapped_column(DECIMAL(20, 3), nullable=True, comment="成交额(千元)")
    
    turnover_rate: Mapped[Decimal] = mapped_column(DECIMAL(10, 4), nullable=True, comment="换手率(%)")
    volume_ratio: Mapped[Decimal] = mapped_column(DECIMAL(10, 4), nullable=True, comment="量比")

    adj_factor: Mapped[Decimal] = mapped_column(DECIMAL(10, 4), nullable=True, comment="复权因子")

class StockDailyTemp(BaseModel):
    """临时股票日线数据表(用于形态初筛)"""
    __tablename__ = "stock_daily_temp"
    __table_args__ = (
        UniqueConstraint("code", "trade_date", name="uk_stock_daily_temp_code_date"),
        Index("idx_stock_daily_temp_date", "trade_date"),
        Index("idx_stock_daily_temp_status", "status"),
        Index("idx_stock_daily_temp_created", "created_at"),
        {"comment": "临时股票日线数据表"}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, comment="股票代码")
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, comment="交易日期")
    
    open: Mapped[Decimal] = mapped_column(DECIMAL(10, 3), nullable=True, comment="开盘价")
    close: Mapped[Decimal] = mapped_column(DECIMAL(10, 3), nullable=True, comment="收盘价")
    high: Mapped[Decimal] = mapped_column(DECIMAL(10, 3), nullable=True, comment="最高价")
    low: Mapped[Decimal] = mapped_column(DECIMAL(10, 3), nullable=True, comment="最低价")
    vol: Mapped[int] = mapped_column(BigInteger, nullable=True, comment="成交量(手)")
    amount: Mapped[Decimal] = mapped_column(DECIMAL(20, 3), nullable=True, comment="成交额(千元)")
    
    turnover_rate: Mapped[Decimal] = mapped_column(DECIMAL(10, 4), nullable=True, comment="换手率(%)")
    
    # 扩展字段
    industry: Mapped[str] = mapped_column(String(50), nullable=True, comment="所属行业")
    concept: Mapped[str] = mapped_column(Text, nullable=True, comment="所属概念")
    
    # 状态字段
    status: Mapped[str] = mapped_column(String(20), default="pending", comment="状态: pending/passed/rejected")
    reject_reason: Mapped[str] = mapped_column(String(200), nullable=True, comment="拒绝原因")
    source: Mapped[str] = mapped_column(String(50), default="wencai", comment="数据来源")

class StockScoreResult(BaseModel):
    """股票评分结果表"""
    __tablename__ = "stock_score_result"
    __table_args__ = (
        UniqueConstraint("code", "trade_date", name="uk_stock_score_code_date"),
        Index("idx_stock_score_date", "trade_date"),
        Index("idx_stock_score_total", "total_score"),
        Index("idx_stock_score_date_code", "trade_date", "code"), # Optimization for aggregation
        {"comment": "股票评分结果表"}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, comment="股票代码")
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, comment="评分日期")
    
    rule_scores: Mapped[dict] = mapped_column(JSON, nullable=True, comment="各规则得分详情")
    daily_score: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=0, comment="每日得分")
    accumulated_score: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=0, comment="累计得分")
    total_score: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=0, comment="总分(兼容字段，同accumulated_score)")
    ranking: Mapped[int] = mapped_column(Integer, nullable=True, comment="排名")
    
    pool_type: Mapped[str] = mapped_column(String(20), default="unknown", comment="股票池类型(self_selected/wencai)")

class TaskLog(BaseModel):
    """定时任务执行日志"""
    __tablename__ = "task_execution_log"
    __table_args__ = (
        Index("idx_task_log_created", "created_at"),
        Index("idx_task_log_name", "task_name"),
        {"comment": "定时任务执行日志"}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="任务名称")
    stock_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="股票代码(可选)")
    status: Mapped[str] = mapped_column(String(20), nullable=False, comment="状态(success/failed/running)")
    message: Mapped[str] = mapped_column(Text, nullable=True, comment="执行消息/错误信息")
    duration: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=True, comment="耗时(秒)")
