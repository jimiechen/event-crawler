# 澳客竞彩数据系统 - 文档中心

## 文档列表

### 1. [系统架构文档](./okooo-system-architecture.md)
系统整体架构、组件关系、技术栈、数据存储结构

### 2. [前端开发指南](./okooo-frontend-guide.md)
前端项目结构、组件详解、状态管理、事件通信、API调用

### 3. [后端API文档](./okooo-backend-api.md)
所有API端点、请求/响应格式、SSE事件、数据模型

### 4. [数据流程文档](./okooo-data-flow.md)
完整数据流程图、详细数据流、数据结构、时序图、异常处理

## 快速开始

### 启动后端服务
```bash
cd apps/stock-monitor-backend
python -m app.main
```

### 启动前端开发
```bash
cd apps/chrome-extension
npm run dev
```

### 加载Chrome扩展
1. 打开 `chrome://extensions`
2. 开启开发者模式
3. 点击"加载已解压的扩展"
4. 选择 `.output/chrome-mv3-dev` 目录

## 主要功能

- ✅ 比赛数据爬虫（8个页面）
- ✅ 实时进度展示
- ✅ 文件完整性检查
- ✅ 自动修复机制
- ✅ 数据解析（HTML → JSON）
- ✅ 数据可视化展示
- ✅ 一键复制功能

## 技术栈

**前端**: Vue 3 + TypeScript + WXT + Chrome Extension API

**后端**: FastAPI + Python + SQLite + Redis

**通信**: HTTP REST API + SSE (Server-Sent Events) + Chrome Message Passing

---

*文档版本: 1.0*
*最后更新: 2026-02-12*
