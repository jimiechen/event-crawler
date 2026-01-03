#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问财数据表初始化脚本
用于创建问财相关的数据库表结构
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils.database_pool import DatabasePool
from app.config.database import DatabaseConfig

async def create_wencai_tables():
    """创建问财数据表"""
    print("开始创建问财数据表...")
    
    # 问财股票数据表
    create_wencai_stocks_sql = """
    CREATE TABLE IF NOT EXISTS wencai_stocks (
        id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
        stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
        stock_name VARCHAR(100) NOT NULL COMMENT '股票名称',
        current_price DECIMAL(10,3) DEFAULT NULL COMMENT '现价',
        price_change DECIMAL(10,3) DEFAULT NULL COMMENT '涨跌额',
        price_change_percent DECIMAL(8,3) DEFAULT NULL COMMENT '涨跌幅(%)',
        volume BIGINT DEFAULT NULL COMMENT '成交量',
        turnover DECIMAL(15,2) DEFAULT NULL COMMENT '成交额',
        amplitude DECIMAL(8,3) DEFAULT NULL COMMENT '振幅(%)',
        highest_price DECIMAL(10,3) DEFAULT NULL COMMENT '最高价',
        lowest_price DECIMAL(10,3) DEFAULT NULL COMMENT '最低价',
        opening_price DECIMAL(10,3) DEFAULT NULL COMMENT '今开',
        previous_close DECIMAL(10,3) DEFAULT NULL COMMENT '昨收',
        volume_ratio DECIMAL(8,3) DEFAULT NULL COMMENT '量比',
        turnover_rate DECIMAL(8,3) DEFAULT NULL COMMENT '换手率(%)',
        pe_ratio DECIMAL(10,3) DEFAULT NULL COMMENT '市盈率(动态)',
        pb_ratio DECIMAL(10,3) DEFAULT NULL COMMENT '市净率',
        total_market_value DECIMAL(20,2) DEFAULT NULL COMMENT '总市值',
        circulating_market_value DECIMAL(20,2) DEFAULT NULL COMMENT '流通市值',
        speed_60_days DECIMAL(8,3) DEFAULT NULL COMMENT '60日涨跌幅(%)',
        speed_year_to_date DECIMAL(8,3) DEFAULT NULL COMMENT '年初至今涨跌幅(%)',
        company_address TEXT DEFAULT NULL COMMENT '公司地址',
        business_scope TEXT DEFAULT NULL COMMENT '经营范围',
        crawl_batch_id BIGINT NOT NULL COMMENT '抓取批次ID',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        
        INDEX idx_stock_code (stock_code),
        INDEX idx_crawl_batch (crawl_batch_id),
        INDEX idx_created_at (created_at),
        UNIQUE KEY uk_stock_batch (stock_code, crawl_batch_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问财股票数据表';
    """
    
    # 问财抓取批次表
    create_wencai_batches_sql = """
    CREATE TABLE IF NOT EXISTS wencai_crawl_batches (
        id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '批次ID',
        batch_name VARCHAR(200) NOT NULL COMMENT '批次名称',
        crawl_url TEXT DEFAULT NULL COMMENT '抓取URL',
        total_records INT DEFAULT 0 COMMENT '总记录数',
        success_records INT DEFAULT 0 COMMENT '成功记录数',
        failed_records INT DEFAULT 0 COMMENT '失败记录数',
        status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending' COMMENT '状态',
        error_message TEXT DEFAULT NULL COMMENT '错误信息',
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
        completed_at TIMESTAMP NULL DEFAULT NULL COMMENT '完成时间',
        created_by VARCHAR(100) DEFAULT 'system' COMMENT '创建者',
        
        INDEX idx_status (status),
        INDEX idx_started_at (started_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问财抓取批次表';
    """
    
    # 问财数据去重表
    create_wencai_dedup_sql = """
    CREATE TABLE IF NOT EXISTS wencai_data_dedup (
        id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
        stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
        data_hash VARCHAR(64) NOT NULL COMMENT '数据哈希值',
        crawl_batch_id BIGINT NOT NULL COMMENT '抓取批次ID',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        
        UNIQUE KEY uk_stock_hash (stock_code, data_hash),
        INDEX idx_crawl_batch (crawl_batch_id),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问财数据去重表';
    """
    
    # 最新问财股票数据视图
    create_latest_view_sql = """
    CREATE OR REPLACE VIEW v_latest_wencai_stocks AS
    SELECT 
        ws.*,
        wcb.batch_name,
        wcb.started_at as batch_time
    FROM wencai_stocks ws
    INNER JOIN (
        SELECT stock_code, MAX(crawl_batch_id) as latest_batch_id
        FROM wencai_stocks
        GROUP BY stock_code
    ) latest ON ws.stock_code = latest.stock_code AND ws.crawl_batch_id = latest.latest_batch_id
    INNER JOIN wencai_crawl_batches wcb ON ws.crawl_batch_id = wcb.id
    WHERE wcb.status = 'completed';
    """
    
    # 问财抓取统计视图
    create_stats_view_sql = """
    CREATE OR REPLACE VIEW v_wencai_crawl_stats AS
    SELECT 
        DATE(started_at) as crawl_date,
        COUNT(*) as total_batches,
        SUM(total_records) as total_records,
        SUM(success_records) as total_success,
        SUM(failed_records) as total_failed,
        AVG(success_records * 100.0 / NULLIF(total_records, 0)) as avg_success_rate
    FROM wencai_crawl_batches
    WHERE status = 'completed'
    GROUP BY DATE(started_at)
    ORDER BY crawl_date DESC;
    """
    
    # 系统配置插入
    insert_config_sql = """
    INSERT IGNORE INTO system_config (config_key, config_value, description, created_at) VALUES
    ('wencai_crawl_enabled', 'true', '问财数据抓取功能开关', NOW()),
    ('wencai_crawl_interval', '300', '问财数据抓取间隔(秒)', NOW()),
    ('wencai_data_retention_days', '90', '问财数据保留天数', NOW()),
    ('wencai_batch_size', '1000', '问财数据批处理大小', NOW());
    """
    
    try:
        db_pool = DatabasePool(DatabaseConfig())
        await db_pool.initialize()
        
        # 执行表创建
        print("1. 创建问财股票数据表...")
        await db_pool.execute_update(create_wencai_stocks_sql)
        print("   ✓ wencai_stocks 表创建成功")
        
        print("2. 创建问财抓取批次表...")
        await db_pool.execute_update(create_wencai_batches_sql)
        print("   ✓ wencai_crawl_batches 表创建成功")
        
        print("3. 创建问财数据去重表...")
        await db_pool.execute_update(create_wencai_dedup_sql)
        print("   ✓ wencai_data_dedup 表创建成功")
        
        print("4. 创建最新问财股票数据视图...")
        await db_pool.execute_update(create_latest_view_sql)
        print("   ✓ v_latest_wencai_stocks 视图创建成功")
        
        print("5. 创建问财抓取统计视图...")
        await db_pool.execute_update(create_stats_view_sql)
        print("   ✓ v_wencai_crawl_stats 视图创建成功")
        
        print("6. 插入系统配置...")
        await db_pool.execute_update(insert_config_sql)
        print("   ✓ 系统配置插入成功")
        
        await db_pool.close()
        
        print("\n✅ 问财数据表结构创建完成！")
        return True
        
    except Exception as e:
        print(f"❌ 创建问财数据表失败: {e}")
        return False

