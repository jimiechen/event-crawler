"""
初始化MCP协作系统数据库
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_manager, init_database, close_database
from app.models.collaboration_log import Base


async def init_db():
    """初始化数据库表"""
    try:
        await init_database()
        print('数据库初始化完成')
    except Exception as e:
        print(f'数据库初始化失败: {e}')
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_db())