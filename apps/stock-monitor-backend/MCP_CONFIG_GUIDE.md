# MCP配置说明

## 概述

本文档详细说明如何配置DeepSeek + Trae AI模型协作系统的MCP服务。

## 配置文件

### 1. 环境变量配置 (.env)

在项目根目录下创建或编辑 `.env` 文件，添加以下配置：

```bash
# ============================================================================
# DeepSeek配置
# ============================================================================
DEEPSEEK_EMAIL=your_email@example.com
DEEPSEEK_PASSWORD=your_password_here

# ============================================================================
# API配置
# ============================================================================
MCP_API_HOST=0.0.0.0
MCP_API_PORT=8000
MCP_API_KEY=your_secret_key_here

# ============================================================================
# 文档配置
# ============================================================================
COLLABORATION_DIR=collaboration_docs

# ============================================================================
# 模型配置
# ============================================================================
ALLOWED_MODELS=GLM4.7,Gemini,DeepSeek

# ============================================================================
# MCP工具配置
# ============================================================================
MCP_DEEPSEEK_ENABLED=true
MCP_COLLABORATION_ENABLED=true
MCP_CODE_ANALYSIS_ENABLED=true

# ============================================================================
# 数据库配置
# ============================================================================
# SQLite（默认）
DATABASE_URL=sqlite:///./collaboration.db

# MySQL（可选）
# DATABASE_URL=mysql+pymysql://user:password@localhost:3306/collaboration

# PostgreSQL（可选）
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/collaboration

# ============================================================================
# 日志配置
# ============================================================================
LOG_LEVEL=INFO
LOG_FILE=mcp_collaboration.log

# ============================================================================
# 超时配置
# ============================================================================
REQUEST_TIMEOUT=120
RESPONSE_TIMEOUT=60

# ============================================================================
# 备份配置
# ============================================================================
BACKUP_COUNT=10
BACKUP_RETENTION_DAYS=30
```

## 配置项详细说明

### DeepSeek配置

| 配置项 | 说明 | 必填 | 示例 |
|--------|------|--------|------|
| `DEEPSEEK_EMAIL` | DeepSeek账号邮箱 | 是 | `your_email@example.com` |
| `DEEPSEEK_PASSWORD` | DeepSeek账号密码 | 是 | `your_password_here` |

**注意事项**：
- 请使用真实的DeepSeek账号
- 确保账号可以正常登录
- 不要在代码中硬编码密码

### API配置

| 配置项 | 说明 | 必填 | 默认值 |
|--------|------|--------|--------|
| `MCP_API_HOST` | API服务监听地址 | 否 | `0.0.0.0` |
| `MCP_API_PORT` | API服务监听端口 | 否 | `8000` |
| `MCP_API_KEY` | API密钥（生产环境建议设置） | 否 | - |

**注意事项**：
- 开发环境可以使用默认值
- 生产环境建议设置API密钥
- 确保端口没有被占用

### 文档配置

| 配置项 | 说明 | 必填 | 默认值 |
|--------|------|--------|--------|
| `COLLABORATION_DIR` | 协作文档存储目录 | 否 | `collaboration_docs` |

**注意事项**：
- 目录会自动创建
- 确保有写入权限
- 建议使用相对路径

### 模型配置

| 配置项 | 说明 | 必填 | 默认值 |
|--------|------|--------|--------|
| `ALLOWED_MODELS` | 允许使用的模型列表 | 否 | `GLM4.7,Gemini,DeepSeek` |

**注意事项**：
- 模型名称用逗号分隔
- 必须包含 `GLM4.7` 或 `Gemini`
- `DeepSeek` 可选

### MCP工具配置

| 配置项 | 说明 | 必填 | 默认值 |
|--------|------|--------|--------|
| `MCP_DEEPSEEK_ENABLED` | 是否启用DeepSeek工具 | 否 | `true` |
| `MCP_COLLABORATION_ENABLED` | 是否启用协作文档工具 | 否 | `true` |
| `MCP_CODE_ANALYSIS_ENABLED` | 是否启用代码分析工具 | 否 | `true` |

**注意事项**：
- 使用 `true` 或 `false`（小写）
- 禁用工具后相关API将不可用

### 数据库配置

| 配置项 | 说明 | 必填 | 默认值 |
|--------|------|--------|--------|
| `DATABASE_URL` | 数据库连接URL | 否 | `sqlite:///./collaboration.db` |

**注意事项**：
- SQLite适合开发和测试
- 生产环境建议使用MySQL或PostgreSQL
- 确保数据库服务已启动

### 日志配置

| 配置项 | 说明 | 必填 | 默认值 |
|--------|------|--------|--------|
| `LOG_LEVEL` | 日志级别 | 否 | `INFO` |
| `LOG_FILE` | 日志文件路径 | 否 | `mcp_collaboration.log` |

