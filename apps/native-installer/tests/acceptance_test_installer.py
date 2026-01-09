#!/usr/bin/env python3
import sys
import os
import platform
import subprocess
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from loguru import logger

sys.path.append(str(Path(__file__).parent.parent))


class InstallerAcceptanceTest:
    """打包解决方案验收测试"""
    
    def __init__(self):
        self.test_start_time = datetime.now()
        self.os_type = platform.system()
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        self.project_root = Path(__file__).parent.parent
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
        
        self._setup_logging()
        
        logger.info("=" * 60)
        logger.info("StockMonitor 打包解决方案验收测试")
        logger.info("=" * 60)
        logger.info(f"测试时间: {self.test_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"操作系统: {self.os_type}")
        logger.info(f"Python 版本: {self.python_version}")
        logger.info(f"项目路径: {self.project_root}")
    
    def _setup_logging(self):
        log_dir = self.project_root / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f'acceptance_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        logger.add(
            log_file,
            rotation='10 MB',
            retention='7 days',
            level='INFO',
            format='{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}'
        )
    
    def record_test(self, test_name: str, passed: bool, details: str = '', duration: float = 0.0):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'passed': passed,
            'details': details,
            'duration': duration,
            'timestamp': datetime.now()
        }
        self.test_results.append(result)
        
        if passed:
            self.passed_tests += 1
            logger.success(f"✅ {test_name} - 通过 ({duration:.2f}s)")
        else:
            self.failed_tests += 1
            logger.error(f"❌ {test_name} - 失败 ({duration:.2f}s) - {details}")
    
    def test_project_structure(self):
        """测试项目结构"""
        logger.info("\n" + "=" * 60)
        logger.info("阶段1: 项目结构测试")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        required_dirs = [
            'src',
            'scripts',
            'resources',
            'resources/configs',
            'resources/chrome-extension',
            'resources/csv-data',
            'tests',
        ]
        
        missing_dirs = []
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)
                logger.error(f"❌ 缺少目录: {dir_name}")
            else:
                logger.success(f"✅ 目录存在: {dir_name}")
        
        required_files = [
            'pyinstaller.spec',
            'requirements-installer.txt',
            'README.md',
            'QUICKSTART.md',
            'PROJECT_SUMMARY.md',
            'src/launcher.py',
            'src/browser_manager.py',
            'src/extension_loader.py',
            'scripts/build.py',
            'scripts/setup_windows.py',
            'scripts/setup_macos.py',
        ]
        
        missing_files = []
        for file_name in required_files:
            file_path = self.project_root / file_name
            if not file_path.exists():
                missing_files.append(file_name)
                logger.error(f"❌ 缺少文件: {file_name}")
            else:
                logger.success(f"✅ 文件存在: {file_name}")
        
        duration = time.time() - start_time
        passed = len(missing_dirs) == 0 and len(missing_files) == 0
        details = f"缺少目录: {missing_dirs}, 缺少文件: {missing_files}"
        
        self.record_test("项目结构完整性", passed, details, duration)
        return passed
    
    def test_source_code_syntax(self):
        """测试源代码语法"""
        logger.info("\n" + "=" * 60)
        logger.info("阶段2: 源代码语法测试")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        python_files = [
            'src/launcher.py',
            'src/browser_manager.py',
            'src/extension_loader.py',
            'scripts/build.py',
            'scripts/setup_windows.py',
            'scripts/setup_macos.py',
            'tests/test_installer.py',
        ]
        
        syntax_errors = []
        for file_path in python_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                continue
            
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'py_compile', str(full_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    logger.success(f"✅ 语法正确: {file_path}")
                else:
                    syntax_errors.append(file_path)
                    logger.error(f"❌ 语法错误: {file_path}")
                    logger.error(result.stderr)
            except subprocess.TimeoutExpired:
                syntax_errors.append(file_path)
                logger.error(f"❌ 超时: {file_path}")
            except Exception as e:
                syntax_errors.append(file_path)
                logger.error(f"❌ 编译失败: {file_path} - {e}")
        
        duration = time.time() - start_time
        passed = len(syntax_errors) == 0
        details = f"语法错误文件: {syntax_errors}"
        
        self.record_test("源代码语法", passed, details, duration)
        return passed
    
    def test_configuration_files(self):
        """测试配置文件"""
        logger.info("\n" + "=" * 60)
        logger.info("阶段3: 配置文件测试")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        config_files = {
            'requirements-installer.txt': self._test_requirements_file,
            'pyinstaller.spec': self._test_pyinstaller_spec,
            'resources/configs/.env.example': self._test_env_example,
            'resources/configs/crawler_config.yaml': self._test_crawler_config,
        }
        
        config_errors = []
        for file_path, test_func in config_files.items():
            full_path = self.project_root / file_path
            if not full_path.exists():
                config_errors.append(f"{file_path} 不存在")
                logger.error(f"❌ 文件不存在: {file_path}")
                continue
            
            try:
                result = test_func(full_path)
                if result:
                    logger.success(f"✅ 配置正确: {file_path}")
                else:
                    config_errors.append(f"{file_path} 配置错误")
                    logger.error(f"❌ 配置错误: {file_path}")
            except Exception as e:
                config_errors.append(f"{file_path} 解析失败")
                logger.error(f"❌ 解析失败: {file_path} - {e}")
        
        duration = time.time() - start_time
        passed = len(config_errors) == 0
        details = f"配置错误: {config_errors}"
        
        self.record_test("配置文件", passed, details, duration)
        return passed
    
    def _test_requirements_file(self, file_path: Path) -> bool:
        """测试 requirements 文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_packages = [
            'pyinstaller',
            'playwright',
            'fastapi',
            'uvicorn',
            'loguru',
        ]
        
        for package in required_packages:
            if package.lower() not in content.lower():
                logger.warning(f"⚠️ 缺少包: {package}")
                return False
        
        return True
    
    def _test_pyinstaller_spec(self, file_path: Path) -> bool:
        """测试 PyInstaller 配置"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_sections = [
            'Analysis',
            'EXE',
            'COLLECT',
        ]
        
        for section in required_sections:
            if section not in content:
                logger.warning(f"⚠️ 缺少部分: {section}")
                return False
        
        return True
    
    def _test_env_example(self, file_path: Path) -> bool:
        """测试环境变量示例文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_vars = [
            'APP_NAME',
            'APP_VERSION',
            'HOST',
            'PORT',
            'DB_HOST',
            'DB_PORT',
        ]
        
        for var in required_vars:
            if var not in content:
                logger.warning(f"⚠️ 缺少变量: {var}")
                return False
        
        return True
    
    def _test_crawler_config(self, file_path: Path) -> bool:
        """测试爬虫配置文件"""
        import yaml
        
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        required_keys = [
            'base',
            'browser',
            'platforms',
        ]
        
        for key in required_keys:
            if key not in config:
                logger.warning(f"⚠️ 缺少配置: {key}")
                return False
        
        return True
    
    def test_documentation(self):
        """测试文档完整性"""
        logger.info("\n" + "=" * 60)
        logger.info("阶段4: 文档测试")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        doc_files = {
            'README.md': self._test_readme,
            'QUICKSTART.md': self._test_quickstart,
            'PROJECT_SUMMARY.md': self._test_project_summary,
        }
        
        doc_errors = []
        for file_path, test_func in doc_files.items():
            full_path = self.project_root / file_path
            if not full_path.exists():
                doc_errors.append(f"{file_path} 不存在")
                logger.error(f"❌ 文件不存在: {file_path}")
                continue
            
            try:
                result = test_func(full_path)
                if result:
                    logger.success(f"✅ 文档完整: {file_path}")
                else:
                    doc_errors.append(f"{file_path} 内容不完整")
                    logger.error(f"❌ 文档不完整: {file_path}")
            except Exception as e:
                doc_errors.append(f"{file_path} 读取失败")
                logger.error(f"❌ 读取失败: {file_path} - {e}")
        
        duration = time.time() - start_time
        passed = len(doc_errors) == 0
        details = f"文档错误: {doc_errors}"
        
        self.record_test("文档完整性", passed, details, duration)
        return passed
    
    def _test_readme(self, file_path: Path) -> bool:
        """测试 README 文档"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_sections = [
            '项目概述',
            '功能特性',
            '快速开始',
            '平台特定说明',
            '配置',
            '使用指南',
            '故障排除',
        ]
        
        for section in required_sections:
            if section not in content:
                logger.warning(f"⚠️ 缺少章节: {section}")
                return False
        
        return True
    
    def _test_quickstart(self, file_path: Path) -> bool:
        """测试快速开始文档"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_sections = [
            '安装应用',
            '配置数据库',
            '访问 Web 界面',
            '常用命令',
            '故障排除',
        ]
        
        for section in required_sections:
            if section not in content:
                logger.warning(f"⚠️ 缺少章节: {section}")
                return False
        
        return True
    
    def _test_project_summary(self, file_path: Path) -> bool:
        """测试项目总结文档"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_sections = [
            '项目概述',
            '已完成的工作',
            '技术特性',
            '使用方法',
            '项目亮点',
        ]
        
        for section in required_sections:
            if section not in content:
                logger.warning(f"⚠️ 缺少章节: {section}")
                return False
        
        return True
    
    def test_cross_platform_compatibility(self):
        """测试跨平台兼容性"""
        logger.info("\n" + "=" * 60)
        logger.info("阶段5: 跨平台兼容性测试")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        compatibility_issues = []
        
        # 检查 Windows 支持
        if self.os_type == 'Windows':
            logger.info("📋 检查 Windows 支持...")
            if not (self.project_root / 'scripts/setup_windows.py').exists():
                compatibility_issues.append("Windows 安装脚本不存在")
                logger.error("❌ Windows 安装脚本不存在")
            else:
                logger.success("✅ Windows 安装脚本存在")
        
        # 检查 macOS 支持
        if self.os_type == 'Darwin':
            logger.info("📋 检查 macOS 支持...")
            if not (self.project_root / 'scripts/setup_macos.py').exists():
                compatibility_issues.append("macOS 安装脚本不存在")
                logger.error("❌ macOS 安装脚本不存在")
            else:
                logger.success("✅ macOS 安装脚本存在")
        
        # 检查跨平台代码
        logger.info("📋 检查跨平台代码...")
        cross_platform_files = [
            'src/launcher.py',
            'src/browser_manager.py',
            'src/extension_loader.py',
        ]
        
        for file_path in cross_platform_files:
            full_path = self.project_root / file_path
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'platform.system()' in content:
                logger.success(f"✅ 跨平台检测: {file_path}")
            else:
                compatibility_issues.append(f"{file_path} 缺少跨平台检测")
                logger.warning(f"⚠️ 缺少跨平台检测: {file_path}")
        
        duration = time.time() - start_time
        passed = len(compatibility_issues) == 0
        details = f"兼容性问题: {compatibility_issues}"
        
        self.record_test("跨平台兼容性", passed, details, duration)
        return passed
    
    def test_dependencies(self):
        """测试依赖完整性"""
        logger.info("\n" + "=" * 60)
        logger.info("阶段6: 依赖完整性测试")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # 检查 requirements 文件
        requirements_file = self.project_root / 'requirements-installer.txt'
        if not requirements_file.exists():
            logger.error("❌ requirements-installer.txt 不存在")
            self.record_test("依赖完整性", False, "requirements-installer.txt 不存在", 0.0)
            return False
        
        with open(requirements_file, 'r', encoding='utf-8') as f:
            requirements = f.read()
        
        # 检查关键依赖
        critical_deps = {
            'pyinstaller': '打包工具',
            'playwright': '浏览器自动化',
            'fastapi': 'Web 框架',
            'uvicorn': 'ASGI 服务器',
            'loguru': '日志库',
        }
        
        missing_deps = []
        for dep, description in critical_deps.items():
            if dep.lower() not in requirements.lower():
                missing_deps.append(f"{dep} ({description})")
                logger.error(f"❌ 缺少依赖: {dep} - {description}")
            else:
                logger.success(f"✅ 依赖存在: {dep} - {description}")
        
        duration = time.time() - start_time
        passed = len(missing_deps) == 0
        details = f"缺少依赖: {missing_deps}"
        
        self.record_test("依赖完整性", passed, details, duration)
        return passed
    
    def test_build_readiness(self):
        """测试构建准备状态"""
        logger.info("\n" + "=" * 60)
        logger.info("阶段7: 构建准备测试")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        readiness_issues = []
        
        # 检查 Python 环境
        logger.info("📋 检查 Python 环境...")
        if sys.version_info < (3, 11):
            readiness_issues.append(f"Python 版本过低: {self.python_version}，需要 3.11+")
            logger.error(f"❌ Python 版本过低: {self.python_version}")
        else:
            logger.success(f"✅ Python 版本符合要求: {self.python_version}")
        
        # 检查 PyInstaller
        logger.info("📋 检查 PyInstaller...")
        try:
            import PyInstaller
            logger.success(f"✅ PyInstaller 已安装: {PyInstaller.__version__}")
        except ImportError:
            readiness_issues.append("PyInstaller 未安装")
            logger.error("❌ PyInstaller 未安装")
        
        # 检查 Playwright
        logger.info("📋 检查 Playwright...")
        try:
            import playwright
            try:
                version = playwright.__version__
            except AttributeError:
                version = "已安装（版本未知）"
            logger.success(f"✅ Playwright 已安装: {version}")
        except ImportError:
            readiness_issues.append("Playwright 未安装")
            logger.error("❌ Playwright 未安装")
        
        duration = time.time() - start_time
        passed = len(readiness_issues) == 0
        details = f"准备问题: {readiness_issues}"
        
        self.record_test("构建准备状态", passed, details, duration)
        return passed
    
    def generate_report(self):
        """生成测试报告"""
        logger.info("\n" + "=" * 60)
        logger.info("生成验收测试报告")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        total_duration = sum(r['duration'] for r in self.test_results)
        
        report = f"""
# StockMonitor 打包解决方案验收测试报告

## 测试概述

**测试时间**: {self.test_start_time.strftime('%Y-%m-%d %H:%M:%S')}
**操作系统**: {self.os_type}
**Python 版本**: {self.python_version}
**项目路径**: {self.project_root}

## 测试结果

### 总体统计

- **总测试数**: {total_tests}
- **通过**: {self.passed_tests} ✅
- **失败**: {self.failed_tests} ❌
- **通过率**: {(self.passed_tests/total_tests*100):.1f}%
- **总耗时**: {total_duration:.2f} 秒

### 详细结果

| 测试项 | 状态 | 耗时 (秒) | 详情 |
|--------|------|------------|------|
"""
        
        for result in self.test_results:
            status_icon = "✅" if result['passed'] else "❌"
            status_text = "通过" if result['passed'] else "失败"
            report += f"| {result['test_name']} | {status_icon} {status_text} | {result['duration']:.2f} | {result['details']} |\n"
        
        report += f"""
## 测试结论

"""
        
        if self.failed_tests == 0:
            report += """
### 🎉 验收测试全部通过！

所有测试项目均已通过，打包解决方案已准备就绪，可以开始构建和部署。

### 下一步操作

1. 运行构建脚本: `python scripts/build.py`
2. 测试构建产物
3. 在目标平台进行安装测试
4. 进行功能验证测试
"""
        else:
            report += f"""
### ⚠️ 验收测试部分失败

共有 {self.failed_tests} 个测试项失败，需要修复后重新测试。

### 需要修复的问题

"""
            failed_results = [r for r in self.test_results if not r['passed']]
            for result in failed_results:
                report += f"- **{result['test_name']}**: {result['details']}\n"
            
            report += """
### 修复建议

1. 根据失败的测试项修复相应问题
2. 重新运行验收测试: `python tests/acceptance_test_installer.py`
3. 确保所有测试通过后再进行构建
"""
        
        report += f"""
## 测试时间戳

- **开始时间**: {self.test_start_time.strftime('%Y-%m-%d %H:%M:%S')}
- **结束时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **总耗时**: {(datetime.now() - self.test_start_time).total_seconds():.2f} 秒

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # 保存报告
        report_file = self.project_root / 'ACCEPTANCE_REPORT.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.success(f"✅ 验收测试报告已生成: {report_file}")
        
        # 同时输出到控制台
        print(report)
        
        return report_file
    
    def run_all_tests(self):
        """运行所有验收测试"""
        logger.info("\n" + "=" * 60)
        logger.info("开始运行验收测试")
        logger.info("=" * 60)
        
        test_phases = [
            ("项目结构测试", self.test_project_structure),
            ("源代码语法测试", self.test_source_code_syntax),
            ("配置文件测试", self.test_configuration_files),
            ("文档完整性测试", self.test_documentation),
            ("跨平台兼容性测试", self.test_cross_platform_compatibility),
            ("依赖完整性测试", self.test_dependencies),
            ("构建准备测试", self.test_build_readiness),
        ]
        
        for phase_name, test_func in test_phases:
            try:
                test_func()
            except Exception as e:
                logger.error(f"❌ {phase_name} 执行失败: {e}")
                self.record_test(phase_name, False, str(e), 0.0)
        
        # 生成报告
        report_file = self.generate_report()
        
        # 返回测试结果
        return self.failed_tests == 0


def main():
    """主函数"""
    tester = InstallerAcceptanceTest()
    success = tester.run_all_tests()
    
    logger.info("\n" + "=" * 60)
    if success:
        logger.success("🎉 验收测试全部通过！")
    else:
        logger.error("⚠️ 验收测试部分失败，请查看报告了解详情")
    logger.info("=" * 60)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()