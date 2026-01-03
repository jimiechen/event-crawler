import asyncio
import sys
from sqlalchemy import text
from app.database import db_manager
from app.models.stock import StockInfo

async def analyze_batches():
    # 确保数据库已初始化
    await db_manager.initialize()
    async with db_manager.get_session() as session:
        print("\n=== 2025-12-27 StockInfo (Wencai) -> Batch ID Distribution ===")
        # Find which batch these stocks belong to
        # StockInfo(code) <-> WencaiStocks(stock_code) -> crawl_batch_id
        stmt = text("""
            SELECT 
                ws.crawl_batch_id,
                count(*) as stock_count
            FROM stock_info s
            JOIN wencai_stocks ws ON s.code = ws.stock_code
            WHERE DATE(s.created_at) = '2025-12-27' 
              AND s.source = 'wencai'
            GROUP BY ws.crawl_batch_id
            ORDER BY stock_count DESC
        """)
        result = await session.execute(stmt)
        
        batch_counts = result.fetchall()
        for row in batch_counts:
            bid = row.crawl_batch_id
            count = row.stock_count
            print(f"Batch ID: {bid}, Count: {count}")
            
            if bid:
                # Get batch details
                b_stmt = text("SELECT * FROM wencai_crawl_batches WHERE id = :id")
                b_res = await session.execute(b_stmt, {'id': bid})
                b_info = b_res.fetchone()
                if b_info:
                    print(f"  Name: {b_info.batch_name}")
                    print(f"  Query: {b_info.query_condition}") # using query_condition based on schema
                    print(f"  Created By: {b_info.created_by}")

        print("\n=== End of Analysis ===")

        
        print("\n=== Market 为 unknown 的股票 (前20个) ===")
        stmt = text("""
            SELECT code, name 
            FROM stock_info 
            WHERE source='wencai' AND market='unknown'
            LIMIT 20
        """)
        result = await session.execute(stmt)
        for row in result:
            print(f"Code: {row.code}, Name: {row.name}")

        print("\n=== WencaiStocks 表批次分布 (Top 10) ===")
        stmt = text("""
            SELECT 
                ws.crawl_batch_id, 
                count(*) as count,
                b.batch_name,
                b.started_at
            FROM wencai_stocks ws
            LEFT JOIN wencai_crawl_batches b ON ws.crawl_batch_id = b.id
            GROUP BY ws.crawl_batch_id 
            ORDER BY count DESC
            LIMIT 10
        """)
        result = await session.execute(stmt)
        for row in result:
            print(f"Batch ID: {row.crawl_batch_id}, Count: {row.count}, Name: {row.batch_name}, Started: {row.started_at}")
            
        print("\n=== 2025-12-27 新增股票的批次来源 ===")
        stmt = text("""
            SELECT 
                ws.crawl_batch_id, 
                b.batch_name,
                b.started_at,
                count(*) as count
            FROM stock_info si 
            JOIN wencai_stocks ws ON si.code = ws.stock_code
            LEFT JOIN wencai_crawl_batches b ON ws.crawl_batch_id = b.id
            WHERE DATE(si.created_at) = '2025-12-27'
            GROUP BY ws.crawl_batch_id, b.batch_name, b.started_at
            ORDER BY count DESC
        """)
        result = await session.execute(stmt)
        for row in result:
            print(f"Batch ID: {row.crawl_batch_id}, Count: {row.count}, Name: {row.batch_name}, Started: {row.started_at}")
            
        print("\n=== 2025-12-27 新增股票中没有对应 WencaiStocks 的数量 ===")
        stmt = text("""
            SELECT count(*) 
            FROM stock_info si 
            LEFT JOIN wencai_stocks ws ON si.code = ws.stock_code
            WHERE DATE(si.created_at) = '2025-12-27' AND si.source='wencai' AND ws.id IS NULL
        """)
        count = (await session.execute(stmt)).scalar()
        print(f"Orphaned 'wencai' stocks count: {count}")

        print("\n=== StockInfo 问财来源统计 ===")
        # 统计 source='wencai' 的股票数量
        stmt = text("SELECT count(*) FROM stock_info WHERE source='wencai'")
        count = (await session.execute(stmt)).scalar()
        print(f"Total 'wencai' stocks: {count}")
        
        # 统计 source='wencai' 的股票的创建时间分布
        print("\n=== 创建时间分布 (Top 10) ===")
        stmt = text("""
            SELECT DATE_FORMAT(created_at, '%Y-%m-%d %H') as hour_group, count(*) 
            FROM stock_info 
            WHERE source='wencai' 
            GROUP BY hour_group 
            ORDER BY hour_group DESC
            LIMIT 10
        """)
        result = await session.execute(stmt)
        for row in result:
            print(f"Time: {row[0]}, Count: {row[1]}")

        print("\n=== 市场分布 ===")
        stmt = text("""
            SELECT market, count(*) 
            FROM stock_info 
            WHERE source='wencai' 
            GROUP BY market
        """)
        result = await session.execute(stmt)
        for row in result:
            print(f"Market: {row[0]}, Count: {row[1]}")

if __name__ == "__main__":
    asyncio.run(analyze_batches())
