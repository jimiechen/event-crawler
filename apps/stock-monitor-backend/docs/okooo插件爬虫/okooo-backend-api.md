# 澳客竞彩数据系统 - 后端API文档

## 1. API概述

后端服务基于FastAPI框架构建，提供RESTful API接口，支持比赛数据抓取、解析、管理和实时监控。

**基础URL**: `http://localhost:8000/api/v1/okooo`

**响应格式**: JSON

**认证方式**: 无（本地开发环境）

## 2. 爬虫API

### 2.1 启动爬虫

```http
POST /crawl
```

启动比赛数据爬虫。

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| date | string | 否 | 日期 (YYYY-MM-DD)，默认当天 |
| force | boolean | 否 | 是否强制重新抓取 |

**请求示例**:

```json
{
  "date": "2026-02-12",
  "force": false
}
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "task_id": "task_123456",
    "date": "2026-02-12",
    "match_count": 30,
    "status": "started"
  },
  "message": "爬虫任务已启动"
}
```

### 2.2 停止爬虫

```http
POST /crawl/stop
```

停止正在运行的爬虫任务。

**响应示例**:

```json
{
  "success": true,
  "message": "爬虫已停止"
}
```

### 2.3 获取爬虫状态

```http
GET /crawl/status
```

获取当前爬虫状态。

**响应示例**:

```json
{
  "success": true,
  "data": {
    "is_running": true,
    "phase": "crawling",
    "progress": {
      "current": 15,
      "total": 30
    },
    "current_match": "1311642"
  }
}
```

## 3. 修复API

### 3.1 检查并修复

```http
POST /repair
```

检查文件完整性并生成修复任务。

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| date | string | 否 | 日期 (YYYY-MM-DD)，默认当天 |
| dry_run | boolean | 否 | 是否仅检查不修复，默认false |

**请求示例**:

```json
{
  "date": "2026-02-12",
  "dry_run": true
}
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "date": "2026-02-12",
    "total_checked": 30,
    "repairing_count": 5,
    "ids": ["1311642", "1311643", "1307953"],
    "repair_details": [
      {
        "id": "1311642",
        "reason": "目录缺失",
        "missing_files": ["history", "odds", "handicap"]
      }
    ]
  },
  "message": "发现 5 个比赛需要修复"
}
```

### 3.2 获取修复任务

```http
GET /repair-tasks
```

获取待修复的任务列表。

**响应示例**:

```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "match_id": "1311642",
        "page_type": "历史",
        "url": "https://m.okooo.com/match/history.php?MatchID=1311642",
        "filename_prefix": "history",
        "date": "2026-02-12"
      }
    ],
    "total": 8
  }
}
```

## 4. 文件API

### 4.1 保存比赛HTML

```http
POST /save-match-html
```

保存比赛详情页面HTML。

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| html | string | 是 | 页面HTML内容 |
| url | string | 是 | 页面URL |
| match_id | string | 是 | 比赛ID |
| page_type | string | 是 | 页面类型 |
| filename_prefix | string | 否 | 文件名前缀 |
| captured_at | string | 是 | 捕获时间 |
| date | string | 是 | 日期 |

**请求示例**:

```json
{
  "html": "<!DOCTYPE html>...",
  "url": "https://m.okooo.com/match/history.php?MatchID=1311642",
  "match_id": "1311642",
  "page_type": "历史",
  "filename_prefix": "history",
  "captured_at": "2026-02-12T10:30:00Z",
  "date": "2026-02-12"
}
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "save_path": "/data/okooo/matches/2026-02-12/1311642/history_1311642.html",
    "file_size": 15234
  },
  "message": "保存成功"
}
```

### 4.2 保存历史战绩HTML

```http
POST /save-history-html
```

保存历史战绩页面HTML。

**请求参数**: 同 `/save-match-html`

### 4.3 保存亚盘数据HTML

```http
POST /save-handicap-html
```

保存亚盘数据页面HTML。

**请求参数**: 同 `/save-match-html`

### 4.4 检查文件是否存在

