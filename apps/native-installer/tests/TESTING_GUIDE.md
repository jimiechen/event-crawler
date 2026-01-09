# 测试和验收指南

## 概述

本文档提供了 StockMonitor 跨平台打包解决方案的完整测试和验收指南，包括测试方法、测试流程和验收标准。

## 测试环境准备

### 1. 环境要求

#### 系统要求

- **操作系统**: macOS 10.13+ 或 Windows 10+
- **Python 版本**: 3.11 或更高
- **内存**: 至少 4GB RAM
- **磁盘空间**: 至少 10GB 可用空间
- **网络**: 稳定的网络连接（用于下载依赖）

#### 软件依赖

```bash
# 必需软件
- Python 3.11+
- Git (用于版本控制）
- 文本编辑器 (VS Code, PyCharm 等）

# 可选软件
- Docker (用于容器化测试）
- VirtualBox/VMware (用于跨平台测试）
```

### 2. 环境配置

#### Python 环境设置

```bash
# 创建虚拟环境（推荐）
cd /Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/native-installer
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements-installer.txt
```

#### 项目路径配置

```bash
# 设置项目根目录
export PROJECT_ROOT="/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/native-installer"

# 设置测试输出目录
export TEST_OUTPUT_DIR="$PROJECT_ROOT/tests/test_reports"

# 设置日志目录
export LOG_DIR="$PROJECT_ROOT/tests/test_logs"
```

## 测试类型

### 1. 单元测试

#### 目的

验证各个组件的独立功能是否正常工作。

#### 测试范围

- 启动器 (launcher.py)
- 浏览器管理器 (browser_manager.py)
- 扩展加载器 (extension_loader.py)
- 构建管理器 (build.py)

#### 运行方法

```bash
# 方法1: 使用测试运行器
python tests/run_tests.py unit

# 方法2: 直接运行
python tests/test_installer.py

# 方法3: 使用 pytest（如果配置）
pytest tests/test_installer.py -v
```

#### 预期结果

所有测试用例应该通过，无失败或错误。

### 2. 验收测试

#### 目的

验证整个打包解决方案是否满足所有需求和验收标准。

#### 测试范围

- 项目结构完整性
- 源代码语法正确性
- 配置文件完整性
- 文档完整性
- 跨平台兼容性
- 依赖完整性
- 构建准备状态

#### 运行方法

```bash
# 方法1: 使用测试运行器
python tests/run_tests.py acceptance

# 方法2: 直接运行
python tests/acceptance_test_installer.py
```

#### 预期结果

所有验收项应该通过，通过率应该达到 95% 以上。

### 3. 集成测试

#### 目的

验证各个组件之间的集成是否正常工作。

#### 测试范围

- 完整构建流程
- 资源集成
- 平台特定安装程序生成

#### 运行方法

```bash
# 运行完整构建流程
python scripts/build.py

# 或使用调试模式
python scripts/build.py --debug
```

#### 预期结果

构建流程应该成功完成，生成正确的打包产物。

### 4. 平台测试

#### macOS 平台测试

##### 测试项目

1. **应用包生成**
   ```bash
   python scripts/build.py
   # 验证: dist/StockMonitor.app 存在
   ```

2. **DMG 生成**
   ```bash
   python scripts/setup_macos.py build/dmg
   # 验证: build/macos/StockMonitor.dmg 存在
   ```

3. **应用安装**
   ```bash
   # 手动安装
   # 1. 打开 StockMonitor.dmg
   # 2. 拖拽 StockMonitor.app 到 Applications
   # 3. 验证: /Applications/StockMonitor.app 存在
   ```

4. **应用启动**
   ```bash
   # 启动应用
   open /Applications/StockMonitor.app
   # 验证: 应用进程运行
   ```

5. **Web 服务访问**
   ```bash
   # 访问健康检查
   curl http://localhost:8000/api/v1/health
   # 预期: {"status": "healthy"}
   ```

6. **Chrome 扩展加载**
   ```bash
   # 打开 Chrome
   open -a "Google Chrome" chrome://extensions/
   # 验证: StockMonitor Extension 显示在列表中
   ```

7. **应用卸载**
   ```bash
   # 运行卸载脚本
   ~/Library/Application\ Support/StockMonitor/uninstall.sh
   # 验证: 应用已从 Applications 删除
   ```

