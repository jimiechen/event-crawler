#!/usr/bin/env python3
"""
测试修复检查逻辑
"""
import os
import sys
sys.path.insert(0, '/Users/mac/StudioProjects/2026/open-citycloud-workspace/python/event-crawler/apps/stock-monitor-backend')

def check_match_files(match_id: str, date: str = "2026-02-03"):
    """模拟修复检查逻辑"""
    base_dir = f"/Users/mac/StudioProjects/2026/open-citycloud-workspace/python/event-crawler/apps/stock-monitor-backend/data/okooo/matches/{date}"
    match_dir = os.path.join(base_dir, match_id)
    
    if not os.path.exists(match_dir):
        return {"exists": False, "missing": []}
    
    files = os.listdir(match_dir)
    html_files = [f for f in files if f.endswith('.html')]
    
    print(f"\n比赛 {match_id} 的文件:")
    for f in sorted(html_files):
        size = os.path.getsize(os.path.join(match_dir, f))
        print(f"  - {f} ({size} bytes)")
    
    # 模拟 expected_checks
    expected_checks = {
        "history": {"name": "澳客历史", "prefixes": ["history_"]},
        "odds": {"name": "澳客欧赔", "prefixes": ["odds_"]},
        "handicap": {"name": "澳客亚盘", "prefixes": ["handicap_"]},
        "exchanges": {"name": "澳客盈亏", "prefixes": ["exchanges_"]},
        "form": {"name": "澳客阵容", "prefixes": ["form_"]},
        "game": {"name": "澳客积分", "prefixes": ["game_", "table_"]},
        "macao_change": {"name": "澳客澳门亚盘变化", "prefixes": ["macao_change_", "odds_change_"]},
        "bifa_change": {"name": "澳客必发指数变化", "prefixes": ["bifa_change_", "odds_change_"]}
    }
    
    missing = []
    found = []
    
    for key, check in expected_checks.items():
        name = check["name"]
        prefixes = check["prefixes"]
        
        matching_files = [f for f in html_files if any(f.startswith(p) for p in prefixes)]
        
        # Special handling for handicap
        if key == "handicap":
            matching_files = [f for f in matching_files if not f.startswith("handicap-change")]
        
        if not matching_files:
            missing.append(name)
        else:
            found.append(f"{name}: {matching_files}")
    
    return {
        "exists": True,
        "found": found,
        "missing": missing,
        "total_files": len(html_files)
    }

def main():
    # 测试完整数据的比赛
    print("="*60)
    print("测试完整数据的比赛: 1320777")
    print("="*60)
    result = check_match_files("1320777")
    print(f"\n找到: {len(result['found'])} 项")
    for item in result['found']:
        print(f"  ✓ {item}")
    if result['missing']:
        print(f"\n缺失: {len(result['missing'])} 项")
        for item in result['missing']:
            print(f"  ✗ {item}")
    else:
        print("\n✓ 无缺失项")
    
    # 测试不完整数据的比赛
    print("\n" + "="*60)
    print("测试不完整数据的比赛: 1320245")
    print("="*60)
    result = check_match_files("1320245")
    print(f"\n找到: {len(result['found'])} 项")
    for item in result['found']:
        print(f"  ✓ {item}")
    if result['missing']:
        print(f"\n缺失: {len(result['missing'])} 项")
        for item in result['missing']:
            print(f"  ✗ {item}")
    else:
        print("\n✓ 无缺失项")

if __name__ == "__main__":
    main()
