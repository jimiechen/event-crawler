# TASK_批量定时任务系统.md

## 任务 1: 数据库与模型 (Database)
**输入契约**: DESIGN文档
**输出契约**: `TaskExecutionLog` 模型代码, 数据库表创建脚本
**验收标准**: 数据库中存在 `task_execution_log` 表，字段正确。

## 任务 2: 原子 API 接口 (Atomic APIs)
**输入契约**: 现有 Service 代码
**输出契约**:
- `GET /api/v1/stock/sync/csv/{code}`
- `GET /api/v1/stock/sync/tushare/{code}`
- `GET /api/v1/stock/sync/calculate/{code}`
**验收标准**: 调用接口可成功对单只股票进行操作。

## 任务 3: 任务管理 API (Task Management APIs)
**输入契约**: 任务 1 完成
**输出契约**:
- `POST /api/tasks/batch-create`
- `GET /api/tasks/logs`
- `POST /api/tasks/execute`
**验收标准**: 可以创建任务记录，可以查询，可以执行并更新状态。

## 任务 4: 前端开发 (Frontend)
**输入契约**: 任务 2, 3 完成
**输出契约**:
- 更新 `static/timed-task.html`
**验收标准**: 页面能显示日志，筛选生效，能执行任务。
