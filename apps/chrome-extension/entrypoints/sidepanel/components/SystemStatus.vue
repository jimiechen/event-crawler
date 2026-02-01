<template>
  <div class="system-status-container">
    <!-- 总体健康度 -->
    <div class="status-summary" :class="overallStatusClass">
      <div class="status-icon">{{ overallStatusIcon }}</div>
      <div class="status-text">
        <h3>{{ overallStatusText }}</h3>
        <span class="last-updated">更新时间: {{ lastUpdated }}</span>
      </div>
      <button class="action-icon-btn" @click="copyStatusToClipboard" title="复制状态(YAML)">
        📋
      </button>
      <button class="action-icon-btn" @click="refreshStatus" :disabled="isRefreshing" title="刷新状态">
        {{ isRefreshing ? '...' : '↻' }}
      </button>
    </div>

    <!-- Native Server 状态 -->
    <div class="status-card">
      <div class="card-header">
        <h4>Native Server (MCP)</h4>
        <span class="port-badge">3000</span>
      </div>
      <div class="status-row">
        <span class="label">连接状态:</span>
        <span class="value" :class="nativeStatus.connected ? 'success' : 'error'">
          {{ nativeStatus.connected ? '已连接' : '未连接' }}
        </span>
      </div>
      <div class="status-row" v-if="nativeStatus.connected">
        <span class="label">WebSocket:</span>
        <span class="value" :class="nativeStatus.wsConnected ? 'success' : 'warning'">
          {{ nativeStatus.wsConnected ? '活跃' : '断开' }}
        </span>
      </div>
      <div class="status-row" v-if="nativeStatus.connected">
        <span class="label">SSE:</span>
        <span class="value" :class="nativeStatus.sseConnected ? 'success' : 'warning'">
          {{ nativeStatus.sseConnected ? '活跃' : '断开' }}
        </span>
      </div>
    </div>

    <!-- Stock Backend 状态 -->
    <div class="status-card">
      <div class="card-header">
        <h4>Stock Monitor Backend</h4>
        <span class="port-badge">8000</span>
      </div>
      <div class="status-row">
        <span class="label">API 状态:</span>
        <span class="value" :class="backendStatus.alive ? 'success' : 'error'">
          {{ backendStatus.alive ? '在线' : '离线' }}
        </span>
      </div>
      <div class="status-row" v-if="backendStatus.alive">
        <span class="label">数据库:</span>
        <span class="value" :class="backendStatus.dbHealthy ? 'success' : 'error'">
          {{ backendStatus.dbHealthy ? '正常' : '异常' }}
        </span>
      </div>
    </div>

    <!-- 爬虫/平台登录状态 -->
    <div class="status-card">
      <div class="card-header">
        <h4>平台登录状态</h4>
      </div>
      <div class="crawler-list">
        <div v-for="crawler in crawlerStatus" :key="crawler.id" class="crawler-item">
          <div class="crawler-info">
            <span class="crawler-name">{{ crawler.name }}</span>
            <span class="crawler-state" :class="crawler.state">{{ crawler.stateLabel }}</span>
          </div>
          <div class="crawler-actions">
             <button 
               v-if="crawler.state !== 'running'" 
               class="action-btn login-btn"
               @click="quickLogin(crawler.id)"
             >
               登录
             </button>
             <button 
               v-if="crawler.state === 'running' || crawler.state === 'warning'" 
               class="action-btn sync-btn"
               @click="syncSession(platforms.find(p => p.id === crawler.id))"
             >
               同步会话
             </button>
             <span v-else class="status-ok">✓ Ready</span>
          </div>
        </div>
        <div v-if="crawlerStatus.length === 0" class="empty-state">
          暂无平台配置
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';

// 接口定义
interface NativeStatus {
  connected: boolean;
  wsConnected: boolean;
  sseConnected: boolean;
}

interface BackendStatus {
  alive: boolean;
  dbHealthy: boolean;
  version?: string;
}

interface CrawlerStatus {
  id: string;
  name: string;
  state: 'running' | 'idle' | 'error' | 'stopped' | 'warning';
  stateLabel: string;
  lastActive: string;
  isSynced?: boolean;
  nickname?: string;
}

interface PlatformConfig {
  id: string;
  name: string;
  url: string;
  loginUrl: string;
  cookieDomain: string;
  cookieName?: string;
  verifyApi?: string;
  verifyType?: 'json' | 'text';
  verifyXPath?: string; // Add XPath support
  verifyParser?: (data: any) => string | null;
}

