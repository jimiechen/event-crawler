# 安装依赖、配置MCP到Trae及使用说明 - 完成总结

## 实施完成情况

✅ **所有任务已成功完成！**

## 已完成的工作

### 1. 更新Python依赖 ✅
- [x] 更新 `requirements.txt`
  - 添加 `playwright>=1.40.0`
  - 添加 `jinja2>=3.1.2`
  - 添加 `markdown>=3.5.0`

### 2. 创建MCP配置说明文档 ✅
- [x] `MCP_CONFIG_GUIDE.md` - 详细的配置说明
  - 所有配置项的详细说明
  - 常见配置问题和解决方案
  - 安全建议和配置示例

### 3. 创建Trae MCP配置文件 ✅
- [x] `.trae/mcp-config.json` - Trae MCP配置
  - DeepSeek MCP服务器配置
  - 协作文档MCP服务器配置
  - 允许的模型列表
  - API基础URL配置

### 4. 创建安装和启动脚本 ✅
- [x] `scripts/install_mcp.sh` - 自动化安装脚本
  - [x] `scripts/start_mcp.sh` - 启动脚本
  - [x] `scripts/stop_mcp.sh` - 停止脚本
  - 所有脚本已添加执行权限

### 5. 创建使用说明文档 ✅
- [x] `MCP_QUICKSTART.md` - 快速开始指南
  - [x] `MCP_USAGE_EXAMPLES.md` - 详细使用示例
  - 包含5个典型使用场景
  - 完整的步骤说明

### 6. 创建测试脚本和用例 ✅
- [x] `scripts/test_mcp.sh` - Shell测试脚本
- [x] `tests/test_mcp_integration.py` - Python集成测试用例
  - 包含10个测试用例
  - 覆盖所有主要功能

## 创建的文件清单

### Python相关（5个文件）
1. `requirements.txt` - 更新添加MCP依赖
2. `MCP_CONFIG_GUIDE.md` - 配置说明文档
3. `MCP_QUICKSTART.md` - 快速开始指南
4. `MCP_USAGE_EXAMPLES.md` - 使用示例文档
5. `tests/test_mcp_integration.py` - 集成测试用例

### Trae配置（1个文件）
1. `.trae/mcp-config.json` - Trae MCP配置文件

### Shell脚本（3个文件）
1. `scripts/install_mcp.sh` - 安装脚本（可执行）
2. `scripts/start_mcp.sh` - 启动脚本（可执行）
3. `scripts/stop_mcp.sh` - 停止脚本（可执行）
4. `scripts/test_mcp.sh` - 测试脚本（可执行）

## 快速开始

### 方式一：自动化安装（推荐）

```bash
# 进入项目目录
cd /Users/mac/StudioProjects/open-citycloud/projects/event-crawler

# 运行安装脚本
bash scripts/install_mcp.sh
```

### 方式二：手动安装

#### 1. 安装Python依赖

```bash
cd apps/stock-monitor-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

#### 2. 配置环境变量

```bash
cd apps/stock-monitor-backend
cp .env.mcp.example .env
# 编辑.env文件，填入DeepSeek登录信息
```

#### 3. 初始化数据库

```bash
cd apps/stock-monitor-backend
python3 -c "
from app.database import engine
from app.models.collaboration_log import Base
import asyncio

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('数据库初始化完成')

asyncio.run(init_db())
"
```

#### 4. 安装TypeScript MCP工具

```bash
cd mcp-tools/deepseek-mcp
npm install
npm run build

cd ../../collaboration-tools
npm install
npm run build
```

### 启动服务

#### 方式一：自动化启动（推荐）

```bash
cd /Users/mac/StudioProjects/open-citycloud/projects/event-crawler
bash scripts/start_mcp.sh
```

#### 方式二：手动启动

```bash
# 启动MCP API服务
cd apps/stock-monitor-backend
source venv/bin/activate
python3 main_mcp.py

# 启动DeepSeek MCP工具（新终端）
cd mcp-tools/deepseek-mcp
npm run start

