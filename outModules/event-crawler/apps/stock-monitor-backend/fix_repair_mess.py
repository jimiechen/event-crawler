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
        # Fetch data for update
        print("🔄 Fetching data...")
        cursor.execute("SELECT id, open_price, high, low, current_price FROM tonghuashun_stocks")
        rows = cursor.fetchall()
        print(f"Found {len(rows)} rows to process.")
        
        updates = []
        for row in rows:
            # Current State (Broken):
            # open_price    = Real Current
            # high          = Real Open
            # low           = Real High
            # current_price = Real Low
            
            # Wait, let's re-verify the mapping from thought process:
            # My previous broken script did:
            # row['prev_close'] (Old Open) -> open_price. So Current Open = Real Open?
            # NO.
            # Old Mapping (Hypothesis): Swap 6(Prev) and 10(Curr). 7,8,9 Correct.
            # DB Before: Prev=RealCurr, Open=RealOpen, High=RealHigh, Low=RealLow, Curr=RealPrev.
            
            # My Broken Script:
            # Updates:
            # prev_close = Old current (RealPrev) -> Correct.
            # open_price = Old prev_close (RealCurr) -> So Current Open holds Real Current.
            # high       = Old open_price (RealOpen) -> So Current High holds Real Open.
            # low        = Old high (RealHigh) -> So Current Low holds Real High.
            # current    = Old low (RealLow) -> So Current Curr holds Real Low.
            
            # So:
            # Current Open = Real Current
            # Current High = Real Open
            # Current Low = Real High
            # Current Curr = Real Low
            
            # We want:
            # New Open = Real Open = Current High
            # New High = Real High = Current Low
            # New Low = Real Low = Current Curr
            # New Curr = Real Current = Current Open
            
            updates.append((
                row['high'],          # New Open = Old High
                row['low'],           # New High = Old Low
                row['current_price'], # New Low = Old Current
                row['open_price'],    # New Curr = Old Open
                row['id']
            ))
            
        print(f"📝 Prepared {len(updates)} updates. Executing...")
        
        # Batch update
        batch_size = 1000
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i+batch_size]
            cursor.executemany("""
                UPDATE tonghuashun_stocks 
                SET open_price=%s, high=%s, low=%s, current_price=%s 
                WHERE id=%s
            """, batch)
            connection.commit()
            print(f"   Processed {min(i+batch_size, len(updates))}/{len(updates)} rows...")
            
        print("✅ Data repair complete!")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
finally:
    if 'connection' in locals() and connection.open:
        connection.close()
