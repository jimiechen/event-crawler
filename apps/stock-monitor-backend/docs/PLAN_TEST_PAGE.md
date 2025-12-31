# 量化规则测试页面开发计划

## 1. 概述
本计划旨在开发一个专门的测试页面，用于验证量化策略规则的准确性。通过构造模拟的市场数据消息，实时调用后端策略引擎，验证告警逻辑是否符合预期。

## 2. 功能需求
### 2.1 消息构造
- **手动输入**: 提供表单输入股票代码、当前价格、成交量、涨幅、量比等关键字段。
- **自动生成**: 一键生成随机的市场数据，支持设置生成数量（如批量生成10条）。
- **模板管理**: 保存当前输入为模板，或加载预设的典型场景模板（如"放量上涨"、"缩量下跌"）。

### 2.2 页面展示
- **消息列表**: 以表格形式展示构造的消息数据。
- **筛选与搜索**: 支持按股票代码搜索，按是否触发告警筛选。
- **分页**: 支持每页显示10/20/50条数据。

### 2.3 测试验证
- **规则执行**: 对列表中的消息应用当前的量化策略（StrategyService）。
- **结果对比**: 显示策略计算结果（是否触发、触发原因）。
- **统计**: 显示总测试数、触发数、未触发数。

### 2.4 其他
- **操作日志**: 记录用户的测试操作（生成数据、验证规则等）。
- **响应式设计**: 适配桌面和移动端展示。

## 3. 技术架构
### 3.1 后端 (FastAPI)
- **Controller**: `app/api/test_tool_controller.py`
- **Schema**: `app/api/schemas/test_tool.py` (定义Request/Response模型)
- **Endpoints**:
    - `POST /api/v1/test-tool/generate`: 生成模拟数据
    - `POST /api/v1/test-tool/validate`: 验证单条或多条数据
    - `GET /api/v1/test-tool/templates`: 获取模板列表
    - `POST /api/v1/test-tool/templates`: 保存模板
    - `GET /api/v1/test-tool/logs`: 获取操作日志

### 3.2 前端 (HTML/JS)
- **文件**: `static/test-tool.html`
- **技术栈**: 
    - Vue.js (CDN引入，用于数据绑定和交互)
    - Tailwind CSS (CDN引入，用于样式)
    - Axios (CDN引入，用于API请求)

## 4. 数据结构
### 4.1 模拟消息模型 (MockStockData)
```json
{
  "code": "300059",
  "name": "东方财富",
  "price": 15.5,
  "volume": 1000000,
  "amount": 15500000,
  "change_percent": 3.5,
  "volume_ratio": 3.2,
  "timestamp": "2023-10-27 10:30:00"
}
```

### 4.2 验证结果模型 (ValidationResult)
```json
{
  "is_triggered": true,
  "trigger_reason": "量比(3.2) > 3.0, 涨幅(3.5%) > 3.0%",
  "strategy_config": {
    "vol_ratio_threshold": 3.0,
    "price_change_threshold": 3.0
  }
}
```

## 5. 开发步骤
1. **定义Schema**: 创建 `app/api/schemas.py` 中的相关模型 (或新建 `app/api/schemas/test_tool.py`).
2. **实现Controller**: 创建 `app/api/test_tool_controller.py`，实现生成、验证逻辑。
3. **注册路由**: 在 `app/main.py` 中注册新的Router。
4. **开发前端**: 创建 `static/test-tool.html`，实现界面交互。
5. **联调验证**: 启动服务，测试各项功能。
