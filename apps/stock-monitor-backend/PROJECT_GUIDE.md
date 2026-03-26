# Stock Monitor Backend - 项目开发指南

## 📋 项目概述

**Stock Monitor Backend** 是一个基于 FastAPI 的股票监控后端系统，提供股票数据采集、存储、监控、选股和量化分析的全套功能。

### 核心功能
- **实时数据采集**: 从同花顺、通达信等数据源采集股票实时数据
- **日线数据管理**: 支持 Tushare、Baostock、Akshare 多源数据同步
- **智能选股**: 通达信 3倍量+涨停 策略选股
- **量化评分**: 基于成交量异动的多维度评分系统
- **飞书同步**: 选股结果自动同步到飞书多维表格
- **截图分析**: 自动生成股票分时图和日K线图

---

## 🏗️ 项目结构

```
stock-monitor-backend/
├── app/                          # 核心应用代码
│   ├── api/                      # API 控制器 (路由层)
│   │   ├── stock_controller.py   # 股票数据接口
│   │   ├── stock_daily_controller.py  # 日线数据接口
│   │   ├── monitor_controller.py # 监控接口
│   │   ├── wencai_controller.py  # 问财数据接口
│   │   └── ...                   # 其他控制器
│   ├── config/                   # 配置管理
│   │   ├── settings.py           # 应用配置
│   │   ├── database.py           # 数据库配置
│   │   └── logging.py            # 日志配置
│   ├── crawler/                  # 爬虫模块
│   │   ├── okooo/                # 澳客网爬虫
│   │   ├── wencai_crawler.py     # 问财爬虫
│   │   └── base.py               # 爬虫基类
│   ├── models/                   # 数据模型 (ORM)
│   │   ├── stock.py              # 股票信息模型
│   │   ├── stock_daily.py        # 日线数据模型
│   │   ├── tdx_selection.py      # TDX选股结果模型
│   │   └── base.py               # 模型基类
│   ├── repositories/             # 数据访问层
│   │   ├── stock_repository.py   # 股票数据仓库
│   │   └── base.py               # 仓库基类
│   ├── services/                 # 业务逻辑层
│   │   ├── stock_service.py      # 股票服务
│   │   ├── tdx_selection_service.py  # TDX选股服务
│   │   ├── daily_workflow.py     # 每日工作流
│   │   ├── volume_analysis_service.py  # 成交量分析
│   │   └── ...                   # 其他服务
│   ├── utils/                    # 工具函数
│   └── main.py                   # FastAPI 应用入口
├── analyzer/                     # 独立分析器模块
├── docs/                         # 项目文档
├── scripts/                      # 运维脚本
├── sql/                          # SQL 脚本
├── static/                       # 静态文件 (前端页面)
├── tests/                        # 测试文件
├── docker/                       # Docker 配置
├── config/                       # 配置文件
├── requirements.txt              # Python 依赖
├── docker-compose.yml            # Docker Compose 配置
└── main.py                       # 启动入口
```

---

## 🎯 核心需求实现

### 1. 数据采集需求

#### 1.1 实时数据采集
- **来源**: 同花顺浏览器插件 (Chrome Extension)
- **接口**: `POST /api/v1/stocks/data/batch`
- **处理**: 解码原始数据 → 去重检查 → 存储到 `tonghuashun_stocks`
- **触发**: Pathway 实时计算引擎

#### 1.2 日线数据同步
- **主源**: Tushare API
- **备用**: Baostock、Akshare
- **存储**: `stock_daily` 表
- **策略**: 自动回退机制，优先使用本地 CSV 缓存

