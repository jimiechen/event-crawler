<template>
  <div class="popup-container">
    <div class="header">
      <div class="header-content">
        <h1 class="header-title">同花顺股票监控</h1>
      </div>
    </div>

    <!-- Tab导航 -->
    <div class="tab-navigation">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        @click="activeTab = tab.id"
        :class="['tab-btn', { active: activeTab === tab.id }]"
      >
        {{ tab.name }}
      </button>
    </div>

    <div class="content">
      <!-- 数据监控Tab -->
      <div v-if="activeTab === 'monitor'" class="tab-content">
        <!-- URL显示区域 -->
        <div class="section">
          <div class="url-section">
            <div class="url-label">当前页面URL:</div>
            <div class="url-display">{{ currentUrl || '未获取到URL' }}</div>
          </div>
        </div>

        <!-- 同花顺数据抓取区域 -->
        <div class="section">
          <div class="config-card">
            <div class="section-header">
              <h3>同花顺股票数据抓取</h3>
            </div>

            <div class="tonghuashun-section">
              <!-- Wencai Data Capture Section -->
              <WencaiDataCapture />
            </div>

            <!-- 导航区域 -->
            <div class="tonghuashun-section">
              <h4>页面导航</h4>
              <button 
                @click="navigateToThs" 
                :disabled="thsLoading"
                class="ths-btn ths-btn-primary ths-btn-large"
              >
                {{ thsLoading ? '导航中...' : (currentTabId ? '刷新同花顺页面' : '🚀 打开同花顺自选股') }}
              </button>
            </div>
            
            <!-- 登录状态区域 -->
            <div class="tonghuashun-section">
              <h4>登录状态</h4>
              <div class="ths-status-indicator">
                <span :class="{ 'ths-success': isLoggedIn, 'ths-error': !isLoggedIn }">
                  {{ isLoggedIn ? '已登录' : '未登录' }}
                </span>
                <button 
                  @click="checkLoginStatus" 
                  :disabled="thsLoading"
                  class="ths-btn ths-btn-secondary"
                >
                  检查登录状态
                </button>
                <button 
                  v-if="!isLoggedIn" 
                  @click="clickLogin" 
                  class="ths-btn ths-btn-primary"
                >
                  点击登录
                </button>
              </div>
            </div>
            
            <!-- 网页内容抓取区域 -->
            <div class="tonghuashun-section">
              <h4>网页内容</h4>
              <button 
                @click="capturePageContent" 
                :disabled="thsLoading"
                class="ths-btn ths-btn-secondary"
              >
                {{ thsLoading ? '抓取中...' : '抓取网页内容' }}
              </button>
              <div v-if="pageContent" class="ths-content-area">
                <pre>{{ pageContent }}</pre>
              </div>
            </div>
            
            <!-- 网络监听区域 -->
            <div class="tonghuashun-section">
              <h4>网络监听</h4>
              <div class="ths-controls">
                <button 
                  @click="toggleNetworkListening" 
                  class="ths-btn"
                  :class="isListening ? 'ths-btn-danger' : 'ths-btn-success'"
                  :disabled="thsLoading"
                >
                  {{ thsLoading ? '处理中...' : (isListening ? '停止监听' : '开始监听') }}
                </button>
                <button 
                  @click="clearNetworkData" 
                  :disabled="networkData.length === 0"
                  class="ths-btn ths-btn-secondary"
                >
                  清空数据
                </button>
                <span class="ths-status-indicator">
                  <span :class="{ 'ths-success': isListening, 'ths-error': !isListening }">
                    {{ isListening ? '监听中' : '未监听' }}
                  </span>
                </span>
              </div>
              
              <!-- 数据统计信息 
              <div v-if="networkDataStats.totalCount > 0" class="ths-data-stats">
                <div class="stats-grid">
                  <div class="stat-item">
                    <span class="stat-label">总数据量:</span>
                    <span class="stat-value">{{ networkDataStats.totalCount }}条</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">显示条数:</span>
                    <span class="stat-value">{{ networkDataStats.displayCount }}条</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">数据长度:</span>
                    <span class="stat-value">{{ networkDataStats.totalLength }}字符</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">第一股票:</span>
                    <span class="stat-value">{{ networkDataStats.firstStockCode || '未识别' }}</span>
                  </div>
                </div>
              </div>-->
              
              <!-- 网络数据显示 
              <div v-if="displayedNetworkData.length > 0" class="ths-network-data">
                <h5>股票数据 (显示前{{ displayedNetworkData.length }}条，共{{ networkDataStats.totalCount }}条)</h5>
                <div v-for="data in displayedNetworkData" :key="data.id" class="ths-data-item">
                  <div class="ths-data-header">
                    <span class="ths-timestamp">{{ new Date(data.timestamp).toLocaleTimeString() }}</span>
                    <span class="ths-url">{{ data.url }}</span>
                    <span class="ths-data-size">({{ data.dataLength }}字符)</span>
                  </div>
                  <div class="ths-data-content">
                    <pre>{{ formatJson(data.response) }}</pre>
                  </div>
                </div>
              </div>-->
            </div>
            
            <!-- 错误消息 -->
            <div v-if="thsError" class="ths-error">{{ thsError }}</div>
            
            <!-- 数据推送和清理区域 -->
            <div class="tonghuashun-section">
              <h4>数据管理</h4>
              <div class="ths-controls">
                <button 
                  @click="pushDataToBackend" 
                  :disabled="!networkData.length || isPushing"
                  class="ths-btn ths-btn-primary"
                >
                  {{ isPushing ? '推送中...' : '📤 推送数据到后端' }}
                </button>
                <button 
                  @click="clearTestData" 
                  :disabled="isClearing"
                  class="ths-btn ths-btn-danger"
                >
                  {{ isClearing ? '清理中...' : '🗑️ 清空测试数据' }}
                </button>
                <button 
                  @click="startProductionMode" 
                  class="ths-btn ths-btn-success"
                >
                  🚀 启动生产模式
                </button>
              </div>
              
              <div v-if="pushStatus" class="ths-status-message" :class="pushStatus.type">
                {{ pushStatus.message }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 系统状态Tab -->
      <div v-if="activeTab === 'status'" class="tab-content">
        <div class="section">
          <div class="config-card">
            <div class="section-header">
              <h3>监控状态面板</h3>
            </div>
            <MonitoringStatusPanel />
          </div>
        </div>
        <SystemStatus />
      </div>

      <!-- 会话管理Tab -->
      <div v-if="activeTab === 'session'" class="tab-content">
        <div class="section">
          <div class="config-card">
            <div class="section-header">
              <h3>平台会话管理</h3>
            </div>
            <SessionManager />
          </div>
        </div>
      </div>

      <!-- MCP测试Tab -->
      <div v-if="activeTab === 'mcp'" class="tab-content">
        <div class="section">
          <div class="config-card">
            <div class="section-header">
              <h3>🔧 MCP调试工具</h3>
              <p>Chrome扩展MCP功能测试平台</p>
            </div>

            <!-- 状态指示器 -->
            <div class="mcp-status-bar">
              <div class="status-item">
                <div class="status-indicator" :class="mcpStatus.connected ? 'connected' : 'disconnected'"></div>
                <span>{{ mcpStatus.text }}</span>
              </div>
              <div class="status-item">
                <div class="status-indicator" :class="extensionStatus.connected ? 'connected' : 'disconnected'"></div>
                <span>Chrome扩展</span>
              </div>
              <div class="status-item">
                <div class="status-indicator" :class="nativeStatus.connected ? 'connected' : 'disconnected'"></div>
                <span>Native Host</span>
              </div>
            </div>

            <!-- 快速测试场景 -->
            <div class="mcp-section">
              <h4>🚀 快速测试场景</h4>
              <div class="scenario-grid">
                <div class="scenario-card" @click="executeScenario('navigate')">
                  <div class="scenario-title">
                    <span>🌐</span>
                    打开澳客网
                  </div>
                  <div class="scenario-description">
                    打开 m.okooo.com 页面进行测试
                  </div>
                  <div class="scenario-params">
                    工具: chrome_navigate | URL: m.okooo.com
                  </div>
                </div>

                <div class="scenario-card" @click="executeScenario('alert')">
                  <div class="scenario-title">
                    <span>⚡</span>
                    插入Alert脚本
                  </div>
                  <div class="scenario-description">
                    在页面中插入并执行alert脚本
                  </div>
                  <div class="scenario-params">
                    工具: chrome_inject_script | 脚本: alert('测试')
                  </div>
                </div>

                <div class="scenario-card" @click="executeScenario('get-title')">
                  <div class="scenario-title">
                    <span>📄</span>
                    获取页面标题
                  </div>
                  <div class="scenario-description">
                    获取当前页面的标题信息
                  </div>
                  <div class="scenario-params">
                    工具: chrome_get_page_title
                  </div>
                </div>

                <div class="scenario-card" @click="executeScenario('get-tabs')">
                  <div class="scenario-title">
                    <span>🗂️</span>
                    获取所有标签页
                  </div>
                  <div class="scenario-description">
                    获取所有浏览器标签页信息
                  </div>
                  <div class="scenario-params">
                    工具: get_windows_and_tabs
                  </div>
                </div>
              </div>
            </div>

            <!-- 参数配置区域 -->
            <div class="mcp-section">
              <h4>⚙️ 参数配置</h4>
              <div class="parameter-form">
                <div class="form-group">
                  <label class="form-label">
                    <span>🔧</span>
                    工具名称
                  </label>
                  <input 
                    type="text" 
                    class="form-input" 
                    v-model="mcpToolName" 
                    placeholder="例如: chrome_navigate"
                  />
                </div>

                <div class="form-group">
                  <label class="form-label">
                    <span>📝</span>
                    参数 (JSON格式)
                  </label>
                  <textarea 
                    class="form-input form-textarea" 
                    v-model="mcpToolParams" 
                    placeholder='{"url": "https://example.com"}'
                    rows="4"
                  ></textarea>
                  <div v-if="mcpJsonError" class="json-error">{{ mcpJsonError }}</div>
                </div>
              </div>
            </div>

            <!-- 执行按钮区域 -->
            <div class="mcp-section">
              <div class="execute-buttons">
                <button 
                  class="ths-btn ths-btn-primary" 
                  @click="executeMCPTool" 
                  :disabled="mcpLoading"
                >
                  <span>🚀</span>
                  {{ mcpLoading ? '执行中...' : '执行工具' }}
                </button>
                <button 
                  class="ths-btn ths-btn-secondary" 
                  @click="connectMCP" 
                  :disabled="mcpLoading"
                >
                  <span>🔌</span>
                  连接MCP
                </button>
                <button 
                  class="ths-btn ths-btn-success" 
                  @click="validateMCPParams" 
                  :disabled="mcpLoading"
                >
                  <span>✅</span>
                  验证参数
                </button>
                <button 
                  class="ths-btn ths-btn-info" 
                  @click="testMCPPing" 
                  :disabled="mcpLoading"
                >
                  <span>📡</span>
                  Ping测试
                </button>
                <button 
                  class="ths-btn ths-btn-warning" 
                  @click="getMCPToolsList" 
                  :disabled="mcpLoading"
                >
                  <span>📋</span>
                  获取工具列表
                </button>
              </div>
            </div>

            <!-- 结果显示区域 -->
            <div v-if="mcpResult" class="mcp-section">
              <h4>📊 执行结果</h4>
              <div class="mcp-result">
                <div class="result-header">
                  <span class="result-status" :class="mcpResult.success ? 'success' : 'error'">
                    {{ mcpResult.success ? '✅ 成功' : '❌ 失败' }}
                  </span>
                  <span class="result-time">{{ new Date(mcpResult.timestamp).toLocaleTimeString() }}</span>
                </div>
                <div class="result-content">
                  <pre>{{ formatMCPResult(mcpResult.data) }}</pre>
                </div>
              </div>
            </div>

            <!-- 工具列表显示 -->
            <div v-if="mcpToolsList.length > 0" class="mcp-section">
              <h4>🛠️ 可用工具列表</h4>
              <div class="tools-list">
                <div 
                  v-for="tool in mcpToolsList" 
                  :key="tool.name" 
                  class="tool-card"
                  @click="selectTool(tool)"
                >
                  <div class="tool-name">{{ tool.name }}</div>
                  <div class="tool-description">{{ tool.description }}</div>
                  <details v-if="tool.inputSchema">
                    <summary>参数说明</summary>
                    <pre>{{ JSON.stringify(tool.inputSchema, null, 2) }}</pre>
                  </details>
                </div>
              </div>
            </div>

            <!-- 错误消息 -->
            <div v-if="mcpError" class="mcp-error">{{ mcpError }}</div>
          </div>
        </div>
      </div>

      <!-- 配置管理Tab -->
      <div v-if="activeTab === 'config'" class="tab-content">
        <div class="section">
          <div class="config-card">
            <div class="section-header">
              <h3>系统配置</h3>
            </div>
            <div class="config-options">
              <div class="config-item">
                <label class="config-label">自动推送间隔 (秒):</label>
                <input 
                  v-model="autoPushInterval" 
                  type="number" 
                  min="1" 
                  max="60" 
                  class="config-input"
                />
              </div>
              <div class="config-item">
                <label class="config-label">最大数据缓存条数:</label>
                <input 
                  v-model="maxDataCache" 
                  type="number" 
                  min="10" 
                  max="1000" 
                  class="config-input"
                />
              </div>
              <div class="config-item">
                <label class="config-label">启用自动推送:</label>
                <input 
                  v-model="enableAutoPush" 
                  type="checkbox" 
                  class="config-checkbox"
                />
              </div>
              <div class="config-item">
                <label class="config-label">后端服务地址:</label>
                <input 
                  v-model="backendUrl" 
                  type="text" 
                  class="config-input"
                  placeholder="http://localhost:8000"
                />
              </div>
            </div>
            
            <div class="config-actions">
              <button @click="saveConfig" class="ths-btn ths-btn-primary">
                💾 保存配置
              </button>
              <button @click="resetConfig" class="ths-btn ths-btn-secondary">
                🔄 重置配置
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 澳客爬虫Tab -->
      <div v-if="activeTab === 'okooo'" class="tab-content">
        <div class="section">
          <div class="config-card">
            <div class="section-header">
              <h3>⚽ 澳客竞彩自动爬虫</h3>
              <p>自动遍历比赛列表和历史记录</p>
            </div>
            
            <!-- 比赛列表捕获按钮 -->
            <div class="list-capture-section">
              <h4>📋 比赛列表</h4>
              <p class="section-desc">打开比赛列表页面并捕获 HTML</p>
              <div class="list-capture-buttons">
                <button 
                  @click="openAndCaptureList"
                  :disabled="okoooListStatus.isCapturing"
                  class="ths-btn ths-btn-primary ths-btn-large"
                >
                  {{ okoooListStatus.isCapturing ? '捕获中...' : '📄 打开并捕获比赛列表' }}
                </button>
                <button 
                  @click="openListPage"
                  class="ths-btn ths-btn-secondary"
                >
                  🔗 打开比赛列表
                </button>
              </div>
              <div v-if="okoooListStatus.lastResult" class="list-result">
                <span :class="['result-badge', okoooListStatus.lastResult.success ? 'result-success' : 'result-error']">
                  {{ okoooListStatus.lastResult.success ? '✓' : '✗' }} {{ okoooListStatus.lastResult.message }}
                </span>
                <span v-if="okoooListStatus.lastResult.size" class="size-info">
                  ({{ formatSize(okoooListStatus.lastResult.size) }})
                </span>
              </div>
            </div>
            
            <!-- 当前页面 -->
            <div class="current-page">
              <span class="page-label">当前页面:</span>
              <span class="page-url" :class="{ 'url-valid': currentUrl?.includes('m.okooo.com') }">
                {{ currentUrl || '未检测到页面' }}
              </span>
            </div>
            
            <!-- 爬虫阶段 -->
            <div class="phase-indicator">
              <span :class="['phase-badge', `phase-${okoooCrawlerStatus.phase}`]">
                {{ getPhaseText(okoooCrawlerStatus.phase) }}
              </span>
            </div>
            
            <!-- 统计信息 -->
            <div class="crawler-stats">
              <div class="stat-grid">
                <div class="stat-item">
                  <span class="stat-label">比赛进度</span>
                  <span class="stat-value">{{ okoooCrawlerStatus.currentMatchIndex }}/{{ okoooCrawlerStatus.totalMatches }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">历史进度</span>
                  <span class="stat-value">{{ okoooCrawlerStatus.currentHistoryIndex }}/{{ okoooCrawlerStatus.totalHistory }}</span>
                </div>
                <div class="stat-item success">
                  <span class="stat-label">成功</span>
                  <span class="stat-value">{{ okoooCrawlerStatus.successCount }}</span>
                </div>
                <div class="stat-item error">
                  <span class="stat-label">失败</span>
                  <span class="stat-value">{{ okoooCrawlerStatus.errorCount }}</span>
                </div>
              </div>
            </div>
            
            <!-- 进度条 -->
            <div v-if="okoooCrawlerStatus.totalMatches > 0" class="progress-section">
              <div class="progress-bar large">
                <div 
                  class="progress-fill"
                  :style="{ width: `${(okoooCrawlerStatus.currentMatchIndex / okoooCrawlerStatus.totalMatches) * 100}%` }"
                ></div>
              </div>
              <span class="progress-text">
                {{ Math.round((okoooCrawlerStatus.currentMatchIndex / okoooCrawlerStatus.totalMatches) * 100) }}%
              </span>
            </div>
            
            <!-- 控制按钮 -->
            <div class="action-buttons">
              <button 
                @click="startOkoooCrawler"
                :disabled="okoooCrawlerStatus.isRunning || !currentUrl?.includes('m.okooo.com')"
                class="ths-btn ths-btn-success ths-btn-large"
              >
                {{ okoooCrawlerStatus.isRunning ? '爬取中...' : '🚀 开始自动爬取' }}
              </button>
              
              <button 
                @click="stopOkoooCrawler"
                :disabled="!okoooCrawlerStatus.isRunning"
                class="ths-btn ths-btn-danger ths-btn-large"
              >
                ⏹️ 停止爬取
              </button>
            </div>
            
            <!-- 让球盘爬取按钮 -->
            <div class="action-section">
              <h4>让球盘/指数爬取</h4>
              <p class="description">从数据库查询数据，爬取让球盘页面</p>
              <button 
                @click="startHandicapCrawler"
                :disabled="handicapCrawlerStatus.isRunning"
                class="ths-btn ths-btn-primary ths-btn-large"
              >
                {{ handicapCrawlerStatus.isRunning ? '爬取中...' : '📊 爬取让球盘' }}
              </button>
              
              <div v-if="handicapCrawlerStatus.totalCount > 0" class="stats-row">
                <div class="stat-item">
                  <span class="stat-label">进度</span>
                  <span class="stat-value">{{ handicapCrawlerStatus.currentIndex }}/{{ handicapCrawlerStatus.totalCount }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">成功</span>
                  <span class="stat-value success">{{ handicapCrawlerStatus.successCount }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">失败</span>
                  <span class="stat-value error">{{ handicapCrawlerStatus.errorCount }}</span>
                </div>
              </div>
            </div>
            
            <!-- 结果列表 -->
            <div v-if="okoooCrawlerStatus.results && okoooCrawlerStatus.results.length > 0" class="results-section">
              <h4>爬取结果 ({{ okoooCrawlerStatus.results.length }})</h4>
              <div class="results-scroll">
                <div 
                  v-for="(result, index) in okoooCrawlerStatus.results.slice(-30)" 
                  :key="index"
                  :class="['result-item', `result-${result.status}`]"
                >
                  <span class="match-id">#{{ result.matchId }}</span>
                  <span class="status-icon">
                    {{ result.status === 'success' ? '✓' : (result.status === 'error' ? '✗' : '...') }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 实时日志 -->
            <div class="log-section">
              <div class="section-header-small">
                <h4>
                  <span class="status-dot" :class="{ 'active': isLogStreamActive }"></span>
                  实时日志
                </h4>
                <button @click="clearOkoooLogs" class="text-btn">清空</button>
              </div>
              <div ref="logContainer" class="log-container">
                <div v-if="okoooLogs.length === 0" class="empty-logs">等待日志...</div>
                <div v-for="(log, index) in okoooLogs" :key="index" :class="['log-item', log.level]">
                  <span class="log-time">[{{ log.timestamp }}]</span>
                  <span class="log-msg">{{ log.message }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- 数据详情模态框 -->
    <div v-if="showModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>数据详情</h3>
          <button @click="closeModal" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div class="modal-section">
            <h4>URL:</h4>
            <div class="modal-url">{{ selectedData?.url }}</div>
          </div>
          <div class="modal-section">
            <h4>时间戳:</h4>
            <div class="modal-timestamp">{{ selectedData?.timestamp }}</div>
          </div>
          <div class="modal-section">
            <h4>响应数据:</h4>
            <pre class="modal-data">{{ formatJson(selectedData?.response) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import {
  initializeMCPSession,
  getChromeWebContent,
  parseFootballMatches,
  generateFootballReport,
} from '../../utils/football-parser.js';
import MonitoringStatusPanel from '../../components/MonitoringStatusPanel.vue';
import SystemStatus from './components/SystemStatus.vue';
import WencaiDataCapture from './components/WencaiDataCapture.vue';
import SessionManager from './components/SessionManager.vue';
interface TemplateField {
  id: string;
  name: string;
  description: string;
  regex: string;
  note: string;
}

// 响应式数据
const currentUrl = ref<string>('');
const error = ref<string>('');
const isLoading = ref<boolean>(false);
const isLoadingOriginal = ref<boolean>(false);
const isLoadingTemplate = ref<boolean>(false);
const footballMatches = ref<any[]>([]);
const originalMatches = ref<any[]>([]);
const templateMatches = ref<any[]>([]);
const regexRules = ref<any[]>([]);
const originalRegexRules = ref<any[]>([]);
const showRawDataModal = ref<boolean>(false);
const selectedMatchRawData = ref<string>('');
const templateFields = ref<TemplateField[]>([]);
const tableHeaders = ref<string[]>([]);
const activeTab = ref<string>('monitor'); // 默认显示数据监控tab
const showRegexRules = ref<boolean>(false); // 默认隐藏正则表达式规则

// Tab导航配置
const tabs = ref([
  { id: 'monitor', name: '数据监控' },
  { id: 'status', name: '系统状态' },
  { id: 'session', name: '会话管理' },
  { id: 'mcp', name: 'MCP测试' },
  { id: 'okooo', name: '澳客爬虫' },
  { id: 'config', name: '配置管理' }
]);

// 配置管理相关响应式数据
const autoPushInterval = ref<number>(5); // 自动推送间隔（秒）
const maxDataCache = ref<number>(100); // 最大数据缓存条数
const enableAutoPush = ref<boolean>(true); // 启用自动推送
const backendUrl = ref<string>('http://localhost:8000'); // 后端服务地址

// 同花顺相关响应式数据
const isLoggedIn = ref<boolean>(false);
const isListening = ref<boolean>(false);
const pageContent = ref<string>('');
const networkData = ref<any[]>([]);
const allNetworkData = ref<any[]>([]); // 存储所有原始数据
const thsLoading = ref<boolean>(false);
const thsError = ref<string>('');
const currentTabId = ref<number | undefined>();

// 新增的响应式数据
const showModal = ref<boolean>(false);
const selectedData = ref<any>(null);
const isPushing = ref<boolean>(false);
const isClearing = ref<boolean>(false);
const pushStatus = ref<any>(null);

// MCP测试相关响应式数据
const mcpToolName = ref<string>('');
const mcpToolParams = ref<string>('{}');
const mcpJsonError = ref<string>('');
const mcpLoading = ref<boolean>(false);
const mcpError = ref<string>('');
const mcpResult = ref<any>(null);
const mcpToolsList = ref<any[]>([]);
const mcpStatus = ref({ connected: false, text: 'MCP服务' });
const extensionStatus = ref({ connected: true, text: 'Chrome扩展' });
const nativeStatus = ref({ connected: false, text: 'Native Host' });

// MCP服务器配置
const MCP_SERVER_URL = 'http://localhost:56889';

// Okooo crawler status
interface CrawlerStatus {
  isRunning: boolean;
  phase: 'idle' | 'matches' | 'history' | 'completed';
  totalMatches: number;
  currentMatchIndex: number;
  totalHistory: number;
  currentHistoryIndex: number;
  successCount: number;
  errorCount: number;
  results: Array<{
    matchId: string;
    url: string;
    status: 'pending' | 'success' | 'error';
  }>;
}

const okoooCrawlerStatus = ref<CrawlerStatus>({
  isRunning: false,
  phase: 'idle',
  totalMatches: 0,
  currentMatchIndex: 0,
  totalHistory: 0,
  currentHistoryIndex: 0,
  successCount: 0,
  errorCount: 0,
  results: []
});

interface OkoooListStatus {
  isCapturing: boolean;
  lastResult: { success: boolean; message: string; size?: number } | null;
}

const okoooListStatus = ref<OkoooListStatus>({
  isCapturing: false,
  lastResult: null
});

// Handicap crawler status
interface HandicapCrawlerStatus {
  isRunning: boolean;
  phase: 'idle' | 'query' | 'processing' | 'completed';
  totalCount: number;
  currentIndex: number;
  successCount: number;
  errorCount: number;
}

const handicapCrawlerStatus = ref<HandicapCrawlerStatus>({
  isRunning: false,
  phase: 'idle',
  totalCount: 0,
  currentIndex: 0,
  successCount: 0,
  errorCount: 0
});

// 实时日志相关
interface LogEntry {
  message: string;
  level: string;
  timestamp: string;
}

const okoooLogs = ref<LogEntry[]>([]);
const isLogStreamActive = ref(false);
let eventSource: EventSource | null = null;

const clearOkoooLogs = () => {
  okoooLogs.value = [];
};

const setupSSE = () => {
  if (eventSource) {
    eventSource.close();
  }

  const serverUrl = backendUrl.value || 'http://localhost:8000';
  const sseUrl = `${serverUrl}/api/sse/subscribe`;
  
  try {
    eventSource = new EventSource(sseUrl);
    
    eventSource.onopen = () => {
      console.log('SSE连接已建立');
      isLogStreamActive.value = true;
    };
    
    eventSource.addEventListener('log', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        okoooLogs.value.unshift({
          message: data.message,
          level: data.level || 'info',
          timestamp: data.timestamp || new Date().toLocaleTimeString()
        });
        
        // 保持日志数量在合理范围
        if (okoooLogs.value.length > 200) {
          okoooLogs.value = okoooLogs.value.slice(0, 200);
        }
      } catch (e) {
        console.error('解析日志数据失败:', e);
      }
    });
    
    eventSource.onerror = (error) => {
      console.error('SSE连接错误:', error);
      isLogStreamActive.value = false;
      // 尝试重连 logic could go here, but EventSource usually auto-reconnects
    };
    
  } catch (e) {
    console.error('建立SSE连接失败:', e);
    isLogStreamActive.value = false;
  }
};

let crawlerStatusTimer: number | null = null;

// 调试模式配置 - 设为false可大幅减少console.log输出
const DEBUG_MODE = false;

// 计算属性：处理网络数据显示逻辑
const displayedNetworkData = computed(() => {
  // 只显示前5条数据
  const displayData = networkData.value.slice(0, 5);
  if (DEBUG_MODE) {
    console.log('显示的网络数据条数:', displayData.length);
    console.log('原始网络数据条数:', networkData.value.length);
  }
  
  return displayData.map(data => ({
    ...data,
    dataLength: JSON.stringify(data.response).length
  }));
});

// 计算属性：网络数据统计信息
const networkDataStats = computed(() => {
  const totalCount = allNetworkData.value.length;
  const displayCount = Math.min(networkData.value.length, 5);
  const totalLength = allNetworkData.value.reduce((sum, data) => {
    return sum + JSON.stringify(data.response).length;
  }, 0);
  
  // 尝试从第一条数据中提取股票代码
  let firstStockCode = '';
  if (networkData.value.length > 0) {
    try {
      const firstData = networkData.value[0].response;
      if (firstData && typeof firstData === 'object') {
        // 尝试多种可能的股票代码字段
        firstStockCode = firstData.code || firstData.symbol || firstData.stock_code || 
                        (firstData.data && firstData.data[0] && firstData.data[0].code) || '';
      }
    } catch (e) {
      console.warn('提取股票代码失败:', e);
    }
  }
  
  return {
    totalCount,
    displayCount,
    totalLength,
    firstStockCode
  };
});

// 从test-rules.json加载解析规则
const loadTestRules = async () => {
  try {
    // 从Chrome扩展的public目录加载规则文件
    const response = await fetch(chrome.runtime.getURL('test-rules.json'));
    if (response.ok) {
      const testRulesData = await response.json();
      console.log('从test-rules.json加载规则:', testRulesData.parsingRules.length, '条规则');
      return testRulesData.parsingRules;
    }
  } catch (error) {
    console.error('加载test-rules.json失败:', error);
  }
  
  // 如果加载失败，返回空数组
  return [];
};

// 将test-rules.json的规则转换为页面显示格式
const convertTestRulesToDisplayFormat = (testRules: any[]) => {
  return testRules.map((rule: any) => ({
    field: rule.fieldName,
    label: rule.description || rule.name,
    description: rule.description,
    pattern: rule.regex,
    placeholder: `${rule.description}正则表达式`,
  }));
};

// 正则表达式规则定义
const initRegexRules = async () => {
  const testRules = await loadTestRules();
  const convertedRules = convertTestRulesToDisplayFormat(testRules);
  
  originalRegexRules.value = convertedRules;

  regexRules.value = convertedRules;
};

// 生成唯一ID
const generateId = (): string => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
};

// 初始化默认字段 - 从test-rules.json读取数据
const initializeDefaultFields = async () => {
  try {
    const response = await fetch(chrome.runtime.getURL('test-rules.json'));
    const testRulesData = await response.json();
    
    // 将test-rules.json的数据转换为模板字段格式
    templateFields.value = testRulesData.parsingRules.map(rule => ({
      id: generateId(),
      name: rule.description, // 使用description作为显示名称
      description: rule.description,
      regex: rule.regex,
      note: rule.fieldName,
    }));
    
    console.log('从test-rules.json初始化模板字段:', templateFields.value.length, '个字段');
    updateTableHeaders();
  } catch (error) {
    console.error('初始化模板字段失败:', error);
    // 如果加载失败，使用空数组
    templateFields.value = [];
    updateTableHeaders();
  }
};

// 添加新字段
const addField = () => {
  templateFields.value.push({
    id: generateId(),
    name: '新字段',
    description: '请输入字段说明',
    regex: '',
    note: '请添加备注',
  });
  updateTableHeaders();
};

// 删除字段
const removeField = (index: number) => {
  if (templateFields.value.length > 1) {
    templateFields.value.splice(index, 1);
    updateTableHeaders();
    updateParseResults();
  }
};

// 更新表头
const updateTableHeaders = () => {
  tableHeaders.value = ['序号', ...templateFields.value.map((field) => field.name), '查看原始数据'];
};

// 保存模板
const saveTemplate = () => {
  const template = {
    fields: templateFields.value,
    updatedAt: new Date().toISOString(),
  };

  chrome.storage.local
    .set({ crawlerTemplate: template })
    .then(() => {
      console.log('模板保存成功');
    })
    .catch((error) => {
      console.error('模板保存失败:', error);
    });
};

// 重置模板
const resetTemplate = async () => {
  await initializeDefaultFields();
};

// 加载保存的模板
const loadTemplate = async () => {
  try {
    const result = await chrome.storage.local.get('crawlerTemplate');
    if (result.crawlerTemplate && result.crawlerTemplate.fields) {
      templateFields.value = result.crawlerTemplate.fields;
    } else {
      await initializeDefaultFields();
    }
    updateTableHeaders();
  } catch (error) {
    console.error('加载模板失败:', error);
    await initializeDefaultFields();
  }
};

// 获取当前标签页URL
const getCurrentTabUrl = async (): Promise<string> => {
  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    return tabs[0]?.url || '';
  } catch (err) {
    console.error('Failed to get current tab URL:', err);
    return '';
  }
};

// initializeMCPSession 函数已从 utils/football-parser.js 导入

// getChromeWebContent 函数已从 utils/football-parser.js 导入

// 根据模板字段动态解析数据
const parseFootballMatches = (htmlContent: string): any[] => {
  console.debug('开始解析足球比赛数据，HTML内容长度:', htmlContent?.length || 0);

  if (!htmlContent || typeof htmlContent !== 'string') {
    console.error('HTML内容无效:', typeof htmlContent, htmlContent);
    return [];
  }

  if (templateFields.value.length === 0) {
    console.warn('模板字段为空，无法解析数据');
    return [];
  }

  const matches: any[] = [];

  // 提取日期信息
  let matchDate = '';
  const dateMatch = htmlContent.match(/<p class="listtoptxt fl font12"[^>]*>([^<]+)</);
  if (dateMatch) {
    const dateText = dateMatch[1].trim();
    console.debug('提取到的日期文本:', dateText);

    // 解析日期格式，例如："2025年01月23日 星期四"
    const yearMatch = dateText.match(/(\d{4})年/);
    const monthMatch = dateText.match(/(\d{1,2})月/);
    const dayMatch = dateText.match(/(\d{1,2})日/);

    if (yearMatch && monthMatch && dayMatch) {
      const year = yearMatch[1];
      const month = monthMatch[1].padStart(2, '0');
      const day = dayMatch[1].padStart(2, '0');
      matchDate = `${year}-${month}-${day}`;
      console.debug('解析后的日期:', matchDate);
    }
  }

  // 使用第一个字段（通常是比赛ID）来确定比赛数量
  const firstField = templateFields.value[0];
  if (!firstField || !firstField.regex) {
    console.warn('第一个字段的正则表达式为空');
    return [];
  }

  try {
    const firstRegex = new RegExp(firstField.regex, 'g');
    const firstMatches = [...htmlContent.matchAll(firstRegex)];
    console.debug(`使用字段"${firstField.name}"找到${firstMatches.length}个匹配项`);

    // 为每个匹配项创建一个比赛对象
    firstMatches.forEach((firstMatch, index) => {
      const match: any = {
        index: index + 1,
        rawData: '', // 用于调试的原始数据
      };

      // 为每个模板字段提取数据
      templateFields.value.forEach((field, fieldIndex) => {
        if (!field.regex) {
          match[field.name] = '';
          return;
        }

        try {
          const regex = new RegExp(field.regex, 'g');
          const fieldMatches = [...htmlContent.matchAll(regex)];

          if (fieldMatches[index] && fieldMatches[index][1]) {
            let value = fieldMatches[index][1].trim();

            // 如果是时间字段且有日期，则添加日期前缀
            if (field.name.includes('时间') && matchDate && !value.includes('-')) {
              value = `${matchDate} ${value}`;
            }

            match[field.name] = value;
          } else {
            match[field.name] = '';
          }
        } catch (regexError) {
          console.error(`字段"${field.name}"的正则表达式错误:`, regexError);
          match[field.name] = '';
        }
      });

      // 生成原始数据用于调试
      const firstValue = firstMatch[1] || firstMatch[0];
      const startPos = Math.max(0, htmlContent.indexOf(firstValue) - 200);
      const endPos = Math.min(htmlContent.length, htmlContent.indexOf(firstValue) + 500);
      match.rawData = htmlContent.substring(startPos, endPos);

      matches.push(match);
    });
  } catch (error) {
    console.error('解析过程中发生错误:', error);
    return [];
  }

  console.debug('解析完成，共找到', matches.length, '场比赛');
  return matches;
};

// 存储网页内容
const webContent = ref<string>('');

// 实时更新解析结果
const updateParseResults = () => {
  if (webContent.value) {
    footballMatches.value = parseFootballMatches(webContent.value);
  }
};

// 使用原始规则解析数据的函数
const parseFootballMatchesWithOriginalRules = (content: string, rules: any[]): any[] => {
  const matches: any[] = [];

  try {
    console.log('🚀 开始使用原始规则解析足球比赛数据...');
    console.log('📋 可用规则数量:', rules.length);
    console.log('📄 HTML内容长度:', content.length);
    
    // 调试：显示HTML内容的前500个字符
    console.log('🔍 HTML内容预览:', content.substring(0, 500));
    
    // 调试：检查是否包含关键标识
    const hasMatchData = content.includes('MatchID') || content.includes('matchid') || content.includes('比赛') || content.includes('ctrl_eachmatch');
    console.log('🎯 HTML是否包含比赛数据标识:', hasMatchData);
    
    // 调试：检查关键CSS类的存在
    const hasOddsData = content.includes('ctrl_odds') || content.includes('betway');
    console.log('🎲 HTML是否包含赔率数据标识:', hasOddsData);
    
    // 创建规则映射，便于查找
    const ruleMap = new Map();
    rules.forEach(rule => {
      ruleMap.set(rule.fieldName, rule.regex);
      console.log(`📝 规则 ${rule.fieldName}: ${rule.regex}`);
    });

    // 提取日期信息
    let matchDate = '';
    const dateRegex = ruleMap.get('matchDate') || '<p[^>]*class="listtoptxt fl font12"[^>]*>[\\s\\S]*?&nbsp;&nbsp;([0-9]{4}-[0-9]{2}-[0-9]{2})&nbsp;&nbsp;';
    console.log('🔍 使用日期正则:', dateRegex);
    
    try {
      const datePattern = new RegExp(dateRegex, 'i');
      const dateMatch = content.match(datePattern);
      if (dateMatch) {
        matchDate = dateMatch[1];
        console.log('✅ 提取到日期:', matchDate);
      } else {
        console.log('❌ 未找到日期信息');
      }
    } catch (dateError) {
      console.error('❌ 日期正则表达式错误:', dateError);
    }

    // 使用比赛容器来分割每场比赛
    const containerRegex = ruleMap.get('matchContainer') || '<div[^>]*class="[^"]*clearfix center listItem ctrl_eachmatch[^"]*"[^>]*>[\\s\\S]*?</div></div></div>';
    console.log('🔍 使用容器正则:', containerRegex);
    
    let matchBlocks = [];
    try {
      const containerPattern = new RegExp(containerRegex, 'g');
      matchBlocks = content.match(containerPattern) || [];
      console.log(`✅ 主要方案找到 ${matchBlocks.length} 个比赛容器`);
      
      // 如果主要方案找到的数据少于预期，尝试多种备用方案
      if (matchBlocks.length < 5) {
        console.log('🔄 主要方案找到的比赛数量较少，尝试备用方案...');
        
        // 备用方案1: 更简单的匹配
        const fallbackPattern1 = /<div[^>]*class="[^"]*ctrl_eachmatch[^"]*"[^>]*>[\s\S]*?(?=<div[^>]*class="[^"]*ctrl_eachmatch[^"]*"|$)/g;
        const fallbackBlocks1 = content.match(fallbackPattern1) || [];
        console.log(`🔄 备用方案1找到 ${fallbackBlocks1.length} 个比赛块`);
        
        // 备用方案2: 只匹配包含ctrl_eachmatch的div
        const fallbackPattern2 = /<div[^>]*ctrl_eachmatch[^>]*>[\s\S]*?(?=<div[^>]*ctrl_eachmatch|<\/body>|$)/g;
        const fallbackBlocks2 = content.match(fallbackPattern2) || [];
        console.log(`🔄 备用方案2找到 ${fallbackBlocks2.length} 个比赛块`);
        
        // 备用方案3: 查找所有包含比赛关键信息的div
        const fallbackPattern3 = /<div[^>]*>[\s\S]*?ctrl_homename[\s\S]*?ctrl_awayname[\s\S]*?(?=<div[^>]*ctrl_homename|<\/body>|$)/g;
        const fallbackBlocks3 = content.match(fallbackPattern3) || [];
        console.log(`🔄 备用方案3找到 ${fallbackBlocks3.length} 个比赛块`);
        
        // 选择找到最多比赛的方案
        if (fallbackBlocks1.length > matchBlocks.length) {
          matchBlocks = fallbackBlocks1;
          console.log(`✅ 使用备用方案1，找到 ${matchBlocks.length} 个比赛`);
        }
        if (fallbackBlocks2.length > matchBlocks.length) {
          matchBlocks = fallbackBlocks2;
          console.log(`✅ 使用备用方案2，找到 ${matchBlocks.length} 个比赛`);
        }
        if (fallbackBlocks3.length > matchBlocks.length) {
          matchBlocks = fallbackBlocks3;
          console.log(`✅ 使用备用方案3，找到 ${matchBlocks.length} 个比赛`);
        }
      }
    } catch (containerError) {
      console.error('❌ 容器正则表达式错误:', containerError);
      // 最后的备用方案
      const finalFallbackPattern = /<div[^>]*ctrl_eachmatch[^>]*>[\s\S]*?(?=<div[^>]*ctrl_eachmatch|$)/g;
      matchBlocks = content.match(finalFallbackPattern) || [];
      console.log(`🔄 最终备用方案找到 ${matchBlocks.length} 个比赛块`);
    }

    if (!matchBlocks || matchBlocks.length === 0) {
      console.warn('❌ 所有方案都未找到比赛数据块');
      console.log('🔍 尝试在HTML中查找ctrl_eachmatch关键字...');
      const keywordMatches = content.match(/ctrl_eachmatch/g) || [];
      console.log(`🔍 在HTML中找到 ${keywordMatches.length} 个ctrl_eachmatch关键字`);
      return matches;
    }

    console.log(`🎯 最终确定找到 ${matchBlocks.length} 场比赛，开始逐一解析...`);

    // 为每场比赛提取数据
    matchBlocks.forEach((matchHtml, index) => {
      const match: any = {
        index: index + 1,
        matchId: '',
        matchNumber: '',
        league: '',
        matchTime: '',
        homeTeam: '',
        homeRank: '',
        awayTeam: '',
        awayRank: '',
        winOdds: null,
        drawOdds: null,
        loseOdds: null,
        handicap: '',
        handicapWinOdds: null,
        handicapDrawOdds: null,
        handicapLoseOdds: null,
        basicInfo: {
          league: '',
          time: '',
        },
        teams: {
          home: { name: '', rank: '' },
          away: { name: '', rank: '' },
        },
        odds: { win: null, draw: null, lose: null },
        handicapOdds: { win: null, draw: null, lose: null, handicap: '' },
        links: {
          handicap: '',
          exchanges: '',
          game: '',
          form: '',
          odds: '',
          history: '',
        },
        moreGames: 0,
        rawData: matchHtml,
        rawHtml: matchHtml, // 用于显示原始数据
      };

      console.log(`📋 解析第${index + 1}场比赛...`);
      console.log(`🔍 比赛HTML长度: ${matchHtml.length}`);
      console.log(`🔍 比赛HTML预览: ${matchHtml.substring(0, 200)}...`);
      
      // 检查这场比赛的HTML是否包含赔率相关标识
      const hasOddsInMatch = matchHtml.includes('ctrl_odds') || matchHtml.includes('betway');
      console.log(`🎲 当前比赛是否包含赔率标识: ${hasOddsInMatch}`);

      // 1. 提取MatchID
      const matchIdRegex = ruleMap.get('matchId') || 'MatchID=([0-9]+)';
      try {
        const matchIdPattern = new RegExp(matchIdRegex, 'i');
        const matchIdMatch = matchHtml.match(matchIdPattern);
        if (matchIdMatch) {
          match.matchId = matchIdMatch[1].trim();
          console.log(`    ✅ MatchID: ${match.matchId}`);
        } else {
          console.log(`    ❌ 未找到MatchID`);
        }
      } catch (error) {
        console.error(`    ❌ MatchID正则错误:`, error);
      }

      // 2. 提取比赛序号
      const matchNumberRegex = ruleMap.get('matchNumber') || '<p[^>]*class="xuhao"[^>]*>\\s*([^<\\s]+)\\s*</p>';
      try {
        const matchNumberPattern = new RegExp(matchNumberRegex, 'i');
        const matchNumberMatch = matchHtml.match(matchNumberPattern);
        if (matchNumberMatch) {
          match.matchNumber = matchNumberMatch[1].trim();
          console.log(`    ✅ 比赛序号: ${match.matchNumber}`);
        } else {
          console.log(`    ❌ 未找到比赛序号`);
        }
      } catch (error) {
        console.error(`    ❌ 比赛序号正则错误:`, error);
      }

      // 3. 提取联赛名称
      const leagueRegex = ruleMap.get('league') || '<a[^>]*class="liansai"[^>]*>[\\s]*([^<]+?)[\\s]*</a>';
      try {
        const leaguePattern = new RegExp(leagueRegex, 'i');
        const leagueMatch = matchHtml.match(leaguePattern);
        if (leagueMatch) {
          const leagueValue = leagueMatch[1].trim();
          match.basicInfo.league = leagueValue;
          match.league = leagueValue; // 平铺结构
          console.log(`    ✅ 联赛: ${leagueValue}`);
        } else {
          console.log(`    ❌ 未找到联赛名称`);
        }
      } catch (error) {
        console.error(`    ❌ 联赛正则错误:`, error);
      }

      // 4. 提取比赛时间
      const timeRegex = ruleMap.get('matchTime') || '<time[^>]*class="timetxt"[^>]*>(\\d{2}:\\d{2})</time>';
      try {
        const timePattern = new RegExp(timeRegex, 'i');
        const timeMatch = matchHtml.match(timePattern);
        if (timeMatch) {
          const timeValue = timeMatch[1].trim();
          match.basicInfo.time = timeValue;
          match.matchTime = timeValue; // 平铺结构
          console.log(`    ✅ 比赛时间: ${timeValue}`);
        } else {
          console.log(`    ❌ 未找到比赛时间`);
        }
      } catch (error) {
        console.error(`    ❌ 比赛时间正则错误:`, error);
      }

      // 5. 提取球队信息
      // 主队名称
      const homeTeamRegex = ruleMap.get('homeTeam') || '<em[^>]*class="ctrl_homename"[^>]*>([^<]+)</em>';
      try {
        const homeTeamPattern = new RegExp(homeTeamRegex, 'i');
        const homeTeamMatch = matchHtml.match(homeTeamPattern);
        if (homeTeamMatch) {
          const homeTeamValue = homeTeamMatch[1].trim();
          match.teams.home.name = homeTeamValue;
          match.homeTeam = homeTeamValue; // 平铺结构
          console.log(`    ✅ 主队名称: ${homeTeamValue}`);
        } else {
          console.log(`    ❌ 未找到主队名称`);
        }
      } catch (error) {
        console.error(`    ❌ 主队名称正则错误:`, error);
      }
      
      // 主队排名
      const homeRankRegex = ruleMap.get('homeRank') || '<cite class="pm">\\[([^\\]]+)\\]([^<]*)</cite><em class="ctrl_homename">';
      try {
        const homeRankPattern = new RegExp(homeRankRegex, 'i');
        const homeRankMatch = matchHtml.match(homeRankPattern);
        if (homeRankMatch) {
          const homeRankValue = homeRankMatch[1].trim();
          match.teams.home.rank = homeRankValue;
          match.homeRank = homeRankValue; // 平铺结构
          console.log(`    ✅ 主队排名: ${homeRankValue}`);
        } else {
          console.log(`    ❌ 未找到主队排名`);
        }
      } catch (error) {
        console.error(`    ❌ 主队排名正则错误:`, error);
      }

      // 客队名称
      const awayTeamRegex = ruleMap.get('awayTeam') || '<em[^>]*class="ctrl_awayname"[^>]*>([^<]+)</em>';
      try {
        const awayTeamPattern = new RegExp(awayTeamRegex, 'i');
        const awayTeamMatch = matchHtml.match(awayTeamPattern);
        if (awayTeamMatch) {
          const awayTeamValue = awayTeamMatch[1].trim();
          match.teams.away.name = awayTeamValue;
          match.awayTeam = awayTeamValue; // 平铺结构
          console.log(`    ✅ 客队名称: ${awayTeamValue}`);
        } else {
          console.log(`    ❌ 未找到客队名称`);
        }
      } catch (error) {
        console.error(`    ❌ 客队名称正则错误:`, error);
      }
      
      // 客队排名
      const awayRankRegex = ruleMap.get('awayRank') || '<em class="ctrl_awayname">[^<]+</em>\\s*<cite class="pm">\\[([^\\]]+)\\]([^<]*)</cite>';
      try {
        const awayRankPattern = new RegExp(awayRankRegex, 'i');
        const awayRankMatch = matchHtml.match(awayRankPattern);
        if (awayRankMatch) {
          const awayRankValue = awayRankMatch[1].trim();
          match.teams.away.rank = awayRankValue;
          match.awayRank = awayRankValue; // 平铺结构
          console.log(`    ✅ 客队排名: ${awayRankValue}`);
        } else {
          console.log(`    ❌ 未找到客队排名`);
        }
      } catch (error) {
        console.error(`    ❌ 客队排名正则错误:`, error);
      }

      // 6. 提取胜平负赔率 (betway="0")
      console.log(`    🔍 开始提取赔率数据...`);
      console.log(`    📄 当前比赛HTML片段长度: ${matchHtml.length}`);
      
      // 更新赔率正则表达式以匹配澳客网当前结构
      const winOddsRegex = ruleMap.get('winOdds') || 'betway="0"[\\s\\S]*?<div[^>]*class="[^"]*listbetbtn[^"]*ctrl_betopt[^"]*"[^>]*>[\\s]*<p[^>]*class="[^"]*fl[^"]*font3[^"]*ctrl_txt[^"]*">胜</p>[\\s]*<p[^>]*class="[^"]*fr[^"]*gray9[^"]*ctrl_odds[^"]*">([\\d.]+)</p>';
      const drawOddsRegex = ruleMap.get('drawOdds') || 'betway="0"[\\s\\S]*?<div[^>]*class="[^"]*listbetbtn[^"]*ctrl_betopt[^"]*"[^>]*>[\\s]*<p[^>]*class="[^"]*fl[^"]*font3[^"]*ctrl_txt[^"]*">平</p>[\\s]*<p[^>]*class="[^"]*fr[^"]*gray9[^"]*ctrl_odds[^"]*">([\\d.]+)</p>';
      const loseOddsRegex = ruleMap.get('loseOdds') || 'betway="0"[\\s\\S]*?<div[^>]*class="[^"]*listbetbtn[^"]*ctrl_betopt[^"]*"[^>]*>[\\s]*<p[^>]*class="[^"]*fl[^"]*font3[^"]*ctrl_txt[^"]*">负</p>[\\s]*<p[^>]*class="[^"]*fr[^"]*gray9[^"]*ctrl_odds[^"]*">([\\d.]+)</p>';
      
      // 添加多种备用赔率正则表达式
      const fallbackOddsRegexes = [
        // 标准ctrl_odds类格式
        /<p[^>]*class="[^"]*ctrl_odds[^"]*"[^>]*>([\d.]+)<\/p>/g,
        // td标签中的数字
        /<td[^>]*>([\d.]+)<\/td>/g,
        // span标签中的数字
        /<span[^>]*>([\d.]+)<\/span>/g,
        // div标签中的数字
        /<div[^>]*>([\d.]+)<\/div>/g,
        // 简单数字格式（最后尝试，因为匹配范围太广）
        />([\d.]+)</g
      ];
      
      // 从HTML中提取所有可能的赔率数字
      function extractAllOdds(html) {
        const allOdds = [];
        console.log(`    🔍 开始使用备用正则提取赔率，HTML长度: ${html.length}`);
        fallbackOddsRegexes.forEach((regex, index) => {
          const matches = [...html.matchAll(regex)];
          console.log(`    📊 正则${index + 1}找到 ${matches.length} 个匹配`);
          matches.forEach(match => {
            const value = parseFloat(match[1]);
            if (value && value > 1 && value < 100) {
              allOdds.push({ value, source: `regex${index + 1}`, match: match[0] });
              console.log(`    ✅ 找到有效赔率: ${value} (来源: regex${index + 1})`);
            } else {
              console.log(`    ❌ 无效赔率值: ${value} (来源: regex${index + 1})`);
            }
          });
        });
        console.log(`    📈 总共提取到 ${allOdds.length} 个有效赔率`);
        return allOdds;
      }
      
      try {
        const winOddsPattern = new RegExp(winOddsRegex, 'i');
        const winOddsMatch = matchHtml.match(winOddsPattern);
        if (winOddsMatch) {
          const winOddsValue = parseFloat(winOddsMatch[1]) || null;
          match.odds.win = winOddsValue;
          match.winOdds = winOddsValue; // 平铺结构
          match.oddsWin = winOddsValue; // 表格绑定字段
          console.log(`    ✅ 胜赔率: ${winOddsValue}`);
        } else {
          console.log(`    ❌ 主正则未找到胜赔率，尝试备用正则...`);
          // 使用新的提取函数
          const allOdds = extractAllOdds(matchHtml);
          if (allOdds.length >= 3) {
            const winOddsValue = allOdds[0].value;
            match.odds.win = winOddsValue;
            match.winOdds = winOddsValue;
            match.oddsWin = winOddsValue;
            console.log(`    ✅ 备用方案找到胜赔率: ${winOddsValue} (来源: ${allOdds[0].source})`);
          } else {
            console.log(`    ❌ 备用方案未找到足够的赔率数据，只找到 ${allOdds.length} 个`);
          }
        }
      } catch (error) {
        console.error(`    ❌ 胜赔率正则错误:`, error);
      }
      
      try {
        const drawOddsPattern = new RegExp(drawOddsRegex, 'i');
        const drawOddsMatch = matchHtml.match(drawOddsPattern);
        if (drawOddsMatch) {
          const drawOddsValue = parseFloat(drawOddsMatch[1]) || null;
          match.odds.draw = drawOddsValue;
          match.drawOdds = drawOddsValue; // 平铺结构
          match.oddsDraw = drawOddsValue; // 表格绑定字段
          console.log(`    ✅ 平赔率: ${drawOddsValue}`);
        } else {
          console.log(`    ❌ 主正则未找到平赔率，尝试备用正则...`);
          // 使用新的提取函数
          const allOdds = extractAllOdds(matchHtml);
          if (allOdds.length >= 3) {
            const drawOddsValue = allOdds[1].value;
            match.odds.draw = drawOddsValue;
            match.drawOdds = drawOddsValue;
            match.oddsDraw = drawOddsValue;
            console.log(`    ✅ 备用方案找到平赔率: ${drawOddsValue} (来源: ${allOdds[1].source})`);
          } else {
            console.log(`    ❌ 备用方案未找到足够的赔率数据，只找到 ${allOdds.length} 个`);
          }
        }
      } catch (error) {
        console.error(`    ❌ 平赔率正则错误:`, error);
      }
      
      try {
        const loseOddsPattern = new RegExp(loseOddsRegex, 'i');
        const loseOddsMatch = matchHtml.match(loseOddsPattern);
        if (loseOddsMatch) {
          const loseOddsValue = parseFloat(loseOddsMatch[1]) || null;
          match.odds.lose = loseOddsValue;
          match.loseOdds = loseOddsValue; // 平铺结构
          match.oddsLose = loseOddsValue; // 表格绑定字段
          console.log(`    ✅ 负赔率: ${loseOddsValue}`);
        } else {
          console.log(`    ❌ 主正则未找到负赔率，尝试备用正则...`);
          // 使用新的提取函数
          const allOdds = extractAllOdds(matchHtml);
          if (allOdds.length >= 3) {
            const loseOddsValue = allOdds[2].value;
            match.odds.lose = loseOddsValue;
            match.loseOdds = loseOddsValue;
            match.oddsLose = loseOddsValue;
            console.log(`    ✅ 备用方案找到负赔率: ${loseOddsValue} (来源: ${allOdds[2].source})`);
          } else {
            console.log(`    ❌ 备用方案未找到足够的赔率数据，只找到 ${allOdds.length} 个`);
          }
        }
      } catch (error) {
        console.error(`    ❌ 负赔率正则错误:`, error);
      }

      // 7. 提取让球胜平负赔率 (betway="1")
      const handicapRegex = ruleMap.get('handicap') || '<em[^>]*data-v="([^"]+)"[^>]*>([^<]+)</em>';
      // 更新让球赔率正则表达式以匹配澳客网当前结构
      const handicapWinOddsRegex = ruleMap.get('handicapWinOdds') || 'betway="1"[\\s\\S]*?<div[^>]*class="[^"]*listbetbtn[^"]*ctrl_betopt[^"]*"[^>]*>[\\s]*<p[^>]*class="[^"]*fl[^"]*font3[^"]*ctrl_txt[^"]*">胜</p>[\\s]*<p[^>]*class="[^"]*fr[^"]*gray9[^"]*ctrl_odds[^"]*">([\\d.]+)</p>';
      const handicapDrawOddsRegex = ruleMap.get('handicapDrawOdds') || 'betway="1"[\\s\\S]*?<div[^>]*class="[^"]*listbetbtn[^"]*ctrl_betopt[^"]*"[^>]*>[\\s]*<p[^>]*class="[^"]*fl[^"]*font3[^"]*ctrl_txt[^"]*">平</p>[\\s]*<p[^>]*class="[^"]*fr[^"]*gray9[^"]*ctrl_odds[^"]*">([\\d.]+)</p>';
      const handicapLoseOddsRegex = ruleMap.get('handicapLoseOdds') || 'betway="1"[\\s\\S]*?<div[^>]*class="[^"]*listbetbtn[^"]*ctrl_betopt[^"]*"[^>]*>[\\s]*<p[^>]*class="[^"]*fl[^"]*font3[^"]*ctrl_txt[^"]*">负</p>[\\s]*<p[^>]*class="[^"]*fr[^"]*gray9[^"]*ctrl_odds[^"]*">([\\d.]+)</p>';
      
      // 提取让球数
      try {
        const handicapPattern = new RegExp(handicapRegex, 'i');
        const handicapMatch = matchHtml.match(handicapPattern);
        if (handicapMatch) {
          const handicapValue = handicapMatch[2] || handicapMatch[1]; // 使用第二个捕获组（让球数值）
          match.handicapOdds.handicap = handicapValue;
          match.handicap = handicapValue; // 平铺结构
          match.handicapValue = handicapValue; // 表格绑定字段
          console.log(`    ✅ 让球数: ${handicapValue}`);
        } else {
          console.log(`    ❌ 未找到让球数`);
          console.log(`    🔍 尝试备用让球数正则...`);
          // 备用正则表达式
          const fallbackHandicapRegex = /<em[^>]*>([+-]?\d+(?:\.\d+)?)<\/em>|>([+-]?\d+(?:\.\d+)?)<\/em>/;
          const fallbackMatch = matchHtml.match(fallbackHandicapRegex);
          if (fallbackMatch) {
            const handicapValue = fallbackMatch[1] || fallbackMatch[2];
            match.handicapOdds.handicap = handicapValue;
            match.handicap = handicapValue;
            match.handicapValue = handicapValue; // 表格绑定字段
            console.log(`    ✅ 备用方案找到让球数: ${handicapValue}`);
          }
        }
      } catch (error) {
        console.error(`    ❌ 让球数正则错误:`, error);
      }
      
      // 提取让球胜赔率
      try {
        const handicapWinOddsPattern = new RegExp(handicapWinOddsRegex, 'i');
        const handicapWinOddsMatch = matchHtml.match(handicapWinOddsPattern);
        if (handicapWinOddsMatch) {
          const handicapWinValue = parseFloat(handicapWinOddsMatch[1]) || null;
          match.handicapOdds.win = handicapWinValue;
          match.handicapWin = handicapWinValue; // 表格绑定字段
          console.log(`    ✅ 让球胜赔率: ${handicapWinValue}`);
        } else {
          console.log(`    ❌ 主正则未找到让球胜赔率，尝试备用正则...`);
          // 使用新的提取函数
          const allOdds = extractAllOdds(matchHtml);
          if (allOdds.length >= 6) { // 让球赔率通常在后面
            const handicapWinValue = allOdds[3].value;
            match.handicapOdds.win = handicapWinValue;
            match.handicapWin = handicapWinValue;
            console.log(`    ✅ 备用方案找到让球胜赔率: ${handicapWinValue} (来源: ${allOdds[3].source})`);
          } else {
            console.log(`    ❌ 备用方案未找到足够的赔率数据，只找到 ${allOdds.length} 个`);
          }
        }
      } catch (error) {
        console.error(`    ❌ 让球胜赔率正则错误:`, error);
      }
      
      // 提取让球平赔率
      try {
        const handicapDrawOddsPattern = new RegExp(handicapDrawOddsRegex, 'i');
        const handicapDrawOddsMatch = matchHtml.match(handicapDrawOddsPattern);
        if (handicapDrawOddsMatch) {
          const handicapDrawValue = parseFloat(handicapDrawOddsMatch[1]) || null;
          match.handicapOdds.draw = handicapDrawValue;
          match.handicapDraw = handicapDrawValue; // 表格绑定字段
          console.log(`    ✅ 让球平赔率: ${handicapDrawValue}`);
        } else {
          console.log(`    ❌ 主正则未找到让球平赔率，尝试备用正则...`);
          // 使用新的提取函数
          const allOdds = extractAllOdds(matchHtml);
          if (allOdds.length >= 6) { // 让球赔率通常在后面
            const handicapDrawValue = allOdds[4].value;
            match.handicapOdds.draw = handicapDrawValue;
            match.handicapDraw = handicapDrawValue;
            console.log(`    ✅ 备用方案找到让球平赔率: ${handicapDrawValue} (来源: ${allOdds[4].source})`);
          } else {
            console.log(`    ❌ 备用方案未找到足够的赔率数据，只找到 ${allOdds.length} 个`);
          }
        }
      } catch (error) {
        console.error(`    ❌ 让球平赔率正则错误:`, error);
      }
      
      // 提取让球负赔率
      try {
        const handicapLoseOddsPattern = new RegExp(handicapLoseOddsRegex, 'i');
        const handicapLoseOddsMatch = matchHtml.match(handicapLoseOddsPattern);
        if (handicapLoseOddsMatch) {
          const handicapLoseValue = parseFloat(handicapLoseOddsMatch[1]) || null;
          match.handicapOdds.lose = handicapLoseValue;
          match.handicapLose = handicapLoseValue; // 表格绑定字段
          console.log(`    ✅ 让球负赔率: ${handicapLoseValue}`);
        } else {
          console.log(`    ❌ 主正则未找到让球负赔率，尝试备用正则...`);
          // 使用新的提取函数
          const allOdds = extractAllOdds(matchHtml);
          if (allOdds.length >= 6) { // 让球赔率通常在后面
            const handicapLoseValue = allOdds[5].value;
            match.handicapOdds.lose = handicapLoseValue;
            match.handicapLose = handicapLoseValue;
            console.log(`    ✅ 备用方案找到让球负赔率: ${handicapLoseValue} (来源: ${allOdds[5].source})`);
          } else {
            console.log(`    ❌ 备用方案未找到足够的赔率数据，只找到 ${allOdds.length} 个`);
          }
        }
      } catch (error) {
        console.error(`    ❌ 让球负赔率正则错误:`, error);
      }

      // 8. 构建链接信息
      if (match.matchId) {
        const baseUrl = 'https://m.okooo.com';
        const fromParam = '&from=%2Fweixin%2Fjing%2F';

        match.links = {
          handicap: `${baseUrl}/match/handicap.php?MatchID=${match.matchId}${fromParam}`,
          exchanges: `${baseUrl}/match/exchanges.php?MatchID=${match.matchId}${fromParam}`,
          game: `${baseUrl}/match/game.php?MatchID=${match.matchId}${fromParam}`,
          form: `${baseUrl}/match/form.php?MatchID=${match.matchId}${fromParam}`,
          odds: `${baseUrl}/match/odds.php?MatchID=${match.matchId}${fromParam}`,
          history: `${baseUrl}/match/history.php?MatchID=${match.matchId}${fromParam}`,
        };
        console.log(`    ✅ 链接已生成`);
      } else {
        console.log(`    ❌ 无法生成链接，缺少MatchID`);
      }

      // 9. 提取更多玩法数量
      const moreGamesRegex = ruleMap.get('moreGames') || '<cite[^>]*class="[^"]*morenum[^"]*"[^>]*>(\\d+)</cite>';
      try {
        const moreGamesPattern = new RegExp(moreGamesRegex, 'i');
        const moreGamesMatch = matchHtml.match(moreGamesPattern);
        match.moreGames = moreGamesMatch ? parseInt(moreGamesMatch[1]) : 0;
        console.log(`    ✅ 更多玩法数量: ${match.moreGames}`);
      } catch (error) {
        console.error(`    ❌ 更多玩法数量正则错误:`, error);
        match.moreGames = 0;
      }

      matches.push(match);
      console.log(
        `✅ 第${index + 1}场比赛解析完成: 序号=${match.matchNumber} 联赛=${match.league} 时间=${match.matchTime} ${match.homeTeam || 'undefined'} vs ${match.awayTeam || 'undefined'} 让球=${match.handicap}`,
      );
      console.log(`📊 当前已解析 ${matches.length} 场比赛`);
    });

    console.log(`🎯 总共解析到 ${matches.length} 场比赛`);
  } catch (err) {
    console.error('❌ 解析数据时出错:', err);
  }

  return matches;
};

// 使用原始规则获取网页内容
const fetchWebContentWithOriginalRules = async () => {
  isLoadingOriginal.value = true;
  error.value = '';

  // 清空之前的数据，防止重复显示
  originalMatches.value = [];
  footballMatches.value = [];
  webContent.value = '';

  try {
    console.debug('开始使用原始规则获取网页内容...');

    // 初始化MCP会话
    const session = await initializeMCPSession();
    if (!session) {
      throw new Error('无法初始化MCP会话');
    }

    console.debug('MCP会话初始化成功');

    // 获取当前页面URL
    const url = await getCurrentTabUrl();
    if (!url) {
      throw new Error('无法获取当前页面URL');
    }

    // 获取网页内容
    const content = await getChromeWebContent(url, session);
    console.debug('获取到的内容类型:', typeof content, '长度:', content?.length || 0);

    if (!content) {
      throw new Error('未能获取到网页内容');
    }

    // 确保content是字符串
    let htmlContent: string;
    if (typeof content === 'string') {
      htmlContent = content;
    } else if (content && typeof content === 'object' && 'content' in content) {
      // 如果content是对象且包含content属性
      htmlContent = String((content as any).content || '');
    } else if (Array.isArray(content) && content.length > 0) {
      // 如果content是数组，提取第一个元素的内容
      const firstItem = content[0];
      if (typeof firstItem === 'string') {
        htmlContent = firstItem;
      } else if (firstItem && typeof firstItem === 'object' && 'content' in firstItem) {
        htmlContent = String(firstItem.content || '');
      } else {
        htmlContent = String(firstItem || '');
      }
    } else {
      htmlContent = String(content);
    }

    console.debug('处理后的HTML内容长度:', htmlContent.length);

    if (!htmlContent || htmlContent.length < 10) {
      throw new Error(`HTML内容太短或为空，长度: ${htmlContent.length}`);
    }

    webContent.value = htmlContent;

    // 使用原始规则解析足球比赛数据
    console.debug('开始使用原始规则解析足球比赛数据...');
    const matches = parseFootballMatchesWithOriginalRules(htmlContent, originalRegexRules.value);
    console.debug('解析结果:', matches);

    originalMatches.value = matches;
    footballMatches.value = matches;

    if (matches.length === 0) {
      error.value = '未找到足球比赛数据，请检查页面内容或原始规则配置';
    }
  } catch (err) {
    console.error('获取内容失败:', err);
    error.value = err instanceof Error ? err.message : '获取内容失败';
  } finally {
    isLoadingOriginal.value = false;
  }
};

// 使用模板配置获取网页内容
const fetchWebContentWithTemplate = async () => {
  isLoadingTemplate.value = true;
  error.value = '';

  // 清空之前的数据，防止重复显示
  templateMatches.value = [];
  footballMatches.value = [];
  webContent.value = '';

  try {
    console.debug('开始使用模板配置获取网页内容...');

    // 初始化MCP会话
    const session = await initializeMCPSession();
    if (!session) {
      throw new Error('无法初始化MCP会话');
    }

    console.debug('MCP会话初始化成功');

    // 获取当前页面URL
    const url = await getCurrentTabUrl();
    if (!url) {
      throw new Error('无法获取当前页面URL');
    }

    // 获取网页内容
    const content = await getChromeWebContent(url, session);
    console.debug('获取到的内容类型:', typeof content, '长度:', content?.length || 0);

    if (!content) {
      throw new Error('未能获取到网页内容');
    }

    // 确保content是字符串
    let htmlContent: string;
    if (typeof content === 'string') {
      htmlContent = content;
    } else if (content && typeof content === 'object' && 'content' in content) {
      // 如果content是对象且包含content属性
      htmlContent = String((content as any).content || '');
    } else if (Array.isArray(content) && content.length > 0) {
      // 如果content是数组，提取第一个元素的内容
      const firstItem = content[0];
      if (typeof firstItem === 'string') {
        htmlContent = firstItem;
      } else if (firstItem && typeof firstItem === 'object' && 'content' in firstItem) {
        htmlContent = String(firstItem.content || '');
      } else {
        htmlContent = String(firstItem || '');
      }
    } else {
      htmlContent = String(content);
    }

    console.debug('处理后的HTML内容长度:', htmlContent.length);

    if (!htmlContent || htmlContent.length < 10) {
      throw new Error(`HTML内容太短或为空，长度: ${htmlContent.length}`);
    }

    webContent.value = htmlContent;

    // 使用模板配置解析逻辑
    console.debug('开始使用模板配置解析足球比赛数据...');
    const matches = parseFootballMatches(htmlContent);
    console.debug('解析结果:', matches);

    templateMatches.value = matches;
    footballMatches.value = matches;

    if (matches.length === 0) {
      error.value = '未找到足球比赛数据，请检查页面内容或模板配置';
    }
  } catch (err) {
    console.error('获取内容失败:', err);
    error.value = err instanceof Error ? err.message : '获取内容失败';
  } finally {
    isLoadingTemplate.value = false;
  }
};

// 格式化赔率显示
const formatOdds = (odds: number | null): string => {
  if (odds === null || odds === undefined) return '-';
  if (odds === 0) return '未开售';
  return odds.toString();
};

// 显示原始数据
const showRawData = (match: any): void => {
  console.log('显示原始数据，match对象:', match);
  // 尝试多个可能的字段名
  const rawData = match.rawData || match.rawHtml || match.matchHtml || '无原始数据';
  console.log('提取到的原始数据长度:', rawData.length);
  selectedMatchRawData.value = rawData;
  showRawDataModal.value = true;
};

// 关闭原始数据模态框
const closeRawDataModal = (): void => {
  showRawDataModal.value = false;
  selectedMatchRawData.value = '';
};

// 切换正则表达式规则显示状态
const toggleRegexRules = (): void => {
  showRegexRules.value = !showRegexRules.value;
};

// 处理模板更新
const onTemplateUpdated = (fields: TemplateField[]): void => {
  console.log('模板已更新:', fields);
  // 可以在这里更新正则规则或重新解析数据
  updateRegexRulesFromTemplate(fields);
};

// 从模板字段更新正则规则
const updateRegexRulesFromTemplate = (fields: TemplateField[]): void => {
  regexRules.value = fields.map((field) => ({
    field: field.name,
    description: field.description,
    pattern: field.regex,
    label: field.name,
  }));
};

// 同花顺相关方法
// 导航到同花顺自选股页面
const navigateToThs = async () => {
  try {
    thsLoading.value = true;
    thsError.value = '';
    
    console.log('正在导航到同花顺页面...');
    
    // 打开同花顺页面
    const tab = await chrome.tabs.create({
      url: 'https://t.10jqka.com.cn/newcircle/user/userPersonal/?from=finance&tab=zx###'
    });
    
    currentTabId.value = tab.id;
    console.log('同花顺页面已打开，Tab ID:', tab.id);
    
    // 等待页面加载
    setTimeout(() => {
      checkLoginStatus();
    }, 3000);
    
  } catch (err) {
    console.error('导航失败:', err);
    thsError.value = '导航失败: ' + err;
  } finally {
    thsLoading.value = false;
  }
};

// 检查登录状态
const checkLoginStatus = async () => {
  try {
    console.log('Sidepanel: 开始检查登录状态...');
    
    // 优先获取当前活跃标签页
    let tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    
    // 如果当前标签页不是目标页面，尝试查找特定域名的标签页
    if (tabs.length === 0 || (!tabs[0].url?.includes('10jqka.com.cn') && !tabs[0].url?.includes('okooo.com'))) {
        const thsTabs = await chrome.tabs.query({ url: '*://t.10jqka.com.cn/*' });
        const okoooTabs = await chrome.tabs.query({ url: '*://*.okooo.com/*' });
        tabs = [...thsTabs, ...okoooTabs];
    }
    
    console.log('Sidepanel: 查询到的相关标签页数量:', tabs.length);
    
    if (tabs.length > 0 && tabs[0]?.id) {
      currentTabId.value = tabs[0].id;
      console.log('Sidepanel: 找到目标页面，Tab ID:', tabs[0].id);
      console.log('Sidepanel: 页面URL:', tabs[0].url);
      
      try {
          const response = await chrome.tabs.sendMessage(currentTabId.value, {
            action: 'checkLogin'
          });
          
          console.log('Sidepanel: 登录状态检查结果:', response);
          isLoggedIn.value = response?.isLoggedIn || false;
          
          if (response?.isLoggedIn) {
            console.log('Sidepanel: ✅ 用户已登录');
          } else {
            console.log('Sidepanel: ❌ 用户未登录');
          }
      } catch (msgErr: any) {
          // 忽略连接错误，可能是页面正在加载或content script未注入
          if (msgErr.message && msgErr.message.includes('Receiving end does not exist')) {
             console.log('Sidepanel: 无法连接到页面 (可能未加载完成或不支持的页面)');
             isLoggedIn.value = false;
          } else {
             throw msgErr;
          }
      }
    } else {
      console.log('Sidepanel: 未找到目标页面');
      thsError.value = '请先打开同花顺或澳客网页面';
    }
  } catch (err) {
    console.error('Sidepanel: 检查登录状态失败:', err);
    thsError.value = '检查登录状态失败: ' + err;
  }
};

// 点击登录按钮
const clickLogin = async () => {
  try {
    console.log('Sidepanel: 开始点击登录按钮...');
    console.log('Sidepanel: 当前标签页ID:', currentTabId.value);
    
    if (currentTabId.value) {
      const response = await chrome.tabs.sendMessage(currentTabId.value, {
        action: 'clickLogin'
      });
      
      console.log('Sidepanel: 登录按钮点击响应:', response);
      console.log('Sidepanel: 登录按钮已点击，等待登录完成...');
      
      // 等待登录完成后重新检查状态
      setTimeout(() => {
        console.log('Sidepanel: 2秒后重新检查登录状态...');
        checkLoginStatus();
      }, 2000);
    } else {
      console.log('Sidepanel: 当前标签页ID为空，无法点击登录按钮');
      thsError.value = '请先打开同花顺页面';
    }
  } catch (err) {
    console.error('Sidepanel: 点击登录失败:', err);
    thsError.value = '点击登录失败: ' + err;
  }
};

// 抓取网页内容
const capturePageContent = async () => {
  try {
    thsLoading.value = true;
    console.log('Sidepanel: 开始抓取页面内容...');
    console.log('Sidepanel: 当前标签页ID:', currentTabId.value);
    
    if (currentTabId.value) {
      const response = await chrome.tabs.sendMessage(currentTabId.value, {
        action: 'getWebContent'
      });
      
      console.log('Sidepanel: 页面内容抓取响应:', response);
      pageContent.value = response?.content || '无法获取页面内容';
      console.log('Sidepanel: 页面内容抓取完成，内容长度:', pageContent.value.length);
    } else {
      console.log('Sidepanel: 当前标签页ID为空，无法抓取页面内容');
      thsError.value = '请先打开同花顺页面';
    }
  } catch (err) {
    console.error('Sidepanel: 抓取页面内容失败:', err);
    thsError.value = '抓取页面内容失败: ' + err;
  } finally {
    thsLoading.value = false;
    console.log('Sidepanel: 页面内容抓取操作完成');
  }
};

// 开始/停止网络监听
const toggleNetworkListening = async () => {
  try {
    console.log('Sidepanel: 开始切换网络监听状态，当前状态:', isListening.value);
    thsLoading.value = true;
    thsError.value = '';
    
    if (isListening.value) {
      // 停止监听
      console.log('Sidepanel: 正在停止网络监听...');
      
      try {
        const response = await chrome.runtime.sendMessage({
          action: 'stopNetworkCapture'
        });
        
        console.log('Sidepanel: 停止监听响应:', response);
        
        if (response && response.success !== false) {
          isListening.value = false;
          console.log('Sidepanel: 网络监听已停止');
        } else {
          throw new Error('停止监听失败: ' + (response?.error || '未知错误'));
        }
        
      } catch (stopError) {
        console.error('Sidepanel: 停止监听失败:', stopError);
        // 即使停止失败，也要重置状态
        isListening.value = false;
        throw stopError;
      }
      
    } else {
      // 开始监听
      if (DEBUG_MODE) console.log('Sidepanel: 正在开始网络监听...');
      
      try {
        const response = await chrome.runtime.sendMessage({
          action: 'startNetworkCapture',
          pattern: 'https://t.10jqka.com.cn/', // 更通用的同花顺域名模式
          tabId: currentTabId.value
        });
        
        if (DEBUG_MODE) console.log('Sidepanel: 开始监听响应:', response);
        
        if (response && response.success !== false) {
          isListening.value = true;
          if (DEBUG_MODE) console.log('Sidepanel: 网络监听已开始');
        } else {
          throw new Error('启动监听失败: ' + (response?.error || '未知错误'));
        }
        
      } catch (startError) {
        console.error('Sidepanel: 开始监听失败:', startError);
        isListening.value = false;
        throw startError;
      }
    }
    
  } catch (err) {
    console.error('Sidepanel: 网络监听操作失败:', err);
    thsError.value = '网络监听操作失败: ' + (err instanceof Error ? err.message : String(err));
    // 确保在错误情况下状态正确
    isListening.value = false;
  } finally {
    // 确保loading状态总是被重置
    thsLoading.value = false;
    if (DEBUG_MODE) console.log('Sidepanel: 网络监听操作完成，最终状态:', isListening.value);
  }
};

// 清空网络数据
const clearNetworkData = (): void => {
    if (DEBUG_MODE) {
      console.log('Sidepanel: 开始清空网络数据');
      console.log('Sidepanel: 清空前数据条数:', networkData.value.length, '/', allNetworkData.value.length);
    }
  
  networkData.value = [];
  allNetworkData.value = [];
  
  if (DEBUG_MODE) console.log('Sidepanel: 已清空所有网络数据');
};

// 格式化JSON显示
const formatJson = (obj: any): string => {
  try {
    return JSON.stringify(obj, null, 2);
  } catch {
    return String(obj);
  }
};

// 新增的方法
// 显示数据详情
const showDataDetails = (data: any): void => {
  selectedData.value = data;
  showModal.value = true;
};

// 关闭模态框
const closeModal = (): void => {
  showModal.value = false;
  selectedData.value = null;
};

// 配置管理相关方法
const saveConfig = async () => {
  try {
    const config = {
      autoPushInterval: autoPushInterval.value,
      maxDataCache: maxDataCache.value,
      enableAutoPush: enableAutoPush.value,
      backendUrl: backendUrl.value
    };
    
    // 保存到Chrome存储
    await chrome.storage.local.set({ extensionConfig: config });
    
    pushStatus.value = { 
      success: true, 
      message: '配置已保存' 
    };
    
    if (DEBUG_MODE) console.log('配置已保存:', config);
  } catch (error) {
    console.error('保存配置失败:', error);
    pushStatus.value = { 
      success: false, 
      message: `保存失败: ${error instanceof Error ? error.message : '未知错误'}` 
    };
  }
};

const resetConfig = async () => {
  try {
    // 重置为默认值
    autoPushInterval.value = 5;
    maxDataCache.value = 100;
    enableAutoPush.value = true;
    backendUrl.value = 'http://localhost:8000';
    
    // 清除存储的配置
    await chrome.storage.local.remove('extensionConfig');
    
    pushStatus.value = { 
      success: true, 
      message: '配置已重置为默认值' 
    };
    
    if (DEBUG_MODE) console.log('配置已重置');
  } catch (error) {
    console.error('重置配置失败:', error);
    pushStatus.value = { 
      success: false, 
      message: `重置失败: ${error instanceof Error ? error.message : '未知错误'}` 
    };
  }
};

const loadConfig = async () => {
  try {
    const result = await chrome.storage.local.get('extensionConfig');
    if (result.extensionConfig) {
      const config = result.extensionConfig;
      autoPushInterval.value = config.autoPushInterval || 5;
      maxDataCache.value = config.maxDataCache || 100;
      enableAutoPush.value = config.enableAutoPush !== undefined ? config.enableAutoPush : true;
      backendUrl.value = config.backendUrl || 'http://localhost:8000';
      
      if (DEBUG_MODE) console.log('配置已加载:', config);
    }
  } catch (error) {
    console.error('加载配置失败:', error);
  }
};

// 推送数据到后端
const pushDataToBackend = async () => {
  if (isPushing.value) return;
  
  isPushing.value = true;
  pushStatus.value = null;
  
  try {
    if (DEBUG_MODE) console.log('开始推送数据到后端...');
    
    // 过滤出同花顺相关的数据
    const thsData = allNetworkData.value.filter(data => 
      data.url && (
        data.url.includes('t.10jqka.com.cn/newcircle/user/userPersonal333') ||
        data.url.includes('t.10jqka.com.cn/newcircle/group/getSelfStockWithMarket444') ||
        data.url.includes('d.10jqka.com.cn/multimarketreal/hs/')
      )
    );
    
    if (thsData.length === 0) {
      thsError.value = '未找到同花顺相关数据';
      pushStatus.value = { success: false, message: '未找到同花顺相关数据' };
      return;
    }
    
    if (DEBUG_MODE) {
      console.log(`找到 ${thsData.length} 条同花顺数据，准备推送...`);
      console.log('推送数据概览:', thsData.map(d => ({
        url: d.url,
        timestamp: d.timestamp,
        responseSize: JSON.stringify(d.response || {}).length
      })));
    }
    
    // 推送到后端API - 使用配置中的后端URL
    const apiUrl = `${backendUrl.value}/api/v1/stocks/tonghuashun/raw-data`;
    const requestPayload = {
      data: thsData,
      timestamp: new Date().toISOString(),
      source: 'chrome-extension'
    };
    
    if (DEBUG_MODE) {
      console.log('发送批量请求到:', apiUrl);
      console.log('批量请求负载:', {
        dataCount: requestPayload.data.length,
        timestamp: requestPayload.timestamp,
        source: requestPayload.source
      });
    }
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestPayload)
    });
    
    if (DEBUG_MODE) console.log('批量推送响应状态:', response.status, response.statusText);
    
    if (response.ok) {
      const result = await response.json();
      pushStatus.value = { 
        success: true, 
        message: `成功推送 ${thsData.length} 条数据到后端` 
      };
      if (DEBUG_MODE) console.log('批量数据推送成功:', result);
      
      // 显示详细的处理结果
      if (result.data && result.data.processed_count !== undefined) {
        pushStatus.value.message = `成功推送 ${thsData.length} 条数据，后端处理了 ${result.data.processed_count} 条`;
      }
    } else {
      const errorText = await response.text();
      console.error('批量推送失败响应:', errorText);
      if (DEBUG_MODE) console.error('批量推送响应头:', Object.fromEntries(response.headers.entries()));
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }
    
  } catch (error) {
    console.error('推送数据失败:', error);
    pushStatus.value = { 
      success: false, 
      message: `推送失败: ${error instanceof Error ? error.message : '未知错误'}` 
    };
  } finally {
    isPushing.value = false;
  }
};

// 自动推送单条数据到后端
const autoPushToBackend = async (data: any) => {
  try {
    if (DEBUG_MODE) {
      console.log('自动推送数据到后端:', data.url);
      console.log('推送数据详情:', {
        url: data.url,
        dataLength: JSON.stringify(data.response || {}).length,
        timestamp: data.timestamp
      });
    }
    
    // 推送单条数据到后端API - 使用配置中的后端URL
    const apiUrl = `${backendUrl.value}/api/v1/stocks/tonghuashun/raw-data`;
    const requestPayload = {
      data: [data], // 包装成数组
      timestamp: new Date().toISOString(),
      source: 'chrome-extension-auto'
    };
    
    if (DEBUG_MODE) {
      console.log('发送请求到:', apiUrl);
      console.log('请求负载:', {
        dataCount: requestPayload.data.length,
        timestamp: requestPayload.timestamp,
        source: requestPayload.source
      });
    }
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestPayload)
    });
    
    if (DEBUG_MODE) console.log('响应状态:', response.status, response.statusText);
    
    if (response.ok) {
      const result = await response.json();
      if (DEBUG_MODE) console.log('自动推送成功:', result);
      
      // 更新推送状态显示
      if (result.data && result.data.processed_count > 0) {
        pushStatus.value = { 
          success: true, 
          message: `自动推送成功: ${result.data.processed_count} 条数据` 
        };
      }
    } else {
      const errorText = await response.text();
      console.error('自动推送失败:', `HTTP ${response.status}: ${errorText}`);
      if (DEBUG_MODE) console.error('响应头:', Object.fromEntries(response.headers.entries()));
      
      // 更新推送状态显示
      pushStatus.value = { 
        success: false, 
        message: `自动推送失败: HTTP ${response.status}` 
      };
    }
    
  } catch (error) {
    console.error('自动推送数据失败:', error);
    console.error('错误详情:', {
      name: error.name,
      message: error.message,
      stack: error.stack
    });
    
    // 更新推送状态显示
    pushStatus.value = { 
      success: false, 
      message: `自动推送异常: ${error.message}` 
    };
  }
};

