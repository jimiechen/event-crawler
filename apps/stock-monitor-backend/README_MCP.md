# DeepSeek + Trae AI 模型协作系统

## 项目概述

这是一个支持 DeepSeek、GLM4.7、Gemini 3 Pro 三个模型协作交流的系统，已完全集成到 `stock-monitor-backend` 服务中。它实现每日进度汇报、计划讨论、技术方案评审等功能。

## 系统架构

```
GLM4.7/Gemini (Trae AI) 
    ↓ (通过 mcp_bridge.py)
MCP Bridge (Stdio)
    ↓ (HTTP REST)
stock-monitor-backend (Port 56666)
    ↓
DeepSeek 爬虫 (集成在后端，单例浏览器) → 浏览器自动化 → DeepSeek 网页版
    ↓
返回响应给 GLM4.7/Gemini → 整合项目信息 → 更新文档
    ↓
循环协作，直到达成共识
```

## 目录结构

```
projects/event-crawler/
├── apps/
│   └── stock-monitor-backend/
│       ├── app/
│       │   ├── crawler/
│       │   │   └── deepseek_crawler.py        # DeepSeek 爬虫实现 (单例模式)
│       │   ├── services/
│       │   │   └── deepseek_mcp_service.py    # DeepSeek MCP 服务逻辑
│       │   ├── api/
│       │   │   └── mcp_controller.py          # MCP REST & SSE 接口
│       │   └── ...
│       ├── mcp_bridge.py                      # Trae MCP 桥接脚本
│       ├── requirements.txt
│       └── README_MCP.md
```

## 快速开始

### 1. 环境要求

- Python 3.8+
- Playwright 浏览器
- 数据库 (MySQL/PostgreSQL)

### 2. 安装依赖

```bash
cd apps/stock-monitor-backend

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 3. 配置环境

```bash
# 复制配置示例
cp .env.mcp.example .env

# 编辑 .env 文件，配置数据库连接等信息
```

### 4. 启动后端服务

必须使用 **56666** 端口启动服务，因为 MCP Bridge 默认连接此端口：

```bash
# 方式一：使用兼容脚本（推荐，解决 uvloop 冲突）
python3 run.py --port 56666

# 方式二：直接使用 uvicorn (需自行处理 loop 配置)
uvicorn app.main:app --host 0.0.0.0 --port 56666 --loop asyncio
```

### 5. 配置 Trae MCP

编辑 `/Users/mac/StudioProjects/open-citycloud/.trae/mcp-config.json`，添加如下配置：

```json
{
    "mcpServers": {
        "DeepSeek": {
            "command": "python3",
            "args": [
                "/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/mcp_bridge.py"
            ],
            "env": {
                "PYTHONPATH": "/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend"
            }
        }
    }
}
```

## 功能特性

1.  **会话保持**：后端使用单例模式管理 Playwright 浏览器实例，确保多次请求复用同一个浏览器窗口，避免频繁重启。
2.  **兼容性**：完全兼容原有的 `run.py` 启动方式，不影响原有业务逻辑。
3.  **MCP 桥接**：提供 `mcp_bridge.py` 脚本，将 REST 接口转换为 Trae 可识别的 Stdio MCP 协议。

## API 接口 (后端)

基础前缀：`/mcp`

### DeepSeek 相关操作

#### 获取会话列表
```bash
GET /mcp/deepseek/chats
```

#### 读取会话内容
```bash
GET /mcp/deepseek/chats/{chat_id}
```

#### 发送消息
```bash
POST /mcp/deepseek/send
Content-Type: application/json

{
  "text": "你好，请分析这个项目...",
  "chat_id": "optional_chat_id"
}
```
