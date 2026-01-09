import asyncio
from app.database import db_manager
from sqlalchemy import text

async def check():
    async with db_manager.get_session() as session:
        # Check 92xxxx
        try:
            res_92 = await session.execute(text("SELECT count(*) FROM stock_pool WHERE code LIKE '92%'"))
            count_92 = res_92.scalar()
            print(f'Count 92xxxx in stock_pool: {count_92}')
        except Exception as e:
            print(f"Could not query stock_pool: {e}")
        
        # Check 603601 in stock_pool/wencai
        result = await session.execute(text("SELECT count(*) FROM monitor_list WHERE code = '603601'"))
        count_monitor = result.scalar()
        print(f"603601 in monitor_list: {count_monitor}")

        result = await session.execute(text("SELECT count(*) FROM wencai_stocks WHERE stock_code = '603601'"))
        count_wencai = result.scalar()
        print(f"603601 in wencai_stocks: {count_wencai}")

        # Check 603601 scores for target range
        result = await session.execute(text("SELECT trade_date, total_score, rule_scores FROM stock_score_result WHERE code = '603601' AND trade_date BETWEEN '2025-11-20' AND '2025-12-10' ORDER BY trade_date DESC"))
        rows = result.fetchall()
        print(f"603601 scores (2025-11-20 to 2025-12-10):")
        for row in rows:
            print(row)

    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(check())
