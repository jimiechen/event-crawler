# MCP系统时序图

## 概述

本文档详细说明DeepSeek + Trae AI模型协作系统中各组件之间的交互时序。

## 场景一：GLM4.7读取项目代码并创建协作文档

### 时序图

```mermaid
sequenceDiagram
    autonumber
    participant GLM47 as GLM4.7<br/>Trae IDE
    participant DeepSeekMCP as DeepSeek MCP工具<br/>stdio
    participant CollabMCP as 协作文档MCP工具<br/>stdio
    participant FastAPI as FastAPI服务<br/>端口: 8000
    participant CollabService as 协作文档服务
    participant CollabDocs as 协作文档目录
    participant ProjectFiles as 项目代码文件
    
    Note over GLM47: 用户请求分析项目代码
    
    GLM47->>DeepSeekMCP: 1. 调用read_file工具<br/>请求读取app/main.py
    Note over DeepSeekMCP: 接收stdio请求
    
    DeepSeekMCP->>FastAPI: 2. HTTP GET /file?path=app/main.py
    Note over FastAPI: 接收HTTP请求<br/>端口8000
    
    FastAPI->>ProjectFiles: 3. 读取app/main.py文件
    Note over ProjectFiles: 文件系统读取
    
    ProjectFiles-->>FastAPI: 4. 返回文件内容
    Note over FastAPI: 获取文件内容
    
    FastAPI-->>DeepSeekMCP: 5. HTTP 200 OK<br/>返回文件内容
    Note over DeepSeekMCP: 接收HTTP响应
    
    DeepSeekMCP-->>GLM47: 6. stdio返回文件内容
    Note over GLM47: 获取代码内容
    
    GLM47->>GLM47: 7. 分析代码结构
    Note over GLM47: AI分析代码
    
    GLM47->>CollabMCP: 8. 调用create_collaboration_doc工具<br/>doc_type=daily_progress
    Note over CollabMCP: 接收stdio请求
    
    CollabMCP->>FastAPI: 9. HTTP POST /mcp/collaboration/doc/create<br/>{doc_type, title, content, author}
    Note over FastAPI: 接收HTTP请求<br/>端口8000
    
    FastAPI->>CollabService: 10. 调用create_document方法
    Note over CollabService: 处理文档创建
    
    CollabService->>CollabDocs: 11. 写入daily_progress_20260114.md
    Note over CollabDocs: 文件系统写入
    
    CollabDocs-->>CollabService: 12. 文件创建成功
    Note over CollabService: 确认文件写入
    
    CollabService->>CollabService: 13. 记录文档版本到数据库
    Note over CollabService: 数据库操作
    
    CollabService-->>FastAPI: 14. 返回成功结果<br/>{success: true, filepath: ...}
    Note over FastAPI: 获取创建结果
    
    FastAPI-->>CollabMCP: 15. HTTP 200 OK<br/>返回创建结果
    Note over CollabMCP: 接收HTTP响应
    
    CollabMCP-->>GLM47: 16. stdio返回成功<br/>文档路径: collaboration_docs/daily_progress/...
    Note over GLM47: 获取创建结果
    
    Note over GLM47: 任务完成<br/>成功创建协作文档
```

### 关键步骤说明

1. **读取代码** (步骤1-6)
   - GLM4.7通过MCP工具读取项目文件
   - MCP工具通过HTTP调用FastAPI服务
   - FastAPI从文件系统读取文件
   - 结果通过stdio返回给GLM4.7

2. **分析代码** (步骤7)
   - GLM4.7分析代码内容
   - 准备创建协作文档

3. **创建文档** (步骤8-16)
   - GLM4.7通过MCP工具创建文档
   - MCP工具通过HTTP调用FastAPI服务
   - FastAPI调用协作文档服务
   - 服务写入Markdown文件到文件系统
   - 服务记录文档版本到数据库
   - 结果通过stdio返回给GLM4.7

---

## 场景二：Gemini调用DeepSeek获取架构分析

### 时序图

