import requests
import time
import pymysql
import json

BASE_URL = "http://localhost:8000"

DB_CONFIG = {
    "host": "192.168.1.6",
    "user": "root",
    "password": "12345678",
    "database": "stock_monitor_new",
    "port": 3306,
    "cursorclass": pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

def test_sync_pool():
    print("\n[1] Testing Stock Pool Sync...")
    try:
        resp = requests.post(f"{BASE_URL}/api/tasks/sync/pool")
        print(f"Status: {resp.status_code}, Response: {resp.json()}")
        if resp.status_code == 200:
            print("Waiting 5s for sync...")
            time.sleep(5)
            # Check DB
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT count(*) as count FROM stock_pool")
                res = cursor.fetchone()
                print(f"Stock Pool Count: {res['count']}")
            conn.close()
    except Exception as e:
        print(f"Error: {e}")

def test_incremental_sync():
    print("\n[2] Testing Incremental Sync...")
    try:
        resp = requests.post(f"{BASE_URL}/api/tasks/sync/incremental")
        print(f"Status: {resp.status_code}, Response: {resp.json()}")
        # This is async, might take time.
        print("Waiting 10s (task running in background)...")
        time.sleep(10)
    except Exception as e:
        print(f"Error: {e}")

def test_calculate():
    print("\n[3] Testing Score Calculation...")
    try:
        resp = requests.post(f"{BASE_URL}/api/tasks/calculate")
        print(f"Status: {resp.status_code}, Response: {resp.json()}")
        print("Waiting 10s (calculation running in background)...")
        time.sleep(10)
    except Exception as e:
        print(f"Error: {e}")

def check_rankings_and_scores():
    print("\n[4] Checking Rankings and Scores for 600724.SH...")
    try:
        # Check Total Ranking API
        resp = requests.get(f"{BASE_URL}/api/v1/rankings/total?limit=10")
        if resp.status_code == 200:
            data = resp.json().get('data', [])
            print(f"Top 5 Total Rankings: {json.dumps(data[:5], ensure_ascii=False, indent=2)}")
        else:
            print(f"Failed to get rankings: {resp.status_code}")

        # Deep dive into DB for 600724.SH
        conn = get_db_connection()
        target_code = "600724.SH"
        with conn.cursor() as cursor:
            # 1. Stock Info Score
            cursor.execute("SELECT code, name, volume_anomaly_score, latest_price FROM stock_info WHERE code = %s", (target_code,))
            info = cursor.fetchone()
            print(f"\nStock Info for {target_code}: {info}")

            # 2. Stock Volume Baseline
            cursor.execute("SELECT * FROM stock_volume_baseline WHERE code = %s", (target_code,))
            baseline = cursor.fetchone()
            print(f"\nBaseline for {target_code}:")
            if baseline:
                for k, v in baseline.items():
                    if v is not None:
                        print(f"  {k}: {v}")
            else:
                print("  No baseline record found.")

            # 3. Score History Sum
            cursor.execute("SELECT sum(total_score) as total FROM stock_score_result WHERE code = %s", (target_code,))
            score_sum = cursor.fetchone()
            print(f"\nSum of daily scores for {target_code}: {score_sum['total']}")

            # 4. Recent Anomalies
            cursor.execute("SELECT trade_date, analysis_type, value, description FROM volume_analysis_result WHERE code = %s ORDER BY trade_date DESC LIMIT 5", (target_code,))
            anomalies = cursor.fetchall()
            print(f"\nRecent Anomalies for {target_code}:")
            for a in anomalies:
                print(f"  {a}")

        conn.close()

    except Exception as e:
        print(f"Error checking rankings: {e}")

if __name__ == "__main__":
    test_sync_pool()
    test_incremental_sync()
    test_calculate()
    check_rankings_and_scores()
