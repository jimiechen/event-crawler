#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问财表结构迁移脚本
执行SQL迁移文件，添加TDX支持所需的字段
"""

import os
import sys
import argparse
from pathlib import Path
from loguru import logger

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import db_manager
from sqlalchemy import text


async def check_column_exists(table_name: str, column_name: str) -> bool:
    """检查字段是否已存在"""
    async with db_manager.get_session() as session:
        # 使用数据库配置中的数据库名
        from app.config.database import get_config
        config = get_config()
        database_name = config.database
        
        sql = """
        SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_schema = :database_name
        AND table_name = :table_name 
        AND column_name = :column_name
        """
        result = await session.execute(text(sql), {
            "database_name": database_name,
            "table_name": table_name,
            "column_name": column_name
        })
        count = result.scalar()
        return count > 0


async def add_column(table_name: str, column_name: str, column_def: str):
    """添加字段"""
    async with db_manager.get_session() as session:
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"
        await session.execute(text(sql))
        await session.commit()
        logger.info(f"✅ 添加字段 {table_name}.{column_name}")


async def create_index(index_name: str, table_name: str, column_name: str):
    """创建索引"""
    async with db_manager.get_session() as session:
        # 使用数据库配置中的数据库名
        from app.config.database import get_config
        config = get_config()
        database_name = config.database
        
        # 检查索引是否存在
        check_sql = """
        SELECT COUNT(*) FROM information_schema.statistics 
        WHERE table_schema = :database_name
        AND table_name = :table_name 
        AND index_name = :index_name
        """
        result = await session.execute(text(check_sql), {
            "database_name": database_name,
            "table_name": table_name,
            "index_name": index_name
        })
        if result.scalar() > 0:
            logger.info(f"⚠️ 索引 {index_name} 已存在，跳过")
            return
        
        sql = f"CREATE INDEX {index_name} ON {table_name}({column_name})"
        await session.execute(text(sql))
        await session.commit()
        logger.info(f"✅ 创建索引 {index_name}")


async def migrate_wencai_batches():
    """迁移 wencai_crawl_batches 表"""
    logger.info("\n📦 迁移 wencai_crawl_batches 表...")
    
    # 添加 source 字段
    if not await check_column_exists("wencai_crawl_batches", "source"):
        await add_column(
            "wencai_crawl_batches",
            "source",
            "VARCHAR(20) DEFAULT 'wencai' COMMENT '数据来源(wencai/tdx)'"
        )
    else:
        logger.info("⚠️ 字段 source 已存在，跳过")
    
    # 添加 sector_code 字段
    if not await check_column_exists("wencai_crawl_batches", "sector_code"):
        await add_column(
            "wencai_crawl_batches",
            "sector_code",
            "VARCHAR(20) DEFAULT NULL COMMENT 'TDX板块代码(如: 3BL0325)'"
        )
    else:
        logger.info("⚠️ 字段 sector_code 已存在，跳过")
    
    # 添加 query_date 字段
    if not await check_column_exists("wencai_crawl_batches", "query_date"):
        await add_column(
            "wencai_crawl_batches",
            "query_date",
            "DATE DEFAULT NULL COMMENT '查询日期'"
        )
    else:
        logger.info("⚠️ 字段 query_date 已存在，跳过")
    
    # 创建索引
    await create_index("idx_wencai_batch_source", "wencai_crawl_batches", "source")
    await create_index("idx_wencai_batch_sector", "wencai_crawl_batches", "sector_code")
    await create_index("idx_wencai_batch_query_date", "wencai_crawl_batches", "query_date")


async def migrate_wencai_stocks():
    """迁移 wencai_stocks 表"""
    logger.info("\n📦 迁移 wencai_stocks 表...")
    
    # 添加 source 字段
    if not await check_column_exists("wencai_stocks", "source"):
        await add_column(
            "wencai_stocks",
            "source",
            "VARCHAR(20) DEFAULT 'wencai' COMMENT '数据来源(wencai/tdx)'"
        )
    else:
        logger.info("⚠️ 字段 source 已存在，跳过")
    
    # 添加 change_percent 字段
    if not await check_column_exists("wencai_stocks", "change_percent"):
        await add_column(
            "wencai_stocks",
            "change_percent",
            "DECIMAL(8, 4) DEFAULT NULL COMMENT '涨跌幅(%)'"
        )
    else:
        logger.info("⚠️ 字段 change_percent 已存在，跳过")
    
    # 添加 volume_ratio 字段
    if not await check_column_exists("wencai_stocks", "volume_ratio"):
        await add_column(
            "wencai_stocks",
            "volume_ratio",
            "DECIMAL(10, 4) DEFAULT NULL COMMENT '成交量比值'"
        )
    else:
        logger.info("⚠️ 字段 volume_ratio 已存在，跳过")
    
    # 添加 turnover 字段
    if not await check_column_exists("wencai_stocks", "turnover"):
        await add_column(
            "wencai_stocks",
            "turnover",
            "DECIMAL(20, 3) DEFAULT NULL COMMENT '成交额(元)'"
        )
    else:
        logger.info("⚠️ 字段 turnover 已存在，跳过")
    
    # 添加 high_price 字段
    if not await check_column_exists("wencai_stocks", "high_price"):
        await add_column(
            "wencai_stocks",
            "high_price",
            "DECIMAL(10, 3) DEFAULT NULL COMMENT '最高价'"
        )
    else:
        logger.info("⚠️ 字段 high_price 已存在，跳过")
    
    # 添加 low_price 字段
    if not await check_column_exists("wencai_stocks", "low_price"):
        await add_column(
            "wencai_stocks",
            "low_price",
            "DECIMAL(10, 3) DEFAULT NULL COMMENT '最低价'"
        )
    else:
        logger.info("⚠️ 字段 low_price 已存在，跳过")
    
    # 添加 open_price 字段
    if not await check_column_exists("wencai_stocks", "open_price"):
        await add_column(
            "wencai_stocks",
            "open_price",
            "DECIMAL(10, 3) DEFAULT NULL COMMENT '开盘价'"
        )
    else:
        logger.info("⚠️ 字段 open_price 已存在，跳过")
    
    # 添加 prev_close 字段
    if not await check_column_exists("wencai_stocks", "prev_close"):
        await add_column(
            "wencai_stocks",
            "prev_close",
            "DECIMAL(10, 3) DEFAULT NULL COMMENT '昨收价'"
        )
    else:
        logger.info("⚠️ 字段 prev_close 已存在，跳过")
    
    # 添加 is_limit_up 字段
    if not await check_column_exists("wencai_stocks", "is_limit_up"):
        await add_column(
            "wencai_stocks",
            "is_limit_up",
            "TINYINT(1) DEFAULT 0 COMMENT '是否涨停'"
        )
    else:
        logger.info("⚠️ 字段 is_limit_up 已存在，跳过")
    
    # 添加 strategy_name 字段
    if not await check_column_exists("wencai_stocks", "strategy_name"):
        await add_column(
            "wencai_stocks",
            "strategy_name",
            "VARCHAR(50) DEFAULT NULL COMMENT '策略名称'"
        )
    else:
        logger.info("⚠️ 字段 strategy_name 已存在，跳过")
    
    # 创建索引
    await create_index("idx_wencai_source", "wencai_stocks", "source")
    await create_index("idx_wencai_change_percent", "wencai_stocks", "change_percent")
    await create_index("idx_wencai_volume_ratio", "wencai_stocks", "volume_ratio")


async def verify_migration():
    """验证迁移结果"""
    logger.info("\n🔍 验证迁移结果...")
    
    async with db_manager.get_session() as session:
        # 使用数据库配置中的数据库名
        from app.config.database import get_config
        config = get_config()
        database_name = config.database
        
        # 检查 wencai_crawl_batches 字段
        sql = """
        SELECT column_name FROM information_schema.columns 
        WHERE table_schema = :database_name
        AND table_name = 'wencai_crawl_batches'
        AND column_name IN ('source', 'sector_code', 'query_date')
        """
        result = await session.execute(text(sql), {"database_name": database_name})
        columns = [row[0] for row in result.all()]
        logger.info(f"wencai_crawl_batches 新增字段: {columns}")
        
        # 检查 wencai_stocks 字段
        sql = """
        SELECT column_name FROM information_schema.columns 
        WHERE table_schema = :database_name
        AND table_name = 'wencai_stocks'
        AND column_name IN ('source', 'change_percent', 'volume_ratio', 'turnover', 
                           'high_price', 'low_price', 'open_price', 'prev_close', 
                           'is_limit_up', 'strategy_name')
        """
        result = await session.execute(text(sql), {"database_name": database_name})
        columns = [row[0] for row in result.all()]
        logger.info(f"wencai_stocks 新增字段: {columns}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="问财表结构迁移脚本")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="仅验证迁移结果，不执行迁移"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("问财表结构迁移工具")
    logger.info("=" * 60)
    
    try:
        # 初始化数据库连接
        await db_manager.initialize()
        
        if args.verify_only:
            await verify_migration()
        else:
            # 执行迁移
            await migrate_wencai_batches()
            await migrate_wencai_stocks()
            await verify_migration()
            
            logger.info("\n" + "=" * 60)
            logger.info("✅ 迁移完成！")
            logger.info("=" * 60)
            
    except Exception as e:
        logger.error(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 关闭数据库连接
        await db_manager.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
