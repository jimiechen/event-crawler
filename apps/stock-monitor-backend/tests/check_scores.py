import pymysql
import os
import csv

DB_CONFIG = {
    "host": "192.168.1.6",
    "user": "root",
    "password": "12345678",
    "database": "stock_monitor_new",
    "port": 3306,
    "cursorclass": pymysql.cursors.DictCursor
}

def check_data_integrity():
    conn = pymysql.connect(**DB_CONFIG)
    target_code = "600724.SH"
    try:
        with conn.cursor() as cursor:
            # Check the single score result
            cursor.execute("SELECT * FROM stock_score_result WHERE code = %s", (target_code,))
            scores = cursor.fetchall()
            print(f"\nStockScoreResult records ({len(scores)}):")
            for s in scores:
                print(s)
            
    finally:
        conn.close()

    # Check stock_basic.csv for the code
    basic_csv = "/Users/mac/ok-mcp/history/stock_basic/stock_basic.csv"
    print(f"\nChecking {basic_csv} for 600724...")
    found = False
    try:
        with open(basic_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if '600724' in row['股票代码']:
                    print(f"Found in CSV: {row}")
                    found = True
                    break
    except Exception as e:
        print(f"Error reading CSV: {e}")
    
    if not found:
        print("600724 NOT found in stock_basic.csv")

if __name__ == "__main__":
    check_data_integrity()
