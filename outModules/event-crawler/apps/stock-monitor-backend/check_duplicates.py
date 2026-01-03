import asyncio
from sqlalchemy import select, func, text
from app.database import db_manager
from app.models.stock_daily import StockDaily

async def main():
    await db_manager.initialize()
    
    code = "002735"
    
    async with db_manager.get_session() as session:
        # Check for duplicates on date
        stmt = select(StockDaily.trade_date, func.count(StockDaily.id)).where(
            StockDaily.code == code
        ).group_by(StockDaily.trade_date).having(func.count(StockDaily.id) > 1)
        
        result = await session.execute(stmt)
        duplicates = result.all()
        
        if duplicates:
            print(f"Found {len(duplicates)} duplicate dates:")
            for d in duplicates:
                print(d)
                
                # Show the duplicate records
                stmt_recs = select(StockDaily).where(
                    StockDaily.code == code,
                    StockDaily.trade_date == d[0]
                )
                recs = (await session.execute(stmt_recs)).scalars().all()
                for r in recs:
                    print(f"  ID={r.id}, Date={r.trade_date}, Close={r.close}, Adj={r.adj_factor}")
        else:
            print("No duplicates found.")

        # Check the latest record specifically
        stmt_latest = select(StockDaily).where(StockDaily.code == code).order_by(StockDaily.trade_date.desc()).limit(5)
        latest_recs = (await session.execute(stmt_latest)).scalars().all()
        print("\nLatest 5 records:")
        for r in latest_recs:
            print(f"  ID={r.id}, Date={r.trade_date}, Close={r.close}, Adj={r.adj_factor}")

if __name__ == "__main__":
    asyncio.run(main())
