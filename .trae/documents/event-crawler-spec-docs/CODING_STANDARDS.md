# Event-Crawler 编码规范

## 1. 概述

本文档详细描述Event-Crawler项目的编码规范，包括Python、TypeScript/JavaScript、Vue组件的编码规范，以及命名规范、注释规范、代码组织结构等。

**项目位置**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler`  
**文档版本**: V1.0  
**最后更新**: 2026-01-08

---

## 2. Python编码规范

### 2.1 基础规范

#### 2.1.1 遵循PEP 8

```python
# 好的示例
def calculate_score(stock_code: str, price: float) -> float:
    """计算股票评分"""
    return price * 1.5

# 不好的示例
def CalculateScore(stockCode, price):
    return price*1.5
```

#### 2.1.2 使用类型注解

```python
# 好的示例
from typing import List, Dict, Optional

def get_stock_data(stock_code: str) -> Optional[Dict[str, Any]]:
    """获取股票数据"""
    return None

def get_stock_list(limit: int = 100) -> List[Dict[str, Any]]:
    """获取股票列表"""
    return []

# 不好的示例
def get_stock_data(stock_code):
    return None
```

#### 2.1.3 使用异步编程

```python
# 好的示例
import asyncio
from typing import List

async def fetch_stock_data(stock_codes: List[str]) -> List[Dict[str, Any]]:
    """异步获取股票数据"""
    tasks = [fetch_single_stock(code) for code in stock_codes]
    results = await asyncio.gather(*tasks)
    return results

async def fetch_single_stock(stock_code: str) -> Dict[str, Any]:
    """异步获取单只股票数据"""
    await asyncio.sleep(0.1)
    return {"code": stock_code, "price": 10.0}

# 不好的示例
def fetch_stock_data(stock_codes):
    results = []
    for code in stock_codes:
        results.append(fetch_single_stock(code))
    return results
```

### 2.2 命名规范

#### 2.2.1 变量命名

```python
# 好的示例：使用snake_case
stock_code = "000001"
current_price = 12.50
is_active = True
user_name = "John Doe"

# 不好的示例：使用camelCase或大写
stockCode = "000001"
CurrentPrice = 12.50
IsActive = True
```

#### 2.2.2 函数命名

```python
# 好的示例：使用动词开头，snake_case
def calculate_score(stock_code: str) -> float:
    """计算评分"""
    return 100.0

def get_stock_info(stock_code: str) -> Dict[str, Any]:
    """获取股票信息"""
    return {}

def update_monitor_status(monitor_id: int, status: str) -> bool:
    """更新监控状态"""
    return True

# 不好的示例：使用名词或不规范的命名
def score(stock_code):
    return 100.0

def stock_info(stock_code):
    return {}
```

#### 2.2.3 类命名

```python
# 好的示例：使用PascalCase
class StockService:
    """股票服务类"""
    pass

class MonitorEngine:
    """监控引擎类"""
    pass

class DataDeduplicationOptimizer:
    """数据去重优化器类"""
    pass

# 不好的示例：使用snake_case或小写
class stock_service:
    pass

class monitor_engine:
    pass
```

#### 2.2.4 常量命名

```python
# 好的示例：使用大写字母+下划线
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30
DATABASE_URL = "mysql+aiomysql://..."
API_VERSION = "v1"

# 不好的示例：使用小写或camelCase
max_retry_count = 3
defaultTimeout = 30
databaseUrl = "mysql+aiomysql://..."
```

### 2.3 注释规范

#### 2.3.1 文档字符串

```python
# 好的示例：使用Google风格的文档字符串
def calculate_score(
    stock_code: str,
    price: float,
    volume: int
) -> float:
    """
    计算股票评分
    
    Args:
        stock_code: 股票代码
        price: 当前价格
        volume: 成交量
        
    Returns:
        评分值
        
    Raises:
        ValueError: 当价格或成交量小于0时
        
    Example:
        >>> calculate_score("000001", 12.50, 1000000)
        150.0
    """
    if price <= 0 or volume < 0:
        raise ValueError("价格和成交量必须大于0")
    
    return price * (volume / 1000000)

