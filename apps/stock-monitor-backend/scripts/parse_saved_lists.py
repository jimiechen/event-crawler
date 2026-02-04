#!/usr/bin/env python3
"""
解析已保存的比赛列表 HTML 文件
"""
import os
import sys
import glob

# Add project root to path
sys.path.insert(0, '/Users/mac/StudioProjects/2026/open-citycloud-workspace/python/event-crawler/apps/stock-monitor-backend')

from app.crawler.okooo.parser import OkoooParser

def parse_list_html(file_path: str):
    """解析单个列表 HTML 文件"""
    print(f"\n{'='*60}")
    print(f"解析文件: {file_path}")
    print(f"{'='*60}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 解析比赛列表
    matches = OkoooParser.parse_mobile_match_list(html)
    
    print(f"\n找到 {len(matches)} 场比赛:\n")
    
    for i, match in enumerate(matches, 1):
        print(f"{i}. ID: {match.get('match_id', 'N/A')}")
        print(f"   联赛: {match.get('league', 'N/A')}")
        print(f"   时间: {match.get('match_time', 'N/A')}")
        print(f"   主队: {match.get('home_team', 'N/A')}")
        print(f"   客队: {match.get('away_team', 'N/A')}")
        print(f"   状态: {match.get('status', 'N/A')}")
        print()
    
    return matches

def main():
    date = "2026-02-03"
    list_dir = f"/Users/mac/StudioProjects/2026/open-citycloud-workspace/python/event-crawler/apps/stock-monitor-backend/data/okooo/list/{date}"
    
    if not os.path.exists(list_dir):
        print(f"目录不存在: {list_dir}")
        return
    
    # 获取所有 HTML 文件
    html_files = sorted(glob.glob(os.path.join(list_dir, "*.html")))
    
    if not html_files:
        print(f"没有找到 HTML 文件: {list_dir}")
        return
    
    print(f"找到 {len(html_files)} 个 HTML 文件")
    
    # 解析最新的文件
    latest_file = html_files[-1]
    matches = parse_list_html(latest_file)
    
    print(f"\n{'='*60}")
    print(f"总计: {len(matches)} 场比赛")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
