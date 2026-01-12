# 双模计算引擎与行动技术方案 (Dual-Mode Engine & Action Plan)

## 1. 什么是"双模计算引擎"？

这个概念是为了解决**时效性**与**计算深度**的矛盾而设计的架构：

| 模式 | **盘中实时模式 (Real-time)** | **盘后批处理模式 (Batch)** |
| :--- | :--- | :--- |
| **场景** | 交易时间 (09:30-15:00) | 收盘后 (15:30+) |
| **目标** | **快**：毫秒级发现异动 (如主力突袭、瞬间拉升) | **全**：全市场 5000+ 只股票深度复盘与排名 |
| **输入** | 前端采集的秒级快照 (Snapshot) | 完整的日线数据 (OHLCV) |
| **技术栈** | **PathwayEngine** (Python原生/内存计算) | **PathwayVectorizedEngine** (Pandas/向量化矩阵运算) |
| **动作** | 触发 SSE 弹窗告警 | 更新 `volume_anomaly_score` 长期积分 |

---

## 2. 现状评估与行动方案

**评估结论**: 
您在 `DATA_FLOW_2026.md` 中看到的"下一步"是 **必须执行** 的。
经代码核查，目前系统处于 **"有数据无大脑"** 的状态：
1.  后端 `StockService` 只负责存数据，**未调用** Pathway 引擎。
2.  Pathway 引擎缺少处理实时流数据的接口 (`process_realtime_batch`)。
3.  前端插件完全没有 SSE 监听代码，无法接收告警。

**如果不执行，明天验收只能展示"数据采集"，无法展示"智能监控"。**

---

## 3. 行动技术方案 (Action Technical Plan)

我制定了以下三阶段方案，预计耗时 15-20 分钟完成核心闭环。

### Phase 1: 后端引擎升级 (Backend Engine Upgrade)
**目标**: 让 Pathway 听得懂实时数据。
1.  **修改 `app/services/pathway_engine.py`**:
    - 新增 `process_realtime_batch(data_list)` 方法。
    - 实现轻量级计算逻辑：仅计算"量比"和"涨幅"，跳过复杂的历史形态分析以保证速度。
2.  **修改 `app/services/stock_service.py`**:
    - 在 `submit_stock_data` 中引入 `PathwayEngine`。
    - 使用 `asyncio.create_task` 异步调用引擎，**绝不阻塞** 数据入库主流程。

### Phase 2: 告警通路建设 (Alert Pipeline)
**目标**: 打通服务器到浏览器的电话线。
1.  **确认 `SSEService`**: 确保广播接口可用。
2.  **集成**: 在 `PathwayEngine` 发现异动（如量比 > 3.0）时，直接调用 `SSEService.broadcast`。

### Phase 3: 前端哨兵部署 (Frontend Sentinel)
**目标**: 浏览器收到信号即刻弹窗。
1.  **修改 `apps/chrome-extension/entrypoints/background/index.ts`**:
    - 引入 `EventSource` 连接 `/api/v1/sse/stream`。
    - 监听 `alert` 事件，调用 `chrome.notifications.create` 弹出原生通知。

---

**请确认是否立即开始执行此方案？**
(建议立即执行，以确保明天验收拥有"实时告警"这一核心亮点)
