from typing import List, Optional, Tuple, Dict, Any
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag_management import StockTagInfo, StockTagRelation, OperationLog
from app.repositories.tag_repository import TagRepository
from app.api.tag_schemas import TagCreate, TagUpdate

class TagManagementService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = TagRepository(session)

    async def get_tags(self, page: int, page_size: int, name: Optional[str] = None, date_filter: Optional[str] = None, tag_type: Optional[str] = None) -> Tuple[List[StockTagInfo], int]:
        tags, total = await self.repository.get_tags_by_page(page, page_size, name, date_filter, tag_type)
        
        # Populate stocks
        tag_ids = [tag.id for tag in tags]
        stocks_map = await self.repository.get_stocks_for_tags(tag_ids)
        
        # Get latest prices
        all_codes = set()
        for stock_list in stocks_map.values():
            for s in stock_list:
                all_codes.add(s['code'])
                
        prices = await self.repository.get_latest_prices(list(all_codes))
        
        for tag in tags:
            # Attach transient attribute for Pydantic serialization
            tag_stocks = stocks_map.get(tag.id, [])
            for s in tag_stocks:
                s['daily_change'] = prices.get(s['code'])
            tag.stocks = tag_stocks
            
        return tags, total

    async def get_tag_stocks_paginated(self, tag_id: int, page: int, page_size: int) -> Tuple[List[Dict[str, Any]], int]:
        stocks, total = await self.repository.get_tag_stocks_paginated(tag_id, page, page_size)
        
        # Get prices
        codes = [s['code'] for s in stocks]
        prices = await self.repository.get_latest_prices(codes)
        
        for s in stocks:
            s['daily_change'] = prices.get(s['code'])
            
        return stocks, total

    async def create_tag(self, tag_data: TagCreate, operator: str = "system") -> StockTagInfo:
        existing = await self.repository.get_by_name(tag_data.name)
        if existing:
            raise ValueError(f"Tag with name '{tag_data.name}' already exists")

        tag = await self.repository.create(tag_data)
        
        # Log
        await self.log_operation(operator, "create", "tag", str(tag.id), 
                               {"name": tag.name, "score": float(tag.score)})
        
        return tag

    async def update_tag(self, tag_id: int, tag_data: TagUpdate, operator: str = "system") -> Optional[StockTagInfo]:
        tag = await self.repository.get(tag_id)
        if not tag or tag.is_deleted:
            return None
        
        old_data = {"name": tag.name, "score": float(tag.score)}
        
        if tag_data.name and tag_data.name != tag.name:
            existing = await self.repository.get_by_name(tag_data.name)
            if existing:
                raise ValueError(f"Tag with name '{tag_data.name}' already exists")
            
        updated_tag = await self.repository.update(tag_id, tag_data)
        
        # Log
        if updated_tag:
            await self.log_operation(operator, "update", "tag", str(updated_tag.id), 
                                   {"before": old_data, "after": {"name": updated_tag.name, "score": float(updated_tag.score)}})
        
        return updated_tag

    async def delete_tag(self, tag_id: int, operator: str = "system") -> bool:
        tag = await self.repository.get(tag_id)
        if not tag:
            return False
            
        success = await self.repository.soft_delete(tag_id)
        if success:
             await self.log_operation(operator, "delete", "tag", str(tag_id), {"name": tag.name})
        return success

    async def batch_import_tags(self, tags_data: List[TagCreate], operator: str = "system") -> Dict[str, int]:
        success_count = 0
        failed_count = 0
        
        for data in tags_data:
            try:
                # Basic check, not efficient for huge batch but safe
                existing = await self.repository.get_by_name(data.name)
                if not existing:
                    await self.repository.create(data)
                    success_count += 1
                else:
                    failed_count += 1
            except Exception:
                failed_count += 1
        
        await self.log_operation(operator, "batch_import", "tag", "batch", 
                               {"success": success_count, "failed": failed_count})
        
        return {"success": success_count, "failed": failed_count}

    async def add_tags_to_stock(self, stock_code: str, tags: List[TagCreate], operator: str = "system") -> Dict[str, Any]:
        """
        批量给股票添加标签
        """
        processed_tags = []
        new_relations = []
        
        # Get existing tags for this stock to avoid duplicates
        existing_tags = await self.repository.get_tags_by_stock(stock_code)
        existing_tag_ids = {t[0].id for t in existing_tags}
        
        for tag_data in tags:
            # Check if tag exists or create
            tag = await self.repository.get_by_name(tag_data.name)
            if not tag:
                tag = await self.create_tag(tag_data, operator=operator)
            
            processed_tags.append(tag)
            
            if tag.id not in existing_tag_ids:
                new_relations.append(StockTagRelation(stock_code=stock_code, tag_id=tag.id))
                # Add to existing_tag_ids to handle duplicates within the input list
                existing_tag_ids.add(tag.id)
                
        if new_relations:
            await self.repository.add_relations(new_relations)
            await self.log_operation(operator, "batch_associate", "relation", stock_code, 
                                   {"tags": [t.name for t in processed_tags]})
                                   
        # Return updated tags and score
        return await self.get_stock_tags(stock_code)

    async def associate_stocks(self, tag_id: int, stock_codes: List[str], operator: str = "system"):
        tag = await self.repository.get(tag_id)
        if not tag:
            raise ValueError("Tag not found")
            
        # Get existing relations to avoid unique constraint error
        # In a real high-concurrency scenario, this check-then-insert is not atomic, 
        # but for this requirement it's likely sufficient or handle exception.
        # Efficient way: fetch existing for this tag and filter.
        existing_stocks = await self.repository.get_stocks_by_tag(tag_id)
        existing_set = set(existing_stocks)
        
        new_relations = []
        for code in stock_codes:
            if code not in existing_set:
                new_relations.append(StockTagRelation(stock_code=code, tag_id=tag_id))
        
        if new_relations:
            await self.repository.add_relations(new_relations)
            await self.log_operation(operator, "associate", "relation", str(tag_id), 
                                   {"stocks": [r.stock_code for r in new_relations]})

    async def dissociate_stocks(self, tag_id: int, stock_codes: List[str], operator: str = "system"):
        await self.repository.remove_relations(tag_id, stock_codes)
        await self.log_operation(operator, "dissociate", "relation", str(tag_id), 
                               {"stocks": stock_codes})

    async def get_stock_tags(self, stock_code: str) -> Dict[str, Any]:
        tags_data = await self.repository.get_tags_by_stock(stock_code)
        total_score = sum([t[0].score for t in tags_data])
        
        # Fetch StockInfo for stock pool time
        from app.models.stock import StockInfo
        from sqlalchemy import select
        
        stmt = select(StockInfo).where(StockInfo.code == stock_code)
        result = await self.session.execute(stmt)
        stock_info = result.scalars().first()
        
        stock_pool_time = None
        if stock_info:
             stock_pool_time = stock_info.created_at
        
        # Convert to dict for serialization
        tag_list = []
        for t, relation_created_at in tags_data:
            tag_dict = {
                "id": t.id,
                "name": t.name,
                "score": float(t.score),
                "tag_type": t.tag_type,
                "is_deleted": t.is_deleted,
                "created_at": t.created_at,
                "updated_at": t.updated_at,
                "relation_created_at": relation_created_at,
                "stocks": []
            }
            tag_list.append(tag_dict)
            
        return {
            "stock_code": stock_code,
            "tags": tag_list,
            "total_score": float(total_score),
            "stock_pool_time": stock_pool_time
        }

    async def get_all_tag_stocks(self, tag_id: int) -> List[str]:
        return await self.repository.get_stocks_by_tag(tag_id)
        
    async def log_operation(self, operator: str, action: str, target_type: str, target_id: str, details: Dict):
        log = OperationLog(
            operator=operator,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details
        )
        await self.repository.add_log(log)

    async def get_logs(self, page: int, page_size: int) -> Tuple[List[OperationLog], int]:
        return await self.repository.get_logs(page, page_size)
