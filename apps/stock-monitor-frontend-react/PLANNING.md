# A 股监控系统前端重构规划 (Stock Monitor Frontend Plan)

## 1. 核心策略：复用与适配 (Reuse & Adapt)
我们将在 `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-frontend-react` 建立全新的前端项目，但为了快速实现核心目标，我们将采取 **"Copy-Paste-Modify"** 策略，深度参考 `Hyper-Alpha-Arena` 的前端代码。

**为什么不直接合并？**
*   **业务逻辑差异**：A 股 (T+1, 涨跌停, 集合竞价) vs Crypto (T+0, 永续合约, 7*24)。
*   **数据结构差异**：A 股数据源 (TuShare/AKShare) 字段与 Crypto 交易所 API 完全不同。
*   **轻量化需求**：A 股复盘更侧重于"日报"和"选股"，而非高频交易终端。

## 2. 功能模块规划

### 2.1 信号管理模块 (Signal Management)
*   **目标**：实现异动信号的配置与管理。
*   **参考源**：`Hyper-Alpha-Arena/frontend/app/components/signal/SignalManager.tsx`
*   **A 股适配**：
    *   **UI 复用**：保留信号列表、添加/编辑/删除弹窗、JSON 编辑器组件。
    *   **逻辑修改**：将 Crypto 指标参数（如 `rsi_period`）适配为 A 股常用指标（`ma5`, `vol_ratio`, `turnover`）。
    *   **新增功能**：增加 A 股特有的"板块效应"或"连板高度"标签。

### 2.2 提示词管理模块 (Prompt Management)
*   **目标**：管理 AI 复盘和决策的 Prompt 模板。
*   **参考源**：`Hyper-Alpha-Arena/frontend/app/components/prompt/PromptManager.tsx`
*   **A 股适配**：
    *   **UI 复用**：保留 Prompt 列表、版本控制、变量插入辅助 UI。
    *   **逻辑修改**：变量列表替换为 A 股上下文变量（如 `{concept_list}`, `{limit_up_count}`, `{north_money_flow}`）。

### 2.3 每日复盘与 AI 决策 (Daily Review & AI Decision)
*   **目标**：展示 AI 生成的复盘报告和个股决策。
*   **参考源**：`Hyper-Alpha-Arena/frontend/app/components/analytics/AiAttributionChatModal.tsx`
*   **A 股适配**：
    *   **重构模式**：从"聊天模式"改为"日报模式" (Report View)。
    *   **布局设计**：左侧为股票列表/自选股，右侧为 AI 分析报告（支持 Markdown 渲染）。
    *   **交互逻辑**：点击股票 -> 触发 DeepSeek 实时分析 -> 展示结果。

## 3. 技术架构与目录结构

### 技术栈
*   **Framework**: React 18 + Vite
*   **Language**: TypeScript
*   **Styling**: Tailwind CSS + Shadcn UI (Radix UI) - *保持与 Arena 一致*
*   **State Management**: Zustand (轻量级，适合本场景)
*   **Charting**: Recharts (适合绘制 A 股 K 线和统计图)

### 建议目录结构
```
apps/stock-monitor-frontend-react/
├── src/
│   ├── components/
│   │   ├── business/           # 业务组件
│   │   │   ├── prompt/         # 复用 Arena (PromptManager)
│   │   │   ├── signal/         # 复用 Arena (SignalManager)
│   │   │   ├── dashboard/      # A 股专属看板
│   │   │   └── report/         # AI 复盘报告组件
│   │   ├── ui/                 # Shadcn 基础组件 (Button, Input, Dialog...)
│   │   └── layout/             # 布局组件 (Sidebar, Header)
│   ├── hooks/                  # 自定义 Hooks
│   ├── lib/                    # 工具函数 (utils, api)
│   ├── services/               # API 请求层 (Axios)
│   ├── store/                  # 全局状态 (Zustand)
│   └── types/                  # TypeScript 类型定义
```

## 4. 实施步骤

1.  **环境搭建**: 配置 Vite, Tailwind, Shadcn UI。
2.  **组件迁移**: 将 Arena 的 `ui` 文件夹和 `prompt`, `signal` 组件复制过来，解决依赖报错。
3.  **API 对接**: 修改 API 请求地址，指向 `stock-monitor-backend`。
4.  **页面组装**: 搭建主布局，集成上述模块。
