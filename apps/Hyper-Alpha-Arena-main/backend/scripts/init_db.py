import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def init_db():
    db_url = os.getenv(
        "ASHARE_DB_URL", 
        "mysql+aiomysql://stock_user:stock123456@localhost:3306/stock_monitor?charset=utf8mb4"
    )
    print(f"Connecting to database: {db_url}")
    
    engine = create_async_engine(db_url, echo=True)
    
    sql_file = os.path.join(os.path.dirname(__file__), "setup_ashare_db.sql")
    print(f"Reading SQL file: {sql_file}")
    
    with open(sql_file, "r") as f:
        sql_content = f.read()
        
    # Split by ; to get individual statements, filtering out empty ones
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
    
    async with engine.begin() as conn:
        for statement in statements:
            print(f"Executing: {statement[:50]}...")
            await conn.execute(text(statement))
            
    print("Database initialization completed successfully.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())