```mermaid
sequenceDiagram
    autonumber
    participant Gemini as Gemini 3 Pro<br/>Trae IDE
    participant DeepSeekMCP as DeepSeek MCP工具<br/>stdio
    participant FastAPI as FastAPI服务<br/>端口: 8000
    participant DeepSeekCrawler as DeepSeek爬虫<br/>Playwright
    participant DeepSeekWeb as DeepSeek网页版<br/>HTTPS
    
    Note over Gemini: 用户请求分析项目架构
    
    Gemini->>DeepSeekMCP: 1. 调用deepseek_login工具<br/>{email, password}
    Note over DeepSeekMCP: 接收stdio请求
    
    DeepSeekMCP->>FastAPI: 2. HTTP POST /mcp/deepseek/login
    Note over FastAPI: 接收HTTP请求<br/>端口8000
    
    FastAPI->>DeepSeekCrawler: 3. 调用login方法
    Note over DeepSeekCrawler: 初始化爬虫
    
    DeepSeekCrawler->>DeepSeekWeb: 4. Playwright打开https://chat.deepseek.com
    Note over DeepSeekWeb: 浏览器自动化
    
    DeepSeekWeb-->>DeepSeekCrawler: 5. 返回登录页面
    Note over DeepSeekCrawler: 获取页面元素
    
    DeepSeekCrawler->>DeepSeekWeb: 6. Playwright输入邮箱
    Note over DeepSeekWeb: 表单填写
    
    DeepSeekCrawler->>DeepSeekWeb: 7. Playwright输入密码
    Note over DeepSeekWeb: 表单填写
    
    DeepSeekCrawler->>DeepSeekWeb: 8. Playwright点击登录按钮
    Note over DeepSeekWeb: 提交表单
    
    DeepSeekWeb-->>DeepSeekCrawler: 9. 返回登录成功页面
    Note over DeepSeekCrawler: 验证登录
    
    DeepSeekCrawler->>DeepSeekCrawler: 10. 保存Cookie
    Note over DeepSeekCrawler: 会话管理
    
    DeepSeekCrawler-->>FastAPI: 11. 返回登录成功<br/>{success: true}
    Note over FastAPI: 获取登录结果
    
    FastAPI-->>DeepSeekMCP: 12. HTTP 200 OK<br/>返回登录成功
    Note over DeepSeekMCP: 接收HTTP响应
    
    DeepSeekMCP-->>Gemini: 13. stdio返回登录成功
    Note over Gemini: 获取登录结果
    
    Note over Gemini: 登录成功<br/>准备发送消息
    
    Gemini->>DeepSeekMCP: 14. 调用send_message_to_deepseek工具<br/>{message: "请分析项目架构"}
    Note over DeepSeekMCP: 接收stdio请求
    
    DeepSeekMCP->>FastAPI: 15. HTTP POST /mcp/deepseek/send
    Note over FastAPI: 接收HTTP请求<br/>端口8000
    
    FastAPI->>DeepSeekCrawler: 16. 调用send_message方法
    Note over DeepSeekCrawler: 发送消息
    
    DeepSeekCrawler->>DeepSeekWeb: 17. Playwright查找输入框
    Note over DeepSeekWeb: 查找元素
    
    DeepSeekCrawler->>DeepSeekWeb: 18. Playwright输入消息
    Note over DeepSeekWeb: 输入内容
    
    DeepSeekCrawler->>DeepSeekWeb: 19. Playwright点击发送按钮
    Note over DeepSeekWeb: 提交消息
    
    DeepSeekWeb-->>DeepSeekCrawler: 20. 返回响应页面
    Note over DeepSeekCrawler: 获取响应
    
    DeepSeekCrawler->>DeepSeekCrawler: 21. 等待响应稳定
    Note over DeepSeekCrawler: 等待2秒
    
    DeepSeekCrawler->>DeepSeekWeb: 22. Playwright读取响应内容
    Note over DeepSeekWeb: 提取文本
    
    DeepSeekWeb-->>DeepSeekCrawler: 23. 返回响应文本
    Note over DeepSeekCrawler: 获取响应
    
    DeepSeekCrawler-->>FastAPI: 24. 返回响应内容<br/>{success: true, response: "..."}
    Note over FastAPI: 获取响应
    
    FastAPI-->>DeepSeekMCP: 25. HTTP 200 OK<br/>返回响应
    Note over DeepSeekMCP: 接收HTTP响应
    
    DeepSeekMCP-->>Gemini: 26. stdio返回DeepSeek分析
    Note over Gemini: 获取架构分析
    
    Note over Gemini: 任务完成<br/>成功获取DeepSeek架构分析
```

### 关键步骤说明

