# DESIGN_WENCAI_BATCH_SYNC

## 系统架构

### 1. API 层
在 `app/api/wencai_controller.py` 中新增接口：
- `POST /api/v1/wencai/batches/{batch_id}/sync_to_pool`
    - 输入: `batch_id` (路径参数)
    - 输出: 同步结果 (成功数量, 失败数量)

### 2. 服务层
在 `app/services/wencai_service.py` 中新增方法 `sync_batch_stocks_to_pool`:
- 逻辑:
    1. 获取批次详情，提取日期 (query_date 或 created_at)。
    2. 获取该批次下的所有去重股票记录。
    3. 遍历股票:
        a. 调用 `MonitorService.add_monitor` 将股票加入监控池。
        b. 准备标签列表:
            - 日期标签: 批次日期 (e.g., "2023-10-27")，类型为 `date`
            - 计算标签: "三倍量"，类型为 `calculation` (或通用类型)
        c. 调用 `TagManagementService.add_tags_to_stock` 添加标签。
    4. 记录并返回统计结果。

### 3. 前端层
修改 `static/wencai-data-viewer.html`:
- 在 `renderBatches` 方法生成的表格中，"操作"列增加按钮。
- 按钮样式: 蓝色或绿色，带有同步图标。
- 绑定点击事件 `syncBatchToPool(batchId)`。
- 实现 `syncBatchToPool` 方法:
    - 发送 API 请求。
    - 显示 Loading 状态。
    - 成功后提示用户并刷新(可选)。

## 接口契约

### 请求
```http
POST /api/v1/wencai/batches/{batch_id}/sync_to_pool
Content-Type: application/json
```

### 响应
```json
{
  "success": true,
  "data": {
    "total": 100,
    "success": 100,
    "failed": 0,
    "errors": []
  },
  "message": "同步成功，共同步 100 只股票"
}
```

## 依赖关系
- `WencaiService` 依赖 `MonitorService` 和 `TagManagementService`。
- 需要确保 `MonitorService` 和 `TagManagementService` 已正确初始化并可用。

## 异常处理
- 批次不存在: 返回 404。
- 数据库错误: 捕获并记录日志，返回 500。
- 单个股票同步失败: 记录错误但不中断整体流程 (Best Effort)。