#### Windows 平台测试（如适用）

##### 测试项目

1. **可执行文件生成**
   ```bash
   python scripts/build.py
   # 验证: dist/StockMonitor/StockMonitor.exe 存在
   ```

2. **安装程序生成**
   ```bash
   python scripts/setup_windows.py
   # 验证: build/windows/StockMonitor-Setup.exe 存在
   ```

3. **应用安装**
   ```bash
   # 运行安装程序
   StockMonitor-Setup.exe
   # 验证: 应用安装到 Program Files
   ```

4. **应用启动**
   ```bash
   # 双击启动
   StockMonitor.exe
   # 验证: 应用窗口打开
   ```

5. **Web 服务访问**
   ```bash
   # 访问健康检查
   curl http://localhost:8000/api/v1/health
   # 预期: {"status": "healthy"}
   ```

6. **Chrome 扩展加载**
   ```bash
   # 打开 Chrome
   chrome.exe chrome://extensions/
   # 验证: StockMonitor Extension 显示在列表中
   ```

7. **应用卸载**
   ```bash
   # 运行卸载程序
   uninstall.exe
   # 验证: 应用已从系统卸载
   ```

### 5. 功能测试

#### 应用启动测试

```bash
# 测试启动时间
time python src/launcher.py
# 预期: 启动时间 < 15 秒

# 检查进程
ps aux | grep StockMonitor
# 预期: 进程正在运行

# 检查日志
tail -f logs/launcher.log
# 预期: 日志无错误
```

#### Web 服务测试

```bash
# 健康检查
curl http://localhost:8000/api/v1/health
# 预期: HTTP 200, {"status": "healthy"}

# API 文档访问
curl http://localhost:8000/docs
# 预期: HTTP 200, Swagger UI 显示

# 静态文件访问
curl http://localhost:8000/static/js/navbar.js
# 预期: HTTP 200, JavaScript 文件
```

#### 浏览器自动化测试

```python
# 测试浏览器启动
from src.browser_manager import BrowserManager

async def test_browser():
    async with BrowserManager(
        extension_path='resources/chrome-extension',
        headless=True
    ) as browser:
        # 测试导航
        await browser.navigate('https://example.com')
        
        # 测试截图
        await browser.screenshot(path='test.png')
        
        # 测试脚本执行
        result = await browser.execute_script('return document.title')
        print(f"页面标题: {result}")
```

#### Chrome 扩展测试

```bash
# 1. 打开 Chrome
open -a "Google Chrome"

# 2. 访问扩展页面
# 导航到: chrome://extensions/

# 3. 验证扩展加载
# 检查: StockMonitor Extension 在列表中

# 4. 测试扩展功能
# 点击扩展图标
# 验证: 侧边栏打开

# 5. 测试扩展权限
# 检查: nativeMessaging, tabs, activeTab 权限已授予
```

#### CSV 数据测试

```bash
# 检查 CSV 文件
ls -la resources/csv-data/

# 验证 CSV 格式
head -n 5 resources/csv-data/*.csv

# 测试数据加载
python -c "
import pandas as pd
df = pd.read_csv('resources/csv-data/sample.csv')
print(f'数据行数: {len(df)}')
print(f'数据列: {list(df.columns)}')
"
```

### 6. 性能测试

#### 启动性能测试

```bash
# 冷启动时间测试
time python src/launcher.py
# 记录启动时间
# 预期: < 15 秒

# 热启动时间测试
# 重复启动 3 次
for i in {1..3}; do
    time python src/launcher.py
done
# 预期: < 5 秒

# 内存占用测试
# 启动应用后检查内存
ps aux | grep StockMonitor | awk '{print $6}'
# 预期: < 500 MB
```

#### 运行性能测试

```bash
# CPU 占用率测试
top -p $(pgrep StockMonitor) -o %cpu
# 预期: < 30%

# 内存占用率测试
top -p $(pgrep StockMonitor) -o %mem
# 预期: < 1 GB

# 响应时间测试
for i in {1..10}; do
    time curl http://localhost:8000/api/v1/health
done
# 预期: < 1 秒
```

## 验收标准

### 通过标准

