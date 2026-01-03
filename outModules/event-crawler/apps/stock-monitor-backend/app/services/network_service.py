#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络数据服务层
处理网络数据的业务逻辑
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from loguru import logger

from ..models.network import NetworkData


class NetworkService:
    """网络数据服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_network_data(self, data: Dict[str, Any]) -> NetworkData:
        """创建网络数据记录"""
        try:
            # 处理headers字段，确保它是JSON字符串
            headers = data.get('headers', {})
            if isinstance(headers, dict):
                headers_json = json.dumps(headers, ensure_ascii=False)
            else:
                headers_json = str(headers)
            
            network_data = NetworkData(
                url=data.get('url', ''),
                method=data.get('method', 'GET'),
                response_data=data.get('response_data', {}),
                data_size=data.get('data_size', 0),
                source=data.get('source', 'chrome_extension'),
                request_id=data.get('request_id', ''),
                user_agent=data.get('user_agent', ''),
                headers=headers_json
            )
            
            self.session.add(network_data)
            await self.session.commit()
            await self.session.refresh(network_data)
            
            logger.info(f"创建网络数据记录成功: {network_data.id}")
            return network_data
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"创建网络数据记录失败: {e}")
            raise
    
    async def get_network_data_list(
        self,
        url_pattern: Optional[str] = None,
        source: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[NetworkData]:
        """获取网络数据列表"""
        try:
            query = select(NetworkData)
            
            # 构建过滤条件
            conditions = []
            
            if url_pattern:
                conditions.append(NetworkData.url.like(f'%{url_pattern}%'))
            
            if source:
                conditions.append(NetworkData.source == source)
            
            if start_time:
                conditions.append(NetworkData.created_at >= start_time)
            
            if end_time:
                conditions.append(NetworkData.created_at <= end_time)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # 排序和分页
            query = query.order_by(desc(NetworkData.created_at))
            query = query.offset(offset).limit(limit)
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"获取网络数据列表失败: {e}")
            raise
    
    async def get_network_data_count(
        self,
        url_pattern: Optional[str] = None,
        source: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """获取网络数据总数"""
        try:
            query = select(func.count(NetworkData.id))
            
            # 构建过滤条件
            conditions = []
            
            if url_pattern:
                conditions.append(NetworkData.url.like(f'%{url_pattern}%'))
            
            if source:
                conditions.append(NetworkData.source == source)
            
            if start_time:
                conditions.append(NetworkData.created_at >= start_time)
            
            if end_time:
                conditions.append(NetworkData.created_at <= end_time)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            result = await self.session.execute(query)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"获取网络数据总数失败: {e}")
            raise
    
    async def get_network_data_stats(self) -> Dict[str, Any]:
        """获取网络数据统计信息"""
        try:
            # 总记录数
            total_count_query = select(func.count(NetworkData.id))
            total_result = await self.session.execute(total_count_query)
            total_count = total_result.scalar() or 0
            
            # 今日记录数
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_count_query = select(func.count(NetworkData.id)).where(
                NetworkData.created_at >= today
            )
            today_result = await self.session.execute(today_count_query)
            today_count = today_result.scalar() or 0
            
            # 总数据大小
            total_size_query = select(func.sum(NetworkData.data_size))
            size_result = await self.session.execute(total_size_query)
            total_size = size_result.scalar() or 0
            
            # 按来源统计
            source_stats_query = select(
                NetworkData.source,
                func.count(NetworkData.id).label('count')
            ).group_by(NetworkData.source)
            source_result = await self.session.execute(source_stats_query)
            source_stats = {row.source: row.count for row in source_result}
            
            # 最新记录时间
            latest_query = select(func.max(NetworkData.created_at))
            latest_result = await self.session.execute(latest_query)
            latest_time = latest_result.scalar()
            
            return {
                'total_count': total_count,
                'today_count': today_count,
                'total_size': total_size,
                'source_stats': source_stats,
                'latest_time': latest_time.isoformat() if latest_time else None
            }
            
        except Exception as e:
            logger.error(f"获取网络数据统计失败: {e}")
            raise
    
    async def delete_network_data(self, data_id: int) -> bool:
        """删除网络数据记录"""
        try:
            query = select(NetworkData).where(NetworkData.id == data_id)
            result = await self.session.execute(query)
            network_data = result.scalar_one_or_none()
            
            if not network_data:
                return False
            
            await self.session.delete(network_data)
            await self.session.commit()
            
            logger.info(f"删除网络数据记录成功: {data_id}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"删除网络数据记录失败: {e}")
            raise
    
    async def clear_network_data(
        self,
        before_date: Optional[datetime] = None,
        source: Optional[str] = None
    ) -> int:
        """清理网络数据"""
        try:
            conditions = []
            
            if before_date:
                conditions.append(NetworkData.created_at < before_date)
            
            if source:
                conditions.append(NetworkData.source == source)
            
            if not conditions:
                # 如果没有条件，默认清理7天前的数据
                week_ago = datetime.now() - timedelta(days=7)
                conditions.append(NetworkData.created_at < week_ago)
            
            # 先查询要删除的记录数
            count_query = select(func.count(NetworkData.id)).where(and_(*conditions))
            count_result = await self.session.execute(count_query)
            delete_count = count_result.scalar() or 0
            
            if delete_count > 0:
                # 删除记录
                delete_query = select(NetworkData).where(and_(*conditions))
                result = await self.session.execute(delete_query)
                records_to_delete = result.scalars().all()
                
                for record in records_to_delete:
                    await self.session.delete(record)
                
                await self.session.commit()
                logger.info(f"清理网络数据记录成功: {delete_count} 条")
            
            return delete_count
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"清理网络数据失败: {e}")
            raise