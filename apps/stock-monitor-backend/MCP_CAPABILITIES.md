# MCP工具能力说明

## 概述

本文档详细说明DeepSeek + Trae AI模型协作系统中MCP工具提供的能力。

## 能力分类

MCP工具提供三大核心能力：

1. **读代码能力** - 读取和分析项目代码
2. **写文档能力** - 创建和管理协作文档
3. **DeepSeek交互能力** - 与DeepSeek AI进行交互

---

## 一、读代码能力

### 1.1 读取项目文件

**工具名称**: `read_file`（计划中）
**功能**: 读取项目中的任意文件内容
**输入参数**:
```json
{
  "file_path": "app/models/stock.py"
}
```
**输出结果**:
```json
{
  "success": true,
  "content": "文件内容...",
  "metadata": {
    "size": 1024,
    "modified": "2026-01-14T10:30:00Z"
  }
}
```

**使用场景**:
- GLM4.7/Gemini读取项目源代码
- 分析代码结构和实现
- 提取关键信息

**限制**:
- 只能读取项目目录内的文件
- 文件大小限制：10MB
- 支持的文件类型：.py, .ts, .js, .md, .json, .yaml

### 1.2 列出目录内容

**工具名称**: `list_directory`（计划中）
**功能**: 列出指定目录的文件和子目录
**输入参数**:
```json
{
  "directory_path": "app/models",
  "recursive": false
}
```
**输出结果**:
```json
{
  "success": true,
  "files": [
    {
      "name": "stock.py",
      "type": "file",
      "size": 1024
    },
    {
      "name": "base.py",
      "type": "file",
      "size": 512
    }
  ],
  "directories": [
    {
      "name": "repositories",
      "type": "directory"
    }
  ]
}
```

**使用场景**:
- 探索项目结构
- 查找特定文件
- 了解代码组织

### 1.3 搜索代码

**工具名称**: `search_code`（计划中）
**功能**: 在项目代码中搜索关键词
**输入参数**:
```json
{
  "keyword": "async def",
  "file_pattern": "*.py",
  "case_sensitive": false
}
```
**输出结果**:
```json
{
  "success": true,
  "matches": [
    {
      "file": "app/services/stock_service.py",
      "line": 45,
      "context": "async def get_stock_info(...)"
    }
  ]
}
```

**使用场景**:
- 查找函数定义
- 搜索特定实现
- 定位代码位置

---

## 二、写文档能力

### 2.1 创建协作文档

**工具名称**: `create_collaboration_doc`
**功能**: 创建新的协作文档
**输入参数**:
```json
{
  "doc_type": "daily_progress",
  "title": "2026-01-14 每日进度",
  "content": "今日完成了MCP系统的安装和配置工作",
  "author": "GLM4.7"
}
```

**doc_type选项**:
- `daily_progress` - 每日进度
- `weekly_report` - 周报
- `technical_review` - 技术方案评审
- `test_report` - 测试报告

**输出结果**:
```json
{
  "success": true,
  "filepath": "collaboration_docs/daily_progress/daily_progress_20260114_103000.md",
  "filename": "daily_progress_20260114_103000.md",
  "message": "文档创建成功"
}
```

**文档结构**:
```markdown
# [标题]

## 元数据
- 创建时间: YYYY-MM-DD HH:MM:SS
- 最后更新: YYYY-MM-DD HH:MM:SS
- 当前模型: GLM4.7/Gemini/DeepSeek
- 文档版本: v1.0.0
- 文档类型: daily_progress/weekly_report/technical_review/test_report

## 内容
[实际内容]

## 变更记录
- [时间] @ModelName: [变更描述]
```

**使用场景**:
- GLM4.7创建每日进度
- Gemini创建周报
- GLM4.7创建技术评审
- Gemini创建测试报告

### 2.2 更新协作文档

**工具名称**: `update_collaboration_doc`
**功能**: 更新现有协作文档
**输入参数**:
```json
{
  "doc_path": "daily_progress/daily_progress_20260114.md",
  "content": "更新后的内容",
  "signature": "[2026-01-14 11:00] @GLM4.7: 添加了架构分析",
  "author": "GLM4.7"
}
```

**署名格式**:
```
[YYYY-MM-DD HH:MM] @ModelName: [操作描述]
```

**输出结果**:
```json
{
  "success": true,
  "filepath": "collaboration_docs/daily_progress/daily_progress_20260114.md",
  "backup": "collaboration_docs/daily_progress/daily_progress_20260114.md.123456.bak",
  "message": "文档更新成功"
}
```

**自动备份**:
- 更新前自动备份原文件
- 备份文件名：`原文件名.时间戳.bak`
- 保留最近10个备份

**使用场景**:
- GLM4.7更新每日进度
- Gemini更新周报
- 多模型协作更新同一文档
- 添加DeepSeek分析到文档

### 2.3 获取协作文档

