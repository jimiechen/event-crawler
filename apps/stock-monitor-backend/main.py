#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票监控后端主程序
整合所有服务，提供统一的入口点
"""

import sys
import os
import asyncio
import argparse
from datetime import date, datetime
from pathlib import Path
from typing import Optional
from loguru import logger

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 添加通达信路径
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

from app.services.daily_workflow import DailyWorkflow
from app.services.tdx_data_sync_checker import TdxDataSyncChecker
from app.services.daily_stock_selection_service import DailyStockSelectionService
from app.services.screenshot_service import ScreenshotService
from app.services.feishu_notification_service import FeishuNotificationService
from app.services.feishu_sync_service import FeishuSyncService
from app.services.tdx_selection_service import TdxSelectionService
from app.services.tdx_selection_workflow import TdxSelectionWorkflow, run_tdx_selection_workflow
from app.services.feishu_client import FeishuClient


class StockMonitorApp:
    """
    股票监控应用主类
    整合所有服务，提供完整的每日工作流
    """
    
    def __init__(self):
        """初始化应用"""
        self.tdx_client = None
        self.feishu_client = None
        self.workflow = None
        self._setup_logging()
        
    def _setup_logging(self):
        """配置日志"""
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # 移除默认处理器
        logger.remove()
        
        # 添加控制台输出
        logger.add(
            sys.stdout,
            level="INFO",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        
        # 添加文件输出
        logger.add(
            log_dir / "stock_monitor_{time:YYYY-MM-DD}.log",
            rotation="00:00",
            retention="30 days",
            level="DEBUG",
            encoding="utf-8"
        )
        
    def initialize_tdx(self) -> bool:
        """
        初始化通达信连接
        
        Returns:
            bool: 是否成功
        """
        try:
            from tqcenter import tq
            tq.initialize(__file__)
            self.tdx_client = tq
            logger.info("✅ 通达信连接初始化成功")
            return True
        except Exception as e:
            logger.error(f"❌ 通达信连接失败: {e}")
            return False
    
    def initialize_feishu(self, app_id: Optional[str] = None, app_secret: Optional[str] = None) -> bool:
        """
        初始化飞书客户端
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
            
        Returns:
            bool: 是否成功
        """
        try:
            # 使用真实的飞书客户端
            self.feishu_client = FeishuClient()
            
            # 测试获取访问令牌
            token = self.feishu_client._get_access_token()
            if token:
                logger.info("✅ 飞书客户端初始化成功")
                return True
            else:
                logger.warning("⚠️ 飞书客户端初始化失败，但会继续运行")
                return False
        except Exception as e:
            logger.error(f"❌ 飞书客户端初始化失败: {e}")
            return False
    
    async def run_daily_workflow(self, trade_date: Optional[date] = None, use_tdx_workflow: bool = True) -> dict:
        """
        执行每日工作流
        
        Args:
            trade_date: 交易日期，默认为今天
            use_tdx_workflow: 是否使用TDX选股工作流（同步到数据库并区分问财来源）
            
        Returns:
            dict: 执行结果
        """
        if trade_date is None:
            trade_date = date.today()
        
        logger.info(f"\n{'='*60}")
        logger.info(f"开始执行每日工作流: {trade_date}")
        if use_tdx_workflow:
            logger.info("模式: TDX选股工作流（数据库同步+飞书通知）")
        logger.info(f"{'='*60}\n")
        
        # 初始化服务
        if not self.tdx_client:
            if not self.initialize_tdx():
                return {"status": "failed", "reason": "通达信初始化失败"}
        
        if not self.feishu_client:
            self.initialize_feishu()
        
        try:
            if use_tdx_workflow:
                # 使用新的TDX选股工作流
                result = await run_tdx_selection_workflow(
                    tdx_client=self.tdx_client,
                    trade_date=trade_date,
                    feishu_client=self.feishu_client
                )
            else:
                # 使用旧的每日工作流
                self.workflow = DailyWorkflow(
                    tdx_client=self.tdx_client,
                    feishu_client=self.feishu_client
                )
                result = await self.workflow.execute(trade_date)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"工作流执行完成")
            logger.info(f"状态: {result['status']}")
            logger.info(f"选中股票: {result.get('selected_count', 0)} 只")
            if result.get('batch_id'):
                logger.info(f"批次ID: {result['batch_id']}")
            logger.info(f"{'='*60}\n")
            
            return result
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "failed", "reason": str(e)}
    
    async def run_backtest(self, start_date: date, end_date: date) -> list:
        """
        执行回测
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            list: 每日结果列表
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"开始回测: {start_date} 至 {end_date}")
        logger.info(f"{'='*60}\n")
        
        # 初始化
        if not self.tdx_client:
            if not self.initialize_tdx():
                logger.error("通达信初始化失败，无法执行回测")
                return []
        
        # 生成交易日列表
        from datetime import timedelta
        
        def is_trading_day(d: date) -> bool:
            return d.weekday() < 5
        
        trading_days = []
        current = start_date
        while current <= end_date:
            if is_trading_day(current):
                trading_days.append(current)
            current += timedelta(days=1)
        
        logger.info(f"共 {len(trading_days)} 个交易日")
        
        # 执行每日回测
        results = []
        for i, trade_date in enumerate(trading_days):
            logger.info(f"\n[{i+1}/{len(trading_days)}] 回测日期: {trade_date}")
            
            result = await self.run_daily_workflow(trade_date)
            results.append(result)
            
            # 暂停一下，避免请求过快
            await asyncio.sleep(1)
        
        # 统计结果
        success_count = sum(1 for r in results if r['status'] == 'success')
        total_selected = sum(r.get('selected_count', 0) for r in results)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"回测完成")
        logger.info(f"总交易日: {len(trading_days)}")
        logger.info(f"成功: {success_count}")
        logger.info(f"总选中: {total_selected} 只")
        logger.info(f"平均每日: {total_selected/len(trading_days):.2f} 只")
        logger.info(f"{'='*60}\n")
        
        return results
    
    def check_data_sync(self, trade_date: Optional[date] = None) -> dict:
        """
        检查数据同步状态
        
        Args:
            trade_date: 交易日期
            
        Returns:
            dict: 检查结果
        """
        if trade_date is None:
            trade_date = date.today()
        
        if not self.tdx_client:
            if not self.initialize_tdx():
                return {"status": "failed", "reason": "通达信初始化失败"}
        
        checker = TdxDataSyncChecker(tdx_client=self.tdx_client)
        result = checker.check_daily_data_sync(trade_date)
        
        logger.info(f"\n数据同步检查结果:")
        logger.info(f"  状态: {result['status']}")
        logger.info(f"  客户端在线: {result['checks']['client_online']}")
        logger.info(f"  数据完整: {result['checks']['data_complete']}")
        logger.info(f"  时间戳有效: {result['checks']['timestamp_valid']}")
        logger.info(f"  数据合理: {result['checks']['data_reasonable']}")
        
        return result