```http
POST /check-files-exist
```

批量检查文件是否存在。

**请求参数**:

```json
{
  "tasks": [
    {
      "match_id": "1311642",
      "page_type": "历史",
      "filename_prefix": "history"
    }
  ],
  "date": "2026-02-12"
}
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "match_id": "1311642",
        "page_type": "历史",
        "exists": true,
        "skip": true
      }
    ]
  }
}
```

## 5. 解析API

### 5.1 解析每日比赛

```http
POST /parse/daily
```

解析指定日期的所有比赛。

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| date | string | 否 | 日期 (YYYY-MM-DD)，默认当天 |
| background | boolean | 否 | 是否后台执行，默认true |

**请求示例**:

```json
{
  "date": "2026-02-12",
  "background": true
}
```

**响应示例**:

```json
{
  "success": true,
  "message": "解析任务已提交: 2026-02-12"
}
```

### 5.2 解析单个比赛

```http
POST /parse/match/{date}/{match_id}
```

解析指定日期和比赛ID的比赛数据。

**路径参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| date | string | 日期 (YYYY-MM-DD) |
| match_id | string | 比赛ID |

**响应示例**:

```json
{
  "success": true,
  "data": {
    "match_id": "1311642",
    "date": "2026-02-12",
    "is_complete": true,
    "missing_fields": [],
    "output_path": "/data/okooo/processed/2026-02-12/1311642.json"
  },
  "message": "解析成功"
}
```

### 5.3 获取解析结果

```http
GET /parse/result/{date}/{match_id}
```

获取指定日期和比赛ID的解析结果。

**路径参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| date | string | 日期 (YYYY-MM-DD) |
| match_id | string | 比赛ID |

**响应示例** (成功):

```json
{
  "success": true,
  "data": {
    "match_id": "1311642",
    "match_info": {
      "home_team": "主队",
      "away_team": "客队",
      "match_time": "2026-02-12 20:00"
    },
    "odds": { ... },
    "handicap": { ... },
    "history": { ... }
  },
  "message": "获取解析数据成功"
}
```

**响应示例** (404):

```json
{
  "detail": "比赛 1311642 在 2026-02-12 的解析数据不存在，请先完成爬虫和解析"
}
```

### 5.4 获取可解析日期列表

```http
GET /parse/dates
```

获取所有可解析的日期列表。

**响应示例**:

```json
{
  "success": true,
  "data": ["2026-02-12", "2026-02-11", "2026-02-10"],
  "message": "共 3 个日期"
}
```

## 6. SSE事件API

### 6.1 建立SSE连接

```http
GET /sse?client_id={client_id}
```

建立Server-Sent Events连接，接收实时事件推送。

**查询参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| client_id | string | 是 | 客户端标识 |

### 6.2 事件类型

#### 6.2.1 日志事件

```
event: okooo_log
data: {
  "level": "INFO",
  "message": "爬虫任务已启动",
  "timestamp": "2026-02-12T10:30:00Z"
}
```

#### 6.2.2 爬虫进度事件

```
event: okooo_crawl_progress
data: {
  "match_id": "1311642",
  "page_type": "历史",
  "progress": {
    "current": 5,
    "total": 8
  }
}
```

#### 6.2.3 爬虫完成事件

```
event: okooo_crawl_complete
data: {
  "match_id": "1311642",
  "date": "2026-02-12",
  "files_downloaded": 8
}
```

#### 6.2.4 解析完成事件

```
event: okooo_parse_complete
data: {
  "match_id": "1311642",
  "date": "2026-02-12",
  "is_complete": true,
  "missing_fields": [],
  "output_path": "/data/okooo/processed/2026-02-12/1311642.json"
}
```

#### 6.2.5 任务流程事件

**目录状态**:
```
event: okooo_task_directory_status
data: {
  "match_id": "1311642",
  "date": "2026-02-12",
  "exists": true,
  "path": "/data/okooo/matches/2026-02-12/1311642",
  "status": "completed"
}
```

