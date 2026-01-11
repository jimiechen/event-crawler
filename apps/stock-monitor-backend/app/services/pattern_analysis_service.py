import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
import pandas as pd
import akshare as ak
from sqlalchemy import select, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.mysql import insert

from app.models.stock_daily import StockDailyTemp, StockDaily
from app.models.pattern_config import PatternConfig, PatternStockPool
from app.services.stock_service import StockService
from app.services.pathway_engine import PathwayVolumePriceEngine
from app.utils.technical_indicators import calculate_expma
from app.utils.morphology_recognition import check_bullish_engulfing, check_bottom_fractal, check_shooting_star
from loguru import logger
# Avoid circular import by using TYPE_CHECKING or local import if needed, 
# but StockSyncService is high level. Let's try direct import or handle dynamically.
# For now, I will add the field to __init__ and import inside methods or if safe.

class PatternAnalysisService:
    """
    缠论量价形态分析服务
    处理临时数据存储、形态识别、优胜劣汰
    """

    def __init__(self, db: AsyncSession, stock_sync_service: Any = None):
        self.db = db
        self.stock_sync_service = stock_sync_service

    async def init_configs(self):
        """初始化默认配置"""
        defaults = [
            {"code": "bullish_engulfing", "name": "阳包阴(2日)", "score": 200, "description": "昨天阴线今天阳线，且包裹昨天"},
            {"code": "bottom_fractal", "name": "底分型(3日)", "score": 300, "description": "中间K线低点最低，高点最低"},
            {"code": "shooting_star", "name": "冲高回落(1日)", "score": 50, "description": "上影线长，实体小"},
            {"code": "low_volume_ratio", "name": "地量比率", "score": 0.6, "description": "成交量低于5日均量的倍数"}
        ]
        
        for cfg in defaults:
            stmt = select(PatternConfig).where(PatternConfig.pattern_code == cfg["code"])
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if not existing:
                new_cfg = PatternConfig(
                    pattern_code=cfg["code"],
                    pattern_name=cfg["name"],
                    score=cfg["score"],
                    description=cfg["description"],
                    is_enabled=True
                )
                self.db.add(new_cfg)
        
        await self.db.commit()

    async def save_temp_data(self, data_list: List[Dict[str, Any]], source: str = "wencai") -> int:
        """
        保存临时数据到 stock_daily_temp
        """
        if not data_list:
            return 0

        try:
            # 转换为模型对象或字典
            values = []
            for item in data_list:
                # 确保字段匹配
                record = {
                    "code": item.get("code"),
                    "trade_date": item.get("trade_date") or datetime.now().date(),
                    "open": item.get("open"),
                    "close": item.get("close"),
                    "high": item.get("high"),
                    "low": item.get("low"),
                    "vol": item.get("volume"), # 注意字段名映射
                    "amount": item.get("amount"),
                    "turnover_rate": item.get("turnover"),
                    "industry": item.get("industry"),
                    "concept": item.get("concept"),
                    "source": source,
                    "status": "pending",
                    "created_at": datetime.now()
                }
                values.append(record)

            # 使用 Upsert (MySQL)
            stmt = insert(StockDailyTemp).values(values)
            update_stmt = stmt.on_duplicate_key_update(
                open=stmt.inserted.open,
                close=stmt.inserted.close,
                high=stmt.inserted.high,
                low=stmt.inserted.low,
                vol=stmt.inserted.vol,
                amount=stmt.inserted.amount,
                industry=stmt.inserted.industry,
                concept=stmt.inserted.concept,
                updated_at=datetime.now()
            )
            
            result = await self.db.execute(update_stmt)
            await self.db.commit()
            return len(values) # 近似值，execute返回受影响行数可能不同

        except Exception as e:
            await self.db.rollback()
            print(f"Error saving temp data: {e}")
            raise e

    async def clean_expired_data(self, retention_days: int = 3) -> int:
        """
        清理过期临时数据
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            stmt = delete(StockDailyTemp).where(StockDailyTemp.created_at < cutoff_date)
            result = await self.db.execute(stmt)
            await self.db.commit()
            return result.rowcount
        except Exception as e:
            await self.db.rollback()
            print(f"Error cleaning expired data: {e}")
            raise e

    async def get_temp_stocks(self, status: Optional[str] = None) -> List[StockDailyTemp]:
        """
        获取临时表中的股票数据
        """
        stmt = select(StockDailyTemp)
        if status:
            stmt = stmt.where(StockDailyTemp.status == status)
        stmt = stmt.order_by(desc(StockDailyTemp.created_at))
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def perform_screening(self, analysis_date: Optional[date] = None) -> Dict[str, Any]:
        """
        执行筛选流程：
        1. 获取 StockDailyTemp 中 pending 的股票
        2. 逐个分析 (EXPMA + 形态评分)
        3. 符合条件的入池 (PatternStockPool)
        4. 更新 StockDailyTemp 状态
        5. 维护股票池 (优胜劣汰)
        """
        pending_stocks = await self.get_temp_stocks(status="pending")
        results = {
            "total": len(pending_stocks),
            "processed": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0
        }
        
        for stock in pending_stocks:
            try:
                # 分析
                analysis = await self.analyze_history_and_score(stock.code, analysis_date=analysis_date)
                
                # 检查 EXPMA
                if not analysis.get("expma_ok"):
                    stock.status = "rejected"
                    stock.reject_reason = "EXPMA13下方"
                    results["failed"] += 1
                
                # 检查评分
                elif analysis.get("score", 0) <= 0:
                     stock.status = "rejected"
                     stock.reject_reason = "评分不足"
                     results["failed"] += 1
                
                else:
                    # 通过筛选
                    stock.status = "passed"
                    results["passed"] += 1
                    
                    # 入池
                    await self._update_stock_pool(
                        stock_code=stock.code,
                        score=analysis["score"],
                        patterns=analysis["patterns"],
                        industry=stock.industry,
                        concept=stock.concept
                    )
                
                results["processed"] += 1
                
            except Exception as e:
                print(f"Error screening stock {stock.code}: {e}")
                results["errors"] += 1
        
        await self.db.commit()
        
        # 筛选后进行优胜劣汰 (确保总数 <= 100, Core <= 20)
        await self._manage_pool_size()
        
        return results

    async def _update_stock_pool(self, stock_code: str, score: float, patterns: List[str], industry: str, concept: str):
        """
        更新股票池
        """
        
        # Check if exists
        stmt = select(PatternStockPool).where(PatternStockPool.stock_code == stock_code)
        result = await self.db.execute(stmt)
        pool_item = result.scalar_one_or_none()
        
        if pool_item:
            pool_item.score = score
            pool_item.patterns = patterns
            pool_item.updated_at = datetime.now()
            # industry/concept might change? Keep latest
            if industry: pool_item.industry = industry
            if concept: pool_item.concept = concept
        else:
            pool_item = PatternStockPool(
                stock_code=stock_code,
                score=score,
                patterns=patterns,
                industry=industry,
                concept=concept,
                status="observation" # Default to observation
            )
            self.db.add(pool_item)
            
        # Flush to get ID if needed, but we commit later
    
    async def _manage_pool_size(self):
        """
        管理股票池大小和分层
        1. 按分数排序
        2. Top 20 -> Core
        3. Top 21-100 -> Observation
        4. > 100 -> Delete
        """
        stmt = select(PatternStockPool).order_by(desc(PatternStockPool.score), desc(PatternStockPool.updated_at))
        result = await self.db.execute(stmt)
        all_stocks = result.scalars().all()
        
        max_total = 100
        max_core = 20
        
        for i, stock in enumerate(all_stocks):
            if i < max_core:
                stock.status = "core"
            elif i < max_total:
                stock.status = "observation"
            else:
                # Delete excess
                await self.db.delete(stock)
                
        await self.db.commit()

    async def get_tag_cloud_data(self, days: int = 3) -> Dict[str, Any]:
        """
        获取标签云数据 (基于 StockDailyTemp 近N天数据)
        统计 Industry 和 Concept 的出现频次
        """
        cutoff_date = datetime.now().date() - timedelta(days=days)
        stmt = select(StockDailyTemp).where(StockDailyTemp.trade_date >= cutoff_date)
        result = await self.db.execute(stmt)
        stocks = result.scalars().all()
        
        industry_data = {}
        concept_data = {}
        
        for stock in stocks:
            # Industry
            if stock.industry:
                ind = stock.industry.strip()
                if ind:
                    if ind not in industry_data:
                        industry_data[ind] = {"count": 0, "stocks": []}
                    industry_data[ind]["count"] += 1
                    industry_data[ind]["stocks"].append({"code": stock.code, "name": stock.code}) # name unavailable in temp?
            
            # Concept (comma separated)
            if stock.concept:
                concepts = stock.concept.replace('，', ',').split(',')
                for c in concepts:
                    c = c.strip()
                    if c:
                        if c not in concept_data:
                            concept_data[c] = {"count": 0, "stocks": []}
                        concept_data[c]["count"] += 1
                        concept_data[c]["stocks"].append({"code": stock.code, "name": stock.code})
                        
        # Format for frontend
        return {
            "industries": [{"name": k, "value": v["count"], "stocks": v["stocks"]} for k, v in sorted(industry_data.items(), key=lambda x: x[1]["count"], reverse=True)],
            "concepts": [{"name": k, "value": v["count"], "stocks": v["stocks"]} for k, v in sorted(concept_data.items(), key=lambda x: x[1]["count"], reverse=True)]
        }

    async def check_expma_criteria(self, stock_code: str, period: int = 13) -> bool:
        """
        检查 EXPMA 均线条件 (准入条件)
        实时价格是否在 EXPMA(13) 上方
        """
        result = await self.analyze_history_and_score(stock_code)
        return result.get("expma_ok", False)

    async def check_low_volume_alert(self, stock_code: str) -> Dict[str, Any]:
        """
        检查是否满足地量条件 (用于实时监控)
        使用 Pathway 引擎计算
        """
        try:
            # 1. 获取实时数据 (akshare or tushare or wencai)
            # 这里为了速度，可以使用 akshare 的实时接口
            clean_code = stock_code.split('.')[0]
            df_hist = await asyncio.to_thread(ak.stock_zh_a_hist, symbol=clean_code, period="daily", adjust="qfq")
            
            if df_hist.empty or len(df_hist) < 5:
                return {"is_low_vol": False, "msg": "Insufficient data"}
            
            # 2. Prepare data for Pathway (descending order)
            df_desc = df_hist.sort_values(by='日期', ascending=False)
            
            history_dicts = []
            for _, row in df_desc.iterrows():
                history_dicts.append({
                    'open': row['开盘'],
                    'close': row['收盘'],
                    'high': row['最高'],
                    'low': row['最低'],
                    'vol': row['成交量'],
                    'trade_date': row['日期']
                })
            
            # 3. Calculate tags
            tags = self.pathway_engine.calculate_tags(history_dicts)
            
            # 4. Check for '地量比率' or 'N日地量'
            is_low = False
            current_vol = 0.0
            avg_vol_5 = 0.0 
            ratio = 0.0
            
            if history_dicts:
                current_vol = history_dicts[0]['vol']
            
            # Check tags
            for tag in tags:
                if tag['name'] == '地量比率':
                    is_low = True
                    ratio = tag['value'] # current / avg
                    if ratio > 0:
                        avg_vol_5 = current_vol / ratio
                
                # Also consider strict low volume as an alert
                if '日地量' in tag['name']:
                    is_low = True
                    # If we didn't get avg from '地量比率', we might need to calc it manually or just leave as 0
                    # But usually if it's strict low volume, it's also likely low volume ratio (unless volatility is high)
            
            # If still 0, calculate manually for display purposes (fallback)
            if avg_vol_5 == 0 and len(history_dicts) >= 6:
                past_5_vols = [d['vol'] for d in history_dicts[1:6]]
                avg_vol_5 = sum(past_5_vols) / 5
                if avg_vol_5 > 0:
                    ratio = current_vol / avg_vol_5

            return {
                "is_low_vol": is_low,
                "current_vol": float(current_vol),
                "avg_vol_5": float(avg_vol_5),
                "ratio": float(ratio)
            }
            
        except Exception as e:
            logger.error(f"Error checking low volume for {stock_code}: {e}")
            return {"is_low_vol": False, "msg": str(e)}

    async def analyze_history_and_score(self, stock_code: str, analysis_date: Optional[date] = None) -> Dict[str, Any]:
        """
        拉取历史数据，计算EXPMA和形态得分
        优先使用 StockSyncService.get_mixed_history (CSV+Tushare)
        :param analysis_date: 如果提供，则只分析该日期及之前的数据 (用于回测/补录)
        """
        try:
            # 1. Fetch History Data (Last 250 days preferred for mixed history)
            clean_code = stock_code.split('.')[0]
            
            df = pd.DataFrame()
            
            if self.stock_sync_service:
                # Use optimized mixed history
                # days=250 to ensure enough data for MA/EXPMA
                result = await self.stock_sync_service.get_mixed_history(clean_code, days=250)
                if result.get("success") and result.get("data"):
                    df = pd.DataFrame(result["data"])
                    # Ensure columns match internal expectations
                    # get_mixed_history returns: code, trade_date, open, high, low, close, vol, amount
                    if not df.empty:
                        df = df.rename(columns={
                            'trade_date': 'date', 
                            'vol': 'volume'
                        })
            else:
                # Fallback to Akshare
                start_date = (datetime.now() - timedelta(days=100)).strftime("%Y%m%d")
                end_date = datetime.now().strftime("%Y%m%d")
                
                # Run blocking akshare call in a separate thread
                def fetch_data():
                    return ak.stock_zh_a_hist(symbol=clean_code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
                
                df = await asyncio.to_thread(fetch_data)
                
                if not df.empty:
                    # Rename columns to match our internal format
                    df = df.rename(columns={
                        '日期': 'date', '开盘': 'open', '收盘': 'close', 
                        '最高': 'high', '最低': 'low', '成交量': 'volume'
                    })
            
            if df.empty or len(df) < 20:
                return {"score": 0, "reason": "Insufficient data"}
                
            # Filter by analysis_date if provided
            if analysis_date:
                # Ensure date column is date object
                df['date'] = pd.to_datetime(df['date']).dt.date
                df = df[df['date'] <= analysis_date]
                if df.empty or len(df) < 20:
                     return {"score": 0, "reason": "Insufficient data after date filter"}
            
            # 2. Use Pathway Engine to calculate tags and score
            # Convert DataFrame to list of dicts (descending order)
            # Pathway expects: open, close, high, low, vol, trade_date
            
            # Sort descending first
            df_desc = df.sort_values(by='date', ascending=False)
            
            history_dicts = []
            for _, row in df_desc.iterrows():
                history_dicts.append({
                    'open': row['open'],
                    'close': row['close'],
                    'high': row['high'],
                    'low': row['low'],
                    'vol': row['volume'],
                    'trade_date': row['date']
                })
                
            tags = self.pathway_engine.calculate_tags(history_dicts)
            
            # 3. Format result for PatternAnalysisService
            # PatternAnalysisService expects: score, patterns (list of strings), expma_ok, latest_close, latest_expma
            
            score = 0
            patterns = []
            expma_ok = False
            latest_expma = 0
            latest_close = float(df_desc.iloc[0]['close'])
            
            for tag in tags:
                score += tag.get('score', 0)
                name = tag.get('name')
                
                if name == 'EXPMA13上方':
                    expma_ok = True
                    latest_expma = tag.get('value')
                elif name != 'basic_info':
                    # Format pattern string: "Name(+Score)"
                    s = tag.get('score', 0)
                    if s != 0:
                        patterns.append(f"{name}({'+' if s>0 else ''}{s})")
                    else:
                        patterns.append(name)

            return {
                "score": score,
                "patterns": patterns,
                "expma_ok": expma_ok,
                "latest_close": latest_close,
                "latest_expma": latest_expma
            }
            
        except Exception as e:
            logger.error(f"Error analyzing stock {stock_code}: {e}")
            return {"score": 0, "reason": str(e)}

    async def analyze_patterns(self, stock_code: str) -> Dict[str, Any]:
        """
        分析缠论形态 (Wrapper)
        """
        return await self.analyze_history_and_score(stock_code)
