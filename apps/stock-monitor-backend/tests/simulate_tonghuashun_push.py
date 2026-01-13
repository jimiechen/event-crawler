"""
模拟同花顺推送数据（完整版 - 包含400天历史数据）
"""
import asyncio
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.stock_service import StockService
from app.services.volume_analysis_service import VolumeAnalysisService
from app.services.scheduler_service import SchedulerService
from app.config.database import DatabaseConfig
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.stock import StockInfo
from app.models.stock_daily import StockDaily

class TonghuashunSimulator:
    """同花顺推送模拟器"""
    
    def __init__(self, stock_codes: list):
        self.stock_codes = stock_codes
        self.current_date = datetime(2024, 1, 1)  # 从2024年1月1日开始
        self.test_start_date = datetime(2025, 11, 20)  # 测试开始日期
        self.test_end_date = datetime(2025, 12, 10)  # 测试结束日期
        
    def generate_daily_data(self, code: str, date: datetime, day_index: int):
        """
        生成单只股票的模拟数据
        """
        # 模拟价格波动（随机游走）
        base_price = 10.0 + random.uniform(-2, 2)
        if day_index > 0:
            # 前一天的价格
            prev_price = base_price * (1 + random.uniform(-0.05, 0.05))
        else:
            prev_price = base_price
        
        # 当天价格变化
        price_change = random.uniform(-0.05, 0.05)
        current_price = prev_price * (1 + price_change)
        
        # 模拟成交量变化（随机波动，偶尔出现倍量）
        base_volume = 10000000
        volume_multiplier = random.uniform(0.5, 2.0)
        
        # 偶尔出现3倍量（约5%概率）
        if random.random() < 0.05:
            volume_multiplier = 3.0 + random.uniform(0, 1.0)
        
        # 偶尔出现地量（约5%概率）
        if random.random() < 0.05:
            volume_multiplier = 0.3 + random.uniform(0, 0.2)
        
        volume = int(base_volume * volume_multiplier)
        
        # 计算其他价格
        high = current_price * (1 + random.uniform(0, 0.02))
        low = current_price * (1 - random.uniform(0, 0.02))
        open_price = low + random.uniform(0, high - low)
        
        change_percent = (current_price - prev_price) / prev_price * 100 if prev_price > 0 else 0
        
        return {
            'code': code,
            'stock_name': f'模拟股票{code}',
            'current_price': round(current_price, 2),
            'volume': volume,
            'high': round(high, 2),
            'low': round(low, 2),
            'open_price': round(open_price, 2),
            'change_percent': round(change_percent, 2),
            'timestamp': date.isoformat()
        }
    
    async def generate_historical_data(self, session: AsyncSession):
        """
        生成400天历史数据
        """
        print(f"\n📊 开始生成400天历史数据...")
        
        stock_service = StockService(session)
        
        # 先删除旧数据
        print(f"   清理旧数据...")
        from sqlalchemy import delete
        stmt = delete(StockDaily).where(StockDaily.code == self.stock_codes[0])
        await session.execute(stmt)
        await session.commit()
        print(f"   ✅ 旧数据已清理")
        
        # 计算需要生成的天数（从2024-01-01到2025-11-19）
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2025, 11, 19)
        delta = end_date - start_date
        total_days = delta.days + 1
        
        print(f"   生成日期范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        print(f"   总天数: {total_days}")
        
        for code in self.stock_codes:
            for day in range(total_days):
                current_date = start_date + timedelta(days=day)
                
                # 只生成工作日数据（排除周末）
                if current_date.weekday() >= 5:
                    continue
                
                data = self.generate_daily_data(code, current_date, day)
                
                try:
                    # 保存到stock_daily表
                    daily_data = StockDaily(
                        code=code,
                        trade_date=current_date.date(),
                        open=data['open_price'],
                        close=data['current_price'],
                        high=data['high'],
                        low=data['low'],
                        vol=data['volume'],
                        amount=data['volume'] * data['current_price'],
                        volume_ratio=1.0
                    )
                    session.add(daily_data)
                    
                    if day % 50 == 0:
                        print(f"   已生成 {day}/{total_days} 天数据")
                
                except Exception as e:
                    print(f"   ❌ 生成历史数据失败 {current_date}: {e}")
            
            await session.commit()
            print(f"   ✅ {code} 历史数据生成完成")
        
        print(f"✅ 历史数据生成完成\n")
    
    async def simulate_realtime_push(self, session: AsyncSession):
        """
        模拟盘中实时推送（14:00-15:00）
        """
        print(f"\n📥 开始模拟盘中实时推送: {self.current_date.strftime('%Y-%m-%d')}")
        
        stock_service = StockService(session)
        volume_service = VolumeAnalysisService()
        
        for code in self.stock_codes:
            data = self.generate_daily_data(code, self.current_date, 0)
            
            try:
                # 处理同花顺推送数据
                result = await stock_service.process_tonghuashun_raw_data(
                    raw_data={
                        'source': 'browser_plugin',
                        'timestamp': data['timestamp'],
                        'stocks': [data]
                    },
                    request_timestamp=data['timestamp']
                )
                
                print(f"   ✅ {code} 推送成功: 价格={data['current_price']}, 成交量={data['volume']}")
                
                # 运行盘后更新（模拟15:30定时任务）
                print(f"   🔄 运行盘后更新（向量化计算250天积分）...")
                await volume_service.analyze_stock(code, session=session)
                print(f"   ✅ 盘后更新完成")
                
            except Exception as e:
                print(f"   ❌ {code} 推送失败: {e}")
        
        print(f"✅ 盘中实时推送完成: {len(self.stock_codes)} 只股票\n")

async def main():
    """主函数"""
    # 只测试一只股票
    stock_codes = ['603601']
    
    print(f"📊 开始模拟同花顺推送测试（完整版）")
    print(f"   测试股票: {stock_codes}")
    print(f"   历史数据: 400天（2024-01-01 至 2025-11-19）")
    print(f"   测试天数: 20天（2025-11-20 至 2025-12-10）\n")
    
    simulator = TonghuashunSimulator(stock_codes)
    
    # 初始化数据库
    from app.database import db_manager as db_mgr
    await db_mgr.initialize()
    
    session = db_mgr.session_factory()
    try:
        # 第一步：生成400天历史数据
        await simulator.generate_historical_data(session)
        
        # 第二步：模拟20个交易日的推送
        simulator.current_date = simulator.test_start_date
        test_days = (simulator.test_end_date - simulator.test_start_date).days + 1
        
        for day in range(test_days):
            # 只处理工作日
            if simulator.current_date.weekday() >= 5:
                simulator.current_date = simulator.current_date + timedelta(days=1)
                continue
            
            await simulator.simulate_realtime_push(session)
            
            simulator.current_date = simulator.current_date + timedelta(days=1)
            await asyncio.sleep(0.5)
        
        print("\n🎉 所有模拟完成！")
        
    finally:
        await session.close()
        await db_mgr.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被中断")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
