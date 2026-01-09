# Event-Crawler API接口规范

## 1. 概述

本文档详细描述Event-Crawler系统的所有API接口，包括请求参数、响应格式、错误处理等。所有接口都遵循RESTful设计规范，支持JSON格式数据交换。

**基础URL**: `http://localhost:8000`  
**API版本**: `v1`  
**API前缀**: `/api/v1`  
**内容类型**: `application/json`  
**字符编码**: `UTF-8`

**文档版本**: V1.0  
**最后更新**: 2026-01-08

---

## 2. 通用规范

### 2.1 请求头

```http
Content-Type: application/json
Accept: application/json
User-Agent: Chrome-Extension/1.0.0
```

### 2.2 通用响应格式

#### 成功响应

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 错误响应

```json
{
  "error": true,
  "message": "错误描述",
  "code": 400,
  "path": "/api/v1/stocks/info",
  "details": [],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2.3 HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 422 | 请求参数验证失败 |
| 429 | 请求频率过高 |
| 500 | 服务器内部错误 |

---

## 3. 健康检查接口

### 3.1 基础健康检查

**端点**: `GET /api/v1/health`

**描述**: 检查系统基础健康状态

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0",
    "uptime": 3600.5
  },
  "message": "系统运行正常"
}
```

### 3.2 详细健康检查

**端点**: `GET /api/v1/health/detailed`

**描述**: 检查系统详细健康状态，包含数据库和服务状态

**响应示例**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0",
    "uptime": 3600.5,
    "response_time": 0.025,
    "checks": {
      "database": {
        "status": "healthy",
        "response_time": 0.015
      },
      "stock_service": {
        "status": "healthy",
        "stock_count": 4500
      },
      "monitor_service": {
        "status": "healthy",
        "active_monitors": 100,
        "total_monitors": 150
      }
    }
  },
  "message": "系统状态: healthy"
}
```

### 3.3 数据库健康检查

**端点**: `GET /api/v1/health/database`

**描述**: 检查数据库连接状态

**响应示例**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "connection_time": 0.015,
    "database_version": "8.0.35"
  },
  "message": "数据库连接正常"
}
```

---

## 4. 股票信息管理接口

### 4.1 创建股票信息

**端点**: `POST /api/v1/stocks/info`

**描述**: 创建股票基本信息

**请求体**:
```json
{
  "code": "000001",
  "name": "平安银行",
  "market": "SZ",
  "industry": "银行",
  "is_active": true
}
```

**请求参数**:

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| code | string | 是 | 股票代码(6位数字) | "000001" |
| name | string | 是 | 股票名称 | "平安银行" |
| market | string | 是 | 市场代码(SZ/SH) | "SZ" |
| industry | string | 否 | 行业分类 | "银行" |
| is_active | boolean | 否 | 是否活跃(默认true) | true |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "code": "000001",
    "name": "平安银行",
    "market": "SZ",
    "industry": "银行",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "message": "股票信息创建成功"
}
```

### 4.2 获取股票信息

**端点**: `GET /api/v1/stocks/info/{stock_code}`

**描述**: 获取指定股票的基本信息

**路径参数**:

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| stock_code | string | 股票代码 | "000001" |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "code": "000001",
    "name": "平安银行",
    "market": "SZ",
    "industry": "银行",
    "is_active": true,
    "latest_price": 12.50,
    "volume_anomaly_score": 1500,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "message": "获取股票信息成功"
}
```

### 4.3 更新股票信息

**端点**: `PUT /api/v1/stocks/info/{stock_code}`

**描述**: 更新指定股票的基本信息

**路径参数**:

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| stock_code | string | 股票代码 | "000001" |

**请求体**:
```json
{
  "name": "平安银行(更新)",
  "industry": "金融服务",
  "is_active": false
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "code": "000001",
    "name": "平安银行(更新)",
    "market": "SZ",
    "industry": "金融服务",
    "is_active": false,
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "message": "股票信息更新成功"
}
```

### 4.4 获取股票列表

**端点**: `GET /api/v1/stocks/info`

