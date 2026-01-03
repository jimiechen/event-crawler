# ALIGNMENT_TaskExecutionLogSystem

## 1. 需求分析 (Requirements Analysis)

### 1.1 原始需求 (Original Request)
- 将“定时任务页面”的几个全局按钮改为“批量创建任务”。
- 将 `stockinfo` 表中的股票列表拆分为单个任务，插入到 `task_execution_log` 表中。
- 每个任务对应一个具体的 API URL，例如：
    - `/api/v1/stock/sync/csv/{stock_code}`
    - `/api/v1/stock/sync/tushare/{stock_code}`
    - `/api/v1/stock/sync/calculate/{stock_code}`
- 定时任务或用户可以通过请求这些链接来执行任务。
- 全局导航增加 `task_execution_log` 列表页面。
- 列表页支持：
    - 筛选：时间段、股票代码、任务状态。
    - 操作：单选执行、多选执行、全选执行。
    - 状态更新：任务执行后更新状态。

### 1.2 核心目标 (Core Objectives)
1.  **细粒度任务管理**：从全局的大任务（如“同步所有股票”）转变为以“股票”为维度的原子任务。
2.  **可观测性**：通过 `task_execution_log` 记录每个股票每个任务的执行状态（待执行、执行中、成功、失败）。
3.  **灵活执行**：支持手动批量或单个触发任务，方便重试和补录。

## 2. 系统设计 (System Design)

### 2.1 数据库设计 (Database)
新增 `task_execution_log` 表：
- `id`: 主键
- `task_type`: 任务类型 (Enum: `csv_sync`, `tushare_sync`, `calculate_score`)
- `stock_code`: 股票代码
- `status`: 状态 (Enum: `pending`, `running`, `success`, `failed`)
- `target_url`: 执行的 API URL (例如 `/api/v1/stock/sync/csv/000001`)
- `result_message`: 执行结果/错误信息
- `created_at`: 创建时间
- `updated_at`: 更新时间
- `completed_at`: 完成时间

### 2.2 API 接口设计 (API Design)

#### 2.2.1 单个股票任务接口 (Single Stock Task APIs)
需要新增或确认以下接口存在：
- `POST /api/v1/stock/sync/csv/{stock_code}`: 单个股票 CSV 同步
- `POST /api/v1/stock/sync/tushare/{stock_code}`: 单个股票 Tushare 同步
- `POST /api/v1/stock/sync/calculate/{stock_code}`: 单个股票 评分计算

#### 2.2.2 任务日志管理接口 (Task Log Management APIs)
- `POST /api/tasks/batch-create`: 批量创建任务 (接收任务类型，扫描 `stock_info` 并插入 logs)
- `POST /api/tasks/execute`: 执行任务 (接收 log_ids，调用对应的 target_url 或内部 service)
- `GET /api/tasks/logs`: 查询任务日志列表 (支持筛选)

### 2.3 前端设计 (Frontend)
1.  **修改 `timed-task.html`**:
    - 将原有的 "立即同步" 等按钮行为改为调用 `batch-create` 接口。
    - 提示用户任务已创建，并引导至任务日志列表页。
2.  **新增 `task-log-list.html`**:
    - 表格展示日志。
    - 顶部筛选栏 (日期、代码、状态)。
    - 顶部/行内操作栏 (执行、批量执行)。
    - 自动刷新或手动刷新状态。
3.  **更新 `NavBar.js`**:
    - 增加 "任务日志" 入口。

## 3. 疑问与澄清 (Clarifications)
- **执行方式**: 用户提到“定时任务请求以上链接”。
    - **解释**: 系统将提供这些 HTTP 接口。目前的实现重点是“手动触发”执行（通过前端列表点击）。
    - **实现**: 前端点击“执行”时，前端可以直接请求 `target_url` (更新状态需配合)，或者请求后端 `execute` 接口，由后端代理请求或直接调用 Service 并更新状态。
    - **决策**: 采用后端 `execute` 接口统一处理。前端提交 log_ids，后端查找对应的 stock_code 和 type，调用 Service 执行逻辑，并更新 DB 状态。这样更安全且状态一致性更好。虽然 url 存在 log 中，但仅作为参考或外部调用使用。

## 4. 任务拆分 (Task Breakdown)
1.  **Backend Models**: 创建 `TaskExecutionLog` 模型。
2.  **Backend Services**:
    - 实现单个股票的 CSV/Tushare/Calculate 逻辑 (复用现有 Service，增加单股方法)。
    - 实现 TaskLogService (创建日志、更新状态、执行任务)。
3.  **Backend APIs**:
    - 实现 `/api/v1/stock/sync/.../{stock_code}` 接口。
    - 实现 `/api/tasks/logs` 及其相关接口。
4.  **Frontend**:
    - 创建 `task-log-list.html`。
    - 修改 `timed-task.html`。
    - 更新 `NavBar.js`。

