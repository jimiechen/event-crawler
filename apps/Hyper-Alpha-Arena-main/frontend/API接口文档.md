# Hyper Alpha Arena API 接口文档

> 本文档详细描述了 Hyper Alpha Arena 前端应用的所有 API 接口，包括请求参数、响应结构和 Mock 数据示例。

## 目录

- [1. 配置管理](#1-配置管理)
- [2. 加密货币](#2-加密货币)
- [3. AI决策日志](#3-ai决策日志)
- [4. 用户认证](#4-用户认证)
- [5. 交易账户管理](#5-交易账户管理)
- [6. 策略配置](#6-策略配置)
- [7. 提示词模板管理](#7-提示词模板管理)
- [8. Alpha Arena 聚合数据](#8-alpha-arena-聚合数据)
- [9. Hyperliquid 相关](#9-hyperliquid-相关)
- [10. 会员服务](#10-会员服务)
- [11. Hyperliquid Builder Fee 授权](#11-hyperliquid-builder-fee-授权)
- [12. 交易员数据导入导出](#12-交易员数据导入导出)
- [13. Prompt 回测](#13-prompt-回测)

---

## 1. 配置管理

### 1.1 检查必需配置

检查系统是否已配置所有必需的配置项。

**接口信息**
- 方法：`GET`
- 路径：`/api/config/check-required`
- 函数名：`checkRequiredConfigs`

**请求参数**
无

**响应数据结构**
```typescript
{
  required_configs: string[]
  missing_configs: string[]
  all_configured: boolean
}
```

**Mock 响应数据**
```json
{
  "required_configs": [
    "OPENAI_API_KEY",
    "HYPERLIQUID_API_KEY",
    "HYPERLIQUID_API_SECRET"
  ],
  "missing_configs": [],
  "all_configured": true
}
```

---

## 2. 加密货币

### 2.1 获取加密货币符号列表

获取所有可用的加密货币交易对。

**接口信息**
- 方法：`GET`
- 路径：`/api/crypto/symbols`
- 函数名：`getCryptoSymbols`

**请求参数**
无

**响应数据结构**
```typescript
{
  symbols: string[]
  count: number
}
```

**Mock 响应数据**
```json
{
  "symbols": [
    "BTC",
    "ETH",
    "SOL",
    "DOGE",
    "XRP",
    "ADA",
    "AVAX",
    "MATIC",
    "LINK",
    "DOT"
  ],
  "count": 10
}
```

---

### 2.2 获取加密货币价格

获取指定加密货币的当前价格。

**接口信息**
- 方法：`GET`
- 路径：`/api/crypto/price/{symbol}`
- 函数名：`getCryptoPrice`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| symbol | string | 是 | 加密货币符号，如 BTC、ETH |

**响应数据结构**
```typescript
{
  symbol: string
  price: number
  price_change_24h: number
  price_change_percent_24h: number
  timestamp: string
}
```

**Mock 响应数据**
```json
{
  "symbol": "BTC",
  "price": 67542.50,
  "price_change_24h": 1234.50,
  "price_change_percent_24h": 1.86,
  "timestamp": "2026-01-13T10:30:00Z"
}
```

---

### 2.3 获取加密货币市场状态

获取指定加密货币的市场状态信息。

**接口信息**
- 方法：`GET`
- 路径：`/api/crypto/status/{symbol}`
- 函数名：`getCryptoMarketStatus`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| symbol | string | 是 | 加密货币符号 |

**响应数据结构**
```typescript
{
  symbol: string
  market_status: string
  trading_hours: string
  last_update: string
}
```

**Mock 响应数据**
```json
{
  "symbol": "BTC",
  "market_status": "open",
  "trading_hours": "24/7",
  "last_update": "2026-01-13T10:30:00Z"
}
```

---

### 2.4 获取热门加密货币

获取热门加密货币列表。

**接口信息**
- 方法：`GET`
- 路径：`/api/crypto/popular`
- 函数名：`getPopularCryptos`

**请求参数**
无

**响应数据结构**
```typescript
{
  popular: Array<{
    symbol: string
    name: string
    price: number
    volume_24h: number
  }>
}
```

**Mock 响应数据**
```json
{
  "popular": [
    {
      "symbol": "BTC",
      "name": "Bitcoin",
      "price": 67542.50,
      "volume_24h": 28500000000
    },
    {
      "symbol": "ETH",
      "name": "Ethereum",
      "price": 3456.78,
      "volume_24h": 15200000000
    },
    {
      "symbol": "SOL",
      "name": "Solana",
      "price": 142.35,
      "volume_24h": 3200000000
    }
  ]
}
```

---

## 3. AI决策日志

### 3.1 获取AI决策列表

获取指定账户的AI决策记录，支持多种过滤条件。

**接口信息**
- 方法：`GET`
- 路径：`/api/accounts/{accountId}/ai-decisions`
- 函数名：`getAIDecisions`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| accountId | number | 是 | 账户ID（路径参数） |
| operation | string | 否 | 操作类型过滤（buy/sell/hold） |
| symbol | string | 否 | 交易符号过滤 |
| executed | boolean | 否 | 是否已执行过滤 |
| start_date | string | 否 | 开始日期（ISO格式） |
| end_date | string | 否 | 结束日期（ISO格式） |
| limit | number | 否 | 返回数量限制 |

**响应数据结构**
```typescript
{
  decisions: Array<{
    id: number
    account_id: number
    decision_time: string
    reason: string
    operation: string
    symbol?: string
    prev_portion: number
    target_portion: number
    total_balance: number
    executed: string
    order_id?: number
  }>
  total: number
}
```

**Mock 响应数据**
```json
{
  "decisions": [
    {
      "id": 1,
      "account_id": 1,
      "decision_time": "2026-01-13T10:15:00Z",
      "reason": "BTC突破阻力位，趋势强劲",
      "operation": "buy",
      "symbol": "BTC",
      "prev_portion": 0.3,
      "target_portion": 0.5,
      "total_balance": 100000,
      "executed": "true",
      "order_id": 12345
    },
    {
      "id": 2,
      "account_id": 1,
      "decision_time": "2026-01-13T09:30:00Z",
      "reason": "市场波动加大，保持观望",
      "operation": "hold",
      "symbol": "ETH",
      "prev_portion": 0.4,
      "target_portion": 0.4,
      "total_balance": 100000,
      "executed": "true"
    }
  ],
  "total": 2
}
```

---

### 3.2 获取单个AI决策详情

获取指定ID的AI决策详细信息。

**接口信息**
- 方法：`GET`
- 路径：`/api/accounts/{accountId}/ai-decisions/{decisionId}`
- 函数名：`getAIDecisionById`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| accountId | number | 是 | 账户ID（路径参数） |
| decisionId | number | 是 | 决策ID（路径参数） |

**响应数据结构**
```typescript
{
  id: number
  account_id: number
  decision_time: string
  reason: string
  operation: string
  symbol?: string
  prev_portion: number
  target_portion: number
  total_balance: number
  executed: string
  order_id?: number
  prompt_snapshot?: string
  reasoning_snapshot?: string
  decision_snapshot?: string
}
```

**Mock 响应数据**
```json
{
  "id": 1,
  "account_id": 1,
  "decision_time": "2026-01-13T10:15:00Z",
  "reason": "BTC突破阻力位，趋势强劲",
  "operation": "buy",
  "symbol": "BTC",
  "prev_portion": 0.3,
  "target_portion": 0.5,
  "total_balance": 100000,
  "executed": "true",
  "order_id": 12345,
  "prompt_snapshot": "当前市场状况分析...",
  "reasoning_snapshot": "基于技术指标分析...",
  "decision_snapshot": "{\"operation\":\"buy\",\"symbol\":\"BTC\",\"portion\":0.5}"
}
```

---

### 3.3 获取AI决策统计

获取指定账户的AI决策统计数据。

**接口信息**
- 方法：`GET`
- 路径：`/api/accounts/{accountId}/ai-decisions/stats`
- 函数名：`getAIDecisionStats`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| accountId | number | 是 | 账户ID（路径参数） |
| days | number | 否 | 统计天数，默认7天 |

**响应数据结构**
```typescript
{
  total_decisions: number
  executed_decisions: number
  execution_rate: number
  operations: {
    [key: string]: number
  }
  avg_target_portion: number
  period_start: string
  period_end: string
}
```

**Mock 响应数据**
```json
{
  "total_decisions": 45,
  "executed_decisions": 42,
  "execution_rate": 0.9333,
  "operations": {
    "buy": 18,
    "sell": 15,
    "hold": 12
  },
  "avg_target_portion": 0.45,
  "period_start": "2026-01-06T00:00:00Z",
  "period_end": "2026-01-13T00:00:00Z"
}
```

---

## 4. 用户认证

### 4.1 用户登录

使用用户名和密码进行登录认证。

**接口信息**
- 方法：`POST`
- 路径：`/api/users/login`
- 函数名：`loginUser`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

**请求示例**
```json
{
  "username": "trader001",
  "password": "securePassword123"
}
```

**响应数据结构**
```typescript
{
  user: {
    id: number
    username: string
    email?: string
    is_active: boolean
  }
  session_token: string
  expires_at: string
}
```

**Mock 响应数据**
```json
{
  "user": {
    "id": 1,
    "username": "trader001",
    "email": "trader001@example.com",
    "is_active": true
  },
  "session_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2026-01-20T10:30:00Z"
}
```

---

### 4.2 获取用户资料

使用会话令牌获取用户资料信息。

**接口信息**
- 方法：`GET`
- 路径：`/api/users/profile`
- 函数名：`getUserProfile`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| session_token | string | 是 | 会话令牌（查询参数） |

**响应数据结构**
```typescript
{
  id: number
  username: string
  email?: string
  is_active: boolean
  created_at: string
  last_login: string
}
```

**Mock 响应数据**
```json
{
  "id": 1,
  "username": "trader001",
  "email": "trader001@example.com",
  "is_active": true,
  "created_at": "2025-06-15T08:00:00Z",
  "last_login": "2026-01-13T10:25:00Z"
}
```

---

## 5. 交易账户管理

### 5.1 列出交易账户（带会话令牌）

使用会话令牌获取用户的交易账户列表。

**接口信息**
- 方法：`GET`
- 路径：`/api/accounts/`
- 函数名：`listTradingAccounts`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| session_token | string | 是 | 会话令牌（查询参数） |

**响应数据结构**
```typescript
{
  accounts: Array<{
    id: number
    user_id: number
    name: string
    model?: string
    base_url?: string
    api_key?: string
    initial_capital: number
    current_cash: number
    frozen_cash: number
    account_type: string
    is_active: boolean
    auto_trading_enabled?: boolean
    wallet_address?: string | null
    has_mainnet_wallet?: boolean
    show_on_dashboard?: boolean
  }>
}
```

**Mock 响应数据**
```json
{
  "accounts": [
    {
      "id": 1,
      "user_id": 1,
      "name": "GPT Trader",
      "model": "gpt-4-turbo",
      "base_url": "https://api.openai.com/v1",
      "api_key": "sk-****",
      "initial_capital": 100000,
      "current_cash": 125000,
      "frozen_cash": 0,
      "account_type": "AI",
      "is_active": true,
      "auto_trading_enabled": true,
      "wallet_address": null,
      "has_mainnet_wallet": false,
      "show_on_dashboard": true
    },
    {
      "id": 2,
      "user_id": 1,
      "name": "Claude Analyst",
      "model": "claude-3-opus",
      "base_url": "https://api.anthropic.com/v1",
      "api_key": "sk-ant-****",
      "initial_capital": 50000,
      "current_cash": 48500,
      "frozen_cash": 0,
      "account_type": "AI",
      "is_active": true,
      "auto_trading_enabled": false,
      "wallet_address": null,
      "has_mainnet_wallet": false,
      "show_on_dashboard": true
    }
  ]
}
```

---

### 5.2 创建交易账户（带会话令牌）

使用会话令牌创建新的交易账户。

**接口信息**
- 方法：`POST`
- 路径：`/api/accounts/`
- 函数名：`createTradingAccount`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| session_token | string | 是 | 会话令牌（查询参数） |
| name | string | 是 | 账户名称 |
| model | string | 否 | AI模型名称 |
| base_url | string | 否 | API基础URL |
| api_key | string | 否 | API密钥 |
| initial_capital | number | 否 | 初始资金，默认10000 |
| account_type | string | 否 | 账户类型，默认"AI" |
| auto_trading_enabled | boolean | 否 | 是否启用自动交易，默认true |

**请求示例**
```json
{
  "name": "New AI Trader",
  "model": "gpt-4-turbo",
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-proj-xxxxx",
  "initial_capital": 100000,
  "account_type": "AI",
  "auto_trading_enabled": true
}
```

**响应数据结构**
```typescript
{
  id: number
  user_id: number
  name: string
  model?: string
  base_url?: string
  api_key?: string
  initial_capital: number
  current_cash: number
  frozen_cash: number
  account_type: string
  is_active: boolean
  auto_trading_enabled?: boolean
  wallet_address?: string | null
  has_mainnet_wallet?: boolean
  show_on_dashboard?: boolean
  created_at: string
}
```

**Mock 响应数据**
```json
{
  "id": 3,
  "user_id": 1,
  "name": "New AI Trader",
  "model": "gpt-4-turbo",
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-proj-xxxxx",
  "initial_capital": 100000,
  "current_cash": 100000,
  "frozen_cash": 0,
  "account_type": "AI",
  "is_active": true,
  "auto_trading_enabled": true,
  "wallet_address": null,
  "has_mainnet_wallet": false,
  "show_on_dashboard": true,
  "created_at": "2026-01-13T10:30:00Z"
}
```

---

### 5.3 更新交易账户（带会话令牌）

使用会话令牌更新交易账户信息。

**接口信息**
- 方法：`PUT`
- 路径：`/api/accounts/{accountId}`
- 函数名：`updateTradingAccount`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| accountId | number | 是 | 账户ID（路径参数） |
| session_token | string | 是 | 会话令牌（查询参数） |
| name | string | 否 | 账户名称 |
| model | string | 否 | AI模型名称 |
| base_url | string | 否 | API基础URL |
| api_key | string | 否 | API密钥 |
| auto_trading_enabled | boolean | 否 | 是否启用自动交易 |

**请求示例**
```json
{
  "name": "Updated GPT Trader",
  "model": "gpt-4o",
  "auto_trading_enabled": false
}
```

**响应数据结构**
```typescript
{
  id: number
  user_id: number
  name: string
  model?: string
  base_url?: string
  api_key?: string
  initial_capital: number
  current_cash: number
  frozen_cash: number
  account_type: string
  is_active: boolean
  auto_trading_enabled?: boolean
  wallet_address?: string | null
  has_mainnet_wallet?: boolean
  show_on_dashboard?: boolean
  updated_at: string
}
```

**Mock 响应数据**
```json
{
  "id": 1,
  "user_id": 1,
  "name": "Updated GPT Trader",
  "model": "gpt-4o",
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-****",
  "initial_capital": 100000,
  "current_cash": 125000,
  "frozen_cash": 0,
  "account_type": "AI",
  "is_active": true,
  "auto_trading_enabled": false,
  "wallet_address": null,
  "has_mainnet_wallet": false,
  "show_on_dashboard": true,
  "updated_at": "2026-01-13T10:35:00Z"
}
```

---

### 5.4 删除交易账户（带会话令牌）

使用会话令牌删除交易账户。

**接口信息**
- 方法：`DELETE`
- 路径：`/api/accounts/{accountId}`
- 函数名：`deleteTradingAccount`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| accountId | number | 是 | 账户ID（路径参数） |
| session_token | string | 是 | 会话令牌（查询参数） |

**响应数据结构**
```typescript
{
  success: boolean
  message: string
}
```

**Mock 响应数据**
```json
{
  "success": true,
  "message": "账户已成功删除"
}
```

---

### 5.5 获取账户列表（模拟交易）

获取模拟交易模式下的账户列表，使用硬编码的默认用户。

**接口信息**
- 方法：`GET`
- 路径：`/api/account/list`
- 函数名：`getAccounts`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| include_hidden | boolean | 否 | 是否包含隐藏账户，默认false |

**响应数据结构**
```typescript
{
  accounts: Array<{
    id: number
    user_id: number
    name: string
    model?: string
    base_url?: string
    api_key?: string
    initial_capital: number
    current_cash: number
    frozen_cash: number
    account_type: string
    is_active: boolean
    auto_trading_enabled?: boolean
    wallet_address?: string | null
    has_mainnet_wallet?: boolean
    show_on_dashboard?: boolean
  }>
}
```

**Mock 响应数据**
```json
{
  "accounts": [
    {
      "id": 1,
      "user_id": 1,
      "name": "GPT Trader",
      "model": "gpt-4-turbo",
      "base_url": "https://api.openai.com/v1",
      "api_key": "sk-****",
      "initial_capital": 100000,
      "current_cash": 125000,
      "frozen_cash": 0,
      "account_type": "AI",
      "is_active": true,
      "auto_trading_enabled": true,
      "wallet_address": null,
      "has_mainnet_wallet": false,
      "show_on_dashboard": true
    },
    {
      "id": 2,
      "user_id": 1,
      "name": "Claude Analyst",
      "model": "claude-3-opus",
      "base_url": "https://api.anthropic.com/v1",
      "api_key": "sk-ant-****",
      "initial_capital": 50000,
      "current_cash": 48500,
      "frozen_cash": 0,
      "account_type": "AI",
      "is_active": true,
      "auto_trading_enabled": false,
      "wallet_address": null,
      "has_mainnet_wallet": false,
      "show_on_dashboard": true
    },
    {
      "id": 3,
      "user_id": 1,
      "name": "Hidden Account",
      "model": "gpt-3.5-turbo",
      "base_url": "https://api.openai.com/v1",
      "api_key": "sk-****",
      "initial_capital": 20000,
      "current_cash": 19500,
      "frozen_cash": 0,
      "account_type": "AI",
      "is_active": true,
      "auto_trading_enabled": false,
      "wallet_address": null,
      "has_mainnet_wallet": false,
      "show_on_dashboard": false
    }
  ]
}
```

---

### 5.6 更新仪表板可见性

批量更新账户在仪表板上的显示状态。

**接口信息**
- 方法：`PATCH`
- 路径：`/api/account/dashboard-visibility`
- 函数名：`updateDashboardVisibility`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| updates | array | 是 | 更新数组，每个元素包含 account_id 和 show_on_dashboard |

**请求示例**
```json
{
  "updates": [
    {
      "account_id": 1,
      "show_on_dashboard": true
    },
    {
      "account_id": 2,
      "show_on_dashboard": false
    },
    {
      "account_id": 3,
      "show_on_dashboard": true
    }
  ]
}
```

**响应数据结构**
```typescript
{
  success: boolean
  updated_count: number
  updates: Array<{
    account_id: number
    show_on_dashboard: boolean
  }>
}
```

**Mock 响应数据**
```json
{
  "success": true,
  "updated_count": 3,
  "updates": [
    {
      "account_id": 1,
      "show_on_dashboard": true
    },
    {
      "account_id": 2,
      "show_on_dashboard": false
    },
    {
      "account_id": 3,
      "show_on_dashboard": true
    }
  ]
}
```

---

### 5.7 获取账户概览

获取所有账户的概览信息。

**接口信息**
- 方法：`GET`
- 路径：`/api/account/overview`
- 函数名：`getOverview`

**请求参数**
无

**响应数据结构**
```typescript
{
  total_accounts: number
  active_accounts: number
  total_assets: number
  total_pnl: number
  total_return_percent: number
  accounts: Array<{
    id: number
    name: string
    initial_capital: number
    current_assets: number
    pnl: number
    return_percent: number
  }>
}
```

**Mock 响应数据**
```json
{
  "total_accounts": 3,
  "active_accounts": 3,
  "total_assets": 193000,
  "total_pnl": 23000,
  "total_return_percent": 13.52,
  "accounts": [
    {
      "id": 1,
      "name": "GPT Trader",
      "initial_capital": 100000,
      "current_assets": 125000,
      "pnl": 25000,
      "return_percent": 25.0
    },
    {
      "id": 2,
      "name": "Claude Analyst",
      "initial_capital": 50000,
      "current_assets": 48500,
      "pnl": -1500,
      "return_percent": -3.0
    },
    {
      "id": 3,
      "name": "Hidden Account",
      "initial_capital": 20000,
      "current_assets": 19500,
      "pnl": -500,
      "return_percent": -2.5
    }
  ]
}
```

---

### 5.8 创建账户（模拟交易）

在模拟交易模式下创建新账户。

**接口信息**
- 方法：`POST`
- 路径：`/api/account/`
- 函数名：`createAccount`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | string | 是 | 账户名称 |
| model | string | 否 | AI模型名称 |
| base_url | string | 否 | API基础URL |
| api_key | string | 否 | API密钥 |
| account_type | string | 否 | 账户类型，默认"AI" |
| initial_capital | number | 否 | 初始资金，默认10000 |
| auto_trading_enabled | boolean | 否 | 是否启用自动交易，默认true |

**请求示例**
```json
{
  "name": "New AI Trader",
  "model": "gpt-4-turbo",
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-proj-xxxxx",
  "account_type": "AI",
  "initial_capital": 100000,
  "auto_trading_enabled": true
}
```

**响应数据结构**
```typescript
{
  id: number
  user_id: number
  name: string
  model?: string
  base_url?: string
  api_key?: string
  initial_capital: number
  current_cash: number
  frozen_cash: number
  account_type: string
  is_active: boolean
  auto_trading_enabled?: boolean
  wallet_address?: string | null
  has_mainnet_wallet?: boolean
  show_on_dashboard?: boolean
  created_at: string
}
```

**Mock 响应数据**
```json
{
  "id": 4,
  "user_id": 1,
  "name": "New AI Trader",
  "model": "gpt-4-turbo",
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-proj-xxxxx",
  "initial_capital": 100000,
  "current_cash": 100000,
  "frozen_cash": 0,
  "account_type": "AI",
  "is_active": true,
  "auto_trading_enabled": true,
  "wallet_address": null,
  "has_mainnet_wallet": false,
  "show_on_dashboard": true,
  "created_at": "2026-01-13T10:40:00Z"
}
```

---

### 5.9 更新账户（模拟交易）

在模拟交易模式下更新账户信息。

**接口信息**
- 方法：`PUT`
- 路径：`/api/account/{accountId}`
- 函数名：`updateAccount`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| accountId | number | 是 | 账户ID（路径参数） |
| name | string | 否 | 账户名称 |
| model | string | 否 | AI模型名称 |
| base_url | string | 否 | API基础URL |
| api_key | string | 否 | API密钥 |
| auto_trading_enabled | boolean | 否 | 是否启用自动交易 |

**请求示例**
```json
{
  "name": "Updated AI Trader",
  "model": "gpt-4o",
  "auto_trading_enabled": false
}
```

**响应数据结构**
```typescript
{
  id: number
  user_id: number
  name: string
  model?: string
  base_url?: string
  api_key?: string
  initial_capital: number
  current_cash: number
  frozen_cash: number
  account_type: string
  is_active: boolean
  auto_trading_enabled?: boolean
  wallet_address?: string | null
  has_mainnet_wallet?: boolean
  show_on_dashboard?: boolean
  updated_at: string
}
```

**Mock 响应数据**
```json
{
  "id": 1,
  "user_id": 1,
  "name": "Updated AI Trader",
  "model": "gpt-4o",
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-****",
  "initial_capital": 100000,
  "current_cash": 125000,
  "frozen_cash": 0,
  "account_type": "AI",
  "is_active": true,
  "auto_trading_enabled": false,
  "wallet_address": null,
  "has_mainnet_wallet": false,
  "show_on_dashboard": true,
  "updated_at": "2026-01-13T10:45:00Z"
}
```

---

### 5.10 测试LLM连接

测试LLM API连接是否正常。

**接口信息**
- 方法：`POST`
- 路径：`/api/account/test-llm`
- 函数名：`testLLMConnection`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model | string | 否 | 模型名称 |
| base_url | string | 否 | API基础URL |
| api_key | string | 否 | API密钥 |

**请求示例**
```json
{
  "model": "gpt-4-turbo",
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-proj-xxxxx"
}
```

**响应数据结构**
```typescript
{
  success: boolean
  message: string
  response?: any
}
```

**Mock 响应数据**
```json
{
  "success": true,
  "message": "LLM连接测试成功",
  "response": {
    "model": "gpt-4-turbo",
    "latency_ms": 234,
    "status": "ok"
  }
}
```

---

## 6. 策略配置

### 6.1 获取账户策略配置

获取指定账户的策略配置信息。

**接口信息**
- 方法：`GET`
- 路径：`/api/account/{accountId}/strategy`
- 函数名：`getAccountStrategy`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| accountId | number | 是 | 账户ID（路径参数） |

**响应数据结构**
```typescript
{
  trigger_mode: 'realtime' | 'interval' | 'tick_batch'
  interval_seconds?: number | null
  tick_batch_size?: number | null
  enabled: boolean
  last_trigger_at?: string | null
}
```

**Mock 响应数据**
```json
{
  "trigger_mode": "interval",
  "interval_seconds": 300,
  "tick_batch_size": null,
  "enabled": true,
  "last_trigger_at": "2026-01-13T10:30:00Z"
}
```

---

### 6.2 更新账户策略配置

更新指定账户的策略配置。

**接口信息**
- 方法：`PUT`
- 路径：`/api/account/{accountId}/strategy`
- 函数名：`updateAccountStrategy`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| accountId | number | 是 | 账户ID（路径参数） |
| trigger_mode | string | 是 | 触发模式：realtime/interval/tick_batch |
| interval_seconds | number | 否 | 间隔秒数（interval模式） |
| tick_batch_size | number | 否 | 批量大小（tick_batch模式） |
| enabled | boolean | 是 | 是否启用 |

**请求示例**
```json
{
  "trigger_mode": "interval",
  "interval_seconds": 600,
  "tick_batch_size": null,
  "enabled": true
}
```

**响应数据结构**
```typescript
{
  trigger_mode: 'realtime' | 'interval' | 'tick_batch'
  interval_seconds?: number | null
  tick_batch_size?: number | null
  enabled: boolean
  last_trigger_at?: string | null
  updated_at: string
}
```

**Mock 响应数据**
```json
{
  "trigger_mode": "interval",
  "interval_seconds": 600,
  "tick_batch_size": null,
  "enabled": true,
  "last_trigger_at": "2026-01-13T10:30:00Z",
  "updated_at": "2026-01-13T10:50:00Z"
}
```

---

## 7. 提示词模板管理

### 7.1 获取提示词模板列表

获取所有提示词模板和绑定关系。

**接口信息**
- 方法：`GET`
- 路径：`/api/prompts`
- 函数名：`getPromptTemplates`

**请求参数**
无

**响应数据结构**
```typescript
{
  templates: Array<{
    id: number
    key: string
    name: string
    description?: string | null
    templateText: string
    systemTemplateText: string
    isSystem: string
    isDeleted: string
    createdBy: string
    updatedBy?: string | null
    createdAt?: string | null
    updatedAt?: string | null
  }>
  bindings: Array<{
    id: number
    accountId: number
    accountName: string
    accountModel?: string | null
    promptTemplateId: number
    promptKey: string
    promptName: string
    updatedBy?: string | null
    updatedAt?: string | null
  }>
}
```

**Mock 响应数据**
```json
{
  "templates": [
    {
      "id": 1,
      "key": "default_trading",
      "name": "默认交易提示词",
      "description": "适用于大多数交易场景的通用提示词",
      "templateText": "当前市场状况：{{market_data}}\n账户余额：{{balance}}\n持仓情况：{{positions}}\n请分析并给出交易建议。",
      "systemTemplateText": "你是一个专业的交易分析师，基于市场数据和账户状况提供交易建议。",
      "isSystem": "true",
      "isDeleted": "false",
      "createdBy": "system",
      "updatedBy": null,
      "createdAt": "2025-06-01T00:00:00Z",
      "updatedAt": null
    },
    {
      "id": 2,
      "key": "aggressive_trading",
      "name": "激进交易提示词",
      "description": "适用于追求高收益的激进交易策略",
      "templateText": "当前市场状况：{{market_data}}\n账户余额：{{balance}}\n持仓情况：{{positions}}\n请基于激进策略分析并给出交易建议，关注短期波动机会。",
      "systemTemplateText": "你是一个激进交易专家，善于捕捉短期市场波动机会。",
      "isSystem": "false",
      "isDeleted": "false",
      "createdBy": "admin",
      "updatedBy": "trader001",
      "createdAt": "2025-07-15T10:00:00Z",
      "updatedAt": "2025-12-01T15:30:00Z"
    }
  ],
  "bindings": [
    {
      "id": 1,
      "accountId": 1,
      "accountName": "GPT Trader",
      "accountModel": "gpt-4-turbo",
      "promptTemplateId": 1,
      "promptKey": "default_trading",
      "promptName": "默认交易提示词",
      "updatedBy": "trader001",
      "updatedAt": "2026-01-10T10:00:00Z"
    },
    {
      "id": 2,
      "accountId": 2,
      "accountName": "Claude Analyst",
      "accountModel": "claude-3-opus",
      "promptTemplateId": 2,
      "promptKey": "aggressive_trading",
      "promptName": "激进交易提示词",
      "updatedBy": "trader001",
      "updatedAt": "2026-01-12T14:20:00Z"
    }
  ]
}
```

---

### 7.2 更新提示词模板

更新指定key的提示词模板内容。

**接口信息**
- 方法：`PUT`
- 路径：`/api/prompts/{key}`
- 函数名：`updatePromptTemplate`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| key | string | 是 | 提示词模板key（路径参数） |
| templateText | string | 是 | 模板文本内容 |
| description | string | 否 | 描述信息 |
| updatedBy | string | 否 | 更新人 |

**请求示例**
```json
{
  "templateText": "更新后的模板内容：{{market_data}}",
  "description": "更新后的描述",
  "updatedBy": "trader001"
}
```

**响应数据结构**
```typescript
{
  id: number
  key: string
  name: string
  description?: string | null
  templateText: string
  systemTemplateText: string
  isSystem: string
  isDeleted: string
  createdBy: string
  updatedBy?: string | null
  createdAt?: string | null
  updatedAt?: string | null
}
```

**Mock 响应数据**
```json
{
  "id": 1,
  "key": "default_trading",
  "name": "默认交易提示词",
  "description": "更新后的描述",
  "templateText": "更新后的模板内容：{{market_data}}\n账户余额：{{balance}}\n持仓情况：{{positions}}\n请分析并给出交易建议。",
  "systemTemplateText": "你是一个专业的交易分析师，基于市场数据和账户状况提供交易建议。",
  "isSystem": "true",
  "isDeleted": "false",
  "createdBy": "system",
  "updatedBy": "trader001",
  "createdAt": "2025-06-01T00:00:00Z",
  "updatedAt": "2026-01-13T11:00:00Z"
}
```

---

### 7.3 创建提示词模板

创建新的提示词模板。

**接口信息**
- 方法：`POST`
- 路径：`/api/prompts`
- 函数名：`createPromptTemplate`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | string | 是 | 模板名称 |
| description | string | 否 | 描述信息 |
| templateText | string | 否 | 模板文本内容 |
| createdBy | string | 否 | 创建人 |

**请求示例**
```json
{
  "name": "保守交易提示词",
  "description": "适用于追求稳健收益的保守交易策略",
  "templateText": "当前市场状况：{{market_data}}\n账户余额：{{balance}}\n持仓情况：{{positions}}\n请基于保守策略分析并给出交易建议，注重风险控制。",
  "createdBy": "trader001"
}
```

**响应数据结构**
```typescript
{
  id: number
  key: string
  name: string
  description?: string | null
  templateText: string
  systemTemplateText: string
  isSystem: string
  isDeleted: string
  createdBy: string
  updatedBy?: string | null
  createdAt?: string | null
  updatedAt?: string | null
}
```

**Mock 响应数据**
```json
{
  "id": 3,
  "key": "conservative_trading",
  "name": "保守交易提示词",
  "description": "适用于追求稳健收益的保守交易策略",
  "templateText": "当前市场状况：{{market_data}}\n账户余额：{{balance}}\n持仓情况：{{positions}}\n请基于保守策略分析并给出交易建议，注重风险控制。",
  "systemTemplateText": "你是一个保守交易专家，注重风险控制和稳健收益。",
  "isSystem": "false",
  "isDeleted": "false",
  "createdBy": "trader001",
  "updatedBy": null,
  "createdAt": "2026-01-13T11:05:00Z",
  "updatedAt": null
}
```

---

### 7.4 复制提示词模板

复制现有的提示词模板。

**接口信息**
- 方法：`POST`
- 路径：`/api/prompts/{templateId}/copy`
- 函数名：`copyPromptTemplate`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| templateId | number | 是 | 模板ID（路径参数） |
| newName | string | 否 | 新模板名称 |
| createdBy | string | 否 | 创建人 |

**请求示例**
```json
{
  "newName": "默认交易提示词副本",
  "createdBy": "trader001"
}
```

**响应数据结构**
```typescript
{
  id: number
  key: string
  name: string
  description?: string | null
  templateText: string
  systemTemplateText: string
  isSystem: string
  isDeleted: string
  createdBy: string
  updatedBy?: string | null
  createdAt?: string | null
  updatedAt?: string | null
}
```

**Mock 响应数据**
```json
{
  "id": 4,
  "key": "default_trading_copy",
  "name": "默认交易提示词副本",
  "description": "适用于大多数交易场景的通用提示词",
  "templateText": "当前市场状况：{{market_data}}\n账户余额：{{balance}}\n持仓情况：{{positions}}\n请分析并给出交易建议。",
  "systemTemplateText": "你是一个专业的交易分析师，基于市场数据和账户状况提供交易建议。",
  "isSystem": "false",
  "isDeleted": "false",
  "createdBy": "trader001",
  "updatedBy": null,
  "createdAt": "2026-01-13T11:10:00Z",
  "updatedAt": null
}
```

---

### 7.5 删除提示词模板

删除指定的提示词模板。

**接口信息**
- 方法：`DELETE`
- 路径：`/api/prompts/{templateId}`
- 函数名：`deletePromptTemplate`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| templateId | number | 是 | 模板ID（路径参数） |

**响应数据结构**
```typescript
{
  success: boolean
  message: string
}
```

**Mock 响应数据**
```json
{
  "success": true,
  "message": "提示词模板已成功删除"
}
```

---

### 7.6 更新提示词模板名称

更新提示词模板的名称和描述。

**接口信息**
- 方法：`PATCH`
- 路径：`/api/prompts/{templateId}/name`
- 函数名：`updatePromptTemplateName`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| templateId | number | 是 | 模板ID（路径参数） |
| name | string | 是 | 新模板名称 |
| description | string | 否 | 新描述信息 |
| updatedBy | string | 否 | 更新人 |

**请求示例**
```json
{
  "name": "更新后的模板名称",
  "description": "更新后的描述信息",
  "updatedBy": "trader001"
}
```

**响应数据结构**
```typescript
{
  id: number
  key: string
  name: string
  description?: string | null
  templateText: string
  systemTemplateText: string
  isSystem: string
  isDeleted: string
  createdBy: string
  updatedBy?: string | null
  createdAt?: string | null
  updatedAt?: string | null
}
```

**Mock 响应数据**
```json
{
  "id": 1,
  "key": "default_trading",
  "name": "更新后的模板名称",
  "description": "更新后的描述信息",
  "templateText": "当前市场状况：{{market_data}}\n账户余额：{{balance}}\n持仓情况：{{positions}}\n请分析并给出交易建议。",
  "systemTemplateText": "你是一个专业的交易分析师，基于市场数据和账户状况提供交易建议。",
  "isSystem": "true",
  "isDeleted": "false",
  "createdBy": "system",
  "updatedBy": "trader001",
  "createdAt": "2025-06-01T00:00:00Z",
  "updatedAt": "2026-01-13T11:15:00Z"
}
```

---

### 7.7 创建或更新提示词绑定

为账户创建或更新提示词绑定关系。

**接口信息**
- 方法：`POST`
- 路径：`/api/prompts/bindings`
- 函数名：`upsertPromptBinding`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | number | 否 | 绑定ID（更新时必填） |
| accountId | number | 是 | 账户ID |
| promptTemplateId | number | 是 | 提示词模板ID |
| updatedBy | string | 否 | 更新人 |

**请求示例**
```json
{
  "accountId": 1,
  "promptTemplateId": 2,
  "updatedBy": "trader001"
}
```

**响应数据结构**
```typescript
{
  id: number
  accountId: number
  accountName: string
  accountModel?: string | null
  promptTemplateId: number
  promptKey: string
  promptName: string
  updatedBy?: string | null
  updatedAt?: string | null
}
```

**Mock 响应数据**
```json
{
  "id": 3,
  "accountId": 1,
  "accountName": "GPT Trader",
  "accountModel": "gpt-4-turbo",
  "promptTemplateId": 2,
  "promptKey": "aggressive_trading",
  "promptName": "激进交易提示词",
  "updatedBy": "trader001",
  "updatedAt": "2026-01-13T11:20:00Z"
}
```

---

### 7.8 删除提示词绑定

删除指定的提示词绑定关系。

**接口信息**
- 方法：`DELETE`
- 路径：`/api/prompts/bindings/{bindingId}`
- 函数名：`deletePromptBinding`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| bindingId | number | 是 | 绑定ID（路径参数） |

**响应数据结构**
```typescript
{
  success: boolean
  message: string
}
```

**Mock 响应数据**
```json
{
  "success": true,
  "message": "提示词绑定已成功删除"
}
```

---

### 7.9 获取变量参考文档

获取提示词模板中可用的变量参考文档。

**接口信息**
- 方法：`GET`
- 路径：`/api/prompts/variables-reference`
- 函数名：`getVariablesReference`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| lang | string | 否 | 语言，默认"en" |

**响应数据结构**
```typescript
{
  content: string
}
```

**Mock 响应数据**
```json
{
  "content": "# 提示词变量参考\n\n## 市场数据变量\n- `{{market_data}}`: 当前市场状况\n- `{{symbol_prices}}`: 各交易对价格\n\n## 账户变量\n- `{{balance}}`: 账户余额\n- `{{positions}}`: 持仓情况\n- `{{pnl}}`: 盈亏情况\n\n## 技术指标变量\n- `{{rsi}}`: RSI指标\n- `{{macd}}`: MACD指标\n- `{{ma}}`: 移动平均线"
}
```

---

### 7.10 预览提示词

预览提示词模板的填充效果。

**接口信息**
- 方法：`POST`
- 路径：`/api/prompts/preview`
- 函数名：`previewPrompt`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| templateText | string | 否 | 直接使用的模板文本 |
| promptTemplateKey | string | 否 | 数据库中的模板key（与templateText二选一） |
| accountIds | array | 是 | 账户ID数组 |
| symbols | array | 否 | 交易符号数组 |

**请求示例**
```json
{
  "templateText": "当前市场状况：{{market_data}}\n账户余额：{{balance}}\n持仓情况：{{positions}}",
  "accountIds": [1, 2],
  "symbols": ["BTC", "ETH"]
}
```

**响应数据结构**
```typescript
{
  previews: Array<{
    accountId: number
    accountName: string
    symbols: string[]
    filledPrompt: string
  }>
}
```

**Mock 响应数据**
```json
{
  "previews": [
    {
      "accountId": 1,
      "accountName": "GPT Trader",
      "symbols": ["BTC", "ETH"],
      "filledPrompt": "当前市场状况：BTC $67,542.50 (+1.86%), ETH $3,456.78 (+2.15%)\n账户余额：$125,000\n持仓情况：BTC 0.5, ETH 10.0"
    },
    {
      "accountId": 2,
      "accountName": "Claude Analyst",
      "symbols": ["BTC", "ETH"],
      "filledPrompt": "当前市场状况：BTC $67,542.50 (+1.86%), ETH $3,456.78 (+2.15%)\n账户余额：$48,500\n持仓情况：BTC 0.2, ETH 5.0"
    }
  ]
}
```

---

## 8. Alpha Arena 聚合数据

### 8.1 获取Arena交易记录

获取Alpha Arena的交易记录，支持多种过滤条件。

**接口信息**
- 方法：`GET`
- 路径：`/api/arena/trades`
- 函数名：`getArenaTrades`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| limit | number | 否 | 返回数量限制 |
| account_id | number | 否 | 账户ID过滤 |
| trading_mode | string | 否 | 交易模式过滤 |
| wallet_address | string | 否 | 钱包地址过滤 |
| symbol | string | 否 | 交易符号过滤 |

**响应数据结构**
```typescript
{
  generated_at: string
  accounts: Array<{
    account_id: number
    name: string
    model?: string | null
  }>
  trades: Array<{
    trade_id: number
    order_id?: number | null
    order_no?: string | null
    account_id: number
    account_name: string
    model?: string | null
    side: string
    direction: string
    symbol: string
    market: string
    price: number
    quantity: number
    notional: number
    commission: number
    trade_time?: string | null
    wallet_address?: string | null
    signal_trigger_id?: number | null
    prompt_template_id?: number | null
    prompt_template_name?: string | null
    related_orders?: Array<{
      type: 'sl' | 'tp'
      price: number
      quantity: number
      notional: number
      commission: number
      trade_time?: string | null
    }>
  }>
}
```

**Mock 响应数据**
```json
{
  "generated_at": "2026-01-13T12:00:00Z",
  "accounts": [
    {
      "account_id": 1,
      "name": "GPT Trader",
      "model": "gpt-4-turbo"
    },
    {
      "account_id": 2,
      "name": "Claude Analyst",
      "model": "claude-3-opus"
    }
  ],
  "trades": [
    {
      "trade_id": 1001,
      "order_id": 12345,
      "order_no": "ORD-20260113-001",
      "account_id": 1,
      "account_name": "GPT Trader",
      "model": "gpt-4-turbo",
      "side": "buy",
      "direction": "long",
      "symbol": "BTC",
      "market": "hyperliquid",
      "price": 67500.00,
      "quantity": 0.5,
      "notional": 33750.00,
      "commission": 33.75,
      "trade_time": "2026-01-13T10:15:00Z",
      "wallet_address": "0x1234...5678",
      "signal_trigger_id": 501,
      "prompt_template_id": 1,
      "prompt_template_name": "默认交易提示词",
      "related_orders": [
        {
          "type": "tp",
          "price": 69000.00,
          "quantity": 0.5,
          "notional": 34500.00,
          "commission": 34.50,
          "trade_time": "2026-01-13T11:30:00Z"
        }
      ]
    },
    {
      "trade_id": 1002,
      "order_id": 12346,
      "order_no": "ORD-20260113-002",
      "account_id": 2,
      "account_name": "Claude Analyst",
      "model": "claude-3-opus",
      "side": "sell",
      "direction": "short",
      "symbol": "ETH",
      "market": "hyperliquid",
      "price": 3450.00,
      "quantity": 10.0,
      "notional": 34500.00,
      "commission": 34.50,
      "trade_time": "2026-01-13T09:45:00Z",
      "wallet_address": "0xabcd...efgh",
      "signal_trigger_id": 502,
      "prompt_template_id": 2,
      "prompt_template_name": "激进交易提示词",
      "related_orders": [
        {
          "type": "sl",
          "price": 3500.00,
          "quantity": 10.0,
          "notional": 35000.00,
          "commission": 35.00,
          "trade_time": "2026-01-13T10:00:00Z"
        }
      ]
    }
  ]
}
```

---

### 8.2 更新Arena盈亏

触发Arena盈亏数据的更新同步。

**接口信息**
- 方法：`POST`
- 路径：`/api/arena/update-pnl`
- 函数名：`updateArenaPnl`

**请求参数**
无

**响应数据结构**
```typescript
{
  success: boolean
  message?: string
  environments: Record<string, {
    fills_count: number
    unique_orders: number
    trades_updated: number
    decisions_updated: number
    skipped: number
  }>
  errors: string[]
}
```

**Mock 响应数据**
```json
{
  "success": true,
  "message": "盈亏数据更新成功",
  "environments": {
    "paper": {
      "fills_count": 150,
      "unique_orders": 120,
      "trades_updated": 150,
      "decisions_updated": 145,
      "skipped": 5
    },
    "mainnet": {
      "fills_count": 75,
      "unique_orders": 60,
      "trades_updated": 75,
      "decisions_updated": 70,
      "skipped": 5
    }
  },
  "errors": []
}
```

---

### 8.3 检查盈亏同步状态

检查Arena盈亏数据是否需要同步。

**接口信息**
- 方法：`GET`
- 路径：`/api/arena/check-pnl-status`
- 函数名：`checkPnlSyncStatus`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| trading_mode | string | 否 | 交易模式过滤 |

**响应数据结构**
```typescript
{
  needs_sync: boolean
  unsync_count: number
}
```

**Mock 响应数据**
```json
{
  "needs_sync": true,
  "unsync_count": 25
}
```

---

### 8.4 获取Arena模型聊天记录

获取AI模型的决策聊天记录。

**接口信息**
- 方法：`GET`
- 路径：`/api/arena/model-chat`
- 函数名：`getArenaModelChat`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| limit | number | 否 | 返回数量限制 |
| account_id | number | 否 | 账户ID过滤 |
| trading_mode | string | 否 | 交易模式过滤 |
| wallet_address | string | 否 | 钱包地址过滤 |
| before_time | string | 否 | 时间过滤（获取此时间之前的记录） |
| symbol | string | 否 | 交易符号过滤 |

**响应数据结构**
```typescript
{
  generated_at: string
  entries: Array<{
    id: number
    account_id: number
    account_name: string
    model?: string | null
    operation: string
    symbol?: string | null
    reason: string
    executed: boolean
    prev_portion: number
    target_portion: number
    total_balance: number
    order_id?: number | null
    decision_time?: string | null
    trigger_mode?: 'realtime' | 'interval' | 'tick_batch' | null
    strategy_enabled?: boolean
    last_trigger_at?: string | null
    trigger_latency_seconds?: number | null
    prompt_snapshot?: string | null
    reasoning_snapshot?: string | null
    decision_snapshot?: string | null
    wallet_address?: string | null
    signal_trigger_id?: number | null
    prompt_template_id?: number | null
    prompt_template_name?: string | null
  }>
}
```

**Mock 响应数据**
```json
{
  "generated_at": "2026-01-13T12:05:00Z",
  "entries": [
    {
      "id": 1,
      "account_id": 1,
      "account_name": "GPT Trader",
      "model": "gpt-4-turbo",
      "operation": "buy",
      "symbol": "BTC",
      "reason": "BTC突破67000阻力位，RSI指标显示超买信号缓解，建议加仓",
      "executed": true,
      "prev_portion": 0.3,
      "target_portion": 0.5,
      "total_balance": 125000,
      "order_id": 12345,
      "decision_time": "2026-01-13T10:15:00Z",
      "trigger_mode": "interval",
      "strategy_enabled": true,
      "last_trigger_at": "2026-01-13T10:15:00Z",
      "trigger_latency_seconds": 2.5,
      "prompt_snapshot": "当前市场状况：BTC $67,542.50 (+1.86%), ETH $3,456.78 (+2.15%)\n账户余额：$125,000\n持仓情况：BTC 0.3, ETH 10.0",
      "reasoning_snapshot": "基于技术分析：\n1. BTC成功突破67000阻力位\n2. RSI从75降至68，超买信号缓解\n3. 成交量放大，显示买盘强劲\n4. MACD金叉形成",
      "decision_snapshot": "{\"operation\":\"buy\",\"symbol\":\"BTC\",\"portion\":0.5,\"reason\":\"BTC突破67000阻力位，RSI指标显示超买信号缓解，建议加仓\"}",
      "wallet_address": "0x1234...5678",
      "signal_trigger_id": 501,
      "prompt_template_id": 1,
      "prompt_template_name": "默认交易提示词"
    },
    {
      "id": 2,
      "account_id": 2,
      "account_name": "Claude Analyst",
      "model": "claude-3-opus",
      "operation": "sell",
      "symbol": "ETH",
      "reason": "ETH在3500附近遇到强阻力，短期回调风险加大，建议减仓",
      "executed": true,
      "prev_portion": 0.6,
      "target_portion": 0.3,
      "total_balance": 48500,
      "order_id": 12346,
      "decision_time": "2026-01-13T09:45:00Z",
      "trigger_mode": "realtime",
      "strategy_enabled": true,
      "last_trigger_at": "2026-01-13T09:45:00Z",
      "trigger_latency_seconds": 1.8,
      "prompt_snapshot": "当前市场状况：BTC $67,542.50 (+1.86%), ETH $3,456.78 (+2.15%)\n账户余额：$48,500\n持仓情况：BTC 0.2, ETH 5.0",
      "reasoning_snapshot": "基于技术分析：\n1. ETH在3500附近多次受阻\n2. RSI达到72，超买信号明显\n3. 成交量萎缩，买盘不足\n4. MACD顶背离形成",
      "decision_snapshot": "{\"operation\":\"sell\",\"symbol\":\"ETH\",\"portion\":0.3,\"reason\":\"ETH在3500附近遇到强阻力，短期回调风险加大，建议减仓\"}",
      "wallet_address": "0xabcd...efgh",
      "signal_trigger_id": 502,
      "prompt_template_id": 2,
      "prompt_template_name": "激进交易提示词"
    }
  ]
}
```

---

### 8.5 获取模型聊天快照

获取指定决策的详细快照信息。

**接口信息**
- 方法：`GET`
- 路径：`/api/arena/model-chat/{decisionId}/snapshots`
- 函数名：`getModelChatSnapshots`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| decisionId | number | 是 | 决策ID（路径参数） |

**响应数据结构**
```typescript
{
  id: number
  prompt_snapshot?: string | null
  reasoning_snapshot?: string | null
  decision_snapshot?: string | null
  error?: string
}
```

**Mock 响应数据**
```json
{
  "id": 1,
  "prompt_snapshot": "当前市场状况：BTC $67,542.50 (+1.86%), ETH $3,456.78 (+2.15%)\n账户余额：$125,000\n持仓情况：BTC 0.3, ETH 10.0\n技术指标：\n- BTC RSI: 68\n- BTC MACD: 金叉\n- ETH RSI: 72\n- ETH MACD: 顶背离",
  "reasoning_snapshot": "基于技术分析：\n1. BTC成功突破67000阻力位，显示强势\n2. RSI从75降至68，超买信号缓解，仍有上涨空间\n3. 成交量放大至日均1.5倍，显示买盘强劲\n4. MACD金叉形成，动能增强\n5. 建议将BTC仓位从30%提升至50%\n\n风险评估：\n- 止损位：66000\n- 目标位：69000\n- 风险收益比：1:2",
  "decision_snapshot": "{\"operation\":\"buy\",\"symbol\":\"BTC\",\"portion\":0.5,\"reason\":\"BTC突破67000阻力位，RSI指标显示超买信号缓解，建议加仓\",\"stop_loss\":66000,\"target_price\":69000,\"risk_reward_ratio\":2}",
  "error": null
}
```

---

### 8.6 获取Arena持仓信息

获取Arena的持仓信息。

**接口信息**
- 方法：`GET`
- 路径：`/api/arena/positions`
- 函数名：`getArenaPositions`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account_id | number | 否 | 账户ID过滤 |
| trading_mode | string | 否 | 交易模式过滤 |

**响应数据结构**
```typescript
{
  generated_at: string
  accounts: Array<{
    account_id: number
    account_name: string
    model?: string | null
    environment?: string | null
    wallet_address?: string | null
    total_unrealized_pnl: number
    available_cash: number
    used_margin?: number | null
    positions: Array<{
      id: number
      symbol: string
      name: string
      market: string
      side: string
      quantity: number
      avg_cost: number
      current_price: number
      notional: number
      current_value: number
      unrealized_pnl: number
      leverage?: number | null
      margin_used?: number | null
      return_on_equity?: number | null
      percentage?: number | null
      margin_mode?: string | null
      liquidation_px?: number | null
      max_leverage?: number | null
      leverage_type?: string | null
    }>
    total_assets: number
    initial_capital: number
    total_return?: number | null
    margin_usage_percent?: number | null
    margin_mode?: string | null
  }>
}
```

**Mock 响应数据**
```json
{
  "generated_at": "2026-01-13T12:10:00Z",
  "accounts": [
    {
      "account_id": 1,
      "account_name": "GPT Trader",
      "model": "gpt-4-turbo",
      "environment": "paper",
      "wallet_address": null,
      "total_unrealized_pnl": 2500.00,
      "available_cash": 75000.00,
      "used_margin": 50000.00,
      "positions": [
        {
          "id": 1,
          "symbol": "BTC",
          "name": "Bitcoin",
          "market": "hyperliquid",
          "side": "long",
          "quantity": 0.5,
          "avg_cost": 66000.00,
          "current_price": 67500.00,
          "notional": 33750.00,
          "current_value": 33750.00,
          "unrealized_pnl": 750.00,
          "leverage": 2.0,
          "margin_used": 16875.00,
          "return_on_equity": 4.44,
          "percentage": 27.0,
          "margin_mode": "cross",
          "liquidation_px": 63000.00,
          "max_leverage": 20.0,
          "leverage_type": "isolated"
        },
        {
          "id": 2,
          "symbol": "ETH",
          "name": "Ethereum",
          "market": "hyperliquid",
          "side": "long",
          "quantity": 10.0,
          "avg_cost": 3300.00,
          "current_price": 3456.78,
          "notional": 34567.80,
          "current_value": 34567.80,
          "unrealized_pnl": 1567.80,
          "leverage": 3.0,
          "margin_used": 11522.60,
          "return_on_equity": 13.61,
          "percentage": 46.1,
          "margin_mode": "cross",
          "liquidation_px": 3000.00,
          "max_leverage": 20.0,
          "leverage_type": "isolated"
        }
      ],
      "total_assets": 125000.00,
      "initial_capital": 100000.00,
      "total_return": 25.0,
      "margin_usage_percent": 40.0,
      "margin_mode": "cross"
    },
    {
      "account_id": 2,
      "account_name": "Claude Analyst",
      "model": "claude-3-opus",
      "environment": "paper",
      "wallet_address": null,
      "total_unrealized_pnl": -1500.00,
      "available_cash": 35000.00,
      "used_margin": 13500.00,
      "positions": [
        {
          "id": 3,
          "symbol": "SOL",
          "name": "Solana",
          "market": "hyperliquid",
          "side": "long",
          "quantity": 100.0,
          "avg_cost": 150.00,
          "current_price": 142.35,
          "notional": 14235.00,
          "current_value": 14235.00,
          "unrealized_pnl": -765.00,
          "leverage": 5.0,
          "margin_used": 2847.00,
          "return_on_equity": -26.87,
          "percentage": 27.8,
          "margin_mode": "cross",
          "liquidation_px": 120.00,
          "max_leverage": 20.0,
          "leverage_type": "isolated"
        }
      ],
      "total_assets": 48500.00,
      "initial_capital": 50000.00,
      "total_return": -3.0,
      "margin_usage_percent": 27.8,
      "margin_mode": "cross"
    }
  ]
}
```

---

### 8.7 获取Arena分析数据

获取Arena的分析统计数据。

**接口信息**
- 方法：`GET`
- 路径：`/api/arena/analytics`
- 函数名：`getArenaAnalytics`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account_id | number | 否 | 账户ID过滤 |

**响应数据结构**
```typescript
{
  generated_at: string
  accounts: Array<{
    account_id: number
    account_name: string
    model?: string | null
    initial_capital: number
    current_cash: number
    positions_value: number
    total_assets: number
    total_pnl: number
    total_return_pct?: number | null
    total_fees: number
    trade_count: number
    total_volume: number
    first_trade_time?: string | null
    last_trade_time?: string | null
    biggest_gain: number
    biggest_loss: number
    win_rate?: number | null
    loss_rate?: number | null
    sharpe_ratio?: number | null
    balance_volatility: number
    decision_count: number
    executed_decisions: number
    decision_execution_rate?: number | null
    avg_target_portion?: number | null
    avg_decision_interval_minutes?: number | null
  }>
  summary: {
    total_assets: number
    total_pnl: number
    total_return_pct?: number | null
    total_fees: number
    total_volume: number
    average_sharpe_ratio?: number | null
  }
}
```

**Mock 响应数据**
```json
{
  "generated_at": "2026-01-13T12:15:00Z",
  "accounts": [
    {
      "account_id": 1,
      "account_name": "GPT Trader",
      "model": "gpt-4-turbo",
      "initial_capital": 100000,
      "current_cash": 75000,
      "positions_value": 50000,
      "total_assets": 125000,
      "total_pnl": 25000,
      "total_return_pct": 25.0,
      "total_fees": 1250.00,
      "trade_count": 156,
      "total_volume": 2850000.00,
      "first_trade_time": "2025-06-15T10:00:00Z",
      "last_trade_time": "2026-01-13T10:15:00Z",
      "biggest_gain": 5250.00,
      "biggest_loss": -2100.00,
      "win_rate": 0.65,
      "loss_rate": 0.35,
      "sharpe_ratio": 2.35,
      "balance_volatility": 0.15,
      "decision_count": 180,
      "executed_decisions": 165,
      "decision_execution_rate": 0.917,
      "avg_target_portion": 0.45,
      "avg_decision_interval_minutes": 45.5
    },
    {
      "account_id": 2,
      "account_name": "Claude Analyst",
      "model": "claude-3-opus",
      "initial_capital": 50000,
      "current_cash": 35000,
      "positions_value": 13500,
      "total_assets": 48500,
      "total_pnl": -1500,
      "total_return_pct": -3.0,
      "total_fees": 675.00,
      "trade_count": 89,
      "total_volume": 1250000.00,
      "first_trade_time": "2025-07-01T14:00:00Z",
      "last_trade_time": "2026-01-13T09:45:00Z",
      "biggest_gain": 1850.00,
      "biggest_loss": -3200.00,
      "win_rate": 0.52,
      "loss_rate": 0.48,
      "sharpe_ratio": 0.85,
      "balance_volatility": 0.22,
      "decision_count": 95,
      "executed_decisions": 88,
      "decision_execution_rate": 0.926,
      "avg_target_portion": 0.52,
      "avg_decision_interval_minutes": 38.2
    }
  ],
  "summary": {
    "total_assets": 173500,
    "total_pnl": 23500,
    "total_return_pct": 13.52,
    "total_fees": 1925.00,
    "total_volume": 4100000.00,
    "average_sharpe_ratio": 1.60
  }
}
```

---

## 9. Hyperliquid 相关

### 9.1 获取Hyperliquid可用符号

获取Hyperliquid平台上可用的交易符号。

**接口信息**
- 方法：`GET`
- 路径：`/api/hyperliquid/symbols/available`
- 函数名：`getHyperliquidAvailableSymbols`

**请求参数**
无

**响应数据结构**
```typescript
{
  symbols: Array<{
    symbol: string
    name?: string
    type?: string
  }>
  updated_at?: string
  max_symbols: number
}
```

**Mock 响应数据**
```json
{
  "symbols": [
    {
      "symbol": "BTC",
      "name": "Bitcoin",
      "type": "perp"
    },
    {
      "symbol": "ETH",
      "name": "Ethereum",
      "type": "perp"
    },
    {
      "symbol": "SOL",
      "name": "Solana",
      "type": "perp"
    },
    {
      "symbol": "DOGE",
      "name": "Dogecoin",
      "type": "perp"
    },
    {
      "symbol": "XRP",
      "name": "Ripple",
      "type": "perp"
    },
    {
      "symbol": "ADA",
      "name": "Cardano",
      "type": "perp"
    },
    {
      "symbol": "AVAX",
      "name": "Avalanche",
      "type": "perp"
    },
    {
      "symbol": "MATIC",
      "name": "Polygon",
      "type": "perp"
    },
    {
      "symbol": "LINK",
      "name": "Chainlink",
      "type": "perp"
    },
    {
      "symbol": "DOT",
      "name": "Polkadot",
      "type": "perp"
    }
  ],
  "updated_at": "2026-01-13T12:00:00Z",
  "max_symbols": 100
}
```

---

### 9.2 获取Hyperliquid观察列表

获取当前用户的Hyperliquid观察列表。

**接口信息**
- 方法：`GET`
- 路径：`/api/hyperliquid/symbols/watchlist`
- 函数名：`getHyperliquidWatchlist`

**请求参数**
无

**响应数据结构**
```typescript
{
  symbols: string[]
  max_symbols: number
}
```

**Mock 响应数据**
```json
{
  "symbols": [
    "BTC",
    "ETH",
    "SOL",
    "DOGE",
    "XRP"
  ],
  "max_symbols": 20
}
```

---

### 9.3 更新Hyperliquid观察列表

更新用户的Hyperliquid观察列表。

**接口信息**
- 方法：`PUT`
- 路径：`/api/hyperliquid/symbols/watchlist`
- 函数名：`updateHyperliquidWatchlist`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| symbols | array | 是 | 符号数组 |

**请求示例**
```json
{
  "symbols": ["BTC", "ETH", "SOL", "DOGE", "XRP", "ADA", "AVAX"]
}
```

**响应数据结构**
```typescript
{
  symbols: string[]
  max_symbols: number
}
```

**Mock 响应数据**
```json
{
  "symbols": [
    "BTC",
    "ETH",
    "SOL",
    "DOGE",
    "XRP",
    "ADA",
    "AVAX"
  ],
  "max_symbols": 20
}
```

---

## 10. 会员服务

### 10.1 获取会员信息

从外部会员服务获取用户的会员信息。

**接口信息**
- 方法：`GET`
- 路径：`https://www.akooi.com/api/membership/me`
- 函数名：`getMembershipInfo`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 否 | Bearer token（请求头） |

**响应数据结构**
```typescript
{
  membership: {
    status: string
    planKey: string
    planId?: string
    subscriptionId?: string
    environment: string
    currentPeriodStart?: string
    currentPeriodEnd?: string
    nextBillingTime?: string
    lastPaymentTime?: string
    updatedAt?: string
  } | null
  events?: Array<{
    id: number
    eventType: string
    status: string
    createdAt: string
    environment: string
  }>
}
```

**Mock 响应数据**
```json
{
  "membership": {
    "status": "active",
    "planKey": "premium",
    "planId": "plan_premium_monthly",
    "subscriptionId": "sub_1234567890",
    "environment": "production",
    "currentPeriodStart": "2026-01-01T00:00:00Z",
    "currentPeriodEnd": "2026-02-01T00:00:00Z",
    "nextBillingTime": "2026-02-01T00:00:00Z",
    "lastPaymentTime": "2026-01-01T00:00:00Z",
    "updatedAt": "2026-01-01T00:00:00Z"
  },
  "events": [
    {
      "id": 1,
      "eventType": "subscription_created",
      "status": "completed",
      "createdAt": "2025-12-01T00:00:00Z",
      "environment": "production"
    },
    {
      "id": 2,
      "eventType": "payment_success",
      "status": "completed",
      "createdAt": "2026-01-01T00:00:00Z",
      "environment": "production"
    }
  ]
}
```

---

## 11. Hyperliquid Builder Fee 授权

### 11.1 检查Builder授权状态

检查指定钱包地址的Builder授权状态。

**接口信息**
- 方法：`GET`
- 路径：`/api/account/hyperliquid/check-builder-authorization`
- 函数名：`checkBuilderAuthorization`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| wallet_address | string | 是 | 钱包地址（查询参数） |

**响应数据结构**
```typescript
{
  authorized: boolean
  max_fee: number
  required_fee: number
  builder_address: string
}
```

**Mock 响应数据**
```json
{
  "authorized": true,
  "max_fee": 0.001,
  "required_fee": 0.0005,
  "builder_address": "0xBuilderAddress123"
}
```

---

### 11.2 检查主网账户授权

检查所有主网账户的Builder授权状态。

**接口信息**
- 方法：`GET`
- 路径：`/api/account/hyperliquid/check-mainnet-accounts`
- 函数名：`checkMainnetAccounts`

**请求参数**
无

**响应数据结构**
```typescript
{
  unauthorized_accounts: Array<{
    account_id: number
    account_name: string
    wallet_address: string
    max_fee: number
    required_fee: number
    error_message?: string
  }>
}
```

**Mock 响应数据**
```json
{
  "unauthorized_accounts": [
    {
      "account_id": 1,
      "account_name": "GPT Trader",
      "wallet_address": "0x1234...5678",
      "max_fee": 0.0005,
      "required_fee": 0.001,
      "error_message": "Builder授权费用不足"
    }
  ]
}
```

---

### 11.3 批准Builder授权

为指定账户批准Builder授权。

**接口信息**
- 方法：`POST`
- 路径：`/api/account/hyperliquid/approve-builder`
- 函数名：`approveBuilder`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account_id | number | 是 | 账户ID（查询参数） |

**响应数据结构**
```typescript
{
  success: boolean
  message: string
  builder_address: string
  approved_fee: string
  result?: unknown
}
```

**Mock 响应数据**
```json
{
  "success": true,
  "message": "Builder授权已成功批准",
  "builder_address": "0xBuilderAddress123",
  "approved_fee": "0.001",
  "result": {
    "transaction_hash": "0xabcdef1234567890",
    "status": "confirmed"
  }
}
```

---

### 11.4 禁用交易

禁用指定账户的交易功能。

**接口信息**
- 方法：`POST`
- 路径：`/api/account/{accountId}/disable-trading`
- 函数名：`disableTrading`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| accountId | number | 是 | 账户ID（路径参数） |

**响应数据结构**
```typescript
{
  success: boolean
  message: string
  account_id: number
  account_name: string
}
```

**Mock 响应数据**
```json
{
  "success": true,
  "message": "账户交易功能已禁用",
  "account_id": 1,
  "account_name": "GPT Trader"
}
```

---

## 12. 交易员数据导入导出

### 12.1 导出交易员数据

导出指定账户的交易员数据。

**接口信息**
- 方法：`GET`
- 路径：`/api/trader/{accountId}/export`
- 函数名：`exportTraderData`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| accountId | number | 是 | 账户ID（路径参数） |

**响应数据结构**
```typescript
{
  account_id: number
  account_name: string
  exported_at: string
  decision_logs: Array<{
    symbol: string
    decision_time: string
    operation: string
    reason?: string
    prev_portion?: number
    target_portion?: number
    total_balance?: number
    executed?: string
    prompt_snapshot?: string
    reasoning_snapshot?: string
    decision_snapshot?: string
    hyperliquid_environment?: string
    wallet_address?: string
    hyperliquid_order_id?: string
    tp_order_id?: string
    sl_order_id?: string
    realized_pnl?: number
    pnl_updated_at?: string
  }>
  trades: Array<{
    environment: string
    wallet_address: string
    symbol: string
    side: string
    quantity: number
    price: number
    leverage: number
    order_id: string
    trade_value: number
    fee: number
    trade_time: string
  }>
}
```

**Mock 响应数据**
```json
{
  "account_id": 1,
  "account_name": "GPT Trader",
  "exported_at": "2026-01-13T12:30:00Z",
  "decision_logs": [
    {
      "symbol": "BTC",
      "decision_time": "2026-01-13T10:15:00Z",
      "operation": "buy",
      "reason": "BTC突破67000阻力位，RSI指标显示超买信号缓解，建议加仓",
      "prev_portion": 0.3,
      "target_portion": 0.5,
      "total_balance": 125000,
      "executed": "true",
      "prompt_snapshot": "当前市场状况：BTC $67,542.50 (+1.86%), ETH $3,456.78 (+2.15%)\n账户余额：$125,000\n持仓情况：BTC 0.3, ETH 10.0",
      "reasoning_snapshot": "基于技术分析：\n1. BTC成功突破67000阻力位\n2. RSI从75降至68，超买信号缓解\n3. 成交量放大，显示买盘强劲\n4. MACD金叉形成",
      "decision_snapshot": "{\"operation\":\"buy\",\"symbol\":\"BTC\",\"portion\":0.5,\"reason\":\"BTC突破67000阻力位，RSI指标显示超买信号缓解，建议加仓\"}",
      "hyperliquid_environment": "paper",
      "wallet_address": null,
      "hyperliquid_order_id": "ORD-20260113-001",
      "tp_order_id": "TP-20260113-001",
      "sl_order_id": "SL-20260113-001",
      "realized_pnl": 750.00,
      "pnl_updated_at": "2026-01-13T11:30:00Z"
    }
  ],
  "trades": [
    {
      "environment": "paper",
      "wallet_address": null,
      "symbol": "BTC",
      "side": "buy",
      "quantity": 0.5,
      "price": 67500.00,
      "leverage": 2.0,
      "order_id": "ORD-20260113-001",
      "trade_value": 33750.00,
      "fee": 33.75,
      "trade_time": "2026-01-13T10:15:00Z"
    },
    {
      "environment": "paper",
      "wallet_address": null,
      "symbol": "BTC",
      "side": "sell",
      "quantity": 0.5,
      "price": 69000.00,
      "leverage": 2.0,
      "order_id": "TP-20260113-001",
      "trade_value": 34500.00,
      "fee": 34.50,
      "trade_time": "2026-01-13T11:30:00Z"
    }
  ]
}
```

---

### 12.2 预览交易员导入

预览交易员数据的导入效果。

**接口信息**
- 方法：`POST`
- 路径：`/api/trader/{accountId}/import/preview`
- 函数名：`previewTraderImport`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| accountId | number | 是 | 账户ID（路径参数） |
| data | object | 是 | 导入数据（与export格式相同） |

**请求示例**
```json
{
  "data": {
    "account_id": 1,
    "account_name": "GPT Trader",
    "exported_at": "2026-01-13T12:30:00Z",
    "decision_logs": [...],
    "trades": [...]
  }
}
```

**响应数据结构**
```typescript
{
  will_import: {
    decision_logs: number
    trades: number
  }
  will_skip: {
    decision_logs: number
    trades: number
  }
  details: {
    new_decision_times: string[]
    duplicate_decision_times: string[]
    new_trade_ids: string[]
    duplicate_trade_ids: string[]
  }
}
```

**Mock 响应数据**
```json
{
  "will_import": {
    "decision_logs": 45,
    "trades": 89
  },
  "will_skip": {
    "decision_logs": 5,
    "trades": 3
  },
  "details": {
    "new_decision_times": [
      "2026-01-13T10:15:00Z",
      "2026-01-13T09:45:00Z"
    ],
    "duplicate_decision_times": [
      "2026-01-12T14:30:00Z"
    ],
    "new_trade_ids": [
      "ORD-20260113-001",
      "ORD-20260113-002"
    ],
    "duplicate_trade_ids": [
      "ORD-20260112-001"
    ]
  }
}
```

---

### 12.3 执行交易员导入

执行交易员数据的导入。

**接口信息**
- 方法：`POST`
- 路径：`/api/trader/{accountId}/import/execute`
- 函数名：`executeTraderImport`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| accountId | number | 是 | 账户ID（路径参数） |
| data | object | 是 | 导入数据（与export格式相同） |
| confirmed | boolean | 否 | 是否已确认，默认true |

**请求示例**
```json
{
  "data": {
    "account_id": 1,
    "account_name": "GPT Trader",
    "exported_at": "2026-01-13T12:30:00Z",
    "decision_logs": [...],
    "trades": [...]
  },
  "confirmed": true
}
```

**响应数据结构**
```typescript
{
  success: boolean
  imported: {
    decision_logs: number
    trades: number
  }
  skipped: {
    decision_logs: number
    trades: number
  }
  errors: string[]
}
```

**Mock 响应数据**
```json
{
  "success": true,
  "imported": {
    "decision_logs": 45,
    "trades": 89
  },
  "skipped": {
    "decision_logs": 5,
    "trades": 3
  },
  "errors": []
}
```

---

## 13. Prompt 回测

### 13.1 创建回测任务

创建新的Prompt回测任务。

**接口信息**
- 方法：`POST`
- 路径：`/api/prompt-backtest/tasks`
- 函数名：`createBacktestTask`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account_id | number | 是 | 账户ID |
| name | string | 否 | 任务名称 |
| items | array | 是 | 回测项目数组 |
| replace_rules | array | 否 | 替换规则数组 |

**请求示例**
```json
{
  "account_id": 1,
  "name": "BTC策略回测",
  "items": [
    {
      "decision_log_id": 1,
      "modified_prompt": "更新后的提示词内容..."
    },
    {
      "decision_log_id": 2,
      "modified_prompt": "更新后的提示词内容..."
    }
  ],
  "replace_rules": [
    {
      "find": "保守",
      "replace": "激进"
    }
  ]
}
```

**响应数据结构**
```typescript
{
  id: number
  account_id: number
  name: string | null
  status: string
  total_count: number
  completed_count: number
  failed_count: number
  created_at: string
  started_at: string | null
  finished_at: string | null
}
```

**Mock 响应数据**
```json
{
  "id": 1,
  "account_id": 1,
  "name": "BTC策略回测",
  "status": "pending",
  "total_count": 50,
  "completed_count": 0,
  "failed_count": 0,
  "created_at": "2026-01-13T13:00:00Z",
  "started_at": null,
  "finished_at": null
}
```

---

### 13.2 列出回测任务

获取回测任务列表。

**接口信息**
- 方法：`GET`
- 路径：`/api/prompt-backtest/tasks`
- 函数名：`listBacktestTasks`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account_id | number | 否 | 账户ID过滤 |
| limit | number | 否 | 返回数量限制，默认20 |

**响应数据结构**
```typescript
{
  tasks: Array<{
    id: number
    account_id: number
    name: string | null
    status: string
    total_count: number
    completed_count: number
    failed_count: number
    created_at: string
    started_at: string | null
    finished_at: string | null
  }>
}
```

**Mock 响应数据**
```json
{
  "tasks": [
    {
      "id": 1,
      "account_id": 1,
      "name": "BTC策略回测",
      "status": "completed",
      "total_count": 50,
      "completed_count": 48,
      "failed_count": 2,
      "created_at": "2026-01-13T13:00:00Z",
      "started_at": "2026-01-13T13:01:00Z",
      "finished_at": "2026-01-13T13:15:00Z"
    },
    {
      "id": 2,
      "account_id": 2,
      "name": "ETH策略回测",
      "status": "running",
      "total_count": 30,
      "completed_count": 20,
      "failed_count": 0,
      "created_at": "2026-01-13T13:10:00Z",
      "started_at": "2026-01-13T13:11:00Z",
      "finished_at": null
    }
  ]
}
```

---

### 13.3 获取回测任务状态

获取指定回测任务的状态。

**接口信息**
- 方法：`GET`
- 路径：`/api/prompt-backtest/tasks/{taskId}`
- 函数名：`getBacktestTaskStatus`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| taskId | number | 是 | 任务ID（路径参数） |

**响应数据结构**
```typescript
{
  id: number
  account_id: number
  name: string | null
  status: string
  total_count: number
  completed_count: number
  failed_count: number
  created_at: string
  started_at: string | null
  finished_at: string | null
}
```

**Mock 响应数据**
```json
{
  "id": 1,
  "account_id": 1,
  "name": "BTC策略回测",
  "status": "completed",
  "total_count": 50,
  "completed_count": 48,
  "failed_count": 2,
  "created_at": "2026-01-13T13:00:00Z",
  "started_at": "2026-01-13T13:01:00Z",
  "finished_at": "2026-01-13T13:15:00Z"
}
```

---

### 13.4 获取回测任务结果

获取回测任务的详细结果。

**接口信息**
- 方法：`GET`
- 路径：`/api/prompt-backtest/tasks/{taskId}/results`
- 函数名：`getBacktestTaskResults`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| taskId | number | 是 | 任务ID（路径参数） |

**响应数据结构**
```typescript
{
  task: {
    id: number
    account_id: number
    name: string | null
    status: string
    total_count: number
    completed_count: number
    failed_count: number
    created_at: string
    started_at: string | null
    finished_at: string | null
  }
  items: Array<{
    id: number
    original_decision_time: string | null
    original_operation: string | null
    original_symbol: string | null
    original_target_portion: number | null
    original_realized_pnl: number | null
    new_operation: string | null
    new_symbol: string | null
    new_target_portion: number | null
    decision_changed: boolean | null
    change_type: string | null
    status: string
  }>
  summary: {
    total: number
    completed: number
    failed: number
    changed: number
    unchanged: number
    avoided_loss_count: number
    avoided_loss_amount: number
    missed_profit_count: number
    missed_profit_amount: number
  }
}
```

**Mock 响应数据**
```json
{
  "task": {
    "id": 1,
    "account_id": 1,
    "name": "BTC策略回测",
    "status": "completed",
    "total_count": 50,
    "completed_count": 48,
    "failed_count": 2,
    "created_at": "2026-01-13T13:00:00Z",
    "started_at": "2026-01-13T13:01:00Z",
    "finished_at": "2026-01-13T13:15:00Z"
  },
  "items": [
    {
      "id": 1,
      "original_decision_time": "2026-01-13T10:15:00Z",
      "original_operation": "buy",
      "original_symbol": "BTC",
      "original_target_portion": 0.5,
      "original_realized_pnl": 750.00,
      "new_operation": "hold",
      "new_symbol": "BTC",
      "new_target_portion": 0.5,
      "decision_changed": true,
      "change_type": "avoided_loss",
      "status": "completed"
    },
    {
      "id": 2,
      "original_decision_time": "2026-01-13T09:45:00Z",
      "original_operation": "sell",
      "original_symbol": "ETH",
      "original_target_portion": 0.3,
      "original_realized_pnl": -500.00,
      "new_operation": "sell",
      "new_symbol": "ETH",
      "new_target_portion": 0.3,
      "decision_changed": false,
      "change_type": null,
      "status": "completed"
    }
  ],
  "summary": {
    "total": 50,
    "completed": 48,
    "failed": 2,
    "changed": 15,
    "unchanged": 33,
    "avoided_loss_count": 8,
    "avoided_loss_amount": 3200.00,
    "missed_profit_count": 7,
    "missed_profit_amount": 1850.00
  }
}
```

---

### 13.5 获取回测项目详情

获取单个回测项目的详细信息。

**接口信息**
- 方法：`GET`
- 路径：`/api/prompt-backtest/items/{itemId}`
- 函数名：`getBacktestItemDetail`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| itemId | number | 是 | 项目ID（路径参数） |

**响应数据结构**
```typescript
{
  id: number
  original_operation: string | null
  original_symbol: string | null
  original_reasoning: string | null
  original_decision_json: string | null
  original_prompt_template_name: string | null
  modified_prompt: string | null
  new_operation: string | null
  new_symbol: string | null
  new_reasoning: string | null
  new_decision_json: string | null
  decision_changed: boolean | null
  change_type: string | null
  error_message: string | null
}
```

**Mock 响应数据**
```json
{
  "id": 1,
  "original_operation": "buy",
  "original_symbol": "BTC",
  "original_reasoning": "基于技术分析：\n1. BTC成功突破67000阻力位\n2. RSI从75降至68，超买信号缓解\n3. 成交量放大，显示买盘强劲\n4. MACD金叉形成",
  "original_decision_json": "{\"operation\":\"buy\",\"symbol\":\"BTC\",\"portion\":0.5,\"reason\":\"BTC突破67000阻力位，RSI指标显示超买信号缓解，建议加仓\"}",
  "original_prompt_template_name": "默认交易提示词",
  "modified_prompt": "更新后的提示词内容：{{market_data}}\n账户余额：{{balance}}\n持仓情况：{{positions}}\n请基于激进策略分析并给出交易建议，关注短期波动机会。",
  "new_operation": "hold",
  "new_symbol": "BTC",
  "new_reasoning": "基于激进策略分析：\n1. BTC在67000-68000区间震荡\n2. 短期指标显示超买风险\n3. 建议等待更明确的突破信号\n4. 当前持仓保持不变",
  "new_decision_json": "{\"operation\":\"hold\",\"symbol\":\"BTC\",\"portion\":0.5,\"reason\":\"BTC在67000-68000区间震荡，短期指标显示超买风险，建议等待更明确的突破信号\"}",
  "decision_changed": true,
  "change_type": "avoided_loss",
  "error_message": null
}
```

---

### 13.6 删除回测任务

删除指定的回测任务。

**接口信息**
- 方法：`DELETE`
- 路径：`/api/prompt-backtest/tasks/{taskId}`
- 函数名：`deleteBacktestTask`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| taskId | number | 是 | 任务ID（路径参数） |

**响应数据结构**
```typescript
{
  success: boolean
  message: string
}
```

**Mock 响应数据**
```json
{
  "success": true,
  "message": "回测任务已成功删除"
}
```

---

### 13.7 重试回测任务

重试失败的回测任务。

**接口信息**
- 方法：`POST`
- 路径：`/api/prompt-backtest/tasks/{taskId}/retry`
- 函数名：`retryBacktestTask`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| taskId | number | 是 | 任务ID（路径参数） |

**响应数据结构**
```typescript
{
  success: boolean
  message: string
  retry_count: number
}
```

**Mock 响应数据**
```json
{
  "success": true,
  "message": "回测任务重试已启动",
  "retry_count": 1
}
```

---

### 13.8 获取回测任务项目列表

获取回测任务的所有项目列表。

**接口信息**
- 方法：`GET`
- 路径：`/api/prompt-backtest/tasks/{taskId}/items`
- 函数名：`getBacktestTaskItems`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| taskId | number | 是 | 任务ID（路径参数） |

**响应数据结构**
```typescript
{
  task_id: number
  task_name: string
  items: Array<{
    id: number
    modified_prompt: string
    operation: string | null
    symbol: string | null
    reason: string | null
    decision_time: string | null
    realized_pnl: number | null
  }>
}
```

**Mock 响应数据**
```json
{
  "task_id": 1,
  "task_name": "BTC策略回测",
  "items": [
    {
      "id": 1,
      "modified_prompt": "更新后的提示词内容：{{market_data}}\n账户余额：{{balance}}\n持仓情况：{{positions}}\n请基于激进策略分析并给出交易建议，关注短期波动机会。",
      "operation": "hold",
      "symbol": "BTC",
      "reason": "BTC在67000-68000区间震荡，短期指标显示超买风险，建议等待更明确的突破信号",
      "decision_time": "2026-01-13T10:15:00Z",
      "realized_pnl": 750.00
    },
    {
      "id": 2,
      "modified_prompt": "更新后的提示词内容：{{market_data}}\n账户余额：{{balance}}\n持仓情况：{{positions}}\n请基于激进策略分析并给出交易建议，关注短期波动机会。",
      "operation": "sell",
      "symbol": "ETH",
      "reason": "ETH在3500附近遇到强阻力，短期回调风险加大，建议减仓",
      "decision_time": "2026-01-13T09:45:00Z",
      "realized_pnl": -500.00
    }
  ]
}
```

---

## 附录

### A. 通用错误响应

所有API在发生错误时可能返回以下格式：

```json
{
  "detail": "错误描述信息",
  "message": "错误描述信息",
  "error_code": "ERROR_CODE"
}
```

### B. 分页参数

支持分页的接口通常包含以下参数：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| limit | number | 否 | 每页返回数量，默认20 |
| offset | number | 否 | 偏移量，默认0 |

### C. 时间格式

所有时间字段均使用 ISO 8601 格式：
- 示例：`2026-01-13T10:30:00Z`

### D. 金额格式

所有金额字段均使用数字类型，单位为最小货币单位：
- 示例：`67542.50` 表示 $67,542.50

### E. 交易模式

系统支持以下交易模式：
- `paper`: 模拟交易
- `mainnet`: 主网交易

### F. 策略触发模式

系统支持以下策略触发模式：
- `realtime`: 实时触发
- `interval`: 定时触发
- `tick_batch`: 批量触发

---

**文档版本**: 1.0.0
**最后更新**: 2026-01-13
**维护者**: Hyper Alpha Arena Team
