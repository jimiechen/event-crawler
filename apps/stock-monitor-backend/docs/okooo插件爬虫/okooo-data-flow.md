# 澳客竞彩数据系统 - 数据流程文档

## 1. 数据流程概述

系统数据流分为三个主要阶段：
1. **数据采集阶段** - 爬虫抓取比赛数据
2. **数据处理阶段** - 解析HTML生成JSON
3. **数据展示阶段** - 前端可视化展示

## 2. 完整数据流程图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据采集阶段                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  用户操作                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. 点击"开始爬虫" 或 "立即修复"                                      │   │
│  │  2. 前端发送请求到后端                                               │   │
│  │  3. 后端生成任务队列                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Chrome扩展爬虫                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  4. 打开标签页访问比赛页面                                            │   │
│  │  5. 逐个下载8个页面：                                                │   │
│  │     - 历史战绩 (history)                                             │   │
│  │     - 欧赔数据 (odds)                                                │   │
│  │     - 亚盘数据 (handicap)                                            │   │
│  │     - 盈亏指数 (exchanges)                                           │   │
│  │     - 阵容信息 (form)                                                │   │
│  │     - 积分排名 (game)                                                │   │
│  │     - 澳门亚盘变化 (macao_change)                                     │   │
│  │     - 必发指数变化 (bifa_change)                                      │   │
│  │  6. 保存HTML到文件系统                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  文件系统存储                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  data/okooo/matches/{date}/{match_id}/                              │   │
│  │  ├── history_{match_id}.html                                        │   │
│  │  ├── odds_{match_id}.html                                           │   │
│  │  ├── handicap_{match_id}.html                                       │   │
│  │  ├── exchanges_{match_id}.html                                      │   │
│  │  ├── form_{match_id}.html                                           │   │
│  │  ├── game_{match_id}.html                                           │   │
│  │  ├── macao_change_{match_id}.html                                   │   │
│  │  └── bifa_change_{match_id}.html                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据处理阶段                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  解析器处理                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  7. 读取8个HTML文件                                                  │   │
│  │  8. 提取关键数据：                                                   │   │
│  │     - 比赛基本信息                                                   │   │
│  │     - 赔率数据                                                       │   │
│  │     - 历史战绩                                                       │   │
│  │     - 阵容信息                                                       │   │
│  │     - 积分排名                                                       │   │
│  │     - 指数变化                                                       │   │
│  │  9. 验证15个必需字段                                                  │   │
│  │  10. 生成JSON文件                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  JSON文件存储                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  data/okooo/processed/{date}/{match_id}.json                        │   │
│  │  {                                                                  │   │
│  │    "match_id": "1311642",                                           │   │
│  │    "match_info": { ... },                                           │   │
│  │    "odds": { ... },                                                 │   │
│  │    "handicap": { ... },                                             │   │
│  │    "history": { ... },                                              │   │
│  │    ...                                                              │   │
│  │  }                                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据展示阶段                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  前端展示                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  11. 任务流程可视化                                                  │   │
│  │      - 目录创建状态                                                  │   │
│  │      - 8个文件下载进度                                               │   │
│  │      - 解析完成状态                                                  │   │
│  │  12. 点击查看数据                                                    │   │
│  │  13. 弹窗显示JSON                                                    │   │
│  │  14. 支持一键复制                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3. 详细数据流

### 3.1 爬虫数据流

```
用户点击"开始爬虫"
    │
    ▼
App.vue: startOkoooCrawler()
    │
    ▼
chrome.runtime.sendMessage({ type: 'OKOOO_START_CRAWLER' })
    │
    ▼
okooo-message-handler.ts: 处理消息
    │
    ▼
okoooMainCrawler.start()
    │
    ├── 1. fetchTemplatesFromBackend() 获取页面模板
    │
    ├── 2. generateTaskQueue() 生成任务队列
    │       └── 为每个比赛生成8个任务
    │
    ├── 3. initMatchCompletionTracker() 初始化完成跟踪
    │       └── Map<matchId, {total: 8, completed: 0}>
    │
    ├── 4. processTaskQueue() 处理任务队列
    │       └── 逐个执行任务
    │
    ├── 5. processTask() 处理单个任务
    │       ├── 打开标签页
    │       ├── 获取页面HTML
    │       ├── 保存HTML到后端
    │       └── 更新任务状态
    │
    ├── 6. updateMatchCompletion() 更新完成状态
    │       └── completed++
    │           └── if completed >= 8:
    │               └── triggerMatchParse()
    │
    └── 7. triggerMatchParse() 触发解析
            └── 调用后端API: POST /parse/match/{date}/{matchId}
```

