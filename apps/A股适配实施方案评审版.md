# Hyper-Alpha-Arena A股适配实施方案评审与规划

## 1. 总体评审结论

经过对 `Hyper-Alpha-Arena-main` (以下简称 **HAA**) 和 `stock-monitor-backend` (以下简称 **SMB**) 的代码库深度分析，您提出的 `Hyper-Alpha-Arena-A股适配对话归档.md` 方案总体**合理且可行**。

**核心价值点确认**：
1.  **复用 AI 基础设施**：HAA 拥有成熟的 Prompt 构建、LLM 调用（DeepSeek/OpenAI）、流式响应处理机制，这正是 SMB 缺失的核心能力。
2.  **前端可视化升级**：HAA 的 React + Radix UI 组件库远优于 SMB 的 Vue CDN 页面，能提供更好的交互体验。
3.  **架构解耦**：将 "数据计算" (SMB) 与 "决策展现" (HAA) 分离，符合单一职责原则。

**关键调整建议**：
原方案中提到 "共享数据库" 或 "合并代码"，考虑到两者分别使用 Postgres 和 MySQL，且依赖库（如 akshare 与 ccxt）可能存在环境冲突，**强烈建议采用「服务集成模式」而非「代码合并模式」**。即：SMB 继续作为独立的数据服务运行，HAA 通过 API 接口获取 A 股数据，将其作为一种新的 "资产类别" 接入 AI 决策系统。

---

## 2. 详细架构调整建议

### 2.1 后端架构：服务集成 (Service Integration)

保持两个后端独立运行，HAA 后端充当 "网关" 和 "大脑"。

*   **Stock Monitor Backend (SMB)**:
    *   **角色**: 数据提供商 (Data Provider) & 信号引擎 (Signal Engine)。
    *   **职责**: 负责爬取 A 股数据、计算形态（底分型、阳包阴）、计算评分、维护股票池。
    *   **新增**: 需要暴露标准的 REST API 供 HAA 调用（目前已有部分 controller，需标准化）。
*   **Hyper Alpha Arena Backend (HAA)**:
    *   **角色**: 决策引擎 (Decision Engine) & 用户界面 (UI Backend)。
    *   **职责**: 负责构建 Prompt、调用 DeepSeek、管理用户会话、展示前端。
    *   **新增**: `StockDataService`，用于桥接 SMB 的 API。

### 2.2 前端架构：组件复用 (Component Reuse)

利用 HAA 现有的高质量组件，扩展出 A 股专用界面。

*   **Prompt 组件**: 复用 `AiPromptChatModal`，但需增加 "A股模板" 选择。
*   **Signal 组件**: 复用 `SignalManager`，但将 "CVD/OI 信号" 替换为 "形态/评分 信号"。
*   **Analytics 组件**: 复用 `AttributionAnalysis`，用于复盘 A 股的历史决策。

---

## 3. 关键模块映射与改造方案

### 3.1 数据层：从 Crypto 到 Stock

HAA 目前高度耦合加密货币概念（Funding Rate, OI, CVD），需要建立映射层。

| Crypto 概念 (HAA) | A 股映射概念 (SMB) | 适配方案 |
| :--- | :--- | :--- |
| **Market Flow** (CVD, Taker Ratio) | **量价关系** (放量/缩量, 换手率) | 修改 `_get_metric_unit` 支持 `vol_ratio` 等单位 |
| **Funding Rate / OI** | **技术指标** (RSI, MACD, KDJ) | 扩展 Prompt 变量解析器 |
| **Regime** (7种市场状态) | **趋势判断** (多头/空头/震荡) | 映射 SMB 的 `morphology` 结果 |
| **Symbol** (BTC-USD) | **Stock Code** (600519.SH) | 修改 `SUPPORTED_SYMBOLS` 逻辑，支持动态股票代码 |

### 3.2 AI 决策层：Prompt 工程

HAA 的 `ai_decision_service.py` 和 `prompt_templates.py` 需要扩展。

**新建文件**: `backend/config/stock_prompt_templates.py`

```python
STOCK_DAILY_DECISION_TEMPLATE = """
=== 交易环境 ===
市场: 中国 A 股 (T+1 交易规则)
当前时间: {current_time_utc}

=== 账户概览 ===
可用资金: ¥{available_cash}
当前持仓: {holdings_detail}

=== 重点关注股票 (Top Focus) ===
{stock_focus_list}

=== 形态识别信号 (来自 Stock Monitor) ===
{morphology_signals}
(注: 数据包含最近 3 日的 K 线形态，如 "阳包阴", "底分型" 等)

=== 市场评分 ===
{market_score_summary}

=== 决策目标 ===
请基于上述形态信号和评分，结合 A 股 T+1 规则，给出今日的交易建议（买入/卖出/持有）。
重点分析：形态的有效性、止损位设置。

=== 输出格式 ===
{output_format}
"""
```

### 3.3 信号层：告警接入

SMB 的 `morphology_controller.py` 产生的 `three_day_pattern` 结果，直接映射为 HAA 的 Signal。

*   **原逻辑**: 监听 WebSocket -> 触发 Signal -> AI 分析
*   **新逻辑**: 定时轮询 SMB 接口 -> 发现新 Pattern -> 触发 Signal -> AI 分析

---

## 4. 实施路线图 (Roadmap)

我们不需要一次性重写所有代码，建议分三步走：

### 第一阶段：基础设施连通 (The Bridge)
**目标**：让 HAA 后端能读到 SMB 的数据。
1.  **SMB 端**: 确保 `/api/morphology/analyze/{code}` 和 `/api/stock/pool` 接口可用且稳定。
2.  **HAA 端**:
    *   创建 `backend/services/stock_data_service.py`。
    *   实现 `fetch_stock_patterns(code)` 和 `fetch_stock_pool()` 方法，通过 HTTP 请求 SMB。
    *   编写单元测试，验证 HAA 能成功获取 A 股数据。

### 第二阶段：Prompt 系统适配 (The Brain)
**目标**：让 DeepSeek 能理解 A 股数据。
1.  **模板开发**: 在 `backend/config/` 下创建 A 股专用 Prompt 模板。
2.  **变量注入**: 修改 `backend/services/ai_decision_service.py`，在 `_build_prompt_context` 中增加 `stock_context` 分支。
3.  **测试验证**: 使用 HAA 的 "Prompt Debugger" (如果有) 或直接 API 测试，验证生成的 Prompt 包含准确的 A 股形态数据。

### 第三阶段：前端可视化呈现 (The Face)
**目标**：在 UI 上操作和查看。
1.  **路由增加**: 在 HAA 前端增加 `/stock` 路由。
2.  **组件适配**:
    *   **StockSignalBoard**: 展示 SMB 识别出的 "底分型" 等形态。
    *   **AiStockChat**: 点击形态，弹出 AI 对话框（复用现有的 Chat Modal），自动带入该股票的 Prompt 上下文。
3.  **每日复盘页**: 聚合当日所有信号，一键生成 "每日决策日报"。

---

## 5. 下一步行动建议

**当前无需修改代码**。请确认上述 "服务集成" 的架构方向是否符合您的预期。如果确认，我将按照 **第一阶段：基础设施连通** 开始编写代码任务。
