# 同花顺股票监控系统使用说明

## 概述

同花顺股票监控系统是一个专业的股票数据采集、存储、监控和查询平台。本系统提供完整的RESTful API接口，支持实时股票数据处理、智能监控管理和高效数据查询。

## 功能特性

### 核心功能

- **股票信息管理**: 支持股票基本信息的增删改查
- **股票数据采集**: 支持实时股票数据的单条和批量提交
- **监控管理**: 支持股票监控列表的灵活管理
- **数据去重**: 智能数据去重，避免重复存储
- **健康监控**: 完善的系统健康检查机制

### 技术特性

- **高性能**: 基于FastAPI和异步数据库连接
- **高可用**: 支持连接池和故障恢复
- **易扩展**: 模块化设计，便于功能扩展
- **易维护**: 完整的日志记录和错误处理

## 快速开始

### 1. HTML查询页面使用

系统提供了用户友好的HTML查询页面，无需编程知识即可使用。

#### 访问方式

在浏览器中打开：`http://localhost:8001/`

#### 页面功能

**1. 股票搜索**
- 在搜索框中输入股票代码（如：000001）或股票名称（如：平安银行）
- 支持模糊搜索，输入部分关键词即可匹配
- 点击"搜索"按钮或按回车键执行搜索

**2. 搜索结果展示**
- 以表格形式展示搜索结果
- 显示股票代码、名称、当前价格、涨跌幅、成交量等信息
- 支持分页浏览，每页显示20条记录

**3. 数据操作**
- **刷新数据**: 点击"刷新数据"按钮获取最新股票信息
- **分页导航**: 使用页面底部的分页控件浏览更多数据
- **清空搜索**: 清空搜索框可查看所有股票数据

**4. 响应式设计**
- 自适应不同屏幕尺寸
- 在手机、平板、电脑上都有良好的显示效果

#### 使用示例

1. **查找特定股票**：
   - 输入"平安银行"或"000001"
   - 查看该股票的详细信息

2. **浏览所有股票**：
   - 保持搜索框为空
   - 点击"搜索"查看所有股票列表

3. **按行业查找**：
   - 输入"银行"查找所有银行类股票
   - 输入"科技"查找科技类股票

### 2. 系统访问

确保系统已正确部署并启动后，可以通过以下方式访问：

- **HTML查询页面**: `http://localhost:8001/`
- **API基础地址**: `http://localhost:8001`
- **API文档**: `http://localhost:8001/docs`
- **健康检查**: `http://localhost:8001/health`

### 2. 基础操作流程

#### 步骤1: 检查系统状态

```bash
curl http://localhost:8001/health
```

#### 步骤2: 创建股票信息

```bash
curl -X POST "http://localhost:8000/api/v1/stocks/info" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "000001",
    "name": "平安银行",
    "market": "SZ",
    "industry": "银行"
  }'
```

#### 步骤3: 添加监控

```bash
curl -X POST "http://localhost:8000/api/v1/monitors" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001",
    "priority": 1
  }'
```

#### 步骤4: 提交股票数据

```bash
curl -X POST "http://localhost:8000/api/v1/stocks/data" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "000001",
    "name": "平安银行",
    "current_price": 12.50,
    "volume": 1000000
  }'
```

## 详细使用指南

### 股票信息管理

#### 创建股票信息

股票信息是系统的基础数据，包含股票的基本属性。

**必填字段:**
- `code`: 股票代码 (6位数字)
- `name`: 股票名称
- `market`: 市场代码 (SZ/SH)

**可选字段:**
- `industry`: 行业分类
- `is_active`: 是否活跃 (默认true)

**示例:**
```json
{
  "code": "000001",
  "name": "平安银行",
  "market": "SZ",
  "industry": "银行",
  "is_active": true
}
```

#### 查询股票信息

**单个查询:**
```bash
curl http://localhost:8000/api/v1/stocks/info/000001
```

**列表查询:**
```bash
# 获取所有活跃股票
curl "http://localhost:8000/api/v1/stocks/info?active_only=true&limit=50"

# 按市场过滤
curl "http://localhost:8000/api/v1/stocks/info?market=SZ&limit=100"
```

#### 更新股票信息

```bash
curl -X PUT "http://localhost:8000/api/v1/stocks/info/000001" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "平安银行(更新)",
    "industry": "金融服务"
  }'
```

