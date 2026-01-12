#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验收阶段测试脚本
用于手动触发验收测试
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.daily_acceptance_service import daily_acceptance_service
from app.database import db_manager
from loguru import logger


async def main():
    """主函数"""
    print("=" * 80)
    print("验收阶段测试")
    print("=" * 80)
    print()
    
    logger.info("开始验收阶段测试...")
    
    try:
        # 初始化数据库
        await db_manager.initialize()
        
        # 获取数据库会话
        session = db_manager.session_factory()
        
        try:
            # 运行每日验收测试
            print("📊 开始运行每日验收测试...")
            results = await daily_acceptance_service.run_daily_acceptance(session)
            
            # 输出测试结果摘要
            print("\n" + "=" * 80)
            print("验收测试结果摘要")
            print("=" * 80)
            
            # 数据一致性检查
            data_cons = results.get('data_consistency', {})
            redis_cons = data_cons.get('redis_consistency', {})
            print(f"\n✅ Redis一致性: {redis_cons.get('consistent', 0)}/{redis_cons.get('total_checked', 0)} 一致")
            
            db_cons = data_cons.get('database_consistency', {})
            info_vs_score = db_cons.get('stock_info_vs_score_result', {})
            print(f"✅ 数据库一致性: {info_vs_score.get('consistent', 0)}/{info_vs_score.get('total_checked', 0)} 一致")
            
            # 性能指标
            perf = results.get('performance_metrics', {})
            if perf.get('redis_query_time'):
                avg_redis = sum(perf['redis_query_time']) / len(perf['redis_query_time'])
                print(f"✅ Redis查询平均时间: {avg_redis:.4f}秒")
            
            if perf.get('vectorized_calculation_time'):
                avg_vec = sum(perf['vectorized_calculation_time']) / len(perf['vectorized_calculation_time'])
                print(f"✅ 向量化计算平均时间: {avg_vec:.4f}秒")
            
            # 功能测试
            func_tests = results.get('functional_tests', {})
            passed = sum(1 for test in func_tests.values() if test.get('status') == 'passed')
            total = len(func_tests)
            print(f"\n✅ 功能测试: {passed}/{total} 通过")
            
            for test_name, test_result in func_tests.items():
                status = test_result.get('status', 'N/A')
                print(f"   - {test_result.get('test_name', test_name)}: {status}")
            
            # 报告文件位置
            print("\n" + "=" * 80)
            print("验收报告文件")
            print("=" * 80)
            print(f"报告目录: /Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/logs/acceptance/")
            print(f"CSV报告: {results['test_date'].strftime('%Y%m%d')}_acceptance_report.csv")
            print(f"详细报告: {results['test_date'].strftime('%Y%m%d')}_acceptance_detail.txt")
            
            print("\n" + "=" * 80)
            print("验收阶段测试完成！")
            print("=" * 80)
            
        finally:
            # 关闭数据库会话
            await session.close()
            await db_manager.close()
    
    except Exception as e:
        logger.error(f"验收阶段测试失败: {e}")
        print(f"\n❌ 验收阶段测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
