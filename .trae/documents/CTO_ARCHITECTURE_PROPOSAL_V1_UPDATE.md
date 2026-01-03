# Open CityCloud: 百万级 Agent 仿真与微观世界构建 - CTO 技术架构方案 (V1.0)

## 1. 核心愿景与挑战 (Executive Summary)

**项目目标**：构建一个拥有 **100万+ 活跃 Agent** 的微观经营世界。
**核心差异点**：

1. **算力众筹模式**：DeepSeek API Key 由真实用户提供，通过“算力入股”参与平台分成。
2. **虚实融合**：真实世界事件（爬虫）直接驱动微观世界演化。
3. **超大规模仿真**：百万级智能体在有限资源下的拟人化生存。

**当前技术瓶颈**：

* **现有架构 (Fat Agent)**：当前 `module-ai-character` 为每个 Agent 独立维护重型上下文和向量检索，无法线性扩展至百万级。

* **API 成本与限流**：DeepSeek API 即使由用户提供，也存在严重的并发限制（Rate Limit）和网络延迟，无法支撑百万 Agent 同时在线思考。

***

## 2. 核心架构设计：蜂巢式混合智能架构 (Cellular Hybrid-AI Architecture)

为了解决上述挑战，提出 **CHAA (Cellular Hybrid-AI Architecture)** 架构。核心思想是 **“分级智能 (LOD AI)”** 与 **“算力电网 (Compute Grid)”**。

### 2.1 算力电网子系统 (The API Key Power Grid)

这是商业模式的技术实现核心。我们将 API Key 视为“燃料棒”。

* **Key Vault (密钥金库)**：

  * 用户上传 Key 后，系统立即进行 **有效性验证** 和 **余额探测**。

  * Key 被 AES-256 加密存储，永不回显给前端。

  * **Credit Pool (信用池)**：根据 Key 的历史贡献（成功 Token 数）计算用户的“算力贡献值”，据此进行每日收益分红。

* **Smart Router (智能调度器)**：

  * 维护一个 **活跃 Key 池**。

  * **轮询与熔断**：当某个 Key 触发 Rate Limit (429) 或 余额不足 (402) 时，自动熔断该 Key 并切换至下一个，同时扣除提供者的“信用分”。

  * **优先级队列**：付费用户的交互请求使用“高质量/低延迟”Key 池。

### 2.2 百万 Agent 分级智能系统 (LOD AI System)

不仅图形渲染有 LOD (Level of Detail)，**智能也需要 LOD**。

| 智能等级 (LOD)               | Agent 状态 | 数量占比 | 技术实现                                                      | 触发条件                 |
| :----------------------- | :------- | :--- | :-------------------------------------------------------- | :------------------- |
| **LOD 0 (Hibernation)**  | 冬眠       | 90%  | **冷存储 (Cold DB)**。仅保留核心属性和摘要。                             | 玩家不在线，且处于非活跃区域。      |
| **LOD 1 (Instinct)**     | 本能       | 9%   | **FSM (有限状态机) / 行为树**。执行"打工"、"睡觉"等固定逻辑。无 LLM 介入。          | 处于活跃区域背景，无直接交互。      |
| **LOD 2 (Conversation)** | 浅层交流     | 0.9% | **SLM (小参数本地模型)** 或 **DeepSeek-V3 (极简Prompt)**。进行简单寒暄、交易。 | 玩家靠近，或发生轻度交互。        |
| **LOD 3 (Awakening)**    | 觉醒       | 0.1% | **DeepSeek-V3 (完整上下文)**。启用长期记忆、情感计算、复杂推理。                 | **玩家深度对话**、重大世界事件触发。 |

* **Group Mind (群体思维优化)**：对于聚集在同一场所（如“广场”）的 100 个 Agent，不进行 100 次 LLM 调用。而是由 **Scene Server** 生成一个“群体反应事件”（如“大家都在讨论刚刚的新闻”），然后分发给 100 个 Agent 更新状态。

### 2.3 虚实融合管道 (Reality Injection Pipeline)

利用 `module-bettafish-integration` 构建世界观的动态演进。

1. **Event Crawler (触角)**：抓取真实新闻（如“油价上涨”）。
2. **World Narrator (世界旁白 - LLM)**：将新闻转化为游戏内事件。

   * 输入：“国际原油上涨 5%”

   * 输出 Game Event：`{ type: "ECONOMY_SHOCK", target: "OIL", impact: +0.05, summary: "燃料价格飙升，运输成本增加" }`
3. **Effect Broadcaster (广播塔)**：

   * **宏观影响**：直接修改 `module-economy` 中的商品基准价格。

   * **微观影响**：向所有 **LOD 2/3** 的 Agent 推送“突发新闻”记忆，触发他们的行为改变（如囤油）。

