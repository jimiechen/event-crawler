# Hyper-Alpha-Arena 项目分析与 A股适配计划

## 对话概览

本文档归档了关于 Hyper-Alpha-Arena 项目分析、与 stock-monitor-backend 项目的对比评估，以及 A 股适配的完整实施计划。

---

## 第一部分：项目评估与合并可行性分析

### 1.1 项目概述

**Hyper-Alpha-Arena-main**：
- AI 驱动加密货币永续合约交易平台
- 使用 LLM 模型（GPT-5、Claude、Deepseek）进行实时交易决策
- 15 秒级实时市场流信号监控（CVD、Taker Ratio、OI Delta）
- 市场状态分类系统（7 种 Regime 类型）
- 信号池系统（边缘触发逻辑）
- React + TypeScript 前端，30+ 可复用 UI 组件

**stock-monitor-backend**：
- A 股量价形态分析系统
- 缠论量价形态识别（阳包阴、底分型、顶分型等）
- 量价关系分析（放量/缩量/平量）
- 股票池管理（Top 20 核心，Top 100 观察）
- Vue 3 + CDN 前端，传统技术栈

### 1.2 算法差异对比

| 维度 | Hyper-Alpha-Arena | stock-monitor-backend |
|------|------------------|---------------------|
| **市场对象** | 加密货币（BTC、ETH 等） | A 股（6000+ 只） |
| **数据频率** | 15 秒级实时数据 | 日 K 线数据 |
| **算法体系** | 高频市场流信号（CVD、Taker Ratio、OI Delta） | 传统技术分析（形态识别、量价关系） |
| **决策机制** | AI 驱动（LLM 实时决策） | 规则驱动（形态评分、量价关系） |
| **市场状态** | 7 种 Regime 类型（Stop Hunt、Absorption、Breakout、Continuation、Exhaustion、Trap、Noise） | 无明确市场状态分类 |
| **信号系统** | 信号池（AND/OR 逻辑，边缘触发） | 无信号池系统 |
| **技术指标** | 市场流指标（CVD、OI、Funding、Depth） | 传统指标（MA、EMA、RSI、MACD、KDJ、BOLL） |
| **触发机制** | 信号触发 + 定时触发 | 无明确触发机制 |
| **交易规则** | 永续合约（T+0） | A 股（T+1） |

### 1.3 第三方依赖开源性分析

**Hyper-Alpha-Arena-main 依赖**（pyproject.toml）：
- fastapi>=0.104.0（MIT 许可证）
- hyperliquid-python-sdk>=0.20.0（MIT 许可证）
- ccxt>=4.0.0（MIT 许可证）
- pandas-ta==0.4.67b0（MIT 许可证）
- cryptography>=41.0.0（Apache 2.0/BSD 许可证）
- eth-account>=0.10.0（MIT 许可证）

**结论**：所有依赖均为开源，用户需自行配置 API 密钥，无无法开源的第三方依赖。

**stock-monitor-backend 依赖**（requirements.txt）：
- fastapi==0.104.1（MIT 许可证）
- akshare>=1.12.0（MIT 许可证）
- tushare>=1.2.0（MIT 许可证）
- baostock>=0.1.0（MIT 许可证）
- pathway>=0.8.0（Apache 2.0 许可证）

**结论**：所有依赖均为开源。

### 1.4 项目合并可行性评估

**不推荐完全合并**，原因如下：

1. **市场对象完全不同**：加密货币 vs A 股，交易规则、数据结构、指标体系完全不同
2. **算法体系差异大**：高频市场流 vs 传统技术分析，无法直接复用
3. **决策机制不同**：AI 驱动 vs 规则驱动，架构设计理念不同
4. **数据频率差异**：15 秒级 vs 日 K 线，数据采集和存储架构不同
5. **交易规则差异**：永续合约（T+0） vs A 股（T+1），持仓和交易逻辑不同

**建议方案**：保持独立，共享基础设施
- 保持两个项目独立运行
- 共享数据库基础设施（PostgreSQL）
- 共用前端组件库（菜单导航）
- 参考 Hyper-Alpha-Arena 的架构设计，但不直接合并代码

---

## 第二部分：UI 升级参考建议

### 2.1 技术栈对比

| 维度 | Hyper-Alpha-Arena | stock-monitor-backend |
|------|------------------|---------------------|
| **前端框架** | React 18 + TypeScript | Vue 3 + CDN |
| **构建工具** | Vite | 无构建工具（直接引用） |
| **UI 组件库** | Radix UI + Tailwind CSS | 无组件库（原生 HTML/CSS） |
| **组件化** | 30+ 可复用组件 | 无组件化 |
| **状态管理** | React Context API | Vue 3 Reactivity |
| **国际化** | i18next（多语言） | 无国际化 |
| **图表库** | Lightweight Charts、Recharts | 无图表库 |
| **实时更新** | WebSocket（15 秒级） | 定时轮询（5 分钟） |

### 2.2 值得参考升级的地方

#### 2.2.1 迁移到 React + TypeScript

**优势**：
- 类型安全：TypeScript 提供静态类型检查
- 组件化：可复用组件库，减少重复代码
- 生态系统：React 生态更成熟，第三方库丰富
- 性能优化：Vite 构建工具，HMR 热更新

**改造量**：2-3 个月（重写整个前端）

#### 2.2.2 采用 Radix UI 组件库

**优势**：
- 无障碍支持：符合 WCAG 标准
- 可定制性：基于 Headless UI，完全可控样式
- 性能优化：虚拟滚动、懒加载等性能优化
- 一致性：统一的组件风格和交互

**改造量**：1-2 个月（替换所有 UI 组件）

#### 2.2.3 集成 Tailwind CSS

**优势**：
- 快速开发：原子化 CSS，快速构建界面
- 响应式设计：移动端优先，自动适配不同屏幕
- 可维护性：统一的样式系统，易于维护

**改造量**：2-4 周（替换所有样式）

#### 2.2.4 实现组件化设计