# 启动协作文档MCP工具（新终端）
cd mcp-tools/collaboration-tools
npm run start
```

## Trae IDE配置

### 1. 配置MCP服务器

在Trae IDE中添加以下MCP服务器配置：

```json
{
  "mcpServers": [
    {
      "name": "deepseek-mcp",
      "command": "node",
      "args": [
        "/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/mcp-tools/deepseek-mcp/dist/mcp-server.js"
      ],
      "env": {
        "MCP_API_URL": "http://localhost:8000"
      }
    },
    {
      "name": "collaboration-tools",
      "command": "node",
      "args": [
        "/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/mcp-tools/collaboration-tools/dist/mcp-server.js"
      ],
      "env": {
        "MCP_API_URL": "http://localhost:8000"
      }
    }
  ]
}
```

### 2. 验证MCP连接

在Trae IDE中：
1. 打开MCP工具面板
2. 查看已连接的MCP服务器
3. 测试工具调用

## 使用示例

### 示例1：创建每日进度文档

在Trae IDE中使用GLM4.7：

1. 调用MCP工具 `create_collaboration_doc`
2. 输入参数：
   ```json
   {
     "doc_type": "daily_progress",
     "title": "2026-01-14 每日进度",
     "content": "今日完成了MCP系统的安装和配置工作",
     "author": "GLM4.7"
   }
   ```
3. 查看返回结果

### 示例2：调用DeepSeek获取分析

在Trae IDE中使用GLM4.7：

1. 调用MCP工具 `deepseek_login`
2. 输入DeepSeek账号和密码
3. 查看登录结果

4. 调用MCP工具 `send_message_to_deepseek`
5. 输入消息：`请分析event-crawler项目的整体架构和关键模块`
6. 查看DeepSeek的响应

## 测试验证

### 运行测试脚本

```bash
cd /Users/mac/StudioProjects/open-citycloud/projects/event-crawler
bash scripts/test_mcp.sh
```

测试脚本会执行以下测试：
1. 检查Python依赖
2. 检查数据库模型
3. 检查MCP配置
4. 检查协作文档目录
5. 检查MCP工具文件
6. 检查TypeScript编译
7. 测试MCP API健康检查
8. 测试DeepSeek登录（需要配置）
9. 测试创建协作文档
10. 测试列出协作文档

### 运行Python测试用例

```bash
cd apps/stock-monitor-backend
source venv/bin/activate
pytest tests/test_mcp_integration.py -v
```

## 文档资源

### 配置文档
- [MCP_CONFIG_GUIDE.md](apps/stock-monitor-backend/MCP_CONFIG_GUIDE.md) - 详细的配置说明
- [.env.mcp.example](apps/stock-monitor-backend/.env.mcp.example) - 配置示例文件

### 使用文档
- [MCP_QUICKSTART.md](apps/stock-monitor-backend/MCP_QUICKSTART.md) - 快速开始指南
- [MCP_USAGE_EXAMPLES.md](apps/stock-monitor-backend/MCP_USAGE_EXAMPLES.md) - 详细使用示例
- [README_MCP.md](apps/stock-monitor-backend/README_MCP.md) - 系统README
- [IMPLEMENTATION_SUMMARY.md](apps/stock-monitor-backend/IMPLEMENTATION_SUMMARY.md) - 实施总结

### 文档规范
- [standards.md](apps/stock-monitor-backend/collaboration_docs/standards.md) - 文档规范

## 故障排查

### 常见问题

#### 问题1：安装脚本失败

**解决方案**：
1. 检查Python和Node.js版本
2. 确保有网络连接
3. 查看错误日志

#### 问题2：MCP API服务启动失败

**解决方案**：
1. 检查端口8000是否被占用
2. 检查.env配置文件
3. 查看日志文件 `mcp_collaboration.log`

#### 问题3：DeepSeek登录失败

**解决方案**：
1. 检查邮箱和密码是否正确
2. 确保账号可以正常登录DeepSeek网页版
3. 检查网络连接

#### 问题4：MCP工具无法连接

**解决方案**：
1. 确认MCP API服务已启动
2. 检查MCP_API_URL配置
3. 查看MCP工具日志

## 下一步

安装和配置完成后，你可以：

1. **查看使用示例**：了解5个典型使用场景
2. **运行测试**：验证系统功能正常
3. **开始使用**：在Trae IDE中使用MCP工具
4. **查看文档**：了解更多功能和使用方法

## 技术支持

如果遇到问题，请查看：
- [MCP_CONFIG_GUIDE.md](apps/stock-monitor-backend/MCP_CONFIG_GUIDE.md) - 配置说明
- [MCP_QUICKSTART.md](apps/stock-monitor-backend/MCP_QUICKSTART.md) - 快速开始
- [MCP_USAGE_EXAMPLES.md](apps/stock-monitor-backend/MCP_USAGE_EXAMPLES.md) - 使用示例

## 总结

✅ **Python依赖已更新**
✅ **MCP配置说明已完善**
✅ **Trae MCP配置已创建**
✅ **安装和启动脚本已就绪**
✅ **使用说明文档已完成**
✅ **测试脚本和用例已创建**

系统已经完全配置好，可以开始使用DeepSeek + Trae AI模型协作系统！

---

*完成时间: 2026-01-14*