import asyncio
import asyncpg
import sys

DB_CONFIG = {
    "user": "chroma_user",
    "password": "chroma_password",
    "database": "chroma_db",
    "host": "192.168.1.6",
    "port": 5432,
}

async def list_tables():
    print(f"Listing tables in {DB_CONFIG['database']}...")
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        rows = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        if not rows:
            print("No tables found in 'public' schema.")
        else:
            print("Tables found:")
            for row in rows:
                print(f" - {row['table_name']}")
            
        await conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_tables())