**优势**：
- 可复用性：30+ 可复用组件，减少重复代码
- 可测试性：组件独立，易于单元测试
- 可维护性：组件职责单一，易于维护和扩展

**改造量**：1-2 个月（重构所有组件）

#### 2.2.5 集成 WebSocket 实时更新

**优势**：
- 实时性：15 秒级数据推送，无需轮询
- 性能优化：减少服务器负载，降低带宽消耗
- 用户体验：实时数据更新，更流畅的交互

**改造量**：2-3 周（实现 WebSocket 服务和前端集成）

#### 2.2.6 添加国际化支持

**优势**：
- 多语言：支持中文、英文等多种语言
- 可扩展性：易于添加新语言
- 用户体验：根据用户偏好切换语言

**改造量**：1-2 周（集成 i18next，提取所有文本）

### 2.3 改造工作量评估

| 功能模块 | 改造量 | 优先级 |
|---------|--------|--------|
| React + TypeScript 迁移 | 2-3 个月 | 高 |
| Radix UI 组件库集成 | 1-2 个月 | 高 |
| Tailwind CSS 集成 | 2-4 周 | 中 |
| 组件化设计 | 1-2 个月 | 高 |
| WebSocket 实时更新 | 2-3 周 | 高 |
| 国际化支持 | 1-2 周 | 中 |
| 图表库集成 | 1-2 周 | 中 |

**总改造量**：2.5-11 个月（取决于功能范围）

### 2.4 stock-monitor-backend 缺失功能分析

1. **股票池管理**：无股票池系统，需要实现 Top 20 核心、Top 100 观察
2. **形态识别系统**：无形态识别展示界面，需要实现形态卡片、形态历史
3. **量价关系展示**：无量价关系展示界面，需要实现量价面板、操作建议
4. **排名系统**：无排名展示界面，需要实现增长排名、总分排名
5. **标签系统**：无标签管理界面，需要实现标签配置、标签筛选
6. **问财集成**：无自然语言查询，需要集成同花顺问财 API
7. **多数据源支持**：无数据源切换，需要实现 akshare、tushare、baostock 切换
8. **定时任务**：无定时任务界面，需要实现任务配置、任务历史
9. **自动化交易**：无模拟交易系统，需要实现订单管理、持仓管理
10. **数据去重**：无数据去重机制，需要实现去重逻辑、完整性检查

---

## 第三部分：AI 提示词系统详细分析

### 3.1 核心架构

**提示词模板系统**（prompt_templates.py）：
- DEFAULT_PROMPT_TEMPLATE：基础模板，包含交易环境、账户状态、市场价格、新闻、触发上下文
- PRO_PROMPT_TEMPLATE：高级模板，增加技术分析支持（K 线、指标）
- KLINE_ANALYSIS_PROMPT_TEMPLATE：K 线分析专用模板
- HYPERLIQUID_PROMPT_TEMPLATE：Hyperliquid 永续合约专用模板

**变量参考文档**（PROMPT_VARIABLES_REFERENCE.md）：
- 定义所有可用变量（200+ 行文档）
- 分类清晰：基础变量、会话变量、投资组合变量、Hyperliquid 变量、K 线指标变量、市场流指标变量、市场 Regime 分类变量

**提示词生成系统提示**（prompt_generation_system_prompt.md）：
- 多语言支持（中文、英文、日文等）
- 变量替换规则：保持英文，仅 reason 和 trading_strategy 字段使用用户语言
- 策略完整性检查清单
- 示例提示词模板（趋势跟踪、均值回归等）
- 变量选择最佳实践（根据交易风格、时间框架选择指标）

### 3.2 核心服务实现

**AI 决策服务**（ai_decision_service.py - 2770 行）：

关键函数：
- `_build_prompt_context()`: 构建完整提示词上下文（唯一入口点）
- `_parse_kline_indicator_variables()`: 解析 K 线和指标变量
- `_build_klines_and_indicators_context()`: 构建 K 线和指标上下文
- `call_ai_for_decision()`: 调用 AI 模型 API 获取交易决策

**核心特性**：
1. **多模型兼容**：支持 GPT-5、o1、Deepseek-R1、Claude、Gemini、Grok 等
2. **流式响应处理**：针对 Deepseek-R1 的流式响应优化
3. **推理内容提取**：多供应商协议支持（OpenAI、DeepSeek、Claude、Gemini、Grok）
4. **变量替换系统**：SafeDict 机制，缺失变量返回 "N/A" 而不报错
5. **多语言支持**：根据用户语言自动适配
6. **市场 Regime 集成**：7 种市场状态分类（breakout、absorption、stop_hunt、exhaustion、trap、continuation、noise）
7. **触发上下文机制**：区分信号触发和定时触发
8. **多时间框架支持**：1m、5m、15m、1h 等
9. **历史交易记录**：避免 flip-flop 行为（频繁反转）
10. **新闻摘要**：集成 CoinJournal 新闻

### 3.3 stock-monitor-backend 参考建议

#### 3.3.1 创建 A 股提示词模板系统

**文件结构**：
```
stock-monitor-backend/
├── config/
│   ├── prompt_templates.py          # 提示词模板定义
│   ├── PROMPT_VARIABLES_REFERENCE.md # A 股变量参考文档
│   └── prompt_generation_system_prompt.md # 提示词生成系统提示
└── services/
    └── ai_decision_service.py       # AI 决策服务
```

**提示词模板示例**（A 股基础模板）：
```python
STOCK_DEFAULT_PROMPT_TEMPLATE = """You are a Chinese A-share trading AI.

=== TRADING ENVIRONMENT ===
Platform: Chinese A-Share Market (Shanghai/Shenzhen)
{trading_environment}

=== SESSION CONTEXT ===
Runtime: {runtime_minutes} minutes since trading started
Current UTC time: {current_time_utc}

=== ACCOUNT STATUS ===
Total Return: {total_return_percent}%
Available Cash: ¥{available_cash}
Account Value: ¥{total_account_value}

=== HOLDINGS ===
{holdings_detail}

=== MARKET PRICES ===
{market_prices}

=== NEWS ===
{news_section}

=== TRIGGER CONTEXT ===
{trigger_context}

=== TRADING RULES ===
- operation: "buy" (long), "sell" (short), "hold", or "close"
- target_portion_of_balance: 0.0-1.0 (portion of balance to use)
- max_price: required for "buy" operations
- min_price: required for "sell" operations
- Keep position size reasonable (≤ 20% of available cash per trade)

=== OUTPUT FORMAT ===
{output_format}
"""
```

