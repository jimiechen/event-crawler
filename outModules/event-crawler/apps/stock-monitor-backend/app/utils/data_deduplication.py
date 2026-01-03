#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据去重机制实现
使用SHA256哈希算法进行重复数据检测
"""

import json
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass
from decimal import Decimal
from loguru import logger
from app.utils.database_pool import DatabasePool

@dataclass
class DeduplicationConfig:
    """去重配置"""
    # 数据保留时间（小时）
    retention_hours: int = 24
    # 清理间隔（分钟）
    cleanup_interval_minutes: int = 60
    # 内存缓存大小限制
    memory_cache_limit: int = 10000

class DataDeduplicationManager:
    """数据去重管理器"""
    
    def __init__(self, db_pool: DatabasePool, config: Optional[DeduplicationConfig] = None):
        self.db_pool = db_pool
        self.config = config or DeduplicationConfig()
        # 内存缓存，用于快速检查最近的重复数据
        self._memory_cache: Set[str] = set()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    def _generate_hash(self, data: Dict[str, Any], exclude_fields: Optional[Set[str]] = None) -> str:
        """
        生成数据的SHA256哈希值
        
        Args:
            data: 要计算哈希的数据
            exclude_fields: 排除的字段（如timestamp等时间相关字段）
        
        Returns:
            SHA256哈希值
        """
        # 创建数据副本，排除指定字段
        filtered_data = data.copy()
        exclude_fields = exclude_fields or {'timestamp', 'created_at', 'updated_at'}
        
        for field in exclude_fields:
            filtered_data.pop(field, None)
        
        # 确保数据的一致性排序
        normalized_data = json.dumps(filtered_data, sort_keys=True, ensure_ascii=False)
        
        # 生成SHA256哈希
        return hashlib.sha256(normalized_data.encode('utf-8')).hexdigest()
    
    async def is_duplicate(self, data: Dict[str, Any], data_type: str = 'stock_data') -> bool:
        """
        检查数据是否重复
        
        Args:
            data: 要检查的数据
            data_type: 数据类型
        
        Returns:
            True表示重复，False表示不重复
        """
        data_hash = self._generate_hash(data)
        
        # 首先检查内存缓存
        if data_hash in self._memory_cache:
            return True
        
        # 检查数据库
        async with self.db_pool.get_connection_context() as conn:
            async with self.db_pool.get_cursor_context(conn) as cursor:
                query = """
                SELECT COUNT(*) as count 
                FROM data_dedup_log 
                WHERE data_hash = %s AND table_name = %s
                AND created_at > %s
                """
                
                # 只检查保留时间内的数据
                cutoff_time = datetime.now() - timedelta(hours=self.config.retention_hours)
                
                await cursor.execute(query, (data_hash, data_type, cutoff_time))
                result = await cursor.fetchone()
                
                is_dup = result['count'] > 0
                
                # 如果不重复，记录到数据库和内存缓存
                if not is_dup:
                    await self._record_hash(cursor, data_hash, data_type, data)
                    self._add_to_memory_cache(data_hash)
                
                return is_dup
    
    def _serialize_data(self, data: Any) -> str:
        """
        序列化数据为JSON字符串，处理datetime和Decimal类型
        
        Args:
            data: 要序列化的数据
        
        Returns:
            JSON字符串
        """
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, Decimal):
                return float(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return json.dumps(data, ensure_ascii=False, default=json_serializer)
    
    async def _record_hash(self, cursor, data_hash: str, data_type: str, original_data: Dict[str, Any]):
        """
        记录数据哈希到数据库
        
        Args:
            cursor: 数据库游标
            data_hash: 数据哈希值
            data_type: 数据类型
            original_data: 原始数据
        """
        query = """
        INSERT INTO data_dedup_log (data_hash, table_name, original_data, created_at)
        VALUES (%s, %s, %s, %s)
        """
        
        await cursor.execute(query, (
            data_hash,
            data_type,
            self._serialize_data(original_data),
            datetime.now()
        ))
    
    def _add_to_memory_cache(self, data_hash: str):
        """
        添加哈希到内存缓存
        
        Args:
            data_hash: 数据哈希值
        """
        # 如果缓存已满，移除一些旧的条目
        if len(self._memory_cache) >= self.config.memory_cache_limit:
            # 简单的FIFO策略，移除一半的缓存
            cache_list = list(self._memory_cache)
            self._memory_cache = set(cache_list[len(cache_list)//2:])
        
        self._memory_cache.add(data_hash)
    
    async def start_cleanup_task(self):
        """
        启动定期清理任务
        """
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup_task(self):
        """
        停止定期清理任务
        """
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    async def _cleanup_loop(self):
        """
        定期清理过期数据
        """
        while self._running:
            try:
                await self._cleanup_expired_data()
                await asyncio.sleep(self.config.cleanup_interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"清理任务出错: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再重试
    
    async def _cleanup_expired_data(self):
        """
        清理过期的去重数据
        """
        async with self.db_pool.get_connection_context() as conn:
            async with self.db_pool.get_cursor_context(conn) as cursor:
                cutoff_time = datetime.now() - timedelta(hours=self.config.retention_hours)
                
                # 删除过期数据
                delete_query = """
                DELETE FROM data_dedup_log 
                WHERE created_at < %s
                """
                
                await cursor.execute(delete_query, (cutoff_time,))
                deleted_count = cursor.rowcount
                
                if deleted_count > 0:
                    print(f"清理了 {deleted_count} 条过期的去重记录")
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取去重统计信息
        
        Returns:
            统计信息字典
        """
        async with self.db_pool.get_connection_context() as conn:
            async with self.db_pool.get_cursor_context(conn) as cursor:
                # 总记录数
                await cursor.execute("SELECT COUNT(*) as total FROM data_dedup_log")
                total_result = await cursor.fetchone()
                
                # 按数据类型统计
                await cursor.execute("""
                    SELECT table_name, COUNT(*) as count 
                    FROM data_dedup_log 
                    GROUP BY table_name
                """)
                type_stats = await cursor.fetchall()
                
                # 最近24小时的记录数
                cutoff_time = datetime.now() - timedelta(hours=24)
                await cursor.execute("""
                    SELECT COUNT(*) as recent_count 
                    FROM data_dedup_log 
                    WHERE created_at > %s
                """, (cutoff_time,))
                recent_result = await cursor.fetchone()
                
                return {
                    'total_records': total_result['total'],
                    'recent_24h_records': recent_result['recent_count'],
                    'memory_cache_size': len(self._memory_cache),
                    'memory_cache_limit': self.config.memory_cache_limit,
                    'retention_hours': self.config.retention_hours,
                    'type_statistics': {row['table_name']: row['count'] for row in type_stats}
                }