// 清空测试数据
const clearTestData = async () => {
  if (isClearing.value) return;
  
  isClearing.value = true;
  
  try {
    console.log('开始清空测试数据...');
    
    // 清空本地数据
    clearNetworkData();
    
    // 调用后端API清空测试数据 - 使用配置中的后端URL
    const apiUrl = `${backendUrl.value}/api/v1/stocks/test-data/clear`;
    const response = await fetch(apiUrl, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('测试数据清空成功:', result);
      pushStatus.value = { success: true, message: result.message || '测试数据已清空' };
    } else {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }
    
  } catch (error) {
    console.error('清空测试数据失败:', error);
    pushStatus.value = { 
      success: false, 
      message: `清空失败: ${error instanceof Error ? error.message : '未知错误'}` 
    };
  } finally {
    isClearing.value = false;
  }
};

// 启动生产模式
const startProductionMode = async () => {
  try {
    console.log('启动生产模式...');
    
    // 清空测试数据
    await clearTestData();
    
    // 开始网络监听
    if (!isListening.value) {
      await toggleNetworkListening();
    }
    
    pushStatus.value = { success: true, message: '生产模式已启动，开始接收实时数据' };
    
  } catch (error) {
    console.error('启动生产模式失败:', error);
    pushStatus.value = { 
      success: false, 
      message: `启动失败: ${error instanceof Error ? error.message : '未知错误'}` 
    };
  }
};

