#!/usr/bin/env python3
import sys
import os
import platform
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from src.launcher import Launcher
from src.browser_manager import BrowserManager
from src.extension_loader import ExtensionLoader


class TestLauncher:
    """启动器单元测试"""
    
    def test_init(self):
        """测试启动器初始化"""
        launcher = Launcher()
        
        assert launcher.app_dir is not None
        assert launcher.os_type in ['Windows', 'Darwin', 'Linux']
        assert launcher.is_windows == (platform.system() == 'Windows')
        assert launcher.is_macos == (platform.system() == 'Darwin')
        assert launcher.is_linux == (platform.system() == 'Linux')
        
        print("✅ 启动器初始化测试通过")
    
    def test_get_app_dir(self):
        """测试应用目录获取"""
        launcher = Launcher()
        app_dir = launcher.app_dir
        
        assert app_dir.exists()
        assert app_dir.is_dir()
        
        print(f"✅ 应用目录测试通过: {app_dir}")
    
    def test_setup_paths(self):
        """测试路径设置"""
        launcher = Launcher()
        
        assert launcher.resources_dir is not None
        assert launcher.chrome_extension_dir is not None
        assert launcher.csv_data_dir is not None
        assert launcher.configs_dir is not None
        assert launcher.chromium_dir is not None
        assert launcher.backend_dir is not None
        
        print("✅ 路径设置测试通过")
    
    def test_setup_logging(self):
        """测试日志设置"""
        launcher = Launcher()
        
        log_dir = launcher.app_dir / 'logs'
        assert log_dir.exists()
        
        log_file = log_dir / 'launcher.log'
        assert log_file.exists() or log_file.parent.exists()
        
        print("✅ 日志设置测试通过")
    
    @patch('subprocess.run')
    def test_install_playwright_browsers(self, mock_run):
        """测试 Playwright 浏览器安装"""
        launcher = Launcher()
        
        mock_run.return_value = Mock(
            returncode=0,
            stdout='Chromium installed',
            stderr=''
        )
        
        result = launcher._install_playwright_browsers()
        
        assert result is True
        mock_run.assert_called_once()
        
        print("✅ Playwright 浏览器安装测试通过")
    
    @patch('sys.exit')
    def test_check_dependencies_failure(self, mock_exit):
        """测试依赖检查失败"""
        launcher = Launcher()
        
        with patch.object(launcher, '_check_dependencies', return_value=False):
            launcher.run()
            
            mock_exit.assert_called_once_with(1)
        
        print("✅ 依赖检查失败测试通过")


class TestBrowserManager:
    """浏览器管理器单元测试"""
    
    def test_init(self):
        """测试浏览器管理器初始化"""
        manager = BrowserManager(
            extension_path='/tmp/test-extension',
            headless=True
        )
        
        assert manager.extension_path == Path('/tmp/test-extension')
        assert manager.headless is True
        assert manager.os_type in ['Windows', 'Darwin', 'Linux']
        
        print("✅ 浏览器管理器初始化测试通过")
    
    def test_get_launch_args(self):
        """测试启动参数获取"""
        manager = BrowserManager(
            extension_path='/tmp/test-extension',
            headless=True
        )
        
        args = manager._get_launch_args()
        
        assert '--no-sandbox' in args
        assert '--disable-setuid-sandbox' in args
        assert '--headless' in args
        assert '--load-extension=/tmp/test-extension' in args
        
        print("✅ 启动参数测试通过")
    
    def test_get_user_agent(self):
        """测试 User-Agent 获取"""
        manager = BrowserManager(
            extension_path='/tmp/test-extension',
            headless=True
        )
        
        user_agent = manager._get_user_agent()
        
        assert 'Chrome' in user_agent
        assert 'Safari' in user_agent or 'Windows' in user_agent or 'Linux' in user_agent
        
        print(f"✅ User-Agent 测试通过: {user_agent[:50]}...")
    
    @patch('playwright.async_api.async_playwright')
    async def test_initialize(self, mock_playwright):
        """测试浏览器初始化"""
        mock_playwright.return_value.start.return_value = Mock()
        mock_browser = Mock()
        mock_playwright.return_value.start.return_value.chromium.launch.return_value = mock_browser
        
        manager = BrowserManager(
            extension_path='/tmp/test-extension',
            headless=True
        )
        
        await manager.initialize()
        
        assert manager.playwright is not None
        assert manager.browser is not None
        
        print("✅ 浏览器初始化测试通过")


