#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日工作流单元测试
TDD Step 1: 编写测试用例 (红)
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, AsyncMock, patch, call
from typing import List, Dict, Any, Optional

# 被测试的类 (先定义接口，稍后实现)
from app.services.daily_workflow import DailyWorkflow


class TestWorkflowStateMachine:
    """测试工作流状态机"""
    
    @pytest.mark.asyncio
    async def test_workflow_transitions(self):
        """
        测试场景: 工作流状态转换
        预期结果: 状态按预期流转
        """
        # Arrange
        workflow = DailyWorkflow()
        
        # Act & Assert
        assert workflow.state == "PENDING"
        
        await workflow.start()
        assert workflow.state == "SYNC_CHECK"
        
        await workflow.complete_sync_check(success=True)
        assert workflow.state == "SELECTION"
        
        await workflow.complete_selection()
        assert workflow.state == "SCREENSHOT"
        
        await workflow.complete_screenshot()
        assert workflow.state == "FEISHU_SYNC"
        
        await workflow.complete_feishu_sync()
        assert workflow.state == "DONE"
    
    @pytest.mark.asyncio
    async def test_workflow_pause_on_sync_failure(self):
        """
        测试场景: 数据同步检查失败时暂停
        预期结果: 状态变为PAUSED
        """
        # Arrange
        workflow = DailyWorkflow()
        await workflow.start()
        
        # Act
        await workflow.complete_sync_check(success=False)
        
        # Assert
        assert workflow.state == "PAUSED"
        assert workflow.can_resume is True


class TestWorkflowResume:
    """测试工作流恢复"""
    
    @pytest.mark.asyncio
    async def test_resume_from_pause(self):
        """
        测试场景: 从暂停状态恢复
        预期结果: 工作流继续执行
        """
        # Arrange
        workflow = DailyWorkflow()
        await workflow.start()
        await workflow.complete_sync_check(success=False)
        assert workflow.state == "PAUSED"
        
        # Act
        await workflow.resume(skip_sync_check=True)
        
        # Assert
        assert workflow.state == "SELECTION"
    
    @pytest.mark.asyncio
    async def test_resume_with_sync_check(self):
        """
        测试场景: 恢复时重新进行同步检查
        预期结果: 从SYNC_CHECK状态开始
        """
        # Arrange
        workflow = DailyWorkflow()
        await workflow.start()
        await workflow.complete_sync_check(success=False)
        assert workflow.state == "PAUSED"
        
        # Act
        await workflow.resume(skip_sync_check=False)
        
        # Assert
        assert workflow.state == "SYNC_CHECK"


class TestWorkflowExecution:
    """测试工作流执行"""
    
    @pytest.mark.asyncio
    async def test_execute_complete_workflow(self):
        """
        测试场景: 执行完整工作流
        预期结果: 所有阶段成功完成
        """
        # Arrange
        import pandas as pd
        
        # 创建模拟的DataFrame
        mock_df = pd.DataFrame({
            'Close': [10.0] * 5000,
            'Volume': [1000000] * 5000,
            'Amount': [10000000] * 5000
        })
        
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = True
        mock_tdx.get_market_data.return_value = mock_df
        mock_tdx.get_more_info.return_value = pd.DataFrame({'Close': [10.0]})
        mock_tdx.get_user_sector.return_value = []
        mock_tdx.create_sector.return_value = True
        mock_tdx.send_user_block.return_value = True
        
        mock_feishu = Mock()
        mock_feishu.send_group_message.return_value = {"status": "success"}
        mock_feishu.add_records.return_value = {"status": "success"}
        mock_feishu.create_task_card.return_value = {"status": "success"}
        
        workflow = DailyWorkflow(tdx_client=mock_tdx, feishu_client=mock_feishu)
        
        # Act
        result = await workflow.execute(date(2026, 3, 25))
        
        # Assert
        assert result["status"] == "success"
        assert result["completed_phases"] == ["SYNC_CHECK", "SELECTION", "SCREENSHOT", "FEISHU_SYNC", "REPORT"]
    
    @pytest.mark.asyncio
    async def test_execute_workflow_with_failure(self):
        """
        测试场景: 工作流执行失败
        预期结果: 记录失败阶段
        """
        # Arrange
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = False  # 模拟客户端离线
        
        mock_feishu = Mock()
        mock_feishu.send_group_message.return_value = {"status": "success"}
        
        workflow = DailyWorkflow(tdx_client=mock_tdx, feishu_client=mock_feishu)
        
        # Act
        result = await workflow.execute(date(2026, 3, 25))
        
        # Assert
        assert result["status"] == "paused"
        assert "SYNC_CHECK" in result["failed_phases"]


