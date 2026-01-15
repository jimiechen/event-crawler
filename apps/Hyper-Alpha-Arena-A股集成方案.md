# A股智能交易与监控平台 - 提示词与信号集成方案

## 1. 方案概述

本方案旨在将 `stock-monitor-backend`（A股数据监控与异动分析）与 `Hyper-Alpha-Arena-main`（AI 决策与交易执行）深度融合。

**核心目标**：
1.  **信号互通**：将 A股监控系统产生的“异动信号”（如 3倍量、地量、突破）无缝接入 Arena 的信号管理体系。
2.  **每日复盘**：利用 DeepSeek 大模型，结合 A股市场数据和异动信号，自动生成每日个股复盘报告和交易决策。
3.  **提示词驱动**：通过 Arena 的提示词（Prompt）管理系统，灵活调整 AI 的分析逻辑和决策风格。

---

## 2. 信号管理集成 (Signal Management)

### 2.1 信号源分析 (`stock-monitor-backend`)

在 A股监控系统中，信号被称为 **"Tags" (标签)**。
-   **定义表**: `stock_tags_info` (包含标签名称、分值，如 "3倍量", score: 300)。
-   **关联表**: `stock_tag_relations` (记录某只股票在某日触发了哪些标签)。
-   **生成逻辑**: 由 `VolumeAnalysisService.generate_daily_tags` 每日盘后计算生成。

**常见 A股异动信号示例**：
| 标签名称 | 分值 | 含义 |
| :--- | :--- | :--- |
| **3倍量** | 300 | 当日成交量是昨日的 3 倍以上 |
| **60日地量** | 600 | 过去 60 个交易日内的最低成交量 |
| **价格双重突破** | 500 | 收盘价同时突破近期关键压力位 |
| **平台突破** | 400 | 突破长期横盘平台 |

### 2.2 信号同步机制 (SignalSyncer)

我们需要在 `Hyper-Alpha-Arena` 中建立一个同步机制，将上述 Tags 映射为 Arena 可识别的信号。

**同步策略**:
无需将所有 A股历史信号导入 Arena 数据库，建议采用 **"即时查询 + 映射"** 的轻量化方案。

1.  **信号定义映射**:
    在 Arena 的 `signals` 表中预置 A股常用信号定义，以便在前端展示和筛选。

2.  **数据获取适配器 (`AShareDataAdapter`)**:
    在 Arena 的 `ai_decision_service.py` 中实现适配器，直接读取 `stock-monitor-backend` 的数据库或调用其 API。

```python
# 伪代码示例：A股数据适配器
async def get_ashare_context(stock_code: str):
    # 1. 调用 stock-monitor API 获取基础数据 (价格、涨跌幅、成交量)
    # 2. 调用 tag_controller 获取当日 Tags
    # 3. 组装为标准 Context 字典
    return {
        "symbol": stock_code,
        "price": 10.50,
        "change_percent": 5.2,
        "tags": ["3倍量", "平台突破"],  # 关键信号列表
        "score": 850,                  # 综合评分
        "technical_pattern": "放量突破前期高点" 
    }
```

---

## 3. 提示词管理集成 (Prompt Management)

利用 `Hyper-Alpha-Arena` 现有的 `PromptTemplate` 系统，创建专门针对 A股复盘的提示词模板。

### 3.1 模板设计 (A股复盘专用)

**模板名称**: `AShare_Daily_Review_v1`
**适用场景**: 每日收盘后，针对当日有异动的股票进行复盘分析。

**模板内容 (Template Text)**:

```text
你是一位拥有20年经验的A股资深交易员，擅长量价分析和龙头战法。
请根据以下数据，对股票 【{{symbol}} - {{stock_name}}】 进行今日复盘分析。

### 1. 市场数据
- **收盘价**: {{close_price}} ({{change_percent}}%)
- **成交量**: {{volume}} 手 (量比: {{volume_ratio}})
- **流通市值**: {{market_cap}} 亿
- **所属板块**: {{industry}}

### 2. 异动信号 (关键!)
系统检测到今日触发了以下异动信号：
{{#each tags}}
- 【{{this}}】
{{/each}}

### 3. 综合评分
当前系统评分: {{total_score}} 分 (分数越高代表爆发力越强)

### 4. 任务要求
请结合上述数据和信号，进行深度分析：
1.  **异动解读**: 解释为什么会出现今天的异动信号？(例如：3倍量意味着主力资金介入...)
2.  **主力意图**: 判断主力是在洗盘、出货、还是启动行情？
3.  **明日预演**: 预测明日可能的走势 (高开/低开/震荡)，并给出关键压力位和支撑位。
4.  **操作建议**: 给出明确的交易指令 (买入/卖出/持有/观望)，并说明仓位控制建议。

### 5. 输出格式
请以 JSON 格式输出，包含以下字段：
{
    "summary": "一句话点评",
    "trend": "看涨/看跌/震荡",
    "support_price": 10.20,
    "pressure_price": 11.50,
    "action": "BUY/SELL/HOLD",
    "reasoning": "详细分析内容..."
}
```

