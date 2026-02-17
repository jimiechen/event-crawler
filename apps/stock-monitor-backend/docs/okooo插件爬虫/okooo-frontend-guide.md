# 澳客竞彩数据系统 - 前端开发指南

## 1. 项目概述

前端采用 Chrome 浏览器扩展形式，基于 Vue 3 + TypeScript + WXT 构建，提供比赛数据抓取、解析和可视化的完整用户界面。

## 2. 项目结构

```
apps/chrome-extension/
├── entrypoints/
│   ├── sidepanel/              # 侧边栏主界面
│   │   ├── App.vue            # 主应用组件
│   │   ├── main.ts            # 入口文件
│   │   ├── style.css          # 样式文件
│   │   └── components/        # 子组件
│   │       ├── SessionManager.vue
│   │       ├── SystemStatus.vue
│   │       ├── TemplateEditor.vue
│   │       └── WencaiDataCapture.vue
│   ├── background/            # 后台脚本
│   │   ├── okooo-main-crawler.ts      # 主爬虫逻辑
│   │   ├── okooo-message-handler.ts   # 消息处理器
│   │   ├── okooo-network-monitor.ts   # 网络监控
│   │   ├── okooo-handicap-crawler.ts  # 亚盘爬虫
│   │   ├── okooo-list-crawler.ts      # 列表爬虫
│   │   └── sse-handler.ts             # SSE处理器
│   └── popup/                 # 弹出窗口
├── components/                # 共享组件
│   ├── MatchDataModal.vue    # 比赛数据弹窗
│   └── MonitoringStatusPanel.vue
├── common/                    # 公共配置
│   ├── constants.ts          # 常量定义
│   ├── message-types.ts      # 消息类型
│   └── shared-types.ts       # 共享类型
└── utils/                     # 工具函数
    ├── football-parser.js    # 足球数据解析
    └── date-utils.ts         # 日期工具
```

## 3. 核心组件详解

### 3.1 App.vue (主界面)

#### 3.1.1 状态管理

```typescript
// 爬虫状态
interface CrawlerStatus {
  isRunning: boolean;
  phase: 'idle' | 'initializing' | 'crawling' | 'paused' | 'completed';
  totalMatches: number;
  currentMatchIndex: number;
  totalHistory: number;
  currentHistoryIndex: number;
  results: CrawlerResult[];
}

// 修复状态
interface RepairStatus {
  isRunning: boolean;
  isDryRun: boolean;
  totalChecked: number;
  repairingCount: number;
  ids: string[];
  repairDetails: RepairDetail[];
  message: string;
}

// 任务流程状态
interface MatchTaskFlow {
  matchId: string;
  date: string;
  directory: DirectoryStatus;
  files: FilesStatus;
  parse: ParseStatus;
}
```

#### 3.1.2 主要功能区域

1. **比赛列表区域**
   - 显示待修复的比赛
   - 显示已完成的比赛
   - 支持查看数据弹窗

2. **任务流程展示区域**
   - 3步骤可视化：创建目录 → 下载8文件 → 解析JSON
   - 实时状态更新
   - 文件级进度展示

3. **日志区域**
   - 实时日志流
   - 分级显示 (INFO/WARNING/ERROR/SUCCESS)
   - 支持清空

4. **控制按钮区域**
   - 开始/停止爬虫
   - 立即修复
   - 数据同步

### 3.2 MatchDataModal.vue (数据弹窗)

#### 3.2.1 功能特性

- **JSON展示**: 格式化显示，语法高亮
- **一键复制**: 复制到剪贴板
- **错误处理**: 404错误友好提示
- **加载状态**: 加载动画

#### 3.2.2 Props

```typescript
interface Props {
  visible: boolean;    // 控制显示/隐藏
  matchId: string;     // 比赛ID
  date: string;        // 日期 (YYYY-MM-DD)
}
```

#### 3.2.3 事件

```typescript
interface Emits {
  (e: 'close'): void;  // 关闭事件
}
```

### 3.3 okooo-main-crawler.ts (主爬虫)

#### 3.3.1 核心类