### 股票数据管理

#### 数据字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 股票代码 |
| name | string | 是 | 股票名称 |
| current_price | number | 是 | 当前价格 |
| open_price | number | 否 | 开盘价 |
| prev_close | number | 否 | 昨收价 |
| change_amount | number | 否 | 涨跌额 |
| volume | integer | 否 | 成交量 |
| timestamp | string | 否 | 数据时间戳 |

#### 单条数据提交

```bash
curl -X POST "http://localhost:8000/api/v1/stocks/data" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "000001",
    "name": "平安银行",
    "current_price": 12.50,
    "open_price": 12.30,
    "prev_close": 12.40,
    "change_amount": 0.10,
    "volume": 1000000,
    "timestamp": "2024-01-15T10:30:00Z"
  }'
```

#### 批量数据提交

批量提交可以显著提高数据处理效率，建议每批次不超过1000条记录。

```bash
curl -X POST "http://localhost:8000/api/v1/stocks/data/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {
        "code": "000001",
        "name": "平安银行",
        "current_price": 12.50,
        "volume": 1000000,
        "timestamp": "2024-01-15T10:30:00Z"
      },
      {
        "code": "000002",
        "name": "万科A",
        "current_price": 25.68,
        "volume": 2000000,
        "timestamp": "2024-01-15T10:30:00Z"
      }
    ]
  }'
```

**批量提交响应:**
```json
{
  "success": true,
  "data": {
    "total": 2,
    "success": 2,
    "failed": 0,
    "errors": [],
    "duplicates": 0
  },
  "message": "批量提交完成"
}
```

### 监控管理

#### 监控优先级

系统支持1-10级优先级设置：
- **1-3**: 高优先级 (重点关注股票)
- **4-6**: 中优先级 (一般关注股票)
- **7-10**: 低优先级 (备选关注股票)

#### 添加监控

```bash
curl -X POST "http://localhost:8000/api/v1/monitors" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001",
    "priority": 1,
    "auto_create_stock": false
  }'
```

**参数说明:**
- `stock_code`: 股票代码
- `priority`: 优先级 (1-10)
- `auto_create_stock`: 是否自动创建股票信息

#### 查询监控列表

```bash
# 获取所有活跃监控
curl "http://localhost:8000/api/v1/monitors?active_only=true"

# 按优先级过滤
curl "http://localhost:8000/api/v1/monitors?priority_filter=1"

# 包含股票信息
curl "http://localhost:8000/api/v1/monitors?include_stock_info=true"

# 包含最新数据
curl "http://localhost:8000/api/v1/monitors?include_latest_data=true"
```

#### 更新监控设置

```bash
# 更新优先级
curl -X PUT "http://localhost:8000/api/v1/monitors/000001" \
  -H "Content-Type: application/json" \
  -d '{"priority": 2}'

# 停用监控
curl -X PUT "http://localhost:8000/api/v1/monitors/000001" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

#### 移除监控

```bash
curl -X DELETE "http://localhost:8000/api/v1/monitors/000001"
```

#### 获取监控代码列表

```bash
# 获取所有活跃监控的股票代码
curl "http://localhost:8000/api/v1/monitors/codes?active_only=true"
```

响应示例:
```json
{
  "success": true,
  "data": ["000001", "000002", "600036"],
  "message": "获取监控股票代码成功，共3只"
}
```

## 高级功能

### 数据去重机制

系统内置智能数据去重功能，基于以下策略：

1. **哈希去重**: 基于关键字段生成哈希值
2. **时间窗口**: 在指定时间窗口内检测重复
3. **自动清理**: 定期清理过期的去重记录

### 健康监控

#### 基础健康检查

```bash
curl http://localhost:8000/api/v1/health
```

#### 详细健康检查

```bash
curl http://localhost:8000/api/v1/health/detailed
```

详细检查包含：
- 数据库连接状态
- 各服务模块状态
- 系统性能指标
- 响应时间统计

#### 数据库健康检查

```bash
curl http://localhost:8000/api/v1/health/database
```

### 分页查询

所有列表查询都支持分页参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | integer | 100 | 每页数量 (1-1000) |
| offset | integer | 0 | 偏移量 |

**示例:**
```bash
# 获取第2页，每页50条
curl "http://localhost:8000/api/v1/stocks/info?limit=50&offset=50"
```

## 最佳实践

### 1. 数据提交

#### 批量提交优化

- **批次大小**: 建议每批次100-1000条记录
- **并发控制**: 避免过多并发请求
- **错误处理**: 检查批量提交的响应，处理失败记录

```python
import httpx
import asyncio