const platforms: PlatformConfig[] = [
  {
    id: 'weibo',
    name: '微博',
    url: 'https://weibo.com',
    loginUrl: 'https://weibo.com/login.php',
    cookieDomain: '.weibo.com',
    cookieName: 'SUB',
    verifyApi: 'https://weibo.com/ajax/profile/info',
    verifyType: 'json',
    verifyParser: (data) => data?.data?.user?.screen_name || null
  },
  {
    id: 'bilibili',
    name: 'B站',
    url: 'https://www.bilibili.com',
    loginUrl: 'https://passport.bilibili.com/login',
    cookieDomain: '.bilibili.com',
    cookieName: 'SESSDATA',
    verifyApi: 'https://api.bilibili.com/x/web-interface/nav',
    verifyType: 'json',
    verifyParser: (data) => data?.data?.uname || null
  },
  {
    id: 'douyin',
    name: '抖音',
    url: 'https://www.douyin.com',
    loginUrl: 'https://www.douyin.com',
    cookieDomain: '.douyin.com',
    cookieName: 'sessionid',
    verifyApi: 'https://www.douyin.com/',
    verifyType: 'text',
    verifyXPath: '//script[@id="RENDER_DATA"]', // Example XPath (User can provide better one)
    verifyParser: (text) => {
        // Fallback or complex parsing if XPath result needs processing
        const match = text.match(/<script id="RENDER_DATA" type="application\/json">(.+?)<\/script>/);
        if (match) {
            try {
                const data = JSON.parse(decodeURIComponent(match[1]));
                // TODO: Extract nickname from data structure if known
                return null; 
            } catch (e) { return null; }
        }
        return null;
    }
  },
  {
    id: 'xiaohongshu',
    name: '小红书',
    url: 'https://www.xiaohongshu.com',
    loginUrl: 'https://www.xiaohongshu.com',
    cookieDomain: '.xiaohongshu.com',
    cookieName: 'web_session',
    verifyApi: 'https://edith.xiaohongshu.com/api/sns/web/v1/user/me',
    verifyType: 'json',
    verifyParser: (data) => data?.data?.nickname || null
  },
  {
    id: 'okooo',
    name: '澳客',
    url: 'https://www.okooo.com',
    loginUrl: 'https://www.okooo.com',
    cookieDomain: '.okooo.com',
    verifyApi: 'https://www.okooo.com/',
    verifyType: 'text',
    verifyXPath: '//*[@class="user_name"]', // Example XPath
    verifyParser: (text) => {
        const match = text.match(/class="user_name"[^>]*>([^<]+)</);
        return match ? match[1] : null;
    }
  }
];

// 状态数据
const isRefreshing = ref(false);
const lastUpdateTs = ref(Date.now());
const nativeStatus = ref<NativeStatus>({
  connected: false,
  wsConnected: false,
  sseConnected: false
});
const backendStatus = ref<BackendStatus>({
  alive: false,
  dbHealthy: false
});
const crawlerStatus = ref<CrawlerStatus[]>([]);
const syncedPlatforms = ref(new Set<string>());

// 计算属性
const lastUpdated = computed(() => {
  return new Date(lastUpdateTs.value).toLocaleTimeString();
});

const overallStatusClass = computed(() => {
  // User wants to bypass Native Server, so we prioritize Backend Status
  if (backendStatus.value.alive) {
    return 'status-healthy';
  }
  return 'status-critical';
});

const overallStatusIcon = computed(() => {
  if (backendStatus.value.alive) {
    return '✅';
  }
  return '⚠️';
});

const overallStatusText = computed(() => {
  if (backendStatus.value.alive) {
    return '系统运行正常';
  }
  return '部分服务异常';
});

// SSE Connection for Crawler Status
let eventSource: EventSource | null = null;

const connectBackendSSE = () => {
  if (eventSource) {
    eventSource.close();
  }

  try {
    eventSource = new EventSource('http://localhost:8000/api/v1/crawler/events');
    
    eventSource.onopen = () => {
      console.log('Backend SSE Connected');
      backendStatus.value.alive = true;
    };

    eventSource.onmessage = (event) => {
       // Heartbeat or general messages
       console.log('SSE Message:', event.data);
    };

    eventSource.addEventListener('crawler_status', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log('Crawler Status Update:', data);
        updateCrawlerStatus(data);
      } catch (e) {
        console.error('Failed to parse crawler status', e);
      }
    });

    eventSource.onerror = (err) => {
      console.error('Backend SSE Error', err);
      backendStatus.value.alive = false;
      eventSource?.close();
      // Retry after 5s
      setTimeout(connectBackendSSE, 5000);
    };

  } catch (e) {
    console.error('Failed to connect to Backend SSE', e);
  }
};

