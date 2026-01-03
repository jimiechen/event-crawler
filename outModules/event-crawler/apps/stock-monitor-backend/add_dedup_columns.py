
import asyncio
from sqlalchemy import text
from app.database import db_manager

async def add_dedup_columns():
    print("Starting database schema update for wencai_data_dedup...")
    try:
        await db_manager.initialize()
        
        async with db_manager.session_factory() as session:
            print("Checking columns in wencai_data_dedup...")
            
            # Helper function to check and add column
            async def check_and_add_column(column_name, column_type):
                try:
                    await session.execute(text(f"SELECT {column_name} FROM wencai_data_dedup LIMIT 1"))
                    print(f"Column '{column_name}' already exists.")
                except Exception:
                    print(f"Column '{column_name}' does not exist. Adding it...")
                    await session.execute(text(f"ALTER TABLE wencai_data_dedup ADD COLUMN {column_name} {column_type}"))
                    await session.commit()
                    print(f"Column '{column_name}' added successfully.")

            await check_and_add_column("stock_name", "VARCHAR(100) COMMENT '股票名称'")
            await check_and_add_column("current_price", "DECIMAL(10, 2) COMMENT '最新价'")
            await check_and_add_column("change_percent", "DECIMAL(10, 2) COMMENT '涨跌幅'")
            
            print("Schema update completed.")
            
    except Exception as e:
        print(f"Error during schema update: {e}")

if __name__ == "__main__":
    asyncio.run(add_dedup_columns())
