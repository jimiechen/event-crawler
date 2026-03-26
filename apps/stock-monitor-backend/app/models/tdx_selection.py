#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通达信选股结果数据模型
存储TDX三倍量+涨停选股结果，与问财来源区分
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Integer, String, Date, DateTime, DECIMAL, Text, JSON, Boolean,
    Index, UniqueConstraint, BigInteger
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class TdxSelectionResult(BaseModel):
    """通达信选股结果表 - 三倍量+涨停策略"""
    
    __tablename__ = "tdx_selection_result"
    __table_args__ = (
        UniqueConstraint("stock_code", "trade_date", name="uk_tdx_selection_code_date"),
        Index("idx_tdx_selection_date", "trade_date"),
        Index("idx_tdx_selection_code", "stock_code"),
        Index("idx_tdx_selection_sector", "sector_code"),
        Index("idx_tdx_selection_source", "source"),
        {"comment": "通达信选股结果表 - 三倍量+涨停策略"}
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    stock_code: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        comment="股票代码"
    )
    
    stock_name: Mapped[str] = mapped_column(
        String(100), 
        nullable=True, 
        comment="股票名称"
    )
    
    trade_date: Mapped[date] = mapped_column(
        Date, 
        nullable=False, 
        comment="选股日期"
    )
    
    sector_code: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        comment="板块代码(如: 3BL0325)"
    )
    
    sector_name: Mapped[str] = mapped_column(
        String(100), 
        nullable=True, 
        comment="板块名称"
    )
    
    # 价格数据
    open_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 3), 
        nullable=True, 
        comment="开盘价"
    )
    
    close_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 3), 
        nullable=True, 
        comment="收盘价"
    )
    
    high_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 3), 
        nullable=True, 
        comment="最高价"
    )
    
    low_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 3), 
        nullable=True, 
        comment="最低价"
    )
    
    prev_close: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 3), 
        nullable=True, 
        comment="昨收价"
    )
    
    # 成交量数据
    volume: Mapped[int] = mapped_column(
        BigInteger, 
        nullable=True, 
        comment="成交量(手)"
    )
    
    prev_volume: Mapped[int] = mapped_column(
        BigInteger, 
        nullable=True, 
        comment="前一日成交量(手)"
    )
    
    volume_ratio: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 4), 
        nullable=True, 
        comment="成交量比值(当日/前日)"
    )
    
    amount: Mapped[Decimal] = mapped_column(
        DECIMAL(20, 3), 
        nullable=True, 
        comment="成交额(千元)"
    )
    
    # 涨跌幅
    change_percent: Mapped[Decimal] = mapped_column(
        DECIMAL(8, 4), 
        nullable=True, 
        comment="涨跌幅(%)"
    )
    
    limit_up_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 3), 
        nullable=True, 
        comment="涨停价"
    )
    
    is_limit_up: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        comment="是否涨停"
    )
    
    # 策略标记
    strategy_name: Mapped[str] = mapped_column(
        String(50), 
        default="3x_volume_limit_up", 
        comment="策略名称"
    )
    
    # 数据来源标记 - 区分TDX和问财
    source: Mapped[str] = mapped_column(
        String(20), 
        default="tdx", 
        comment="数据来源(tdx/wencai)"
    )
    
    # 截图路径
    screenshot_path: Mapped[str] = mapped_column(
        String(500), 
        nullable=True, 
        comment="截图文件路径"
    )
    
    # 飞书同步状态
    feishu_synced: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        comment="是否已同步到飞书"
    )
    
    feishu_sync_time: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=True, 
        comment="飞书同步时间"
    )
    
    feishu_record_id: Mapped[str] = mapped_column(
        String(100), 
        nullable=True, 
        comment="飞书多维表格记录ID"
    )
    
    # 扩展数据
    extra_data: Mapped[dict] = mapped_column(
        JSON, 
        nullable=True, 
        comment="扩展数据(JSON格式)"
    )
    
    # 备注
    remark: Mapped[str] = mapped_column(
        Text, 
        nullable=True, 
        comment="备注"
    )


class TdxSelectionBatch(BaseModel):
    """通达信选股批次表 - 记录每次选股操作的批次信息"""
    
    __tablename__ = "tdx_selection_batch"
    __table_args__ = (
        Index("idx_tdx_batch_date", "trade_date"),
        Index("idx_tdx_batch_sector", "sector_code"),
        Index("idx_tdx_batch_status", "status"),
        {"comment": "通达信选股批次表"}
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    batch_id: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False, 
        comment="批次ID"
    )
    
    trade_date: Mapped[date] = mapped_column(
        Date, 
        nullable=False, 
        comment="选股日期"
    )
    
    sector_code: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        comment="板块代码"
    )
    
    sector_name: Mapped[str] = mapped_column(
        String(100), 
        nullable=True, 
        comment="板块名称"
    )
    
    strategy_name: Mapped[str] = mapped_column(
        String(50), 
        default="3x_volume_limit_up", 
        comment="策略名称"
    )
    
    total_stocks: Mapped[int] = mapped_column(
        Integer, 
        default=0, 
        comment="选股总数"
    )
    
    limit_up_count: Mapped[int] = mapped_column(
        Integer, 
        default=0, 
        comment="涨停股票数"
    )
    
    high_volume_count: Mapped[int] = mapped_column(
        Integer, 
        default=0, 
        comment="高成交量股票数"
    )
    
    # 执行状态
    status: Mapped[str] = mapped_column(
        String(20), 
        default="running", 
        comment="状态: pending/running/completed/failed"
    )
    
    # 各阶段状态
    data_sync_status: Mapped[str] = mapped_column(
        String(20), 
        default="pending", 
        comment="数据同步状态"
    )
    
    selection_status: Mapped[str] = mapped_column(
        String(20), 
        default="pending", 
        comment="选股状态"
    )
    
    screenshot_status: Mapped[str] = mapped_column(
        String(20), 
        default="pending", 
        comment="截图状态"
    )
    
    feishu_sync_status: Mapped[str] = mapped_column(
        String(20), 
        default="pending", 
        comment="飞书同步状态"
    )
    
    # 时间记录
    started_at: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=True, 
        comment="开始时间"
    )
    
    completed_at: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=True, 
        comment="完成时间"
    )
    
    # 耗时(秒)
    duration: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), 
        nullable=True, 
        comment="耗时(秒)"
    )
    
    # 错误信息
    error_message: Mapped[str] = mapped_column(
        Text, 
        nullable=True, 
        comment="错误信息"
    )
    
    # 数据来源
    source: Mapped[str] = mapped_column(
        String(20), 
        default="tdx", 
        comment="数据来源(tdx/wencai)"
    )