***

## 3. 系统架构图 (System Topology)

```mermaid
graph TD
    User[真实用户] -->|上传 Key / 订阅| GoGateway[Go 业务网关]
    User -->|玩游戏 / 对话| RustGateway[Rust AI 网关]

    subgraph "核心业务层 (Go/Tars)"
        GoGateway --> KeyVault[Key 算力银行]
        GoGateway --> EconomyServer[微观经济引擎]
        GoGateway --> WorldServer[世界模拟服务器 (ECS)]
    end

    subgraph "AI 算力层 (Python Cluster)"
        RustGateway --> Dispatcher[任务分发器 (gRPC)]
        
        subgraph "LOD 3: DeepSeek Cluster"
        DeepSeekWorker[DeepSeek API 调用器]
        end
        
        subgraph "LOD 2: SLM Cluster"
        LocalLLM[本地小模型 (vLLM/Ollama)]
        end
        
        MemoryDB[(Vector DB - Chroma)]
    end

    subgraph "虚实桥接层"
        Crawler[BettaFish 爬虫] --> Narrator[世界旁白 Agent]
        Narrator -->|注入事件| WorldServer
    end

    WorldServer -->|LOD 切换| Dispatcher
    Dispatcher -->|申请 Key| KeyVault
    KeyVault -->|提供 Key| DeepSeekWorker
    DeepSeekWorker -->|调用| RealDeepSeekAPI[DeepSeek 官方 API]
```

***

## 4. 技术栈选型建议

*   **高性能接入网关**: **Rust (Tonic + Axum/Salvo)**。
    *   作为 AI 流量的统一入口，负责处理长连接 (SSE/WebSocket) 和高并发 `MessagePacket` 解析。
    *   替代原有的 TarsPython 网关方案，彻底解决 Python 在 I/O 密集型场景下的性能瓶颈。

*   **仿真内核 (World Server)**: **Go** (基于现有 `module-building` 扩展)。推荐使用 **ECS (Entity Component System)** 架构来管理百万实体。

*   **AI 服务网格**: **Python (gRPC + Celery/Ray)**。
    *   移除 Tars 协议，改用标准的 **gRPC** 与 Rust 网关通信。
    *   Python 专注于 LLM 调用、向量检索等计算密集型任务。

* **前端**: **React + WebGL (Three.js/PixiJS)** 或 **Unity WebGL**。`MineplanetGo` 若为 React 项目，建议引入 **PixiJS** 处理大量 2D 精灵的渲染。

* **数据库**:

  * **Redis Cluster**: 热数据（活跃 Agent 状态、Key 缓存）。

  * **MongoDB/Postgres**: 冷数据（冬眠 Agent、历史记录）。

  * **ChromaDB/Milvus**: 向量数据库（长期记忆）。

***

## 5. 实施路线图 (Roadmap)

### 第一阶段：算力银行与经济闭环 (Month 1)

* [ ] 实现 `KeyVault` 服务：Key 的加密存储、验证、轮询调度。

* [ ] 实现 `CreditSystem`：记录 Key 的消耗量，生成“分红报表”。

* [ ] 对接 `module-economy`：让 Agent 的经济行为消耗 Key 算力。

### 第二阶段：LOD 智能调度系统 (Month 2)

* [ ] 重构 `module-ai-character`，将其拆分为无状态的 Worker。

* [ ] 实现 `LODController`：根据玩家距离动态切换 Agent 的智能等级。

* [ ] 引入本地小模型 (SLM) 处理 LOD 2 级任务。

### 第三阶段：虚实融合与百万压力测试 (Month 3)

* [ ] 打通 `module-bettafish` 到 `WorldServer` 的事件管道。

* [ ] 部署 1000 个模拟玩家 + 10万个 Agent 进行压力测试。

* [ ] 优化数据库分片和 ECS 性能。

***

## 6. 给现有代码的建议

1. **`open-citycloud`**:

   * 保留 `module-building` 和 `module-economy` 作为微服务。

   * **废弃** 单体式的 `AICharacter` 类设计，改为 **Context-Injectable Agent**（上下文可注入式）。Agent 只是一个 ID，它的“灵魂”（记忆+Prompt）在需要时才从 DB 加载到 AI Worker 中。
2. **`MineplanetGo`**:

   * 确保前端架构支持 **视锥剔除 (Frustum Culling)**。只渲染玩家视野内的 Agent，与后端的 LOD 系统配合。

***

**CTO 结语**：
这个方案将“成本中心”（API 调用）转化为“利润中心”（用户提供 Key），并通过 LOD 技术解决了规模化难题。这是实现百万级 Agent 仿真的唯一可行路径。