# 不好的示例：缺少文档字符串或文档不完整
def calculate_score(stock_code, price, volume):
    return price * (volume / 1000000)
```

#### 2.3.2 行内注释

```python
# 好的示例：注释说明"为什么"而不是"是什么"
# 使用SHA256哈希去重，避免重复数据入库
data_hash = hashlib.sha256(data.encode()).hexdigest()

# 不好的示例：注释重复代码内容
# 计算哈希值
data_hash = hashlib.sha256(data.encode()).hexdigest()
```

### 2.4 代码组织结构

#### 2.4.1 文件组织

```python
# 好的示例：按照功能模块组织文件
app/
├── api/              # API控制器
│   ├── __init__.py
│   ├── stock_controller.py
│   └── monitor_controller.py
├── services/          # 业务逻辑层
│   ├── __init__.py
│   ├── stock_service.py
│   └── monitor_service.py
├── models/            # 数据模型
│   ├── __init__.py
│   ├── stock.py
│   └── monitor.py
├── repositories/       # 数据访问层
│   ├── __init__.py
│   ├── stock_repository.py
│   └── monitor_repository.py
└── utils/             # 工具类
    ├── __init__.py
    ├── data_utils.py
    └── cache_utils.py
```

#### 2.4.2 导入顺序

```python
# 好的示例：按照标准库、第三方库、本地模块的顺序导入
# 1. 标准库
import asyncio
import hashlib
from datetime import datetime
from typing import List, Dict, Optional

# 2. 第三方库
from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from loguru import logger

# 3. 本地模块
from app.models.stock import StockInfo
from app.services.stock_service import stock_service
from app.utils.data_utils import calculate_hash

# 不好的示例：导入顺序混乱
from app.models.stock import StockInfo
import asyncio
from fastapi import HTTPException
from sqlalchemy import select
from typing import List, Dict, Optional
```

### 2.5 错误处理

```python
# 好的示例：使用具体的异常类型和有意义的错误消息
async def get_stock_info(stock_code: str) -> Dict[str, Any]:
    """
    获取股票信息
    
    Args:
        stock_code: 股票代码
        
    Returns:
        股票信息字典
        
    Raises:
        HTTPException: 当股票不存在时
    """
    stock = await db.query(StockInfo).filter_by(code=stock_code).first()
    
    if not stock:
        raise HTTPException(
            status_code=404,
            detail=f"股票代码 {stock_code} 不存在"
        )
    
    return stock.to_dict()

# 不好的示例：使用通用的异常类型
async def get_stock_info(stock_code: str):
    stock = await db.query(StockInfo).filter_by(code=stock_code).first()
    
    if not stock:
        raise Exception("股票不存在")
    
    return stock.to_dict()
```

---

## 3. TypeScript/JavaScript编码规范

### 3.1 基础规范

#### 3.1.1 使用TypeScript严格模式

```typescript
// 好的示例：使用类型注解
interface StockData {
  code: string;
  name: string;
  currentPrice: number;
  volume: number;
  timestamp: Date;
}

function calculateScore(data: StockData): number {
  return data.currentPrice * (data.volume / 1000000);
}

// 不好的示例：使用any类型
function calculateScore(data: any): number {
  return data.currentPrice * (data.volume / 1000000);
}
```

#### 3.1.2 使用const和let代替var

```typescript
// 好的示例：使用const和let
const stockCode = "000001";
let currentPrice = 12.50;
const isMonitoring = true;

// 不好的示例：使用var
var stockCode = "000001";
var currentPrice = 12.50;
var isMonitoring = true;
```

### 3.2 命名规范

#### 3.2.1 变量命名

```typescript
// 好的示例：使用camelCase
const stockCode = "000001";
const currentPrice = 12.50;
const isActive = true;
const userName = "John Doe";

