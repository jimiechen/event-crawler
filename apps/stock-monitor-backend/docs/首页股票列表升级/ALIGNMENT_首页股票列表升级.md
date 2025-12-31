# ALIGNMENT_首页股票列表升级.md

## 1. 项目上下文分析
- **项目**: 同花顺股票监控系统
- **当前状态**: 
  - 首页 (`index.html`) 显示股票列表，包含代码、名称、市场、状态。
  - 数据源为 `/api/v1/dashboard/stocks`。
  - 存在一个测试工具 (`test-tool.html`) 用于检测成交量异动和TDX风险。
- **目标**: 升级首页股票列表，增加更多关键指标，支持排序和筛选。

## 2. 需求理解与确认

### 2.1 新增字段
需要在首页股票列表显示的字段：
1.  **最新价格** (`latest_price`): 股票当前价格。
2.  **250日K线同步状态** (`sync_250d_kline`): 是否已同步近一年数据。
3.  **增量同步开启状态** (`incremental_sync`): 是否开启每日增量同步。
4.  **是否持仓** (`is_held`): 用户是否持有该股。
5.  **是否活跃** (`is_active`): 现有字段，需显式展示。
6.  **成交量异动总分** (`volume_anomaly_score`): 基于成交量异动情况的评分。
    - **来源**: "从测试工具的成交量异动列表统计得出"。
    - **理解**: 需要将测试工具中的异动检测逻辑（如3倍量突破、地量检测）迁移到后端，并量化为分数。
7.  **TDX插件评分** (`tdx_plugin_score`): 通达信风险检测评分。
    - **来源**: 已有的 `StockTdxRisk.total_score`。
8.  **最新评分更新时间** (`score_update_time`): 评分或数据的最后更新时间。
9.  **加分项** (`bonus_items`): 其他加分指标（具体需定义，或预留字段）。

### 2.2 功能增强
1.  **按时间段搜索**: 支持筛选特定时间范围内更新或创建的股票。
2.  **默认排序**: 按「成交量异动总分」从大到小排序。

## 3. 疑问与决策策略

### 3.1 成交量异动总分计算规则
**现状**: 测试工具检测 "3倍量突破" 和 "地量"。
**策略**: 定义一套简单的评分标准：
- 突破3倍量收盘价: +20分
- 突破2倍量收盘价: +10分
- 出现60日地量: +5分
- 出现30日地量: +3分
- (可根据实际情况调整权重)
**决策**: 将在 `StockInfo` 表中新增 `volume_anomaly_score` 字段，并通过定时任务或触发式更新该分数。

### 3.2 数据库变更
需要修改 `stock_info` 表，增加上述缺少的字段。
- `latest_price`: DECIMAL(10, 3) (或者关联查询 `StockData`) -> 建议增加缓存字段以提升列表查询速度。
- `sync_250d_kline`: BOOLEAN
- `incremental_sync`: BOOLEAN
- `is_held`: BOOLEAN
- `volume_anomaly_score`: INTEGER
- `tdx_plugin_score`: INTEGER (关联 `StockTdxRisk` 或冗余存储) -> 建议冗余存储以便排序。
- `score_update_time`: DATETIME
- `bonus_items`: TEXT/JSON

### 3.3 时间段搜索
**策略**: 增加 `start_date` 和 `end_date` 参数，默认过滤 `score_update_time` 或 `updated_at`。考虑到主要是查看最新的异动，过滤 `score_update_time` 最为合理。

## 4. 技术实现方案
1.  **数据库**: 编写 SQL 脚本修改 `stock_info` 表。
2.  **后端**: 
    - 更新 `StockInfo` 模型。
    - 更新 `DashboardService.get_stock_list` 查询逻辑，支持排序和筛选。
    - 实现 `calculate_volume_score` 逻辑（迁移测试工具逻辑）。
3.  **前端**: 
    - 修改 `index.html` 表格列。
    - 增加搜索栏（时间选择器）。
    - 对接新 API 字段。

## 5. 验收标准
1.  首页股票列表包含所有新字段。
2.  列表默认按成交量异动总分降序排列。
3.  可以使用时间范围筛选股票。
4.  显示TDX评分和异动分数。