class TestWorkflowPhaseExecution:
    """测试工作流阶段执行"""
    
    @pytest.mark.asyncio
    async def test_execute_sync_check_phase(self):
        """
        测试场景: 执行数据同步检查阶段
        预期结果: 检查成功
        """
        # Arrange
        import pandas as pd
        
        # 创建模拟的DataFrame - 需要5000行数据满足完整性检查
        mock_df = pd.DataFrame({
            'Close': [10.0] * 5000,
            'Volume': [1000000] * 5000,
            'Amount': [10000000] * 5000
        })
        
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = True
        mock_tdx.get_market_data.return_value = mock_df
        
        workflow = DailyWorkflow(tdx_client=mock_tdx)
        
        # Act
        result = await workflow._execute_sync_check_phase(date(2026, 3, 25))
        
        # Assert
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_execute_selection_phase(self):
        """
        测试场景: 执行选股阶段
        预期结果: 选股成功
        """
        # Arrange
        import pandas as pd
        
        # 创建模拟的DataFrame - 需要5000行数据满足完整性检查
        mock_df = pd.DataFrame({
            'Close': [10.0] * 5000,
            'Volume': [1000000] * 5000,
            'Amount': [10000000] * 5000,
            'Open': [9.5] * 5000,
            'High': [10.5] * 5000,
            'Low': [9.0] * 5000
        })
        
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = True
        mock_tdx.get_market_data.return_value = mock_df
        mock_tdx.get_more_info.return_value = pd.DataFrame({
            'Close': [10.0],
            'ZTPrice': [11.0]  # 涨停价
        })
        mock_tdx.get_user_sector.return_value = []
        mock_tdx.create_sector.return_value = True
        mock_tdx.send_user_block.return_value = True
        
        workflow = DailyWorkflow(tdx_client=mock_tdx)
        
        # Act
        result = await workflow._execute_selection_phase(date(2026, 3, 25))
        
        # Assert
        assert result["status"] == "success"
        assert "sector_code" in result
    
    @pytest.mark.asyncio
    async def test_execute_screenshot_phase(self):
        """
        测试场景: 执行截图阶段
        预期结果: 截图成功
        """
        # Arrange
        workflow = DailyWorkflow()
        
        with patch.object(workflow.screenshot_service, 'batch_capture_tlby_screenshots', return_value=["path1.png", "path2.png"]):
            # Act
            result = await workflow._execute_screenshot_phase(date(2026, 3, 25), ["000001.SZ", "600000.SH"])
            
            # Assert
            assert result["status"] == "success"
            assert result["screenshot_count"] == 2
    
    @pytest.mark.asyncio
    async def test_execute_feishu_sync_phase(self):
        """
        测试场景: 执行飞书同步阶段
        预期结果: 同步成功
        """
        # Arrange
        mock_feishu = Mock()
        mock_feishu.add_records.return_value = {"status": "success"}
        mock_feishu.upload_file.return_value = {"status": "success"}
        
        workflow = DailyWorkflow(feishu_client=mock_feishu)
        
        # Act
        result = await workflow._execute_feishu_sync_phase(
            date(2026, 3, 25),
            [{"stock_code": "000001.SZ"}],
            ["path1.png"]
        )
        
        # Assert
        assert result["status"] == "success"


