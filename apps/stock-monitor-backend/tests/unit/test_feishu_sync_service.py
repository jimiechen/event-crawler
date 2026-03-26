#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书数据同步服务单元测试
TDD Step 1: 编写测试用例 (红)
"""

import pytest
from datetime import date
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any, Optional

# 被测试的类 (先定义接口，稍后实现)
from app.services.feishu_sync_service import FeishuSyncService


class TestSyncSelectionToFeishu:
    """测试同步选股结果到飞书"""
    
    @pytest.mark.asyncio
    async def test_sync_selection_success(self):
        """
        测试场景: 成功同步选股结果
        预期结果: 数据成功写入飞书多维表格
        """
        # Arrange
        mock_feishu = Mock()
        mock_feishu.add_records.return_value = {"status": "success", "records": [{"id": "rec_xxx"}]}
        
        service = FeishuSyncService(feishu_client=mock_feishu)
        
        selection_data = [
            {
                "stock_code": "000001.SZ",
                "stock_name": "平安银行",
                "strategy": "3x_volume",
                "volume_ratio": 3.5,
                "close_price": 11.2
            },
            {
                "stock_code": "600000.SH",
                "stock_name": "浦发银行",
                "strategy": "limit_up",
                "change_percent": 9.8,
                "close_price": 8.5
            }
        ]
        
        # Act
        result = await service.sync_selection_to_feishu(selection_data)
        
        # Assert
        assert result["status"] == "success"
        assert result["synced_count"] == 2
        mock_feishu.add_records.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sync_selection_empty_data(self):
        """
        测试场景: 同步空数据
        预期结果: 返回成功，但同步数量为0
        """
        # Arrange
        mock_feishu = Mock()
        
        service = FeishuSyncService(feishu_client=mock_feishu)
        
        # Act
        result = await service.sync_selection_to_feishu([])
        
        # Assert
        assert result["status"] == "success"
        assert result["synced_count"] == 0
        assert not mock_feishu.add_records.called
    
    @pytest.mark.asyncio
    async def test_sync_selection_partial_failure(self):
        """
        测试场景: 部分数据同步失败
        预期结果: 返回部分成功状态
        """
        # Arrange
        mock_feishu = Mock()
        mock_feishu.add_records.side_effect = [
            {"status": "success", "records": [{"id": "rec_1"}]},
            {"status": "failed", "error": "网络错误"}
        ]
        
        service = FeishuSyncService(feishu_client=mock_feishu)
        
        selection_data = [
            {"stock_code": "000001.SZ", "strategy": "3x_volume"},
            {"stock_code": "600000.SH", "strategy": "limit_up"}
        ]
        
        # Act
        result = await service.sync_selection_to_feishu(selection_data, batch_size=1)
        
        # Assert
        assert result["status"] == "partial"
        assert result["synced_count"] == 1
        assert result["failed_count"] == 1


class TestSyncScreenshotsToFeishu:
    """测试同步截图到飞书"""
    
    @pytest.mark.asyncio
    async def test_sync_screenshots_success(self):
        """
        测试场景: 成功同步截图
        预期结果: 截图成功上传到飞书文档
        """
        # Arrange
        mock_feishu = Mock()
        mock_feishu.upload_file.return_value = {"status": "success", "file_token": "file_xxx"}
        
        service = FeishuSyncService(feishu_client=mock_feishu)
        
        screenshot_paths = [
            "./screenshots/20260325/tlby/000001.SZ.png",
            "./screenshots/20260325/tlby/600000.SH.png"
        ]
        
        # Act
        result = await service.sync_screenshots_to_feishu(screenshot_paths)
        
        # Assert
        assert result["status"] == "success"
        assert result["uploaded_count"] == 2
        assert mock_feishu.upload_file.call_count == 2
    
    @pytest.mark.asyncio
    async def test_sync_screenshots_with_metadata(self):
        """
        测试场景: 同步截图并附带元数据
        预期结果: 截图和元数据都成功上传
        """
        # Arrange
        mock_feishu = Mock()
        mock_feishu.upload_file.return_value = {"status": "success", "file_token": "file_xxx"}
        
        service = FeishuSyncService(feishu_client=mock_feishu)
        
        screenshots_with_metadata = [
            {
                "path": "./screenshots/20260325/tlby/000001.SZ.png",
                "stock_code": "000001.SZ",
                "stock_name": "平安银行",
                "ai_analysis": {"trend": "upward"}
            }
        ]
        
        # Act
        result = await service.sync_screenshots_with_metadata(screenshots_with_metadata)
        
        # Assert
        assert result["status"] == "success"
        assert result["uploaded_count"] == 1


class TestBatchSync:
    """测试批量同步"""
    
    @pytest.mark.asyncio
    async def test_batch_sync_selection(self):
        """
        测试场景: 批量同步选股结果
        预期结果: 数据分批同步成功
        """
        # Arrange
        mock_feishu = Mock()
        mock_feishu.add_records.return_value = {"status": "success", "records": [{"id": "rec_xxx"}]}
        
        service = FeishuSyncService(feishu_client=mock_feishu)
        
        # 生成大量测试数据
        selection_data = [
            {"stock_code": f"{i:06d}.SZ", "strategy": "3x_volume"}
            for i in range(100)
        ]
        
        # Act
        result = await service.sync_selection_to_feishu(selection_data, batch_size=50)
        
        # Assert
        assert result["status"] == "success"
        assert result["synced_count"] == 100
        # 应该分2批调用
        assert mock_feishu.add_records.call_count == 2


class TestSyncValidation:
    """测试同步数据验证"""
    
    def test_validate_selection_data_valid(self):
        """
        测试场景: 验证有效的选股数据
        预期结果: 返回True
        """
        # Arrange
        service = FeishuSyncService()
        
        valid_data = {
            "stock_code": "000001.SZ",
            "stock_name": "平安银行",
            "strategy": "3x_volume",
            "close_price": 11.2
        }
        
        # Act
        result = service.validate_selection_data(valid_data)
        
        # Assert
        assert result is True
    
    def test_validate_selection_data_invalid(self):
        """
        测试场景: 验证无效的选股数据
        预期结果: 返回False
        """
        # Arrange
        service = FeishuSyncService()
        
        invalid_data = {
            "stock_name": "平安银行",
            # 缺少 stock_code
        }
        
        # Act
        result = service.validate_selection_data(invalid_data)
        
        # Assert
        assert result is False


class TestSyncRetry:
    """测试同步重试机制"""
    
    @pytest.mark.asyncio
    async def test_sync_retry_on_failure(self):
        """
        测试场景: 同步失败时重试
        预期结果: 重试后成功
        """
        # Arrange
        mock_feishu = Mock()
        mock_feishu.add_records.side_effect = [
            {"status": "failed", "error": "网络错误"},
            {"status": "success", "records": [{"id": "rec_xxx"}]}
        ]
        
        service = FeishuSyncService(feishu_client=mock_feishu, max_retries=3)
        
        selection_data = [{"stock_code": "000001.SZ", "strategy": "3x_volume"}]
        
        # Act
        result = await service.sync_selection_to_feishu(selection_data)
        
        # Assert
        assert result["status"] == "success"
        assert mock_feishu.add_records.call_count == 2
    
    @pytest.mark.asyncio
    async def test_sync_max_retry_exceeded(self):
        """
        测试场景: 超过最大重试次数
        预期结果: 返回失败
        """
        # Arrange
        mock_feishu = Mock()
        mock_feishu.add_records.return_value = {"status": "failed", "error": "网络错误"}
        
        service = FeishuSyncService(feishu_client=mock_feishu, max_retries=3)
        
        selection_data = [{"stock_code": "000001.SZ", "strategy": "3x_volume"}]
        
        # Act
        result = await service.sync_selection_to_feishu(selection_data)
        
        # Assert
        assert result["status"] == "failed"
        assert mock_feishu.add_records.call_count == 3


class TestSyncStatusTracking:
    """测试同步状态跟踪"""
    
    @pytest.mark.asyncio
    async def test_track_sync_status(self):
        """
        测试场景: 跟踪同步状态
        预期结果: 状态正确记录
        """
        # Arrange
        mock_feishu = Mock()
        mock_feishu.add_records.return_value = {"status": "success", "records": [{"id": "rec_xxx"}]}
        
        service = FeishuSyncService(feishu_client=mock_feishu)
        
        selection_data = [{"stock_code": "000001.SZ", "strategy": "3x_volume"}]
        
        # Act
        result = await service.sync_selection_to_feishu(selection_data)
        
        # Assert
        assert "sync_time" in result
        assert result["sync_time"] is not None


class TestDataTransformation:
    """测试数据转换"""
    
    def test_transform_selection_data(self):
        """
        测试场景: 转换选股数据格式
        预期结果: 转换为飞书多维表格格式
        """
        # Arrange
        service = FeishuSyncService()
        
        raw_data = {
            "stock_code": "000001.SZ",
            "stock_name": "平安银行",
            "strategy": "3x_volume",
            "volume_ratio": 3.5,
            "close_price": 11.2,
            "date": date(2026, 3, 25)
        }
        
        # Act
        transformed = service.transform_selection_data(raw_data)
        
        # Assert
        assert "fields" in transformed
        assert transformed["fields"]["股票代码"] == "000001.SZ"
        assert transformed["fields"]["股票名称"] == "平安银行"
    
    def test_transform_screenshot_data(self):
        """
        测试场景: 转换截图数据格式
        预期结果: 转换为飞书文档格式
        """
        # Arrange
        service = FeishuSyncService()
        
        raw_data = {
            "path": "./screenshots/20260325/tlby/000001.SZ.png",
            "stock_code": "000001.SZ",
            "ai_analysis": {"trend": "upward"}
        }
        
        # Act
        transformed = service.transform_screenshot_data(raw_data)
        
        # Assert
        assert "title" in transformed
        assert "000001.SZ" in transformed["title"]


class TestSyncConfiguration:
    """测试同步配置"""
    
    def test_default_configuration(self):
        """
        测试场景: 默认配置
        预期结果: 配置项有默认值
        """
        # Arrange & Act
        service = FeishuSyncService()
        
        # Assert
        assert service.batch_size > 0
        assert service.max_retries > 0
    
    def test_custom_configuration(self):
        """
        测试场景: 自定义配置
        预期结果: 配置项正确设置
        """
        # Arrange & Act
        service = FeishuSyncService(batch_size=100, max_retries=5)
        
        # Assert
        assert service.batch_size == 100
        assert service.max_retries == 5
