import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from sqlalchemy import text
from database.connection import get_db
from database.models import PromptTemplate

# Prompt Templates Data
PROMPTS = [
    {
        "key": "ashare_daily_review",
        "name": "A-Share Daily Review & Decision",
        "description": "Standard prompt for A-Share daily market review and trading decisions",
        "is_system": "true",
        "template_text": """You are a Chinese A-share trading AI.

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
""",
        "system_template_text": """Respond with ONLY a JSON object using this schema:
{
  "decisions": [
    {
      "operation": "buy" | "sell" | "hold" | "close",
      "stock_code": "<6-digit stock code>",
      "stock_name": "<stock name>",
      "target_portion_of_balance": <float 0.0-1.0>,
      "max_price": <number, required for "buy" operations>,
      "min_price": <number, required for "sell" operations>,
      "reason": "<string explaining primary signals>",
      "trading_strategy": "<string covering thesis, risk controls, and exit plan>"
    }
  ]
}

CRITICAL OUTPUT REQUIREMENTS:
- Output MUST be a single, valid JSON object only
- NO markdown code blocks (no ```json``` wrappers)
- NO explanatory text before or after JSON

Example output:
{
  "decisions": [
    {
      "operation": "buy",
      "stock_code": "600519",
      "stock_name": "贵州茅台",
      "target_portion_of_balance": 0.2,
      "max_price": 1850.00,
      "reason": "底分型形态确认，RSI 超卖反弹",
      "trading_strategy": "在 1800-1850 区间建仓，止损 1750，目标 1950"
    }
  ]
}
"""
    }
]

def insert_prompts():
    """Insert or update prompt templates"""
    print("Starting A-Share prompt templates insertion...")
    
    db_gen = get_db()
    session = next(db_gen)
    
    try:
        for prompt_data in PROMPTS:
            # Check if exists by key
            existing = session.query(PromptTemplate).filter(PromptTemplate.key == prompt_data["key"]).first()
            
            if existing:
                print(f"Updating prompt: {prompt_data['name']}")
                existing.name = prompt_data["name"]
                existing.description = prompt_data["description"]
                existing.template_text = prompt_data["template_text"]
                existing.system_template_text = prompt_data["system_template_text"]
                existing.is_system = prompt_data["is_system"]
            else:
                print(f"Creating prompt: {prompt_data['name']}")
                new_prompt = PromptTemplate(
                    key=prompt_data["key"],
                    name=prompt_data["name"],
                    description=prompt_data["description"],
                    template_text=prompt_data["template_text"],
                    system_template_text=prompt_data["system_template_text"],
                    is_system=prompt_data["is_system"],
                    is_deleted="false",
                    created_by="system"
                )
                session.add(new_prompt)
        
        session.commit()
        print("Prompt templates insertion completed successfully.")
        
    except Exception as e:
        session.rollback()
        print(f"Error inserting prompts: {e}")
        # raise # Don't raise to allow script to "finish" even if DB is down (for now, or maybe I should raise)
        raise
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass

if __name__ == "__main__":
    insert_prompts()
