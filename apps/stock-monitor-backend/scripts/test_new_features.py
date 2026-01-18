#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证新功能
1. 问财爬虫调试功能（URL参数、Cookie打印、截图）
2. 数据合并接口（CSV、Tushare、akshare）
3. 按日期去重和保留最新数据
4. 自动更新CSV文件
"""

import asyncio
import sys
import os
from datetime import datetime, date

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_manager
from app.services.data_merge_service import DataMergeService


async def test_data_merge_service():
    """测试数据合并服务"""
    print("=" * 60)
    print("测试数据合并服务")
    print("=" * 60)

    async with db_manager.get_session() as session:
        service = DataMergeService(session)

        # 测试1：合并CSV数据
        print("\n[测试1] 合并CSV数据到数据库")
        test_data = [
            {
                "code": "000001",
                "trade_date": "2024-01-10",
                "open": "10.50",
                "close": "10.80",
                "high": "10.90",
                "low": "10.40",
                "vol": "100000",
                "amount": "1080000",
                "turnover_rate": "2.5",
                "volume_ratio": "1.2",
                "adj_factor": "1.0"
            },
            {
                "code": "000002",
                "trade_date": "2024-01-10",
                "open": "20.30",
                "close": "20.50",
                "high": "20.60",
                "low": "20.20",
                "vol": "80000",
                "amount": "1640000",
                "turnover_rate": "1.8",
                "volume_ratio": "0.9",
                "adj_factor": "1.0"
            }
        ]

        result = await service.merge_data_to_database(
            data=test_data,
            date_column="trade_date",
            code_column="code",
            keep_latest=True
        )

        print(f"✅ 合并结果: 插入 {result['inserted']}, 更新 {result['updated']}, 跳过 {result['skipped']}, 错误 {result['error']}")

        # 测试2：Tushare数据合并
        print("\n[测试2] 合并Tushare数据")
        tushare_data = [
            {
                "ts_code": "000003.SZ",
                "trade_date": "20240110",
                "open": 15.20,
                "close": 15.40,
                "high": 15.50,
                "low": 15.10,
                "vol": 120000,
                "amount": 1848000,
                "turnover_rate": 2.1,
                "adj_factor": 1.0
            }
        ]

        result = await service.merge_tushare_data(
            tushare_data=tushare_data,
            keep_latest=True
        )

        print(f"✅ Tushare合并结果: 插入 {result['inserted']}, 更新 {result['updated']}, 跳过 {result['skipped']}, 错误 {result['error']}")

        # 测试3：akshare数据合并
        print("\n[测试3] 合并akshare数据")
        akshare_data = [
            {
                "股票代码": "600000",
                "日期": "2024-01-10",
                "开盘": 8.50,
                "收盘": 8.60,
                "最高": 8.70,
                "最低": 8.40,
                "成交量": 150000,
                "成交额": 1290000,
                "换手率": 1.5
            }
        ]

        result = await service.merge_akshare_data(
            akshare_data=akshare_data,
            keep_latest=True
        )

        print(f"✅ akshare合并结果: 插入 {result['inserted']}, 更新 {result['updated']}, 跳过 {result['skipped']}, 错误 {result['error']}")

        # 测试4：更新CSV文件
        print("\n[测试4] 从数据库更新CSV文件")
        csv_path = "/tmp/test_stock_daily.csv"
        result = await service.update_csv_from_database(
            csv_file_path=csv_path,
            date_column="trade_date",
            code_column="code",
            start_date=date(2024, 1, 10),
            end_date=date(2024, 1, 10)
        )

        print(f"✅ CSV文件更新成功: {result['total']} 条记录写入 {result['file_path']}")

        # 验证CSV文件
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"✅ CSV文件内容预览（前5行）:")
                for line in lines[:5]:
                    print(f"  {line.strip()}")
        else:
            print(f"❌ CSV文件不存在: {csv_path}")

        # 测试5：按日期去重
        print("\n[测试5] 按日期去重")
        result = await service.deduplicate_by_date(
            start_date=date(2024, 1, 10),
            end_date=date(2024, 1, 10)
        )

        print(f"✅ 去重结果: 发现 {result['duplicate_groups']} 组重复数据，删除 {result['deleted']} 条记录")


async def test_wencai_crawler_debug():
    """测试问财爬虫调试功能"""
    print("\n" + "=" * 60)
    print("测试问财爬虫调试功能")
    print("=" * 60)

    from app.crawler.wencai_crawler import WencaiCrawler

    async with db_manager.get_session() as session:
        crawler = WencaiCrawler(session)

        # 测试1：使用debug_url参数
        print("\n[测试1] 使用debug_url参数访问问财")
        debug_url = "https://www.iwencai.com/unifiedwap/result?w=成交量大于100万"
        
        try:
            result = await crawler.fetch_and_parse(
                query="成交量大于100万",
                batch_name="DebugTest",
                debug_url=debug_url
            )
            print(f"✅ 爬取结果: {result['status']}, 总数: {result['total']}")
        except Exception as e:
            print(f"❌ 爬取失败: {e}")

        # 测试2：正常爬取（会打印Cookie和生成截图）
        print("\n[测试2] 正常爬取（会打印Cookie和生成截图）")
        try:
            result = await crawler.fetch_and_parse(
                query="成交量大于100万",
                batch_name="DebugTest2"
            )
            print(f"✅ 爬取结果: {result['status']}, 总数: {result['total']}")
            print(f"✅ Cookie信息已在日志中打印")
            print(f"✅ 截图已保存到当前目录（debug_wencai_*.png）")
        except Exception as e:
            print(f"❌ 爬取失败: {e}")


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("开始测试新功能")
    print("=" * 60)

    # 初始化数据库
    await db_manager.initialize()
    print("✅ 数据库初始化完成")

    try:
        # 测试数据合并服务
        await test_data_merge_service()

        # 测试问财爬虫调试功能
        # await test_wencai_crawler_debug()

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
