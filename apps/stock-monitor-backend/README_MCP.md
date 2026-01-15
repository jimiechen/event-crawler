# DeepSeek + Trae AI模型协作系统

## 项目概述

这是一个支持DeepSeek、GLM4.7、Gemini 3 Pro三个模型协作交流的系统，实现每日进度汇报、计划讨论、技术方案评审等功能。

## 系统架构

```
GLM4.7/Gemini (Trae AI) → 通过MCP工具调用DeepSeek爬虫
    ↓
DeepSeek爬虫 → 登录DeepSeek → 发送消息 → 获取响应
    ↓
返回响应给GLM4.7/Gemini → 整合项目信息 → 更新文档
    ↓
循环协作，直到达成共识
```

## 目录结构

```
projects/event-crawler/
├── apps/
│   └── stock-monitor-backend/
│       ├── app/
│       │   ├── crawler/
│       │   │   └── deepseek_crawler.py        # DeepSeek爬虫实现
│       │   ├── services/
│       │   │   ├── deepseek_mcp_service.py    # DeepSeek MCP服务
│       │   │   └── collaboration_service.py   # 协作文档服务
│       │   ├── api/
│       │   │   └── mcp_controller.py          # MCP API控制器
│       │   └── models/
│       │       └── collaboration_log.py        # 协作日志模型
│       ├── collaboration_docs/                # 协作文档目录
│       │   ├── daily_progress/                # 每日进度
│       │   ├── weekly_report/                 # 周报
│       │   ├── technical_review/               # 技术方案评审
│       │   ├── test_report/                   # 测试报告
│       │   └── standards.md                  # 文档规范
│       ├── config/
│       │   └── mcp_config.py               # MCP配置
│       ├── main_mcp.py                       # MCP主程序
│       └── .env.mcp.example                  # 配置示例
└── mcp-tools/                               # MCP工具目录
    ├── deepseek-mcp/
    │   ├── server/
    │   │   ├── mcp-server.ts                 # MCP服务器
    │   │   └── deepseek-tools.ts             # DeepSeek工具定义
    │   └── package.json
    └── collaboration-tools/
        ├── server/
        │   ├── mcp-server.ts                 # 协作MCP服务器
        │   └── doc-tools.ts                  # 文档工具定义
        └── package.json
```

## 快速开始

### 1. 环境要求

- Python 3.8+
- Node.js 16+
- Playwright浏览器
- SQLite/MySQL/PostgreSQL数据库

### 2. 安装Python依赖

```bash
cd apps/stock-monitor-backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install fastapi uvicorn playwright python-dotenv jinja2 sqlalchemy

# 安装Playwright浏览器
playwright install chromium
```

### 3. 配置环境变量

```bash
# 复制配置示例
cp .env.mcp.example .env

# 编辑.env文件，填入DeepSeek登录信息
# DEEPSEEK_EMAIL=your_email@example.com
# DEEPSEEK_PASSWORD=your_password
```

### 4. 安装TypeScript依赖

```bash
cd mcp-tools/deepseek-mcp
npm install

cd ../../collaboration-tools
npm install
```

### 5. 启动服务

```bash
# 启动MCP API服务（Python）
cd apps/stock-monitor-backend
python main_mcp.py

# 启动DeepSeek MCP服务器（TypeScript）
cd mcp-tools/deepseek-mcp
npm run dev

# 启动协作文档MCP服务器（TypeScript）
cd mcp-tools/collaboration-tools
npm run dev
```

## 使用示例

### 示例1: 了解项目和代码情况

```python
# GLM4.7读取项目结构和代码
# 调用MCP工具 send_message_to_deepseek
# 发送: "请分析event-crawler项目的整体架构和关键模块"
# DeepSeek响应: 提供架构分析
# GLM4.7整合: 结合实际代码，生成详细的项目分析文档
# 更新文档并署名
```

### 示例2: 技术方案评审

```python
# Gemini读取技术方案文档
# 调用MCP工具 send_message_to_deepseek
# 发送: "请评审这个技术方案: [方案内容]"
# DeepSeek响应: 提供评审意见
# Gemini整合: 结合项目实际情况，完善评审意见
# 更新技术评审文档并署名
```

### 示例3: 日报

```python
# GLM4.7读取今日完成的任务和代码变更
# 调用MCP工具 send_message_to_deepseek
# 发送: "今日完成了以下工作，请帮忙整理成日报: [工作内容]"
# DeepSeek响应: 提供日报建议
# GLM4.7整合: 结合项目实际情况，完善日报
# 更新日报文档并署名
```

### 示例4: 周报

```python
# Gemini读取本周所有日报和关键变更
# 调用MCP工具 send_message_to_deepseek
# 发送: "本周工作汇总，请帮忙整理成周报: [周工作内容]"
# DeepSeek响应: 提供周报建议
# Gemini整合: 结合项目实际情况，完善周报
# 更新周报文档并署名
```

### 示例5: 测试报告

