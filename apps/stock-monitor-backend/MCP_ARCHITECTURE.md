# MCP系统架构流程图

## 系统概述

DeepSeek + Trae AI模型协作系统采用分层架构，各组件通过不同的通信协议进行交互。

## 整体架构图

```mermaid
graph TB
    subgraph "Trae IDE环境"
        GLM47[GLM4.7]
        Gemini[Gemini 3 Pro]
    end
    
    subgraph "MCP工具层"
        DeepSeekMCP[DeepSeek MCP工具<br/>stdio通信]
        CollabMCP[协作文档MCP工具<br/>stdio通信]
    end
    
    subgraph "业务服务层"
        FastAPI[FastAPI服务<br/>端口: 8000]
        DeepSeekCrawler[DeepSeek爬虫<br/>Playwright]
        CollabService[协作文档服务]
        Database[(数据库)]
    end
    
    subgraph "外部服务"
        DeepSeekWeb[DeepSeek网页版]
    end
    
    subgraph "文件系统"
        ProjectFiles[项目代码文件]
        CollabDocs[协作文档目录]
    end
    
    GLM47 -->|stdio| DeepSeekMCP
    Gemini -->|stdio| CollabMCP
    
    DeepSeekMCP -->|HTTP: 8000| FastAPI
    CollabMCP -->|HTTP: 8000| FastAPI
    
    FastAPI --> DeepSeekCrawler
    FastAPI --> CollabService
    FastAPI --> Database
    
    DeepSeekCrawler -->|Playwright| DeepSeekWeb
    
    CollabService --> CollabDocs
    DeepSeekMCP --> ProjectFiles
    CollabMCP --> CollabDocs
```

## 组件说明

### 1. Trae IDE环境
**组件**: GLM4.7、Gemini 3 Pro
**职责**:
- 作为AI助手运行在Trae IDE中
- 通过MCP协议调用工具
- 读取项目代码和文档
- 生成协作文档

**通信方式**: stdio（标准输入输出）

### 2. MCP工具层
**组件**: 
- DeepSeek MCP工具（TypeScript）
- 协作文档MCP工具（TypeScript）

**职责**:
- 实现MCP协议
- 提供工具定义
- 处理Trae IDE的调用请求
- 转换为HTTP请求调用业务服务

**通信方式**: 
- 与Trae IDE: stdio
- 与业务服务: HTTP（8000端口）

### 3. 业务服务层
**组件**: 
- FastAPI服务（端口8000）
- DeepSeek爬虫（Playwright）
- 协作文档服务
- 数据库

**职责**:
- 提供HTTP API接口
- 处理DeepSeek爬虫请求
- 管理协作文档
- 存储协作日志和版本

**通信方式**: HTTP（8000端口）

### 4. 外部服务
**组件**: DeepSeek网页版
**职责**:
- 提供AI对话服务
- 响应爬虫的请求

**通信方式**: HTTPS

### 5. 文件系统
**组件**: 
- 项目代码文件
- 协作文档目录

**职责**:
- 存储项目源代码
- 存储协作文档
- 支持版本管理

## 数据流向

### 场景1: GLM4.7读取代码并创建文档

```mermaid
sequenceDiagram
    participant GLM47 as GLM4.7
    participant DeepSeekMCP as DeepSeek MCP工具
    participant FastAPI as FastAPI服务<br/>8000端口
    participant CollabService as 协作文档服务
    participant CollabDocs as 协作文档目录
    
    GLM47->>DeepSeekMCP: 1. 调用read_file工具
    DeepSeekMCP->>FastAPI: 2. HTTP GET /file
    FastAPI->>CollabDocs: 3. 读取文件
    CollabDocs-->>FastAPI: 4. 返回文件内容
    FastAPI-->>DeepSeekMCP: 5. 返回文件内容
    DeepSeekMCP-->>GLM47: 6. 返回代码内容
    
    GLM47->>GLM47: 7. 分析代码
    GLM47->>DeepSeekMCP: 8. 调用create_doc工具
    DeepSeekMCP->>FastAPI: 9. HTTP POST /collaboration/doc/create
    FastAPI->>CollabService: 10. 创建文档
    CollabService->>CollabDocs: 11. 写入Markdown文件
    CollabDocs-->>CollabService: 12. 文件创建成功
    CollabService-->>FastAPI: 13. 返回成功
    FastAPI-->>DeepSeekMCP: 14. 返回成功
    DeepSeekMCP-->>GLM47: 15. 返回文档路径
```

### 场景2: Gemini调用DeepSeek获取分析

```mermaid
sequenceDiagram
    participant Gemini as Gemini 3 Pro
    participant DeepSeekMCP as DeepSeek MCP工具
    participant FastAPI as FastAPI服务<br/>8000端口
    participant DeepSeekCrawler as DeepSeek爬虫
    participant DeepSeekWeb as DeepSeek网页版
    
    Gemini->>DeepSeekMCP: 1. 调用deepseek_login工具
    DeepSeekMCP->>FastAPI: 2. HTTP POST /deepseek/login
    FastAPI->>DeepSeekCrawler: 3. 启动爬虫
    DeepSeekCrawler->>DeepSeekWeb: 4. Playwright登录
    DeepSeekWeb-->>DeepSeekCrawler: 5. 登录成功
    DeepSeekCrawler-->>FastAPI: 6. 返回登录结果
    FastAPI-->>DeepSeekMCP: 7. 返回成功
    DeepSeekMCP-->>Gemini: 8. 登录成功
    
    Gemini->>DeepSeekMCP: 9. 调用send_message工具
    DeepSeekMCP->>FastAPI: 10. HTTP POST /deepseek/send
    FastAPI->>DeepSeekCrawler: 11. 发送消息
    DeepSeekCrawler->>DeepSeekWeb: 12. Playwright发送消息
    DeepSeekWeb-->>DeepSeekCrawler: 13. 返回响应
    DeepSeekCrawler-->>FastAPI: 14. 返回响应内容
    FastAPI-->>DeepSeekMCP: 15. 返回响应
    DeepSeekMCP-->>Gemini: 16. 返回DeepSeek分析
```

