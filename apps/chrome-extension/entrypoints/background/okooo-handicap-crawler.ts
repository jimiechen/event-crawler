import { OKOOO_CRAWLER_CONFIG } from '@/common/constants';
import { BACKEND_CONFIG } from './tonghuashun-data-handler';

interface HandicapResult {
  matchId: string;
  url: string;
  html: string;
  status: 'pending' | 'success' | 'error';
  error?: string;
}

interface HandicapCrawlerStats {
  isRunning: boolean;
  phase: 'idle' | 'query' | 'processing' | 'completed';
  totalCount: number;
  currentIndex: number;
  successCount: number;
  errorCount: number;
  results: HandicapResult[];
}

interface MatchData {
  match_id: string;
  url: string;
  [key: string]: any;
}

class OkoooHandicapCrawler {
  private isRunning: boolean = false;
  private tabId: number | null = null;
  private stats: HandicapCrawlerStats = this.getInitialStats();
  private templateUrl: string = 'https://m.okooo.com/match/handicap.php?MatchID={MATCH_ID}&from=%2Fjczq%2F';

  private getInitialStats(): HandicapCrawlerStats {
    return {
      isRunning: false,
      phase: 'idle',
      totalCount: 0,
      currentIndex: 0,
      successCount: 0,
      errorCount: 0,
      results: []
    };
  }

  private reset(): void {
    this.isRunning = false;
    this.tabId = null;
    this.stats = this.getInitialStats();
  }

  async start(): Promise<{ success: boolean; message: string; total: number }> {
    console.log('[OkoooHandicapCrawler] start() 被调用');
    this.reset();
    this.isRunning = true;
    this.stats.isRunning = true;
    this.stats.phase = 'query';

    try {
      console.log('[OkoooHandicapCrawler] 开始爬取让球盘页面...');

      // Step 1: 从数据库查询获取 match_id 和 url
      console.log('[OkoooHandicapCrawler] 执行 SQL 查询...');
      const queryResult = await this.queryMatchData();
      
      if (!queryResult.success || queryResult.data.length === 0) {
        console.log('[OkoooHandicapCrawler] 未找到匹配的数据');
        this.isRunning = false;
        return { success: false, message: '未找到匹配的数据', total: 0 };
      }

      this.stats.totalCount = queryResult.data.length;
      this.stats.results = queryResult.data.map((item: any) => ({
        matchId: item.match_id || item.MatchID || item.matchId,
        url: item.url || '',
        html: '',
        status: 'pending' as const
      }));

      console.log(`[OkoooHandicapCrawler] 找到 ${this.stats.totalCount} 条记录`);
      this.stats.phase = 'processing';

      // Step 2-6: 遍历处理每个比赛
      await this.processAllHandicapPages();

      this.isRunning = false;
      this.stats.phase = 'completed';
      this.stats.isRunning = false;

      const message = `完成！成功: ${this.stats.successCount}, 失败: ${this.stats.errorCount}`;
      console.log(`[OkoooHandicapCrawler] ${message}`);

      return {
        success: this.stats.errorCount === 0,
        message,
        total: this.stats.totalCount
      };

    } catch (error) {
      console.error('[OkoooHandicapCrawler] 爬取出错:', error);
      this.isRunning = false;
      this.stats.isRunning = false;
      this.stats.phase = 'completed';
      return { success: false, message: String(error), total: 0 };
    }
  }

