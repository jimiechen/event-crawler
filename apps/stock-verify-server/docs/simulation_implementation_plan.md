# 603601 验收模拟实施方案

## 1. 概述
本方案旨在通过 `stock-verify-server` 搭建可视化模拟环境，重现 `report_603601.md` 中的关键数据节点（2025-11-19 和 2025-11-20），验证系统在不同时间点的数据状态、排名逻辑及前端展示的一致性。

## 2. 操作界面
在 `stock-verify-server` 前端 (http://localhost:8001) 增加控制面板，包含以下三个核心按钮：

1.  **🔴 清空数据 (Reset Data)**
2.  **1️⃣ 执行 Step 1 (2025-11-19)**
3.  **2️⃣ 执行 Step 2 (2025-11-20)**

## 3. 详细执行逻辑

### 3.1 🔴 清空数据 (Reset Data)
**目标**: 将数据库重置为“白板”状态，仅保留必要的配置数据。

**执行动作**:
调用后端接口 `/api/simulation/reset`，执行以下 SQL 清理操作：
```sql
TRUNCATE TABLE wencai_stocks;
TRUNCATE TABLE monitor_list;
TRUNCATE TABLE stock_info;
TRUNCATE TABLE stock_daily;
TRUNCATE TABLE stock_daily_temp;
TRUNCATE TABLE stock_volume_baseline;
TRUNCATE TABLE volume_analysis_results;
TRUNCATE TABLE alert_records;
TRUNCATE TABLE wencai_data_dedup;
TRUNCATE TABLE stock_concepts;
TRUNCATE TABLE wencai_crawl_batches;
TRUNCATE TABLE stock_score_results; -- 确保清空评分表
-- 注意：保留 stock_tags_info (标签积分规则表)
```

### 3.2 1️⃣ 执行 Step 1 (2025-11-19)
**场景**: 首次运行，603601 上榜，计算基础分。

**执行动作**:
调用后端接口 `/api/simulation/step1`：
1.  **问财数据入库**:
    *   插入 `603601` (百利电气) 到 `wencai_stocks`。
    *   `trade_date` 设置为 `2025-11-19`。
2.  **模拟评分计算**:
    *   直接写入 `stock_score_results` 表，确保数据精确匹配报告：
        *   **Code**: `603601`
        *   **Date**: `2025-11-19`
        *   **Daily Score**: `50.00`
        *   **Total Score**: `37800.00` (模拟已包含 250 天基础分)
        *   **Rank**: `1`
        *   **Pool Type**: `wencai`

**预期结果验证**:
*   Dashboard 日期控件仅显示 `2025-11-19`。
*   列表仅展示 1 条数据 (603601)。
*   总分显示 `37800`，排名 `1`。

### 3.3 2️⃣ 执行 Step 2 (2025-11-20)
**场景**: 第二天，问财池扩容至 12 只股票，重新计算排名。

**执行动作**:
调用后端接口 `/api/simulation/step2`：
1.  **问财数据扩容**:
    *   新增 11 只模拟股票 (e.g., `000001` - `000011`) 到 `wencai_stocks`。
    *   `trade_date` 设置为 `2025-11-20`。
2.  **模拟评分计算 (2025-11-20)**:
    *   **其他 11 只股票**:
        *   插入 `stock_score_results`，设置 `total_score` > `37800` (例如 `40000` - `50000`)。
        *   确保它们占据排名 1-11 位。
    *   **603601**:
        *   插入 `stock_score_results`:
            *   **Date**: `2025-11-20`
            *   **Daily Score**: `0.00` (无涨停)
            *   **Total Score**: `37800.00` (维持不变)
            *   **Rank**: `12` (跌至最后)
3.  **数据同步**:
    *   确保所有 12 只股票都在 `stock_info` 和 `stock_daily` (模拟当日 K 线) 中有记录，以保证前端能正常查询。

**预期结果验证**:
*   Dashboard 日期控件增加 `2025-11-20`。
*   切换到 `2025-11-20` 时：
    *   列表展示 12 条数据。
    *   603601 排名 `12`，分数 `37800`。
    *   其他 11 只股票排名 1-11。

## 4. 开发计划
1.  **Backend**:
    *   修改 `apps/stock-verify-server/app/services/cleaner.py` 完善清理逻辑。
    *   创建 `apps/stock-verify-server/app/services/simulator.py` 实现 Step1/Step2 的数据注入逻辑。
    *   更新 `apps/stock-verify-server/app/api/endpoints.py` 暴露控制接口。
2.  **Frontend**:
    *   修改 `apps/stock-verify-server/static/index.html` 添加控制按钮和日志面板。
