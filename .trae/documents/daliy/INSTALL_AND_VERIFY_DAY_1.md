# Day 1 验证与安装指南

## 1. 基础设施启动

首先启动 Redis 和 PostgreSQL，这是所有服务的基础依赖。

```bash
cd /Users/mac/ok-mcp/event-crawler/outModules/open-citycloud
docker-compose -f docker-compose-infra.yml up -d
```

验证服务状态：

```bash
docker ps
# 确认 redis 和 postgres 容器状态为 Up (healthy)
```

## 2. 网关 (MineplanetGo/Gateway) 适配验证

已完成 `MineplanetGo/Gateway` 对 Oasis 和 Coin 服务的适配。

### 2.1 变更内容

* **路由配置** (`router.yaml`):

  * 新增 `oasis` 服务 (MaxType: 8000)

  * 新增 `coin` 服务 (MaxType: 10000)

* **代码适配** (`router.go`):

  * 添加 `case 8000` 处理逻辑 (Oasis)

  * 添加 `case 10000` 处理逻辑 (Coin)

* **客户端封装** (`servant/`):

  * `oasis_client.go`: 通用 Invoke 封装

  * `coinobj_client.go`: 通用 Invoke 封装

### 2.2 验证方法

由于 Go 环境编译依赖较多，推荐使用提供的验证脚本进行协议测试。

运行验证脚本（模拟 HTTP 请求发送 MessagePacket）：

```bash
cd /Users/mac/ok-mcp/event-crawler/outModules/MineplanetGo/mineplanet/Gateway
go run verify_day1.go
```

*注：需先启动 Gateway 服务 (通常在 IDE 或通过* *`go run main.go`* *启动)*

## 3. Oasis 仿真服务 (Python)

已初始化 Python Tars 服务项目结构。

### 3.1 项目位置

`/Users/mac/ok-mcp/event-crawler/outModules/open-citycloud/modules/module-oasis`

### 3.2 目录结构

* `oasis.tars`: Tars 接口定义 (Tick, GetState, GetProfile)

* `src/server.py`: 服务启动入口

* `src/impl.py`: 接口实现逻辑 (Mock)

* `Dockerfile`: 容器化构建文件

### 3.3 运行方式 (Docker)

```bash
cd /Users/mac/ok-mcp/event-crawler/outModules/open-citycloud/modules/module-oasis
docker build -t oasis-service .
docker run -d --name oasis-service --network oasis-net -p 10001:10001 oasis-service
```

*注：端口需与* *`router.yaml`* *中配置的一致 (10001)*

## 4. 平台币服务 (Coin Module)

已初始化 Coin 模块 Tars 接口。

### 4.1 项目位置

`/Users/mac/ok-mcp/event-crawler/outModules/MineplanetGo/mineplanet/coin-server`

### 4.2 接口定义

* `Coin.tars`: 定义了 `getBalance`, `addBalance`, `deductBalance`, `transfer` 接口。

* MaxType: 10000

## 5. 下一步计划

* 完善 Oasis 服务 Python 实现 (连接 Redis/PG)

* 实现 Coin 服务 Go 逻辑 (连接 DB)

* 联调 Gateway -> Oasis/Coin 的完整链路

