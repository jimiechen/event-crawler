#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控列表仓库
提供监控股票列表的数据访问方法
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from .base import BaseRepository
from ..models.stock import MonitorList


class MonitorRepository(BaseRepository[MonitorList]):
    """监控列表仓库"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(MonitorList, session)
    
    async def find_by_stock_code(self, stock_code: str) -> Optional[MonitorList]:
        """根据股票代码查找监控记录"""
        try:
            result = await self.session.execute(
                select(MonitorList).where(MonitorList.code == stock_code)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"根据股票代码查找监控记录失败 (code: {stock_code}): {e}")
            raise
    
    async def find_active_monitors(self) -> List[MonitorList]:
        """查找所有活跃的监控记录"""
        try:
            result = await self.session.execute(
                select(MonitorList)
                .where(MonitorList.is_active == True)
                .order_by(desc(MonitorList.priority), asc(MonitorList.code))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"查找活跃监控记录失败: {e}")
            raise
    
    async def find_by_priority(self, priority: int) -> List[MonitorList]:
        """根据优先级查找监控记录"""
        try:
            result = await self.session.execute(
                select(MonitorList)
                .where(
                    and_(
                        MonitorList.priority == priority,
                        MonitorList.is_active == True
                    )
                )
                .order_by(asc(MonitorList.code))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"根据优先级查找监控记录失败 (priority: {priority}): {e}")
            raise
    
    async def find_high_priority_monitors(self, min_priority: int = 5) -> List[MonitorList]:
        """查找高优先级监控记录"""
        try:
            result = await self.session.execute(
                select(MonitorList)
                .where(
                    and_(
                        MonitorList.priority >= min_priority,
                        MonitorList.is_active == True
                    )
                )
                .order_by(desc(MonitorList.priority), asc(MonitorList.code))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"查找高优先级监控记录失败 (min_priority: {min_priority}): {e}")
            raise
    
    async def get_monitor_codes(self, active_only: bool = True) -> List[str]:
        """获取监控股票代码列表"""
        try:
            query = select(MonitorList.code)
            
            if active_only:
                query = query.where(MonitorList.is_active == True)
            
            query = query.order_by(desc(MonitorList.priority), asc(MonitorList.code))
            
            result = await self.session.execute(query)
            return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"获取监控股票代码列表失败: {e}")
            raise
    
    async def add_monitor(
        self, 
        stock_code: str, 
        priority: int = 1, 
        is_active: bool = True
    ) -> MonitorList:
        """添加监控股票"""
        try:
            # 检查是否已存在
            existing = await self.find_by_stock_code(stock_code)
            if existing:
                # 如果已存在，更新优先级和状态
                return await self.update(existing.id, {
                    'priority': priority,
                    'is_active': is_active
                })
            
            # 创建新的监控记录
            monitor_data = {
                'code': stock_code,
                'priority': priority,
                'is_active': is_active
            }
            return await self.create(monitor_data)
        except Exception as e:
            logger.error(f"添加监控股票失败 (code: {stock_code}): {e}")
            raise
    
    async def remove_monitor(self, stock_code: str) -> bool:
        """移除监控股票"""
        try:
            monitor = await self.find_by_stock_code(stock_code)
            if monitor:
                return await self.delete(monitor.id)
            return False
        except Exception as e:
            logger.error(f"移除监控股票失败 (code: {stock_code}): {e}")
            raise
    
    async def activate_monitor(self, stock_code: str) -> Optional[MonitorList]:
        """激活监控股票"""
        try:
            monitor = await self.find_by_stock_code(stock_code)
            if monitor:
                return await self.update(monitor.id, {'is_active': True})
            return None
        except Exception as e:
            logger.error(f"激活监控股票失败 (code: {stock_code}): {e}")
            raise
    
    async def deactivate_monitor(self, stock_code: str) -> Optional[MonitorList]:
        """停用监控股票"""
        try:
            monitor = await self.find_by_stock_code(stock_code)
            if monitor:
                return await self.update(monitor.id, {'is_active': False})
            return None
        except Exception as e:
            logger.error(f"停用监控股票失败 (code: {stock_code}): {e}")
            raise
    
    async def update_priority(self, stock_code: str, priority: int) -> Optional[MonitorList]:
        """更新监控优先级"""
        try:
            monitor = await self.find_by_stock_code(stock_code)
            if monitor:
                return await self.update(monitor.id, {'priority': priority})
            return None
        except Exception as e:
            logger.error(f"更新监控优先级失败 (code: {stock_code}): {e}")
            raise
    
    async def get_monitor_stats(self) -> Dict[str, Any]:
        """获取监控统计信息"""
        try:
            # 总监控数量
            total_result = await self.session.execute(
                select(func.count(MonitorList.id))
            )
            total_count = total_result.scalar() or 0
            
            # 活跃监控数量
            active_result = await self.session.execute(
                select(func.count(MonitorList.id))
                .where(MonitorList.is_active == True)
            )
            active_count = active_result.scalar() or 0
            
            # 按优先级统计
            priority_result = await self.session.execute(
                select(
                    MonitorList.priority,
                    func.count(MonitorList.id).label('count')
                )
                .where(MonitorList.is_active == True)
                .group_by(MonitorList.priority)
                .order_by(desc(MonitorList.priority))
            )
            
            priority_stats = {}
            for row in priority_result:
                priority_stats[f"priority_{row.priority}"] = row.count
            
            return {
                'total_monitors': total_count,
                'active_monitors': active_count,
                'inactive_monitors': total_count - active_count,
                'priority_distribution': priority_stats
            }
        except Exception as e:
            logger.error(f"获取监控统计信息失败: {e}")
            raise
    
    async def batch_update_priority(self, updates: List[Dict[str, Any]]) -> int:
        """批量更新优先级"""
        try:
            updated_count = 0
            for update_data in updates:
                stock_code = update_data.get('stock_code')
                priority = update_data.get('priority')
                
                if stock_code and priority is not None:
                    monitor = await self.find_by_stock_code(stock_code)
                    if monitor:
                        await self.update(monitor.id, {'priority': priority})
                        updated_count += 1
            
            logger.info(f"批量更新监控优先级: {updated_count}条")
            return updated_count
        except Exception as e:
            logger.error(f"批量更新监控优先级失败: {e}")
            raise
    
    async def batch_activate(self, stock_codes: List[str]) -> int:
        """批量激活监控"""
        try:
            updated_count = 0
            for stock_code in stock_codes:
                monitor = await self.find_by_stock_code(stock_code)
                if monitor and not monitor.is_active:
                    await self.update(monitor.id, {'is_active': True})
                    updated_count += 1
            
            logger.info(f"批量激活监控: {updated_count}条")
            return updated_count
        except Exception as e:
            logger.error(f"批量激活监控失败: {e}")
            raise
    
    async def batch_deactivate(self, stock_codes: List[str]) -> int:
        """批量停用监控"""
        try:
            updated_count = 0
            for stock_code in stock_codes:
                monitor = await self.find_by_stock_code(stock_code)
                if monitor and monitor.is_active:
                    await self.update(monitor.id, {'is_active': False})
                    updated_count += 1
            
            logger.info(f"批量停用监控: {updated_count}条")
            return updated_count
        except Exception as e:
            logger.error(f"批量停用监控失败: {e}")
            raise