**工具名称**: `get_collaboration_doc`
**功能**: 获取协作文档内容
**输入参数**:
```json
{
  "doc_path": "daily_progress/daily_progress_20260114.md"
}
```

**输出结果**:
```json
{
  "success": true,
  "content": "# 2026-01-14 每日进度\n\n## 元数据\n...",
  "metadata": {
    "create_time": "2026-01-14 10:30:00",
    "last_update": "2026-01-14 11:00:00",
    "current_model": "GLM4.7",
    "version": "v1.0.0",
    "doc_type": "daily_progress"
  },
  "filepath": "collaboration_docs/daily_progress/daily_progress_20260114.md"
}
```

**使用场景**:
- GLM4.7读取现有文档
- Gemini读取文档进行审查
- 查看文档历史版本

### 2.4 列出协作文档

**工具名称**: `list_collaboration_docs`
**功能**: 列出所有协作文档
**输入参数**:
```json
{
  "doc_type": "daily_progress"
}
```

**doc_type选项**:
- 不指定：列出所有文档
- `daily_progress`：只列出每日进度
- `weekly_report`：只列出周报
- `technical_review`：只列出技术评审
- `test_report`：只列出测试报告

**输出结果**:
```json
{
  "success": true,
  "documents": [
    {
      "name": "daily_progress_20260114.md",
      "path": "daily_progress/daily_progress_20260114.md",
      "type": "daily_progress",
      "modified": 1705254200
    }
  ],
  "count": 1
}
```

**使用场景**:
- 查看所有协作文档
- 按类型筛选文档
- 查找最新文档

---

## 三、DeepSeek交互能力

### 3.1 登录DeepSeek

**工具名称**: `deepseek_login`
**功能**: 登录DeepSeek账号
**输入参数**:
```json
{
  "email": "your_email@example.com",
  "password": "your_password"
}
```

**输出结果**:
```json
{
  "success": true,
  "message": "登录成功"
}
```

**登录流程**:
1. Playwright打开DeepSeek网页
2. 填写邮箱和密码
3. 点击登录按钮
4. 等待登录成功
5. 保存Cookie

**使用场景**:
- GLM4.7登录DeepSeek
- Gemini登录DeepSeek
- 开始新的DeepSeek会话

**注意事项**:
- 密码不会存储在日志中
- 登录状态保存在内存中
- Cookie有效期约24小时

### 3.2 发送消息给DeepSeek

**工具名称**: `send_message_to_deepseek`
**功能**: 发送消息给DeepSeek并获取响应
**输入参数**:
```json
{
  "message": "请分析event-crawler项目的整体架构和关键模块",
  "conversation_id": "optional_conversation_id",
  "from_model": "GLM4.7"
}
```

**from_model选项**:
- `GLM4.7` - GLM4.7发起的请求
- `Gemini` - Gemini发起的请求

**输出结果**:
```json
{
  "success": true,
  "response": "根据分析，event-crawler项目采用微服务架构...",
  "conversation_id": "1705254200",
  "timestamp": "2026-01-14 10:30:00"
}
```

**响应流程**:
1. Playwright查找消息输入框
2. 输入消息内容
3. 点击发送按钮
4. 等待DeepSeek响应
5. 读取响应内容
6. 返回给调用者

**使用场景**:
- GLM4.7获取架构分析
- Gemini获取技术建议
- 询问DeepSeek问题
- 获取外部视角

**注意事项**:
- 响应时间：2-10秒
- 超时时间：60秒
- 支持长消息（最多5000字符）

### 3.3 开始新会话

**工具名称**: `start_deepseek_session`
**功能**: 开始新的DeepSeek对话会话
**输入参数**:
```json
{
  "from_model": "GLM4.7"
}
```

**输出结果**:
```json
{
  "success": true,
  "conversation_id": "1705254200",
  "message": "新会话已开始"
}
```

**会话管理**:
- 每个会话有唯一ID
- 会话内消息按时间顺序
- 支持多会话并发

**使用场景**:
- 开始新的对话主题
- 隔离不同讨论
- 清理历史会话

### 3.4 获取对话历史

**工具名称**: `get_deepseek_conversations`
**功能**: 获取DeepSeek对话历史
**输入参数**:
```json
{
  "conversation_id": "optional_conversation_id"
}
```

**输出结果**:
```json
{
  "success": true,
  "conversations": {
    "1705254200": {
      "last_message": "请分析event-crawler项目的整体架构",
      "last_response": "根据分析，event-crawler项目采用微服务架构...",
      "timestamp": "2026-01-14 10:30:00",
      "from_model": "GLM4.7"
    }
  }
}
```

**使用场景**:
- 查看对话历史
- 恢复之前的讨论
- 分析对话模式

---

## 四、协作能力

### 4.1 多模型协作

**场景**: GLM4.7和Gemini协作更新同一文档

**流程**:
1. GLM4.7读取文档
2. GLM4.7调用DeepSeek获取分析
3. GLM4.7更新文档，添加署名
4. Gemini读取更新后的文档
5. Gemini审查文档
6. Gemini更新文档，添加署名

