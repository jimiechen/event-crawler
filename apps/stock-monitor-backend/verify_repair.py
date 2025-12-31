import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
env_path = "/Users/mac/ok-mcp/app/stock-monitor-backend/.env"
load_dotenv(env_path)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_DATABASE = os.getenv("DB_DATABASE", "stock_monitor")

def verify_data():
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE,
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # Check for invalid High < Low
            cursor.execute("SELECT count(*) as cnt FROM tonghuashun_stocks WHERE high < low")
            result = cursor.fetchone()
            invalid_cnt = result['cnt']
            
            cursor.execute("SELECT count(*) as cnt FROM tonghuashun_stocks")
            total = cursor.fetchone()['cnt']
            
            print(f"Total rows: {total}")
            print(f"Rows with High < Low: {invalid_cnt}")
            
            if invalid_cnt == 0:
                print("✅ Data consistency check passed (High >= Low for all rows).")
            else:
                print("❌ Data consistency check failed!")
                
            # Sample INVALID data
            cursor.execute("SELECT code, prev_close, open_price, high, low, current_price, change_percent FROM tonghuashun_stocks WHERE high < low LIMIT 5")
            rows = cursor.fetchall()
            print("\nSample INVALID Data (High < Low):")
            for row in rows:
                print(f"Code: {row['code']}")
                print(f"  Prev: {row['prev_close']}")
                print(f"  Open: {row['open_price']}")
                print(f"  High: {row['high']}")
                print(f"  Low:  {row['low']}")
                print(f"  Curr: {row['current_price']}")
                print(f"  Chg%: {row['change_percent']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

if __name__ == "__main__":
    verify_data()
