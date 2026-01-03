#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础模型类
定义所有模型的基础类和通用字段
"""

from datetime import datetime
from typing import Any, Dict
from sqlalchemy import DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy基础模型类"""
    
    # 类型注解映射
    type_annotation_map = {
        datetime: DateTime(timezone=True),
    }


class CreatedMixin:
    """仅包含创建时间的混入类"""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="创建时间"
    )


class TimestampMixin(CreatedMixin):
    """时间戳混入类，提供创建时间和更新时间字段"""
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )


class ModelHelperMixin:
    """模型辅助方法混入类"""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """从字典更新模型属性"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        """字符串表示"""
        class_name = self.__class__.__name__
        attrs = []
        
        # 获取主键字段
        for column in self.__table__.primary_key.columns:
            value = getattr(self, column.name, None)
            attrs.append(f"{column.name}={value}")
        
        return f"<{class_name}({', '.join(attrs)})>"


class BaseModel(Base, TimestampMixin, ModelHelperMixin):
    """基础模型类，包含通用字段和方法"""
    
    __abstract__ = True


class BaseModelOnlyCreated(Base, CreatedMixin, ModelHelperMixin):
    """仅包含创建时间的基础模型类"""
    
    __abstract__ = True