#### 3.3.2 A 股变量参考文档

**基础变量**：
- `{trading_environment}`: 交易环境描述
- `{available_cash}`: 可用资金（格式化人民币）
- `{total_account_value}`: 总账户价值
- `{market_prices}`: 当前股票价格
- `{news_section}`: 最新 A 股新闻摘要

**会话变量**：
- `{runtime_minutes}`: 交易运行分钟数
- `{current_time_utc}`: 当前 UTC 时间
- `{total_return_percent}`: 总收益率百分比

**投资组合变量**：
- `{holdings_detail}`: 持仓详情（股票代码、数量、成本、市值）
- `{sampling_data}`: 历史价格采样数据

**A 股专用变量**：
- `{STOCKCODE_market_data}`: 个股市场数据（价格、涨跌幅、成交量、换手率）
- `{STOCKCODE_klines_PERIOD}(COUNT)`: K 线数据（支持日线、周线、月线）
- `{STOCKCODE_MA_PERIOD}`: 移动平均线（MA5、MA10、MA20、MA60）
- `{STOCKCODE_EMA_PERIOD}`: 指数移动平均线（EMA20、EMA50）
- `{STOCKCODE_RSI14_PERIOD}`: RSI(14) 指标
- `{STOCKCODE_MACD_PERIOD}`: MACD 指标
- `{STOCKCODE_KDJ_PERIOD}`: KDJ 指标
- `{STOCKCODE_BOLL_PERIOD}`: 布林带指标
- `{STOCKCODE_VOL_PERIOD}`: 成交量指标

**形态识别变量**：
- `{STOCKCODE_patterns}`: 缠论量价形态（阳包阴、底分型、顶分型、冲高回落等）

**量价关系变量**：
- `{STOCKCODE_volume_status}`: 成交量状态（放量/缩量/平量）
- `{STOCKCODE_price_status}`: 价格状态（上涨/下跌/平盘）
- `{STOCKCODE_action_hint}`: 操作建议（加仓/减仓/卖出/等待）

**市场状态分类变量**：
- `{market_state}`: A 股市场状态（牛市/熊市/震荡市/突破市/回调市/反转市/噪音市）

**触发上下文变量**：
- `{trigger_context}`: 触发上下文（信号触发或定时触发）

#### 3.3.3 AI 决策服务实现

**核心函数**：
```python
def _build_prompt_context(
    account: Account,
    portfolio: Dict[str, Any],
    prices: Dict[str, float],
    news_section: str,
    template_text: Optional[str] = None,
    trigger_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    构建完整提示词上下文（唯一入口点）
    """
    # 基础变量
    runtime_minutes = _calculate_runtime_minutes(account)
    current_time_utc = datetime.utcnow().isoformat() + "Z"
    total_return_percent = _calculate_total_return_percent(account)
    available_cash = _format_currency(portfolio.get('cash'))
    total_account_value = _format_currency(portfolio.get('total_assets'))
    holdings_detail = _build_holdings_detail(portfolio.get('positions', {}))
    market_prices = _build_market_prices(prices)
    
    # K 线和指标变量（动态生成）
    kline_context = {}
    if template_text:
        variable_groups = _parse_kline_indicator_variables(template_text)
        kline_context = _build_klines_and_indicators_context(variable_groups)
    
    # 触发上下文
    trigger_context_text = _format_trigger_context(trigger_context)
    
    # 输出格式
    output_format = _build_output_format()
    
    return {
        "trading_environment": "Platform: Chinese A-Share Market",
        "runtime_minutes": runtime_minutes,
        "current_time_utc": current_time_utc,
        "total_return_percent": total_return_percent,
        "available_cash": available_cash,
        "total_account_value": total_account_value,
        "holdings_detail": holdings_detail,
        "market_prices": market_prices,
        "news_section": news_section,
        "trigger_context": trigger_context_text,
        "output_format": output_format,
        **kline_context,  # 合并 K 线和指标变量
    }
```

**变量解析函数**：
```python
def _parse_kline_indicator_variables(template_text: str) -> Dict[str, Dict[str, Any]]:
    """
    解析 K 线和指标变量
    
    支持变量：
    - {STOCKCODE_klines_PERIOD}(COUNT) - K 线数据
    - {STOCKCODE_MA_PERIOD} - 移动平均线
    - {STOCKCODE_RSI14_PERIOD} - RSI 指标
    - {STOCKCODE_MACD_PERIOD} - MACD 指标
    - {STOCKCODE_KDJ_PERIOD} - KDJ 指标
    """
    # K 线变量模式
    kline_pattern = r'\{([0-9]{6})_klines_(\w+)\}(?:\((\d+)\))?'
    
    # 指标变量模式
    indicator_pattern = r'\{([0-9]{6})_(MA\d*|EMA\d*|RSI\d+|MACD|KDJ|BOLL)_(\w+)\}'
    
    # 解析并分组
    grouped = {}
    # ... 解析逻辑 ...
    
    return grouped
```

