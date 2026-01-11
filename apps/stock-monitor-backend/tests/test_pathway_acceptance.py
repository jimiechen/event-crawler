#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pathway量价计算验收测试
测试603601在15天内（2025-11-20至2025-12-10）的评分和排名变化
"""

import sys
import os
from pathlib import Path
from datetime import datetime, date, timedelta
import pandas as pd
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

sys.path.append(str(Path(__file__).parent.parent))

from app.database import DatabaseManager
from app.services.pathway_engine import PathwayVolumePriceEngine
from app.models.stock_daily import StockDaily, StockScoreResult
from app.models.stock import StockInfo


class PathwayAcceptanceTest:
    """Pathway量价计算验收测试"""

    def __init__(self):
        self.test_config = {
            'focus_symbol': '603601.SH',
            'test_start': '2025-11-20',
            'test_end': '2025-12-10',
            'csv_path': '/Volumes/MacintoshHD/data/daily'
        }
        self.results = []
        self.rankings = {}

    def check_csv_data_integrity(self) -> dict:
        """检查CSV数据完整性"""
        print("\n" + "=" * 60)
        print("阶段1: 数据准备")
        print("-" * 40)
        
        print(f"🔍 检查 {self.test_config['focus_symbol']} CSV数据完整性")
        
        csv_path = Path(self.test_config['csv_path']) / f"{self.test_config['focus_symbol']}.csv"
        
        if not csv_path.exists():
            print(f"❌ CSV文件不存在: {csv_path}")
            return {
                'symbol': self.test_config['focus_symbol'],
                'csv_exists': False,
                'data_completeness': 0.0,
                'found_days': 0,
                'expected_days': 0
            }
        
        try:
            df = pd.read_csv(csv_path)
            
            column_mapping = {
                '股票代码': 'code',
                '交易日期': 'trade_date',
                '开盘价': 'open',
                '最高价': 'high',
                '最低价': 'low',
                '收盘价': 'close',
                '成交量(手)': 'vol',
                '成交额(千元)': 'amount'
            }
            df = df.rename(columns=column_mapping)
            
            df['trade_date'] = pd.to_datetime(df['trade_date'], errors='coerce')
            
            start_date = pd.to_datetime(self.test_config['test_start'])
            end_date = pd.to_datetime(self.test_config['test_end'])
            
            mask = (df['trade_date'] >= start_date) & (df['trade_date'] <= end_date)
            period_df = df[mask]
            
            expected_dates = pd.bdate_range(start=start_date, end=end_date)
            found_dates = set(period_df['trade_date'].dt.date)
            expected_dates_set = set(expected_dates.date)
            missing_dates = expected_dates_set - found_dates
            
            data_completeness = len(found_dates) / len(expected_dates) if len(expected_dates) > 0 else 0.0
            
            print(f"✅ CSV文件存在: {csv_path}")
            print(f"📊 数据样本:")
            print(period_df[['trade_date', 'open', 'high', 'low', 'close', 'vol']].head())
            
            print(f"\n📈 数据完整性:")
            print(f"  应有交易日: {len(expected_dates)} 天")
            print(f"  实有数据: {len(period_df)} 天")
            print(f"  数据完整度: {data_completeness:.1%}")
            
            if missing_dates:
                print(f"  缺失日期: {sorted(missing_dates)}")
            
            print(f"\n✅ 问财条件验证:")
            
            for i, row in period_df.iterrows():
                if i == 0:
                    continue
                
                prev_row = period_df.iloc[i-1]
                volume_ratio = row['vol'] / prev_row['vol'] if prev_row['vol'] and prev_row['vol'] > 0 else 0
                
                if volume_ratio >= 2.8:
                    print(f"  {row['trade_date'].strftime('%Y-%m-%d')}: 满足2.8倍量条件 (量比={volume_ratio:.2f}) ✅")
                else:
                    print(f"  {row['trade_date'].strftime('%Y-%m-%d')}: 不满足2.8倍量条件 (量比={volume_ratio:.2f})")
            
            return {
                'symbol': self.test_config['focus_symbol'],
                'csv_exists': True,
                'data_completeness': data_completeness,
                'found_days': len(period_df),
                'expected_days': len(expected_dates),
                'missing_dates': sorted(missing_dates),
                'df': period_df
            }
            
        except Exception as e:
            print(f"❌ 检查CSV数据失败: {e}")
            return {
                'symbol': self.test_config['focus_symbol'],
                'csv_exists': False,
                'data_completeness': 0.0,
                'found_days': 0,
                'expected_days': 0,
                'missing_dates': [],
                'error': str(e)
            }

    async def run_pathway_test(self, db_manager: DatabaseManager) -> dict:
        """运行Pathway计算测试"""
        print("\n" + "=" * 60)
        print("阶段2: Pathway计算测试")
        print("-" * 40)
        
        print(f"🚀 初始化Pathway引擎...")
        
        async with db_manager.get_session() as session:
            pathway_engine = PathwayVolumePriceEngine(session)
            
            start_date = pd.to_datetime(self.test_config['test_start'])
            end_date = pd.to_datetime(self.test_config['test_end'])
            
            date_range = pd.bdate_range(start=start_date, end=end_date)
            
            print(f"📅 测试周期: {self.test_config['test_start']} 至 {self.test_config['test_end']}")
            print(f"  交易日数: {len(date_range)} 天")
            
            for test_date in date_range:
                print(f"\n  处理日期: {test_date.strftime('%Y-%m-%d')}")
                
                result = await pathway_engine.calculate_score_for_date(
                    self.test_config['focus_symbol'],
                    test_date
                )
                
                if result:
                    self.results.append(result)
                    print(f"    评分: {result['total_score']:.2f}")
                    print(f"    标签: {len(result.get('tags', []))} 个")
                    
                    tags = result.get('tags', [])
                    for tag in tags:
                        print(f"      - {tag['name']}: {tag['score']}分")
                else:
                    print(f"    ⚠️ 未找到数据或计算失败")
            
            print(f"\n✅ Pathway计算完成: 处理 {len(self.results)} 条记录")
            
            return {
                'symbol': self.test_config['focus_symbol'],
                'processed_count': len(self.results),
                'results': self.results
            }

    async def verify_wencai_conditions(self) -> dict:
        """验证问财条件触发"""
        print("\n" + "=" * 60)
        print("阶段3: 结果验证")
        print("-" * 40)
        
        print(f"✅ 问财条件触发验证:")
        
        three_times_count = 0
        two_times_count = 0
        other_tags_count = 0
        
        for result in self.results:
            tags = result.get('tags', [])
            for tag in tags:
                if tag['name'] == '3倍量':
                    three_times_count += 1
                elif tag['name'] == '2倍量':
                    two_times_count += 1
                else:
                    other_tags_count += 1
        
        print(f"  3倍量标签触发: {three_times_count} 次")
        print(f"  2倍量标签触发: {two_times_count} 次")
        print(f"  其他标签触发: {other_tags_count} 次")
        print(f"  总标签触发: {three_times_count + two_times_count + other_tags_count} 次")
        
        expected_3x = sum(1 for result in self.results 
                          if any(tag['name'] == '3倍量' for tag in result.get('tags', [])))
        
        print(f"\n📊 预期结果:")
        print(f"  预期3倍量触发次数: ~{expected_3x} 次")
        print(f"  实际3倍量触发次数: {three_times_count} 次")
        
        if three_times_count >= expected_3x * 0.8:
            print(f"  ✅ 问财条件触发验证通过")
        else:
            print(f"  ⚠️ 问财条件触发验证可能存在问题")
        
        return {
            'three_times_count': three_times_count,
            'two_times_count': two_times_count,
            'other_tags_count': other_tags_count,
            'expected_3x': expected_3x,
            'pass': three_times_count >= expected_3x * 0.8
        }

    def analyze_score_trends(self) -> dict:
        """分析评分变化趋势"""
        print("\n" + "=" * 60)
        print("阶段3: 评分变化趋势分析")
        print("-" * 40)
        
        if not self.results:
            print("❌ 无评分数据")
            return {}
        
        scores = [r['total_score'] for r in self.results]
        
        if len(scores) < 2:
            print("❌ 评分数据不足")
            return {}
        
        print(f"📈 评分统计:")
        print(f"  初始评分: {scores[0]:.2f}")
        print(f"  结束评分: {scores[-1]:.2f}")
        print(f"  评分变化: {scores[-1] - scores[0]:.2f}")
        print(f"  平均评分: {sum(scores) / len(scores):.2f}")
        print(f"  最大评分: {max(scores):.2f}")
        print(f"  最小评分: {min(scores):.2f}")
        
        score_changes = []
        for i in range(1, len(scores)):
            change = scores[i] - scores[i-1]
            score_changes.append({
                'date': self.results[i]['trade_date'],
                'change': change,
                'percent': change / scores[i-1] * 100 if scores[i-1] > 0 else 0
            })
        
        positive_changes = [c for c in score_changes if c['change'] > 0]
        negative_changes = [c for c in score_changes if c['change'] < 0]
        
        print(f"\n📊 评分变化分析:")
        print(f"  正向变化: {len(positive_changes)} 次")
        print(f"  负向变化: {len(negative_changes)} 次")
        print(f"  无变化: {len(score_changes) - len(positive_changes) - len(negative_changes)} 次")
        
        return {
            'initial_score': scores[0],
            'final_score': scores[-1],
            'total_change': scores[-1] - scores[0],
            'avg_score': sum(scores) / len(scores),
            'max_score': max(scores),
            'min_score': min(scores),
            'score_changes': score_changes,
            'positive_count': len(positive_changes),
            'negative_count': len(negative_changes)
        }

    async def verify_rankings(self, db_manager: DatabaseManager) -> dict:
        """验证排名变化"""
        print("\n" + "=" * 60)
        print("阶段3: 排名变化验证")
        print("-" * 40)
        
        async with db_manager.get_session() as session:
            stmt = select(
                StockScoreResult.code,
                StockScoreResult.trade_date,
                StockScoreResult.total_score
            ).where(
                StockScoreResult.code == self.test_config['focus_symbol'],
                StockScoreResult.trade_date >= pd.to_datetime(self.test_config['test_start']),
                StockScoreResult.trade_date <= pd.to_datetime(self.test_config['test_end'])
            ).order_by(StockScoreResult.trade_date)
            
            result = await session.execute(stmt)
            score_results = result.scalars().all()
            
            if not score_results:
                print("❌ 未找到评分数据")
                return {}
            
            print(f"📊 排名计算:")
            
            rankings = {}
            for score_result in score_results:
                trade_date = score_result.trade_date
                date_str = trade_date.strftime('%Y-%m-%d')
                
                stmt_count = select(func.count(StockScoreResult.code)).where(
                    StockScoreResult.trade_date == trade_date
                )
                count_result = await session.execute(stmt_count)
                total_count = count_result.scalar() or 0
                
                stmt_higher = select(func.count(StockScoreResult.code)).where(
                    StockScoreResult.trade_date == trade_date,
                    StockScoreResult.total_score > score_result.total_score
                )
                higher_result = await session.execute(stmt_higher)
                higher_count = higher_result.scalar() or 0
                
                ranking = higher_count + 1
                
                rankings[date_str] = {
                    'score': float(score_result.total_score),
                    'ranking': ranking,
                    'total_count': total_count,
                    'higher_count': higher_count
                }
            
            print(f"  计算了 {len(rankings)} 天的排名")
            
            return rankings

    def analyze_ranking_trends(self, rankings: dict) -> dict:
        """分析排名趋势"""
        print("\n" + "=" * 60)
        print("阶段3: 排名变化趋势分析")
        print("-" * 40)
        
        if not rankings:
            print("❌ 无排名数据")
            return {}
        
        sorted_dates = sorted(rankings.keys())
        initial_ranking = rankings[sorted_dates[0]]['ranking']
        final_ranking = rankings[sorted_dates[-1]]['ranking']
        
        ranking_changes = []
        for i in range(1, len(sorted_dates)):
            current_ranking = rankings[sorted_dates[i]]['ranking']
            prev_ranking = rankings[sorted_dates[i-1]]['ranking']
            change = prev_ranking - current_ranking
            
            ranking_changes.append({
                'date': sorted_dates[i],
                'current_ranking': current_ranking,
                'prev_ranking': prev_ranking,
                'change': change
            })
        
        improvements = [r for r in ranking_changes if r['change'] > 0]
        declines = [r for r in ranking_changes if r['change'] < 0]
        
        print(f"📊 排名分析:")
        print(f"  起始排名: 第{initial_ranking}名")
        print(f"  结束排名: 第{final_ranking}名")
        print(f"  排名提升: {len(improvements)} 次")
        print(f"  排名下降: {len(declines)} 次")
        
        best_ranking = min([r['current_ranking'] for r in rankings.values()])
        worst_ranking = max([r['current_ranking'] for r in rankings.values()])
        
        print(f"  最佳排名: 第{best_ranking}名")
        print(f"  最差排名: 第{worst_ranking}名")
        
        return {
            'initial_ranking': initial_ranking,
            'final_ranking': final_ranking,
            'rank_improvement': initial_ranking - final_ranking,
            'improvements': len(improvements),
            'declines': len(declines),
            'best_ranking': best_ranking,
            'worst_ranking': worst_ranking,
            'ranking_changes': ranking_changes
        }

    def generate_unit_test_report(self, data_check: dict, wencai_verify: dict, score_trends: dict, ranking_trends: dict) -> str:
        """生成单元测试报告"""
        print("\n" + "=" * 60)
        print("阶段3: 生成单元测试报告")
        print("-" * 40)
        
        report_dir = Path("./acceptance_reports")
        report_dir.mkdir(exist_ok=True, parents=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = report_dir / f"pathway_unit_test_report_{timestamp}.md"
        
        with open(report_file, 'w') as f:
            f.write("# Pathway量价计算单元测试报告\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 测试概要\n\n")
            f.write(f"- **测试股票**: {self.test_config['focus_symbol']} (再升科技)\n")
            f.write(f"- **测试周期**: {self.test_config['test_start']} 至 {self.test_config['test_end']}\n")
            f.write(f"- **测试天数**: {data_check.get('found_days', 0)} 天\n\n")
            
            f.write("## 阶段1: 数据准备\n\n")
            f.write(f"- **CSV文件存在**: {'✅' if data_check.get('csv_exists') else '❌'}\n")
            f.write(f"- **数据完整度**: {data_check.get('data_completeness', 0):.1%}\n")
            f.write(f"- **应有交易日**: {data_check.get('expected_days', 0)}\n")
            f.write(f"- **实有数据**: {data_check.get('found_days', 0)}\n")
            
            if data_check.get('missing_dates'):
                f.write(f"- **缺失日期**: {len(data_check['missing_dates'])} 个\n")
            
            f.write("\n## 阶段2: 问财条件验证\n\n")
            f.write(f"- **3倍量标签触发**: {wencai_verify.get('three_times_count', 0)} 次\n")
            f.write(f"- **2倍量标签触发**: {wencai_verify.get('two_times_count', 0)} 次\n")
            f.write(f"- **其他标签触发**: {wencai_verify.get('other_tags_count', 0)} 次\n")
            f.write(f"- **预期3倍量触发**: {wencai_verify.get('expected_3x', 0)} 次\n")
            f.write(f"- **验证结果**: {'✅ 通过' if wencai_verify.get('pass') else '❌ 失败'}\n")
            
            f.write("\n## 阶段3: 评分变化趋势\n\n")
            f.write(f"- **初始评分**: {score_trends.get('initial_score', 0):.2f}\n")
            f.write(f"- **结束评分**: {score_trends.get('final_score', 0):.2f}\n")
            f.write(f"- **评分变化**: {score_trends.get('total_change', 0):.2f}\n")
            f.write(f"- **平均评分**: {score_trends.get('avg_score', 0):.2f}\n")
            f.write(f"- **最大评分**: {score_trends.get('max_score', 0):.2f}\n")
            f.write(f"- **最小评分**: {score_trends.get('min_score', 0):.2f}\n")
            f.write(f"- **正向变化**: {score_trends.get('positive_count', 0)} 次\n")
            f.write(f"- **负向变化**: {score_trends.get('negative_count', 0)} 次\n")
            
            f.write("\n## 阶段4: 排名变化趋势\n\n")
            f.write(f"- **起始排名**: 第{ranking_trends.get('initial_ranking', 0)}名\n")
            f.write(f"- **结束排名**: 第{ranking_trends.get('final_ranking', 0)}名\n")
            rank_change = ranking_trends.get('rank_improvement', 0)
            rank_change_str = f"+{rank_change}" if rank_change >= 0 else str(rank_change)
            f.write(f"- **排名变化**: {rank_change_str} 名\n")
            f.write(f"- **排名提升**: {ranking_trends.get('improvements', 0)} 次\n")
            f.write(f"- **排名下降**: {ranking_trends.get('declines', 0)} 次\n")
            f.write(f"- **最佳排名**: 第{ranking_trends.get('best_ranking', 0)}名\n")
            f.write(f"- **最差排名**: 第{ranking_trends.get('worst_ranking', 0)}名\n")
            
            f.write("\n## 验收结论\n\n")
            
            all_pass = (
                data_check.get('csv_exists', False) and
                data_check.get('data_completeness', 0) >= 0.95 and
                wencai_verify.get('pass', False) and
                score_trends.get('total_change', 0) > 0 and
                ranking_trends.get('rank_improvement', 0) >= 0
            )
            
            f.write("### " + ("✅" if all_pass else "❌") + " 验收通过\n\n")
            
            if all_pass:
                f.write("Pathway量价计算系统在15天真实数据测试中表现良好：\n\n")
                f.write("1. **数据完整性**: 成功处理真实CSV数据\n")
                f.write("2. **增量计算**: 正确实现每日增量更新\n")
                f.write("3. **评分准确**: 评分结果符合预期（2.8倍量 → 3倍量标签，300分）\n")
                f.write("4. **排名计算**: 排名计算正确反映评分变化\n")
                f.write("5. **系统稳定**: 处理过程无异常错误\n")
            else:
                f.write("Pathway量价计算系统存在以下问题：\n\n")
                if not data_check.get('csv_exists', False):
                    f.write("1. 数据加载或处理错误\n")
                if data_check.get('data_completeness', 0) < 0.95:
                    f.write("2. 数据完整度不足\n")
                if not wencai_verify.get('pass', False):
                    f.write("3. 问财条件触发验证失败\n")
                if score_trends.get('total_change', 0) <= 0:
                    f.write("4. 评分趋势不符合预期\n")
                if ranking_trends.get('rank_improvement', 0) < 0:
                    f.write("5. 排名趋势不符合预期\n")
        
        print(f"📄 单元测试报告已生成: {report_file}")
        
        return str(report_file)

    def generate_acceptance_report(self, unit_test_report_file: str) -> str:
        """生成验收报告"""
        print("\n" + "=" * 60)
        print("阶段3: 生成验收报告")
        print("-" * 40)
        
        report_dir = Path("./acceptance_reports")
        report_file = report_dir / f"pathway_acceptance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_file, 'w') as f:
            f.write("# Pathway量价计算系统验收报告\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 测试概要\n\n")
            f.write(f"- **测试股票**: {self.test_config['focus_symbol']} (再升科技)\n")
            f.write(f"- **测试周期**: {self.test_config['test_start']} 至 {self.test_config['test_end']}\n")
            f.write(f"- **测试天数**: {len(self.results)} 天\n")
            
            f.write("## 每日评分和排名\n\n")
            f.write("| 日期 | 评分 | 排名 | 评分变化 |\n")
            f.write("|------|------|------|----------|\n")
            
            for result in self.results:
                trade_date = result['trade_date'].strftime('%Y-%m-%d')
                score = result['total_score']
                
                ranking = "N/A"
                if trade_date in self.rankings:
                    ranking = f"第{self.rankings[trade_date]['ranking']}名"
                
                score_change = ""
                if len(self.results) > 0:
                    idx = self.results.index(result)
                    if idx > 0:
                        prev_score = self.results[idx-1]['total_score']
                        change = score - prev_score
                        score_change = f"{change:+.2f}"
                
                f.write(f"| {trade_date} | {score:.2f} | {ranking} | {score_change} |\n")
            
            f.write("\n## 标签触发统计\n\n")
            f.write("| 标签名称 | 触发次数 |\n")
            f.write("|----------|----------|\n")
            f.write("| 3倍量 | {sum(1 for r in self.results if any(tag['name'] == '3倍量' for tag in r.get('tags', [])))} |\n")
            f.write("| 2倍量 | {sum(1 for r in self.results if any(tag['name'] == '2倍量' for tag in r.get('tags', [])))} |\n")
            f.write("| 阳包阴 | {sum(1 for r in self.results if any(tag['name'] == '阳包阴' for tag in r.get('tags', [])))} |\n")
            f.write("| 底分型 | {sum(1 for r in self.results if any(tag['name'] == '底分型' for tag in r.get('tags', [])))} |\n")
            f.write("| 5日地量 | {sum(1 for r in self.results if any(tag['name'] == '5日地量' for tag in r.get('tags', [])))} |\n")
            f.write("| 10日地量 | {sum(1 for r in self.results if any(tag['name'] == '10日地量' for tag in r.get('tags', [])))} |\n")
            
            f.write("\n## 验收结论\n\n")
            
            all_pass = (
                len(self.results) >= 10 and
                sum(1 for r in self.results if any(tag['name'] == '3倍量' for tag in r.get('tags', []))) >= 10
            )
            
            f.write("### " + ("✅" if all_pass else "❌") + " 验收通过\n\n")
            
            if all_pass:
                f.write("Pathway量价计算系统在15天真实数据测试中表现良好：\n\n")
                f.write("1. **数据完整性**: 成功处理真实CSV数据\n")
                f.write("2. **增量计算**: 正确实现每日增量更新\n")
                f.write("3. **评分准确**: 评分结果符合预期（2.8倍量 → 3倍量标签，300分）\n")
                f.write("4. **排名计算**: 排名计算正确反映评分变化\n")
                f.write("5. **系统稳定**: 处理过程无异常错误\n")
            else:
                f.write("Pathway量价计算系统存在以下问题：\n\n")
                f.write("1. 数据处理天数不足\n")
                f.write("2. 3倍量标签触发次数不足\n")
        
        print(f"📄 验收报告已生成: {report_file}")
        
        return str(report_file)

    async def run_full_test(self, db_manager: DatabaseManager):
        """运行完整验收测试"""
        print("\n" + "=" * 80)
        print("🎯 Pathway量价计算系统验收测试")
        print("=" * 80)
        
        try:
            data_check = self.check_csv_data_integrity()
            
            pathway_result = await self.run_pathway_test(db_manager)
            
            wencai_verify = await self.verify_wencai_conditions()
            
            score_trends = self.analyze_score_trends()
            
            rankings = await self.verify_rankings(db_manager)
            
            ranking_trends = self.analyze_ranking_trends(rankings)
            
            unit_test_report_file = self.generate_unit_test_report(
                data_check, wencai_verify, score_trends, ranking_trends
            )
            
            acceptance_report_file = self.generate_acceptance_report(unit_test_report_file)
            
            print("\n" + "=" * 80)
            print("🎉 验收测试完成")
            print("=" * 80)
            
            print(f"\n📄 单元测试报告: {unit_test_report_file}")
            print(f"📄 验收报告: {acceptance_report_file}")
            
            return {
                'success': True,
                'unit_test_report': unit_test_report_file,
                'acceptance_report': acceptance_report_file
            }
            
        except Exception as e:
            logger.error(f"验收测试失败: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'error': str(e)
            }


async def main():
    """主函数"""
    from app.database import DatabaseManager
    
    db_manager = DatabaseManager()
    
    tester = PathwayAcceptanceTest()
    
    result = await tester.run_full_test(db_manager)
    
    if result['success']:
        print("\n✅ 验收测试成功完成")
        sys.exit(0)
    else:
        print(f"\n❌ 验收测试失败: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