async def submit_batch_data(data_list, batch_size=500):
    """批量提交股票数据"""
    async with httpx.AsyncClient() as client:
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            response = await client.post(
                "http://localhost:8000/api/v1/stocks/data/batch",
                json={"data": batch}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"批次 {i//batch_size + 1}: 成功 {result['data']['success']} 条")
            else:
                print(f"批次 {i//batch_size + 1}: 提交失败")
```

#### 数据质量保证

- **数据验证**: 提交前验证数据格式和范围
- **时间戳**: 使用标准ISO 8601格式
- **价格精度**: 保持合理的价格精度 (通常2位小数)

### 2. 监控管理

#### 监控策略

- **分级管理**: 根据重要性设置不同优先级
- **定期审查**: 定期检查和调整监控列表
- **性能考虑**: 避免监控过多股票影响性能

#### 监控自动化

```python
async def auto_add_monitors(stock_codes, priority=5):
    """自动添加监控"""
    async with httpx.AsyncClient() as client:
        for code in stock_codes:
            response = await client.post(
                "http://localhost:8000/api/v1/monitors",
                json={
                    "stock_code": code,
                    "priority": priority,
                    "auto_create_stock": True
                }
            )
            
            if response.status_code == 200:
                print(f"✅ 添加监控成功: {code}")
            else:
                print(f"❌ 添加监控失败: {code}")
```

### 3. 错误处理

#### 常见错误处理

```python
async def handle_api_request(url, data=None):
    """通用API请求处理"""
    async with httpx.AsyncClient() as client:
        try:
            if data:
                response = await client.post(url, json=data)
            else:
                response = await client.get(url)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print("资源不存在")
            elif response.status_code == 422:
                print("参数验证失败:", response.json())
            else:
                print(f"请求失败: {response.status_code}")
                
        except httpx.TimeoutException:
            print("请求超时")
        except httpx.ConnectError:
            print("连接失败")
        except Exception as e:
            print(f"未知错误: {e}")
```

### 4. 性能优化

#### 查询优化

- **合理分页**: 避免一次查询过多数据
- **字段选择**: 只查询需要的字段
- **缓存策略**: 对频繁查询的数据进行缓存

#### 并发控制

```python
import asyncio
from asyncio import Semaphore

async def concurrent_requests(urls, max_concurrent=10):
    """控制并发请求数量"""
    semaphore = Semaphore(max_concurrent)
    
    async def fetch(url):
        async with semaphore:
            async with httpx.AsyncClient() as client:
                return await client.get(url)
    
    tasks = [fetch(url) for url in urls]
    return await asyncio.gather(*tasks)
```

## 集成示例

### Python集成示例

```python
import httpx
import asyncio
from datetime import datetime
from typing import List, Dict

class StockMonitorClient:
    """股票监控系统客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_prefix = "/api/v1"
    
    async def health_check(self) -> bool:
        """健康检查"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}{self.api_prefix}/health")
                return response.status_code == 200
            except:
                return False
    
    async def create_stock(self, stock_data: Dict) -> Dict:
        """创建股票信息"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{self.api_prefix}/stocks/info",
                json=stock_data
            )
            return response.json()
    
    async def submit_stock_data(self, data_list: List[Dict]) -> Dict:
        """批量提交股票数据"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{self.api_prefix}/stocks/data/batch",
                json={"data": data_list}
            )
            return response.json()
    
    async def add_monitor(self, stock_code: str, priority: int = 5) -> Dict:
        """添加监控"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{self.api_prefix}/monitors",
                json={
                    "stock_code": stock_code,
                    "priority": priority,
                    "auto_create_stock": False
                }
            )
            return response.json()
    
    async def get_monitor_codes(self) -> List[str]:
        """获取监控股票代码列表"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{self.api_prefix}/monitors/codes"
            )
            if response.status_code == 200:
                return response.json()["data"]
            return []

