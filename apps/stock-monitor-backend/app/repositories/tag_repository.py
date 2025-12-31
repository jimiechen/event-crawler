from typing import List, Optional, Tuple, Dict
from datetime import datetime, timedelta
from sqlalchemy import select, update, func, delete, and_, or_, distinct, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag_management import StockTagInfo, StockTagRelation, OperationLog
from app.models.stock import TonghuashunStock, StockInfo, WencaiStock
from app.repositories.base import BaseRepository

class TagRepository(BaseRepository[StockTagInfo]):
    def __init__(self, session: AsyncSession):
        super().__init__(StockTagInfo, session)

    async def get_by_name(self, name: str) -> Optional[StockTagInfo]:
        stmt = select(StockTagInfo).where(StockTagInfo.name == name, StockTagInfo.is_deleted == False)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_tags_by_page(self, page: int = 1, page_size: int = 20, 
                             name: Optional[str] = None,
                             date_filter: Optional[str] = None,
                             tag_type: Optional[str] = None) -> Tuple[List[StockTagInfo], int]:
        stmt = select(StockTagInfo).where(StockTagInfo.is_deleted == False)
        
        if tag_type:
            stmt = stmt.where(StockTagInfo.tag_type == tag_type)
            
        if name:
            stmt = stmt.where(StockTagInfo.name.ilike(f"%{name}%"))
            
        if date_filter:
            # Filter by tag name containing the date (common for date-based tags)
            # OR created_at date matches
            try:
                # Assuming date_filter is YYYY-MM-DD
                # We search for tags that might look like the date
                # or were created on that date
                from sqlalchemy import cast, Date, or_
                
                date_val = date_filter.strip()
                # Remove hyphens for name search (e.g. 20231027) if commonly used
                date_val_compact = date_val.replace("-", "")
                
                stmt = stmt.where(
                    or_(
                        StockTagInfo.name.like(f"%{date_val}%"),
                        StockTagInfo.name.like(f"%{date_val_compact}%"),
                        cast(StockTagInfo.created_at, Date) == date_val
                    )
                )
            except Exception:
                pass
        
        # Calculate total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()
        
        # Pagination
        stmt = stmt.offset((page - 1) * page_size).limit(page_size).order_by(StockTagInfo.created_at.desc())
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        
        return list(items), total

    async def get_tag_stocks_paginated(self, tag_id: int, page: int = 1, page_size: int = 20) -> Tuple[List[dict], int]:
        """Get paginated stocks for a tag"""
        
        # Count total (distinct stock codes)
        count_stmt = select(func.count(distinct(StockTagRelation.stock_code))).select_from(StockTagRelation).join(
            WencaiStock, StockTagRelation.stock_code == WencaiStock.stock_code
        ).outerjoin(
            StockInfo, StockTagRelation.stock_code == StockInfo.code
        ).where(
            and_(
                StockTagRelation.tag_id == tag_id,
                or_(StockInfo.is_active == True, StockInfo.is_active == None)
            )
        )
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()
        
        # Query stocks
        stmt = select(distinct(WencaiStock.stock_code), WencaiStock.stock_name).join(
            StockTagRelation, WencaiStock.stock_code == StockTagRelation.stock_code
        ).outerjoin(
            StockInfo, WencaiStock.stock_code == StockInfo.code
        ).where(
            and_(
                StockTagRelation.tag_id == tag_id,
                or_(StockInfo.is_active == True, StockInfo.is_active == None)
            )
        ).offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        stocks = [{"code": row[0], "name": row[1]} for row in rows]
        return stocks, total

    async def get_stocks_for_tags(self, tag_ids: List[int]) -> Dict[int, List[dict]]:
        """Get stocks for a list of tag IDs"""
        if not tag_ids:
            return {}
            
        from app.models.stock import StockInfo, WencaiStock
        from sqlalchemy import or_, distinct
        
        stmt = select(StockTagRelation.tag_id, WencaiStock.stock_code, WencaiStock.stock_name).join(
            WencaiStock, StockTagRelation.stock_code == WencaiStock.stock_code
        ).outerjoin(
            StockInfo, StockTagRelation.stock_code == StockInfo.code
        ).where(
            and_(
                StockTagRelation.tag_id.in_(tag_ids)
            )
        ).group_by(StockTagRelation.tag_id, WencaiStock.stock_code, WencaiStock.stock_name)
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        # Group by tag_id
        result_map = {tag_id: [] for tag_id in tag_ids}
        for row in rows:
            tag_id, code, name = row
            if tag_id in result_map:
                result_map[tag_id].append({"code": code, "name": name})
                
        return result_map

    async def get_latest_prices(self, stock_codes: List[str]) -> Dict[str, float]:
        """Get latest price change percent for a list of stock codes"""
        if not stock_codes:
            return {}
            
        # Get data from last 7 days to ensure we have something even on weekends/holidays
        start_date = (datetime.now() - timedelta(days=7)).date()
        
        stmt = select(TonghuashunStock.code, TonghuashunStock.change_percent).where(
            TonghuashunStock.code.in_(stock_codes),
            TonghuashunStock.timestamp >= start_date
        ).order_by(TonghuashunStock.timestamp.desc(), TonghuashunStock.id.desc())
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        prices = {}
        for row in rows:
            # Since we ordered by desc, the first encounter for a code is the latest
            if row.code not in prices:
                prices[row.code] = float(row.change_percent) if row.change_percent is not None else 0.0
                
        return prices

    async def soft_delete(self, tag_id: int) -> bool:
        stmt = update(StockTagInfo).where(StockTagInfo.id == tag_id).values(is_deleted=True)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def batch_create(self, tags: List[StockTagInfo]):
        self.session.add_all(tags)
        await self.session.flush()

    # --- Relations ---

    async def add_relations(self, relations: List[StockTagRelation]):
        # Insert ignore or handle duplicates? 
        # Since we have unique constraint, we should probably check existence or use upsert logic if DB supports.
        # But for simplicity, we can just add and let caller handle integrity, 
        # or filter out existing ones first.
        # Here we just add, assuming pre-check or ignore conflicts logic in service.
        self.session.add_all(relations)
        await self.session.flush()

    async def remove_relations(self, tag_id: int, stock_codes: List[str]):
        stmt = delete(StockTagRelation).where(
            StockTagRelation.tag_id == tag_id,
            StockTagRelation.stock_code.in_(stock_codes)
        )
        await self.session.execute(stmt)

    async def get_tags_by_stock(self, stock_code: str) -> List[Tuple[StockTagInfo, datetime]]:
        stmt = select(StockTagInfo, StockTagRelation.created_at).join(StockTagRelation).where(
            StockTagRelation.stock_code == stock_code,
            StockTagInfo.is_deleted == False
        )
        result = await self.session.execute(stmt)
        return result.all()

    async def get_stocks_by_tag(self, tag_id: int) -> List[str]:
        stmt = select(StockTagRelation.stock_code).where(
            StockTagRelation.tag_id == tag_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_all_tagged_stock_codes(self) -> List[str]:
        """Get all stock codes that have at least one tag"""
        stmt = select(distinct(StockTagRelation.stock_code))
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    # --- Logs ---
    
    async def add_log(self, log: OperationLog):
        self.session.add(log)
        await self.session.flush()

    async def get_logs(self, page: int = 1, page_size: int = 20) -> Tuple[List[OperationLog], int]:
        stmt = select(OperationLog).order_by(OperationLog.created_at.desc())
        
        count_stmt = select(func.count()).select_from(OperationLog)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()
        
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(stmt)
        return result.scalars().all(), total
