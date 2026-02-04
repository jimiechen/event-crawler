#!/usr/bin/env python3
"""
解析指定日期目录下的所有比赛数据
"""
import os
import sys
import glob
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, '/Users/mac/StudioProjects/2026/open-citycloud-workspace/python/event-crawler/apps/stock-monitor-backend')

from app.crawler.okooo.parser import OkoooParser

def parse_match_data(match_dir: str, match_id: str):
    """解析单个比赛的所有页面数据"""
    result = {
        'match_id': match_id,
        'files': {},
        'parsed_data': {}
    }
    
    # 定义要解析的文件类型
    file_types = {
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
    
    for page_type, filename in file_types.items():
        file_path = os.path.join(match_dir, filename)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    html = f.read()
                
                file_size = os.path.getsize(file_path)
                result['files'][page_type] = {
                    'exists': True,
                    'size': file_size,
                    'parsed': False
                }
                
                # 尝试解析特定页面类型
                # 这里可以根据不同页面类型调用不同的解析方法
                # 目前只记录文件存在和大小
                
            except Exception as e:
                result['files'][page_type] = {
                    'exists': True,
                    'error': str(e)
                }
        else:
            result['files'][page_type] = {'exists': False}
    
    return result

def main():
    date = "2026-02-03"
    base_dir = f"/Users/mac/StudioProjects/2026/open-citycloud-workspace/python/event-crawler/apps/stock-monitor-backend/data/okooo/matches/{date}"
    
    if not os.path.exists(base_dir):
        print(f"目录不存在: {base_dir}")
        return
    
    # 获取所有比赛文件夹
    match_dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    match_dirs.sort()
    
    print(f"找到 {len(match_dirs)} 个比赛文件夹")
    print(f"\n{'='*80}")
    
    # 统计信息
    stats = {
        'total_matches': len(match_dirs),
        'complete_matches': 0,  # 所有文件都存在
        'partial_matches': 0,   # 部分文件存在
        'missing_files': {}
    }
    
    all_results = []
    
    for i, match_id in enumerate(match_dirs, 1):
        match_dir = os.path.join(base_dir, match_id)
        result = parse_match_data(match_dir, match_id)
        all_results.append(result)
        
        # 统计文件完整性
        existing_files = sum(1 for f in result['files'].values() if f.get('exists'))
        total_files = len(result['files'])
        
        if existing_files == total_files:
            stats['complete_matches'] += 1
        elif existing_files > 0:
            stats['partial_matches'] += 1
        
        # 记录缺失的文件类型
        for page_type, file_info in result['files'].items():
            if not file_info.get('exists'):
                if page_type not in stats['missing_files']:
                    stats['missing_files'][page_type] = 0
                stats['missing_files'][page_type] += 1
        
        # 打印进度
        if i % 10 == 0 or i == len(match_dirs):
            print(f"已处理: {i}/{len(match_dirs)} 个比赛")
    
    # 打印统计结果
    print(f"\n{'='*80}")
    print("解析完成!")
    print(f"{'='*80}")
    print(f"\n统计信息:")
    print(f"  总比赛数: {stats['total_matches']}")
    print(f"  完整数据: {stats['complete_matches']} 场")
    print(f"  部分数据: {stats['partial_matches']} 场")
    print(f"  缺失数据: {stats['total_matches'] - stats['complete_matches'] - stats['partial_matches']} 场")
    
    if stats['missing_files']:
        print(f"\n缺失文件统计:")
        for page_type, count in sorted(stats['missing_files'].items(), key=lambda x: -x[1]):
            print(f"  {page_type}: {count} 场缺失")
    
    # 保存详细结果到文件
    output_file = f"/Users/mac/StudioProjects/2026/open-citycloud-workspace/python/event-crawler/apps/stock-monitor-backend/data/okooo/parse_results_{date}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'date': date,
            'stats': stats,
            'matches': all_results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细结果已保存到: {output_file}")

if __name__ == "__main__":
    main()