// 不好的示例：使用snake_case或大写
const stock_code = "000001";
const CurrentPrice = 12.50;
const IS_ACTIVE = true;
```

#### 3.2.2 函数命名

```typescript
// 好的示例：使用动词开头，camelCase
function calculateScore(stockCode: string, price: number): number {
  return price * 1.5;
}

function getStockInfo(stockCode: string): StockData | null {
  return null;
}

function updateMonitorStatus(monitorId: number, status: string): boolean {
  return true;
}

// 不好的示例：使用名词或不规范的命名
function score(stockCode: string, price: number): number {
  return price * 1.5;
}

function stockInfo(stockCode: string): StockData | null {
  return null;
}
```

#### 3.2.3 类命名

```typescript
// 好的示例：使用PascalCase
class StockService {
  private stockCode: string;
  
  constructor(stockCode: string) {
    this.stockCode = stockCode;
  }
  
  public async fetchData(): Promise<StockData> {
    return {} as StockData;
  }
}

class MonitorEngine {
  private monitors: Map<string, Monitor>;
  
  public addMonitor(monitor: Monitor): void {
    this.monitors.set(monitor.code, monitor);
  }
}

// 不好的示例：使用camelCase或小写
class stockService {
  constructor(stockCode: string) {
    this.stockCode = stockCode;
  }
}

class monitorEngine {
  addMonitor(monitor: Monitor): void {
    this.monitors.set(monitor.code, monitor);
  }
}
```

#### 3.2.4 常量命名

```typescript
// 好的示例：使用大写字母+下划线
const MAX_RETRY_COUNT = 3;
const DEFAULT_TIMEOUT = 30;
const API_BASE_URL = "http://localhost:8000";
const API_VERSION = "v1";

// 不好的示例：使用小写或camelCase
const maxRetryCount = 3;
const defaultTimeout = 30;
const apiBaseUrl = "http://localhost:8000";
```

### 3.3 注释规范

#### 3.3.1 JSDoc注释

```typescript
// 好的示例：使用JSDoc注释
/**
 * 计算股票评分
 * 
 * @param stockCode - 股票代码
 * @param price - 当前价格
 * @param volume - 成交量
 * @returns 评分值
 * @throws {Error} 当价格或成交量小于0时
 * 
 * @example
 * calculateScore("000001", 12.50, 1000000);
 * // 返回: 150.0
 */
function calculateScore(
  stockCode: string,
  price: number,
  volume: number
): number {
  if (price <= 0 || volume < 0) {
    throw new Error("价格和成交量必须大于0");
  }
  
  return price * (volume / 1000000);
}

// 不好的示例：缺少注释或注释不完整
function calculateScore(stockCode: string, price: number, volume: number): number {
  return price * (volume / 1000000);
}
```

#### 3.3.2 行内注释

```typescript
// 好的示例：注释说明"为什么"而不是"是什么"
// 使用SHA256哈希去重，避免重复数据入库
const dataHash = crypto.createHash('sha256').update(data).digest('hex');

// 不好的示例：注释重复代码内容
// 计算哈希值
const dataHash = crypto.createHash('sha256').update(data).digest('hex');
```

### 3.4 代码组织结构

#### 3.4.1 文件组织

```typescript
// 好的示例：按照功能模块组织文件
src/
├── api/              # API相关
│   ├── stock-api.ts
│   └── monitor-api.ts
├── services/          # 业务逻辑
│   ├── stock-service.ts
│   └── monitor-service.ts
├── models/            # 数据模型
│   ├── stock.ts
│   └── monitor.ts
├── utils/             # 工具类
│   ├── data-utils.ts
│   └── cache-utils.ts
└── types/             # 类型定义
    ├── stock.ts
    └── monitor.ts
```

#### 3.4.2 导入顺序

```typescript
// 好的示例：按照标准库、第三方库、本地模块的顺序导入
// 1. 标准库
import { createHash } from 'crypto';
import { join } from 'path';

// 2. 第三方库
import axios from 'axios';
import { z } from 'zod';

