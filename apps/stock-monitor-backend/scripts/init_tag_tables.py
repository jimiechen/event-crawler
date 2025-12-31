#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化标签管理系统数据库表
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils.database_pool import DatabasePool
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
                # 忽略表已存在的错误
                if "already exists" in str(e):
                    print(f"[{i}/{total_count}] 表已存在: {statement[:50]}...")
                    success_count += 1
                else:
                    print(f"[{i}/{total_count}] 执行失败: {statement[:50]}... 错误: {e}")
        
        await db_pool.close()
        
        print(f"\n执行完成: {success_count}/{total_count} 条语句成功")
        return success_count > 0
        
    except Exception as e:
        print(f"执行SQL语句失败: {e}")
        return False

async def main():
    print("开始初始化标签管理系统数据库表...")
    
    sql_file = project_root / "sql" / "tag_management.sql"
    
    if not sql_file.exists():
        print(f"SQL文件不存在: {sql_file}")
        return
    
    sql_content = await read_sql_file(str(sql_file))
    if not sql_content:
        print("SQL文件内容为空")
        return
    
    success = await execute_sql_statements(sql_content)
    
    if success:
        print("标签管理系统数据库表初始化完成！")
    else:
        print("标签管理系统数据库表初始化失败！")

if __name__ == "__main__":
    asyncio.run(main())
