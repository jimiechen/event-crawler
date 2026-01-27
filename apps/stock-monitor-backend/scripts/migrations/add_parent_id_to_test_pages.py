import asyncio
import sys
import os
from sqlalchemy import text

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import db_manager

async def migrate():
    print("开始添加parent_id字段到test_pages表...")
    
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        # 添加 parent_id 字段
        try:
            await session.execute(text("ALTER TABLE test_pages ADD COLUMN parent_id INT NULL DEFAULT NULL COMMENT '父页面ID'"))
            print("已添加 parent_id 字段到 test_pages 表")
        except Exception as e:
            print(f"添加 parent_id 字段失败 (可能已存在): {e}")
            
        await session.commit()
        
    await db_manager.close()
    print("数据库迁移完成")

if __name__ == "__main__":
    asyncio.run(migrate())