const updateCrawlerStatus = (data: any) => {
  const platformName = data.platform;
  const status = data.status;
  
  // Find or create crawler status entry
  let crawler = crawlerStatus.value.find(c => c.id === platformName);
  if (!crawler) {
     // Map platform name to ID/Name if possible, or just add
     // We assume platform name matches ID for simplicity
     const config = platforms.find(p => p.id === platformName);
     crawler = {
       id: platformName,
       name: config ? config.name : platformName,
       state: 'idle',
       stateLabel: '未启动',
       lastActive: new Date().toLocaleTimeString()
     };
     crawlerStatus.value.push(crawler);
  }

  // Update state
  crawler.lastActive = new Date().toLocaleTimeString();
  
  switch(status) {
    case 'starting':
      crawler.state = 'running';
      crawler.stateLabel = '启动中';
      break;
    case 'running':
    case 'crawling':
    case 'ready':
      crawler.state = 'running';
      crawler.stateLabel = '运行中';
      break;
    case 'stopped':
      crawler.state = 'stopped';
      crawler.stateLabel = '已停止';
      break;
    case 'idle':
      crawler.state = 'idle';
      crawler.stateLabel = '空闲';
      break;
    default:
      crawler.state = 'warning';
      crawler.stateLabel = status;
  }
  
  if (data.data_count !== undefined) {
    crawler.stateLabel += ` (${data.data_count})`;
  }
};

const checkNativeServer = async () => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 1000);
    try {
      const res = await fetch('http://localhost:3000/ping', { signal: controller.signal });
      nativeStatus.value.connected = res.ok;
    } catch {
      nativeStatus.value.connected = false;
    } finally {
      clearTimeout(timeoutId);
    }
  } catch {
    nativeStatus.value.connected = false;
  }
};

const checkBackendServer = async () => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);
    try {
      const res = await fetch('http://localhost:8000/api/v1/health', { signal: controller.signal });
      if (res.ok) {
        backendStatus.value.alive = true;
        backendStatus.value.dbHealthy = true;
      } else {
        backendStatus.value.alive = false;
      }
    } catch {
      backendStatus.value.alive = false;
    } finally {
      clearTimeout(timeoutId);
    }
  } catch {
    backendStatus.value.alive = false;
  }
};

const syncCookies = async (p: PlatformConfig) => {
  try {
    if (!chrome.cookies) return;
    const cookies = await chrome.cookies.getAll({ domain: p.cookieDomain });
    const res = await fetch('http://localhost:8000/api/v1/cookies', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        domain: p.cookieDomain,
        cookies: cookies
      })
    });
    if (res.ok) {
        if (!syncedPlatforms.value.has(p.id)) {
            syncedPlatforms.value.add(p.id);
            console.log(`Synced cookies for ${p.name}`);
        }
    } else {
        console.error(`Failed to sync cookies for ${p.name}`);
    }
  } catch (e) {
    console.error(`Error syncing cookies for ${p.name}`, e);
  }
};

const syncSession = async (p: PlatformConfig | undefined) => {
  if (!p) return;
  try {
    if (!chrome.cookies) return;
    
    // 获取Cookie
    const cookies = await chrome.cookies.getAll({ domain: p.cookieDomain });
    
    // 获取账号昵称
    const nickname = await verifyLogin(p);
    
    // 生成用户ID（使用Cookie中的特定字段）
    const userId = cookies.find(c => c.name === (p.cookieName || 'user_id'))?.value || 
                   cookies.find(c => c.name === 'sessionid')?.value || 
                   'unknown';
    
    // 调用新的会话API
    const res = await fetch('http://localhost:8000/api/v1/sessions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        platform_id: p.id,
        user_id: userId,
        account_name: nickname || userId,
        cookies: cookies
      })
    });
    
    if (res.ok) {
      const data = await res.json();
      if (data.success) {
        console.log(`Session synced for ${p.name}: ${data.data?.account_name}`);
        syncedPlatforms.value.add(p.id);
        // 刷新状态
        await fetchCrawlerStatus();
      } else {
        console.error(`Failed to sync session for ${p.name}: ${data.message}`);
      }
    } else {
      console.error(`Failed to sync session for ${p.name}`);
    }
  } catch (e) {
    console.error(`Error syncing session for ${p.name}`, e);
  }
};

