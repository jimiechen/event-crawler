# DESIGN_TaskExecutionLogSystem

## 1. 数据库设计 (Database Design)

### Table: `task_execution_logs`

```sql
CREATE TABLE task_execution_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '任务日志ID',
    task_type VARCHAR(50) NOT NULL COMMENT '任务类型: csv_sync, tushare_sync, calculate_score',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态: pending, running, success, failed',
    target_url VARCHAR(255) COMMENT '目标API地址',
    result_message TEXT COMMENT '执行结果或错误信息',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    completed_at DATETIME COMMENT '完成时间',
    INDEX idx_task_type (task_type),
    INDEX idx_stock_code (stock_code),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) COMMENT='原子任务执行日志表';
```

## 2. API 接口设计 (API Definitions)

### 2.1 任务管理 (Task Management) - `TaskLogController`

| Method | Path | Description | Params/Body |
| :--- | :--- | :--- | :--- |
| POST | `/api/tasks/batch-create` | 批量创建任务 | `{ "task_type": "csv_sync" }` |
| POST | `/api/tasks/execute` | 执行任务(批量/单条) | `{ "log_ids": [1, 2, 3] }` |
| GET | `/api/tasks/logs` | 获取日志列表 | `?page=1&size=20&status=pending&code=000001` |
| POST | `/api/tasks/retry` | 重试失败任务 | `{ "log_ids": [...] }` (可选，复用 execute) |

### 2.2 原子能力接口 (Atomic Capabilities)

#### StockSyncController
- `POST /api/v1/stock/sync/csv/{stock_code}`
    - Logic: 调用 `StockSyncService.sync_csv_single(stock_code)`
- `POST /api/v1/stock/sync/tushare/{stock_code}`
    - Logic: 调用 `StockSyncService.sync_tushare_single(stock_code)`

#### StockScoreController (or TimedTaskController)
- `POST /api/v1/stock/sync/calculate/{stock_code}`
    - Logic: 调用 `RuleEngineService.calculate_single(stock_code)`

## 3. 业务流程 (Business Flow)

### 3.1 批量创建 (Batch Creation)
1. User clicks "Batch CSV Sync" on UI.
2. Frontend calls `POST /api/tasks/batch-create { type: 'csv_sync' }`.
3. Backend:
    - Select all active `stock_code` from `stock_info`.
    - For each code, create a `TaskExecutionLog` record with `status='pending'` and `target_url='/api/v1/stock/sync/csv/{code}'`.
    - Return count of created tasks.

### 3.2 任务执行 (Task Execution)
1. User selects tasks on "Task Logs" page and clicks "Execute".
2. Frontend calls `POST /api/tasks/execute { log_ids: [...] }`.
3. Backend (Async):
    - For each `log_id`:
        - Update status to `running`.
        - Parse `task_type` and `stock_code`.
        - Call corresponding Service method (e.g., `sync_csv_single`).
        - If success: Update status to `success`, set `completed_at`.
        - If error: Update status to `failed`, save `result_message`.

## 4. 前端页面 (Frontend Pages)

### 4.1 任务日志列表 (Task Execution Log List)
- Path: `/static/task-logs.html`
- Components:
    - Filters: DateRangePicker, StockCodeInput, StatusSelect (Pending/Success/Failed).
    - Actions: Execute Selected, Execute All Pending, Refresh.
    - Table: ID, Task Type, Stock Code, Status (Color coded), Result, Created At, Actions (Run).

### 4.2 导航 (Navigation)
- Update `NavBar.js` to include "Task Logs".
