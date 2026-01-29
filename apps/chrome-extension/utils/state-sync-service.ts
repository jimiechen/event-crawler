/**
 * 状态同步服务
 * 在background script和content script之间同步监控状态
 */

import { 
  MonitoringStatus, 
  DataFetchStatus, 
  ErrorLevel,
  StateChangeEvent,
  MonitoringStatistics,
  CurrentRunState
} from './monitoring-state-manager';

// 同步状态数据结构
export interface SyncStateData {
  monitoringStatus: MonitoringStatus;
  currentRun: CurrentRunState | null;
  statistics: MonitoringStatistics;
  lastUpdate: number;
  tabId?: number;
  url?: string;
}

// 状态变更通知
export interface StateChangeNotification {
  type: 'monitoring' | 'dataFetch' | 'error' | 'statistics';
  tabId: number;
  timestamp: number;
  data: any;
}

/**
 * 状态同步服务类
 */
export class StateSyncService {
  private static instance: StateSyncService;
  private syncStates: Map<number, SyncStateData> = new Map(); // tabId -> state
  private listeners: Set<(notification: StateChangeNotification) => void> = new Set();
  
  private constructor() {
    this.initializeMessageHandlers();
  }
  
  /**
   * 获取单例实例
   */
  public static getInstance(): StateSyncService {
    if (!StateSyncService.instance) {
      StateSyncService.instance = new StateSyncService();
    }
    return StateSyncService.instance;
  }
  
