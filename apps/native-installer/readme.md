# StockMonitor 跨平台打包解决方案

## 项目概述

StockMonitor 是一个跨平台的股票监控系统，支持 Windows 和 macOS 操作系统。本打包方案将 Python 后端、Chromium 浏览器、Chrome 扩展插件和离线 CSV 数据文件打包为一个独立的可执行应用程序。

## 功能特性

- ✅ 跨平台支持（Windows 和 macOS）
- ✅ 内置 Chromium 最新稳定版
- ✅ 自动加载 Chrome 扩展插件
- ✅ 包含 Python 3.11 运行时环境
- ✅ 集成离线 CSV 历史数据文件
- ✅ 支持 Playwright 无头浏览器运行
- ✅ 提供浏览器自动化操作 API
- ✅ 自动检测操作系统并应用相应配置

## 目录结构

```
native-installer/
├── build/                    # 构建输出目录
│   ├── windows/             # Windows 打包产物
│   └── macos/               # macOS 打包产物
├── resources/               # 资源文件
│   ├── chromium/            # Chromium 浏览器二进制
│   ├── chrome-extension/    # Chrome 扩展插件
│   ├── csv-data/            # 离线 CSV 数据
│   └── configs/             # 配置文件
├── scripts/                 # 构建和安装脚本
│   ├── build.py            # 主构建脚本
│   ├── setup_windows.py    # Windows 安装脚本
│   └── setup_macos.py      # macOS 安装脚本
├── src/                     # 源代码
│   ├── launcher.py         # 启动器
│   ├── browser_manager.py  # 浏览器管理
│   └── extension_loader.py # 扩展加载器
├── pyinstaller.spec         # PyInstaller 配置
├── requirements-installer.txt # 打包依赖
└── README.md               # 本文档
```

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+ (用于构建 Chrome 扩展)
- PyInstaller 6.0+
- Playwright 1.40+

### 安装依赖

```bash
cd native-installer
pip install -r requirements-installer.txt
```

### 构建应用

#### 完整构建（推荐）

```bash
python scripts/build.py
```

这将执行以下步骤：
1. 清理构建目录
2. 准备资源文件
3. 安装依赖
4. 安装 Playwright 浏览器
5. 使用 PyInstaller 打包
6. 生成平台特定安装包

#### 快速构建（跳过依赖安装）

```bash
python scripts/build.py --skip-deps
```

#### 调试构建

```bash
python scripts/build.py --debug
```

## 平台特定说明

### Windows

#### 构建要求

- Windows 10 或更高版本
- Visual C++ Redistributable
- NSIS (用于创建安装程序)

#### 构建产物

- `dist/StockMonitor/` - 可执行文件目录
- `build/windows/StockMonitor-Setup.exe` - 安装程序

#### 安装

1. 运行 `StockMonitor-Setup.exe`
2. 按照安装向导完成安装
3. 安装完成后，可以在开始菜单和桌面找到快捷方式

#### 卸载

1. 打开"控制面板" > "程序和功能"
2. 选择 "StockMonitor"
3. 点击"卸载"

### macOS

#### 构建要求

- macOS 10.13 (High Sierra) 或更高版本
- Xcode Command Line Tools
- Python 3.11+

#### 构建产物

- `dist/StockMonitor.app` - 应用程序包
- `build/macos/StockMonitor.dmg` - 磁盘镜像

#### 安装

1. 打开 `StockMonitor.dmg`
2. 将 `StockMonitor.app` 拖拽到 `Applications` 文件夹
3. 从启动台或应用程序文件夹启动应用

#### 卸载

1. 打开终端
2. 运行卸载脚本：
   ```bash
   ~/Library/Application\ Support/StockMonitor/uninstall.sh
   ```

## 配置

### 环境变量

应用使用环境变量进行配置，主要配置文件位于 `resources/configs/.env.example`。

#### 必需配置

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_DATABASE=stock_monitor

# Tushare Token
TUSHARE_TOKEN=your_tushare_token
```

#### 可选配置

```bash
# 服务器配置
HOST=0.0.0.0
PORT=8000

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 浏览器配置
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30000
```

### 爬虫配置

爬虫配置文件位于 `resources/configs/crawler_config.yaml`，支持以下平台：

- 微博 (weibo)
- 抖音 (douyin)
- 小红书 (xiaohongshu)
- B站 (bilibili)
- 奥数 (okooo)

## 使用指南

### 启动应用

#### Windows

```bash
# 双击桌面图标或从开始菜单启动
StockMonitor.exe
```

#### macOS

```bash
# 从应用程序文件夹启动
open /Applications/StockMonitor.app
```

### 访问 Web 界面

应用启动后，可以通过浏览器访问：

- 主页: http://localhost:8000
- API 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc

### 使用浏览器自动化

应用内置了 Playwright 浏览器自动化功能，可以通过 API 调用：

```python
from src.browser_manager import BrowserManager