class TestExtensionLoader:
    """扩展加载器单元测试"""
    
    def test_init(self):
        """测试扩展加载器初始化"""
        loader = ExtensionLoader(
            extension_path='/tmp/test-extension'
        )
        
        assert loader.extension_path == Path('/tmp/test-extension')
        assert loader.os_type in ['Windows', 'Darwin', 'Linux']
        
        print("✅ 扩展加载器初始化测试通过")
    
    def test_validate_extension_missing_manifest(self):
        """测试扩展验证 - 缺少 manifest"""
        loader = ExtensionLoader(
            extension_path='/tmp/non-existent-extension'
        )
        
        result = loader.validate_extension()
        
        assert result is False
        
        print("✅ 扩展验证测试通过（缺少 manifest）")
    
    def test_generate_extension_id(self):
        """测试扩展 ID 生成"""
        loader = ExtensionLoader(
            extension_path='/tmp/test-extension'
        )
        
        loader.manifest = {
            'name': 'Test Extension',
            'version': '1.0.0',
            'manifest_version': 3,
            'key': 'test_key_1234567890123456789012345678901234567890123456789012'
        }
        
        extension_id = loader._generate_extension_id()
        
        assert extension_id is not None
        assert len(extension_id) == 32
        
        print(f"✅ 扩展 ID 生成测试通过: {extension_id}")
    
    def test_get_chrome_executable_path(self):
        """测试 Chrome 可执行文件路径获取"""
        loader = ExtensionLoader(
            extension_path='/tmp/test-extension'
        )
        
        chrome_path = loader.get_chrome_executable_path()
        
        if platform.system() == 'Darwin':
            assert 'Google Chrome' in str(chrome_path) or chrome_path is None
        elif platform.system() == 'Windows':
            assert 'chrome.exe' in str(chrome_path) or chrome_path is None
        elif platform.system() == 'Linux':
            assert 'chrome' in str(chrome_path) or chrome_path is None
        
        print(f"✅ Chrome 可执行文件路径测试通过: {chrome_path}")


class TestBuildManager:
    """构建管理器单元测试"""
    
    def test_init(self):
        """测试构建管理器初始化"""
        sys.path.append(str(Path(__file__).parent.parent / 'scripts'))
        from build import BuildManager
        
        manager = BuildManager()
        
        assert manager.project_root is not None
        assert manager.backend_dir is not None
        assert manager.chrome_extension_dir is not None
        assert manager.build_dir is not None
        assert manager.resources_dir is not None
        assert manager.dist_dir is not None
        
        print("✅ 构建管理器初始化测试通过")
    
    @patch('shutil.rmtree')
    def test_clean(self, mock_rmtree):
        """测试清理功能"""
        sys.path.append(str(Path(__file__).parent.parent / 'scripts'))
        from build import BuildManager
        
        manager = BuildManager()
        manager.clean()
        
        assert mock_rmtree.called
        
        print("✅ 清理功能测试通过")
    
    @patch('shutil.copytree')
    @patch('shutil.copy2')
    def test_prepare_resources(self, mock_copytree, mock_copy2):
        """测试资源准备"""
        sys.path.append(str(Path(__file__).parent.parent / 'scripts'))
        from build import BuildManager
        
        manager = BuildManager()
        manager.prepare_resources()
        
        assert mock_copytree.called or mock_copy2.called
        
        print("✅ 资源准备测试通过")


def run_all_tests():
    """运行所有单元测试"""
    print("\n" + "=" * 60)
    print("开始运行单元测试")
    print("=" * 60 + "\n")
    
    test_classes = [
        TestLauncher,
        TestBrowserManager,
        TestExtensionLoader,
        TestBuildManager
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_class in test_classes:
        print(f"\n{'=' * 60}")
        print(f"测试类: {test_class.__name__}")
        print(f"{'=' * 60}\n")
        
        test_instance = test_class()
        test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
        
        for test_method_name in test_methods:
            total_tests += 1
            test_method = getattr(test_instance, test_method_name)
            
            try:
                if asyncio.iscoroutinefunction(test_method):
                    import asyncio
                    asyncio.run(test_method())
                else:
                    test_method()
                passed_tests += 1
            except Exception as e:
                print(f"❌ {test_method_name} 失败: {e}")
                failed_tests += 1
    
    print("\n" + "=" * 60)
    print("单元测试总结")
    print("=" * 60)
    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests} ✅")
    print(f"失败: {failed_tests} ❌")
    print(f"通过率: {(passed_tests/total_tests*100):.1f}%")
    print("=" * 60)
    
    return failed_tests == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)