// 监听来自background的网络数据
const setupNetworkDataListener = () => {
  // 简化的去重机制 - 只使用requestId
  const processedRequestIds = new Set<string>();
  
  chrome.runtime.onMessage.addListener((message) => {
    if (message.action === 'networkData') {
      if (DEBUG_MODE) console.log('Sidepanel: 收到网络数据:', message.url);
      
      // 简化的去重标识
      const requestId = message.requestId || `${message.url}_${message.timestamp || Date.now()}`;
      
      // 基础去重检查
      if (processedRequestIds.has(requestId)) {
        if (DEBUG_MODE) console.log('Sidepanel: 跳过重复数据');
        return;
      }
      
      // 标记此数据已处理
      processedRequestIds.add(requestId);
      
      const newData = {
        url: message.url,
        response: message.response,
        timestamp: message.timestamp || new Date().toISOString(),
        id: requestId,
        requestId: requestId,
        dataLength: JSON.stringify(message.response).length
      };
      
      // 添加到数据数组
      allNetworkData.value.unshift(newData);
      networkData.value.unshift(newData);
      
      // 限制数组长度
      if (networkData.value.length > 5) {
        networkData.value = networkData.value.slice(0, 5);
      }
      
      if (allNetworkData.value.length > maxDataCache.value) {
        allNetworkData.value = allNetworkData.value.slice(0, maxDataCache.value);
      }
      
      // 简化的内存清理
      if (processedRequestIds.size > 500) {
        const idsArray = Array.from(processedRequestIds);
        const toRemove = idsArray.slice(0, 250);
        toRemove.forEach(id => processedRequestIds.delete(id));
      }
      
      if (DEBUG_MODE) {
        console.log('Sidepanel: 新增网络数据成功');
        console.log('Sidepanel: 显示/总数据条数:', networkData.value.length, '/', allNetworkData.value.length);
      }
      
      // 自动推送同花顺数据到后端（基于配置）
      if (enableAutoPush.value && message.url && (
        message.url.includes('t.10jqka.com.cn/newcircle/user/userPersonal444') ||
        message.url.includes('t.10jqka.com.cn/newcircle/group/getSelfStockWithMarket333') ||
        message.url.includes('d.10jqka.com.cn/multimarketreal/hs/')
      )) {
        if (DEBUG_MODE) console.log('Sidepanel: 检测到同花顺关键数据，自动推送到后端...');
        // 使用配置的推送间隔进行延迟推送
        setTimeout(() => {
          autoPushToBackend(newData);
        }, autoPushInterval.value * 1000);
      }
    }
  });
};