**文件状态**:
```
event: okooo_task_files_status
data: {
  "match_id": "1311642",
  "date": "2026-02-12",
  "files": {
    "history": {
      "name": "澳客历史",
      "filename": "history_1311642.html",
      "exists": true,
      "status": "completed"
    }
  },
  "completed_count": 5,
  "total_count": 8
}
```

## 7. 数据模型

### 7.1 比赛数据模型

```typescript
interface OkoooMatch {
  id: string;              // 比赛ID
  match_id: string;        // 比赛ID（澳客）
  home_team: string;       // 主队
  away_team: string;       // 客队
  match_time: string;      // 比赛时间
  league: string;          // 联赛
  date: string;            // 日期
  created_at: string;      // 创建时间
  updated_at: string;      // 更新时间
}
```

### 7.2 解析结果模型

```typescript
interface ParsedMatch {
  match_id: string;
  match_info: {
    home_team: string;
    away_team: string;
    match_time: string;
    league: string;
  };
  odds: {
    european: Array<{
      company: string;
      win: number;
      draw: number;
      loss: number;
    }>;
  };
  handicap: {
    asian: Array<{
      company: string;
      home: number;
      handicap: string;
      away: number;
    }>;
  };
  history: {
    home_recent: Array<{
      opponent: string;
      result: string;
      score: string;
    }>;
    away_recent: Array<{
      opponent: string;
      result: string;
      score: string;
    }>;
    h2h: Array<{
      date: string;
      home: string;
      away: string;
      score: string;
    }>;
  };
  exchanges: {
    volume: number;
    trend: string;
  };
  form: {
    home_formation: string;
    away_formation: string;
  };
  game: {
    home_rank: number;
    away_rank: number;
    home_points: number;
    away_points: number;
  };
  macao_change: Array<{
    time: string;
    handicap: string;
    home_odds: number;
    away_odds: number;
  }>;
  bifa_change: Array<{
    time: string;
    index: number;
    trend: string;
  }>;
}
```

## 8. 错误处理

### 8.1 HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 8.2 错误响应格式

```json
{
  "success": false,
  "message": "错误描述信息",
  "error_code": "ERROR_CODE"
}
```

### 8.3 常见错误

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| FILE_NOT_FOUND | 文件不存在 | 先执行爬虫 |
| PARSE_ERROR | 解析失败 | 检查HTML文件完整性 |
| CRAWL_ERROR | 爬虫失败 | 检查网络连接 |
| VALIDATION_ERROR | 数据验证失败 | 检查字段完整性 |

## 9. 使用示例

### 9.1 完整爬虫流程

```javascript
// 1. 启动爬虫
const startCrawl = async () => {
  const response = await fetch('/api/v1/okooo/crawl', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ date: '2026-02-12' })
  });
  return await response.json();
};

// 2. 监听SSE事件
const eventSource = new EventSource('/api/v1/okooo/sse?client_id=chrome');
eventSource.addEventListener('okooo_crawl_complete', (event) => {
  const data = JSON.parse(event.data);
  console.log('爬虫完成:', data);
});

// 3. 获取解析结果
const getResult = async (matchId) => {
  const response = await fetch(
    `/api/v1/okooo/parse/result/2026-02-12/${matchId}`
  );
  return await response.json();
};
```

### 9.2 修复流程

```javascript
// 1. 检查并生成修复任务
const checkRepair = async () => {
  const response = await fetch('/api/v1/okooo/repair', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ date: '2026-02-12', dry_run: true })
  });
  return await response.json();
};

// 2. 获取修复任务
const getRepairTasks = async () => {
  const response = await fetch('/api/v1/okooo/repair-tasks');
  return await response.json();
};

// 3. 执行修复
const executeRepair = async (tasks) => {
  // 使用Chrome扩展执行爬虫
  chrome.runtime.sendMessage({
    type: 'OKOOO_START_REPAIR_TASKS',
    tasks: tasks
  });
};
```

---

*文档版本: 1.0*
*最后更新: 2026-02-12*
