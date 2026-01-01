# Day 1 & 2 详细执行计划 (精确到小时 + 验收标准)

## Day 1: 无状态 Agent 核心 & 网关集成 (Python Tars + Existing Gateway)

**目标**: 构建基于 Tars 协议的无状态 Agent 服务，并将其集成到现有的 `MineplanetGo` 网关中。

| 时间段               | 模块                 | 任务详情                                                                                                                                                                                      | 验收标准 (Checklist)                                      |
| :---------------- | :----------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------- |
| **09:00 - 09:30** | `oasis-simulation` | **Python Tars 项目初始化**1. 创建 TarsPython 项目结构 (`AgentServer.py`, `config.conf`).2. 定义 `AgentObj.tars` (接口: `tick`, `get_state`).3. 编写 `Dockerfile`。                                          | - \[ ] `tars2py` 生成代码成功- \[ ] Docker 镜像构建成功           |
| **09:30 - 10:30** | `Infra`            | **中间件部署**1. 编写 `docker-compose.yml` (Redis + Postgres).2. 初始化数据库 (创建 `agents` 表).                                                                                                         | - \[ ] `redis-cli` PONG- \[ ] Postgres 连接成功           |
| **10:30 - 11:30** | `oasis-simulation` | **核心模型与存储**1. 定义 `AgentProfile`, `AgentState`.2. 实现 `RedisClient` (State Cache).3. 实现 `ContextLoader` (Redis/DB -> Object).                                                               | - \[ ] 状态存取一致性验证- \[ ] Cache Miss 时回源 DB              |
| **11:30 - 12:00** | `oasis-simulation` | **Tars 接口实现**1. 实现 `AgentObj` Servant 逻辑 (`tick` 方法).2. 模拟 AI 思考 (Sleep).3. 状态提交 (`StateCommitter`).                                                                                      | - \[ ] 本地 Python Client 调用成功- \[ ] 状态变更持久化成功          |
| **13:00 - 14:30** | `Gateway`          | **现有网关适配**1. 在 `MineplanetGo/mineplanet/Gateway/servant` 中添加 `oasis_client.go` (通用 Invoke 封装).2. 修改 `router.go`: 添加 `case 8000` 处理逻辑。3. 修改 `router.yaml`: 添加 `oasis` 服务配置 (MaxType 8000). | - \[ ] `oasis_client` 编译通过- \[ ] `router.yaml` 配置正确加载 |
| **14:30 - 16:30** | `Gateway`          | **网关路由调试**1. 配置 `router.yaml` 中的 MinType (如 8001 -> `tick`).2. 启动 Gateway 连接本地 Python 服务。3. 使用 `curl` 或测试脚本发送 Protobuf 包请求 `/api/hello` (模拟).                                             | - \[ ] 网关成功转发请求至 Python- \[ ] Python 返回结果被网关正确接收      |
| **16:30 - 18:00** | `Test`             | **全链路联调**1. 模拟 Client -> Existing Gateway -> Python Agent (Tars) -> Redis/DB.2. 验证数据流转与状态更新。                                                                                              | - \[ ] 完整调用链路 < 200ms- \[ ] 错误处理正常                    |

### Day 1 每日验收清单

* [ ] `oasis-simulation` (Python Tars) 成功启动并监听端口。

* [ ] 现有 `Gateway` 成功识别并加载 `oasis` 服务配置。

* [ ] 发送 MaxType=8000, MinType=8001 的请求能触发 Python Agent Tick。

* [ ] Redis/Postgres 数据更新正确。

***

## Day 2: 平台币与经济系统 (Go + Tars)

**目标**: 建立独立的平台币系统，并集成到现有网关。

| 时间段               | 模块               | 任务详情                                                                                                                  | 验收标准 (Checklist)                        |
| :---------------- | :--------------- | :-------------------------------------------------------------------------------------------------------------------- | :-------------------------------------- |
| **09:00 - 10:00** | `module-coin`    | **平台币模块设计**1. 创建 `module-coin` (Go Tars).2. 设计 DB: `platform_wallets`, `platform_tx`.3. 定义 `CoinObj.tars`.            | - \[ ] DB Schema 创建成功- \[ ] Tars 接口定义完成 |
| **10:00 - 11:30** | `module-coin`    | **平台币核心逻辑**1. 实现 `GetBalance`, `Transfer`.2. 事务支持。3. 单元测试。                                                            | - \[ ] 转账逻辑正确- \[ ] 余额原子性更新             |
| **11:30 - 12:00** | `Gateway`        | **网关集成平台币**1. 添加 `servant/coin_client.go`.2. 修改 `router.go` (Add case 9000).3. 修改 `router.yaml` (MaxType 9000).       | - \[ ] 网关能查询余额                          |
| **13:00 - 14:30** | `module-economy` | **物品与合成系统**1. 创建 `module-economy` (Go Tars).2. DB: `items`, `inventory`, `recipes`.3. 逻辑: `Craft`.                    | - \[ ] 物品与配方数据结构正确- \[ ] 合成逻辑闭环         |
| **14:30 - 16:00** | `module-economy` | **经济系统集成**1. `module-economy` 调用 `module-coin` (RPC).2. 定义 `EconomyObj.tars`.                                         | - \[ ] 跨服务调用成功- \[ ] 扣费失败导致合成回滚         |
| **16:00 - 17:00** | `Gateway`        | **网关集成经济系统**1. 添加 `servant/economy_client.go`.2. 修改 `router.go` (Add case 10000).3. 修改 `router.yaml` (MaxType 10000). | - \[ ] 网关能触发合成操作                        |
| **17:00 - 18:00** | `Test`           | **系统总验**1. 模拟 1000 次经济交互。2. 检查总账平衡。                                                                                   | - \[ ] 无资金/物品丢失- \[ ] 日志完整              |

### Day 2 每日验收清单

* [ ] `module-coin` 和 `module-economy` 独立运行正常。

* [ ] 现有 `Gateway` 能正确路由平台币和经济请求。

* [ ] 完整的经济循环 (充值 -> 购买/合成 -> 消耗) 跑通。