### 3.2 变量注入 (Context Injection)

在 `ai_decision_service.py` 的 `_build_prompt_context` 方法中，需要增强对 A股数据的支持：

```python
async def _build_prompt_context(self, symbol: str, ...):
    context = {}
    
    if is_ashare(symbol):  # 判断是否为6位数字代码
        # 获取 A股 专用上下文
        ashare_data = await self.ashare_adapter.get_data(symbol)
        context.update({
            "stock_name": ashare_data.name,
            "industry": ashare_data.industry,
            "volume_ratio": ashare_data.vol_ratio,
            "tags": ashare_data.tag_names,  # 注入信号列表 ["3倍量", "突破"]
            "total_score": ashare_data.score
        })
    else:
        # 原有的 Crypto 上下文逻辑
        pass
        
    return context
```

---

## 4. DeepSeek API 集成与每日复盘流程

### 4.1 DeepSeek 配置
在 `Hyper-Alpha-Arena` 前端 "Account Settings" 中：
1.  创建一个新账号 "DeepSeek A股分析师"。
2.  Model 选择: `deepseek-chat` (或自定义输入)。
3.  Base URL: `https://api.deepseek.com/v1` (示例)。
4.  API Key: 输入您的 DeepSeek Key。
5.  绑定 Prompt: 选择 `AShare_Daily_Review_v1`。

### 4.2 每日复盘自动化流程

1.  **盘后触发 (15:30)**:
    `stock-monitor-backend` 完成当日数据清洗和 Tags 生成。

2.  **筛选目标**:
    从 `stock_score_result` 表中筛选出当日 `total_score > 500` 或触发特定 Tags (如"3倍量") 的股票列表。

3.  **批量决策**:
    Arena 的 `ScheduledTask` 遍历上述股票列表，逐一调用 `AIDecisionService.make_decision(symbol)`。

4.  **结果持久化**:
    DeepSeek 返回的 JSON 分析结果存入 `ai_decision_logs` 表。

5.  **前端展示**:
    在 Arena 的 "Dashboard" 或 "Signals" 页面，展示当日复盘结果。
    *   **列表页**: 显示 股票代码、异动信号、AI 建议 (买入/持有)。
    *   **详情页**: 显示 DeepSeek 生成的完整分析报告。

---

## 6. 实施进度 (Implementation Status)

### Phase 0: 基础设施集成 (已完成)
- [x] 配置 `stock-monitor-backend` 连接 Arena 数据库 (PostgreSQL)
- [x] 编写脚本同步 A 股 Prompt 模板到 Arena `prompt_templates` 表
- [x] 编写脚本同步 A 股 Signal 定义到 Arena `signal_definitions` 表
- [x] 验证跨数据库连接和数据读取

### Phase 1: 数据适配器层 (开发中)
- [x] 实现 `ArenaAdapter`：用于从 Arena DB 获取 Prompt 和 Signal
- [x] 实现 `AShareAdapter`：用于获取 A 股行情、财务数据，并映射到 Prompt 变量
- [x] 增强 `AShareAdapter`：增加 MA5, MA10, MA20 等技术指标计算
- [ ] 单元测试：验证适配器数据获取正确性

### Phase 2: AI 决策服务 (已完成)
- [x] 实现 `AIDecisionService`：集成 Adapter，组装 Prompt，调用 DeepSeek
- [x] 增加 JSON Schema 验证：使用 Pydantic 确保大模型输出符合前端要求
- [x] 集成测试：验证 Prompt -> Context -> AI -> Decision 完整流程

### Phase 3: 前端与调度 (进行中)
- [x] 初始化 React + TypeScript 前端项目 (`stock-monitor-frontend-react`)
- [x] 更新 `TaskExecutor`：增加每日 15:30 自动触发 AI 复盘的调度任务
- [ ] 前端页面开发：展示 AI 决策结果
- [ ] 调度逻辑实现：批量生成决策任务

## 7. 使用指南 (Usage Guide)

### 7.1 本地开发环境配置
- **Arena DB**: 确保 Postgres 运行在 `192.168.1.6:5432`，用户/密码 `alpha_user`/`alpha_pass`。
- **A股 DB**: 确保 MySQL 运行在 `192.168.1.6:3306`，用户/密码 `root`/`12345678`。
- **Redis**: 确保 Redis 运行在 `192.168.1.6:6379`。

### 7.2 提示词管理
在 `Hyper-Alpha-Arena` 的数据库 `prompt_templates` 表中，已预置 `ashare_default_v1` 模板。
如需修改 AI 分析逻辑，请直接更新该表中的 `template_text` 字段，无需修改代码。

### 7.3 信号管理
在 `Hyper-Alpha-Arena` 的数据库 `signal_definitions` 表中，已预置 `3倍量` (volume_3x) 等基础信号。
在 `stock-monitor-backend` 中生成的 Tags 会自动映射到这些信号定义，用于 AI 决策上下文。
