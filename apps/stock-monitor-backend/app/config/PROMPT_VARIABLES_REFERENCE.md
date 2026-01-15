# A 股提示词变量参考文档 (A-Share Prompt Variables Reference)

本文档定义了在 A 股提示词模板中可用的所有变量。

## 1. 基础变量 (Basic Variables)

| 变量名 | 描述 | 示例 |
|--------|------|------|
| `{trading_environment}` | 交易环境描述 | "Market is open. T+1 trading rules apply." |
| `{available_cash}` | 可用资金（格式化人民币） | "1,000,000.00" |
| `{total_account_value}` | 总账户价值 | "1,250,000.00" |
| `{market_prices}` | 当前股票价格列表 | "600519: 1800.00 (+1.2%), 000001: 10.50 (-0.5%)" |
| `{news_section}` | 最新 A 股新闻摘要 | "央行降准0.5个百分点..." |
| `{output_format}` | 输出格式定义 | (见 prompt_templates.py 中的 OUTPUT_FORMAT_JSON) |

## 2. 会话变量 (Session Variables)

| 变量名 | 描述 | 示例 |
|--------|------|------|
| `{runtime_minutes}` | 交易运行分钟数 | 240 |
| `{current_time_utc}` | 当前 UTC 时间 | "2024-01-15T02:30:00Z" |
| `{total_return_percent}` | 总收益率百分比 | 15.5 |

## 3. 投资组合变量 (Portfolio Variables)

| 变量名 | 描述 | 示例 |
|--------|------|------|
| `{holdings_detail}` | 持仓详情 | "600519: 100 shares @ 1700.00 (Value: 180000.00)" |
| `{sampling_data}` | 历史价格采样数据 | (用于上下文构建) |

## 4. A 股专用变量 (A-Share Specific Variables)

| 变量名 | 描述 | 参数说明 |
|--------|------|----------|
| `{STOCKCODE_market_data}` | 个股市场数据 | 价格、涨跌幅、成交量、换手率 |
| `{STOCKCODE_klines_PERIOD}(COUNT)` | K 线数据 | PERIOD: 1d, 1w, 1m; COUNT: 数量 |
| `{STOCKCODE_MA_PERIOD}` | 移动平均线 | PERIOD: 5, 10, 20, 60 |
| `{STOCKCODE_EMA_PERIOD}` | 指数移动平均线 | PERIOD: 20, 50 |
| `{STOCKCODE_RSI14_PERIOD}` | RSI(14) 指标 | PERIOD: 1d, 60m |
| `{STOCKCODE_MACD_PERIOD}` | MACD 指标 | PERIOD: 1d, 60m |
| `{STOCKCODE_KDJ_PERIOD}` | KDJ 指标 | PERIOD: 1d, 60m |
| `{STOCKCODE_BOLL_PERIOD}` | 布林带指标 | PERIOD: 1d, 60m |
| `{STOCKCODE_VOL_PERIOD}` | 成交量指标 | PERIOD: 1d, 60m |

示例:
- `{600519_klines_1d}(20)`: 贵州茅台最近 20 日 K 线
- `{000001_MA_5}`: 平安银行 5 日均线

## 5. 形态识别变量 (Pattern Recognition Variables)

| 变量名 | 描述 | 示例 |
|--------|------|------|
| `{STOCKCODE_patterns}` | 缠论量价形态 | "底分型, 阳包阴" |

## 6. 量价关系变量 (Volume-Price Analysis Variables)

| 变量名 | 描述 | 示例 |
|--------|------|------|
| `{STOCKCODE_volume_status}` | 成交量状态 | "放量", "缩量", "平量" |
| `{STOCKCODE_price_status}` | 价格状态 | "上涨", "下跌", "平盘" |
| `{STOCKCODE_action_hint}` | 操作建议 | "加仓", "减仓", "卖出", "等待" |

## 7. 市场状态分类变量 (Market Regime Variables)

| 变量名 | 描述 | 示例 |
|--------|------|------|
| `{market_state}` | A 股市场状态 | "牛市", "熊市", "震荡市", "突破市", "回调市", "反转市", "噪音市" |

## 8. 触发上下文变量 (Trigger Context Variables)

| 变量名 | 描述 | 示例 |
|--------|------|------|
| `{trigger_context}` | 触发上下文 | "Signal triggered: 600519 RSI oversold" |