# 全局去重管理器实例
_deduplication_manager: Optional[DataDeduplicationManager] = None

def init_deduplication_manager(db_pool: DatabasePool, config: Optional[DeduplicationConfig] = None) -> DataDeduplicationManager:
    """
    初始化全局去重管理器
    
    Args:
        db_pool: 数据库连接池
        config: 去重配置
    
    Returns:
        去重管理器实例
    """
    global _deduplication_manager
    _deduplication_manager = DataDeduplicationManager(db_pool, config)
    return _deduplication_manager

def get_deduplication_manager() -> Optional[DataDeduplicationManager]:
    """
    获取全局去重管理器实例
    
    Returns:
        去重管理器实例，如果未初始化则返回None
    """
    return _deduplication_manager

async def check_duplicate(data: Dict[str, Any], data_type: str = 'stock_data') -> bool:
    """
    便捷函数：检查数据是否重复
    
    Args:
        data: 要检查的数据
        data_type: 数据类型
    
    Returns:
        True表示重复，False表示不重复
    """
    manager = get_deduplication_manager()
    if not manager:
        raise RuntimeError("去重管理器未初始化")
    
    return await manager.is_duplicate(data, data_type)

async def get_deduplication_stats() -> Dict[str, Any]:
    """
    便捷函数：获取去重统计信息
    
    Returns:
        统计信息字典
    """
    manager = get_deduplication_manager()
    if not manager:
        raise RuntimeError("去重管理器未初始化")
    
    return await manager.get_stats()