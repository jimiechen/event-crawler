
import asyncio
from sqlalchemy import text
from app.database import db_manager

async def update_schema():
    async with db_manager.get_session() as session:
        # 1. Update wencai_crawl_batches
        try:
            await session.execute(text("ALTER TABLE wencai_crawl_batches ADD COLUMN query_date DATE COMMENT '查询日期'"))
            print("Added query_date to wencai_crawl_batches")
        except Exception as e:
            print(f"wencai_crawl_batches update failed (might already exist): {e}")

        # 2. Update wencai_data_dedup
        try:
            await session.execute(text("ALTER TABLE wencai_data_dedup ADD COLUMN stock_name VARCHAR(100) COMMENT '股票名称'"))
            print("Added stock_name to wencai_data_dedup")
        except Exception as e:
            print(f"wencai_data_dedup stock_name failed: {e}")
            
        try:
            await session.execute(text("ALTER TABLE wencai_data_dedup ADD COLUMN current_price DECIMAL(10,3) COMMENT '当前价格'"))
            print("Added current_price to wencai_data_dedup")
        except Exception as e:
            print(f"wencai_data_dedup current_price failed: {e}")

        try:
            await session.execute(text("ALTER TABLE wencai_data_dedup ADD COLUMN change_percent DECIMAL(8,3) COMMENT '涨跌幅(%)'"))
            print("Added change_percent to wencai_data_dedup")
        except Exception as e:
            print(f"wencai_data_dedup change_percent failed: {e}")

        await session.commit()

if __name__ == "__main__":
    asyncio.run(update_schema())