**AI 调用函数**：
```python
def call_ai_for_decision(
    db: Session,
    account: Account,
    portfolio: Dict,
    prices: Dict[str, float],
    trigger_context: Optional[Dict[str, Any]] = None,
) -> Optional[List[Dict[str, Any]]]:
    """
    调用 AI 模型 API 获取交易决策
    """
    # 获取提示词模板
    template = prompt_repo.get_prompt_for_account(db, account.id)
    
    # 构建上下文
    context = _build_prompt_context(
        account,
        portfolio,
        prices,
        news_section,
        template_text=template.template_text,
        trigger_context=trigger_context,
    )
    
    # 渲染提示词
    prompt = template.template_text.format_map(SafeDict(context))
    
    # 调用 AI API
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {account.api_key}",
    }
    
    payload = {
        "model": account.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 5000,
    }
    
    response = requests.post(
        account.base_url + "/chat/completions",
        headers=headers,
        json=payload,
        timeout=120,
    )
    
    # 解析响应
    result = response.json()
    decision_text = result["choices"][0]["message"]["content"]
    
    # 提取 JSON 决策
    decision = json.loads(decision_text)
    
    return decision
```

#### 3.3.4 输出格式定义

**A 股交易决策输出格式**：
```python
OUTPUT_FORMAT_JSON = """Respond with ONLY a JSON object using this schema:
{
  "decisions": [
    {
      "operation": "buy" | "sell" | "hold" | "close",
      "stock_code": "<6-digit stock code>",
      "stock_name": "<stock name>",
      "target_portion_of_balance": <float 0.0-1.0>,
      "max_price": <number, required for "buy" operations>,
      "min_price": <number, required for "sell" operations>,
      "reason": "<string explaining primary signals>",
      "trading_strategy": "<string covering thesis, risk controls, and exit plan>"
    }
  ]
}

CRITICAL OUTPUT REQUIREMENTS:
- Output MUST be a single, valid JSON object only
- NO markdown code blocks (no ```json``` wrappers)
- NO explanatory text before or after JSON

Example output:
{
  "decisions": [
    {
      "operation": "buy",
      "stock_code": "600519",
      "stock_name": "贵州茅台",
      "target_portion_of_balance": 0.2,
      "max_price": 1850.00,
      "reason": "底分型形态确认，RSI 超卖反弹",
      "trading_strategy": "在 1800-1850 区间建仓，止损 1750，目标 1950"
    }
  ]
}
"""
```

#### 3.3.5 多模型兼容性

**支持的模型**：
- GPT-5、o1、o3、o4（OpenAI）
- Deepseek-R1（DeepSeek）
- Claude-4、Claude-Sonnet-4-5（Anthropic）
- Gemini-2.5、Gemini-3（Google）
- Grok-3-mini（xAI）

**推理内容提取**：
```python
def _extract_reasoning_content_safe(api_result: dict) -> str:
    """
    提取推理内容（多供应商支持）
    支持：OpenAI (o1/o3/gpt-5)、DeepSeek (R1)、Claude (thinking)、Gemini (thoughts)、Grok (3-mini)
    """
    # OpenAI/DeepSeek/Qwen/Grok 标准格式
    reasoning_field = msg.get("reasoning")
    reasoning_content_field = msg.get("reasoning_content")
    
    # Claude 格式 - thinking blocks
    content_array = msg.get("content")
    for block in content_array:
        if block.get("type") == "thinking":
            thinking_text = block.get("thinking")
            # ...
    
    # Gemini 格式 - parts array
    parts_array = msg.get("parts")
    for part in parts_array:
        if part.get("thought") is True:
            thought_text = part.get("text")
            # ...
    
    return merged_reasoning
```

### 3.4 实现步骤建议

1. **创建提示词模板文件**（`config/prompt_templates.py`）
2. **构建 A 股变量参考文档**（`config/PROMPT_VARIABLES_REFERENCE.md`）
3. **实现 AI 决策服务**（`services/ai_decision_service.py`）
4. **集成市场状态分类**（牛市/熊市/震荡市等）
5. **实现触发上下文机制**（信号触发、定时触发）
6. **实现多模型兼容性**（GPT-5、Deepseek、Claude 等）
7. **实现变量替换系统**（SafeDict 机制）
8. **实现多语言支持**（中文、英文）
9. **集成历史交易记录**（避免 flip-flop 行为）
10. **集成新闻摘要**（A 股新闻）

### 3.5 关键优势

1. **灵活性**：模板化设计，易于扩展和修改
2. **可维护性**：变量集中管理，文档完善
3. **多模型支持**：统一接口，支持多种 AI 模型
4. **多语言**：根据用户语言自动适配
5. **实时性**：集成市场状态和触发上下文
6. **可追溯性**：保存提示词快照和推理内容
7. **容错性**：SafeDict 机制，缺失变量不报错

---

## 第四部分：A 股适配分阶段实施计划

### 4.1 架构设计

