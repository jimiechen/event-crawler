# Stock Monitor Backend API Documentation

本文档详细描述了 Stock Monitor Backend 服务的 API 接口。

**Base URL**: `/api/v1` (大部分接口)
**Host**: `localhost:8000` (默认)

## 1. 网络数据接口 (Network Data)
**核心功能**: 接收和管理来自 Chrome 扩展的网络抓包数据（如问财、同花顺的数据）。
**Controller**: `network_controller.py`
**File Path**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/network_controller.py`

### 1.1 接收网络数据
- **URL**: `/api/v1/network/data`
- **Method**: `POST`
- **说明**: 接收 Chrome 扩展推送的网络数据包。
- **Request Body** (`NetworkDataCreate`):
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `url` | string | 是 | 请求的完整 URL |
  | `method` | string | 是 | HTTP 方法 (GET/POST) |
  | `headers` | dict | 否 | 请求头 |
  | `payload` | string/dict | 否 | 请求体数据 |
  | `response` | string/dict | 否 | 响应体数据 |
  | `source` | string | 是 | 数据来源 (如: wencai, tonghuashun) |
  | `timestamp` | datetime | 否 | 时间戳 |

### 1.2 获取网络数据列表
- **URL**: `/api/v1/network/data`
- **Method**: `GET`
- **Query Parameters**:
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `url_pattern` | string | 否 | URL 模糊匹配 |
  | `source` | string | 否 | 来源过滤 |
  | `start_time` | datetime | 否 | 开始时间 |
  | `end_time` | datetime | 否 | 结束时间 |
  | `page` | int | 否 | 页码 (默认 1) |
  | `page_size` | int | 否 | 每页数量 (默认 20) |

### 1.3 获取单条网络数据
- **URL**: `/api/v1/network/data/{data_id}`
- **Method**: `GET`
- **Path Parameters**:
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `data_id` | int | 是 | 数据 ID |

### 1.4 清理网络数据
- **URL**: `/api/v1/network/data/clear`
- **Method**: `DELETE`
- **Query Parameters**:
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `before_days` | int | 否 | 清理几天前的数据 (默认 7) |
  | `source` | string | 否 | 指定来源 |

---

## 2. 股票数据接口 (Stock Data)
**核心功能**: 管理股票基本信息、K线数据、风险数据。
**Controller**: `stock_controller.py`
**File Path**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/stock_controller.py`

### 2.1 获取股票列表
- **URL**: `/api/v1/stocks/info`
- **Method**: `GET`
- **Query Parameters**:
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `market` | string | 否 | 市场代码 (SH/SZ/BJ) |
  | `active_only` | bool | 否 | 仅活跃股票 (默认 True) |
  | `limit` | int | 否 | 限制数量 |
  | `offset` | int | 否 | 偏移量 |

### 2.2 获取股票信息
- **URL**: `/api/v1/stocks/info/{stock_code}`
- **Method**: `GET`

### 2.3 获取股票风险数据 (TDX)
- **URL**: `/api/v1/stocks/{code}/risk`
- **Method**: `GET`
- **说明**: 获取通达信风险提示数据。

### 2.4 提交股票数据 (单条)
- **URL**: `/api/v1/stocks/data`
- **Method**: `POST`
- **Request Body** (`StockDataCreate`):
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `stock_code` | string | 是 | 股票代码 |
  | `trade_date` | date | 是 | 交易日期 |
  | `open` | float | 是 | 开盘价 |
  | `close` | float | 是 | 收盘价 |
  | `high` | float | 是 | 最高价 |
  | `low` | float | 是 | 最低价 |
  | `volume` | float | 是 | 成交量 |
  | `amount` | float | 否 | 成交额 |

### 2.5 批量提交股票数据
- **URL**: `/api/v1/stocks/data/batch`
- **Method**: `POST`

---