**描述**: 获取股票列表，支持分页和过滤

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| market | string | 否 | - | 市场代码过滤(SZ/SH) |
| active_only | boolean | 否 | true | 仅活跃股票 |
| limit | integer | 否 | 100 | 每页数量(1-1000) |
| offset | integer | 否 | 0 | 偏移量 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "code": "000001",
        "name": "平安银行",
        "market": "SZ",
        "industry": "银行",
        "is_active": true,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
      }
    ],
    "total": 1,
    "limit": 100,
    "offset": 0,
    "has_more": false
  },
  "message": "获取股票列表成功"
}
```

---

## 5. 股票数据管理接口

### 5.1 提交股票数据

**端点**: `POST /api/v1/stocks/data`

**描述**: 提交单条股票数据

**请求体**:
```json
{
  "code": "000001",
  "name": "平安银行",
  "current_price": 12.50,
  "open_price": 12.30,
  "prev_close": 12.40,
  "change_amount": 0.10,
  "volume": 1000000,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**请求参数**:

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| code | string | 是 | 股票代码 | "000001" |
| name | string | 是 | 股票名称 | "平安银行" |
| current_price | number | 是 | 当前价格 | 12.50 |
| open_price | number | 否 | 开盘价 | 12.30 |
| prev_close | number | 否 | 昨收价 | 12.40 |
| change_amount | number | 否 | 涨跌额 | 0.10 |
| volume | integer | 否 | 成交量 | 1000000 |
| timestamp | string | 否 | 数据时间戳(ISO 8601) | "2024-01-15T10:30:00Z" |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 12345,
    "code": "000001",
    "name": "平安银行",
    "current_price": 12.50,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "message": "股票数据提交成功"
}
```

### 5.2 批量提交股票数据

**端点**: `POST /api/v1/stocks/data/batch`

**描述**: 批量提交股票数据

**请求体**:
```json
{
  "data": [
    {
      "code": "000001",
      "name": "平安银行",
      "current_price": 12.50,
      "open_price": 12.30,
      "prev_close": 12.40,
      "change_amount": 0.10,
      "volume": 1000000,
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "code": "000002",
      "name": "万科A",
      "current_price": 25.68,
      "open_price": 25.50,
      "prev_close": 25.60,
      "change_amount": 0.08,
      "volume": 2000000,
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total": 2,
    "success": 2,
    "failed": 0,
    "errors": [],
    "duplicates": 0
  },
  "message": "批量提交完成"
}
```

---

## 6. 监控管理接口

### 6.1 添加监控股票

**端点**: `POST /api/v1/monitors`

**描述**: 添加股票到监控列表

**请求体**:
```json
{
  "stock_code": "000001",
  "priority": 1,
  "auto_create_stock": false
}
```

**请求参数**:

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| stock_code | string | 是 | 股票代码 | "000001" |
| priority | integer | 否 | 优先级(1-10) | 1 |
| auto_create_stock | boolean | 否 | 自动创建股票信息 | false |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "code": "000001",
    "priority": 1,
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "message": "监控股票添加成功"
}
```

### 6.2 移除监控股票

**端点**: `DELETE /api/v1/monitors/{stock_code}`

**描述**: 从监控列表中移除股票

**路径参数**:

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| stock_code | string | 股票代码 | "000001" |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "code": "000001"
  },
  "message": "监控股票移除成功"
}
```

### 6.3 更新监控设置

**端点**: `PUT /api/v1/monitors/{stock_code}`

**描述**: 更新监控股票的设置

**路径参数**:

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| stock_code | string | 股票代码 | "000001" |

**请求体**:
```json
{
  "priority": 2,
  "is_active": false
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "code": "000001",
    "priority": 2,
    "is_active": false,
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "message": "监控设置更新成功"
}
```

### 6.4 获取监控列表

**端点**: `GET /api/v1/monitors`

**描述**: 获取监控股票列表

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| active_only | boolean | 否 | true | 仅活跃监控 |
| priority_filter | integer | 否 | - | 优先级过滤(1-10) |
| include_stock_info | boolean | 否 | false | 包含股票信息 |
| include_latest_data | boolean | 否 | false | 包含最新数据 |
| limit | integer | 否 | 100 | 每页数量 |
| offset | integer | 否 | 0 | 偏移量 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "code": "000001",
        "priority": 1,
        "is_active": true,
        "stock_info": {
          "name": "平安银行",
          "market": "SZ",
          "industry": "银行"
        },
        "latest_data": {
          "current_price": 12.50,
          "change_amount": 0.10,
          "volume": 1000000
        }
      }
    ],
    "total": 1,
    "limit": 100,
    "offset": 0,
    "has_more": false
  },
  "message": "获取监控列表成功"
}
```

