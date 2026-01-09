# StockMonitor 快速开始指南

## 5分钟快速上手

### 1. 安装应用

#### Windows

1. 下载 `StockMonitor-Setup.exe`
2. 双击运行安装程序
3. 按照向导完成安装
4. 从桌面或开始菜单启动应用

#### macOS

1. 下载 `StockMonitor.dmg`
2. 双击打开磁盘镜像
3. 将 `StockMonitor.app` 拖拽到 Applications 文件夹
4. 从 Launchpad 或 Applications 文件夹启动应用

### 2. 配置数据库

应用首次启动需要配置数据库连接：

1. 打开浏览器访问 http://localhost:8000
2. 系统会自动检测并提示配置数据库
3. 填写数据库信息：
   - 主机: `localhost`
   - 端口: `3306`
   - 用户名: `root`
   - 密码: `your_password`
   - 数据库名: `stock_monitor`

### 3. 访问 Web 界面

应用启动后，可以通过以下地址访问：

- **主页**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **ReDoc 文档**: http://localhost:8000/redoc

### 4. 使用 Chrome 扩展

1. 打开 Chrome 浏览器
2. 访问 `chrome://extensions/`
3. 找到 "StockMonitor Extension"
4. 点击扩展图标打开侧边栏

### 5. 浏览器自动化

使用内置的 Playwright API 进行浏览器自动化：

```python
from src.browser_manager import BrowserManager

async def main():
    async with BrowserManager(
        extension_path='resources/chrome-extension',
        headless=True
    ) as browser:
        # 导航到网页
        await browser.navigate('https://example.com')
        
        # 获取页面内容
        content = await browser.get_content()
        print(content)
        
        # 截图
        await browser.screenshot(path='screenshot.png')
```

## 常用命令

### 启动应用

#### Windows

```bash
# 从命令行启动
StockMonitor.exe

# 或双击桌面图标
```

#### macOS

```bash
# 从命令行启动
open /Applications/StockMonitor.app

# 或从 Launchpad 启动
```

### 停止应用

#### Windows

```bash
# 使用任务管理器结束进程
# 或按 Ctrl+C 在命令行中停止
```

#### macOS

```bash
# 使用 Activity Monitor 结束进程
# 或在终端中使用 kill 命令
killall StockMonitor
```

### 查看日志

#### Windows

```bash
# 应用日志
type %LOCALAPPDATA%\StockMonitor\logs\launcher.log

# 或使用记事本打开
notepad %LOCALAPPDATA%\StockMonitor\logs\launcher.log
```

#### macOS

```bash
# 应用日志
tail -f ~/Library/Application\ Support/StockMonitor/logs/launcher.log

# 或使用 Console.app 查看
open ~/Library/Logs/
```

## 配置示例

### 基础配置

编辑 `resources/configs/.env` 文件：

```bash
# 服务器配置
HOST=0.0.0.0
PORT=8000

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_DATABASE=stock_monitor

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 浏览器配置
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30000
```

### 爬虫配置

编辑 `resources/configs/crawler_config.yaml` 文件：

```yaml
platforms:
  weibo:
    enabled: true
    base_url: "https://weibo.com"
    max_count: 100
    delay_range: [1, 3]
  
  douyin:
    enabled: true
    base_url: "https://www.douyin.com"
    max_count: 100
    delay_range: [1, 3]
```

## 故障排除快速参考

### 应用无法启动

**检查清单**:
1. 端口 8000 是否被占用
2. 数据库服务是否运行
3. 查看日志文件获取详细错误

**解决方案**:
```bash
# 检查端口占用
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # macOS

# 检查数据库
mysql -h localhost -u root -p
```

### 浏览器无法启动

**检查清单**:
1. Playwright 浏览器是否安装
2. 系统权限是否足够

**解决方案**:
```bash
# 重新安装 Playwright 浏览器
python -m playwright install chromium
```

### 扩展未加载

**检查清单**:
1. 扩展路径是否正确
2. manifest.json 是否存在

**解决方案**:
```bash
# 检查扩展目录
ls -la resources/chrome-extension/

# 验证 manifest.json
cat resources/chrome-extension/manifest.json
```

## 下一步

- 查看 [完整文档](README.md) 了解更多详细信息
- 阅读 [API 文档](http://localhost:8000/docs) 了解所有可用接口
- 查看 [配置示例](resources/configs/) 了解更多配置选项

## 获取帮助

- 查看日志文件获取详细错误信息
- 访问 GitHub Issues 报告问题
- 发送邮件至 support@stockmonitor.com 获取支持

---

**提示**: 首次使用建议先阅读完整文档，了解所有功能和配置选项。