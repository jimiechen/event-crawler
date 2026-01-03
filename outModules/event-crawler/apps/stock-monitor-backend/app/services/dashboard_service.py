
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from sqlalchemy import text, func, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock import StockInfo, WencaiStock, TonghuashunStock
from app.models.stock_daily import StockDaily
from app.services.tdx_service import TdxService
from app.config.logging import get_logger

logger = get_logger(__name__)

class DashboardService:
    """仪表盘数据服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_statistics(self) -> Dict[str, Any]:
        """获取仪表盘统计数据"""
        try:
            # 1. 总股票数
            total_stocks_query = select(func.count()).select_from(StockInfo)
            total_stocks = await self.db.scalar(total_stocks_query)

            # 2. 活跃股票
            active_stocks_query = select(func.count()).select_from(StockInfo).where(StockInfo.is_active == True)
            active_stocks = await self.db.scalar(active_stocks_query)

            # 3. 今日问财数据
            # 注意：使用数据库日期函数可能依赖具体数据库类型，这里假设是MySQL/PostgreSQL通用
            # 或者在应用层处理日期范围
            today = date.today()
            # 构造今日开始和结束时间
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())
            
            today_wencai_query = select(func.count()).select_from(WencaiStock).where(
                WencaiStock.created_at >= start_of_day,
                WencaiStock.created_at <= end_of_day
            )
            today_wencai = await self.db.scalar(today_wencai_query)

            # 4. 最后更新时间
            last_update_query = select(func.max(TonghuashunStock.updated_at))
            last_update = await self.db.scalar(last_update_query)

            return {
                "total_stocks": total_stocks or 0,
                "active_stocks": active_stocks or 0,
                "today_wencai_count": today_wencai or 0,
                "last_update_time": last_update
            }
        except Exception as e:
            logger.error(f"获取仪表盘统计数据失败: {e}")
            raise

    async def get_stock_list(
        self, 
        page: int = 1, 
        page_size: int = 20, 
        active_only: bool = False,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        sort_by: str = "volume_anomaly_score",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """获取股票列表 (Tab 1)"""
        try:
            offset = (page - 1) * page_size
            
            # 构建基础查询
            query = select(StockInfo)
            count_query = select(func.count()).select_from(StockInfo)
            
            # 过滤 active
            if active_only:
                query = query.where(StockInfo.is_active == True)
                count_query = count_query.where(StockInfo.is_active == True)
            
            # 时间段搜索 (基于评分更新时间)
            if start_time:
                query = query.where(StockInfo.score_update_time >= start_time)
                count_query = count_query.where(StockInfo.score_update_time >= start_time)
            
            if end_time:
                query = query.where(StockInfo.score_update_time <= end_time)
                count_query = count_query.where(StockInfo.score_update_time <= end_time)
            
            # 排序
            if sort_by == "volume_anomaly_score":
                if sort_order == "asc":
                    query = query.order_by(StockInfo.volume_anomaly_score.asc())
                else:
                    query = query.order_by(StockInfo.volume_anomaly_score.desc())
            elif sort_by == "tdx_plugin_score":
                if sort_order == "asc":
                    query = query.order_by(StockInfo.tdx_plugin_score.asc())
                else:
                    query = query.order_by(StockInfo.tdx_plugin_score.desc())
            elif sort_by == "latest_price":
                if sort_order == "asc":
                    query = query.order_by(StockInfo.latest_price.asc())
                else:
                    query = query.order_by(StockInfo.latest_price.desc())
            elif sort_by == "score_update_time":
                if sort_order == "asc":
                    query = query.order_by(StockInfo.score_update_time.asc())
                else:
                    query = query.order_by(StockInfo.score_update_time.desc())
            else:
                # 默认按代码排序
                query = query.order_by(StockInfo.code.asc())
            
            # 查询总数
            total = await self.db.scalar(count_query)

            # 查询列表
            stmt = query.offset(offset).limit(page_size)
            result = await self.db.execute(stmt)
            stocks = result.scalars().all()

            return {
                "total": total,
                "items": [
                    {
                        "code": stock.code,
                        "name": stock.name,
                        "is_active": stock.is_active,
                        "market": stock.market,
                        "latest_price": stock.latest_price,
                        "sync_250d_kline": stock.sync_250d_kline,
                        "sync_incremental": stock.sync_incremental,
                        "is_held": stock.is_held,
                        "volume_anomaly_score": stock.volume_anomaly_score,
                        "tdx_plugin_score": stock.tdx_plugin_score,
                        "score_update_time": stock.score_update_time,
                        "bonus_items": stock.bonus_items
                    } for stock in stocks
                ],
                "page": page,
                "page_size": page_size
            }
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            raise

    async def get_wencai_list(self, page: int = 1, page_size: int = 15, tag_filter: Optional[str] = None) -> Dict[str, Any]:
        """获取问财选股列表 (Tab 2)"""
        try:
            offset = (page - 1) * page_size
            
            # 构建基础查询
            query = select(WencaiStock)
            count_query = select(func.count()).select_from(WencaiStock)

            # 应用标签过滤
            if tag_filter:
                # 假设标签在 concept 或 industry 字段中
                filter_condition = (
                    WencaiStock.concept.contains(tag_filter) | 
                    WencaiStock.industry.contains(tag_filter)
                )
                query = query.where(filter_condition)
                count_query = count_query.where(filter_condition)

            # 获取总数
            total = await self.db.scalar(count_query)

            # 获取列表
            stmt = query.order_by(WencaiStock.created_at.desc()).offset(offset).limit(page_size)
            result = await self.db.execute(stmt)
            items = result.scalars().all()

            return {
                "total": total,
                "items": [
                    {
                        "id": item.id,
                        "stock_code": item.stock_code,
                        "stock_name": item.stock_name,
                        "date_tag": item.created_at.strftime('%Y-%m-%d') if item.created_at else "",
                        "tags": f"{item.concept or ''} {item.industry or ''}".strip(),
                        "created_at": item.created_at
                    } for item in items
                ],
                "page": page,
                "page_size": page_size
            }
        except Exception as e:
            logger.error(f"获取问财列表失败: {e}")
            raise

    async def get_stock_extra_info(self, code: str) -> Dict[str, Any]:
        """获取股票额外信息"""
        try:
            # 1. 获取 StockInfo
            stmt = select(StockInfo).where(StockInfo.code == code)
            stock = (await self.db.execute(stmt)).scalar_one_or_none()
            if not stock:
                raise ValueError(f"Stock {code} not found")

            # 2. Check history data < 2025-12-22
            check_date = date(2025, 12, 22)
            
            history_stmt = select(func.count()).select_from(StockDaily).where(
                StockDaily.code == code,
                StockDaily.trade_date < check_date
            )
            has_history = (await self.db.scalar(history_stmt)) > 0

            # 3. Check incremental data > 2025-12-22
            incremental_stmt = select(func.count()).select_from(StockDaily).where(
                StockDaily.code == code,
                StockDaily.trade_date > check_date
            )
            has_incremental = (await self.db.scalar(incremental_stmt)) > 0

            # 4. Get sparkline data (last 60 days closing price)
            sparkline_stmt = select(StockDaily.close).where(
                StockDaily.code == code
            ).order_by(StockDaily.trade_date.desc()).limit(60)
            # Result needs to be reversed to be chronological for chart
            sparkline_data = (await self.db.execute(sparkline_stmt)).scalars().all()
            sparkline_data = [float(x) for x in sparkline_data][::-1]

            return {
                "code": code,
                "tdx_plugin_score": stock.tdx_plugin_score or 0,
                "has_history_data": has_history,
                "has_incremental_data": has_incremental,
                "sparkline_data": sparkline_data
            }
        except Exception as e:
            logger.error(f"Failed to get extra info for {code}: {e}")
            raise

    async def sync_tdx_score(self, code: str) -> int:
        """同步TDX评分"""
        try:
            tdx_service = TdxService(self.db)
            # Fetch and store risk data
            risk_data = await tdx_service.store_stock_risk(code)
            
            score = 0
            if risk_data:
                score = int(risk_data.total_score)
            
            # Update StockInfo
            stmt = select(StockInfo).where(StockInfo.code == code)
            stock = (await self.db.execute(stmt)).scalar_one_or_none()
            if stock:
                stock.tdx_plugin_score = score
                stock.score_update_time = datetime.now()
                await self.db.commit()
            
            return score
        except Exception as e:
            logger.error(f"Failed to sync TDX score for {code}: {e}")
            raise
