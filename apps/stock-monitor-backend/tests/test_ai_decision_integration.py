import asyncio
import sys
import os
import logging

# Add project root to path
# File is in scripts/tests/test_ai_decision_integration.py
# We need to go up 3 levels to reach apps/stock-monitor-backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import DatabaseManager
from app.services.ai_decision_service import AIDecisionService, AIDecisionConfig
from app.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_integration():
    # 1. Initialize Database
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    # 2. Initialize Service
    config = AIDecisionConfig(
        api_key="mock_key",
        base_url="https://api.deepseek.com", # Example
        model="deepseek-chat"
    )
    service = AIDecisionService(config)
    
    logger.info("Service initialized. Testing context generation...")
    
    async with db_manager.session_factory() as session:
        # Use a common stock code
        stock_code = "600519" 
        
        # 3. Test Context Generation
        # This will trigger:
        # - ArenaAdapter.get_prompt_template (if we pass None, but prepare_decision_context expects text)
        # - AShareAdapter.get_stock_context
        # - ArenaAdapter.get_signal_pool_signals
        
        # First fetch template manually to pass it
        template_text = await service.arena_adapter.get_prompt_template("ashare_default_v1")
        if not template_text:
            logger.warning("Could not fetch template from Arena. Using default.")
            template_text = "Mock Template with {stock_code}"
        else:
            logger.info("Successfully fetched template from Arena.")
            
        context = await service.prepare_decision_context(session, stock_code, template_text)
        
        logger.info("Context generated successfully.")
        logger.info(f"Stock Name: {context.get('stock_code')}") # context keys might differ based on template logic
        logger.info(f"Market Prices: {context.get('market_prices')}")
        logger.info(f"Trigger Context: {context.get('trigger_context')}")
        
        # Verify if Arena signals were fetched and matched
        # We expect 'trigger_context' to contain matching signals or raw tags
        
        print("\n=== Context Dump ===")
        for k, v in context.items():
            if k != "news_section": # Skip long text
                print(f"{k}: {v}")
                
if __name__ == "__main__":
    asyncio.run(test_integration())
