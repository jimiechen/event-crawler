import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func

from app.models.base import Base
from app.models.pattern_config import PatternConfig, PatternStockPool
from app.models.stock_daily import StockDailyTemp
from app.services.pattern_analysis_service import PatternAnalysisService
from unittest.mock import MagicMock, patch

# 使用内存数据库进行测试
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest.mark.asyncio
class TestIntegrationFlow:
    
    async def create_session(self):
        """手动创建会话"""
        engine = create_async_engine(TEST_DB_URL, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        return engine, async_session()

    async def test_pool_management_real_db(self):
        """
        集成测试: 股票池优胜劣汰逻辑 (使用内存DB)
        """
        engine, session = await self.create_session()
        
        try:
            service = PatternAnalysisService(session)
            
            # 1. 准备数据: 插入 110 个股票
            stocks = []
            for i in range(110):
                stock = PatternStockPool(
                    stock_code=f"{i:06d}",
                    stock_name=f"Stock-{i}",
                    score=100 + i, # 分数随 i 增加
                    patterns={"test": "pattern"},
                    status="observation", # 初始全为观察
                    updated_at=datetime.now()
                )
                session.add(stock)
            
            await session.commit()
            
            # 2. 执行优胜劣汰
            await service._manage_pool_size()
            
            # 3. 验证结果
            stmt = select(PatternStockPool).order_by(PatternStockPool.score.desc())
            result = await session.execute(stmt)
            all_stocks = result.scalars().all()
            
            # 验证总数
            assert len(all_stocks) == 100, f"总池数量应为100，实际为 {len(all_stocks)}"
            
            # 验证 Core (Top 20)
            core_stocks = [s for s in all_stocks if s.status == "core"]
            assert len(core_stocks) == 20, f"核心池数量应为20，实际为 {len(core_stocks)}"
            
            # 验证 Core 的分数是否最高 (最后20个插入的，分数 190-209)
            min_core_score = min(s.score for s in core_stocks)
            assert min_core_score >= 190, f"核心池最低分应 >= 190, 实际为 {min_core_score}"
            
            # 验证 Observation (Next 80)
            obs_stocks = [s for s in all_stocks if s.status == "observation"]
            assert len(obs_stocks) == 80, f"观察池数量应为80，实际为 {len(obs_stocks)}"
            
            # 验证被删除的股票 (分数 100-109, id 0-9)
            deleted_stmt = select(func.count(PatternStockPool.id)).where(PatternStockPool.score < 110)
            deleted_count = (await session.execute(deleted_stmt)).scalar()
            assert deleted_count == 0, "低分股票应该被物理删除"
            
        finally:
            await session.close()
            await engine.dispose()

    async def test_low_volume_alert(self):
        """
        集成测试: 地量告警逻辑
        Mock AkShare 数据，验证成交量比率计算
        """
        engine, session = await self.create_session()
        
        try:
            service = PatternAnalysisService(session)
            
            # 初始化配置 (确保 low_volume_ratio 存在)
            await service.init_configs()
            
            # Mock ak.stock_zh_a_hist via asyncio.to_thread
            # 我们需要 mock asyncio.to_thread，或者更简单地，patch ak.stock_zh_a_hist 如果它被直接调用
            # service code: df_hist = await asyncio.to_thread(ak.stock_zh_a_hist, ...)
            
            # 构造 Mock DataFrame
            import pandas as pd
            
            # 过去5天数据 + 今天
            # 前5天平均量 = 10000
            data = {
                '日期': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05', '2023-01-06'],
                '成交量': [10000, 10000, 10000, 10000, 10000, 4000] # 今天 4000 < 10000 * 0.6 (6000)
            }
            df_mock = pd.DataFrame(data)
            
            with patch('app.services.pattern_analysis_service.ak.stock_zh_a_hist', return_value=df_mock):
                # check_low_volume_alert 内部使用 asyncio.to_thread(ak...)
                # patch ak.stock_zh_a_hist 应该能生效，只要 asyncio.to_thread 真正去调用它
                
                result = await service.check_low_volume_alert("000001")
                
                assert result["is_low_vol"], "成交量 4000 应小于均量 10000 * 0.6"
                assert result["current_vol"] == 4000
                assert result["avg_vol_5"] == 10000
                
            # 测试非地量情况
            data2 = {
                '日期': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05', '2023-01-06'],
                '成交量': [10000, 10000, 10000, 10000, 10000, 7000] # 7000 > 6000
            }
            df_mock2 = pd.DataFrame(data2)
             
            with patch('app.services.pattern_analysis_service.ak.stock_zh_a_hist', return_value=df_mock2):
                result = await service.check_low_volume_alert("000001")
                assert result["is_low_vol"] is False
                
        finally:
            await session.close()
            await engine.dispose()


    async def test_full_screening_flow(self):
        """
        集成测试: 完整筛选流程
        """
        engine, session = await self.create_session()
        
        try:
            service = PatternAnalysisService(session)
            
            # Mock analyze_history_and_score
            async def mock_analyze(code):
                if code == "000001":
                    return {"score": 200, "patterns": ["bullish_engulfing"], "expma_ok": True}
                elif code == "000002":
                    return {"score": 50, "patterns": ["shooting_star"], "expma_ok": False} # EXPMA Fail
                elif code == "000003":
                    return {"score": -10, "patterns": [], "expma_ok": True} # Score Fail
                return {"score": 0, "patterns": [], "expma_ok": False}

            service.analyze_history_and_score = mock_analyze
            
            # 1. 插入临时数据 (直接插入DB以避开MySQL特有的Upsert语法)
            temp_data = [
                StockDailyTemp(code="000001", trade_date=datetime.now().date(), open=10, close=11, high=11, low=9, vol=1000, amount=10000, turnover_rate=1.5, industry="Bank", concept="Test", status="pending"),
                StockDailyTemp(code="000002", trade_date=datetime.now().date(), open=10, close=11, high=11, low=9, vol=1000, amount=10000, turnover_rate=1.5, industry="Tech", concept="AI", status="pending"),
                StockDailyTemp(code="000003", trade_date=datetime.now().date(), open=10, close=11, high=11, low=9, vol=1000, amount=10000, turnover_rate=1.5, industry="Energy", concept="Solar", status="pending"),
            ]
            session.add_all(temp_data)
            await session.commit()
            
            # 2. 执行筛选
            results = await service.perform_screening()
            
            # 3. 验证统计结果
            assert results["total"] == 3
            assert results["passed"] == 1 # Only 000001
            assert results["failed"] == 2
            
            # 4. 验证数据库状态
            stmt = select(PatternStockPool).where(PatternStockPool.stock_code == "000001")
            pool_item = (await session.execute(stmt)).scalar_one_or_none()
            assert pool_item is not None
            assert pool_item.score == 200
            assert pool_item.status == "core"
            
            stmt = select(PatternStockPool).where(PatternStockPool.stock_code == "000002")
            pool_item = (await session.execute(stmt)).scalar_one_or_none()
            assert pool_item is None
            
            stmt = select(StockDailyTemp).where(StockDailyTemp.code == "000001")
            temp_item = (await session.execute(stmt)).scalar_one()
            assert temp_item.status == "passed"
            
            stmt = select(StockDailyTemp).where(StockDailyTemp.code == "000002")
            temp_item = (await session.execute(stmt)).scalar_one()
            assert temp_item.status == "rejected"
            assert temp_item.reject_reason == "EXPMA13下方"
            
        finally:
            await session.close()
            await engine.dispose()
