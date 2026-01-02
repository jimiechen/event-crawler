# 模块规范与边界定义报告 (Day 1)

## 1. 核心命名规范

根据 CTO 架构提案与 Day 1 开发要求，对 `/Users/mac/ok-mcp/event-crawler/outModules/open-citycloud/modules` 目录下的项目执行了严格的命名规范整理：

* **`xxx-server`**: 独立进程服务。必须包含入口文件（如 `server.py`, `main.go`）和 `Dockerfile`，可独立部署和启动。

* **`module-xxxx`**: 内部功能模块/SDK。通常作为依赖被 Server 引用，不独立运行进程。

## 2. 模块重构与重命名执行结果

| 原目录名                           | 新目录名                          | 类型                | 职责定义                                                                                                                         |
| :----------------------------- | :---------------------------- | :---------------- | :--------------------------------------------------------------------------------------------------------------------------- |
| `module-oasis`                 | **`oasis-server`**            | **Tars Service**  | **微观仿真网关服务**。- 实现了 Tars 协议 (`AgentObj`)，作为 Gateway 的直接下游。- 负责状态持久化 (Redis/Postgres) 和请求路由。- **入口**: `AgentServer.py`         |
| `module-oasis-simulation`      | **`oasis-simulation-server`** | **Flask Service** | **核心仿真计算引擎**。- 纯 Python 计算服务，运行复杂 Agent 逻辑 (DeepSeek, NetworkX)。- 提供 REST API 供 `oasis-server` 或其他服务调用。- **入口**: `server.py` |
| `module-ai-character`          | **`ai-character-server`**     | **Tars Service**  | **AI 角色对话服务**。- 独立的 Tars 服务，处理单体 Agent 的对话请求。- **入口**: `server.py`                                                           |
| `module-aigc-content`          | *保持不变*                        | **Module (Lib)**  | **AIGC 内容生成库**。- 提供文章、报告生成的工具类。- 被 `topic-server` (Go) 或其他 Python 服务调用（需封装为 Service 或作为 Lib 引用）。                             |
| `module-bettafish-integration` | *保持不变*                        | **Module (Lib)**  | **外部集成 SDK**。- 封装了与 BettaFish 爬虫系统的通信逻辑。- 将外部新闻转换为标准 Event 格式。                                                               |

## 3. 待清理/占位模块说明

以下模块目前仅包含 `README.md` 或为空，建议在确认无用后删除，或作为未来开发的占位符：

* **`module-user`**: ⚠️ **冗余**。

  * **说明**: 用户服务 (`user-server`) 已在 `MineplanetGo` 仓库中由 Go 语言实现。此 Python 目录可能是早期遗留或误创建。

  * **建议**: **删除**，避免混淆。

* **`module-admin`**:

  * **说明**: 管理后台服务 (`admin-server`) 计划由 Go/Gin 实现。此目录若无代码应删除。

* **`module-api`,** **`module-auth`**:

  * **说明**: 若无实际 Python 代码，建议清理，避免项目结构臃肿。

## 4. 架构映射 (Reference to Roadmap)

* **Gateway (Go)** -> 调用 -> **`oasis-server`** **(Tars)**

* **`oasis-server`** -> 调用 -> **`oasis-simulation-server`** **(REST/RPC)**

* **`oasis-server`** -> 读写 -> **Redis/PostgreSQL**

此结构完全符合 [CTO\_ARCHITECTURE\_PROPOSAL\_V1\_UPDATE.md](file:///Users/mac/ok-mcp/event-crawler/.trae/documents/CTO_ARCHITECTURE_PROPOSAL_V1_UPDATE.md) 中的 "LOD AI System" 设计：

* `oasis-server` 对应 LOD 1/2 的快速处理层。

* `oasis-simulation-server` 对应 LOD 3 的深度计算 Worker。

