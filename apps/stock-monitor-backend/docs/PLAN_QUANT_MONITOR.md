# 量化股票监听告警平台 - 技术方案与实现计划

## 1. 项目背景
基于现有同花顺自选股监控和问财数据解析功能，构建一个自动化的量化监控告警平台。核心目标是实现基于量价关系的实时监控告警，以及基于问财数据的股票池自动维护。

## 2. 系统架构设计

### 2.1 总体架构
采用模块化设计，主要包含以下子系统：
- **数据采集层 (Data Layer)**:
  - `TongHuaShunMCPClient`: 负责实时行情抓取（同花顺）。
  - `WencaiService`: 负责历史/分析数据抓取（问财）。
- **策略引擎 (Strategy Engine)**:
  - `StrategyService`: 核心组件，负责实时计算量价指标，判定是否触发告警。
  - 支持策略插件化，配置化（如量比阈值、价格阈值）。
- **股票池管理 (Pool Manager)**:
  - `StockPoolService`: 基于问财数据每日自动更新监控列表（增/删/排序）。
- **告警系统 (Alert System)**:
  - `NotificationService`: 统一通知接口，支持桌面弹窗(macOS)、邮件、日志。
- **任务调度 (Scheduler)**:
  - 负责定时任务（每日问财抓取、盘后分析、数据清理）。

### 2.2 核心模块设计

#### A. 量价分析策略模块
*   **输入**: 实时股价(Price)、实时成交量(Volume)、历史均量(AvgVolume)。
*   **逻辑**:
    *   实时计算量比 (Volume Ratio) = 当前成交量 / (过去5日均量 / 240 * 当前已开盘分钟数)。
    *   或者简化版: 当前成交量 > 3 * 历史同时段成交量。
    *   触发条件: `CurrentPrice > ThresholdPrice` AND `VolumeCondition`.
    *   "3倍成交量对应的价格阈值"理解为: 动态计算一个压力位，当放量突破该压力位时告警。
*   **输出**: 告警事件 (AlertEvent)。

#### B. 问财数据处理模块
*   **功能**:
    1.  每日定时抓取问财数据（如"量比大于3", "突破均线"等条件）。
    2.  对抓取结果进行标签分类（如"放量突破", "底部反转"）。
    3.  **动态维护监控池**:
        *   **入池**: 满足核心策略（如量能爆发）的股票自动加入 `monitor_list`，设置高优先级。
        *   **出池**: 连续N天无表现或触发止损条件的股票移除或降级。
        *   **优先级**: 根据量比、涨幅等指标动态调整 `priority`。

#### C. 告警模块
*   **多级告警**:
    *   **Level 1 (High)**: 桌面弹窗 + 声音 (macOS `osascript`)。
    *   **Level 2 (Medium)**: 邮件通知。
    *   **Level 3 (Low)**: 仅记录日志。
*   **频控**: 同一只股票在一定时间内（如5分钟）不重复告警。

## 3. 数据模型变更
*   **StockStrategyConfig**: 存储单股的策略参数（如特有的阈值）。
*   **AlertLog**: 记录告警历史。
*   **StrategyBacktestResult**: 回测结果记录。

## 4. 实现计划

### 阶段一：基础架构与策略引擎 (Days 1-2)
1.  **重构监控循环**: 将现有的 `monitor_stock_data` 改造为支持回调的事件驱动模式。
2.  **实现 `NotificationService`**: 支持 macOS 桌面通知。
3.  **实现 `StrategyService`**:
    *   定义 `BaseStrategy` 接口。
    *   实现 `VolumePriceStrategy` (量价策略)。

### 阶段二：问财自动化与股票池管理 (Days 3-4)
1.  **完善 `WencaiService`**: 增加自动入库和清洗逻辑。
2.  **实现 `StockPoolService`**:
    *   编写规则：根据问财数据更新 `monitor_list`。
    *   实现自动清洗：移除不再符合条件的股票。

### 阶段三：系统集成与调度 (Day 5)
1.  **集成 APScheduler**: 管理每日定时任务。
2.  **配置化**: 将阈值、邮箱配置等移入 `SystemConfig` 或 `.env`。
3.  **异常恢复**: 增加 MCP Client 的断线重连和异常重启机制。

### 阶段四：测试与文档 (Day 6-7)
1.  **回测**: 编写脚本，使用历史 `StockData` 跑策略，验证触发率。
2.  **文档**: 编写部署文档、策略说明文档。

## 5. 关键技术点
*   **macOS 通知**: 使用 `osascript -e 'display notification "内容" with title "标题"'`。
*   **实时性**: 确保 MCP Client 的轮询间隔在可接受范围 (如 3-5秒)。
*   **稳定性**: 使用 `supervisord` 或 Docker restart policy 保证后台进程常驻。

## 6. 交付物清单
1.  源代码 (Python FastAPI + SQLAlchemy)。
2.  `DEPLOY.md` (部署文档)。
3.  `STRATEGY.md` (策略说明与配置)。
4.  `requirements.txt` (依赖更新)。
