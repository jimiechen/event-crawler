# Event Crawler 项目 Code Wiki 文档

**文档日期**: 2026-04-18  
**项目版本**: 1.0.0  
**维护者**: 开发团队

---

## 目录

1. [项目概述](#1-项目概述)
2. [整体架构](#2-整体架构)
3. [核心应用模块](#3-核心应用模块)
4. [技术栈](#4-技术栈)
5. [数据库设计](#5-数据库设计)
6. [API 接口](#6-api-接口)
7. [部署与运行](#7-部署与运行)
8. [开发指南](#8-开发指南)

---

## 1. 项目概述

### 1.1 项目简介

Event Crawler 是一个综合性的多功能项目，包含多个独立但互相关联的应用，主要涵盖：

- **AI 加密货币交易平台** - Hyper-Alpha-Arena
- **Chrome 浏览器扩展** - 网页数据采集与交互
- **股票监控系统** - A股市场数据监控与分析
- **原生服务与安装程序** - 本地部署与管理

### 1.2 核心目标

- 提供完整的 AI 驱动交易解决方案
- 实现网页数据的自动化采集与处理
- 支持股票市场的实时监控与分析
- 提供本地部署与管理的完整工具链

### 1.3 项目结构

```
/workspace/
├── apps/                    # 应用模块目录
│   ├── Hyper-Alpha-Arena-main/  # AI交易平台
│   ├── chrome-extension/         # Chrome扩展
│   ├── native-installer/         # 原生安装程序
│   ├── native-server/            # 原生服务
│   └── stock-monitor-backend/    # 股票监控后端
├── .trae/                   # 项目文档与规则
│   ├── documents/           # 项目文档
│   └── rules/               # 开发规则
└── package.json             # 根项目配置
```

---

## 2. 整体架构

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层                              │
├─────────────────────────────────────────────────────────────┤
│  Hyper-Alpha-Arena Web  │  Chrome扩展 UI  │  股票监控面板  │
└────────────────┬────────────────┬────────────────┬───────────┘
                 │                │                │
┌────────────────▼────────────────▼────────────────▼───────────┐
│                        应用服务层                              │
├─────────────────────────────────────────────────────────────┤
│  Hyper-Alpha-Arena Backend  │  Chrome扩展服务  │  股票监控服务 │
└────────────────┬────────────────┬────────────────┬───────────┘
                 │                │                │
┌────────────────▼────────────────▼────────────────▼───────────┐
│                        数据层                                  │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL  │  Redis  │  飞书多维表格  │  文件存储         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模块间关系

各应用模块相对独立，但可以通过以下方式协同工作：

1. **数据共享** - 通过数据库或文件系统共享数据
2. **API 调用** - 各模块提供 RESTful API 供其他模块调用
3. **消息通信** - 通过 WebSocket 或消息队列进行实时通信

---

## 3. 核心应用模块

### 3.1 Hyper-Alpha-Arena - AI 加密货币交易平台

#### 3.1.1 模块概述

Hyper-Alpha-Arena 是一个生产级别的 AI 加密货币交易平台，让大型语言模型（LLM）自主执行加密货币交易策略。

**主要特性**：
- 市场流向信号监控
- AI 辅助配置（无需编码）
- 交易归因分析
- 多账户实时对比
- Hyperliquid 深度集成
- 多模型 LLM 支持

#### 3.1.2 目录结构

```
Hyper-Alpha-Arena-main/
├── backend/                    # 后端服务
│   ├── adapters/              # 适配器（A股适配）
│   ├── api/                   # API 路由
│   ├── config/                # 配置文件
│   ├── constants/             # 常量定义
│   ├── database/              # 数据库相关
│   │   ├── migrations/        # 数据库迁移
│   │   ├── models.py          # 数据模型
│   │   └── connection.py      # 数据库连接
│   ├── factors/               # 因子计算
│   ├── mock/                  # Mock 数据
│   ├── repositories/          # 数据仓库层
│   ├── schemas/               # Pydantic 模式
│   ├── scripts/               # 脚本工具
│   ├── services/              # 业务逻辑层
│   ├── utils/                 # 工具函数
│   ├── main.py                # 应用入口
│   └── pyproject.toml         # Python 依赖
├── frontend/                   # 前端应用
│   ├── app/
│   │   ├── components/        # React 组件
│   │   ├── contexts/          # React Context
│   │   ├── lib/               # 工具库
│   │   └── locales/           # 国际化
│   └── package.json
└── docker-compose.yml          # Docker 配置
```

#### 3.1.3 核心服务类

| 服务类 | 文件 | 职责 |
|--------|------|------|
| `AIDecisionService` | [ai_decision_service.py](file:///workspace/apps/Hyper-Alpha-Arena-main/backend/services/ai_decision_service.py) | AI 决策服务，调用 LLM 进行交易决策 |
| `HyperliquidTradingClient` | [hyperliquid_trading_client.py](file:///workspace/apps/Hyper-Alpha-Arena-main/backend/services/hyperliquid_trading_client.py) | Hyperliquid 交易所客户端 |
| `AutoTrader` | [auto_trader.py](file:///workspace/apps/Hyper-Alpha-Arena-main/backend/services/auto_trader.py) | 自动交易执行器 |
| `SignalDetectionService` | [signal_detection_service.py](file:///workspace/apps/Hyper-Alpha-Arena-main/backend/services/signal_detection_service.py) | 信号检测服务 |
| `KlineDataService` | [kline_data_service.py](file:///workspace/apps/Hyper-Alpha-Arena-main/backend/services/kline_data_service.py) | K线数据服务 |
| `MarketFlowCollector` | [market_flow_collector.py](file:///workspace/apps/Hyper-Alpha-Arena-main/backend/services/market_flow_collector.py) | 市场流向数据采集 |
| `Scheduler` | [scheduler.py](file:///workspace/apps/Hyper-Alpha-Arena-main/backend/services/scheduler.py) | 任务调度器 |

#### 3.1.4 后端依赖

主要 Python 依赖（来自 [pyproject.toml](file:///workspace/apps/Hyper-Alpha-Arena-main/backend/pyproject.toml)）：

```toml
fastapi>=0.104.0              # Web 框架
uvicorn[standard]>=0.24.0     # ASGI 服务器
sqlalchemy>=2.0.0              # ORM
psycopg2-binary>=2.9.0         # PostgreSQL 驱动
websockets>=12.0                # WebSocket
requests>=2.31.0                # HTTP 客户端
apscheduler>=3.10.0             # 任务调度
pandas>=2.3.3                   # 数据处理
ccxt>=4.0.0                     # 加密货币交易所 API
hyperliquid-python-sdk>=0.20.0  # Hyperliquid SDK
pandas-ta==0.4.67b0             # 技术分析库
```

#### 3.1.5 前端技术栈

- **框架**: React + TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS
- **UI 组件**: shadcn/ui
- **状态管理**: React Context
- **国际化**: i18next

---

### 3.2 Chrome 扩展 - 网页数据采集

#### 3.2.1 模块概述

Chrome 浏览器扩展，用于网页数据采集、自动化交互和网页监控。支持通过 MCP（Model Context Protocol）与其他服务通信。

#### 3.2.2 目录结构

```
chrome-extension/
├── common/                   # 公共模块
│   ├── constants.ts          # 常量定义
│   ├── message-types.ts      # 消息类型
│   └── tool-handler.ts       # 工具处理器
├── components/               # Vue 组件
├── entrypoints/              # 入口文件
│   └── content.ts            # Content Script
├── inject-scripts/           # 注入脚本
├── services/                 # 服务层
│   ├── skill-registry.ts     # 技能注册
│   └── websocket-client.ts   # WebSocket 客户端
├── utils/                    # 工具函数
│   ├── data-deduplication-optimizer.ts
│   ├── enhanced-data-extractor.ts
│   ├── football-parser.js    # 足球数据解析
│   ├── tonghuashun-extractor.ts  # 同花顺数据提取
│   └── vector-database.ts    # 向量数据库
├── workers/                  # Web Workers
├── wxt.config.ts             # WXT 框架配置
└── package.json
```

#### 3.2.3 核心功能

1. **网页数据采集** - 自动提取网页内容
2. **页面交互自动化** - 模拟用户操作
3. **网络监控** - 捕获网络请求
4. **数据去重优化** - 智能数据去重
5. **向量数据库** - 语义搜索支持
6. **MCP 集成** - 与 AI 助手交互

---

### 3.3 Stock Monitor Backend - 股票监控系统

#### 3.3.1 模块概述

A股市场数据监控与分析系统，支持通达信数据同步、问财选股、飞书多维表格集成等功能。

#### 3.3.2 目录结构

```
stock-monitor-backend/
├── analyzer/                 # 分析模块
│   ├── handicap_analyzer.py  # 盘口分析
│   ├── trap_detector.py      # 陷阱检测
│   └── team_analyzer.py      # 团队分析
├── app/                      # 应用代码
│   ├── database.py           # 数据库连接
│   └── main.py               # 应用入口
├── config/                   # 配置文件
│   ├── crawler_config.yaml   # 爬虫配置
│   └── mcp_config.py         # MCP 配置
├── docs/                     # 文档
├── scripts/                  # 脚本（已重组）
│   ├── tests/                # 测试脚本
│   ├── checks/               # 检查脚本
│   ├── fixes/                # 修复脚本
│   ├── migrations/           # 数据库迁移
│   └── legacy/               # 历史脚本
├── sql/                      # SQL 脚本
├── static/                   # 静态文件
├── main.py                   # 主程序入口
└── requirements.txt          # Python 依赖
```

#### 3.3.3 核心服务类

| 服务类 | 职责 |
|--------|------|
| `DailyWorkflow` | 每日工作流编排 |
| `TdxSelectionWorkflow` | TDX 选股工作流 |
| `FeishuSyncService` | 飞书同步服务 |
| `ScreenshotService` | 截图服务 |
| `FeishuNotificationService` | 飞书通知服务 |

#### 3.3.4 主要功能

1. **通达信数据同步** - 与通达信客户端集成
2. **问财选股** - 智能股票筛选
3. **飞书多维表格** - 数据可视化与协作
4. **回测系统** - 策略历史回测
5. **数据监控** - 实时数据质量检查

---

### 3.4 Native Installer & Native Server

#### 3.4.1 Native Installer

原生安装程序，支持 Windows 和 macOS 平台的自动化安装与配置。

**目录结构**：
```
native-installer/
├── src/
│   ├── browser_manager.py     # 浏览器管理
│   ├── extension_loader.py    # 扩展加载
│   └── launcher.py            # 启动器
├── scripts/
│   ├── build.py               # 构建脚本
│   ├── setup_macos.py         # macOS 安装
│   └── setup_windows.py       # Windows 安装
└── tests/                     # 测试
```

#### 3.4.2 Native Server

原生服务器，提供 MCP 服务器功能，支持与浏览器扩展通信。

**主要文件**：
- [mcp-server.ts](file:///workspace/apps/native-server/src/mcp/mcp-server.ts) - MCP 服务器实现
- [direct-controller.ts](file:///workspace/apps/native-server/src/controller/direct-controller.ts) - 直接控制器

---

## 4. 技术栈

### 4.1 后端技术

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.9+ | 主要编程语言 |
| FastAPI | 0.104+ | Web 框架 |
| SQLAlchemy | 2.0+ | ORM |
| PostgreSQL | 13+ | 关系型数据库 |
| Redis | 7+ | 缓存/消息队列 |
| APScheduler | 3.10+ | 任务调度 |
| Pandas | 2.3+ | 数据处理 |
| Docker | latest | 容器化部署 |

### 4.2 前端技术

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18+ | UI 框架 |
| TypeScript | 5+ | 类型安全 |
| Vite | 5+ | 构建工具 |
| Tailwind CSS | 3+ | 样式框架 |
| shadcn/ui | latest | UI 组件库 |

### 4.3 浏览器扩展技术

| 技术 | 用途 |
|------|------|
| WXT | 扩展开发框架 |
| Vue 3 | UI 框架 |
| TypeScript | 类型安全 |
| Web Workers | 后台计算 |

---

## 5. 数据库设计

### 5.1 Hyper-Alpha-Arena 数据库

主要数据表（定义在 [models.py](file:///workspace/apps/Hyper-Alpha-Arena-main/backend/database/models.py)）：

| 表名 | 用途 |
|------|------|
| `users` | 用户表 |
| `accounts` | 账户表（AI 交易者） |
| `trading_configs` | 交易配置 |
| `orders` | 订单表 |
| `positions` | 持仓表 |
| `ai_decision_logs` | AI 决策日志 |
| `crypto_klines` | K线数据 |
| `signal_pools` | 信号池 |
| `prompt_templates` | 提示词模板 |
| `account_asset_snapshots` | 资产快照 |

### 5.2 Stock Monitor 数据库

主要数据表：

| 表名 | 用途 |
|------|------|
| `stock_daily` | 股票日线数据 |
| `wencai_selections` | 问财选股结果 |
| `tdx_selections` | TDX 选股结果 |
| `screenshot_analysis` | 截图分析 |
| `timed_tasks` | 定时任务 |

---

## 6. API 接口

### 6.1 Hyper-Alpha-Arena API

主要 API 路由（在 [main.py](file:///workspace/apps/Hyper-Alpha-Arena-main/backend/main.py) 中注册）：

| 路由模块 | 文件 | 功能 |
|----------|------|------|
| `market_data_router` | [market_data_routes.py](file:///workspace/apps/Hyper-Alpha-Arena-main/backend/api/market_data_routes.py) | 市场数据 |
| `order_router` | [order_routes.py](file:///workspace/apps/Hyper-Alpha-Arena-main/backend/api/order_routes.py) | 订单管理 |
| `account_router` | [account_routes.py](file:///workspace/apps/Hyper-Alpha-Arena-main/backend/api/account_routes.py) | 账户管理 |
| `hyperliquid_router` | [hyperliquid_routes.py](file:///workspace/apps/Hyper-Alpha-Arena-main/backend/api/hyperliquid_routes.py) | Hyperliquid 交互 |
| `signal_router` | [signal_routes.py](file:///workspace/apps/Hyper-Alpha-Arena-main/backend/api/signal_routes.py) | 信号管理 |
| `prompt_router` | [prompt_routes.py](file:///workspace/apps/Hyper-Alpha-Arena-main/backend/api/prompt_routes.py) | 提示词管理 |
| `analytics_router` | [analytics_routes.py](file:///workspace/apps/Hyper-Alpha-Arena-main/backend/api/analytics_routes.py) | 分析统计 |

### 6.2 WebSocket 接口

- `/ws` - 实时数据推送 WebSocket 端点

---

## 7. 部署与运行

### 7.1 Hyper-Alpha-Arena 部署

#### 使用 Docker Compose（推荐）

```bash
# 进入项目目录
cd /workspace/apps/Hyper-Alpha-Arena-main

# 启动服务
docker compose up -d --build

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

访问地址：`http://localhost:8802`

#### 环境变量配置

复制 `.env.example` 为 `.env` 并配置：

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/hyper_alpha_arena
OPENAI_API_KEY=your-api-key
HYPERLIQUID_PRIVATE_KEY=your-private-key
```

### 7.2 Stock Monitor 运行

```bash
# 进入项目目录
cd /workspace/apps/stock-monitor-backend

# 安装依赖
pip install -r requirements.txt

# 每日选股模式
python main.py --mode daily

# 回测模式
python main.py --mode backtest --start-date 2026-01-01 --end-date 2026-04-18

# 数据检查模式
python main.py --mode check
```

### 7.3 Chrome 扩展开发

```bash
# 进入项目目录
cd /workspace/apps/chrome-extension

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建
npm run build
```

在 Chrome 中加载 `dist` 目录作为扩展。

---

## 8. 开发指南

### 8.1 代码规范

项目遵循以下规范文档：

- [RULES_GENERAL.md](file:///workspace/.trae/documents/rules/RULES_GENERAL.md) - 通用规范
- [RULES_PYTHON.md](file:///workspace/.trae/documents/rules/RULES_PYTHON.md) - Python 规范
- [RULES_FLUTTER.md](file:///workspace/.trae/documents/rules/RULES_FLUTTER.md) - Flutter 规范

### 8.2 Git 工作流

项目使用 husky 和 commitlint 进行提交规范管理：

- `pre-commit` - 提交前检查
- `commit-msg` - 提交消息规范
- `pre-push` - 推送前检查

### 8.3 开发环境配置

#### Hyper-Alpha-Arena 后端开发

```bash
cd /workspace/apps/Hyper-Alpha-Arena-main/backend

# 使用 uv 安装依赖
uv sync

# 启动开发服务器
uv run python main.py
```

#### Hyper-Alpha-Arena 前端开发

```bash
cd /workspace/apps/Hyper-Alpha-Arena-main/frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

### 8.4 测试

#### Hyper-Alpha-Arena 后端测试

```bash
cd /workspace/apps/Hyper-Alpha-Arena-main/backend
uv run pytest
```

#### Stock Monitor 测试

```bash
cd /workspace/apps/stock-monitor-backend
python run_tests.py
```

---

## 附录

### A. 相关文档

- [Hyper-Alpha-Arena README](file:///workspace/apps/Hyper-Alpha-Arena-main/README.md)
- [项目架构提案](file:///workspace/.trae/documents/CTO_ARCHITECTURE_PROPOSAL_V1.md)
- [主路线图](file:///workspace/.trae/documents/MASTER_ROADMAP.md)

### B. 联系方式

- GitHub: https://github.com/HammerGPT/Hyper-Alpha-Arena
- Telegram: https://t.me/+RqxjT7Gttm9hOGEx

---

**文档结束**

*最后更新: 2026-04-18*
