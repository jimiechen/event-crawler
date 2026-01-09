
import pymysql
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
env_path = "/Users/mac/ok-mcp/app/stock-monitor-backend/.env"
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"Loaded .env from {env_path}")
else:
    print(f"Warning: .env not found at {env_path}")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_DATABASE = os.getenv("DB_DATABASE", "stock_monitor")

print(f"Connecting to database '{DB_DATABASE}' on {DB_HOST}:{DB_PORT} as {DB_USER}...")

try:
    connection = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_DATABASE,
        cursorclass=pymysql.cursors.DictCursor
    )
    print("✅ Connected successfully.")
    
    with connection.cursor() as cursor:
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'tonghuashun_stocks'")
        result = cursor.fetchone()
        if not result:
            print(f"❌ Table 'tonghuashun_stocks' not found in {DB_DATABASE}.")
            sys.exit(1)
        
        print("✅ Table 'tonghuashun_stocks' found.")
        
        # Verify columns
        cursor.execute("DESCRIBE tonghuashun_stocks")
        columns = [row['Field'] for row in cursor.fetchall()]
        # print(f"Columns: {columns}")
        
        required_cols = ['prev_close', 'open_price', 'high', 'low', 'current_price']
        for col in required_cols:
            if col not in columns:
                print(f"❌ Missing column: {col}")
                sys.exit(1)
                
        # Count rows
        cursor.execute("SELECT COUNT(*) as cnt FROM tonghuashun_stocks")
        count = cursor.fetchone()['cnt']
        print(f"📊 Total rows to process: {count}")
        
        if count == 0:
            print("No data to fix.")
            sys.exit(0)
            
        # Fetch data for update
        print("🔄 Fetching data...")
        cursor.execute("SELECT id, prev_close, open_price, high, low, current_price FROM tonghuashun_stocks")
        rows = cursor.fetchall()
        
        updates = []
        for row in rows:
            # Rotation Logic:
            # We assume current data is WRONG and shifted.
            # Wrong Mapping was:
            # 6 (prev_close) -> current_price
            # 7 (open_price) -> prev_close
            # 8 (high_price) -> open_price
            # 9 (low_price)  -> high_price
            # 10 (current)   -> low_price
            
            # So DB currently holds:
            # current_price = Real prev_close
            # prev_close    = Real open_price
            # open_price    = Real high_price
            # high          = Real low_price (was high_price)
            # low           = Real current_price (was low_price)
            
            # We want to put them back to correct columns:
            # New prev_close = Real prev_close = Old current_price
            # New open_price = Real open_price = Old prev_close
            # New high       = Real high       = Old open_price
            # New low        = Real low        = Old high
            # New current_price = Real current_price = Old low
            
            updates.append((
                row['current_price'], # prev_close
                row['prev_close'],    # open_price
                row['open_price'],    # high
                row['high'],          # low
                row['low'],           # current_price
                row['id']
            ))
            
        print(f"📝 Prepared {len(updates)} updates. Executing...")
        
        # Batch update
        batch_size = 1000
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i+batch_size]
            cursor.executemany("""
                UPDATE tonghuashun_stocks 
                SET prev_close=%s, open_price=%s, high=%s, low=%s, current_price=%s 
                WHERE id=%s
            """, batch)
            connection.commit()
            print(f"   Processed {min(i+batch_size, len(updates))}/{len(updates)} rows...")
            
        print("✅ Data repair complete!")
        
        # Verify one row (Optional, hard to verify without knowing ground truth, but structure is fixed)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'connection' in locals() and connection.open:
        connection.close()
