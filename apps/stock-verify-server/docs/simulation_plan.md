# 每日请求模拟方案文档

## 1. 目标
在 `stock-verify-server` 工程中，通过编写自动化脚本，模拟 `stock-monitor-backend` 的每日核心业务流程（T+1日）。验证系统在完整的一天内的运行逻辑，包括数据爬取、同步、监控、盘后更新、评分及AI复盘。

## 2. 环境说明
*   **执行端**: `stock-verify-server` (独立验证服务)
*   **被测端**: `stock-monitor-backend` (核心业务服务, http://localhost:8000)
*   **数据库**: 共享同一个 PostgreSQL 数据库 (通过 `stock-verify-server` 直接连接数据库进行数据预埋和校验)

## 3. 模拟流程 (Simulation Workflow)

本方案将按时间顺序模拟以下 6 个核心任务。

### 3.1 每日问财爬虫 (wencai_daily_crawler)
*   **原定时间**: 08:00
*   **业务逻辑**: 爬取前一交易日问财上榜股票。
*   **模拟方案**:
    *   **动作**: 由于爬虫依赖外部网络且不稳定，采用 **数据预埋** 方式模拟。直接向 `crawler_data` 表（或问财相关存储表）插入一条模拟的爬虫结果记录。
    *   **数据**: 股票代码 `603601`，日期 `T日`（模拟当天），来源 `wencai`。
    *   **API/操作**: `stock-verify-server` 直接执行 SQL 插入。

### 3.2 问财数据同步 (wencai_data_sync)
*   **原定时间**: 08:30
*   **业务逻辑**: 将爬取的数据同步到 `stock_info` 表，标记 `source='wencai'`。
*   **模拟方案**:
    *   **动作**: 调用后端 API 触发同步，或模拟同步逻辑。
    *   **API**: `POST /api/v1/wencai/validate`
    *   **参数**: `{"stock_code": "603601", "check_date": "YYYY-MM-DD"}`
    *   **说明**: 该接口会触发“校验-爬取-入库”流程。若前一步已预埋数据，此步可作为“确认入库”的动作。或者直接检查 `stock_info` 表中是否存在该股票且 `source='wencai'`。

### 3.3 实时监控 (realtime_monitor)
*   **原定时间**: 09:30 - 15:00
*   **业务逻辑**: 实时计算量比、地量。
*   **模拟方案**:
    *   **动作**: 确认股票已被加入监控列表，并获取监控状态。
    *   **API**: `GET /api/v1/monitors?stock_code=603601`
    *   **预期**: 返回结果中包含该股票，且状态为 `active`。

### 3.4 盘后数据同步 (post_market_update)
*   **原定时间**: 15:05
*   **业务逻辑**: 同步全市场当日 K 线数据。
*   **模拟方案**:
    *   **动作**: 模拟 T 日收盘数据（K线），并触发同步入库。
    *   **步骤 1 (数据生成)**: `stock-verify-server` 生成 `603601` 的 T 日 K 线数据（模拟收盘价、成交量），直接插入 `stock_daily` 表（模拟 Tushare 数据已就绪）。
    *   **步骤 2 (触发同步)**: 调用后端同步接口（可选，若直接插库则视为同步完成）。
    *   **API**: `POST /api/v1/stock/sync/tushare` (参数: `{"stock_codes": ["603601"], "start_date": "YYYY-MM-DD"}`)
    *   **注意**: 若无法连接真实 Tushare，步骤 1 的直接插库是必须的。

### 3.5 每日复盘与评分 (daily_acceptance)
*   **原定时间**: 15:30
*   **业务逻辑**: 异动分析、评分计算、排名计算。
*   **模拟方案**:
    *   **动作 1 (评分)**: 触发当日评分计算。
        *   **API**: `POST /api/v1/scores/calculate/{date_str}`
    *   **动作 2 (排名)**: 触发当日排名计算。
        *   **API**: `GET /api/v1/rankings/calculate/{date_str}`
    *   **验证**: 查询 `stock_score_result` 表，确认 `603601` 在 T 日有分数，且 `ranking` 字段已更新。

### 3.6 AI 复盘报告 (daily_ai_review)
*   **原定时间**: 17:00
*   **业务逻辑**: 生成每日 AI 分析报告。
*   **模拟方案**:
    *   **动作**: 验证复盘数据源是否准备就绪（仪表盘数据）。
    *   **API**: `GET /api/v1/dashboard/stats` 和 `GET /api/v1/dashboard/stocks`
    *   **说明**: 确认接口返回正常，且包含当日数据。

## 4. 执行脚本设计
将在 `projects/event-crawler/apps/stock-verify-server/scripts/` 下创建 `simulate_daily_flow.py`。

### 脚本流程
1.  **Setup**: 初始化数据库连接，确定模拟日期（T日，默认为今天或明天）。
2.  **Step 1 (08:00)**: 检查/清理 T 日 `603601` 的旧数据。插入模拟的问财爬虫数据。
3.  **Step 2 (08:30)**: 调用 `validate` 接口或直接插入 `stock_info` 确保股票在库。
4.  **Step 3 (09:30)**: 调用 `monitor` 接口确认监控状态。
5.  **Step 4 (15:05)**: 插入 T 日 `stock_daily` 模拟 K 线数据（构造一个“放量上涨”或“地量”形态以触发规则）。
6.  **Step 5 (15:30)**: 调用 `scores/calculate` 和 `rankings/calculate`。
7.  **Step 6 (17:00)**: 调用 `dashboard` 接口验证结果。
8.  **Report**: 输出每一步的执行结果和最终验证报告。

## 5. 待确认事项
*   后端 API 是否允许跨域调用（已确认为 `localhost` 环境，通常允许）。
*   是否需要 Mock Tushare 接口？（本方案通过直接写库绕过 Tushare 依赖）。
