import asyncio
from sqlalchemy import select, func
from app.database import db_manager
from app.models.stock_daily import StockDaily
from app.models.stock import StockData

async def check_anomaly(code):
    print(f"--- Checking Anomaly for {code} ---")
    async with db_manager.get_session() as session:
        # Check for any record with adj_factor > 10 for this code
        stmt = select(StockDaily).where(
            StockDaily.code == code,
            StockDaily.adj_factor > 10
        ).limit(5)
        result = await session.execute(stmt)
        anomalies = result.scalars().all()
        if anomalies:
            print(f"Found anomalous adj_factor for {code}:")
            for a in anomalies:
                print(f"Date: {a.trade_date}, Adj: {a.adj_factor}")
        else:
            print(f"No anomalous adj_factor (>10) found for {code}")

        # Check MAX adj_factor
        stmt = select(func.max(StockDaily.adj_factor)).where(StockDaily.code == code)
        res = await session.execute(stmt)
        max_adj = res.scalar()
        print(f"Max Adj Factor for {code}: {max_adj}")

        # Check Latest Record details
        stmt = select(StockDaily).where(StockDaily.code == code).order_by(StockDaily.trade_date.desc()).limit(1)
        res = await session.execute(stmt)
        latest = res.scalar()
        if latest:
            print(f"Latest Record: Date={latest.trade_date}, Code={latest.code}, Close={latest.close}, Adj={latest.adj_factor}")

async def main():
    await db_manager.initialize()
    await check_anomaly("002735")

if __name__ == "__main__":
    asyncio.run(main())
