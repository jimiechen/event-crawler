"""
生成验收报告（简化版）
"""
import sys
sys.path.insert(0, str(__file__).replace('/tests/generate_acceptance_report.py', ''))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import DatabaseConfig
from app.models.stock_daily import StockScoreResult
from app.models.stock import StockInfo
from app.models.volume_analysis import StockVolumeBaseline
from datetime import datetime

async def generate_acceptance_report(test_code: str = '603601'):
    """
    生成验收报告
    
    Args:
        test_code: 测试股票代码
    """
    print("📊 生成验收报告...")
    
    # 初始化数据库
    from app.database import db_manager as db_mgr
    await db_mgr.initialize()
    
    session = db_mgr.session_factory()
    try:
        # 1. 查询每日积分变化
        print("\n📈 每日积分变化:")
        stmt = text(f"""
            SELECT 
                trade_date,
                total_score
            FROM stock_score_result
            WHERE code = '{test_code}'
                AND trade_date >= '2025-11-20'
                AND trade_date <= '2025-12-10'
            ORDER BY trade_date
        """)
        result = await session.execute(stmt)
        scores = result.fetchall()
        
        if not scores:
            print("   ❌ 未找到积分数据")
            return
        
        # 输出积分变化
        for row in scores:
            trade_date, total_score = row
            print(f"   {trade_date}: 总分={total_score}")
        
        # 2. 查询排名变化
        print("\n🏆 每日排名变化:")
        stmt = text(f"""
            SELECT 
                trade_date,
                ranking
            FROM stock_score_result
            WHERE code = '{test_code}'
                AND trade_date >= '2025-11-20'
                AND trade_date <= '2025-12-10'
                AND ranking IS NOT NULL
            ORDER BY trade_date
        """)
        result = await session.execute(stmt)
        rankings = result.fetchall()
        
        # 输出排名变化
        for row in rankings:
            trade_date, ranking = row
            print(f"   {trade_date}: 排名={ranking}")
        
        # 3. 统计摘要
        print("\n📊 统计摘要:")
        print(f"   测试股票: {test_code}")
        print(f"   测试天数: {len(scores)} 天")
        if scores:
            print(f"   初始总分: {scores[0][1]}")
            print(f"   最终总分: {scores[-1][1]}")
            print(f"   总积分增长: {scores[-1][1] - scores[0][1]}")
        
        # 4. 验证Redis缓存
        print("\n🔍 验证Redis缓存:")
        from app.services.redis_cache_service import redis_cache_service
        cached = redis_cache_service.get_baseline(test_code)
        if cached:
            print("   ✅ Redis缓存存在")
            print(f"   3倍量收盘价: {cached.get('last_3x_close', {}).get('value', 'N/A')}")
            print(f"   60日地量: {cached.get('last_60d_low_vol', {}).get('value', 'N/A')}")
        else:
            print("   ⚠️ Redis缓存不存在")
        
        # 5. 验证数据库baseline
        print("\n🔍 验证数据库baseline:")
        stmt = select(StockVolumeBaseline).where(StockVolumeBaseline.code == test_code)
        result = await session.execute(stmt)
        baseline = result.scalar_one_or_none()
        
        if baseline:
            print("   ✅ 数据库baseline存在")
            print(f"   3倍量日期: {baseline.last_3x_date}")
            print(f"   60日地量日期: {baseline.last_60d_low_vol_date}")
        else:
            print("   ⚠️ 数据库baseline不存在")
        
        # 6. 验证stock_info
        print("\n🔍 验证stock_info:")
        stmt = select(StockInfo).where(StockInfo.code == test_code)
        result = await session.execute(stmt)
        info = result.scalar_one_or_none()
        
        if info:
            print("   ✅ stock_info存在")
            print(f"   volume_anomaly_score: {info.volume_anomaly_score}")
            print(f"   score_update_time: {info.score_update_time}")
        else:
            print("   ⚠️ stock_info不存在")
        
        print("\n🎉 验收报告生成完成！")
        
    finally:
        await session.close()
        await db_mgr.close()

if __name__ == '__main__':
    import asyncio
    try:
        asyncio.run(generate_acceptance_report())
    except Exception as e:
        print(f"\n❌ 生成报告异常: {e}")
        import traceback
        traceback.print_exc()
