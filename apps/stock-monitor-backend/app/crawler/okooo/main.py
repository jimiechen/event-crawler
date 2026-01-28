# -*- coding: utf-8 -*-
import asyncio
import logging
import sys
import os

# 添加项目根目录到sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.database import DatabaseManager
from app.services.redis_cache_service import RedisCacheService
from app.crawler.okooo.scheduler import OkoooScheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """
    Okooo爬虫调度器测试
    """
    logger.info("Starting Okooo Scheduler Test...")

    # 1. 初始化服务
    db_manager = DatabaseManager()
    redis_service = RedisCacheService()

    # 验证服务连接
    if not redis_service.ping():
        logger.error("Redis connection failed")
        return
        
    try:
        await db_manager.initialize()
        await db_manager.create_tables()
    except Exception as e:
        logger.error(f"Database init failed: {e}")
        return

    # 2. 启动调度器
    # 设置较小的并发数进行测试
    scheduler = OkoooScheduler(db_manager, redis_service, concurrency=2, delay=2.0)
    
    try:
        # 测试爬取一个小范围的ID
        # 这里的ID 1143895 是之前的示例ID，我们可以取附近几个
        start_id = 1143895
        end_id = 1143897
        
        await scheduler.crawl_range(start_id, end_id)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
    finally:
        await scheduler.close()
        await db_manager.close()
        logger.info("Scheduler test finished")

if __name__ == "__main__":
    asyncio.run(main())
