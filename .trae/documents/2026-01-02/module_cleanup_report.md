# 模块清理与边界定义报告 (2026-01-02)

## 1. 现状分析

在 `outModules/open-citycloud/modules` 目录下发现了三个与 Oasis 相关的项目，导致了开发计划的混淆：

1. **`module-oasis`** **(旧)**: 一个仅包含基础 Tars 结构和 Mock 实现的骨架项目。这是 `INSTALL_AND_VERIFY_DAY_1.md` 中引用的目录。
2. **`oasis-simulation`**: 包含完整的 Day 1 开发成果（Redis/Postgres 集成、ContextLoader、StateCommitter）。这是 `DETAILED_PLAN_DAY_1_2.md` 中实际执行的项目。
3. **`module-oasis-simulation`**: 一个独立的、更复杂的 Flask 仿真引擎（含 50 个 Agent 配置、DeepSeek 集成）。

## 2. 清理操作

为了统一项目结构并遵循 `module-*` 命名规范，执行了以下操作：

1. **删除**了旧的 `module-oasis` 骨架目录（因其功能已被 `oasis-simulation` 覆盖）。
2. **重命名** `oasis-simulation` 为 **`module-oasis`**。

   * **原因**: 这是 Tars 服务的实际实现（Gateway 接口层），且必须与 `router.yaml` 中的服务名和 `INSTALL` 文档中的路径保持一致。
3. **保留** `module-oasis-simulation`。

   * **定位**: 作为 **Core Engine (核心引擎)**。它不直接暴露 Tars 接口，而是作为 `module-oasis` 的上游逻辑库或独立微服务。

## 3. 模块边界定义 (Project Rules)

所有模块均位于 `/Users/mac/ok-mcp/event-crawler/outModules/open-citycloud/modules` 下。

| 模块名称                               | 职责边界                                                                                                       | 关键技术栈                             | 依赖关系                              |
| :--------------------------------- | :--------------------------------------------------------------------------------------------------------- | :-------------------------------- | :-------------------------------- |
| **`module-oasis`**                 | **Tars 网关服务 (Agent Gateway)**- 提供 Tars RPC 接口 (`tick`, `getState`)- 处理状态持久化 (Redis/Postgres)- 调用仿真引擎进行逻辑计算 | Python, Tars, Redis, Postgres     | 调用 `module-oasis-simulation` (逻辑) |
| **`module-oasis-simulation`**      | **仿真引擎 (Simulation Core)**- 纯业务逻辑与 AI 决策- 管理 Social Graph (NetworkX)- 集成 LLM (DeepSeek)- 不直接处理 RPC 协议      | Python, Flask, NetworkX, DeepSeek | 被 `module-oasis` 调用               |
| **`module-admin`**                 | **管理后台**- 系统配置与监控                                                                                          | Vue/React, Go/Python              | -                                 |
| **`module-ai-character`**          | **AI 角色服务**- 角色个性与对话生成                                                                                     | Python                            | -                                 |
| **`module-bettafish-integration`** | **外部集成**- 舆情与外部数据接入                                                                                        | Python                            | -                                 |

## 4. 后续建议

1. 在 `module-oasis` 中完善对 `module-oasis-simulation` 的调用逻辑（目前 `module-oasis` 使用的是内部 Mock 逻辑）。
2. 更新 `INSTALL_AND_VERIFY_DAY_1.md`，明确 `module-oasis` 即为之前的 `oasis-simulation` 目录。

