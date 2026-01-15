# MCP使用示例

## 概述

本文档提供DeepSeek + Trae AI模型协作系统的详细使用示例。

## 场景一：了解项目和代码情况

### 场景描述

GLM4.7需要了解event-crawler项目的整体架构和关键模块，通过DeepSeek获取外部视角的分析。

### 使用步骤

#### 步骤1：读取项目结构

在Trae IDE中，GLM4.7读取项目目录结构和关键文件：

```python
# 读取项目结构
import os
from pathlib import Path

project_root = Path("/Users/mac/StudioProjects/open-citycloud/projects/event-crawler")

# 获取主要目录
main_dirs = [d for d in project_root.iterdir() if d.is_dir()]

# 获取关键文件
key_files = list(project_root.glob("*.md")) + list(project_root.glob("*.json"))

print("项目目录结构:")
for d in main_dirs:
    print(f"  - {d.name}")

print("\n关键文件:")
for f in key_files:
    print(f"  - {f.name}")
```

#### 步骤2：调用DeepSeek获取架构分析

在Trae IDE中，GLM4.7调用MCP工具 `send_message_to_deepseek`：

```json
{
  "message": "请分析event-crawler项目的整体架构和关键模块，重点关注：\n1. 项目的主要功能\n2. 技术栈和架构\n3. 关键模块和它们的职责\n4. 数据流和交互方式\n5. 潜在的优化点",
  "from_model": "GLM4.7"
}
```

#### 步骤3：整合DeepSeek的建议

GLM4.7读取DeepSeek的响应，结合实际代码，生成详细的项目分析文档：

```python
# 整合DeepSeek建议和项目实际情况
deepseek_analysis = """
DeepSeek分析结果：
1. 项目采用微服务架构，包含多个独立的应用
2. 技术栈包括Python、TypeScript、Vue.js、FastAPI等
3. 关键模块包括爬虫、数据监控、AI决策等
4. 数据流通过API和消息队列进行交互
5. 建议优化点：缓存机制、异步处理、错误重试
"""

# 结合实际代码
code_analysis = """
实际代码分析：
- 爬虫模块：使用Playwright实现，支持Cookie管理
- 数据监控：基于FastAPI，提供RESTful API
- AI决策：集成多个AI模型，支持智能决策
"""

# 生成项目分析文档
project_analysis = f"""
# event-crawler项目架构分析

## 项目概述
{deepseek_analysis}

## 实际代码分析
{code_analysis}

## 架构建议
1. 引入缓存层（Redis）提升性能
2. 优化数据库查询，添加索引
3. 实现消息队列（如RabbitMQ）解耦服务
4. 添加监控和告警系统
5. 完善错误处理和日志记录
"""

# 调用MCP工具创建文档
{
  "doc_type": "technical_review",
  "title": "event-crawler项目架构分析",
  "content": project_analysis,
  "author": "GLM4.7"
}
```

#### 步骤4：更新文档并署名

```python
# 更新文档并添加署名
{
  "doc_path": "technical_review/technical_review_20260114.md",
  "content": project_analysis,
  "signature": "[2026-01-14 10:30] @GLM4.7: 整合DeepSeek架构分析和实际代码，生成项目分析文档",
  "author": "GLM4.7"
}
```

### 预期结果

生成一份完整的项目架构分析文档，包含：
- DeepSeek的外部视角分析
- 实际代码的详细分析
- 架构优化建议
- 清晰的署名和变更记录

---

## 场景二：技术方案评审

### 场景描述

Gemini需要评审一个技术方案，通过DeepSeek获取专业的评审意见。

### 使用步骤

#### 步骤1：读取技术方案文档

```python
# 读取技术方案
from pathlib import Path

doc_path = Path("collaboration_docs/technical_review/proposal.md")
with open(doc_path, 'r', encoding='utf-8') as f:
    proposal = f.read()

print("技术方案内容:")
print(proposal)
```

#### 步骤2：调用DeepSeek获取评审意见

```json
{
  "message": f"请评审以下技术方案，从以下角度进行分析：\n\n1. 技术可行性\n2. 架构合理性\n3. 性能和扩展性\n4. 安全性考虑\n5. 实施难度和风险\n\n方案内容：\n{proposal}",
  "from_model": "Gemini"
}
```

#### 步骤3：整合评审意见

```python
# 整合DeepSeek评审意见和项目实际情况
deepseek_review = """
DeepSeek评审意见：
1. 技术可行性：方案可行，但需要考虑兼容性
2. 架构合理性：架构清晰，建议添加服务发现机制
3. 性能和扩展性：需要优化数据库查询和缓存策略
4. 安全性：建议添加认证和授权机制
5. 实施难度：中等，建议分阶段实施
"""

# 结合项目实际情况
project_context = """
项目实际情况：
- 现有系统使用FastAPI和SQLAlchemy
- 已有用户认证和权限管理
- 数据库已建立索引
- 已有日志和监控系统
"""

# 生成评审文档
review_doc = f"""
# 技术方案评审

## 原始方案
{proposal}

## DeepSeek评审意见
{deepseek_review}

## 项目实际情况
{project_context}

## 评审结论
1. 技术可行性：✅ 可行，需注意兼容性
2. 架构合理性：✅ 合理，建议添加服务发现
3. 性能和扩展性：⚠️ 需要优化
4. 安全性：✅ 已有基础，需完善
5. 实施难度：⚠️ 中等，建议分阶段

## 改进建议
1. 添加服务发现机制（如Consul）
2. 优化数据库查询，添加更多索引
3. 实施缓存策略（Redis）
4. 完善API文档和测试
5. 分阶段实施，降低风险
"""

# 更新文档
{
  "doc_path": "technical_review/proposal_review.md",
  "content": review_doc,
  "signature": "[2026-01-14 11:15] @Gemini: 整合DeepSeek评审意见和项目实际情况",
  "author": "Gemini"
}
```

