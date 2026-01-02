# Day 1 安装部署与验收指南

本文档指导如何部署 `oasis-simulation` (Python) 服务，并验证其与 `MineplanetGo` 网关的集成。

## 1. 环境准备

### 1.1 基础设施
确保以下服务已就绪：
*   **Redis**: 远程 `192.168.1.6:6379` (无需操作，代码已配置)
*   **Postgres**: 需要部署。推荐使用 Docker 启动。

**启动 Postgres (在 `outModules/open-citycloud/modules/oasis-simulation` 目录下):**
```bash
cd /Users/mac/ok-mcp/event-crawler/outModules/open-citycloud/modules/oasis-simulation
docker-compose up -d postgres
```
*   这将在端口 `5432` 启动 Postgres 数据库。

### 1.2 Python 环境 (Oasis Service)

**选项 A: Docker 运行 (推荐)**
```bash
cd /Users/mac/ok-mcp/event-crawler/outModules/open-citycloud/modules/oasis-simulation
docker build -t oasis-simulation:v1 .
docker run -d --name oasis-app \
  -p 10000:10000 \
  -p 10001:10001 \
  -e REDIS_HOST=192.168.1.6 \
  -e PG_HOST=host.docker.internal \
  --add-host=host.docker.internal:host-gateway \
  oasis-simulation:v1
```
*(注: 如果 Postgres 也在 Docker 中运行，请确保网络互通。最简单的是都在 docker-compose 中运行，但这里为了灵活性拆分了命令)*

**选项 B: 本地运行 (需安装 Python 3.11)**
1.  安装依赖:
    ```bash
    pip install -r requirements.txt
    ```
    *注意: 如果缺少 `tars` 包，可能需要自行编译 TarsPython 或从私有源安装。由于 TarsPython 比较特殊，如果本地无法安装，请使用 Docker 方式。*

2.  启动服务:
    ```bash
    export REDIS_HOST=192.168.1.6
    export PG_HOST=localhost
    python AgentServer.py --config=config.conf
    ```

### 1.3 Go 网关 (Gateway)

确保已安装 Go 1.20+。

```bash
cd /Users/mac/ok-mcp/event-crawler/outModules/MineplanetGo/mineplanet/Gateway
# 确保已应用代码修改 (servant/oasis_client.go, router.go, router.yaml)
go mod tidy
go run main.go --config=conf/server_config.yaml
```

---

## 2. 验收测试

我们通过网关接口 `/api/hello` 发送 Protobuf 编码的 `MessagePacket` 来触发 Python 端的逻辑。

### 2.1 模拟测试脚本 (Python)

创建一个测试脚本 `verify_day1.py` 来发送请求：

```python
import requests
import struct
# 假设你有 generated protobuf code，或者手动构造
# 这里为了演示，我们构造一个简单的 MessagePacket JSON (如果网关支持 JSON debug) 
# 或者直接说明验证步骤。

# 由于网关对外通常是 HTTP + Protobuf body，我们可以用简单的 curl 验证连通性
# 但由于 Request Body 是二进制 Protobuf，建议使用代码发送。
```

**为了方便，我已为你准备了验证脚本:** `/Users/mac/ok-mcp/event-crawler/verify_day1.py` (稍后创建)

**执行验证:**
```bash
python verify_day1.py
```

### 2.2 预期结果

1.  **Tick (8001)**:
    *   脚本发送 `MaxType: 8000, MinType: 8001`。
    *   网关路由到 `Oasis.AgentServer.AgentObj` -> `tick()`。
    *   Python 服务打印: `[AgentObj] Tick received for <agent_id>`。
    *   Redis 键 `agent:state:<agent_id>` 更新 (hunger 减少)。
    *   脚本收到响应，状态码 `0`。

2.  **GetState (8003)**:
    *   脚本发送 `MaxType: 8000, MinType: 8003`。
    *   网关路由到 `getState()`。
    *   返回 JSON 数据包含当前的 `hunger`, `energy`。

## 3. 故障排查

*   **网关报错 "Service Oasis.AgentServer.AgentObj not configured"**: 检查 `conf/router.yaml` 是否包含 `oasis` 块。
*   **网关报错 "Tars service call failed"**: 检查 Python 服务是否启动并在 `10001` 端口监听 (`netstat -an | grep 10001`)。
*   **Redis 连接失败**: 检查 `192.168.1.6` 是否可达。
