#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书通知服务单元测试
TDD Step 1: 编写测试用例 (红)
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any, Optional

# 被测试的类 (先定义接口，稍后实现)
from app.services.feishu_notification_service import FeishuNotificationService


class TestFeishuGroupMessage:
    """测试飞书群消息发送"""
    
    @pytest.mark.asyncio
    async def test_send_markdown_message(self):
        """
        测试场景: 发送Markdown格式消息
        预期结果: 消息格式正确，包含所有内容
        """
        # Arrange
        message = """
## 盘后数据同步异常

**检查时间**: 2026-03-25 15:05:00

**异常原因**:
- 通达信客户端离线
- 数据同步失败

**建议操作**:
1. 检查通达信客户端是否启动
2. 检查网络连接
3. 手动触发数据同步
        """
        mock_feishu = Mock()
        mock_feishu.send_group_message.return_value = {"status": "success", "message_id": "om_xxx"}
        
        notifier = FeishuNotificationService(feishu_client=mock_feishu)
        
        # Act
        result = await notifier.send_group_message(
            chat_id="oc_xxx",
            message=message,
            at_users=["ou_operator"]
        )
        
        # Assert
        assert result["status"] == "success"
        assert mock_feishu.send_group_message.called
        call_args = mock_feishu.send_group_message.call_args
        assert "## 盘后数据同步异常" in call_args[1]["message"]
    
    @pytest.mark.asyncio
    async def test_send_message_with_at_users(self):
        """
        测试场景: 发送消息并@用户
        预期结果: 消息中包含@用户
        """
        # Arrange
        mock_feishu = Mock()
        mock_feishu.send_group_message.return_value = {"status": "success", "message_id": "om_xxx"}
        
        notifier = FeishuNotificationService(feishu_client=mock_feishu)
        
        # Act
        result = await notifier.send_group_message(
            chat_id="oc_xxx",
            message="测试消息",
            at_users=["ou_user1", "ou_user2"]
        )
        
        # Assert
        assert result["status"] == "success"
        call_args = mock_feishu.send_group_message.call_args
        assert "ou_user1" in call_args[1]["at_users"]
        assert "ou_user2" in call_args[1]["at_users"]
    
    @pytest.mark.asyncio
    async def test_send_message_failure(self):
        """
        测试场景: 发送消息失败
        预期结果: 返回失败状态
        """
        # Arrange
        mock_feishu = Mock()
        mock_feishu.send_group_message.return_value = {"status": "failed", "error": "网络错误"}
        
        notifier = FeishuNotificationService(feishu_client=mock_feishu)
        
        # Act
        result = await notifier.send_group_message(
            chat_id="oc_xxx",
            message="测试消息"
        )
        
        # Assert
        assert result["status"] == "failed"


class TestFeishuTaskCard:
    """测试飞书任务卡片创建"""
    
    @pytest.mark.asyncio
    async def test_create_task_card(self):
        """
        测试场景: 创建任务卡片
        预期结果: 卡片创建成功，包含正确信息
        """
        # Arrange
        task_info = {
            "title": "盘后数据同步异常 - 2026-03-25",
            "content": "通达信客户端数据未同步，需要人工处理",
            "assignee": "ou_operator",
            "deadline": "2026-03-25 16:00:00"
        }
        mock_feishu = Mock()
        mock_feishu.create_task_card.return_value = {"status": "success", "task_card_id": "tc_xxx"}
        
        notifier = FeishuNotificationService(feishu_client=mock_feishu)
        
        # Act
        result = await notifier.create_task_card(**task_info)
        
        # Assert
        assert result["status"] == "success"
        assert result["task_card_id"] == "tc_xxx"
        mock_feishu.create_task_card.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_task_card_with_optional_fields(self):
        """
        测试场景: 创建任务卡片（可选字段）
        预期结果: 卡片创建成功
        """
        # Arrange
        task_info = {
            "title": "简单任务",
            "content": "任务内容"
        }
        mock_feishu = Mock()
        mock_feishu.create_task_card.return_value = {"status": "success", "task_card_id": "tc_yyy"}
        
        notifier = FeishuNotificationService(feishu_client=mock_feishu)
        
        # Act
        result = await notifier.create_task_card(**task_info)
        
        # Assert
        assert result["status"] == "success"