class TestWorkflowStatus:
    """测试工作流状态查询"""
    
    def test_get_workflow_status(self):
        """
        测试场景: 获取工作流状态
        预期结果: 返回当前状态信息
        """
        # Arrange
        workflow = DailyWorkflow()
        workflow.state = "SELECTION"
        workflow.current_phase = "执行选股策略"
        workflow.completed_phases = ["SYNC_CHECK"]
        
        # Act
        status = workflow.get_status()
        
        # Assert
        assert status["state"] == "SELECTION"
        assert status["current_phase"] == "执行选股策略"
        assert "SYNC_CHECK" in status["completed_phases"]
    
    def test_get_workflow_progress(self):
        """
        测试场景: 获取工作流进度
        预期结果: 返回进度百分比
        """
        # Arrange
        workflow = DailyWorkflow()
        workflow.state = "SELECTION"
        workflow.completed_phases = ["SYNC_CHECK"]
        
        # Act
        progress = workflow.get_progress()
        
        # Assert
        assert 0 < progress < 100


class TestWorkflowConfiguration:
    """测试工作流配置"""
    
    def test_default_configuration(self):
        """
        测试场景: 默认配置
        预期结果: 配置项有默认值
        """
        # Arrange & Act
        workflow = DailyWorkflow()
        
        # Assert
        assert workflow.phases is not None
        assert len(workflow.phases) > 0
    
    def test_custom_configuration(self):
        """
        测试场景: 自定义配置
        预期结果: 配置项正确设置
        """
        # Arrange & Act
        custom_phases = ["SYNC_CHECK", "SELECTION"]
        workflow = DailyWorkflow(phases=custom_phases)
        
        # Assert
        assert workflow.phases == custom_phases


class TestWorkflowErrorHandling:
    """测试工作流错误处理"""
    
    @pytest.mark.asyncio
    async def test_handle_phase_error(self):
        """
        测试场景: 处理阶段错误
        预期结果: 错误被记录，工作流暂停
        """
        # Arrange
        workflow = DailyWorkflow()
        await workflow.start()
        
        # Act
        await workflow._handle_phase_error("SELECTION", Exception("选股失败"))
        
        # Assert
        assert workflow.state == "PAUSED"
        assert "SELECTION" in workflow.failed_phases
    
    @pytest.mark.asyncio
    async def test_retry_failed_phase(self):
        """
        测试场景: 重试失败的阶段
        预期结果: 阶段重新执行
        """
        # Arrange
        workflow = DailyWorkflow()
        workflow.failed_phases = ["SELECTION"]
        workflow.state = "PAUSED"
        
        # Act
        result = await workflow.retry_failed_phase("SELECTION")
        
        # Assert
        assert result is not None


class TestWorkflowLogging:
    """测试工作流日志"""
    
    def test_log_phase_start(self):
        """
        测试场景: 记录阶段开始
        预期结果: 日志被记录
        """
        # Arrange
        workflow = DailyWorkflow()
        
        with patch('loguru.logger.info') as mock_logger:
            # Act
            workflow._log_phase_start("SELECTION")
            
            # Assert
            mock_logger.assert_called_once()
    
    def test_log_phase_complete(self):
        """
        测试场景: 记录阶段完成
        预期结果: 日志被记录
        """
        # Arrange
        workflow = DailyWorkflow()
        
        with patch('loguru.logger.info') as mock_logger:
            # Act
            workflow._log_phase_complete("SELECTION", {"status": "success"})
            
            # Assert
            mock_logger.assert_called_once()


class TestWorkflowIntegration:
    """测试工作流集成"""
    
    @pytest.mark.asyncio
    async def test_integration_with_all_services(self):
        """
        集成测试: 所有服务协同工作
        预期结果: 工作流成功完成
        """
        # Arrange
        import pandas as pd
        
        # 创建模拟的DataFrame - 需要5000行数据满足完整性检查
        mock_df = pd.DataFrame({
            'Close': [10.0] * 5000,
            'Volume': [1000000] * 5000,
            'Amount': [10000000] * 5000,
            'Open': [9.5] * 5000,
            'High': [10.5] * 5000,
            'Low': [9.0] * 5000
        })
        
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = True
        mock_tdx.get_market_data.return_value = mock_df
        mock_tdx.get_more_info.return_value = pd.DataFrame({
            'Close': [10.0],
            'ZTPrice': [11.0]  # 涨停价
        })
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
        
        # Act
        result = await workflow.execute(date(2026, 3, 25))
        
        # Assert
        assert result["status"] == "success"
        assert result["sector_code"] is not None