#### 1.3 通达信数据
- **板块读取**: 从 `C:\new_tdx_test\T0002\blocknew\` 读取 `.blk` 文件
- **选股结果**: 3倍量+涨停策略
- **存储**: `tdx_selection_result` 表

### 2. 选股策略需求

#### 2.1 通达信选股 (3倍量+涨停)
```python
# 策略逻辑
条件1: 成交量 >= 前一日成交量 * 3
条件2: 收盘价 >= 涨停价 (或接近涨停)
条件3: 数据来源于通达信板块文件
```

#### 2.2 问财选股
- **接口**: 问财网站抓取
- **存储**: `wencai_stocks` 表
- **字段**: 股票代码、名称、概念、行业、价格等

### 3. 量化评分需求

#### 3.1 当日异动分
- **存储**: `stock_score_result.total_score`
- **规则**:
  - 3倍量: +300分
  - 2倍量: +200分
  - 60日地量: +600分
  - 30日地量: +300分
  - 价格突破: 额外加分

#### 3.2 250日总分
- **存储**: `stock_info.volume_anomaly_score`
- **计算**: SUM(过去250天的当日异动分)
- **用途**: 股票排名和筛选

### 4. 每日工作流需求

```
Phase 1: SYNC_CHECK    - 盘后数据同步检查
Phase 2: SELECTION     - 执行选股策略
Phase 3: SCREENSHOT    - 生成股票截图
Phase 4: FEISHU_SYNC   - 同步到飞书
Phase 5: REPORT        - 生成日报
```

---

## 💾 数据存储方案

### 数据库架构

#### 主数据库: MySQL
```yaml
连接: mysql+aiomysql://root:12345678@192.168.1.6:3306/stock_monitor_new
字符集: utf8mb4
连接池: min=2, max=10
```

#### 缓存: Redis
```yaml
连接: redis://192.168.1.6:6379/0
用途: 数据去重缓存、基准量缓存、任务队列
```

### 核心数据表

#### 1. 股票信息表 (`stock_info`)
| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | VARCHAR(20) | 股票代码 (PK) |
| `name` | VARCHAR(100) | 股票名称 |
| `market` | VARCHAR(20) | 市场 (SH/SZ/BJ) |
| `volume_anomaly_score` | INT | 250日总分 |
| `is_active` | BOOLEAN | 是否活跃 |

#### 2. 日线数据表 (`stock_daily`)
| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | VARCHAR(20) | 股票代码 (联合PK) |
| `trade_date` | DATE | 交易日期 (联合PK) |
| `open/close/high/low` | DECIMAL | OHLC价格 |
| `vol` | BIGINT | 成交量(手) |
| `volume_ratio` | DECIMAL | 量比 |

#### 3. 评分结果表 (`stock_score_result`)
| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | VARCHAR(20) | 股票代码 (联合PK) |
| `trade_date` | DATE | 评分日期 (联合PK) |
| `total_score` | DECIMAL | 当日总得分 |
| `rule_scores` | JSON | 各规则得分详情 |

#### 4. TDX选股结果表 (`tdx_selection_result`)
| 字段 | 类型 | 说明 |
|------|------|------|
| `stock_code` | VARCHAR(20) | 股票代码 |
| `trade_date` | DATE | 选股日期 |
| `sector_code` | VARCHAR(20) | 板块代码 (如: 3BL0325) |
| `volume_ratio` | DECIMAL | 成交量比值 |
| `is_limit_up` | BOOLEAN | 是否涨停 |
| `source` | VARCHAR(20) | 来源 (tdx/wencai) |

#### 5. 问财数据表 (`wencai_stocks`)
| 字段 | 类型 | 说明 |
|------|------|------|
| `stock_code` | VARCHAR(20) | 股票代码 |
| `stock_name` | VARCHAR(100) | 股票名称 |
| `concept` | TEXT | 所属概念 |
| `industry` | VARCHAR(100) | 所属行业 |
| `source` | VARCHAR(20) | 来源标记 |

### 数据流转图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   数据源         │     │   数据处理       │     │   数据存储       │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ 同花顺插件       │────▶│ 数据解码         │────▶│ tonghuashun_    │
│ (实时数据)       │     │ 去重检查         │     │ stocks          │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ 通达信板块       │────▶│ 3倍量筛选        │────▶│ tdx_selection_  │
│ (.blk文件)       │     │ 涨停检测         │     │ result          │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ Tushare API     │────▶│ 数据清洗         │────▶│ stock_daily     │
│ (日线数据)       │     │ 格式转换         │     │                 │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ 问财网站         │────▶│ 网页解析         │────▶│ wencai_stocks   │
│ (选股数据)       │     │ 数据提取         │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                        ┌─────────────────┐
                        │   量化分析       │
                        ├─────────────────┤
                        │ 成交量分析       │────▶ stock_score_result
                        │ 形态识别         │────▶ volume_analysis_
                        │ 评分计算         │        result
                        └─────────────────┘
```

---

## 🔌 API 接口概览

### 股票数据接口
```
GET    /api/v1/stocks/info/{stock_code}    # 获取股票信息
POST   /api/v1/stocks/info                 # 创建股票信息
PUT    /api/v1/stocks/info/{stock_code}    # 更新股票信息
POST   /api/v1/stocks/data/batch           # 批量提交股票数据
GET    /api/v1/stocks/data/{stock_code}    # 获取股票数据
```