```
/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/
├── Hyper-Alpha-Arena-main/          # 原项目（保持不变）
│   ├── backend/                         # 加密货币后端
│   └── frontend/                        # 加密货币前端
├── stock-arena-backend/                # 新增：A 股后端（独立包）
│   ├── app/                             # FastAPI 应用
│   │   ├── main.py                      # 应用入口
│   │   ├── api/                         # API 路由
│   │   │   ├── stock_routes.py            # 股票数据 API
│   │   │   ├── kline_routes.py           # K 线数据 API
│   │   │   ├── pattern_routes.py          # 形态识别 API
│   │   │   ├── volume_price_routes.py     # 量价关系 API
│   │   │   ├── ai_decision_routes.py     # AI 决策 API
│   │   │   ├── signal_routes.py          # 信号检测 API
│   │   │   ├── ranking_routes.py         # 排名 API
│   │   │   ├── tag_routes.py             # 标签 API
│   │   │   ├── stock_pool_routes.py      # 股票池 API
│   │   │   └── ws.py                    # WebSocket
│   │   ├── models/                      # 数据模型
│   │   │   ├── stock.py                 # 股票模型
│   │   │   ├── kline.py                 # K 线模型
│   │   │   ├── pattern.py               # 形态模型
│   │   │   ├── ai_decision.py           # AI 决策模型
│   │   │   └── signal.py                # 信号模型
│   │   ├── services/                    # 业务逻辑
│   │   │   ├── stock_data_service.py     # 股票数据服务
│   │   │   ├── kline_service.py         # K 线数据服务（CSV 主源）
│   │   │   ├── kline_csv_loader.py      # CSV 加载器
│   │   │   ├── kline_incremental_updater.py # 增量更新器
│   │   │   ├── pattern_analysis_service.py # 形态识别服务
│   │   │   ├── volume_price_service.py   # 量价关系服务
│   │   │   ├── ai_decision_service.py   # AI 决策服务
│   │   │   ├── signal_detection_service.py # 信号检测服务
│   │   │   ├── ranking_service.py       # 排名服务
│   │   │   ├── tag_service.py          # 标签服务
│   │   │   └── stock_pool_service.py    # 股票池服务
│   │   ├── config/                     # 配置
│   │   │   ├── prompt_templates.py       # 提示词模板
│   │   │   ├── PROMPT_VARIABLES_STOCK.md # A 股变量文档
│   │   │   ├── prompt_generation_system_prompt_stock.md
│   │   │   ├── settings.py             # 配置文件
│   │   │   └── csv_config.py          # CSV 配置（路径、格式）
│   │   ├── database/                   # 数据库
│   │   │   ├── connection.py            # 数据库连接（PostgreSQL）
│   │   │   └── init_db.py              # 初始化脚本
│   │   └── utils/                      # 工具
│   │       ├── encryption.py             # 加密工具
│   │       └── logger.py               # 日志工具
│   ├── requirements.txt                   # 依赖
│   ├── .env.example                     # 环境变量示例
│   └── README.md                        # 文档
├── stock-arena-frontend/               # 新增：A 股前端（独立包）
│   ├── app/                             # React 应用
│   │   ├── components/                  # 组件
│   │   │   ├── stock/                 # 股票组件
│   │   │   ├── kline/                 # K 线组件
│   │   │   ├── pattern/               # 形态组件
│   │   │   ├── volume_price/           # 量价组件
│   │   │   ├── ai/                    # AI 组件
│   │   │   ├── signal/                # 信号组件
│   │   │   ├── ranking/               # 排名组件
│   │   │   ├── tag/                   # 标签组件
│   │   │   ├── stock_pool/            # 股票池组件
│   │   │   ├── portfolio/             # 投资组合组件
│   │   │   ├── layout/                # 布局组件（共用）
│   │   │   └── ui/                    # UI 组件（共用）
│   │   ├── contexts/                    # 上下文
│   │   ├── lib/                         # 工具库
│   │   ├── locales/                     # 国际化
│   │   ├── main.tsx                     # 应用入口
│   │   └── index.css                    # 样式
│   ├── public/                           # 静态资源
│   ├── package.json                       # 依赖
│   ├── vite.config.ts                    # Vite 配置
│   ├── tailwind.config.js                # Tailwind 配置
│   └── tsconfig.json                     # TypeScript 配置
└── shared-components/                   # 新增：共用组件包
    ├── layout/                          # 布局组件（前后端共用）
    │   ├── Header.tsx                    # 头部导航
    │   ├── Sidebar.tsx                   # 侧边栏
    │   └── Footer.tsx                    # 底部
    ├── navigation/                       # 导航配置
    │   └── menu_config.ts               # 菜单配置
    └── types/                           # 类型定义
        └── navigation.ts                 # 导航类型

# CSV 数据源配置
CSV 文件路径：/Users/mac/Downloads/daily
CSV 文件命名格式：{股票代码}.{交易所后缀}.csv
示例：000030.SZ.csv, 000031.SZ.csv
```

### 4.2 CSV 数据源架构说明

#### 数据源优先级

1. **CSV 文件（主源）**：
   - 路径：/Users/mac/Downloads/daily
   - 文件格式：{股票代码}.{交易所后缀}.csv
   - 示例：000030.SZ.csv, 000031.SZ.csv
   - 加载方式：批量扫描和导入

2. **tushare（增量源 1）**：
   - 用途：获取最新交易日数据
   - 更新频率：每个交易日收盘后
   - 数据类型：日线、分钟线

3. **akshare（增量源 2）**：
   - 用途：获取最新交易日数据
   - 更新频率：每个交易日收盘后
   - 数据类型：日线、分钟线、财务数据

#### 数据流程

1. **初始加载**：扫描 CSV 目录，批量导入所有 CSV 文件到数据库
2. **增量更新**：每个交易日收盘后，调用 tushare/akshare 获取最新数据，更新数据库
3. **数据验证**：验证数据完整性（日期连续性、价格合理性等）
4. **数据去重**：基于股票代码+周期+时间戳的唯一约束，自动去重

#### CSV 文件格式假设

假设 CSV 文件包含以下列：
- date：日期（YYYY-MM-DD）
- open：开盘价
- high：最高价
- low：最低价
- close：收盘价
- volume：成交量
- amount：成交额（可选）
- turnover：换手率（可选）

### 4.3 分阶段实施计划

#### 阶段 1：环境准备和项目初始化（1-2 天）

**1.1 后端项目初始化**
- 创建 `stock-arena-backend` 目录结构
- 初始化 Python 项目（pyproject.toml 或 setup.py）
- 创建 requirements.txt（FastAPI、SQLAlchemy、PostgreSQL、pandas、akshare、tushare 等）
- 创建 .env.example（数据库连接、CSV 路径、API 密钥等）
- 配置本机 PostgreSQL 连接（不使用 Docker）

**1.2 前端项目初始化**
- 创建 `stock-arena-frontend` 目录结构
- 初始化 React + TypeScript + Vite 项目
- 安装依赖（React、Radix UI、Tailwind CSS、i18next 等）
- 配置 Vite 和 Tailwind
- 创建基础组件结构

**1.3 共用组件包初始化**
- 创建 `shared-components` 目录
- 初始化 TypeScript 项目
- 创建布局组件（Header、Sidebar、Footer）
- 创建导航配置（menu_config.ts）
- 导出为 npm 包或直接引用

**1.4 数据库初始化**
- 使用本机 PostgreSQL 创建数据库
- 创建数据库表结构（股票、K 线、形态、AI 决策等）
- 初始化基础数据（股票池、标签等）

