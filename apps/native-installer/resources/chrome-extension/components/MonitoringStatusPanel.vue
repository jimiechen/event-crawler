<template>
  <div class="monitoring-status-panel">
    <!-- 监控状态总览 -->
    <div class="status-overview">
      <div class="status-header">
        <h3>监控状态总览</h3>
        <div class="status-indicator" :class="getStatusClass(currentStatus)">
          <span class="status-dot"></span>
          <span class="status-text">{{ getStatusText(currentStatus) }}</span>
        </div>
      </div>
      
      <!-- 快速控制按钮 -->
      <div class="quick-controls">
        <button 
          @click="toggleMonitoring" 
          :disabled="isTransitioning"
          class="control-btn"
          :class="getControlButtonClass()"
        >
          <span class="btn-icon">{{ getControlButtonIcon() }}</span>
          <span>{{ getControlButtonText() }}</span>
        </button>
        
        <button 
          @click="refreshStatus" 
          :disabled="isRefreshing"
          class="control-btn secondary"
        >
          <span class="btn-icon">{{ isRefreshing ? '🔄' : '🔃' }}</span>
          <span>刷新状态</span>
        </button>
      </div>
    </div>

    <!-- 当前运行状态 -->
    <div class="current-run-section">
      <h4>当前运行状态</h4>
      <div v-if="currentRunState" class="run-status-grid">
        <div class="status-item">
          <span class="label">数据抓取状态:</span>
          <span class="value" :class="getDataFetchStatusClass(currentRunState.dataFetchStatus)">
            {{ getDataFetchStatusText(currentRunState.dataFetchStatus) }}
          </span>
        </div>
        <div class="status-item">
          <span class="label">运行时长:</span>
          <span class="value">{{ formatDuration(currentRunState.duration) }}</span>
        </div>
        <div class="status-item">
          <span class="label">处理进度:</span>
          <div class="progress-container">
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: currentRunState.progress + '%' }"
              ></div>
            </div>
            <span class="progress-text">{{ currentRunState.progress }}%</span>
          </div>
        </div>
        <div class="status-item">
          <span class="label">重试次数:</span>
          <span class="value" :class="{ 'warning': currentRunState.retryCount > 0 }">
            {{ currentRunState.retryCount }}
          </span>
        </div>
      </div>
      <div v-else class="empty-message">
        暂无运行任务
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="statistics-section">
      <h4>运行统计</h4>
      <div v-if="statistics" class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">{{ statistics.totalRuns }}</div>
          <div class="stat-label">总运行次数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ statistics.successfulRuns }}</div>
          <div class="stat-label">成功次数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ statistics.failedRuns }}</div>
          <div class="stat-label">失败次数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ formatSuccessRate(statistics) }}%</div>
          <div class="stat-label">成功率</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ statistics.totalDataFetched }}</div>
          <div class="stat-label">数据条数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ formatDuration(statistics.averageRunTime) }}</div>
          <div class="stat-label">平均耗时</div>
        </div>
      </div>
      <div v-else class="empty-message">
        暂无统计数据
      </div>
    </div>

    <!-- 健康状态 (已移动到 SystemStatus 组件) -->
    <!-- <div v-if="healthStatus" class="health-section">
      <h4>系统健康状态</h4>
      <div class="health-indicator" :class="getHealthStatusClass(healthStatus.status)">
        <span class="health-icon">{{ getHealthStatusIcon(healthStatus.status) }}</span>
        <span class="health-text">{{ getHealthStatusText(healthStatus.status) }}</span>
      </div>
      
      <div v-if="healthStatus.issues.length > 0" class="health-issues">
        <h5>检测到的问题:</h5>
        <ul class="issue-list">
          <li v-for="issue in healthStatus.issues" :key="issue" class="issue-item">
            {{ issue }}
          </li>
        </ul>
      </div>
    </div> -->

    <!-- 最近错误 -->
    <div v-if="recentErrors.length > 0" class="errors-section">
      <h4>最近错误 ({{ recentErrors.length }})</h4>
      <div class="error-list">
        <div 
          v-for="error in recentErrors.slice(0, 3)" 
          :key="error.id"
          class="error-item"
          :class="getErrorLevelClass(error.level)"
        >
          <div class="error-header">
            <span class="error-level">{{ getErrorLevelText(error.level) }}</span>
            <span class="error-time">{{ formatTime(error.timestamp) }}</span>
          </div>
          <div class="error-message">{{ error.message }}</div>
        </div>
      </div>
      
      <button @click="clearErrors" class="clear-errors-btn">
        清除错误记录
      </button>
    </div>

    <!-- 爬虫测试 -->
    <div class="crawler-test-section">
      <h4>爬虫测试与调试</h4>
      
      <!-- HTML调试 -->
      <div class="debug-input-section">
        <div class="input-group">
            <input v-model="debugXpath" placeholder="输入XPath (e.g. //div[@class='title'])" class="xpath-input" />
            <button @click="debugHtml" class="debug-btn">调试HTML</button>
        </div>
        <div class="platform-select">
            <select v-model="debugPlatform">
                <option value="lovart">Lovart</option>
                <option value="tempmail">Tempmail</option>
                <option value="stitch">Stitch</option>
                <option value="deepseek">Deepseek</option>
            </select>
        </div>
      </div>

      <div class="test-buttons">
        <button @click="testCrawler('lovart')" class="test-btn">测试 Lovart</button>
        <button @click="testCrawler('tempmail')" class="test-btn">测试 Tempmail</button>
        <button @click="testCrawler('stitch')" class="test-btn">测试 Stitch</button>
        <button @click="testCrawler('deepseek')" class="test-btn">测试 Deepseek</button>
      </div>
      <div v-if="testResult" class="test-result">
        <pre>{{ testResult }}</pre>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <button @click="exportStatus" class="action-btn">
        <span class="btn-icon">📊</span>
        <span>导出状态</span>
      </button>
      <button @click="resetStatistics" class="action-btn secondary">
        <span class="btn-icon">🔄</span>
        <span>重置统计</span>
      </button>
      <button @click="showRunHistory" class="action-btn secondary">
        <span class="btn-icon">📋</span>
        <span>运行历史</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';

