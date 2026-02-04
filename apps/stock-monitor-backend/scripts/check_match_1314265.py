#!/usr/bin/env python3
"""
检查比赛 1314265 是否在数据库中
"""
import asyncio
import sys
sys.path.insert(0, '/Users/mac/StudioProjects/2026/open-citycloud-workspace/python/event-crawler/apps/stock-monitor-backend')

from app.database import DatabaseManager

async def check_match():
    db = DatabaseManager()
    await db.connect()
    
    async with db.get_session() as session:
        from sqlalchemy import text
        result = await session.execute(text('SELECT * FROM matches WHERE match_id = :match_id'), {'match_id': '1314265'})
        match = result.fetchone()
        
        if match:
            print('比赛已存在于数据库:')
            print(f'  ID: {match.match_id}')
            print(f'  联赛: {match.league}')
            print(f'  主队: {match.home_team}')
            print(f'  客队: {match.away_team}')
            print(f'  时间: {match.match_time}')
            print(f'  状态: {match.status}')
            print(f'  爬取状态: {match.is_caw}')
        else:
            print('比赛 1314265 不存在于数据库中')
            print('需要重新解析并入库')
    
    await db.close()

if __name__ == "__main__":
    asyncio.run(check_match())