async def example():
    async with BrowserManager(
        extension_path='resources/chrome-extension',
        headless=True
    ) as browser:
        await browser.navigate('https://example.com')
        content = await browser.get_content()
        print(content)
```

### 使用 Chrome 扩展

Chrome 扩展会自动加载，可以通过以下方式使用：

1. 打开 Chrome 浏览器
2. 访问 `chrome://extensions/`
3. 找到 "StockMonitor Extension"
4. 点击扩展图标打开侧边栏

## 故障排除

### 常见问题

#### 1. 应用无法启动

**症状**: 双击应用图标后没有任何反应

**解决方案**:
- 检查日志文件: `logs/launcher.log`
- 确认所有依赖已正确安装
- 检查端口 8000 是否被占用

#### 2. 浏览器无法启动

**症状**: Playwright 报错无法启动浏览器

**解决方案**:
```bash
# 重新安装 Playwright 浏览器
python -m playwright install chromium
```

#### 3. Chrome 扩展未加载

**症状**: 扩展列表中找不到 StockMonitor Extension

**解决方案**:
- 确认扩展路径正确: `resources/chrome-extension`
- 检查 manifest.json 文件是否存在
- 查看浏览器控制台错误信息

#### 4. 数据库连接失败

**症状**: 应用启动后无法连接数据库

**解决方案**:
- 检查数据库服务是否运行
- 确认数据库配置正确
- 测试数据库连接:
  ```bash
  mysql -h localhost -u root -p
  ```

### 日志位置

#### Windows

- 应用日志: `%LOCALAPPDATA%\StockMonitor\logs\`
- 构建日志: `native-installer\logs\`

#### macOS

- 应用日志: `~/Library/Application Support/StockMonitor/logs/`
- 构建日志: `native-installer/logs/`

## 开发指南

### 添加新功能

1. 修改 `src/` 目录下的源代码
2. 更新 `requirements-installer.txt` 添加新依赖
3. 运行构建脚本测试:
   ```bash
   python scripts/build.py --debug
   ```

### 修改配置

1. 编辑 `resources/configs/` 下的配置文件
2. 重新构建应用
3. 测试配置是否生效

### 调试技巧

1. 使用 `--debug` 模式构建
2. 查看详细日志输出
3. 使用 PyCharm 或 VSCode 远程调试

## 技术架构

### 核心组件

1. **启动器 (launcher.py)**
   - 系统初始化
   - 环境配置
   - 依赖检查
   - 服务启动

2. **浏览器管理器 (browser_manager.py)**
   - Playwright 封装
   - 浏览器生命周期管理
   - 自动化 API
   - 扩展集成

3. **扩展加载器 (extension_loader.py)**
   - 扩展验证
   - Native Messaging 配置
   - 跨平台兼容性处理

### 打包流程

1. **资源准备**
   - 复制 Chrome 扩展
   - 准备 CSV 数据
   - 复制配置文件

2. **依赖安装**
   - 安装 Python 包
   - 安装 Playwright 浏览器

3. **PyInstaller 打包**
   - 分析依赖
   - 收集资源
   - 生成可执行文件

4. **平台特定处理**
   - Windows: 生成 NSIS 安装程序
   - macOS: 生成 .app 和 .dmg

## 性能优化

### 减小包体积

1. 排除不必要的依赖
2. 使用 UPX 压缩
3. 清理未使用的资源文件

### 提升启动速度

1. 延迟加载非核心模块
2. 优化数据库连接池
3. 使用缓存机制

### 内存优化

1. 限制浏览器实例数量
2. 定期清理缓存
3. 使用流式处理大文件

## 安全建议

1. **生产环境配置**
   - 修改默认密钥
   - 启用 HTTPS
   - 配置防火墙规则

2. **数据保护**
   - 定期备份数据库
   - 加密敏感配置
   - 限制文件访问权限

3. **更新维护**
   - 定期更新依赖
   - 监控安全公告
   - 及时修复漏洞

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎贡献代码、报告问题或提出建议！

## 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [Issues]
- 邮件: support@stockmonitor.com

---

**注意**: 本文档会持续更新，请关注最新版本。