// 3. 本地模块
import { StockData } from '@/types/stock';
import { calculateHash } from '@/utils/data-utils';

// 不好的示例：导入顺序混乱
import { StockData } from '@/types/stock';
import { createHash } from 'crypto';
import axios from 'axios';
import { calculateHash } from '@/utils/data-utils';
```

### 3.5 错误处理

```typescript
// 好的示例：使用try-catch和具体的错误类型
async function getStockInfo(stockCode: string): Promise<StockData> {
  try {
    const response = await axios.get(`/api/v1/stocks/info/${stockCode}`);
    return response.data.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 404) {
        throw new Error(`股票代码 ${stockCode} 不存在`);
      }
      throw new Error(`API请求失败: ${error.message}`);
    }
    throw new Error(`未知错误: ${error}`);
  }
}

// 不好的示例：忽略错误或使用通用错误处理
async function getStockInfo(stockCode: string): Promise<StockData> {
  const response = await axios.get(`/api/v1/stocks/info/${stockCode}`);
  return response.data.data;
}
```

---

## 4. Vue组件编码规范

### 4.1 组件命名

```vue
<!-- 好的示例：使用PascalCase -->
<template>
  <StockList />
  <MonitorPanel />
  <DataChart />
</template>

<!-- 不好的示例：使用kebab-case或小写 -->
<template>
  <stock-list />
  <monitor-panel />
  <data-chart />
</template>
```

### 4.2 组件结构

```vue
<!-- 好的示例：按照template、script、style的顺序组织 -->
<template>
  <div class="stock-list">
    <div v-for="stock in stocks" :key="stock.code" class="stock-item">
      <h3>{{ stock.name }}</h3>
      <p>价格: {{ stock.price }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getStockList } from '@/api/stock-api';

interface Stock {
  code: string;
  name: string;
  price: number;
}

const stocks = ref<Stock[]>([]);

onMounted(async () => {
  stocks.value = await getStockList();
});
</script>

<style scoped>
.stock-list {
  padding: 20px;
}

.stock-item {
  margin-bottom: 10px;
  padding: 10px;
  border: 1px solid #ddd;
}
</style>

<!-- 不好的示例：结构混乱或缺少部分 -->
<template>
  <div>...</div>
</template>

<style>
.stock-list {
  padding: 20px;
}
</style>

<script>
export default {
  data() {
    return {
      stocks: []
    };
  }
};
</script>
```

### 4.3 Props和Emits

```vue
<!-- 好的示例：使用TypeScript定义props和emits -->
<script setup lang="ts">
interface Props {
  stockCode: string;
  autoRefresh?: boolean;
}

interface Emits {
  (e: 'update', value: StockData): void;
  (e: 'delete', code: string): void;
}

const props = withDefaults(defineProps<Props>(), {
  autoRefresh: false
});

const emit = defineEmits<Emits>();

function handleUpdate(data: StockData) {
  emit('update', data);
}

function handleDelete(code: string) {
  emit('delete', code);
}
</script>