// 检查两条数据是否属于同一股票
const checkIfSameStock = (newData: any, firstData: any): boolean => {
  try {
    const newResponse = newData.response;
    const firstResponse = firstData.response;
    
    if (!newResponse || !firstResponse) return false;
    
    // 检查URL是否相似（同一股票的不同接口）
    const newUrl = newData.url || '';
    const firstUrl = firstData.url || '';
    
    // 如果URL包含相同的股票代码模式，认为是同一股票
    const stockCodePattern = /[0-9]{6}/; // 6位数字的股票代码
    const newMatch = newUrl.match(stockCodePattern);
    const firstMatch = firstUrl.match(stockCodePattern);
    
    if (newMatch && firstMatch && newMatch[0] === firstMatch[0]) {
      return true;
    }
    
    // 检查响应数据中的股票代码
    const getStockCode = (response: any): string => {
      if (typeof response === 'object') {
        return response.code || response.symbol || response.stock_code || 
               (response.data && response.data[0] && response.data[0].code) || '';
      }
      return '';
    };
    
    const newCode = getStockCode(newResponse);
    const firstCode = getStockCode(firstResponse);
    
    return newCode && firstCode && newCode === firstCode;
  } catch (e) {
    console.warn('检查股票数据失败:', e);
    return false;
  }
};