  // Step 1: 从数据库查询获取数据
  private async queryMatchData(): Promise<{ success: boolean; data: MatchData[] }> {
    try {
      const response = await fetch(
        `${BACKEND_CONFIG.baseUrl}/api/v1/okooo/query-matches`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sql: 'select * from test_pages where parent_id = 4;',
            limit: 100
          })
        }
      );

      if (response.ok) {
        const result = await response.json();
        console.log(`[OkoooHandicapCrawler] 查询到 ${result.data?.length || 0} 条记录`);
        return { success: true, data: result.data || [] };
      }

      return { success: false, data: [] };
    } catch (error) {
      console.error('[OkoooHandicapCrawler] SQL 查询失败:', error);
      return { success: false, data: [] };
    }
  }

  // Step 2-6: 处理所有让球盘页面
  private async processAllHandicapPages(): Promise<void> {
    for (let i = 0; i < this.stats.results.length; i++) {
      if (!this.isRunning) break;

      this.stats.currentIndex = i;
      const result = this.stats.results[i];

      console.log(`[OkoooHandicapCrawler] === 处理 ${i + 1}/${this.stats.totalCount}: ${result.matchId} ===`);

      try {
        // Step 2: 生成 URL
        const targetUrl = this.generateHandicapUrl(result.matchId);
        console.log(`[OkoooHandicapCrawler] 目标 URL: ${targetUrl}`);

        // Step 3: 在新标签页打开
        console.log(`[OkoooHandicapCrawler] 打开新标签页...`);
        const newTab = await chrome.tabs.create({ url: targetUrl, active: false });
        this.tabId = newTab.id!;

        // Step 4: 等待页面加载
        console.log(`[OkoooHandicapCrawler] 等待页面加载...`);
        await this.waitForPageLoad(this.tabId);
        await this.waitForDOMContentLoaded(this.tabId);
        await this.wait(OKOOO_CRAWLER_CONFIG.CONTENT_WAIT * 2);

        // Step 5: 捕获页面 HTML
        console.log(`[OkoooHandicapCrawler] 捕获页面 HTML...`);
        const htmlContent = await this.capturePageHtml();

        if (htmlContent) {
          // Step 6: 发送到服务端保存
          console.log(`[OkoooHandicapCrawler] 保存到服务端...`);
          const saved = await this.saveHandicapToServer(result.matchId, htmlContent, targetUrl);
          
          if (saved) {
            result.status = 'success';
            result.html = htmlContent.substring(0, 1000); // 保存部分内容用于参考
            this.stats.successCount++;
            console.log(`[OkoooHandicapCrawler] ✓ 保存成功`);
          } else {
            result.status = 'error';
            result.error = '保存失败';
            this.stats.errorCount++;
          }
        } else {
          result.status = 'error';
          result.error = '无法获取页面 HTML';
          this.stats.errorCount++;
        }

      } catch (error) {
        console.error(`[OkoooHandicapCrawler] 处理失败:`, error);
        result.status = 'error';
        result.error = String(error);
        this.stats.errorCount++;
      }

      // 关闭当前标签页
      if (this.tabId) {
        try {
          await chrome.tabs.remove(this.tabId);
        } catch (e) { /* ignore */ }
        this.tabId = null;
      }

      // 延迟再处理下一个
      await this.wait(OKOOO_CRAWLER_CONFIG.UPLOAD_DELAY);
    }
  }

  // 生成让球盘 URL
  private generateHandicapUrl(matchId: string): string {
    return this.templateUrl.replace('{MATCH_ID}', matchId);
  }

  // 等待页面加载完成
  private async waitForPageLoad(tabId: number): Promise<void> {
    return new Promise((resolve) => {
      const listener = (tabId_: number, info: any) => {
        if (tabId_ === tabId && info.status === 'complete') {
          chrome.tabs.onUpdated.removeListener(listener);
          resolve();
        }
      };
      chrome.tabs.onUpdated.addListener(listener);

      setTimeout(() => {
        chrome.tabs.onUpdated.removeListener(listener);
        resolve();
      }, 15000);
    });
  }

  // 等待 DOMContentLoaded 事件
  private async waitForDOMContentLoaded(tabId: number): Promise<void> {
    try {
      const [result] = await chrome.scripting.executeScript({
        target: { tabId },
        func: () => {
          return new Promise<boolean>((resolve) => {
            if (document.readyState === 'complete') {
              resolve(true);
              return;
            }
            const handler = () => {
              if (document.readyState === 'complete') {
                document.removeEventListener('DOMContentLoaded', handler);
                resolve(true);
              }
            };
            document.addEventListener('DOMContentLoaded', handler);
            setTimeout(() => {
              document.removeEventListener('DOMContentLoaded', handler);
              resolve(document.readyState === 'complete');
            }, 10000);
          });
        }
      });
      console.log(`[OkoooHandicapCrawler] DOMContentLoaded: ${(result as any)?.result}`);
    } catch (error) {
      console.log(`[OkoooHandicapCrawler] 等待 DOMContentLoaded 超时`);
    }
  }

  // 捕获页面 HTML
  private async capturePageHtml(): Promise<string | null> {
    if (!this.tabId) return null;

    try {
      // 方式1: 通过 messaging
      let htmlContent: string | null = null;

      try {
        htmlContent = await this.getPageHtmlViaMessage();
      } catch { /* ignore */ }

      // 方式2: executeScript 备用
      if (!htmlContent) {
        const [result] = await chrome.scripting.executeScript({
          target: { tabId: this.tabId },
          func: () => document.documentElement.outerHTML
        });
        htmlContent = (result as any)?.result || null;
      }

      if (htmlContent) {
        console.log(`[OkoooHandicapCrawler] 捕获 HTML 大小: ${htmlContent.length}`);
      }

      return htmlContent;
    } catch (error) {
      console.error('[OkoooHandicapCrawler] 捕获 HTML 失败:', error);
      return null;
    }
  }

  // 通过 Chrome messaging 获取页面 HTML
  private async getPageHtmlViaMessage(): Promise<string | null> {
    if (!this.tabId) return null;

    return new Promise((resolve) => {
      const TIMEOUT = 5000;

      const messageHandler = (message: any, sender: chrome.runtime.MessageSender) => {
        if (sender.tab?.id === this.tabId && message?.type === 'PAGE_HTML') {
          chrome.runtime.onMessage.removeListener(messageHandler);
          clearTimeout(timeout);
          resolve(message.html || null);
        }
      };

      const timeout = setTimeout(() => {
        chrome.runtime.onMessage.removeListener(messageHandler);
        resolve(null);
      }, TIMEOUT);

      chrome.runtime.onMessage.addListener(messageHandler);

      chrome.tabs.sendMessage(this.tabId!, { type: 'GET_PAGE_HTML' }).catch(() => {
        clearTimeout(timeout);
        chrome.runtime.onMessage.removeListener(messageHandler);
        resolve(null);
      });
    });
  }

  // 保存到服务端
  private async saveHandicapToServer(matchId: string, html: string, url: string): Promise<boolean> {
    try {
      const dateStr = new Date().toISOString().split('T')[0];

      const response = await fetch(
        `${BACKEND_CONFIG.baseUrl}/api/v1/okooo/save-handicap-html`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            html: html,
            url: url,
            match_id: matchId,
            captured_at: new Date().toISOString(),
            date: dateStr
          })
        }
      );

      if (response.ok) {
        console.log(`[OkoooHandicapCrawler] ✓ 保存成功: ${matchId}`);
        return true;
      }

      console.error(`[OkoooHandicapCrawler] 保存失败: ${response.status}`);
      return false;
    } catch (error) {
      console.error('[OkoooHandicapCrawler] 保存出错:', error);
      return false;
    }
  }

  // 通用等待
  private async wait(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // 获取当前状态
  getStats(): HandicapCrawlerStats {
    return { ...this.stats };
  }

  // 停止爬虫
  stop(): void {
    console.log('[OkoooHandicapCrawler] 停止爬虫');
    this.isRunning = false;
    this.stats.isRunning = false;
  }
}

export const okoooHandicapCrawler = new OkoooHandicapCrawler();
