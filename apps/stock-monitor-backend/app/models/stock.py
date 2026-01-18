#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
"""
股票相关数据模型
包含股票信息、股票数据、监控列表和数据去重日志模型
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    BigInteger, Boolean, DateTime, Date, Integer, String, Text,
    DECIMAL, Index, UniqueConstraint, JSON, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel, BaseModelOnlyCreated, Base


class StockInfo(BaseModel):
    """股票基本信息表"""
    
    __tablename__ = "stock_info"
    __table_args__ = (
        Index("idx_code", "code"),
        Index("idx_market", "market"),
        Index("idx_status", "is_active"),
        {"comment": "股票基本信息表"}
    )
    
    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="主键ID"
    )
    
    code: Mapped[str] = mapped_column(
        String(20), 
        unique=True, 
        nullable=False,
        comment="股票代码"
    )
    
    name: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="股票名称"
    )
    
    market: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default="unknown",
        comment="市场类型(sh/sz/unknown)"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        comment="是否活跃"
    )

    source: Mapped[str] = mapped_column(
        String(20),
        nullable=True,
        default="unknown",
        comment="来源(self_selected/wencai)"
    )

    latest_price: Mapped[float] = mapped_column(
        DECIMAL(10, 3),
        nullable=True,
        comment="最新价格"
    )

    sync_250d_kline: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否同步250日K线"
    )

    sync_incremental: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否开启增量同步"
    )

    is_held: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否持仓"
    )

    volume_anomaly_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="成交量异动总分"
    )

    tdx_plugin_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="TDX插件评分"
    )

    score_update_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        comment="最新评分更新时间"
    )

    bonus_items: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="加分项(JSON)"
    )
    
    # 注意：由于不使用物理外键约束，暂时不定义ORM关系映射
    # 可以通过查询来获取相关数据


class StockData(BaseModel):
    """股票实时数据表"""
    
    __tablename__ = "stock_prices"
    __table_args__ = (
        Index("idx_stock_prices_code", "symbol"),
        Index("idx_stock_prices_timestamp", "trade_date"),
        Index("idx_stock_prices_code_timestamp", "symbol", "trade_date"),
        Index("idx_stock_prices_created_at", "created_at"),
        Index("idx_stock_prices_code_request_timestamp", "symbol", "request_timestamp"),
        UniqueConstraint("symbol", "request_timestamp", name="uk_stock_code_request_timestamp"),
        {"comment": "股票实时数据表"}
    )
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="主键ID"
    )
    
    code: Mapped[str] = mapped_column("symbol",
        String(20), 
        nullable=False,
        comment="股票代码"
    )
    
    price: Mapped[Decimal] = mapped_column("close_price",
        DECIMAL(10, 3), 
        nullable=False,
        comment="当前价格"
    )
    
    timestamp: Mapped[date] = mapped_column("trade_date",
        Date, 
        nullable=False,
        comment="数据日期"
    )

    open_price: Mapped[Decimal] = mapped_column("open_price",
        DECIMAL(10, 3),
        nullable=True,
        comment="开盘价"
    )

    high_price: Mapped[Decimal] = mapped_column("high_price",
        DECIMAL(10, 3),
        nullable=True,
        comment="最高价"
    )

    low_price: Mapped[Decimal] = mapped_column("low_price",
        DECIMAL(10, 3),
        nullable=True,
        comment="最低价"
    )

    volume: Mapped[int] = mapped_column("volume",
        BigInteger,
        nullable=True,
        comment="成交量"
    )

    amount: Mapped[Decimal] = mapped_column("amount",
        DECIMAL(15, 2),
        nullable=True,
        comment="成交额"
    )

    change_percent: Mapped[Decimal] = mapped_column("change_rate",
        DECIMAL(8, 4),
        nullable=True,
        comment="涨跌幅"
    )
    
    request_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="请求时间"
    )

class StockTdxRisk(BaseModel):
    """通达信股票风险检测数据"""
    
    __tablename__ = "stock_tdx_risk"
    __table_args__ = (
        Index("idx_tdx_risk_code", "stock_code"),
        Index("idx_tdx_risk_date", "date"),
        UniqueConstraint("stock_code", "date", name="uk_tdx_risk_code_date"),
        {"comment": "通达信股票风险检测数据"}
    )
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="主键ID"
    )
    
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
    
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="数据日期"
    )
    
    total_score: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=0,
        comment="总分"
    )
    
    total_items: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="总检查项"
    )
    
    risk_items: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="风险项"
    )
    
    safe_items: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="安全项"
    )
    
    highlight_items: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="亮点项"
    )
    
    raw_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=True,
        comment="原始JSON数据"
    )
    
    change_percent: Mapped[Optional[Decimal]] = mapped_column("change_rate",
        DECIMAL(8, 4), 
        default=0,
        comment="涨跌幅(%)"
    )
    
    volume: Mapped[Optional[int]] = mapped_column(
        BigInteger, 
        default=0,
        comment="成交量"
    )
    
    turnover: Mapped[Optional[Decimal]] = mapped_column("amount",
        DECIMAL(15, 2), 
        default=0,
        comment="成交额"
    )
    
    high: Mapped[Optional[Decimal]] = mapped_column("high_price",
        DECIMAL(10, 3), 
        default=0,
        comment="最高价"
    )
    
    low: Mapped[Optional[Decimal]] = mapped_column("low_price",
        DECIMAL(10, 3), 
        default=0,
        comment="最低价"
    )
    
    open_price: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 3), 
        default=0,
        comment="开盘价"
    )
    
    timestamp: Mapped[datetime] = mapped_column("trade_date",
        Date, 
        nullable=False,
        comment="数据日期"
    )
    
    request_timestamp: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="请求时间戳(来自URL的_参数)"
    )
    
    # 注意：由于不使用物理外键约束，暂时不定义ORM关系映射
    # 可以通过查询来获取相关数据


class MonitorList(BaseModel):
    """监控股票列表表"""
    
    __tablename__ = "monitor_list"
    __table_args__ = (
        UniqueConstraint("code", name="uk_monitor_stock_code"),
        Index("idx_monitor_priority", "priority"),
        Index("idx_monitor_active", "is_active"),
        {"comment": "监控股票列表表"}
    )
    
    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="主键ID"
    )
    
    code: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        comment="股票代码"
    )
    
    priority: Mapped[int] = mapped_column(
        Integer, 
        default=1,
        comment="监控优先级(1-10)"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        comment="是否启用监控"
    )
    
    # 注意：由于不使用物理外键约束，暂时不定义ORM关系映射
    # 可以通过查询来获取相关数据


class DataDedupLog(BaseModelOnlyCreated):
    """数据去重日志表"""
    
    __tablename__ = "data_dedup_log"
    __table_args__ = (
        Index("idx_dedup_table_hash", "table_name", "data_hash"),
        Index("idx_dedup_created_at", "created_at"),
        {"comment": "数据去重日志表"}
    )
    
    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="主键ID"
    )
    
    table_name: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="表名"
    )
    
    data_hash: Mapped[str] = mapped_column(
        String(64), 
        nullable=False,
        comment="数据哈希值(SHA256)"
    )
    
    hash_fields: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="参与哈希计算的字段"
    )
    
    original_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="原始数据(可选)"
    )




class TonghuashunStock(BaseModel):
    __tablename__ = "tonghuashun_stocks"
    __table_args__ = (
        Index("idx_ths_stock_code", "code"),
        Index("idx_ths_record_date", "timestamp"),
        Index("idx_ths_updated_at", "updated_at"),
        {"comment": "同花顺最小字段表", "extend_existing": True}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, comment="股票代码")
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="股票名称")
    current_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10,3), nullable=True, comment="当前价格")
    change_percent: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10,3), nullable=True, comment="涨跌幅")
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="成交量")
    turnover: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20,3), nullable=True, comment="成交额")
    high: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10,3), nullable=True, comment="最高价")
    low: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10,3), nullable=True, comment="最低价")
    open_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10,3), nullable=True, comment="开盘价")
    prev_close: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10,3), nullable=True, comment="昨收价")
    amplitude: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10,3), nullable=True, comment="振幅")
    turnover_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10,3), nullable=True, comment="换手率")
    pe_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10,3), nullable=True, comment="市盈率")
    market_cap: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20,3), nullable=True, comment="总市值")
    timestamp: Mapped[Date] = mapped_column(Date, nullable=False, comment="数据日期")
    request_timestamp: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="请求时间戳")


class TonghuashunRawLog(BaseModel):
    """同花顺原始数据日志表 - 存储实时原始日志，不做去重"""
    __tablename__ = "tonghuashun_raw_logs"
    __table_args__ = (
        Index("idx_ths_raw_logs_source", "source"),
        Index("idx_ths_raw_logs_created_at", "created_at"),
        {"comment": "同花顺原始数据日志表"}
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="主键ID"
    )

    source: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="数据源标识"
    )

    url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="原始请求URL"
    )

    request_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="请求ID/标识"
    )

    request_timestamp: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="请求时间戳"
    )

    payload_type: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="载荷类型(string/json/dict/list)"
    )

    market: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="市场标识，如hs"
    )

    stock_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="包含的股票数量"
    )

    payload: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="原始或解析后的JSON载荷"
    )

    parse_status: Mapped[Optional[str]] = mapped_column(
        String(20),
        default="ok",
        comment="解析状态：ok/failed"
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="解析错误信息"
    )



class SystemConfig(BaseModel):
    """系统配置表"""
    
    __tablename__ = "system_config"
    __table_args__ = (
        Index("idx_system_config_key", "config_key"),
        {"comment": "系统配置表"}
    )
    
    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="主键ID"
    )
    
    config_key: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        nullable=False,
        comment="配置键"
    )
    
    config_value: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="配置值"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="配置描述"
    )




class WencaiStock(BaseModel):
    __tablename__ = "wencai_stocks"
    __table_args__ = (
        Index("idx_wencai_code", "stock_code"),
        Index("idx_wencai_created_at", "created_at"),
        Index("idx_wencai_concept", "concept", mysql_length=100),
        Index("idx_wencai_industry", "industry", mysql_length=100),
        {"comment": "问财股票数据核心字段表"}
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False)
    stock_name: Mapped[str] = mapped_column(String(100), nullable=False)
    current_price: Mapped[Optional[DECIMAL]] = mapped_column(DECIMAL(10, 3), nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    crawl_batch_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否活跃")

    # 新增字段
    concept: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="所属概念")
    industry: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="所属行业")
    raw_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="原始HTML数据")



class WencaiCrawlBatch(BaseModel):
    __tablename__ = "wencai_crawl_batches"
    __table_args__ = (
        Index("idx_wencai_batch_status", "status"),
        Index("idx_wencai_started_at", "started_at"),
        {"comment": "问财抓取批次表"}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_name: Mapped[str] = mapped_column(String(100))
    crawl_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    success_records: Mapped[int] = mapped_column(Integer, default=0)
    failed_records: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # New fields for query and tags
    query_condition: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="原始查询条件")
    # tags字段在数据库中可能不存在，使用BatchTagRelation表进行关联
    # tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="解析出的结构化标签")


class WencaiDataDedup(BaseModel):
    __tablename__ = "wencai_data_dedup"
    __table_args__ = (
        Index("idx_wencai_dedup_hash", "data_hash"),
        Index("idx_wencai_dedup_code", "stock_code"),
        {"comment": "问财数据去重表"}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(20))
    data_hash: Mapped[str] = mapped_column(String(64))
    crawl_batch_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class StockConcept(BaseModel):
    __tablename__ = "stock_concepts"
    __table_args__ = (
        Index("idx_concept_name", "concept_name"),
        Index("idx_concept_stock_code", "stock_code"),
        Index("idx_concept_batch_id", "crawl_batch_id"),
        {"comment": "股票概念关联表"}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False)
    concept_name: Mapped[str] = mapped_column(String(100), nullable=False)
    crawl_batch_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class HiddenConcept(BaseModel):
    """隐藏的概念列表"""
    __tablename__ = "hidden_concepts"
    __table_args__ = (
        Index("idx_hidden_concept_name", "concept_name"),
        {"comment": "隐藏的概念列表"}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    concept_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
