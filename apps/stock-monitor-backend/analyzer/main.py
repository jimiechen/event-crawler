#!/usr/bin/env python3
"""
盘口分析系统主程序
支持单场比赛分析和批量分析
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_loader import DataLoader
from handicap_analyzer import HandicapAnalyzer, analyze_match, ComprehensiveAnalysis, AnalysisReport


class ConsoleColors:
    """控制台颜色输出"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    
    @staticmethod
    def info(msg: str) -> str:
        return f"{ConsoleColors.BLUE}[INFO]{ConsoleColors.ENDC} {msg}"
    
    @staticmethod
    def success(msg: str) -> str:
        return f"{ConsoleColors.GREEN}[成功]{ConsoleColors.ENDC} {msg}"
    
    @staticmethod
    def warning(msg: str) -> str:
        return f"{ConsoleColors.YELLOW}[警告]{ConsoleColors.ENDC} {msg}"
    
    @staticmethod
    def error(msg: str) -> str:
        return f"{ConsoleColors.RED}[错误]{ConsoleColors.ENDC} {msg}"
    
    @staticmethod
    def highlight(msg: str) -> str:
        return f"{ConsoleColors.HEADER}{ConsoleColors.BOLD}{msg}{ConsoleColors.ENDC}"


def print_banner():
    """打印程序横幅"""
    banner = """
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║           盘口浅盘与诱导盘分析系统 v1.0                        ║
    ║           Handicap Analysis System                            ║
    ║                                                                ║
    ║  功能: 检测亚盘盘口是否过浅                                    ║
    ║        识别博彩公司的诱导投注行为                              ║
    ║        提供综合风险评估和投注建议                              ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """
    print(ConsoleColors.highlight(banner))
    print()


def analyze_single_file(file_path: str, output_dir: Optional[str] = None, 
                        verbose: bool = False, json_only: bool = False) -> Optional[ComprehensiveAnalysis]:
    """分析单个比赛文件"""
    print(ConsoleColors.info(f"正在分析文件: {file_path}"))
    
    loader = DataLoader(file_path)
    if not loader.load():
        print(ConsoleColors.error(f"加载数据失败: {file_path}"))
        return None
    
    print(ConsoleColors.success(f"成功加载: {loader.match_info.home_team} vs {loader.match_info.away_team}"))
    
    analysis, report = analyze_match(loader)
    
    if not json_only:
        print_report(report, analysis)
    
    if verbose:
        print_verbose_info(analysis, loader)
    
    if output_dir:
        save_results(analysis, output_dir, file_path)
    
    return analysis


def print_report(report: AnalysisReport, analysis: ComprehensiveAnalysis):
    """打印分析报告"""
    print(f"\n{ConsoleColors.highlight('='*70)}")
    print(f"  {report.title}")
    print(f"{ConsoleColors.highlight('='*70)}")
    
    for section in report.sections:
        print(f"\n【{section['title']}】")
        for line in section['content']:
            if '→' in line or '⚠️' in line or '⚡' in line:
                print(f"  {ConsoleColors.warning(line)}")
            else:
                print(f"  {line}")
    
    print(f"\n{ConsoleColors.highlight('='*70)}")
    risk_level = analysis.overall_risk.get('risk_level', '未知')
    risk_color = ConsoleColors.RED if '高' in risk_level or '危险' in risk_level else \
                 ConsoleColors.YELLOW if '中等' in risk_level else ConsoleColors.GREEN
    
    print(f"  {ConsoleColors.highlight('风险等级:')} {risk_color}{risk_level}{ConsoleColors.ENDC}")
    print(f"  {ConsoleColors.highlight('结论:')} {report.conclusion}")
    print(f"  {ConsoleColors.highlight('置信度:')} {report.confidence:.1%}")
    print(f"{ConsoleColors.highlight('='*70)}\n")


def print_verbose_info(analysis: ComprehensiveAnalysis, loader: DataLoader):
    """打印详细信息"""
    print(f"\n{ConsoleColors.highlight('【详细信息】')}")
    
    print(f"\n球队历史对战:")
    for i, match in enumerate(loader.head_to_head[:5]):
        print(f"  {i+1}. {match.date} {match.score} {'赢' if match.result == '赢' else '输' if match.result == '输' else '平'} {match.opponent}")
    
    print(f"\n主队最近5场:")
    for i, match in enumerate(loader.home_history[:5]):
        print(f"  {i+1}. {match.date} {match.score} {match.result} {match.opponent}")
    
    print(f"\n客队最近5场:")
    for i, match in enumerate(loader.away_history[:5]):
        print(f"  {i+1}. {match.date} {match.score} {match.result} {match.opponent}")
    
    print(f"\n主流公司盘口:")
    major_companies = ['澳门', 'bet365', '威廉希尔', '立博', '皇冠']
    for company in loader.handicap_companies:
        if any(c in company.company for c in major_companies):
            pan_change = company.latest_pan - company.initial_pan
            pan_arrow = "↑" if pan_change > 0 else "↓" if pan_change < 0 else "→"
            print(f"  {company.company}: {company.initial_pan} → {company.latest_pan} {pan_arrow} " +
                  f"({company.latest_home}/{company.latest_away})")


