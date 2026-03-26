# 定时任务错误分析报告

## 1. 404 Not Found 错误

**错误信息**:
```
2026-01-16 15:30:57.345 | ERROR | ... API调用失败: /api/v1/ranking/calculate/2026-01-16, 错误: Client error '404 Not Found'
```

**代码位置**:
- 调用方: `app/services/scheduler_service.py` (Line 356)
- 定义方: `app/api/ranking_controller.py` (Line 19)

**原因分析**:
调度服务中调用的 API 路径为 `/api/v1/ranking/calculate/{date}` (单数 ranking)，而控制器中定义的路由前缀为 `/api/v1/rankings` (复数 rankings)。导致路径不匹配，返回 404。

**解决方案**:
修改 `app/services/scheduler_service.py` 中的 API 调用路径，将其修正为 `/api/v1/rankings/calculate/{date}`。

---

## 2. AttributeError: 'StockInfo' object has no attribute 'industry'

**错误信息**:
```
Error getting stock context for 000056: 'StockInfo' object has no attribute 'industry'
```

**代码位置**:
- `app/adapters/ashare_adapter.py` (Line 33)
- `app/models/stock.py` (StockInfo 模型定义)

**原因分析**:
`AShareAdapter` 试图访问 `StockInfo` 模型的 `industry` 字段，但 `StockInfo` 模型定义中并未包含该字段。目前模型中仅包含 `code`, `name`, `market`, `source` 等字段。

**解决方案**:
1. **短期修复**: 修改 `app/adapters/ashare_adapter.py`，移除对 `industry` 的访问，或使用默认值 (e.g., `"Unknown"`)，避免报错。
2. **长期修复**: 在 `StockInfo` 模型及数据库表中添加 `industry` 字段，并在数据同步流程中补充行业数据的抓取。

---

## 3. Data Insufficiency Warnings (数据不足警告)

**错误信息**:
```
WARNING | ... 股票 603608 数据不足，跳过分析
```

**代码位置**:
- `app/services/volume_analysis_service.py` (Line 496-497)

**原因分析**:
分析服务在执行 `_analyze_stock_impl` 时，会查询最近 400 天的日线数据。如果查询到的数据条数少于 2 条，则会跳过分析并打印警告。这通常发生在：
1. 新上市股票，数据尚未同步。
2. 数据同步任务失败，导致数据库中无该股票的历史数据。
3. 停牌股票或已退市股票。

**解决方案**:
- 检查数据同步任务 (`StockDataManager.sync_stock_daily`) 是否正常运行。
- 确认这些股票是否为活跃股票 (`is_active=True`)。如果是无效股票，应将其标记为非活跃。

---

## 4. SQL Syntax Error (排名计算失败)

**错误信息**:
```
(pymysql.err.ProgrammingError) (1064, "You have an error in your SQL syntax ... near '(ORDER BY total_score DESC) AS ranking ...'")
```

**代码位置**:
- `app/services/daily_acceptance_service.py` (Line 311)

**原因分析**:
代码中使用了 `ROW_NUMBER() OVER (ORDER BY ...)` 窗口函数。
- 如果数据库是 MySQL 5.7 或更低版本，不支持窗口函数，会导致此语法错误。
- 即使是 MySQL 8.0+，如果 SQLAlchemy 的 `text()` 使用方式或 SQL 模式配置有误，也可能导致问题。但最常见原因是数据库版本过低。

**解决方案**:
- **确认数据库版本**: 检查当前使用的 MySQL 版本。
- **兼容性修复**: 如果无法升级数据库，需改写 SQL，使用变量方式实现排名，或者在 Python 代码中查询出所有数据后进行排序和排名（数据量不大时可行）。

---

## 5. UnboundLocalError: local variable 'processed_count' referenced before assignment

**错误信息**:
```
cannot access local variable 'processed_count' where it is not associated with a value
```

**代码位置**:
- `app/services/wencai_service.py` (Line 1352, 1399 等)

**原因分析**:
变量 `processed_count` 的初始化 (`processed_count = 0`) 位于 `if tag_ids:` 的 `else` 分支对应的逻辑块中（或因缩进问题导致作用域受限）。
当 `tag_ids` 为空（即 "没有需要关联的标签"）时，代码跳过了初始化逻辑，直接执行后续的日志记录或错误处理逻辑，导致访问未定义的 `processed_count`。

**解决方案**:
将 `processed_count = 0` 的初始化代码移动到循环或条件判断之前（例如在 `stocks = result.fetchall()` 之后立即初始化），确保无论是否有关联标签，该变量都已被定义。
