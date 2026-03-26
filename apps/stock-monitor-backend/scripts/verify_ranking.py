import sys
import os
import asyncio
from datetime import date, timedelta

# Add path
sys.path.append("/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend")

from app.database import db_manager
from app.services.ranking_service import RankingService

async def main():
    await db_manager.initialize()
    async with db_manager.get_session() as session:
        service = RankingService(session)
        
        # Test Dates
        dates = [date(2025, 11, 27), date(2025, 11, 28), date(2025, 11, 29)]
        
        print("\n=== Growth Ranking (Single Day) ===")
        for d in dates:
            print(f"\nDate: {d}")
            try:
                # Growth for single day
                ranking = await service.get_score_growth_ranking(d, d, limit=3)
                if not ranking:
                    print("  No data found.")
                for item in ranking:
                    print(f"  {item['code']} {item['name']}: {item['growth']}")
            except Exception as e:
                print(f"  Error: {e}")

        print("\n=== Total Ranking (250 Days) ===")
        for d in dates:
            print(f"\nDate: {d}")
            try:
                ranking = await service.get_total_score_ranking(d, limit=3)
                if not ranking:
                    print("  No data found.")
                for item in ranking:
                    # Note: Key changed to 'score' in my fix
                    score = item.get('score')
                    print(f"  {item['code']} {item['name']}: {score}")
            except Exception as e:
                print(f"  Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
