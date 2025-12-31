#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础仓库类
提供通用的CRUD操作和查询方法
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from loguru import logger

from ..models.base import Base

# 泛型类型变量
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(Generic[ModelType], ABC):
    """基础仓库类，提供通用的数据访问方法"""
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def create(self, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> ModelType:
        """创建新记录"""
        try:
            if isinstance(obj_in, dict):
                db_obj = self.model(**obj_in)
            else:
                obj_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in.__dict__
                db_obj = self.model(**obj_data)
            
            self.session.add(db_obj)
            await self.session.flush()
            await self.session.refresh(db_obj)
            
            logger.debug(f"创建{self.model.__name__}记录: {db_obj.id}")
            return db_obj
            
        except Exception as e:
            logger.error(f"创建{self.model.__name__}记录失败: {e}")
            raise
    
    async def get(self, id: Any) -> Optional[ModelType]:
        """根据ID获取记录"""
        try:
            result = await self.session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取{self.model.__name__}记录失败 (ID: {id}): {e}")
            raise
    
    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """获取多条记录"""
        try:
            query = select(self.model)
            
            # 应用过滤条件
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        if isinstance(value, list):
                            query = query.where(getattr(self.model, key).in_(value))
                        else:
                            query = query.where(getattr(self.model, key) == value)
            
            # 应用排序
            if order_by and hasattr(self.model, order_by):
                query = query.order_by(getattr(self.model, order_by))
            
            # 应用分页
            query = query.offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"获取{self.model.__name__}记录列表失败: {e}")
            raise
    
    async def update(
        self, 
        id: Any, 
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> Optional[ModelType]:
        """更新记录"""
        try:
            # 获取现有记录
            db_obj = await self.get(id)
            if not db_obj:
                return None
            
            # 准备更新数据
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in.__dict__
            
            # 更新字段
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            await self.session.flush()
            await self.session.refresh(db_obj)
            
            logger.debug(f"更新{self.model.__name__}记录: {id}")
            return db_obj
            
        except Exception as e:
            logger.error(f"更新{self.model.__name__}记录失败 (ID: {id}): {e}")
            raise
    
    async def delete(self, id: Any) -> bool:
        """删除记录"""
        try:
            result = await self.session.execute(
                delete(self.model).where(self.model.id == id)
            )
            
            deleted = result.rowcount > 0
            if deleted:
                logger.debug(f"删除{self.model.__name__}记录: {id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"删除{self.model.__name__}记录失败 (ID: {id}): {e}")
            raise
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """统计记录数量"""
        try:
            query = select(func.count(self.model.id))
            
            # 应用过滤条件
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        if isinstance(value, list):
                            query = query.where(getattr(self.model, key).in_(value))
                        else:
                            query = query.where(getattr(self.model, key) == value)
            
            result = await self.session.execute(query)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"统计{self.model.__name__}记录数量失败: {e}")
            raise
    
    async def exists(self, id: Any) -> bool:
        """检查记录是否存在"""
        try:
            result = await self.session.execute(
                select(func.count(self.model.id)).where(self.model.id == id)
            )
            return result.scalar() > 0
        except Exception as e:
            logger.error(f"检查{self.model.__name__}记录存在性失败 (ID: {id}): {e}")
            raise
    
    async def bulk_create(self, objs_in: List[Union[CreateSchemaType, Dict[str, Any]]]) -> List[ModelType]:
        """批量创建记录"""
        try:
            db_objs = []
            for obj_in in objs_in:
                if isinstance(obj_in, dict):
                    db_obj = self.model(**obj_in)
                else:
                    obj_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in.__dict__
                    db_obj = self.model(**obj_data)
                db_objs.append(db_obj)
            
            self.session.add_all(db_objs)
            await self.session.flush()
            
            logger.debug(f"批量创建{self.model.__name__}记录: {len(db_objs)}条")
            return db_objs
            
        except Exception as e:
            logger.error(f"批量创建{self.model.__name__}记录失败: {e}")
            raise
    
    async def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """批量更新记录"""
        try:
            if not updates:
                return 0
            
            result = await self.session.execute(
                update(self.model),
                updates
            )
            
            updated_count = result.rowcount
            logger.debug(f"批量更新{self.model.__name__}记录: {updated_count}条")
            return updated_count
            
        except Exception as e:
            logger.error(f"批量更新{self.model.__name__}记录失败: {e}")
            raise
    
    async def find_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """根据字段查找单条记录"""
        try:
            if not hasattr(self.model, field):
                raise ValueError(f"模型{self.model.__name__}没有字段{field}")
            
            result = await self.session.execute(
                select(self.model).where(getattr(self.model, field) == value)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"根据字段查找{self.model.__name__}记录失败 ({field}={value}): {e}")
            raise
    
    async def find_all_by_field(self, field: str, value: Any) -> List[ModelType]:
        """根据字段查找多条记录"""
        try:
            if not hasattr(self.model, field):
                raise ValueError(f"模型{self.model.__name__}没有字段{field}")
            
            result = await self.session.execute(
                select(self.model).where(getattr(self.model, field) == value)
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"根据字段查找{self.model.__name__}记录列表失败 ({field}={value}): {e}")
            raise
    
    async def delete_all(self) -> int:
        """删除所有记录"""
        try:
            result = await self.session.execute(
                delete(self.model)
            )
            
            deleted_count = result.rowcount
            logger.debug(f"删除所有{self.model.__name__}记录: {deleted_count}条")
            return deleted_count
            
        except Exception as e:
            logger.error(f"删除所有{self.model.__name__}记录失败: {e}")
            raise
