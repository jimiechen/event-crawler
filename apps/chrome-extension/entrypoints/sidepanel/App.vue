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

      <!-- MCP测试Tab - 新版MCP与Skill集成测试 -->
      <div v-if="activeTab === 'mcp'" class="tab-content">
        <div class="section">
          <div class="config-card">
            <div class="section-header">
              <h3>🤖 MCP与Skill集成测试</h3>
              <p>基于WebSocket的AI平台交互测试</p>
            </div>

            <!-- 连接状态指示器 -->
            <div class="mcp-status-bar">
              <div class="status-item">
                <div class="status-indicator" :class="wsStatus.connected ? 'connected' : 'disconnected'"></div>
                <span>{{ wsStatus.text }}</span>
              </div>
              <div class="status-item">
                <div class="status-indicator" :class="kimiStatus.ready ? 'connected' : 'disconnected'"></div>
                <span>Kimi网页</span>
              </div>
              <div class="status-item">
                <div class="status-indicator" :class="deepseekStatus.ready ? 'connected' : 'disconnected'"></div>
                <span>DeepSeek网页</span>
              </div>
              <div class="status-item">
                <div class="status-indicator" :class="backendStatus.connected ? 'connected' : 'disconnected'"></div>
                <span>后端服务</span>
              </div>
            </div>

            <!-- 平台选择 -->
            <div class="mcp-section">
              <h4>🎯 选择AI平台</h4>
              <div class="platform-selector">
                <button 
                  class="platform-btn" 
                  :class="{ active: selectedPlatform === 'kimi' }"
                  @click="selectPlatform('kimi')"
                >
                  <span class="platform-icon">🌙</span>
                  <span class="platform-name">Kimi</span>
                  <span class="platform-url">kimi.com</span>
                </button>
                <button 
                  class="platform-btn" 
                  :class="{ active: selectedPlatform === 'deepseek' }"
                  @click="selectPlatform('deepseek')"
                >
                  <span class="platform-icon">🐋</span>
                  <span class="platform-name">DeepSeek</span>
                  <span class="platform-url">deepseek.com</span>
                </button>
              </div>
            </div>

            <!-- 图片上传区域 -->
            <div class="mcp-section">
              <h4>🖼️ 图片上传</h4>
              <div 
                class="image-upload-area"
                :class="{ 'drag-over': isDragging }"
                @dragover.prevent="isDragging = true"
                @dragleave.prevent="isDragging = false"
                @drop.prevent="handleImageDrop"
                @click="triggerImageSelect"
              >
                <input 
                  ref="imageInput"
                  type="file" 
                  accept="image/*" 
                  style="display: none"
                  @change="handleImageSelect"
                />
                <div v-if="!uploadedImage" class="upload-placeholder">
                  <span class="upload-icon">📤</span>
                  <p>点击或拖拽上传图片</p>
                  <p class="upload-hint">支持 JPG, PNG, GIF 格式</p>
                </div>
                <div v-else class="image-preview">
                  <img :src="uploadedImage" alt="预览" />
                  <button class="remove-image" @click.stop="removeImage">✕</button>
                </div>
              </div>
            </div>

            <!-- 消息输入 -->
            <div class="mcp-section">
              <h4>💬 发送消息</h4>
              <div class="message-input-area">
                <textarea 
                  v-model="messageText"
                  class="message-textarea"
                  placeholder="输入要发送给AI的消息..."
                  rows="3"
                ></textarea>
                <div class="message-actions">
                  <button 
                    class="ths-btn ths-btn-secondary"
                    @click="newChat"
                    :disabled="skillLoading"
                  >
                    <span>🆕</span> 新对话
                  </button>
                  <button 
                    class="ths-btn ths-btn-primary"
                    @click="sendMessage"
                    :disabled="skillLoading || !messageText.trim()"
                  >
                    <span>📤</span> {{ skillLoading ? '发送中...' : '发送' }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Skill快速测试 -->
            <div class="mcp-section">
              <h4>🚀 Skill快速测试</h4>
              <div class="skill-grid">
                <div class="skill-card" @click="testSkill('kimi_chat')">
                  <div class="skill-icon">🌙</div>
                  <div class="skill-name">Kimi对话</div>
                  <div class="skill-desc">与Kimi AI进行对话</div>
                </div>
                <div class="skill-card" @click="testSkill('deepseek_chat')">
                  <div class="skill-icon">🐋</div>
                  <div class="skill-name">DeepSeek对话</div>
                  <div class="skill-desc">与DeepSeek AI对话</div>
                </div>
                <div class="skill-card" @click="testSkill('upload_image')">
                  <div class="skill-icon">🖼️</div>
                  <div class="skill-name">上传图片</div>
                  <div class="skill-desc">上传图片到AI平台</div>
                </div>
                <div class="skill-card" @click="testSkill('analyze_image')">
                  <div class="skill-icon">🔍</div>
                  <div class="skill-name">分析图片</div>
                  <div class="skill-desc">OCR或视觉分析</div>
                </div>
                <div class="skill-card" @click="testSkill('get_chat_history')">
                  <div class="skill-icon">📜</div>
                  <div class="skill-name">获取历史</div>
                  <div class="skill-desc">获取对话历史记录</div>
                </div>
                <div class="skill-card" @click="testSkill('get_prompt')">
                  <div class="skill-icon">📝</div>
                  <div class="skill-name">获取提示词</div>
                  <div class="skill-desc">获取提示词模板</div>
                </div>
              </div>
            </div>

            <!-- DeepSeek专项测试 -->
            <div class="mcp-section" v-if="selectedPlatform === 'deepseek'">
              <h4>🐋 DeepSeek专项测试</h4>
              <div class="deepseek-tests">
                <button class="ths-btn ths-btn-secondary" @click="openDeepSeek">
                  <span>🌐</span> 打开DeepSeek
                </button>
                <button class="ths-btn ths-btn-secondary" @click="checkDeepSeekReady">
                  <span>✅</span> 检查页面状态
                </button>
                <button class="ths-btn ths-btn-info" @click="testDeepSeekWithImage">
                  <span>🖼️</span> 图片+消息测试
                </button>
              </div>
            </div>

            <!-- 执行结果 -->
            <div v-if="skillResult" class="mcp-section">
              <h4>📊 执行结果</h4>
              <div class="skill-result">
                <div class="result-header">
                  <span class="result-status" :class="skillResult.success ? 'success' : 'error'">
                    {{ skillResult.success ? '✅ 成功' : '❌ 失败' }}
                  </span>
                  <span class="result-time">{{ formatTime(skillResult.timestamp) }}</span>
                </div>
                <div class="result-content">
                  <div v-if="skillResult.data?.reply" class="reply-content">
                    <strong>AI回复:</strong>
                    <pre>{{ skillResult.data.reply }}</pre>
                  </div>
                  <div v-else-if="skillResult.data?.text" class="ocr-content">
                    <strong>OCR结果:</strong>
                    <pre>{{ skillResult.data.text }}</pre>
                  </div>
                  <div v-else>
                    <pre>{{ JSON.stringify(skillResult.data, null, 2) }}</pre>
                  </div>
                </div>
              </div>
            </div>

            <!-- 流式响应显示 -->
            <div v-if="streamChunks.length > 0" class="mcp-section">
              <h4>🌊 流式响应</h4>
              <div class="stream-content">
                <div v-for="(chunk, index) in streamChunks" :key="index" class="stream-chunk">
                  {{ chunk }}
                </div>
                <div v-if="isStreaming" class="stream-loading">接收中...</div>
              </div>
            </div>

            <!-- 错误消息 -->
            <div v-if="skillError" class="mcp-error">
              <span>❌</span> {{ skillError }}
            </div>

            <!-- 连接控制 -->
            <div class="mcp-section">
              <h4>🔌 连接控制</h4>
              <div class="connection-controls">
                <button 
                  class="ths-btn ths-btn-primary"
                  @click="connectWebSocket"
                  :disabled="wsStatus.connected"
                >
                  <span>🔌</span> 连接WebSocket
                </button>
                <button 
                  class="ths-btn ths-btn-secondary"
                  @click="disconnectWebSocket"
                  :disabled="!wsStatus.connected"
                >
                  <span>🔌</span> 断开连接
                </button>
                <button 
                  class="ths-btn ths-btn-info"
                  @click="checkBackendStatus"
                >
                  <span>📡</span> 检查后端状态
                </button>
              </div>
            </div>
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
            
            <!-- 控制中心 -->
            <div class="control-center-section">
              <div class="main-action">
                <button 
                  @click="openAndCaptureList"
                  :disabled="isSyncing"
                  class="ths-btn ths-btn-primary ths-btn-large full-width-btn"
                >
                  {{ isSyncing ? '🔄 同步中...' : '🚀 一键同步数据 (抓取+质检)' }}
                </button>
                <div class="sync-status-text" :class="{ 'active': isSyncing }">
                  {{ syncStatusMessage }}
                </div>
              </div>
            </div>
            
            <!-- 统计信息 -->
            <div class="crawler-stats">
              <div class="stat-grid">
                <div class="stat-item">
                  <span class="stat-label">列表抓取</span>
                  <span class="stat-value">{{ okoooState.list.progress || '未开始' }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">本次抓取</span>
                  <span class="stat-value">{{ okoooState.crawler.currentMatchIndex }}/{{ okoooState.crawler.totalMatches }}</span>
                </div>
                <div class="stat-item" :class="{ 'error': okoooState.repair.repairingCount > 0 }">
                  <span class="stat-label">待修复</span>
                  <span class="stat-value">{{ okoooState.repair.repairingCount }}</span>
                </div>
                <div class="stat-item success">
                  <span class="stat-label">成功</span>
                  <span class="stat-value">{{ okoooState.crawler.successCount }}</span>
                </div>
              </div>
            </div>
            
            <!-- 进度条 -->
            <div v-if="okoooState.crawler.totalMatches > 0" class="progress-section">
              <div class="progress-bar large">
                <div 
                  class="progress-fill"
                  :style="{ width: `${(okoooState.crawler.currentMatchIndex / okoooState.crawler.totalMatches) * 100}%` }"
                ></div>
              </div>
              <div class="progress-text">
                总进度: {{ Math.round((okoooState.crawler.currentMatchIndex / okoooState.crawler.totalMatches) * 100) }}%
              </div>
            </div>

            <!-- 修复任务与进度列表 -->
            <div v-if="unifiedRepairList.length > 0" class="repair-details-section">
              <div class="section-header">
                <h4>⚠️ 待修复任务 ({{ unifiedRepairList.length }})</h4>
                <button 
                  @click="startRepair(false)" 
                  class="ths-btn ths-btn-warning ths-btn-sm"
                  :disabled="isSyncing"
                >
                  🛠️ 立即修复
                </button>
              </div>
              <div class="repair-list">
                <div
                  v-for="item in unifiedRepairList"
                  :key="item.id"
                  class="repair-item"
                  :class="{'item-success': item.status === 'success', 'item-running': item.status !== 'success' && item.current > 0}"
                >
                  <div class="repair-item-left">
                    <span class="match-id">ID: {{ item.id }}</span>
                    <span class="error-reason">{{ item.reason }}</span>
                  </div>
                  <div class="repair-item-right">
                    <!-- 查看数据按钮 -->
                    <button
                      v-if="item.status === 'success'"
                      class="view-data-btn"
                      @click="openMatchDataModal(item.id)"
                      title="查看解析数据"
                    >
                      📋 数据
                    </button>
                    <span v-if="item.status === 'success'" class="status-success">✅ 完成</span>
                    <span v-else-if="item.current > 0 || item.status === 'pending'" class="status-running">
                      {{ item.current }}/{{ item.total }}
                      <span v-if="item.current > 0" class="loading-dots">...</span>
                    </span>
                    <span v-else class="status-pending">等待中</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 步骤化工作流控制面板 -->
            <div class="workflow-section">
              <div class="section-header-small">
                <h4>📋 数据抓取工作流</h4>
                <button @click="resetWorkflowState" class="text-btn">重置</button>
              </div>

              <!-- 步骤1: 抓取比赛列表 -->
              <div class="workflow-step" :class="workflowState.step1_captureList.status">
                <div class="step-header">
                  <span class="step-number">1</span>
                  <span class="step-title">抓取比赛列表</span>
                  <span class="step-status" :class="workflowState.step1_captureList.status">
                    {{ workflowState.step1_captureList.status === 'idle' ? '待执行' : 
                       workflowState.step1_captureList.status === 'running' ? '执行中...' :
                       workflowState.step1_captureList.status === 'completed' ? '✅ 完成' : '❌ 失败' }}
                  </span>
                </div>
                <div class="step-content">
                  <div v-if="workflowState.step1_captureList.matchIds.length > 0" class="step-result">
                    今日比赛: {{ workflowState.step1_captureList.matchIds.length }} 个
                  </div>
                  <button 
                    @click="startStep1CaptureList" 
                    :disabled="workflowState.step1_captureList.status === 'running' || !currentUrl?.includes('m.okooo.com')"
                    class="ths-btn ths-btn-primary step-btn"
                  >
                    {{ workflowState.step1_captureList.status === 'completed' ? '重新抓取' : '开始抓取' }}
                  </button>
                </div>
              </div>

              <!-- 步骤2: 筛选新比赛 -->
              <div class="workflow-step" :class="workflowState.step2_filterMatches.status">
                <div class="step-header">
                  <span class="step-number">2</span>
                  <span class="step-title">筛选新比赛</span>
                  <span class="step-status" :class="workflowState.step2_filterMatches.status">
                    {{ workflowState.step2_filterMatches.status === 'idle' ? '待执行' : 
                       workflowState.step2_filterMatches.status === 'running' ? '执行中...' :
                       workflowState.step2_filterMatches.status === 'completed' ? '✅ 完成' : '❌ 失败' }}
                  </span>
                </div>
                <div class="step-content">
                  <div v-if="workflowState.step2_filterMatches.status !== 'idle'" class="step-result">
                    <span class="stat new">新: {{ workflowState.step2_filterMatches.newMatches.length }}</span>
                    <span class="stat existing">已存在: {{ workflowState.step2_filterMatches.existingMatches.length }}</span>
                  </div>
                  <button 
                    @click="startStep2FilterMatches" 
                    :disabled="workflowState.step2_filterMatches.status === 'running' || workflowState.step1_captureList.matchIds.length === 0"
                    class="ths-btn ths-btn-primary step-btn"
                  >
                    {{ workflowState.step2_filterMatches.status === 'completed' ? '重新筛选' : '开始筛选' }}
                  </button>
                </div>
              </div>

              <!-- 步骤3: 下载比赛数据 -->
              <div class="workflow-step" :class="workflowState.step3_downloadData.status">
                <div class="step-header">
                  <span class="step-number">3</span>
                  <span class="step-title">下载比赛数据</span>
                  <span class="step-status" :class="workflowState.step3_downloadData.status">
                    {{ workflowState.step3_downloadData.status === 'idle' ? '待执行' : 
                       workflowState.step3_downloadData.status === 'running' ? '执行中...' :
                       workflowState.step3_downloadData.status === 'completed' ? '✅ 完成' : '❌ 失败' }}
                  </span>
                </div>
                <div class="step-content">
                  <div v-if="workflowState.step3_downloadData.status !== 'idle'" class="step-result">
                    <div class="progress-bar">
                      <div class="progress-fill" :style="{ width: workflowState.step3_downloadData.totalTasks > 0 ? (workflowState.step3_downloadData.completedTasks / workflowState.step3_downloadData.totalTasks * 100) + '%' : '0%' }"></div>
                    </div>
                    <div class="progress-text">
                      {{ workflowState.step3_downloadData.completedTasks }}/{{ workflowState.step3_downloadData.totalTasks }}
                      <span v-if="workflowState.step3_downloadData.skippedTasks > 0" class="skipped">(跳过 {{ workflowState.step3_downloadData.skippedTasks }})</span>
                    </div>
                  </div>
                  <button 
                    @click="startStep3DownloadData" 
                    :disabled="workflowState.step3_downloadData.status === 'running' || workflowState.step2_filterMatches.newMatches.length === 0"
                    class="ths-btn ths-btn-primary step-btn"
                  >
                    {{ workflowState.step3_downloadData.status === 'completed' ? '重新下载' : '开始下载' }}
                  </button>
                  <div v-if="workflowState.step3_downloadData.status === 'running'" class="captcha-notice">
                    🛑 如遇验证码请手动处理，处理完成后自动继续
                  </div>
                </div>
              </div>

              <!-- 步骤4: 解析比赛数据 -->
              <div class="workflow-step" :class="workflowState.step4_parseData.status">
                <div class="step-header">
                  <span class="step-number">4</span>
                  <span class="step-title">解析比赛数据</span>
                  <span class="step-status" :class="workflowState.step4_parseData.status">
                    {{ workflowState.step4_parseData.status === 'idle' ? '待执行' : 
                       workflowState.step4_parseData.status === 'running' ? '执行中...' :
                       workflowState.step4_parseData.status === 'completed' ? '✅ 完成' : '❌ 失败' }}
                  </span>
                </div>
                <div class="step-content">
                  <div v-if="workflowState.step4_parseData.status !== 'idle'" class="step-result">
                    <div class="progress-bar">
                      <div class="progress-fill" :style="{ width: workflowState.step4_parseData.totalMatches > 0 ? (workflowState.step4_parseData.parsedMatches / workflowState.step4_parseData.totalMatches * 100) + '%' : '0%' }"></div>
                    </div>
                    <div class="progress-text">
                      {{ workflowState.step4_parseData.parsedMatches }}/{{ workflowState.step4_parseData.totalMatches }}
                    </div>
                  </div>
                  <button 
                    @click="startStep4ParseData" 
                    :disabled="workflowState.step4_parseData.status === 'running' || workflowState.step3_downloadData.status !== 'completed'"
                    class="ths-btn ths-btn-primary step-btn"
                  >
                    {{ workflowState.step4_parseData.status === 'completed' ? '重新解析' : '开始解析' }}
                  </button>
                </div>
              </div>
            </div>

            <!-- 状态显示区域 -->
            <div class="status-bar">
              <div class="status-item">
                <span class="label">插件状态:</span>
                <span class="value" :class="pluginStatus.isRunning ? 'running' : 'idle'">
                  {{ pluginStatus.isRunning ? '运行中' + (pluginStatus.currentTask ? ' - ' + pluginStatus.currentTask : '') : '空闲' }}
                </span>
              </div>
              <div class="status-item">
                <span class="label">服务端状态:</span>
                <span class="value" :class="serverStatus.isProcessing ? 'running' : 'idle'">
                  {{ serverStatus.isProcessing ? '处理中' + (serverStatus.currentMatch ? ' - ' + serverStatus.currentMatch : '') : '空闲' }}
                </span>
              </div>
            </div>

            <!-- 手动控制面板 (保留作为备用) -->
            <div class="manual-controls-section" style="margin-top: 20px; padding-top: 20px; border-top: 1px dashed #ccc;">
              <div class="section-header-small">
                <h4>🔧 手动控制 (备用)</h4>
              </div>
              <div class="manual-buttons">
                <button 
                  v-if="!okoooState.crawler.isRunning"
                  @click="startOkoooCrawler" 
                  :disabled="isSyncing || !currentUrl?.includes('m.okooo.com')"
                  class="ths-btn ths-btn-secondary"
                >
                  🚀 传统模式-开始爬虫
                </button>
                <button 
                  v-else
                  @click="stopOkoooCrawler"
                  class="ths-btn ths-btn-danger"
                >
                  🛑 停止爬虫
                </button>
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

            <!-- 解析结果展示 -->
            <div v-if="parseResults.length > 0 || parseWarnings.length > 0 || parseErrors.length > 0" class="parse-results-section">
              <div class="section-header-small">
                <h4>📊 解析结果</h4>
                <button @click="clearParseResults" class="text-btn">清空</button>
              </div>
              
              <!-- 解析进度 -->
              <div v-if="parseProgress.total > 0" class="parse-progress">
                <div class="progress-bar">
                  <div 
                    class="progress-fill parse"
                    :style="{ width: `${(parseProgress.current / parseProgress.total) * 100}%` }"
                  ></div>
                </div>
                <div class="progress-text">
                  解析进度: {{ parseProgress.current }}/{{ parseProgress.total }}
                </div>
              </div>

              <!-- 解析总结 -->
              <div v-if="parseSummary" class="parse-summary">
                <div class="summary-card" :class="{ 'has-warning': parseSummary.incomplete > 0, 'has-error': parseSummary.failed > 0 }">
                  <div class="summary-title">📋 解析总结</div>
                  <div class="summary-stats">
                    <span class="stat success">✅ {{ parseSummary.parsed }}</span>
                    <span v-if="parseSummary.incomplete > 0" class="stat warning">⚠️ {{ parseSummary.incomplete }}</span>
                    <span v-if="parseSummary.failed > 0" class="stat error">❌ {{ parseSummary.failed }}</span>
                  </div>
                  <div class="summary-message">{{ parseSummary.message }}</div>
                </div>
              </div>

              <!-- 解析错误 -->
              <div v-if="parseErrors.length > 0" class="parse-errors">
                <div class="subsection-header">
                  <h5>❌ 解析失败 ({{ parseErrors.length }})</h5>
                </div>
                <div class="error-list">
                  <div v-for="(error, index) in parseErrors" :key="index" class="error-item">
                    <span class="match-id">ID: {{ error.matchId }}</span>
                    <span class="error-msg">{{ error.error }}</span>
                  </div>
                </div>
              </div>

              <!-- 解析告警 -->
              <div v-if="parseWarnings.length > 0" class="parse-warnings">
                <div class="subsection-header">
                  <h5>⚠️ 字段不完整 ({{ parseWarnings.length }})</h5>
                </div>
                <div class="warning-list">
                  <div v-for="(warning, index) in parseWarnings" :key="index" class="warning-item">
                    <div class="warning-header">
                      <span class="match-id">ID: {{ warning.matchId }}</span>
                      <span class="warning-time">{{ warning.timestamp }}</span>
                    </div>
                    <div class="missing-fields">
                      缺少: {{ warning.missingFields.join(', ') }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- 解析完成列表 -->
              <div v-if="parseResults.length > 0" class="parse-complete-list">
                <div class="subsection-header">
                  <h5>✅ 解析完成 ({{ parseResults.length }})</h5>
                </div>
                <div class="result-list">
                  <div
                    v-for="(result, index) in parseResults"
                    :key="index"
                    class="result-item"
                    :class="{ 'incomplete': !result.isComplete }"
                  >
                    <div class="result-header">
                      <span class="match-id">ID: {{ result.matchId }}</span>
                      <span class="result-status" :class="{ 'complete': result.isComplete, 'incomplete': !result.isComplete }">
                        {{ result.isComplete ? '✅ 完整' : '⚠️ 缺字段' }}
                      </span>
                    </div>
                    <div v-if="!result.isComplete && result.missingFields.length > 0" class="missing-fields">
                      缺少: {{ result.missingFields.join(', ') }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- 任务流程展示 -->
              <div v-if="Object.keys(matchTaskFlows).length > 0" class="task-flow-section">
                <div class="subsection-header">
                  <h5>📋 任务流程 ({{ Object.keys(matchTaskFlows).length }})</h5>
                </div>
                <div class="task-flow-list">
                  <div
                    v-for="(flow, matchId) in matchTaskFlows"
                    :key="matchId"
                    class="task-flow-item"
                    :class="{ 'active': currentProcessingMatchId === matchId }"
                  >
                    <!-- 比赛ID -->
                    <div class="task-flow-header">
                      <span class="match-id">ID: {{ matchId }}</span>
                      <span v-if="currentProcessingMatchId === matchId" class="processing-badge">处理中...</span>
                    </div>

                    <!-- 步骤1: 创建目录 -->
                    <div class="task-step">
                      <span class="step-icon" :class="flow.directory.status">
                        {{ flow.directory.status === 'completed' ? '✅' : flow.directory.status === 'error' ? '❌' : '⏳' }}
                      </span>
                      <span class="step-name" :class="flow.directory.status">
                        创建目录
                      </span>
                      <span v-if="flow.directory.exists" class="step-status success">已存在</span>
                    </div>

                    <!-- 步骤2: 下载8个文件 -->
                    <div class="task-step">
                      <span class="step-icon" :class="flow.files.completedCount === flow.files.totalCount ? 'completed' : 'processing'">
                        {{ flow.files.completedCount === flow.files.totalCount ? '✅' : '⏳' }}
                      </span>
                      <span class="step-name" :class="flow.files.completedCount === flow.files.totalCount ? 'completed' : 'processing'">
                        下载文件 ({{ flow.files.completedCount }}/{{ flow.files.totalCount }})
                      </span>
                    </div>

                    <!-- 8个文件列表 -->
                    <div v-if="Object.keys(flow.files.items).length > 0" class="file-list">
                      <div
                        v-for="(file, key) in flow.files.items"
                        :key="key"
                        class="file-item"
                        :class="file.status"
                      >
                        <span class="file-status-icon">
                          {{ file.status === 'completed' ? '🟢' : file.status === 'missing' ? '⚪' : '🔵' }}
                        </span>
                        <span class="file-name" :class="file.status">{{ file.name }}</span>
                        <span class="file-filename">{{ file.filename }}</span>
                      </div>
                    </div>

                    <!-- 步骤3: 解析JSON -->
                    <div class="task-step">
                      <span class="step-icon" :class="flow.parse.status">
                        {{ flow.parse.status === 'completed' ? '✅' : flow.parse.status === 'error' ? '❌' : flow.parse.status === 'warning' ? '⚠️' : '⏳' }}
                      </span>
                      <span class="step-name" :class="flow.parse.status">
                        解析JSON
                      </span>
                      <span v-if="flow.parse.isComplete" class="step-status success">完成</span>
                      <span v-else-if="flow.parse.status === 'warning'" class="step-status warning">字段不完整</span>
                    </div>

                    <!-- 查看数据按钮 -->
                    <div v-if="flow.parse.status === 'completed' || flow.parse.status === 'warning'" class="task-flow-actions">
                      <button class="view-data-btn-small" @click="openMatchDataModal(matchId)">
                        📋 查看数据
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- 修复任务通知 -->
    <div v-if="repairNotification.visible" class="modal-overlay notification-overlay" @click="repairNotification.visible = false">
      <div class="modal-content notification-content" @click.stop>
        <div class="modal-header">
          <h3>🛠️ 发现需要修复的比赛</h3>
          <button @click="repairNotification.visible = false" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div class="notification-info">
            <p><strong>日期:</strong> {{ repairNotification.date }}</p>
            <p><strong>比赛数量:</strong> {{ repairNotification.totalMatches }} 场</p>
            <p><strong>任务数量:</strong> {{ repairNotification.totalTasks }} 个</p>
            <p class="notification-message">{{ repairNotification.message }}</p>
          </div>
          <div class="notification-actions">
            <button @click="startRepairFromNotification" class="ths-btn ths-btn-primary">
              立即修复
            </button>
            <button @click="repairNotification.visible = false" class="ths-btn ths-btn-secondary">
              稍后处理
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 比赛数据弹窗 -->
    <MatchDataModal
      :visible="matchDataModalVisible"
      :match-id="selectedMatchId"
      :date="selectedMatchDate"
      @close="closeMatchDataModal"
    />

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
// @ts-ignore
import {
  initializeMCPSession,
  getChromeWebContent,
  parseFootballMatches as parseFootballMatchesLib,
  generateFootballReport,
} from '../../utils/football-parser.js';
import MonitoringStatusPanel from '../../components/MonitoringStatusPanel.vue';
import SystemStatus from './components/SystemStatus.vue';
import WencaiDataCapture from './components/WencaiDataCapture.vue';
import SessionManager from './components/SessionManager.vue';
import MatchDataModal from '../../components/MatchDataModal.vue';
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

// MCP测试相关响应式数据 (旧版兼容)
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

// ==================== 新版MCP与Skill集成测试数据 ====================

// WebSocket连接状态
const wsStatus = ref<{ connected: boolean; text: string }>({ connected: false, text: 'WebSocket未连接' });
const wsConnection = ref<WebSocket | null>(null);

// 平台状态
const kimiStatus = ref<{ ready: boolean; tabId: number | null }>({ ready: false, tabId: null });
const deepseekStatus = ref<{ ready: boolean; tabId: number | null }>({ ready: false, tabId: null });
const backendStatus = ref<{ connected: boolean; url: string }>({ connected: false, url: 'http://localhost:8000' });

// 当前选择的平台
const selectedPlatform = ref<'kimi' | 'deepseek'>('deepseek');

// 图片上传
const uploadedImage = ref<string>('');
const isDragging = ref<boolean>(false);
const imageInput = ref<HTMLInputElement | null>(null);

// 消息输入
const messageText = ref<string>('');

// Skill执行
const skillLoading = ref<boolean>(false);
const skillError = ref<string>('');
const skillResult = ref<any>(null);

// 流式响应
const streamChunks = ref<string[]>([]);
const isStreaming = ref<boolean>(false);

// WebSocket配置
const WS_SERVER_URL = 'ws://localhost:8765';

// Okooo Sync State
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

interface OkoooListStatus {
  isCapturing: boolean;
  progress: string;
  lastResult: { success: boolean; message: string; size?: number } | null;
}

interface RepairStatus {
  isRunning: boolean;
  isDryRun: boolean;
  totalChecked: number;
  repairingCount: number;
  ids: string[];
  repairDetails: Array<{
    id: string;
    reason: string;
    status?: 'pending' | 'success' | 'error';
    current?: number;
    total?: number;
  }>;
  message: string;
}

interface OkoooSyncState {
  crawler: CrawlerStatus;
  list: OkoooListStatus;
  repair: RepairStatus;
}

const okoooState = ref<OkoooSyncState>({
  crawler: {
    isRunning: false,
    phase: 'idle',
    totalMatches: 0,
    currentMatchIndex: 0,
    totalHistory: 0,
    currentHistoryIndex: 0,
    successCount: 0,
    errorCount: 0,
    results: []
  },
  list: {
    isCapturing: false,
    progress: '',
    lastResult: null
  },
  repair: {
    isRunning: false,
    isDryRun: false,
    totalChecked: 0,
    repairingCount: 0,
    ids: [],
    repairDetails: [],
    message: ''
  }
});

// ==================== 步骤化工作流状态 ====================
interface WorkflowStep {
  status: 'idle' | 'running' | 'completed' | 'error';
  message: string;
  progress: { current: number; total: number };
}

interface WorkflowState {
  step1_captureList: WorkflowStep & { matchIds: string[] };
  step2_filterMatches: WorkflowStep & { 
    newMatches: string[];
    existingMatches: string[];
    skippedMatches: string[];
  };
  step3_downloadData: WorkflowStep & {
    totalTasks: number;
    completedTasks: number;
    skippedTasks: number;
    errorTasks: number;
    matchProgress: Record<string, { completed: number; total: number }>;
  };
  step4_parseData: WorkflowStep & {
    totalMatches: number;
    parsedMatches: number;
    failedMatches: number;
  };
}

const workflowState = ref<WorkflowState>({
  step1_captureList: {
    status: 'idle',
    message: '等待开始',
    progress: { current: 0, total: 0 },
    matchIds: []
  },
  step2_filterMatches: {
    status: 'idle',
    message: '等待开始',
    progress: { current: 0, total: 0 },
    newMatches: [],
    existingMatches: [],
    skippedMatches: []
  },
  step3_downloadData: {
    status: 'idle',
    message: '等待开始',
    progress: { current: 0, total: 0 },
    totalTasks: 0,
    completedTasks: 0,
    skippedTasks: 0,
    errorTasks: 0,
    matchProgress: {}
  },
  step4_parseData: {
    status: 'idle',
    message: '等待开始',
    progress: { current: 0, total: 0 },
    totalMatches: 0,
    parsedMatches: 0,
    failedMatches: 0
  }
});

// 重置工作流状态
const resetWorkflowState = () => {
  workflowState.value = {
    step1_captureList: {
      status: 'idle',
      message: '等待开始',
      progress: { current: 0, total: 0 },
      matchIds: []
    },
    step2_filterMatches: {
      status: 'idle',
      message: '等待开始',
      progress: { current: 0, total: 0 },
      newMatches: [],
      existingMatches: [],
      skippedMatches: []
    },
    step3_downloadData: {
      status: 'idle',
      message: '等待开始',
      progress: { current: 0, total: 0 },
      totalTasks: 0,
      completedTasks: 0,
      skippedTasks: 0,
      errorTasks: 0,
      matchProgress: {}
    },
    step4_parseData: {
      status: 'idle',
      message: '等待开始',
      progress: { current: 0, total: 0 },
      totalMatches: 0,
      parsedMatches: 0,
      failedMatches: 0
    }
  };
};

// ==================== 状态来源区分 ====================
// 插件端状态（来自background脚本）
const pluginStatus = ref({
  isRunning: false,
  currentTask: null as string | null,
  phase: 'idle' as string,
  logs: [] as string[]
});

// 服务端状态（来自SSE）
const serverStatus = ref({
  isProcessing: false,
  currentMatch: null as string | null,
  progress: null as { current: number; total: number } | null
});

// Backward compatibility proxies for template (optional, but cleaner to update template)
// We will update template references.

// Unified Sync Status
const isSyncing = computed(() => {
  return okoooState.value.list.isCapturing || okoooState.value.repair.isRunning;
});

const syncStatusMessage = computed(() => {
  const { list, repair } = okoooState.value;
  if (list.isCapturing) {
    return `正在抓取列表 ${list.progress}...`;
  }
  if (repair.isRunning && repair.isDryRun) {
    return '正在检查数据完整性...';
  }
  if (list.lastResult && !list.lastResult.success) {
    return `上次失败: ${list.lastResult.message}`;
  }
  if (repair.message) {
    return repair.message;
  }
  return '准备就绪';
});

const repairNotification = ref({
    visible: false,
    message: '',
    totalMatches: 0,
    totalTasks: 0,
    date: ''
});

const startRepairFromNotification = async () => {
    repairNotification.value.visible = false;
    okoooState.value.repair.isRunning = true;
    okoooState.value.repair.message = '正在获取修复任务...';
    
    try {
        // Fetch tasks
        const response = await fetch(`${backendUrl.value}/api/v1/okooo/repair-tasks`);
        const result = await response.json();
        
        if (result.success && result.data && result.data.length > 0) {
            okoooState.value.repair.message = `获取到 ${result.data.length} 个任务，开始爬取...`;
            okoooState.value.crawler.isRunning = true;
            
            // Send to extension
            chrome.runtime.sendMessage({
                type: 'OKOOO_START_REPAIR_TASKS',
                tasks: result.data
            }).then(response => {
                if (response.success) {
                    startCrawlerStatusPolling();
                } else {
                    okoooState.value.crawler.isRunning = false;
                    okoooState.value.repair.message = '修复启动失败: ' + response.message;
                }
            }).catch((err: any) => {
                okoooState.value.crawler.isRunning = false;
                okoooState.value.repair.message = '修复启动异常: ' + err;
            });
        } else {
            okoooState.value.repair.message = '未获取到修复任务或任务列表为空';
            okoooState.value.repair.isRunning = false;
        }
    } catch (e: any) {
        okoooState.value.repair.message = '获取任务失败: ' + e.message;
        okoooState.value.repair.isRunning = false;
    }
};

const startRepair = async (isDryRun: boolean = false) => {
  if (okoooState.value.repair.isRunning) return;
  
  okoooState.value.repair.isRunning = true;
  okoooState.value.repair.isDryRun = isDryRun;
  okoooState.value.repair.message = isDryRun ? '正在检查数据完整性...' : '正在检查并修复...';
  
  try {
    // Default to today's date
    const today = new Date().toISOString().split('T')[0];
    
    const response = await fetch(`${backendUrl.value}/api/v1/okooo/repair`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        date: today,
        dry_run: isDryRun
      })
    });
    
    const data = await response.json();
    if (data.success) {
      okoooState.value.repair.totalChecked = data.data.total_checked;
      okoooState.value.repair.repairingCount = data.data.repairing_count;
      okoooState.value.repair.ids = data.data.ids;
      okoooState.value.repair.repairDetails = data.data.repair_details || [];
      okoooState.value.repair.message = data.data.message;

      // 如果没有需要修复的，清空之前的待修复列表
      if (data.data.repairing_count === 0) {
        okoooState.value.repair.repairDetails = [];
        okoooState.value.repair.isRunning = false;
        return;
      }

      if (data.data.repairing_count > 0 && !isDryRun) {
        okoooState.value.crawler.isRunning = true;
        
        // 获取生成的任务详情
        const tasksResponse = await fetch(`${backendUrl.value}/api/v1/okooo/repair-tasks`);
        const tasksResult = await tasksResponse.json();
        
        if (tasksResult.success && tasksResult.data && tasksResult.data.length > 0) {
            // 触发 Chrome Extension 爬取 (使用直接任务模式)
            chrome.runtime.sendMessage({
              type: 'OKOOO_START_REPAIR_TASKS',
              tasks: tasksResult.data
            }).then(response => {
              if (response.success) {
                startCrawlerStatusPolling();
              } else {
                 okoooState.value.crawler.isRunning = false;
                 okoooState.value.repair.isRunning = false;
                 okoooState.value.repair.message = '修复启动失败: ' + response.message;
              }
            }).catch((err: any) => {
                 okoooState.value.crawler.isRunning = false;
                 okoooState.value.repair.isRunning = false;
                 okoooState.value.repair.message = '修复启动异常: ' + err;
            });
        } else {
            // Fallback to IDs if tasks not found (though unlikely)
            chrome.runtime.sendMessage({
              type: 'OKOOO_START_REPAIR',
              ids: data.data.ids
            }).then(response => {
              if (response.success) {
                startCrawlerStatusPolling();
              } else {
                 okoooState.value.crawler.isRunning = false;
                 okoooState.value.repair.isRunning = false;
                 okoooState.value.repair.message = '修复启动失败(ID模式): ' + response.message;
              }
            }).catch((err: any) => {
                 okoooState.value.crawler.isRunning = false;
                 okoooState.value.repair.isRunning = false;
                 okoooState.value.repair.message = '修复启动异常(ID模式): ' + err;
            });
        }
      } else {
        // 没有需要修复的任务或是 dry_run 模式，立即重置状态
        okoooState.value.repair.isRunning = false;
      }
    } else {
      okoooState.value.repair.message = '失败: ' + data.message;
      okoooState.value.repair.isRunning = false;
    }
  } catch (e: any) {
    okoooState.value.repair.message = '错误: ' + e.message;
    okoooState.value.repair.isRunning = false;
  }
};

// Handicap crawler status (Removed)
/*
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
*/


// 实时日志相关
interface LogEntry {
  message: string;
  level: string;
  timestamp: string;
}

// 解析结果相关类型
interface ParseResult {
  matchId: string;
  date: string;
  isComplete: boolean;
  missingFields: string[];
  outputPath: string;
  timestamp: string;
}

interface ParseWarning {
  matchId: string;
  date: string;
  missingFields: string[];
  message: string;
  timestamp: string;
}

interface ParseError {
  matchId: string;
  date: string;
  error: string;
  timestamp: string;
}

interface ParseSummary {
  date: string;
  total: number;
  parsed: number;
  failed: number;
  incomplete: number;
  message: string;
}

// 任务流程相关类型
interface TaskFileStatus {
  name: string;
  filename: string;
  exists: boolean;
  status: 'pending' | 'processing' | 'completed' | 'missing' | 'error';
}

interface MatchTaskFlow {
  matchId: string;
  date: string;
  directory: {
    status: 'pending' | 'processing' | 'completed' | 'error';
    exists: boolean;
    path: string;
  };
  files: {
    items: Record<string, TaskFileStatus>;
    completedCount: number;
    totalCount: number;
  };
  parse: {
    status: 'pending' | 'processing' | 'completed' | 'incomplete' | 'error' | 'warning';
    outputPath: string;
    isComplete: boolean;
    missingFields: string[];
  };
}

const okoooLogs = ref<LogEntry[]>([]);
const isLogStreamActive = ref(false);
let eventSource: EventSource | null = null;

// 解析结果相关状态
const parseResults = ref<ParseResult[]>([]);
const parseWarnings = ref<ParseWarning[]>([]);
const parseErrors = ref<ParseError[]>([]);
const parseSummary = ref<ParseSummary | null>(null);
const parseProgress = ref<{ current: number; total: number }>({ current: 0, total: 0 });

// 任务流程状态
const matchTaskFlows = ref<Record<string, MatchTaskFlow>>({});
const currentProcessingMatchId = ref<string>('');

// 比赛数据弹窗状态
const matchDataModalVisible = ref(false);
const selectedMatchId = ref('');
const selectedMatchDate = ref('');

const openMatchDataModal = (matchId: string) => {
  selectedMatchId.value = matchId;
  // 使用当前日期，或者从其他状态获取
  selectedMatchDate.value = new Date().toISOString().split('T')[0];
  matchDataModalVisible.value = true;
};

const closeMatchDataModal = () => {
  matchDataModalVisible.value = false;
  selectedMatchId.value = '';
};

const clearOkoooLogs = () => {
  okoooLogs.value = [];
};

const clearParseResults = () => {
  parseResults.value = [];
  parseWarnings.value = [];
  parseErrors.value = [];
  parseSummary.value = null;
  parseProgress.value = { current: 0, total: 0 };
};

// 刷新爬虫状态
const refreshOkoooStatus = async () => {
  try {
    const response = await chrome.runtime.sendMessage({
      type: 'OKOOO_GET_STATUS'
    });

    if (response.success) {
      const data = response.data;
      okoooState.value.crawler.isRunning = data.isRunning;
      okoooState.value.crawler.phase = data.phase;
      okoooState.value.crawler.totalMatches = data.totalTasks || data.totalMatches || 0;
      okoooState.value.crawler.currentMatchIndex = data.currentTaskIndex || data.currentMatchIndex || 0;
      okoooState.value.crawler.successCount = data.successCount || 0;
      okoooState.value.crawler.errorCount = data.errorCount || 0;
      okoooState.value.crawler.results = data.results || [];
      
      // 更新日志
      if (data.logs && data.logs.length > 0) {
        data.logs.forEach((log: string) => {
          const exists = okoooLogs.value.some(l => l.message === log);
          if (!exists) {
            okoooLogs.value.unshift({
              message: log,
              level: 'info',
              timestamp: new Date().toLocaleTimeString()
            });
          }
        });
        // 保持日志数量在合理范围
        if (okoooLogs.value.length > 200) {
          okoooLogs.value = okoooLogs.value.slice(0, 200);
        }
      }
    }
  } catch (error) {
    console.error('刷新爬虫状态失败:', error);
  }
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

    eventSource.addEventListener('okooo_repair_tasks_ready', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log('收到修复任务通知:', data);
        
        repairNotification.value = {
            visible: true,
            message: data.message,
            totalMatches: data.total_matches,
            totalTasks: data.total_tasks,
            date: data.date
        };
        
      } catch (e) {
        console.error('解析修复任务通知失败:', e);
      }
    });
    
    eventSource.addEventListener('okooo_log', (event: MessageEvent) => {
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

    eventSource.addEventListener('okooo_file_saved', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log('File saved confirmation:', data);
        
        const matchId = data.match_id;
        // 创建新对象以触发Vue响应式更新
        const progress = { ...serverConfirmedProgress.value };
        if (!progress[matchId]) {
          progress[matchId] = {
            current: 0,
            total: 8, // 假设每场比赛8个任务
            status: 'pending'
          };
        }
        
        progress[matchId] = {
          ...progress[matchId],
          current: progress[matchId].current + 1
        };
        
        // 自动计算总数（如果任务数动态变化）
        if (progress[matchId].current >= progress[matchId].total) {
          progress[matchId] = {
            ...progress[matchId],
            status: 'success'
          };
        }
        
        serverConfirmedProgress.value = progress;

      } catch (e) {
        console.error('解析文件保存通知失败:', e);
      }
    });

    // 监听爬虫状态更新
    eventSource.addEventListener('okooo_status', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log('收到爬虫状态更新:', data);
        
        // 更新爬虫状态
        if (data.is_running !== undefined) {
          okoooState.value.crawler.isRunning = data.is_running;
        }
        if (data.phase) {
          okoooState.value.crawler.phase = data.phase;
          
          // 如果任务完成，清空待修复列表
          if (data.phase === 'completed') {
            okoooState.value.repair.repairDetails = [];
            okoooState.value.repair.repairingCount = 0;
          }
        }
        
        // 刷新完整状态
        refreshOkoooStatus();
      } catch (e) {
        console.error('解析爬虫状态更新失败:', e);
      }
    });

    // 监听进度更新
    eventSource.addEventListener('okooo_progress', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log('收到进度更新:', data);
        
        if (data.processed !== undefined && data.total !== undefined) {
          okoooState.value.crawler.currentMatchIndex = data.processed;
          okoooState.value.crawler.totalMatches = data.total;
        }
      } catch (e) {
        console.error('解析进度更新失败:', e);
      }
    });

    // 监听解析完成事件
    eventSource.addEventListener('okooo_parse_complete', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log('收到解析完成通知:', data);
        
        // 添加到解析结果列表
        const result: ParseResult = {
          matchId: data.match_id,
          date: data.date,
          isComplete: data.is_complete,
          missingFields: data.missing_fields || [],
          outputPath: data.output_path,
          timestamp: new Date().toLocaleTimeString()
        };
        
        // 更新或添加解析结果
        const existingIndex = parseResults.value.findIndex(r => r.matchId === result.matchId);
        if (existingIndex >= 0) {
          parseResults.value[existingIndex] = result;
        } else {
          parseResults.value.push(result);
        }
        
        // 更新解析进度
        parseProgress.value = {
          current: data.progress?.current || 0,
          total: data.progress?.total || 0
        };
      } catch (e) {
        console.error('解析完成通知处理失败:', e);
      }
    });

    // 监听解析告警事件
    eventSource.addEventListener('okooo_parse_warning', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log('收到解析告警:', data);
        
        // 添加到告警列表
        parseWarnings.value.push({
          matchId: data.match_id,
          date: data.date,
          missingFields: data.missing_fields || [],
          message: data.message,
          timestamp: new Date().toLocaleTimeString()
        });
      } catch (e) {
        console.error('解析告警处理失败:', e);
      }
    });

    // 监听解析错误事件
    eventSource.addEventListener('okooo_parse_error', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log('收到解析错误:', data);
        
        parseErrors.value.push({
          matchId: data.match_id,
          date: data.date,
          error: data.error,
          timestamp: new Date().toLocaleTimeString()
        });
      } catch (e) {
        console.error('解析错误处理失败:', e);
      }
    });

    // 监听解析总结事件
    eventSource.addEventListener('okooo_parse_summary', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log('收到解析总结:', data);

        parseSummary.value = {
          date: data.date,
          total: data.total,
          parsed: data.parsed,
          failed: data.failed,
          incomplete: data.incomplete,
          message: data.message
        };
      } catch (e) {
        console.error('解析总结处理失败:', e);
      }
    });

    // 监听任务流程事件 - 目录状态
    eventSource.addEventListener('okooo_task_directory_status', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log('收到目录状态:', data);

        const { match_id, date, exists, path, status } = data;

        // 初始化或更新任务流程
        if (!matchTaskFlows.value[match_id]) {
          matchTaskFlows.value[match_id] = {
            matchId: match_id,
            date: date,
            directory: { status: 'pending', exists: false, path: '' },
            files: { items: {}, completedCount: 0, totalCount: 8 },
            parse: { status: 'pending', outputPath: '', isComplete: false, missingFields: [] }
          };
        }

        matchTaskFlows.value[match_id].directory = {
          status,
          exists,
          path
        };

        currentProcessingMatchId.value = match_id;
      } catch (e) {
        console.error('目录状态处理失败:', e);
      }
    });

    // 监听任务流程事件 - 文件状态
    eventSource.addEventListener('okooo_task_files_status', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log('收到文件状态:', data);

        const { match_id, files, completed_count, total_count } = data;

        if (!matchTaskFlows.value[match_id]) {
          matchTaskFlows.value[match_id] = {
            matchId: match_id,
            date: data.date,
            directory: { status: 'pending', exists: false, path: '' },
            files: { items: {}, completedCount: 0, totalCount: 8 },
            parse: { status: 'pending', outputPath: '', isComplete: false, missingFields: [] }
          };
        }

        matchTaskFlows.value[match_id].files = {
          items: files,
          completedCount: completed_count,
          totalCount: total_count
        };

        currentProcessingMatchId.value = match_id;
      } catch (e) {
        console.error('文件状态处理失败:', e);
      }
    });

    // 监听任务流程事件 - 解析开始
    eventSource.addEventListener('okooo_task_parse_start', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log('收到解析开始:', data);

        const { match_id, status } = data;

        if (matchTaskFlows.value[match_id]) {
          matchTaskFlows.value[match_id].parse.status = status;
        }

        currentProcessingMatchId.value = match_id;
      } catch (e) {
        console.error('解析开始处理失败:', e);
      }
    });

    // 监听任务流程事件 - 解析完成
    eventSource.addEventListener('okooo_task_parse_complete', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log('收到解析完成:', data);

        const { match_id, status, output_path, is_complete, missing_fields } = data;

        if (matchTaskFlows.value[match_id]) {
          matchTaskFlows.value[match_id].parse = {
            status,
            outputPath: output_path,
            isComplete: is_complete,
            missingFields: missing_fields || []
          };
        }

        currentProcessingMatchId.value = match_id;
      } catch (e) {
        console.error('解析完成处理失败:', e);
      }
    });

    // 监听任务流程事件 - 解析错误
    eventSource.addEventListener('okooo_task_parse_error', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log('收到解析错误:', data);

        const { match_id, error, status } = data;

        if (matchTaskFlows.value[match_id]) {
          matchTaskFlows.value[match_id].parse.status = status;
        }

        currentProcessingMatchId.value = match_id;
      } catch (e) {
        console.error('解析错误处理失败:', e);
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

const serverConfirmedProgress = ref<Record<string, { current: number, total: number, status: string }>>({});

// 计算属性：聚合后的比赛进度
const aggregatedResults = computed(() => {
  const map: Record<string, { matchId: string, current: number, total: number, status: string }> = {};
  
  // 1. 初始化所有任务中的比赛ID
  if (okoooState.value.crawler.results) {
    okoooState.value.crawler.results.forEach(task => {
      if (!map[task.matchId]) {
        map[task.matchId] = {
          matchId: task.matchId,
          current: 0,
          total: 0,
          status: 'pending'
        };
      }
      map[task.matchId].total++;
      // 本地状态更新（如果不用SSE也可以用这个）
      // if (task.status === 'success') map[task.matchId].current++;
    });
  }
  
  // 2. 使用服务端SSE确认的进度覆盖
  Object.keys(serverConfirmedProgress.value).forEach(matchId => {
    if (map[matchId]) {
      map[matchId].current = serverConfirmedProgress.value[matchId].current;
      // 检查是否完成
      if (map[matchId].current >= map[matchId].total && map[matchId].total > 0) {
        map[matchId].status = 'success';
      }
    } else {
        // 如果任务列表里没有（可能是历史遗留），也加上
        map[matchId] = {
            matchId: matchId,
            current: serverConfirmedProgress.value[matchId].current,
            total: serverConfirmedProgress.value[matchId].total,
            status: serverConfirmedProgress.value[matchId].status
        };
    }
  });

  return Object.values(map);
});

// 计算属性：统一的修复任务列表（合并异常列表和爬取进度）
const unifiedRepairList = computed(() => {
  const map = new Map<string, { 
    id: string; 
    reason: string; 
    current: number; 
    total: number; 
    status: string 
  }>();

  // 1. 先添加异常列表中的任务
  okoooState.value.repair.repairDetails.forEach(item => {
    map.set(item.id, {
      id: item.id,
      reason: item.reason,
      current: 0,
      total: 8, // 默认为8，后续会更新
      status: 'pending'
    });
  });

  // 2. 合并爬取进度
  aggregatedResults.value.forEach(res => {
    if (map.has(res.matchId)) {
      const item = map.get(res.matchId)!;
      item.current = res.current;
      item.total = res.total;
      item.status = res.status;
    } else {
      // 如果任务不在异常列表中（可能是手动添加的任务），也加入列表
      map.set(res.matchId, {
        id: res.matchId,
        reason: '手动任务',
        current: res.current,
        total: res.total,
        status: res.status
      });
    }
  });

  return Array.from(map.values());
});

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
    templateFields.value = testRulesData.parsingRules.map((rule: any) => ({
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
      function extractAllOdds(html: string) {
        const allOdds: { value: number; source: string; match: string }[] = [];
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
    
  } catch (error: any) {
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
    
    return !!(newCode && firstCode && newCode === firstCode);
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
  } catch (error: any) {
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
    
  } catch (error: any) {
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
    
  } catch (error: any) {
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
  } catch (e: any) {
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
    
  } catch (error: any) {
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
    
    const response = await new Promise<any>((resolve, reject) => {
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
    
  } catch (error: any) {
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

  okoooState.value.crawler.isRunning = true;
  okoooState.value.crawler.phase = 'matches';

  try {
    const response = await chrome.runtime.sendMessage({
      type: 'OKOOO_START_CRAWLER'
    });

    if (response.success) {
      okoooState.value.crawler.totalMatches = response.total;
      okoooState.value.crawler.currentMatchIndex = 0;
      okoooState.value.crawler.successCount = 0;
      okoooState.value.crawler.errorCount = 0;
      okoooState.value.crawler.results = [];
      startCrawlerStatusPolling();
    } else {
      okoooState.value.crawler.isRunning = false;
      alert('启动失败: ' + response.message);
    }
  } catch (error: any) {
    okoooState.value.crawler.isRunning = false;
    console.error('启动爬虫失败:', error);
  }
};

const stopOkoooCrawler = async () => {
  try {
    await chrome.runtime.sendMessage({
      type: 'OKOOO_STOP_CRAWLER'
    });
  } catch (e) {
    console.log('Stop crawler message failed:', e);
  }

  okoooState.value.crawler.isRunning = false;
  okoooState.value.crawler.phase = 'idle';
  okoooState.value.repair.isRunning = false; // 同时重置修复状态
  stopCrawlerStatusPolling();
};

const startCrawlerStatusPolling = () => {
  crawlerStatusTimer = window.setInterval(async () => {
    const response = await chrome.runtime.sendMessage({
      type: 'OKOOO_GET_STATUS'
    });

    if (response.success) {
      const data = response.data;
      okoooState.value.crawler.isRunning = data.isRunning;
      okoooState.value.crawler.phase = data.phase;
      okoooState.value.crawler.totalMatches = data.totalMatches;
      okoooState.value.crawler.currentMatchIndex = data.currentMatchIndex;
      okoooState.value.crawler.totalHistory = data.totalHistory;
      okoooState.value.crawler.currentHistoryIndex = data.currentHistoryIndex;
      okoooState.value.crawler.successCount = data.successCount;
      okoooState.value.crawler.errorCount = data.errorCount;
      okoooState.value.crawler.results = data.results || [];

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

// ==================== 步骤化工作流处理函数 ====================

// 步骤1: 抓取比赛列表
const startStep1CaptureList = async () => {
  try {
    workflowState.value.step1_captureList.status = 'running';
    workflowState.value.step1_captureList.message = '正在抓取比赛列表...';

    console.log('[步骤1] 开始抓取比赛列表...');

    // 调用后端API获取比赛列表
    const date = new Date().toISOString().split('T')[0];
    const response = await fetch(`${backendUrl}/api/v1/okooo/matches?date=${date}`);
    const result = await response.json();

    console.log('[步骤1] 比赛列表API响应:', result);

    if (result.success && result.data) {
      // 提取比赛ID列表
      const matches = result.data || [];
      const matchIds = matches.map((m: any) => m.match_id || m.id).filter(Boolean);

      workflowState.value.step1_captureList.matchIds = matchIds;
      workflowState.value.step1_captureList.status = 'completed';
      workflowState.value.step1_captureList.message = `抓取完成，共 ${matchIds.length} 个比赛`;

      // 同步更新原有的修复列表状态
      okoooState.value.repair.ids = matchIds;
      okoooState.value.repair.totalChecked = matchIds.length;

      okoooLogs.value.unshift({
        message: `✅ 步骤1完成: 获取到 ${matchIds.length} 个比赛`,
        level: 'success',
        timestamp: new Date().toLocaleTimeString()
      });
    } else {
      throw new Error(result.message || '获取比赛列表失败');
    }
  } catch (error) {
    console.error('[步骤1] 抓取失败:', error);
    workflowState.value.step1_captureList.status = 'error';
    workflowState.value.step1_captureList.message = '抓取失败: ' + (error as Error).message;

    okoooLogs.value.unshift({
      message: `❌ 步骤1失败: ${(error as Error).message}`,
      level: 'error',
      timestamp: new Date().toLocaleTimeString()
    });
  }
};

// 步骤2: 筛选新比赛
const startStep2FilterMatches = async () => {
  try {
    workflowState.value.step2_filterMatches.status = 'running';
    workflowState.value.step2_filterMatches.message = '正在筛选新比赛...';

    const date = new Date().toISOString().split('T')[0];
    const matchIds = workflowState.value.step1_captureList.matchIds;

    const response = await fetch(`${backendUrl}/api/v1/okooo/filter-new-matches`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date, match_ids: matchIds, check_days: 7 })
    });

    const result = await response.json();

    if (result.success) {
      workflowState.value.step2_filterMatches.newMatches = result.data.new_matches || [];
      workflowState.value.step2_filterMatches.existingMatches = result.data.existing_matches || [];
      workflowState.value.step2_filterMatches.status = 'completed';
      workflowState.value.step2_filterMatches.message = `筛选完成: 新比赛 ${result.data.new_count} 个，已存在 ${result.data.existing_count} 个`;

      okoooLogs.value.unshift({
        message: `✅ 步骤2完成: 新比赛 ${result.data.new_count} 个，已存在 ${result.data.existing_count} 个`,
        level: 'success',
        timestamp: new Date().toLocaleTimeString()
      });
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    workflowState.value.step2_filterMatches.status = 'error';
    workflowState.value.step2_filterMatches.message = '筛选失败: ' + (error as Error).message;

    okoooLogs.value.unshift({
      message: `❌ 步骤2失败: ${(error as Error).message}`,
      level: 'error',
      timestamp: new Date().toLocaleTimeString()
    });
  }
};

// 步骤3: 下载比赛数据
const startStep3DownloadData = async () => {
  try {
    workflowState.value.step3_downloadData.status = 'running';
    workflowState.value.step3_downloadData.message = '正在下载比赛数据...';

    const newMatches = workflowState.value.step2_filterMatches.newMatches;
    const date = new Date().toISOString().split('T')[0];

    console.log('[步骤3] 开始下载比赛数据:', newMatches);

    // 构建任务列表（8个页面类型）
    const pageTypes = [
      { type: '历史', prefix: 'history' },
      { type: '欧赔', prefix: 'odds' },
      { type: '亚盘', prefix: 'handicap' },
      { type: '盈亏', prefix: 'exchanges' },
      { type: '阵容', prefix: 'form' },
      { type: '积分', prefix: 'game' },
      { type: '澳门变化', prefix: 'macao_change' },
      { type: '必发变化', prefix: 'bifa_change' }
    ];

    const tasks = newMatches.flatMap((matchId: string) =>
      pageTypes.map(pt => ({
        match_id: matchId,
        page_type: pt.type,
        filename_prefix: pt.prefix,
        url: `https://m.okooo.com/match/${pt.prefix}.php?MatchID=${matchId}`,
        date: date
      }))
    );

    console.log('[步骤3] 生成任务数:', tasks.length);

    // 发送消息到background脚本
    const response = await chrome.runtime.sendMessage({
      type: 'OKOOO_START_REPAIR_TASKS',
      tasks: tasks
    });

    console.log('[步骤3] 下载响应:', response);

    if (response && response.success) {
      workflowState.value.step3_downloadData.totalTasks = tasks.length;

      // 启动状态轮询
      startWorkflowStep3Polling();

      okoooLogs.value.unshift({
        message: `🚀 步骤3开始: 下载 ${newMatches.length} 个新比赛的 ${tasks.length} 个页面`,
        level: 'info',
        timestamp: new Date().toLocaleTimeString()
      });
    } else {
      throw new Error(response?.message || '下载启动失败');
    }
  } catch (error) {
    console.error('[步骤3] 下载失败:', error);
    workflowState.value.step3_downloadData.status = 'error';
    workflowState.value.step3_downloadData.message = '下载失败: ' + (error as Error).message;

    okoooLogs.value.unshift({
      message: `❌ 步骤3失败: ${(error as Error).message}`,
      level: 'error',
      timestamp: new Date().toLocaleTimeString()
    });
  }
};

let workflowStep3Timer: number | null = null;

const startWorkflowStep3Polling = () => {
  workflowStep3Timer = window.setInterval(async () => {
    const response = await chrome.runtime.sendMessage({
      type: 'OKOOO_GET_STATUS'
    });

    if (response.success) {
      const data = response.data;

      // 更新插件状态
      pluginStatus.value.isRunning = data.isRunning;
      pluginStatus.value.currentTask = data.currentTask;
      pluginStatus.value.phase = data.phase;

      // 更新步骤3状态
      workflowState.value.step3_downloadData.completedTasks = data.completedTasks || 0;
      workflowState.value.step3_downloadData.skippedTasks = data.skippedTasks || 0;
      workflowState.value.step3_downloadData.errorTasks = data.errorTasks || 0;

      if (!data.isRunning) {
        // 下载完成
        clearInterval(workflowStep3Timer!);
        workflowStep3Timer = null;

        workflowState.value.step3_downloadData.status = 'completed';
        workflowState.value.step3_downloadData.message = `下载完成: ${workflowState.value.step3_downloadData.completedTasks} 成功, ${workflowState.value.step3_downloadData.skippedTasks} 跳过, ${workflowState.value.step3_downloadData.errorTasks} 失败`;

        okoooLogs.value.unshift({
          message: `✅ 步骤3完成: ${workflowState.value.step3_downloadData.completedTasks} 成功, ${workflowState.value.step3_downloadData.skippedTasks} 跳过`,
          level: 'success',
          timestamp: new Date().toLocaleTimeString()
        });
      }
    }
  }, 1000);
};

// 步骤4: 解析比赛数据
const startStep4ParseData = async () => {
  try {
    workflowState.value.step4_parseData.status = 'running';
    workflowState.value.step4_parseData.message = '正在解析比赛数据...';

    const date = new Date().toISOString().split('T')[0];

    // 调用后端API解析所有比赛
    const response = await fetch(`${backendUrl}/api/v1/okooo/parse/daily`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date, background: true })
    });

    const result = await response.json();

    if (result.success) {
      workflowState.value.step4_parseData.totalMatches = workflowState.value.step1_captureList.matchIds.length;

      // 监听SSE事件获取解析进度
      setupParseProgressListener();

      okoooLogs.value.unshift({
        message: `🚀 步骤4开始: 解析 ${workflowState.value.step4_parseData.totalMatches} 个比赛`,
        level: 'info',
        timestamp: new Date().toLocaleTimeString()
      });
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    workflowState.value.step4_parseData.status = 'error';
    workflowState.value.step4_parseData.message = '解析失败: ' + (error as Error).message;

    okoooLogs.value.unshift({
      message: `❌ 步骤4失败: ${(error as Error).message}`,
      level: 'error',
      timestamp: new Date().toLocaleTimeString()
    });
  }
};

// 监听解析进度
const setupParseProgressListener = () => {
  // 使用现有的SSE连接监听解析事件
  const handleParseProgress = (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data);

      if (data.type === 'okooo_parse_complete') {
        workflowState.value.step4_parseData.parsedMatches++;

        if (workflowState.value.step4_parseData.parsedMatches >= workflowState.value.step4_parseData.totalMatches) {
          workflowState.value.step4_parseData.status = 'completed';
          workflowState.value.step4_parseData.message = `解析完成: ${workflowState.value.step4_parseData.parsedMatches} 成功`;

          okoooLogs.value.unshift({
            message: `✅ 步骤4完成: 解析了 ${workflowState.value.step4_parseData.parsedMatches} 个比赛`,
            level: 'success',
            timestamp: new Date().toLocaleTimeString()
          });
        }
      }
    } catch (e) {
      console.error('解析进度监听错误:', e);
    }
  };

  // 注册到现有的SSE事件监听
  if (eventSource) {
    eventSource.addEventListener('okooo_parse_complete', handleParseProgress);
  }
};

/*
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
*/


// 打开并捕获比赛列表
const openAndCaptureList = async () => {
      okoooState.value.list.isCapturing = true;
      okoooState.value.list.lastResult = null;
      okoooState.value.list.progress = '0/3';

      // 动态获取入口配置
      let captureSteps: {name: string, url: string}[] = [];
      
      try {
        okoooState.value.list.progress = '获取配置...';
        const entryRes = await fetch(`${backendUrl.value}/api/v1/okooo/entry-points`);
        const entryData = await entryRes.json();
        if (entryData.success && Array.isArray(entryData.data) && entryData.data.length > 0) {
            captureSteps = entryData.data;
        } else {
            // Fallback
            captureSteps = [
                { name: '竞彩足球', url: 'https://m.okooo.com/jczq/' }
            ];
        }
      } catch (e) {
         console.error('获取入口失败，使用默认配置', e);
         captureSteps = [
            { name: '竞彩足球', url: 'https://m.okooo.com/jczq/' }
         ];
      }

      try {
        let successCount = 0;
        let totalSize = 0;

        for (let i = 0; i < captureSteps.length; i++) {
          const step = captureSteps[i];
          okoooState.value.list.progress = `${i + 1}/${captureSteps.length}`;
          okoooState.value.list.lastResult = {
            success: true,
            message: `正在捕获 ${step.name}...`
          };

          const response = await chrome.runtime.sendMessage({
            type: 'OKOOO_OPEN_LIST',
            url: step.url
          });

          if (response.success) {
            successCount++;
            totalSize += response.size || 0;
            // 每次成功后等待一小段时间，避免操作过快
            if (i < captureSteps.length - 1) {
              await new Promise(resolve => setTimeout(resolve, 2000));
            }
          } else {
            console.error(`捕获 ${step.name} 失败:`, response.message);
            throw new Error(`捕获 ${step.name} 失败: ${response.message}`);
          }
        }

        okoooState.value.list.isCapturing = false;
        okoooState.value.list.lastResult = {
          success: true,
          message: `成功捕获所有 ${successCount} 个列表，开始质检...`,
          size: totalSize
        };
        
        // 自动触发数据完整性检查 (Dry Run)
        await startRepair(true);
      } catch (error) {
        okoooState.value.list.isCapturing = false;
        okoooState.value.list.lastResult = {
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

const showCaptchaAlert = ref(false);

onMounted(async () => {
  // 监听来自 background 的消息
  chrome.runtime.onMessage.addListener((message) => {
    if (message.type === 'OKOOO_CAPTCHA_DETECTED') {
      showCaptchaAlert.value = true;
    } else if (message.type === 'OKOOO_CAPTCHA_SOLVED') {
      showCaptchaAlert.value = false;
    } else if (message.type === 'OKOOO_MATCH_PARSED') {
      // 单个比赛解析完成
      const { matchId, date, data } = message.data;
      console.log('收到比赛解析完成通知:', matchId);

      // 添加到解析结果列表
      const result: ParseResult = {
        matchId: matchId,
        date: date,
        isComplete: true,
        missingFields: [],
        outputPath: data?.output_path || '',
        timestamp: new Date().toLocaleTimeString()
      };

      // 更新或添加解析结果
      const existingIndex = parseResults.value.findIndex(r => r.matchId === result.matchId);
      if (existingIndex >= 0) {
        parseResults.value[existingIndex] = result;
      } else {
        parseResults.value.push(result);
      }

      // 更新待修复列表中的状态
      const repairItem = okoooState.value.repair.repairDetails.find((item: any) => item.id === matchId);
      if (repairItem) {
        repairItem.status = 'success';
        repairItem.current = repairItem.total;
      }

      // 显示日志
      okoooLogs.value.unshift({
        message: `✅ 比赛 ${matchId} 解析完成`,
        level: 'success',
        timestamp: new Date().toLocaleTimeString()
      });
    } else if (message.type === 'OKOOO_MATCH_PARSE_ERROR') {
      // 单个比赛解析失败
      const { matchId, error } = message.data;
      console.error('收到比赛解析失败通知:', matchId, error);

      // 添加到解析错误列表
      parseErrors.value.push({
        matchId: matchId,
        date: message.data.date,
        error: error,
        timestamp: new Date().toLocaleTimeString()
      });

      // 显示日志
      okoooLogs.value.unshift({
        message: `❌ 比赛 ${matchId} 解析失败: ${error}`,
        level: 'error',
        timestamp: new Date().toLocaleTimeString()
      });
    } else if (message.type === 'OKOOO_CRAWLER_COMPLETED') {
      // 爬虫完成，清空所有相关状态
      console.log('收到爬虫完成通知:', message.data);
      
      // 清空待修复列表
      okoooState.value.repair.repairDetails = [];
      okoooState.value.repair.repairingCount = 0;
      okoooState.value.repair.ids = [];
      
      // 清空爬虫状态
      okoooState.value.crawler.isRunning = false;
      okoooState.value.crawler.phase = 'completed';
      okoooState.value.crawler.currentMatchIndex = 0;
      okoooState.value.crawler.totalMatches = 0;
      okoooState.value.crawler.results = [];
      
      // 清空进度缓存
      serverConfirmedProgress.value = {};
      
      // 显示完成提示
      okoooLogs.value.unshift({
        message: `✅ ${message.data.message} (成功: ${message.data.successCount}, 失败: ${message.data.errorCount})`,
        level: 'success',
        timestamp: new Date().toLocaleTimeString()
      });
      
      // 延迟后自动刷新状态并重新检查物理文件
      setTimeout(async () => {
        await refreshOkoooStatus();
        
        // 自动触发完整性检查（验证物理文件）
        okoooLogs.value.unshift({
          message: '🔍 正在验证物理文件完整性...',
          level: 'info',
          timestamp: new Date().toLocaleTimeString()
        });
        
        // 执行完整性检查
        await startRepair(true);
        
        // 如果还有失败的任务，显示提示
        if (okoooState.value.repair.repairDetails.length > 0) {
          okoooLogs.value.unshift({
            message: `⚠️ 发现 ${okoooState.value.repair.repairDetails.length} 个任务需要重新修复`,
            level: 'warning',
            timestamp: new Date().toLocaleTimeString()
          });
        } else {
          okoooLogs.value.unshift({
            message: '✅ 所有物理文件验证通过，数据一致性确认',
            level: 'success',
            timestamp: new Date().toLocaleTimeString()
          });
        }
      }, 2000);
    }
  });

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
    okoooState.value.crawler = {
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
  // stopHandicapStatusPolling();
  if (eventSource) {
    eventSource.close();
    isLogStreamActive.value = false;
  }
  // 断开WebSocket连接
  disconnectWebSocket();
});

// ==================== 新版MCP与Skill集成测试方法 ====================

// 平台选择
const selectPlatform = (platform: 'kimi' | 'deepseek') => {
  selectedPlatform.value = platform;
  skillResult.value = null;
  skillError.value = '';
};

// 图片上传处理
const triggerImageSelect = () => {
  imageInput.value?.click();
};

const handleImageSelect = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files[0]) {
    const file = input.files[0];
    const reader = new FileReader();
    reader.onload = (e) => {
      uploadedImage.value = e.target?.result as string;
    };
    reader.readAsDataURL(file);
  }
};

const handleImageDrop = (event: DragEvent) => {
  isDragging.value = false;
  const files = event.dataTransfer?.files;
  if (files && files[0]) {
    const file = files[0];
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        uploadedImage.value = e.target?.result as string;
      };
      reader.readAsDataURL(file);
    }
  }
};

const removeImage = () => {
  uploadedImage.value = '';
  if (imageInput.value) {
    imageInput.value.value = '';
  }
};

// WebSocket连接管理
const connectWebSocket = () => {
  try {
    wsConnection.value = new WebSocket(WS_SERVER_URL);
    
    wsConnection.value.onopen = () => {
      wsStatus.value = { connected: true, text: 'WebSocket已连接' };
      console.log('WebSocket连接成功');
    };
    
    wsConnection.value.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };
    
    wsConnection.value.onerror = (error) => {
      console.error('WebSocket错误:', error);
      wsStatus.value = { connected: false, text: 'WebSocket错误' };
    };
    
    wsConnection.value.onclose = () => {
      wsStatus.value = { connected: false, text: 'WebSocket已断开' };
      console.log('WebSocket连接关闭');
    };
  } catch (error) {
    console.error('WebSocket连接失败:', error);
    wsStatus.value = { connected: false, text: '连接失败' };
  }
};

const disconnectWebSocket = () => {
  wsConnection.value?.close();
  wsConnection.value = null;
  wsStatus.value = { connected: false, text: 'WebSocket未连接' };
};

const handleWebSocketMessage = (data: any) => {
  if (data.type === 'skill_response') {
    skillResult.value = data;
    skillLoading.value = false;
  } else if (data.type === 'skill_stream') {
    streamChunks.value.push(data.chunk);
    if (data.is_complete) {
      isStreaming.value = false;
    }
  }
};

// Skill执行
const testSkill = async (skillName: string) => {
  skillLoading.value = true;
  skillError.value = '';
  skillResult.value = null;
  streamChunks.value = [];
  
  try {
    let params: any = {};
    
    switch (skillName) {
      case 'kimi_chat':
      case 'deepseek_chat':
        params = {
          message: messageText.value || '你好',
          image: uploadedImage.value || undefined,
          new_chat: false
        };
        break;
      case 'upload_image':
        params = {
          platform: selectedPlatform.value,
          image_data: uploadedImage.value
        };
        break;
      case 'analyze_image':
        params = {
          image_data: uploadedImage.value,
          mode: 'ocr'
        };
        break;
      case 'get_chat_history':
        params = {
          platform: selectedPlatform.value
        };
        break;
      case 'get_prompt':
        params = {
          name: 'default'
        };
        break;
    }
    
    // 通过Chrome Runtime发送消息到Background Script
    const response = await chrome.runtime.sendMessage({
      type: 'EXECUTE_SKILL',
      skill: skillName,
      params
    });
    
    if (response.success) {
      skillResult.value = {
        success: true,
        data: response.data,
        timestamp: new Date().toISOString()
      };
    } else {
      throw new Error(response.error);
    }
  } catch (error) {
    skillError.value = error instanceof Error ? error.message : String(error);
    skillResult.value = {
      success: false,
      error: skillError.value,
      timestamp: new Date().toISOString()
    };
  } finally {
    skillLoading.value = false;
  }
};

// 发送消息
const sendMessage = async () => {
  if (!messageText.value.trim()) return;
  
  const skillName = selectedPlatform.value === 'kimi' ? 'kimi_chat' : 'deepseek_chat';
  await testSkill(skillName);
};

// 新建对话
const newChat = async () => {
  skillLoading.value = true;
  skillError.value = '';
  
  try {
    const response = await chrome.runtime.sendMessage({
      type: 'EXECUTE_SKILL',
      skill: 'new_chat',
      params: {
        platform: selectedPlatform.value
      }
    });
    
    if (response.success) {
      skillResult.value = {
        success: true,
        data: { message: '新对话已创建' },
        timestamp: new Date().toISOString()
      };
      messageText.value = '';
      uploadedImage.value = '';
    } else {
      throw new Error(response.error);
    }
  } catch (error) {
    skillError.value = error instanceof Error ? error.message : String(error);
  } finally {
    skillLoading.value = false;
  }
};

// DeepSeek专项测试
const openDeepSeek = async () => {
  try {
    const tab = await chrome.tabs.create({
      url: 'https://chat.deepseek.com/',
      active: true
    });
    deepseekStatus.value = { ready: true, tabId: tab.id || null };
  } catch (error) {
    skillError.value = '打开DeepSeek失败: ' + (error instanceof Error ? error.message : String(error));
  }
};

const checkDeepSeekReady = async () => {
  try {
    const tabs = await chrome.tabs.query({ url: 'https://chat.deepseek.com/*' });
    if (tabs.length > 0 && tabs[0].id) {
      const response = await chrome.tabs.sendMessage(tabs[0].id, {
        action: 'is_ready'
      });
      deepseekStatus.value = { 
        ready: response.ready, 
        tabId: tabs[0].id 
      };
      skillResult.value = {
        success: true,
        data: { ready: response.ready, tabId: tabs[0].id },
        timestamp: new Date().toISOString()
      };
    } else {
      skillResult.value = {
        success: false,
        error: 'DeepSeek页面未打开',
        timestamp: new Date().toISOString()
      };
    }
  } catch (error) {
    skillError.value = '检查失败: ' + (error instanceof Error ? error.message : String(error));
  }
};

const testDeepSeekWithImage = async () => {
  if (!uploadedImage.value) {
    skillError.value = '请先上传图片';
    return;
  }
  
  skillLoading.value = true;
  skillError.value = '';
  
  try {
    const response = await chrome.runtime.sendMessage({
      type: 'EXECUTE_SKILL',
      skill: 'deepseek_chat',
      params: {
        message: messageText.value || '分析这张图片',
        image: uploadedImage.value,
        new_chat: false
      }
    });
    
    if (response.success) {
      skillResult.value = {
        success: true,
        data: response.data,
        timestamp: new Date().toISOString()
      };
    } else {
      throw new Error(response.error);
    }
  } catch (error) {
    skillError.value = error instanceof Error ? error.message : String(error);
  } finally {
    skillLoading.value = false;
  }
};

// 检查后端状态
const checkBackendStatus = async () => {
  try {
    const response = await fetch(`${backendStatus.value.url}/api/health`);
    backendStatus.value.connected = response.ok;
    skillResult.value = {
      success: response.ok,
      data: { backend: 'available', status: response.status },
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    backendStatus.value.connected = false;
    skillResult.value = {
      success: false,
      error: '后端服务不可用',
      timestamp: new Date().toISOString()
    };
  }
};

// 格式化时间
const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString();
};

// 监听平台标签页变化
const checkPlatformTabs = async () => {
  const kimiTabs = await chrome.tabs.query({ url: 'https://www.kimi.com/*' });
  kimiStatus.value = { 
    ready: kimiTabs.length > 0, 
    tabId: kimiTabs[0]?.id || null 
  };
  
  const deepseekTabs = await chrome.tabs.query({ url: 'https://chat.deepseek.com/*' });
  deepseekStatus.value = { 
    ready: deepseekTabs.length > 0, 
    tabId: deepseekTabs[0]?.id || null 
  };
};

// 定期检查平台标签页
setInterval(checkPlatformTabs, 5000);
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
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.captcha-overlay {
  background: rgba(0, 0, 0, 0.85);
  z-index: 2000;
}

.notification-overlay {
  z-index: 1500;
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

.captcha-content {
  border: 2px solid #ff4d4f;
  animation: pulse 2s infinite;
  max-width: 600px;
}

.notification-content {
  max-width: 600px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
}

.warning-header h3 {
  color: #ff4d4f;
}

.info-header h3 {
  color: #1890ff;
}

.captcha-message {
  font-size: 16px;
  font-weight: bold;
  color: #ff4d4f;
  text-align: center;
  margin-bottom: 20px;
}

.captcha-tips {
  background: rgba(255, 77, 79, 0.1);
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.captcha-tips p {
  margin: 5px 0;
  color: var(--text-primary);
}

.captcha-actions {
  display: flex;
  justify-content: center;
}

.notification-info {
  padding: 10px;
  background: var(--bg-tertiary);
  border-radius: 6px;
  margin-bottom: 20px;
}

.notification-info p {
  margin: 8px 0;
  color: var(--text-primary);
}

.notification-message {
  margin-top: 15px !important;
  font-weight: bold;
  color: #1890ff;
  border-top: 1px solid var(--border-color);
  padding-top: 10px;
}

.notification-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  justify-content: center;
}

.notification-actions .ths-btn {
  min-width: 100px;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(255, 77, 79, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(255, 77, 79, 0); }
  100% { box-shadow: 0 0 0 0 rgba(255, 77, 79, 0); }
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

/* 解析结果样式 */
.parse-results-section {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
}

.parse-progress {
  margin-bottom: var(--spacing-md);
}

.parse-progress .progress-fill.parse {
  background: linear-gradient(90deg, #8b5cf6, #a78bfa);
}

.parse-summary {
  margin-bottom: var(--spacing-md);
}

.summary-card {
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.summary-card.has-warning {
  border-color: #f59e0b;
  background: #fffbeb;
}

.summary-card.has-error {
  border-color: #ef4444;
  background: #fef2f2;
}

.summary-title {
  font-weight: 600;
  margin-bottom: var(--spacing-sm);
  color: var(--text-primary);
}

.summary-stats {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
}

.summary-stats .stat {
  font-size: 14px;
  font-weight: 600;
}

.summary-stats .stat.success {
  color: #16a34a;
}

.summary-stats .stat.warning {
  color: #d97706;
}

.summary-stats .stat.error {
  color: #dc2626;
}

.summary-message {
  font-size: 12px;
  color: var(--text-secondary);
}

.parse-errors,
.parse-warnings,
.parse-complete-list {
  margin-top: var(--spacing-md);
}

.subsection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.subsection-header h5 {
  margin: 0;
  font-size: 14px;
  color: var(--text-primary);
}

.error-list,
.warning-list,
.result-list {
  max-height: 200px;
  overflow-y: auto;
}

.error-item,
.warning-item,
.result-item {
  padding: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
  border-radius: var(--radius-sm);
  font-size: 12px;
}

.error-item {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

.warning-item {
  background: #fffbeb;
  border: 1px solid #fcd34d;
  color: #92400e;
}

.result-item {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}

/* 任务流程样式 */
.task-flow-section {
  margin-top: var(--spacing-md);
  border-top: 1px solid var(--border-color);
  padding-top: var(--spacing-md);
}

.task-flow-list {
  max-height: 600px;
  overflow-y: auto;
}

.task-flow-item {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  transition: all 0.3s ease;
}

.task-flow-item.active {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2); }
  50% { box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.3); }
}

.task-flow-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--border-light);
}

.task-flow-header .match-id {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}

.processing-badge {
  font-size: 11px;
  padding: 2px 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  animation: blink 1.5s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.task-step {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs) 0;
  font-size: 13px;
}

.step-icon {
  font-size: 16px;
  width: 24px;
  text-align: center;
}

.step-icon.completed {
  color: #16a34a;
}

.step-icon.processing {
  color: #3b82f6;
}

.step-icon.error {
  color: #ef4444;
}

.step-icon.warning {
  color: #f59e0b;
}

.step-name {
  flex: 1;
  color: var(--text-secondary);
}

.step-name.completed {
  color: #16a34a;
  font-weight: 500;
}

.step-name.processing {
  color: #3b82f6;
  font-weight: 500;
}

.step-name.error {
  color: #ef4444;
}

.step-name.warning {
  color: #f59e0b;
}

.step-status {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
}

.step-status.success {
  background: #dcfce7;
  color: #166534;
}

.step-status.warning {
  background: #fef3c7;
  color: #92400e;
}

/* 文件列表 */
.file-list {
  margin-left: 32px;
  margin-top: var(--spacing-xs);
  margin-bottom: var(--spacing-xs);
  padding: var(--spacing-sm);
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
}

.file-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 4px 0;
  font-size: 12px;
}

.file-status-icon {
  font-size: 10px;
  width: 16px;
  text-align: center;
}

.file-name {
  flex: 1;
  color: var(--text-secondary);
}

.file-name.completed {
  color: #16a34a;
  font-weight: 500;
}

.file-name.missing {
  color: #9ca3af;
}

.file-filename {
  color: var(--text-tertiary);
  font-family: monospace;
  font-size: 11px;
}

/* 查看数据按钮 */
.task-flow-actions {
  margin-top: var(--spacing-sm);
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--border-light);
  display: flex;
  justify-content: flex-end;
}

.view-data-btn-small {
  padding: 4px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}

.view-data-btn-small:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
}

