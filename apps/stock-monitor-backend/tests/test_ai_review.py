
import asyncio
import sys
import os
from loguru import logger
from sqlalchemy import select

# Add path to import app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(current_dir)
sys.path.append(backend_root)

from app.database import db_manager
from app.services.ai_decision_service import AIDecisionService, AIDecisionConfig
from app.config.settings import get_settings
from app.models.pattern_config import PatternStockPool

async def test_ai_review():
    settings = get_settings()
    logger.info(f"Testing AI Review with API Key present: {bool(settings.deepseek_api_key)}")
    
    if not settings.deepseek_api_key:
        logger.warning("No DeepSeek API Key found in .env or environment variables.")
        # We can still test the flow if we mock the response, but for now let's just exit or warn
        # Or maybe we can temporarily mock it for testing structure
    
    async with db_manager.get_session() as session:
        # 1. Get a target stock
        stmt = select(PatternStockPool).limit(1)
        result = await session.execute(stmt)
        stock = result.scalar_one_or_none()
        
        target_code = stock.stock_code if stock else "000001"
        logger.info(f"Target stock: {target_code}")

        # 2. Init Service
        config = AIDecisionConfig(
            api_key=settings.deepseek_api_key or "mock_key",
            base_url=settings.deepseek_base_url,
            model=settings.deepseek_model
        )
        ai_service = AIDecisionService(config)
        
        # 3. Analyze
        try:
            logger.info(f"Generating decision for {target_code}...")
            result = await ai_service.generate_decision(session, target_code)
            logger.info("Decision generated successfully!")
            print("Decision Result:")
            print(result)
        except Exception as e:
            logger.error(f"Generation failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai_review())