# 使用示例
async def main():
    client = StockMonitorClient()
    
    # 健康检查
    if await client.health_check():
        print("✅ 系统正常")
    else:
        print("❌ 系统异常")
        return
    
    # 创建股票信息
    stock_data = {
        "code": "000001",
        "name": "平安银行",
        "market": "SZ",
        "industry": "银行"
    }
    result = await client.create_stock(stock_data)
    print("创建股票:", result)
    
    # 添加监控
    result = await client.add_monitor("000001", priority=1)
    print("添加监控:", result)
    
    # 提交数据
    data_list = [
        {
            "code": "000001",
            "name": "平安银行",
            "current_price": 12.50,
            "volume": 1000000,
            "timestamp": datetime.now().isoformat()
        }
    ]
    result = await client.submit_stock_data(data_list)
    print("提交数据:", result)
    
    # 获取监控列表
    codes = await client.get_monitor_codes()
    print("监控股票:", codes)

if __name__ == "__main__":
    asyncio.run(main())
```

### JavaScript集成示例

```javascript
class StockMonitorClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.apiPrefix = '/api/v1';
    }

    async healthCheck() {
        try {
            const response = await fetch(`${this.baseUrl}${this.apiPrefix}/health`);
            return response.ok;
        } catch {
            return false;
        }
    }

    async createStock(stockData) {
        const response = await fetch(`${this.baseUrl}${this.apiPrefix}/stocks/info`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(stockData),
        });
        return response.json();
    }

    async submitStockData(dataList) {
        const response = await fetch(`${this.baseUrl}${this.apiPrefix}/stocks/data/batch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ data: dataList }),
        });
        return response.json();
    }

    async addMonitor(stockCode, priority = 5) {
        const response = await fetch(`${this.baseUrl}${this.apiPrefix}/monitors`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                stock_code: stockCode,
                priority: priority,
                auto_create_stock: false,
            }),
        });
        return response.json();
    }

    async getMonitorCodes() {
        const response = await fetch(`${this.baseUrl}${this.apiPrefix}/monitors/codes`);
        if (response.ok) {
            const result = await response.json();
            return result.data;
        }
        return [];
    }
}

// 使用示例
async function main() {
    const client = new StockMonitorClient();

    // 健康检查
    if (await client.healthCheck()) {
        console.log('✅ 系统正常');
    } else {
        console.log('❌ 系统异常');
        return;
    }

    // 创建股票信息
    const stockData = {
        code: '000001',
        name: '平安银行',
        market: 'SZ',
        industry: '银行',
    };
    const result = await client.createStock(stockData);
    console.log('创建股票:', result);

    // 添加监控
    const monitorResult = await client.addMonitor('000001', 1);
    console.log('添加监控:', monitorResult);

    // 提交数据
    const dataList = [
        {
            code: '000001',
            name: '平安银行',
            current_price: 12.50,
            volume: 1000000,
            timestamp: new Date().toISOString(),
        },
    ];
    const submitResult = await client.submitStockData(dataList);
    console.log('提交数据:', submitResult);

    // 获取监控列表
    const codes = await client.getMonitorCodes();
    console.log('监控股票:', codes);
}

main().catch(console.error);
```

## 常见问题

### Q1: 如何处理重复的股票代码？

A: 系统会自动处理重复的股票代码。如果股票已存在，创建操作会更新现有记录而不是创建新记录。

### Q2: 批量提交失败如何处理？

A: 批量提交会返回详细的结果信息，包括成功数量、失败数量和错误详情。可以根据错误信息重新提交失败的记录。

### Q3: 如何优化查询性能？

A: 
- 使用合理的分页参数
- 避免查询过大的时间范围
- 使用索引字段进行过滤
- 考虑使用缓存机制

### Q4: 系统支持的最大并发量是多少？

A: 系统支持的并发量取决于服务器配置和数据库性能。建议在生产环境中进行压力测试以确定最佳配置。

### Q5: 如何监控系统运行状态？

A: 
- 定期调用健康检查接口
- 监控日志文件
- 设置系统资源监控
- 配置告警机制

## 技术支持

如果在使用过程中遇到问题，请：

1. 查看API文档和错误信息
2. 检查系统日志
3. 参考本文档的常见问题部分
4. 联系技术支持团队

---

**注意**: 请确保在生产环境中使用HTTPS协议，并配置适当的安全措施。