### 场景3: GLM4.7和Gemini协作更新文档

```mermaid
sequenceDiagram
    participant GLM47 as GLM4.7
    participant CollabMCP as 协作文档MCP工具
    participant FastAPI as FastAPI服务<br/>8000端口
    participant CollabService as 协作文档服务
    participant CollabDocs as 协作文档目录
    participant DeepSeekMCP as DeepSeek MCP工具
    
    GLM47->>CollabMCP: 1. 调用get_doc工具
    CollabMCP->>FastAPI: 2. HTTP GET /collaboration/doc
    FastAPI->>CollabService: 3. 读取文档
    CollabService->>CollabDocs: 4. 读取Markdown文件
    CollabDocs-->>CollabService: 5. 返回文档内容
    CollabService-->>FastAPI: 6. 返回文档
    FastAPI-->>CollabMCP: 7. 返回文档
    CollabMCP-->>GLM47: 8. 返回文档内容
    
    GLM47->>GLM47: 9. 分析文档
    GLM47->>DeepSeekMCP: 10. 调用send_message工具
    DeepSeekMCP-->>GLM47: 11. 返回DeepSeek建议
    
    GLM47->>GLM47: 12. 整合建议
    GLM47->>CollabMCP: 13. 调用update_doc工具
    CollabMCP->>FastAPI: 14. HTTP POST /collaboration/doc/update
    FastAPI->>CollabService: 15. 更新文档
    CollabService->>CollabDocs: 16. 写入Markdown文件
    CollabDocs-->>CollabService: 17. 更新成功
    CollabService-->>FastAPI: 18. 返回成功
    FastAPI-->>CollabMCP: 19. 返回成功
    CollabMCP-->>GLM47: 20. 返回更新结果
    
    Note over GLM47: GLM4.7完成第一次更新<br/>署名: @GLM4.7
    
    Gemini->>CollabMCP: 21. 调用get_doc工具
    CollabMCP-->>Gemini: 22. 返回更新后的文档
    
    Gemini->>Gemini: 23. 审查文档
    Gemini->>CollabMCP: 24. 调用update_doc工具
    CollabMCP-->>Gemini: 25. 返回更新结果
    
    Note over Gemini: Gemini完成第二次更新<br/>署名: @Gemini
```

## 端口说明

### 8000端口 - 业务服务端口
**用途**: FastAPI服务监听端口
**通信协议**: HTTP
**服务对象**: MCP工具层
**功能**:
- 提供DeepSeek爬虫API
- 提供协作文档管理API
- 提供协作日志查询API

**示例请求**:
```bash
# DeepSeek登录
POST http://localhost:8000/mcp/deepseek/login

# 创建协作文档
POST http://localhost:8000/mcp/collaboration/doc/create

# 更新协作文档
POST http://localhost:8000/mcp/collaboration/doc/update
```

### stdio通信 - MCP协议
**用途**: Trae IDE与MCP工具之间的通信
**通信协议**: stdio（标准输入输出）
**服务对象**: Trae IDE
**功能**:
- 工具调用
- 结果返回
- 错误处理

**特点**:
- 不需要网络端口
- 通过标准输入输出通信
- 支持流式传输

## MCP工具能力

### DeepSeek MCP工具能力
1. **deepseek_login** - 登录DeepSeek
2. **send_message_to_deepseek** - 发送消息给DeepSeek
3. **start_deepseek_session** - 开始新会话
4. **get_deepseek_conversations** - 获取对话历史

### 协作文档MCP工具能力
1. **create_collaboration_doc** - 创建协作文档
2. **update_collaboration_doc** - 更新协作文档
3. **get_collaboration_doc** - 获取协作文档
4. **list_collaboration_docs** - 列出协作文档

## 部署架构

### 开发环境
```
Trae IDE (本地)
    ↓ stdio
MCP工具 (本地进程)
    ↓ HTTP: 8000
FastAPI服务 (本地进程)
    ↓ Playwright
DeepSeek网页版 (远程)
    ↓
协作文档 (本地文件系统)
```

### 生产环境
```
Trae IDE (本地)
    ↓ stdio
MCP工具 (本地进程)
    ↓ HTTP: 8000
FastAPI服务 (Docker容器)
    ↓ Playwright
DeepSeek网页版 (远程)
    ↓
协作文档 (持久化存储)
```

## 安全考虑

### 1. API安全
- 使用API密钥保护8000端口
- 限制允许的模型列表
- 实施请求限流

### 2. 数据安全
- 敏感信息不存储在文档中
- 使用环境变量管理凭证
- 定期备份协作文档

### 3. 通信安全
- MCP工具与Trae IDE: 本地stdio通信
- MCP工具与业务服务: 本地HTTP通信
- DeepSeek爬虫: HTTPS加密通信

## 性能优化

### 1. 缓存策略
- 协作文档缓存
- DeepSeek响应缓存
- 代码文件缓存

### 2. 异步处理
- FastAPI异步请求处理
- DeepSeek爬虫异步操作
- 数据库异步查询

### 3. 负载均衡
- 多个MCP工具实例
- 数据库连接池
- 请求队列管理

---

*架构流程图最后更新: 2026-01-14*