<!-- 不好的示例：缺少类型定义 -->
<script setup>
const props = defineProps({
  stockCode: String,
  autoRefresh: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update', 'delete']);
</script>
```

---

## 5. 通用编码规范

### 5.1 代码格式化

#### 5.1.1 Python代码格式化

使用Black进行代码格式化：

```bash
# 安装Black
pip install black

# 格式化代码
black app/

# 检查格式化
black --check app/

# 配置pyproject.toml
[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'
```

#### 5.1.2 TypeScript代码格式化

使用Prettier进行代码格式化：

```bash
# 安装Prettier
npm install --save-dev prettier

# 格式化代码
npx prettier --write "src/**/*.{ts,tsx,vue}"

# 检查格式化
npx prettier --check "src/**/*.{ts,tsx,vue}"

# 配置.prettierrc
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

### 5.2 代码检查

#### 5.2.1 Python代码检查

使用pylint进行代码检查：

```bash
# 安装pylint
pip install pylint

# 检查代码
pylint app/

# 配置.pylintrc
[MASTER]
disable = [
  'C0111',  # missing-docstring
  'R0903',  # too-few-public-methods
]
```

使用mypy进行类型检查：

```bash
# 安装mypy
pip install mypy

# 检查类型
mypy app/

# 配置mypy.ini
[mypy]
python_version = 3.8
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

#### 5.2.2 TypeScript代码检查

使用ESLint进行代码检查：

```bash
# 安装ESLint
npm install --save-dev eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin

# 检查代码
npx eslint "src/**/*.{ts,tsx,vue}"

# 配置.eslintrc.js
module.exports = {
  parser: '@typescript-eslint/parser',
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended'
  ],
  rules: {
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/no-unused-vars': 'error'
  }
};
```

### 5.3 代码复杂度

#### 5.3.1 圈复杂度

```python
# 好的示例：圈复杂度<10
def calculate_score(stock_code: str, price: float, volume: int) -> float:
    """计算股票评分"""
    if price <= 0:
        return 0
    if volume <= 0:
        return 0
    
    return price * (volume / 1000000)

# 不好的示例：圈复杂度>10
def calculate_score(stock_code: str, price: float, volume: int, 
                market: str, industry: str, sector: str,
                is_active: bool, is_held: bool, score: float) -> float:
    """计算股票评分"""
    if price <= 0:
        if volume <= 0:
            if market == 'SZ':
                if industry == '银行':
                    if sector == '金融':
                        if is_active:
                            if is_held:
                                if score > 100:
                                    return score * 1.5
                                else:
                                    return score * 1.2
                            else:
                                return score * 1.1
                        else:
                            return score * 1.0
                    else:
                        return score * 0.9
                else:
                    return score * 0.8
            else:
                return score * 0.7
        else:
            return score * 0.6
    else:
        return score * 0.5
```

### 5.4 代码重复

#### 5.4.1 避免代码重复

```python
# 好的示例：提取公共函数
def format_stock_data(stock: StockInfo) -> Dict[str, Any]:
    """格式化股票数据"""
    return {
        "code": stock.code,
        "name": stock.name,
        "market": stock.market,
        "industry": stock.industry
    }

def get_stock_list() -> List[Dict[str, Any]]:
    """获取股票列表"""
    stocks = db.query(StockInfo).all()
    return [format_stock_data(stock) for stock in stocks]

def get_monitor_list() -> List[Dict[str, Any]]:
    """获取监控列表"""
    monitors = db.query(MonitorList).all()
    return [format_stock_data(monitor.stock) for monitor in monitors]

# 不好的示例：代码重复
def get_stock_list() -> List[Dict[str, Any]]:
    """获取股票列表"""
    stocks = db.query(StockInfo).all()
    return [
        {
            "code": stock.code,
            "name": stock.name,
            "market": stock.market,
            "industry": stock.industry
        }
        for stock in stocks
    ]

def get_monitor_list() -> List[Dict[str, Any]]:
    """获取监控列表"""
    monitors = db.query(MonitorList).all()
    return [
        {
            "code": monitor.stock.code,
            "name": monitor.stock.name,
            "market": monitor.stock.market,
            "industry": monitor.stock.industry
        }
        for monitor in monitors
    ]
```

---

## 6. 总结

本文档详细描述了Event-Crawler项目的编码规范，包括：

1. **Python编码规范**: PEP 8、类型注解、异步编程、命名规范、注释规范、代码组织、错误处理
2. **TypeScript/JavaScript编码规范**: 严格模式、命名规范、注释规范、代码组织、错误处理
3. **Vue组件编码规范**: 组件命名、组件结构、Props和Emits
4. **通用编码规范**: 代码格式化、代码检查、代码复杂度、代码重复

遵循这些编码规范可以确保代码质量、可读性和可维护性。

---

**文档维护**: 本文档应随着项目编码规范的演进而持续更新，确保与实际编码实践保持一致。