// 状态枚举定义
enum MonitoringStatus {
  STOPPED = 'stopped',
  STARTING = 'starting',
  RUNNING = 'running',
  STOPPING = 'stopping',
  ERROR = 'error'
}

enum DataFetchStatus {
  IDLE = 'idle',
  EXTRACTING_CODES = 'extracting_codes',
  FETCHING_DATA = 'fetching_data',
  SENDING_DATA = 'sending_data',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

enum ErrorLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

// 响应式状态
const currentStatus = ref<MonitoringStatus>(MonitoringStatus.STOPPED);
const currentRunState = ref<any>(null);
const statistics = ref<any>(null);
const healthStatus = ref<any>(null);
const recentErrors = ref<any[]>([]);
const isTransitioning = ref(false);
const isRefreshing = ref(false);

// 定时器
let statusUpdateTimer: NodeJS.Timeout | null = null;

// 获取状态样式类
const getStatusClass = (status: MonitoringStatus) => {
  const classMap = {
    [MonitoringStatus.STOPPED]: 'status-stopped',
    [MonitoringStatus.STARTING]: 'status-starting',
    [MonitoringStatus.RUNNING]: 'status-running',
    [MonitoringStatus.STOPPING]: 'status-stopping',
    [MonitoringStatus.ERROR]: 'status-error'
  };
  return classMap[status] || 'status-unknown';
};

// 获取状态文本
const getStatusText = (status: MonitoringStatus) => {
  const textMap = {
    [MonitoringStatus.STOPPED]: '已停止',
    [MonitoringStatus.STARTING]: '启动中',
    [MonitoringStatus.RUNNING]: '运行中',
    [MonitoringStatus.STOPPING]: '停止中',
    [MonitoringStatus.ERROR]: '错误'
  };
  return textMap[status] || '未知';
};

// 获取控制按钮样式
const getControlButtonClass = () => {
  if (isTransitioning.value) return 'loading';
  return currentStatus.value === MonitoringStatus.RUNNING ? 'danger' : 'primary';
};

// 获取控制按钮图标
const getControlButtonIcon = () => {
  if (isTransitioning.value) return '⏳';
  return currentStatus.value === MonitoringStatus.RUNNING ? '⏹️' : '▶️';
};

// 获取控制按钮文本
const getControlButtonText = () => {
  if (isTransitioning.value) {
    return currentStatus.value === MonitoringStatus.STARTING ? '启动中...' : '停止中...';
  }
  return currentStatus.value === MonitoringStatus.RUNNING ? '停止监控' : '开始监控';
};

// 获取数据抓取状态样式
const getDataFetchStatusClass = (status: DataFetchStatus) => {
  const classMap = {
    [DataFetchStatus.IDLE]: 'fetch-idle',
    [DataFetchStatus.EXTRACTING_CODES]: 'fetch-extracting',
    [DataFetchStatus.FETCHING_DATA]: 'fetch-fetching',
    [DataFetchStatus.SENDING_DATA]: 'fetch-sending',
    [DataFetchStatus.COMPLETED]: 'fetch-completed',
    [DataFetchStatus.FAILED]: 'fetch-failed'
  };
  return classMap[status] || 'fetch-unknown';
};

// 获取数据抓取状态文本
const getDataFetchStatusText = (status: DataFetchStatus) => {
  const textMap = {
    [DataFetchStatus.IDLE]: '空闲',
    [DataFetchStatus.EXTRACTING_CODES]: '提取股票代码',
    [DataFetchStatus.FETCHING_DATA]: '获取股票数据',
    [DataFetchStatus.SENDING_DATA]: '发送数据',
    [DataFetchStatus.COMPLETED]: '已完成',
    [DataFetchStatus.FAILED]: '失败'
  };
  return textMap[status] || '未知';
};

// 格式化时长
const formatDuration = (ms: number) => {
  if (!ms) return '0秒';
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) {
    return `${hours}小时${minutes % 60}分钟`;
  } else if (minutes > 0) {
    return `${minutes}分钟${seconds % 60}秒`;
  } else {
    return `${seconds}秒`;
  }
};

