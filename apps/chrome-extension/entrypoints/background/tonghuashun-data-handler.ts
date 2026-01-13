import { TongHuaShunExtractor } from '@/utils/tonghuashun-extractor';
import { ErrorHandler, ErrorType, ErrorSeverity } from '@/utils/error-handler';
import { RetryMechanism } from '@/utils/retry-mechanism';

// 同花顺数据处理状态
interface TongHuaShunDataState {
  isMonitoring: boolean;
  monitoringTabs: Set<number>;
  dataBuffer: Map<string, any[]>; // 按股票代码缓存数据
  lastSyncTime: number;
  retryCount: number;
}

// 后端API配置
export const BACKEND_CONFIG = {
  baseUrl: 'http://localhost:8000',
  endpoints: {
    batchData: '/api/v1/stocks/data/batch',
    stockInfo: '/api/v1/stocks/info'
  },
  maxRetries: 3,
  retryDelay: 1000,
  batchSize: 50,
  syncInterval: 30000 // 30秒同步一次
};

let dataState: TongHuaShunDataState = {
  isMonitoring: false,
  monitoringTabs: new Set(),
  dataBuffer: new Map(),
  lastSyncTime: 0,
  retryCount: 0
};

let syncTimer: NodeJS.Timeout | null = null;

/**
 * 初始化同花顺数据处理器
 */
export function initTongHuaShunDataHandler() {
  console.log('初始化同花顺数据处理器');
  
  // 监听来自content script的消息
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (!message.action?.startsWith('tonghuashun_')) return false;
    
    handleTongHuaShunMessage(message, sender, sendResponse);
    return true; // 保持消息通道开放
  });
  
  // 监听标签页关闭事件
  chrome.tabs.onRemoved.addListener((tabId) => {
    if (dataState.monitoringTabs.has(tabId)) {
      dataState.monitoringTabs.delete(tabId);
      console.log(`标签页 ${tabId} 已关闭，停止监控`);
      
      // 如果没有监控的标签页了，停止整体监控
      if (dataState.monitoringTabs.size === 0) {
        stopDataMonitoring();
      }
    }
  });
}

/**
 * 处理同花顺相关消息
 */
async function handleTongHuaShunMessage(
  message: any, 
  sender: chrome.runtime.MessageSender, 
  sendResponse: (response: any) => void
) {
  const tabId = sender.tab?.id;
  
  try {
    switch (message.action) {
      case 'tonghuashun_start_monitoring':
        try {
          await startDataMonitoring(tabId);
          sendResponse({ success: true });
        } catch (error) {
          const handleResult = ErrorHandler.handleError(error, { 
            context: 'startDataMonitoring',
            tabId 
          });
          sendResponse({ success: false, error: handleResult.errorMessage });
        }
        break;
        
      case 'tonghuashun_stop_monitoring':
        try {
          await stopDataMonitoring(tabId);
          sendResponse({ success: true });
        } catch (error) {
          const handleResult = ErrorHandler.handleError(error, { 
            context: 'stopDataMonitoring',
            tabId 
          });
          sendResponse({ success: false, error: handleResult.errorMessage });
        }
        break;
        
      case 'tonghuashun_submit_data':
        try {
          await handleDataSubmission(message.data, tabId);
          sendResponse({ success: true });
        } catch (error) {
          const handleResult = ErrorHandler.handleError(error, { 
            context: 'handleDataSubmission',
            tabId,
            dataLength: message.data?.length 
          });
          sendResponse({ success: false, error: handleResult.errorMessage });
        }
        break;
        
      case 'tonghuashun_get_status':
        try {
          const stats = ErrorHandler.getErrorStats();
          sendResponse({
            success: true,
            status: {
              isMonitoring: dataState.isMonitoring,
              monitoringTabs: Array.from(dataState.monitoringTabs),
              bufferSize: dataState.dataBuffer.size,
              lastSyncTime: dataState.lastSyncTime,
              retryCount: dataState.retryCount,
              errorStats: {
                totalErrors: stats.total,
                recentErrors: stats.recent.length,
                errorsByType: stats.byType
              }
            }
          });
        } catch (error) {
          const handleResult = ErrorHandler.handleError(error, { 
            context: 'getStatus',
            tabId 
          });
          sendResponse({ success: false, error: handleResult.errorMessage });
        }
        break;
        
      default:
        const unknownError = new Error(`未知的消息类型: ${message.action}`);
        const handleResult = ErrorHandler.handleError(unknownError, { 
          context: 'unknownMessageAction',
          action: message.action 
        });
        sendResponse({ success: false, error: handleResult.errorMessage });
    }
  } catch (error) {
    const handleResult = ErrorHandler.handleError(error, { 
      context: 'handleTongHuaShunMessage',
      action: message?.action,
      tabId 
    });
    sendResponse({ 
      success: false, 
      error: handleResult.errorMessage 
    });
  }
}