### 6.5 获取监控股票代码列表

**端点**: `GET /api/v1/monitors/codes`

**描述**: 获取监控股票代码列表

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| active_only | boolean | 否 | true | 仅活跃监控 |

**响应示例**:
```json
{
  "success": true,
  "data": ["000001", "000002", "600036"],
  "message": "获取监控股票代码成功，共3只"
}
```

---

## 7. 爬虫控制器接口

### 7.1 SSE实时更新端点

**端点**: `GET /api/v1/crawler/events`

**描述**: SSE实时更新端点，用于推送爬虫状态、股票数据更新等事件

**SSE事件类型**:

| 事件类型 | 说明 | 数据格式 |
|---------|------|---------|
| `crawler_status` | 爬虫状态更新 | `{platform, status, message, data_count, error}` |
| `login_failed` | 登录失败事件 | `{platform, message}` |
| `stock_data_update` | 股票数据更新 | `{code, price, change_percent, volume, ...}` |
| `batch_completed` | 批次完成事件 | `{batch_id, total_records, success_records, failed_records}` |
| `monitor_alert` | 监控告警事件 | `{code, alert_type, message, data}` |

**SSE消息格式**:
```json
{
  "event": "crawler_status",
  "data": "{\"platform\":\"wencai\",\"status\":\"running\",\"message\":\"正在抓取...\",\"data_count\":150}",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 7.2 解析HTML并检查登录状态

**端点**: `POST /api/v1/crawler/parse_html`

**描述**: 解析HTML并检查登录状态

**请求体**:
```json
{
  "platform": "wencai",
  "html": "<html>...</html>",
  "url": "https://www.wencai.com/..."
}
```

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| platform | string | 是 | 平台名称(wencai/tonghuashun) |
| html | string | 是 | HTML内容 |
| url | string | 否 | 页面URL |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "is_logged_in": true,
    "parsed_data": {
      "stocks": [
        {
          "code": "000001",
          "name": "平安银行",
          "price": 12.50
        }
      ]
    }
  },
  "message": "HTML解析成功"
}
```

### 7.3 更新爬虫状态

**端点**: `POST /api/v1/crawler/status`

**描述**: 更新爬虫状态

**请求体**:
```json
{
  "platform": "wencai",
  "status": "running",
  "message": "正在抓取数据",
  "data_count": 150,
  "error": null
}
```

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| platform | string | 是 | 平台名称 |
| status | string | 是 | 状态(running/completed/failed) |
| message | string | 否 | 状态消息 |
| data_count | integer | 否 | 数据数量 |
| error | string | 否 | 错误信息 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "platform": "wencai",
    "status": "running",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "message": "爬虫状态更新成功"
}
```

### 7.4 调试HTML与XPath

**端点**: `POST /api/v1/crawler/debughtml`

**描述**: 调试HTML与XPath

**请求体**:
```json
{
  "platform": "wencai",
  "url": "https://www.wencai.com/...",
  "xpath": "//table[@class='data-table']//tr",
  "html": "<html>...</html>"
}
```

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| platform | string | 是 | 平台名称 |
| url | string | 是 | 页面URL |
| xpath | string | 是 | XPath表达式 |
| html | string | 否 | HTML内容(可选) |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "xpath_result": [
      {
        "code": "000001",
        "name": "平安银行",
        "price": 12.50
      }
    ],
    "match_count": 1
  },
  "message": "XPath调试成功"
}
```

### 7.5 获取调试日志

**端点**: `GET /api/v1/crawler/debug_logs`

