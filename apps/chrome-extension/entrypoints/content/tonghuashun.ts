/**
 * 同花顺股票数据抓取 Content Script
 * 专门用于同花顺网站的数据抓取和监控
 */

import { ErrorHandler, ErrorType, ErrorSeverity } from '@/utils/error-handler';
import { EnhancedDataExtractor, ExtractionConfig, ExtractionResult } from '@/utils/enhanced-data-extractor';
import { RetryMechanism } from '@/utils/retry-mechanism';
import { monitoringStateManager, MonitoringStatus, DataFetchStatus, ErrorLevel } from '@/utils/monitoring-state-manager';
import { SyncStateData, StateChangeNotification } from '@/utils/state-sync-service';

export default defineContentScript({
  matches: [
    '*://*.10jqka.com.cn/*',
    '*://*.ths.com.cn/*',
    '*://q.10jqka.com.cn/*',
    '*://stockpage.10jqka.com.cn/*',
    '*://data.10jqka.com.cn/*'
  ],
  main() {
    console.log('同花顺股票监控插件已加载');

    // 数据抓取配置
    const CONFIG = {
      // 后端API地址
      BACKEND_API: 'http://localhost:8000/api/v1',
      // 抓取间隔（毫秒）
      FETCH_INTERVAL: 30000,
      // 重试次数
      MAX_RETRIES: 3,
      // 重试延迟
      RETRY_DELAY: 1000
    };
    
    // 增强数据抓取配置
    const EXTRACTION_CONFIG: ExtractionConfig = {
      maxRetries: 3,
      retryDelay: 1000,
      timeout: 15000,
      batchSize: 15,
      enableCache: true,
      cacheExpiry: 25000, // 25秒缓存，略小于抓取间隔
      enableParallelProcessing: true,
      maxConcurrentRequests: 3,
      enableProgressCallback: true,
      enableAdvancedDeduplication: true
    };

    // 股票数据接口
    interface StockData {
      code: string;
      name: string;
      price: number;
      change_amount: number;
      change_percent: number;
      volume: number;
      turnover: number;
      high: number;
      low: number;
      open_price: number;
      prev_close: number;
      timestamp: string;
    }

    // 监控状态
    let isMonitoring = false;
    let monitoringInterval: NodeJS.Timeout | null = null;

    /**
     * 解析JSONP响应数据
     */
    function parseJSONP(jsonpString: string): any {
      try {
        // 移除JSONP包装，提取JSON数据
        const match = jsonpString.match(/\((.*)\)/);
        if (match && match[1]) {
          return JSON.parse(match[1]);
        }
        return null;
      } catch (error) {
        console.error('JSONP解析失败:', error);
        return null;
      }
    }

    /**
     * 从DOM中提取股票列表 - 使用增强版抓取器
     */
    async function extractStockListFromDOM(): Promise<string[]> {
      try {
        console.log('开始使用增强版抓取器从DOM提取股票列表...');
        
        // 使用增强版数据抓取器
        const stockInfos = await EnhancedDataExtractor.extractStockCodesFromDOM(EXTRACTION_CONFIG);
        
        const stockCodes = stockInfos.map(info => info.code);
        
        console.log(`增强版DOM提取完成，共找到 ${stockCodes.length} 个股票代码:`, stockCodes);
        
        // 记录提取的股票信息（包含名称）
        if (stockInfos.length > 0) {
          console.log('提取的股票详情:', stockInfos.slice(0, 5)); // 只显示前5个避免日志过长
        }
        
        return stockCodes;
        
      } catch (error) {
        const handleResult = ErrorHandler.handleError(error, { context: 'extractStockListFromDOM_Enhanced' });
        console.error('增强版DOM提取失败，回退到基础提取:', handleResult.errorMessage);
        
        // 回退到基础提取方法
        return await fallbackExtractStockListFromDOM();
      }
    }

    /**
     * 回退的基础DOM提取方法
     */
    async function fallbackExtractStockListFromDOM(): Promise<string[]> {
      try {
        console.log('执行回退DOM提取...');
        
        const stockCodes: string[] = [];
        const processedCodes = new Set<string>();

        // 简化的提取策略
        const strategies = [
          // 股票链接
          () => {
            const links = document.querySelectorAll('a[href*="/stock/"]');
            links.forEach(link => {
              const href = link.getAttribute('href') || '';
              const match = href.match(/\/stock\/(\d{6})/);
              if (match && match[1] && !processedCodes.has(match[1])) {
                processedCodes.add(match[1]);
                stockCodes.push(match[1]);
              }
            });
          },
          
          // data属性
          () => {
            const elements = document.querySelectorAll('[data-code]');
            elements.forEach(element => {
              const code = element.getAttribute('data-code') || '';
              if (code.match(/^\d{6}$/) && !processedCodes.has(code)) {
                processedCodes.add(code);
                stockCodes.push(code);
              }
            });
          },
          
          // 文本匹配
          () => {
            const elements = document.querySelectorAll('.stock-code, .code, td, th');
            elements.forEach(element => {
              const text = element.textContent || '';
              const match = text.match(/\b(\d{6})\b/);
              if (match && match[1] && /^[0236]/.test(match[1]) && !processedCodes.has(match[1])) {
                processedCodes.add(match[1]);
                stockCodes.push(match[1]);
              }
            });
          }
        ];

        // 执行所有策略
        strategies.forEach((strategy, index) => {
          try {
            strategy();
          } catch (error) {
            ErrorHandler.handleError(error, { 
              context: 'fallbackExtractStockListFromDOM',
              strategyIndex: index 
            });
          }
        });

        console.log(`回退DOM提取完成，共找到 ${stockCodes.length} 个股票代码`);
        return stockCodes;
        
      } catch (error) {
        ErrorHandler.handleError(error, { context: 'fallbackExtractStockListFromDOM' });
        return [];
      }
    }

    /**
     * 通过API获取股票实时数据 - 使用增强版抓取器
     */
    async function fetchStockDataFromAPI(stockCodes: string[]): Promise<StockData[]> {
      if (stockCodes.length === 0) return [];

      try {
        console.log(`开始使用增强版抓取器获取 ${stockCodes.length} 个股票的数据...`);
        
        // 使用增强版数据抓取器获取股票数据
        const extractionResult = await EnhancedDataExtractor.fetchStockDataEnhanced(stockCodes, EXTRACTION_CONFIG);
        
        // 过滤出成功的结果并转换为StockData格式
        const successfulData: StockData[] = extractionResult.data.map((item: any) => {
            return {
              code: item.code,
              name: item.name || '',
              price: item.price || 0,
              change_amount: item.change_amount || 0,
              change_percent: item.change_percent || 0,
              volume: item.volume || 0,
              turnover: item.turnover || 0,
              high: item.high || 0,
              low: item.low || 0,
              open_price: item.open_price || 0,
              prev_close: item.prev_close || 0,
              timestamp: item.timestamp || new Date().toISOString()
            } as StockData;
          });
        
        const failedCount = stockCodes.length - successfulData.length;
        
        console.log(`增强版API获取完成: 成功 ${successfulData.length} 个，失败 ${failedCount} 个`);
        
        if (failedCount > 0) {
          console.warn('获取失败的股票代码数量:', failedCount);
          console.warn('错误信息:', extractionResult.errors);
          
          // 记录失败信息但不阻断流程
          ErrorHandler.handleError(new Error(`部分股票数据获取失败: ${failedCount}/${stockCodes.length}`), {
            context: 'fetchStockDataFromAPI_PartialFailure',
            errors: extractionResult.errors,
            failedCount,
            totalCount: stockCodes.length
          });
        }
        
        return successfulData;
        
      } catch (error) {
        const handleResult = ErrorHandler.handleError(error, {
          context: 'fetchStockDataFromAPI_Enhanced',
          stockCodes,
          stockCodesCount: stockCodes.length
        });
        
        console.error('增强版API获取失败，回退到基础方法:', handleResult.errorMessage);
        
        // 回退到基础API获取方法
        return await fallbackFetchStockDataFromAPI(stockCodes);
      }
    }

    /**
     * 回退的基础API获取方法
     */
    async function fallbackFetchStockDataFromAPI(stockCodes: string[]): Promise<StockData[]> {
      try {
        console.log(`执行回退API获取，股票数量: ${stockCodes.length}`);
        
        // 构建同花顺API请求URL
        const codeList = stockCodes.map(code => {
          // 判断市场：6开头为上海，0/3开头为深圳
          const market = code.startsWith('6') ? 'sh' : 'sz';
          return `${market}${code}`;
        }).join(',');

        const apiUrl = `http://d.10jqka.com.cn/v6/line/hs_${codeList}/01/last.js`;
        
        console.log('回退API请求URL:', apiUrl);

        // 使用fetch获取数据
        const response = await fetch(apiUrl, {
          method: 'GET',
          headers: {
            'Referer': 'http://stockpage.10jqka.com.cn/',
            'User-Agent': navigator.userAgent
          }
        });

        if (!response.ok) {
          const apiError = new Error(`API请求失败: ${response.status}`);
          (apiError as any).status = response.status;
          throw apiError;
        }

        const jsonpText = await response.text();
        const data = parseJSONP(jsonpText);

        if (!data || !data.data) {
          const parseError = new Error('API返回数据格式异常');
          parseError.name = 'ParseError';
          throw parseError;
        }

        // 解析股票数据
        const stockDataList: StockData[] = [];
        const timestamp = new Date().toISOString();

        Object.entries(data.data).forEach(([key, value]: [string, any]) => {
          try {
            const market = key.substring(0, 2);
            const code = key.substring(2);
            
            if (value && Array.isArray(value) && value.length >= 11) {
              const stockData: StockData = {
                code: code,
                name: value[0] || '',
                price: parseFloat(value[1]) || 0,
                change_amount: parseFloat(value[2]) || 0,
                change_percent: parseFloat(value[3]) || 0,
                volume: parseInt(value[4]) || 0,
                turnover: parseFloat(value[5]) || 0,
                high: parseFloat(value[6]) || 0,
                low: parseFloat(value[7]) || 0,
                open_price: parseFloat(value[8]) || 0,
                prev_close: parseFloat(value[9]) || 0,
                timestamp: timestamp
              };

              stockDataList.push(stockData);
            }
          } catch (error) {
            const handleResult = ErrorHandler.handleError(error, {
              context: 'parseStockData_Fallback',
              stockKey: key,
              stockValue: value
            });
            
            if (handleResult.logLevel === 'error') {
              console.error(`回退解析股票数据失败 ${key}:`, handleResult.errorMessage);
            } else {
              console.warn(`回退解析股票数据警告 ${key}:`, handleResult.errorMessage);
            }
          }
        });

        console.log(`回退API获取完成，成功解析 ${stockDataList.length} 条股票数据`);
        return stockDataList;

      } catch (error) {
        const handleResult = ErrorHandler.handleError(error, {
          context: 'fallbackFetchStockDataFromAPI',
          stockCodes,
          stockCodesCount: stockCodes.length
        });
        
        console.error('回退API获取失败:', handleResult.errorMessage);
        return [];
      }
    }

    /**
     * 发送数据到后端 - 使用增强重试机制
     */
    async function sendDataToBackend(stockDataList: StockData[]): Promise<boolean> {
      if (stockDataList.length === 0) return true;

      // 创建网络请求专用重试配置
      const retryConfig = RetryMechanism.createNetworkRetryConfig({
        maxRetries: 4,
        baseDelay: 800,
        maxDelay: 6000,
        backoffMultiplier: 1.6,
        onRetry: (error: any, attempt: number, delay: number) => {
          console.log(`数据发送重试: 第${attempt}次失败，${delay}ms后重试`);
          
          // 记录重试详情
          ErrorHandler.handleError(error, {
            context: 'sendDataToBackend_Retry',
            attempt,
            dataCount: stockDataList.length,
            errorMessage: error?.message
          });
        },
        onFinalFailure: (error: any, totalAttempts: number) => {
          console.error(`数据发送最终失败: 经过${totalAttempts}次尝试后仍然失败`);
          
          // 记录最终失败
          ErrorHandler.handleError(error, {
            context: 'sendDataToBackend_FinalFailure',
            totalAttempts,
            dataCount: stockDataList.length
          });
        }
      });

      // 使用重试机制执行发送操作
      const retryResult = await RetryMechanism.executeWithRetry(async () => {
        console.log(`发送 ${stockDataList.length} 条股票数据到后端...`);
        
        const response = await fetch(`${CONFIG.BACKEND_API}/stocks/data/batch`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            stock_data_list: stockDataList
          })
        });

        if (!response.ok) {
          const errorText = await response.text();
          const apiError = new Error(`后端API错误: ${errorText}`);
          (apiError as any).status = response.status;
          throw apiError;
        }

        return await response.json();
        
      }, retryConfig);

      if (retryResult.success) {
        console.log(`数据发送成功: ${stockDataList.length} 条数据，经过 ${retryResult.totalAttempts} 次尝试`);
        
        // 记录成功统计
        if (retryResult.totalAttempts > 1) {
          console.log('发送重试统计:', {
            totalAttempts: retryResult.totalAttempts,
            totalTime: retryResult.totalTime,
            dataCount: stockDataList.length
          });
        }
        
        return true;
      } else {
        console.error(`数据发送失败: ${retryResult.error?.message || '未知错误'}`);
        console.error('发送失败统计:', {
          totalAttempts: retryResult.totalAttempts,
          totalTime: retryResult.totalTime,
          dataCount: stockDataList.length,
          retryHistory: retryResult.retryHistory
        });
        
        return false;
      }
    }

    /**
     * 执行数据抓取 - 使用增强版数据抓取器、重试机制和状态管理
     */
    async function performDataFetch(): Promise<void> {
      // 开始新的运行
      const runId = monitoringStateManager.startNewRun();
      
      try {
        // 创建数据处理专用重试配置
        const retryConfig = RetryMechanism.createDataProcessingRetryConfig({
          maxRetries: 3,
          baseDelay: 1000,
          maxDelay: 5000,
          backoffMultiplier: 1.5,
          onRetry: (error: any, attempt: number, delay: number) => {
            console.log(`数据抓取重试: 第${attempt}次失败，${delay}ms后重试`);
            
            // 记录重试到状态管理器
            monitoringStateManager.incrementRetryCount();
            monitoringStateManager.addRunError(ErrorLevel.WARNING, `重试第${attempt}次: ${error?.message}`, {
              attempt,
              delay,
              errorType: error?.type
            });
            
            // 记录重试详情到错误处理器
            ErrorHandler.handleError(error, {
              context: 'performDataFetch_Retry',
              attempt,
              url: window.location.href,
              errorMessage: error?.message
            });
          },
          onFinalFailure: (error: any, totalAttempts: number) => {
            console.error(`数据抓取最终失败: 经过${totalAttempts}次尝试后仍然失败`);
            
            // 记录最终失败到状态管理器
            monitoringStateManager.addRunError(ErrorLevel.CRITICAL, `最终失败: ${error?.message}`, {
              totalAttempts,
              errorType: error?.type
            });
            
            // 记录最终失败到错误处理器
            ErrorHandler.handleError(error, {
              context: 'performDataFetch_FinalFailure',
              totalAttempts,
              url: window.location.href
            });
          }
        });

        // 使用重试机制执行数据抓取
        const retryResult = await RetryMechanism.executeWithRetry(async () => {
          const startTime = Date.now();
          
          console.log(`=== 开始执行增强版数据抓取 (运行ID: ${runId}) ===`);
          
          // 更新状态：等待DOM稳定
          monitoringStateManager.updateRunStatus(DataFetchStatus.EXTRACTING_CODES);
          
          // 1. 等待DOM稳定
          await EnhancedDataExtractor.waitForDOMStable(EXTRACTION_CONFIG.domStableWaitTime || 1000);
          
          // 2. 从DOM提取股票代码
          const stockCodes = await extractStockListFromDOM();
          
          // 更新进度
          monitoringStateManager.updateRunStatus(DataFetchStatus.EXTRACTING_CODES, {
            extractedCodes: stockCodes.length,
            totalExpected: stockCodes.length
          });
          
          if (stockCodes.length === 0) {
            const error = new Error('未找到股票代码');
            (error as any).type = ErrorType.PARSING;
            (error as any).severity = ErrorSeverity.MEDIUM;
            throw error;
          }

          console.log(`提取到 ${stockCodes.length} 个股票代码，开始获取数据...`);

          // 更新状态：获取股票数据
          monitoringStateManager.updateRunStatus(DataFetchStatus.FETCHING_DATA);

          // 3. 获取股票数据
          const stockDataList = await fetchStockDataFromAPI(stockCodes);
          
          // 更新进度
          monitoringStateManager.updateRunStatus(DataFetchStatus.FETCHING_DATA, {
            fetchedData: stockDataList.length
          });
          
          if (stockDataList.length === 0) {
            const error = new Error('未获取到股票数据');
            (error as any).type = ErrorType.API;
            (error as any).severity = ErrorSeverity.MEDIUM;
            throw error;
          }

          console.log(`获取到 ${stockDataList.length} 个股票数据，开始发送到后端...`);

          // 更新状态：发送数据
          monitoringStateManager.updateRunStatus(DataFetchStatus.SENDING_DATA);

          // 4. 发送数据到后端
          const success = await sendDataToBackend(stockDataList);
          
          if (!success) {
            const error = new Error('数据发送失败');
            (error as any).type = ErrorType.API;
            (error as any).severity = ErrorSeverity.HIGH;
            throw error;
          }
          
          // 更新进度
          monitoringStateManager.updateRunStatus(DataFetchStatus.SENDING_DATA, {
            sentData: stockDataList.length
          });
          
          const duration = Date.now() - startTime;
          
          return {
            stockCodes: stockCodes.length,
            stockData: stockDataList.length,
            dataSent: stockDataList.length,
            duration,
            success: true
          };
          
        }, retryConfig);

        if (retryResult.success) {
          console.log(`=== 增强版数据抓取完成: 经过 ${retryResult.totalAttempts} 次尝试，耗时: ${retryResult.totalTime}ms ===`);
          console.log('抓取结果:', retryResult.data);
          
          // 获取并更新缓存统计
          const cacheStats = EnhancedDataExtractor.getCacheStats();
          monitoringStateManager.updateCacheStats(cacheStats);
          if (cacheStats.size > 0) {
            console.log('缓存统计:', cacheStats);
          }
          
          // 完成运行 - 成功
          monitoringStateManager.completeRun(true, retryResult.data);
          
          // 记录成功统计
          const stats = ErrorHandler.getErrorStats();
          if (stats.total > 0) {
            console.log('错误统计:', {
              总错误数: stats.total,
              按类型: stats.byType,
              按严重级别: stats.bySeverity
            });
          }
          
          // 记录重试统计
          if (retryResult.totalAttempts > 1) {
            console.log('抓取重试统计:', {
              totalAttempts: retryResult.totalAttempts,
              totalTime: retryResult.totalTime,
              result: retryResult.data
            });
          }
          
        } else {
          console.error(`数据抓取失败: ${retryResult.error?.message || '未知错误'}`);
          console.error('抓取失败统计:', {
            totalAttempts: retryResult.totalAttempts,
            totalTime: retryResult.totalTime,
            retryHistory: retryResult.retryHistory
          });
          
          // 完成运行 - 失败
          monitoringStateManager.completeRun(false, {
            error: retryResult.error?.message,
            totalAttempts: retryResult.totalAttempts,
            totalTime: retryResult.totalTime
          });
          
          // 检查是否需要设置错误状态
          const healthStatus = monitoringStateManager.getHealthStatus();
          if (healthStatus.status === 'critical') {
            monitoringStateManager.setMonitoringStatus(MonitoringStatus.ERROR);
            console.error('系统健康状态严重，设置监控状态为错误');
          }
          
          // 如果是严重错误，可能需要停止监控
          const stats = ErrorHandler.getErrorStats();
          const recentErrors = stats.recent.filter(e => 
            e.timestamp > Date.now() - 60000 && // 最近1分钟
            (e.severity === ErrorSeverity.HIGH || e.severity === ErrorSeverity.CRITICAL)
          );
          
          if (recentErrors.length >= 3) {
            console.error('检测到连续严重错误，建议检查系统状态');
            ErrorHandler.handleError(new Error('连续严重错误检测'), {
              context: 'performDataFetch_ContinuousErrors',
              recentSevereErrorsCount: recentErrors.length,
              errorStats: stats
            });
          }
        }
        
      } catch (error) {
        // 处理意外错误
        console.error('数据抓取过程中发生意外错误:', error);
        
        monitoringStateManager.addRunError(ErrorLevel.CRITICAL, `意外错误: ${error instanceof Error ? error.message : '未知错误'}`, {
          stack: error instanceof Error ? error.stack : undefined
        });
        
        // 完成运行 - 失败
        monitoringStateManager.completeRun(false, {
          error: error instanceof Error ? error.message : '意外错误'
        });
        
        // 设置监控状态为错误
        monitoringStateManager.setMonitoringStatus(MonitoringStatus.ERROR);
      }
    }

    /**
     * 开始监控
     */
    function startMonitoring(): void {
      if (isMonitoring) {
        console.log('监控已在运行中');
        return;
      }

      console.log('开始股票数据监控...');
      
      // 设置监控状态为启动中
      monitoringStateManager.setMonitoringStatus(MonitoringStatus.STARTING);
      
      isMonitoring = true;
      
      // 设置监控状态为运行中
      monitoringStateManager.setMonitoringStatus(MonitoringStatus.RUNNING);

      // 立即执行一次
      performDataFetch();

      // 设置定时器
      monitoringInterval = setInterval(() => {
        performDataFetch();
      }, CONFIG.FETCH_INTERVAL);
    }

    /**
     * 停止监控
     */
    function stopMonitoring(): void {
      if (!isMonitoring) {
        console.log('监控未在运行');
        return;
      }

      console.log('停止同花顺数据监控...');
      
      // 设置监控状态为停止中
      monitoringStateManager.setMonitoringStatus(MonitoringStatus.STOPPING);
      
      isMonitoring = false;
      
      if (monitoringInterval) {
        clearInterval(monitoringInterval);
        monitoringInterval = null;
      }
      
      // 设置监控状态为已停止
      monitoringStateManager.setMonitoringStatus(MonitoringStatus.STOPPED);
      
      console.log('监控已停止');
    }

    /**
     * 状态同步功能
     */
    function syncStateToBackground(): void {
      try {
        const currentState = monitoringStateManager.getCurrentRun();
        const statistics = monitoringStateManager.getStatistics();
        const monitoringStatus = monitoringStateManager.getMonitoringStatus();
        
        const syncData: Partial<SyncStateData> = {
          monitoringStatus,
          currentRun: currentState,
          statistics,
          lastUpdate: Date.now(),
          url: window.location.href
        };
        
        // 发送状态更新到background script
        chrome.runtime.sendMessage({
          type: 'state_sync_update',
          data: syncData
        }).catch(error => {
          console.warn('状态同步失败:', error);
        });
      } catch (error) {
        console.error('状态同步过程中发生错误:', error);
      }
    }
    
    /**
     * 监听状态变更并同步
     */
    monitoringStateManager.addListener((event: StateChangeEvent) => {
      // 同步状态到background script
      syncStateToBackground();
    });
    
    // 定期同步状态（每30秒）
    setInterval(() => {
      syncStateToBackground();
    }, 30000);

    /**
     * 监听来自background script的消息
     */
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      try {
        console.log('收到消息:', message);

        switch (message.action || message.type) {
          case 'startMonitoring':
            try {
              startMonitoring();
              sendResponse({ success: true, message: '开始监控' });
            } catch (error) {
              const handleResult = ErrorHandler.handleError(error, { context: 'startMonitoring' });
              sendResponse({ success: false, message: handleResult.errorMessage });
            }
            break;

          case 'stopMonitoring':
            try {
              stopMonitoring();
              sendResponse({ success: true, message: '停止监控' });
            } catch (error) {
              const handleResult = ErrorHandler.handleError(error, { context: 'stopMonitoring' });
              sendResponse({ success: false, message: handleResult.errorMessage });
            }
            break;

          case 'getStatus':
            try {
              const stats = ErrorHandler.getErrorStats();
              const currentRun = monitoringStateManager.getCurrentRun();
              const statistics = monitoringStateManager.getStatistics();
              const healthStatus = monitoringStateManager.getHealthStatus();
              
              sendResponse({ 
                success: true, 
                isMonitoring: isMonitoring,
                monitoringStatus: monitoringStateManager.getMonitoringStatus(),
                currentRun,
                statistics,
                healthStatus,
                message: isMonitoring ? '监控中' : '已停止',
                errorStats: {
                  totalErrors: stats.total,
                  recentErrors: stats.recent.length,
                  errorsByType: stats.byType
                }
              });
            } catch (error) {
              const handleResult = ErrorHandler.handleError(error, { context: 'getStatus' });
              sendResponse({ success: false, message: handleResult.errorMessage });
            }
            break;

          case 'getRunHistory':
            try {
              const runHistory = monitoringStateManager.getRunHistory(message.limit || 20);
              sendResponse({
                success: true,
                data: runHistory
              });
            } catch (error) {
              const handleResult = ErrorHandler.handleError(error, { context: 'getRunHistory' });
              sendResponse({ success: false, message: handleResult.errorMessage });
            }
            break;

          case 'getDetailedStatus':
            try {
              const detailedStatus = monitoringStateManager.exportStateData();
              sendResponse({
                success: true,
                data: detailedStatus
              });
            } catch (error) {
              const handleResult = ErrorHandler.handleError(error, { context: 'getDetailedStatus' });
              sendResponse({ success: false, message: handleResult.errorMessage });
            }
            break;

          case 'resetStatistics':
            try {
              monitoringStateManager.resetStatistics();
              sendResponse({ success: true, message: '统计信息已重置' });
            } catch (error) {
              const handleResult = ErrorHandler.handleError(error, { context: 'resetStatistics' });
              sendResponse({ success: false, message: handleResult.errorMessage });
            }
            break;

          case 'fetchOnce':
            performDataFetch().then(() => {
              sendResponse({ success: true, message: '单次抓取完成' });
            }).catch(error => {
              const handleResult = ErrorHandler.handleError(error, { context: 'fetchOnce' });
              sendResponse({ success: false, message: handleResult.errorMessage });
            });
            return true; // 保持消息通道开放

          case 'getErrorStats':
            try {
              const stats = ErrorHandler.getErrorStats();
              sendResponse({ 
                success: true, 
                data: stats
              });
            } catch (error) {
              const handleResult = ErrorHandler.handleError(error, { context: 'getErrorStats' });
              sendResponse({ success: false, message: handleResult.errorMessage });
            }
            break;

          case 'clearErrorHistory':
            try {
              ErrorHandler.clearHistory();
              sendResponse({ success: true, message: '错误历史已清除' });
            } catch (error) {
              const handleResult = ErrorHandler.handleError(error, { context: 'clearErrorHistory' });
              sendResponse({ success: false, message: handleResult.errorMessage });
            }
            break;

          // 状态同步相关消息
          case 'state_sync_request':
            try {
              const currentState = monitoringStateManager.getCurrentRun();
              const statistics = monitoringStateManager.getStatistics();
              const monitoringStatus = monitoringStateManager.getMonitoringStatus();
              
              const syncData: Partial<SyncStateData> = {
                monitoringStatus,
                currentRun: currentState,
                statistics,
                lastUpdate: Date.now(),
                url: window.location.href
              };
              
              sendResponse({ success: true, data: syncData });
            } catch (error) {
              const handleResult = ErrorHandler.handleError(error, { context: 'state_sync_request' });
              sendResponse({ success: false, message: handleResult.errorMessage });
            }
            break;

          case 'state_sync_broadcast':
            try {
              // 处理来自其他标签页的状态广播
              const notification: StateChangeNotification = message.data;
              console.log('收到状态广播:', notification);
              
              // 可以在这里处理跨标签页的状态同步逻辑
              // 例如：如果其他标签页开始监控，可以显示提示信息
              
              sendResponse({ success: true });
            } catch (error) {
              console.warn('处理状态广播失败:', error);
              sendResponse({ success: false, message: '处理状态广播失败' });
            }
            break;

          default:
            sendResponse({ success: false, message: '未知操作' });
        }
      } catch (error) {
        const handleResult = ErrorHandler.handleError(error, { 
          context: 'messageListener',
          action: message?.action 
        });
        sendResponse({ success: false, message: handleResult.errorMessage });
      }
    });
    
    // 页面加载完成后立即同步一次状态
    syncStateToBackground();

    // 页面加载完成后自动开始监控（如果在股票相关页面）
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
          if (window.location.href.includes('stock') || 
              window.location.href.includes('quote') ||
              document.querySelector('[data-code]') ||
              document.querySelector('.stock-code')) {
            console.log('检测到股票页面，自动开始监控');
            startMonitoring();
          }
        }, 2000);
      });
    } else {
      setTimeout(() => {
        if (window.location.href.includes('stock') || 
            window.location.href.includes('quote') ||
            document.querySelector('[data-code]') ||
            document.querySelector('.stock-code')) {
          console.log('检测到股票页面，自动开始监控');
          startMonitoring();
        }
      }, 2000);
    }

    console.log('同花顺股票监控插件初始化完成');
  }
});