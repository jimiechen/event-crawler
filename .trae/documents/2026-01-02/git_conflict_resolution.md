# Git 冲突修复报告 (2026-01-02)

## 问题描述
用户执行 `git pull --tags origin main` 时遇到冲突，主要涉及 `mineplanet/Gateway/conf/router.yaml` 文件。上游分支（origin/main）占用了 MaxType 8000 用于 `building` 服务，而本地修改也使用了 8000 用于 `oasis` 服务。

## 修复方案

### 1. 路由配置 (`router.yaml`)
- 保留上游的 `building` 服务配置 (MaxType: 8000)。
- 将本地新增的 `oasis` 服务迁移至 MaxType **8500**。
- 保留本地新增的 `coin` 服务配置 (MaxType: 10000)。

**修改后的 MaxTypes:**
```yaml
maxTypes:
  8000: "building"  # 上游
  8500: "oasis"     # 本地迁移
  10000: "coin"     # 本地新增
```

### 2. 网关代码 (`router.go`)
- 更新 `MessageRouter.invokeByMethod` 方法以支持新的 MaxType 映射。
- **MaxType 8000 (Building)**: 由于本地缺少 `BuildingObjClient`，暂时使用 `HelloObjClient` 作为通用 Tars 客户端进行调用，并传递上下文 `ctx`。
- **MaxType 8500 (Oasis)**: 映射到 `OasisObjClient`。

### 3. 验证脚本 (`verify_day1.go`)
- 更新测试脚本中的 `MaxType` 为 8500。
- 更新 `MinType` 为 8501 (tick 方法)。

## 执行结果
- 冲突已解决。
- 所有相关文件（`router.yaml`, `router.go`, `verify_day1.go`, 以及新增的 servant 客户端）已提交到本地仓库。
- 提交信息: "Merge conflict resolution: Update Gateway router configuration for Oasis (8500) and Coin (10000) services while preserving upstream Building service (8000)"

## 后续建议
- 建议检查上游是否提供了 `BuildingObjClient` 的具体实现，以便在未来替换通用的 `HelloObjClient`。
- 运行 `go run verify_day1.go` 验证 Oasis 服务是否正常响应（需确保 Gateway 和 Oasis 服务已启动）。
