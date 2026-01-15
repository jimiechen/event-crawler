from typing import Optional, Dict, List, Any
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.config.settings import settings
from loguru import logger

class ArenaAdapter:
    """
    Adapter for interacting with the Hyper-Alpha-Arena shared database.
    Used to fetch prompt templates and signal definitions/pools.
    """
    def __init__(self):
        # Use settings.arena_database_url
        self.engine = create_async_engine(settings.arena_database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def get_prompt_template(self, key: str) -> Optional[str]:
        """
        Fetch a prompt template by key from the Arena database.
        """
        async with self.async_session() as session:
            try:
                # Assuming prompt_templates table exists in the schema connected by arena_database_url
                result = await session.execute(
                    text("SELECT template_text FROM prompt_templates WHERE key = :key AND is_deleted = 'false'"),
                    {"key": key}
                )
                row = result.fetchone()
                if row:
                    return row[0]
                else:
                    logger.warning(f"Prompt template '{key}' not found in Arena DB.")
                    return None
            except Exception as e:
                logger.error(f"Failed to fetch prompt template '{key}' from Arena: {e}")
                return None

    async def get_signal_pool_signals(self, pool_name: str) -> List[Dict[str, Any]]:
        """
        Fetch all enabled signals for a given signal pool name.
        Returns a list of signal dictionaries with 'name', 'description', 'trigger_condition'.
        """
        async with self.async_session() as session:
            try:
                # 1. Get Signal IDs from Pool
                result = await session.execute(
                    text("SELECT signal_ids, logic FROM signal_pools WHERE pool_name = :name AND enabled = true"),
                    {"name": pool_name}
                )
                pool_row = result.fetchone()
                if not pool_row:
                    logger.warning(f"Signal pool '{pool_name}' not found or disabled.")
                    return []
                
                signal_ids_json = pool_row[0]
                if not signal_ids_json:
                    return []
                
                # Handle JSON string or list
                if isinstance(signal_ids_json, str):
                    signal_ids = json.loads(signal_ids_json)
                else:
                    signal_ids = signal_ids_json # Already a list if using JSONB type in sqlalchemy

                if not signal_ids:
                    return []

                # 2. Get Signal Definitions
                # Use ANY(:ids) for array matching
                query = text("""
                    SELECT id, signal_name, description, trigger_condition 
                    FROM signal_definitions 
                    WHERE id = ANY(:ids) AND enabled = true
                """)
                
                result = await session.execute(query, {"ids": signal_ids})
                
                signals = []
                for row in result:
                    trigger_cond = row[3]
                    if isinstance(trigger_cond, str):
                        try:
                            trigger_cond = json.loads(trigger_cond)
                        except:
                            trigger_cond = {}
                    
                    signals.append({
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "trigger_condition": trigger_cond
                    })
                
                return signals

            except Exception as e:
                logger.error(f"Failed to fetch signals for pool '{pool_name}' from Arena: {e}")
                return []