#### 阶段 2：CSV 数据加载系统（3-4 天）

**2.1 CSV 配置**
- 创建 `config/csv_config.py`
- 配置 CSV 文件路径（/Users/mac/Downloads/daily）
- 配置 CSV 文件格式（列名、数据类型）
- 配置 CSV 文件命名规则（{股票代码}.{交易所后缀}.csv）

**2.2 CSV 加载器**
- 创建 `services/kline_csv_loader.py`
- 实现 CSV 文件扫描（扫描 daily 目录）
- 实现 CSV 文件解析（pandas 读取）
- 实现数据验证（日期、价格、成交量等）
- 实现数据标准化（统一格式）
- 实现批量导入数据库

**2.3 数据模型**
- 创建 `models/kline.py`
- 定义 K 线数据模型（股票代码、周期、时间戳、开高低收、成交量、换手率）
- 添加索引优化查询性能
- 添加唯一约束（股票代码+周期+时间戳）

**2.4 K 线数据服务**
- 创建 `services/kline_service.py`
- 实现 CSV 数据加载接口
- 实现 K 线数据查询接口（多周期）
- 实现数据覆盖情况查询
- 实现数据去重和完整性检查

**2.5 API 路由**
- 创建 `api/kline_routes.py`
- 实现 K 线数据查询接口（/api/klines/data）
- 实现数据覆盖情况查询接口（/api/klines/coverage）
- 实现 CSV 重新加载接口（/api/klines/reload）

#### 阶段 3：增量更新系统（2-3 天）

**3.1 增量更新器**
- 创建 `services/kline_incremental_updater.py`
- 实现 tushare 增量更新（获取最新交易日数据）
- 实现 akshare 增量更新（获取最新交易日数据）
- 实现增量数据验证
- 实现增量数据合并到数据库

**3.2 定时任务**
- 扩展 `services/scheduler.py`
- 实现增量更新定时任务（每个交易日收盘后）
- 实现 CSV 文件监控（检测新文件）
- 实现数据完整性检查

**3.3 API 路由**
- 扩展 `api/kline_routes.py`
- 实现增量更新触发接口（/api/klines/update）
- 实现更新状态查询接口（/api/klines/update-status）

#### 阶段 4：提示词系统（2-3 天）

**4.1 提示词模板**
- 创建 `config/prompt_templates.py`
- 实现基础模板（STOCK_DEFAULT_PROMPT_TEMPLATE）
- 实现高级模板（STOCK_PRO_PROMPT_TEMPLATE）
- 实现 K 线分析模板（STOCK_KLINE_ANALYSIS_TEMPLATE）

**4.2 变量参考文档**
- 创建 `config/PROMPT_VARIABLES_STOCK.md`
- 定义所有 A 股变量（基础、会话、投资组合、K 线、形态、量价、市场状态）
- 提供变量使用示例

**4.3 提示词生成系统提示**
- 创建 `config/prompt_generation_system_prompt_stock.md`
- 支持中文策略描述
- 变量替换规则
- 策略完整性检查清单

**4.4 AI 决策服务**
- 创建 `services/ai_decision_service.py`
- 实现 `_build_prompt_context()` 构建提示词上下文
- 实现 `_parse_kline_indicator_variables()` 解析 K 线和指标变量
- 实现 `_build_klines_and_indicators_context()` 构建技术指标上下文
- 集成形态识别和量价关系分析结果
- 实现 AI 模型调用（GPT-5、Deepseek、Claude 等）
- 实现多模型兼容性

#### 阶段 5：形态识别和量价关系（3-4 天）

**5.1 形态识别服务**
- 创建 `services/pattern_analysis_service.py`
- 集成现有形态识别逻辑（stock-monitor-backend）
- 支持形态：阳包阴、底分型、顶分型、冲高回落等
- 实现形态评分
- 实现形态历史查询

**5.2 量价关系服务**
- 创建 `services/volume_price_service.py`
- 集成现有量价关系分析逻辑（stock-monitor-backend）
- 实现成交量状态判断（放量/缩量/平量）
- 实现价格状态判断（上涨/下跌/平盘）
- 实现操作建议生成（加仓/减仓/卖出/等待）

**5.3 API 路由**
- 创建 `api/pattern_routes.py`（形态识别 API）
- 创建 `api/volume_price_routes.py`（量价关系 API）

#### 阶段 6：股票池和排名系统（2-3 天）

**6.1 股票池服务**
- 创建 `services/stock_pool_service.py`
- 实现股票池管理（Top 20 核心、Top 100 观察）
- 实现股票池更新机制（定时任务）
- 实现股票池排名

**6.2 排名服务**
- 创建 `services/ranking_service.py`
- 实现增长排名（按收益率排序）
- 实现总分排名（按异动总分排序）
- 实现排名历史查询

**6.3 API 路由**
- 创建 `api/stock_pool_routes.py`（股票池 API）
- 创建 `api/ranking_routes.py`（排名 API）

#### 阶段 7：信号检测系统（3-4 天）

**7.1 信号检测服务**
- 创建 `services/signal_detection_service.py`
- 实现信号池管理（AND/OR 逻辑）
- 实现边缘触发逻辑（避免重复触发）
- 实现触发上下文记录
- 实现定时触发机制

**7.2 API 路由**
- 创建 `api/signal_routes.py`（信号检测 API）
- 实现信号池配置接口
- 实现信号触发历史查询
- 实现信号回测功能

#### 阶段 8：AI 决策 API（2-3 天）

**8.1 AI 决策 API**
- 创建 `api/ai_decision_routes.py`
- 实现 AI 决策调用接口（/api/ai/decision）
- 实现提示词预览接口（/api/ai/prompt-preview）
- 实现决策历史查询接口（/api/ai/decisions）
- 实现决策执行接口（模拟交易）

**8.2 WebSocket 实时推送**
- 创建 `api/ws.py`
- 实现价格实时推送
- 实现 K 线实时推送
- 实现信号触发推送
- 实现 AI 决策推送

