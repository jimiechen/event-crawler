import { OKOOO_CRAWLER_CONFIG } from '@/common/constants';
import { BACKEND_CONFIG } from './tonghuashun-data-handler';
import { okoooNetworkMonitor } from './okooo-network-monitor';

interface CrawlerTask {
  matchId: string;
  homeTeam?: string;
  awayTeam?: string;
  pageType: string;
  url: string;
  status: 'pending' | 'success' | 'error' | 'skipped';
  error?: string;
  filenamePrefix?: string;
  skipped?: boolean;
  skipReason?: string;
  date?: string;  // 日期字段，用于历史数据检查
}

interface CrawlerStats {
  isRunning: boolean;
  phase: 'idle' | 'initializing' | 'crawling' | 'paused' | 'completed';
  totalTasks: number;
  currentTaskIndex: number;
  successCount: number;
  errorCount: number;
  skippedCount: number;
  currentTask?: CrawlerTask;
  logs: string[];
  results?: Array<{
    matchId: string;
    url: string;
    status: 'pending' | 'success' | 'error' | 'skipped';
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
  private eventSource: EventSource | null = null;  // SSE连接

  // 比赛完成状态跟踪
  private matchCompletionTracker: Map<string, {
    total: number;
    completed: number;
    date: string;
    status: 'pending' | 'parsing' | 'completed' | 'error';
  }> = new Map();

  private getInitialStats(): CrawlerStats {
    return {
      isRunning: false,
      phase: 'idle',
      totalTasks: 0,
      currentTaskIndex: 0,
      successCount: 0,
      errorCount: 0,
      skippedCount: 0,
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

    // 注意: 不再发送 HTTP 请求，改为通过 SSE 接收后端推送的日志
  }

  /**
   * 建立 SSE 连接接收后端日志
   */
  private connectSSE(): void {
    // 关闭已有连接
    if (this.eventSource) {
      this.eventSource.close();
    }

    // 建立新连接
    this.eventSource = new EventSource(`${BACKEND_CONFIG.baseUrl}/api/sse/subscribe`);

    // 监听 okooo_log 事件
    this.eventSource.addEventListener('okooo_log', (event) => {
      try {
        const data = JSON.parse(event.data);
        // 将接收到的日志添加到本地
        const timestamp = new Date().toLocaleTimeString();
        const logStr = `[${timestamp}] ${data.message}`;

        this.stats.logs.unshift(logStr);
        if (this.stats.logs.length > this.MAX_LOGS) {
          this.stats.logs.pop();
        }

        console.log(`[OkoooSSE] ${data.message}`);
      } catch (e) {
        console.error('Failed to parse SSE log:', e);
      }
    });

    // 监听连接错误
    this.eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
    };

    // 监听连接打开
    this.eventSource.onopen = () => {
      console.log('SSE connection established');
    };
  }

  /**
   * 关闭 SSE 连接
   */
  private disconnectSSE(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
      console.log('SSE connection closed');
    }
  }

