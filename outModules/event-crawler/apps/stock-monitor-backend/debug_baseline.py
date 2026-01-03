
import asyncio
from sqlalchemy import select
from app.database import db_manager
from app.models.volume_analysis import StockVolumeBaseline, VolumeAnalysisResult
from app.models.stock_daily import StockDaily

async def check_data():
    await db_manager.initialize()
    async with db_manager.session_factory() as session:
        code = "600724.SH"
        
        # Check Baseline
        stmt = select(StockVolumeBaseline).where(StockVolumeBaseline.code == code)
        result = await session.execute(stmt)
        baseline = result.scalars().first()
        
        print(f"=== Baseline for {code} ===")
        if baseline:
            print(f"ID: {baseline.id}")
            print(f"Last 3x Date: {baseline.last_3x_date}, Close: {baseline.last_3x_close}")
            print(f"Last 2x Date: {baseline.last_2x_date}, Close: {baseline.last_2x_close}")
            print(f"Last 60d Low Vol Date: {baseline.last_60d_low_vol_date}, Vol: {baseline.last_60d_low_vol}")
            # Print all fields
            for key, value in baseline.__dict__.items():
                if not key.startswith('_'):
                    print(f"{key}: {value}")
        else:
            print("No baseline record found.")

        # Check Analysis Results (Anomalies)
        stmt = select(VolumeAnalysisResult).where(VolumeAnalysisResult.code == code).order_by(VolumeAnalysisResult.trade_date.desc()).limit(10)
        result = await session.execute(stmt)
        anomalies = result.scalars().all()
        
        print(f"\n=== Recent Anomalies for {code} (Top 10) ===")
        for a in anomalies:
            print(f"Date: {a.trade_date}, Type: {a.analysis_type}, Desc: {a.description}")

        # Check Daily Data Count
        stmt = select(StockDaily).where(StockDaily.code == code).order_by(StockDaily.trade_date.desc()).limit(5)
        result = await session.execute(stmt)
        daily = result.scalars().all()
        print(f"\n=== Recent Daily Data for {code} ===")
        for d in daily:
            print(f"Date: {d.trade_date}, Vol: {d.vol}, Close: {d.close}")

if __name__ == "__main__":
    asyncio.run(check_data())
