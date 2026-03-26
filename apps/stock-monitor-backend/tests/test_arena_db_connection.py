import asyncio
import asyncpg
import sys

# Connection details from settings.py
# default="postgresql+asyncpg://chroma_user:chroma_password@192.168.1.6:5432/chroma_db"
DB_CONFIG = {
    "user": "chroma_user",
    "password": "chroma_password",
    "database": "chroma_db",
    "host": "192.168.1.6",
    "port": 5432,
}

async def test_connection():
    print(f"Testing connection to {DB_CONFIG['host']}:{DB_CONFIG['port']} / {DB_CONFIG['database']}...")
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        print("Successfully connected!")
        
        # Test 1: Simple query
        version = await conn.fetchval("SELECT version()")
        print(f"Database version: {version}")
        
        # Test 2: Check for prompt_templates table
        print("Checking for 'prompt_templates' table...")
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'prompt_templates'
            );
        """)
        
        if table_exists:
            print("Table 'prompt_templates' found. This looks like the correct Arena database.")
            # Optional: Count rows
            count = await conn.fetchval("SELECT count(*) FROM prompt_templates")
            print(f"Row count in prompt_templates: {count}")
        else:
            print("WARNING: Table 'prompt_templates' NOT found. Is this the initialized Arena database?")
            
        await conn.close()
        print("Connection closed.")
        return True
        
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    if not success:
        sys.exit(1)