**描述**: 获取调试日志

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| platform | string | 否 | - | 平台过滤 |
| limit | integer | 否 | 100 | 日志数量 |
| offset | integer | 否 | 0 | 偏移量 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "id": 1,
        "platform": "wencai",
        "level": "INFO",
        "message": "开始抓取数据",
        "timestamp": "2024-01-15T10:30:00Z"
      }
    ],
    "total": 1
  },
  "message": "获取调试日志成功"
}
```

---

## 8. 问财控制器接口

### 8.1 创建抓取批次

**端点**: `POST /api/v1/wencai/batches`

**描述**: 创建抓取批次

**请求体**:
```json
{
  "batch_name": "2024-01-15 涨幅榜",
  "crawl_url": "https://www.wencai.com/...",
  "query_string": "涨幅>5% 成交量>100万"
}
```

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| batch_name | string | 是 | 批次名称 |
| crawl_url | string | 是 | 抓取URL |
| query_string | string | 是 | 查询条件 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "batch_id": "batch_20240115_001",
    "batch_name": "2024-01-15 涨幅榜",
    "status": "pending",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "message": "抓取批次创建成功"
}
```

### 8.2 获取批次信息

**端点**: `GET /api/v1/wencai/batches/{batch_id}`

**描述**: 获取批次信息

**路径参数**:

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| batch_id | string | 批次ID | "batch_20240115_001" |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "batch_id": "batch_20240115_001",
    "batch_name": "2024-01-15 涨幅榜",
    "status": "completed",
    "started_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:35:00Z",
    "total_records": 150,
    "success_records": 148,
    "failed_records": 2,
    "query_condition": "涨幅>5% 成交量>100万"
  },
  "message": "获取批次信息成功"
}
```

### 8.3 获取批次股票

**端点**: `GET /api/v1/wencai/batches/{batch_id}/stocks`

**描述**: 获取批次股票列表

**路径参数**:

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| batch_id | string | 批次ID | "batch_20240115_001" |

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| limit | integer | 否 | 100 | 每页数量 |
| offset | integer | 否 | 0 | 偏移量 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "stock_code": "000001",
        "stock_name": "平安银行",
        "current_price": 12.50,
        "price_change_percent": 5.2,
        "volume": 1500000
      }
    ],
    "total": 150,
    "limit": 100,
    "offset": 0,
    "has_more": true
  },
  "message": "获取批次股票成功"
}
```

### 8.4 处理批次数据

**端点**: `POST /api/v1/wencai/batches/{batch_id}/process`

**描述**: 处理批次数据

**路径参数**:

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| batch_id | string | 批次ID | "batch_20240115_001" |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "batch_id": "batch_20240115_001",
    "processed_count": 150,
    "created_stocks": 148,
    "updated_stocks": 2
  },
  "message": "批次数据处理完成"
}
```

### 8.5 获取概念统计

**端点**: `GET /api/v1/wencai/concepts`

**描述**: 获取概念统计数据

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| start_date | string | 否 | - | 开始日期(YYYY-MM-DD) |
| end_date | string | 否 | - | 结束日期(YYYY-MM-DD) |
| keyword | string | 否 | - | 关键词过滤 |
| limit | integer | 否 | 100 | 返回数量 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "concepts": [
      {
        "concept_name": "人工智能",
        "stock_count": 50,
        "avg_change_percent": 3.5,
        "top_stocks": ["000001", "000002", "600036"]
      }
    ],
    "total": 100
  },
  "message": "获取概念统计成功"
}
```

### 8.6 隐藏概念

**端点**: `POST /api/v1/wencai/concepts/hide`

**描述**: 隐藏指定概念

**请求体**:
```json
{
  "concept_name": "人工智能"
}
```

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| concept_name | string | 是 | 概念名称 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "concept_name": "人工智能",
    "hidden_at": "2024-01-15T10:30:00Z"
  },
  "message": "概念隐藏成功"
}
```

---

## 9. Cookie管理接口

### 9.1 获取Cookie列表

**端点**: `GET /api/v1/cookies`

**描述**: 获取Cookie列表

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| platform | string | 否 | - | 平台过滤 |
| is_valid | boolean | 否 | - | 是否有效 |
| limit | integer | 否 | 100 | 每页数量 |
| offset | integer | 否 | 0 | 偏移量 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "platform": "wencai",
        "account_name": "user@example.com",
        "is_valid": true,
        "last_tested_at": "2024-01-15T10:30:00Z",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ],
    "total": 1
  },
  "message": "获取Cookie列表成功"
}
```