## 3. 监控管理接口 (Monitor Management)
**核心功能**: 管理股票监控列表、优先级、告警。
**Controller**: `monitor_controller.py`
**File Path**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/monitor_controller.py`

### 3.1 获取监控列表
- **URL**: `/api/v1/monitors`
- **Method**: `GET`
- **Query Parameters**:
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `active_only` | bool | 否 | 仅活跃 (默认 True) |
  | `priority_filter` | int | 否 | 优先级过滤 |
  | `stock_code` | string | 否 | 股票代码过滤 |
  | `include_latest_data` | bool | 否 | 包含最新行情数据 |

### 3.2 添加监控股票
- **URL**: `/api/v1/monitors`
- **Method**: `POST`
- **Request Body** (`MonitorCreate`):
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `stock_code` | string | 是 | 股票代码 |
  | `priority` | int | 否 | 优先级 (1-10) |
  | `auto_create_stock` | bool | 否 | 自动创建股票信息 |

### 3.3 移除监控股票
- **URL**: `/api/v1/monitors/{stock_code}`
- **Method**: `DELETE`

### 3.4 获取监控告警
- **URL**: `/api/v1/monitors/alerts`
- **Method**: `GET`
- **Query Parameters**:
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `hours` | int | 否 | 过去几小时 (默认 24) |

---

## 4. 问财数据接口 (Wencai Data)
**核心功能**: 问财数据解析、概念云图、抓取批次管理。
**Controller**: `wencai_controller.py`
**File Path**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/wencai_controller.py`

### 4.1 解析并保存问财 HTML
- **URL**: `/api/v1/wencai/parse`
- **Method**: `POST`
- **Request Body** (`WencaiParseRequest`):
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `html_content` | string | 是 | 完整的 HTML 源码 |
  | `crawl_url` | string | 否 | 来源 URL |
  | `batch_name` | string | 否 | 批次名称 |
  | `query_string` | string | 否 | 查询语句 |

### 4.2 获取概念云图
- **URL**: `/api/v1/wencai/concepts`
- **Method**: `GET`
- **Query Parameters**:
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `startDate` | string | 否 | 开始日期 (YYYY-MM-DD) |
  | `keyword` | string | 否 | 搜索关键词 |

---

## 5. 测试工具接口 (Test Tool)
**核心功能**: 用于开发调试、数据模拟、环境检查。
**Controller**: `test_tool_controller.py`
**File Path**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/test_tool_controller.py`

### 5.1 添加自定义股票 (支持批量)
- **URL**: `/api/v1/test-tool/add-custom-stock`
- **Method**: `POST`
- **Request Body** (`AddCustomStockRequest`):
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `code` | string | 是 | 股票代码 (支持逗号分隔批量) |
  | `label` | string | 否 | 标签/名称 |
  | `days` | int | 否 | 获取K线天数 (默认 250) |
  | `custom_date` | string | 否 | 自定义日期 |
  | `platform` | string | 否 | 指定数据源 (tushare/baostock/akshare) |

### 5.2 设置首选数据源
- **URL**: `/api/v1/test-tool/set-platform`
- **Method**: `POST`
- **Request Body**: `{"platform": "tushare"}`

---

## 6. 仪表盘接口 (Dashboard)
**核心功能**: 提供前端首页所需的数据聚合。
**Controller**: `dashboard_controller.py`
**File Path**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/dashboard_controller.py`

### 6.1 获取统计概览
- **URL**: `/api/v1/dashboard/stats`
- **Method**: `GET`

### 6.2 获取股票列表 (Tab1)
- **URL**: `/api/v1/dashboard/stocks`
- **Method**: `GET`
- **Query Parameters**:
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `sort_by` | string | 否 | 排序字段 (如 volume_anomaly_score) |
  | `active_only` | bool | 否 | 仅活跃 |

### 6.3 获取股票额外信息 (Sparkline, TDX)
- **URL**: `/api/v1/dashboard/stocks/extra`
- **Method**: `GET`
- **Query Parameters**: `code`

---

