# 股票监控系统数据流转与积分计算全流程梳理

## 1. 概述

本文档详细梳理了从外部数据抓取（问财/Tushare）、基础数据入库、异动标签分析、到最终积分计算和排名的完整数据流转过程。特别澄清了“当日积分增长”与“250日总分排名”的区别及计算逻辑。

## 2. 核心概念澄清

| 概念         | 对应字段/表                            | 说明                                              |
| :--------- | :-------------------------------- | :---------------------------------------------- |
| **当日异动分**  | `stock_score_result.total_score`  | 仅代表**当天**触发规则（如3倍量、地量）所获得的积分。用于首页的“今日增长排名”。     |
| **250日总分** | `stock_info.volume_anomaly_score` | 代表该股票在**过去250天**（可配置）内累积的所有当日异动分之和。用于首页的“总分排名”。 |
| **异动记录**   | `volume_analysis_result`          | 记录具体的异动详情（如“2025-12-09 触发3倍量”），用于前端K线图画线。       |
| **当前标签**   | `stock_tag_relation`              | 标记股票当前是否具有某种特征（如“3倍量”），用于快速筛选。                  |

## 3. 数据流转全景图

```HTML
graph TD
    %% 数据源
    SubGraph_Source[数据源]
    Wencai[问财数据] -->|抓取| WencaiStock[wencai_stocks]
    
    %% 多源数据架构
    DataManager[StockDataManager\n(数据管理器)]
    LocalCSV[(本地CSV/DB)] -->|优先读取| DataManager
    Tushare[Tushare接口] -->|1. 主源| DataManager
    Akshare[Akshare接口] -->|2. 备用| DataManager
    Baostock[Baostock接口] -->|3. 兜底| DataManager
    
    DataManager -->|清洗/校验/合并| StockDaily[stock_daily\n(基础日线数据)]

    %% 异动分析服务
    SubGraph_Analysis[异动分析服务 VolumeAnalysisService]
    StockDaily -->|输入: 过去400天数据| AnalyzeStock[analyze_stock\n(核心分析逻辑)]
    
    %% 计算过程
    AnalyzeStock -->|1. 规则匹配| Rules{匹配规则}
    Rules -->|3倍量/2倍量| DailyScore[计算当日得分]
    Rules -->|5/10/20/30/60日地量| DailyScore
    Rules -->|价格双重突破| DailyScore

    %% 结果存储
    DailyScore -->|保存| Table_ScoreResult[stock_score_result\n(每日得分表)]
    Rules -->|异动详情| Table_Anomaly[volume_analysis_result\n(异动记录表)]
    
    %% 总分计算
    Table_ScoreResult -->|聚合: Sum(过去250天)| CalcTotal[计算250日总分]
    CalcTotal -->|更新| Table_StockInfo[stock_info\n(volume_anomaly_score)]

    %% 标签生成 (可选/并行)
    AnalyzeStock -.->|生成当前标签| Table_Tags[stock_tag_relation\n(当前标签表)]
    
    %% 前端展示
    Table_ScoreResult -->|查询当日分| UI_Growth[首页: 积分增长排名]
    Table_StockInfo -->|查询总分| UI_Total[首页: 总分排名]
    Table_Anomaly -->|查询| UI_Chart[K线图: 异动标注]
```

## 4. 详细数据流转步骤

### 4.1 基础数据同步

1. **问财抓取**: 定时任务抓取问财选股结果，存入 `wencai_stocks`。
2. **日线同步**: 系统根据活跃股票列表，通过 Tushare 同步日线数据到 `stock_daily`。这是后续分析的基础。

### 4.2 异动分析与积分计算 (`VolumeAnalysisService.analyze_stock`)

这是系统的核心计算引擎，对单只股票进行全量分析：

1. **加载数据**: 从 `stock_daily` 加载该股票最近 `HISTORY_LOAD_DAYS` (默认400) 天的数据。
2. **每日扫描**: 遍历每一天的数据，进行以下判断：

   * **倍量检查**:

     * `成交量 / 昨日成交量 >= 3.0` -> **3倍量** (+300分)

     * `成交量 / 昨日成交量 >= 2.0` -> **2倍量** (+200分)

   * **地量检查**:

     * 检查是否为过去 60/30/20/10/5 天内的最低量。

     * 触发 60日地量 (+600分) 等。

   * **价格突破**:

     * 收盘价同时突破最近一次3倍量和2倍量的收盘价 -> **价格双重突破**。
