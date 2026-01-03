#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控服务
处理股票监控相关的业务逻辑
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..repositories.monitor_repository import MonitorRepository
from ..repositories.stock_repository import StockRepository, StockDataRepository
from ..models.stock import MonitorList, StockInfo, StockData


class MonitorService:
    """监控服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.monitor_repo = MonitorRepository(session)
        self.stock_repo = StockRepository(session)
        self.stock_data_repo = StockDataRepository(session)
    
    async def add_monitor(
        self, 
        stock_code: str, 
        priority: int = 1,
        auto_create_stock: bool = True,
        stock_name: str = None
    ) -> MonitorList:
        """添加监控股票"""
        try:
            # 移除可能的后缀 (e.g. 000001.SZ -> 000001)
            if '.' in stock_code:
                stock_code = stock_code.split('.')[0]
                
            # 验证股票代码格式
            if not self._validate_stock_code(stock_code):
                raise ValueError(f"无效的股票代码: {stock_code}")
            
            # 验证优先级
            if not (1 <= priority <= 10):
                raise ValueError(f"优先级必须在1-10之间: {priority}")
            
            # 检查股票是否存在
            stock_info = await self.stock_repo.find_by_code(stock_code)
            if not stock_info and auto_create_stock:
                # 自动创建股票基本信息（对齐StockInfo字段）
                stock_data = {
                    'code': stock_code,
                    'name': stock_name if stock_name else f'股票{stock_code}',
                    'market': 'SZ' if stock_code.startswith(('0','3')) else 'SH',
                    'is_active': True
                }
                await self.stock_repo.create(stock_data)
                logger.info(f"自动创建股票信息: {stock_code}")
            elif not stock_info:
                raise ValueError(f"股票不存在且未启用自动创建: {stock_code}")
            
            # 添加监控
            monitor = await self.monitor_repo.add_monitor(
                stock_code=stock_code,
                priority=priority,
                is_active=True
            )
            
            logger.info(f"添加监控股票: {stock_code}, 优先级: {priority}")
            return monitor
            
        except Exception as e:
            logger.error(f"添加监控股票失败 (code: {stock_code}): {e}")
            raise
    
    async def remove_monitor(self, stock_code: str) -> bool:
        """移除监控股票"""
        try:
            result = await self.monitor_repo.remove_monitor(stock_code)
            if result:
                logger.info(f"移除监控股票: {stock_code}")
            else:
                logger.warning(f"监控股票不存在: {stock_code}")
            return result
        except Exception as e:
            logger.error(f"移除监控股票失败 (code: {stock_code}): {e}")
            raise
    
    async def update_monitor_priority(self, stock_code: str, priority: int) -> Optional[MonitorList]:
        """更新监控优先级"""
        try:
            if not (1 <= priority <= 10):
                raise ValueError(f"优先级必须在1-10之间: {priority}")
            
            monitor = await self.monitor_repo.update_priority(stock_code, priority)
            if monitor:
                logger.info(f"更新监控优先级: {stock_code} -> {priority}")
            else:
                logger.warning(f"监控股票不存在: {stock_code}")
            return monitor
        except Exception as e:
            logger.error(f"更新监控优先级失败 (code: {stock_code}): {e}")
            raise
    
    async def activate_monitor(self, stock_code: str) -> Optional[MonitorList]:
        """激活监控"""
        try:
            monitor = await self.monitor_repo.activate_monitor(stock_code)
            if monitor:
                logger.info(f"激活监控: {stock_code}")
            else:
                logger.warning(f"监控股票不存在: {stock_code}")
            return monitor
        except Exception as e:
            logger.error(f"激活监控失败 (code: {stock_code}): {e}")
            raise
    
    async def deactivate_monitor(self, stock_code: str) -> Optional[MonitorList]:
        """停用监控"""
        try:
            monitor = await self.monitor_repo.deactivate_monitor(stock_code)
            if monitor:
                logger.info(f"停用监控: {stock_code}")
            else:
                logger.warning(f"监控股票不存在: {stock_code}")
            return monitor
        except Exception as e:
            logger.error(f"停用监控失败 (code: {stock_code}): {e}")
            raise
    
    async def get_monitor_list(
        self, 
        active_only: bool = True,
        priority_filter: Optional[int] = None
    ) -> List[MonitorList]:
        """获取监控列表"""
        try:
            if priority_filter is not None:
                return await self.monitor_repo.find_by_priority(priority_filter)
            elif active_only:
                return await self.monitor_repo.find_active_monitors()
            else:
                return await self.monitor_repo.get_multi()
        except Exception as e:
            logger.error(f"获取监控列表失败: {e}")
            raise
    
    async def get_high_priority_monitors(self, min_priority: int = 5) -> List[MonitorList]:
        """获取高优先级监控列表"""
        try:
            return await self.monitor_repo.find_high_priority_monitors(min_priority)
        except Exception as e:
            logger.error(f"获取高优先级监控列表失败: {e}")
            raise
    
    async def get_monitor_codes(self, active_only: bool = True) -> List[str]:
        """获取监控股票代码列表"""
        try:
            return await self.monitor_repo.get_monitor_codes(active_only)
        except Exception as e:
            logger.error(f"获取监控股票代码列表失败: {e}")
            raise
    
    async def get_monitor_with_stock_info(
        self, 
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """获取监控列表及股票信息"""
        try:
            monitors = await self.get_monitor_list(active_only)
            result = []
            
            for monitor in monitors:
                stock_info = await self.stock_repo.find_by_code(monitor.stock_code)
                monitor_data = {
                    'monitor_id': monitor.id,
                    'stock_code': monitor.stock_code,
                    'priority': monitor.priority,
                    'is_active': monitor.is_active,
                    'created_at': monitor.created_at,
                    'updated_at': monitor.updated_at,
                    'stock_info': {
                        'stock_name': stock_info.stock_name if stock_info else '',
                        'market': stock_info.market if stock_info else '',
                        'industry': stock_info.industry if stock_info else '',
                        'is_stock_active': stock_info.is_active if stock_info else False
                    } if stock_info else None
                }
                result.append(monitor_data)
            
            return result
        except Exception as e:
            logger.error(f"获取监控列表及股票信息失败: {e}")
            raise
    
    async def get_monitor_with_latest_data(
        self, 
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """获取监控列表及最新股票数据"""
        try:
            monitors = await self.get_monitor_list(active_only)
            result = []
            
            for monitor in monitors:
                # 获取股票信息
                stock_info = await self.stock_repo.find_by_code(monitor.stock_code)
                
                # 获取最新股票数据
                latest_data = await self.stock_data_repo.find_latest_data(monitor.stock_code)
                
                monitor_data = {
                    'monitor_id': monitor.id,
                    'stock_code': monitor.stock_code,
                    'priority': monitor.priority,
                    'is_active': monitor.is_active,
                    'created_at': monitor.created_at,
                    'updated_at': monitor.updated_at,
                    'stock_info': {
                        'stock_name': stock_info.stock_name if stock_info else '',
                        'market': stock_info.market if stock_info else '',
                        'industry': stock_info.industry if stock_info else ''
                    } if stock_info else None,
                    'latest_data': {
                        'price': float(latest_data.price) if latest_data else None,
                        'volume': latest_data.volume if latest_data else None,
                        'change_amount': float(latest_data.change_amount) if latest_data else None,
                        'change_percent': float(latest_data.change_percent) if latest_data else None,
                        'data_time': latest_data.data_time.isoformat() if latest_data else None
                    } if latest_data else None
                }
                result.append(monitor_data)
            
            return result
        except Exception as e:
            logger.error(f"获取监控列表及最新股票数据失败: {e}")
            raise
    
    async def get_monitor_statistics(self) -> Dict[str, Any]:
        """获取监控统计信息"""
        try:
            stats = await self.monitor_repo.get_monitor_stats()
            
            # 添加额外统计信息
            active_codes = await self.get_monitor_codes(active_only=True)
            
            # 统计有数据的监控股票数量
            stocks_with_data = 0
            for code in active_codes:
                latest_data = await self.stock_data_repo.find_latest_data(code)
                if latest_data:
                    stocks_with_data += 1
            
            stats['stocks_with_data'] = stocks_with_data
            stats['stocks_without_data'] = len(active_codes) - stocks_with_data
            
            return stats
        except Exception as e:
            logger.error(f"获取监控统计信息失败: {e}")
            raise
    
    async def batch_add_monitors(
        self, 
        stock_codes: List[str], 
        default_priority: int = 1
    ) -> Dict[str, Any]:
        """批量添加监控"""
        try:
            success_count = 0
            failed_count = 0
            errors = []
            
            for stock_code in stock_codes:
                try:
                    await self.add_monitor(stock_code, default_priority)
                    success_count += 1
                except Exception as e:
                    failed_count += 1
                    errors.append(f"{stock_code}: {str(e)}")
            
            result = {
                'success': success_count,
                'failed': failed_count,
                'total': len(stock_codes),
                'errors': errors
            }
            
            logger.info(f"批量添加监控完成: {result}")
            return result
        except Exception as e:
            logger.error(f"批量添加监控失败: {e}")
            raise
    
    async def batch_update_priority(
        self, 
        updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """批量更新优先级"""
        try:
            success_count = 0
            failed_count = 0
            errors = []
            
            for update in updates:
                try:
                    stock_code = update.get('stock_code')
                    priority = update.get('priority')
                    
                    if not stock_code or priority is None:
                        failed_count += 1
                        errors.append(f"缺少必要参数: {update}")
                        continue
                    
                    result = await self.update_monitor_priority(stock_code, priority)
                    if result:
                        success_count += 1
                    else:
                        failed_count += 1
                        errors.append(f"监控不存在: {stock_code}")
                        
                except Exception as e:
                    failed_count += 1
                    errors.append(f"{update.get('stock_code', 'unknown')}: {str(e)}")
            
            result = {
                'success': success_count,
                'failed': failed_count,
                'total': len(updates),
                'errors': errors
            }
            
            logger.info(f"批量更新优先级完成: {result}")
            return result
        except Exception as e:
            logger.error(f"批量更新优先级失败: {e}")
            raise
    
    async def batch_activate(self, stock_codes: List[str]) -> int:
        """批量激活监控"""
        try:
            return await self.monitor_repo.batch_activate(stock_codes)
        except Exception as e:
            logger.error(f"批量激活监控失败: {e}")
            raise
    
    async def batch_deactivate(self, stock_codes: List[str]) -> int:
        """批量停用监控"""
        try:
            return await self.monitor_repo.batch_deactivate(stock_codes)
        except Exception as e:
            logger.error(f"批量停用监控失败: {e}")
            raise
    
    def _validate_stock_code(self, stock_code: str) -> bool:
        """验证股票代码格式"""
        try:
            if not isinstance(stock_code, str):
                return False
            
            # 检查长度
            if len(stock_code) != 6:
                return False
            
            # 检查是否全为数字
            if not stock_code.isdigit():
                return False
            
            return True
        except Exception:
            return False
    
    async def get_monitor_alerts(
        self, 
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """获取监控告警信息（无数据更新的股票）"""
        try:
            active_monitors = await self.get_monitor_list(active_only=True)
            alerts = []
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            for monitor in active_monitors:
                latest_data = await self.stock_data_repo.find_latest_data(monitor.stock_code)
                
                if not latest_data or latest_data.data_time < cutoff_time:
                    stock_info = await self.stock_repo.find_by_code(monitor.stock_code)
                    
                    alert = {
                        'stock_code': monitor.stock_code,
                        'stock_name': stock_info.stock_name if stock_info else '',
                        'priority': monitor.priority,
                        'last_data_time': latest_data.data_time.isoformat() if latest_data else None,
                        'hours_since_update': (
                            (datetime.now() - latest_data.data_time).total_seconds() / 3600
                        ) if latest_data else None,
                        'alert_type': 'no_recent_data'
                    }
                    alerts.append(alert)
            
            # 按优先级和时间排序
            alerts.sort(key=lambda x: (-x['priority'], x['hours_since_update'] or float('inf')))
            
            logger.info(f"发现 {len(alerts)} 个监控告警")
            return alerts
        except Exception as e:
            logger.error(f"获取监控告警失败: {e}")
            raise