### 3.2 解析数据流

```
爬虫完成 (8个文件)
    │
    ▼
okoooService.parse_specific_match()
    │
    ├── 1. OkoooParser.process_date_match()
    │       │
    │       ├── 1.1 读取8个HTML文件
    │       │       ├── history_{match_id}.html
    │       │       ├── odds_{match_id}.html
    │       │       ├── handicap_{match_id}.html
    │       │       ├── exchanges_{match_id}.html
    │       │       ├── form_{match_id}.html
    │       │       ├── game_{match_id}.html
    │       │       ├── macao_change_{match_id}.html
    │       │       └── bifa_change_{match_id}.html
    │       │
    │       ├── 1.2 解析每个文件
    │       │       ├── parse_history() - 历史战绩
    │       │       ├── parse_odds() - 欧赔数据
    │       │       ├── parse_handicap() - 亚盘数据
    │       │       ├── parse_exchanges() - 盈亏指数
    │       │       ├── parse_form() - 阵容信息
    │       │       ├── parse_game() - 积分排名
    │       │       ├── parse_macao_change() - 澳门亚盘变化
    │       │       └── parse_bifa_change() - 必发指数变化
    │       │
    │       └── 1.3 合并数据
    │               └── result = { match_info, odds, handicap, ... }
    │
    ├── 2. OkoooParser.save_result()
    │       └── 保存到 data/okooo/processed/{date}/{match_id}.json
    │
    ├── 3. OkoooParser.validate_parsed_data()
    │       └── 验证15个必需字段
    │           └── return (is_complete, missing_fields)
    │
    └── 4. 发送SSE事件
            ├── okooo_task_parse_complete
            │   └── { match_id, is_complete, missing_fields, output_path }
            ├── okooo_parse_complete (兼容旧版本)
            └── okooo_parse_warning (如果有缺失字段)
```

### 3.3 实时推送数据流

```
后端事件
    │
    ├── 爬虫事件 ──────────────────────────┐
    │   ├── okooo_crawl_progress           │
    │   └── okooo_crawl_complete           │
    │                                      │
    ├── 解析事件 ──────────────────────────┤
    │   ├── okooo_parse_start              │
    │   ├── okooo_parse_complete           │
    │   ├── okooo_parse_warning            │
    │   └── okooo_parse_error              │
    │                                      │
    ├── 任务流程事件 ──────────────────────┤
    │   ├── okooo_task_directory_status    │
    │   ├── okooo_task_files_status        │
    │   ├── okooo_task_parse_start         │
    │   ├── okooo_task_parse_complete      │
    │   └── okooo_task_parse_error         │
    │                                      │
    └── 日志事件 ──────────────────────────┤
        └── okooo_log                      │
                                           │
                                           ▼
                              ┌──────────────────────┐
                              │   SSE服务            │
                              │   sse_service.py     │
                              │   - 广播事件         │
                              │   - 管理连接         │
                              └──────────────────────┘
                                           │
                                           ▼
                              ┌──────────────────────┐
                              │   前端监听           │
                              │   App.vue            │
                              │   - setupSSE()       │
                              │   - 更新状态         │
                              └──────────────────────┘
                                           │
                                           ▼
                              ┌──────────────────────┐
                              │   UI更新             │
                              │   - 任务流程展示     │
                              │   - 日志显示         │
                              │   - 进度条           │
                              └──────────────────────┘
```

## 4. 数据结构详解

### 4.1 爬虫任务结构

```typescript
interface CrawlerTask {
  matchId: string;           // 比赛ID
  homeTeam: string;          // 主队名称
  awayTeam: string;          // 客队名称
  pageType: string;          // 页面类型 (历史/欧赔/亚盘等)
  url: string;               // 页面URL
  filenamePrefix: string;    // 文件名前缀
  status: 'pending' | 'processing' | 'completed' | 'error' | 'skipped';
  error?: string;            // 错误信息
  html?: string;             // HTML内容
}
```

### 4.2 比赛完成跟踪结构