.result-item.incomplete {
  background: #fffbeb;
  border-color: #fcd34d;
  color: #92400e;
}

.result-header,
.warning-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xs);
}

.match-id {
  font-weight: 600;
  font-family: monospace;
}

.result-status {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-weight: 500;
}

.result-status.complete {
  background: #16a34a;
  color: white;
}

.result-status.incomplete {
  background: #d97706;
  color: white;
}

.missing-fields {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: var(--spacing-xs);
}

.error-msg {
  color: #dc2626;
}

.warning-time {
  font-size: 11px;
  color: var(--text-tertiary);
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
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

/* Repair Section Styles */
.repair-details-section {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.repair-details-section .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.repair-details-section h4 {
  margin: 0;
  color: #d97706; /* Warning color */
}

.repair-list {
  max-height: 200px;
  overflow-y: auto;
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
}

.repair-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--border-light);
  font-size: 12px;
}

.repair-item:last-child {
  border-bottom: none;
}

.repair-item-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.repair-item-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.match-id {
  font-family: monospace;
  font-weight: 500;
}

.error-reason {
  color: #ef4444;
}

/* 查看数据按钮 */
.view-data-btn {
  padding: 4px 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}

.view-data-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
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

/* ==================== 步骤化工作流样式 ==================== */

.workflow-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.workflow-step {
  background: var(--bg-primary);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  transition: all 0.3s ease;
}

