# Stock Arena - A股适配项目

## 项目概述

本项目是基于 Hyper-Alpha-Arena 架构的 A 股交易分析系统，采用独立包架构，保持源项目不变。

## 项目结构

```
/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/
├── Hyper-Alpha-Arena-main/          # 原项目（保持不变）
├── stock-arena-backend/                # A股后端（新增）
│   ├── app/
│   │   ├── main.py                      # FastAPI 应用入口
│   │   ├── api/                         # API 路由（待创建）
│   │   ├── models/                      # 数据模型（待创建）
│   │   ├── services/                     # 业务逻辑（待创建）
│   │   ├── config/                       # 配置（已创建）
│   │   ├── database/                     # 数据库（待创建）
│   │   └── utils/                       # 工具（待创建）
│   ├── requirements.txt                   # 依赖（已创建）
│   └── .env.example                     # 环境变量（已创建）
├── stock-arena-frontend/               # A股前端（新增）
│   ├── app/
│   │   ├── components/                  # 组件（目录已创建）
│   │   ├── contexts/                     # 上下文（目录已创建）
│   │   ├── lib/                         # 工具库（目录已创建）
│   │   ├── locales/                     # 国际化（目录已创建）
│   │   ├── main.tsx                     # 应用入口（已创建）
│   │   └── index.css                    # 样式（已创建）
│   ├── public/                           # 静态资源（目录已创建）
│   ├── package.json                       # 依赖（已创建）
│   ├── vite.config.ts                    # Vite 配置（已创建）
│   ├── tailwind.config.js                # Tailwind 配置（已创建）
│   └── tsconfig.json                     # TypeScript 配置（已创建）
└── shared-components/                   # 共用组件（新增）
    ├── layout/                          # 布局组件（已创建）
    ├── navigation/                       # 导航配置（已创建）
    ├── types/                           # 类型定义（已创建）
    └── package.json                       # 包配置（已创建）
```

## 已完成工作

### 第一阶段：环境准备和项目初始化 ✅

#### stock-arena-backend
- [x] 创建目录结构（api, models, services, config, database, utils）
- [x] 创建 requirements.txt
- [x] 创建 .env.example
- [x] 创建 main.py（FastAPI 应用入口）
- [ ] 初始化数据库
- [ ] 安装依赖并启动服务

#### stock-arena-frontend
- [x] 创建目录结构（components, contexts, lib, locales, public）
- [x] 创建 package.json
- [x] 创建 vite.config.ts
- [x] 创建 tailwind.config.js
- [x] 创建 tsconfig.json
- [x] 创建 main.tsx
- [x] 创建 index.css
- [ ] 安装依赖并启动服务

#### shared-components
- [x] 创建目录结构（layout, navigation, types）
- [x] 创建 Header.tsx
- [x] 创建 Sidebar.tsx
- [x] 创建 Footer.tsx
- [x] 创建 menu_config.ts
- [x] 创建 navigation.ts
- [x] 创建 package.json
- [ ] 安装依赖并导出

## 下一步工作

### 阶段 2：CSV 数据加载系统（3-4 天）

1. 创建 CSV 配置（config/csv_config.py）
2. 创建 CSV 加载器（services/kline_csv_loader.py）
3. 创建数据模型（models/kline.py）
4. 创建 K 线数据服务（services/kline_service.py）
5. 创建 API 路由（api/kline_routes.py）

### 阶段 3：增量更新系统（2-3 天）

1. 创建增量更新器（services/kline_incremental_updater.py）
2. 扩展定时任务（services/scheduler.py）
3. 扩展 API 路由（api/kline_routes.py）

### 阶段 4：提示词系统（2-3 天）

1. 创建提示词模板（config/prompt_templates.py）
2. 创建变量参考文档（config/PROMPT_VARIABLES_STOCK.md）
3. 创建提示词生成系统提示（config/prompt_generation_system_prompt_stock.md）
4. 创建 AI 决策服务（services/ai_decision_service.py）

### 阶段 5-15：前端组件开发（预计 20-30 天）

1. 创建股票相关组件（StockSelector, KlinesView）
2. 创建形态识别组件（PatternManager）
3. 创建量价关系组件（VolumePricePanel）
4. 创建 AI 相关组件（AiPromptChatModal, AiDecisionPanel, PromptManager）
5. 创建信号和排名组件（SignalManager, RankingView）
6. 创建投资组合组件（PortfolioView, PositionTable, AssetCurve）

## 技术栈

### 后端
- Python 3.10+
- FastAPI 0.104.1
- SQLAlchemy 2.0.23
- PostgreSQL
- Pandas 2.0+
- Akshare 1.12.0+
- Tushare 1.2.0+

### 前端
- React 18.2.0
- TypeScript 5.0+
- Vite 4.4.0
- Tailwind CSS 3.3.3
- Radix UI
- i18next 25.7.3

### 共用组件
- React 18.2.0
- TypeScript 5.0+

## 数据源

### CSV 文件（主源）
- 路径：/Users/mac/Downloads/daily
- 文件格式：{股票代码}.{交易所后缀}.csv
- 示例：000030.SZ.csv, 000031.SZ.csv

### 增量更新源
- Tushare：获取最新交易日数据
- Akshare：获取最新交易日数据

## 环境配置

### 后端
- 数据库：postgresql://user:password@localhost:5432/stock_arena
- CSV 路径：/Users/mac/Downloads/daily
- API 密钥：OPENAI_API_KEY, DEEPSEEK_API_KEY, CLAUDE_API_KEY
- 服务器：0.0.0.0:8001

### 前端
- 开发服务器：http://localhost:5174
- API 代理：/api -> http://localhost:8001

## 启动说明

### 后端启动
```bash
cd stock-arena-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app/main.py
```

### 前端启动
```bash
cd stock-arena-frontend
pnpm install
pnpm dev
```

### 共用组件安装
```bash
cd shared-components
pnpm install
pnpm build
```

## 注意事项

1. **数据库准备**：需要先创建 PostgreSQL 数据库
2. **环境变量**：需要配置 .env 文件中的数据库连接和 API 密钥
3. **CSV 文件**：需要确保 CSV 文件存在且格式正确
4. **端口冲突**：Hyper-Alpha-Arena 使用 8000/5173，stock-arena 使用 8001/5174
5. **依赖安装**：后端和前端需要分别安装依赖

## 文档参考

- [Hyper-Alpha-Arena 项目分析](/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/Hyper-Alpha-Arena-A股适配对话归档.md)
- [A 股适配分阶段实施计划](/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/Hyper-Alpha-Arena-A股适配对话归档.md)

## 版本信息

- 版本：0.1.0
- 创建日期：2025-01-13
- 最后更新：2025-01-13