1. **登录DeepSeek** (步骤1-13)
   - Gemini通过MCP工具调用登录
   - MCP工具通过HTTP调用FastAPI服务
   - FastAPI调用DeepSeek爬虫
   - 爬虫使用Playwright自动化登录
   - 登录成功后保存Cookie
   - 结果通过stdio返回给Gemini

2. **发送消息** (步骤14-26)
   - Gemini通过MCP工具发送消息
   - MCP工具通过HTTP调用FastAPI服务
   - FastAPI调用DeepSeek爬虫
   - 爬虫使用Playwright发送消息
   - 爬虫等待DeepSeek响应
   - 爬虫读取响应内容
   - 结果通过stdio返回给Gemini

---

## 场景三：GLM4.7和Gemini协作更新文档

### 时序图

```mermaid
sequenceDiagram
    autonumber
    participant GLM47 as GLM4.7<br/>Trae IDE
    participant CollabMCP as 协作文档MCP工具<br/>stdio
    participant FastAPI as FastAPI服务<br/>端口: 8000
    participant CollabService as 协作文档服务
    participant CollabDocs as 协作文档目录
    participant Gemini as Gemini 3 Pro<br/>Trae IDE
    
    Note over GLM47: GLM4.7第一次更新文档
    
    GLM47->>CollabMCP: 1. 调用get_collaboration_doc工具<br/>doc_path=daily_progress/...
    Note over CollabMCP: 接收stdio请求
    
    CollabMCP->>FastAPI: 2. HTTP GET /mcp/collaboration/doc/daily_progress/...
    Note over FastAPI: 接收HTTP请求<br/>端口8000
    
    FastAPI->>CollabService: 3. 调用get_document方法
    Note over CollabService: 读取文档
    
    CollabService->>CollabDocs: 4. 读取daily_progress_20260114.md
    Note over CollabDocs: 文件系统读取
    
    CollabDocs-->>CollabService: 5. 返回文件内容
    Note over CollabService: 获取文档内容
    
    CollabService-->>FastAPI: 6. 返回文档内容<br/>{success: true, content: "..."}
    Note over FastAPI: 获取文档
    
    FastAPI-->>CollabMCP: 7. HTTP 200 OK<br/>返回文档内容
    Note over CollabMCP: 接收HTTP响应
    
    CollabMCP-->>GLM47: 8. stdio返回文档内容
    Note over GLM47: 获取文档
    
    GLM47->>GLM47: 9. 分析文档并准备更新
    Note over GLM47: AI分析文档
    
    GLM47->>CollabMCP: 10. 调用update_collaboration_doc工具<br/>{doc_path, content, signature}
    Note over CollabMCP: 接收stdio请求<br/>signature: "[2026-01-14 10:30] @GLM4.7: 添加架构分析"
    
    CollabMCP->>FastAPI: 11. HTTP POST /mcp/collaboration/doc/update
    Note over FastAPI: 接收HTTP请求<br/>端口8000
    
    FastAPI->>CollabService: 12. 调用update_document方法
    Note over CollabService: 更新文档
    
    CollabService->>CollabDocs: 13. 备份原文件<br/>daily_progress_20260114.md.123456.bak
    Note over CollabDocs: 文件系统备份
    
    CollabDocs-->>CollabService: 14. 备份成功
    Note over CollabService: 确认备份
    
    CollabService->>CollabDocs: 15. 写入新内容<br/>daily_progress_20260114.md
    Note over CollabDocs: 文件系统写入
    
    CollabDocs-->>CollabService: 16. 写入成功
    Note over CollabService: 确认写入
    
    CollabService->>CollabService: 17. 记录新版本到数据库
    Note over CollabService: 数据库操作
    
    CollabService-->>FastAPI: 18. 返回成功<br/>{success: true, backup: ...}
    Note over FastAPI: 获取更新结果
    
    FastAPI-->>CollabMCP: 19. HTTP 200 OK<br/>返回更新结果
    Note over CollabMCP: 接收HTTP响应
    
    CollabMCP-->>GLM47: 20. stdio返回成功
    Note over GLM47: 获取更新结果
    
    Note over GLM47: GLM4.7完成第一次更新<br/>署名: @GLM4.7
    
    Note over Gemini: Gemini准备第二次更新
    
    Gemini->>CollabMCP: 21. 调用get_collaboration_doc工具<br/>doc_path=daily_progress/...
    Note over CollabMCP: 接收stdio请求
    
    CollabMCP->>FastAPI: 22. HTTP GET /mcp/collaboration/doc/daily_progress/...
    Note over FastAPI: 接收HTTP请求<br/>端口8000
    
    FastAPI->>CollabService: 23. 调用get_document方法
    Note over CollabService: 读取文档
    
    CollabService->>CollabDocs: 24. 读取daily_progress_20260114.md
    Note over CollabDocs: 文件系统读取
    
    CollabDocs-->>CollabService: 25. 返回更新后的文件内容
    Note over CollabService: 获取更新后的文档
    
    CollabService-->>FastAPI: 26. 返回文档内容
    Note over FastAPI: 获取文档
    
    FastAPI-->>CollabMCP: 27. HTTP 200 OK<br/>返回文档内容
    Note over CollabMCP: 接收HTTP响应
    
    CollabMCP-->>Gemini: 28. stdio返回更新后的文档
    Note over Gemini: 获取更新后的文档
    
    Gemini->>Gemini: 29. 审查文档内容
    Note over Gemini: AI审查文档
    
    Gemini->>CollabMCP: 30. 调用update_collaboration_doc工具<br/>{doc_path, content, signature}
    Note over CollabMCP: 接收stdio请求<br/>signature: "[2026-01-14 11:00] @Gemini: 审查并完善内容"
    
    CollabMCP->>FastAPI: 31. HTTP POST /mcp/collaboration/doc/update
    Note over FastAPI: 接收HTTP请求<br/>端口8000
    
    FastAPI->>CollabService: 32. 调用update_document方法
    Note over CollabService: 更新文档
    
    CollabService->>CollabDocs: 33. 备份原文件
    Note over CollabDocs: 文件系统备份
    
    CollabDocs-->>CollabService: 34. 备份成功
    Note over CollabService: 确认备份
    
    CollabService->>CollabDocs: 35. 写入新内容
    Note over CollabDocs: 文件系统写入
    
    CollabDocs-->>CollabService: 36. 写入成功
    Note over CollabService: 确认写入
    
    CollabService->>CollabService: 37. 记录新版本到数据库
    Note over CollabService: 数据库操作
    
    CollabService-->>FastAPI: 38. 返回成功
    Note over FastAPI: 获取更新结果
    
    FastAPI-->>CollabMCP: 39. HTTP 200 OK<br/>返回更新结果
    Note over CollabMCP: 接收HTTP响应
    
    CollabMCP-->>Gemini: 40. stdio返回成功
    Note over Gemini: 获取更新结果
    
    Note over Gemini: Gemini完成第二次更新<br/>署名: @Gemini
```