async def check_wencai_tables():
    """检查问财表是否存在"""
    print("\n检查问财数据表...")
    
    expected_tables = [
        'wencai_stocks',
        'wencai_crawl_batches', 
        'wencai_data_dedup'
    ]
    
    expected_views = [
        'v_latest_wencai_stocks',
        'v_wencai_crawl_stats'
    ]
    
    try:
        db_pool = DatabasePool(DatabaseConfig())
        await db_pool.initialize()
        
        # 检查表
        tables = await db_pool.execute_query(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE'"
        )
        existing_tables = [table['table_name'] for table in tables]
        
        # 检查视图
        views = await db_pool.execute_query(
            "SELECT table_name FROM information_schema.views WHERE table_schema = DATABASE()"
        )
        existing_views = [view['table_name'] for view in views]
        
        await db_pool.close()
        
        print(f"现有表: {existing_tables}")
        print(f"现有视图: {existing_views}")
        
        missing_tables = [table for table in expected_tables if table not in existing_tables]
        missing_views = [view for view in expected_views if view not in existing_views]
        
        if missing_tables:
            print(f"❌ 缺少表: {missing_tables}")
            return False
        
        if missing_views:
            print(f"❌ 缺少视图: {missing_views}")
            return False
        
        print("✅ 所有问财相关表和视图都存在")
        return True
        
    except Exception as e:
        print(f"❌ 检查表失败: {e}")
        return False

async def main():
    """主函数"""
    print("=== 问财数据表初始化 ===")
    
    # 检查表是否已存在
    tables_exist = await check_wencai_tables()
    
    if tables_exist:
        print("问财数据表已存在，是否重新创建？(y/N): ", end="")
        choice = input().strip().lower()
        if choice != 'y':
            print("跳过创建")
            return
    
    # 创建问财数据表
    success = await create_wencai_tables()
    
    if success:
        # 再次检查表
        await check_wencai_tables()
        print("\n🎉 问财数据表初始化完成！")
    else:
        print("\n💥 问财数据表初始化失败！")

if __name__ == "__main__":
    asyncio.run(main())