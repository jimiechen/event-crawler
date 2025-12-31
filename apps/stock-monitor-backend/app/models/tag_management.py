#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标签管理系统相关数据模型
"""

from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    BigInteger, Boolean, DateTime, Integer, String, DECIMAL, Index, UniqueConstraint, JSON, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel, BaseModelOnlyCreated

class StockTagInfo(BaseModel):
    """标签信息表"""
    
    __tablename__ = "stock_tags_info"
    __table_args__ = (
        Index("idx_score", "score"),
        Index("idx_is_deleted", "is_deleted"),
        {"comment": "标签信息表"}
    )
    
    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="主键ID"
    )
    
    name: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False,
        comment="标签名称"
    )
    
    score: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 2), 
        default=0.00,
        comment="分值"
    )
    
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        comment="是否软删除"
    )
    
    tag_type: Mapped[str] = mapped_column(
        String(20),
        default="calculation",
        comment="标签类型(date/calculation)"
    )
    
    # 关联关系
    relations: Mapped[List["StockTagRelation"]] = relationship(
        "StockTagRelation", 
        back_populates="tag",
        cascade="all, delete-orphan"
    )


class StockTagRelation(BaseModelOnlyCreated):
    """股票标签关联表"""
    
    __tablename__ = "stock_tag_relations"
    __table_args__ = (
        UniqueConstraint("stock_code", "tag_id", name="uk_stock_tag"),
        Index("idx_stock_code", "stock_code"),
        Index("idx_tag_id", "tag_id"),
        {"comment": "股票标签关联表"}
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
    
    tag_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("stock_tags_info.id", ondelete="CASCADE"),
        nullable=False,
        comment="标签ID"
    )
    
    # 关联关系
    tag: Mapped["StockTagInfo"] = relationship("StockTagInfo", back_populates="relations")


class BatchTagRelation(BaseModelOnlyCreated):
    """批次标签关联表"""
    
    __tablename__ = "batch_tag_relations"
    __table_args__ = (
        UniqueConstraint("batch_id", "tag_id", name="uk_batch_tag"),
        Index("idx_batch_id", "batch_id"),
        Index("idx_tag_id", "tag_id"),
        {"comment": "批次标签关联表"}
    )
    
    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="主键ID"
    )
    
    batch_id: Mapped[int] = mapped_column(
        Integer, 
        nullable=False,
        comment="批次ID"
    )
    
    tag_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("stock_tags_info.id", ondelete="CASCADE"),
        nullable=False,
        comment="标签ID"
    )
    
    # 关联关系
    tag: Mapped["StockTagInfo"] = relationship("StockTagInfo")


class OperationLog(BaseModelOnlyCreated):
    """操作日志表"""
    
    __tablename__ = "operation_logs"
    __table_args__ = (
        Index("idx_action", "action"),
        Index("idx_target_type", "target_type"),
        {"comment": "操作日志表"}
    )
    
    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="主键ID"
    )
    
    operator: Mapped[str] = mapped_column(
        String(50), 
        default="system",
        comment="操作人"
    )
    
    action: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="操作类型"
    )
    
    target_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="目标类型"
    )
    
    target_id: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="目标ID"
    )
    
    details: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="操作详情"
    )
