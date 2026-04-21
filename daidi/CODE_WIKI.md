# 「待敌」市场分析系统 - Code Wiki

## 项目概述

「待敌」市场分析系统是一个六层递进式市场分析框架，结合实时数据采集和LLM智能分析，自动生成投资决策报告。系统名称来源于《孙子兵法·形篇》："昔之善战者，先为不可胜，以待敌之可胜。"

### 核心价值
- **多维度数据整合**：从宏观风险到个股仓位的六层分析
- **实时数据采集**：自动获取最新市场数据和新闻信号
- **LLM智能分析**：利用大模型进行产业链匹配和趋势判断
- **可视化决策**：Web仪表盘直观展示分析结果
- **自动化报告**：生成结构化的投资决策报告

## 系统架构

### 六层架构设计

```
┌─────────────────────────────────────────────────────┐
│                   Layer 0 风险管理                    │
│  上证指数 / VIX / 汇率 / 北向资金                     │
│  → 输出：GREEN / YELLOW / RED + 最大仓位              │
├─────────────────────────────────────────────────────┤
│                   Layer 1 实业数据                    │
│  农产品价格 / 期货铜螺纹铝 / M1M2剪刀差 / PMI         │
│  / 用电量 / 建筑业景气 / 房地产投资 / BDI             │
│  → 输出：综合评分 + 异动指标                          │
├─────────────────────────────────────────────────────┤
│                 Layer 2 金融期货                      │
│  美元指数 / 美中10Y利差 / QVIX / 股指期货基差          │
│  / 黄金现货 / SPDR持仓 / ISM PMI                     │
│  → 输出：资金方向 + 背离信号                          │
├─────────────────────────────────────────────────────┤
│               Layer 3 产业链传导图谱                  │
│  LLM 动态匹配产业链 + 国际信号源新闻数据              │
│  （AI算力 / 半导体 / 新能源车 / 航空航天 / 有色金属）  │
│  → 输出：激活产业链 + 最佳操作节点                    │
├─────────────────────────────────────────────────────┤
│                 Layer 4 头部企业                      │
│  自动化财务评分：PE/PB/ROE/毛利率/营收增速            │
│  四道过滤器：收入结构 + 客户 + 毛利率 + 资本开支       │
│  → 输出：REAL / WATCH / FAKE 筛选结果                │
├─────────────────────────────────────────────────────┤
│                 Layer 5 个股确认                      │
│  量价信号（突破/缩量/蓄势）+ 支撑止损位              │
│  → 输出：GO / WAIT / NO + 建议仓位 + 首批金额        │
└─────────────────────────────────────────────────────┘
```

## 核心功能模块

### 1. 主控模块（main.py）

