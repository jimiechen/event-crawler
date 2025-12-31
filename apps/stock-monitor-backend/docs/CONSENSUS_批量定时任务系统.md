# CONSENSUS_批量定时任务系统.md

## 最终共识
我们将改造现有的定时任务系统，使其支持基于单只股票的原子任务批量创建和执行。

## 核心变更点
1. **数据库**：新增 `task_execution_log` 表。
2. **API**：
   - 新增单只股票的操作接口 (GET 方式)。
   - 新增批量创建任务接口。
   - 新增任务管理与执行接口。
3. **前端**：
   - 改造 `timed-task.html`，按钮改为“批量创建”。
   - 增强日志列表功能，支持任务筛选与手动执行。

## 详细设计

### 1. 数据库模型 (SQLAlchemy)
```python
class TaskExecutionLog(BaseModel):
    __tablename__ = "task_execution_log"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_type: Mapped[str] = mapped_column(String(50), comment="任务类型")
    task_url: Mapped[str] = mapped_column(String(500), comment="任务URL")
    stock_code: Mapped[str] = mapped_column(String(20), comment="股票代码")
    status: Mapped[str] = mapped_column(String(20), default="pending", comment="状态: pending/running/success/failed")
    result_message: Mapped[str] = mapped_column(Text, nullable=True, comment="结果信息")
    executed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, comment="执行时间")
```

### 2. API 接口
- `GET /api/v1/stock/sync/csv/{code}`: 调用 `StockSyncService.sync_csv_to_db` (single)
- `GET /api/v1/stock/sync/tushare/{code}`: 调用 `StockSyncService.sync_tushare_increment` (single)
- `GET /api/v1/stock/sync/calculate/{code}`: 调用 `RankingService.calculate_score` (single)

- `POST /api/tasks/batch-create`: 接收 `type` (pool/incremental/calculate)，批量插入 pending 任务。
- `GET /api/tasks/list`: 查询任务日志，支持分页、筛选。
- `POST /api/tasks/execute`: 接收 `task_ids`，异步执行任务。

### 3. 前端交互
- 点击“立即从csv数据源同步” -> 调用 `/api/tasks/batch-create` (type=pool) -> 提示“已创建XX个任务，请在列表查看”。
- 列表页展示任务 -> 用户勾选 -> 点击“执行选中” -> 调用 `/api/tasks/execute`。

## 验收标准
1. 点击原来的三个按钮，不再直接执行，而是生成大量 pending 状态的任务记录。
2. 在任务列表可以看到生成的任务，且URL格式正确。
3. 可以筛选出 pending 的任务。
4. 选中任务并执行，状态变为 running 然后 success/failed。
5. 任务执行时，确实调用了底层的同步或计算逻辑。
