#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端验收测试
验证完整的每日工作流从数据检查到飞书通知的全链路
"""

import pytest
import asyncio
from datetime import date, datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import pandas as pd

from app.services.daily_workflow import DailyWorkflow
from app.services.tdx_data_sync_checker import TdxDataSyncChecker
from app.services.daily_stock_selection_service import DailyStockSelectionService
from app.services.screenshot_service import ScreenshotService
from app.services.feishu_notification_service import FeishuNotificationService
from app.services.feishu_sync_service import FeishuSyncService


class TestEndToEndHappyPath:
    """端到端正常流程测试"""
    
    @pytest.mark.asyncio
    async def test_complete_daily_workflow_success(self):
        """
        验收场景: 完整的每日工作流成功执行
        触发条件: 交易日下午3点后，通达信数据已同步
        预期结果: 
            1. 数据同步检查通过
            2. 选股成功，创建日期命名板块
            3. 截图完成
            4. 飞书同步成功
            5. 日报发送成功
        """
        # Arrange: 构建完整的模拟环境
        trade_date = date(2026, 3, 25)
        
        # 模拟通达信客户端
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = True
        
        # 生成5000条模拟数据（满足完整性检查）
        mock_market_data = pd.DataFrame({
            'code': [f"{i:06d}.SZ" for i in range(5000)],
            'date': [trade_date] * 5000,
            'open': [10.0] * 5000,
            'close': [11.0] * 5000,
            'high': [11.5] * 5000,
            'low': [9.5] * 5000,
            'volume': [1000000] * 5000,
            'amount': [10000000] * 5000
        })
        mock_tdx.get_market_data.return_value = mock_market_data
        mock_tdx.get_more_info.return_value = pd.DataFrame({
            'Close': [11.0],
            'ZTPrice': [12.1],  # 涨停价
            'Open': [10.0]
        })
        mock_tdx.get_user_sector.return_value = []
        mock_tdx.create_sector.return_value = True
        mock_tdx.send_user_block.return_value = True
        
        # 模拟飞书客户端
        mock_feishu = Mock()
        mock_feishu.send_group_message.return_value = {"status": "success", "data": {"message_id": "msg_123"}}
        mock_feishu.create_task_card.return_value = {"status": "success", "data": {"task_id": "task_123"}}
        mock_feishu.add_records.return_value = {"status": "success"}
        mock_feishu.upload_file.return_value = {"status": "success", "data": {"file_token": "file_123"}}
        
        # 创建工作流
        workflow = DailyWorkflow(
            tdx_client=mock_tdx,
            feishu_client=mock_feishu
        )
        
        # Act: 执行完整工作流
        result = await workflow.execute(trade_date)
        
        # Assert: 验证每个阶段的结果
        assert result["status"] == "success", f"工作流执行失败: {result.get('message')}"
        assert result["sector_code"] == "3BL0325", "板块代码不正确"
        assert "completed_phases" in result
        assert "SYNC_CHECK" in result["completed_phases"]
        assert "SELECTION" in result["completed_phases"]
        assert "SCREENSHOT" in result["completed_phases"]
        assert "FEISHU_SYNC" in result["completed_phases"]
        assert "REPORT" in result["completed_phases"]
        
        # 验证飞书通知被调用
        assert mock_feishu.send_group_message.called, "飞书群消息未发送"
    
    @pytest.mark.asyncio
    async def test_data_sync_failure_workflow_pause(self):
        """
        验收场景: 数据同步检查失败，工作流暂停
        触发条件: 通达信客户端离线或数据不完整
        预期结果:
            1. 工作流在SYNC_CHECK阶段暂停
            2. 发送告警通知到飞书群
            3. 创建任务卡片提醒操作员
            4. 可以恢复工作流
        """
        # Arrange
        trade_date = date(2026, 3, 25)
        
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = False  # 模拟离线
        
        mock_feishu = Mock()
        mock_feishu.send_group_message.return_value = {"status": "success"}
        mock_feishu.create_task_card.return_value = {"status": "success"}
        
        workflow = DailyWorkflow(
            tdx_client=mock_tdx,
            feishu_client=mock_feishu
        )
        
        # Act
        result = await workflow.execute(trade_date)
        
        # Assert
        assert result["status"] == "paused"
        assert "SYNC_CHECK" in result["failed_phases"]
        assert workflow.state == "PAUSED"
        assert workflow.can_resume is True
        
        # 验证告警通知已发送
        assert mock_feishu.send_group_message.called, "告警通知未发送"
        assert mock_feishu.create_task_card.called, "任务卡片未创建"
    
    @pytest.mark.asyncio
    async def test_workflow_resume_after_pause(self):
        """
        验收场景: 从暂停状态恢复工作流
        触发条件: 操作员修复问题后手动恢复
        预期结果: 工作流从暂停点继续执行
        """
        # Arrange
        trade_date = date(2026, 3, 25)
        
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = True
        mock_tdx.get_market_data.return_value = pd.DataFrame({
            'Close': [10.0] * 5000,
            'Volume': [1000000] * 5000
        })
        mock_tdx.get_more_info.return_value = pd.DataFrame({'Close': [10.0]})
        mock_tdx.get_user_sector.return_value = []
        mock_tdx.create_sector.return_value = True
        mock_tdx.send_user_block.return_value = True
        
        mock_feishu = Mock()
        mock_feishu.send_group_message.return_value = {"status": "success"}
        mock_feishu.create_task_card.return_value = {"status": "success"}
        mock_feishu.add_records.return_value = {"status": "success"}
        
        workflow = DailyWorkflow(
            tdx_client=mock_tdx,
            feishu_client=mock_feishu
        )
        
        # 先执行并暂停
        await workflow.start()
        await workflow.complete_sync_check(success=False)
        assert workflow.state == "PAUSED"
        
        # Act: 恢复工作流
        await workflow.resume(skip_sync_check=True)
        
        # Assert
        assert workflow.state == "SELECTION"
        assert workflow.can_resume is False


class TestEndToEdgeCases:
    """端到端边界情况测试"""
    
    @pytest.mark.asyncio
    async def test_empty_stock_selection(self):
        """
        验收场景: 选股结果为空
        预期结果: 正常创建空板块，发送空结果报告
        """
        # Arrange
        trade_date = date(2026, 3, 25)
        
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = True
        # 生成数据但没有符合策略的股票
        mock_tdx.get_market_data.return_value = pd.DataFrame({
            'Close': [10.0] * 5000,
            'Volume': [100000] * 5000,  # 正常成交量，不满足3倍量
            'Open': [10.0] * 5000,
            'High': [10.1] * 5000,
            'Low': [9.9] * 5000
        })
        mock_tdx.get_more_info.return_value = pd.DataFrame({
            'Close': [10.0],
            'ZTPrice': [11.0]  # 未达到涨停
        })
        mock_tdx.get_user_sector.return_value = []
        mock_tdx.create_sector.return_value = True
        mock_tdx.send_user_block.return_value = True
        
        mock_feishu = Mock()
        mock_feishu.send_group_message.return_value = {"status": "success"}
        mock_feishu.add_records.return_value = {"status": "success"}
        
        workflow = DailyWorkflow(
            tdx_client=mock_tdx,
            feishu_client=mock_feishu
        )
        
        # Act
        result = await workflow.execute(trade_date)
        
        # Assert
        assert result["status"] == "success"
        assert result["selected_count"] == 0
        assert result["sector_code"] == "3BL0325"
    
    @pytest.mark.asyncio
    async def test_feishu_sync_partial_failure(self):
        """
        验收场景: 飞书同步部分失败
        预期结果: 记录失败项，继续后续流程
        """
        # Arrange
        trade_date = date(2026, 3, 25)
        
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = True
        mock_tdx.get_market_data.return_value = pd.DataFrame({
            'Close': [10.0] * 5000,
            'Volume': [1000000] * 5000
        })
        mock_tdx.get_more_info.return_value = pd.DataFrame({'Close': [10.0]})
        mock_tdx.get_user_sector.return_value = []
        mock_tdx.create_sector.return_value = True
        mock_tdx.send_user_block.return_value = True
        
        mock_feishu = Mock()
        mock_feishu.send_group_message.return_value = {"status": "success"}
        # 模拟部分同步失败
        mock_feishu.add_records.side_effect = [
            {"status": "success"},  # 第一批成功
            {"status": "failed", "error": "rate limit"},  # 第二批失败
            {"status": "success"}  # 第三批成功
        ]
        
        workflow = DailyWorkflow(
            tdx_client=mock_tdx,
            feishu_client=mock_feishu
        )
        
        # Act
        result = await workflow.execute(trade_date)
        
        # Assert
        assert result["status"] == "success"  # 整体成功


class TestEndToEndIntegration:
    """端到端集成测试"""
    
    @pytest.mark.asyncio
    async def test_all_services_integration(self):
        """
        验收场景: 所有服务协同工作
        验证服务之间的调用链
        """
        # Arrange
        trade_date = date(2026, 3, 25)
        
        # 创建真实服务实例（使用mock客户端）
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = True
        mock_tdx.get_market_data.return_value = pd.DataFrame({
            'Close': [10.0] * 5000,
            'Volume': [1000000] * 5000,
            'Open': [9.5] * 5000,
            'High': [10.5] * 5000,
            'Low': [9.0] * 5000,
            'Amount': [10000000] * 5000
        })
        mock_tdx.get_more_info.return_value = pd.DataFrame({
            'Close': [10.0],
            'ZTPrice': [11.0]
        })
        mock_tdx.get_user_sector.return_value = []
        mock_tdx.create_sector.return_value = True
        mock_tdx.send_user_block.return_value = True
        
        mock_feishu = Mock()
        mock_feishu.send_group_message.return_value = {"status": "success"}
        mock_feishu.create_task_card.return_value = {"status": "success"}
        mock_feishu.add_records.return_value = {"status": "success"}
        mock_feishu.upload_file.return_value = {"status": "success"}
        
        # 创建各个服务
        data_checker = TdxDataSyncChecker(tdx_client=mock_tdx)
        selection_service = DailyStockSelectionService(tdx_client=mock_tdx)
        screenshot_service = ScreenshotService()
        notification_service = FeishuNotificationService(feishu_client=mock_feishu)
        sync_service = FeishuSyncService(feishu_client=mock_feishu)
        
        # Act & Assert: 验证服务链
        
        # 1. 数据同步检查
        sync_result = data_checker.check_daily_data_sync(trade_date)
        assert sync_result["status"] == "success"
        
        # 2. 选股服务
        selection_result = selection_service.execute_daily_selection(trade_date)
        assert selection_result["status"] == "success"
        
        # 3. 飞书同步
        selection_data = [
            {"stock_code": "000001.SZ", "strategy": "3x_volume", "date": trade_date},
            {"stock_code": "600000.SH", "strategy": "limit_up", "date": trade_date}
        ]
        sync_result = await sync_service.sync_selection_to_feishu(selection_data)
        assert sync_result["status"] == "success"
        
        # 4. 通知服务
        report_data = {
            "date": trade_date,
            "sector_code": "3BL0325",
            "sector_name": "3倍量20260325",
            "selected_count": 10,
            "strategies": {"3x_volume": 5, "limit_up": 3, "gap": 2}
        }
        await notification_service.send_daily_report(
            chat_id="test_chat",
            report_data=report_data
        )
        assert mock_feishu.send_group_message.called


class TestEndToEndPerformance:
    """端到端性能测试"""
    
    @pytest.mark.asyncio
    async def test_workflow_execution_time(self):
        """
        验收场景: 工作流执行时间
        预期结果: 完整工作流应在5分钟内完成
        """
        import time
        
        # Arrange
        trade_date = date(2026, 3, 25)
        
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = True
        mock_tdx.get_market_data.return_value = pd.DataFrame({
            'Close': [10.0] * 5000,
            'Volume': [1000000] * 5000
        })
        mock_tdx.get_more_info.return_value = pd.DataFrame({'Close': [10.0]})
        mock_tdx.get_user_sector.return_value = []
        mock_tdx.create_sector.return_value = True
        mock_tdx.send_user_block.return_value = True
        
        mock_feishu = Mock()
        mock_feishu.send_group_message.return_value = {"status": "success"}
        mock_feishu.add_records.return_value = {"status": "success"}
        
        workflow = DailyWorkflow(
            tdx_client=mock_tdx,
            feishu_client=mock_feishu
        )
        
        # Act
        start_time = time.time()
        result = await workflow.execute(trade_date)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Assert
        assert result["status"] == "success"
        assert execution_time < 300, f"工作流执行时间过长: {execution_time}秒"


class TestEndToEndDataConsistency:
    """端到端数据一致性测试"""
    
    @pytest.mark.asyncio
    async def test_sector_naming_convention(self):
        """
        验收场景: 板块命名规范
        预期结果: 板块代码格式为 3BL{MMDD}
        """
        test_cases = [
            (date(2026, 3, 25), "3BL0325"),
            (date(2026, 12, 31), "3BL1231"),
            (date(2026, 1, 1), "3BL0101"),
        ]
        
        for trade_date, expected_code in test_cases:
            mock_tdx = Mock()
            mock_tdx.is_connected.return_value = True
            mock_tdx.get_market_data.return_value = pd.DataFrame({
                'Close': [10.0] * 5000,
                'Volume': [1000000] * 5000
            })
            mock_tdx.get_more_info.return_value = pd.DataFrame({'Close': [10.0]})
            mock_tdx.get_user_sector.return_value = []
            mock_tdx.create_sector.return_value = True
            mock_tdx.send_user_block.return_value = True
            
            mock_feishu = Mock()
            mock_feishu.send_group_message.return_value = {"status": "success"}
            mock_feishu.add_records.return_value = {"status": "success"}
            
            workflow = DailyWorkflow(
                tdx_client=mock_tdx,
                feishu_client=mock_feishu
            )
            
            result = await workflow.execute(trade_date)
            
            assert result["sector_code"] == expected_code, \
                f"日期 {trade_date} 的板块代码应为 {expected_code}, 实际为 {result['sector_code']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
