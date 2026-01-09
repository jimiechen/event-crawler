# Chrome 扩展与 Playwright 互调可行性分析与实施方案

## 1. 评估结论

**可行性：高**

经过对项目代码的深入分析，当前的架构已经具备了实现 Chrome 扩展与 Playwright（或其他外部进程）双向通信的基础设施。

*   **Native Server 已就绪**: `projects/event-crawler/apps/native-server` 已经实现了一个基于 Fastify 的 HTTP 服务器，并且通过 Native Messaging 协议与 Chrome 扩展建立了持久连接。
*   **通信链路已打通**: 现有的 `/ask-extension` 接口已经证明了 "外部 HTTP 请求 -> Native Server -> Chrome 扩展 -> Native Server -> 外部响应" 这一链路的畅通。
*   **Direct API 支持**: 针对 MCP 协议不稳定的情况，项目在 Native Server 中引入了 `DirectController`，提供稳定、直接的 REST API (`/api/login-request`, `/api/login-status`)，确保关键业务流程（如登录互调）的高可用性。
*   **MCP 支持 (可选)**: 项目中保留了 Model Context Protocol (MCP) 集成，作为 AI Agent 的实验性接口，不影响核心业务稳定性。

## 2. 场景解决方案

针对您提出的三个核心场景，以下是具体的实现方案（优先采用 Direct API 模式）：

### 场景一：解决 Playwright 登录/验证码/会话过期问题

**流程设计（Direct API 模式）：**

1.  **检测**: Playwright 爬虫在运行过程中检测到登录页、验证码或 401/403 错误。
2.  **请求**: Playwright 暂停爬取任务，向 Native Server 发送 HTTP 请求 `POST /api/login-request`，携带当前目标 URL。
3.  **通知**: Native Server 通过 Native Messaging 将请求转发给 Chrome 扩展。
4.  **交互**: Chrome 扩展接收到消息后：
    *   弹窗提示运营人员："爬虫遇到登录墙，请在当前浏览器中完成登录"。
    *   自动打开目标 URL。
5.  **捕获**: 扩展监听登录成功信号（可以是用户点击"我已登录"按钮，或自动检测 Cookie 变化）。
6.  **同步**: 扩展获取当前域名的 Cookies 和 LocalStorage，通过 `nativePort.postMessage({ type: 'LOGIN_COMPLETED', payload: { ... } })` 发送回 Native Server。
7.  **恢复**: Native Server 更新内存中的请求状态。Playwright 轮询 `GET /api/login-status/:requestId` 获取凭证，注入后恢复爬取。

**实现关键点：**
*   **稳定性优先**: 绕过 MCP 复杂的 Session 握手，使用无状态的 REST API + 内存状态存储。
*   **长轮询**: Playwright 端使用简单的轮询机制，避免长连接超时。

### 场景二：Chrome 扩展数据投递给 Playwright

**流程设计：**

1.  **监听**: Chrome 扩展利用 `chrome.webRequest` 或 `chrome.debugger` 监听特定页面的网络请求（XHR/Fetch）。
2.  **过滤**: 根据规则筛选出有价值的 API 响应数据。
3.  **投递**: 扩展通过 `nativePort.postMessage` 将数据发送给 Native Server (e.g., `{ type: 'DATA_CAPTURED', payload: { ... } }`).
4.  **实时转发 (WebSocket/SSE)**:
    *   **Native Server**: 接收到扩展消息后，立即通过 WebSocket (`/api/ws`) 和 SSE (`/api/events`) 广播给所有连接的客户端（Playwright）。
    *   **Playwright**: 
        *   **WebSocket 模式**: 连接 `ws://localhost:3000/api/ws`，监听 `message` 事件。系统健康状态
        *   **SSE 模式**: 连接 `http://localhost:3000/api/events`，监听 `EXTENSION_MESSAGE` 事件。
    *   **优势**: 相比轮询或缓冲，这种方式延迟极低，适合实时数据流处理。

**Native Server 实现更新 (DirectController):**
*   已集成 `@fastify/websocket` 支持 WebSocket。
*   已实现 `/api/ws` 双向通信接口。
*   已实现 `/api/events` Server-Sent Events 单向流接口。
*   实现了消息广播机制：`Extension -> NativeHost -> DirectController -> Broadcast -> WebSocket/SSE Clients`。

### 场景三：MCP 协议集成

**价值**:
如果引入第三方 MCP Client (如 Claude Desktop, Cursor 等)，可以将 "登录" 封装为一个 MCP Tool。
*   **Tool**: `wait_for_user_login(url: string)`
*   **效果**: AI 模型调用此工具时，会自动触发上述流程，等待用户操作完成后，AI 获得 Cookie 并继续执行任务。
*   **现状**: `apps/native-server` 中已经有 `mcp-server.ts`，扩展此功能非常容易。

## 3. 详细实施计划

### 第一步：扩展 Native Server (中间件)

修改 `apps/native-server/src/server/index.ts`:
1.  新增 `POST /api/login-session` 接口：接收 Playwright 的登录请求。
2.  新增 `GET /api/login-session/:id` 接口：供 Playwright 轮询登录状态和获取 Cookie。
3.  新增 `POST /api/data-ingest` 接口 (或 WebSocket)：供 Playwright 接收扩展投递的数据。

### 第二步：升级 Chrome 扩展 (前端)

修改 `apps/chrome-extension`:
1.  **Background (`background/index.ts`)**:
    *   监听来自 Native Host 的 `LOGIN_REQUIRED` 消息。
    *   创建通知 (`chrome.notifications`) 或打开新窗口提示用户。
2.  **Popup/Content Script**:
    *   提供一个界面供用户确认 "登录完成"。
    *   实现 `getCookies(url)` 逻辑，打包 Session 数据。
3.  **Data Capture**:
    *   完善现有的网络请求捕获逻辑 (参考 `network-capture-web-request.ts`)，增加向 Native Host 转发数据的通道。

### 第三步：封装 Playwright 客户端 (后端)

在 `modules/module-playwright-crawler` 中创建 `ChromeBridge` 类：
```python
class ChromeBridge:
    def __init__(self, api_url="http://localhost:3000"):
        self.api_url = api_url

    def request_manual_login(self, url):
        # 1. 发起请求
        # 2. 轮询等待
        # 3. 获取 Cookie
        pass

    def inject_cookies(self, context, cookies):
        # 注入 Playwright 上下文
        pass
```

## 4. 示例代码架构

**Native Server (TypeScript)**
```typescript
// 伪代码
fastify.post('/request-login', async (req, reply) => {
  const { url } = req.body;
  // 发送消息给 Chrome 扩展
  const requestId = uuid();
  await nativeHost.sendMessage({ type: 'LOGIN_REQUEST', url, requestId });
  return { requestId, status: 'pending' };
});
```

**Chrome Extension (TypeScript)**
```typescript
// 伪代码
nativePort.onMessage.addListener((msg) => {
  if (msg.type === 'LOGIN_REQUEST') {
    chrome.tabs.create({ url: msg.url });
    chrome.notifications.create({ title: '请登录', message: 'Playwright 需要您完成登录' });
    // 监听登录完成...
  }
});
```

## 5. 总结

您现有的项目结构非常适合这种集成。`native-server` 是完美的桥梁。
*   **工作量**: 中等 (约 2-3 天开发测试)。
*   **风险**: 低。Native Messaging 是 Chrome 官方支持的稳定方案。
*   **扩展性**: 极强。未来可以支持更多的人机协作场景。