const quickLogin = async (platformId: string) => {
  try {
    const platform = platforms.find(p => p.id === platformId);
    if (!platform) {
      console.error(`Platform not found: ${platformId}`);
      return;
    }
    
    // 打开平台首页
    await chrome.tabs.create({ url: platform.url });
  } catch (e) {
    console.error(`Failed to open platform ${platformId}`, e);
  }
};


const verifyLogin = async (p: PlatformConfig): Promise<string | null> => {
  if (!p.verifyApi) return null;
  
  try {
    const res = await fetch(p.verifyApi);
    if (!res.ok) return null;
    
    if (p.verifyType === 'json') {
      const data = await res.json();
      return p.verifyParser ? p.verifyParser(data) : null;
    } else {
      const text = await res.text();
      
      // Try XPath if provided
      if (p.verifyXPath) {
        try {
            const parser = new DOMParser();
            const doc = parser.parseFromString(text, 'text/html');
            const result = doc.evaluate(p.verifyXPath, doc, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
            const node = result.singleNodeValue;
            if (node && node.textContent) {
                return node.textContent.trim();
            }
        } catch (xpathErr) {
            console.warn(`XPath verification failed for ${p.name}`, xpathErr);
        }
      }

      // Fallback to custom parser
      return p.verifyParser ? p.verifyParser(text) : null;
    }
  } catch (e) {
    console.error(`Verify ${p.name} failed`, e);
    return null;
  }
};

const fetchCrawlerStatus = async () => {
  const statusList: CrawlerStatus[] = [];
  
  for (const p of platforms) {
    let isLoggedIn = false;
    let nickname: string | undefined = undefined;
    let statusMessage = '未登录';

    try {
      // 1. Basic Cookie Check
      if (chrome.cookies) {
        const cookies = await chrome.cookies.getAll({ domain: p.cookieDomain });
        if (p.cookieName) {
           isLoggedIn = cookies.some(c => c.name === p.cookieName);
        } else {
           isLoggedIn = cookies.length > 0;
        }

        // 2. Advanced Verification (Fetch Nickname)
        if (isLoggedIn && p.verifyApi) {
           const fetchedName = await verifyLogin(p);
           if (fetchedName) {
             nickname = fetchedName;
             statusMessage = `已登录: ${nickname}`;
           } else {
             // Cookie exists but verification failed
             // This usually means cookie is expired or invalid, OR we need better parsing (XPath)
             statusMessage = '已登录 (需更新Cookie或提供XPath)';
           }
        } else if (isLoggedIn) {
           statusMessage = '已登录';
        }

        if (isLoggedIn) {
           // Auto sync cookies
           await syncCookies(p);
        }
      } else {
        console.warn('chrome.cookies API not available');
      }
    } catch (e) {
      console.error(`Check ${p.name} failed`, e);
      statusMessage = '检查失败';
    }
    
    // Determine state based on login and verification
    let state: CrawlerStatus['state'] = 'idle';
    if (isLoggedIn) {
        if (nickname) {
            state = 'running'; // Verified with nickname
        } else {
            state = 'warning'; // Logged in but verification failed (or no verifyApi)
        }
    }

    statusList.push({
      id: p.id,
      name: p.name,
      state: state,
      stateLabel: statusMessage,
      lastActive: '刚刚',
      isSynced: syncedPlatforms.value.has(p.id),
      nickname: nickname
    });
  }
  crawlerStatus.value = statusList;
};

const refreshStatus = async () => {
  if (isRefreshing.value) return;
  isRefreshing.value = true;
  
  await Promise.all([
    checkNativeServer(),
    checkBackendServer(),
    fetchCrawlerStatus()
  ]);
  
  lastUpdateTs.value = Date.now();
  isRefreshing.value = false;
};

const copyStatusToClipboard = async () => {
  const lines = [];
  lines.push(`system:`);
  lines.push(`  status: "${overallStatusText.value}"`);
  lines.push(`  last_updated: "${lastUpdated.value}"`);
  
  lines.push(`native_server:`);
  lines.push(`  port: 3000`);
  lines.push(`  connected: ${nativeStatus.value.connected}`);
  if (nativeStatus.value.connected) {
      lines.push(`  ws_connected: ${nativeStatus.value.wsConnected}`);
      lines.push(`  sse_connected: ${nativeStatus.value.sseConnected}`);
  }

  lines.push(`backend_server:`);
  lines.push(`  port: 8000`);
  lines.push(`  alive: ${backendStatus.value.alive}`);
  if (backendStatus.value.alive) {
      lines.push(`  db_healthy: ${backendStatus.value.dbHealthy}`);
  }

  lines.push(`platforms:`);
  if (crawlerStatus.value.length === 0) {
    lines.push(`  []`);
  } else {
    crawlerStatus.value.forEach(c => {
      lines.push(`  - name: "${c.name}"`);
      lines.push(`    status: "${c.stateLabel}"`);
      lines.push(`    state: "${c.state}"`);
      if (c.nickname) {
        lines.push(`    nickname: "${c.nickname}"`);
      }
    });
  }

  const yamlString = lines.join('\n');
  
  try {
    await navigator.clipboard.writeText(yamlString);
    // 可以在这里添加一个简单的提示，比如更改图标或文字一秒钟
    const originalTitle = document.title;
    console.log('Status copied to clipboard');
    // 如果有toast组件可以调用，这里简单log一下
  } catch (err) {
    console.error('Failed to copy status: ', err);
  }
};

let autoRefreshTimer: any = null;

onMounted(() => {
  refreshStatus();
  connectBackendSSE();
  autoRefreshTimer = setInterval(refreshStatus, 30000); // 每30秒自动刷新
});

onUnmounted(() => {
  if (autoRefreshTimer) clearInterval(autoRefreshTimer);
  if (eventSource) {
    eventSource.close();
  }
});
</script>

<style scoped>
.system-status-container {
  padding: 16px;
  background-color: #f5f7fa;
  min-height: 100%;
}

.status-summary {
  display: flex;
  align-items: center;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  background: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.status-summary.status-healthy { border-left: 4px solid #52c41a; }
.status-summary.status-warning { border-left: 4px solid #faad14; }
.status-summary.status-critical { border-left: 4px solid #f5222d; }

.status-icon {
  font-size: 24px;
  margin-right: 12px;
}

.status-text h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.last-updated {
  font-size: 12px;
  color: #999;
}

.action-icon-btn {
  margin-left: 8px;
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #666;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.action-icon-btn:hover {
  color: #1890ff;
  background-color: #f0f0f0;
}

/* Maintain margin-left: auto for the first button in the group to push them to the right */
.status-summary .action-icon-btn:first-of-type {
  margin-left: auto;
}

.status-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  border-bottom: 1px solid #eee;
  padding-bottom: 8px;
}

.card-header h4 {
  margin: 0;
  font-size: 14px;
  color: #333;
}

.port-badge {
  background: #e6f7ff;
  color: #1890ff;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.status-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
}

.status-row:last-child { margin-bottom: 0; }

.label { color: #666; }

.value.success { color: #52c41a; font-weight: 500; }
.value.warning { color: #faad14; font-weight: 500; }
.value.error { color: #f5222d; font-weight: 500; }

.crawler-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.crawler-item:last-child { border-bottom: none; }

.crawler-info {
  display: flex;
  flex-direction: column;
}

.crawler-name {
  font-size: 13px;
  color: #333;
  font-weight: 500;
}

.crawler-state {
  font-size: 12px;
  margin-top: 2px;
}

.crawler-state.running { color: #52c41a; }
.crawler-state.idle { color: #999; }
.crawler-state.warning { color: #faad14; }
.crawler-state.error { color: #f5222d; }

.crawler-actions {
  display: flex;
  align-items: center;
}

.action-btn {
  border: none;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.login-btn {
  background: #1890ff;
  color: white;
}

.login-btn:hover {
  background: #40a9ff;
}

.status-ok {
  color: #52c41a;
  font-size: 12px;
  font-weight: 500;
}

.status-container {
  display: flex;
  align-items: center;
  gap: 4px;
}

.sync-badge {
  font-size: 12px;
  cursor: help;
}

.empty-state {
  text-align: center;
  color: #999;
  padding: 16px 0;
  font-size: 13px;
}
</style>