**结果**: 文档包含两个模型的署名和意见

### 4.2 版本管理

**自动版本控制**:
- 每次更新自动备份
- 版本号自动递增
- 保留最近10个版本

**版本号格式**: `v1.0.0` → `v1.0.1` → `v1.0.2`

### 4.3 变更记录

**自动变更记录**:
- 记录每次更新的时间
- 记录更新的模型
- 记录更新的描述

**变更记录格式**:
```markdown
## 变更记录
- [2026-01-14 10:30] @GLM4.7: 创建文档
- [2026-01-14 11:00] @GLM4.7: 添加了架构分析
- [2026-01-14 14:30] @Gemini: 审查并完善内容
```

---

## 五、限制和约束

### 5.1 文件大小限制
- 单个文件最大：10MB
- 总文档大小：1GB

### 5.2 并发限制
- DeepSeek并发：最多3个
- 文档更新并发：最多5个

### 5.3 频率限制
- DeepSeek消息：每分钟最多10条
- 文档创建：每分钟最多5个
- 文档更新：每分钟最多10个

### 5.4 安全限制
- 只能访问项目目录内的文件
- 敏感信息不记录在文档中
- API密钥验证（生产环境）

---

## 六、最佳实践

### 6.1 使用MCP工具

1. **先读取后分析**
   - 读取代码和文档
   - 分析内容
   - 准备更新

2. **明确署名**
   - 每次更新都添加署名
   - 说明更新内容
   - 记录时间

3. **协作流程**
   - GLM4.7/Gemini轮流更新
   - 每次更新前读取最新版本
   - 避免冲突

### 6.2 文档管理

1. **定期备份**
   - 重要文档定期备份
   - 保留历史版本
   - 使用版本控制

2. **规范命名**
   - 使用统一的命名格式
   - 包含日期和类型
   - 便于查找

3. **清晰结构**
   - 遵循文档规范
   - 使用标准格式
   - 保持一致性

### 6.3 DeepSeek交互

1. **明确问题**
   - 问题要具体
   - 提供上下文
   - 避免模糊

2. **整合结果**
   - 结合项目实际情况
   - 批判性采纳建议
   - 记录决策原因

---

## 七、未来扩展

### 7.1 计划中的能力

1. **代码分析工具**
   - 代码质量分析
   - 依赖关系分析
   - 安全漏洞扫描

2. **高级文档功能**
   - 文档模板
   - 自动生成报告
   - 文档对比

3. **AI增强**
   - 代码自动生成
   - 智能文档摘要
   - 自动化测试

### 7.2 集成能力

1. **版本控制集成**
   - Git集成
   - 自动提交
   - 变更追踪

2. **CI/CD集成**
   - 自动测试
   - 自动部署
   - 持续集成

3. **监控集成**
   - 性能监控
   - 错误追踪
   - 使用分析

---

## 八、API参考

### 8.1 DeepSeek MCP工具API

**基础URL**: `http://localhost:8000/mcp/deepseek`

**端点**:
- `POST /login` - 登录
- `POST /send` - 发送消息
- `POST /session/new` - 开始新会话
- `GET /conversations` - 获取对话历史

### 8.2 协作文档MCP工具API

**基础URL**: `http://localhost:8000/mcp/collaboration`

**端点**:
- `POST /doc/create` - 创建文档
- `POST /doc/update` - 更新文档
- `GET /doc/{doc_path}` - 获取文档
- `GET /docs` - 列出文档

### 8.3 健康检查API

**端点**: `GET /mcp/health`

**响应**:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-14 10:30:00",
  "services": {
    "deepseek": true,
    "collaboration": true
  }
}
```

---

## 九、故障排查

### 9.1 常见问题

**问题1**: 文档创建失败
- **原因**: 目录不存在或权限不足
- **解决**: 检查目录和权限

**问题2**: DeepSeek登录失败
- **原因**: 凭证错误或网络问题
- **解决**: 检查凭证和网络

**问题3**: MCP工具无响应
- **原因**: 服务未启动或端口错误
- **解决**: 检查服务状态和端口

### 9.2 调试技巧

1. **查看日志**
   - MCP工具日志
   - FastAPI日志
   - 协作文档日志

2. **测试连接**
   - 健康检查
   - 工具调用测试
   - API端点测试

3. **检查配置**
   - 环境变量
   - MCP配置
   - 权限设置

---

## 十、总结

MCP工具提供三大核心能力：

1. **读代码能力** - 读取和分析项目代码
2. **写文档能力** - 创建和管理协作文档
3. **DeepSeek交互能力** - 与DeepSeek AI进行交互

通过这些能力，GLM4.7和Gemini可以：
- 读取项目代码和文档
- 创建和更新协作文档
- 调用DeepSeek获取外部视角
- 实现多模型协作
- 完成每日进度、周报、技术评审等任务

---

*MCP能力说明最后更新: 2026-01-14*