def save_results(analysis: ComprehensiveAnalysis, output_dir: str, source_file: str):
    """保存分析结果"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    base_name = Path(source_file).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    json_file = output_path / f"{base_name}_analysis_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        f.write(analysis.to_json())
    print(ConsoleColors.success(f"结果已保存: {json_file}"))


def analyze_directory(directory: str, output_dir: Optional[str] = None,
                      recursive: bool = False, json_only: bool = False) -> List[Dict[str, Any]]:
    """分析目录下的所有JSON文件"""
    print(ConsoleColors.info(f"分析目录: {directory}"))
    
    path = Path(directory)
    pattern = "**/*.json" if recursive else "*.json"
    json_files = list(path.glob(pattern))
    
    if not json_files:
        print(ConsoleColors.warning(f"目录中未找到JSON文件: {directory}"))
        return []
    
    print(ConsoleColors.info(f"找到 {len(json_files)} 个JSON文件"))
    
    results = []
    
    for i, json_file in enumerate(json_files, 1):
        print(f"\n{ConsoleColors.highlight('-'*60)}")
        print(f"[{i}/{len(json_files)}] 正在分析: {json_file.name}")
        print(f"{ConsoleColors.highlight('-'*60)}")
        
        try:
            analysis = analyze_single_file(str(json_file), output_dir, json_only=json_only)
            
            if analysis:
                results.append({
                    'file': str(json_file),
                    'match': f"{analysis.match_info['home_team']} vs {analysis.match_info['away_team']}",
                    'risk_level': analysis.overall_risk.get('risk_level', '未知'),
                    'shallow_score': analysis.shallow_analysis.get('shallow_score', 0),
                    'trap_score': analysis.trap_analysis.get('trap_score', 0),
                    'suggestion': analysis.betting_suggestion.get('primary_suggestion', '无'),
                })
        except Exception as e:
            print(ConsoleColors.error(f"分析失败: {e}"))
            results.append({
                'file': str(json_file),
                'error': str(e),
            })
    
    print_summary(results)
    
    return results


def print_summary(results: List[Dict[str, Any]]):
    """打印分析汇总"""
    print(f"\n{ConsoleColors.highlight('='*70)}")
    print(f"  分析汇总")
    print(f"{ConsoleColors.highlight('='*70)}")
    
    successful = [r for r in results if 'error' not in r]
    failed = [r for r in results if 'error' in r]
    
    print(f"\n成功分析: {len(successful)} 场")
    print(f"分析失败: {len(failed)} 场")
    
    if successful:
        risk_distribution = {}
        suggestion_distribution = {}
        
        for r in successful:
            risk = r.get('risk_level', '未知')
            suggestion = r.get('suggestion', '无')
            risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
            suggestion_distribution[suggestion] = suggestion_distribution.get(suggestion, 0) + 1
        
        print(f"\n风险分布:")
        for risk, count in sorted(risk_distribution.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * count
            print(f"  {risk}: {bar} ({count})")
        
        print(f"\n建议分布:")
        for suggestion, count in sorted(suggestion_distribution.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * count
            print(f"  {suggestion}: {bar} ({count})")
    
    if failed:
        print(f"\n失败文件:")
        for r in failed:
            print(f"  - {Path(r['file']).name}: {r['error']}")


def export_summary_csv(results: List[Dict[str, Any]], output_file: str):
    """导出汇总CSV"""
    import csv
    
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        if not results:
            return
        
        fieldnames = ['file', 'match', 'risk_level', 'shallow_score', 'trap_score', 'suggestion']
        
        if 'error' in results[0]:
            fieldnames = ['file', 'error']
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for r in results:
            row = {k: v for k, v in r.items() if k in fieldnames}
            writer.writerow(row)
    
    print(ConsoleColors.success(f"汇总已导出: {output_file}"))


def main():
    """主函数"""
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="盘口浅盘与诱导盘分析系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py -f data.json                    # 分析单个文件
  python main.py -f data.json -o output/         # 分析并保存结果
  python main.py -f data.json -v                 # 显示详细信息
  python main.py -d data/                        # 分析目录下所有文件
  python main.py -d data/ -r                     # 递归分析子目录
  python main.py -d data/ --csv summary.csv      # 导出汇总CSV
        """
    )
    
    parser.add_argument('-f', '--file', type=str, help='分析单个JSON文件')
    parser.add_argument('-d', '--directory', type=str, help='分析目录下所有JSON文件')
    parser.add_argument('-o', '--output', type=str, help='结果输出目录')
    parser.add_argument('-r', '--recursive', action='store_true', help='递归处理子目录')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    parser.add_argument('--json-only', action='store_true', help='只输出JSON结果')
    parser.add_argument('--csv', type=str, help='导出汇总CSV文件路径')
    
    args = parser.parse_args()
    
    if not args.file and not args.directory:
        parser.print_help()
        print()
        print(ConsoleColors.warning("请指定要分析的文件或目录"))
        print(ConsoleColors.info("使用示例: python main.py -f data.json"))
        sys.exit(1)
    
    results = []
    
    if args.file:
        result = analyze_single_file(
            file_path=args.file,
            output_dir=args.output,
            verbose=args.verbose,
            json_only=args.json_only
        )
        if result:
            results.append({
                'file': args.file,
                'match': f"{result.match_info['home_team']} vs {result.match_info['away_team']}",
                'risk_level': result.overall_risk.get('risk_level', '未知'),
                'shallow_score': result.shallow_analysis.get('shallow_score', 0),
                'trap_score': result.trap_analysis.get('trap_score', 0),
                'suggestion': result.betting_suggestion.get('primary_suggestion', '无'),
            })
    
    if args.directory:
        results = analyze_directory(
            directory=args.directory,
            output_dir=args.output,
            recursive=args.recursive,
            json_only=args.json_only
        )
    
    if args.csv and results:
        export_summary_csv(results, args.csv)
    
    print()
    print(ConsoleColors.success("分析完成！"))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断分析")
        sys.exit(0)
    except Exception as e:
        print(f"\n程序异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
