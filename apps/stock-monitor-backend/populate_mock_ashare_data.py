#!/usr/bin/env python3
import sys
import os
import asyncio
from datetime import datetime, timedelta
import random
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add app directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import Settings

settings = Settings()

# DB Config
# Use settings but allow env var override for password if needed
DB_PASSWORD = os.getenv("DB_PASSWORD", settings.db_password)
DB_URL = f"mysql+aiomysql://{settings.db_user}:{DB_PASSWORD}@{settings.db_host}:{settings.db_port}/{settings.db_database}"

async def get_engine():
    return create_async_engine(DB_URL, echo=False)

async def populate_data():
    try:
        engine = await get_engine()
        
        async with engine.begin() as conn:
            print("Populating Mock A-Share Data...")
            
            # 1. Stocks
            stocks = [
                ("000001", "平安银行", "sz"),
                ("600519", "贵州茅台", "sh"),
                ("300750", "宁德时代", "sz"),
                ("601988", "中国银行", "sh")
            ]
            
            for code, name, market in stocks:
                # Check if exists
                res = await conn.execute(text("SELECT id FROM stock_info WHERE code = :code"), {"code": code})
                if not res.fetchone():
                    await conn.execute(text("""
                        INSERT INTO stock_info (code, name, market, is_active, created_at, updated_at)
                        VALUES (:code, :name, :market, 1, NOW(), NOW())
                    """), {"code": code, "name": name, "market": market})
                    print(f"Added stock {name} ({code})")

            # 2. Daily Data (Last 30 days)
            today = datetime.now().date()
            for code, _, _ in stocks:
                base_price = 100.0 if code == "600519" else 10.0
                
                for i in range(30):
                    date_val = today - timedelta(days=i)
                    # Skip weekends
                    if date_val.weekday() >= 5:
                        continue
                    
                    # Check if exists
                    res = await conn.execute(text("""
                        SELECT id FROM stock_prices 
                        WHERE symbol = :code AND trade_date = :date
                    """), {"code": code, "date": date_val})
                    
                    if not res.fetchone():
                        open_p = base_price * (1 + random.uniform(-0.02, 0.02))
                        close_p = open_p * (1 + random.uniform(-0.03, 0.03))
                        high_p = max(open_p, close_p) * (1 + random.uniform(0, 0.01))
                        low_p = min(open_p, close_p) * (1 - random.uniform(0, 0.01))
                        vol = int(random.uniform(10000, 1000000))
                        amt = vol * float(close_p)
                        
                        await conn.execute(text("""
                            INSERT INTO stock_prices (
                                symbol, trade_date, open_price, high_price, low_price, close_price, 
                                volume, amount, change_rate, request_timestamp, created_at
                            ) VALUES (
                                :code, :date, :open, :high, :low, :close, 
                                :vol, :amt, :chg, NOW(), NOW()
                            )
                        """), {
                            "code": code,
                            "date": date_val,
                            "open": open_p,
                            "high": high_p,
                            "low": low_p,
                            "close": close_p,
                            "vol": vol,
                            "amt": amt,
                            "chg": (close_p - open_p) / open_p * 100
                        })
                        
            print("Added daily K-line data.")
            
            # 3. Tags
            tags = [
                ("3倍量", "calculation", 5.0),
                ("平台突破", "calculation", 8.0),
                ("60日地量", "calculation", 3.0)
            ]
            
            tag_ids = {}
            for name, ttype, score in tags:
                res = await conn.execute(text("SELECT id FROM stock_tags_info WHERE name = :name"), {"name": name})
                row = res.fetchone()
                if row:
                    tag_ids[name] = row.id
                else:
                    await conn.execute(text("""
                        INSERT INTO stock_tags_info (name, tag_type, score, created_at, updated_at)
                        VALUES (:name, :type, :score, NOW(), NOW())
                    """), {"name": name, "type": ttype, "score": score})
                    
                    # Get ID
                    res = await conn.execute(text("SELECT LAST_INSERT_ID()"))
                    tag_ids[name] = res.scalar()
                    print(f"Added tag {name}")
                    
            # 4. Tag Relations (Signals for today)
            # Assign random tags to random stocks for today
            for code, _, _ in stocks:
                if random.random() > 0.5: # 50% chance
                    tag_name = random.choice(list(tag_ids.keys()))
                    tag_id = tag_ids[tag_name]
                    
                    # Check if exists
                    res = await conn.execute(text("""
                        SELECT id FROM stock_tag_relations 
                        WHERE stock_code = :code AND tag_id = :tid
                    """), {"code": code, "tid": tag_id})
                    
                    if not res.fetchone():
                        await conn.execute(text("""
                            INSERT INTO stock_tag_relations (stock_code, tag_id, created_at)
                            VALUES (:code, :tid, NOW())
                        """), {"code": code, "tid": tag_id})
                        print(f"Added signal {tag_name} for {code}")
                        
            print("Data population complete.")
    except Exception as e:
        print(f"Error populating data: {e}")

if __name__ == "__main__":
    asyncio.run(populate_data())