.workflow-step:last-child {
  margin-bottom: 0;
}

.workflow-step.running {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.workflow-step.completed {
  border-color: #10b981;
}

.workflow-step.error {
  border-color: #ef4444;
}

.step-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.step-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.step-title {
  flex: 1;
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}

.step-status {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 12px;
  font-weight: 500;
}

.step-status.idle {
  background: #f3f4f6;
  color: #6b7280;
}

.step-status.running {
  background: #dbeafe;
  color: #1d4ed8;
  animation: pulse 2s infinite;
}

.step-status.completed {
  background: #d1fae5;
  color: #065f46;
}

.step-status.error {
  background: #fee2e2;
  color: #991b1b;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.step-content {
  margin-left: 36px;
}

.step-result {
  margin-bottom: var(--spacing-sm);
  font-size: 13px;
  color: var(--text-secondary);
}

.step-result .stat {
  margin-right: var(--spacing-md);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.step-result .stat.new {
  background: #d1fae5;
  color: #065f46;
}

.step-result .stat.existing {
  background: #fef3c7;
  color: #92400e;
}

.step-btn {
  padding: 8px 16px;
  font-size: 13px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: var(--spacing-xs);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: var(--text-secondary);
}

.progress-text .skipped {
  color: #f59e0b;
  margin-left: var(--spacing-sm);
}

.captcha-notice {
  margin-top: var(--spacing-sm);
  font-size: 11px;
  color: #f59e0b;
  background: #fef3c7;
  padding: 4px 8px;
  border-radius: 4px;
}

/* 状态栏样式 */
.status-bar {
  display: flex;
  gap: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-md);
}

.status-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.status-item .label {
  font-size: 12px;
  color: var(--text-secondary);
}

.status-item .value {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}

.status-item .value.idle {
  background: #f3f4f6;
  color: #6b7280;
}

.status-item .value.running {
  background: #dbeafe;
  color: #1d4ed8;
}

/* 备用控制面板 */
.manual-controls-section {
  opacity: 0.8;
}

.manual-controls-section:hover {
  opacity: 1;
}

</style>
