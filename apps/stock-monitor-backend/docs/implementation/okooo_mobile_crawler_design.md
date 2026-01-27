# 澳客网 (Okooo) 移动端反爬虫技术方案深度分析与实施路线图

## 1. 方案概述

针对 `m.okooo.com` 存在的 Aliyun WAF (405 Block) 及潜在的高级行为检测机制，本方案旨在构建一个高成功率、高隐蔽性的爬虫系统。我们采用了基于 Playwright 的**全栈模拟**策略，通过深度伪装浏览器指纹、模拟人类操作行为以及智能化的网络请求管理，来绕过反爬虫防御。

目标页面：
1. `https://m.okooo.com/match/history.php?MatchID=1314249&from=%2Fjczq%2F` (战绩)
2. `https://m.okooo.com/match/handicap.php?MatchID=1314249&from=%2Fjczq%2F` (亚指)
3. `https://m.okooo.com/match/odds.php?MatchID=1314249&from=%2Fjczq%2F` (欧指)

---

## 2. 核心技术方案深度分析

### 2.1 高级行为分析方案 (Advanced Behavioral Analysis)

**技术原理**：
反爬系统通过收集用户在页面上的鼠标移动、点击、滚动以及键盘输入等事件序列，利用机器学习模型判断操作主体是否为人类。

**实施方案**：
- **轨迹模拟**：摒弃直线移动，使用贝塞尔曲线 (Bezier Curve) 生成鼠标/触摸轨迹。引入随机加速度和抖动。
- **触摸模拟**：针对移动端 (`m.okooo.com`)，模拟 `TouchStart`, `TouchMove`, `TouchEnd` 事件，而非 `MouseMove`。
- **页面交互**：
    - **随机滚动**：模拟阅读时的非线性滚动（快-慢-停-回滚）。
    - **智能停顿**：在关键操作（如点击）前后加入符合正态分布的随机延时。

**评估**：
- **准确率**：极高。配合 Playwright 的 CDP 协议，可以生成浏览器内核级别的真实事件。
- **性能影响**：中等。需要计算轨迹，但对单次爬取影响可忽略。

### 2.2 浏览器指纹增强方案 (Enhanced Browser Fingerprinting)

**技术原理**：
WAF 通过检测 Canvas、WebGL、AudioContext 的渲染结果，以及 `navigator` 对象属性（如 `webdriver`, `plugins`, `languages`）来识别自动化工具。

**实施方案**：
- **Stealth 注入**：注入 JavaScript 代码覆盖 `navigator.webdriver` 属性。
- **WebGL/Canvas 噪声**：对 Canvas 绘图接口进行 Hook，微调像素值（加入微小噪声），使得指纹不仅唯一且看似真实，防止指纹碰撞或黑名单匹配。
- **移动端特征伪装**：
    - 设置 `hasTouch=true`。
    - 伪装 `navigator.platform` (如 `iPhone`).
    - 匹配 `screen.width` / `window.innerWidth` 与 User-Agent 中的设备型号。

**评估**：
- **对抗能力**：强。能通过大多数静态指纹检测（如 FingerprintJS）。
- **维护成本**：需定期更新 User-Agent 库和对应的指纹配置。

### 2.3 网络请求特征分析 (Network Traffic Analysis)

**技术原理**：
检测 HTTP 请求头的顺序、缺失（如缺少 `Referer`）、TLS 指纹（JA3）以及请求频率。

**实施方案**：
- **头部一致性**：确保 `User-Agent` 与 `Sec-Ch-Ua` (Client Hints) 严格对应。
- **TLS 指纹**：Playwright 基于真实浏览器，天然具备合法的 TLS 指纹（这也是相比 Python `requests` 的巨大优势）。
- **时序控制**：请求间隔引入随机化，避免固定心跳模式。
- **Referer 链**：严格维护 `Referer`，模拟从列表页 -> 详情页的跳转路径。

### 2.4 机器学习检测对抗 (Counter-ML Detection)

**技术原理**：
反爬方利用 LSTM 等模型分析时序行为异常。

**实施方案**：
- **行为基线拟合**：记录真实人类访问该页面的操作日志，训练爬虫的行为参数（如停留时长分布）。
- **低频慢速**：降低单 IP 请求频率，处于异常检测阈值之下。
- **IP 轮换**：使用高质量住宅代理 (Residential Proxy)，避免数据中心 IP 段被直接封锁。

### 2.5 分布式协作防御对抗 (Counter-Distributed Defense)

**技术原理**：
共享 IP 信誉库。

**实施方案**：
- **分布式架构**：如果规模扩大，需部署在不同地理位置的节点。
- **账号/Cookie 池**：维护大量有效的 `acw_tc` (Aliyun WAF cookie) 池，减少频繁触发验证的风险。

---

## 3. 推荐方案组合与实施路线图

综合考虑成功率与稳定性，推荐采用 **Playwright + Mobile Emulation + Advanced Stealth + Behavior Simulation** 组合方案。

### 3.1 实施路线图

1.  **环境准备**
    - Python 3.10+
    - Playwright (`chromium` 引擎)
    - 依赖库：`playwright-stealth`, `numpy` (用于生成轨迹)

2.  **核心模块开发 (`scripts/crawl_okooo_mobile.py`)**
    - **初始化**：配置 iPhone 13/14 Pro 模拟环境（UserAgent, Viewport, DeviceScaleFactor）。
    - **反检测注入**：加载 Stealth 脚本，Mock `navigator` 属性。
    - **行为模拟器**：封装 `human_scroll`, `human_touch`, `random_delay` 函数。
    - **WAF 处理**：
        - 策略：Homepage First (先访问主页获取 Cookie)。
        - 检测：检查 `acw_tc` Cookie 和 405 状态码。
        - 绕过：如果遇到滑块，需接入打码平台（本阶段暂不涉及，通常 Aliyun WAF 静默验证即可通过）。

3.  **数据抓取与解析**
    - 针对 3 个目标 URL 分别编写解析逻辑。
    - 保存为 Markdown 或 JSON 格式。

4.  **测试与验证**
    - 运行脚本，验证是否返回 200 OK。
    - 检查截图，确认为移动端渲染且无验证码遮挡。

### 3.2 资源消耗评估
- **单实例内存**：约 200-300MB (Headless Chromium)。
- **速度**：单页加载约 3-8 秒（包含随机延时）。
- **成功率预期**：>95% (配合住宅 IP)。

---

## 4. 关键代码逻辑预演

```python
# 移动端设备模拟配置
iphone_13 = playwright.devices['iPhone 13']
browser = await playwright.chromium.launch(headless=True)
context = await browser.new_context(
    **iphone_13,
    locale='zh-CN',
    timezone_id='Asia/Shanghai'
)

# 注入反检测脚本
await context.add_init_script(path="stealth.min.js")

# 行为模拟：随机滚动
async def human_scroll(page):
    for _ in range(random.randint(3, 6)):
        await page.mouse.wheel(0, random.randint(300, 800))
        await asyncio.sleep(random.uniform(0.5, 1.5))
```

此方案虽然牺牲了部分速度，但能最大程度保证数据获取的稳定性，符合“即使执行速度较慢也可以接受”的需求。