// 初始化同花顺应用
const initializeTonghuashunApp = async () => {
  try {
    const tabs = await chrome.tabs.query({ 
      url: '*://t.10jqka.com.cn/*'
    });
    
    if (tabs.length > 0 && tabs[0]?.id) {
      currentTabId.value = tabs[0].id;
      checkLoginStatus();
    }
  } catch (err) {
    console.error('初始化同花顺应用失败:', err);
  }
};

// MCP测试相关方法
const executeScenario = async (scenario: string) => {
  mcpLoading.value = true;
  mcpError.value = '';
  
  try {
    let toolName = '';
    let params = {};
    
    switch (scenario) {
      case 'navigate':
        toolName = 'chrome_navigate';
        params = { url: 'https://m.okooo.com' };
        break;
      case 'alert':
        toolName = 'chrome_inject_script';
        params = { script: "alert('MCP测试成功！')" };
        break;
      case 'get-title':
        toolName = 'chrome_get_page_title';
        params = {};
        break;
      case 'get-tabs':
        toolName = 'get_windows_and_tabs';
        params = {};
        break;
      default:
        throw new Error('未知的测试场景');
    }
    
    mcpToolName.value = toolName;
    mcpToolParams.value = JSON.stringify(params, null, 2);
    
    await executeMCPTool();
  } catch (error) {
    mcpError.value = `场景执行失败: ${error.message}`;
    console.error('场景执行失败:', error);
  } finally {
    mcpLoading.value = false;
  }
};

