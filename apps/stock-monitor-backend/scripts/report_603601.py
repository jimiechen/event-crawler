import asyncio
import os
import sys
from datetime import date, timedelta
from decimal import Decimal

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_manager
from app.models.stock_daily import StockScoreResult
from sqlalchemy import select, desc, func

async def generate_603601_report():
    print("🚀 Generating report for 603601...")
    
    report_date = date.today().strftime("%Y-%m-%d")
    report_dir = f"/Users/mac/StudioProjects/open-citycloud/.trae/documents/{report_date}"
    os.makedirs(report_dir, exist_ok=True)
    report_file = os.path.join(report_dir, "report_603601.md")
    
    await db_manager.initialize()
    target_code = "603601"
    
    async with db_manager.get_session() as session:
        # 1. Fetch ALL wencai scores to calculate ranking dynamically
        # We need all data to calculate rolling scores for everyone
        print("Fetching all wencai pool data...")
        stmt = select(StockScoreResult).where(
            StockScoreResult.pool_type == 'wencai'
        ).order_by(StockScoreResult.trade_date.asc())
        
        result = await session.execute(stmt)
        all_records = result.scalars().all()
        
        if not all_records:
            print("❌ No wencai records found.")
            await db_manager.close()
            return

        # 2. Organize data by date and code
        # date -> code -> score
        date_map = {}
        for r in all_records:
            if r.trade_date not in date_map:
                date_map[r.trade_date] = {}
            # Currently total_score stores daily_score
            date_map[r.trade_date][r.code] = r.total_score

        # 3. Calculate Rolling Scores and Rankings
        # We need to calculate rolling score for EVERY stock on EVERY day to get correct rank
        
        sorted_dates = sorted(date_map.keys())
        
        # To store 603601 stats
        stats_603601 = []
        
        print("Calculating rankings...")
        
        # Cache for rolling scores: code -> list of (date, score)
        # Or just re-calculate per day (slower but simpler)
        # Optimization: Keep a running window? 
        # Since dataset is small (100 stocks * 60 days), brute force window sum is fine.
        
        history_scores = {} # code -> {date: score}
        
        for d in sorted_dates:
            # Update history
            current_day_scores = date_map[d]
            for code, score in current_day_scores.items():
                if code not in history_scores:
                    history_scores[code] = {}
                history_scores[code][d] = score
            
            # Calculate rolling score for ALL stocks active up to this day
            # (or just stocks present today? Ranking usually implies active stocks)
            # Wencai pool ranking usually means "Ranking among stocks that appeared in Wencai pool ever?" 
            # OR "Ranking among stocks currently in Wencai pool?"
            # User said: "问财股票池的排名" (Ranking in Wencai Stock Pool).
            # Usually implies stocks that are considered "in the pool".
            # If a stock appeared once 20 days ago, is it still in the pool?
            # Assuming "Pool" = All stocks that have ever appeared in Wencai lists (since we set pool_type='wencai' permanently).
            
            day_rolling_scores = []
            
            # Get all codes known so far
            all_codes = history_scores.keys()
            
            for code in all_codes:
                # Calculate rolling sum for last 250 days
                window_start = d - timedelta(days=250)
                
                r_score = sum(
                    s for dt, s in history_scores[code].items()
                    if window_start < dt <= d
                )
                
                # Only include in ranking if r_score > 0? Or always?
                # Usually always if it's in the pool.
                day_rolling_scores.append({
                    "code": code,
                    "score": r_score
                })
            
            # Sort desc
            day_rolling_scores.sort(key=lambda x: x["score"], reverse=True)
            
            # Find 603601
            rank = -1
            score = 0
            found = False
            for idx, item in enumerate(day_rolling_scores):
                if item["code"] == target_code:
                    rank = idx + 1
                    score = item["score"]
                    found = True
                    break
            
            if found:
                daily_s = current_day_scores.get(target_code, Decimal(0))
                stats_603601.append({
                    "date": d,
                    "rolling_score": score,
                    "daily_score": daily_s,
                    "rank": rank,
                    "pool_size": len(day_rolling_scores)
                })

        # 4. Generate Markdown
        with open(report_file, "w") as f:
            f.write(f"# 603601 问财股票池分析报告\n\n")
            f.write(f"**生成日期**: {date.today()}\n")
            f.write(f"**股票代码**: {target_code}\n")
            f.write(f"**统计范围**: {sorted_dates[0]} 至 {sorted_dates[-1]}\n\n")
            
            f.write("## 每日评分与排名变化\n\n")
            f.write("| 日期 | 滚动总分 | 每日得分 | 每日变化 | 排名 | 排名变化 | 池总数 |\n")
            f.write("|---|---|---|---|---|---|---|\n")
            
            prev_score = None
            prev_rank = None
            
            for stat in stats_603601:
                d = stat['date']
                rolling = stat['rolling_score']
                daily = stat['daily_score']
                rank = stat['rank']
                pool_size = stat['pool_size']
                
                score_chg = "-"
                if prev_score is not None:
                    diff = rolling - prev_score
                    score_chg = f"{diff:+g}"
                
                rank_chg = "-"
                if prev_rank is not None:
                    # Rank change: Lower is better. 
                    # Prev 10, Curr 5 => Improved by 5 (+5)
                    # Prev 5, Curr 10 => Dropped by 5 (-5)
                    diff = prev_rank - rank
                    rank_chg = f"{diff:+d}"
                
                f.write(f"| {d} | {rolling} | {daily} | {score_chg} | {rank} | {rank_chg} | {pool_size} |\n")
                
                prev_score = rolling
                prev_rank = rank
        
        print(f"✅ Report generated at: {report_file}")
        
        # Also print to console for immediate view
        with open(report_file, "r") as f:
            print(f.read())
            
    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(generate_603601_report())