  async start(): Promise<{ success: boolean; message: string }> {
    this.addLog('🚀 爬虫启动 - 任务队列模式 (多入口)');
    this.reset();

    // 建立 SSE 连接
    this.connectSSE();

    try {
      this.stats.phase = 'initializing';
      this.isRunning = true;
      this.stats.isRunning = true;

      // 1. 获取所有入口点配置
      this.addLog('正在获取爬虫入口配置...');
      const entryPoints = await this.fetchEntryPoints();
      if (entryPoints.length === 0) {
        // Fallback to default if fetch fails or returns empty
        this.addLog('⚠️ 未获取到入口配置，使用默认入口', 'warning');
        entryPoints.push({ name: '默认', url: OKOOO_CRAWLER_CONFIG.ENTRY_URL });
      } else {
        this.addLog(`获取到 ${entryPoints.length} 个入口: ${entryPoints.map(e => e.name).join(', ')}`);
      }

      // 2. 遍历每个入口，收集所有 MatchID
      const allMatchesMap = new Map<string, {id: string, home: string, away: string}>();
      
      for (const entry of entryPoints) {
          if (!this.isRunning) break;
          this.addLog(`正在扫描入口: ${entry.name} (${entry.url}) ...`);
          
          this.tabId = await this.getOrCreateTab(entry.url);
          if (!this.tabId) {
            this.addLog(`❌ 无法打开入口: ${entry.name}`, 'error');
            continue;
          }

          await this.wait(3000); // 等待页面加载
          const matches = await this.extractMatchInfo();
          this.addLog(`入口 [${entry.name}] 解析到 ${matches.length} 场比赛`);
          
          matches.forEach(m => {
              // 优先保留有名字的记录
              if (!allMatchesMap.has(m.id) || (m.home !== '主队' && m.home !== '未知主队')) {
                  allMatchesMap.set(m.id, m);
              }
          });
      }

      const allMatches = Array.from(allMatchesMap.values());
      if (allMatches.length === 0) {
        throw new Error('未解析到任何比赛ID');
      }
      this.addLog(`汇总: 共解析到 ${allMatches.length} 场比赛`);

      // 3. 从后端获取页面模板
      this.addLog('正在从后端获取页面模板...');
      const templates = await this.fetchTemplatesFromBackend();
      if (templates.length === 0) {
        throw new Error('未获取到页面模板');
      }
      this.addLog(`获取到 ${templates.length} 个页面模板`);

      // 4. 生成任务队列
      this.generateTaskQueue(allMatches, templates);
      this.addLog(`生成任务队列完成，共 ${this.taskQueue.length} 个任务`);

      // 5. 开始执行队列
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

  private async fetchEntryPoints(): Promise<{name: string, url: string}[]> {
      try {
        const response = await fetch(`${BACKEND_CONFIG.baseUrl}/api/v1/okooo/entry-points`);
        const data = await response.json();
        if (data.success && Array.isArray(data.data)) {
            return data.data;
        }
        return [];
      } catch (e) {
          this.addLog(`获取入口配置失败: ${e}`, 'error');
          return [];
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

  async startWithTasks(tasks: any[]): Promise<{ success: boolean; message: string }> {
    this.addLog(`🚀 修复模式启动 (Direct Tasks) - 接收到 ${tasks.length} 个任务`);

    // 1. 预检查文件是否存在
    this.addLog('正在检查文件是否存在...');
    const checkResult = await this.checkFilesExist(tasks);

    // 过滤出需要爬取的任务，并保留原始任务的URL
    const tasksToCrawl: any[] = [];
    const skippedTasks: any[] = [];
    
    checkResult.forEach((result: any, index: number) => {
      const originalTask = tasks[index];
      if (result.skip) {
        skippedTasks.push(result);
      } else {
        // 合并检查结果和原始任务，保留所有必要字段
        tasksToCrawl.push({
          ...result,
          match_id: originalTask.match_id,
          page_type: originalTask.page_type,
          filename_prefix: originalTask.filename_prefix || originalTask.filenamePrefix,
          url: originalTask.url  // 保留原始URL
        });
      }
    });

    this.addLog(`预检查完成: ${skippedTasks.length} 个文件已存在，${tasksToCrawl.length} 个需要爬取`);

    // 显示跳过的文件
    skippedTasks.forEach((task: any) => {
      this.addLog(`⏭️ 跳过已存在: ${task.filename} (${task.size} bytes)`);
    });

    if (tasksToCrawl.length === 0) {
      return { success: true, message: '所有文件已存在，无需爬取' };
    }

    this.reset();

    try {
      // 2. 建立 SSE 连接
      this.connectSSE();

      this.stats.phase = 'initializing';
      this.isRunning = true;
      this.stats.isRunning = true;

      // 3. 获取入口页面（实际上只是为了拿 Tab ID）
      this.addLog('正在打开/获取标签页...');
      this.tabId = await this.getOrCreateTab(OKOOO_CRAWLER_CONFIG.ENTRY_URL);
      if (!this.tabId) {
        throw new Error('无法创建标签页');
      }

      // 4. 使用过滤后的任务队列
      this.taskQueue = tasksToCrawl.map((t: any) => ({
          matchId: t.match_id,
          homeTeam: '未知主队',
          awayTeam: '未知客队',
          pageType: t.page_type,
          url: t.url,  // 现在URL已正确保留
          filenamePrefix: t.filename_prefix || t.filenamePrefix,
          status: 'pending'
      }));
      this.stats.totalTasks = this.taskQueue.length;
      this.addLog(`任务队列准备就绪，共 ${this.taskQueue.length} 个任务需要爬取`);

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

  /**
   * 检查文件是否存在
   */
  private async checkFilesExist(tasks: any[]): Promise<any[]> {
    try {
      const requestBody = {
        tasks: tasks.map(t => ({
          match_id: t.match_id,
          page_type: t.page_type,
          url: t.url,
          filename_prefix: t.filename_prefix || t.filenamePrefix  // 兼容两种命名
        })),
        date: new Date().toISOString().split('T')[0]  // 当前日期
      };
      console.log('[OkoooCrawler] checkFilesExist request:', JSON.stringify(requestBody, null, 2));
      
      const response = await fetch(`${BACKEND_CONFIG.baseUrl}/api/v1/okooo/check-files-exist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();
      console.log('[OkoooCrawler] checkFilesExist response:', JSON.stringify(data, null, 2));
      
      if (data.success) {
        return data.data;
      }
      // 如果检查失败，返回所有任务都需要爬取
      return tasks.map(t => ({ ...t, skip: false }));
    } catch (e) {
      console.error('Failed to check files exist:', e);
      // 如果检查失败，返回所有任务都需要爬取
      return tasks.map(t => ({ ...t, skip: false }));
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
              let text = link.textContent || '';
              // 移除 [1] [3] 这种排名
              text = text.replace(/\[\d+\]/g, '').trim();
              
              // 检查 VS (支持大小写)
              const vsMatch = text.match(/\s*(vs|VS)\s*/i);
              if (vsMatch) {
                 const parts = text.split(vsMatch[0]);
                 if (parts.length >= 2) {
                     home = parts[0].trim();
                     away = parts[1].trim();
                 }
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
        if (url && (url.includes('{MatchID}') || url.includes('{id}'))) {
          url = url.replace(/{MatchID}|{id}/g, match.id);
        } else if (url && (url.match(/MatchID=\d+/) || url.match(/mid=\d+/))) {
           // 如果 URL 中已经包含 MatchID=数字 或 mid=数字，直接替换
           if (url.includes('MatchID=')) {
             url = url.replace(/MatchID=\d+/g, `MatchID=${match.id}`);
           }
           if (url.includes('mid=')) {
             url = url.replace(/mid=\d+/g, `mid=${match.id}`);
           }
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

        // 获取 filenamePrefix
        const filenamePrefix = t.filename_prefix || this.getFilenamePrefix(t.name, t.url);

        this.taskQueue.push({
          matchId: match.id,
          homeTeam: match.home,
          awayTeam: match.away,
          pageType: t.name || '未知',
          url,
          filenamePrefix,
          status: 'pending'
        });
      }
    }

    this.stats.totalTasks = this.taskQueue.length;

    // 初始化比赛完成状态跟踪
    this.initMatchCompletionTracker();
  }

  /**
   * 初始化比赛完成状态跟踪
   */
  private initMatchCompletionTracker() {
    this.matchCompletionTracker.clear();

    // 统计每个比赛的页面数量
    const matchPageCount: Map<string, number> = new Map();
    this.taskQueue.forEach(task => {
      const count = matchPageCount.get(task.matchId) || 0;
      matchPageCount.set(task.matchId, count + 1);
    });

    // 初始化跟踪器
    const date = new Date().toISOString().split('T')[0];
    matchPageCount.forEach((total, matchId) => {
      this.matchCompletionTracker.set(matchId, {
        total,
        completed: 0,
        date,
        status: 'pending'
      });
    });

    this.addLog(`📊 初始化比赛跟踪: ${this.matchCompletionTracker.size} 个比赛`);
  }

  /**
   * 根据页面名称或URL获取文件名前缀
   */
  private getFilenamePrefix(name: string, url: string): string {
    const nameMap: {[key: string]: string} = {
      '历史': 'history',
      '战绩': 'history',
      '欧赔': 'odds',
      '亚盘': 'handicap',
      '盈亏': 'exchanges',
      '阵容': 'form',
      '积分': 'game',
      '澳门亚盘变化': 'macao_change',
      '必发指数变化': 'bifa_change'
    };

    // 先尝试匹配名称
    if (name && nameMap[name]) {
      return nameMap[name];
    }

    // 根据URL判断
    if (url) {
      if (url.includes('history')) return 'history';
      if (url.includes('op.php') || url.includes('/odds')) return 'odds';
      if (url.includes('yp.php') || url.includes('/handicap')) return 'handicap';
      if (url.includes('exchanges')) return 'exchanges';
      if (url.includes('form')) return 'form';
      if (url.includes('game') || url.includes('table')) return 'game';
      if (url.includes('change.php') && url.includes('PID=84')) return 'macao_change';
      if (url.includes('change.php') && url.includes('PID=0')) return 'bifa_change';
    }

    // 默认使用页面名称的小写形式
    return name ? name.toLowerCase().replace(/\s+/g, '_') : 'unknown';
  }

  private async processTaskQueue() {
    if (!this.isRunning) return;

    // 任务完成检查
    if (this.currentTaskIndex >= this.taskQueue.length) {
      this.stats.phase = 'completed';
      this.isRunning = false;
      this.stats.isRunning = false;
      this.addLog('🏁 所有任务完成');
      // 广播完成状态
      this.broadcastStatus();
      
      // 发送完成事件，通知前端清空待修复列表
      chrome.runtime.sendMessage({
        type: 'OKOOO_CRAWLER_COMPLETED',
        data: {
          message: '所有任务完成',
          completedAt: new Date().toISOString(),
          totalTasks: this.stats.totalTasks,
          successCount: this.stats.successCount,
          errorCount: this.stats.errorCount
        }
      }).catch(() => {});
      
      return;
    }

    const task = this.taskQueue[this.currentTaskIndex];
    this.stats.currentTask = task;
    this.stats.currentTaskIndex = this.currentTaskIndex;
    
    // 广播状态更新
    this.broadcastStatus();
    
    const teamInfo = task.homeTeam && task.awayTeam ? `(${task.homeTeam} VS ${task.awayTeam})` : '';
    this.addLog(`▶️ [${this.currentTaskIndex + 1}/${this.stats.totalTasks}] ID:${task.matchId} ${teamInfo} - 爬取 [${task.pageType}]`);

    try {
      // 0. 检查文件是否已存在（防重复）
      const exists = await this.checkFileExists(task.matchId, task.pageType, task.date);
      if (exists) {
        this.addLog(`⏭️ 跳过已存在: ${task.matchId} [${task.pageType}]`);
        task.status = 'skipped';
        task.skipped = true;
        task.skipReason = '文件已存在';
        this.stats.skippedCount++;

        // 关键修复：跳过任务也要计入完成度，触发解析
        await this.updateMatchCompletion(task.matchId, 'skipped');

        // 继续下一个任务
        this.currentTaskIndex++;
        this.broadcastStatus();
        if (this.isRunning) {
          setTimeout(() => this.processTaskQueue(), 100);
        }
        return;
      }

      this.addLog(`🚀 [任务开始] ${task.matchId} - ${task.pageType} - ${task.url}`);

      // 1. 打开 URL 并等待页面完全加载
      this.addLog('📡 开始导航...');
      await this.navigateAndWaitForLoad(this.tabId!, task.url);
      this.addLog('✅ 导航完成');

      // 调试: 检查URL是否发生跳转
      const currentUrl = await this.getCurrentUrl();
      this.addLog(`🔍 URL检查: 目标=${task.url} 实际=${currentUrl}`);
      if (currentUrl && task.url && currentUrl.split('?')[0] !== task.url.split('?')[0]) {
         this.addLog(`⚠️ 检测到URL跳转/不一致`, 'warning');
      }

      // 3. 检查验证码
      this.addLog('🔐 检查验证码...');
      await this.checkCaptchaAndPause();
      if (!this.isRunning) {
        this.addLog('⏹️ 爬虫已停止，退出任务');
        return;
      }

      // 4. 再次确认内容加载 (防止空白页)
      this.addLog('📄 检查页面内容...');
      const hasContent = await this.checkPageHasContent();
      if (!hasContent) {
        this.addLog(`⚠️ 页面内容为空，重试一次...`, 'warning');
        await chrome.tabs.reload(this.tabId!);
        await this.wait(3000);
        await this.checkCaptchaAndPause();
      }

      // 5. 等待所有网络请求完成（再次确认）
      this.addLog('⏳ 等待网络请求完成...');
      await this.waitForNetworkIdle(this.tabId!, 5000);
      this.addLog('✅ 网络请求完成');

      // 6. 捕获并保存
      this.addLog('📥 捕获页面HTML...');
      const html = await this.getPageHtml();
      this.addLog(`📊 HTML大小: ${html.length} 字符`);

      // 7. 验证HTML内容完整性
      if (!html || html.length < 1000) {
        this.addLog(`❌ HTML内容不完整: ${html?.length || 0} 字符`, 'error');
        throw new Error('页面内容不完整，可能请求被取消');
      }

      // 8. 检查是否包含关键内容（根据页面类型）
      this.addLog('🔍 验证页面内容...');
      const isValidContent = await this.validatePageContent(task.pageType);
      if (!isValidContent) {
        this.addLog(`❌ 页面内容验证失败`, 'error');
        throw new Error('页面内容验证失败，缺少关键数据');
      }
      this.addLog('✅ 页面内容验证通过');

      // 9. 保存到后端
      this.addLog('💾 保存到后端...');
      await this.saveHtmlToBackend(task, html);
      
      task.status = 'success';
      this.stats.successCount++;
      this.addLog(`✅ [任务完成] ${task.matchId} - ${task.pageType}`);

    } catch (error) {
      task.status = 'error';
      task.error = String(error);
      this.stats.errorCount++;
      this.addLog(`❌ [任务失败] ${task.matchId} - ${task.pageType}: ${error}`, 'error');
    }

    // 更新比赛完成状态
    await this.updateMatchCompletion(task.matchId, task.status);

    // 广播状态更新
    this.broadcastStatus();

    // 继续下一个
    this.currentTaskIndex++;
    if (this.isRunning) {
      // 增加间隔时间，确保上一个页面的所有请求都已完成
      this.addLog('⏳ 等待页面完全卸载...');
      await this.wait(3000); // 等待3秒确保页面卸载完成
      setTimeout(() => this.processTaskQueue(), 1500); // 额外间隔1.5秒
    }
  }

  /**
   * 更新比赛完成状态
   * 当一个比赛的所有页面都完成时，触发解析
   */
  private async updateMatchCompletion(matchId: string, taskStatus: string) {
    const tracker = this.matchCompletionTracker.get(matchId);
    if (!tracker) return;

    // 增加完成计数（无论成功、失败还是跳过，都算完成）
    tracker.completed++;

    this.addLog(`📊 比赛 ${matchId} 进度: ${tracker.completed}/${tracker.total}`);

    // 检查是否所有页面都已完成
    if (tracker.completed >= tracker.total) {
      this.addLog(`✅ 比赛 ${matchId} 所有页面已完成，准备解析...`);
      tracker.status = 'parsing';

      // 触发解析
      await this.triggerMatchParse(matchId, tracker.date);
    }
  }

  /**
   * 触发单个比赛的解析
   */
  private async triggerMatchParse(matchId: string, date: string) {
    try {
      this.addLog(`🔍 开始解析比赛 ${matchId}...`);

      // 调用后端解析API
      const response = await fetch(
        `${BACKEND_CONFIG.baseUrl}/api/v1/okooo/parse/match/${date}/${matchId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        this.addLog(`✅ 比赛 ${matchId} 解析完成`);

        // 更新跟踪器状态
        const tracker = this.matchCompletionTracker.get(matchId);
        if (tracker) {
          tracker.status = 'completed';
        }

        // 通知前端
        chrome.runtime.sendMessage({
          type: 'OKOOO_MATCH_PARSED',
          data: {
            matchId,
            date,
            success: true,
            data: result.data
          }
        }).catch(() => {});
      } else {
        throw new Error(result.message || '解析失败');
      }
    } catch (error) {
      this.addLog(`❌ 比赛 ${matchId} 解析失败: ${error}`, 'error');

      // 更新跟踪器状态
      const tracker = this.matchCompletionTracker.get(matchId);
      if (tracker) {
        tracker.status = 'error';
      }

      // 通知前端
      chrome.runtime.sendMessage({
        type: 'OKOOO_MATCH_PARSE_ERROR',
        data: {
          matchId,
          date,
          success: false,
          error: String(error)
        }
      }).catch(() => {});
    }
  }

  /**
   * 检查文件是否已存在
   */
  private async checkFileExists(matchId: string, pageType: string, date?: string): Promise<boolean> {
    try {
      const checkDate = date || new Date().toISOString().split('T')[0];
      const response = await fetch(
        `${BACKEND_CONFIG.baseUrl}/api/v1/okooo/check-file?match_id=${matchId}&page_type=${encodeURIComponent(pageType)}&date=${checkDate}`
      );
      if (response.ok) {
        const data = await response.json();
        return data.exists === true;
      }
    } catch (e) {
      console.error('检查文件存在性失败:', e);
    }
    return false;
  }

  /**
   * 广播状态更新到所有监听者
   */
  private broadcastStatus(): void {
    const status = this.getStatus();
    
    // 1. 发送给 Sidepanel
    chrome.runtime.sendMessage({
      type: 'OKOOO_STATUS_UPDATE',
      data: status
    }).catch(() => {});

    // 2. 发送给 Popup
    chrome.runtime.sendMessage({
      type: 'OKOOO_CRAWLER_STATUS',
      data: status
    }).catch(() => {});
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
      func: () => {
        // 检查页面是否有错误提示（如请求被取消）
        const errorIndicators = [
          '请求被取消',
          '请求中断',
          '网络错误',
          '加载失败',
          'ERR_ABORTED',
          'cancelled',
          'aborted'
        ];
        
        const pageText = document.body.innerText || '';
        const hasError = errorIndicators.some(indicator => 
          pageText.includes(indicator)
        );
        
        if (hasError) {
          return { error: '页面包含错误信息', html: '' };
        }
        
        return { html: document.documentElement.outerHTML };
      }
    });
    
    const data = (result as any)?.result;
    if (data?.error) {
      throw new Error(data.error);
    }
    
    return data?.html || '';
  }

  private async saveHtmlToBackend(task: CrawlerTask, html: string) {
    let apiUrl = '/api/v1/okooo/save-match-html';
    let body: any = {
      html,
      url: task.url,
      match_id: task.matchId,
      page_type: task.pageType,
      filename_prefix: task.filenamePrefix,  // 添加文件名前缀
      captured_at: new Date().toISOString(),
      date: new Date().toISOString().split('T')[0]
    };

    if (task.pageType.includes('历史') || task.pageType.includes('战绩') || task.pageType === 'history') {
      apiUrl = '/api/v1/okooo/save-history-html';
      body.parent_match_id = task.matchId;
    } else if (task.pageType.includes('亚盘') || task.pageType === 'handicap' || task.pageType.includes('yp')) {
      apiUrl = '/api/v1/okooo/save-handicap-html';
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
    this.disconnectSSE();
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
    this.disconnectSSE();
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
    // 第一阶段：等待 document.readyState === 'complete'
    for (let i = 0; i < 30; i++) {
      try {
        const [res] = await chrome.scripting.executeScript({
          target: { tabId },
          func: () => document.readyState
        });
        if ((res as any)?.result === 'complete') break;
      } catch(e) {}
      await this.wait(500);
    }
    
    // 第二阶段：等待网络空闲（没有正在进行的请求）
    this.addLog('⏳ 等待网络请求完成...');
    await this.waitForNetworkIdle(tabId, 3000); // 等待3秒网络空闲
  }
  
  /**
   * 等待网络空闲（没有正在进行的请求）
   */
  private async waitForNetworkIdle(tabId: number, idleTime: number = 2000): Promise<void> {
    this.addLog(`[网络] 开始等待网络空闲 ${idleTime}ms...`);
    
    // 使用 Performance API 检查网络状态
    const checkNetworkIdle = async (): Promise<boolean> => {
      try {
        const [res] = await chrome.scripting.executeScript({
          target: { tabId },
          func: () => {
            // 检查是否有未完成的图片、XHR、fetch请求
            const performanceEntries = performance.getEntriesByType('resource');
            const recentEntries = performanceEntries.slice(-10); // 最近10个资源
            const now = performance.now();
            
            // 检查是否有正在进行的请求（最近100ms内开始的请求）
            const hasRecentRequests = recentEntries.some((entry: any) => {
              const startTime = entry.startTime;
              const duration = entry.duration;
              // 如果请求在100ms内开始且还未完成（duration为0或很小）
              return (now - startTime < 100) || duration === 0;
            });
            
            return !hasRecentRequests;
          }
        });
        return (res as any)?.result || false;
      } catch {
        return true; // 如果出错，假设网络已空闲
      }
    };
    
    // 连续检查网络空闲状态
    let idleCount = 0;
    const requiredIdleCount = Math.ceil(idleTime / 500); // 需要连续检查的次数
    let lastStatus = '';
    
    for (let i = 0; i < 60; i++) { // 最多等待30秒
      const isIdle = await checkNetworkIdle();
      const status = isIdle ? '空闲' : '忙碌';
      
      // 只在状态变化时打印日志
      if (status !== lastStatus) {
        this.addLog(`[网络] 状态: ${status} (检查 ${i}/${60})`);
        lastStatus = status;
      }
      
      if (isIdle) {
        idleCount++;
        if (idleCount >= requiredIdleCount) {
          this.addLog(`[网络] ✅ 网络已空闲，共检查 ${i} 次`);
          return;
        }
      } else {
        idleCount = 0; // 重置计数器
      }
      
      await this.wait(500);
    }
    
    this.addLog('[网络] ⚠️ 等待网络空闲超时，继续执行');
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

  private async getCurrentUrl(): Promise<string> {
    try {
      const tab = await chrome.tabs.get(this.tabId!);
      return tab.url || '';
    } catch { return ''; }
  }

  /**
   * 验证页面内容是否完整（根据页面类型检查关键元素）
   */
  private async validatePageContent(pageType: string): Promise<boolean> {
    try {
      const [result] = await chrome.scripting.executeScript({
        target: { tabId: this.tabId! },
        func: (type: string) => {
          const html = document.documentElement.outerHTML;
          const text = document.body.innerText || '';

          // 根据页面类型检查关键内容
          switch (true) {
            case type.includes('历史') || type.includes('战绩') || type === 'history':
              // 历史战绩页面应该包含比赛记录表格
              return html.includes('match') || html.includes('比赛') || text.includes('VS') || text.includes('vs');

            case type.includes('欧赔') || type === 'odds':
              // 欧赔页面应该包含赔率数据
              return html.includes('odds') || text.includes('胜') || text.includes('平') || text.includes('负');

            case type.includes('亚盘') || type === 'handicap':
              // 亚盘页面应该包含盘口数据
              return html.includes('handicap') || text.includes('盘口') || text.includes('让球');

            case type.includes('盈亏') || type === 'exchanges':
              // 盈亏页面应该包含指数数据
              return html.includes('exchange') || text.includes('盈亏') || text.includes('指数');

            case type.includes('阵容') || type === 'form':
              // 阵容页面应该包含球员信息
              return html.includes('player') || text.includes('阵容') || text.includes('球员');

            case type.includes('积分') || type === 'game':
              // 积分页面应该包含排名数据
              return html.includes('rank') || text.includes('排名') || text.includes('积分');

            default:
              // 默认检查：页面应该有足够的内容
              return html.length > 5000 && text.length > 200;
          }
        },
        args: [pageType]
      });

      return (result as any)?.result || false;
    } catch {
      return false;
    }
  }

  /**
   * 导航到URL并等待页面完全加载
   * 使用 chrome.tabs.onUpdated 监听加载完成事件
   */
  private async navigateAndWaitForLoad(tabId: number, url: string): Promise<void> {
    this.addLog(`[导航] 开始导航到: ${url}`);
    
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.addLog('[导航] ❌ 60秒超时', 'error');
        cleanup();
        reject(new Error('页面加载超时'));
      }, 60000); // 60秒超时

      let isLoading = false;
      let loadStartTime = 0;

      const listener = (updatedTabId: number, changeInfo: chrome.tabs.TabChangeInfo, tab: chrome.tabs.Tab) => {
        if (updatedTabId !== tabId) return;

        this.addLog(`[导航] onUpdated: status=${changeInfo.status}, url=${tab.url?.substring(0, 50)}...`);

        // 监听加载开始
        if (changeInfo.status === 'loading') {
          isLoading = true;
          loadStartTime = Date.now();
          this.addLog('[导航] 🔄 页面开始加载...');
        }

        // 监听加载完成
        if (changeInfo.status === 'complete' && isLoading) {
          const loadTime = Date.now() - loadStartTime;
          this.addLog(`[导航] ✅ 页面加载完成，耗时 ${loadTime}ms`);
          cleanup();
          resolve();
        }
      };

      const cleanup = () => {
        clearTimeout(timeout);
        chrome.tabs.onUpdated.removeListener(listener);
      };

      // 注册监听器
      chrome.tabs.onUpdated.addListener(listener);
      this.addLog('[导航] 已注册 onUpdated 监听器');

      // 执行导航
      this.addLog(`[导航] 执行 chrome.tabs.update...`);
      chrome.tabs.update(tabId, { url }).then(() => {
        this.addLog('[导航] chrome.tabs.update 已执行');
      }).catch((err) => {
        this.addLog(`[导航] ❌ chrome.tabs.update 失败: ${err}`, 'error');
        cleanup();
        reject(err);
      });
    });
  }
}

export const okoooMainCrawler = new OkoooMainCrawler();