**注意事项**：
- 日志级别：`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- 日志文件会自动创建
- 确保有写入权限

### 超时配置

| 配置项 | 说明 | 必填 | 默认值 |
|--------|------|--------|--------|
| `REQUEST_TIMEOUT` | 请求超时时间（秒） | 否 | `120` |
| `RESPONSE_TIMEOUT` | 响应超时时间（秒） | 否 | `60` |

**注意事项**：
- 单位为秒
- 根据网络情况调整
- 超时时间不宜过短

### 备份配置

| 配置项 | 说明 | 必填 | 默认值 |
|--------|------|--------|--------|
| `BACKUP_COUNT` | 保留的备份数量 | 否 | `10` |
| `BACKUP_RETENTION_DAYS` | 备份保留天数 | 否 | `30` |

**注意事项**：
- 超过限制的备份会被自动删除
- 根据磁盘空间调整
- 建议定期清理旧备份

## 配置验证

### 自动验证

启动MCP服务时会自动验证配置：

```bash
python main_mcp.py
```

系统会输出：
- ✅ 配置验证通过（所有配置正常）
- ⚠️ 配置警告（有非关键配置缺失）
- ❌ 配置错误（有关键配置缺失）

### 手动验证

使用Python脚本验证配置：

```python
from config.mcp_config import MCPConfig

# 验证配置
MCPConfig.validate()

# 检查DeepSeek凭证
credentials = MCPConfig.get_deepseek_credentials()
print(f"DeepSeek邮箱: {credentials['email']}")

# 检查模型列表
print(f"允许的模型: {MCPConfig.ALLOWED_MODELS}")

# 检查数据库URL
print(f"数据库URL: {MCPConfig.get_database_url()}")
```

## 常见配置问题

### 问题1: DeepSeek登录失败

**原因**：
- 邮箱或密码错误
- 账号被锁定
- 网络连接问题

**解决方案**：
1. 检查 `.env` 文件中的 `DEEPSEEK_EMAIL` 和 `DEEPSEEK_PASSWORD`
2. 确保账号可以正常登录DeepSeek网页版
3. 检查网络连接
4. 查看日志文件 `mcp_collaboration.log` 获取详细错误信息

### 问题2: API端口被占用

**原因**：
- 端口8000已被其他服务占用

**解决方案**：
1. 修改 `.env` 文件中的 `MCP_API_PORT` 为其他端口（如8001）
2. 或者停止占用8000端口的服务
3. 使用命令检查端口占用：
   ```bash
   # macOS/Linux
   lsof -i :8000
   
   # Windows
   netstat -ano | findstr :8000
   ```

### 问题3: 数据库连接失败

**原因**：
- 数据库服务未启动
- 连接URL配置错误
- 数据库权限不足

**解决方案**：
1. 检查数据库服务是否启动
2. 验证 `DATABASE_URL` 配置是否正确
3. 确保数据库用户有足够权限
4. 对于SQLite，确保有文件写入权限

### 问题4: 日志文件无法创建

**原因**：
- 目录不存在
- 没有写入权限
- 磁盘空间不足

**解决方案**：
1. 检查目录是否存在，如不存在会自动创建
2. 确保有目录的写入权限
3. 检查磁盘空间是否充足

## 安全建议

### 1. 保护敏感信息

- 不要将 `.env` 文件提交到版本控制
- 使用 `.env.example` 作为模板
- 定期更换密码和密钥

### 2. 使用环境变量

- 所有敏感信息通过环境变量配置
- 不要在代码中硬编码
- 使用密钥管理服务（生产环境）

### 3. 限制访问

- 设置 `MCP_API_KEY` 保护API
- 使用防火墙限制访问
- 定期审计访问日志

## 配置示例

### 开发环境配置

```bash
# DeepSeek配置
DEEPSEEK_EMAIL=dev@example.com
DEEPSEEK_PASSWORD=dev_password

# API配置
MCP_API_HOST=127.0.0.1
MCP_API_PORT=8000

# 数据库配置
DATABASE_URL=sqlite:///./collaboration_dev.db

# 日志配置
LOG_LEVEL=DEBUG
LOG_FILE=mcp_collaboration_dev.log
```

### 生产环境配置

```bash
# DeepSeek配置
DEEPSEEK_EMAIL=prod@example.com
DEEPSEEK_PASSWORD=strong_password_here

# API配置
MCP_API_HOST=0.0.0.0
MCP_API_PORT=8000
MCP_API_KEY=strong_api_key_here

# 数据库配置
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/collaboration

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/var/log/mcp_collaboration.log
```

## 配置更新

### 更新配置后重启服务

修改 `.env` 文件后，需要重启MCP服务：

```bash
# 停止服务（Ctrl+C）
# 重新启动
python main_mcp.py
```

### 热重载配置（开发环境）

开发环境可以使用热重载：

```bash
# 使用uvicorn的reload功能
uvicorn main_mcp:app --reload
```

## 配置备份

### 备份配置文件

```bash
# 备份当前配置
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
```

### 恢复配置

```bash
# 恢复备份配置
cp .env.backup.20260114_100000 .env
```

---

*配置说明文档最后更新: 2026-01-14*