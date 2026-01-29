import { OKOOO_CRAWLER_CONFIG } from '@/common/constants';
import { BACKEND_CONFIG } from './tonghuashun-data-handler';

interface CaptureResult {
  url: string;
  status: 'pending' | 'success' | 'error';
  htmlSize?: number;
  error?: string;
}

class OkoooListCrawler {
  private isCapturing: boolean = false;
  private tabId: number | null = null;
  private captureListenerId: number | null = null;
  private result: CaptureResult | null = null;

  async openAndCapture(): Promise<{ success: boolean; message: string; size?: number }> {
    this.isCapturing = true;
    this.result = null;

    // 打开比赛列表页面
    this.tabId = await this.getOrCreateTab(OKOOO_CRAWLER_CONFIG.ENTRY_URL);
    if (!this.tabId) {
      this.isCapturing = false;
      return { success: false, message: '无法创建标签页' };
    }

    // 等待页面加载
    await this.waitForPageLoad(this.tabId);
    await this.wait(OKOOO_CRAWLER_CONFIG.PAGE_LOAD_WAIT);

    // 获取页面 HTML（带重试机制）
    let htmlContent: string | null = null;
    let retries = 3;
    while (retries > 0 && !htmlContent) {
      htmlContent = await this.getPageHtmlWithRetry(this.tabId);
      if (!htmlContent) {
        retries--;
        if (retries > 0) {
          console.log(`[OkoooListCrawler] 重试获取 HTML，剩余 ${retries} 次`);
          await this.wait(2000);
        }
      }
    }
    
    if (!htmlContent) {
      this.isCapturing = false;
      return { success: false, message: '无法获取页面内容，请确保页面已加载完成' };
    }

    // 发送到后端
    const success = await this.uploadToBackend(htmlContent);
    
    this.isCapturing = false;
    
    if (success) {
      return { 
        success: true, 
        message: '比赛列表 HTML 已保存', 
        size: htmlContent.length 
      };
    } else {
      return { success: false, message: '上传失败' };
    }
  }

  private async getPageHtmlWithRetry(tabId: number): Promise<string | null> {
    try {
      // 首先尝试通过消息获取
      const result = await this.sendMessageToTab(tabId, {
        action: 'GET_PAGE_HTML'
      });
      
      if (result?.success && result.html) {
        console.log(`[OkoooListCrawler] 通过消息获取到 HTML，大小: ${result.html.length} 字符`);
        return result.html;
      }
    } catch (error) {
      console.log(`[OkoooListCrawler] 消息方式失败，尝试 executeScript: ${error}`);
    }

    // 如果消息方式失败，使用 executeScript 直接获取
    try {
      const [result] = await chrome.scripting.executeScript({
        target: { tabId: tabId },
        func: () => document.documentElement.outerHTML
      });

      if (result && (result as any).result !== undefined) {
        const html = (result as any).result as string;
        console.log(`[OkoooListCrawler] 通过 executeScript 获取到 HTML，大小: ${html.length} 字符`);
        return html;
      }
    } catch (error) {
      console.error('[OkoooListCrawler] executeScript 失败:', error);
    }

    return null;
  }

  private async uploadToBackend(htmlContent: string): Promise<boolean> {
    try {
      const dateStr = new Date().toISOString().split('T')[0];
      
      const response = await fetch(
        `${BACKEND_CONFIG.baseUrl}/api/v1/okooo/save-list-html`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            html: htmlContent,
            url: OKOOO_CRAWLER_CONFIG.ENTRY_URL,
            captured_at: new Date().toISOString(),
            date: dateStr
          })
        }
      );

      if (response.ok) {
        console.log(`[OkoooListCrawler] ✓ 上传成功，大小: ${htmlContent.length}`);
        return true;
      } else {
        console.error('[OkoooListCrawler] 上传失败:', response.statusText);
        return false;
      }
    } catch (error) {
      console.error('[OkoooListCrawler] 上传异常:', error);
      return false;
    }
  }

  async stop(): Promise<void> {
    this.isCapturing = false;
    
    if (this.captureListenerId !== null) {
      chrome.webRequest.onBeforeRequest.removeListener(this.captureListenerId as any);
      this.captureListenerId = null;
    }
  }

  getStatus(): { isCapturing: boolean; result: CaptureResult | null } {
    return {
      isCapturing: this.isCapturing,
      result: this.result
    };
  }

  private async waitForPageLoad(tabId: number): Promise<void> {
    return new Promise((resolve) => {
      const listener = (tabIdListener: number, changeInfo: chrome.tabs.TabChangeInfo) => {
        if (tabIdListener === tabId && changeInfo.status === 'complete') {
          chrome.tabs.onUpdated.removeListener(listener);
          resolve();
        }
      };
      chrome.tabs.onUpdated.addListener(listener);
      setTimeout(resolve, 15000);
    });
  }

  private async wait(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private sendMessageToTab(tabId: number, message: any): Promise<any> {
    return new Promise((resolve, reject) => {
      chrome.tabs.sendMessage(tabId, message, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve(response);
        }
      });
    });
  }

  private async getOrCreateTab(url: string): Promise<number | null> {
    const tabs = await chrome.tabs.query({ currentWindow: true });
    const existing = tabs.find(t => t.url?.includes(url.split('?')[0]));
    if (existing?.id) {
      await chrome.tabs.update(existing.id, { active: true });
      return existing.id;
    }
    const tab = await chrome.tabs.create({ url, active: true });
    return tab.id!;
  }
}

export const okoooListCrawler = new OkoooListCrawler();
