# 同花顺股票监控系统 API 文档

## 概述

同花顺股票监控系统提供完整的股票数据采集、存储、监控和查询API服务。本文档详细描述了所有可用的API端点、请求参数和响应格式。

## 基础信息

- **基础URL**: `http://localhost:8000`
- **API版本**: `v1`
- **API前缀**: `/api/v1`
- **内容类型**: `application/json`
- **字符编码**: `UTF-8`

## 通用响应格式

所有API响应都遵循统一的格式：

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 操作是否成功 |
| data | object/array | 响应数据 |
| message | string | 响应消息 |
| timestamp | string | 响应时间戳 |

### 错误响应格式

```json
{
  "error": true,
  "message": "错误描述",
  "code": 400,
  "path": "/api/v1/stocks/info",
  "details": []
}
```

## API 端点

### 1. 健康检查

#### 1.1 基础健康检查

**端点**: `GET /api/v1/health`

**描述**: 检查系统基础健康状态

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

#### 1.2 详细健康检查

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

#### 1.3 数据库健康检查

**端点**: `GET /api/v1/health/database`

**描述**: 检查数据库连接状态

### 2. 股票信息管理

#### 2.1 创建股票信息

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

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 股票代码 |
| name | string | 是 | 股票名称 |
| market | string | 是 | 市场代码(SZ/SH) |
| industry | string | 否 | 行业分类 |
| is_active | boolean | 否 | 是否活跃(默认true) |

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

#### 2.2 获取股票信息

**端点**: `GET /api/v1/stocks/info/{stock_code}`

**描述**: 获取指定股票的基本信息

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| stock_code | string | 股票代码 |

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
  "message": "获取股票信息成功"
}
```

#### 2.3 更新股票信息

**端点**: `PUT /api/v1/stocks/info/{stock_code}`

**描述**: 更新指定股票的基本信息

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| stock_code | string | 股票代码 |

**请求体**:
```json
{
  "name": "平安银行(更新)",
  "industry": "金融服务",
  "is_active": false
}
```

#### 2.4 获取股票列表

**端点**: `GET /api/v1/stocks/info`

**描述**: 获取股票列表，支持分页和过滤

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| market | string | 否 | - | 市场代码过滤 |
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

### 3. 股票数据管理

#### 3.1 提交股票数据

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

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 股票代码 |
| name | string | 是 | 股票名称 |
| current_price | number | 是 | 当前价格 |
| open_price | number | 否 | 开盘价 |
| prev_close | number | 否 | 昨收价 |
| change_amount | number | 否 | 涨跌额 |
| volume | integer | 否 | 成交量 |
| timestamp | string | 否 | 数据时间戳 |

#### 3.2 批量提交股票数据

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

### 4. 监控管理

#### 4.1 添加监控股票

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

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| stock_code | string | 是 | 股票代码 |
| priority | integer | 否 | 优先级(1-10) |
| auto_create_stock | boolean | 否 | 自动创建股票信息 |

#### 4.2 移除监控股票

**端点**: `DELETE /api/v1/monitors/{stock_code}`

**描述**: 从监控列表中移除股票

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| stock_code | string | 股票代码 |

#### 4.3 更新监控设置

**端点**: `PUT /api/v1/monitors/{stock_code}`

**描述**: 更新监控股票的设置

**请求体**:
```json
{
  "priority": 2,
  "is_active": false
}
```

#### 4.4 获取监控列表

**端点**: `GET /api/v1/monitors`

**描述**: 获取监控股票列表

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| active_only | boolean | 否 | true | 仅活跃监控 |
| priority_filter | integer | 否 | - | 优先级过滤 |
| include_stock_info | boolean | 否 | false | 包含股票信息 |
| include_latest_data | boolean | 否 | false | 包含最新数据 |
| limit | integer | 否 | 100 | 每页数量 |
| offset | integer | 否 | 0 | 偏移量 |

#### 4.5 获取监控股票代码列表

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

## 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 422 | 请求参数验证失败 |
| 500 | 服务器内部错误 |

## 错误处理

### 常见错误类型

1. **参数验证错误** (422)
   - 缺少必填参数
   - 参数类型不正确
   - 参数值超出范围

2. **资源不存在** (404)
   - 股票代码不存在
   - 监控记录不存在

3. **业务逻辑错误** (400)
   - 重复添加监控
   - 股票代码格式错误

### 错误响应示例

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
  ]
}
```

## 使用示例

### Python 示例

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

asyncio.run(example())
```

### curl 示例

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

## 注意事项

1. **时间格式**: 所有时间字段使用ISO 8601格式 (YYYY-MM-DDTHH:MM:SSZ)
2. **股票代码**: 支持6位数字格式，如 "000001", "600036"
3. **市场代码**: 支持 "SZ"(深圳) 和 "SH"(上海)
4. **分页**: 建议每页数量不超过1000条记录
5. **并发**: API支持高并发访问，建议合理控制请求频率

## 更新日志

### v1.0.0 (2024-01-15)
- 初始版本发布
- 支持股票信息管理
- 支持股票数据提交
- 支持监控管理
- 支持健康检查