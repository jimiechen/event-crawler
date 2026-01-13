#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证智能数据合并接口
"""

import asyncio
import sys
import os
from datetime import datetime, date

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_manager
from app.services.data_merge_service import DataMergeService


async def test_smart_merge():
    """测试智能数据合并"""
    print("=" * 60)
    print("测试智能数据合并接口")
    print("=" * 60)

    async with db_manager.get_session() as session:
        service = DataMergeService(session)

        # 测试1：自动判断日期（CSV最新日期和数据库最新日期）
        print("\n[测试1] 自动判断日期")
        stock_code = "000001.SZ"
        
        try:
            result = await service.merge_stock_smart(
                stock_code=stock_code
            )
            
            print(f"✅ 股票 {stock_code} 处理结果:")
            print(f"  - CSV最新日期: {result.get('csv_last_date')}")
            print(f"  - 数据库最新日期: {result.get('db_last_date')}")
            print(f"  - 是否同步: {result.get('synced', False)}")
            print(f"  - 消息: {result.get('message')}")
            
            if result.get('synced', False):
                print(f"  - 合并统计: {result.get('merged', 0)} 条, 跳过 {result.get('skipped', 0)} 条, 错误 {result.get('error', 0)} 条")
                
        except Exception as e:
            print(f"❌ 测试1失败: {e}")
            import traceback
            traceback.print_exc()

        # 测试2：指定数据源
        print("\n[测试2] 指定数据源（CSV）")
        try:
            result = await service.merge_stock_smart(
                stock_code="000002.SZ",
                source="csv"
            )
            
            print(f"✅ 股票 000002.SZ 处理结果:")
            print(f"  - 消息: {result.get('message')}")
            
            if result.get('synced', False):
                print(f"  - 合并统计: {result.get('merged', 0)} 条")
                
        except Exception as e:
            print(f"❌ 测试2失败: {e}")

        # 测试3：强制同步
        print("\n[测试3] 强制同步")
        try:
            result = await service.merge_stock_smart(
                stock_code="600000.SH",
                force_sync=True
            )
            
            print(f"✅ 股票 600000.SH 处理结果:")
            print(f"  - 消息: {result.get('message')}")
            
            if result.get('synced', False):
                print(f"  - 合并统计: {result.get('merged', 0)} 条")
                
        except Exception as e:
            print(f"❌ 测试3失败: {e}")

        # 测试4：指定目标日期（补全数据）
        print("\n[测试4] 指定目标日期（补全数据）")
        try:
            target_date = "20240110"
            result = await service.merge_stock_smart(
                stock_code="000003.SZ",
                target_date=target_date
            )
            
            print(f"✅ 股票 000003.SZ 补全日期 {target_date} 处理结果:")
            print(f"  - 消息: {result.get('message')}")
            
            if result.get('synced', False):
                print(f"  - 合并统计: {result.get('merged', 0)} 条")
                
        except Exception as e:
            print(f"❌ 测试4失败: {e}")

        # 测试5：获取CSV最新日期
        print("\n[测试5] 获取CSV最新日期")
        try:
            csv_last_date = await service._get_csv_last_date("000001.SZ")
            print(f"✅ CSV最新日期: {csv_last_date}")
        except Exception as e:
            print(f"❌ 测试5失败: {e}")

        # 测试6：获取数据库最新日期
        print("\n[测试6] 获取数据库最新日期")
        try:
            db_last_date = await service._get_db_last_date("000001.SZ")
            print(f"✅ 数据库最新日期: {db_last_date}")
        except Exception as e:
            print(f"❌ 测试6失败: {e}")

        # 测试7：判断需要同步的日期
        print("\n[测试7] 判断需要同步的日期")
        try:
            csv_date = date(2024, 1, 10)
            db_date = date(2024, 1, 8)
            
            sync_dates = await service._get_sync_dates("000001.SZ", csv_date, db_date)
            print(f"✅ 需要同步的日期: {[str(d) for d in sync_dates[:5]]}... (共 {len(sync_dates)} 天)")
        except Exception as e:
            print(f"❌ 测试7失败: {e}")

        # 测试8：数据一致性校验
        print("\n[测试8] 数据一致性校验")
        try:
            # 模拟新数据
            new_data = {
                "open": 10.50,
                "close": 10.80,
                "high": 10.90,
                "low": 10.40,
                "vol": 100000
            }
            
            # 模拟最近数据
            recent_data = [
                {"open": 10.40, "close": 10.70, "high": 10.80, "low": 10.30, "vol": 95000},
                {"open": 10.45, "close": 10.75, "high": 10.85, "low": 10.35, "vol": 98000},
                {"open": 10.50, "close": 10.80, "high": 10.90, "low": 10.40, "vol": 100000}
            ]
            
            is_valid = service._validate_data_consistency(new_data, recent_data)
            print(f"✅ 数据一致性校验: {'通过' if is_valid else '未通过'}")
            
        except Exception as e:
            print(f"❌ 测试8失败: {e}")

        # 测试9：获取CSV路径
        print("\n[测试9] 获取CSV路径")
        try:
            csv_path = service._get_csv_path("000001")
            print(f"✅ CSV路径: {csv_path}")
            print(f"  - 文件存在: {os.path.exists(csv_path)}")
        except Exception as e:
            print(f"❌ 测试9失败: {e}")

        # 测试10：日期解析和格式化
        print("\n[测试10] 日期解析和格式化")
        try:
            # 解析测试
            date1 = service._parse_date("20240110")
            print(f"✅ 解析日期 '20240110': {date1}")
            
            date2 = service._parse_date("2024-01-10")
            print(f"✅ 解析日期 '2024-01-10': {date2}")
            
            # 格式化测试
            date_str = service._format_date(date1)
            print(f"✅ 格式化日期: {date_str}")
            
        except Exception as e:
            print(f"❌ 测试10失败: {e}")


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("开始测试智能数据合并功能")
    print("=" * 60)

    # 初始化数据库
    await db_manager.initialize()
    print("✅ 数据库初始化完成")

    try:
        # 测试智能合并
        await test_smart_merge()

        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 关闭数据库连接
        await db_manager.close()
        print("✅ 数据库连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())