1. **功能完整性**: 所有核心功能正常工作
2. **跨平台兼容性**: 在目标平台上正常运行
3. **性能达标**: 启动时间和资源占用在可接受范围内
4. **文档完整**: 所有文档准确且完整
5. **测试覆盖**: 单元测试覆盖率 > 80%
6. **无严重缺陷**: 无阻塞性缺陷

### 失败标准

1. **功能缺失**: 核心功能未实现或无法工作
2. **平台不兼容**: 在目标平台上无法运行
3. **性能不达标**: 启动时间或资源占用超出阈值
4. **文档不完整**: 关键文档缺失或不准确
5. **测试覆盖不足**: 单元测试覆盖率 < 80%
6. **存在严重缺陷**: 存在阻塞性缺陷

## 测试报告

### 报告生成

测试完成后，会自动生成以下报告：

1. **验收自测报告** (ACCEPTANCE_REPORT.md)
   - 包含所有验收测试结果
   - 总体统计和结论
   - 遗留问题和改进建议

2. **测试报告模板** (TESTING_REPORT.md)
   - 详细的测试用例清单
   - 测试结果记录表
   - 性能测试数据

### 报告位置

```
tests/
├── test_reports/           # 测试报告输出目录
│   ├── ACCEPTANCE_REPORT.md
│   └── TESTING_REPORT.md
└── test_logs/             # 测试日志目录
    ├── unit_test.log
    ├── acceptance_test.log
    └── platform_test.log
```

## 故障排除

### 常见问题

#### 1. 测试失败

**问题**: 单元测试失败

**解决方案**:
```bash
# 检查 Python 版本
python --version

# 检查依赖安装
pip list

# 重新安装依赖
pip install -r requirements-installer.txt --force-reinstall
```

#### 2. 构建失败

**问题**: PyInstaller 打包失败

**解决方案**:
```bash
# 清理构建目录
rm -rf build/ dist/

# 重新安装 PyInstaller
pip install --upgrade pyinstaller

# 检查 PyInstaller 版本
pyinstaller --version
```

#### 3. 平台测试失败

**问题**: 应用无法在目标平台上运行

**解决方案**:
```bash
# 检查平台特定依赖
# macOS: 检查 pyobjc
# Windows: 检查 pywin32

# 检查系统权限
# macOS: 检查文件访问权限
# Windows: 检查管理员权限
```

### 调试技巧

1. **启用详细日志**
   ```bash
   export LOG_LEVEL=DEBUG
   python tests/run_tests.py --verbose
   ```

2. **使用调试模式**
   ```bash
   python scripts/build.py --debug
   ```

3. **检查日志文件**
   ```bash
   # 查看启动日志
   tail -f logs/launcher.log
   
   # 查看构建日志
   tail -f logs/build.log
   ```

4. **使用 Python 调试器**
   ```bash
   # 使用 pdb
   python -m pdb tests/test_installer.py
   
   # 或使用 VS Code 调试
   code --debug tests/test_installer.py
   ```

## 持续集成

### CI/CD 配置

可以将测试集成到 CI/CD 流程中：

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: [macos-latest, windows-latest]
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements-installer.txt
      
      - name: Run unit tests
        run: python tests/run_tests.py unit
      
      - name: Run acceptance tests
        run: python tests/run_tests.py acceptance
      
      - name: Upload test reports
        uses: actions/upload-artifact@v3
        with:
          name: test-reports
          path: tests/test_reports/
```

## 最佳实践

1. **测试隔离**: 每个测试应该独立运行，不依赖其他测试
2. **测试覆盖率**: 目标是达到 80% 以上的代码覆盖率
3. **自动化测试**: 尽可能自动化测试流程
4. **测试文档**: 为每个测试用例编写清晰的文档
5. **持续测试**: 定期运行测试，及时发现回归问题
6. **性能基准**: 建立性能基准，监控性能变化
7. **跨平台测试**: 在所有目标平台上进行测试
8. **用户场景测试**: 模拟真实用户使用场景

## 资源链接

- [PyInstaller 文档](https://pyinstaller.org/en/stable/)
- [Playwright 文档](https://playwright.dev/python/)
- [pytest 文档](https://docs.pytest.org/)
- [Python 测试最佳实践](https://docs.python-guide.org/writing/tests/)

---

**文档版本**: v1.0
**最后更新**: 2025-01-08