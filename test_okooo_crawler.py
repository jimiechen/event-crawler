#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
澳客爬虫测试脚本
"""

import asyncio
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def test_okooo_crawler():
    """测试澳客爬虫"""
    try:
        logger.info("Starting ooooo crawler test...")
        
        # 导入爬虫相关模块
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from apps.stock_monitor_backend.app.crawler.okooo_crawler import OkoooCrawler
        
        # 配置数据库连接
        # 注意：这里使用SQLite内存数据库进行测试，避免依赖真实数据库
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False
        )
        
        # 创建异步会话工厂
        AsyncSessionLocal = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # 创建数据库表（如果需要）
        # 这里使用SQLite内存数据库，不需要创建表
        
        # 创建数据库会话
        async with AsyncSessionLocal() as session:
            # 创建爬虫实例
            crawler = OkoooCrawler(session)
            
            # 测试fetch_and_parse方法
            logger.info("Testing fetch_and_parse method...")
            result = await crawler.fetch_and_parse(
                debug_url="https://m.okooo.com/jczq/"
            )
            
            logger.info(f"Fetch result: {result}")
            
            # 检查结果
            if result.get("status") == "success":
                logger.info("✓ Crawler fetch succeeded")
                logger.info(f"Total items: {result.get('total')}")
                
                # 打印前几个解析结果
                data = result.get("data", [])
                logger.info(f"First few items: {data[:3]}")
            else:
                logger.error(f"✗ Crawler fetch failed: {result.get('error')}")
                
    except Exception as e:
        logger.error(f"✗ Test failed with exception: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        logger.info("Test completed")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_okooo_crawler())