```typescript
class OkoooMainCrawler {
  // 状态
  private isRunning: boolean;
  private taskQueue: CrawlerTask[];
  private currentTaskIndex: number;
  
  // 比赛完成跟踪
  private matchCompletionTracker: Map<string, MatchTracker>;
  
  // 核心方法
  async start(): Promise<void>;           // 启动爬虫
  async stop(): Promise<void>;            // 停止爬虫
  private async processTaskQueue(): Promise<void>;  // 处理任务队列
  private async updateMatchCompletion(matchId: string): Promise<void>;  // 更新完成状态
  private async triggerMatchParse(matchId: string, date: string): Promise<void>;  // 触发解析
}
```

#### 3.3.2 任务队列处理流程

1. **初始化**: `generateTaskQueue()` 生成任务队列
2. **执行**: `processTaskQueue()` 逐个执行任务
3. **跟踪**: `updateMatchCompletion()` 更新比赛完成状态
4. **解析**: `triggerMatchParse()` 触发后端解析

## 4. 状态管理

### 4.1 响应式状态

```typescript
// 主状态
const okoooState = ref<OkoooSyncState>({
  crawler: { /* ... */ },
  list: { /* ... */ },
  repair: { /* ... */ }
});

// 日志
const okoooLogs = ref<LogEntry[]>([]);

// 解析结果
const parseResults = ref<ParseResult[]>([]);
const parseWarnings = ref<ParseWarning[]>([]);
const parseErrors = ref<ParseError[]>([]);

// 任务流程
const matchTaskFlows = ref<Record<string, MatchTaskFlow>>({});
const currentProcessingMatchId = ref<string>('');
```

### 4.2 计算属性

```typescript
// 聚合后的比赛进度
const aggregatedResults = computed(() => {
  // 合并本地状态和服务端确认的进度
});

// 统一修复列表
const unifiedRepairList = computed(() => {
  // 合并待修复列表和爬虫结果
});
```

## 5. 事件通信

### 5.1 Chrome Message Passing

#### 5.1.1 消息类型

```typescript
// 爬虫控制
'OKOOO_START_CRAWLER'         // 启动爬虫
'OKOOO_STOP_CRAWLER'          // 停止爬虫
'OKOOO_GET_STATUS'            // 获取状态

// 修复任务
'OKOOO_START_REPAIR'          // 开始修复
'OKOOO_START_REPAIR_TASKS'    // 开始修复任务队列

// 解析完成
'OKOOO_MATCH_PARSED'          // 单个比赛解析完成
'OKOOO_MATCH_PARSE_ERROR'     // 解析错误

// 爬虫完成
'OKOOO_CRAWLER_COMPLETED'     // 爬虫完成

// 验证码
'OKOOO_CAPTCHA_DETECTED'      // 检测到验证码
'OKOOO_CAPTCHA_SOLVED'        // 验证码已解决
```

#### 5.1.2 使用示例

```typescript
// 发送消息
chrome.runtime.sendMessage({
  type: 'OKOOO_START_REPAIR_TASKS',
  tasks: repairTasks
}).then(response => {
  if (response.success) {
    // 处理成功
  }
});

// 监听消息
chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'OKOOO_MATCH_PARSED') {
    // 处理解析完成事件
  }
});
```

### 5.2 SSE (Server-Sent Events)

#### 5.2.1 事件类型

```typescript
// 日志事件
'okooo_log'                   // 普通日志

// 爬虫事件
'okooo_crawl_progress'        // 爬虫进度
'okooo_crawl_complete'        // 爬虫完成

// 解析事件
'okooo_parse_start'           // 解析开始
'okooo_parse_complete'        // 解析完成
'okooo_parse_warning'         // 解析警告
'okooo_parse_error'           // 解析错误
'okooo_parse_summary'         // 解析总结

// 任务流程事件
'okooo_task_directory_status' // 目录状态
'okooo_task_files_status'     // 文件状态
'okooo_task_parse_start'      // 解析开始
'okooo_task_parse_complete'   // 解析完成
'okooo_task_parse_error'      // 解析错误
```