const executeMCPTool = async () => {
  if (!mcpToolName.value.trim()) {
    mcpError.value = '请输入工具名称';
    return;
  }
  
  mcpLoading.value = true;
  mcpError.value = '';
  
  try {
    // 验证JSON参数
    let params = {};
    if (mcpToolParams.value.trim()) {
      try {
        params = JSON.parse(mcpToolParams.value);
        mcpJsonError.value = '';
      } catch (e) {
        mcpJsonError.value = 'JSON格式错误';
        mcpLoading.value = false;
        return;
      }
    }
    
    // 通过Chrome扩展的native messaging发送MCP请求
    const message = {
      type: 'mcp_call',
      tool: mcpToolName.value,
      params: params
    };
    
    console.log('发送MCP请求:', message);
    
    // 使用chrome.runtime.sendNativeMessage发送到native host
    const response = await new Promise((resolve, reject) => {
      chrome.runtime.sendNativeMessage('com.chrome.mcp.server', message, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve(response);
        }
      });
    });
    
    mcpResult.value = {
      success: true,
      data: response,
      timestamp: Date.now()
    };
    
    mcpStatus.value = { connected: true, text: 'MCP服务已连接' };
    nativeStatus.value = { connected: true, text: 'Native Host已连接' };
    
  } catch (error) {
    mcpResult.value = {
      success: false,
      data: error.message,
      timestamp: Date.now()
    };
    mcpError.value = `执行失败: ${error.message}`;
    console.error('MCP工具执行失败:', error);
  } finally {
    mcpLoading.value = false;
  }
};

