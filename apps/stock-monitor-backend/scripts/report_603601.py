import asyncio
import sys
import os
from sqlalchemy import text
from datetime import date

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import db_manager

async def generate_report():
    await db_manager.initialize()
    
    start_date = '2025-11-20'
    end_date = '2025-12-10'
    target_stock = '603601'
    
    print(f"\n=== 每日评分 Top 3 及 603601 追踪 ({start_date} 至 {end_date}) ===")
    
    async with db_manager.get_session() as session:
        # Get all dates
        res = await session.execute(text("""
            SELECT DISTINCT trade_date 
            FROM stock_score_result 
            WHERE trade_date BETWEEN :start AND :end
            ORDER BY trade_date
        """), {"start": start_date, "end": end_date})
        dates = [row[0] for row in res.fetchall()]
        
        if not dates:
            print("该时间段内无评分数据。")
            return

        for d in dates:
            d_str = d.strftime('%Y-%m-%d')
            print(f"\n--- {d_str} ---")
            
            # Top 3
            res = await session.execute(text("""
                SELECT code, total_score 
                FROM stock_score_result 
                WHERE trade_date = :date 
                ORDER BY total_score DESC 
                LIMIT 3
            """), {"date": d})
            top_stocks = res.fetchall()
            print("Top 3:")
            for s in top_stocks:
                print(f"  {s[0]}: {s[1]}")
            
            # 603601 Check
            res = await session.execute(text("""
                SELECT total_score, 
                (SELECT COUNT(*) + 1 FROM stock_score_result WHERE trade_date = :date AND total_score > t.total_score) as ranking,
                (SELECT COUNT(*) FROM stock_score_result WHERE trade_date = :date) as total
                FROM stock_score_result t
                WHERE code = :code AND trade_date = :date
            """), {"code": target_stock, "date": d})
            target_row = res.fetchone()
            
            if target_row:
                print(f"603601: 评分 {target_row[0]}, 排名 {target_row[1]}/{target_row[2]}")
            else:
                print(f"603601: 未入选")

if __name__ == "__main__":
    asyncio.run(generate_report())
