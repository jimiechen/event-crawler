# A股智能交易与监控平台 - 实施与验收计划

## 1. 概述

本文档基于已确认的《Hyper-Alpha-Arena-A股集成方案》，详细制定了**实施改造计划**与**验收测试方案**。旨在确保从数据接入、信号同步到 AI 决策生成的全链路功能按预期落地。

---

## 2. 实施改造计划 (Implementation Plan)

本项目将分为三个阶段执行，优先打通数据链路，再完善 AI 逻辑，最后进行调度配置。

### 阶段一：数据适配层开发 (Data Adapter Layer)
**目标**：使 Arena 能够读取 stock-monitor 的基础数据和异动信号。

1.  **创建 A股数据适配器**
    *   **文件**: `Hyper-Alpha-Arena-main/backend/adapters/ashare_adapter.py` (新增)
    *   **功能**:
        *   连接 `stock-monitor` 数据库 (MySQL)。
        *   实现 `get_stock_context(symbol)` 方法。
        *   聚合数据：最新行情 (`stock_daily`) + 异动信号 (`stock_tag_relations`) + 综合评分 (`stock_score_result`)。
    *   **依赖**: `sqlalchemy`, `pandas`。

2.  **定义信号映射常量**
    *   **文件**: `Hyper-Alpha-Arena-main/backend/constants/ashare_signals.py` (新增)
    *   **内容**: 定义 A股常用 Tags (如 "3倍量", "平台突破") 与 Arena 内部 ID 的映射关系（如有必要），或直接使用字符串透传。

### 阶段二：AI 决策核心改造 (AI Core Modification)
**目标**：让 AI 决策服务识别 A股代码，并加载专用 Prompt 和上下文。

1.  **注入 A股 Prompt 模板**
    *   **操作**: 编写 SQL 脚本或 Python 脚本。
    *   **内容**: 向 `prompt_templates` 表插入 `AShare_Daily_Review_v1` 模板。
    *   **验证**: 在 Arena 前端 "Prompt Management" 可见。

2.  **改造决策上下文构建逻辑**
    *   **文件**: `Hyper-Alpha-Arena-main/backend/services/ai_decision_service.py`
    *   **修改点**: `_build_prompt_context` 方法。
    *   **逻辑**:
        *   检测 `symbol` 格式（6位数字）。
        *   若是 A股，调用 `ashare_adapter.get_stock_context`。
        *   注入 `tags`, `score`, `volume_ratio` 等特有字段。

3.  **配置 DeepSeek 模型**
    *   **操作**: 更新 `accounts` 表或通过前端配置。
    *   **内容**: 创建/更新 Account，设置 `model="deepseek-chat"`, `base_url="https://api.deepseek.com"`.

### 阶段三：调度与触发配置 (Scheduling & Trigger)
**目标**：自动化执行每日复盘。

1.  **开发每日复盘任务脚本**
    *   **文件**: `Hyper-Alpha-Arena-main/backend/tasks/ashare_daily_review.py` (新增)
    *   **逻辑**:
        *   查询当日 `stock-monitor` 中 Score > 500 或有特定 Tag 的股票。
        *   遍历列表，调用 `AIDecisionService.make_decision`。
    *   **调度**: 集成到 `apscheduler` 或通过 Cron 触发 (建议 15:30)。

---

## 3. 验收方案 (Acceptance Plan)

### 3.1 单元测试验收

| 测试项ID | 测试内容 | 前置条件 | 预期结果 |
| :--- | :--- | :--- | :--- |
| **UT-01** | **数据适配器读取** | 数据库中存在代码 `000001` 的数据和 Tags | `ashare_adapter.get_stock_context('000001')` 返回字典，包含 `tags` 列表且非空，`score` 字段存在。 |
| **UT-02** | **Prompt 上下文注入** | 模拟 A股代码输入 | `_build_prompt_context` 返回的 `context` 中包含 `signal_list` 和 `volume_ratio` 字段。 |
| **UT-03** | **Prompt 渲染测试** | 数据库已插入模板 | 使用 `jinja2` 或 `f-string` 渲染模板，生成的 Prompt 文本中包含具体的信号名称（如"3倍量"）。 |

### 3.2 集成测试验收 (端到端)

**场景**: 模拟一只股票 "600519" 触发了 "3倍量" 和 "平台突破" 信号，执行 AI 复盘。

**步骤**:
1.  **准备数据**: 在 `stock-monitor` 数据库中手动插入/确认 "600519" 当日的 Tags 记录。
2.  **触发决策**: 运行 `python scripts/trigger_ashare_review.py --symbol 600519` (临时脚本)。
3.  **验证日志**: 检查 `ai_decision_logs` 表。
    *   `symbol`: "600519"
    *   `prompt_snapshot`: 包含 "3倍量" 字样。
    *   `decision_snapshot`: 包含 DeepSeek 返回的 JSON，且 `reasoning` 字段提及了成交量放大的分析。
4.  **前端验证**: 打开 Arena Dashboard，查看 "Signals" 或 "Logs" 面板，确认能看到该条决策记录。

### 3.3 交付物清单

1.  `ashare_adapter.py` 源码。
2.  `ai_decision_service.py` 修改后的源码。
3.  `init_ashare_prompt.sql` 初始化脚本。
4.  验收测试报告 (包含测试截图或日志片段)。

---

## 4. 执行时间表 (预估)

*   **T+0.5h**: 完成数据适配器开发与测试。
*   **T+1.0h**: 完成 Prompt 模板注入与 Service 逻辑改造。
*   **T+1.5h**: 完成集成测试与验证。
*   **T+2.0h**: 交付验收。

请确认以上计划，确认无误后我将立即开始 **阶段一：数据适配层开发**。
