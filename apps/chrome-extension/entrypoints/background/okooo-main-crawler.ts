import { OKOOO_CRAWLER_CONFIG } from '@/common/constants';
import { BACKEND_CONFIG } from './tonghuashun-data-handler';
import { okoooNetworkMonitor } from './okooo-network-monitor';

interface CrawlerTask {
  matchId: string;
  homeTeam?: string;
  awayTeam?: string;
  pageType: string;
  url: string;
  status: 'pending' | 'success' | 'error';
  error?: string;
}

interface CrawlerStats {
  isRunning: boolean;
  phase: 'idle' | 'initializing' | 'crawling' | 'paused' | 'completed';
  totalTasks: number;
  currentTaskIndex: number;
  successCount: number;
  errorCount: number;
  currentTask?: CrawlerTask;
  logs: string[];
  results?: Array<{
    matchId: string;
    url: string;
    status: 'pending' | 'success' | 'error';
  }>;
}

export class OkoooMainCrawler {
  private isRunning: boolean = false;
  private isPaused: boolean = false;
  private tabId: number | null = null;
  private taskQueue: CrawlerTask[] = [];
  private currentTaskIndex: number = 0;
  private stats: CrawlerStats = this.getInitialStats();
  private readonly MAX_LOGS = 100;

  private getInitialStats(): CrawlerStats {
    return {
      isRunning: false,
      phase: 'idle',
      totalTasks: 0,
      currentTaskIndex: 0,
      successCount: 0,
      errorCount: 0,
      logs: [],
      results: []
    };
  }