## 7. 爬虫与自动化接口 (Crawler & Automation)
**核心功能**: 管理爬虫任务、自动化测试、Cookie。
**Controllers**: 
- `crawler_controller.py`: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/crawler_controller.py`
- `automation_controller.py`: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/automation_controller.py`
- `cookie_controller.py`: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/cookie_controller.py`

### 7.1 Crawler SSE Events
- **URL**: `/api/v1/crawler/events`
- **Method**: `GET`
- **说明**: Server-Sent Events 接口，用于实时推送爬虫状态。

### 7.2 解析 HTML (通用)
- **URL**: `/api/v1/crawler/parse_html`
- **Method**: `POST`

### 7.3 创建自动化任务
- **URL**: `/api/v1/automation/task/create`
- **Method**: `POST`

### 7.4 Cookie 管理
- **URL**: `/api/v1/cookies`
- **Method**: `GET` / `POST`

---

## 8. 调试与分析接口 (Debug & Analysis)
**核心功能**: 调试量价逻辑、查看分析日志、形态筛选。
**Controllers**:
- `debug_controller.py`
- `analysis_controller.py`
- `pattern_analysis_controller.py`

### 8.1 触发模拟场景 (调试)
- **URL**: `/api/v1/debug/trigger`
- **Method**: `POST`
- **说明**: 模拟特定行情 (如3倍放量) 以测试策略逻辑。

### 8.2 获取量价分析日志
- **URL**: `/api/v1/analysis/logs/{code}`
- **Method**: `GET`

### 8.3 形态筛选
- **URL**: `/api/pattern/screen`
- **Method**: `POST`

---

## 9. 健康检查 (Health Check)
**Controller**: `health_controller.py`

- **URL**: `/api/v1/health`
- **Method**: `GET`
- **Response**: `{"status": "healthy", ...}`

- **URL**: `/api/v1/health/detailed`
- **Method**: `GET`
- **说明**: 检查数据库连接、服务状态等详细信息。

---

## 10. ADB Android 接口
**Controller**: `adb_controller.py`
**File Path**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/adb_controller.py`

### 10.1 设备健康上报
- **URL**: `/api/v1/adb/health`
- **Method**: `POST`

### 10.2 SSE 命令通道
- **URL**: `/api/v1/adb/events`
- **Method**: `GET`

---

## 11. 自选股接口 (Favorites)
**核心功能**: 管理自选股，同步问财选股结果。
**Controller**: `favorites_controller.py`
**File Path**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/favorites_controller.py`

### 11.1 同步问财选股
- **URL**: `/api/v1/favorites/sync-from-wencai`
- **Method**: `POST`
- **Query Parameters**:
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `batch_id` | int | 否 | 问财批次ID |
  | `default_priority` | int | 否 | 默认优先级 (1-10) |

---

## 12. K线形态分析 (Morphology)
**核心功能**: K线形态识别（如三日K线组合）。
**Controller**: `morphology_controller.py`
**File Path**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/morphology_controller.py`

### 12.1 分析形态
- **URL**: `/api/morphology/analyze/{code}`
- **Method**: `POST`
- **Query Parameters**:
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `days` | int | 否 | 分析天数 (默认 120) |

---

## 13. 股票排名接口 (Rankings)
**核心功能**: 获取股票得分排名（增长榜、总分榜）。
**Controller**: `ranking_controller.py`
**File Path**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/ranking_controller.py`

### 13.1 获取增长排名
- **URL**: `/api/v1/rankings/growth`
- **Method**: `GET`
- **Query Parameters**:
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `start_date` | date | 是 | 开始日期 |
  | `end_date` | date | 是 | 结束日期 |
  | `limit` | int | 否 | 限制数量 (默认 10) |

### 13.2 获取总分排名
- **URL**: `/api/v1/rankings/total`
- **Method**: `GET`
- **Query Parameters**:
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `target_date` | date | 否 | 目标日期 |
  | `limit` | int | 否 | 限制数量 (默认 10) |

---

## 14. 股票日线接口 (Stock Daily)
**核心功能**: 股票日线数据查询与管理。
**Controller**: `stock_daily_controller.py`
**File Path**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/stock_daily_controller.py`

### 14.1 分页查询日线数据
- **URL**: `/api/stock/daily/search`
- **Method**: `GET`
- **Query Parameters**:
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `page` | int | 否 | 页码 |
  | `code` | string | 否 | 股票代码 |
  | `start_date` | date | 否 | 开始日期 |
  | `end_date` | date | 否 | 结束日期 |

### 14.2 获取单只股票日线
- **URL**: `/api/stock/daily/{code}`
- **Method**: `GET`
- **Query Parameters**:
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `days` | int | 否 | 最近N天 |
  | `start_date` | date | 否 | 开始日期 |
  | `end_date` | date | 否 | 结束日期 |

### 14.3 获取任务日志
- **URL**: `/api/stock/daily/logs`
- **Method**: `GET`

---

## 15. 评分结果接口 (Scores)
**核心功能**: 查询股票评分结果。
**Controller**: `stock_score_controller.py`
**File Path**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/stock_score_controller.py`

### 15.1 查询评分结果列表
- **URL**: `/api/v1/scores/latest`
- **Method**: `GET`
- **Query Parameters**:
  | 参数名 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `trade_date` | date | 否 | 交易日期 |
  | `code` | string | 否 | 股票代码 |
  | `min_score` | float | 否 | 最低分 |

### 15.2 查询历史评分
- **URL**: `/api/v1/scores/history/{code}`
- **Method**: `GET`

---

## 16. 数据同步接口 (Stock Sync)
**核心功能**: CSV导入、Tushare数据同步。
**Controller**: `stock_sync_controller.py`
**File Path**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/stock_sync_controller.py`