/**
 * 开始数据监控
 */
async function startDataMonitoring(tabId?: number) {
  if (tabId) {
    dataState.monitoringTabs.add(tabId);
  }
  
  if (!dataState.isMonitoring) {
    dataState.isMonitoring = true;
    console.log('开始同花顺数据监控');
    
    // 启动定时同步
    startSyncTimer();
  }
}

/**
 * 停止数据监控
 */
async function stopDataMonitoring(tabId?: number) {
  if (tabId) {
    dataState.monitoringTabs.delete(tabId);
  } else {
    // 停止所有监控
    dataState.monitoringTabs.clear();
  }
  
  if (dataState.monitoringTabs.size === 0) {
    dataState.isMonitoring = false;
    console.log('停止同花顺数据监控');
    
    // 停止定时同步
    stopSyncTimer();
    
    // 最后一次同步剩余数据
    await syncDataToBackend();
  }
}

/**
 * 处理数据提交
 */
async function handleDataSubmission(data: any[], tabId?: number) {
  try {
    if (!Array.isArray(data) || data.length === 0) {
      const error = new Error('收到空数据或格式错误的数据');
      (error as any).type = ErrorType.VALIDATION;
      (error as any).severity = ErrorSeverity.MEDIUM;
      throw error;
    }
    
    console.log(`收到来自标签页 ${tabId} 的 ${data.length} 条股票数据`);
    
    // 数据去重和缓存
    let processedCount = 0;
    let duplicateCount = 0;
    
    for (const stockData of data) {
      try {
        if (!stockData.stock_code) {
          console.warn('跳过无股票代码的数据:', stockData);
          continue;
        }
        
        const stockCode = stockData.stock_code;
        if (!dataState.dataBuffer.has(stockCode)) {
          dataState.dataBuffer.set(stockCode, []);
        }
        
        const buffer = dataState.dataBuffer.get(stockCode)!;
        
        // 简单去重：检查最近的数据是否重复
        const isDuplicate = buffer.some(existing => 
          existing.timestamp === stockData.timestamp &&
          existing.current_price === stockData.current_price
        );
        
        if (!isDuplicate) {
          buffer.push({
            ...stockData,
            source_tab_id: tabId,
            received_at: Date.now()
          });
          
          // 限制缓存大小
          if (buffer.length > 100) {
            buffer.splice(0, buffer.length - 100);
          }
          
          processedCount++;
        } else {
          duplicateCount++;
        }
      } catch (error) {
        ErrorHandler.handleError(error, { 
          context: 'processStockData',
          stockCode: stockData?.stock_code,
          tabId 
        });
      }
    }
    
    console.log(`数据处理完成: 新增 ${processedCount} 条, 重复 ${duplicateCount} 条`);
    
    // 如果缓存数据过多，立即同步
    const totalBufferSize = Array.from(dataState.dataBuffer.values())
      .reduce((sum, buffer) => sum + buffer.length, 0);
      
    if (totalBufferSize >= BACKEND_CONFIG.batchSize) {
      await syncDataToBackend();
    }
  } catch (error) {
    const handleResult = ErrorHandler.handleError(error, { 
      context: 'handleDataSubmission',
      tabId,
      dataLength: data?.length 
    });
    throw new Error(handleResult.errorMessage);
  }
}

/**
 * 启动同步定时器
 */
function startSyncTimer() {
  if (syncTimer) return;
  
  syncTimer = setInterval(async () => {
    await syncDataToBackend();
  }, BACKEND_CONFIG.syncInterval);
}

/**
 * 停止同步定时器
 */
function stopSyncTimer() {
  if (syncTimer) {
    clearInterval(syncTimer);
    syncTimer = null;
  }
}

/**
 * 同步数据到后端
 */
