import asyncio
import json
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load env
load_dotenv()

async def check_keys():
    # Database connection
    db_user = os.getenv("DB_USER", "root")
    db_pass = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_DATABASE", "stock_monitor")
    
    db_url = f"mysql+aiomysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Query rule_scores
        stmt = text("SELECT rule_scores FROM stock_score_result WHERE rule_scores IS NOT NULL LIMIT 100")
        result = await session.execute(stmt)
        rows = result.fetchall()
        
        all_keys = set()
        sample_data = {}
        
        for row in rows:
            rule_scores_json = row[0]
            if not rule_scores_json:
                continue
                
            try:
                if isinstance(rule_scores_json, str):
                    scores = json.loads(rule_scores_json)
                else:
                    scores = rule_scores_json # Already dict if driver handles it
                
                if isinstance(scores, dict):
                    for k in scores.keys():
                        all_keys.add(k)
                        if k not in sample_data:
                             sample_data[k] = scores[k]
            except Exception as e:
                print(f"Error parsing: {e}")
                
        print("Found Keys:", sorted(list(all_keys)))
        print("Sample Data:", sample_data)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_keys())