---

## 场景三：每日进度汇报

### 场景描述

GLM4.7需要生成每日进度报告，通过DeepSeek帮助整理工作内容。

### 使用步骤

#### 步骤1：收集今日工作内容

```python
# 收集今日完成的任务
today_tasks = [
    "完成MCP系统的安装和配置",
    "创建协作文档管理服务",
    "实现DeepSeek爬虫功能",
    "编写MCP工具定义",
    "创建安装和启动脚本"
]

# 收集代码变更
code_changes = """
新增文件：
- app/crawler/deepseek_crawler.py
- app/services/deepseek_mcp_service.py
- app/services/collaboration_service.py
- app/api/mcp_controller.py
- app/models/collaboration_log.py
- config/mcp_config.py
- main_mcp.py

修改文件：
- requirements.txt（添加MCP依赖）
"""

# 收集遇到的问题
issues = """
1. Playwright浏览器安装时间较长
2. MCP工具配置需要手动调整
3. 数据库初始化需要异步支持
"""
```

#### 步骤2：调用DeepSeek整理日报

```json
{
  "message": f"请帮我整理成每日进度报告，今日完成的工作：\n\n{chr(10).join(today_tasks)}\n\n代码变更：\n{code_changes}\n\n遇到的问题：\n{issues}\n\n请按照以下格式整理：\n1. 今日完成\n2. 遇到问题\n3. 明日计划\n4. 需要支持",
  "from_model": "GLM4.7"
}
```

#### 步骤3：生成日报文档

```python
# 整合DeepSeek建议和实际情况
daily_report = f"""
# 2026-01-14 每日进度

## 今日完成
{chr(10).join([f"{i+1}. {task}" for i, task in enumerate(today_tasks)])}

## 代码变更
{code_changes}

## 遇到问题
{issues}

## 明日计划
1. 完善MCP工具的错误处理
2. 添加单元测试和集成测试
3. 优化文档和示例
4. 测试DeepSeek爬虫的稳定性

## 需要支持
1. Playwright浏览器优化
2. MCP工具配置自动化
3. 数据库异步操作支持
"""

# 创建日报文档
{
  "doc_type": "daily_progress",
  "title": "2026-01-14 每日进度",
  "content": daily_report,
  "author": "GLM4.7"
}
```

---

## 场景四：周报

### 场景描述

Gemini需要生成周报，汇总本周所有日报和关键变更。

### 使用步骤

#### 步骤1：读取本周所有日报

```python
# 读取本周所有日报
from pathlib import Path
import glob

daily_reports_dir = Path("collaboration_docs/daily_progress")
daily_reports = sorted(daily_reports_dir.glob("daily_progress_*.md"))

print(f"找到 {len(daily_reports)} 份日报")

# 汇总本周工作
weekly_work = []
for report_path in daily_reports:
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
        weekly_work.append(content)
```

#### 步骤2：调用DeepSeek整理周报

```json
{
  "message": f"本周完成了MCP系统的完整实现，包括：\n\n1. 基础设施搭建\n2. DeepSeek爬虫实现\n3. MCP服务层开发\n4. API控制器实现\n5. MCP工具定义\n6. 文档和脚本编写\n\n请帮我整理成周报，重点突出：\n1. 主要成果\n2. 技术亮点\n3. 遇到的问题\n4. 下周计划",
  "from_model": "Gemini"
}
```

#### 步骤3：生成周报文档

```python
# 生成周报
weekly_report = f"""
# 2026年第2周周报（01-08 ~ 01-14）

## 本周主要成果
1. ✅ 完成MCP系统的基础设施搭建
2. ✅ 实现DeepSeek网页版爬虫
3. ✅ 开发MCP服务层和API控制器
4. ✅ 定义TypeScript MCP工具
5. ✅ 编写完整的文档和脚本

## 技术亮点
1. 使用Playwright实现稳定的网页爬虫
2. 采用FastAPI提供高性能API服务
3. 实现完整的文档版本管理和备份
4. 提供自动化安装和部署脚本
5. 遵循Trae项目规则，使用中文文档

## 遇到的问题
1. Playwright浏览器安装时间较长
2. MCP工具配置需要手动调整
3. 数据库异步操作需要额外支持

## 下周计划
1. 完善MCP工具的错误处理
2. 添加单元测试和集成测试
3. 优化DeepSeek爬虫性能
4. 添加更多使用示例和文档
5. 实现Docker部署支持

## 关键指标
- 代码文件：18个
- 文档文件：8个
- 脚本文件：3个
- MCP工具：8个
"""

# 创建周报文档
{
  "doc_type": "weekly_report",
  "title": "2026年第2周周报",
  "content": weekly_report,
  "author": "Gemini"
}
```