#### 阶段 9：前端基础框架（3-4 天）

**9.1 布局组件（共用）**
- 创建 `shared-components/layout/Header.tsx`
- 创建 `shared-components/layout/Sidebar.tsx`
- 创建 `shared-components/layout/Footer.tsx`
- 实现菜单导航配置（menu_config.ts）

**9.2 前端基础配置**
- 配置 API 基础 URL（指向 stock-arena-backend）
- 配置 i18n（支持中文、英文）
- 配置路由（React Router）
- 配置状态管理（Context API）

**9.3 UI 组件库**
- 创建基础 UI 组件（Button、Card、Input、Select、Table、Dialog 等）
- 使用 Radix UI 作为基础
- 使用 Tailwind CSS 进行样式

#### 阶段 10：前端股票相关组件（4-5 天）

**10.1 股票选择器**
- 创建 `components/stock/StockSelector.tsx`
- 支持 A 股代码输入（6 位数字）
- 支持股票名称搜索
- 支持股票列表展示

**10.2 K 线视图**
- 创建 `components/kline/KlinesView.tsx`
- 支持多周期选择（日线、周线、月线等）
- 支持指标选择（MA、EMA、RSI、MACD、KDJ、BOLL 等）
- 集成 TradingView 图表
- 实现 K 线实时更新

**10.3 形态识别展示**
- 创建 `components/pattern/PatternManager.tsx`
- 展示形态识别结果
- 展示形态评分
- 展示形态历史

**10.4 量价关系展示**
- 创建 `components/volume_price/VolumePricePanel.tsx`
- 展示量价关系分析结果
- 展示操作建议
- 展示历史查询

#### 阶段 11：前端 AI 相关组件（3-4 天）

**11.1 AI 提示词聊天**
- 创建 `components/ai/AiPromptChatModal.tsx`
- 实现提示词模板选择
- 实现变量选择器
- 实现提示词预览
- 实现 AI 生成提示词

**11.2 AI 决策面板**
- 创建 `components/ai/AiDecisionPanel.tsx`
- 展示 AI 决策结果
- 展示决策历史
- 展示决策执行状态

**11.3 提示词管理器**
- 创建 `components/ai/PromptManager.tsx`
- 实现提示词模板管理（创建、编辑、删除）
- 实现提示词预览
- 实现提示词回测

#### 阶段 12：前端信号和排名组件（2-3 天）

**12.1 信号管理器**
- 创建 `components/signal/SignalManager.tsx`
- 实现信号池配置界面
- 实现信号触发历史展示
- 实现信号回测功能

**12.2 排名视图**
- 创建 `components/ranking/RankingView.tsx`
- 展示增长排名
- 展示总分排名
- 实现排名历史查询

**12.3 股票池视图**
- 创建 `components/stock_pool/StockPoolView.tsx`
- 展示股票池配置
- 展示股票池排名
- 实现股票池更新

#### 阶段 13：前端投资组合组件（2-3 天）

**13.1 投资组合视图**
- 创建 `components/portfolio/PortfolioView.tsx`
- 展示 A 股持仓
- 展示资产曲线
- 展示交易历史

**13.2 持仓表格**
- 创建 `components/portfolio/PositionTable.tsx`
- 展示持仓详情（股票代码、名称、数量、成本、市值、盈亏）
- 实现持仓操作（平仓、调整）

**13.3 资产曲线**
- 创建 `components/portfolio/AssetCurve.tsx`
- 展示资产曲线
- 支持多时间框架（日、周、月）
- 实现实时更新

#### 阶段 14：标签和问财集成（2-3 天）

**14.1 标签管理器**
- 创建 `components/tag/TagManager.tsx`
- 实现标签配置（行业、概念、热点等）
- 实现标签筛选功能
- 实现标签统计

**14.2 问财集成**
- 集成同花顺问财 API
- 实现自然语言查询
- 实现查询结果展示

#### 阶段 15：测试和优化（3-5 天）

**15.1 功能测试**
- 测试 CSV 数据加载
- 测试增量更新
- 测试提示词系统
- 测试 AI 决策
- 测试信号检测
- 测试前端功能

**15.2 性能优化**
- CSV 加载优化（pandas 批量读取）
- 数据库查询优化
- API 响应优化
- 前端渲染优化
- WebSocket 推送优化

**15.3 部署准备**
- 环境配置（.env）
- 数据库迁移
- 监控和日志
- 文档完善

### 4.4 预计总时间

**总时间**：38-58 天（约 1.3-2 个月）

### 4.5 关键里程碑

- **M1（第 1-2 天）**：项目初始化完成，基础环境就绪
- **M2（第 5-8 天）**：CSV 数据加载系统完成，K 线数据可用
- **M3（第 8-11 天）**：增量更新系统完成，数据可持续更新
- **M4（第 11-14 天）**：提示词系统完成，AI 决策可用
- **M5（第 15-19 天）**：形态识别和量价关系完成
- **M6（第 18-22 天）**：股票池和排名系统完成
- **M7（第 22-26 天）**：信号检测系统完成
- **M8（第 25-29 天）**：AI 决策 API 完成
- **M9（第 29-33 天）**：前端基础框架完成
- **M10（第 34-39 天）**：前端股票相关组件完成
- **M11（第 38-42 天）**：前端 AI 相关组件完成
- **M12（第 41-44 天）**：前端信号和排名组件完成
- **M13（第 44-47 天）**：前端投资组合组件完成
- **M14（第 47-50 天）**：标签和问财集成完成
- **M15（第 51-58 天）**：测试优化完成，可部署上线

### 4.6 关键优势

1. **源代码隔离**：Hyper-Alpha-Arena-main 保持不变，独立维护 A 股代码
2. **包独立**：后端和前端都是独立包，便于维护和部署
3. **共用组件**：菜单导航共用，减少重复代码
4. **本机 PostgreSQL**：使用本机数据库，不依赖 Docker
5. **CSV 主源**：CSV 文件作为主要数据源，稳定可靠
6. **增量更新**：tushare/akshare 作为增量更新源，保持数据新鲜度
7. **模块化设计**：每个功能模块独立，便于开发和测试
8. **渐进式开发**：分阶段实现，每个阶段都有可交付成果