// 格式化成功率
const formatSuccessRate = (stats: any) => {
  if (!stats || stats.totalRuns === 0) return 0;
  return Math.round((stats.successfulRuns / stats.totalRuns) * 100);
};

// 获取健康状态样式
const getHealthStatusClass = (status: string) => {
  const classMap = {
    'healthy': 'health-good',
    'warning': 'health-warning',
    'critical': 'health-critical'
  };
  return classMap[status] || 'health-unknown';
};

// 获取健康状态图标
const getHealthStatusIcon = (status: string) => {
  const iconMap = {
    'healthy': '✅',
    'warning': '⚠️',
    'critical': '❌'
  };
  return iconMap[status] || '❓';
};

// 获取健康状态文本
const getHealthStatusText = (status: string) => {
  const textMap = {
    'healthy': '健康',
    'warning': '警告',
    'critical': '严重'
  };
  return textMap[status] || '未知';
};

// 获取错误级别样式
const getErrorLevelClass = (level: ErrorLevel) => {
  const classMap = {
    [ErrorLevel.LOW]: 'error-low',
    [ErrorLevel.MEDIUM]: 'error-medium',
    [ErrorLevel.HIGH]: 'error-high',
    [ErrorLevel.CRITICAL]: 'error-critical'
  };
  return classMap[level] || 'error-unknown';
};

// 获取错误级别文本
const getErrorLevelText = (level: ErrorLevel) => {
  const textMap = {
    [ErrorLevel.LOW]: '低',
    [ErrorLevel.MEDIUM]: '中',
    [ErrorLevel.HIGH]: '高',
    [ErrorLevel.CRITICAL]: '严重'
  };
  return textMap[level] || '未知';
};

// 格式化时间
const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleTimeString();
};

