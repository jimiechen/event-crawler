import { initNativeHostListener } from './native-host';
import {
  initSemanticSimilarityListener,
  initializeSemanticEngineIfCached,
} from './semantic-similarity';
import { initStorageManagerListener } from './storage-manager';
import { initThsPanelListener } from './thspanel-handler';
import { initSSEListener } from './sse-handler';
import { cleanupModelCache } from '@/utils/semantic-similarity-engine';
import { stateSyncService } from '@/utils/state-sync-service';

/**
 * Background script entry point
 * Initializes all background services and listeners
 */
export default defineBackground(() => {
  console.log('Hello from background script!');
  
  // 初始化状态同步服务
  initStateSyncService();
  
  // 初始化其他服务
  initNativeHostListener();
  initSemanticSimilarityListener();
  initStorageManagerListener();
  initThsPanelListener();
  initSSEListener(); // Start SSE Listener
  initializeSemanticEngineIfCached();
  
  // 定期清理过期状态
  setInterval(() => {
    stateSyncService.cleanupExpiredStates();
  }, 300000); // 每5分钟清理一次
});

/**
 * 初始化状态同步服务
 */
function initStateSyncService(): void {
  console.log('初始化状态同步服务...');
  
  // 添加状态变更监听器
  stateSyncService.addListener((notification) => {
    console.log('状态变更通知:', notification);
    
    // 广播状态变更到其他标签页
    stateSyncService.broadcastStateChange(notification);
  });
  
  // 监听扩展安装/启动事件
  chrome.runtime.onInstalled.addListener(() => {
    console.log('扩展已安装/更新，初始化状态同步服务');
  });
  
  // 监听扩展启动事件
  chrome.runtime.onStartup.addListener(() => {
    console.log('扩展已启动，初始化状态同步服务');
  });
  
  // 添加消息监听器处理状态同步相关请求
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'get_system_health') {
      const healthStatus = stateSyncService.getSystemHealthStatus();
      sendResponse({ success: true, data: healthStatus });
      return true;
    }
    
    if (message.type === 'get_aggregated_statistics') {
      const aggregatedStats = stateSyncService.getAggregatedStatistics();
      sendResponse({ success: true, data: aggregatedStats });
      return true;
    }
    
    if (message.type === 'get_all_tab_states') {
      const allStates = Array.from(stateSyncService.getAllTabStates().entries()).map(([tabId, state]) => ({
        tabId,
        ...state
      }));
      sendResponse({ success: true, data: allStates });
      return true;
    }
    
    if (message.type === 'get_active_monitoring_tabs') {
      const activeTabs = stateSyncService.getActiveMonitoringTabs();
      sendResponse({ success: true, data: activeTabs });
      return true;
    }
  });
  
  console.log('状态同步服务初始化完成');
}