### 9.2 创建Cookie

**端点**: `POST /api/v1/cookies`

**描述**: 创建Cookie

**请求体**:
```json
{
  "platform": "wencai",
  "account_name": "user@example.com",
  "cookies": [{"name": "session", "value": "..."}],
  "test_url": "https://www.wencai.com/...",
  "xpath_config": {"login_status": "//div[@class='user-info']"}
}
```

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| platform | string | 是 | 平台名称 |
| account_name | string | 是 | 账户名称 |
| cookies | array | 是 | Cookie列表 |
| test_url | string | 否 | 测试URL |
| xpath_config | object | 否 | XPath配置 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "platform": "wencai",
    "account_name": "user@example.com",
    "is_valid": true,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "message": "Cookie创建成功"
}
```

### 9.3 更新Cookie

**端点**: `PUT /api/v1/cookies/{cookie_id}`

**描述**: 更新Cookie

**路径参数**:

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| cookie_id | integer | Cookie ID | 1 |

**请求体**:
```json
{
  "is_valid": false,
  "test_url": "https://www.wencai.com/...",
  "xpath_config": {"login_status": "//div[@class='user-info']"}
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "is_valid": false,
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "message": "Cookie更新成功"
}
```

### 9.4 删除Cookie

**端点**: `DELETE /api/v1/cookies/{cookie_id}`

**描述**: 删除Cookie

**路径参数**:

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| cookie_id | integer | Cookie ID | 1 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1
  },
  "message": "Cookie删除成功"
}
```

### 9.5 测试Cookie

**端点**: `POST /api/v1/cookies/{cookie_id}/test`

**描述**: 测试Cookie有效性

**路径参数**:

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| cookie_id | integer | Cookie ID | 1 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "is_valid": true,
    "test_result": {
      "status": "success",
      "response_time": 0.5
    },
    "tested_at": "2024-01-15T10:30:00Z"
  },
  "message": "Cookie测试成功"
}
```

---

## 10. 定时任务接口

### 10.1 获取定时任务列表

**端点**: `GET /api/v1/timed-tasks`

**描述**: 获取定时任务列表

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| status | string | 否 | - | 状态过滤(active/inactive) |
| task_type | string | 否 | - | 任务类型过滤 |
| limit | integer | 否 | 100 | 每页数量 |
| offset | integer | 否 | 0 | 偏移量 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "同步股票数据",
        "task_type": "sync_stock_data",
        "cron_expression": "0 15 * * *",
        "is_active": true,
        "last_run_at": "2024-01-15T15:30:00Z",
        "next_run_at": "2024-01-16T15:30:00Z"
      }
    ],
    "total": 1
  },
  "message": "获取定时任务列表成功"
}
```

### 10.2 创建定时任务

**端点**: `POST /api/v1/timed-tasks`

**描述**: 创建定时任务

**请求体**:
```json
{
  "name": "同步股票数据",
  "task_type": "sync_stock_data",
  "cron_expression": "0 15 * * *",
  "parameters": {
    "codes": ["000001", "000002"]
  }
}
```

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 任务名称 |
| task_type | string | 是 | 任务类型 |
| cron_expression | string | 是 | Cron表达式 |
| parameters | object | 否 | 任务参数 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "同步股票数据",
    "task_type": "sync_stock_data",
    "cron_expression": "0 15 * * *",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "message": "定时任务创建成功"
}
```

### 10.3 更新定时任务

**端点**: `PUT /api/v1/timed-tasks/{task_id}`

**描述**: 更新定时任务

**路径参数**:

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| task_id | integer | 任务ID | 1 |

**请求体**:
```json
{
  "name": "同步股票数据(更新)",
  "cron_expression": "0 16 * * *",
  "parameters": {
    "codes": ["000001", "000002", "600036"]
  },
  "is_active": false
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "同步股票数据(更新)",
    "cron_expression": "0 16 * * *",
    "is_active": false,
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "message": "定时任务更新成功"
}
```

### 10.4 删除定时任务

**端点**: `DELETE /api/v1/timed-tasks/{task_id}`

**描述**: 删除定时任务

**路径参数**:

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| task_id | integer | 任务ID | 1 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1
  },
  "message": "定时任务删除成功"
}
```

