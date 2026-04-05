#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行最近3天的选股任务，测试新多维表格
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

import asyncio
from datetime import date, timedelta
from loguru import logger

# 初始化通达信
from tqcenter import tq


async def run_selection_for_date(trade_date: date):
    """执行指定日期的选股任务"""
    
    logger.info("=" * 60)
    logger.info(f"📊 开始执行选股: {trade_date}")
    logger.info("=" * 60)
    
    try:
        # 导入选股工作流
        from app.services.tdx_selection_workflow import TdxSelectionWorkflow
        from app.services.feishu_client import FeishuClient
        
        # 初始化飞书客户端
        feishu_client = FeishuClient()
        
        # 创建选股服务（飞书客户端在初始化时传入）
        selection_service = TdxSelectionWorkflow(
            tdx_client=tq,
            feishu_client=feishu_client
        )
        
        # 板块代码格式: 3BL260401 (年份后两位+月份+日期)
        sector_code = f"3BL{trade_date.strftime('%y%m%d')}"
        
        # 执行选股（跳过截图）
        result = await selection_service.execute_selection(
            trade_date=trade_date,
            sector_code=sector_code,
            skip_screenshot=True
        )
        
        # 输出结果
        if result['status'] == 'success':
            logger.info(f"✅ 选股完成: {trade_date}")
            logger.info(f"   选中股票: {result.get('selected_count', 0)} 只")
            logger.info(f"   板块代码: {sector_code}")
            logger.info(f"   批次ID: {result.get('batch_id', 'N/A')}")
        else:
            logger.error(f"❌ 选股失败: {trade_date} - {result.get('reason', '未知错误')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 选股异常: {trade_date} - {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "failed", "error": str(e)}


async def main():
    """主函数 - 执行最近3天选股"""
    
    logger.info("=" * 60)
    logger.info("🚀 开始执行最近3天选股任务")
    logger.info("=" * 60)
    
    # 初始化通达信
    logger.info("[初始化] 连接通达信客户端...")
    tq.initialize(__file__)
    logger.info("✅ 通达信连接成功")
    
    # 计算最近3天（工作日）
    today = date.today()
    dates_to_run = []
    
    # 获取最近3个交易日
    check_date = today
    while len(dates_to_run) < 3:
        # 跳过周末
        if check_date.weekday() < 5:  # 0-4 是周一到周五
            dates_to_run.append(check_date)
        check_date -= timedelta(days=1)
    
    # 反转顺序，从最早到最晚
    dates_to_run.reverse()
    
    logger.info(f"将执行以下日期的选股: {[d.strftime('%Y-%m-%d') for d in dates_to_run]}")
    
    # 执行选股
    results = []
    for trade_date in dates_to_run:
        result = await run_selection_for_date(trade_date)
        results.append({
            "date": trade_date,
            "result": result
        })
        
        # 间隔5秒，避免请求过快
        await asyncio.sleep(5)
    
    # 汇总报告
    logger.info("\n" + "=" * 60)
    logger.info("📋 选股任务执行汇总")
    logger.info("=" * 60)
    
    success_count = 0
    failed_count = 0
    total_selected = 0
    
    for item in results:
        trade_date = item["date"]
        result = item["result"]
        
        if result.get("status") == "success":
            success_count += 1
            selected = result.get("selected_count", 0)
            total_selected += selected
            logger.info(f"✅ {trade_date}: 选中 {selected} 只")
        else:
            failed_count += 1
            logger.error(f"❌ {trade_date}: 失败")
    
    logger.info("-" * 60)
    logger.info(f"成功: {success_count}/{len(results)}")
    logger.info(f"失败: {failed_count}/{len(results)}")
    logger.info(f"总选中: {total_selected} 只")
    logger.info("=" * 60)
    
    # 检查飞书表格数据
    logger.info("\n[检查] 飞书多维表格数据...")
    await check_bitable_data()
    
    logger.info("\n🎉 所有任务执行完成!")


async def check_bitable_data():
    """检查飞书多维表格中的数据"""
    
    try:
        from app.services.feishu_client import FeishuClient
        
        feishu_client = FeishuClient()
        
        # 获取访问令牌
        access_token = feishu_client._get_access_token()
        if not access_token:
            logger.error("❌ 无法获取飞书访问令牌")
            return
        
        import requests
        
        # 查询表格记录
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{feishu_client.app_token}/tables/{feishu_client.table_id}/records"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        params = {"page_size": 100}
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        result = response.json()
        
        if result.get("code") == 0:
            records = result.get("data", {}).get("items", [])
            total = result.get("data", {}).get("total", 0)
            
            logger.info(f"✅ 飞书表格查询成功")
            logger.info(f"   总记录数: {total}")
            logger.info(f"   返回记录数: {len(records)}")
            
            if records:
                logger.info("\n   最近10条记录:")
                for i, record in enumerate(records[:10], 1):
                    fields = record.get("fields", {})
                    stock_code = fields.get("股票代码", "N/A")
                    stock_name = fields.get("股票名称", "N/A")
                    trade_date = fields.get("选股日期", "N/A")
                    logger.info(f"   {i}. {stock_code} {stock_name} - {trade_date}")
        else:
            logger.error(f"❌ 查询失败: {result}")
            
    except Exception as e:
        logger.error(f"❌ 检查表格数据异常: {e}")


if __name__ == "__main__":
    asyncio.run(main())