  /**
   * 初始化消息处理器
   */
  private initializeMessageHandlers(): void {
    // 监听来自content script的状态更新
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      if (message.type === 'state_sync_update' && sender.tab?.id) {
        this.handleStateUpdate(sender.tab.id, message.data);
        sendResponse({ success: true });
        return true;
      }
      
      if (message.type === 'state_sync_get' && sender.tab?.id) {
        const state = this.getTabState(sender.tab.id);
        sendResponse({ success: true, data: state });
        return true;
      }
    });
    
    // 仅在 chrome.tabs API 可用时添加标签页监听器（Background context）
    if (chrome.tabs) {
      // 监听标签页关闭事件
      chrome.tabs.onRemoved.addListener((tabId) => {
        this.removeTabState(tabId);
      });
      
      // 监听标签页更新事件
      chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
        if (changeInfo.status === 'complete' && tab.url) {
          this.updateTabUrl(tabId, tab.url);
        }
      });
    }
  }
  
  /**
   * 处理状态更新
   */
  private handleStateUpdate(tabId: number, stateData: Partial<SyncStateData>): void {
    const currentState = this.syncStates.get(tabId) || this.createDefaultState(tabId);
    
    // 更新状态
    const updatedState: SyncStateData = {
      ...currentState,
      ...stateData,
      lastUpdate: Date.now(),
      tabId
    };
    
    this.syncStates.set(tabId, updatedState);
    
    // 通知监听器
    this.notifyListeners({
      type: 'monitoring',
      tabId,
      timestamp: Date.now(),
      data: updatedState
    });
    
    console.log(`状态同步更新 - Tab ${tabId}:`, updatedState);
  }
  
  /**
   * 创建默认状态
   */
  private createDefaultState(tabId: number): SyncStateData {
    return {
      monitoringStatus: MonitoringStatus.IDLE,
      currentRun: null,
      statistics: {
        totalRuns: 0,
        successfulRuns: 0,
        failedRuns: 0,
        totalStocksCodes: 0,
        totalStocksData: 0,
        totalDataSent: 0,
        averageRunTime: 0,
        lastRunTime: 0,
        uptime: 0,
        errorCount: 0,
        retryCount: 0,
        cacheHitRate: 0
      },
      lastUpdate: Date.now(),
      tabId
    };
  }
  
  /**
   * 获取标签页状态
   */
  public getTabState(tabId: number): SyncStateData | null {
    return this.syncStates.get(tabId) || null;
  }
  
  /**
   * 获取所有标签页状态
   */
  public getAllTabStates(): Map<number, SyncStateData> {
    return new Map(this.syncStates);
  }
  
  /**
   * 移除标签页状态
   */
  public removeTabState(tabId: number): void {
    if (this.syncStates.has(tabId)) {
      this.syncStates.delete(tabId);
      console.log(`移除标签页状态 - Tab ${tabId}`);
      
      // 通知监听器
      this.notifyListeners({
        type: 'monitoring',
        tabId,
        timestamp: Date.now(),
        data: { action: 'removed' }
      });
    }
  }
  
  /**
   * 更新标签页URL
   */
  private updateTabUrl(tabId: number, url: string): void {
    const state = this.syncStates.get(tabId);
    if (state) {
      state.url = url;
      state.lastUpdate = Date.now();
      this.syncStates.set(tabId, state);
    }
  }
  
  /**
   * 添加状态变更监听器
   */
  public addListener(listener: (notification: StateChangeNotification) => void): void {
    this.listeners.add(listener);
  }
  
  /**
   * 移除状态变更监听器
   */
  public removeListener(listener: (notification: StateChangeNotification) => void): void {
    this.listeners.delete(listener);
  }
  
  /**
   * 通知所有监听器
   */
  private notifyListeners(notification: StateChangeNotification): void {
    this.listeners.forEach(listener => {
      try {
        listener(notification);
      } catch (error) {
        console.error('状态同步监听器执行失败:', error);
      }
    });
  }
  
  /**
   * 向指定标签页发送状态同步请求
   */
  public async requestStateSync(tabId: number): Promise<SyncStateData | null> {
    if (!chrome.tabs) return null;
    
    try {
      const response = await chrome.tabs.sendMessage(tabId, {
        type: 'state_sync_request'
      });
      
      if (response && response.success) {
        this.handleStateUpdate(tabId, response.data);
        return this.getTabState(tabId);
      }
    } catch (error) {
      console.warn(`无法从标签页 ${tabId} 获取状态:`, error);
    }
    
    return null;
  }
  
  /**
   * 广播状态变更到所有标签页
   */
  public async broadcastStateChange(notification: StateChangeNotification): Promise<void> {
    if (!chrome.tabs) return;

    const tabs = await chrome.tabs.query({ url: '*://*.10jqka.com.cn/*' });
    
    for (const tab of tabs) {
      if (tab.id && tab.id !== notification.tabId) {
        try {
          await chrome.tabs.sendMessage(tab.id, {
            type: 'state_sync_broadcast',
            data: notification
          });
        } catch (error) {
          // 忽略无法发送消息的标签页（可能已关闭或未加载扩展）
        }
      }
    }
  }
  
  /**
   * 获取活跃的监控标签页
   */
  public getActiveMonitoringTabs(): Array<{ tabId: number; state: SyncStateData }> {
    const activeTabs: Array<{ tabId: number; state: SyncStateData }> = [];
    
    this.syncStates.forEach((state, tabId) => {
      if (state.monitoringStatus === MonitoringStatus.RUNNING || 
          state.monitoringStatus === MonitoringStatus.STARTING) {
        activeTabs.push({ tabId, state });
      }
    });
    
    return activeTabs;
  }
  
  /**
   * 获取汇总统计信息
   */
  public getAggregatedStatistics(): MonitoringStatistics {
    const aggregated: MonitoringStatistics = {
      totalRuns: 0,
      successfulRuns: 0,
      failedRuns: 0,
      totalStocksCodes: 0,
      totalStocksData: 0,
      totalDataSent: 0,
      averageRunTime: 0,
      lastRunTime: 0,
      uptime: 0,
      errorCount: 0,
      retryCount: 0,
      cacheHitRate: 0
    };
    
    let totalRunTime = 0;
    let totalCacheRequests = 0;
    let totalCacheHits = 0;
    let tabCount = 0;
    
    this.syncStates.forEach((state) => {
      const stats = state.statistics;
      
      aggregated.totalRuns += stats.totalRuns;
      aggregated.successfulRuns += stats.successfulRuns;
      aggregated.failedRuns += stats.failedRuns;
      aggregated.totalStocksCodes += stats.totalStocksCodes;
      aggregated.totalStocksData += stats.totalStocksData;
      aggregated.totalDataSent += stats.totalDataSent;
      aggregated.errorCount += stats.errorCount;
      aggregated.retryCount += stats.retryCount;
      
      totalRunTime += stats.averageRunTime * stats.totalRuns;
      
      if (stats.lastRunTime > aggregated.lastRunTime) {
        aggregated.lastRunTime = stats.lastRunTime;
      }
      
      if (stats.uptime > aggregated.uptime) {
        aggregated.uptime = stats.uptime;
      }
      
      // 计算缓存命中率
      const cacheRequests = Math.round(stats.totalRuns * (stats.cacheHitRate / 100));
      totalCacheRequests += stats.totalRuns;
      totalCacheHits += cacheRequests;
      
      tabCount++;
    });
    
    // 计算平均值
    if (aggregated.totalRuns > 0) {
      aggregated.averageRunTime = totalRunTime / aggregated.totalRuns;
    }
    
    if (totalCacheRequests > 0) {
      aggregated.cacheHitRate = (totalCacheHits / totalCacheRequests) * 100;
    }
    
    return aggregated;
  }
  
  /**
   * 获取系统健康状态
   */
  public getSystemHealthStatus(): {
    status: 'healthy' | 'warning' | 'critical';
    activeTabsCount: number;
    issues: string[];
    recommendations: string[];
  } {
    const activeTabs = this.getActiveMonitoringTabs();
    const aggregatedStats = this.getAggregatedStatistics();
    const issues: string[] = [];
    const recommendations: string[] = [];
    
    // 检查活跃标签页数量
    if (activeTabs.length === 0) {
      issues.push('没有活跃的监控标签页');
      recommendations.push('在同花顺页面启动监控');
    } else if (activeTabs.length > 5) {
      issues.push(`活跃监控标签页过多: ${activeTabs.length}`);
      recommendations.push('关闭不必要的监控标签页以节省资源');
    }
    
    // 检查错误率
    const errorRate = aggregatedStats.totalRuns > 0 ? 
      (aggregatedStats.failedRuns / aggregatedStats.totalRuns) * 100 : 0;
    
    if (errorRate > 50) {
      issues.push(`系统错误率过高: ${errorRate.toFixed(1)}%`);
      recommendations.push('检查网络连接和API配置');
    } else if (errorRate > 20) {
      issues.push(`系统错误率较高: ${errorRate.toFixed(1)}%`);
      recommendations.push('监控错误日志，考虑优化重试策略');
    }
    
    // 检查平均运行时间
    if (aggregatedStats.averageRunTime > 30000) {
      issues.push(`平均运行时间过长: ${(aggregatedStats.averageRunTime / 1000).toFixed(1)}s`);
      recommendations.push('优化数据抓取逻辑，考虑增加缓存');
    }
    
    // 确定整体状态
    let status: 'healthy' | 'warning' | 'critical' = 'healthy';
    if (issues.length > 0) {
      status = errorRate > 50 || aggregatedStats.averageRunTime > 60000 ? 'critical' : 'warning';
    }
    
    return {
      status,
      activeTabsCount: activeTabs.length,
      issues,
      recommendations
    };
  }
  
  /**
   * 清理过期状态
   */
  public cleanupExpiredStates(maxAge: number = 3600000): void { // 默认1小时
    const now = Date.now();
    const expiredTabs: number[] = [];
    
    this.syncStates.forEach((state, tabId) => {
      if (now - state.lastUpdate > maxAge) {
        expiredTabs.push(tabId);
      }
    });
    
    expiredTabs.forEach(tabId => {
      this.removeTabState(tabId);
    });
    
    if (expiredTabs.length > 0) {
      console.log(`清理了 ${expiredTabs.length} 个过期状态`);
    }
  }
}

// 导出单例实例
export const stateSyncService = StateSyncService.getInstance();