3. **结果入库**:

   * **`stock_score_result`**: 插入/更新每一天的得分记录。

     * 字段 `total_score` = 当日各项规则得分之和。

   * **`volume_analysis_result`**: 记录具体的异动点（用于画图）。

   * **`alert_record`** **/** **`rule_calculation_log`**: 记录日志和报警。

### 4.3 总分聚合 (`_save_stock_internal`)

在完成每日异动分析后，系统会立即计算该股票的250日总分：

1. **聚合查询**: `SELECT SUM(total_score) FROM stock_score_result WHERE trade_date >= (Today - 250 days)`
2. **更新总表**: 将计算结果更新到 `stock_info.volume_anomaly_score` 字段。

### 4.4 基准量计算与每日监控

为了支持实时盘中监控和盘后快速筛选，系统维护了一份"基准量"数据。

#### 4.4.1 基准量数据 (`stock_volume_baseline`)

该表记录了每只股票的关键参考指标，由 `VolumeAnalysisService.save_baseline` 维护：

* **最近倍量**: 记录最近一次3倍量/2倍量的日期和收盘价。

  * *用途*: 判断当前价格是否有效突破前期大量位置（压力/支撑互换）。

* **最近地量**: 记录最近一次5/10/20/30/60日地量的日期和成交量。

  * *用途*: 判断今日成交量是否萎缩至极致（变盘信号）。

#### 4.4.2 监控逻辑

每日监控服务 (`MonitorEngine` / `MonitorService`) 执行以下校验流程：

1. **读取基准**: 从 `stock_volume_baseline` 加载目标股票的基准数据。
2. **获取实时/收盘数据**: 从 `stock_daily` (盘后) 或 实时API (盘中) 获取今日数据。
3. **对比触发报警**:

   * **缩量报警**: `今日成交量 <= 基准.60日地量` -> 触发"60日地量"报警。

   * **突破报警**: `今日收盘价 > 基准.3倍量收盘价` (且昨日未突破) -> 触发"突破3倍量"报警。

这一机制实现了离线分析（基准计算）与实时监控的解耦，大幅降低了实时计算的压力。

## 5. 数据库表结构关键字段说明

### 5.1 `stock_score_result` (每日评分表)

| 字段            | 类型      | 说明                          |
| :------------ | :------ | :-------------------------- |
| `code`        | String  | 股票代码                        |
| `trade_date`  | Date    | 交易日期                        |
| `total_score` | Decimal | **当日得分** (例如今天触发3倍量，此处为300) |
| `rule_scores` | JSON    | 规则得分详情 (如 `{"3倍量": 300}`)   |

### 5.2 `stock_info` (股票信息表)

| 字段                     | 类型      | 说明                                              |
| :--------------------- | :------ | :---------------------------------------------- |
| `code`                 | String  | 股票代码                                            |
| `volume_anomaly_score` | Decimal | **250日总分** (基于250天内所有 `stock_score_result` 的累加) |
| `bonus_items`          | JSON    | 最新异动项列表                                         |

### 5.3 `volume_analysis_result` (异动详情表)

| 字段              | 类型      | 说明                      |
| :-------------- | :------ | :---------------------- |
| `analysis_type` | String  | 异动类型 (如 "3倍量", "60日地量") |
| `value`         | Decimal | 触发时的数值 (价格或成交量)         |
| `description`   | String  | 描述文本                    |

## 6. 配置说明

在 `app/services/volume_analysis_service.py` 中可配置以下参数：

```python
class VolumeAnalysisService:
    # Configuration
    SCORE_WINDOW_DAYS = 250  # 总分计算窗口（天），影响 stock_info.volume_anomaly_score
    HISTORY_LOAD_DAYS = 400  # 计算时加载的历史数据天数，确保有足够数据计算250日前的指标
    BASELINE_LOAD_DAYS = 100 # 前端展示/基准加载天数
```