---

## 场景五：测试报告

### 场景描述

GLM4.7需要生成测试报告，汇总测试结果和问题。

### 使用步骤

#### 步骤1：收集测试结果

```python
# 收集测试结果
test_results = {
    "unit_tests": {
        "total": 50,
        "passed": 48,
        "failed": 2,
        "coverage": "85%"
    },
    "integration_tests": {
        "total": 20,
        "passed": 18,
        "failed": 2,
        "coverage": "70%"
    },
    "e2e_tests": {
        "total": 10,
        "passed": 9,
        "failed": 1,
        "coverage": "60%"
    }
}

# 收集测试问题
test_issues = [
    {
        "test": "test_deepseek_login",
        "error": "登录超时",
        "severity": "high",
        "status": "open"
    },
    {
        "test": "test_collaboration_doc_update",
        "error": "并发更新冲突",
        "severity": "medium",
        "status": "open"
    }
]
```

#### 步骤2：调用DeepSeek整理测试报告

```json
{
  "message": f"测试结果如下，请帮忙整理成测试报告：\n\n单元测试：{test_results['unit_tests']}\n集成测试：{test_results['integration_tests']}\n端到端测试：{test_results['e2e_tests']}\n\n测试问题：\n{chr(10).join([f\"- {issue['test']}: {issue['error']}\" for issue in test_issues])}\n\n请按照以下格式整理：\n1. 测试概览\n2. 测试结果\n3. 问题分析\n4. 改进建议",
  "from_model": "GLM4.7"
}
```

#### 步骤3：生成测试报告

```python
# 生成测试报告
test_report = f"""
# MCP系统测试报告

## 测试概览
- 测试时间：2026-01-14
- 测试人员：GLM4.7
- 测试环境：开发环境

## 测试结果

### 单元测试
- 总数：{test_results['unit_tests']['total']}
- 通过：{test_results['unit_tests']['passed']}
- 失败：{test_results['unit_tests']['failed']}
- 覆盖率：{test_results['unit_tests']['coverage']}

### 集成测试
- 总数：{test_results['integration_tests']['total']}
- 通过：{test_results['integration_tests']['passed']}
- 失败：{test_results['integration_tests']['failed']}
- 覆盖率：{test_results['integration_tests']['coverage']}

### 端到端测试
- 总数：{test_results['e2e_tests']['total']}
- 通过：{test_results['e2e_tests']['passed']}
- 失败：{test_results['e2e_tests']['failed']}
- 覆盖率：{test_results['e2e_tests']['coverage']}

## 问题分析

### 高优先级问题
1. **test_deepseek_login**: 登录超时
   - 严重性：高
   - 状态：待解决
   - 原因：网络延迟或DeepSeek服务器响应慢
   - 解决方案：增加超时时间，添加重试机制

### 中优先级问题
2. **test_collaboration_doc_update**: 并发更新冲突
   - 严重性：中
   - 状态：待解决
   - 原因：缺少并发控制
   - 解决方案：添加文件锁机制

## 改进建议
1. 增加测试覆盖率到90%以上
2. 添加性能测试和压力测试
3. 实现自动化测试流水线
4. 完善错误处理和日志记录
5. 添加测试数据管理

## 测试结论
系统整体功能正常，主要功能已实现。发现2个问题，建议优先解决高优先级问题。系统可以进入下一阶段测试。
"""

# 创建测试报告文档
{
  "doc_type": "test_report",
  "title": "MCP系统测试报告",
  "content": test_report,
  "author": "GLM4.7"
}
```

---

## 最佳实践

### 1. 协作流程

1. GLM4.7/Gemini读取项目文档和代码
2. 通过MCP工具调用DeepSeek获取外部视角
3. 整合DeepSeek的建议和本地项目情况
4. 更新协作文档并添加署名
5. 循环直到达成共识

### 2. 署名规范

每次更新文档时，必须添加署名：

```
[YYYY-MM-DD HH:MM] @ModelName: [操作描述]
```

示例：
```
[2026-01-14 10:30] @GLM4.7: 整合DeepSeek架构分析和实际代码
[2026-01-14 11:15] @Gemini: 完善技术方案评审意见
```

### 3. 文档管理

- 使用版本控制
- 定期备份重要文档
- 及时更新变更记录
- 保持文档结构一致

### 4. 错误处理

- 捕获并记录所有错误
- 提供清晰的错误信息
- 实现重试机制
- 添加超时控制

---

## 更多资源

- [MCP快速开始指南](MCP_QUICKSTART.md)
- [MCP配置说明](MCP_CONFIG_GUIDE.md)
- [故障排查指南](MCP_TROUBLESHOOTING.md)
- [系统README](README_MCP.md)
- [文档规范](collaboration_docs/standards.md)

---

*使用示例文档最后更新: 2026-01-14*