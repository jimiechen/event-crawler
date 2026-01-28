# Okooo竞彩爬虫集成与页面设计方案

## 1. 概述
本方案旨在将独立的 Okooo 爬虫模块集成到 Stock Monitor Backend 的 FastAPI 服务中，并通过 `test-center.html` 提供图形化的控制和监控界面。

## 2. 后端集成设计

### 2.1 服务层 (Service Layer)
创建单例服务 `OkoooService` (`app/services/okooo_service.py`)，负责：
- 管理 `OkoooScheduler` 的生命周期（初始化、启动、停止）。
- 维护当前爬虫状态（空闲、运行中、进度）。
- 通过 `ConnectionManager` 广播实时日志。

```python
class OkoooService:
    def __init__(self):
        self.scheduler = None
        self.is_running = False
        self.stats = {"total": 0, "processed": 0, "success": 0, "failed": 0}

    async def start_crawl(self, start_id: int, end_id: int):
        # 启动异步任务
        pass

    async def stop_crawl(self):
        # 停止任务
        pass
```

### 2.2 API 层 (Controller Layer)
新增控制器 `app/api/okooo_controller.py`，提供以下接口：

- `POST /api/v1/okooo/start`: 启动爬虫
    - 参数: `start_id`, `end_id`
- `POST /api/v1/okooo/stop`: 停止爬虫
- `GET /api/v1/okooo/status`: 获取当前状态和统计信息

### 2.3 日志与消息推送
复用现有的 WebSocket 通道 `/api/v1/timed-task/ws`。
后端在爬虫执行过程中，通过 `manager.broadcast()` 发送特定类型的消息，例如：
```json
{
    "type": "okooo_log",
    "level": "INFO",
    "message": "Worker 1: Downloaded match 1143895",
    "timestamp": "2026-01-28 10:00:00"
}
```

## 3. 前端页面设计方案 (test-center.html)

### 3.1 导航栏
在现有的 Tabs 中增加 "Okooo竞彩" 选项卡。

### 3.2 页面布局
"Okooo竞彩" 面板包含左右两栏或上下结构：

#### A. 控制面板 (Control Panel)
- **ID 范围设置**:
    - 起始 ID (Start Match ID) 输入框
    - 结束 ID (End Match ID) 输入框
- **操作按钮**:
    - "开始爬取" (Start Crawl) - 绿色按钮，运行中禁用
    - "停止爬取" (Stop Crawl) - 红色按钮，空闲时禁用
- **状态概览**:
    - 状态指示器 (Status Badge): 空闲 (Gray) / 运行中 (Green)
    - 进度条 (Progress Bar): 根据 (Processed / Total) 显示进度

#### B. 实时日志 (Live Logs)
- 黑色背景终端风格的日志显示区域。
- 自动滚动到底部。
- 支持 "清空日志" 按钮。

#### C. 定时任务管理 (Scheduled Tasks)
- 显示 Okooo 相关的定时任务（如每日增量爬取）。
- 显示 Cron 表达式。
- 提供 "立即触发" 和 "启用/禁用" 开关。

### 3.3 数据交互
- **初始化**: 页面加载时调用 `/api/v1/okooo/status` 获取当前状态。
- **WebSocket**: 连接 `/api/v1/timed-task/ws`，监听 `okooo_log` 类型的消息并追加到日志区域。
- **操作**: 点击按钮发送 AJAX 请求到对应 API。

## 4. 实施计划

1.  **后端实现**:
    - 创建 `app/services/okooo_service.py`。
    - 创建 `app/api/okooo_controller.py` 并注册路由。
    - 修改 `app/crawler/okooo/scheduler.py` 以支持通过回调或事件发送日志。

2.  **前端实现**:
    - 修改 `static/test-center.html`，添加 Vue 组件逻辑和 UI 模板。
    - 集成 WebSocket 监听逻辑。

3.  **验证**:
    - 启动 `run.py`。
    - 打开 `http://localhost:8000/static/test-center.html` 进行测试。
