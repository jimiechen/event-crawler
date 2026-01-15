#!/usr/bin/env python3
"""
Script to sync A-Share prompt templates to Arena database.
"""

import sys
import os
from sqlalchemy import text

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db

# A-Share Default Prompt Template
# Copied from stock-monitor-backend/app/config/prompt_templates.py to ensure availability
STOCK_DEFAULT_PROMPT_TEMPLATE = """You are a Chinese A-share trading AI.

=== TRADING ENVIRONMENT ===
Platform: Chinese A-Share Market (Shanghai/Shenzhen)
{trading_environment}

=== SESSION CONTEXT ===
Runtime: {runtime_minutes} minutes since trading started
Current UTC time: {current_time_utc}

=== ACCOUNT STATUS ===
Total Return: {total_return_percent}%
Available Cash: ¥{available_cash}
Account Value: ¥{total_account_value}

=== HOLDINGS ===
{holdings_detail}

=== MARKET PRICES ===
{market_prices}

=== NEWS ===
{news_section}

=== TRIGGER CONTEXT ===
{trigger_context}

=== TRADING RULES ===
- operation: "buy" (long), "sell" (short), "hold", or "close"
- target_portion_of_balance: 0.0-1.0 (portion of balance to use)
- max_price: required for "buy" operations
- min_price: required for "sell" operations
- Keep position size reasonable (≤ 20% of available cash per trade)

=== OUTPUT FORMAT ===
{output_format}
"""

SYSTEM_TEMPLATE = """You are a professional trading assistant specialized in Chinese A-Shares.
Response in JSON format only.
"""

ASHARE_PROMPTS = [
    {
        "key": "ashare_default_v1",
        "name": "A-Share Default Strategy",
        "description": "Default prompt template for A-Share day trading/swing trading decisions.",
        "template_text": STOCK_DEFAULT_PROMPT_TEMPLATE,
        "system_template_text": SYSTEM_TEMPLATE,
        "is_system": "true"
    }
]

def sync_prompts():
    """Sync prompts to database"""
    print("Starting A-Share prompt synchronization...")
    
    # Get database session
    db_gen = get_db()
    session = next(db_gen)
    
    try:
        for prompt in ASHARE_PROMPTS:
            # Check if prompt exists
            query = text("SELECT id FROM prompt_templates WHERE key = :key")
            result = session.execute(query, {"key": prompt["key"]})
            existing = result.fetchone()
            
            if existing:
                print(f"Updating prompt: {prompt['name']}")
                update_query = text("""
                    UPDATE prompt_templates 
                    SET name = :name, 
                        description = :desc, 
                        template_text = :text,
                        system_template_text = :sys_text,
                        is_system = :is_sys,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE key = :key
                """)
                session.execute(update_query, {
                    "name": prompt["name"],
                    "desc": prompt["description"],
                    "text": prompt["template_text"],
                    "sys_text": prompt["system_template_text"],
                    "is_sys": prompt["is_system"],
                    "key": prompt["key"]
                })
            else:
                print(f"Creating prompt: {prompt['name']}")
                insert_query = text("""
                    INSERT INTO prompt_templates (key, name, description, template_text, system_template_text, is_system, is_deleted, created_by)
                    VALUES (:key, :name, :desc, :text, :sys_text, :is_sys, 'false', 'system')
                """)
                session.execute(insert_query, {
                    "key": prompt["key"],
                    "name": prompt["name"],
                    "desc": prompt["description"],
                    "text": prompt["template_text"],
                    "sys_text": prompt["system_template_text"],
                    "is_sys": prompt["is_system"]
                })
        
        session.commit()
        print("Prompt synchronization completed successfully.")
    except Exception as e:
        session.rollback()
        print(f"Error syncing prompts: {e}")
        raise
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass

if __name__ == "__main__":
    sync_prompts()
