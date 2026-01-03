#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据服务
处理股票信息和股票数据的业务逻辑
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, date, time
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from loguru import logger

from ..repositories.stock_repository import (
    StockRepository, 
    StockDataRepository, 
    DataDedupRepository
)
from ..repositories.stock_daily_repository import StockDailyRepository
from ..models.stock import StockInfo, StockData, TonghuashunStock, WencaiStock
from ..models.stock_daily import StockDaily
from .data_dedup_service import DataDedupService
from .tonghuashun_data_decoder import tonghuashun_decoder
from .tushare_service import TushareService
from .baostock_service import BaostockService
from .akshare_service import AkshareService
from app.database import db_manager

class StockService:
    """股票数据服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.stock_repo = StockRepository(session)
        self.stock_data_repo = StockDataRepository(session)
        self.stock_daily_repo = StockDailyRepository(db_manager) # Initialize with db_manager
        self.dedup_repo = DataDedupRepository(session)
        self.dedup_service = DataDedupService(session)
    
    async def get_stock_info(self, stock_code: str) -> Optional[StockInfo]:
        """获取股票基本信息"""
        try:
            info = await self.stock_repo.find_by_code(stock_code)
            
            if not info:
                # 尝试其他代码格式
                alt_code = None
                if '.' in stock_code:
                    alt_code = stock_code.split('.')[0]
                else:
                    if stock_code.startswith('6'): alt_code = f"{stock_code}.SH"
                    elif stock_code.startswith('0') or stock_code.startswith('3'): alt_code = f"{stock_code}.SZ"
                    elif stock_code.startswith('4') or stock_code.startswith('8'): alt_code = f"{stock_code}.BJ"
                
                if alt_code:
                    logger.info(f"First attempt for {stock_code} failed, trying alternative code: {alt_code}")
                    info = await self.stock_repo.find_by_code(alt_code)
            
            # 临时硬编码 fallback (针对 Tushare 限流导致无法获取名称的情况)
            # if not info and (stock_code == '603601' or stock_code == '603601.SH'):
            #     logger.warning(f"Using hardcoded fallback for {stock_code}")
            #     # 构造一个临时的 StockInfo 对象或字典
            #     # 注意: 这里最好返回 StockInfo 模型实例，或者让调用者处理字典
            #     # 但 stock_repo.find_by_code 返回的是模型实例
            #     # 我们这里创建一个临时的模型实例
            #     info = StockInfo(
            #         code='603601.SH',
            #         name='中科曙光',
            #         market='SH',
            #         is_active=True
            #     )
            
            return info
        except Exception as e:
            logger.error(f"获取股票信息失败 (code: {stock_code}): {e}")
            raise
    
    async def create_or_update_stock_info(self, stock_data: Dict[str, Any]) -> StockInfo:
        """创建或更新股票基本信息"""
        try:
            stock_code = stock_data.get('stock_code')
            if not stock_code:
                raise ValueError("股票代码不能为空")
            
            # 检查是否已存在
            existing_stock = await self.stock_repo.find_by_code(stock_code)
            
            if existing_stock:
                # 更新现有股票信息
                update_data = {
                    'name': stock_data.get('stock_name', existing_stock.name),
                    'market': stock_data.get('market', existing_stock.market),
                    'is_active': stock_data.get('is_active', existing_stock.is_active)
                }
                return await self.stock_repo.update(existing_stock.id, update_data)
            else:
                # 创建新股票信息
                create_data = {
                    'code': stock_code,
                    'name': stock_data.get('stock_name', ''),
                    'market': stock_data.get('market', 'SZ'),
                    'is_active': stock_data.get('is_active', True)
                }
                return await self.stock_repo.create(create_data)
        except Exception as e:
            logger.error(f"创建或更新股票信息失败: {e}")
            raise
    
    async def get_stock_list(
        self, 
        market: Optional[str] = None,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[StockInfo]:
        """获取股票列表"""
        try:
            filters = {}
            if market:
                filters['market'] = market
            if active_only:
                filters['status'] = True
            
            return await self.stock_repo.get_multi(
                filters=filters,
                limit=limit,
                skip=offset
            )
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            raise
    
    async def submit_stock_data(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提交股票数据"""
        try:
            if not data_list:
                return {'success': 0, 'failed': 0, 'duplicated': 0, 'errors': []}
            
            success_count = 0
            failed_count = 0
            duplicated_count = 0
            errors = []
            
            for data in data_list:
                try:
                    # 验证必要字段
                    if not self._validate_stock_data(data):
                        failed_count += 1
                        errors.append(f"数据验证失败: {data}")
                        continue
                    
                    # 检查数据去重
                    is_duplicate = await self.dedup_service.check_duplicate(data)
                    if is_duplicate:
                        duplicated_count += 1
                        continue
                    
                    # 确保股票信息存在
                    stock_code = data['stock_code']
                    stock_info = await self.get_stock_info(stock_code)
                    if not stock_info:
                        # 创建基本股票信息
                        await self.create_or_update_stock_info({
                            'stock_code': stock_code,
                            'stock_name': data.get('stock_name', ''),
                            'market': data.get('market', 'SZ')
                        })
                    
                    # 创建股票数据记录
                    # 处理 request_timestamp
                    req_ts = data.get('request_timestamp')
                    req_ts_dt = datetime.now()
                    if isinstance(req_ts, (int, float)):
                        req_ts_dt = datetime.fromtimestamp(req_ts)
                    
                    price_val = Decimal(str(data.get('current_price', data.get('price'))))

                    stock_data_record = {
                        'code': stock_code,
                        'price': price_val,
                        'timestamp': date.today(),
                        'request_timestamp': req_ts_dt
                    }
                    
                    await self.stock_data_repo.create(stock_data_record)
                    ths_record = TonghuashunStock(
                        code=stock_code,
                        name=data.get('stock_name', ''),
                        current_price=price_val,
                        change_percent=Decimal(str(data.get('change_percent', 0))),
                        volume=data.get('volume', 0),
                        turnover=Decimal(str(data.get('turnover', 0))),
                        high=Decimal(str(data.get('high_price', price_val))),
                        low=Decimal(str(data.get('low_price', price_val))),
                        open_price=Decimal(str(data.get('open_price', price_val))),
                        prev_close=Decimal(str(data.get('prev_close', price_val))),
                        timestamp=date.today(),
                        request_timestamp=data.get('request_timestamp')
                    )
                    self.session.add(ths_record)
                    await self.session.flush()
                    
                    # 记录去重日志
                    await self.dedup_service.log_data(data)
                    
                    success_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    errors.append(f"处理数据失败 {data.get('stock_code', 'unknown')}: {str(e)}")
                    logger.error(f"处理股票数据失败: {e}")
            
            result = {
                'success': success_count,
                'failed': failed_count,
                'duplicated': duplicated_count,
                'total': len(data_list),
                'errors': errors
            }
            
            logger.info(f"股票数据提交完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"提交股票数据失败: {e}")
            raise
    
    def _validate_stock_data(self, data: Dict[str, Any]) -> bool:
        """验证股票数据"""
        try:
            # 检查必要字段
            required_fields = ['stock_code']
            if not all(field in data for field in required_fields):
                return False
            
            if 'price' not in data and 'current_price' not in data:
                return False
            
            # 检查股票代码格式
            stock_code = data['stock_code']
            # 允许6位纯数字或带后缀的代码 (例如 600000.SH)
            if not isinstance(stock_code, str) or len(stock_code) < 6:
                return False
            
            # 检查价格
            try:
                price = float(data.get('current_price', data.get('price')))
                if price <= 0:
                    return False
            except (ValueError, TypeError):
                return False
            
            # 检查成交量
            volume = data.get('volume', 0)
            if volume is not None:
                try:
                    volume = int(volume)
                    if volume < 0:
                        return False
                except (ValueError, TypeError):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证股票数据失败: {e}")
            return False
    
    async def get_stock_data(
        self,
        stock_code: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[StockData]:
        """获取股票数据"""
        try:
            if not start_time:
                start_time = datetime.now() - timedelta(days=30)
            if not end_time:
                end_time = datetime.now()
            
            data = await self.stock_data_repo.find_by_code(
                code=stock_code,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )

            if not data:
                # 尝试其他代码格式
                alt_code = None
                if '.' in stock_code:
                    alt_code = stock_code.split('.')[0]
                else:
                    if stock_code.startswith('6'): alt_code = f"{stock_code}.SH"
                    elif stock_code.startswith('0') or stock_code.startswith('3'): alt_code = f"{stock_code}.SZ"
                    elif stock_code.startswith('4') or stock_code.startswith('8'): alt_code = f"{stock_code}.BJ"
                
                if alt_code:
                    logger.info(f"First attempt for {stock_code} failed, trying alternative code: {alt_code}")
                    data = await self.stock_data_repo.find_by_code(
                        code=alt_code,
                        start_time=start_time,
                        end_time=end_time,
                        limit=limit
                    )
            
            return data
        except Exception as e:
            logger.error(f"获取股票数据失败 (code: {stock_code}): {e}")
            raise
    
    async def get_latest_stock_data(self, stock_code: str) -> Optional[StockData]:
        """获取最新股票数据"""
        try:
            data = await self.stock_data_repo.find_latest_by_code(stock_code)
            
            if not data:
                # 尝试其他代码格式
                alt_code = None
                if '.' in stock_code:
                    alt_code = stock_code.split('.')[0]
                else:
                    if stock_code.startswith('6'): alt_code = f"{stock_code}.SH"
                    elif stock_code.startswith('0') or stock_code.startswith('3'): alt_code = f"{stock_code}.SZ"
                    elif stock_code.startswith('4') or stock_code.startswith('8'): alt_code = f"{stock_code}.BJ"
                
                if alt_code:
                    logger.info(f"First attempt for {stock_code} failed, trying alternative code: {alt_code}")
                    data = await self.stock_data_repo.find_latest_by_code(alt_code)
            
            return data
        except Exception as e:
            logger.error(f"获取最新股票数据失败 (code: {stock_code}): {e}")
            raise
    
    async def get_recent_stock_data(
        self, 
        stock_code: str, 
        hours: int = 24
    ) -> List[StockData]:
        """获取最近的股票数据"""
        try:
            data = await self.stock_data_repo.find_recent_data(stock_code, hours)
            
            if not data:
                # 尝试其他代码格式
                alt_code = None
                if '.' in stock_code:
                    alt_code = stock_code.split('.')[0]
                else:
                    if stock_code.startswith('6'): alt_code = f"{stock_code}.SH"
                    elif stock_code.startswith('0') or stock_code.startswith('3'): alt_code = f"{stock_code}.SZ"
                    elif stock_code.startswith('4') or stock_code.startswith('8'): alt_code = f"{stock_code}.BJ"
                
                if alt_code:
                    logger.info(f"First attempt for {stock_code} failed, trying alternative code: {alt_code}")
                    data = await self.stock_data_repo.find_recent_data(alt_code, hours)
            
            return data
        except Exception as e:
            logger.error(f"获取最近股票数据失败 (code: {stock_code}): {e}")
            raise
    
    async def get_stock_data_by_price_range(
        self,
        stock_code: str,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        limit: int = 100
    ) -> List[StockData]:
        """根据价格范围获取股票数据"""
        try:
            # 先获取所有数据，然后在应用层过滤价格
            all_data = await self.stock_data_repo.find_by_code(
                code=stock_code,
                limit=limit * 2  # 获取更多数据以便过滤
            )
            
            if not all_data:
                # 尝试其他代码格式
                alt_code = None
                if '.' in stock_code:
                    alt_code = stock_code.split('.')[0]
                else:
                    if stock_code.startswith('6'): alt_code = f"{stock_code}.SH"
                    elif stock_code.startswith('0') or stock_code.startswith('3'): alt_code = f"{stock_code}.SZ"
                    elif stock_code.startswith('4') or stock_code.startswith('8'): alt_code = f"{stock_code}.BJ"
                
                if alt_code:
                    logger.info(f"First attempt for {stock_code} failed, trying alternative code: {alt_code}")
                    all_data = await self.stock_data_repo.find_by_code(
                        code=alt_code,
                        limit=limit * 2
                    )
            
            # 价格过滤
            filtered_data = []
            for data in all_data:
                if min_price is not None and data.price < min_price:
                    continue
                if max_price is not None and data.price > max_price:
                    continue
                filtered_data.append(data)
                if len(filtered_data) >= limit:
                    break
            
            return filtered_data
        except Exception as e:
            logger.error(f"根据价格范围获取股票数据失败 (code: {stock_code}): {e}")
            raise
    
    async def get_stock_statistics(self, stock_code: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """获取股票统计信息"""
        try:
            # 如果没有提供股票代码，返回全局统计信息
            if not stock_code:
                total_stocks = await self.stock_repo.count()
                return {
                    "total_stocks": total_stocks,
                    "message": "全局统计信息"
                }

            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            # 获取时间范围内的数据
            data_list = await self.stock_data_repo.find_by_code(
                code=stock_code,
                start_time=start_time,
                end_time=end_time,
                limit=1000
            )
            
            if not data_list:
                # 尝试其他代码格式
                alt_code = None
                if '.' in stock_code:
                    alt_code = stock_code.split('.')[0]
                else:
                    if stock_code.startswith('6'): alt_code = f"{stock_code}.SH"
                    elif stock_code.startswith('0') or stock_code.startswith('3'): alt_code = f"{stock_code}.SZ"
                    elif stock_code.startswith('4') or stock_code.startswith('8'): alt_code = f"{stock_code}.BJ"
                
                if alt_code:
                    logger.info(f"First attempt for {stock_code} failed, trying alternative code: {alt_code}")
                    data_list = await self.stock_data_repo.find_by_code(
                        code=alt_code,
                        start_time=start_time,
                        end_time=end_time,
                        limit=1000
                    )

            if not data_list:
                return {
                    'stock_code': stock_code,
                    'period_days': days,
                    'data_count': 0,
                    'message': '暂无数据'
                }
            
            # 计算统计信息
            prices = [float(data.price) for data in data_list]
            volumes = [data.volume for data in data_list if data.volume is not None]
            
            stats = {
                'stock_code': stock_code,
                'period_days': days,
                'data_count': len(data_list),
                'price_stats': {
                    'max_price': max(prices),
                    'min_price': min(prices),
                    'avg_price': sum(prices) / len(prices),
                    'latest_price': prices[0] if data_list else 0,  # 数据按时间倒序
                    'first_price': prices[-1] if data_list else 0
                },
                'volume_stats': {
                    'max_volume': max(volumes) if volumes else 0,
                    'min_volume': min(volumes) if volumes else 0,
                    'avg_volume': sum(volumes) / len(volumes) if volumes else 0,
                    'total_volume': sum(volumes) if volumes else 0
                },
                'time_range': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'latest_data_time': data_list[0].timestamp.isoformat() if data_list else None
                }
            }
            
            # 计算涨跌幅
            if len(prices) > 1:
                price_change = prices[0] - prices[-1]
                price_change_percent = (price_change / prices[-1]) * 100
                stats['price_change'] = {
                    'amount': price_change,
                    'percent': price_change_percent
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取股票统计信息失败 (code: {stock_code}): {e}")
            raise

    async def get_daily_data_with_fallback(
        self,
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 250,
        sync_if_missing: bool = True,
        force_sync: bool = False,
        preferred_platform: str = 'tushare'
    ) -> List[StockDaily]:
        """
        获取日线数据，如果数据库中没有则尝试同步
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制条数
            sync_if_missing: 是否在缺失时自动同步
            force_sync: 是否强制同步（忽略已有数据）
            preferred_platform: 优先使用的数据平台 (tushare/baostock/akshare)
            
        Returns:
            List[StockDaily]: 日线数据列表
        """
        try:
            data = []
            
            # 1. 如果不是强制同步，先尝试从数据库获取
            if not force_sync:
                query = select(StockDaily).where(StockDaily.code == stock_code)
                
                if start_date:
                    query = query.where(StockDaily.trade_date >= start_date)
                if end_date:
                    query = query.where(StockDaily.trade_date <= end_date)
                    
                query = query.order_by(StockDaily.trade_date.desc()).limit(limit)
                
                result = await self.session.execute(query)
                data = result.scalars().all()
                
                # 尝试其他代码格式
                if not data:
                    alt_code = None
                    if '.' in stock_code:
                        alt_code = stock_code.split('.')[0]
                    else:
                        if stock_code.startswith('6'): alt_code = f"{stock_code}.SH"
                        elif stock_code.startswith('0') or stock_code.startswith('3'): alt_code = f"{stock_code}.SZ"
                        elif stock_code.startswith('4') or stock_code.startswith('8'): alt_code = f"{stock_code}.BJ"
                    
                    if alt_code:
                        logger.info(f"First attempt for {stock_code} failed, trying alternative code: {alt_code}")
                        query = select(StockDaily).where(StockDaily.code == alt_code)
                        if start_date: query = query.where(StockDaily.trade_date >= start_date)
                        if end_date: query = query.where(StockDaily.trade_date <= end_date)
                        query = query.order_by(StockDaily.trade_date.desc()).limit(limit)
                        
                        result = await self.session.execute(query)
                        data = result.scalars().all()
                        if data:
                            stock_code = alt_code # Use found code
            
            # 2. 如果 (没有数据且允许同步) 或 (强制同步)，则执行同步
            should_sync = (not data and sync_if_missing) or force_sync
            
            if should_sync:
                logger.info(f"{'Force syncing' if force_sync else 'No data found'} for {stock_code}, attempting sync via {preferred_platform}...")
                
                success = False
                
                # 定义同步函数
                async def try_tushare():
                    try:
                        svc = TushareService(db_manager)
                        res = await svc.sync_daily_data(mode="full", codes=[stock_code])
                        return res.get("status") != "failed" and res.get("processed", 0) > 0
                    except Exception as e:
                        logger.error(f"Tushare sync failed: {e}")
                        return False
                
                async def try_baostock():
                    try:
                        svc = BaostockService(db_manager)
                        return await svc.sync_daily_data(stock_code, mode="full") > 0
                    except Exception as e:
                        logger.error(f"Baostock sync failed: {e}")
                        return False
                    
                async def try_akshare():
                    try:
                        svc = AkshareService(db_manager)
                        return await svc.sync_daily_data(stock_code, mode="full") > 0
                    except Exception as e:
                        logger.error(f"AkShare sync failed: {e}")
                        return False

                # 优先尝试
                if preferred_platform == 'tushare':
                    success = await try_tushare()
                elif preferred_platform == 'baostock':
                    success = await try_baostock()
                elif preferred_platform == 'akshare':
                    success = await try_akshare()
                
                # 失败则回退
                if not success:
                    platforms = ['tushare', 'baostock', 'akshare']
                    if preferred_platform in platforms:
                        platforms.remove(preferred_platform)
                    
                    for p in platforms:
                        logger.info(f"Primary platform {preferred_platform} failed, trying fallback: {p}")
                        if p == 'tushare':
                            if await try_tushare(): success = True; break
                        elif p == 'baostock':
                            if await try_baostock(): success = True; break
                        elif p == 'akshare':
                            if await try_akshare(): success = True; break
                
                if success:
                    # 重新查询
                    await self.session.commit() # 确保同步的数据可见
                    # Re-execute query
                    query = select(StockDaily).where(StockDaily.code == stock_code)
                    if start_date: query = query.where(StockDaily.trade_date >= start_date)
                    if end_date: query = query.where(StockDaily.trade_date <= end_date)
                    query = query.order_by(StockDaily.trade_date.desc()).limit(limit)
                    result = await self.session.execute(query)
                    data = result.scalars().all()
            
            return data
            
        except Exception as e:
            logger.error(f"获取日线数据失败 (code: {stock_code}): {e}")
            raise

    
    async def cleanup_old_data(self, days: int = 90) -> int:
        """清理旧数据"""
        try:
            return await self.stock_data_repo.cleanup_old_data(days)
        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
            raise
    
    async def batch_get_latest_data(self, stock_codes: List[str]) -> Dict[str, Optional[StockData]]:
        """批量获取最新股票数据"""
        try:
            result = {}
            for stock_code in stock_codes:
                try:
                    latest_data = await self.get_latest_stock_data(stock_code)
                    result[stock_code] = latest_data
                except Exception as e:
                    logger.error(f"获取股票 {stock_code} 最新数据失败: {e}")
                    result[stock_code] = None
            
            return result
        except Exception as e:
            logger.error(f"批量获取最新股票数据失败: {e}")
            raise
    
    async def search_stocks(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[StockInfo]:
        """搜索股票（支持股票代码和名称模糊匹配）"""
        try:
            return await self.stock_repo.search_stocks(
                keyword=query,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            logger.error(f"搜索股票失败 (keyword: {query}): {e}")
            raise
    
    async def get_stocks_with_pagination(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[StockInfo]:
        """获取分页股票列表"""
        try:
            return await self.stock_repo.get_stocks_with_pagination(
                limit=limit,
                offset=offset
            )
        except Exception as e:
            logger.error(f"获取分页股票列表失败: {e}")
            raise
    
    async def get_all_stock_data(
        self,
        limit: int = 1000,
        offset: int = 0,
        request_timestamp: Optional[str] = None,
        start_timestamp: Optional[str] = None,
        end_timestamp: Optional[str] = None,
        stock_code: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取所有股票数据，包含股票名称，返回(数据列表, 总数)"""
        try:
            return await self.stock_data_repo.find_all_stock_data_with_names(
                limit=limit,
                offset=offset,
                order_by_timestamp=True,
                request_timestamp=request_timestamp,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                stock_code=stock_code
            )
        except Exception as e:
            logger.error(f"获取所有股票数据失败: {e}")
            raise
    
    async def clear_test_data(self) -> Dict[str, Any]:
        """清空所有测试数据"""
        try:
            # 删除股票数据
            deleted_stock_data = await self.stock_data_repo.delete_all()
            
            # 删除去重日志
            deleted_dedup_logs = await self.dedup_repo.delete_all()
            
            # 删除同花顺原始数据（如果存在相关表）
            deleted_tonghuashun_data = 0
            try:
                # 这里可以添加删除同花顺原始数据的逻辑
                # deleted_tonghuashun_data = await self.tonghuashun_repo.delete_all()
                pass
            except Exception as e:
                logger.warning(f"删除同花顺数据失败: {e}")
            
            result = {
                'success': True,
                'deleted_stock_data': deleted_stock_data,
                'deleted_dedup_logs': deleted_dedup_logs,
                'deleted_tonghuashun_data': deleted_tonghuashun_data
            }
            
            logger.info(f"清空测试数据完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"清空测试数据失败: {e}")
            return {
                'success': False,
                'deleted_stock_data': 0,
                'deleted_dedup_logs': 0,
                'deleted_tonghuashun_data': 0,
                'error': str(e)
            }
    
    async def process_tonghuashun_raw_data(self, raw_data: Dict[str, Any], request_timestamp: Optional[str] = None) -> Dict[str, Any]:
        """
        处理同花顺原始数据
        
        Args:
            raw_data: 同花顺原始数据，格式如：
                {
                    "300466": {
                        "6": "9.65",
                        "7": "9.61",
                        "8": "9.67",
                        "9": "9.40",
                        "10": "9.40",
                        "13": "7199100.00",
                        "19": "68172919.00",
                        "199112": "-2.591",
                        "264648": "-0.250",
                        "526792": "2.798",
                        "1968584": "1.604",
                        "2034120": "",
                        "3541450": "5033981100.000",
                        "name": "赛摩智能"
                    }
                }
                
        Returns:
            Dict: 处理结果
        """
        try:
            # 验证时间范围 (09:30 - 15:10)
            # 使用服务器当前时间进行判断
            try:
                dt = datetime.now()
                current_time = dt.time()
                start_time = time(9, 30)
                end_time = time(15, 10)
                
                # 检查是否在交易时间范围内
                if not (start_time <= current_time <= end_time):
                    logger.info(f"⏳ 当前服务器时间 {current_time} 不在接收范围内 (09:30-15:10)，忽略此批数据")
                    return {
                        'success': True,
                        'processed_count': 0,
                        'ignored': True,
                        'message': f'Server time {current_time} out of range (09:30-15:10)'
                    }
                logger.info(f"✅ 当前服务器时间 {current_time} 在接收范围内 (09:30-15:10)，继续处理")
            except Exception as e:
                logger.error(f"⚠️ 时间检查出错: {e}，将尝试处理数据")

            stock_count = len(raw_data)
            logger.info(f"🔧 StockService开始处理同花顺原始数据，包含 {stock_count} 只股票")
            logger.info(f"🔍 raw_data 类型: {type(raw_data)}")
            
            # 检查数据格式并打印结构信息
            if isinstance(raw_data, dict):
                logger.info(f"📊 原始数据结构(字典): {list(raw_data.keys())[:5]}{'...' if stock_count > 5 else ''}")
            elif isinstance(raw_data, list):
                logger.info(f"📊 原始数据结构(列表): 包含 {stock_count} 个元素")
                # 打印前几个元素的结构
                for i, item in enumerate(raw_data[:3]):
                    if isinstance(item, list) and len(item) > 0:
                        logger.info(f"📋 元素 {i+1}: {item[0] if len(item) > 0 else '空'} (长度: {len(item)})")
                    else:
                        logger.info(f"📋 元素 {i+1}: {type(item)} = {item}")
            else:
                logger.error(f"❌ 未知的数据格式: {type(raw_data)}")
            
            # 使用解码器解码原始数据
            logger.info("🔍 开始调用解码器解码数据...")
            decoded_result = tonghuashun_decoder.decode_batch_data(raw_data)
            logger.info(f"📋 解码结果: {decoded_result}")
            
            if not decoded_result['success']:
                logger.error(f"❌ 解码同花顺数据失败: {decoded_result['errors']}")
                return {
                    'success': False,
                    'processed_count': 0,
                    'failed_count': decoded_result['failed_count'],
                    'errors': decoded_result['errors']
                }
            
            # 处理解码后的数据
            processed_count = 0
            failed_count = 0
            errors = []
            decoded_stocks = decoded_result.get('decoded_stocks', {})
            
            logger.info(f"✅ 解码成功，得到 {len(decoded_stocks)} 只股票的解码数据")
            
            for i, (stock_code, decoded_stock_data) in enumerate(decoded_stocks.items()):
                try:
                    logger.info(f"🏷️ 处理股票 {i+1}/{len(decoded_stocks)}: {stock_code}")
                    logger.info(f"📊 解码后数据: {decoded_stock_data}")
                    
                    # 验证解码数据
                    logger.info(f"🔍 验证股票 {stock_code} 的解码数据...")
                    is_valid = tonghuashun_decoder.validate_decoded_data(decoded_stock_data)
                    logger.info(f"✅ 验证结果: {is_valid}")
                    
                    if not is_valid:
                        error_msg = f"股票 {stock_code} 数据验证失败"
                        logger.warning(f"⚠️ {error_msg}")
                        errors.append(error_msg)
                        failed_count += 1
                        continue
                    
                    # 转换为标准股票数据格式
                    logger.info(f"🔄 转换股票 {stock_code} 为标准格式...")
                    standard_data = self._convert_to_standard_format(decoded_stock_data, request_timestamp)
                    logger.info(f"📊 标准格式数据: {standard_data}")
                    
                    # 确保股票信息存在
                    logger.info(f"🏢 确保股票 {stock_code} 信息存在...")
                    stock_info_data = {
                        'stock_code': stock_code,
                        'stock_name': decoded_stock_data.get('stock_name', ''),
                        'market': self._determine_market(stock_code)
                    }
                    logger.info(f"📋 股票信息: {stock_info_data}")
                    await self.create_or_update_stock_info(stock_info_data)
                    
                    # 检查数据去重
                    logger.info(f"🔍 检查股票 {stock_code} 数据是否重复...")
                    is_duplicate = await self.dedup_service.check_duplicate(standard_data)
                    logger.info(f"🔄 重复检查结果: {is_duplicate}")
                    
                    if is_duplicate:
                        logger.debug(f"⚠️ 股票 {stock_code} 数据重复，跳过")
                        continue
                    
                    # 创建股票数据记录
                    logger.info(f"💾 保存股票 {stock_code} 数据到数据库...")
                    await self.stock_data_repo.create(standard_data)
                    ths_record = TonghuashunStock(
                        code=stock_code,
                        name=decoded_stock_data.get('stock_name', ''),
                        current_price=Decimal(str(decoded_stock_data.get('current_price'))),
                        change_percent=Decimal(str(decoded_stock_data.get('change_percent', 0))),
                        volume=decoded_stock_data.get('volume', 0),
                        turnover=Decimal(str(decoded_stock_data.get('turnover', 0))),
                        high=Decimal(str(decoded_stock_data.get('high_price', decoded_stock_data.get('current_price', 0)))),
                        low=Decimal(str(decoded_stock_data.get('low_price', decoded_stock_data.get('current_price', 0)))),
                        open_price=Decimal(str(decoded_stock_data.get('open_price', decoded_stock_data.get('current_price', 0)))),
                        prev_close=Decimal(str(decoded_stock_data.get('prev_close', decoded_stock_data.get('current_price', 0)))),
                        amplitude=Decimal(str(decoded_stock_data.get('amplitude', 0))) if decoded_stock_data.get('amplitude') else None,
                        turnover_rate=Decimal(str(decoded_stock_data.get('turnover_rate', 0))) if decoded_stock_data.get('turnover_rate') else None,
                        pe_ratio=Decimal(str(decoded_stock_data.get('pe_ratio', 0))) if decoded_stock_data.get('pe_ratio') else None,
                        market_cap=Decimal(str(decoded_stock_data.get('market_cap', 0))) if decoded_stock_data.get('market_cap') else None,
                        timestamp=date.today(),
                        request_timestamp=request_timestamp
                    )
                    self.session.add(ths_record)
                    await self.session.flush()
                    processed_count += 1
                    
                    logger.info(f"✅ 成功处理股票 {stock_code} 数据")
                    
                except Exception as e:
                    error_msg = f"处理股票 {stock_code} 失败: {e}"
                    logger.error(f"💥 {error_msg}")
                    import traceback
                    logger.error(f"📋 错误堆栈: {traceback.format_exc()}")
                    errors.append(error_msg)
                    failed_count += 1
            
            result = {
                'success': True,
                'processed_count': processed_count,
                'failed_count': failed_count,
                'total_decoded': decoded_result['total_count'],
                'errors': errors,
                'processed_at': datetime.now().isoformat()
            }
            
            logger.info(f"🎯 同花顺数据处理完成: 成功 {processed_count} 只，失败 {failed_count} 只")
            
            return result
            
        except Exception as e:
            logger.error(f"💥 处理同花顺原始数据失败: {e}")
            import traceback
            logger.error(f"📋 错误堆栈: {traceback.format_exc()}")
            return {
                'success': False,
                'processed_count': 0,
                'failed_count': 0,
                'errors': [str(e)],
                'processed_at': datetime.now().isoformat()
            }
    
    def _convert_to_standard_format(self, decoded_data: Dict[str, Any], request_timestamp: Optional[str] = None) -> Dict[str, Any]:
        """
        将解码后的数据转换为标准股票数据格式
        
        Args:
            decoded_data: 解码后的数据
            request_timestamp: 请求时间戳
            
        Returns:
            Dict: 标准格式的股票数据
        """
        try:
            # 计算涨跌额（如果没有提供）
            change_amount = decoded_data.get('change_amount')
            if change_amount is None:
                current_price = decoded_data.get('current_price', 0)
                prev_close = decoded_data.get('prev_close', 0)
                if current_price and prev_close:
                    change_amount = current_price - prev_close
            
            # 计算涨跌幅（如果没有提供）
            change_percent = decoded_data.get('change_percent')
            if change_percent is None and change_amount is not None:
                prev_close = decoded_data.get('prev_close', 0)
                if prev_close and prev_close > 0:
                    change_percent = (change_amount / prev_close) * 100
            
            # 确保涨跌幅在合理范围内 (DECIMAL(8,4) 最大值约为 9999.9999)
            if change_percent is not None:
                change_percent = max(-9999.9999, min(9999.9999, float(change_percent)))
            
            # 只包含StockData模型实际支持的字段
            standard_data = {
                'code': decoded_data['stock_code'],
                'price': Decimal(str(decoded_data.get('current_price', 0))),
                'change_percent': Decimal(str(change_percent or 0)),
                'volume': decoded_data.get('volume', 0),
                'high_price': Decimal(str(decoded_data.get('high_price', 0))),
                'low_price': Decimal(str(decoded_data.get('low_price', 0))),
                'open_price': Decimal(str(decoded_data.get('open_price', 0))),
                'timestamp': date.today(),  # 使用date而不是datetime
                'request_timestamp': request_timestamp  # 添加请求时间戳
            }
            
            return standard_data
            
        except Exception as e:
            logger.error(f"转换标准格式失败: {e}")
            raise
    
    def _determine_market(self, stock_code: str) -> str:
        """
        根据股票代码确定市场
        
        Args:
            stock_code: 股票代码
            
        Returns:
            str: 市场代码
        """
        if stock_code.startswith(('60', '68', '90')):
            return 'SH'  # 上海证券交易所
        elif stock_code.startswith(('00', '30')):
            return 'SZ'  # 深圳证券交易所
        elif stock_code.startswith(('4', '8', '920')):
            return 'BJ'  # 北京证券交易所
        else:
            return 'UNKNOWN'

    async def toggle_stock_status(self, stock_code: str, is_active: bool) -> bool:
        """
        切换股票状态 (激活/停用)
        """
        try:
            stock = await self.stock_repo.find_by_code(stock_code)
            if not stock:
                raise ValueError(f"股票 {stock_code} 不存在")
            
            await self.stock_repo.update(stock.id, {"is_active": is_active})
            return True
        except Exception as e:
            logger.error(f"切换股票状态失败: {e}")
            raise

    async def move_to_wencai(self, stock_code: str) -> bool:
        """
        将股票移动到问财股票表 (复制)
        """
        try:
            # 1. 获取股票信息
            stock = await self.stock_repo.find_by_code(stock_code)
            if not stock:
                raise ValueError(f"股票 {stock_code} 不存在")
            
            # 2. 检查问财表中是否已存在
            query = select(WencaiStock).where(WencaiStock.stock_code == stock_code)
            result = await self.session.execute(query)
            existing = result.scalar_one_or_none()
            
            if existing:
                return True # 已经存在
            
            # 3. 创建问财股票记录
            # 尝试获取最新价格
            latest_data = await self.stock_data_repo.find_latest_by_code(stock_code)
            current_price = latest_data.price if latest_data else None
            volume = latest_data.volume if latest_data else None
            
            new_wencai = WencaiStock(
                stock_code=stock.code,
                stock_name=stock.name,
                current_price=current_price,
                volume=volume,
                concept="From Stock List",
                created_at=datetime.now()
            )
            self.session.add(new_wencai)
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"移动股票到问财表失败: {e}")
            raise

    async def move_to_stock_info(self, wencai_id: int) -> bool:
        """
        将股票从问财表移动到股票信息表 (复制)
        """
        try:
            # 1. 获取问财股票信息
            query = select(WencaiStock).where(WencaiStock.id == wencai_id)
            result = await self.session.execute(query)
            wencai_stock = result.scalar_one_or_none()
            
            if not wencai_stock:
                raise ValueError(f"问财股票 ID {wencai_id} 不存在")
            
            # 2. 检查股票信息表中是否已存在
            existing_stock = await self.stock_repo.find_by_code(wencai_stock.stock_code)
            
            if existing_stock:
                # 如果已存在但未激活，则激活
                if not existing_stock.is_active:
                    await self.stock_repo.update(existing_stock.id, {"is_active": True})
                return True
            
            # 3. 创建股票信息记录
            market = self._determine_market(wencai_stock.stock_code)
            
            new_stock = StockInfo(
                code=wencai_stock.stock_code,
                name=wencai_stock.stock_name,
                market=market,
                is_active=True,
                created_at=datetime.now()
            )
            
            # Use repository to create to handle potential auto-increment or other logic if needed, 
            # but repository.create commits.
            await self.stock_repo.create({
                "code": wencai_stock.stock_code,
                "name": wencai_stock.stock_name,
                "market": market,
                "is_active": True
            })
            
            return True
            
        except Exception as e:
            logger.error(f"移动股票到信息表失败: {e}")
            raise
