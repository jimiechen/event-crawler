# 实盘交易系统运维手册 (Live Trading Operations)

## 1. 启动前检查清单 (Pre-Market Checklist)

### 08:30 - 09:00 准备阶段
- [ ] **启动 Docker 环境** (Database & Redis)
  ```bash
  docker-compose up -d
  ```
- [ ] **启动后端服务**
  ```bash
  cd apps/stock-monitor-backend
  source venv/bin/activate  # 如果使用虚拟环境
  python main.py
  # 或
  uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
  ```
- [ ] **加载 Chrome 扩展**
  - 打开 Chrome -> 扩展程序
  - 确保 "Stock Monitor Extension" 已启用
  - 点击 "刷新" 按钮确保最新代码生效
- [ ] **登录同花顺网页版**
  - 访问 [同花顺行情中心](http://q.10jqka.com.cn/)
  - 确保已登录账户
  - 打开 "自选股" 或 "涨幅榜" 页面
- [ ] **启动实时监控面板**
  ```bash
  cd apps/stock-monitor-backend
  python tools/live_monitor.py
  ```
  - 确认所有状态均为 **HEALTHY** (绿色)

## 2. 盘中监控 (Market Hours Monitoring)

### 监控指标
1. **Live Monitor 状态**: 保持绿色。如果变红，立即检查后端日志。
2. **Chrome 扩展图标**: 应该显示 Badge 计数或保持活动状态。
3. **数据流延迟**: 观察 Live Monitor 中的响应时间。

### 常见问题与快速修复

#### 🔴 后端服务无响应 / 500 错误
**症状**: `live_monitor.py` 显示 `HTTP 500` 或连接失败。
**操作**:
1. 查看后端控制台日志，寻找报错信息。
2. 重启后端服务:
   ```bash
   # Ctrl+C 停止服务
   python main.py
   ```

#### 🔴 Chrome 扩展不发送数据
**症状**: 扩展图标无反应，后端没有日志输出。
**操作**:
1. 刷新同花顺网页。
2. 点击扩展图标 -> "重新加载扩展"。
3. 确认 "开始监听" 开关已打开。

#### 🔴 数据异常 / 缓存问题
**症状**: 告警逻辑混乱，或 Baseline 数据不更新。
**操作**:
1. 清除 Redis 缓存:
   ```bash
   cd apps/stock-monitor-backend
   python tools/clear_cache.py
   ```

## 3. 盘后维护 (Post-Market Maintenance)

### 15:00 - 15:30 收盘阶段
- [ ] **停止监听**: 在 Chrome 扩展中点击 "停止监听"。
- [ ] **数据备份**: 检查数据库中当日数据量是否正常。
- [ ] **日志归档**: (可选) 备份 logs/ 目录下的日志文件。

## 4. 紧急联系与日志

- **后端日志**: `apps/stock-monitor-backend/logs/`
- **Chrome 日志**: Chrome 扩展管理页 -> 背景页 -> Console

---
**技术支持**: 请参考 `docs/` 目录下的架构文档或联系开发人员。
