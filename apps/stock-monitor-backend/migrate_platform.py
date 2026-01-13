#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本
执行平台配置和会话管理表的创建
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.database import db_manager
from loguru import logger


async def migrate_platform_tables():
    """执行平台表迁移"""
    try:
        # 初始化数据库
        await db_manager.initialize()
        
        # 读取SQL脚本
        sql_file = Path(__file__).parent / "sql" / "platform_tables.sql"
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 执行SQL
        async with db_manager.get_session() as session:
            from sqlalchemy import text
            
            # 分割SQL语句
            statements = []
            current_statement = []
            in_comment = False
            
            for line in sql_content.split('\n'):
                line = line.strip()
                
                # 跳过注释行
                if line.startswith('--'):
                    continue
                
                # 跳过空行
                if not line:
                    continue
                
                # 跳过USE语句
                if line.upper().startswith('USE '):
                    continue
                
                # 跳过COMMIT语句
                if line.upper() == 'COMMIT;':
                    continue
                
                current_statement.append(line)
                
                # 检查语句结束
                if line.endswith(';'):
                    statement = ' '.join(current_statement)
                    if statement:
                        statements.append(statement)
                    current_statement = []
            
            # 执行每个语句
            for stmt in statements:
                try:
                    await session.execute(text(stmt))
                    logger.info(f"执行成功: {stmt[:50]}...")
                except Exception as e:
                    # 忽略表已存在的错误
                    if "already exists" in str(e).lower():
                        logger.info(f"表已存在，跳过: {stmt[:50]}...")
                    else:
                        logger.error(f"执行失败: {stmt[:50]}... 错误: {e}")
                        raise
            
            await session.commit()
        
        logger.info("平台表迁移完成")
        return True
        
    except Exception as e:
        logger.error(f"平台表迁移失败: {e}")
        return False
    finally:
        await db_manager.close()


if __name__ == "__main__":
    success = asyncio.run(migrate_platform_tables())
    sys.exit(0 if success else 1)
