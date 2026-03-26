"""
生成验收报告（物理文件版）
"""
import sys
import csv
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(__file__).replace('/tests/generate_acceptance_report_file.py', ''))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import DatabaseConfig
from app.models.stock_daily import StockScoreResult
from app.models.stock import StockInfo
from app.models.volume_analysis import StockVolumeBaseline

async def generate_acceptance_report_file(test_codes: list = None):
    """
    生成验收报告文件
    
    Args:
        test_codes: 测试股票代码列表，如果为None则查询所有
    """
    print("📊 生成验收报告文件...")
    
    # 初始化数据库
    from app.database import db_manager as db_mgr
    await db_mgr.initialize()
    
    session = db_mgr.session_factory()
    try:
        # 查询测试股票代码
        if test_codes is None:
            # 查询所有有评分结果的股票
            stmt = text("""
                SELECT DISTINCT code 
                FROM stock_score_result 
                WHERE trade_date >= '2025-11-20' 
                    AND trade_date <= '2025-12-10'
                ORDER BY code
            """)
            result = await session.execute(stmt)
            test_codes = [row[0] for row in result.fetchall()]
        
        print(f"   测试股票数量: {len(test_codes)}")
        
        # 创建报告目录
        report_dir = Path('/Users/mac/StudioProjects/open-citycloud/tests/reports')
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成报告文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = report_dir / f'acceptance_report_{timestamp}.csv'
        
        # 写入CSV报告
        with open(report_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入表头
            writer.writerow([
                '股票代码',
                '股票名称',
                '测试天数',
                '初始总分',
                '最终总分',
                '总积分增长',
                '最高排名',
                '最低排名',
                '最新排名',
                '3倍量日期',
                '60日地量日期',
                'volume_anomaly_score',
                'score_update_time'
            ])
            
            # 遍历每只股票
            for code in test_codes:
                # 1. 查询每日积分变化
                stmt = text(f"""
                    SELECT 
                        trade_date,
                        total_score
                    FROM stock_score_result
                    WHERE code = '{code}'
                        AND trade_date >= '2025-11-20'
                        AND trade_date <= '2025-12-10'
                    ORDER BY trade_date
                """)
                result = await session.execute(stmt)
                scores = result.fetchall()
                
                if not scores:
                    continue
                
                # 2. 查询排名变化
                stmt = text(f"""
                    SELECT 
                        trade_date,
                        ranking
                    FROM stock_score_result
                    WHERE code = '{code}'
                        AND trade_date >= '2025-11-20'
                        AND trade_date <= '2025-12-10'
                        AND ranking IS NOT NULL
                    ORDER BY trade_date
                """)
                result = await session.execute(stmt)
                rankings = result.fetchall()
                
                # 3. 查询stock_info
                stmt = select(StockInfo).where(StockInfo.code == code)
                result = await session.execute(stmt)
                info = result.scalar_one_or_none()
                
                # 4. 查询baseline
                stmt = select(StockVolumeBaseline).where(StockVolumeBaseline.code == code)
                result = await session.execute(stmt)
                baseline = result.scalar_one_or_none()
                
                # 5. 计算统计信息
                test_days = len(scores)
                initial_score = float(scores[0][1]) if scores else 0
                final_score = float(scores[-1][1]) if scores else 0
                score_growth = final_score - initial_score
                
                ranking_values = [r[1] for r in rankings if r[1] is not None]
                max_ranking = min(ranking_values) if ranking_values else None
                min_ranking = max(ranking_values) if ranking_values else None
                latest_ranking = rankings[-1][1] if rankings else None
                
                last_3x_date = baseline.last_3x_date if baseline else None
                last_60d_low_vol_date = baseline.last_60d_low_vol_date if baseline else None
                
                volume_anomaly_score = info.volume_anomaly_score if info else None
                score_update_time = info.score_update_time if info else None
                
                stock_name = info.name if info else f'股票{code}'
                
                # 写入CSV行
                writer.writerow([
                    code,
                    stock_name,
                    test_days,
                    f'{initial_score:.2f}',
                    f'{final_score:.2f}',
                    f'{score_growth:.2f}',
                    max_ranking,
                    min_ranking,
                    latest_ranking,
                    last_3x_date,
                    last_60d_low_vol_date,
                    volume_anomaly_score,
                    score_update_time
                ])
                
                print(f"   ✅ {code} 报告生成完成")
        
        print(f"\n✅ 验收报告文件已生成: {report_file}")
        print(f"   报告路径: {report_file}")
        
        # 生成汇总报告
        summary_file = report_dir / f'acceptance_summary_{timestamp}.txt'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("验收报告汇总\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"测试股票数量: {len(test_codes)}\n")
            f.write(f"测试日期范围: 2025-11-20 至 2025-12-10\n\n")
            
            # 计算汇总统计
            total_score_growth = 0
            max_score_growth = -float('inf')
            min_score_growth = float('inf')
            
            for code in test_codes:
                stmt = text(f"""
                    SELECT total_score 
                    FROM stock_score_result 
                    WHERE code = '{code}'
                        AND trade_date >= '2025-11-20'
                        AND trade_date <= '2025-12-10'
                    ORDER BY trade_date
                """)
                result = await session.execute(stmt)
                scores = result.fetchall()
                
                if len(scores) >= 2:
                    growth = float(scores[-1][0]) - float(scores[0][0])
                    total_score_growth += growth
                    max_score_growth = max(max_score_growth, growth)
                    min_score_growth = min(min_score_growth, growth)
            
            avg_score_growth = total_score_growth / len(test_codes) if test_codes else 0
            
            f.write("汇总统计:\n")
            f.write("-" * 80 + "\n")
            f.write(f"总积分增长: {total_score_growth:.2f}\n")
            f.write(f"平均积分增长: {avg_score_growth:.2f}\n")
            f.write(f"最高积分增长: {max_score_growth:.2f}\n")
            f.write(f"最低积分增长: {min_score_growth:.2f}\n\n")
            
            f.write("=" * 80 + "\n")
        
        print(f"✅ 汇总报告文件已生成: {summary_file}")
        
        # 生成详细报告（每只股票的每日积分）
        detail_file = report_dir / f'acceptance_detail_{timestamp}.csv'
        with open(detail_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入表头
            writer.writerow([
                '股票代码',
                '交易日期',
                '总分',
                '排名'
            ])
            
            # 遍历每只股票
            for code in test_codes:
                # 查询每日积分
                stmt = text(f"""
                    SELECT 
                        trade_date,
                        total_score,
                        ranking
                    FROM stock_score_result
                    WHERE code = '{code}'
                        AND trade_date >= '2025-11-20'
                        AND trade_date <= '2025-12-10'
                    ORDER BY trade_date
                """)
                result = await session.execute(stmt)
                rows = result.fetchall()
                
                # 写入CSV行
                for row in rows:
                    writer.writerow([
                        code,
                        row[0],
                        f'{float(row[1]):.2f}' if row[1] else '',
                        row[2]
                    ])
        
        print(f"✅ 详细报告文件已生成: {detail_file}")
        print(f"\n🎉 所有报告文件生成完成！")
        
    finally:
        await session.close()
        await db_mgr.close()

if __name__ == '__main__':
    import asyncio
    try:
        # 生成所有股票的验收报告
        asyncio.run(generate_acceptance_report_file())
    except Exception as e:
        print(f"\n❌ 生成报告异常: {e}")
        import traceback
        traceback.print_exc()
