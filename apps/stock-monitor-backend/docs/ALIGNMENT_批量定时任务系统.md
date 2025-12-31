# ALIGNMENT_批量定时任务系统.md

## 需求理解
用户希望将现有的"定时任务"页面改造为"批量创建任务"系统。不再是点击按钮直接执行所有股票的同步或计算，而是点击按钮后，为系统中的每只股票生成一条待执行的任务记录。这些任务记录可以在一个新的列表中查看、筛选和执行。

## 核心需求
1. **任务原子化**：
   - 将原来的批量操作拆分为针对单只股票的原子任务。
   - 涉及三种任务类型：
     - CSV同步: `http://localhost:8000/api/v1/stock/sync/csv/{stock_code}`
     - Tushare同步: `http://localhost:8000/api/v1/stock/sync/tushare/{stock_code}`
     - 评分计算: `http://localhost:8000/api/v1/stock/sync/calculate/{stock_code}`

2. **批量创建任务**：
   - 改造现有按钮功能，点击后遍历 `stockinfo` 表，为每只股票生成上述对应的任务URL，并保存到 `task_execution_log` 表中。

3. **任务管理界面**：
   - 新增 `task_execution_log` 列表页面（或Tab）。
   - 支持筛选：时间段、股票代码、任务状态。
   - 支持操作：多选执行、单选执行、全选执行。
   - 执行任务即请求对应的URL，并更新任务状态。

## 疑问澄清
1. **执行方式**：用户提到“请求以上链接”，这意味着后端需要提供这些 GET 接口（目前是 POST 且是批量的）。我们需要新增这些 GET 接口。
2. **并发控制**：批量执行时是否需要控制并发数？（假设前端循环调用或者后端批量处理，用户描述中提到“支持多选执行”，通常意味着前端发起请求通知后端执行这些任务，或者前端逐个请求。考虑到任务量可能较大（几千只股票），前端逐个请求可能会导致浏览器卡顿或请求积压。建议后端提供一个“批量执行”接口，接收任务ID列表，然后在后台（可能是异步）执行。）
   - **修正**：用户说“定时任务请求以上链接”，这可能意味着用户希望有一个调度器去请求，或者用户手动点击执行时，系统去请求。根据“操作列可以支持多选执行”，可能是用户手动触发。
   - **决策**：后端提供一个“执行任务”的接口，接收任务ID，后端去请求那个URL（内部调用或HTTP请求）。或者，前端直接请求那个URL？
   - 如果前端直接请求URL，那么状态更新怎么做？URL的响应应该包含状态更新逻辑，或者前端请求完后更新状态。
   - **更合理的方案**：
     - 前端点击“执行”，调用后端 `/api/tasks/execute` 接口，传入任务ID。
     - 后端 `/api/tasks/execute` 逻辑：
       1. 更新状态为 "running"。
       2. 解析任务URL，调用对应的 Service 方法（而不是发起 HTTP 请求，这样效率更高且不需要网络开销）。或者严格按照用户描述“请求以上链接”，那就是发起 HTTP 请求。考虑到系统解耦和用户明确给出了URL格式，我们支持通过 HTTP 请求执行，这样也方便测试和扩展。
       3. 根据请求结果更新状态为 "success" or "failed"。

3. **任务状态**：pending (待执行), running (执行中), success (成功), failed (失败)。

## 技术方案
### 数据库设计
新增 `task_execution_log` 表：
- `id`: 主键
- `task_type`: 任务类型 (csv_sync, tushare_sync, calculate)
- `task_url`: 执行的URL
- `stock_code`: 股票代码
- `status`: 状态 (pending, running, success, failed)
- `result_message`: 结果信息
- `created_at`: 创建时间
- `updated_at`: 更新时间
- `executed_at`: 执行时间

### 接口设计
1. **GET /api/v1/stock/sync/csv/{code}**: 单只股票CSV同步
2. **GET /api/v1/stock/sync/tushare/{code}**: 单只股票Tushare同步
3. **GET /api/v1/stock/sync/calculate/{code}**: 单只股票评分计算

4. **POST /api/tasks/batch-create**: 批量创建任务
   - 参数: `type` (pool/incremental/calculate)
   - 逻辑: 遍历 `stock_info`，插入 `task_execution_log`。

5. **GET /api/tasks/logs**: 获取任务列表 (支持筛选)

6. **POST /api/tasks/execute**: 执行任务
   - 参数: `task_ids` (List[int])
   - 逻辑: 遍历任务ID，异步执行（请求URL），更新状态。

### 前端改造
- 修改 `timed-task.html`。
- 将“手动触发任务”区的按钮改为调用 `/api/tasks/batch-create`。
- 新增“任务执行日志”Tab（或复用现有Logs Tab但增强功能），显示 `task_execution_log` 数据。
- 增加筛选栏和执行按钮。
