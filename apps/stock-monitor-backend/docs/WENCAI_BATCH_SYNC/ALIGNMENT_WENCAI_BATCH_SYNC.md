# ALIGNMENT_WENCAI_BATCH_SYNC

## 需求理解
用户希望在“问财数据页面”的“问财批次列表”中，增加一个“同步股票到股票池”的操作按钮。
点击该按钮后，需要将当前批次的所有股票同步到股票池，并自动关联以下标签：
1. 日期标签（当前批次的日期，格式 YYYY-MM-DD）
2. 计算标签：固定为“三倍量”

## 现有系统分析
- **前端页面**: `static/wencai-data-viewer.html` 展示问财抓取批次列表。
- **后端API**: `app/api/wencai_controller.py` 提供问财相关接口。
- **服务层**: 
    - `WencaiService` 处理问财数据。
    - `MonitorService` (推测) 处理股票监控/股票池逻辑。
    - `TagManagementService` 处理标签管理。

## 疑问澄清
1. **日期标签来源**: 是使用批次的 `query_date` (查询日期) 还是 `created_at` (创建时间)？
   - *假设*: 优先使用 `query_date`，如果为空则使用 `created_at` 的日期部分。
2. **股票池定义**: “同步到股票池”具体是指添加到 `monitor_stocks` 表（监控列表）还是 `stock_info` 表（基础信息表）？
   - *假设*: 根据 `StockPoolService` 的逻辑，应该是添加到监控列表 (`monitor_stocks`)，因为“股票池”通常指监控范围。同时确保 `stock_info` 中存在该股票。
3. **重复处理**: 如果股票已经在股票池中，是否更新？
   - *假设*: 如果已存在，则更新（或忽略），重点是确保标签被添加。

## 任务范围
1. **后端开发**:
    - 新增 API 接口: `POST /api/v1/wencai/batches/{batch_id}/sync_to_pool`
    - 实现服务逻辑: 获取批次股票 -> 添加到监控池 -> 添加指定标签。
2. **前端开发**:
    - 修改 `static/wencai-data-viewer.html`，在批次列表的操作列添加按钮。
    - 实现按钮点击事件，调用后端接口并反馈结果。

## 验收标准
1. 点击“同步股票到股票池”按钮后，前端提示成功。
2. 后台数据库中，相关股票被加入监控列表。
3. 相关股票被打上对应的“日期标签”和“三倍量”标签。