// 切换监控状态
const toggleMonitoring = async () => {
  try {
    console.log('MonitoringStatusPanel: 开始切换监控状态，当前状态:', currentStatus.value);
    isTransitioning.value = true;
    
    if (currentStatus.value === MonitoringStatus.RUNNING) {
      console.log('MonitoringStatusPanel: 正在停止监控...');
      // 发送停止监控消息到background script
      const response = await chrome.runtime.sendMessage({
        action: 'stopNetworkCapture'
      });
      console.log('MonitoringStatusPanel: 停止监控响应:', response);
      
      if (response && response.success !== false) {
        currentStatus.value = MonitoringStatus.STOPPED;
        console.log('MonitoringStatusPanel: 监控已停止');
      } else {
        throw new Error('停止监控失败: ' + (response?.error || '未知错误'));
      }
    } else {
      console.log('MonitoringStatusPanel: 正在启动监控...');
      // 获取当前标签页ID
      const tabId = await getCurrentTabId();
      console.log('MonitoringStatusPanel: 当前标签页ID:', tabId);
      
      // 发送启动监控消息到background script
      const response = await chrome.runtime.sendMessage({
        action: 'startNetworkCapture',
        pattern: 'https://d.10jqka.com.cn/multimarketreal/hs/',
        tabId: tabId
      });
      console.log('MonitoringStatusPanel: 启动监控响应:', response);
      
      if (response && response.success !== false) {
        currentStatus.value = MonitoringStatus.RUNNING;
        console.log('MonitoringStatusPanel: 监控已启动');
      } else {
        throw new Error('启动监控失败: ' + (response?.error || '未知错误'));
      }
    }
    
    // 立即刷新状态
    await refreshStatus();
  } catch (error) {
    console.error('MonitoringStatusPanel: 切换监控状态失败:', error);
    currentStatus.value = MonitoringStatus.ERROR;
    // 添加错误到错误列表
    recentErrors.value.unshift({
      id: Date.now(),
      level: ErrorLevel.HIGH,
      message: `切换监控状态失败: ${error instanceof Error ? error.message : String(error)}`,
      timestamp: Date.now()
    });
  } finally {
    isTransitioning.value = false;
  }
};

// 刷新状态
const refreshStatus = async () => {
  try {
    console.log('MonitoringStatusPanel: 开始刷新状态...');
    isRefreshing.value = true;
    await updateStatus();
    console.log('MonitoringStatusPanel: 状态刷新完成');
  } catch (error) {
    console.error('MonitoringStatusPanel: 刷新状态失败:', error);
  } finally {
    isRefreshing.value = false;
  }
};

// 更新状态
const updateStatus = async () => {
  try {
    console.log('MonitoringStatusPanel: 开始更新状态...');
    
    // 通过background script获取监控状态
    const response = await chrome.runtime.sendMessage({
      action: 'getNetworkCaptureStatus'
    });
    
    console.log('MonitoringStatusPanel: 获取状态响应:', response);
    
    if (response) {
      // 根据响应更新状态
      if (response.isCapturing) {
        currentStatus.value = MonitoringStatus.RUNNING;
      } else {
        currentStatus.value = MonitoringStatus.STOPPED;
      }
      
      // 更新其他状态信息
      currentRunState.value = response.currentRunState || null;
      statistics.value = response.statistics || null;
      healthStatus.value = response.healthStatus || { status: 'healthy', issues: [] };
      
      console.log('MonitoringStatusPanel: 状态更新完成，当前状态:', currentStatus.value);
    } else {
      console.warn('MonitoringStatusPanel: 未收到有效的状态响应');
    }
  } catch (error) {
    console.error('MonitoringStatusPanel: 更新状态失败:', error);
    currentStatus.value = MonitoringStatus.ERROR;
  }
};

// 获取当前标签页ID
const getCurrentTabId = async () => {
  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const tabId = tabs[0]?.id;
    console.log('MonitoringStatusPanel: 获取当前标签页ID:', tabId);
    return tabId;
  } catch (error) {
    console.error('MonitoringStatusPanel: 获取标签页ID失败:', error);
    throw error;
  }
};

// 清除错误
const clearErrors = async () => {
  try {
    const tabId = await getCurrentTabId();
    await chrome.tabs.sendMessage(tabId, {
      action: 'clear_errors'
    });
    recentErrors.value = [];
  } catch (error) {
    console.error('清除错误失败:', error);
  }
};