#### 5.2.2 连接管理

```typescript
let eventSource: EventSource | null = null;

const setupSSEConnection = () => {
  eventSource = new EventSource(
    'http://localhost:8000/api/v1/okooo/sse?client_id=chrome-extension'
  );
  
  // 监听事件
  eventSource.addEventListener('okooo_log', (event) => {
    const data = JSON.parse(event.data);
    // 处理日志
  });
  
  // 错误处理
  eventSource.onerror = (error) => {
    console.error('SSE连接错误:', error);
  };
};
```

## 6. API 调用

### 6.1 HTTP API

```typescript
// 基础配置
const backendUrl = 'http://localhost:8000';

// 获取状态
const response = await fetch(`${backendUrl}/api/v1/okooo/status`);

// 开始修复
const response = await fetch(`${backendUrl}/api/v1/okooo/repair`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ date: '2026-02-12', dry_run: false })
});

// 获取解析数据
const response = await fetch(
  `${backendUrl}/api/v1/okooo/parse/result/${date}/${matchId}`
);
```

### 6.2 错误处理

```typescript
try {
  const response = await fetch(url);
  
  if (response.status === 404) {
    // 数据不存在
    error.value = '比赛数据不存在，请先完成爬虫和解析';
    return;
  }
  
  const result = await response.json();
  
  if (!result.success) {
    error.value = result.message;
  }
} catch (e) {
  error.value = '网络请求失败: ' + e.message;
}
```

## 7. 样式系统

### 7.1 CSS 变量

```css
:root {
  /* 颜色 */
  --primary-color: #667eea;
  --success-color: #16a34a;
  --warning-color: #f59e0b;
  --error-color: #ef4444;
  
  /* 背景 */
  --bg-primary: #ffffff;
  --bg-secondary: #f9fafb;
  
  /* 边框 */
  --border-color: #e5e7eb;
  --border-light: #f3f4f6;
  
  /* 间距 */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  
  /* 圆角 */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
}
```

### 7.2 状态颜色

```css
/* 完成状态 */
.status-completed { color: #16a34a; }
.status-success { background: #dcfce7; color: #166534; }

/* 处理中状态 */
.status-processing { color: #3b82f6; }

/* 警告状态 */
.status-warning { color: #f59e0b; }

/* 错误状态 */
.status-error { color: #ef4444; }

/* 等待状态 */
.status-pending { color: #9ca3af; }
```

## 8. 开发规范

### 8.1 代码风格

- 使用 TypeScript 严格模式
- 组件名使用 PascalCase
- 变量名使用 camelCase
- 常量名使用 UPPER_SNAKE_CASE

### 8.2 组件规范

```typescript
// Props 定义
interface Props {
  visible: boolean;
  matchId: string;
}

// Emits 定义
interface Emits {
  (e: 'close'): void;
  (e: 'update', data: Data): void;
}

// 组件定义
const props = defineProps<Props>();
const emit = defineEmits<Emits>();
```

### 8.3 错误处理

```typescript
// 使用 try-catch
const fetchData = async () => {
  try {
    const response = await fetch(url);
    return await response.json();
  } catch (error) {
    console.error('获取数据失败:', error);
    throw error;
  }
};
```

## 9. 调试技巧

### 9.1 Chrome DevTools

1. **查看日志**: Console 面板
2. **网络请求**: Network 面板
3. **扩展状态**: chrome://extensions
4. **背景页**: Service Worker 调试

### 9.2 日志级别

```typescript
// 开发环境
const DEBUG = true;

if (DEBUG) {
  console.log('调试信息:', data);
}
```

## 10. 部署说明

### 10.1 构建命令

```bash
# 开发模式
npm run dev

# 生产构建
npm run build

# 打包扩展
npm run zip
```

### 10.2 加载扩展

1. 打开 Chrome 扩展管理页面: `chrome://extensions`
2. 开启开发者模式
3. 点击"加载已解压的扩展"
4. 选择 `.output/chrome-mv3-dev` 目录

---

*文档版本: 1.0*
*最后更新: 2026-02-12*