const connectMCP = async () => {
  mcpLoading.value = true;
  mcpError.value = '';
  
  try {
    // 测试连接
    const message = {
      type: 'mcp_ping'
    };
    
    const response = await new Promise((resolve, reject) => {
      chrome.runtime.sendNativeMessage('com.chrome.mcp.server', message, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve(response);
        }
      });
    });
    
    mcpStatus.value = { connected: true, text: 'MCP服务已连接' };
    nativeStatus.value = { connected: true, text: 'Native Host已连接' };
    
    mcpResult.value = {
      success: true,
      data: 'MCP连接成功',
      timestamp: Date.now()
    };
    
  } catch (error) {
    mcpStatus.value = { connected: false, text: 'MCP服务连接失败' };
    nativeStatus.value = { connected: false, text: 'Native Host连接失败' };
    mcpError.value = `连接失败: ${error.message}`;
    console.error('MCP连接失败:', error);
  } finally {
    mcpLoading.value = false;
  }
};

const validateMCPParams = () => {
  mcpJsonError.value = '';
  
  if (!mcpToolParams.value.trim()) {
    mcpJsonError.value = '参数不能为空';
    return;
  }
  
  try {
    JSON.parse(mcpToolParams.value);
    mcpJsonError.value = '';
    mcpResult.value = {
      success: true,
      data: 'JSON参数格式正确',
      timestamp: Date.now()
    };
  } catch (e) {
    mcpJsonError.value = `JSON格式错误: ${e.message}`;
  }
};

const testMCPPing = async () => {
  mcpLoading.value = true;
  mcpError.value = '';
  
  try {
    const message = {
      type: 'mcp_ping'
    };
    
    const startTime = Date.now();
    const response = await new Promise((resolve, reject) => {
      chrome.runtime.sendNativeMessage('com.chrome.mcp.server', message, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve(response);
        }
      });
    });
    const endTime = Date.now();
    
    mcpResult.value = {
      success: true,
      data: `Ping成功，响应时间: ${endTime - startTime}ms`,
      timestamp: Date.now()
    };
    
    mcpStatus.value = { connected: true, text: 'MCP服务正常' };
    
  } catch (error) {
    mcpResult.value = {
      success: false,
      data: `Ping失败: ${error.message}`,
      timestamp: Date.now()
    };
    mcpError.value = `Ping测试失败: ${error.message}`;
  } finally {
    mcpLoading.value = false;
  }
};

const getMCPToolsList = async () => {
  mcpLoading.value = true;
  mcpError.value = '';
  
  try {
    const message = {
      type: 'mcp_list_tools'
    };
    
    const response = await new Promise((resolve, reject) => {
      chrome.runtime.sendNativeMessage('com.chrome.mcp.server', message, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve(response);
        }
      });
    });
    
    if (response && response.tools) {
      mcpToolsList.value = response.tools;
      mcpResult.value = {
        success: true,
        data: `获取到 ${response.tools.length} 个可用工具`,
        timestamp: Date.now()
      };
    } else {
      mcpToolsList.value = [];
      mcpResult.value = {
        success: false,
        data: '未获取到工具列表',
        timestamp: Date.now()
      };
    }
    
  } catch (error) {
    mcpError.value = `获取工具列表失败: ${error.message}`;
    mcpResult.value = {
      success: false,
      data: error.message,
      timestamp: Date.now()
    };
  } finally {
    mcpLoading.value = false;
  }
};

const selectTool = (tool: any) => {
  mcpToolName.value = tool.name;
  
  // 根据工具的输入模式生成示例参数
  if (tool.inputSchema && tool.inputSchema.properties) {
    const exampleParams: Record<string, any> = {};
    Object.keys(tool.inputSchema.properties).forEach(key => {
      const prop = tool.inputSchema.properties[key];
      if (prop.type === 'string') {
        exampleParams[key] = prop.example || `示例${key}`;
      } else if (prop.type === 'number') {
        exampleParams[key] = prop.example || 0;
      } else if (prop.type === 'boolean') {
        exampleParams[key] = prop.example || false;
      }
    });
    mcpToolParams.value = JSON.stringify(exampleParams, null, 2);
  } else {
    mcpToolParams.value = '{}';
  }
};

const formatMCPResult = (data: any): string => {
  if (typeof data === 'string') {
    return data;
  }
  return JSON.stringify(data, null, 2);
};

// Okooo crawler functions
const startOkoooCrawler = async () => {
  if (!currentUrl.value?.includes('m.okooo.com')) {
    alert('请先打开澳客竞彩页面');
    return;
  }

  okoooCrawlerStatus.value.isRunning = true;
  okoooCrawlerStatus.value.phase = 'matches';

  try {
    const response = await chrome.runtime.sendMessage({
      type: 'OKOOO_START_CRAWLER'
    });

    if (response.success) {
      okoooCrawlerStatus.value.totalMatches = response.total;
      okoooCrawlerStatus.value.currentMatchIndex = 0;
      okoooCrawlerStatus.value.successCount = 0;
      okoooCrawlerStatus.value.errorCount = 0;
      okoooCrawlerStatus.value.results = [];
      startCrawlerStatusPolling();
    } else {
      okoooCrawlerStatus.value.isRunning = false;
      alert('启动失败: ' + response.message);
    }
  } catch (error) {
    okoooCrawlerStatus.value.isRunning = false;
    console.error('启动爬虫失败:', error);
  }
};

const stopOkoooCrawler = async () => {
  await chrome.runtime.sendMessage({
    type: 'OKOOO_STOP_CRAWLER'
  });

  okoooCrawlerStatus.value.isRunning = false;
  okoooCrawlerStatus.value.phase = 'idle';
  stopCrawlerStatusPolling();
};

const startCrawlerStatusPolling = () => {
  crawlerStatusTimer = setInterval(async () => {
    const response = await chrome.runtime.sendMessage({
      type: 'OKOOO_GET_STATUS'
    });

    if (response.success) {
      const data = response.data;
      okoooCrawlerStatus.value.isRunning = data.isRunning;
      okoooCrawlerStatus.value.phase = data.phase;
      okoooCrawlerStatus.value.totalMatches = data.totalMatches;
      okoooCrawlerStatus.value.currentMatchIndex = data.currentMatchIndex;
      okoooCrawlerStatus.value.totalHistory = data.totalHistory;
      okoooCrawlerStatus.value.currentHistoryIndex = data.currentHistoryIndex;
      okoooCrawlerStatus.value.successCount = data.successCount;
      okoooCrawlerStatus.value.errorCount = data.errorCount;
      okoooCrawlerStatus.value.results = data.results || [];

      if (!data.isRunning) {
        stopCrawlerStatusPolling();
      }
    }
  }, 1000);
};

const stopCrawlerStatusPolling = () => {
  if (crawlerStatusTimer) {
    clearInterval(crawlerStatusTimer);
    crawlerStatusTimer = null;
  }
};

// 启动让球盘爬虫
const startHandicapCrawler = async () => {
  handicapCrawlerStatus.value.isRunning = true;
  handicapCrawlerStatus.value.phase = 'query';

  try {
    const response = await chrome.runtime.sendMessage({
      type: 'OKOOO_HANDICAP_START'
    });

    if (response.success) {
      handicapCrawlerStatus.value.totalCount = response.total;
      handicapCrawlerStatus.value.currentIndex = 0;
      handicapCrawlerStatus.value.successCount = 0;
      handicapCrawlerStatus.value.errorCount = 0;
      handicapCrawlerStatus.value.phase = 'processing';
      startHandicapStatusPolling();
    } else {
      handicapCrawlerStatus.value.isRunning = false;
      handicapCrawlerStatus.value.phase = 'idle';
      alert('启动失败: ' + response.message);
    }
  } catch (error) {
    handicapCrawlerStatus.value.isRunning = false;
    handicapCrawlerStatus.value.phase = 'idle';
    console.error('启动让球盘爬虫失败:', error);
  }
};

let handicapStatusTimer: number | null = null;

const startHandicapStatusPolling = () => {
  handicapStatusTimer = setInterval(async () => {
    const response = await chrome.runtime.sendMessage({
      type: 'OKOOO_HANDICAP_STATUS'
    });

    if (response.success) {
      const data = response.data;
      handicapCrawlerStatus.value.isRunning = data.isRunning;
      handicapCrawlerStatus.value.phase = data.phase;
      handicapCrawlerStatus.value.totalCount = data.totalCount;
      handicapCrawlerStatus.value.currentIndex = data.currentIndex;
      handicapCrawlerStatus.value.successCount = data.successCount;
      handicapCrawlerStatus.value.errorCount = data.errorCount;

      if (!data.isRunning) {
        stopHandicapStatusPolling();
        handicapCrawlerStatus.value.phase = 'completed';
      }
    }
  }, 1000);
};

const stopHandicapStatusPolling = () => {
  if (handicapStatusTimer) {
    clearInterval(handicapStatusTimer);
    handicapStatusTimer = null;
  }
};

