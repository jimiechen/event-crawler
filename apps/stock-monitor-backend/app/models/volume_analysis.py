#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成交量异动分析相关模型
包含异动分析结果、规则计算日志和提醒记录
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Integer, String, Date, DateTime, DECIMAL, Text, JSON,
    Index, UniqueConstraint, BigInteger, Boolean
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel

class VolumeAnalysisResult(BaseModel):
    """成交量异动分析结果表"""
    __tablename__ = "volume_analysis_result"
    __table_args__ = (
        Index("idx_vol_analysis_code_date", "code", "trade_date"),
        Index("idx_vol_analysis_type", "analysis_type"),
        Index("idx_vol_analysis_code_type_date", "code", "analysis_type", "trade_date"),
        UniqueConstraint("code", "trade_date", "analysis_type", name="idx_unique_analysis"),
        {"comment": "成交量异动分析结果表"}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, comment="股票代码")
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, comment="交易日期")
    
    # Analysis Type: '2x_close', '3x_close', '5d_low_vol', '10d_low_vol', etc.
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="分析类型")
    
    # Value: Close Price (for 2x/3x) or Volume (for Low Vol)
    value: Mapped[Decimal] = mapped_column(DECIMAL(20, 3), nullable=False, comment="关键值(价格或成交量)")
    
    description: Mapped[str] = mapped_column(String(255), nullable=True, comment="描述")
    extra_data: Mapped[dict] = mapped_column(JSON, nullable=True, comment="额外数据")


class RuleCalculationLog(BaseModel):
    """规则计算日志表"""
    __tablename__ = "rule_calculation_log"
    __table_args__ = (
        Index("idx_rule_log_code", "code"),
        Index("idx_rule_log_created", "created_at"),
        {"comment": "规则计算日志表"}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, comment="股票代码")
    rule_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="规则名称")
    is_match: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否符合规则")
    details: Mapped[str] = mapped_column(Text, nullable=True, comment="计算详情")
    

class AlertRecord(BaseModel):
    """提醒记录表"""
    __tablename__ = "alert_record"
    __table_args__ = (
        Index("idx_alert_code", "code"),
        Index("idx_alert_type", "alert_type"),
        {"comment": "提醒记录表"}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, comment="股票代码")
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="提醒类型(Price/Volume)")
    message: Mapped[str] = mapped_column(Text, nullable=False, comment="提醒消息")
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已发送")

class StockVolumeBaseline(BaseModel):
    """股票成交量异动基准表"""
    __tablename__ = "stock_volume_baseline"
    __table_args__ = (
        {"comment": "股票成交量异动基准表"}
    )

    code: Mapped[str] = mapped_column(String(20), primary_key=True, comment="股票代码")
    
    # 3倍量信息
    last_3x_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="最近一次3倍量日期")
    last_3x_close: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 3), nullable=True, comment="最近一次3倍量收盘价")
    
    # 2倍量信息
    last_2x_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="最近一次2倍量日期")
    last_2x_close: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 3), nullable=True, comment="最近一次2倍量收盘价")
    
    # 地量信息 - 5日
    last_5d_low_vol_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="最近一次5日地量日期")
    last_5d_low_vol: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 3), nullable=True, comment="最近一次5日地量成交量")

    # 地量信息 - 10日
    last_10d_low_vol_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="最近一次10日地量日期")
    last_10d_low_vol: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 3), nullable=True, comment="最近一次10日地量成交量")
    
    # 地量信息 - 20日
    last_20d_low_vol_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="最近一次20日地量日期")
    last_20d_low_vol: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 3), nullable=True, comment="最近一次20日地量成交量")
    
    # 地量信息 - 30日
    last_30d_low_vol_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="最近一次30日地量日期")
    last_30d_low_vol: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 3), nullable=True, comment="最近一次30日地量成交量")
    
    # 地量信息 - 60日
    last_60d_low_vol_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="最近一次60日地量日期")
    last_60d_low_vol: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 3), nullable=True, comment="最近一次60日地量成交量")
