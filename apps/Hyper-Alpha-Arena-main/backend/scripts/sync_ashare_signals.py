import sys
import os
import json
from sqlalchemy import create_engine, text

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import DATABASE_URL

# Standard A-Share Signals (Tags)
ASHARE_SIGNALS = [
    {
        "name": "Volume_Spike",
        "description": "成交量显著放大 (Volume > 2 * MA5_Volume)",
        "trigger_condition": json.dumps({"source": "ashare_quant", "tag": "volume_spike", "threshold": 2.0})
    },
    {
        "name": "Price_Breakout",
        "description": "股价突破20日均线",
        "trigger_condition": json.dumps({"source": "ashare_quant", "tag": "price_breakout", "ma_period": 20})
    },
    {
        "name": "MACD_Golden_Cross",
        "description": "MACD金叉 (DIF crosses above DEA)",
        "trigger_condition": json.dumps({"source": "ashare_quant", "tag": "macd_gold"})
    },
    {
        "name": "RSI_Oversold",
        "description": "RSI超卖 (RSI < 30)",
        "trigger_condition": json.dumps({"source": "ashare_quant", "tag": "rsi_oversold", "threshold": 30})
    },
    {
        "name": "Main_Fund_Inflow",
        "description": "主力资金净流入",
        "trigger_condition": json.dumps({"source": "ashare_quant", "tag": "main_fund_inflow"})
    }
]

def sync_signals():
    print("Starting A-Share signal synchronization...")
    
    # Use the same DB connection as the app
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # 1. Sync Signals
        signal_ids = []
        for sig in ASHARE_SIGNALS:
            # Check if exists
            result = conn.execute(
                text("SELECT id FROM signal_definitions WHERE signal_name = :name"),
                {"name": sig["name"]}
            )
            row = result.fetchone()
            
            if row:
                print(f"Updating signal: {sig['name']}")
                conn.execute(
                    text("""
                        UPDATE signal_definitions 
                        SET description = :desc, trigger_condition = :cond, updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                    """),
                    {"desc": sig["description"], "cond": sig["trigger_condition"], "id": row[0]}
                )
                signal_ids.append(row[0])
            else:
                print(f"Creating signal: {sig['name']}")
                result = conn.execute(
                    text("""
                        INSERT INTO signal_definitions (signal_name, description, trigger_condition, enabled)
                        VALUES (:name, :desc, :cond, true)
                        RETURNING id
                    """),
                    {"name": sig["name"], "desc": sig["description"], "cond": sig["trigger_condition"]}
                )
                new_id = result.fetchone()[0]
                signal_ids.append(new_id)
        
        # 2. Create/Update Signal Pool
        pool_name = "A-Share Basic Strategy"
        pool_signals_json = json.dumps(signal_ids)
        
        result = conn.execute(
            text("SELECT id FROM signal_pools WHERE pool_name = :name"),
            {"name": pool_name}
        )
        row = result.fetchone()
        
        if row:
            print(f"Updating signal pool: {pool_name}")
            conn.execute(
                text("""
                    UPDATE signal_pools
                    SET signal_ids = :sids, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """),
                {"sids": pool_signals_json, "id": row[0]}
            )
        else:
            print(f"Creating signal pool: {pool_name}")
            conn.execute(
                text("""
                    INSERT INTO signal_pools (pool_name, signal_ids, symbols, logic, enabled)
                    VALUES (:name, :sids, '[]', 'OR', true)
                """),
                {"name": pool_name, "sids": pool_signals_json}
            )
            
        conn.commit()
        print("Signal synchronization completed successfully.")

if __name__ == "__main__":
    sync_signals()
