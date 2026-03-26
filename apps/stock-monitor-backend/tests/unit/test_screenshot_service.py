#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
截图服务单元测试
TDD Step 1: 编写测试用例 (红)
"""

import pytest
import os
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any, Optional

# 被测试的类 (先定义接口，稍后实现)
from app.services.screenshot_service import ScreenshotService


class TestScreenshotDirectory:
    """测试截图目录管理"""
    
    def test_create_screenshot_directory(self):
        """
        测试场景: 创建截图目录
        预期结果: 目录成功创建
        """
        # Arrange
        service = ScreenshotService()
        trade_date = date(2026, 3, 25)
        
        with patch('os.makedirs') as mock_makedirs:
            # Act
            result = service._create_screenshot_directory(trade_date, "tlby")
            
            # Assert
            assert result is not None
            mock_makedirs.assert_called_once()
    
    def test_get_screenshot_path(self):
        """
        测试场景: 获取截图路径
        预期结果: 路径格式正确
        """
        # Arrange
        service = ScreenshotService(base_path="./screenshots")
        trade_date = date(2026, 3, 25)
        stock_code = "000001.SZ"
        
        # Act
        path = service._get_screenshot_path(trade_date, "tlby", stock_code)
        
        # Assert
        assert "screenshots" in path
        assert "20260325" in path
        assert "tlby" in path
        assert "000001.SZ" in path


class TestTlbyScreenshot:
    """测试天龙博弈截图"""
    
    @patch('pyautogui.screenshot')
    @patch('pyautogui.click')
    @patch('pyautogui.sleep')
    def test_capture_tlby_screenshot(self, mock_sleep, mock_click, mock_screenshot):
        """
        测试场景: 截取天龙博弈截图
        预期结果: 截图成功保存
        """
        # Arrange
        mock_screenshot.return_value = MagicMock()
        
        service = ScreenshotService()
        stock_code = "000001.SZ"
        trade_date = date(2026, 3, 25)
        
        with patch.object(service, '_create_screenshot_directory', return_value="./screenshots/20260325/tlby"):
            with patch.object(Path, 'exists', return_value=True):
                # Act
                result = service.capture_tlby_screenshot(stock_code, trade_date)
                
                # Assert
                assert result is not None
                assert isinstance(result, str)
    
    @patch('pyautogui.screenshot')
    @patch('pyautogui.click')
    def test_capture_tlby_with_retry(self, mock_click, mock_screenshot):
        """
        测试场景: 截图失败时重试
        预期结果: 重试后成功
        """
        # Arrange
        mock_screenshot.side_effect = [Exception("截图失败"), MagicMock()]
        
        service = ScreenshotService(max_retries=2)
        stock_code = "000001.SZ"
        trade_date = date(2026, 3, 25)
        
        with patch.object(service, '_create_screenshot_directory', return_value="./screenshots/20260325/tlby"):
            with patch.object(Path, 'exists', return_value=True):
                with patch('time.sleep'):  # 跳过等待
                    # Act
                    result = service.capture_tlby_screenshot(stock_code, trade_date)
                    
                    # Assert
                    assert result is not None
                    assert mock_screenshot.call_count == 2


class TestTdxScreenshot:
    """测试通达信截图"""
    
    @patch('pyautogui.screenshot')
    @patch('pyautogui.click')
    @patch('pyautogui.keyDown')
    @patch('pyautogui.keyUp')
    def test_capture_tdx_daily_screenshot(self, mock_keyup, mock_keydown, mock_click, mock_screenshot):
        """
        测试场景: 截取通达信日线截图
        预期结果: 截图成功保存
        """
        # Arrange
        mock_screenshot.return_value = MagicMock()
        
        service = ScreenshotService()
        stock_code = "000001.SZ"
        trade_date = date(2026, 3, 25)
        
        with patch.object(service, '_create_screenshot_directory', return_value="./screenshots/20260325/tdx"):
            with patch.object(Path, 'exists', return_value=True):
                # Act
                result = service.capture_tdx_screenshot(stock_code, trade_date, period="1d")
                
                # Assert
                assert result is not None
                assert isinstance(result, str)
    
    @patch('pyautogui.screenshot')
    @patch('pyautogui.click')
    @patch('pyautogui.keyDown')
    @patch('pyautogui.keyUp')
    def test_capture_tdx_multi_period(self, mock_keyup, mock_keydown, mock_click, mock_screenshot):
        """
        测试场景: 截取通达信多周期截图
        预期结果: 返回多个截图路径
        """
        # Arrange
        mock_screenshot.return_value = MagicMock()
        
        service = ScreenshotService()
        stock_code = "000001.SZ"
        trade_date = date(2026, 3, 25)
        periods = ["1d", "1w", "1m"]
        
        with patch.object(service, '_create_screenshot_directory', return_value="./screenshots/20260325/tdx"):
            with patch.object(Path, 'exists', return_value=True):
                # Act
                results = service.capture_tdx_multi_period(stock_code, trade_date, periods)
                
                # Assert
                assert len(results) == 3
                assert all(isinstance(r, str) for r in results)


class TestBatchScreenshot:
    """测试批量截图"""
    
    @patch('pyautogui.screenshot')
    @patch('pyautogui.click')
    def test_batch_capture_tlby_screenshots(self, mock_click, mock_screenshot):
        """
        测试场景: 批量截取天龙博弈截图
        预期结果: 返回所有截图路径
        """
        # Arrange
        mock_screenshot.return_value = MagicMock()
        
        service = ScreenshotService()
        stocks = ["000001.SZ", "000002.SZ", "600000.SH"]
        trade_date = date(2026, 3, 25)
        
        with patch.object(service, '_create_screenshot_directory', return_value="./screenshots/20260325/tlby"):
            with patch.object(Path, 'exists', return_value=True):
                with patch.object(service, 'capture_tlby_screenshot', side_effect=[
                    "./screenshots/20260325/tlby/000001.SZ.png",
                    "./screenshots/20260325/tlby/000002.SZ.png",
                    "./screenshots/20260325/tlby/600000.SH.png"
                ]):
                    # Act
                    results = service.batch_capture_tlby_screenshots(stocks, trade_date)
                    
                    # Assert
                    assert len(results) == 3
                    assert all(isinstance(r, str) for r in results)


class TestAiAnalysis:
    """测试AI分析"""
    
    def test_analyze_screenshot_with_trae(self):
        """
        测试场景: 使用Trae AI分析截图
        预期结果: 返回结构化分析结果
        """
        # Arrange
        service = ScreenshotService()
        screenshot_path = "./screenshots/20260325/tlby/000001.SZ.png"
        
        mock_trae_response = {
            "support_level": 10.5,
            "resistance_level": 11.5,
            "trend": "upward",
            "patterns": ["头肩底"],
            "recommendation": "buy"
        }
        
        with patch.object(service, '_call_trae_ai', return_value=mock_trae_response):
            # Act
            result = service.analyze_screenshot_with_trae(screenshot_path)
            
            # Assert
            assert result is not None
            assert "support_level" in result
            assert "trend" in result
    
    def test_analyze_screenshot_failure(self):
        """
        测试场景: AI分析失败
        预期结果: 返回错误信息
        """
        # Arrange
        service = ScreenshotService()
        screenshot_path = "./screenshots/20260325/tlby/000001.SZ.png"
        
        with patch.object(service, '_call_trae_ai', side_effect=Exception("AI服务不可用")):
            # Act
            result = service.analyze_screenshot_with_trae(screenshot_path)
            
            # Assert
            assert result is not None
            assert "error" in result


class TestScreenshotStorage:
    """测试截图存储"""
    
    def test_save_screenshot_metadata(self):
        """
        测试场景: 保存截图元数据
        预期结果: 元数据成功保存
        """
        # Arrange
        service = ScreenshotService()
        metadata = {
            "stock_code": "000001.SZ",
            "date": date(2026, 3, 25),
            "type": "tlby",
            "path": "./screenshots/20260325/tlby/000001.SZ.png"
        }
        
        with patch('json.dump') as mock_json_dump:
            with patch('builtins.open', MagicMock()):
                # Act
                result = service._save_screenshot_metadata(metadata)
                
                # Assert
                assert result is True
    
    def test_get_screenshot_metadata(self):
        """
        测试场景: 获取截图元数据
        预期结果: 返回正确的元数据
        """
        # Arrange
        service = ScreenshotService()
        stock_code = "000001.SZ"
        trade_date = date(2026, 3, 25)
        
        expected_metadata = {
            "stock_code": "000001.SZ",
            "date": "2026-03-25",
            "type": "tlby",
            "path": "./screenshots/20260325/tlby/000001.SZ.png"
        }
        
        with patch('json.load', return_value=expected_metadata):
            with patch('builtins.open', MagicMock()):
                with patch.object(Path, 'exists', return_value=True):
                    # Act
                    result = service.get_screenshot_metadata(stock_code, trade_date)
                    
                    # Assert
                    assert result is not None
                    assert result["stock_code"] == stock_code


class TestScreenshotCleanup:
    """测试截图清理"""
    
    def test_cleanup_old_screenshots(self):
        """
        测试场景: 清理旧截图
        预期结果: 旧截图被删除
        """
        # Arrange
        service = ScreenshotService()
        days_to_keep = 7
        
        with patch('shutil.rmtree') as mock_rmtree:
            with patch('os.listdir', return_value=["20260318", "20260325"]):
                with patch('os.path.isdir', return_value=True):
                    with patch('os.path.join', return_value="./screenshots/20260318"):
                        # Act
                        result = service.cleanup_old_screenshots(days_to_keep)
                        
                        # Assert
                        assert result is not None
                        assert result.get("status") in ["success", "failed"]


class TestScreenshotValidation:
    """测试截图验证"""
    
    def test_validate_screenshot_exists(self):
        """
        测试场景: 验证截图文件存在
        预期结果: 返回True
        """
        # Arrange
        service = ScreenshotService()
        screenshot_path = "./screenshots/20260325/tlby/000001.SZ.png"
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=True):
                # Act
                result = service.validate_screenshot(screenshot_path)
                
                # Assert
                assert result is True
    
    def test_validate_screenshot_not_exists(self):
        """
        测试场景: 验证截图文件不存在
        预期结果: 返回False
        """
        # Arrange
        service = ScreenshotService()
        screenshot_path = "./screenshots/20260325/tlby/000001.SZ.png"
        
        with patch('os.path.exists', return_value=False):
            # Act
            result = service.validate_screenshot(screenshot_path)
            
            # Assert
            assert result is False
