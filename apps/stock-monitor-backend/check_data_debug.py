import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from sqlalchemy import text
from app.database import db_manager

async def check_data():
    async with db_manager.get_session() as db:
        # Check code formats
        print('--- Code Format Check ---')
        try:
            res = await db.execute(text('SELECT stock_code FROM wencai_stocks LIMIT 3'))
            print('Wencai Stocks:', [r[0] for r in res.fetchall()])
        except Exception as e:
            print(f"Error reading wencai_stocks: {e}")
        
        try:
            res = await db.execute(text('SELECT code FROM stock_daily LIMIT 3'))
            print('Stock Daily:', [r[0] for r in res.fetchall()])
        except Exception as e:
            print(f"Error reading stock_daily: {e}")

        # Check counts
        print('\n--- Counts ---')
        try:
            res = await db.execute(text('SELECT COUNT(*) FROM wencai_stocks'))
            print('Wencai Count:', res.scalar())
        except:
            print("Error counting wencai_stocks")
        
        try:
            res = await db.execute(text('SELECT COUNT(DISTINCT code) FROM stock_daily'))
            print('Daily Score Distinct Codes:', res.scalar())
        except:
            print("Error counting stock_daily")
        
        print('\n--- Top 5 Daily Scores ---')
        try:
            res = await db.execute(text('SELECT * FROM stock_daily ORDER BY daily_score DESC LIMIT 5'))
            for r in res.fetchall():
                print(r)
        except:
            print("Error fetching top scores")

if __name__ == '__main__':
    asyncio.run(check_data())
