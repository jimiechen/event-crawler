# 可视化每日请求模拟方案文档 (Visualized Daily Simulation Plan)

## 1. 目标
利用 `stock-verify-server` 现有的 Web 控制台 (`/static/index.html`)，升级为**可视化全流程模拟中心**。用户只需在浏览器点击按钮，即可触发 T+1 日全流程模拟，并在网页端实时观看执行日志、进度状态和最终验证结果。

## 2. 核心架构设计

### 2.1 交互界面 (Frontend)
在现有的 `index.html` 基础上进行改造，增加以下可视组件：
*   **流程进度条 (Stepper)**: 直观显示当前执行步骤 (共6步)，如 "等待中" -> "进行中" (高亮) -> "完成" (绿色) / "失败" (红色)。
*   **实时日志控制台 (Live Console)**: 自动滚动显示后端执行的详细日志 (如 "Step 1: 爬虫数据注入成功...", "Step 3: 监控状态检查通过...")。
*   **控制面板**: 保留原有功能的简化版，核心增加 "🚀 执行每日全流程模拟" 按钮。

### 2.2 后端服务 (Backend)
*   **API 升级**:
    *   `POST /api/simulation/daily-flow`: 启动异步后台任务，执行 6 步模拟逻辑。
    *   `GET /api/simulation/logs`: 前端轮询接口，获取最新的模拟执行日志。
    *   `GET /api/simulation/status`: 获取当前各步骤的执行状态 (Pending/Running/Success/Failed)。
*   **日志系统**: 实现一个轻量级的内存日志缓冲 (Log Buffer)，将模拟脚本的 `print/logger` 输出捕获并暴露给 API。

## 3. 模拟流程详解 (Simulation Steps)

系统将按顺序自动执行以下步骤，并在前端实时反馈：

| 步骤 | 任务名称 | 模拟逻辑 | 前端展示 |
| :--- | :--- | :--- | :--- |
| **Step 1** | **每日问财爬虫** (08:00) | **数据预埋**: 清理旧数据，直接向数据库写入模拟的问财爬虫记录 (T日, 603601)。 | ✅ 爬虫数据就绪 |
| **Step 2** | **问财数据同步** (08:30) | **API调用**: 调用 `validate` 接口触发入库校验，确认 `stock_info` 表更新。 | ✅ 股票已入库 |
| **Step 3** | **实时监控** (09:30) | **状态检查**: 调用监控 API，验证股票是否处于 `active` 监控状态。 | ✅ 监控中 |
| **Step 4** | **盘后数据更新** (15:05) | **K线生成**: 生成 T 日模拟 K 线 (构造倍量/地量形态)，直接写入 `stock_daily`。 | ✅ K线数据已生成 |
| **Step 5** | **复盘与评分** (15:30) | **核心计算**: 依次触发 `scores/calculate` 和 `rankings/calculate`，并校验分数结果。 | ✅ 评分: 350分 |
| **Step 6** | **AI 复盘报告** (17:00) | **结果验证**: 查询仪表盘接口，确认 T 日数据已在前端可见。 | ✅ 报表已更新 |

## 4. 执行指南

### 4.1 准备工作
1.  确保 `stock-monitor-backend` (8000端口) 正常运行。
2.  确保 `stock-verify-server` (8001端口) 正常运行。

### 4.2 操作步骤
1.  浏览器访问 `http://localhost:8001/static/index.html`。
2.  在 "Stock Code" 输入框确认代码 (默认 `603601`)。
3.  点击页面中央醒目的 **"Start Daily Simulation"** 按钮。
4.  观察下方控制台的实时日志输出。
5.  观察进度条逐步变绿。
6.  等待约 10-15 秒，直至显示 "✅ Simulation Complete"。

## 5. 开发计划 (待确认)

### 5.1 前端改造 (`static/index.html`)
*   引入 Vue.js (现有代码已包含 `vue.global.prod.min.js` 引用) 或继续使用原生 JS + CSS 优化 UI。
*   增加轮询逻辑 (`setInterval`) 读取日志。

### 5.2 后端实现 (`app/services/simulator.py` & `endpoints.py`)
*   实现 `DailyFlowSimulator` 类，封装 6 步逻辑。
*   实现 `LogStream` 类，用于管理内存日志。

---
**请确认是否按此方案进行开发？**
