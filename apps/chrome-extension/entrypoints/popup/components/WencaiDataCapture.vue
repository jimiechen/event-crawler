<template>
  <div class="section">
    <h2 class="section-title">问财数据抓取</h2>
    <div class="wencai-card">
      <div class="wencai-status">
        <div class="status-info">
          <span :class="['status-dot', getWencaiStatusClass()]"></span>
          <span class="status-text">{{ getWencaiStatusText() }}</span>
        </div>
        <div v-if="lastCaptureTime" class="status-timestamp">
          最后抓取: {{ new Date(lastCaptureTime).toLocaleString() }}
        </div>
      </div>

      <div class="wencai-controls">
        <button 
          class="capture-button" 
          :disabled="isCapturing || !isPageReady" 
          @click="captureWencaiData"
        >
          <span class="capture-icon">📊</span>
          <span>{{ isCapturing ? '抓取中...' : '抓取当前页面数据' }}</span>
        </button>
        
        <button 
          class="view-data-button" 
          @click="viewCapturedData"
          :disabled="!hasData"
        >
          <span class="view-icon">👁️</span>
          <span>查看已抓取数据</span>
        </button>
      </div>

      <div v-if="captureProgress" class="progress-section">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercentage + '%' }"></div>
        </div>
        <p class="progress-text">{{ captureProgress }}</p>
      </div>

      <div v-if="captureResult" class="result-section">
        <div :class="['result-card', captureResult.success ? 'success' : 'error']">
          <div class="result-header">
            <span class="result-icon">{{ captureResult.success ? '✅' : '❌' }}</span>
            <span class="result-title">
              {{ captureResult.success ? '抓取成功' : '抓取失败' }}
            </span>
          </div>
          <div class="result-details">
            <p v-if="captureResult.success">
              成功抓取 {{ captureResult.recordCount }} 条股票数据
            </p>
            <p v-else class="error-message">
              {{ captureResult.error }}
            </p>
          </div>
        </div>
      </div>

      <div class="wencai-stats">
        <div class="stats-grid">
          <div class="stats-item">
            <span class="stats-label">总抓取次数</span>
            <span class="stats-value">{{ totalCaptures }}</span>
          </div>
          <div class="stats-item">
            <span class="stats-label">成功次数</span>
            <span class="stats-value">{{ successfulCaptures }}</span>
          </div>
          <div class="stats-item">
            <span class="stats-label">数据条数</span>
            <span class="stats-value">{{ totalRecords }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue';

// 状态管理
const isCapturing = ref(false);
const isPageReady = ref(false);
const captureProgress = ref('');
const progressPercentage = ref(0);
const lastCaptureTime = ref<number | null>(null);
const hasData = ref(false);

// 统计数据
const totalCaptures = ref(0);
const successfulCaptures = ref(0);
const totalRecords = ref(0);

// 抓取结果
const captureResult = ref<{
  success: boolean;
  recordCount?: number;
  error?: string;
} | null>(null);

// 计算属性
const getWencaiStatusClass = () => {
  if (isCapturing.value) return 'bg-yellow-500';
  if (isPageReady.value) return 'bg-emerald-500';
  return 'bg-gray-500';
};

const getWencaiStatusText = () => {
  if (isCapturing.value) return '抓取中';
  if (isPageReady.value) return '就绪';
  return '未就绪';
};

// 检查页面是否为问财页面
const checkPageReady = async () => {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab?.url?.includes('iwencai.com')) {
      isPageReady.value = true;
    } else {
      isPageReady.value = false;
    }
  } catch (error) {
    console.error('检查页面状态失败:', error);
    isPageReady.value = false;
  }
};

