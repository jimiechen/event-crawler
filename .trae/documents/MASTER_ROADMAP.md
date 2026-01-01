# MineplanetGo Open CityCloud 总体研发战略规划

## 1. 愿景与目标

构建一个支持**多层级智能体仿真**的开放城市云平台。核心目标是在 **3 个月内** 完成内测版本，实现移动端用户与 AI 智能体在同一个数字世界（Topic/Group）中的深度共生与互动。

## 2. 总体架构设计

平台严格遵循 **Tars 微服务架构**。所有内部服务调用通过 Tars 协议（Go/Python 互通），对外统一通过网关提供 **Protobuf** 接口。

### 2.1 架构分层图

```mermaid
graph TD
    Client[Flutter App (Mobile)] -->|Protobuf| Gateway[统一网关 (Go/Tars)]
    
    subgraph Infrastructure [核心业务层 (Go/Tars)]
        Gateway --> UserServer[用户服务]
        Gateway --> GroupServer[社交关系服务1]
        Gateway --> TopicServer[内容话题服务]
        Gateway --> BuildingServer[模拟经营服务 (New)]
    end
    
    subgraph Operations [运营管理层 (Go/Gin)]
        AdminServer[管理后台 (admin-server)] -->|审核/管理| TopicServer
        AdminServer -->|管理| BuildingServer
        AdminServer -->|监控| AILayer
    end
    
    subgraph AILayer [AI 智能层 (Python/Tars)]
        direction TB
        Gateway --> AICharacter[AI 角色服务]
        Gateway --> OASIS[微观仿真服务]
        Gateway --> MacroEngine[宏观预测服务]
        
        OASIS -.->|Tars RPC| GroupServer
        OASIS -.->|Tars RPC| TopicServer
        OASIS -.->|Tars RPC| BuildingServer
        
        AICharacter --> DeepSeek[DeepSeek API]
    end
```

### 2.2 核心层级说明

1. **客户端 (Client)**

   * **平台**: Flutter App (Android/iOS).

   * **路径**: `/Users/mac/StudioProjects/MineplanetGo/outModules/TorFApp/true_or_false_app`

   * **交互**: 通过 Protobuf 定义的接口与 Gateway 通信，展示 AI 生成的内容和社交动态。

2. **核心业务层 (Core Services)**

   * **技术栈**: Go, TarsGo.

   * **职责**: 维护“真实”的业务数据。

   * **user-server**: 用户账号体系。

   * **group-server**: 社交关系链（群组、关注），**OASIS 智能体的社交关系也将直接存储于此**。

   * **topic-server**: 内容广场（帖子、回复），**OASIS 智能体生成的内容将直接写入此服务**。

   * **building-server** (New): 模拟经营核心（建筑、资产、地图），**原 Java Building API 迁移至 TarsGo**，为 OASIS 提供物理世界交互能力。

3. **AI 智能层 (AI Layer)**

   * **技术栈**: Python, TarsPython.

   * **职责**: 提供智能驱动力，统一调用 DeepSeek。

   * **AI Character**: 单体智能，处理对话、记忆。

   * **OASIS Simulation**: 50+ 智能体仿真驱动器。它不存储社交数据，而是**调用 group-server/topic-server** 来产生对用户可见的行为。

   * **Macro Engine**: 百万级群体模拟与舆情预测。

4. **运营管理层 (Operations)**

   * **平台**: Admin Web + Admin Server (Go/Gin).

   * **路径**: `admin-server`.

   * **职责**: 内容审核（包括 AI 生成的内容）、用户管理、仿真参数配置。

## 3. 模块映射与集成计划

| 模块名称              | 角色    | 对应路径/仓库                                                         | 技术栈     | 接入方式            |
| :---------------- | :---- | :-------------------------------------------------------------- | :------ | :-------------- |
| **Gateway**       | 统一入口  | `mineplanet/Gateway`                                            | Go      | Tars/Protobuf   |
| **Core Services** | 社交/内容 | `mineplanet/{user,group,topic}-server`                          | Go      | Tars            |
| **App Client**    | 用户端   | `outModules/TorFApp/true_or_false_app`                          | Flutter | Protobuf Client |
| **AI Services**   | 智能驱动  | `open-citycloud/modules/module-{ai-character,oasis,collective}` | Python  | TarsPython      |
| **Admin**         | 运营审核  | `admin-server`                                                  | Go      | HTTP/Gin        |

## 4. 3个月内测冲刺路线图 (Beta Roadmap)

### 第 1 个月：基础打通 (Infrastructure & Bridge)

**目标**: 实现 App 与 AI 服务的端到端联通。

* **网关**: 在 Gateway 引入 AI Tars 定义，发布 Protobuf 接口。

* **AI 服务**: 完成 `module-ai-character` 的 TarsPython 实现，跑通 `chatCompletion`。

* **客户端**: Flutter App 生成 AI 模块的 Protobuf 代码，实现与 AI 角色的基础对话 UI。

### 第 2 个月：微观融合 (Micro-Simulation Integration)

**目标**: 50 个智能体进入“真实”社交网络。

* **OASIS 接入**: 
    * [x] **Core Logic**: 完成 `SimulationEngine` 与 `AgentManager` 开发。
    * [x] **Mock Integration**: 完成 `MockTarsClient` 与仿真主循环的联调。
    * [ ] **Real Integration**: 实现 Python 调用 Go Tars 服务的客户端 (`group-server`, `topic-server`) (等待环境)。

* **仿真循环**: 
    * [x] **Logic**: 启动 50 个 Agent，让它们在 `topic-server` 中发帖，在 `group-server` 中建立群组 (Mock验证通过)。
    * [ ] **Deployment**: 在真实 Tars 环境中运行。

* **用户互动**: 真实用户可以在 App 中看到 Agent 的帖子并进行回复（回复由 Agent 异步处理）。

### 第 3 个月：宏观与运营 (Macro & Ops)

**目标**: 具备宏观预测能力与完善的管理后台。

* **宏观引擎**: 部署 MediaCrawler 和 Swarm Engine，生成市场/舆情报告内容。

* **管理后台**: `admin-server` 增加仿真控制面板（启动/停止、加速），增加 AI 内容审核队列。

* **内测发布**: 完成全链路压力测试，打包 Android/iOS 内测包。

## 5. 关键技术决策

1. **数据归一化**: 无论是人产生的社交数据，还是 AI 产生的，**必须**统一存储在 `group-server` 和 `topic-server`。AI 层不维护独立的社交数据库。
2. **协议强约束**: 客户端只认 Gateway 的 Protobuf 接口。Gateway 负责将请求路由到 Go 服务或 Python 服务。
3. **审核前置**: AI 产生的高风险内容（如帖子）在写入 `topic-server` 前，应经过敏感词过滤或人工审核标记（由 Admin Server 配置策略）。

## 6. 下一步行动

请参考更新后的 [PLAN.md](file:///Users/mac/StudioProjects/MineplanetGo/outModules/open-citycloud/.trae/documents/start/PLAN.md) 查看详细的周维度执行计划。
