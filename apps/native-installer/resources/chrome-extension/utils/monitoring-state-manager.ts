/**
 * 监控状态管理器
 * 实现实时状态同步机制，管理扩展的运行状态、数据抓取状态和错误状态
 */

// 监控状态枚举
export enum MonitoringStatus {
  IDLE = 'idle',           // 空闲状态
  STARTING = 'starting',   // 启动中
  RUNNING = 'running',     // 运行中
  PAUSED = 'paused',       // 暂停
  STOPPING = 'stopping',   // 停止中
  STOPPED = 'stopped',     // 已停止
  ERROR = 'error'          // 错误状态
}

// 数据抓取状态枚举
export enum DataFetchStatus {
  IDLE = 'idle',                    // 空闲
  EXTRACTING_CODES = 'extracting',  // 提取股票代码中
  FETCHING_DATA = 'fetching',       // 获取数据中
  SENDING_DATA = 'sending',         // 发送数据中
  COMPLETED = 'completed',          // 完成
  FAILED = 'failed'                 // 失败
}

// 错误级别枚举
export enum ErrorLevel {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical'
}

// 状态变更事件类型
export interface StateChangeEvent {
  type: 'monitoring' | 'dataFetch' | 'error' | 'statistics';
  timestamp: number;
  data: any;
}

// 监控统计信息
export interface MonitoringStatistics {
  totalRuns: number;
  successfulRuns: number;
  failedRuns: number;
  totalStocksCodes: number;
  totalStocksData: number;
  totalDataSent: number;
  averageRunTime: number;
  lastRunTime: number;
  uptime: number;
  errorCount: number;
  retryCount: number;
  cacheHitRate: number;
}

// 当前运行状态
export interface CurrentRunState {
  runId: string;
  startTime: number;
  status: DataFetchStatus;
  progress: {
    extractedCodes: number;
    fetchedData: number;
    sentData: number;
    totalExpected: number;
  };
  errors: Array<{
    level: ErrorLevel;
    message: string;
    timestamp: number;
    context?: any;
  }>;
  retries: number;
  cacheStats?: any;
}

// 状态监听器类型
export type StateListener = (event: StateChangeEvent) => void;

/**
 * 监控状态管理器类
 */
export class MonitoringStateManager {
  private static instance: MonitoringStateManager;
  
  // 状态数据
  private monitoringStatus: MonitoringStatus = MonitoringStatus.IDLE;
  private currentRun: CurrentRunState | null = null;
  private statistics: MonitoringStatistics;
  private listeners: Set<StateListener> = new Set();
  private startTime: number = Date.now();
  
  // 历史记录
  private runHistory: Array<{
    runId: string;
    startTime: number;
    endTime: number;
    status: DataFetchStatus;
    statistics: any;
  }> = [];
  
  private constructor() {
    this.statistics = this.initializeStatistics();
    this.loadPersistedState();
  }
  
  /**
   * 获取单例实例
   */
  public static getInstance(): MonitoringStateManager {
    if (!MonitoringStateManager.instance) {
      MonitoringStateManager.instance = new MonitoringStateManager();
    }
    return MonitoringStateManager.instance;
  }
  
