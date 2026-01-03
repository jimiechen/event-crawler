#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接管理模块
提供异步数据库连接池和会话管理
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    AsyncEngine, 
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.pool import QueuePool
from sqlalchemy import event, text
from loguru import logger

from .config.database import DatabaseConfig, get_config
from .models.base import Base


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or get_config()
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """初始化数据库连接"""
        if self._initialized:
            return
        
        try:
            self.config.validate()
            if self.config.db_type.lower() == "sqlite":
                self.engine = create_async_engine(
                    self._get_async_url(),
                    echo=False,
                    connect_args={"check_same_thread": False}
                )
            else:
                self.engine = create_async_engine(
                    self._get_async_url(),
                    echo=False,
                    pool_size=self.config.min_size,
                    max_overflow=self.config.max_size - self.config.min_size,
                    pool_timeout=self.config.pool_timeout,
                    pool_recycle=self.config.pool_recycle,
                    pool_pre_ping=True,
                    connect_args={
                        "charset": self.config.charset,
                        "autocommit": False,
                    }
                )
        
            # 创建会话工厂
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
            
            # 注册事件监听器
            self._register_events()
            
            self._initialized = True
            logger.info(f"数据库连接池初始化成功: {self.config.host}:{self.config.port}/{self.config.database}")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            # 如果是MySQL且数据库不存在，尝试自动创建数据库后重试
            err_msg = str(e)
            if self.config.db_type.lower() == "mysql" and ("Unknown database" in err_msg or "1049" in err_msg):
                try:
                    # 使用系统库连接，创建数据库
                    admin_url = (
                        f"mysql+aiomysql://{self.config.user}:{self.config.password}"
                        f"@{self.config.host}:{self.config.port}/mysql"
                    )
                    admin_engine = create_async_engine(admin_url, echo=False, pool_pre_ping=True)
                    async with admin_engine.begin() as conn:
                        await conn.exec_driver_sql(
                            f"CREATE DATABASE IF NOT EXISTS `{self.config.database}` CHARACTER SET {self.config.charset} COLLATE utf8mb4_unicode_ci"
                        )
                    await admin_engine.dispose()
                    # 创建成功后重试初始化
                    self.engine = create_async_engine(self._get_async_url(), echo=False, pool_pre_ping=True)
                    self.session_factory = async_sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False, autoflush=True, autocommit=False)
                    self._register_events()
                    self._initialized = True
                    logger.info(f"数据库已创建并初始化成功: {self.config.host}:{self.config.port}/{self.config.database}")
                except Exception as ce:
                    logger.error(f"自动创建数据库失败: {ce}")
                    raise
            else:
                raise
    
    async def close(self) -> None:
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()
            logger.info("数据库连接池已关闭")
    
    def _get_async_url(self) -> str:
        """获取异步数据库连接URL"""
        if self.config.db_type.lower() == "sqlite":
            return f"sqlite+aiosqlite:///{self.config.database}"
        else:
            return (
                f"mysql+aiomysql://{self.config.user}:{self.config.password}"
                f"@{self.config.host}:{self.config.port}/{self.config.database}"
            )
    
    def _register_events(self) -> None:
        """注册数据库事件监听器"""
        if not self.engine:
            return
        
        # 只为MySQL注册字符集设置事件
        if self.config.db_type.lower() != "sqlite":
            @event.listens_for(self.engine.sync_engine, "connect")
            def set_mysql_charset(dbapi_connection, connection_record):
                """设置MySQL字符集"""
                cursor = dbapi_connection.cursor()
                try:
                    cursor.execute(f"SET NAMES {self.config.charset}")
                finally:
                    cursor.close()
        
        @event.listens_for(self.engine.sync_engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """连接检出事件"""
            logger.debug("数据库连接检出")
        
        @event.listens_for(self.engine.sync_engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """连接检入事件"""
            logger.debug("数据库连接检入")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话上下文管理器"""
        if not self._initialized:
            await self.initialize()
        
        if not self.session_factory:
            raise RuntimeError("数据库会话工厂未初始化")
        
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库会话异常: {e}")
            raise
        finally:
            await session.close()
    
    async def create_tables(self) -> None:
        """创建数据库表"""
        if not self.engine:
            await self.initialize()
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")
            raise
    
    async def drop_tables(self) -> None:
        """删除数据库表"""
        if not self.engine:
            await self.initialize()
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("数据库表删除成功")
        except Exception as e:
            logger.error(f"删除数据库表失败: {e}")
            raise
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return False


# 全局数据库管理器实例
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖注入函数"""
    async with db_manager.get_session() as session:
        yield session


async def init_database() -> None:
    """初始化数据库"""
    await db_manager.initialize()


async def close_database() -> None:
    """关闭数据库连接"""
    await db_manager.close()


# 便捷函数
async def create_all_tables() -> None:
    """创建所有表"""
    await db_manager.create_tables()


async def drop_all_tables() -> None:
    """删除所有表"""
    await db_manager.drop_tables()


async def database_health_check() -> bool:
    """数据库健康检查"""
    return await db_manager.health_check()
