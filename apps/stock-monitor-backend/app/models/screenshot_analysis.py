#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
截图分析相关数据模型
支持三龙聚首指标、K/D信号、主力控盘识别
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    BigInteger, Boolean, DateTime, Integer, String, Text, Index, JSON, DECIMAL
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class ScreenshotAnalysis(BaseModel):
    """股票截图分析记录表"""
    
    __tablename__ = "screenshot_analysis"
    __table_args__ = (
        Index("idx_screenshot_stock_code", "stock_code"),
        Index("idx_screenshot_task_id", "task_id"),
        Index("idx_screenshot_status", "status"),
        Index("idx_screenshot_pattern", "detected_pattern"),
        Index("idx_screenshot_created_at", "created_at"),
        Index("idx_screenshot_batch_id", "batch_id"),
        {"comment": "股票截图分析记录表"}
    )
    
    # 主键
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="主键ID"
    )
    
    # 任务信息
    task_id: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="任务ID"
    )
    batch_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="批次ID"
    )
    
    # 股票信息
    stock_code: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="股票代码"
    )
    stock_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="股票名称"
    )
    industry: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="所属行业"
    )
    
    # 截图类型: tlby=天龙博弈日K, fenxi=分时图, kline=普通K线
    screenshot_type: Mapped[str] = mapped_column(
        String(20), default="tlby", comment="截图类型"
    )
    
    # Base64图片数据
    image_data: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Base64图片数据"
    )
    image_format: Mapped[str] = mapped_column(
        String(10), default="png", comment="图片格式"
    )
    image_size: Mapped[int] = mapped_column(
        Integer, default=0, comment="图片大小(字节)"
    )
    
    # 来源信息
    source_ip: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="来源IP"
    )
    agent_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Agent标识"
    )
    
    # 状态: pending/analyzing/completed/failed
    status: Mapped[str] = mapped_column(
        String(20), default="pending", comment="状态"
    )
    
    # AI识别基础数据
    ai_price: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 3), nullable=True, comment="AI识别价格"
    )
    ai_change_percent: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4), nullable=True, comment="AI识别涨跌幅"
    )
    ai_volume: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="AI识别成交量"
    )
    ai_amount: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(15, 2), nullable=True, comment="AI识别成交额"
    )
    
    # 三龙聚首指标
    sanlong_trend_alert: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="趋势警戒 0/1"
    )
    sanlong_volume_alert: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="量能警戒 0/1"
    )
    sanlong_mid_alert: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="中期警戒 0/1"
    )
    sanlong_short_alert: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="短期警戒 0/1"
    )
    sanlong_alert_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="亮灯数量0-4"
    )
    sanlong_all_red: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, comment="是否全红警戒"
    )
    
    # K/D信号
    has_k_signal_today: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, comment="今天是否有K信号"
    )
    has_d_signal_today: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, comment="今天是否有D信号"
    )
    k_signal_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="K信号数量"
    )
    d_signal_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="D信号数量"
    )
    
    # 形态识别
    detected_pattern: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="识别形态"
    )
    pattern_confidence: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(3, 2), nullable=True, comment="形态置信度"
    )
    
    # 主力控盘数据
    main_force_buy_ratio: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(5, 2), nullable=True, comment="主力买入占比"
    )
    main_force_sell_ratio: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(5, 2), nullable=True, comment="主力卖出占比"
    )
    retail_buy_ratio: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(5, 2), nullable=True, comment="散户买入占比"
    )
    retail_sell_ratio: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(5, 2), nullable=True, comment="散户卖出占比"
    )
    
    # AI结果
    ai_result: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, comment="AI完整识别结果"
    )
    ai_model: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="AI模型"
    )
    ai_analysis_text: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="AI分析文本"
    )
    
    # 数据比对结果
    verification_result: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, comment="数据比对结果"
    )
    is_data_match: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, comment="数据是否匹配"
    )
    match_confidence: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(3, 2), nullable=True, comment="匹配置信度"
    )
    
    # 错误信息
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="错误信息"
    )
    
    # 时间戳
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="分析完成时间"
    )
    callback_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="回调发送时间"
    )
