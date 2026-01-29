import { OKOOO_CRAWLER_CONFIG } from '@/common/constants';

interface CapturedRequest {
  url: string;
  matchId: string;
  timestamp: number;
}

export class OkoooNetworkMonitor {
  private monitoredTabs: Set<number> = new Set();
  private capturedRequests: Map<string, CapturedRequest> = new Map(); // requestId -> info
  private static instance: OkoooNetworkMonitor;

  constructor() {
    // 绑定事件监听器
    chrome.debugger.onEvent.addListener(this.handleDebuggerEvent.bind(this));
    chrome.debugger.onDetach.addListener(this.handleDebuggerDetach.bind(this));
  }

  public static getInstance(): OkoooNetworkMonitor {
    if (!OkoooNetworkMonitor.instance) {
      OkoooNetworkMonitor.instance = new OkoooNetworkMonitor();
    }
    return OkoooNetworkMonitor.instance;
  }

  /**
   * 开始监听指定标签页
   */
  public async attach(tabId: number): Promise<boolean> {
    if (this.monitoredTabs.has(tabId)) {
      console.log(`[OkoooMonitor] 已经在监听标签页 ${tabId}`);
      return true;
    }

    try {
      await chrome.debugger.attach({ tabId }, '1.3');
      await chrome.debugger.sendCommand({ tabId }, 'Network.enable');
      this.monitoredTabs.add(tabId);
      console.log(`[OkoooMonitor] 开始监听标签页 ${tabId}`);
      return true;
    } catch (error) {
      console.error(`[OkoooMonitor] 无法附加到标签页 ${tabId}:`, error);
      // 如果已经附加（可能是其他工具），尝试复用？
      // 通常 debugger 只能被一个 extension 独占。
      return false;
    }
  }

  /**
   * 停止监听指定标签页
   */
  public async detach(tabId: number): Promise<void> {
    if (!this.monitoredTabs.has(tabId)) return;

    try {
      await chrome.debugger.detach({ tabId });
    } catch (error) {
      // 忽略 detach 错误（可能已经关闭）
    }
    this.monitoredTabs.delete(tabId);
    this.cleanupRequestsForTab(tabId); // 清理该 tab 相关的请求缓存（如果需要）
    console.log(`[OkoooMonitor] 停止监听标签页 ${tabId}`);
  }

  private handleDebuggerDetach(source: chrome.debugger.Debuggee, reason: string) {
    if (source.tabId && this.monitoredTabs.has(source.tabId)) {
      console.log(`[OkoooMonitor] 调试器意外断开 ${source.tabId}: ${reason}`);
      this.monitoredTabs.delete(source.tabId);
    }
  }

  private async handleDebuggerEvent(source: chrome.debugger.Debuggee, method: string, params: any) {
    if (!source.tabId || !this.monitoredTabs.has(source.tabId)) return;

    const tabId = source.tabId;

    if (method === 'Network.responseReceived') {
      this.handleResponseReceived(params);
    } else if (method === 'Network.loadingFinished') {
      await this.handleLoadingFinished(tabId, params);
    }
  }

  private handleResponseReceived(params: any) {
    const { requestId, response } = params;
    const url = response.url as string;

    // 过滤目标 URL: https://m.okooo.com/match/
    // 排除静态资源等干扰
    if (url.startsWith('https://m.okooo.com/match/') && !this.isStaticResource(url)) {
      // 提取 match_id
      const matchId = this.extractMatchId(url);
      if (matchId) {
        console.log(`[OkoooMonitor] 捕获到目标请求: ${url}`);
        this.capturedRequests.set(requestId, {
          url,
          matchId,
          timestamp: Date.now()
        });
      }
    }
  }

  private async handleLoadingFinished(tabId: number, params: any) {
    const { requestId } = params;
    const requestInfo = this.capturedRequests.get(requestId);

    if (requestInfo) {
      // 立即移除，防止重复处理
      this.capturedRequests.delete(requestId);

      try {
        // 获取响应体
        const responseBody = await chrome.debugger.sendCommand({ tabId }, 'Network.getResponseBody', { requestId });
        const body = (responseBody as any).body;
        const base64Encoded = (responseBody as any).base64Encoded;

        if (body) {
            // 如果是 base64，可能需要解码（虽然 HTML 通常不是 base64，除非压缩）
            // Chrome Network.getResponseBody 对于文本通常返回字符串。
            // 提交到后端
            await this.uploadToBackend(requestInfo, body);
        }
      } catch (error) {
        console.error(`[OkoooMonitor] 获取响应体失败 ${requestInfo.url}:`, error);
      }
    }
  }

  private async uploadToBackend(info: CapturedRequest, html: string) {
    const cleanedHtml = this.cleanHtml(html);
    try {
      const dateStr = new Date().toISOString().split('T')[0];
      const response = await fetch(
        `${OKOOO_CRAWLER_CONFIG.API_BASE_URL}/api/v1/okooo/save-match-html`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            html: cleanedHtml,
            url: info.url,
            match_id: info.matchId,
            captured_at: new Date().toISOString(),
            date: dateStr
          })
        }
      );

      if (response.ok) {
        console.log(`[OkoooMonitor] ✓ 已上传: ${info.matchId}`);
      } else {
        console.error(`[OkoooMonitor] 上传失败: ${response.statusText}`);
      }
    } catch (error) {
      console.error(`[OkoooMonitor] 上传异常:`, error);
    }
  }

  /**
   * 清洗 HTML 内容
   * 1. 去除多余的空白字符
   * 2. 确保内容不为空
   */
  private cleanHtml(html: string): string {
    if (!html) return '';
    // 这里可以添加更多的清洗逻辑，例如移除某些无用的标签
    // 目前仅做简单的空白字符处理，保留原始结构以便后续提取数据
    return html.trim();
  }

  private extractMatchId(url: string): string | null {
    // URL 格式: https://m.okooo.com/match/1143895/
    // 或者带参数
    const match = url.match(/\/match\/(\d+)/);
    return match ? match[1] : null;
  }

  private isStaticResource(url: string): boolean {
    const extensions = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.woff', '.ttf'];
    return extensions.some(ext => url.toLowerCase().includes(ext));
  }

  private cleanupRequestsForTab(tabId: number) {
      // 简单清理：实际场景中 requestId 是全局唯一的吗？
      // 在 Chrome Protocol 中 requestId 是唯一的 per session?
      // 这里为了简单，暂不遍历清理 map，依赖 handleLoadingFinished 的自动清理。
      // 可以添加定期清理超时请求的逻辑。
  }
}

export const okoooNetworkMonitor = OkoooNetworkMonitor.getInstance();