### 4.7 风险和注意事项

1. **CSV 文件管理**：需要定期更新 CSV 文件，确保数据新鲜度
2. **增量更新稳定性**：tushare/akshare 可能有限流，需要实现重试和缓存
3. **A 股交易时间**：需要考虑 A 股交易时间限制（9:30-11:30, 13:00-15:00）
4. **T+1 交易规则**：A 股 T+1 交易，需要调整持仓和交易逻辑
5. **涨跌停限制**：A 股有 10% 涨跌停限制，需要考虑价格波动范围
6. **数据量**：A 股有 5000+ 只股票，需要优化 CSV 加载和存储
7. **合规性**：需要确保符合 A 股交易规则和监管要求
8. **共用组件维护**：需要确保共用组件的兼容性和可维护性
9. **CSV 格式一致性**：需要确保所有 CSV 文件格式一致，否则需要预处理
10. **增量更新冲突**：需要处理 CSV 数据和增量更新数据的冲突（以增量更新为准）

---

## 第五部分：关键文件参考

### 5.1 Hyper-Alpha-Arena 关键文件

**后端核心文件**：
- `/backend/services/ai_decision_service.py`（2770 行）：AI 决策核心服务
- `/backend/config/prompt_templates.py`：提示词模板定义
- `/backend/config/PROMPT_VARIABLES_REFERENCE.md`：变量参考文档（200+ 行）
- `/backend/config/prompt_generation_system_prompt.md`（650 行）：提示词生成系统提示
- `/backend/services/kline_data_service.py`：K 线数据统一服务
- `/backend/services/kline_collectors.py`：K 线采集器（交易所分流架构）
- `/backend/api/kline_routes.py`：K 线数据管理 API 路由

**前端核心文件**：
- `/frontend/app/components/klines/KlinesView.tsx`：K 线视图组件
- `/frontend/app/components/prompt/PromptManager.tsx`：提示词管理器
- `/frontend/app/components/signal/SignalManager.tsx`：信号管理器
- `/frontend/app/lib/api.ts`：API 请求封装
- `/frontend/app/locales/zh.json`：中文国际化

**依赖文件**：
- `/backend/pyproject.toml`：后端依赖配置
- `/frontend/package.json`：前端依赖配置

### 5.2 stock-monitor-backend 关键文件

**核心文件**：
- `/app/services/analysis_service.py`：量价关系分析服务
- `/app/services/pattern_analysis_service.py`（450 行）：形态识别服务
- `/app/static/dashboard.html`（876 行）：Vue 3 前端主页面

**依赖文件**：
- `/requirements.txt`：Python 依赖配置

---

## 第六部分：总结和建议

### 6.1 项目对比总结

| 维度 | Hyper-Alpha-Arena | stock-monitor-backend | 建议 |
|------|------------------|---------------------|------|
| **市场对象** | 加密货币 | A 股 | 保持独立 |
| **技术栈** | React + TypeScript | Vue 3 + CDN | 参考 React 架构 |
| **数据源** | 实时 API | CSV 文件 | CSV 主源 + 增量更新 |
| **AI 集成** | 完整的提示词系统 | 无 | 参考提示词系统 |
| **实时性** | WebSocket（15 秒级） | 轮询（5 分钟） | 集成 WebSocket |
| **组件化** | 30+ 可复用组件 | 无组件化 | 实现组件化 |

### 6.2 实施建议

1. **保持项目独立**：不推荐完全合并，保持两个项目独立运行
2. **共享基础设施**：共用数据库、共用组件库
3. **渐进式迁移**：分阶段实现，每个阶段都有可交付成果
4. **参考架构设计**：学习 Hyper-Alpha-Arena 的架构设计，但不直接合并代码
5. **优先实现核心功能**：先实现 K 线数据、提示词系统、AI 决策
6. **逐步完善功能**：后续添加形态识别、量价关系、股票池、排名等

### 6.3 下一步行动

1. **创建独立包**：创建 stock-arena-backend 和 stock-arena-frontend 独立包
2. **实现 CSV 数据加载**：扫描 /Users/mac/Downloads/daily 目录，批量导入 CSV 文件
3. **实现提示词系统**：参考 Hyper-Alpha-Arena 的提示词系统，适配 A 股
4. **实现 AI 决策服务**：集成 GPT-5、Deepseek、Claude 等多模型
5. **实现前端基础框架**：React + TypeScript + Radix UI + Tailwind CSS
6. **实现共用组件**：Header、Sidebar、Footer 等布局组件

---

## 附录

### A.1 环境配置

**后端环境**：
- Python 3.10+
- PostgreSQL（本机安装）
- FastAPI 0.104+
- SQLAlchemy 2.0+

**前端环境**：
- Node.js 18+
- React 18+
- TypeScript 5+
- Vite 4+

### A.2 数据库配置

**PostgreSQL 连接**：
```
DATABASE_URL=postgresql://user:password@localhost:5432/stock_arena
```

**CSV 路径配置**：
```
CSV_DATA_PATH=/Users/mac/Downloads/daily
```

### A.3 API 密钥配置

**AI 模型 API 密钥**：
```
OPENAI_API_KEY=sk-xxx
DEEPSEEK_API_KEY=sk-xxx
CLAUDE_API_KEY=sk-xxx
```

**tushare/akshare API 密钥**：
```
TUSHARE_TOKEN=xxx
```

---

## 文档信息

- **创建日期**：2025-01-13
- **归档目的**：保存 Hyper-Alpha-Arena 项目分析与 A 股适配计划的完整对话记录
- **文档版本**：v1.0
- **维护者**：AI Assistant

---

*本文档归档了完整的对话内容，包括项目评估、算法对比、依赖分析、UI 升级建议、AI 提示词系统分析、以及分阶段实施计划。*
