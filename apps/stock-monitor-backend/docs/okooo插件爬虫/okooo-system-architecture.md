# 澳客竞彩数据系统架构文档

## 1. 系统概述

澳客竞彩数据系统是一个用于抓取、解析和管理足球比赛数据的完整解决方案。系统由Chrome浏览器扩展（前端）和Python FastAPI服务（后端）组成，支持实时数据同步和可视化展示。

## 2. 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户界面层                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Chrome浏览器扩展 (Sidepanel)                  │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │  │
│  │  │  比赛列表    │  │  任务流程    │  │  数据查看弹窗    │  │  │
│  │  │  - 待修复    │  │  - 目录创建  │  │  - JSON展示     │  │  │
│  │  │  - 已完成    │  │  - 文件下载  │  │  - 一键复制     │  │  │
│  │  │  - 查看数据  │  │  - 解析JSON  │  │                 │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/WebSocket/SSE
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         服务层                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              FastAPI后端服务 (Python)                      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │  │
│  │  │  爬虫调度    │  │  文件管理    │  │  SSE事件服务    │  │  │
│  │  │  - 任务队列  │  │  - 保存HTML  │  │  - 实时推送     │  │  │
│  │  │  - 进度跟踪  │  │  - 读取JSON  │  │  - 状态更新     │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 文件IO
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         数据层                                   │
│  ┌─────────────────────┐  ┌─────────────────────────────────┐  │
│  │   原始HTML文件       │  │      解析后的JSON文件            │  │
│  │  data/okooo/matches │  │   data/okooo/processed          │  │
│  │  /{date}/{match_id} │  │   /{date}/{match_id}.json       │  │
│  │  - history_*.html   │  │                                 │  │
│  │  - odds_*.html      │  │                                 │  │
│  │  - handicap_*.html  │  │                                 │  │
│  │  - exchanges_*.html │  │                                 │  │
│  │  - form_*.html      │  │                                 │  │
│  │  - game_*.html      │  │                                 │  │
│  │  - macao_change_*.  │  │                                 │  │
│  │  - bifa_change_*.   │  │                                 │  │
│  └─────────────────────┘  └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 3. 核心组件

### 3.1 前端组件 (Chrome Extension)

| 组件 | 文件路径 | 功能描述 |
|------|---------|---------|
| App.vue | `entrypoints/sidepanel/App.vue` | 主界面，包含所有功能模块 |
| MatchDataModal.vue | `components/MatchDataModal.vue` | 比赛数据查看弹窗 |
| MonitoringStatusPanel.vue | `components/MonitoringStatusPanel.vue` | 监控状态面板 |
| okooo-main-crawler.ts | `entrypoints/background/okooo-main-crawler.ts` | 主爬虫逻辑 |
| okooo-message-handler.ts | `entrypoints/background/okooo-message-handler.ts` | 消息处理 |

### 3.2 后端服务 (FastAPI)

| 服务 | 文件路径 | 功能描述 |
|------|---------|---------|
| okooo_service.py | `app/services/okooo_service.py` | 核心业务逻辑 |
| okooo_parser_service.py | `app/services/okooo_parser_service.py` | 解析服务 |
| okooo_controller.py | `app/api/okooo_controller.py` | API控制器 |
| okooo_parser_controller.py | `app/api/okooo_parser_controller.py` | 解析API控制器 |
| sse_service.py | `app/services/sse_service.py` | SSE事件服务 |

## 4. 技术栈

### 4.1 前端
- **框架**: Vue 3 + TypeScript
- **构建工具**: WXT
- **状态管理**: Vue Ref/Reactive
- **通信**: Chrome Extension API + SSE

### 4.2 后端
- **框架**: FastAPI
- **数据库**: SQLite + SQLAlchemy
- **缓存**: Redis
- **异步**: asyncio
- **解析**: BeautifulSoup4 + 正则表达式

## 5. 通信协议

### 5.1 HTTP API
- RESTful API设计
- JSON数据格式
- 标准HTTP状态码

### 5.2 SSE (Server-Sent Events)
- 实时推送爬虫进度
- 实时推送解析状态
- 单向服务器到客户端

### 5.3 Chrome Message Passing
- 扩展内部组件通信
- Background ↔ Sidepanel
- 异步消息处理

## 6. 数据存储

### 6.1 文件系统结构
```
data/okooo/
├── list/                          # 比赛列表
│   └── {date}/
│       └── match_list_*.html
├── matches/                       # 原始HTML文件
│   └── {date}/
│       └── {match_id}/
│           ├── history_{match_id}.html
│           ├── odds_{match_id}.html
│           ├── handicap_{match_id}.html
│           ├── exchanges_{match_id}.html
│           ├── form_{match_id}.html
│           ├── game_{match_id}.html
│           ├── macao_change_{match_id}.html
│           └── bifa_change_{match_id}.html
└── processed/                     # 解析后的JSON
    └── {date}/
        └── {match_id}.json
```

### 6.2 数据库表结构
- **OkoooMatch**: 比赛基本信息
- **OkoooMatchDetail**: 比赛详情数据
- **TestPage**: 页面配置信息

## 7. 关键流程

### 7.1 爬虫流程
1. 用户点击"开始爬虫"
2. 前端发送任务到后端
3. Chrome扩展打开标签页
4. 逐个下载8个页面
5. 保存HTML到文件系统
6. 实时推送进度到前端

### 7.2 解析流程
1. 爬虫完成后自动触发
2. 读取8个HTML文件
3. 提取关键数据
4. 生成JSON文件
5. 验证数据完整性
6. 实时推送结果到前端

### 7.3 修复流程
1. 检查文件完整性
2. 识别缺失的文件
3. 生成修复任务
4. 重新下载缺失文件
5. 重新解析

## 8. 扩展性设计

### 8.1 模块化架构
- 组件独立，职责清晰
- 插件化设计，易于扩展
- 配置驱动，灵活调整

### 8.2 可配置项
- 页面类型配置 (test_pages表)
- 爬虫间隔时间
- 文件大小阈值
- 并发任务数

## 9. 监控与日志

### 9.1 日志系统
- 分级日志 (DEBUG/INFO/WARNING/ERROR)
- 文件日志 + 控制台日志
- 实时日志推送到前端

### 9.2 监控指标
- 爬虫成功率
- 解析成功率
- 文件完整性
- 系统性能

## 10. 安全考虑

### 10.1 数据安全
- 本地文件存储
- 无敏感数据传输
- 访问权限控制

### 10.2 爬虫安全
- 请求间隔控制
- User-Agent模拟
- 验证码处理

---

*文档版本: 1.0*
*最后更新: 2026-02-12*