class TestAlertNotification:
    """测试告警通知"""
    
    @pytest.mark.asyncio
    async def test_send_warning_alert(self):
        """
        测试场景: 发送警告级别告警
        预期结果: 告警消息正确发送
        """
        # Arrange
        mock_feishu = Mock()
        mock_feishu.send_group_message.return_value = {"status": "success", "message_id": "om_xxx"}
        mock_feishu.create_task_card.return_value = {"status": "success", "task_card_id": "tc_xxx"}
        
        notifier = FeishuNotificationService(feishu_client=mock_feishu)
        
        sync_result = {
            "status": "failed",
            "checks": {
                "client_online": False,
                "data_complete": False,
                "timestamp_valid": False,
                "data_reasonable": False
            },
            "message": "通达信客户端离线",
            "action_required": True
        }
        
        # Act
        result = await notifier.notify_operator(
            sync_result=sync_result,
            chat_id="oc_xxx",
            at_users=["ou_operator"],
            create_task_card=True
        )
        
        # Assert
        assert result["status"] == "success"
        assert mock_feishu.send_group_message.called
        assert mock_feishu.create_task_card.called
    
    @pytest.mark.asyncio
    async def test_send_info_alert(self):
        """
        测试场景: 发送信息级别通知
        预期结果: 通知消息正确发送
        """
        # Arrange
        mock_feishu = Mock()
        mock_feishu.send_group_message.return_value = {"status": "success", "message_id": "om_xxx"}
        
        notifier = FeishuNotificationService(feishu_client=mock_feishu)
        
        # Act
        result = await notifier.send_alert(
            level="info",
            title="系统通知",
            message="每日选股任务已完成",
            chat_id="oc_xxx"
        )
        
        # Assert
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_no_alert_on_success(self):
        """
        测试场景: 检查成功时不发送告警
        预期结果: 不发送告警消息
        """
        # Arrange
        mock_feishu = Mock()
        
        notifier = FeishuNotificationService(feishu_client=mock_feishu)
        
        sync_result = {
            "status": "success",
            "checks": {
                "client_online": True,
                "data_complete": True,
                "timestamp_valid": True,
                "data_reasonable": True
            }
        }
        
        # Act
        should_notify = notifier.should_notify_operator(sync_result)
        
        # Assert
        assert should_notify is False


class TestDailyReportNotification:
    """测试每日报告通知"""
    
    @pytest.mark.asyncio
    async def test_send_daily_report(self):
        """
        测试场景: 发送每日选股报告
        预期结果: 报告消息正确发送
        """
        # Arrange
        mock_feishu = Mock()
        mock_feishu.send_group_message.return_value = {"status": "success", "message_id": "om_xxx"}
        
        notifier = FeishuNotificationService(feishu_client=mock_feishu)
        
        report_data = {
            "date": date(2026, 3, 25),
            "sector_code": "3BL0325",
            "sector_name": "3倍量20260325",
            "selected_count": 25,
            "strategies": {
                "3x_volume": 18,
                "limit_up": 5,
                "gap": 2
            }
        }
        
        # Act
        result = await notifier.send_daily_report(
            chat_id="oc_xxx",
            report_data=report_data
        )
        
        # Assert
        assert result["status"] == "success"
        call_args = mock_feishu.send_group_message.call_args
        assert "3BL0325" in call_args[1]["message"]
        assert "25" in call_args[1]["message"]


class TestNotificationConfiguration:
    """测试通知配置"""
    
    def test_default_configuration(self):
        """
        测试场景: 默认配置
        预期结果: 配置项有默认值
        """
        # Arrange & Act
        notifier = FeishuNotificationService()
        
        # Assert
        assert notifier.default_chat_id is not None
        assert notifier.operator_ids is not None
    
    def test_custom_configuration(self):
        """
        测试场景: 自定义配置
        预期结果: 配置项正确设置
        """
        # Arrange & Act
        notifier = FeishuNotificationService(
            default_chat_id="oc_custom",
            operator_ids=["ou_1", "ou_2"]
        )
        
        # Assert
        assert notifier.default_chat_id == "oc_custom"
        assert notifier.operator_ids == ["ou_1", "ou_2"]


class TestNotificationRetry:
    """测试通知重试机制"""
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """
        测试场景: 发送失败时重试
        预期结果: 重试后成功
        """
        # Arrange
        mock_feishu = Mock()
        # 第一次失败，第二次成功
        mock_feishu.send_group_message.side_effect = [
            {"status": "failed", "error": "网络错误"},
            {"status": "success", "message_id": "om_xxx"}
        ]
        
        notifier = FeishuNotificationService(
            feishu_client=mock_feishu,
            max_retries=3
        )
        
        # Act
        result = await notifier.send_group_message_with_retry(
            chat_id="oc_xxx",
            message="测试消息"
        )
        
        # Assert
        assert result["status"] == "success"
        assert mock_feishu.send_group_message.call_count == 2
    
    @pytest.mark.asyncio
    async def test_max_retry_exceeded(self):
        """
        测试场景: 超过最大重试次数
        预期结果: 返回失败
        """
        # Arrange
        mock_feishu = Mock()
        mock_feishu.send_group_message.return_value = {"status": "failed", "error": "网络错误"}
        
        notifier = FeishuNotificationService(
            feishu_client=mock_feishu,
            max_retries=3
        )
        
        # Act
        result = await notifier.send_group_message_with_retry(
            chat_id="oc_xxx",
            message="测试消息"
        )
        
        # Assert
        assert result["status"] == "failed"
        assert mock_feishu.send_group_message.call_count == 3