### 关键步骤说明

1. **GLM4.7第一次更新** (步骤1-20)
   - GLM4.7通过MCP工具获取文档
   - MCP工具通过HTTP调用FastAPI服务
   - FastAPI从文件系统读取文档
   - GLM4.7分析文档并准备更新
   - GLM4.7通过MCP工具更新文档
   - 服务自动备份原文件
   - 服务写入新内容
   - 服务记录新版本到数据库
   - 结果通过stdio返回给GLM4.7

2. **Gemini第二次更新** (步骤21-40)
   - Gemini通过MCP工具获取更新后的文档
   - MCP工具通过HTTP调用FastAPI服务
   - FastAPI从文件系统读取文档
   - Gemini审查文档内容
   - Gemini通过MCP工具更新文档
   - 服务自动备份原文件
   - 服务写入新内容
   - 服务记录新版本到数据库
   - 结果通过stdio返回给Gemini

---

## 场景四：完整协作流程（GLM4.7 → DeepSeek → Gemini → 文档）

### 时序图

```mermaid
sequenceDiagram
    autonumber
    participant GLM47 as GLM4.7<br/>Trae IDE
    participant DeepSeekMCP as DeepSeek MCP工具<br/>stdio
    participant FastAPI as FastAPI服务<br/>端口: 8000
    participant DeepSeekCrawler as DeepSeek爬虫
    participant CollabMCP as 协作文档MCP工具<br/>stdio
    participant Gemini as Gemini 3 Pro<br/>Trae IDE
    
    Note over GLM47: GLM4.7读取代码并获取DeepSeek分析
    
    GLM47->>DeepSeekMCP: 1. 调用read_file工具<br/>读取app/models/stock.py
    DeepSeekMCP->>FastAPI: 2. HTTP GET /file
    FastAPI-->>DeepSeekMCP: 3. 返回文件内容
    DeepSeekMCP-->>GLM47: 4. 返回代码
    
    GLM47->>GLM47: 5. 分析代码
    
    GLM47->>DeepSeekMCP: 6. 调用send_message_to_deepseek工具<br/>message: "请分析股票数据模型"
    DeepSeekMCP->>FastAPI: 7. HTTP POST /mcp/deepseek/send
    FastAPI->>DeepSeekCrawler: 8. 发送消息到DeepSeek
    DeepSeekCrawler-->>FastAPI: 9. 返回DeepSeek分析
    FastAPI-->>DeepSeekMCP: 10. 返回分析
    DeepSeekMCP-->>GLM47: 11. 返回DeepSeek分析
    
    GLM47->>GLM47: 12. 整合代码和DeepSeek分析
    
    GLM47->>CollabMCP: 13. 调用create_collaboration_doc工具<br/>doc_type=technical_review
    CollabMCP->>FastAPI: 14. HTTP POST /mcp/collaboration/doc/create
    FastAPI-->>CollabMCP: 15. 返回创建成功
    CollabMCP-->>GLM47: 16. 返回文档路径
    
    Note over GLM47: GLM4.7完成初步分析<br/>署名: @GLM4.7
    
    Note over Gemini: Gemini准备审查文档
    
    Gemini->>CollabMCP: 17. 调用get_collaboration_doc工具
    CollabMCP->>FastAPI: 18. HTTP GET /mcp/collaboration/doc/technical_review/...
    FastAPI-->>CollabMCP: 19. 返回文档内容
    CollabMCP-->>Gemini: 20. 返回文档
    
    Gemini->>Gemini: 21. 审查技术评审
    
    Gemini->>CollabMCP: 22. 调用update_collaboration_doc工具<br/>添加Gemini意见
    CollabMCP->>FastAPI: 23. HTTP POST /mcp/collaboration/doc/update
    FastAPI-->>CollabMCP: 24. 返回更新成功
    CollabMCP-->>Gemini: 25. 返回更新结果
    
    Note over Gemini: Gemini完成审查<br/>署名: @Gemini
```

