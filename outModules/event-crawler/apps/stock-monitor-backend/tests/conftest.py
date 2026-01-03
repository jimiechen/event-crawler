#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest配置文件
"""

import os
import sys
import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.models.base import Base
from app.database import DatabaseManager, get_db_session


# 测试数据库URL（使用内存SQLite）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        }
    )
    
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # 清理
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_client(test_session) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    
    # 覆盖数据库依赖
    async def override_get_db_session():
        yield test_session
    
    app.dependency_overrides[get_db_session] = override_get_db_session
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # 清理依赖覆盖
    app.dependency_overrides.clear()


@pytest.fixture
def sample_stock_info():
    """示例股票信息"""
    return {
        "code": "000001",
        "name": "平安银行",
        "market": "SZ",
        "is_active": True
    }


@pytest.fixture
def sample_stock_data():
    """示例股票数据"""
    from datetime import datetime
    return {
        "code": "000001",
        "name": "平安银行",
        "price": 12.50,
        "volume": 1000000,
        "turnover": 12500000.0,
        "high": 12.80,
        "low": 12.20,
        "open_price": 12.30,
        "prev_close": 12.30,
        "change_amount": 0.20,
        "change_percent": 1.63,
        "timestamp": datetime.now()
    }


@pytest.fixture
def sample_monitor():
    """示例监控配置"""
    return {
        "code": "000001",
        "priority": 5,
        "is_active": True
    }


@pytest.fixture
def multiple_stock_codes():
    """多个股票代码"""
    return ["000001", "000002", "600000", "600036", "000858"]


@pytest.fixture
def multiple_stock_data():
    """多个股票数据"""
    return [
        {
            "stock_code": "000001",
            "price": 12.50,
            "volume": 1000000,
            "turnover": 12500000.0,
            "high": 12.80,
            "low": 12.20,
            "open": 12.30,
            "close": 12.50,
            "change": 0.20,
            "change_percent": 1.63
        },
        {
            "stock_code": "000002",
            "price": 25.30,
            "volume": 800000,
            "turnover": 20240000.0,
            "high": 25.50,
            "low": 25.00,
            "open": 25.10,
            "close": 25.30,
            "change": 0.30,
            "change_percent": 1.20
        }
    ]


# 配置pytest-asyncio
# pytest-asyncio 0.21+ 不需要手动配置mark