# Okooo 数据流水线实施文档

## 1. 实施目标 (Implementation Goals)
构建全自动化的体育赛事数据处理流水线，实现从原始网页爬取到向量知识库构建的完整闭环。具体目标包括：
1.  **数据完整性**：成功爬取指定比赛ID的详情页HTML，无乱码，保留所有关键赔率和事件数据。
2.  **数据可用性**：将HTML清洗为结构化Markdown，便于阅读和LLM处理。
3.  **检索增强**：将Markdown切片并向量化，存入ChromaDB，支持语义检索。
4.  **系统集成**：提供标准接口供sports-betting框架调用。

## 2. 处理流程设计 (Workflow Design)

### 阶段一：HTML源文件爬取 (Phase 1)
- **输入**：Match ID列表 (JSON格式)。
- **过程**：
    1.  初始化爬虫任务，加载ID列表。
    2.  启动浏览器实例 (Playwright)，注入反爬配置 (User-Agent, stealth.js)。
    3.  遍历ID，访问 `https://www.okooo.com/soccer/match/{match_id}/`。
    4.  **关键步骤**：检测WAF拦截，若被拦截则重试或切换IP/Session。
    5.  保存原始HTML到 `data/okooo/raw_html/{date}/`，文件名包含 `match_id` 和哈希值。
    6.  **乱码修复**：在保存前将 GBK/GB2312 编码声明替换为 UTF-8。
- **输出**：UTF-8 编码的 HTML 文件。

### 阶段二：数据提取与清洗 (Phase 2)
- **输入**：原始 HTML 文件。
- **过程**：
    1.  使用 BeautifulSoup4 解析 HTML。
    2.  提取比赛元数据（时间、联赛、队伍）。
    3.  提取赔率表格（欧赔、亚盘、大小球）。
    4.  提取比赛事件（进球、红黄牌）。
    5.  生成 Markdown 格式的摘要文档。
- **输出**：标准化 JSON 数据 + Markdown 文档。

### 阶段三：向量结构组装 (Phase 3)
- **输入**：Markdown 文档。
- **过程**：
    1.  **Chunking**：按“比赛信息”、“赔率变化”、“事件流”进行文本切片。
    2.  **Embedding**：调用 Embedding 模型（如 OpenAI text-embedding-3 或 HuggingFace 本地模型）生成向量。
    3.  **Storage**：存入 Chroma 向量数据库，附带 Metadata（MatchID, Date, League）。
- **输出**：ChromaDB Collection。

### 阶段四 & 五：集成与应用 (Phase 4 & 5)
- **集成**：在 sports-betting 框架中注册 ChromaRetriever。
- **应用**：实现基于自然语言的赛事查询（如“查询切尔西最近的主场赔率变化”）。

## 3. 技术栈与工具 (Tech Stack)
- **编程语言**: Python 3.10+
- **爬虫**: Playwright (动态渲染), BeautifulSoup4 (解析)
- **数据库**: 
    - 向量库: ChromaDB (Local/Server)
    - 关系型: MySQL (可选，用于存储任务状态)
- **LLM/Embeddings**: LangChain, OpenAI API / HuggingFace Transformers
- **工具库**: loguru (日志), pydantic (数据校验), pandas (数据处理)

## 4. 目录结构与配置 (Directory Structure)
```
python/event-crawler/
├── apps/stock-monitor-backend/
│   ├── app/
│   │   ├── crawler/
│   │   │   ├── okooo_crawler.py      # [核心] 澳客网爬虫实现
│   │   │   └── base.py               # 爬虫基类 (Session管理)
│   ├── scripts/
│   │   ├── batch_crawl_okooo.py      # [脚本] 批量爬取入口
│   │   └── crawl_bypass_test.py      # [测试] WAF绕过测试
│   ├── docs/
│   │   ├── implementation/           # 实施文档
│   │   └── reviews/                  # 评审记录
│   └── task_plan.md                  # 任务进度计划
├── data/
│   └── okooo/
│       ├── raw_html/                 # 原始 HTML (按日期归档)
│       └── markdown/                 # 清洗后的 Markdown
└── requirements.txt                  # 项目依赖
```

## 5. 核心代码模块设计 (Core Code Design)
- **OkoooCrawler (app/crawler/okooo_crawler.py)**:
    - `fetch_and_parse(url)`: 负责页面访问、等待加载、重试逻辑。
    - `save_raw_html(content, match_id)`: 负责编码修复 (GBK->UTF-8) 和文件持久化。
    - `extract_data(html)`: (Phase 2) 负责解析 DOM 树。

## 6. 错误处理与日志 (Error Handling)
- **日志策略**: 使用 `loguru`，按天轮转日志文件 `logs/crawler_{date}.log`。
- **异常捕获**:
    - `TimeoutError`: 页面加载超时 -> 重试 3 次。
    - `WAF Block (405/403)`: 检测到拦截 -> 暂停任务，记录错误，发送告警。
    - `ParseError`: 解析失败 -> 保存原始 HTML 以便后续排查，不中断任务。

## 7. 测试方案 (Testing Plan)
- **单元测试**: 测试 `save_raw_html` 的编码转换逻辑；测试正则表达式提取 ID 的准确性。
- **集成测试**:
    - **Phase 1**: 运行 `batch_crawl_okooo.py` 爬取 5 个样本，检查文件大小 (>50KB) 和内容可读性。
    - **Phase 2**: 对比 HTML 和生成的 Markdown，确保赔率数据无缺失。

## 8. 部署与执行计划 (Deployment)
1.  **环境准备**: `pip install -r requirements.txt && playwright install chromium`
2.  **执行**: `python scripts/batch_crawl_okooo.py`
3.  **监控**: 观察日志输出，监控 `data/okooo/raw_html` 目录文件增长情况。

## 9. 回滚与监控 (Rollback & Monitoring)
- **回滚**: 如果新代码导致数据损坏，回退 git commit，并使用备份的 HTML 重新处理。
- **监控**: 统计成功率 (Success Rate)，若低于 80% 自动暂停。
