import asyncio
from sqlalchemy import text
from app.database import db_manager

async def fix_market_bj():
    await db_manager.initialize()
    async with db_manager.get_session() as session:
        print("=== 修复北交所(920开头)市场字段 ===")
        
        # 查找所有920开头且market为unknown的股票
        stmt = text("""
            SELECT id, code, name 
            FROM stock_info 
            WHERE code LIKE '920%' AND market = 'unknown'
        """)
        result = await session.execute(stmt)
        stocks = result.fetchall()
        
        print(f"找到 {len(stocks)} 个待修复的北交所股票")
        
        if not stocks:
            return

        # 更新
        update_stmt = text("""
            UPDATE stock_info 
            SET market = 'BJ' 
            WHERE code LIKE '920%' AND market = 'unknown'
        """)
        await session.execute(update_stmt)
        await session.commit()
        
        print("修复完成")

if __name__ == "__main__":
    asyncio.run(fix_market_bj())
