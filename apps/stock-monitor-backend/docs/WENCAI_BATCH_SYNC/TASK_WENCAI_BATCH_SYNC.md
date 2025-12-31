# TASK_WENCAI_BATCH_SYNC

## 任务1：后端服务层实现
**输入契约**: `batch_id`
**输出契约**: 同步统计结果
**文件**: `app/services/wencai_service.py`
**步骤**:
1. 引入 `MonitorService`。
2. 实现 `sync_batch_stocks_to_pool` 方法。
3. 获取批次日期和股票列表。
4. 循环调用 `monitor_service.add_monitor` 和 `tag_mgmt_service.add_tags_to_stock`。
5. 标签需包含: 日期标签(type='date'), "三倍量"(type='calculation')。

## 任务2：后端API实现
**输入契约**: HTTP POST 请求
**输出契约**: JSON 响应
**文件**: `app/api/wencai_controller.py`
**步骤**:
1. 定义新路由 `@router.post("/batches/{batch_id}/sync_to_pool")`。
2. 调用 Service 层方法。
3. 处理异常和响应格式。

## 任务3：前端页面修改
**输入契约**: 用户点击事件
**输出契约**: UI 反馈
**文件**: `static/wencai-data-viewer.html`
**步骤**:
1. 在批次列表表格的操作列添加“同步到股票池”按钮。
2. 实现 `syncBatchToPool` JS 函数。
3. 添加简单的 Loading 和 Toast 提示。

## 依赖关系
任务1 -> 任务2 -> 任务3