### 关键步骤说明

1. **GLM4.7分析阶段** (步骤1-12)
   - GLM4.7读取项目代码
   - GLM4.7调用DeepSeek获取分析
   - GLM4.7整合代码和DeepSeek分析
   - GLM4.7创建技术评审文档

2. **Gemini审查阶段** (步骤17-25)
   - Gemini读取技术评审文档
   - Gemini审查文档内容
   - Gemini更新文档，添加自己的意见
   - 文档包含GLM4.7和Gemini的署名

---

## 通信协议对比

### stdio通信（Trae IDE ↔ MCP工具）
**特点**:
- 本地进程间通信
- 无需网络端口
- 标准输入输出流
- 支持流式传输

**优势**:
- 低延迟
- 无网络开销
- 安全性高
- 简单可靠

**使用场景**:
- Trae IDE调用MCP工具
- 工具调用结果返回
- 错误信息传递

### HTTP通信（MCP工具 ↔ 业务服务）
**特点**:
- 基于HTTP协议
- 使用8000端口
- RESTful API设计
- JSON数据格式

**优势**:
- 标准化协议
- 易于调试
- 支持跨语言
- 可扩展性强

**使用场景**:
- MCP工具调用业务服务
- 文件读写操作
- DeepSeek爬虫请求
- 数据库查询

### Playwright通信（业务服务 ↔ DeepSeek网页版）
**特点**:
- 浏览器自动化
- 模拟用户操作
- 支持JavaScript执行
- Cookie管理

**优势**:
- 真实浏览器环境
- 支持复杂交互
- 可处理动态内容
- 稳定可靠

**使用场景**:
- DeepSeek登录
- 消息发送
- 响应读取
- 会话管理

## 性能指标

### 响应时间
- **stdio调用**: < 10ms
- **HTTP调用**: < 50ms
- **DeepSeek响应**: 2-10s（取决于消息复杂度）
- **文件读写**: < 100ms
- **数据库操作**: < 50ms

### 并发能力
- **stdio并发**: 支持（每个MCP工具独立进程）
- **HTTP并发**: 支持（FastAPI异步处理）
- **DeepSeek并发**: 限制（避免被封锁）

---

*时序图最后更新: 2026-01-14*