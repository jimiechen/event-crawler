# 架构升级计划：引入 Rust AI 网关与移除 TarsPython

## 1. 核心变更说明
响应用户指令，针对 TarsPython 废弃及 AI 业务实时性需求（SSE 流式输出），对架构进行以下关键调整：
1.  **移除 TarsPython**: Python 服务（AI 层）不再作为 Tars 服务运行，改为 **gRPC Server**。
2.  **新增 Rust AI Gateway**:
    *   **职责**: 专门处理 AI 相关的 `MessagePacket` 请求及 SSE 长连接。
    *   **协议**: 对外提供 HTTP/SSE 接口（接收 Protobuf），对内通过 gRPC 调用 Python 服务。
    *   **性能**: 利用 Rust (Tokio/Tonic/Axum) 的高并发能力处理百万级 Agent 的实时流推送。
3.  **双网关架构 (Dual-Gateway Strategy)**:
    *   **Go Gateway (现有)**: 继续负责 User/Group/Topic/Building 等核心业务的 Tars 请求与鉴权。
    *   **Rust Gateway (新增)**: 负责 AI Chat、Oasis 仿真等需要流式响应的业务。

## 2. 文档修改计划

### 2.1 修改 `MASTER_ROADMAP.md`
*   **架构图更新**:
    *   新增 `Rust AI Gateway` 节点。
    *   将 `Gateway -> AI Services (Tars)` 连线改为 `Rust Gateway -> AI Services (gRPC)`。
    *   移除 `TarsPython` 相关描述。
*   **模块映射表**:
    *   新增 `ai-gateway` (Rust)。
    *   更新 `AI Services` 技术栈为 `Python (gRPC)`.
*   **里程碑 (Phase 1)**:
    *   添加 "Rust 网关开发" 任务。
    *   添加 "Python 服务 gRPC 改造" 任务。

### 2.2 修改 `CTO_ARCHITECTURE_PROPOSAL_V1_UPDATE.md`
*   **核心架构设计**:
    *   在 "AI 算力层" 引入 **Rust Edge Gateway**，作为 "算力电网" 的高性能接入点。
    *   说明 Rust 网关如何解析 `MessagePacket` 并通过 SSE 推送 DeepSeek 的思考过程。
*   **技术栈选型**:
    *   **网关**: 明确区分 业务网关 (Go/Tars) 和 AI 网关 (Rust/gRPC+SSE)。
    *   **通信**: 废弃 TarsPython，确立 **gRPC** 为 AI 内部标准协议。

### 2.3 里程碑开发计划调整
*   **Day 1-3**: 
    *   初始化 `ai-gateway` (Rust) 项目结构。
    *   定义 `ai_service.proto`。
    *   将 `oasis-simulation-server` 改造为 gRPC Server。

## 3. 下一步执行操作
1.  **更新文档**: 执行上述文档修改。
2.  **创建 Rust 网关脚手架**: 在 `outModules/MineplanetGo/mineplanet/AiGateway` (新建) 初始化 Rust 项目。
3.  **清理旧代码**: 标记/删除 TarsPython 相关配置（如果需要）。
