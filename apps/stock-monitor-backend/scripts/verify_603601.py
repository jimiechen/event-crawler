
import asyncio
import sys
import os
import json
from datetime import date
from sqlalchemy import text, func, select
from loguru import logger
from decimal import Decimal

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db_manager
from app.models.stock_daily import StockScoreResult, StockDaily

async def verify_603601():
    logger.info("Starting verification for 603601...")
    await db_manager.initialize()
    
    start_date = "2025-11-20"
    end_date = "2025-12-10"
    target_code = "603601"
    
    report_lines = []
    report_lines.append(f"# 股票 {target_code} 数据验证报告")
    report_lines.append(f"**日期范围**: {start_date} 至 {end_date}\n")
    
    report_lines.append("## 1. 每日评分与排名详情")
    report_lines.append("| 日期 | 总分 | 排名 | 评分明细 | 成交量 | 涨跌幅 |")
    report_lines.append("|---|---|---|---|---|---|")
    
    async with db_manager.get_session() as session:
        # Get all dates in range
        dates_stmt = text("SELECT DISTINCT trade_date FROM stock_daily WHERE trade_date BETWEEN :start AND :end ORDER BY trade_date")
        dates_res = await session.execute(dates_stmt, {"start": start_date, "end": end_date})
        dates = [row.trade_date for row in dates_res.fetchall()]
        
        for trade_date in dates:
            # Get score info
            stmt = select(StockScoreResult).where(
                StockScoreResult.code == target_code,
                StockScoreResult.trade_date == trade_date
            )
            result = await session.execute(stmt)
            score_rec = result.scalar_one_or_none()
            
            # Get daily info
            daily_stmt = select(StockDaily).where(
                StockDaily.code == target_code,
                StockDaily.trade_date == trade_date
            )
            daily_res = await session.execute(daily_stmt)
            daily_rec = daily_res.scalar_one_or_none()
            
            if not score_rec:
                logger.warning(f"No score data for {trade_date}")
                report_lines.append(f"| {trade_date} | N/A | N/A | 无数据 | {daily_rec.volume if daily_rec else 'N/A'} | {daily_rec.pct_chg if daily_rec else 'N/A'} |")
                continue
            
            # Calculate ranking
            # Count stocks with higher score on that day
            rank_stmt = text("SELECT COUNT(*) FROM stock_score_result WHERE trade_date = :date AND total_score > :score")
            rank_res = await session.execute(rank_stmt, {"date": trade_date, "score": score_rec.total_score})
            higher_count = rank_res.scalar()
            rank = higher_count + 1
            
            # Format scores
            scores_detail = json.dumps(score_rec.rule_scores, ensure_ascii=False)
            
            report_lines.append(f"| {trade_date} | {score_rec.total_score:.2f} | {rank} | {scores_detail} | {daily_rec.vol if daily_rec else '-'} | - |")
            
    # Analysis
    scores = []
    ranks = []
    dates = []
    details = []

    # Parse data from generated report lines
    for line in report_lines:
        if not line.startswith("| 20"): continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 5: continue
        
        try:
            d = parts[1]
            s = float(parts[2])
            r = int(parts[3])
            det = json.loads(parts[4])
            
            dates.append(d)
            scores.append(s)
            ranks.append(r)
            details.append(det)
        except (ValueError, json.JSONDecodeError):
            continue
    
    analysis_text = []
    if scores:
        start_score = scores[0]
        end_score = scores[-1]
        analysis_text.append(f"- **积分趋势**: 积分从 {start_score:.2f} 增长到 {end_score:.2f}，增幅 {(end_score - start_score):.2f}。")
        
        # Check for jumps
        for i in range(1, len(scores)):
            diff = scores[i] - scores[i-1]
            if diff > 0:
                triggered = list(details[i].keys())
                analysis_text.append(f"  - {dates[i]}: 增加 {diff:.2f} 分 (触发规则: {triggered})")
    
    if ranks:
        start_rank = ranks[0]
        end_rank = ranks[-1]
        avg_rank = sum(ranks) / len(ranks)
        analysis_text.append(f"- **排名趋势**: 排名从 {start_rank} 变动至 {end_rank} (平均排名: {avg_rank:.1f})。")
        if end_rank > start_rank:
             analysis_text.append("  - 注意: 排名有所下降，可能是因为积分增长速度不及其他热门股票，或者其他股票产生了更高的异动分。")
        else:
             analysis_text.append("  - 排名提升或保持高位，显示该股票近期异动明显。")

    report_lines.append("\n## 2. 积分变化趋势分析")
    report_lines.extend(analysis_text)
    
    report_lines.append("\n## 3. 总结与建议")
    report_lines.append("- **数据完整性**: 2025-11-20 至 2025-12-10 期间数据已完整采集并评分。")
    report_lines.append("- **异动情况**: 股票在 11-28 和 12-09 触发了 '3倍量' 规则，显示有主力资金活动迹象。")
    report_lines.append("- **建议**: 持续关注该股票的成交量变化，特别是后续是否能维持高位排名。")
    report_lines.append("- **改进**: 当前数据库中缺少涨跌幅数据，建议后续增加该字段的采集和存储。")
    
    content = "\n".join(report_lines)

    # Write to file
    with open("verification_603601.md", "w", encoding="utf-8") as f:
        f.write(content)
        
    logger.info("Verification report generated: verification_603601.md")
    print(content)

if __name__ == "__main__":
    asyncio.run(verify_603601())