async function syncDataToBackend() {
  try {
    if (dataState.dataBuffer.size === 0) return;
    
    // 收集所有缓存的数据
    const allData: any[] = [];
    for (const [stockCode, buffer] of dataState.dataBuffer.entries()) {
      allData.push(...buffer);
    }
    
    if (allData.length === 0) return;
    
    console.log(`开始同步 ${allData.length} 条数据到后端`);
    
    try {
      const success = await submitDataToBackend(allData);
      if (success) {
        // 清空已同步的数据
        dataState.dataBuffer.clear();
        dataState.lastSyncTime = Date.now();
        dataState.retryCount = 0;
        console.log('数据同步成功');
      } else {
        const error = new Error('数据同步失败');
        (error as any).type = ErrorType.API;
        (error as any).severity = ErrorSeverity.HIGH;
        throw error;
      }
    } catch (error) {
      const handleResult = ErrorHandler.handleError(error, { 
        context: 'syncDataToBackend',
        dataLength: allData.length,
        retryCount: dataState.retryCount 
      });
      
      dataState.retryCount++;
      
      // 如果重试次数过多，清空部分旧数据避免内存泄漏
      if (dataState.retryCount > BACKEND_CONFIG.maxRetries) {
        console.warn('重试次数过多，清空部分旧数据');
        for (const [stockCode, buffer] of dataState.dataBuffer.entries()) {
          if (buffer.length > 20) {
            buffer.splice(0, buffer.length - 20);
          }
        }
        dataState.retryCount = 0;
        
        // 记录数据丢失警告
        const dataLossError = new Error(`数据同步重试失败，丢失 ${allData.length} 条数据`);
        (dataLossError as any).type = ErrorType.SYSTEM;
        (dataLossError as any).severity = ErrorSeverity.CRITICAL;
        ErrorHandler.handleError(dataLossError, { 
          context: 'dataLoss',
          lostDataCount: allData.length 
        });
      }
      
      // 重新抛出错误以便上层处理
      throw new Error(handleResult.errorMessage);
    }
  } catch (error) {
    ErrorHandler.handleError(error, { 
      context: 'syncDataToBackend',
      bufferSize: dataState.dataBuffer.size 
    });
  }
}

/**
 * 提交数据到后端API - 使用增强重试机制
 */
async function submitDataToBackend(data: any[]): Promise<boolean> {
  // 创建网络请求专用重试配置
  const retryConfig = RetryMechanism.createNetworkRetryConfig({
    maxRetries: 5,
    baseDelay: 1000,
    maxDelay: 15000,
    backoffMultiplier: 1.8,
    onRetry: (error: any, attempt: number, delay: number) => {
      console.log(`数据提交重试: 第${attempt}次失败 (${error?.message || '未知错误'})，${delay}ms后重试`);
      
      // 记录重试信息
      ErrorHandler.handleError(error, {
        context: 'submitDataToBackend_Retry',
        attempt,
        dataCount: data.length,
        statusCode: error?.statusCode,
        errorType: error?.type
      });
    },
    onFinalFailure: (error: any, totalAttempts: number) => {
      console.error(`数据提交最终失败: 经过${totalAttempts}次尝试后仍然失败`);
      
      // 记录最终失败
      ErrorHandler.handleError(error, {
        context: 'submitDataToBackend_FinalFailure',
        totalAttempts,
        dataCount: data.length
      });
    }
  });

  // 使用重试机制执行提交操作
  const retryResult = await RetryMechanism.executeWithRetry(async () => {
    console.log(`提交 ${data.length} 条数据到后端...`);
    
    const response = await fetch(`${BACKEND_CONFIG.baseUrl}${BACKEND_CONFIG.endpoints.batchData}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        data: data,
        source: 'chrome_extension',
        timestamp: Date.now()
      })
    });

    if (!response.ok) {
      const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
      (error as any).type = ErrorType.API;
      (error as any).severity = response.status >= 500 ? ErrorSeverity.HIGH : ErrorSeverity.MEDIUM;
      (error as any).statusCode = response.status;
      throw error;
    }

    const result = await response.json();
    return result;
    
  }, retryConfig);

  if (retryResult.success) {
    console.log(`数据提交成功: ${data.length} 条数据，经过 ${retryResult.totalAttempts} 次尝试`);
    
    // 记录成功统计
    if (retryResult.totalAttempts > 1) {
      console.log('重试统计:', {
        totalAttempts: retryResult.totalAttempts,
        totalTime: retryResult.totalTime,
        retryHistory: retryResult.retryHistory
      });
    }
    
    return true;
  } else {
    console.error(`数据提交失败: ${retryResult.error?.message || '未知错误'}`);
    console.error('失败统计:', {
      totalAttempts: retryResult.totalAttempts,
      totalTime: retryResult.totalTime,
      retryHistory: retryResult.retryHistory
    });
    
    return false;
  }
}

/**
 * 获取数据处理状态
 */
export function getDataHandlerStatus() {
  return {
    isMonitoring: dataState.isMonitoring,
    monitoringTabs: Array.from(dataState.monitoringTabs),
    bufferSize: dataState.dataBuffer.size,
    lastSyncTime: dataState.lastSyncTime,
    retryCount: dataState.retryCount
  };
}

/**
 * 手动触发数据同步
 */
export async function manualSyncData() {
  await syncDataToBackend();
}

/**
 * 清空数据缓存
 */
export function clearDataBuffer() {
  dataState.dataBuffer.clear();
  console.log('数据缓存已清空');
}