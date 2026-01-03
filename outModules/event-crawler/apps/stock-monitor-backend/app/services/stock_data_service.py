#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同花顺股票数据服务
负责股票数据的存储和管理
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.utils.database_pool import execute_query, execute_one, execute_update, execute_many
from app.utils.data_deduplication import check_duplicate

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StockInfo:
    """股票基本信息"""
    code: str
    name: str
    market: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class StockData:
    """股票实时数据"""
    stock_code: str
    current_price: float
    change_amount: float
    change_percent: float
    volume: int
    turnover: float
    data_timestamp: datetime
    data_hash: str
    raw_data: str

class StockDataService:
    """股票数据服务类"""
    
    def __init__(self):
        """初始化股票数据服务"""
        self.logger = logging.getLogger(__name__)
        self._monitoring = False
        self._monitor_task = None
    
    async def sync_stock_info(self, stocks: List[Dict[str, Any]]) -> int:
        """同步股票信息到数据库"""
        try:
            if not stocks:
                self.logger.warning("股票列表为空")
                return 0
            
            # 使用REPLACE INTO来处理重复数据
            insert_data = []
            for stock in stocks:
                insert_data.append((
                    stock['code'],
                    stock['name'],
                    stock.get('market', 'unknown'),
                    datetime.now(),
                    datetime.now()
                ))
            
            if insert_data:
                sql = """
                REPLACE INTO stock_info (code, name, market, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                """
                count = await execute_many(sql, insert_data)
                self.logger.info(f"同步股票信息成功: {count} 条")
                return count
            
            return 0
            
        except Exception as e:
            self.logger.error(f"同步股票信息失败: {e}")
            return 0
    
    async def get_monitor_stock_list(self) -> List[str]:
        """
        获取需要监控的股票代码列表
        
        Returns:
            List[str]: 股票代码列表
        """
        try:
            results = await execute_query(
                "SELECT stock_code FROM monitor_list WHERE is_active = %s ORDER BY priority DESC, created_at ASC",
                (True,)
            )
            
            stock_codes = [row['stock_code'] for row in results]
            logger.info(f"获取到 {len(stock_codes)} 只监控股票")
            
            return stock_codes
            
        except Exception as e:
            logger.error(f"获取监控股票列表失败: {e}")
            return []
    
    async def store_stock_data(self, stock_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """存储股票实时数据"""
        try:
            if not stock_data_list:
                self.logger.warning("股票数据列表为空")
                return {'success': True, 'stored_count': 0, 'duplicate_count': 0}
            
            stored_count = 0
            duplicate_count = 0
            
            for stock_data in stock_data_list:
                try:
                    # 检查数据是否重复
                    is_duplicate = await check_duplicate(stock_data, 'stock_data')
                    
                    if is_duplicate:
                        duplicate_count += 1
                        continue
                    
                    # 存储股票数据
                    sql = """
                    INSERT INTO stock_data 
                    (code, name, price, change_amount, change_percent, volume, 
                     turnover, high, low, open_price, prev_close, timestamp, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """
                    
                    await execute_update(sql, (
                        stock_data['code'],
                        stock_data['name'],
                        stock_data['price'],
                        stock_data.get('change_amount', 0),
                        stock_data.get('change_percent', 0),
                        stock_data.get('volume', 0),
                        stock_data.get('turnover', 0),
                        stock_data.get('high', 0),
                        stock_data.get('low', 0),
                        stock_data.get('open_price', 0),
                        stock_data.get('prev_close', 0),
                        stock_data.get('timestamp', datetime.now())
                    ))
                    
                    stored_count += 1
                    
                except Exception as e:
                    self.logger.error(f"存储股票数据失败 {stock_data.get('code', 'unknown')}: {e}")
                    continue
            
            self.logger.info(f"股票数据处理完成: 存储 {stored_count} 条，重复 {duplicate_count} 条")
            
            return {
                'success': True,
                'total_count': len(stock_data_list),
                'stored_count': stored_count,
                'duplicate_count': duplicate_count
            }
            
        except Exception as e:
            self.logger.error(f"存储股票数据失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'stored_count': 0,
                'duplicate_count': 0
            }
    
    async def _is_duplicate_data(self, data_hash: str) -> bool:
        """
        检查数据是否重复
        
        Args:
            data_hash: 数据哈希值
            
        Returns:
            bool: 是否重复
        """
        try:
            result = await execute_one(
                "SELECT id FROM data_dedup_log WHERE data_hash = %s LIMIT 1",
                (data_hash,)
            )
            return result is not None
            
        except Exception as e:
            logger.error(f"检查重复数据失败: {e}")
            return False
    
    async def process_tonghuashun_raw_data(self, raw_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理同花顺原始数据
        
        Args:
            raw_data_list: 原始数据列表，包含 url, responseBody 等
            
        Returns:
            Dict: 处理结果
        """
        processed_count = 0
        total_count = len(raw_data_list)
        parsed_stocks = []
        
        for item in raw_data_list:
            try:
                # 获取响应体
                body = item.get('responseBody')
                if not body:
                    continue
                
                # 尝试解析 JSON
                data = None
                if isinstance(body, str):
                    try:
                        data = json.loads(body)
                    except json.JSONDecodeError:
                        continue
                elif isinstance(body, dict):
                    data = body
                else:
                    continue
                
                if not data:
                    continue

                # 提取股票数据
                stocks = self._extract_stocks_from_data(data)
                parsed_stocks.extend(stocks)
                
                if stocks:
                    processed_count += 1
                    
            except Exception as e:
                self.logger.error(f"处理单条同花顺数据失败: {e}")
                continue
        
        if parsed_stocks:
            # 存储数据
            # 强制使用当前时间，忽略原始数据中的时间戳
            current_time = datetime.now()
            for stock in parsed_stocks:
                stock['timestamp'] = current_time
            
            store_result = await self.store_stock_data(parsed_stocks)
            return {
                'success': True,
                'received_count': total_count,
                'processed_items': processed_count,
                'parsed_stocks': len(parsed_stocks),
                'stored_count': store_result.get('stored_count', 0),
                'duplicate_count': store_result.get('duplicate_count', 0)
            }
        
        return {
            'success': True,
            'received_count': total_count,
            'processed_items': processed_count,
            'parsed_stocks': 0,
            'stored_count': 0,
            'duplicate_count': 0
        }

    def _extract_stocks_from_data(self, data: Any) -> List[Dict[str, Any]]:
        """从任意JSON数据中提取股票信息 (递归搜索)"""
        stocks = []
        
        if isinstance(data, dict):
            # 检查当前字典是否像股票数据
            # 同花顺常见字段: stockcode/code, stockname/zwjc, newprice/xj/zxj
            code = data.get('stockcode') or data.get('code') or data.get('sc')
            name = data.get('stockname') or data.get('zwjc') or data.get('name')
            
            # 价格字段可能有很多种变体
            price = data.get('xj') or data.get('zxj') or data.get('newprice') or data.get('price') or data.get('c')
            
            if code and (name or price):
                try:
                    # 尝试标准化数据
                    stock_item = {
                        'code': str(code),
                        'name': str(name) if name else '',
                        'price': float(price) if price else 0.0,
                        'change_percent': float(data.get('zdf', 0) or data.get('pc', 0) or 0),
                        'change_amount': float(data.get('zde', 0) or data.get('ud', 0) or 0),
                        'volume': int(data.get('cjl', 0) or data.get('v', 0) or 0),
                        'turnover': float(data.get('cje', 0) or data.get('amount', 0) or 0),
                        'high': float(data.get('zg', 0) or data.get('h', 0) or 0),
                        'low': float(data.get('zd', 0) or data.get('l', 0) or 0),
                        'open_price': float(data.get('kp', 0) or data.get('o', 0) or 0),
                        'prev_close': float(data.get('zs', 0) or data.get('yc', 0) or 0),
                    }
                    stocks.append(stock_item)
                except (ValueError, TypeError):
                    pass
            
            # 递归搜索所有值
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    stocks.extend(self._extract_stocks_from_data(value))
                    
        elif isinstance(data, list):
            for item in data:
                stocks.extend(self._extract_stocks_from_data(item))
                
        return stocks

    async def start_continuous_monitoring(self, interval: int = 30) -> bool:
        """开始连续监控股票数据"""
        if self._monitoring:
            self.logger.warning("监控已在运行中")
            return False
        
        try:
            self._monitoring = True
            self._monitor_task = asyncio.create_task(self._monitor_loop(interval))
            self.logger.info(f"开始连续监控，间隔: {interval} 秒")
            return True
        except Exception as e:
            self.logger.error(f"启动监控失败: {e}")
            self._monitoring = False
            return False
    
    async def stop_continuous_monitoring(self) -> bool:
        """停止连续监控"""
        if not self._monitoring:
            self.logger.warning("监控未在运行")
            return False
        
        try:
            self._monitoring = False
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
                self._monitor_task = None
            
            self.logger.info("监控已停止")
            return True
        except Exception as e:
            self.logger.error(f"停止监控失败: {e}")
            return False
    
    async def _monitor_loop(self, interval: int):
        """监控循环 - 等待外部数据推送"""
        while self._monitoring:
            try:
                # 这里只是保持监控状态，实际数据由API接口接收
                self.logger.debug("监控状态检查")
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"监控循环异常: {e}")
                await asyncio.sleep(interval)
    
    @property
    def is_monitoring(self) -> bool:
        """获取监控状态"""
        return self._monitoring
    
    async def add_monitor_stock(self, stock_code: str, priority: int = 1) -> bool:
        """
        添加监控股票
        
        Args:
            stock_code: 股票代码
            priority: 优先级（1-10，数字越大优先级越高）
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 检查股票是否存在
            stock_info = await execute_one(
                "SELECT code FROM stock_info WHERE code = %s",
                (stock_code,)
            )
            
            if not stock_info:
                logger.error(f"股票代码 {stock_code} 不存在于股票信息表中")
                return False
            
            # 检查是否已在监控列表中
            existing = await execute_one(
                "SELECT id FROM monitor_list WHERE stock_code = %s",
                (stock_code,)
            )
            
            if existing:
                # 更新优先级和状态
                await execute_update(
                    "UPDATE monitor_list SET priority = %s, is_active = %s, updated_at = NOW() WHERE stock_code = %s",
                    (priority, True, stock_code)
                )
                logger.info(f"更新监控股票: {stock_code}，优先级: {priority}")
            else:
                # 添加新的监控股票
                await execute_update(
                    "INSERT INTO monitor_list (stock_code, priority, is_active, created_at, updated_at) VALUES (%s, %s, %s, NOW(), NOW())",
                    (stock_code, priority, True)
                )
                logger.info(f"添加监控股票: {stock_code}，优先级: {priority}")
            
            return True
            
        except Exception as e:
            logger.error(f"添加监控股票失败: {e}")
            return False
    
    async def remove_monitor_stock(self, stock_code: str) -> bool:
        """
        移除监控股票
        
        Args:
            stock_code: 股票代码
            
        Returns:
            bool: 是否移除成功
        """
        try:
            await execute_update(
                "UPDATE monitor_list SET is_active = %s, updated_at = NOW() WHERE stock_code = %s",
                (False, stock_code)
            )
            
            logger.info(f"移除监控股票: {stock_code}")
            return True
            
        except Exception as e:
            logger.error(f"移除监控股票失败: {e}")
            return False
    
    async def get_stock_data_by_code(self, stock_code: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        根据股票代码获取历史数据
        
        Args:
            stock_code: 股票代码
            limit: 返回数据条数限制
            
        Returns:
            List[Dict]: 股票历史数据列表
        """
        try:
            # 获取股票基本信息
            stock_info = await execute_one(
                "SELECT code, name, market FROM stock_info WHERE code = %s AND is_active = %s",
                (stock_code, True)
            )
            
            if not stock_info:
                logger.warning(f"股票代码 {stock_code} 不存在或已停用")
                return []
            
            # 获取股票历史数据
            stock_data = await execute_query(
                """
                SELECT stock_code, current_price, change_amount, change_percent, 
                       volume, turnover, high_price, low_price, open_price, 
                       prev_close_price, data_timestamp, created_at
                FROM stock_data 
                WHERE stock_code = %s 
                ORDER BY data_timestamp DESC, created_at DESC 
                LIMIT %s
                """,
                (stock_code, limit)
            )
            
            # 格式化返回数据
            result = {
                'stock_info': {
                    'code': stock_info['code'],
                    'name': stock_info['name'],
                    'market': stock_info['market']
                },
                'data_count': len(stock_data),
                'data_list': []
            }
            
            for data in stock_data:
                result['data_list'].append({
                    'stock_code': data['stock_code'],
                    'current_price': float(data['current_price']) if data['current_price'] else 0,
                    'change_amount': float(data['change_amount']) if data['change_amount'] else 0,
                    'change_percent': float(data['change_percent']) if data['change_percent'] else 0,
                    'volume': int(data['volume']) if data['volume'] else 0,
                    'turnover': float(data['turnover']) if data['turnover'] else 0,
                    'high_price': float(data['high_price']) if data['high_price'] else 0,
                    'low_price': float(data['low_price']) if data['low_price'] else 0,
                    'open_price': float(data['open_price']) if data['open_price'] else 0,
                    'prev_close_price': float(data['prev_close_price']) if data['prev_close_price'] else 0,
                    'data_timestamp': data['data_timestamp'].isoformat() if data['data_timestamp'] else None,
                    'created_at': data['created_at'].isoformat() if data['created_at'] else None
                })
            
            logger.info(f"获取股票 {stock_code} 历史数据成功，共 {len(stock_data)} 条")
            return result
            
        except Exception as e:
            logger.error(f"获取股票 {stock_code} 历史数据失败: {e}")
            return []
    
    async def get_stock_data_statistics(self) -> Dict[str, Any]:
        """
        获取股票数据统计信息
        
        Returns:
            Dict: 统计信息
        """
        try:
            # 总股票数
            total_stocks = await execute_one("SELECT COUNT(*) as count FROM stock_info WHERE is_active = %s", (True,))
            
            # 监控股票数
            monitor_stocks = await execute_one("SELECT COUNT(*) as count FROM monitor_list WHERE is_active = %s", (True,))
            
            # 今日数据条数
            today_data = await execute_one(
                "SELECT COUNT(*) as count FROM stock_data WHERE DATE(created_at) = CURDATE()"
            )
            
            # 去重日志条数
            dedup_logs = await execute_one("SELECT COUNT(*) as count FROM data_dedup_log")
            
            # 最新数据时间
            latest_data = await execute_one(
                "SELECT MAX(data_timestamp) as latest_time FROM stock_data"
            )
            
            return {
                'total_stocks': total_stocks['count'] if total_stocks else 0,
                'monitor_stocks': monitor_stocks['count'] if monitor_stocks else 0,
                'today_data_count': today_data['count'] if today_data else 0,
                'total_dedup_logs': dedup_logs['count'] if dedup_logs else 0,
                'latest_data_time': latest_data['latest_time'].isoformat() if latest_data and latest_data['latest_time'] else None,
                'is_monitoring': self.is_monitoring
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                'total_stocks': 0,
                'monitor_stocks': 0,
                'today_data_count': 0,
                'total_dedup_logs': 0,
                'latest_data_time': None,
                'is_monitoring': False
            }
    
    async def cleanup_old_data(self, days: int = 30) -> Dict[str, Any]:
        """
        清理旧数据
        
        Args:
            days: 保留天数
            
        Returns:
            Dict: 清理结果
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 清理旧的股票数据
            stock_data_result = await execute_update(
                "DELETE FROM stock_data WHERE created_at < %s",
                (cutoff_date,)
            )
            
            # 清理旧的去重日志
            dedup_result = await execute_update(
                "DELETE FROM data_dedup_log WHERE created_at < %s",
                (cutoff_date,)
            )
            
            logger.info(f"数据清理完成: 删除 {stock_data_result} 条股票数据，{dedup_result} 条去重日志")
            
            return {
                'success': True,
                'deleted_stock_data': stock_data_result,
                'deleted_dedup_logs': dedup_result,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'deleted_stock_data': 0,
                'deleted_dedup_logs': 0
            }
    
    async def clear_test_data(self) -> Dict[str, Any]:
        """
        清空所有测试数据
        
        Returns:
            Dict: 清理结果
        """
        try:
            # 清空股票数据表
            stock_data_result = await execute_update("DELETE FROM stock_data")
            
            # 清空去重日志表
            dedup_result = await execute_update("DELETE FROM data_dedup_log")
            
            # 清空同花顺原始数据表（如果存在）
            try:
                tonghuashun_result = await execute_update("DELETE FROM tonghuashun_raw_data")
            except Exception:
                tonghuashun_result = 0  # 表可能不存在
            
            logger.info(f"测试数据清理完成: 删除 {stock_data_result} 条股票数据，{dedup_result} 条去重日志，{tonghuashun_result} 条同花顺数据")
            
            return {
                'success': True,
                'deleted_stock_data': stock_data_result,
                'deleted_dedup_logs': dedup_result,
                'deleted_tonghuashun_data': tonghuashun_result,
                'message': '所有测试数据已清空，准备接收生产数据'
            }
            
        except Exception as e:
            logger.error(f"清空测试数据失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'deleted_stock_data': 0,
                'deleted_dedup_logs': 0,
                'deleted_tonghuashun_data': 0
            }

# 使用示例
if __name__ == "__main__":
    async def main():
        # 创建股票数据服务
        service = StockDataService()
        
        try:
            # 同步股票信息
            sync_result = await service.sync_stock_info_from_web()
            print(f"同步结果: {sync_result}")
            
            # 获取统计信息
            stats = await service.get_stock_data_statistics()
            print(f"统计信息: {stats}")
            
            # 添加监控股票（示例）
            await service.add_monitor_stock('000001', priority=5)
            await service.add_monitor_stock('000002', priority=3)
            
            # 手动抓取一次数据
            stock_codes = await service.get_monitor_stock_list()
            if stock_codes:
                fetch_result = await service.fetch_and_store_stock_data(stock_codes)
                print(f"抓取结果: {fetch_result}")
        
        except Exception as e:
            print(f"测试失败: {e}")
    
    # 运行测试
    asyncio.run(main())