
import asyncio
from app.database import db_manager
from app.models.tag_management import StockTagInfo
from sqlalchemy import select

async def fix_scores():
    await db_manager.initialize()
    async with db_manager.get_session() as db:
        # Define tags to update/insert
        tags_config = [
            {"name": "3倍量", "score": 20, "description": "成交量是昨天的3倍以上", "tag_type": "calculation"},
            {"name": "2倍量", "score": 10, "description": "成交量是昨天的2倍以上", "tag_type": "calculation"},
            {"name": "5日地量", "score": 2, "description": "成交量创5日新低", "tag_type": "calculation"},
            {"name": "10日地量", "score": 3, "description": "成交量创10日新低", "tag_type": "calculation"},
            {"name": "20日地量", "score": 5, "description": "成交量创20日新低", "tag_type": "calculation"},
            {"name": "30日地量", "score": 8, "description": "成交量创30日新低", "tag_type": "calculation"},
            {"name": "60日地量", "score": 10, "description": "成交量创60日新低", "tag_type": "calculation"},
        ]

        for config in tags_config:
            # Check if exists
            query = select(StockTagInfo).where(StockTagInfo.name == config["name"])
            result = await db.execute(query)
            tag = result.scalar()

            if tag:
                print(f"Updating {config['name']} score from {tag.score} to {config['score']}")
                tag.score = config['score']
                # tag.description = config['description'] # Field not present in model
                tag.tag_type = config['tag_type']
            else:
                print(f"Creating {config['name']} with score {config['score']}")
                new_tag = StockTagInfo(
                    name=config['name'],
                    score=config['score'],
                    # description=config['description'], # Field not present in model
                    tag_type=config['tag_type']
                )
                db.add(new_tag)
        
        await db.commit()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(fix_scores())
