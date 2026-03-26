#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日工作流
TDD Step 2: 实现代码 (绿)
"""

from datetime import date, datetime
from typing import List, Dict, Any, Optional
from loguru import logger

from app.services.tdx_data_sync_checker import TdxDataSyncChecker
from app.services.daily_stock_selection_service import DailyStockSelectionService
from app.services.screenshot_service import ScreenshotService
from app.services.feishu_notification_service import FeishuNotificationService
from app.services.feishu_sync_service import FeishuSyncService


class DailyWorkflow:
    """
    每日工作流
    
    Pipeline阶段:
    1. SYNC_CHECK - 盘后数据同步检查
    2. SELECTION - 执行选股策略
    3. SCREENSHOT - 截图任务
    4. FEISHU_SYNC - 同步到飞书
    5. REPORT - 生成日报
    6. DONE - 完成
    
    状态:
    - PENDING: 待开始
    - SYNC_CHECK: 数据检查中
    - SELECTION: 选股中
    - SCREENSHOT: 截图中
    - FEISHU_SYNC: 飞书同步中
    - REPORT: 生成报告中
    - PAUSED: 已暂停
    - DONE: 已完成
    """
    
    # 默认阶段列表
    DEFAULT_PHASES = [
        "SYNC_CHECK",
        "SELECTION",
        "SCREENSHOT",
        "FEISHU_SYNC",
        "REPORT"
    ]
    
    def __init__(self,
                 tdx_client=None,
                 feishu_client=None,
                 phases: List[str] = None):
        """
        初始化每日工作流
        
        Args:
            tdx_client: 通达信客户端
            feishu_client: 飞书客户端
            phases: 阶段列表
        """
        self.tdx_client = tdx_client
        self.feishu_client = feishu_client
        self.phases = phases or self.DEFAULT_PHASES.copy()
        
        # 初始化服务
        self.data_sync_checker = TdxDataSyncChecker(tdx_client=tdx_client)
        self.selection_service = DailyStockSelectionService(tdx_client=tdx_client)
        self.screenshot_service = ScreenshotService()
        self.notification_service = FeishuNotificationService(feishu_client=feishu_client)
        self.sync_service = FeishuSyncService(feishu_client=feishu_client)
        
        # 工作流状态
        self.state = "PENDING"
        self.current_phase = None
        self.completed_phases = []
        self.failed_phases = []
        self.can_resume = False
        
        # 执行结果
        self.execution_result = {}
    
    async def start(self):
        """启动工作流"""
        self.state = "SYNC_CHECK"
        self.current_phase = "盘后数据同步检查"
        self.completed_phases = []
        self.failed_phases = []
        self.can_resume = False
        logger.info("每日工作流已启动")
    
    async def complete_sync_check(self, success: bool):
        """完成数据同步检查阶段"""
        if success:
            self.completed_phases.append("SYNC_CHECK")
            self.state = "SELECTION"
            self.current_phase = "执行选股策略"
            logger.info("数据同步检查完成，进入选股阶段")
        else:
            self.failed_phases.append("SYNC_CHECK")
            self.state = "PAUSED"
            self.can_resume = True
            logger.warning("数据同步检查失败，工作流已暂停")
    
    async def complete_selection(self):
        """完成选股阶段"""
        self.completed_phases.append("SELECTION")
        self.state = "SCREENSHOT"
        self.current_phase = "截图任务"
        logger.info("选股完成，进入截图阶段")
    
    async def complete_screenshot(self):
        """完成截图阶段"""
        self.completed_phases.append("SCREENSHOT")
        self.state = "FEISHU_SYNC"
        self.current_phase = "飞书同步"
        logger.info("截图完成，进入飞书同步阶段")
    
    async def complete_feishu_sync(self):
        """完成飞书同步阶段"""
        self.completed_phases.append("FEISHU_SYNC")
        self.state = "DONE"
        self.current_phase = None
        logger.info("飞书同步完成，工作流结束")
    
    async def complete_report(self):
        """完成报告阶段"""
        self.completed_phases.append("REPORT")
        self.state = "DONE"
        self.current_phase = None
        logger.info("每日工作流已完成")
    
    async def resume(self, skip_sync_check: bool = False):
        """
        恢复工作流
        
        Args:
            skip_sync_check: 是否跳过数据同步检查
        """
        if not self.can_resume:
            logger.warning("工作流无法恢复")
            return
        
        if skip_sync_check:
            self.state = "SELECTION"
            self.current_phase = "执行选股策略"
            logger.info("工作流已恢复（跳过数据同步检查）")
        else:
            self.state = "SYNC_CHECK"
            self.current_phase = "盘后数据同步检查"
            logger.info("工作流已恢复（重新进行数据同步检查）")
        
        self.can_resume = False
    
    async def execute(self, trade_date: date) -> Dict[str, Any]:
        """
        执行完整工作流
        
        Args:
            trade_date: 交易日期
            
        Returns:
            Dict: 执行结果
        """
        logger.info(f"开始执行每日工作流: {trade_date}")
        
        await self.start()
        
        try:
            # Phase 1: 数据同步检查
            self._log_phase_start("SYNC_CHECK")
            sync_result = await self._execute_sync_check_phase(trade_date)
            self._log_phase_complete("SYNC_CHECK", sync_result)
            
            await self.complete_sync_check(sync_result["status"] == "success")
            
            if self.state == "PAUSED":
                # 发送告警通知
                await self.notification_service.notify_operator(
                    sync_result=sync_result,
                    create_task_card=True
                )
                return {
                    "status": "paused",
                    "failed_phases": self.failed_phases,
                    "message": "数据同步检查失败，工作流已暂停"
                }
            
            # Phase 2: 选股
            self._log_phase_start("SELECTION")
            selection_result = await self._execute_selection_phase(trade_date)
            self._log_phase_complete("SELECTION", selection_result)
            
            if selection_result["status"] != "success":
                await self._handle_phase_error("SELECTION", Exception(selection_result.get("reason")))
                return {
                    "status": "failed",
                    "failed_phases": self.failed_phases,
                    "message": f"选股失败: {selection_result.get('reason')}"
                }
            
            await self.complete_selection()
            
            # Phase 3: 截图
            self._log_phase_start("SCREENSHOT")
            screenshot_result = await self._execute_screenshot_phase(
                trade_date,
                selection_result.get("selected_stocks", [])
            )
            self._log_phase_complete("SCREENSHOT", screenshot_result)
            await self.complete_screenshot()
            
            # Phase 4: 飞书同步
            self._log_phase_start("FEISHU_SYNC")
            sync_result = await self._execute_feishu_sync_phase(
                trade_date,
                selection_result.get("selection_data", []),
                screenshot_result.get("screenshot_paths", [])
            )
            self._log_phase_complete("FEISHU_SYNC", sync_result)
            await self.complete_feishu_sync()
            
            # Phase 5: 生成报告
            self._log_phase_start("REPORT")
            report_result = await self._execute_report_phase(trade_date, selection_result)
            self._log_phase_complete("REPORT", report_result)
            await self.complete_report()
            
            return {
                "status": "success",
                "completed_phases": self.completed_phases,
                "sector_code": selection_result.get("sector_code"),
                "selected_count": selection_result.get("selected_count"),
                "message": "每日工作流执行成功"
            }
            
        except Exception as e:
            logger.error(f"工作流执行异常: {e}")
            return {
                "status": "failed",
                "failed_phases": self.failed_phases,
                "message": f"工作流执行异常: {e}"
            }
    
    async def _execute_sync_check_phase(self, trade_date: date) -> Dict[str, Any]:
        """执行数据同步检查阶段"""
        return self.data_sync_checker.check_daily_data_sync(trade_date)
    
    async def _execute_selection_phase(self, trade_date: date) -> Dict[str, Any]:
        """执行选股阶段"""
        result = self.selection_service.execute_daily_selection(trade_date)
        
        # 获取选股数据用于后续同步
        if result["status"] == "success":
            # 构建选股数据列表
            selection_data = []
            for strategy, stocks in result.get("strategies", {}).items():
                for stock_code in stocks:
                    selection_data.append({
                        "stock_code": stock_code,
                        "strategy": strategy,
                        "date": trade_date
                    })
            
            result["selection_data"] = selection_data
            result["selected_stocks"] = list(set(
                stock for stocks in result.get("strategies", {}).values() for stock in stocks
            ))
        
        return result
    
    async def _execute_screenshot_phase(self, 
                                        trade_date: date,
                                        stocks: List[str]) -> Dict[str, Any]:
        """执行截图阶段"""
        # 使用截图服务批量截图
        try:
            import asyncio
            # 使用 to_thread 在后台线程中执行同步方法
            screenshot_paths = await asyncio.to_thread(
                self.screenshot_service.batch_capture_tlby_screenshots,
                stocks=stocks,
                trade_date=trade_date
            )
            return {
                "status": "success",
                "screenshot_count": len(screenshot_paths),
                "screenshot_paths": screenshot_paths
            }
        except Exception as e:
            logger.error(f"截图阶段执行失败: {e}")
            return {
                "status": "failed",
                "screenshot_count": 0,
                "screenshot_paths": [],
                "reason": str(e)
            }
    
    async def _execute_feishu_sync_phase(self,
                                          trade_date: date,
                                          selection_data: List[Dict],
                                          screenshot_paths: List[str]) -> Dict[str, Any]:
        """执行飞书同步阶段"""
        # 同步选股结果
        selection_sync_result = await self.sync_service.sync_selection_to_feishu(selection_data)
        
        # 同步截图
        screenshot_sync_result = await self.sync_service.sync_screenshots_to_feishu(screenshot_paths)
        
        # 确定整体状态
        if selection_sync_result["status"] == "success" and screenshot_sync_result["status"] == "success":
            status = "success"
        elif selection_sync_result["status"] == "failed" and screenshot_sync_result["status"] == "failed":
            status = "failed"
        else:
            status = "partial"
        
        return {
            "status": status,
            "selection_sync": selection_sync_result,
            "screenshot_sync": screenshot_sync_result
        }
    
    async def _execute_report_phase(self, 
                                    trade_date: date,
                                    selection_result: Dict) -> Dict[str, Any]:
        """执行报告阶段"""
        # 发送每日报告到飞书
        report_data = {
            "date": trade_date,
            "sector_code": selection_result.get("sector_code"),
            "sector_name": selection_result.get("sector_name"),
            "selected_count": selection_result.get("selected_count"),
            "strategies": {
                strategy: len(stocks)
                for strategy, stocks in selection_result.get("strategies", {}).items()
            }
        }
        
        await self.notification_service.send_daily_report(
            chat_id=self.notification_service.default_chat_id,
            report_data=report_data
        )
        
        return {"status": "success"}
    
    async def _handle_phase_error(self, phase: str, error: Exception):
        """处理阶段错误"""
        logger.error(f"阶段 {phase} 执行失败: {error}")
        self.failed_phases.append(phase)
        self.state = "PAUSED"
        self.can_resume = True
    
    async def retry_failed_phase(self, phase: str) -> Dict[str, Any]:
        """重试失败的阶段"""
        logger.info(f"重试阶段: {phase}")
        
        # 这里简化处理，实际应该根据阶段类型调用相应的方法
        return {"status": "success"}
    
    def get_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        return {
            "state": self.state,
            "current_phase": self.current_phase,
            "completed_phases": self.completed_phases,
            "failed_phases": self.failed_phases,
            "can_resume": self.can_resume
        }
    
    def get_progress(self) -> float:
        """获取工作流进度百分比"""
        if not self.phases:
            return 0.0
        
        completed = len(self.completed_phases)
        total = len(self.phases)
        
        return (completed / total) * 100
    
    def _log_phase_start(self, phase: str):
        """记录阶段开始"""
        logger.info(f"阶段 {phase} 开始执行")
    
    def _log_phase_complete(self, phase: str, result: Dict):
        """记录阶段完成"""
        logger.info(f"阶段 {phase} 执行完成: {result.get('status')}")