// 抓取问财数据
const captureWencaiData = async () => {
  if (isCapturing.value || !isPageReady.value) return;
  
  isCapturing.value = true;
  captureProgress.value = '正在解析页面数据...';
  progressPercentage.value = 20;
  captureResult.value = null;

  try {
    // 获取当前活动标签页
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) {
      throw new Error('无法获取当前标签页');
    }

    // 同步Cookie到后端
    if (tab.url) {
      try {
        captureProgress.value = '同步Cookie...';
        const urlObj = new URL(tab.url);
        // 获取所有相关的cookie (主域)
        // 注意：chrome.cookies.getAll 需要 host_permissions 或 cookies 权限
        // 获取 iwencai.com 和 10jqka.com.cn 的 cookie
        const domains = ['iwencai.com', '10jqka.com.cn'];
        const allCookies = [];
        
        for (const domain of domains) {
            const cookies = await chrome.cookies.getAll({ domain });
            if (cookies && cookies.length > 0) {
                allCookies.push(...cookies);
                // 分域名同步
                await fetch('http://localhost:8000/api/v1/cookies', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        domain: domain,
                        cookies: cookies
                    })
                });
            }
        }
        console.log('Cookies synced successfully');
      } catch (cookieError) {
        console.warn('Cookie同步失败，但不影响主流程:', cookieError);
      }
    }

    // 注入内容脚本并执行解析
    captureProgress.value = '注入解析脚本...';
    progressPercentage.value = 40;

    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: parseWencaiTable,
    });

    if (!results || !results[0]) {
      throw new Error('脚本执行失败');
    }

    const tableData = results[0].result;
    if (!tableData || !tableData.success) {
      throw new Error(tableData?.error || '解析失败');
    }

    captureProgress.value = '发送数据到后端...';
    progressPercentage.value = 70;

    // 发送数据到后端API
    const response = await fetch('http://localhost:8000/api/v1/wencai/parse', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        html_content: tableData.html,
        crawl_url: tab.url,
        batch_name: `Chrome扩展抓取_${new Date().toISOString().slice(0, 19).replace(/[T:]/g, '_')}`,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || errorData.detail || '后端处理失败');
    }

    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message || '数据处理失败');
    }
    
    captureProgress.value = '完成';
    progressPercentage.value = 100;

    // 更新结果
    captureResult.value = {
      success: true,
      recordCount: result.data?.success_records || 0,
    };

    // 保存最新的文件名到storage
    if (result.data?.file_path) {
      await chrome.storage.local.set({ lastSavedFile: result.data.file_path });
    }

    // 更新统计
    totalCaptures.value++;
    successfulCaptures.value++;
    totalRecords.value += result.data?.success_records || 0;
    lastCaptureTime.value = Date.now();
    hasData.value = true;

    // 保存到本地存储
    await saveStats();

  } catch (error) {
    console.error('抓取失败:', error);
    
    let errorMessage = '未知错误';
    if (error instanceof Error) {
      if (error.message.includes('fetch')) {
        errorMessage = '网络连接失败，请检查后端服务是否启动';
      } else if (error.message.includes('Failed to fetch')) {
        errorMessage = '无法连接到后端服务，请确认服务地址正确';
      } else if (error.message.includes('NetworkError')) {
        errorMessage = '网络错误，请检查网络连接';
      } else {
        errorMessage = error.message;
      }
    }
    
    captureResult.value = {
      success: false,
      error: errorMessage,
    };
    totalCaptures.value++;
    await saveStats();
  } finally {
    isCapturing.value = false;
    setTimeout(() => {
      captureProgress.value = '';
      progressPercentage.value = 0;
    }, 2000);
  }
};

// 解析问财表格的函数（在页面上下文中执行）
function parseWencaiTable() {
  try {
    // 查找问财表格 - 使用更精确的选择器
    const table = document.querySelector('table.table') || 
                  document.querySelector('.table-container table') ||
                  document.querySelector('[class*="table"]') ||
                  document.querySelector('table') ||
                  document.querySelector('[role="table"]');
    
    if (!table) {
      return { success: false, error: '未找到数据表格，请确认页面已加载完成且包含股票数据表格' };
    }

    // 检查表格是否有足够的行数
    const rows = table.querySelectorAll('tr');
    if (rows.length < 2) {
      return { success: false, error: '表格数据不足，至少需要表头和一行数据' };
    }

    // 获取表格HTML
    const tableHtml = table.outerHTML;
    
    // 更严格的股票数据验证
    const hasStockCode = /\d{6}/.test(tableHtml); // 6位股票代码
    const hasStockKeywords = tableHtml.includes('股票') || 
                            tableHtml.includes('代码') || 
                            tableHtml.includes('名称') ||
                            tableHtml.includes('现价') ||
                            tableHtml.includes('涨跌') ||
                            tableHtml.includes('市值');

    if (!hasStockCode && !hasStockKeywords) {
      return { success: false, error: '表格中未找到有效的股票数据，请确认当前页面显示的是股票列表' };
    }

    // 检查表格大小，避免过大的HTML
    if (tableHtml.length > 1000000) { // 1MB限制
      return { success: false, error: '表格数据过大，请尝试筛选数据后再抓取' };
    }

    return {
      success: true,
      html: tableHtml,
      rowCount: rows.length - 1, // 减去表头
    };
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : '解析过程中发生错误，请刷新页面后重试' 
    };
  }
}

