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
from app.utils.technical_indicators import calculate_expma
from app.utils.morphology_recognition import check_bullish_engulfing, check_bottom_fractal, check_shooting_star
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
        地量定义：当前成交量 < 5日均量 * 0.5 (可配置)
        """
        try:
            # 1. 获取实时数据 (akshare or tushare or wencai)
            # 这里为了速度，可以使用 akshare 的实时接口
            df_hist = await asyncio.to_thread(ak.stock_zh_a_hist, symbol=stock_code.split('.')[0], period="daily", adjust="qfq")
            
            if df_hist.empty or len(df_hist) < 5:
                return {"is_low_vol": False, "msg": "Insufficient data"}
                
            # 计算5日均量 (不包含今天，如果今天是收盘后)
            # 如果是盘中，最后一行是今天。我们需要比较今天的实时量 vs 过去5天的均量
            # 假设 df_hist 包含了今天(实时)的数据
            
            last_record = df_hist.iloc[-1]
            past_5_days = df_hist.iloc[-6:-1] # 前5天
            
            avg_vol_5 = past_5_days['成交量'].mean()
            current_vol = last_record['成交量']
            
            # 获取配置
            stmt = select(PatternConfig).where(PatternConfig.pattern_code == 'low_volume_ratio')
            res = await self.db.execute(stmt)
            config = res.scalar_one_or_none()
            ratio = float(config.score) if config else 0.6 # 默认0.6倍以下算地量
            
            is_low = bool(current_vol < (avg_vol_5 * ratio))
            
            return {
                "is_low_vol": is_low,
                "current_vol": float(current_vol),
                "avg_vol_5": float(avg_vol_5),
                "ratio": float(current_vol / avg_vol_5) if avg_vol_5 > 0 else 0
            }
            
        except Exception as e:
            print(f"Error checking low volume for {stock_code}: {e}")
            return {"is_low_vol": False, "msg": str(e)}

    async def analyze_history_and_score(self, stock_code: str, analysis_date: Optional[date] = None) -> Dict[str, Any]:
        """
        拉取历史数据，计算EXPMA和形态得分
        优先使用 StockSyncService.get_mixed_history (CSV+Tushare)
        :param analysis_date: 如果提供，则只分析该日期及之前的数据 (用于回测/补录)
        """
        try:
            # 1. Fetch History Data (Last 250 days preferred for mixed history)
            # akshare expects 6 digit code. remove suffix if present.
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
                    # internal logic uses: date, open, close, high, low, volume
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
            
            # 2. Calculate EXPMA
            df['expma13'] = calculate_expma(df['close'], 13)
            current_close = df.iloc[-1]['close']
            current_expma = df.iloc[-1]['expma13']
            
            # 3. Morphology Analysis (Last 3 days)
            if len(df) < 3:
                 return {"score": 0, "reason": "Insufficient data for pattern", "expma_ok": current_close > current_expma}
            
            last_3_days = df.iloc[-3:].to_dict('records')
            
            k1, k2, k3 = last_3_days[0], last_3_days[1], last_3_days[2] # k3 is today
            
            # Load configs
            stmt = select(PatternConfig).where(PatternConfig.is_enabled == True)
            res = await self.db.execute(stmt)
            configs = {c.pattern_code: float(c.score) for c in res.scalars().all()}
            
            score = 0
            patterns = []
            
            # 2-Day Patterns (k2, k3) - 阳包阴
            if check_bullish_engulfing(k2, k3):
                s = configs.get("bullish_engulfing", 200)
                score += s
                patterns.append(f"阳包阴(+{s})")
                
            # 3-Day Patterns (k1, k2, k3) - 底分型
            if check_bottom_fractal(k1, k2, k3):
                s = configs.get("bottom_fractal", 300)
                score += s
                patterns.append(f"底分型(+{s})")
                
            # 1-Day Pattern (k3) - 冲高回落
            if check_shooting_star(k3):
                s = configs.get("shooting_star", 50)
                score += s
                patterns.append(f"冲高回落(+{s})")
                
            return {
                "score": score,
                "patterns": patterns,
                "expma_ok": current_close > current_expma,
                "latest_close": current_close,
                "latest_expma": current_expma
            }
            
        except Exception as e:
            print(f"Error analyzing stock {stock_code}: {e}")
            return {"score": 0, "reason": str(e)}

    async def analyze_patterns(self, stock_code: str) -> Dict[str, Any]:
        """
        分析缠论形态 (Wrapper)
        """
        return await self.analyze_history_and_score(stock_code)