  /**
   * 初始化统计信息
   */
  private initializeStatistics(): MonitoringStatistics {
    return {
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
  }
  
  /**
   * 加载持久化状态
   */
  private async loadPersistedState(): Promise<void> {
    try {
      const result = await chrome.storage.local.get(['monitoringStatistics', 'runHistory']);
      
      if (result.monitoringStatistics) {
        this.statistics = { ...this.statistics, ...result.monitoringStatistics };
      }
      
      if (result.runHistory) {
        this.runHistory = result.runHistory.slice(-50); // 保留最近50次运行记录
      }
      
    } catch (error) {
      console.warn('加载持久化状态失败:', error);
    }
  }
  
  /**
   * 保存状态到存储
   */
  private async persistState(): Promise<void> {
    try {
      await chrome.storage.local.set({
        monitoringStatistics: this.statistics,
        runHistory: this.runHistory
      });
    } catch (error) {
      console.warn('保存状态失败:', error);
    }
  }
  
  /**
   * 添加状态监听器
   */
  public addListener(listener: StateListener): void {
    this.listeners.add(listener);
  }
  
  /**
   * 移除状态监听器
   */
  public removeListener(listener: StateListener): void {
    this.listeners.delete(listener);
  }
  
  /**
   * 触发状态变更事件
   */
  private emitStateChange(type: StateChangeEvent['type'], data: any): void {
    const event: StateChangeEvent = {
      type,
      timestamp: Date.now(),
      data
    };
    
    this.listeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        console.error('状态监听器执行失败:', error);
      }
    });
  }
  
  /**
   * 设置监控状态
   */
  public setMonitoringStatus(status: MonitoringStatus): void {
    const previousStatus = this.monitoringStatus;
    this.monitoringStatus = status;
    
    console.log(`监控状态变更: ${previousStatus} -> ${status}`);
    
    this.emitStateChange('monitoring', {
      status,
      previousStatus,
      timestamp: Date.now()
    });
    
    // 更新运行时间
    if (status === MonitoringStatus.RUNNING) {
      this.startTime = Date.now();
    }
  }
  
  /**
   * 获取当前监控状态
   */
  public getMonitoringStatus(): MonitoringStatus {
    return this.monitoringStatus;
  }
  
  /**
   * 开始新的数据抓取运行
   */
  public startNewRun(): string {
    const runId = `run_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    this.currentRun = {
      runId,
      startTime: Date.now(),
      status: DataFetchStatus.IDLE,
      progress: {
        extractedCodes: 0,
        fetchedData: 0,
        sentData: 0,
        totalExpected: 0
      },
      errors: [],
      retries: 0
    };
    
    this.statistics.totalRuns++;
    
    console.log(`开始新的数据抓取运行: ${runId}`);
    
    this.emitStateChange('dataFetch', {
      action: 'start',
      runId,
      currentRun: this.currentRun
    });
    
    return runId;
  }
  
  /**
   * 更新当前运行状态
   */
  public updateRunStatus(status: DataFetchStatus, progress?: Partial<CurrentRunState['progress']>): void {
    if (!this.currentRun) {
      console.warn('尝试更新运行状态，但没有活动的运行');
      return;
    }
    
    this.currentRun.status = status;
    
    if (progress) {
      this.currentRun.progress = { ...this.currentRun.progress, ...progress };
    }
    
    console.log(`运行状态更新: ${this.currentRun.runId} -> ${status}`, progress);
    
    this.emitStateChange('dataFetch', {
      action: 'update',
      runId: this.currentRun.runId,
      status,
      progress: this.currentRun.progress
    });
  }
  
  /**
   * 添加运行错误
   */
  public addRunError(level: ErrorLevel, message: string, context?: any): void {
    if (!this.currentRun) {
      console.warn('尝试添加运行错误，但没有活动的运行');
      return;
    }
    
    const error = {
      level,
      message,
      timestamp: Date.now(),
      context
    };
    
    this.currentRun.errors.push(error);
    this.statistics.errorCount++;
    
    console.log(`运行错误: ${this.currentRun.runId} - ${level}: ${message}`);
    
    this.emitStateChange('error', {
      runId: this.currentRun.runId,
      error
    });
  }
  
  /**
   * 增加重试计数
   */
  public incrementRetryCount(): void {
    if (this.currentRun) {
      this.currentRun.retries++;
    }
    this.statistics.retryCount++;
  }
  
  /**
   * 更新缓存统计
   */
  public updateCacheStats(cacheStats: any): void {
    if (this.currentRun) {
      this.currentRun.cacheStats = cacheStats;
    }
    
    // 计算缓存命中率
    if (cacheStats.totalRequests > 0) {
      this.statistics.cacheHitRate = (cacheStats.hits / cacheStats.totalRequests) * 100;
    }
  }
  
  /**
   * 完成当前运行
   */
  public completeRun(success: boolean, finalStats?: any): void {
    if (!this.currentRun) {
      console.warn('尝试完成运行，但没有活动的运行');
      return;
    }
    
    const endTime = Date.now();
    const duration = endTime - this.currentRun.startTime;
    
    // 更新统计信息
    if (success) {
      this.statistics.successfulRuns++;
      this.currentRun.status = DataFetchStatus.COMPLETED;
    } else {
      this.statistics.failedRuns++;
      this.currentRun.status = DataFetchStatus.FAILED;
    }
    
    // 更新数据统计
    if (finalStats) {
      this.statistics.totalStocksCodes += finalStats.stockCodes || 0;
      this.statistics.totalStocksData += finalStats.stockData || 0;
      this.statistics.totalDataSent += finalStats.dataSent || 0;
    }
    
    // 更新平均运行时间
    this.statistics.lastRunTime = duration;
    this.statistics.averageRunTime = (
      (this.statistics.averageRunTime * (this.statistics.totalRuns - 1) + duration) / 
      this.statistics.totalRuns
    );
    
    // 添加到历史记录
    this.runHistory.push({
      runId: this.currentRun.runId,
      startTime: this.currentRun.startTime,
      endTime,
      status: this.currentRun.status,
      statistics: finalStats
    });
    
    // 保持历史记录在合理范围内
    if (this.runHistory.length > 100) {
      this.runHistory = this.runHistory.slice(-50);
    }
    
    console.log(`运行完成: ${this.currentRun.runId} - ${success ? '成功' : '失败'} (${duration}ms)`);
    
    this.emitStateChange('dataFetch', {
      action: 'complete',
      runId: this.currentRun.runId,
      success,
      duration,
      finalStats
    });
    
    // 清除当前运行
    this.currentRun = null;
    
    // 持久化状态
    this.persistState();
  }
  
  /**
   * 获取当前运行状态
   */
  public getCurrentRun(): CurrentRunState | null {
    return this.currentRun;
  }
  
  /**
   * 获取统计信息
   */
  public getStatistics(): MonitoringStatistics {
    // 更新运行时间
    this.statistics.uptime = Date.now() - this.startTime;
    return { ...this.statistics };
  }
  
  /**
   * 获取运行历史
   */
  public getRunHistory(limit: number = 20): typeof this.runHistory {
    return this.runHistory.slice(-limit);
  }
  
  /**
   * 重置统计信息
   */
  public resetStatistics(): void {
    this.statistics = this.initializeStatistics();
    this.runHistory = [];
    this.startTime = Date.now();
    
    this.emitStateChange('statistics', {
      action: 'reset'
    });
    
    this.persistState();
  }
  
  /**
   * 获取系统健康状态
   */
  public getHealthStatus(): {
    status: 'healthy' | 'warning' | 'critical';
    issues: string[];
    recommendations: string[];
  } {
    const issues: string[] = [];
    const recommendations: string[] = [];
    
    // 检查错误率
    const errorRate = this.statistics.totalRuns > 0 ? 
      (this.statistics.failedRuns / this.statistics.totalRuns) * 100 : 0;
    
    if (errorRate > 50) {
      issues.push(`错误率过高: ${errorRate.toFixed(1)}%`);
      recommendations.push('检查网络连接和API配置');
    } else if (errorRate > 20) {
      issues.push(`错误率较高: ${errorRate.toFixed(1)}%`);
      recommendations.push('监控错误日志，考虑优化重试策略');
    }
    
    // 检查平均运行时间
    if (this.statistics.averageRunTime > 30000) {
      issues.push(`平均运行时间过长: ${(this.statistics.averageRunTime / 1000).toFixed(1)}s`);
      recommendations.push('优化数据抓取逻辑，考虑增加缓存');
    }
    
    // 检查缓存命中率
    if (this.statistics.cacheHitRate < 30 && this.statistics.totalRuns > 5) {
      issues.push(`缓存命中率较低: ${this.statistics.cacheHitRate.toFixed(1)}%`);
      recommendations.push('检查缓存配置，优化缓存策略');
    }
    
    // 确定整体状态
    let status: 'healthy' | 'warning' | 'critical' = 'healthy';
    if (issues.length > 0) {
      status = errorRate > 50 || this.statistics.averageRunTime > 60000 ? 'critical' : 'warning';
    }
    
    return { status, issues, recommendations };
  }
  
  /**
   * 导出状态数据
   */
  public exportStateData(): {
    monitoringStatus: MonitoringStatus;
    currentRun: CurrentRunState | null;
    statistics: MonitoringStatistics;
    runHistory: typeof this.runHistory;
    healthStatus: ReturnType<MonitoringStateManager['getHealthStatus']>;
  } {
    return {
      monitoringStatus: this.monitoringStatus,
      currentRun: this.currentRun,
      statistics: this.getStatistics(),
      runHistory: this.getRunHistory(),
      healthStatus: this.getHealthStatus()
    };
  }
}

// 导出单例实例
export const monitoringStateManager = MonitoringStateManager.getInstance();