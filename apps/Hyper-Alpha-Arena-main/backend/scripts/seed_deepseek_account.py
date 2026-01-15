#!/usr/bin/env python3
import sys
import os
import asyncio
from sqlalchemy import text

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_context
from database.models import Account

async def seed_deepseek():
    print("Seeding DeepSeek Account...")
    async with get_db_context() as session:
        # Get default user (assuming id 1 or first available)
        result = await session.execute(text("SELECT id FROM users ORDER BY id ASC LIMIT 1"))
        user = result.fetchone()
        
        if not user:
            print("No user found. Please run init_db or create a user first.")
            return
        
        user_id = user.id
        
        # Check if DeepSeek account exists
        result = await session.execute(text("SELECT id FROM accounts WHERE name = 'DeepSeek Trader'"))
        if result.fetchone():
            print("DeepSeek Trader account already exists.")
            return

        # Create DeepSeek Account
        # Note: API Key is a placeholder. User must update it in Settings.
        new_account = Account(
            user_id=user_id,
            name="DeepSeek Trader",
            account_type="AI",
            model="deepseek-chat", 
            base_url="https://api.deepseek.com",
            api_key="sk-placeholder", 
            initial_capital=1000000.0,
            current_cash=1000000.0,
            is_active="true",
            auto_trading_enabled="false",
            show_on_dashboard=True
        )
        session.add(new_account)
        await session.commit()
        print(f"DeepSeek Trader account created for User ID {user_id}.")

if __name__ == "__main__":
    asyncio.run(seed_deepseek())
