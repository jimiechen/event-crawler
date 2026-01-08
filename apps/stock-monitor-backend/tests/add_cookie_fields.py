import asyncio
import sys
import os
from sqlalchemy import text

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import db_manager

async def migrate():
    print("开始添加字段到 chrome_cookies 表...")
    
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        # 添加 xpath_config 字段
        try:
            await session.execute(text("ALTER TABLE chrome_cookies ADD COLUMN xpath_config TEXT COMMENT '登录检查XPath配置'"))
            print("已添加 xpath_config 字段")
        except Exception as e:
            print(f"添加 xpath_config 字段失败 (可能已存在): {e}")
            
        # 添加 is_valid 字段
        try:
            await session.execute(text("ALTER TABLE chrome_cookies ADD COLUMN is_valid BOOLEAN DEFAULT TRUE COMMENT 'Cookie是否有效'"))
            print("已添加 is_valid 字段")
        except Exception as e:
            print(f"添加 is_valid 字段失败 (可能已存在): {e}")

        # 添加 account_name 字段
        try:
            await session.execute(text("ALTER TABLE chrome_cookies ADD COLUMN account_name VARCHAR(255) COMMENT '账号名称/备注'"))
            print("已添加 account_name 字段")
        except Exception as e:
            print(f"添加 account_name 字段失败 (可能已存在): {e}")

        # 添加 test_url 字段
        try:
            await session.execute(text("ALTER TABLE chrome_cookies ADD COLUMN test_url VARCHAR(500) COMMENT '测试URL'"))
            print("已添加 test_url 字段")
        except Exception as e:
            print(f"添加 test_url 字段失败 (可能已存在): {e}")

        # 添加 status 字段
        try:
            await session.execute(text("ALTER TABLE chrome_cookies ADD COLUMN status VARCHAR(50) DEFAULT 'unknown' COMMENT '状态'"))
            print("已添加 status 字段")
        except Exception as e:
            print(f"添加 status 字段失败 (可能已存在): {e}")

        # 添加 last_checked_at 字段
        try:
            await session.execute(text("ALTER TABLE chrome_cookies ADD COLUMN last_checked_at DATETIME COMMENT '最后检查时间'"))
            print("已添加 last_checked_at 字段")
        except Exception as e:
            print(f"添加 last_checked_at 字段失败 (可能已存在): {e}")
            
        await session.commit()
        
    await db_manager.close()
    print("数据库迁移完成")

if __name__ == "__main__":
    asyncio.run(migrate())