```typescript
interface MatchTracker {
  total: number;             // 总任务数 (8)
  completed: number;         // 已完成数
  date: string;              // 日期
  status: 'pending' | 'parsing' | 'completed' | 'error';
}

// Map<matchId, MatchTracker>
matchCompletionTracker: Map<string, MatchTracker>
```

### 4.3 解析结果结构

```typescript
interface ParsedMatch {
  match_id: string;
  
  // 比赛基本信息
  match_info: {
    home_team: string;       // 主队
    away_team: string;       // 客队
    match_time: string;      // 比赛时间
    league: string;          // 联赛
    round?: string;          // 轮次
  };
  
  // 欧赔数据
  odds: {
    european: Array<{
      company: string;       // 公司
      win: number;           // 主胜
      draw: number;          // 平局
      loss: number;          // 客胜
      update_time?: string;  // 更新时间
    }>;
  };
  
  // 亚盘数据
  handicap: {
    asian: Array<{
      company: string;       // 公司
      home: number;          // 主队水位
      handicap: string;      // 盘口
      away: number;          // 客队水位
      update_time?: string;  // 更新时间
    }>;
  };
  
  // 历史战绩
  history: {
    home_recent: Array<{     // 主队近期战绩
      opponent: string;
      result: string;        // 胜/平/负
      score: string;         // 比分
      date?: string;
    }>;
    away_recent: Array<{     // 客队近期战绩
      opponent: string;
      result: string;
      score: string;
      date?: string;
    }>;
    h2h: Array<{             // 交锋记录
      date: string;
      home: string;
      away: string;
      score: string;
    }>;
  };
  
  // 盈亏指数
  exchanges: {
    volume: number;          // 交易量
    trend: string;           // 趋势
    home?: number;           // 主队盈亏
    away?: number;           // 客队盈亏
  };
  
  // 阵容信息
  form: {
    home_formation: string;  // 主队阵型
    away_formation: string;  // 客队阵型
    home_players?: Array<{   // 主队球员
      name: string;
      position: string;
      number?: string;
    }>;
    away_players?: Array<{   // 客队球员
      name: string;
      position: string;
      number?: string;
    }>;
  };
  
  // 积分排名
  game: {
    home_rank: number;       // 主队排名
    away_rank: number;       // 客队排名
    home_points: number;     // 主队积分
    away_points: number;     // 客队积分
    home_matches?: number;   // 主队场次
    away_matches?: number;   // 客队场次
  };
  
  // 澳门亚盘变化
  macao_change: Array<{
    time: string;            // 时间
    handicap: string;        // 盘口
    home_odds: number;       // 主队赔率
    away_odds: number;       // 客队赔率
  }>;
  
  // 必发指数变化
  bifa_change: Array<{
    time: string;            // 时间
    index: number;           // 指数
    trend: string;           // 趋势
  }>;
}
```

### 4.4 任务流程展示结构

```typescript
interface MatchTaskFlow {
  matchId: string;
  date: string;
  
  // 目录状态
  directory: {
    status: 'pending' | 'processing' | 'completed' | 'error';
    exists: boolean;
    path: string;
  };
  
  // 文件状态
  files: {
    items: Record<string, {
      name: string;          // 显示名称
      filename: string;      // 文件名
      exists: boolean;       // 是否存在
      status: 'pending' | 'processing' | 'completed' | 'missing' | 'error';
    }>;
    completedCount: number;  // 已完成数
    totalCount: number;      // 总数 (8)
  };
  
  // 解析状态
  parse: {
    status: 'pending' | 'processing' | 'completed' | 'incomplete' | 'error' | 'warning';
    outputPath: string;      // 输出路径
    isComplete: boolean;     // 是否完整
    missingFields: string[]; // 缺失字段
  };
}
```

## 5. 关键流程时序图

### 5.1 爬虫流程时序

```
用户    前端App    后台脚本    后端API    文件系统
 │         │          │          │          │
 │ 点击    │          │          │          │
 │────────►│          │          │          │
 │         │ 发送消息 │          │          │
 │         │─────────►│          │          │
 │         │          │ 获取模板 │          │
 │         │          │─────────►│          │
 │         │          │◄─────────│          │
 │         │          │          │          │
 │         │          │ 生成任务 │          │
 │         │          │ 队列     │          │
 │         │          │          │          │
 │         │          │ 执行任务 │          │
 │         │          │─────────►│ 保存HTML │
 │         │          │          │─────────►│
 │         │          │◄─────────│          │
 │         │          │          │          │
 │         │◄─────────│ SSE事件  │          │
 │         │          │          │          │
 │         │ 更新UI   │          │          │
 │◄────────│          │          │          │
 │         │          │          │          │
```