// 打开并捕获比赛列表
const openAndCaptureList = async () => {
  okoooListStatus.value.isCapturing = true;
  okoooListStatus.value.lastResult = null;

  try {
    const response = await chrome.runtime.sendMessage({
      type: 'OKOOO_OPEN_LIST'
    });

    okoooListStatus.value.isCapturing = false;

    if (response.success) {
      okoooListStatus.value.lastResult = {
        success: true,
        message: '比赛列表已保存',
        size: response.size
      };
    } else {
      okoooListStatus.value.lastResult = {
        success: false,
        message: response.message || '捕获失败'
      };
    }
  } catch (error) {
    okoooListStatus.value.isCapturing = false;
    okoooListStatus.value.lastResult = {
      success: false,
      message: String(error)
    };
    console.error('捕获比赛列表失败:', error);
  }
};

// 打开比赛列表页面
const openListPage = async () => {
  await chrome.tabs.create({
    url: 'https://m.okooo.com/jczq/',
    active: true
  });
};

// 格式化文件大小
const formatSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
};

const getPhaseText = (phase: string): string => {
  const phaseMap: Record<string, string> = {
    'idle': '待机中',
    'matches': '爬取比赛列表',
    'history': '爬取历史记录',
    'completed': '完成'
  };
  return phaseMap[phase] || phase;
};

onMounted(async () => {
  // 加载配置
  await loadConfig();
  
  // 初始化SSE连接
  setupSSE();
  
  // 初始化时获取当前URL
  currentUrl.value = await getCurrentTabUrl();
  // 初始化正则规则
  await initRegexRules();
  // 加载模板配置
  await loadTemplate();
  // 初始化同花顺应用
  await initializeTonghuashunApp();
  // 设置网络数据监听器
  setupNetworkDataListener();
  // 初始化爬虫状态
  const status = await chrome.runtime.sendMessage({
    type: 'OKOOO_GET_STATUS'
  });
  if (status.success) {
    okoooCrawlerStatus.value = {
      ...status.data,
      results: status.data.results || []
    };
    if (status.data.isRunning) {
      startCrawlerStatusPolling();
    }
  }
});

onUnmounted(() => {
  stopCrawlerStatusPolling();
  stopHandicapStatusPolling();
  if (eventSource) {
    eventSource.close();
    isLogStreamActive.value = false;
  }
});
</script>

<style scoped>
/* Tab导航样式 */
.tab-navigation {
  display: flex;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  padding: 0;
  margin: 0;
}

.tab-btn {
  flex: 1;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-secondary);
  border: none;
  border-bottom: 3px solid transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  text-align: center;
}

.tab-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.tab-btn.active {
  background: var(--bg-primary);
  color: var(--primary-color);
  border-bottom-color: var(--primary-color);
  font-weight: 600;
}

.popup-container {
  width: 100%;
  height: 100vh;
  min-height: 100vh;
  background: var(--bg-secondary);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.header {
  background: var(--primary-gradient);
  color: white;
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-md);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.content {
  flex: 1;
  padding: var(--spacing-lg);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.config-card,
.content-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.url-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.url-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.url-display {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-tertiary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  font-size: 12px;
  color: var(--text-muted);
  word-break: break-all;
  max-height: 60px;
  overflow-y: auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.connect-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--primary-gradient);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.connect-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.connect-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.save-btn,
.reset-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.save-btn {
  background: #10b981;
  color: white;
}

.save-btn:hover {
  background: #059669;
}

.reset-btn {
  background: #f59e0b;
  color: white;
}

.reset-btn:hover {
  background: #d97706;
}

.original-crawler-config {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-md);
}

.original-crawler-config h4 {
  margin: 0 0 var(--spacing-md) 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.regex-rules {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.rule-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.rule-item label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.rule-item input {
  padding: var(--spacing-sm);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.rule-item input[readonly] {
  background: var(--bg-tertiary);
  color: var(--text-muted);
}

.action-buttons {
  display: flex;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.btn {
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.btn-secondary {
  background: var(--bg-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  background: var(--bg-tertiary);
}

.template-config {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-md);
}

.template-config h4 {
  margin: 0 0 var(--spacing-md) 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.template-fields {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.field-row {
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

.field-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.field-number {
  background: var(--primary-color);
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.field-name {
  flex: 1;
  padding: var(--spacing-xs) var(--spacing-sm);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 500;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.remove-btn {
  background: #ef4444;
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
}

.remove-btn:hover:not(:disabled) {
  background: #dc2626;
}

.remove-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.field-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.input-group label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.field-input {
  padding: var(--spacing-sm);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 14px;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.field-textarea {
  padding: var(--spacing-sm);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  background: var(--bg-primary);
  color: var(--text-primary);
  resize: vertical;
}

.actions {
  margin-top: var(--spacing-md);
}

.add-btn {
  background: #10b981;
  color: white;
  border: none;
  border-radius: var(--radius-md);
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.add-btn:hover {
  background: #059669;
}

.rules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-sm);
}

.rule-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.rule-pattern {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 11px;
  background: var(--bg-tertiary);
  padding: var(--spacing-xs);
  border-radius: var(--radius-sm);
  word-break: break-all;
  color: var(--text-muted);
}

.error-card {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

.error-content {
  display: flex;
  gap: var(--spacing-md);
  align-items: flex-start;
}

.error-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.error-details {
  flex: 1;
}

.error-title {
  font-weight: 600;
  color: #dc2626;
  margin: 0 0 var(--spacing-xs) 0;
}

.error-message {
  color: #7f1d1d;
  font-size: 14px;
  margin: 0;
}

.matches-table {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.data-table th,
.data-table td {
  border: 1px solid var(--border-light);
  padding: var(--spacing-sm);
  text-align: left;
  vertical-align: top;
}

.data-table th {
  background: var(--bg-secondary);
  font-weight: 600;
  color: var(--text-secondary);
  position: sticky;
  top: 0;
}

.data-table td {
  color: var(--text-primary);
}

.match-row:hover {
  background: var(--bg-secondary);
}

.debug {
  text-align: center;
  width: 100px;
}

.debug-btn {
  padding: 4px 8px;
  background: #f59e0b;
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 11px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.debug-btn:hover {
  background: #d97706;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-xl);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--text-muted);
  padding: 4px;
  border-radius: var(--radius-sm);
  transition: background-color 0.2s;
}

.close-btn:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.modal-body {
  flex: 1;
  overflow: hidden;
  padding: var(--spacing-lg);
}

.raw-data {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 60vh;
  overflow-y: auto;
  margin: 0;
  color: var(--text-primary);
}

/* 同花顺相关样式 */
.tonghuashun-section {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-md);
}

/* 数据统计样式 */
.ths-data-stats {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-sm);
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--bg-primary);
  border-radius: calc(var(--border-radius) / 2);
  border: 1px solid var(--border-color);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.stat-value {
  font-size: 12px;
  color: var(--primary-color);
  font-weight: 600;
}

.ths-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  border-radius: var(--border-radius);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.ths-btn-primary {
  background: var(--primary-color);
  color: white;
}

.ths-btn-primary:hover {
  background: var(--primary-hover);
}

.ths-btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.ths-btn-secondary:hover {
  background: var(--bg-tertiary);
}

.ths-btn-success {
  background: #10b981;
  color: white;
}

.ths-btn-success:hover {
  background: #059669;
}

.ths-btn-danger {
  background: #ef4444;
  color: white;
}

.ths-btn-danger:hover {
  background: #dc2626;
}

.ths-controls {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.ths-status-indicator {
  margin-left: auto;
}

.ths-success {
  color: #10b981;
  font-weight: 600;
}

.ths-error {
  color: #ef4444;
  font-weight: 600;
}

.ths-network-data {
  margin-top: var(--spacing-md);
}

.ths-data-item {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  margin-bottom: var(--spacing-sm);
  overflow: hidden;
}

.ths-data-header {
  background: var(--bg-tertiary);
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  gap: var(--spacing-md);
  align-items: center;
  font-size: 12px;
}

.ths-timestamp {
  color: var(--text-secondary);
  font-weight: 500;
}

.ths-url {
  color: var(--primary-color);
  font-weight: 500;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ths-data-size {
  color: var(--text-muted);
  font-size: 11px;
}

.ths-data-content {
  padding: var(--spacing-md);
}

.ths-data-content pre {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: var(--spacing-sm);
  font-size: 11px;
  line-height: 1.4;
  max-height: 200px;
  overflow-y: auto;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.ths-content-area {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
  max-height: 200px;
  overflow-y: auto;
  font-size: 12px;
  line-height: 1.4;
}

/* 健康状态样式 */
.health-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.health-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
}

.health-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.health-status {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.health-status.active {
  background: #dcfce7;
  color: #166534;
}

.health-status.inactive {
  background: #fee2e2;
  color: #991b1b;
}

.health-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--primary-color);
}

/* 配置管理样式 */
.config-options {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.config-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.config-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.config-input {
  padding: var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 14px;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: border-color var(--transition-fast);
}

.config-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.config-checkbox {
  width: 20px;
  height: 20px;
  accent-color: var(--primary-color);
}

.config-actions {
  display: flex;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--border-color);
}

/* Tab内容样式 */
.tab-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 状态消息样式 */
.ths-status-message {
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  margin-top: var(--spacing-md);
}

.ths-status-message.success {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.ths-status-message.error {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

/* MCP测试样式 */
.mcp-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.mcp-section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--border-light);
}

.mcp-status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.mcp-status-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-md);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  text-align: center;
}

.mcp-status-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.mcp-status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-bottom: var(--spacing-xs);
}

.mcp-status-indicator.connected {
  background: #10b981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
}

.mcp-status-indicator.disconnected {
  background: #ef4444;
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.2);
}

.mcp-status-indicator.unknown {
  background: #6b7280;
  box-shadow: 0 0 0 2px rgba(107, 114, 128, 0.2);
}

.mcp-status-text {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-primary);
}

.mcp-scenarios {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.mcp-scenario-btn {
  padding: var(--spacing-sm);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
  cursor: pointer;
  transition: all var(--transition-fast);
  text-align: center;
}

.mcp-scenario-btn:hover:not(:disabled) {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.mcp-scenario-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.mcp-param-grid {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.mcp-param-input {
  padding: var(--spacing-sm);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 14px;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.mcp-param-textarea {
  padding: var(--spacing-sm);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  background: var(--bg-primary);
  color: var(--text-primary);
  resize: vertical;
  min-height: 80px;
}

.mcp-param-textarea.error {
  border-color: #ef4444;
  background: #fef2f2;
}

.mcp-json-error {
  color: #ef4444;
  font-size: 12px;
  margin-top: var(--spacing-xs);
}

.mcp-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.mcp-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  background: var(--bg-primary);
  color: var(--text-primary);
}

.mcp-btn.primary {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.mcp-btn.success {
  background: #10b981;
  color: white;
  border-color: #10b981;
}

.mcp-btn.info {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.mcp-btn:hover:not(:disabled) {
  opacity: 0.8;
}

.mcp-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.mcp-result {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  max-height: 300px;
  overflow-y: auto;
}

.mcp-result pre {
  margin: 0;
  font-size: 12px;
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.mcp-tools-list {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  max-height: 200px;
  overflow-y: auto;
}

.mcp-tool-item {
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--border-light);
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.mcp-tool-item:last-child {
  border-bottom: none;
}

.mcp-tool-item:hover {
  background: var(--bg-secondary);
}

.mcp-tool-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.mcp-tool-description {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.3;
}

.mcp-loading {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  color: var(--text-secondary);
  font-size: 14px;
}

.mcp-loading::before {
  content: '';
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-color);
  border-top: 2px solid var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Okooo Crawler Styles */
.current-page {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-md);
}

.page-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.page-url {
  font-size: 12px;
  color: var(--text-muted);
  word-break: break-all;
}

.page-url.url-valid {
  color: var(--primary-color);
}

.phase-indicator {
  margin-bottom: var(--spacing-md);
}

.phase-badge {
  display: inline-block;
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
}

.phase-idle { background: var(--bg-tertiary); color: var(--text-secondary); }
.phase-matches { background: #dbeafe; color: #1e40af; }
.phase-history { background: #fef3c7; color: #92400e; }
.phase-completed { background: #dcfce7; color: #166534; }

.crawler-stats {
  margin-bottom: var(--spacing-md);
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-sm);
}

.stat-item {
  text-align: center;
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.stat-item.success { background: #dcfce7; }
.stat-item.error { background: #fee2e2; }

.stat-label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.stat-item.success .stat-value { color: #166534; }
.stat-item.error .stat-value { color: #991b1b; }

.progress-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.progress-bar.large {
  flex: 1;
  height: 12px;
}

.action-buttons {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.action-section {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.action-section h4 {
  margin: 0 0 var(--spacing-xs) 0;
  font-size: 14px;
  color: var(--text-primary);
}

.action-section .description {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0 0 var(--spacing-md) 0;
}

.stats-row {
  display: flex;
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border-light);
}

.results-section {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

.results-section h4 {
  margin: 0 0 var(--spacing-sm) 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.results-scroll {
  max-height: 200px;
  overflow-y: auto;
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.result-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: 12px;
}

.result-pending { background: var(--bg-tertiary); color: var(--text-secondary); }
.result-success { background: #dcfce7; color: #166534; }
.result-error { background: #fee2e2; color: #991b1b; }

/* Okooo List Capture Styles */
.list-capture-section {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.list-capture-section h4 {
  margin: 0 0 var(--spacing-xs) 0;
  font-size: 14px;
  color: var(--text-primary);
}

.section-desc {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0 0 var(--spacing-md) 0;
}

.list-capture-buttons {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.list-result {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 12px;
}

.size-info {
  color: var(--text-muted);
}

.result-badge {
  display: inline-block;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: 12px;
}

.result-badge.result-success {
  background: #dcfce7;
  color: #166534;
}

.result-badge.result-error {
  background: #fee2e2;
  color: #991b1b;
}

/* Real-time Log Styles */
.log-section {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  margin-top: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.section-header-small {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header-small h4 {
  margin: 0;
  font-size: 14px;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--text-muted);
  transition: background-color 0.3s;
}

.status-dot.active {
  background-color: #10b981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
  }
  70% {
    box-shadow: 0 0 0 6px rgba(16, 185, 129, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
  }
}

.text-btn {
  background: none;
  border: none;
  color: var(--primary-color);
  font-size: 12px;
  cursor: pointer;
  padding: 0;
}

.text-btn:hover {
  text-decoration: underline;
}

.log-container {
  height: 200px;
  background: #1a1a1a;
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm);
  overflow-y: auto;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  border: 1px solid var(--border-color);
}

.empty-logs {
  color: #6b7280;
  text-align: center;
  padding-top: var(--spacing-lg);
}

.log-item {
  margin-bottom: 4px;
  line-height: 1.4;
  word-break: break-all;
  display: flex;
  gap: 8px;
}

.log-time {
  color: #6b7280;
  flex-shrink: 0;
}

.log-msg {
  color: #e5e7eb;
}

.log-item.error .log-msg {
  color: #ef4444;
}

.log-item.success .log-msg {
  color: #10b981;
}

.log-item.warning .log-msg {
  color: #f59e0b;
}

</style>
