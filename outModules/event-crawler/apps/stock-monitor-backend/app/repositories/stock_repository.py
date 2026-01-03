#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据仓库
提供股票相关的数据访问方法
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, desc, asc, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from .base import BaseRepository
from ..models.stock import StockInfo, StockData, DataDedupLog, TonghuashunRawLog


class StockRepository(BaseRepository[StockInfo]):
    """股票信息仓库"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(StockInfo, session)
    
    async def find_by_code(self, code: str) -> Optional[StockInfo]:
        """根据股票代码查找股票信息"""
        try:
            result = await self.session.execute(
                select(StockInfo).where(StockInfo.code == code)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"根据代码查找股票信息失败 (code: {code}): {e}")
            raise
    
    async def find_by_codes(self, codes: List[str]) -> List[StockInfo]:
        """根据股票代码列表查找股票信息"""
        try:
            result = await self.session.execute(
                select(StockInfo).where(StockInfo.code.in_(codes))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"根据代码列表查找股票信息失败 (codes: {codes}): {e}")
            raise
    
    async def find_active_stocks(self) -> List[StockInfo]:
        """查找所有活跃股票"""
        try:
            result = await self.session.execute(
                select(StockInfo).where(StockInfo.is_active == True)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"查找活跃股票失败: {e}")
            raise
    
    async def find_by_market(self, market: str) -> List[StockInfo]:
        """根据市场类型查找股票"""
        try:
            result = await self.session.execute(
                select(StockInfo).where(StockInfo.market == market)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"根据市场查找股票失败 (market: {market}): {e}")
            raise

    async def get_all_codes(self) -> List[str]:
        """获取所有股票代码"""
        try:
            result = await self.session.execute(select(StockInfo.code).distinct())
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取所有股票代码失败: {e}")
            raise
    
    async def search_stocks(
        self, 
        keyword: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[StockInfo]:
        """搜索股票（支持股票代码和名称模糊匹配）"""
        try:
            # 构建搜索条件：股票代码或股票名称包含关键词
            search_condition = (
                (StockInfo.code.ilike(f"%{keyword}%")) |
                (StockInfo.name.ilike(f"%{keyword}%"))
            )
            
            result = await self.session.execute(
                select(StockInfo)
                .where(search_condition)
                .order_by(asc(StockInfo.code))
                .offset(offset)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"搜索股票失败 (keyword: {keyword}): {e}")
            raise
    
    async def get_stocks_with_pagination(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[StockInfo]:
        """分页获取股票列表"""
        try:
            result = await self.session.execute(
                select(StockInfo)
                .order_by(asc(StockInfo.code))
                .offset(offset)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"分页获取股票列表失败: {e}")
            raise

    async def get_wencai_stock_codes(self) -> List[str]:
        """获取问财股票池中的所有不重复股票代码"""
        from ..models.stock import WencaiStock
        try:
            result = await self.session.execute(
                select(WencaiStock.stock_code).distinct()
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"获取问财股票代码失败: {e}")
            raise

    async def get_sync_stock_list(
        self,
        keyword: Optional[str] = None,
        date_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取同步任务股票列表（支持搜索和分页）"""
        try:
            from ..models.stock_daily import StockDaily
            
            # Subquery to get latest sync date for each stock
            latest_dates = select(
                StockDaily.code, 
                func.max(StockDaily.trade_date).label('last_date')
            ).group_by(StockDaily.code).subquery()

            # Base query: Join StockInfo with latest_dates
            # We select StockInfo and the last_date
            query = select(StockInfo, latest_dates.c.last_date).outerjoin(
                latest_dates, StockInfo.code == latest_dates.c.code
            )

            # Apply filters
            if keyword:
                query = query.where(
                    (StockInfo.code.ilike(f"%{keyword}%")) |
                    (StockInfo.name.ilike(f"%{keyword}%"))
                )
            
            if date_filter:
                try:
                    # Parse date string to date object if necessary, or rely on string comparison if DB supports it
                    # Usually passed as 'YYYY-MM-DD'
                    filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
                    query = query.where(latest_dates.c.last_date == filter_date)
                except ValueError:
                    logger.warning(f"Invalid date format for filter: {date_filter}")
            
            # Calculate total count (using a subquery wrapper to count rows correctly after join/filter)
            # Efficient way: count the matching rows
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.session.execute(count_query)
            total = total_result.scalar() or 0
            
            # Apply sorting and pagination
            # Sort by last_date desc, then code asc
            query = query.order_by(desc(latest_dates.c.last_date), asc(StockInfo.code))
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            result = await self.session.execute(query)
            rows = result.all()
            
            stock_list = []
            for row in rows:
                stock = row[0]
                last_date = row[1]
                
                stock_list.append({
                    "code": stock.code,
                    "name": stock.name,
                    "market": stock.market,
                    "last_sync_date": last_date.strftime("%Y-%m-%d") if last_date else None,
                    "is_active": stock.is_active
                })
                
            return stock_list, total
            
        except Exception as e:
            logger.error(f"获取同步股票列表失败: {e}")
            raise