### 日线数据接口
```
GET    /api/v1/stock-daily/{code}          # 获取日线数据
POST   /api/v1/stock-daily/sync            # 同步日线数据
GET    /api/v1/stock-daily/{code}/latest   # 获取最新日线
```

### TDX选股接口
```
POST   /api/v1/tdx/selection               # 执行选股
GET    /api/v1/tdx/selection/results       # 获取选股结果
POST   /api/v1/tdx/sync-to-feishu          # 同步到飞书
```

### 监控接口
```
GET    /api/v1/monitors                    # 获取监控列表
POST   /api/v1/monitors/start              # 启动监控
POST   /api/v1/monitors/stop               # 停止监控
```

---

## 🚀 开发指南

### 环境配置

#### 1. 安装依赖
```bash
pip install -r requirements.txt
```

#### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件配置数据库连接
```

#### 3. 启动服务
```bash
# 开发模式
python main.py

# 或使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 添加新功能

#### 1. 添加新模型
```python
# app/models/my_model.py
from .base import BaseModel
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

class MyModel(BaseModel):
    __tablename__ = "my_table"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
```

#### 2. 添加新服务
```python
# app/services/my_service.py
from sqlalchemy.ext.asyncio import AsyncSession

class MyService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def do_something(self):
        # 业务逻辑
        pass
```

#### 3. 添加新接口
```python
# app/api/my_controller.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db_session

router = APIRouter(prefix="/api/v1/my", tags=["My Module"])

@router.get("/items")
async def get_items(db: AsyncSession = Depends(get_db_session)):
    # 接口逻辑
    return {"items": []}
```

#### 4. 注册路由
```python
# app/main.py
from .api import my_controller

app.include_router(my_controller.router)
```

### 数据库迁移

```bash
# 自动创建表 (基于 SQLAlchemy 模型)
# 启动应用时会自动执行

# 手动执行 SQL 脚本
mysql -u root -p stock_monitor_new < sql/create_tables.sql
```

---

## 📊 关键配置

### 应用配置 (`app/config/settings.py`)
```python
# 数据库
DATABASE_URL = "mysql+aiomysql://root:12345678@192.168.1.6:3306/stock_monitor_new"

# Redis
REDIS_URL = "redis://192.168.1.6:6379/0"

# Tushare
TUSHARE_TOKEN = "your_token_here"

# 数据保留策略
DATA_RETENTION_DAYS = 90

# 评分配置
SCORE_WINDOW_DAYS = 250  # 250日总分计算窗口
```

### 通达信配置
```python
# 通达信安装路径
TDX_PATH = "C:\\new_tdx_test"

# 板块文件路径
TDX_BLOCK_PATH = "C:\\new_tdx_test\\T0002\\blocknew"

# Python 插件路径
TDX_PYPLUGIN_PATH = "C:\\new_tdx_test\\PYPlugins\\user"
```

---

## 🔍 调试技巧

### 1. 查看日志
```bash
# 日志文件位置
tail -f logs/app.log

# 日志级别
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
```

### 2. API 文档
```
# Swagger UI
http://localhost:8000/docs

# ReDoc
http://localhost:8000/redoc
```

### 3. 数据库查询
```bash
# 连接数据库
mysql -h 192.168.1.6 -u root -p stock_monitor_new

# 常用查询
SELECT * FROM stock_info LIMIT 10;
SELECT * FROM tdx_selection_result WHERE trade_date = CURDATE();
```

---

## 📝 开发规范

### 代码规范
- 使用 `black` 格式化代码
- 使用 `isort` 排序导入
- 函数添加类型注解
- 异步函数使用 `async/await`

### 提交规范
```
feat: 新增功能
fix: 修复Bug
docs: 文档更新
refactor: 重构代码
test: 测试相关
chore: 构建/工具
```

### 目录规范
- 新模型 → `app/models/`
- 新服务 → `app/services/`
- 新接口 → `app/api/`
- 新脚本 → `scripts/`
- 新文档 → `docs/`

---

## 🔗 相关文档

- [API 文档](docs/API_DOCUMENTATION.md)
- [数据流文档](docs/stock_monitor_data_flow.md)
- [架构文档](docs/PROJECT_ARCHITECTURE_FINAL.md)
- [部署指南](docs/DEPLOYMENT_GUIDE.md)

---

## 📞 联系方式

如有问题，请联系项目维护者或查看项目文档。