### 10.5 手动执行任务

**端点**: `POST /api/v1/timed-tasks/{task_id}/run`

**描述**: 手动执行任务

**路径参数**:

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| task_id | integer | 任务ID | 1 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "task_id": 1,
    "execution_id": "exec_20240115_001",
    "status": "running",
    "started_at": "2024-01-15T10:30:00Z"
  },
  "message": "任务已开始执行"
}
```

---

## 11. 错误处理

### 11.1 常见错误类型

#### 11.1.1 参数验证错误 (422)

**示例**:
```json
{
  "error": true,
  "message": "请求参数验证失败",
  "code": 422,
  "path": "/api/v1/stocks/info",
  "details": [
    {
      "loc": ["body", "code"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 11.1.2 资源不存在 (404)

**示例**:
```json
{
  "error": true,
  "message": "股票代码不存在",
  "code": 404,
  "path": "/api/v1/stocks/info/999999",
  "details": [],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 11.1.3 业务逻辑错误 (400)

**示例**:
```json
{
  "error": true,
  "message": "重复添加监控",
  "code": 400,
  "path": "/api/v1/monitors",
  "details": [
    {
      "field": "stock_code",
      "message": "该股票已在监控列表中"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 11.2 错误码列表

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 422 | 请求参数验证失败 |
| 429 | 请求频率过高 |
| 500 | 服务器内部错误 |

---

## 12. 使用示例

### 12.1 Python示例

```python
import httpx
import asyncio

async def example():
    async with httpx.AsyncClient() as client:
        # 健康检查
        response = await client.get("http://localhost:8000/api/v1/health")
        print(response.json())
        
        # 创建股票信息
        stock_data = {
            "code": "000001",
            "name": "平安银行",
            "market": "SZ",
            "industry": "银行"
        }
        response = await client.post(
            "http://localhost:8000/api/v1/stocks/info",
            json=stock_data
        )
        print(response.json())
        
        # 获取股票信息
        response = await client.get("http://localhost:8000/api/v1/stocks/info/000001")
        print(response.json())

asyncio.run(example())
```

### 12.2 JavaScript示例

```javascript
// 健康检查
async function healthCheck() {
  const response = await fetch('http://localhost:8000/api/v1/health');
  const data = await response.json();
  console.log(data);
}

// 创建股票信息
async function createStockInfo() {
  const stockData = {
    code: "000001",
    name: "平安银行",
    market: "SZ",
    industry: "银行"
  };
  
  const response = await fetch('http://localhost:8000/api/v1/stocks/info', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(stockData)
  });
  
  const data = await response.json();
  console.log(data);
}

// 获取股票信息
async function getStockInfo(code) {
  const response = await fetch(`http://localhost:8000/api/v1/stocks/info/${code}`);
  const data = await response.json();
  console.log(data);
}

// 执行示例
healthCheck();
createStockInfo();
getStockInfo('000001');
```

### 12.3 curl示例

```bash
# 健康检查
curl -X GET "http://localhost:8000/api/v1/health"

# 创建股票信息
curl -X POST "http://localhost:8000/api/v1/stocks/info" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "000001",
    "name": "平安银行",
    "market": "SZ",
    "industry": "银行"
  }'

# 获取股票信息
curl -X GET "http://localhost:8000/api/v1/stocks/info/000001"

# 添加监控
curl -X POST "http://localhost:8000/api/v1/monitors" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001",
    "priority": 1
  }'
```

---

## 13. 总结

本文档详细描述了Event-Crawler系统的所有API接口，包括：

1. **健康检查接口**: 系统健康状态检查
2. **股票信息管理接口**: 股票信息的CRUD操作
3. **股票数据管理接口**: 股票数据的提交和查询
4. **监控管理接口**: 监控列表的管理
5. **爬虫控制器接口**: 爬虫状态和调试
6. **问财控制器接口**: 问财数据抓取和管理
7. **Cookie管理接口**: Cookie的CRUD操作
8. **定时任务接口**: 定时任务的管理

所有接口都遵循统一的请求/响应格式，包含完善的错误处理机制，支持数据校验、分页、过滤等功能。

---

**文档维护**: 本文档应随着API接口的演进而持续更新，确保与实际接口保持一致。
