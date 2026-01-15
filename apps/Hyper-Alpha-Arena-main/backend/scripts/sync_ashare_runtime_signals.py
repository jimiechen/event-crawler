#!/usr/bin/env python3
import sys
import os
import time
from datetime import datetime
from sqlalchemy import text, create_engine

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db

# A-Share DB Config
ASHARE_DB_HOST = os.getenv("ASHARE_DB_HOST", "localhost") 
ASHARE_DB_PORT = os.getenv("ASHARE_DB_PORT", "3306")
ASHARE_DB_USER = os.getenv("ASHARE_DB_USER", "stock_user") 
ASHARE_DB_PASSWORD = os.getenv("ASHARE_DB_PASSWORD", "Stock@2024")
ASHARE_DB_NAME = os.getenv("ASHARE_DB_NAME", "stock_monitor")

# Sync MySQL connection
ASHARE_DATABASE_URL = f"mysql+pymysql://{ASHARE_DB_USER}:{ASHARE_DB_PASSWORD}@{ASHARE_DB_HOST}:{ASHARE_DB_PORT}/{ASHARE_DB_NAME}"

def get_ashare_engine():
    return create_engine(ASHARE_DATABASE_URL, echo=False)

def sync_runtime_signals():
    print(f"Starting A-Share runtime signal sync from {ASHARE_DB_HOST}/{ASHARE_DB_NAME}...")
    
    # 1. Get Arena DB Context (Sync)
    db_gen = get_db()
    arena_session = next(db_gen)
    
    ashare_engine = None
    
    try:
        # Load signal definitions
        signal_map = {} # name -> id
        result = arena_session.execute(text("SELECT id, signal_name FROM signal_definitions"))
        for row in result:
            signal_map[row.signal_name] = row.id
            
        print(f"Loaded {len(signal_map)} signal definitions from Arena.")

        if not signal_map:
            print("No signal definitions found in Arena. Please run sync_ashare_signals.py first.")
            return

        # 2. Connect to A-Share DB and Fetch Today's Tags
        ashare_engine = get_ashare_engine()
        rows = []
        try:
            with ashare_engine.connect() as ashare_conn:
                # Query tags created today
                query = text("""
                    SELECT 
                        r.stock_code, 
                        t.name as tag_name, 
                        r.created_at,
                        t.score
                    FROM stock_tag_relations r
                    JOIN stock_tags_info t ON r.tag_id = t.id
                    WHERE DATE(r.created_at) = CURDATE()
                """)
                
                result = ashare_conn.execute(query)
                rows = result.fetchall()
        except Exception as e:
            print(f"Error fetching from A-Share DB: {e}")
            print("Check if A-Share DB is running and accessible.")
            # Don't raise, just exit or continue empty
        
        print(f"Fetched {len(rows)} tags from A-Share DB for today.")
        
        synced_count = 0
        
        for row in rows:
            stock_code = row.stock_code
            tag_name = row.tag_name
            triggered_at = row.created_at
            score = row.score
            
            if tag_name not in signal_map:
                continue
                
            signal_id = signal_map[tag_name]
            
            # Deduplicate
            check_query = text("""
                SELECT id FROM signal_trigger_logs 
                WHERE signal_id = :sid 
                AND symbol = :symbol 
                AND DATE(triggered_at) = DATE(:date)
            """)
            existing = arena_session.execute(check_query, {
                "sid": signal_id,
                "symbol": stock_code,
                "date": triggered_at
            }).fetchone()
            
            if not existing:
                # Insert
                insert_query = text("""
                    INSERT INTO signal_trigger_logs 
                    (signal_id, symbol, market, triggered_at, metadata, created_at)
                    VALUES 
                    (:sid, :symbol, 'ASHARE', :triggered_at, :meta, CURRENT_TIMESTAMP)
                """)
                # Store score in metadata
                meta = f'{{"score": {score}}}' if score else '{}'
                
                arena_session.execute(insert_query, {
                    "sid": signal_id,
                    "symbol": stock_code,
                    "triggered_at": triggered_at,
                    "meta": meta
                })
                synced_count += 1
        
        arena_session.commit()
        print(f"Successfully synced {synced_count} new signals to Arena.")

    except Exception as e:
        arena_session.rollback()
        print(f"Error syncing runtime signals: {e}")
        raise
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass
        if ashare_engine:
            ashare_engine.dispose()

if __name__ == "__main__":
    sync_runtime_signals()
