#!/usr/bin/env python3
"""
解析指定日期的所有比赛数据
"""
import os
import sys
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.parse_okooo_mobile import OkoooParser

DATA_DIR = "/Users/mac/StudioProjects/2026/open-citycloud-workspace/python/event-crawler/apps/stock-monitor-backend/data/okooo/matches"
OUTPUT_DIR = "/Users/mac/StudioProjects/2026/open-citycloud-workspace/python/event-crawler/apps/stock-monitor-backend/data/okooo/processed"


def parse_date(date_str: str):
    """解析指定日期的所有比赛"""
    parser = OkoooParser(DATA_DIR, OUTPUT_DIR)
    date_path = os.path.join(DATA_DIR, date_str)

    if not os.path.exists(date_path):
        print(f"Directory not found: {date_path}")
        return

    match_dirs = [d for d in os.listdir(date_path) if os.path.isdir(os.path.join(date_path, d))]
    print(f"Found {len(match_dirs)} matches to parse for {date_str}")

    success_count = 0
    fail_count = 0

    for match_id in match_dirs:
        try:
            data = parser.process_date_match(date_str, match_id)
            parser.save_result(date_str, match_id, data)
            success_count += 1

            # 打印前几个的解析结果作为示例
            if success_count <= 3:
                print(f"\n  Match {match_id}:")
                print(f"    handicap: {len(data.get('handicap', []))} items")
                print(f"    bifaIndex: {len(data.get('bifaIndex', []))} items")
                print(f"    macaoIndex: {len(data.get('macaoIndex', []))} items")

            if success_count % 10 == 0:
                print(f"  Progress: {success_count}/{len(match_dirs)}")
        except Exception as e:
            fail_count += 1
            print(f"  Failed {match_id}: {e}")

    print(f"\nCompleted: {success_count} success, {fail_count} failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse Okooo match data for a specific date")
    parser.add_argument("date", help="Date in YYYY-MM-DD format")
    args = parser.parse_args()

    parse_date(args.date)