class StockDataRepository(BaseRepository[StockData]):
    """股票数据仓库"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(StockData, session)
    
    async def find_by_code(
        self, 
        code: str, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[StockData]:
        """根据股票代码查找股票数据"""
        try:
            query = select(StockData).where(StockData.code == code)
            
            if start_time:
                query = query.where(StockData.timestamp >= start_time)
            if end_time:
                query = query.where(StockData.timestamp <= end_time)
            
            query = query.order_by(desc(StockData.timestamp)).limit(limit)
            
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"根据代码查找股票数据失败 (code: {code}): {e}")
            raise

    async def find_latest_by_code(self, code: str) -> Optional[StockData]:
        """查找指定股票的最新数据"""
        try:
            result = await self.session.execute(
                select(StockData)
                .where(StockData.code == code)
                .order_by(desc(StockData.timestamp))
                .limit(1)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"查找最新股票数据失败 (code: {code}): {e}")
            raise
            
    async def find_latest_by_codes(self, codes: List[str]) -> List[StockData]:
        """查找多只股票的最新数据"""
        try:
            # 使用窗口函数获取每只股票的最新数据
            subquery = select(
                StockData,
                func.row_number().over(
                    partition_by=StockData.code,
                    order_by=desc(StockData.timestamp)
                ).label('rn')
            ).where(StockData.code.in_(codes)).subquery()
            
            result = await self.session.execute(
                select(subquery).where(subquery.c.rn == 1)
            )
            
            # 转换结果为StockData对象
            stock_data_list = []
            for row in result:
                stock_data = StockData()
                for column in StockData.__table__.columns:
                    if hasattr(row, column.name):
                        setattr(stock_data, column.name, getattr(row, column.name))
                stock_data_list.append(stock_data)
            
            return stock_data_list
        except Exception as e:
            logger.error(f"查找多只股票最新数据失败 (codes: {codes}): {e}")
            raise
    
    async def find_recent_data(
        self, 
        code: str, 
        hours: int = 24
    ) -> List[StockData]:
        """查找指定股票最近几小时的数据"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            result = await self.session.execute(
                select(StockData)
                .where(
                    and_(
                        StockData.code == code,
                        StockData.timestamp >= cutoff_time
                    )
                )
                .order_by(desc(StockData.timestamp))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"查找最近股票数据失败 (code: {code}, hours: {hours}): {e}")
            raise

    async def find_all_stock_data_with_names(
        self,
        limit: int = 1000,
        offset: int = 0,
        order_by_timestamp: bool = True,
        request_timestamp: Optional[str] = None,
        start_timestamp: Optional[str] = None,
        end_timestamp: Optional[str] = None,
        stock_code: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取所有股票数据，包含股票名称，返回(数据列表, 总数)"""
        try:
            # Base query: Join StockData and StockInfo
            base_query = select(StockData, StockInfo.name.label('stock_name')).outerjoin(
                StockInfo, StockData.code == StockInfo.code
            )
            
            # Apply filters to base query
            if stock_code:
                base_query = base_query.where(
                    (StockData.code.ilike(f"%{stock_code}%")) |
                    (StockInfo.name.ilike(f"%{stock_code}%"))
                )

            if request_timestamp:
                base_query = base_query.where(StockData.request_timestamp == request_timestamp)
                
            if start_timestamp:
                base_query = base_query.where(StockData.created_at >= datetime.fromisoformat(start_timestamp))
                
            if end_timestamp:
                base_query = base_query.where(StockData.created_at <= datetime.fromisoformat(end_timestamp))
            
            # Calculate total count
            # We use select_from(base_query.subquery()) to handle joins and filters correctly
            # Note: For simple queries, count(StockData.id) might be faster, but subquery is safer for complex joins
            count_query = select(func.count()).select_from(base_query.subquery())
            total_result = await self.session.execute(count_query)
            total_count = total_result.scalar() or 0
            
            # Apply ordering
            query = base_query
            if order_by_timestamp:
                query = query.order_by(desc(StockData.timestamp), desc(StockData.created_at), desc(StockData.id))
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            result = await self.session.execute(query)
            
            # Convert to list of dicts
            data_list = []
            for row in result:
                stock_data = row[0]
                stock_name = row[1]
                
                # Convert StockData to dict safely (handling mapped_column with different names)
                try:
                    inst = inspect(stock_data)
                    data_dict = {c.key: getattr(stock_data, c.key) for c in inst.mapper.column_attrs}
                except Exception as conversion_error:
                    # Fallback to to_dict or manual
                    logger.warning(f"Failed to inspect stock_data: {conversion_error}")
                    data_dict = stock_data.to_dict() if hasattr(stock_data, 'to_dict') else {
                        c.name: getattr(stock_data, c.name, None) for c in stock_data.__table__.columns
                    }
                
                # Add stock name
                data_dict['stock_name'] = stock_name
                
                # Add symbol key for backward compatibility or controller expectation
                if 'code' in data_dict and 'symbol' not in data_dict:
                    data_dict['symbol'] = data_dict['code']
                    
                data_list.append(data_dict)
                
            return data_list, total_count
            
        except Exception as e:
            logger.error(f"获取所有股票数据(含名称)失败: {e}")
            raise


class DataDedupRepository(BaseRepository[DataDedupLog]):
    """数据去重日志仓库"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(DataDedupLog, session)
        
    async def check_hash_exists(self, table_name: str, data_hash: str) -> bool:
        """检查哈希值是否存在"""
        try:
            result = await self.session.execute(
                select(DataDedupLog).where(
                    and_(
                        DataDedupLog.table_name == table_name,
                        DataDedupLog.data_hash == data_hash
                    )
                )
            )
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"检查哈希值失败 (table: {table_name}, hash: {data_hash}): {e}")
            raise

class TonghuashunRawLogRepository(BaseRepository[TonghuashunRawLog]):
    """同花顺原始日志仓库"""

    def __init__(self, session: AsyncSession):
        super().__init__(TonghuashunRawLog, session)

    async def create_log(self, data: Dict[str, Any]) -> TonghuashunRawLog:
        """创建原始日志记录"""
        try:
            return await self.create(data)
        except Exception as e:
            logger.error(f"创建同花顺原始日志失败: {e}")
            raise

    async def count_logs(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> int:
        """统计时间范围内的日志数量"""
        try:
            from sqlalchemy import select, and_

            query = select(func.count(TonghuashunRawLog.id))
            if start_time and end_time:
                query = query.where(and_(TonghuashunRawLog.created_at >= start_time, TonghuashunRawLog.created_at <= end_time))
            result = await self.session.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"统计同花顺原始日志数量失败: {e}")
            return 0
