# 定时任务执行备忘录 (Scheduled Task Execution Memo)

## 任务概览 (Task Overview)

| 时间 (Time) | 任务名称 (Task Name) | 函数 (Function) | 描述 (Description) |
| :--- | :--- | :--- | :--- |
| **14:00 - 15:00** | 盘中实时监控检查 | `run_realtime_monitor_check` | 每5分钟执行一次，盘中实时监控预警。 |
| **15:30** | 盘后积分更新 | `run_post_market_update` | **补充数据，计算历史池的数据积分**。<br>1. 调用 Tushare/Akshare 同步基础数据。<br>2. 计算全量股票（含历史池）的评分。 |
| **15:40** | 每日AI复盘 | `run_daily_ai_review` | 在盘后数据更新后，对核心池股票进行AI复盘分析。 |
| **16:00** | 每日验收测试 | `run_daily_acceptance` | 执行每日验收测试脚本，验证系统状态。 |
| **16:30** | 每日问财爬虫 | `run_wencai_daily_crawler` | **只负责爬取新股票**。<br>1. 从 `crawler_targets` 读取启用的爬虫目标。<br>2. 自动替换查询参数（如 `{query_date}`, `{prev_date_str}`）。<br>3. 执行爬取并保存到 `wencai_stocks` 表。 |
| **17:00** | 问财数据同步与评分 | `run_wencai_data_sync` | **补全今天的问财CSV数据，和计算积分量价**。<br>1. 触发 `/api/v1/stock/sync/wencai` 同步新发现股票的 CSV 历史数据。<br>2. 触发 `/api/v1/rankings/calculate` 重新计算当日评分（包含新同步的股票）。 |

## 详细参数说明 (Detailed Parameters)

### 1. 每日问财爬虫 (16:30)
*   **目标源**: 数据库 `crawler_targets` 表。
*   **动态参数支持**:
    *   `{query_date}`: 查询日期 (格式: YYYY年MM月DD日)。
    *   `{prev_date_str}`: 前一交易日 (格式: YYYY年MM月DD日)。
    *   `{date}`: 同 `{query_date}`。
    *   `{prev_date}`: 同 `{prev_date_str}`。
*   **页面维护**:
    *   需在 `crawler_targets` 表中配置 `url` 字段为包含上述占位符的模板字符串。
    *   示例: `{query_date}成交量是{prev_date_str}成交量的2.9倍以上...`

### 2. 问财数据同步与评分 (17:00)
*   **API 1**: `/api/v1/stock/sync/wencai/{today_str}/0`
    *   功能: 扫描 `wencai_stocks` 表中今日新爬取的股票，检查本地 CSV 是否存在/完整，缺失则调用 Tushare/Akshare 补充历史 K 线数据。
*   **API 2**: `/api/v1/rankings/calculate/{today_str}`
    *   功能: 基于最新的 K 线数据（包含刚补充的问财股票），计算量价积分和策略评分。

## 维护记录 (Maintenance Log)
*   **2026-01-16**:
    *   修改 `run_wencai_daily_crawler` 时间为 16:30，并剥离数据同步逻辑。
    *   新增 `run_wencai_data_sync` 任务于 17:00，专门处理数据补全和评分。
    *   更新 `crawler_targets` 支持动态日期参数 `{query_date}` 和 `{prev_date_str}`。
    *   执行历史数据回补 (Backfill): 补全 2025-12-12 至 2026-01-14 期间缺失的问财数据、K线数据及评分。
