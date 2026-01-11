# Kliner 训练模块 (kliner_trainer)

## 1. 项目概览
`kliner` 是一个基于 Flutter 开发的股票 K 线训练工具，旨在帮助用户通过模拟交易（盲测模式）提升看盘和交易能力。该模块包含 K 线图表展示、交易操作记录、资金账户管理以及日历复盘等核心功能。

## 2. 目录结构
```
kliner_trainer/
├── lib/
│   ├── controllers/
│   │   └── training_controller.dart  # 核心控制器 (状态管理、业务逻辑)
│   ├── models/
│   │   ├── stock_data.dart           # K线数据模型
│   │   ├── operation_record.dart     # 操作记录模型
│   │   ├── account_snapshot.dart     # 账户快照模型
│   │   ├── blind_test_config.dart    # 盲测配置
│   │   └── blind_test_session.dart   # 训练会话状态
│   ├── pages/
│   │   └── training_page.dart        # 主页面
│   ├── services/
│   │   ├── csv_data_service.dart     # CSV数据加载服务
│   │   ├── indicator_calculator.dart # 技术指标计算
│   │   └── storage_service.dart      # 本地持久化服务
│   ├── widgets/
│   │   ├── calendar_widget.dart      # 日历组件 (日期选择与操作可视化)
│   │   ├── desktop_operation_panel.dart # 桌面端操作面板 (显示每日/所有操作)
│   │   ├── kline_chart_widget.dart   # K线图表组件
│   │   ├── operation_panel_widget.dart # 移动端操作面板
│   │   ├── desktop_layout_widget.dart # 桌面端布局容器
│   │   ├── overlays/                 # 浮层组件 (十字光标、提示框)
│   │   └── painters/                 # 自定义绘制 (K线、成交量、均线)
│   └── main.dart                     # 入口文件
└── assets/
    └── csv_data/                     # 股票历史数据 (CSV格式)
```

## 3. 数据模型详解

### 3.1 StockData (K线数据)
| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `code` | String | 股票代码 |
| `date` | DateTime | 交易日期 |
| `open` | double | 开盘价 |
| `high` | double | 最高价 |
| `low` | double | 最低价 |
| `close` | double | 收盘价 |
| `volume` | double | 成交量 |
| `amount` | double | 成交额 |
| `changePercent` | double | 涨跌幅 |
| `isBullish` | bool | 是否阳线 (getter) |

### 3.2 OperationRecord (操作记录)
| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | String | 唯一标识 (UUID) |
| `timestamp` | DateTime | 操作时间 |
| `type` | OperationType | 操作类型 (buy, sell, hold) |
| `price` | double | 操作价格 |
| `quantity` | int | 成交股数 |
| `realizedProfit` | double | 实现盈亏 (仅卖出时) |
| `profit` | double? | 浮动盈亏 |
| `reason` | String | 操作理由 |

## 4. 核心逻辑与状态管理

本项目使用 **GetX** 进行状态管理，核心逻辑位于 `TrainingController`。

### 4.1 状态联动机制
*   **全局状态**：
    *   `selectedDate` (Rx<DateTime?>): 当前选中的日期。
    *   `allOperations` (RxList): 所有历史操作记录。
    *   `dailyOperations` (RxList): 选中日期的操作记录子集。
*   **联动逻辑**：
    *   在 `onInit` 中通过 `ever(selectedDate, ...)` 监听日期变化。
    *   当 `selectedDate` 变更时，自动过滤 `allOperations` 并更新 `dailyOperations`。
    *   UI 组件 (如 `DesktopOperationPanel`) 使用 `Obx` 监听 `dailyOperations` 实现自动刷新。

### 4.2 训练流程
1.  **初始化**：加载 CSV 数据，生成 `BlindTestSession`。
2.  **交易**：用户点击买/卖/观望，生成 `OperationRecord` 并存入 `allOperations`。
3.  **推进**：点击“下一天”，更新 `currentSession` 数据，追加 K 线。
4.  **复盘**：通过日历点击特定日期，查看当天的操作记录和 K 线状态。

## 5. 开发规范 (Rules)

1.  **代码风格**：
    *   严格遵守 Dart 官方规范。
    *   **注释必须使用中文**。
    *   单文件行数不超过 400 行，超过需拆分。
2.  **编译检查**：
    *   每次修改后必须运行 `./skill-template/gen/flutter/verify_project.sh`。
    *   严禁提交存在 `flutter analyze` 错误的代码。
3.  **状态管理**：
    *   UI 与逻辑分离，逻辑放入 Controller。
    *   使用 `Obx` 局部刷新，避免全局重建。
4.  **空安全**：
    *   严格处理 `null` 值，避免运行时异常。
    *   使用 `?` 和 `!` 操作符时需确保逻辑正确。

## 6. 实现指南：每日操作数据源对接

### 6.1 需求背景
在日历组件上点击日期时，需在操作面板显示当天的交易记录，实现“所见即所得”的复盘效果。

### 6.2 实现步骤
1.  **Controller 层改造**：
    *   在 `TrainingController` 中添加 `dailyOperations` 响应式列表。
    *   添加 `onDateSelected(DateTime? date)` 方法。
    *   配置监听器：`ever(selectedDate, (_) => _updateDailyOperations())`。

2.  **日历组件 (`CalendarWidget`) 对接**：
    *   绑定点击事件：`onTap` 调用 `controller.onDateSelected(date)`。
    *   视觉反馈：选中日期高亮显示 (边框/背景色)。

3.  **操作面板 (`DesktopOperationPanel`) 对接**：
    *   标题动态化：使用 `Obx` 显示 "X月X日操作" 或 "所有操作"。
    *   列表数据源：根据 `selectedDate` 是否为空，切换显示 `dailyOperations` 或 `allOperations`。
    *   布局优化：使用 `Wrap` 替代 `Row` 解决小屏幕溢出问题。

4.  **移动端适配**：
    *   在 `OperationPanelWidget` 中复用相同的 `Obx` 逻辑。
    *   确保移动端布局兼容性。

### 6.3 验证方法
*   运行应用，点击日历上的日期。
*   确认操作面板列表立即刷新为该日期的记录。
*   确认再次点击或其他交互能清除选中状态（如需）。
*   执行编译检查确保无报错。
