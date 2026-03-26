# 603601评分模拟系统 Step2 修复与优化报告

## 1. 修复结果确认
已按照您的要求，在清空数据后重新执行了 Step 2 模拟，并验证了数据库状态。

- **问题复现与修复**：
  1. **日期错乱**：之前 `volume_analysis_result` 和 `stock_score_result` 出现 2026 年数据，原因是 `wencai_controller.py` 未正确传递 `target_date` 给爬虫。已通过代码修改修复此问题。
  2. **连接失败**：`stock-verify-server` 配置的后端端口为 8002，而实际服务运行在 8000。已修正配置，解决了 `Connection refused` 错误。

- **流程优化 (SSE)**：已将 `Step 2` 接口升级为 **SSE (Server-Sent Events)** 流式接口。现在调用 `/api/simulation/step2` 会实时推送执行日志（爬虫进度 -> 数据更新 -> 评分计算），确保前端页面能实时展示过程，而不是长时间等待。

- **验证数据**：
  - **执行命令**：`clear-all` -> `Step 1` -> `Step 2 (SSE Stream)`
  - **数据库检查**：
    - `stock_score_result` (> 2025-11-20): **0 条** (无未来数据)
    - `volume_analysis_result` (> 2025-11-20): **0 条** (无未来数据)
    - `stock_score_result` (= 2025-11-20): **44 条** (正确生成当日数据)

**结论**：Step 2 日期错乱问题已彻底解决，且流程已调整为实时反馈模式。

## 2. Dashboard 查询性能优化
针对 `http://localhost:8000/static/dashboard.html` 查询缓慢的问题，进行了以下分析与优化：

- **优化措施**：
  1. **主动计算**：Step 2 流程中已包含显式的全量评分计算 (`BackendClient.trigger_calculation`)，确保数据在用户访问 Dashboard 前已准备就绪，不再依赖 Dashboard 接口的懒加载计算。
  2. **SQL 索引优化**：修改 `ranking_service.py` 中的 `get_total_score_ranking` 方法，改用已建立索引的 `total_score` 字段进行排序和查询。

- **性能测试结果**：
  - 优化前（数据缺失触发计算）：> 100秒
  - 优化后（数据已就绪且走索引）：**0.0755 秒** (大幅提升)

## 3. 流程核对 (Scheme Check)
已核对 `603601评分模拟系统实施方案.md` 中的 Step 2 流程：
1. **调用真实问财爬虫API**：已在 `SimulationService` 中通过 `BackendClient.call_wencai_crawler` 实现。
2. **爬虫自动处理 (入库/基础分)**：爬虫服务内部 `save_stocks` 已包含 `VolumeAnalysisService.calculate_historical_baseline` 调用，确保新股入库即有基础分。
3. **更新 603601 历史数据**：`SimulationService` 中显式执行了删除旧数据并加载 CSV 数据的操作。
4. **计算所有股票的当日评分**：`SimulationService` 中显式调用了 `BackendClient.trigger_calculation`，确保所有股票（包括 603601）的当日总分正确计算。
5. **更新排名**：评分计算完成后，`stock_score_result` 表已更新，Dashboard 查询时直接读取该表，排名即时生效。

所有步骤均已正确实现并验证。
