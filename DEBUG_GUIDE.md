# 联调操作指引

## 1. 准备工作

确保以下服务已启动：

1.  **Native Server (MCP Server)**
    *   路径: `projects/event-crawler/apps/native-server`
    *   命令: `npm start`
    *   端口: `3000` (HTTP/WS)
    *   日志: `projects/event-crawler/logs/server.log`

2.  **Stock Monitor Backend**
    *   路径: `projects/event-crawler/apps/stock-monitor-backend`
    *   命令: `python3 -m uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000`
    *   端口: `8000`

3.  **Chrome Extension**
    *   已加载最新构建的插件 (需重新加载以应用 Sidepanel 更改)
    *   确保 Native Host 连接成功 (Extension Log 中显示 `Native host connected`)

## 2. 联调步骤

### 步骤一：启动 Python 调试客户端

在项目根目录运行调试脚本，监听 Native Server 的 WebSocket 广播：

```bash
# 需要安装 websockets 库: pip install websockets
python3 projects/event-crawler/debug_client.py
```

客户端启动后会显示：
`[INFO] Connected to Native Server via WebSocket`
`[INFO] Waiting for messages from Chrome Extension...`

### 步骤二：操作 Chrome 扩展 Sidepanel

1.  打开 Chrome 浏览器，点击扩展图标打开 Sidepanel。
2.  切换到 **"系统状态"** Tab。
3.  **验证状态显示**：
    *   **Native Server**: 应显示 "已连接" (绿色)，WS/SSE 状态 "活跃"。
    *   **Stock Monitor Backend**: 应显示 "在线" (绿色)，数据库 "正常"。
    *   **总体健康度**: 应显示 "系统运行正常" (绿色 ✅)。
    *   如果显示异常，点击右上角刷新按钮重试。

### 步骤三：验证数据流 (Extension -> Native Server -> Python Client)

1.  在 Sidepanel 切换回 **"数据监控"** Tab。
2.  点击 **"抓取网页内容"** 或 **"检查登录状态"**。
3.  观察 Python 调试客户端的终端输出：
    *   应收到 JSON 格式的消息。
    *   示例:
        ```json
        {
          "type": "FORWARD_TO_NATIVE",
          "payload": { ... }
        }
        ```

### 步骤四：验证 Playwright/爬虫集成 (可选)

如果需要验证 Playwright 触发流程：
1.  确保 Native Server 正常运行。
2.  运行你的 Playwright 脚本（需配置连接 `ws://localhost:3000/api/ws`）。
3.  Playwright 脚本发送指令到 WS，Sidepanel 应能通过 SSE 或轮询接收到状态变化（目前 Sidepanel 主要实现了单向状态展示，双向控制需进一步开发 "配置管理" 或 "MCP测试" 模块）。

## 3. 故障排查

*   **Native Server 连接失败**:
    *   检查端口 3000 是否被占用: `lsof -i :3000`
    *   检查 `logs/server.log` 是否有报错。
*   **Extension 无法连接 Native Host**:
    *   检查 Chrome 扩展管理页面的 "错误" 按钮。
    *   确认 `com.chromemcp.nativehost.json` manifest 文件路径正确且已加载。
    *   **关键**: 检查 Chrome 扩展 ID 是否与 Native Host 配置一致。
        *   打开 `chrome://extensions` 查看你的扩展 ID。
        *   检查 `projects/event-crawler/apps/native-server/src/scripts/constant.ts` 中的 `EXTENSION_ID`。
        *   如果不一致，请修改 `constant.ts`，然后运行 `cd projects/event-crawler/apps/native-server && npm run build && npm run register:dev`。
*   **Python Client 连接失败**:
    *   确认 Native Server 已启动且支持 WebSocket (`@fastify/websocket` 已安装)。
*   **Backend 状态异常**:
    *   检查端口 8000 是否启动。
    *   检查数据库连接是否正常。

---
**Happy Debugging!** 🚀
