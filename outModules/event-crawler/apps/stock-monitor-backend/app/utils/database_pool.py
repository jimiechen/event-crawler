# -*- coding: utf-8 -*-
"""
异步MySQL数据库连接池模块
提供高性能的异步数据库连接池，支持自动重连和连接管理
"""

import asyncio
import logging
from typing import Optional, AsyncGenerator, Any, Dict
from contextlib import asynccontextmanager
import aiomysql
from aiomysql import Pool, Connection, Cursor
from app.config.database import DatabaseConfig, default_config


logger = logging.getLogger(__name__)


class DatabasePool:
    """异步MySQL数据库连接池类"""
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or default_config
        self._pool: Optional[Pool] = None
        self._lock = asyncio.Lock()
        self._is_closed = False
    
    async def initialize(self) -> None:
        """初始化连接池"""
        if self._pool is not None:
            logger.warning("数据库连接池已经初始化")
            return
        
        async with self._lock:
            if self._pool is not None:
                return
            
            try:
                logger.info(f"正在初始化数据库连接池，配置: {self.config.host}:{self.config.port}/{self.config.database}")
                
                self._pool = await aiomysql.create_pool(
                    host=self.config.host,
                    port=self.config.port,
                    user=self.config.user,
                    password=self.config.password,
                    db=self.config.database,
                    charset=self.config.charset,
                    minsize=self.config.min_size,
                    maxsize=self.config.max_size,
                    pool_recycle=self.config.pool_recycle,
                    autocommit=True,
                    echo=False
                )
                
                logger.info(f"数据库连接池初始化成功，连接数: {self.config.min_size}-{self.config.max_size}")
                
            except Exception as e:
                logger.error(f"数据库连接池初始化失败: {e}")
                raise
    
    async def close(self) -> None:
        """关闭连接池"""
        if self._pool is None or self._is_closed:
            return
        
        async with self._lock:
            if self._pool is None or self._is_closed:
                return
            
            try:
                logger.info("正在关闭数据库连接池")
                self._pool.close()
                await self._pool.wait_closed()
                self._pool = None
                self._is_closed = True
                logger.info("数据库连接池已关闭")
            except Exception as e:
                logger.error(f"关闭数据库连接池失败: {e}")
    
    async def get_connection(self) -> Connection:
        """获取数据库连接（带重试机制）"""
        if self._pool is None:
            await self.initialize()
        
        for attempt in range(self.config.max_retries):
            try:
                conn = await asyncio.wait_for(
                    self._pool.acquire(),
                    timeout=self.config.pool_timeout
                )
                
                # 测试连接是否有效
                await conn.ping()
                return conn
                
            except (aiomysql.Error, asyncio.TimeoutError) as e:
                logger.warning(f"获取数据库连接失败 (尝试 {attempt + 1}/{self.config.max_retries}): {e}")
                
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    # 尝试重新初始化连接池
                    if attempt == self.config.max_retries - 2:
                        await self._reinitialize_pool()
                else:
                    raise ConnectionError(f"无法获取数据库连接，已重试 {self.config.max_retries} 次")
    
    async def release_connection(self, conn: Connection) -> None:
        """释放数据库连接"""
        if self._pool and conn:
            try:
                self._pool.release(conn)
            except Exception as e:
                logger.error(f"释放数据库连接失败: {e}")
    
    async def _reinitialize_pool(self) -> None:
        """重新初始化连接池"""
        try:
            logger.info("正在重新初始化数据库连接池")
            await self.close()
            self._is_closed = False
            await self.initialize()
        except Exception as e:
            logger.error(f"重新初始化连接池失败: {e}")
    
    @asynccontextmanager
    async def get_connection_context(self) -> AsyncGenerator[Connection, None]:
        """连接上下文管理器"""
        conn = None
        try:
            conn = await self.get_connection()
            yield conn
        finally:
            if conn:
                await self.release_connection(conn)
    
    @asynccontextmanager
    async def get_cursor_context(self, conn: Connection = None) -> AsyncGenerator[Cursor, None]:
        """游标上下文管理器"""
        cursor = None
        connection_acquired = False
        
        try:
            if conn is None:
                conn = await self.get_connection()
                connection_acquired = True
            
            cursor = await conn.cursor(aiomysql.DictCursor)
            yield cursor
            
        finally:
            if cursor:
                await cursor.close()
            if connection_acquired and conn:
                await self.release_connection(conn)
    
    async def execute_query(self, sql: str, params: tuple = None) -> list:
        """执行查询语句"""
        async with self.get_connection_context() as conn:
            async with self.get_cursor_context(conn) as cursor:
                await cursor.execute(sql, params)
                return await cursor.fetchall()
    
    async def execute_one(self, sql: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """执行查询语句并返回单条记录"""
        async with self.get_connection_context() as conn:
            async with self.get_cursor_context(conn) as cursor:
                await cursor.execute(sql, params)
                return await cursor.fetchone()
    
    async def execute_update(self, sql: str, params: tuple = None) -> int:
        """执行更新语句"""
        async with self.get_connection_context() as conn:
            async with self.get_cursor_context(conn) as cursor:
                result = await cursor.execute(sql, params)
                await conn.commit()
                return result
    
    async def execute_many(self, sql: str, params_list: list) -> int:
        """批量执行语句"""
        async with self.get_connection_context() as conn:
            async with self.get_cursor_context(conn) as cursor:
                result = await cursor.executemany(sql, params_list)
                await conn.commit()
                return result
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """获取连接池状态"""
        if self._pool is None:
            return {"status": "not_initialized"}
        
        return {
            "status": "active",
            "size": self._pool.size,
            "used": self._pool.size - self._pool.freesize,
            "free": self._pool.freesize,
            "min_size": self.config.min_size,
            "max_size": self.config.max_size
        }


# 全局数据库连接池实例
db_pool: Optional[DatabasePool] = None

# 便捷函数
async def init_database(config: DatabaseConfig = None) -> bool:
    """初始化数据库连接池"""
    global db_pool
    try:
        db_pool = DatabasePool(config or default_config)
        await db_pool.initialize()
        logger.info("数据库连接池初始化成功")
        return True
    except Exception as e:
        logger.error(f"数据库连接池初始化失败: {e}")
        return False


async def close_database():
    """关闭数据库连接池"""
    await db_pool.close()


@asynccontextmanager
async def get_db_connection():
    """获取数据库连接的便捷函数"""
    async with db_pool.get_connection_context() as conn:
        yield conn


@asynccontextmanager
async def get_db_cursor(conn: Connection = None):
    """获取数据库游标的便捷函数"""
    async with db_pool.get_cursor_context(conn) as cursor:
        yield cursor


# 便捷的数据库操作函数
async def execute_query(sql: str, params: tuple = None) -> list:
    """执行查询语句"""
    return await db_pool.execute_query(sql, params)


async def execute_one(sql: str, params: tuple = None) -> Optional[Dict[str, Any]]:
    """执行查询语句并返回单条记录"""
    return await db_pool.execute_one(sql, params)


async def execute_update(sql: str, params: tuple = None) -> int:
    """执行更新语句"""
    return await db_pool.execute_update(sql, params)


async def execute_many(sql: str, params_list: list) -> int:
    """批量执行语句"""
    return await db_pool.execute_many(sql, params_list)


async def get_pool_status() -> Dict[str, Any]:
    """获取连接池状态"""
    return await db_pool.get_pool_status()