[main.py](file:///workspace/daidi/main.py) 是系统的主控程序，负责串联六层分析，生成终端交互式报告。

**主要功能**：
- 解析命令行参数（总资金、市场环境、指定股票代码）
- 按顺序执行各层分析
- 格式化输出分析结果
- 保存分析报告到本地

**关键函数**：
- `main()`：主函数，协调整个分析流程
- `print_layer0()` 至 `print_layer45()`：各层结果的格式化输出
- `save_report()`：保存分析报告

### 2. 风险管理模块（layer0_risk.py）

[layer0_risk.py](file:///workspace/daidi/layer0_risk.py) 是系统的否决层，负责评估市场风险并给出最大仓位建议。

**主要功能**：
- 获取大盘环境关键指标（上证指数、北向资金、VIX、人民币汇率）
- 根据预设规则评估风险等级
- 输出风险状态和最大仓位建议

**关键函数**：
- `get_market_env()`：获取市场环境数据
- `evaluate_layer0()`：评估风险等级
- `run_layer0()`：执行风险评估并返回结果

### 3. 实业数据模块（layer1_industry.py）

[layer1_industry.py](file:///workspace/daidi/layer1_industry.py) 负责采集和分析实业相关数据，作为市场温度的指示器。

**主要功能**：
- 采集食品板块数据（农产品、生猪、玉米、大豆等）
- 采集大宗商品数据（铜、螺纹钢、原油、黄金、铝等）
- 采集宏观货币数据（M1/M2、社融、PMI等）
- 采集基建需求数据（建筑业景气、房地产投资等）
- 采集全国用电量数据
- 采集物流运价数据（BDI、BCI等）
- 识别异动指标并生成分析

**关键函数**：
- `get_food_data()`：获取食品板块数据
- `get_bulk_data()`：获取大宗商品数据
- `get_macro_data()`：获取宏观货币数据
- `get_infra_data()`：获取基建需求数据
- `get_electricity_data()`：获取用电量数据
- `get_logistics_data()`：获取物流运价数据

### 4. 金融期货模块（layer2_futures.py）

负责采集和分析金融期货相关数据，判断资金方向和背离信号。

**主要功能**：
- 采集美元指数、美中10Y利差、沪深300 QVIX等数据
- 分析股指期货基差
- 识别资金方向和背离信号

### 5. 产业链传导模块（layer3_chains.py）

利用LLM动态匹配产业链，结合国际信号源新闻数据，识别激活的产业链和最佳操作节点。

**主要功能**：
- 内置产业链知识库
- LLM结合实时数据进行产业链匹配
- 分析国际信号源新闻数据
- 输出激活的产业链和最佳操作节点

### 6. 头部企业与个股确认模块（layer45_stocks.py）

负责筛选头部企业并进行个股确认，给出具体的投资决策。

**主要功能**：
- 自动抓取企业财务数据
- 四道过滤器筛选（收入结构、客户、毛利率、资本开支）
- 量价信号分析（突破、缩量、蓄势）
- 计算支撑止损位和建议仓位
- 分批建仓策略建议

### 7. 国际信号采集模块（international_signals.py）

负责从东方财富抓取近14天新闻，提取结构化信号，并获取费城半导体指数实时行情。

**主要功能**：
- 32个关键词从东方财富抓取新闻
- 提取结构化信号
- 获取费城半导体指数实时行情

### 8. 大模型客户端（llm_client.py）

负责与大模型API交互，支持多个品牌的大模型。

**主要功能**：
- 支持DeepSeek、OpenAI、通义千问、智谱GLM、Kimi、硅基流动等品牌
- 图形化配置器
- 测试连接和保存配置

### 9. 趋势判断模块（trend_judge.py）

利用LLM进行趋势综合判定。

**主要功能**：
- 综合各层数据进行趋势判断
- 生成趋势分析报告

## 技术栈与依赖

### 核心技术栈
- **编程语言**：Python 3.9+
- **数据采集**：akshare（金融数据）、东方财富API
- **数据处理**：pandas、numpy
- **可视化**：Rich（终端美化）、ECharts（Web仪表盘）
- **大模型集成**：支持多个大模型API
- **Web界面**：HTML、JavaScript

### 主要依赖包

| 依赖包 | 用途 | 来源 |
|--------|------|------|
| akshare | 金融数据采集 | [requirements.txt](file:///workspace/daidi/requirements.txt) |
| pandas | 数据处理 | [requirements.txt](file:///workspace/daidi/requirements.txt) |
| numpy | 数值计算 | [requirements.txt](file:///workspace/daidi/requirements.txt) |
| rich | 终端美化输出 | [requirements.txt](file:///workspace/daidi/requirements.txt) |
| requests | HTTP请求 | [requirements.txt](file:///workspace/daidi/requirements.txt) |
| python-dotenv | 环境变量管理 | [requirements.txt](file:///workspace/daidi/requirements.txt) |
| echarts | Web可视化 | [web/echarts.min.js](file:///workspace/daidi/web/echarts.min.js) |

## 关键API和函数

### 1. 风险管理API
- `run_layer0()`：执行风险评估，返回风险状态和环境数据
- `get_market_env()`：获取大盘环境关键指标
- `evaluate_layer0()`：根据环境数据评估风险等级

### 2. 实业数据API
- `run_layer1()`：执行实业数据采集和分析
- `get_food_data()`：获取食品板块数据
- `get_bulk_data()`：获取大宗商品数据
- `get_macro_data()`：获取宏观货币数据
- `get_infra_data()`：获取基建需求数据
- `get_electricity_data()`：获取用电量数据
- `get_logistics_data()`：获取物流运价数据

### 3. 金融期货API
- `run_layer2()`：执行金融期货数据采集和分析

### 4. 产业链传导API
- `run_layer3()`：执行产业链匹配和分析

### 5. 企业与个股API
- `run_layer4()`：执行头部企业筛选
- `run_layer5()`：执行个股确认和决策

### 6. 国际信号API
- 从东方财富抓取新闻数据
- 获取费城半导体指数实时行情

### 7. 大模型API
- 支持多个品牌的大模型
- 提供图形化配置界面

## 配置与部署

### 1. 环境要求
- Python 3.9+
- 网络连接（用于数据采集和API调用）
- 可选：大模型API Key（用于产业链分析和趋势判断）

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 大模型配置

**方式一：图形化配置器（推荐）**

```bash
python setup_llm.py
```

**方式二：手动创建 `.env` 文件**

```
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

### 4. 运行模式

**方式一：终端交互式报告**

```bash
python main.py
python main.py --capital 500000          # 指定总资金50万
python main.py --env BULL                # 强制牛市环境
python main.py --codes 300308 300394     # 只分析指定股票
```

**方式二：生成JSON数据文件**

```bash
python export_json.py
```

**方式三：定时自动执行**

- **Windows**：双击 `run_daily.bat`
- **macOS/Linux**：

```bash
chmod +x run_daily.sh
./run_daily.sh
```

## 使用指南

### 1. 快速开始

**Windows**：双击 `start.bat`
**macOS**：双击 `start.command`（首次需右键→打开→确认）
**Linux**：终端运行 `chmod +x start.command && ./start.command`

脚本会自动完成以下步骤：
1. 检测 Python 环境
2. 安装/更新依赖包
3. 运行六层分析，生成数据
4. 启动 Web 服务器，自动打开浏览器

### 2. 查看分析结果

- **终端报告**：直接在终端查看美化后的分析结果
- **Web仪表盘**：打开 `web/index.html` 查看可视化仪表盘
- **报告存档**：分析结果会自动保存到 `reports/` 目录

### 3. 检查数据完整性

```bash
python test_all.py
```

逐层测试，确认所有 API 接口可用，输出每层的关键数据摘要。

## 扩展与自定义

### 1. 添加/修改分析标的

编辑 `layer45_stocks.py` 中的 `COMPANY_DB` 字典：

```python
"300308": CompanyProfile(
    code="300308", name="中际旭创", chain="AI算力链", node="光模块",
    revenue_score=20, client_score=22, margin_score=18, capex_score=20,
    green_flags=["800G光模块全球份额第一"], red_flags=["客户集中度高"],
    verdict="REAL", note="800G光模块龙头"
),
```

### 2. 调整异动阈值

在 `layer1_industry.py` 的 `zscore_signal()` 函数中修改 Z-Score 阈值：

- `> 2.0` → ALERT_UP（强烈异动）
- `> 1.5` → UP（正向信号）
- `< -1.5` → DOWN（负向信号）
- `< -2.0` → ALERT_DOWN（强烈异动）

### 3. 修改国际信号关键词

编辑 `international_signals.py` 中的 `KEYWORD_GROUPS` 字典，按产业链添加/删除新闻搜索关键词。

### 4. LLM 模型切换

**方式一：图形化配置器**
```bash
python setup_llm.py
```

**方式二：编辑 `llm_config.json`**
```json
{
  "provider": "deepseek",
  "api_key": "sk-xxx",
  "base_url": "https://api.deepseek.com",
  "model": "deepseek-reasoner"
}
```

## 故障排查

### 1. 常见问题

**Q: 运行报错 "ConnectionError" 或连接超时？**
A: 部分数据源（北向资金、美股行情）偶尔不稳定，系统已做容错处理，不影响整体分析。

**Q: 没有 DeepSeek API Key 能用吗？**
A: 能。L3 产业链会退化为规则匹配（基于关键词触发），L5 仓位计算和 L0-L2 数据采集不受影响。

**Q: 分析耗时多久？**
A: 约 2-3 分钟。其中新闻采集 ~25秒、LLM 调用 ~20秒、行情数据 ~30秒，其余为并行 API 调用。

**Q: 数据更新频率？**
A: L0/L2/L5 实时数据每日更新；L1 宏观数据月度更新（自动取最新可用）；L4 财务数据季报更新。

### 2. 日志与调试

- 错误日志：`logs/error.log`
- 运行日志：`logs/` 目录下的其他日志文件
- 测试脚本：`python test_all.py` 可用于验证各层数据采集是否正常

## 项目文件结构

```
daidi/
├── main.py                    # 主控程序（终端交互式报告）
├── export_json.py             # JSON 导出（供 Web 面板）
├── layer0_risk.py             # L0 风险管理
├── layer1_industry.py         # L1 实业数据采集
├── layer2_futures.py          # L2 金融期货数据
├── layer3_chains.py           # L3 产业链匹配（LLM）
├── layer45_stocks.py          # L4 企业筛选 + L5 个股确认
├── international_signals.py   # 国际信号源采集（新闻+指数）
├── trend_judge.py             # 趋势综合判定（LLM）
├── llm_client.py              # 大模型客户端（多品牌支持）
├── test_all.py                # 逐层测试脚本
├── run_daily.bat              # Windows 一键运行
├── run_daily.sh               # macOS / Linux 一键运行
├── requirements.txt            # Python 依赖清单
├── setup_llm.py               # 大模型图形化配置器
├── llm_config.json            # 大模型配置（配置器自动生成）
├── .env                       # API Key 配置（旧方式，可选）
├── web/
│   ├── index.html             # Web 面板入口
│   ├── config.html            # 大模型配置页面
│   ├── echarts.min.js         # ECharts 本地副本
│   ├── dashboard.json         # 最新分析数据
│   └── dashboard_standalone.html
├── reports/                   # 文本报告存档
├── logs/                      # 运行日志
└── docs/                      # 文档和图片
```

## 总结

「待敌」市场分析系统是一个功能强大、架构清晰的投资决策辅助工具。通过六层递进式分析，从宏观风险到个股仓位，为投资者提供全面的市场洞察和决策建议。系统结合了实时数据采集、LLM智能分析和可视化展示，为投资决策提供了科学依据。

系统的设计理念——"先为不可胜，以待敌之可胜"——体现了风险管理的重要性，通过严格的风险控制和多维度分析，帮助投资者在复杂多变的市场环境中做出更加理性的决策。