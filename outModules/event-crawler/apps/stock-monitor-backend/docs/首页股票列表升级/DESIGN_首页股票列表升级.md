# DESIGN_首页股票列表升级.md

## 1. 系统架构
保持现有架构不变，主要在 `StockInfo` 表中增加缓存字段，以提高查询性能。

```mermaid
graph TB
    A[Frontend (index.html)] --> B[API (DashboardController)]
    B --> C[DashboardService]
    C --> D[StockInfo Table]
    C --> E[VolumeAnalysisService]
    E --> D
```

## 2. 数据库设计
修改 `stock_info` 表，新增以下字段：

```sql
ALTER TABLE stock_info 
ADD COLUMN latest_price DECIMAL(10, 3) COMMENT '最新价格',
ADD COLUMN sync_250d_kline BOOLEAN DEFAULT FALSE COMMENT '是否同步250日K线',
ADD COLUMN incremental_sync BOOLEAN DEFAULT FALSE COMMENT '是否开启增量同步',
ADD COLUMN is_held BOOLEAN DEFAULT FALSE COMMENT '是否持仓',
ADD COLUMN volume_anomaly_score INTEGER DEFAULT 0 COMMENT '成交量异动总分',
ADD COLUMN tdx_plugin_score INTEGER DEFAULT 0 COMMENT 'TDX插件评分',
ADD COLUMN score_update_time DATETIME COMMENT '最新评分更新时间',
ADD COLUMN bonus_items TEXT COMMENT '加分项(JSON)';
```

## 3. 接口设计

### 3.1 获取股票列表
`GET /api/v1/dashboard/stocks`

**请求参数更新**:
- `start_date`: 评分更新开始时间 (YYYY-MM-DD)
- `end_date`: 评分更新结束时间 (YYYY-MM-DD)
- `sort_by`: 排序字段 (默认 `volume_anomaly_score`)
- `order`: 排序方向 (默认 `desc`)

**响应数据更新**:
`StockInfoResponse` 增加上述新字段。

## 4. 业务逻辑

### 4.1 评分计算逻辑
需要实现一个评分更新服务，包含以下规则：

**成交量异动总分 (`volume_anomaly_score`)**:
- 基础分: 0
- 突破3倍量收盘价: +20
- 突破2倍量收盘价: +10
- 5日地量: +2
- 10日地量: +3
- 20日地量: +5
- 30日地量: +8
- 60日地量: +10

**TDX评分**:
- 直接同步 `StockTdxRisk.total_score`。

## 5. 前端设计
- 修改 `index.html` 中的表格，增加对应列。
- 增加时间范围选择器。
- 增加“刷新评分”按钮（可选，调用后端触发重算）。
