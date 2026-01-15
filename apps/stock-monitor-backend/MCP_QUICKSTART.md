# MCP快速开始指南

## 概述

本指南帮助你快速开始使用DeepSeek + Trae AI模型协作系统。

## 前置条件

- Python 3.8+
- Node.js 16+
- DeepSeek账号
- Trae IDE（支持MCP）

## 快速安装

### 方式一：使用自动化脚本（推荐）

```bash
# 进入项目目录
cd /Users/mac/StudioProjects/open-citycloud/projects/event-crawler

# 运行安装脚本
bash scripts/install_mcp.sh
```

安装脚本会自动完成：
1. 检查Python和Node.js版本
2. 创建Python虚拟环境
3. 安装所有Python依赖
4. 安装Playwright浏览器
5. 配置环境变量
6. 创建协作文档目录
7. 初始化数据库
8. 安装TypeScript MCP工具
9. 编译TypeScript代码

### 方式二：手动安装

#### 1. 安装Python依赖

```bash
cd apps/stock-monitor-backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 升级pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium
```

#### 2. 配置环境变量

```bash
# 复制配置示例
cp .env.mcp.example .env

# 编辑.env文件，填入DeepSeek登录信息
# DEEPSEEK_EMAIL=your_email@example.com
# DEEPSEEK_PASSWORD=your_password
```

#### 3. 创建协作文档目录

```bash
cd apps/stock-monitor-backend
mkdir -p collaboration_docs/{daily_progress,weekly_report,technical_review,test_report,archive}
```

#### 4. 初始化数据库

```bash
cd apps/stock-monitor-backend
python3 -c "
from app.database import engine
from app.models.collaboration_log import Base
import asyncio

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('数据库初始化完成')

asyncio.run(init_db())
"
```

#### 5. 安装TypeScript MCP工具

```bash
# 安装DeepSeek MCP工具
cd mcp-tools/deepseek-mcp
npm install
npm run build

# 安装协作文档MCP工具
cd ../../collaboration-tools
npm install
npm run build
```

## 快速启动

### 方式一：使用自动化脚本（推荐）

```bash
# 进入项目目录
cd /Users/mac/StudioProjects/open-citycloud/projects/event-crawler

# 运行启动脚本
bash scripts/start_mcp.sh
```

启动脚本会自动完成：
1. 激活虚拟环境
2. 启动MCP API服务
3. 启动DeepSeek MCP工具
4. 启动协作文档MCP工具
5. 保存服务PID

### 方式二：手动启动

#### 1. 启动MCP API服务

```bash
cd apps/stock-monitor-backend
source venv/bin/activate
python3 main_mcp.py
```

#### 2. 启动DeepSeek MCP工具（新终端）

```bash
cd mcp-tools/deepseek-mcp
npm run start
```

#### 3. 启动协作文档MCP工具（新终端）

```bash
cd mcp-tools/collaboration-tools
npm run start
```

## 验证安装

### 1. 检查MCP API服务

```bash
curl http://localhost:8000/mcp/health
```

预期响应：
```json
{
  "status": "healthy",
  "timestamp": "2026-01-14 10:30:00",
  "services": {
    "deepseek": true,
    "collaboration": true
  }
}
```

### 2. 检查MCP工具

查看MCP工具日志，确认工具已启动。

### 3. 测试DeepSeek登录

```bash
curl -X POST http://localhost:8000/mcp/deepseek/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_email@example.com",
    "password": "your_password"
  }'
```

## Trae IDE配置

### 1. 配置MCP服务器

在Trae IDE中配置MCP服务器：

```json
{
  "mcpServers": [
    {
      "name": "deepseek-mcp",
      "command": "node",
      "args": [
        "/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/mcp-tools/deepseek-mcp/dist/mcp-server.js"
      ],
      "env": {
        "MCP_API_URL": "http://localhost:8000"
      }
    },
    {
      "name": "collaboration-tools",
      "command": "node",
      "args": [
        "/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/mcp-tools/collaboration-tools/dist/mcp-server.js"
      ],
      "env": {
        "MCP_API_URL": "http://localhost:8000"
      }
    }
  ]
}
```

### 2. 配置允许的模型

在Trae IDE中设置允许使用的模型：

- GLM4.7
- Gemini
- DeepSeek

### 3. 验证MCP连接

在Trae IDE中：
1. 打开MCP工具面板
2. 查看已连接的MCP服务器
3. 测试工具调用

## 第一个使用示例

### 示例：创建每日进度文档

在Trae IDE中使用GLM4.7：

1. 调用MCP工具 `create_collaboration_doc`
2. 输入参数：
   ```json
   {
     "doc_type": "daily_progress",
     "title": "2026-01-14 每日进度",
     "content": "今日完成了MCP系统的安装和配置工作",
     "author": "GLM4.7"
   }
   ```
3. 查看返回结果，确认文档创建成功

### 示例：调用DeepSeek

在Trae IDE中使用GLM4.7：

1. 调用MCP工具 `deepseek_login`
2. 输入DeepSeek账号和密码
3. 查看登录结果

4. 调用MCP工具 `send_message_to_deepseek`
5. 输入消息：`请分析event-crawler项目的整体架构`
6. 查看DeepSeek的响应

## 常见问题

### 问题1：安装脚本失败

**解决方案**：
1. 检查Python和Node.js版本
2. 确保有网络连接
3. 查看错误日志

### 问题2：MCP API服务启动失败

**解决方案**：
1. 检查端口8000是否被占用
2. 检查.env配置文件
3. 查看日志文件 `mcp_collaboration.log`

### 问题3：DeepSeek登录失败

**解决方案**：
1. 检查邮箱和密码是否正确
2. 确保账号可以正常登录DeepSeek网页版
3. 检查网络连接

### 问题4：MCP工具无法连接

**解决方案**：
1. 确认MCP API服务已启动
2. 检查MCP_API_URL配置
3. 查看MCP工具日志

## 下一步

安装和启动成功后，你可以：

1. 查看 [MCP使用示例](MCP_USAGE_EXAMPLES.md) 了解更多使用场景
2. 查看 [MCP配置说明](MCP_CONFIG_GUIDE.md) 了解详细配置
3. 查看 [故障排查指南](MCP_TROUBLESHOOTING.md) 解决常见问题

## 停止服务

### 使用自动化脚本

```bash
bash scripts/stop_mcp.sh
```

### 手动停止

```bash
# 停止MCP API服务
# 在终端中按Ctrl+C

# 停止MCP工具
# 在各自的终端中按Ctrl+C
```

## 日志查看

### MCP API服务日志

```bash
tail -f apps/stock-monitor-backend/mcp_collaboration.log
```

### DeepSeek MCP工具日志

查看启动DeepSeek MCP工具的终端输出。

### 协作文档MCP工具日志

查看启动协作文档MCP工具的终端输出。

## 更多资源

- [MCP配置说明](MCP_CONFIG_GUIDE.md)
- [MCP使用示例](MCP_USAGE_EXAMPLES.md)
- [故障排查指南](MCP_TROUBLESHOOTING.md)
- [系统README](README_MCP.md)
- [实施总结](IMPLEMENTATION_SUMMARY.md)

---

*快速开始指南最后更新: 2026-01-14*