### 5.2 解析流程时序

```
爬虫    后端API    解析器    文件系统    前端App
 │        │         │          │          │
 │ 完成   │         │          │          │
 │───────►│         │          │          │
 │        │ 调用    │          │          │
 │        │────────►│          │          │
 │        │         │ 读取HTML │          │
 │        │         │─────────►│          │
 │        │         │◄─────────│          │
 │        │         │          │          │
 │        │         │ 解析数据 │          │
 │        │         │          │          │
 │        │         │ 保存JSON │          │
 │        │         │─────────►│          │
 │        │         │◄─────────│          │
 │        │         │          │          │
 │        │◄────────│          │          │
 │        │         │          │          │
 │        │ SSE事件 ────────────────►│
 │        │         │          │          │
 │        │         │          │ 更新UI   │
 │        │         │          │◄─────────│
 │        │         │          │          │
```

## 6. 异常处理流程

### 6.1 爬虫异常

```
processTask() 执行失败
    │
    ├── 1. 捕获异常
    │       └── task.status = 'error'
    │       └── task.error = error.message
    │
    ├── 2. 更新统计
    │       └── stats.errorCount++
    │
    ├── 3. 记录日志
    │       └── addLog('❌ 任务失败: ' + error, 'error')
    │
    ├── 4. 继续下一个任务
    │       └── currentTaskIndex++
    │       └── setTimeout(processTaskQueue, 1500)
    │
    └── 5. 通知前端
            └── sendMessage({ type: 'OKOOO_CRAWLER_ERROR', error })
```

### 6.2 解析异常

```
parse_specific_match() 执行失败
    │
    ├── 1. 捕获异常
    │       └── error_msg = str(e)
    │
    ├── 2. 记录日志
    │       └── _on_log('ERROR', error_msg)
    │
    ├── 3. 发送错误事件
    │       └── sse_service.broadcast('okooo_task_parse_error', {
    │               match_id, date, error: error_msg, status: 'error'
    │           })
    │
    └── 4. 继续下一个比赛
            └── for循环继续
```

### 6.3 文件不存在异常

```
get_parsed_result() 文件不存在
    │
    ├── 1. 检查文件
    │       └── os.path.exists(result_file) = False
    │
    ├── 2. 返回错误
    │       └── return { success: False, error: '解析数据不存在' }
    │
    ├── 3. API返回404
    │       └── raise HTTPException(status_code=404, detail='...')
    │
    └── 4. 前端处理
            └── 显示友好错误提示
```

## 7. 性能优化

### 7.1 爬虫优化

1. **任务队列**: 批量处理，避免内存溢出
2. **请求间隔**: 1.5秒间隔，避免被封
3. **并发控制**: 单任务顺序执行，避免并发问题
4. **文件检查**: 下载前检查，避免重复下载

### 7.2 解析优化

1. **延迟加载**: 按需导入解析器
2. **缓存机制**: 避免重复解析
3. **增量更新**: 只解析缺失的数据
4. **异步处理**: 后台解析不阻塞主流程

### 7.3 前端优化

1. **虚拟滚动**: 大量数据时优化性能
2. **状态合并**: 减少重渲染
3. **事件节流**: 避免频繁更新
4. **懒加载**: 按需加载组件

## 8. 监控指标

### 8.1 爬虫指标

- **成功率**: 成功下载的任务数 / 总任务数
- **平均耗时**: 每个任务的平均执行时间
- **错误率**: 失败任务数 / 总任务数
- **文件完整性**: 存在的文件数 / 期望的文件数

### 8.2 解析指标

- **解析成功率**: 成功解析的比赛数 / 总比赛数
- **字段完整率**: 完整字段数 / 总字段数
- **解析耗时**: 每个比赛的平均解析时间
- **数据质量**: 有效数据占比

### 8.3 系统指标

- **内存使用**: 峰值内存占用
- **CPU使用**: 平均CPU占用率
- **磁盘IO**: 文件读写频率
- **网络延迟**: API响应时间

---

*文档版本: 1.0*
*最后更新: 2026-02-12*
