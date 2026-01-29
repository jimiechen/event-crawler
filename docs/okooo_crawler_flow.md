# 澳客爬虫流程优化方案

## 1. 核心流程概述

本方案旨在优化澳客网比赛数据的爬取流程，通过“预生成任务列表”的方式替代原有的“页面点击/Tab交互”方式，以提高稳定性和可控性。

### 主要变更点
1.  **任务生成前置**：不再依赖页面内的 Tab 点击跳转，而是预先根据 MatchID 和子页面类型生成所有目标 URL。
2.  **去交互化**：将复杂的“点击-等待-抓取”流程简化为“打开URL-等待-抓取”，避免因 DOM 变动导致的点击失败。
3.  **全程可视化**：在 Sidepanel 中实时展示总任务数、当前进度和成功/失败状态。

## 2. 数据流转图 (Mermaid)

```mermaid
sequenceDiagram
    participant User as 用户 (Sidepanel)
    participant Crawler as 爬虫脚本 (Background)
    participant Browser as 浏览器 (Tab)
    participant Backend as 后端服务 (Python)

    Note over User, Backend: 阶段一：任务初始化
    User->>Crawler: 点击 "开始自动爬取"
    Crawler->>Browser: 打开入口页 https://m.okooo.com/jczq/
    Browser-->>Crawler: 页面加载完成
    Crawler->>Browser: 提取页面所有 match_id
    Browser-->>Crawler: 返回 match_id 列表 (N个)
    
    Crawler->>Backend: 请求子页面模板 (parent_id=4)
    Backend-->>Crawler: 返回页面类型列表 (M个, 如 history, odds...)
    
    Note over Crawler: 阶段二：任务生成
    Crawler->>Crawler: 生成任务队列
    Note right of Crawler: Total = N * M (每个比赛8个页面)
    Crawler->>User: 更新 UI: 显示总任务数 (Total)

    Note over User, Backend: 阶段三：循环执行
    loop 遍历任务队列
        Crawler->>Browser: 打开目标 URL (填充 match_id)
        Browser-->>Crawler: 页面加载完成
        
        opt 检测到验证码
            Crawler->>User: 暂停并提示 "请手动验证"
            User->>Browser: 手动完成验证
            Crawler->>Browser: 检测到验证通过，继续
        end
        
        Crawler->>Browser: 获取 HTML 内容 (document.outerHTML)
        Browser-->>Crawler: 返回 HTML 字符串
        Crawler->>Backend: 上传 HTML (/save-match-html)
        Backend-->>Crawler: 保存成功确认
        
        Crawler->>User: 更新进度 (已完成/总数)
    end

    Crawler->>User: 爬取完成，显示最终统计
```

## 3. 详细步骤说明

### 步骤 1: 获取比赛 ID (Match IDs)
*   **动作**: 访问 `https://m.okooo.com/jczq/`。
*   **逻辑**: 等待页面加载，使用 DOM 选择器提取所有当日比赛的 ID。
*   **输出**: `MatchID List = [1001, 1002, ...]`

### 步骤 2: 获取页面模板
*   **动作**: 调用后端 API `/api/v1/okooo/query-matches`。
*   **参数**: `sql: "select * from test_pages where parent_id = 4"`。
*   **输出**: 子页面配置列表，包含页面类型和 URL 模板（例如 `history.php?MatchID={id}`）。

### 步骤 3: 生成任务队列
*   **逻辑**: 将每个 MatchID 与所有子页面模板进行笛卡尔积组合。
*   **结果**: 一个包含所有待爬取 URL 的扁平化数组。
    *   Task 1: Match 1001 - History
    *   Task 2: Match 1001 - Odds
    *   ...
    *   Task X: Match 1002 - History
*   **UI 更新**: 在 Sidepanel 更新“总任务数”。

### 步骤 4: 执行爬取 (循环)
*   **导航**: `chrome.tabs.update(url)`。
*   **等待**: 等待页面 `readyState === 'complete'` 且关键内容元素出现。
*   **验证码处理**:
    *   检查页面是否包含“滑动验证”、“aliyun_waf”等关键词。
    *   若存在，暂停爬虫，通过 Sidepanel 或 Alert 提示用户。
    *   轮询检查直到验证码消失。
*   **数据抓取**: 使用 `chrome.scripting.executeScript` 获取 `document.documentElement.outerHTML`。
*   **数据上传**: POST 请求发送至后端 `/save-match-html`。

### 步骤 5: 结果统计
*   Sidepanel 实时显示：
    *   **比赛进度**: `当前 MatchIndex / 总 Match 数`
    *   **页面进度**: `当前 PageIndex / 总 Page 数` (或直接显示总进度)
    *   **成功/失败**: 计数器。

## 4. 异常处理与备选方案
*   **[NetworkMonitor]**: 暂时关闭初始化日志和自动 attach 功能，作为备选方案。仅在 DOM 获取失败时启用。
*   **超时重试**: 单个页面加载超过 30秒 视为超时，记录错误并跳过（或重试 1 次）。
*   **空页面**: 若获取的 HTML 内容过短（<1000字符），标记为“待验证”或“错误”。

