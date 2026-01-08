import asyncio
from sqlalchemy import select
from app.database import db_manager
from app.models.stock import StockData
from app.models.stock_daily import StockDaily

async def check_snapshot(code):
    print(f"--- Checking Snapshot for {code} ---")
    async with db_manager.get_session() as session:
        # Check StockData (Snapshot)
        stmt = select(StockData).where(StockData.code.like(f"%{code}%")).order_by(StockData.timestamp.desc()).limit(5)
        result = await session.execute(stmt)
        snapshots = result.scalars().all()
        if not snapshots:
            print("No snapshot data found.")
        for snap in snapshots:
            print(f"Snapshot: Date={snap.timestamp}, Price={snap.price}, Code={snap.code}")

        # Check Latest Adj Factor Logic
        print(f"--- Checking Adj Factor Logic for {code} ---")
        # Mimic controller logic
        query_code = code
        # Try exact match first
        stmt = select(StockDaily).where(StockDaily.code == query_code).limit(1)
        res = await session.execute(stmt)
        if not res.scalar():
            if code.startswith('6'): query_code = f"{code}.SH"
            else: query_code = f"{code}.SZ"
            
        print(f"Using query_code: {query_code}")
        
        stmt_factor = select(StockDaily.adj_factor).where(
            StockDaily.code == query_code, 
            StockDaily.adj_factor.is_not(None)
        ).order_by(StockDaily.trade_date.desc()).limit(1)
        res_factor = await session.execute(stmt_factor)
        latest_factor = res_factor.scalar()
        print(f"Latest Adj Factor: {latest_factor}")
        
        # Check a few daily records with QFQ calculation
        stmt = select(StockDaily).where(StockDaily.code == query_code).order_by(StockDaily.trade_date.desc()).limit(5)
        result = await session.execute(stmt)
        records = result.scalars().all()
        
        if latest_factor:
            latest_factor = float(latest_factor)
            
        for item in records:
            adj_rate = 1.0
            if item.adj_factor and latest_factor:
                adj_rate = float(item.adj_factor) / latest_factor
            
            close_price = float(item.close) * adj_rate if item.close else 0
            print(f"Date: {item.trade_date}, Raw: {item.close}, ItemAdj: {item.adj_factor}, Rate: {adj_rate:.4f}, QFQ: {close_price:.2f}")

async def main():
    await db_manager.initialize()
    await check_snapshot("002735")

if __name__ == "__main__":
    asyncio.run(main())