// 查看已抓取数据
const viewCapturedData = async () => {
  try {
    // 获取最新保存的文件名
    const storage = await chrome.storage.local.get(['lastSavedFile']);
    const fileName = storage.lastSavedFile || 'latest';
    
    // 打开新标签页显示数据，传递文件参数
    const url = `http://localhost:8000/static/index.html?file=${fileName}`;
    await chrome.tabs.create({ url });
  } catch (error) {
    console.error('打开数据页面失败:', error);
  }
};

// 保存统计数据
const saveStats = async () => {
  try {
    await chrome.storage.local.set({
      wencaiStats: {
        totalCaptures: totalCaptures.value,
        successfulCaptures: successfulCaptures.value,
        totalRecords: totalRecords.value,
        lastCaptureTime: lastCaptureTime.value,
        hasData: hasData.value,
      },
    });
  } catch (error) {
    console.error('保存统计数据失败:', error);
  }
};

// 加载统计数据
const loadStats = async () => {
  try {
    const result = await chrome.storage.local.get(['wencaiStats']);
    if (result.wencaiStats) {
      const stats = result.wencaiStats;
      totalCaptures.value = stats.totalCaptures || 0;
      successfulCaptures.value = stats.successfulCaptures || 0;
      totalRecords.value = stats.totalRecords || 0;
      lastCaptureTime.value = stats.lastCaptureTime || null;
      hasData.value = stats.hasData || false;
    }
  } catch (error) {
    console.error('加载统计数据失败:', error);
  }
};

// 组件挂载时初始化
onMounted(async () => {
  await loadStats();
  await checkPageReady();
  
  // 监听标签页变化
  chrome.tabs.onActivated.addListener(checkPageReady);
  chrome.tabs.onUpdated.addListener(checkPageReady);
});
</script>

<style scoped>
.section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 12px;
}

.wencai-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
}

.wencai-status {
  margin-bottom: 16px;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-text {
  font-weight: 500;
  color: #374151;
}

.status-timestamp {
  font-size: 12px;
  color: #6b7280;
}

.wencai-controls {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.capture-button, .view-data-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s;
  border: none;
  cursor: pointer;
}

.capture-button {
  background: #3b82f6;
  color: white;
}

.capture-button:hover:not(:disabled) {
  background: #2563eb;
}

.capture-button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.view-data-button {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.view-data-button:hover:not(:disabled) {
  background: #e5e7eb;
}

.view-data-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.progress-section {
  margin-bottom: 16px;
}

.progress-bar {
  width: 100%;
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: #3b82f6;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 14px;
  color: #6b7280;
  text-align: center;
}

.result-section {
  margin-bottom: 16px;
}

.result-card {
  padding: 12px;
  border-radius: 8px;
  border: 1px solid;
}

.result-card.success {
  background: #f0fdf4;
  border-color: #22c55e;
}

.result-card.error {
  background: #fef2f2;
  border-color: #ef4444;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.result-title {
  font-weight: 500;
}

.result-details {
  font-size: 14px;
}

.error-message {
  color: #dc2626;
}

.wencai-stats {
  border-top: 1px solid #e5e7eb;
  padding-top: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stats-item {
  text-align: center;
}

.stats-label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.stats-value {
  display: block;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

/* 状态点颜色 */
.bg-emerald-500 {
  background-color: #10b981;
}

.bg-yellow-500 {
  background-color: #f59e0b;
}

.bg-gray-500 {
  background-color: #6b7280;
}
</style>