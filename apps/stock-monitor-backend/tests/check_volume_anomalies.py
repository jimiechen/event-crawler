
import asyncio
from sqlalchemy import select, desc
from app.database import db_manager
from app.models.volume_analysis import VolumeAnalysisResult
from app.models.stock_daily import StockDaily
import sys

# Add path to find app
import os
sys.path.append(os.getcwd())

async def check_000881_data():
    async with db_manager.get_session() as session:
        # Check VolumeAnalysisResult
        print("--- Checking VolumeAnalysisResult for 000881 ---")
        stmt = select(VolumeAnalysisResult).where(VolumeAnalysisResult.code.like("000881%")).order_by(VolumeAnalysisResult.trade_date.desc()).limit(20)
        result = await session.execute(stmt)
        anomalies = result.scalars().all()
        
        if not anomalies:
            print("No anomalies found for 000881")
        else:
            for a in anomalies:
                print(f"Date: {a.trade_date}, Type: {a.analysis_type}, Value: {a.value}")
        
        # Check total count
        stmt_count = select(VolumeAnalysisResult).where(VolumeAnalysisResult.code.like("000881%"))
        result_count = await session.execute(stmt_count)
        all_anomalies = result_count.scalars().all()
        print(f"Total anomalies count: {len(all_anomalies)}")
        
        # Calculate potential score
        total_score = 0
        for a in all_anomalies:
            if "3倍量" in a.analysis_type: total_score += 5
            elif "2倍量" in a.analysis_type: total_score += 3
            elif "地量" in a.analysis_type: total_score += 1
        
        print(f"Calculated Score from VolumeAnalysisResult: {total_score}")

if __name__ == "__main__":
    asyncio.run(check_000881_data())