```python
# GLM4.7读取测试用例和测试结果
# 调用MCP工具 send_message_to_deepseek
# 发送: "测试结果如下，请帮忙整理成测试报告: [测试数据]"
# DeepSeek响应: 提供测试报告建议
# GLM4.7整合: 结合项目实际情况，完善测试报告
# 更新测试报告文档并署名
```

## API接口

### DeepSeek相关

#### 登录DeepSeek
```bash
POST /mcp/deepseek/login
{
  "email": "your_email@example.com",
  "password": "your_password"
}
```

#### 发送消息给DeepSeek
```bash
POST /mcp/deepseek/send
{
  "message": "你好，请分析这个股票监控项目的架构",
  "conversation_id": "optional_conversation_id",
  "from_model": "GLM4.7"
}
```

#### 开始新会话
```bash
POST /mcp/deepseek/session/new
{
  "from_model": "GLM4.7"
}
```

#### 获取对话历史
```bash
GET /mcp/deepseek/conversations?conversation_id=optional_id
```

### 协作文档相关

#### 创建协作文档
```bash
POST /mcp/collaboration/doc/create
{
  "doc_type": "daily_progress",
  "title": "2026-01-14 每日进度",
  "content": "今日完成的工作内容...",
  "author": "GLM4.7"
}
```

#### 更新协作文档
```bash
POST /mcp/collaboration/doc/update
{
  "doc_path": "daily_progress/daily_progress_20260114.md",
  "content": "更新后的内容...",
  "signature": "[2026-01-14 10:30] @GLM4.7: 添加了技术方案细节",
  "author": "GLM4.7"
}
```

#### 获取协作文档
```bash
GET /mcp/collaboration/doc/{doc_path}
```

#### 列出协作文档
```bash
GET /mcp/collaboration/docs?doc_type=daily_progress
```

## 文档规范

所有协作文档必须遵循[文档规范](collaboration_docs/standards.md)：

### Markdown文档结构
```markdown
# [文档标题]

## 元数据
- 创建时间: YYYY-MM-DD HH:MM:SS
- 最后更新: YYYY-MM-DD HH:MM:SS
- 当前模型: DeepSeek/GLM4.7/Gemini
- 文档版本: v1.0
- 文档类型: [daily_progress/weekly_report/technical_review/test_report]

## 内容
[实际内容]

## 变更记录
- [时间] @ModelName: [变更描述]
```

### 署名规范
- 署名格式: `[YYYY-MM-DD HH:MM] @ModelName: [操作描述]`
- 示例: `[2026-01-14 10:30] @GLM4.7: 添加了技术方案细节]`

## Trae AI协作规则

### GLM4.7约束规则
- 必须遵循项目规则中的中文文档要求
- 使用MCP工具与DeepSeek交互
- 更新文档时必须添加署名
- 读取项目代码和文档时遵循项目结构

### Gemini 3 Pro约束规则
- 必须遵循项目规则中的代码质量标准
- 使用MCP工具与DeepSeek交互
- 更新文档时必须添加署名
- 技术方案评审需符合安全规范

### 协作流程规则
1. GLM4.7/Gemini读取项目文档和代码
2. 通过MCP工具调用DeepSeek获取外部视角
3. 整合DeepSeek的建议和本地项目情况
4. 更新协作文档并添加署名
5. 循环直到达成共识

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DEEPSEEK_EMAIL | DeepSeek账号邮箱 | - |
| DEEPSEEK_PASSWORD | DeepSeek账号密码 | - |
| MCP_API_HOST | API服务地址 | 0.0.0.0 |
| MCP_API_PORT | API服务端口 | 8000 |
| MCP_API_KEY | API密钥 | - |
| COLLABORATION_DIR | 协作文档目录 | collaboration_docs |
| ALLOWED_MODELS | 允许的模型列表 | GLM4.7,Gemini,DeepSeek |
| DATABASE_URL | 数据库连接URL | sqlite:///./collaboration.db |
| LOG_LEVEL | 日志级别 | INFO |
| LOG_FILE | 日志文件路径 | mcp_collaboration.log |

## 故障排查

### 问题1: DeepSeek登录失败
- 检查邮箱和密码是否正确
- 检查网络连接是否正常
- 查看日志文件获取详细错误信息

### 问题2: MCP工具调用失败
- 确认MCP API服务已启动
- 检查API地址和端口配置
- 查看MCP服务器日志

### 问题3: 文档更新失败
- 检查文档路径是否正确
- 确认有写入权限
- 查看API日志获取详细错误信息

## 开发计划

- [x] 阶段一：基础设施
- [x] 阶段二：DeepSeek爬虫
- [x] 阶段三：MCP服务
- [x] 阶段四：MCP工具定义
- [ ] 阶段五：集成测试
- [ ] 阶段六：性能优化
- [ ] 阶段七：文档完善

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 联系方式

- 项目地址: https://github.com/your-org/event-crawler
- 问题反馈: https://github.com/your-org/event-crawler/issues

---

*本文档由Trae AI协作系统维护*