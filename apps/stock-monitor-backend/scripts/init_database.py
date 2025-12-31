#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
用于创建数据库表结构和初始化数据
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils.database_pool import DatabasePool, init_database, close_database
from app.config.database import DatabaseConfig

async def read_sql_file(file_path: str) -> str:
    """读取SQL文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取SQL文件失败 {file_path}: {e}")
        return ""

async def execute_sql_statements(sql_content: str) -> bool:
    """执行SQL语句"""
    try:
        # 分割SQL语句（以分号分隔）
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        db_pool = DatabasePool(DatabaseConfig())
        await db_pool.initialize()
        
        success_count = 0
        total_count = len(statements)
        
        for i, statement in enumerate(statements, 1):
            try:
                await db_pool.execute_update(statement)
                print(f"[{i}/{total_count}] 执行成功: {statement[:50]}...")
                success_count += 1
            except Exception as e:
                print(f"[{i}/{total_count}] 执行失败: {statement[:50]}... 错误: {e}")
        
        await db_pool.close()
        
        print(f"\n执行完成: {success_count}/{total_count} 条语句成功")
        return success_count > 0
        
    except Exception as e:
        print(f"执行SQL语句失败: {e}")
        return False

async def init_database_tables():
    """初始化数据库表结构"""
    print("开始初始化数据库表结构...")
    
    # SQL文件路径
    sql_file = project_root / "sql" / "create_tables.sql"
    
    if not sql_file.exists():
        print(f"SQL文件不存在: {sql_file}")
        return False
    
    # 读取SQL文件
    sql_content = await read_sql_file(str(sql_file))
    if not sql_content:
        print("SQL文件内容为空")
        return False
    
    # 执行SQL语句
    success = await execute_sql_statements(sql_content)
    
    if success:
        print("数据库表结构初始化完成！")
    else:
        print("数据库表结构初始化失败！")
    
    return success

async def check_database_connection():
    """检查数据库连接"""
    print("检查数据库连接...")
    
    try:
        db_pool = DatabasePool(DatabaseConfig())
        await db_pool.initialize()
        
        # 测试查询
        result = await db_pool.execute_one("SELECT 1 as test")
        
        await db_pool.close()
        
        if result and result.get('test') == 1:
            print("数据库连接正常")
            return True
        else:
            print("数据库连接测试失败")
            return False
            
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False

async def check_tables_exist():
    """检查表是否存在"""
    print("检查数据库表...")
    
    expected_tables = [
        'stock_info',
        'stock_data', 
        'monitor_list',
        'data_dedup_log',
        'system_config'
    ]
    
    try:
        db_pool = DatabasePool(DatabaseConfig())
        await db_pool.initialize()
        
        # 查询所有表
        tables = await db_pool.execute_query(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE()"
        )
        
        await db_pool.close()
        
        existing_tables = [table['table_name'] for table in tables]
        
        print(f"现有表: {existing_tables}")
        
        missing_tables = [table for table in expected_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"缺少表: {missing_tables}")
            return False
        else:
            print("所有必需的表都存在")
            return True
            
    except Exception as e:
        print(f"检查表失败: {e}")
        return False

async def main():
    """主函数"""
    print("=== 同花顺股票监控系统数据库初始化 ===")
    print(f"项目根目录: {project_root}")
    
    # 1. 检查数据库连接
    if not await check_database_connection():
        print("数据库连接失败，请检查配置")
        return
    
    # 2. 检查表是否已存在
    tables_exist = await check_tables_exist()
    
    if tables_exist:
        print("数据库表已存在，是否重新初始化？(y/N): ", end="")
        choice = input().strip().lower()
        if choice != 'y':
            print("跳过初始化")
            return
    
    # 3. 初始化数据库表
    success = await init_database_tables()
    
    if success:
        # 4. 再次检查表
        await check_tables_exist()
        print("\n数据库初始化完成！")
    else:
        print("\n数据库初始化失败！")

if __name__ == "__main__":
    asyncio.run(main())