// 导出状态
const exportStatus = async () => {
  try {
    const tabId = await getCurrentTabId();
    const response = await chrome.tabs.sendMessage(tabId, {
      action: 'export_status'
    });
    
    if (response) {
      const blob = new Blob([JSON.stringify(response, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `monitoring-status-${new Date().toISOString().slice(0, 19)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    }
  } catch (error) {
    console.error('导出状态失败:', error);
  }
};

// 重置统计
const resetStatistics = async () => {
  try {
    const tabId = await getCurrentTabId();
    await chrome.tabs.sendMessage(tabId, {
      action: 'reset_statistics'
    });
    await updateStatus();
  } catch (error) {
    console.error('重置统计失败:', error);
  }
};

// 显示运行历史
const showRunHistory = async () => {
  try {
    const tabId = await getCurrentTabId();
    const response = await chrome.tabs.sendMessage(tabId, {
      action: 'get_run_history'
    });
    
    if (response) {
      console.log('运行历史:', response);
      // 这里可以打开一个模态框显示历史记录
    }
  } catch (error) {
    console.error('获取运行历史失败:', error);
  }
};

// 爬虫测试
const testResult = ref('');
const debugXpath = ref('');
const debugPlatform = ref('lovart');

const debugHtml = async () => {
  if (!debugXpath.value) {
    testResult.value = "Please enter XPath";
    return;
  }
  
  try {
    testResult.value = `Debugging HTML with XPath: ${debugXpath.value}...`;
    
    // Get current tab ID
    const tabId = await getCurrentTabId();
    if (!tabId) throw new Error("No active tab found");

    // Execute script to get HTML and URL
    // @ts-ignore
    const results = await chrome.scripting.executeScript({
      target: { tabId: tabId },
      func: () => ({
          html: document.documentElement.outerHTML,
          url: window.location.href
      })
    });
    
    const { html, url } = results[0].result;
    
    // Send to backend
    const response = await fetch('http://localhost:8000/api/v1/crawler/debughtml', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        platform: debugPlatform.value,
        url: url,
        xpath: debugXpath.value,
        html: html
      })
    });
    
    const data = await response.json();
    testResult.value = JSON.stringify(data, null, 2);
    
  } catch (error: any) {
    testResult.value = `Error: ${error.message || String(error)}`;
    console.error(error);
  }
};

const testCrawler = async (platform: string) => {
  try {
    testResult.value = `Testing ${platform}...`;
    
    // Get current tab ID
    const tabId = await getCurrentTabId();
    if (!tabId) throw new Error("No active tab found");

    // Execute script to get HTML
    // @ts-ignore
    const results = await chrome.scripting.executeScript({
      target: { tabId: tabId },
      func: () => document.documentElement.outerHTML
    });
    
    const html = results[0].result;
    
    // Send to backend
    const response = await fetch('http://localhost:8000/api/v1/crawler/parse_html', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        platform: platform,
        html: html,
        url: 'current_tab_url' 
      })
    });
    
    const data = await response.json();
    testResult.value = JSON.stringify(data, null, 2);
    
  } catch (error: any) {
    testResult.value = `Error: ${error.message || String(error)}`;
    console.error(error);
  }
};

// 生命周期
onMounted(() => {
  updateStatus();
  // 每5秒更新一次状态
  statusUpdateTimer = setInterval(updateStatus, 5000);
});

onUnmounted(() => {
  if (statusUpdateTimer) {
    clearInterval(statusUpdateTimer);
  }
});
</script>

<style scoped>
.monitoring-status-panel {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.status-overview {
  background: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.status-header h3 {
  margin: 0;
  color: #333;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 20px;
  font-weight: 500;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-stopped { background: #f8f9fa; color: #6c757d; }
.status-stopped .status-dot { background: #6c757d; }

.status-starting { background: #fff3cd; color: #856404; }
.status-starting .status-dot { background: #ffc107; animation: pulse 1s infinite; }

.status-running { background: #d1edff; color: #0c5460; }
.status-running .status-dot { background: #17a2b8; animation: pulse 1s infinite; }

.status-stopping { background: #f8d7da; color: #721c24; }
.status-stopping .status-dot { background: #dc3545; animation: pulse 1s infinite; }

.status-error { background: #f8d7da; color: #721c24; }
.status-error .status-dot { background: #dc3545; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.quick-controls {
  display: flex;
  gap: 12px;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.control-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.control-btn.primary {
  background: #007bff;
  color: white;
}

.control-btn.primary:hover:not(:disabled) {
  background: #0056b3;
}

.control-btn.danger {
  background: #dc3545;
  color: white;
}

.control-btn.danger:hover:not(:disabled) {
  background: #c82333;
}

.control-btn.secondary {
  background: #6c757d;
  color: white;
}

.control-btn.secondary:hover:not(:disabled) {
  background: #545b62;
}

.control-btn.loading {
  background: #ffc107;
  color: #212529;
}

.current-run-section,
.statistics-section,
.health-section,
.errors-section {
  background: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.current-run-section h4,
.statistics-section h4,
.health-section h4,
.errors-section h4 {
  margin: 0 0 16px 0;
  color: #333;
  font-size: 16px;
}

.run-status-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.status-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.status-item .label {
  font-size: 12px;
  color: #6c757d;
  font-weight: 500;
}

.status-item .value {
  font-weight: 600;
  color: #333;
}

.status-item .value.warning {
  color: #dc3545;
}

.progress-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: #e9ecef;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #007bff;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: #6c757d;
  min-width: 35px;
}

.fetch-idle { color: #6c757d; }
.fetch-extracting { color: #ffc107; }
.fetch-fetching { color: #17a2b8; }
.fetch-sending { color: #007bff; }
.fetch-completed { color: #28a745; }
.fetch-failed { color: #dc3545; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.stat-card {
  text-align: center;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #007bff;
  display: block;
}

.stat-label {
  font-size: 12px;
  color: #6c757d;
  margin-top: 4px;
}

.health-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-radius: 6px;
  font-weight: 500;
}

.health-good { background: #d4edda; color: #155724; }
.health-warning { background: #fff3cd; color: #856404; }
.health-critical { background: #f8d7da; color: #721c24; }

.health-issues {
  margin-top: 12px;
}

.health-issues h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #333;
}

.issue-list {
  margin: 0;
  padding-left: 20px;
}

.issue-item {
  font-size: 14px;
  color: #6c757d;
  margin-bottom: 4px;
}

.error-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.error-item {
  padding: 12px;
  border-radius: 6px;
  border-left: 4px solid;
}

.error-low { background: #f8f9fa; border-color: #6c757d; }
.error-medium { background: #fff3cd; border-color: #ffc107; }
.error-high { background: #ffe6cc; border-color: #fd7e14; }
.error-critical { background: #f8d7da; border-color: #dc3545; }

.error-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.error-level {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.error-time {
  font-size: 12px;
  color: #6c757d;
}

.error-message {
  font-size: 14px;
  color: #333;
}

.clear-errors-btn {
  margin-top: 12px;
  padding: 8px 16px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.clear-errors-btn:hover {
  background: #545b62;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background: white;
  color: #333;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #f8f9fa;
  border-color: #adb5bd;
}

.action-btn.secondary {
  background: #f8f9fa;
  color: #6c757d;
}

.btn-icon {
  font-size: 16px;
}

.empty-message {
  padding: 24px;
  text-align: center;
  color: #6c757d;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 14px;
}

.crawler-test-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #dee2e6;
}

.test-buttons {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.test-btn {
  padding: 6px 12px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.test-btn:hover {
  background: #0056b3;
}

.test-result {
  margin-top: 8px;
  padding: 8px;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  max-height: 200px;
  overflow: auto;
}

.test-result pre {
  margin: 0;
  font-size: 12px;
  white-space: pre-wrap;
}

.debug-input-section {
  margin-bottom: 12px;
}

.input-group {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.xpath-input {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.debug-btn {
  padding: 6px 12px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  white-space: nowrap;
}

.debug-btn:hover {
  background: #218838;
}

.platform-select select {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  background-color: white;
}
</style>