  private async addLog(message: string, level: string = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const logStr = `[${timestamp}] ${message}`;
    
    // 1. 本地日志
    console.log(`[OkoooCrawler] ${message}`);
    this.stats.logs.unshift(logStr);
    if (this.stats.logs.length > this.MAX_LOGS) {
      this.stats.logs.pop();
    }

    // 2. 发送给 Sidepanel (通过 Runtime Message，可选)
    // chrome.runtime.sendMessage({ type: 'OKOOO_LOG', data: { message, level, timestamp } }).catch(() => {});

    // 3. 发送给 Backend (SSE 广播)
    try {
      await fetch(`${BACKEND_CONFIG.baseUrl}/api/v1/okooo/log`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          level: level,
          timestamp: timestamp
        })
      });
    } catch (e) {
      console.error('Failed to send log to backend:', e);
    }
  }

  async start(): Promise<{ success: boolean; message: string }> {
    this.addLog('🚀 爬虫启动 - 任务队列模式');
    this.reset();
    
    try {
      this.stats.phase = 'initializing';
      this.isRunning = true;
      this.stats.isRunning = true;

      // 1. 获取入口页面，解析 MatchID
      this.addLog('正在打开入口页面解析 MatchID...');
      this.tabId = await this.getOrCreateTab(OKOOO_CRAWLER_CONFIG.ENTRY_URL);
      if (!this.tabId) {
        throw new Error('无法创建标签页');
      }

      await this.wait(3000); // 等待页面加载
      const matches = await this.extractMatchInfo();
      if (matches.length === 0) {
        throw new Error('未解析到任何比赛ID');
      }
      this.addLog(`解析到 ${matches.length} 场比赛`);

      // 2. 从后端获取页面模板
      this.addLog('正在从后端获取页面模板...');
      const templates = await this.fetchTemplatesFromBackend();
      if (templates.length === 0) {
        throw new Error('未获取到页面模板');
      }
      this.addLog(`获取到 ${templates.length} 个页面模板`);

      // 3. 生成任务队列
      this.generateTaskQueue(matches, templates);
      this.addLog(`生成任务队列完成，共 ${this.taskQueue.length} 个任务`);

      // 4. 开始执行队列
      this.stats.phase = 'crawling';
      this.processTaskQueue();

      return { success: true, message: `开始爬取，共 ${this.taskQueue.length} 个任务` };
    } catch (error) {
      this.isRunning = false;
      this.stats.isRunning = false;
      this.stats.phase = 'idle';
      const msg = error instanceof Error ? error.message : String(error);
      this.addLog(`❌ 启动失败: ${msg}`, 'error');
      return { success: false, message: msg };
    }
  }

  async startWithIds(ids: string[]): Promise<{ success: boolean; message: string }> {
    this.addLog(`🚀 修复模式启动 - 处理 ${ids.length} 个比赛`);
    this.reset();
    
    try {
      this.stats.phase = 'initializing';
      this.isRunning = true;
      this.stats.isRunning = true;

      // 1. 获取入口页面（实际上只是为了拿 Tab ID）
      this.addLog('正在打开/获取标签页...');
      this.tabId = await this.getOrCreateTab(OKOOO_CRAWLER_CONFIG.ENTRY_URL);
      if (!this.tabId) {
        throw new Error('无法创建标签页');
      }

      // 2. 构造初始 Matches (home/away 未知)
      const matches = ids.map(id => ({ id, home: '未知主队', away: '未知客队' }));
      this.addLog(`准备修复 ${matches.length} 场比赛`);

      // 3. 从后端获取页面模板
      this.addLog('正在从后端获取页面模板...');
      const templates = await this.fetchTemplatesFromBackend();
      if (templates.length === 0) {
        throw new Error('未获取到页面模板');
      }
      this.addLog(`获取到 ${templates.length} 个页面模板`);

      // 4. 生成任务队列
      this.generateTaskQueue(matches, templates);
      this.addLog(`生成任务队列完成，共 ${this.taskQueue.length} 个任务`);

      // 5. 开始执行队列
      this.stats.phase = 'crawling';
      this.processTaskQueue();

      return { success: true, message: `开始修复，共 ${this.taskQueue.length} 个任务` };
    } catch (error) {
      this.isRunning = false;
      this.stats.isRunning = false;
      this.stats.phase = 'idle';
      const msg = error instanceof Error ? error.message : String(error);
      this.addLog(`❌ 启动失败: ${msg}`, 'error');
      return { success: false, message: msg };
    }
  }

  async startWithTasks(tasks: CrawlerTask[]): Promise<{ success: boolean; message: string }> {
    this.addLog(`🚀 修复模式启动 (Direct Tasks) - 接收到 ${tasks.length} 个任务`);
    this.reset();
    
    try {
      this.stats.phase = 'initializing';
      this.isRunning = true;
      this.stats.isRunning = true;

      // 1. 获取入口页面（实际上只是为了拿 Tab ID）
      this.addLog('正在打开/获取标签页...');
      this.tabId = await this.getOrCreateTab(OKOOO_CRAWLER_CONFIG.ENTRY_URL);
      if (!this.tabId) {
        throw new Error('无法创建标签页');
      }

      // 2. 直接使用传入的任务队列
      this.taskQueue = tasks.map(t => ({
          ...t,
          status: 'pending',
          homeTeam: t.homeTeam || '未知主队',
          awayTeam: t.awayTeam || '未知客队'
      }));
      this.stats.totalTasks = this.taskQueue.length;
      this.addLog(`任务队列准备就绪，共 ${this.taskQueue.length} 个任务`);

      // 3. 开始执行队列
      this.stats.phase = 'crawling';
      this.processTaskQueue();

      return { success: true, message: `开始修复，共 ${this.taskQueue.length} 个任务` };
    } catch (error) {
      this.isRunning = false;
      this.stats.isRunning = false;
      this.stats.phase = 'idle';
      const msg = error instanceof Error ? error.message : String(error);
      this.addLog(`❌ 启动失败: ${msg}`, 'error');
      return { success: false, message: msg };
    }
  }

  private async extractMatchInfo(): Promise<{id: string, home: string, away: string}[]> {
    try {
      const [result] = await chrome.scripting.executeScript({
        target: { tabId: this.tabId! },
        func: () => {
          // 尝试解析页面上的比赛信息
          const matches: {id: string, home: string, away: string}[] = [];
          
          // 策略A: 查找特定链接模式 (最通用)
          const links = document.querySelectorAll('a[href*="MatchID="]');
          links.forEach(link => {
            const href = link.getAttribute('href');
            const match = href?.match(/MatchID=(\d+)/);
            if (match && match[1]) {
              // 尝试找附近的队名
              // 通常结构: <a> <span>Home</span> vs <span>Away</span> </a>
              let home = '主队';
              let away = '客队';
              
              // 简单尝试获取文本
              const text = link.textContent || '';
              if (text.includes('vs')) {
                 const parts = text.split('vs');
                 home = parts[0].trim();
                 away = parts[1].trim();
              }
              
              matches.push({ id: match[1], home, away });
            }
          });
          
          // 如果策略A没找到，尝试策略B (data attributes)
          if (matches.length === 0) {
              const elements = document.querySelectorAll('[data-id], [data-matchid]');
              elements.forEach(el => {
                const id = el.getAttribute('data-id') || el.getAttribute('data-matchid');
                if (id && /^\d+$/.test(id)) {
                  matches.push({ id, home: '主队', away: '客队' });
                }
              });
          }

          // 去重
          const unique = new Map();
          matches.forEach(m => unique.set(m.id, m));
          return Array.from(unique.values());
        }
      });
      return (result as any)?.result || [];
    } catch (e) {
      this.addLog(`提取MatchID失败: ${e}`, 'error');
      return [];
    }
  }

  private async fetchTemplatesFromBackend(): Promise<any[]> {
    try {
      const response = await fetch(`${BACKEND_CONFIG.baseUrl}/api/v1/okooo/query-matches`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sql: "select * from test_pages where parent_id = 4"
        })
      });
      
      const data = await response.json();
      if (data.success && Array.isArray(data.data)) {
        return data.data;
      }
      return [];
    } catch (error) {
      this.addLog(`获取模板异常: ${error}`, 'error');
      return [];
    }
  }

  private generateTaskQueue(matches: {id: string, home: string, away: string}[], templates: any[]) {
    this.taskQueue = [];
    
    for (const match of matches) {
      for (const t of templates) {
        let url = t.url;
        // 构造 URL
        if (url && url.includes('{MatchID}')) {
          url = url.replace('{MatchID}', match.id);
        } else if (t.name === '欧赔' || (t.url && t.url.includes('op'))) {
            url = `https://m.okooo.com/match/op.php?MatchID=${match.id}`;
        } else if (t.name === '亚盘' || (t.url && t.url.includes('yp'))) {
            url = `https://m.okooo.com/match/yp.php?MatchID=${match.id}`;
        } else if (t.name === '战绩' || t.name === '历史' || (t.url && t.url.includes('history'))) {
            url = `https://m.okooo.com/match/history.php?MatchID=${match.id}`;
        } else {
            // 默认拼接
            if (url.includes('?')) {
                url = `${url}&MatchID=${match.id}`;
            } else {
                url = `${url}?MatchID=${match.id}`;
            }
        }

        this.taskQueue.push({
          matchId: match.id,
          homeTeam: match.home,
          awayTeam: match.away,
          pageType: t.name || '未知',
          url,
          status: 'pending'
        });
      }
    }
    
    this.stats.totalTasks = this.taskQueue.length;
  }

  private async processTaskQueue() {
    if (!this.isRunning) return;

    if (this.currentTaskIndex >= this.taskQueue.length) {
      this.stats.phase = 'completed';
      this.isRunning = false;
      this.stats.isRunning = false;
      this.addLog('🏁 所有任务完成');
      return;
    }

    const task = this.taskQueue[this.currentTaskIndex];
    this.stats.currentTask = task;
    this.stats.currentTaskIndex = this.currentTaskIndex;
    
    const teamInfo = task.homeTeam && task.awayTeam ? `(${task.homeTeam} VS ${task.awayTeam})` : '';
    this.addLog(`▶️ [${this.currentTaskIndex + 1}/${this.stats.totalTasks}] ID:${task.matchId} ${teamInfo} - 爬取 [${task.pageType}]`);

    try {
      // 1. 打开 URL
      await chrome.tabs.update(this.tabId!, { url: task.url });
      
      // 2. 等待加载
      await this.wait(2000); // 基础等待
      await this.waitForPageLoad(this.tabId!);
      
      // 3. 检查验证码
      await this.checkCaptchaAndPause();
      if (!this.isRunning) return; // 如果在暂停期间被停止

      // 4. 再次确认内容加载 (防止空白页)
      const hasContent = await this.checkPageHasContent();
      if (!hasContent) {
        this.addLog(`⚠️ 页面内容为空，重试一次...`, 'warning');
        await chrome.tabs.reload(this.tabId!);
        await this.wait(3000);
        await this.checkCaptchaAndPause();
      }

      // 5. 捕获并保存
      const html = await this.getPageHtml();
      await this.saveHtmlToBackend(task, html);
      
      task.status = 'success';
      this.stats.successCount++;
      // Log success is handled in saveHtmlToBackend

    } catch (error) {
      task.status = 'error';
      task.error = String(error);
      this.stats.errorCount++;
      this.addLog(`❌ 任务失败: ${error}`, 'error');
    }

    // 继续下一个
    this.currentTaskIndex++;
    if (this.isRunning) {
      setTimeout(() => this.processTaskQueue(), 1500); // 间隔1.5秒
    }
  }

  private async checkCaptchaAndPause() {
    let isCaptcha = await this.isCaptchaPage();
    if (isCaptcha) {
      this.isPaused = true;
      this.stats.phase = 'paused';
      this.addLog('🛑 检测到验证码，爬虫已暂停，请手动处理验证码...', 'warning');
      
      // 通知 Sidepanel 显示验证码提示
      chrome.runtime.sendMessage({ type: 'OKOOO_CAPTCHA_DETECTED' }).catch(() => {});

      while (isCaptcha && this.isRunning) {
        await this.wait(3000);
        isCaptcha = await this.isCaptchaPage();
        if (!isCaptcha) {
          this.addLog('✅ 验证码已通过，继续爬取');
          this.isPaused = false;
          this.stats.phase = 'crawling';
          // 通知 Sidepanel 验证码已解决
          chrome.runtime.sendMessage({ type: 'OKOOO_CAPTCHA_SOLVED' }).catch(() => {});
          await this.wait(2000);
        }
      }
    }
  }

  private async isCaptchaPage(): Promise<boolean> {
    try {
      const [result] = await chrome.scripting.executeScript({
        target: { tabId: this.tabId! },
        func: () => {
          const html = document.body.innerHTML;
          return html.includes('滑动验证') || 
                 html.includes('aliyun_waf') || 
                 html.includes('访问验证');
        }
      });
      return (result as any)?.result || false;
    } catch {
      return false;
    }
  }

  private async getPageHtml(): Promise<string> {
    const [result] = await chrome.scripting.executeScript({
      target: { tabId: this.tabId! },
      func: () => document.documentElement.outerHTML
    });
    return (result as any)?.result || '';
  }

  private async saveHtmlToBackend(task: CrawlerTask, html: string) {
    let apiUrl = '/api/v1/okooo/save-match-html';
    let body: any = {
      html,
      url: task.url,
      match_id: task.matchId,
      page_type: task.pageType,
      captured_at: new Date().toISOString(),
      date: new Date().toISOString().split('T')[0]
    };

    if (task.pageType.includes('历史') || task.pageType.includes('战绩') || task.pageType === 'history') {
      apiUrl = '/api/v1/okooo/save-history-html';
      body.parent_match_id = task.matchId; 
    } else if (task.pageType.includes('列表') || task.pageType === 'list') {
      apiUrl = '/api/v1/okooo/save-list-html';
    }

    try {
      const response = await fetch(`${BACKEND_CONFIG.baseUrl}${apiUrl}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const resData = await response.json();
      const savePath = resData.data?.save_path || resData.data?.path || '未知路径';
      this.addLog(`✓ 保存成功: ${savePath}`);
      
    } catch (e) {
      throw new Error(`保存失败: ${e}`);
    }
  }

  async stop(): Promise<void> {
    this.isRunning = false;
    this.stats.isRunning = false;
    this.stats.phase = 'idle';
    this.addLog('⏹️ 爬虫已停止');
  }

  getStatus(): CrawlerStats {
    // 实时构建 results 列表
    this.stats.results = this.taskQueue.map(task => ({
      matchId: task.matchId,
      url: task.url,
      status: task.status
    }));
    return this.stats;
  }

  private reset(): void {
    this.isRunning = false;
    this.isPaused = false;
    this.taskQueue = [];
    this.currentTaskIndex = 0;
    this.stats = this.getInitialStats();
  }

  private async getOrCreateTab(url: string): Promise<number | null> {
    const tabs = await chrome.tabs.query({ url: '*://m.okooo.com/*' });
    if (tabs.length > 0) {
      await chrome.tabs.update(tabs[0].id!, { url, active: true });
      return tabs[0].id!;
    }
    const tab = await chrome.tabs.create({ url, active: true });
    return tab.id || null;
  }
  
  private wait(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  private async waitForPageLoad(tabId: number): Promise<void> {
    for (let i = 0; i < 30; i++) {
      try {
        const [res] = await chrome.scripting.executeScript({
          target: { tabId },
          func: () => document.readyState
        });
        if ((res as any)?.result === 'complete') return;
      } catch(e) {}
      await this.wait(500);
    }
  }
  
  private async checkPageHasContent(): Promise<boolean> {
    try {
      const [res] = await chrome.scripting.executeScript({
        target: { tabId: this.tabId! },
        func: () => document.body.innerText.length > 500
      });
      return (res as any)?.result || false;
    } catch { return false; }
  }
}

export const okoooMainCrawler = new OkoooMainCrawler();
