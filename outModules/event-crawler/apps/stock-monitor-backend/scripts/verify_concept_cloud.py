import asyncio
import os
import sys
from datetime import datetime, date

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import DatabaseManager
from app.services.wencai_service import WencaiService
from sqlalchemy import text

async def main():
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        service = WencaiService(session)
        
        print("--- Testing get_concept_statistics (Latest) ---")
        concepts = await service.get_concept_statistics()
        print(f"Got {len(concepts)} concepts (latest batch)")
        if concepts:
            print(f"Sample: {concepts[0]['name']} - {concepts[0]['date']}")
            
        print("\n--- Testing get_concept_statistics (Date Range) ---")
        today = date.today().strftime('%Y-%m-%d')
        concepts_today = await service.get_concept_statistics(start_date=today, end_date=today)
        print(f"Got {len(concepts_today)} concepts for today {today}")
        
        if concepts:
            target_concept = concepts[0]['name']
            print(f"\n--- Testing Hide Concept: {target_concept} ---")
            
            # Hide it
            await service.hide_concept(target_concept)
            print(f"Hidden {target_concept}")
            
            # Query again
            concepts_after = await service.get_concept_statistics()
            found = any(c['name'] == target_concept for c in concepts_after)
            print(f"Concept {target_concept} found after hiding: {found}")
            
            # Unhide it (cleanup) - need to do manual SQL or add unhide method?
            # Service doesn't have unhide, so I'll just delete from table manually for cleanup
            await session.execute(text("DELETE FROM hidden_concepts WHERE concept_name = :name"), {"name": target_concept})
            await session.commit()
            print(f"Unhidden {target_concept} (cleanup)")
            
            # Verify reappearance
            concepts_restored = await service.get_concept_statistics()
            found_restored = any(c['name'] == target_concept for c in concepts_restored)
            print(f"Concept {target_concept} found after restore: {found_restored}")

if __name__ == "__main__":
    try:
        # Use existing loop if available (for environments like Jupyter), else new one
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(main())