def parse_date(date_str: str) -> date:
    """解析日期字符串"""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="股票监控后端")
    parser.add_argument(
        "--mode",
        choices=["daily", "backtest", "check", "tdx-select"],
        default="daily",
        help="运行模式: daily=每日选股, backtest=回测, check=数据检查, tdx-select=TDX选股并同步到数据库"
    )
    parser.add_argument(
        "--date",
        type=parse_date,
        help="交易日期 (格式: YYYY-MM-DD)"
    )
    parser.add_argument(
        "--start-date",
        type=parse_date,
        help="回测开始日期 (格式: YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        type=parse_date,
        help="回测结束日期 (格式: YYYY-MM-DD)"
    )
    parser.add_argument(
        "--sector-code",
        type=str,
        help="板块代码 (如: 3BL0325)"
    )
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="使用旧版工作流（不同步到数据库）"
    )
    
    args = parser.parse_args()
    
    # 创建应用实例
    app = StockMonitorApp()
    
    if args.mode == "daily":
        # 每日选股模式
        trade_date = args.date or date.today()
        result = await app.run_daily_workflow(trade_date, use_tdx_workflow=not args.legacy)
        
        if result['status'] == 'success':
            print(f"\n✅ 每日选股完成: 选中 {result.get('selected_count', 0)} 只股票")
            if result.get('batch_id'):
                print(f"   批次ID: {result['batch_id']}")
        else:
            print(f"\n❌ 每日选股失败: {result.get('reason', '未知错误')}")
            sys.exit(1)
    
    elif args.mode == "tdx-select":
        # TDX选股并同步到数据库
        trade_date = args.date or date.today()
        # 板块代码格式: 3BL260201 (年份后两位+月份+日期)
        sector_code = args.sector_code or f"3BL{trade_date.strftime('%y%m%d')}"
        
        print(f"\n开始TDX选股: {trade_date}, 板块: {sector_code}")
        
        # 初始化
        if not app.tdx_client:
            if not app.initialize_tdx():
                print("❌ 通达信初始化失败")
                sys.exit(1)
        
        if not app.feishu_client:
            app.initialize_feishu()
        
        # 执行选股工作流
        result = await run_tdx_selection_workflow(
            tdx_client=app.tdx_client,
            trade_date=trade_date,
            sector_code=sector_code,
            feishu_client=app.feishu_client
        )
        
        if result['status'] == 'success':
            print(f"\n✅ TDX选股完成: 选中 {result.get('selected_count', 0)} 只股票")
            print(f"   批次ID: {result['batch_id']}")
            print(f"   板块: {sector_code}")
            print(f"   数据已同步到数据库，来源标记为: tdx")
        else:
            print(f"\n❌ TDX选股失败: {result.get('reason', '未知错误')}")
            sys.exit(1)
    
    elif args.mode == "backtest":
        # 回测模式
        start_date = args.start_date or date(2026, 2, 1)
        end_date = args.end_date or date.today()
        
        results = await app.run_backtest(start_date, end_date)
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        print(f"\n✅ 回测完成: {success_count}/{len(results)} 天成功")
    
    elif args.mode == "check":
        # 数据检查模式
        trade_date = args.date or date.today()
        result = app.check_data_sync(trade_date)
        
        if result['status'] == 'success':
            print(f"\n✅ 数据同步检查通过")
        else:
            print(f"\n❌ 数据同步检查未通过: {result.get('message', '')}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
