#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据去重服务
处理股票数据去重相关的业务逻辑
"""

import hashlib
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..repositories.stock_repository import DataDedupRepository
from ..models.stock import DataDedupLog


class DataDedupService:
    """数据去重服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.dedup_repo = DataDedupRepository(session)
    
    def generate_data_hash(self, data: Dict[str, Any]) -> str:
        """生成数据哈希值"""
        try:
            # 提取关键字段用于生成哈希
            key_fields = {
                'stock_code': data.get('stock_code'),
                'price': str(data.get('price', '')),
                'volume': data.get('volume', 0),
                'data_time': data.get('data_time', datetime.now()).isoformat() if isinstance(data.get('data_time'), datetime) else str(data.get('data_time', ''))
            }
            
            # 按键排序确保一致性
            sorted_data = json.dumps(key_fields, sort_keys=True, ensure_ascii=False)
            
            # 生成MD5哈希
            hash_obj = hashlib.md5(sorted_data.encode('utf-8'))
            return hash_obj.hexdigest()
            
        except Exception as e:
            logger.error(f"生成数据哈希失败: {e}")
            # 返回基于时间戳的备用哈希
            fallback_data = f"{data.get('stock_code', '')}{datetime.now().timestamp()}"
            return hashlib.md5(fallback_data.encode('utf-8')).hexdigest()
    
    async def check_duplicate(self, data: Dict[str, Any]) -> bool:
        """检查数据是否重复"""
        try:
            data_hash = self.generate_data_hash(data)
            return await self.dedup_repo.check_hash_exists('stock_prices', data_hash)
        except Exception as e:
            logger.error(f"检查数据重复失败: {e}")
            # 出错时假设不重复，避免丢失数据
            return False
    
    async def log_data(self, data: Dict[str, Any]) -> DataDedupLog:
        """记录数据去重日志"""
        try:
            data_hash = self.generate_data_hash(data)
            
            # 将Decimal对象转换为字符串以支持JSON序列化
            serializable_data = {}
            for key, value in data.items():
                if hasattr(value, '__class__') and value.__class__.__name__ == 'Decimal':
                    serializable_data[key] = str(value)
                elif isinstance(value, datetime):
                    serializable_data[key] = value.isoformat()
                else:
                    serializable_data[key] = value
            
            log_data = {
                'table_name': 'stock_prices',
                'data_hash': data_hash,
                'hash_fields': 'stock_code,price,volume,data_time',
                'original_data': serializable_data
            }
            
            return await self.dedup_repo.create(log_data)
        except Exception as e:
            logger.error(f"记录去重日志失败: {e}")
            raise
    
    async def check_and_log(self, data: Dict[str, Any]) -> Tuple[bool, Optional[DataDedupLog]]:
        """检查重复并记录日志"""
        try:
            is_duplicate = await self.check_duplicate(data)
            
            if not is_duplicate:
                # 不重复则记录日志
                log_entry = await self.log_data(data)
                return False, log_entry
            else:
                return True, None
        except Exception as e:
            logger.error(f"检查重复并记录日志失败: {e}")
            # 出错时假设不重复，避免丢失数据
            return False, None

    async def get_dedup_statistics(self) -> Dict[str, Any]:
        """获取去重统计信息"""
        try:
            total_logs = await self.dedup_repo.count()
            return {
                "total_logs": total_logs,
                "duplicate_rate": 0.0,
                "message": "去重统计信息"
            }
        except Exception as e:
            logger.error(f"获取去重统计信息失败: {e}")
            return {
                "total_logs": 0,
                "duplicate_rate": 0.0,
                "error": str(e)
            }
    
    async def get_dedup_stats(self, days: int = 7) -> Dict[str, Any]:
        """获取去重统计信息"""
        try:
            return await self.dedup_repo.get_dedup_stats(days)
        except Exception as e:
            logger.error(f"获取去重统计信息失败: {e}")
            raise
    
    async def cleanup_old_logs(self, days: int = 30) -> int:
        """清理旧的去重日志"""
        try:
            deleted_count = await self.dedup_repo.cleanup_old_logs(days)
            logger.info(f"清理了 {deleted_count} 条旧的去重日志")
            return deleted_count
        except Exception as e:
            logger.error(f"清理旧去重日志失败: {e}")
            raise
    
    async def get_duplicate_data_by_stock(
        self, 
        stock_code: str, 
        hours: int = 24
    ) -> List[DataDedupLog]:
        """获取指定股票的重复数据记录"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # 这里需要在repository中添加相应的查询方法
            # 暂时返回空列表，后续可以扩展
            return []
        except Exception as e:
            logger.error(f"获取股票重复数据记录失败 (code: {stock_code}): {e}")
            raise
    
    async def validate_data_integrity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证数据完整性"""
        try:
            validation_result = {
                'is_valid': True,
                'errors': [],
                'warnings': []
            }
            
            # 检查必要字段
            required_fields = ['stock_code', 'price']
            for field in required_fields:
                if field not in data or data[field] is None:
                    validation_result['is_valid'] = False
                    validation_result['errors'].append(f"缺少必要字段: {field}")
            
            # 检查股票代码格式
            stock_code = data.get('stock_code')
            if stock_code:
                if not isinstance(stock_code, str) or len(stock_code) != 6 or not stock_code.isdigit():
                    validation_result['is_valid'] = False
                    validation_result['errors'].append(f"无效的股票代码格式: {stock_code}")
            
            # 检查价格
            price = data.get('price')
            if price is not None:
                try:
                    price_float = float(price)
                    if price_float <= 0:
                        validation_result['is_valid'] = False
                        validation_result['errors'].append(f"价格必须大于0: {price}")
                    elif price_float > 10000:
                        validation_result['warnings'].append(f"价格异常高: {price}")
                except (ValueError, TypeError):
                    validation_result['is_valid'] = False
                    validation_result['errors'].append(f"无效的价格格式: {price}")
            
            # 检查成交量
            volume = data.get('volume')
            if volume is not None:
                try:
                    volume_int = int(volume)
                    if volume_int < 0:
                        validation_result['is_valid'] = False
                        validation_result['errors'].append(f"成交量不能为负数: {volume}")
                except (ValueError, TypeError):
                    validation_result['warnings'].append(f"无效的成交量格式: {volume}")
            
            # 检查时间
            data_time = data.get('data_time')
            if data_time:
                if isinstance(data_time, str):
                    try:
                        datetime.fromisoformat(data_time.replace('Z', '+00:00'))
                    except ValueError:
                        validation_result['warnings'].append(f"无效的时间格式: {data_time}")
                elif not isinstance(data_time, datetime):
                    validation_result['warnings'].append(f"时间字段类型错误: {type(data_time)}")
            
            return validation_result
        except Exception as e:
            logger.error(f"验证数据完整性失败: {e}")
            return {
                'is_valid': False,
                'errors': [f"验证过程出错: {str(e)}"],
                'warnings': []
            }
    
    async def batch_check_duplicates(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量检查重复数据"""
        try:
            total_count = len(data_list)
            duplicate_count = 0
            new_count = 0
            errors = []
            
            for i, data in enumerate(data_list):
                try:
                    is_duplicate = await self.check_duplicate(data)
                    if is_duplicate:
                        duplicate_count += 1
                    else:
                        new_count += 1
                except Exception as e:
                    errors.append(f"检查第{i+1}条数据失败: {str(e)}")
            
            result = {
                'total': total_count,
                'duplicates': duplicate_count,
                'new_data': new_count,
                'errors': len(errors),
                'error_details': errors
            }
            
            logger.info(f"批量去重检查完成: {result}")
            return result
        except Exception as e:
            logger.error(f"批量检查重复数据失败: {e}")
            raise
    
    async def get_hash_collision_stats(self) -> Dict[str, Any]:
        """获取哈希碰撞统计（用于监控哈希算法效果）"""
        try:
            # 获取最近7天的数据
            stats = await self.get_dedup_stats(7)
            
            # 计算哈希碰撞率（这里简化处理）
            total_logs = stats.get('total_logs', 0)
            unique_hashes = stats.get('unique_hashes', 0)
            
            collision_rate = 0
            if total_logs > 0:
                collision_rate = (total_logs - unique_hashes) / total_logs * 100
            
            return {
                'total_logs': total_logs,
                'unique_hashes': unique_hashes,
                'collision_rate_percent': round(collision_rate, 4),
                'hash_efficiency': round((unique_hashes / total_logs * 100) if total_logs > 0 else 0, 2)
            }
        except Exception as e:
            logger.error(f"获取哈希碰撞统计失败: {e}")
            raise
    
    async def optimize_dedup_performance(self) -> Dict[str, Any]:
        """优化去重性能（清理旧数据、重建索引等）"""
        try:
            # 清理30天前的旧日志
            cleaned_logs = await self.cleanup_old_logs(30)
            
            # 获取当前统计信息
            current_stats = await self.get_dedup_stats(7)
            
            optimization_result = {
                'cleaned_old_logs': cleaned_logs,
                'current_stats': current_stats,
                'optimization_time': datetime.now().isoformat(),
                'recommendations': []
            }
            
            # 添加优化建议
            total_logs = current_stats.get('total_logs', 0)
            if total_logs > 100000:
                optimization_result['recommendations'].append(
                    "建议增加清理频率，当前日志数量较多"
                )
            
            if cleaned_logs > 10000:
                optimization_result['recommendations'].append(
                    "建议调整日志保留策略，清理了大量旧数据"
                )
            
            logger.info(f"去重性能优化完成: 清理 {cleaned_logs} 条旧日志")
            return optimization_result
        except Exception as e:
            logger.error(f"优化去重性能失败: {e}")
            raise