### 16.1 CSV 同步
- **URL**: `/api/v1/stock/sync/csv`
- **Method**: `POST`
- **Request Body**: `CsvSyncRequest` (batch_id, days, end_date, stock_codes)

### 16.2 Tushare 同步
- **URL**: `/api/v1/stock/sync/tushare`
- **Method**: `POST`
- **Request Body**: `TushareSyncRequest` (batch_id, start_date, stock_codes)

### 16.3 单只股票同步
- **URL**: `/api/v1/stock/sync/csv/{stock_code}`
- **URL**: `/api/v1/stock/sync/tushare/{stock_code}`
- **Method**: `GET`

### 16.4 获取同步日志
- **URL**: `/api/v1/stock/sync/logs`
- **Method**: `GET`

---

## 17. 系统接口 (System)
**核心功能**: 系统级操作，如桌面通知。
**Controller**: `system_controller.py`
**File Path**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/system_controller.py`

### 17.1 发送桌面通知 (macOS)
- **URL**: `/notify`
- **Method**: `POST`
- **Request Body**: `{"title": "...", "message": "..."}`

---

## 18. 标签管理接口 (Tags)
**核心功能**: 股票标签管理、关联。
**Controller**: `tag_controller.py`
**File Path**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/tag_controller.py`

### 18.1 获取标签列表
- **URL**: `/api/v1/tags`
- **Method**: `GET`

### 18.2 创建标签
- **URL**: `/api/v1/tags`
- **Method**: `POST`
- **Request Body**: `TagCreate`

### 18.3 关联股票
- **URL**: `/api/v1/tags/{tag_id}/stocks`
- **Method**: `POST`
- **Request Body**: `StockRelationCreate`

### 18.4 获取股票的标签
- **URL**: `/api/v1/tags/stocks/{stock_code}`
- **Method**: `GET`

---

## 19. 定时任务接口 (Timed Task)
**核心功能**: 任务调度、执行器控制、批量任务创建。
**Controller**: `timed_task_controller.py`
**File Path**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/timed_task_controller.py`

### 19.1 WebSocket 连接
- **URL**: `/api/v1/timed-task/ws`
- **Method**: `WebSocket`

### 19.2 执行器控制
- **URL**: `/api/v1/timed-task/executor/start`
- **URL**: `/api/v1/timed-task/executor/stop`
- **Method**: `POST`

### 19.3 批量创建任务
- **URL**: `/api/v1/timed-task/batch-create`
- **Method**: `POST`
- **Request Body**: `{"task_type": "csv_sync"}`

### 19.4 获取执行日志
- **URL**: `/api/v1/timed-task/execution-logs`
- **Method**: `GET`

### 19.5 调度任务管理
- **URL**: `/api/v1/timed-task/scheduled/list`
- **Method**: `GET`
- **URL**: `/api/v1/timed-task/scheduled/update`
- **Method**: `POST`
- **URL**: `/api/v1/timed-task/scheduled/run/{task_id}`
- **Method**: `POST`

---

## 20. 交易规则接口 (Trading Rules)
**核心功能**: 量价分析、规则匹配日志。
**Controller**: `trading_rules_controller.py`
**File Path**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/trading_rules_controller.py`

### 20.1 分析股票
- **URL**: `/api/trading-rules/analyze/{code}`
- **Method**: `POST`

### 20.2 获取分析日志
- **URL**: `/api/trading-rules/logs/{code}`
- **Method**: `GET`

---

## 21. 成交量异动分析 (Volume Analysis)
**核心功能**: 成交量基准、异动检测。
**Controller**: `volume_analysis_controller.py`
**File Path**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend/app/api/volume_analysis_controller.py`

### 21.1 获取基准列表
- **URL**: `/api/v1/volume-analysis/baselines`
- **Method**: `GET`

### 21.2 触发分析 (单只)
- **URL**: `/api/v1/volume-analysis/run/{code}`
- **Method**: `GET`

### 21.3 批量触发分析
- **URL**: `/api/v1/volume-analysis/batch-run`
- **Method**: `POST`
