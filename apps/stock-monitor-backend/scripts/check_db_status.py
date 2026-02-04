#!/usr/bin/env python3
"""
检查数据库中比赛的 is_caw 状态
"""
import asyncio
import sys
sys.path.insert(0, '/Users/mac/StudioProjects/2026/open-citycloud-workspace/python/event-crawler/apps/stock-monitor-backend')

from app.database import DatabaseManager
from sqlalchemy import text

async def check_matches():
    db = DatabaseManager()
    await db.initialize()
    
    match_ids = [
        "1314253", "1314256", "1314258", "1314259", "1314263", "1314264", "1314265", "1314266",
        "1315661", "1316063", "1316064", "1317416", "1317455", "1317782", "1319515",
        "1320212", "1320215", "1320216", "1320217", "1320218", "1320219", "1320220", "1320221",
        "1320234", "1320245", "1320246", "1320767", "1320769", "1320777", "1320780", "1321067"
    ]
    
    async with db.get_session() as session:
        print("检查数据库中的比赛状态:\n")
        print(f"{'比赛ID':<12} {'联赛':<10} {'主队':<10} {'客队':<10} {'is_caw':<8} {'状态'}")
        print("-" * 70)
        
        for match_id in match_ids:
            result = await session.execute(
                text('SELECT match_id, league, home_team, away_team, is_caw FROM okooo_matches WHERE match_id = :match_id'),
                {'match_id': match_id}
            )
            row = result.fetchone()
            
            if row:
                status = "✓ 可爬取" if row.is_caw == 1 else "✗ 已禁用"
                print(f"{row.match_id:<12} {row.league:<10} {row.home_team:<10} {row.away_team:<10} {row.is_caw:<8} {status}")
            else:
                print(f"{match_id:<12} {'N/A':<10} {'N/A':<10} {'N/A':<10} {'N/A':<8} ✗ 不存在")
    
    await db.close()

if __name__ == "__main__":
    asyncio.run(check_matches())
