#!/usr/bin/env python3
"""
检查用户指定的比赛ID列表的文件完整性
"""
import os
import sys
import json

sys.path.insert(0, '/Users/mac/StudioProjects/2026/open-citycloud-workspace/python/event-crawler/apps/stock-monitor-backend')

# 用户提供的比赛ID列表
match_ids = [
    "1314253", "1314256", "1314258", "1314259", "1314263", "1314264", "1314265", "1314266",
    "1315661", "1316063", "1316064", "1317416", "1317455", "1317782", "1319515",
    "1320212", "1320215", "1320216", "1320217", "1320218", "1320219", "1320220", "1320221",
    "1320234", "1320245", "1320246", "1320767", "1320769", "1320777", "1320780", "1321067"
]

def check_match_files(match_id: str, date: str = "2026-02-03"):
    """检查单个比赛的文件完整性"""
    base_dir = f"/Users/mac/StudioProjects/2026/open-citycloud-workspace/python/event-crawler/apps/stock-monitor-backend/data/okooo/matches/{date}"
    match_dir = os.path.join(base_dir, match_id)
    
    if not os.path.exists(match_dir):
        return {
            'match_id': match_id,
            'exists': False,
            'files': {}
        }
    
    # 定义标准文件类型
    expected_files = {
        'history': f'history_{match_id}.html',
        'odds': f'odds_{match_id}.html',
        'handicap': f'handicap_{match_id}.html',
        'exchanges': f'exchanges_{match_id}.html',
        'form': f'form_{match_id}.html',
        'game': f'game_{match_id}.html',
        'bifa_change': f'bifa_change_{match_id}.html',
        'odds_change': f'odds_change_{match_id}.html',
        'table': f'table_{match_id}.html'
    }
    
    files_status = {}
    existing_count = 0
    
    for page_type, filename in expected_files.items():
        file_path = os.path.join(match_dir, filename)
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            files_status[page_type] = {
                'exists': True,
                'size': file_size
            }
            existing_count += 1
        else:
            files_status[page_type] = {'exists': False}
    
    return {
        'match_id': match_id,
        'exists': True,
        'total_files': len(expected_files),
        'existing_files': existing_count,
        'missing_files': len(expected_files) - existing_count,
        'files': files_status
    }

def main():
    date = "2026-02-03"
    
    print(f"检查 {len(match_ids)} 个比赛的文件完整性")
    print(f"{'='*80}\n")
    
    results = []
    complete_matches = []
    incomplete_matches = []
    missing_matches = []
    
    for match_id in match_ids:
        result = check_match_files(match_id, date)
        results.append(result)
        
        if not result['exists']:
            missing_matches.append(match_id)
        elif result['missing_files'] == 0:
            complete_matches.append(match_id)
        else:
            incomplete_matches.append({
                'match_id': match_id,
                'missing': result['missing_files'],
                'existing': result['existing_files']
            })
    
    # 打印结果
    print(f"统计结果:")
    print(f"  完整数据 (9/9文件): {len(complete_matches)} 场")
    print(f"  部分数据: {len(incomplete_matches)} 场")
    print(f"  数据缺失 (无文件夹): {len(missing_matches)} 场")
    print()
    
    if complete_matches:
        print(f"完整数据的比赛 ({len(complete_matches)} 场):")
        for mid in complete_matches:
            print(f"  ✓ {mid}")
        print()
    
    if incomplete_matches:
        print(f"部分数据的比赛 ({len(incomplete_matches)} 场):")
        for item in incomplete_matches:
            mid = item['match_id']
            missing = item['missing']
            existing = item['existing']
            print(f"  ⚠ {mid}: {existing}/9 文件 (缺失 {missing} 个)")
            
            # 显示具体缺失的文件
            result = next(r for r in results if r['match_id'] == mid)
            missing_types = [k for k, v in result['files'].items() if not v.get('exists')]
            print(f"     缺失: {', '.join(missing_types)}")
        print()
    
    if missing_matches:
        print(f"数据缺失的比赛 ({len(missing_matches)} 场):")
        for mid in missing_matches:
            print(f"  ✗ {mid}: 无数据文件夹")
        print()
    
    # 保存详细结果
    output_file = f"/Users/mac/StudioProjects/2026/open-citycloud-workspace/python/event-crawler/apps/stock-monitor-backend/data/okooo/match_check_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'date': date,
            'summary': {
                'total': len(match_ids),
                'complete': len(complete_matches),
                'incomplete': len(incomplete_matches),
                'missing': len(missing_matches)
            },
            'complete_matches': complete_matches,
            'incomplete_matches': incomplete_matches,
            'missing_matches': missing_matches,
            'details': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"详细结果已保存到: {output_file}")

if __name__ == "__main__":
    main()
