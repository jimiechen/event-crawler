/**
 * 增强版数据抓取器
 * 优化DOM解析和JSONP接口调用机制
 */

import { ErrorHandler, ErrorType, ErrorSeverity } from './error-handler';
import { TongHuaShunExtractor, StockInfo, StockData, StockDataResponse } from './tonghuashun-extractor';
import { RetryMechanism, RetryConfig } from './retry-mechanism';
import { 
  DataDeduplicationOptimizer, 
  DeduplicationConfig, 
  TimestampedStockInfo, 
  TimestampedStockData 
} from './data-deduplication-optimizer';

// 抓取配置接口
export interface ExtractionConfig {
  maxRetries: number;
  retryDelay: number;
  timeout: number;
  batchSize: number;
  enableCache: boolean;
  cacheExpiry: number; // 缓存过期时间（毫秒）
  enableParallelProcessing: boolean;
  maxConcurrentRequests: number;
  enableProgressCallback: boolean;
  progressCallback?: (progress: number, message: string) => void;
  // 去重配置
  enableAdvancedDeduplication: boolean;
  deduplicationConfig?: Partial<DeduplicationConfig>;
}

// 抓取结果接口
export interface ExtractionResult {
  success: boolean;
  data: StockData[];
  errors: string[];
  stats: {
    totalFound: number;
    totalProcessed: number;
    totalErrors: number;
    processingTime: number;
  };
}

// 缓存项接口
interface CacheItem {
  data: StockData[];
  timestamp: number;
  expiry: number;
}

/**
 * 增强版数据抓取器类
 */
export class EnhancedDataExtractor {
  private static readonly DEFAULT_CONFIG: ExtractionConfig = {
    maxRetries: 3,
    retryDelay: 1000,
    timeout: 10000,
    batchSize: 20,
    enableCache: true,
    cacheExpiry: 30000, // 30秒缓存
    enableParallelProcessing: false,
    maxConcurrentRequests: 3,
    enableProgressCallback: false,
    enableAdvancedDeduplication: true,
    deduplicationConfig: {
      timeWindowMs: 60000, // 1分钟时间窗口
      strategy: 'highest_quality'
    }
  };

  private static cache = new Map<string, CacheItem>();
  private static domObserver: MutationObserver | null = null;
  private static lastDOMChange = 0;

  /**
   * 智能DOM股票代码提取
   * 使用多种策略和启发式算法提高提取准确性
   */
  static async extractStockCodesFromDOM(config: Partial<ExtractionConfig> = {}): Promise<StockInfo[]> {
    const finalConfig = { ...this.DEFAULT_CONFIG, ...config };
    const startTime = Date.now();
    
    try {
      console.log('开始智能DOM股票代码提取...');
      
      // 等待DOM稳定
      await this.waitForDOMStable();
      
      const stockInfos: StockInfo[] = [];
      const processedCodes = new Set<string>();
      const errors: string[] = [];

      // 增强的提取策略
      const strategies = [
        // 策略1: 专业股票元素
        {
          name: 'professional_elements',
          selectors: [
            'a[href*="/stock/"]', 'a[href*="/guba/"]', 'a[href*="/company/"]',
            '.stock-item', '.stock-link', '.stock-name', '.stock-code',
            '[data-stock-code]', '[data-symbol]'
          ],
          extractor: (selectors: string[]) => this.extractFromProfessionalElements(selectors, 'professional_elements')
        },
        
        // 策略2: 表格数据
        {
          name: 'table_extraction',
          selectors: ['table', 'tbody', 'tr'],
          extractor: (selectors: string[]) => this.extractFromTables(selectors, 'tables')
        },
        
        // 策略3: 列表数据
        {
          name: 'list_extraction',
          selectors: ['ul', 'ol', 'li', '.list-item'],
          extractor: (selectors: string[]) => this.extractFromLists(selectors, 'lists')
        },
        
        // 策略4: 文本内容智能匹配
        {
          name: 'text_pattern_matching',
          selectors: ['div', 'span', 'p', 'td', 'th'],
          extractor: (selectors: string[]) => this.extractFromTextPatterns(selectors, 'text_patterns')
        }
      ];

      // 执行所有策略
      for (const strategy of strategies) {
        try {
          console.log(`执行策略: ${strategy.name}`);
          const strategyResults = await strategy.extractor(strategy.selectors);
          
          strategyResults.forEach(stockInfo => {
            if (!processedCodes.has(stockInfo.code)) {
              processedCodes.add(stockInfo.code);
              stockInfos.push(stockInfo);
            }
          });
          
          console.log(`策略 ${strategy.name} 提取到 ${strategyResults.length} 个股票`);
        } catch (error) {
          const errorMsg = `策略 ${strategy.name} 执行失败: ${error instanceof Error ? error.message : '未知错误'}`;
          errors.push(errorMsg);
          ErrorHandler.handleError(error, { 
            context: 'extractStockCodesFromDOM',
            strategy: strategy.name 
          });
        }
      }

      // 验证和清理结果
      let validStockInfos = this.validateAndCleanStockInfos(stockInfos);
      
      // 应用高级去重（如果启用）
      if (finalConfig.enableAdvancedDeduplication) {
        const timestampedInfos = validStockInfos.map(info => 
          DataDeduplicationOptimizer.createTimestampedStockInfo(info, 'dom_extraction')
        );
        
        const deduplicationResult = DataDeduplicationOptimizer.deduplicateStockInfos(
          timestampedInfos, 
          finalConfig.deduplicationConfig
        );
        
        validStockInfos = deduplicationResult.deduplicated.map(({ timestamp, source, qualityScore, ...info }) => info);
        
        console.log(`高级去重完成: ${deduplicationResult.duplicatesRemoved} 个重复项被移除, ${deduplicationResult.qualityImproved} 个项目质量提升`);
      }
      
      const processingTime = Date.now() - startTime;
      console.log(`DOM提取完成: 找到 ${validStockInfos.length} 个有效股票，耗时 ${processingTime}ms`);
      
      return validStockInfos;
      
    } catch (error) {
      ErrorHandler.handleError(error, { context: 'extractStockCodesFromDOM' });
      return [];
    }
  }

  /**
   * 增强的股票数据获取
   * 支持批量处理、缓存、重试和错误恢复
   */
  static async fetchStockDataEnhanced(
    stockCodes: string[], 
    config: Partial<ExtractionConfig> = {}
  ): Promise<ExtractionResult> {
    const finalConfig = { ...this.DEFAULT_CONFIG, ...config };
    const startTime = Date.now();
    const errors: string[] = [];
    let allStockData: StockData[] = [];

    try {
      console.log(`开始获取 ${stockCodes.length} 个股票的数据...`);
      
      // 清理和验证股票代码
      const validCodes = TongHuaShunExtractor.cleanStockCodes(stockCodes);
      if (validCodes.length === 0) {
        return {
          success: false,
          data: [],
          errors: ['没有有效的股票代码'],
          stats: {
            totalFound: 0,
            totalProcessed: 0,
            totalErrors: 1,
            processingTime: Date.now() - startTime
          }
        };
      }

      // 检查缓存
      const { cachedData, uncachedCodes } = this.checkCache(validCodes, finalConfig);
      allStockData.push(...cachedData);
      
      if (uncachedCodes.length > 0) {
        console.log(`从缓存获取 ${cachedData.length} 条数据，需要请求 ${uncachedCodes.length} 条数据`);
        
        // 分批处理
        const batches = this.createBatches(uncachedCodes, finalConfig.batchSize);
        
        for (let i = 0; i < batches.length; i++) {
          const batch = batches[i];
          console.log(`处理批次 ${i + 1}/${batches.length}: ${batch.length} 个股票`);
          
          try {
            const batchResult = await this.fetchBatchWithRetry(batch, finalConfig);
            if (batchResult.success) {
              allStockData.push(...batchResult.data);
              
              // 更新缓存
              if (finalConfig.enableCache) {
                this.updateCache(batchResult.data, finalConfig);
              }
            } else {
              errors.push(`批次 ${i + 1} 处理失败: ${batchResult.message || '未知错误'}`);
            }
          } catch (error) {
            const errorMsg = `批次 ${i + 1} 处理异常: ${error instanceof Error ? error.message : '未知错误'}`;
            errors.push(errorMsg);
            ErrorHandler.handleError(error, { 
              context: 'fetchStockDataEnhanced',
              batchIndex: i,
              batchSize: batch.length 
            });
          }
          
          // 批次间延迟，避免请求过于频繁
          if (i < batches.length - 1) {
            await this.delay(200);
          }
        }
      }

      // 应用高级去重（如果启用）
      if (finalConfig.enableAdvancedDeduplication && allStockData.length > 0) {
        const timestampedData = allStockData.map(data => 
          DataDeduplicationOptimizer.createTimestampedStockData(data, 'api_response')
        );
        
        const deduplicationResult = DataDeduplicationOptimizer.deduplicateStockData(
          timestampedData, 
          finalConfig.deduplicationConfig
        );
        
        allStockData = deduplicationResult.deduplicated.map(({ timestamp, source, qualityScore, ...data }) => data);
        
        console.log(`股票数据高级去重完成: ${deduplicationResult.duplicatesRemoved} 个重复项被移除, ${deduplicationResult.qualityImproved} 个项目质量提升`);
      }

      const processingTime = Date.now() - startTime;
      const stats = {
        totalFound: stockCodes.length,
        totalProcessed: allStockData.length,
        totalErrors: errors.length,
        processingTime
      };

      console.log(`数据获取完成:`, stats);
      
      return {
        success: errors.length === 0 || allStockData.length > 0,
        data: allStockData,
        errors,
        stats
      };
      
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : '未知错误';
      ErrorHandler.handleError(error, { context: 'fetchStockDataEnhanced' });
      
      return {
        success: false,
        data: allStockData,
        errors: [errorMsg, ...errors],
        stats: {
          totalFound: stockCodes.length,
          totalProcessed: allStockData.length,
          totalErrors: errors.length + 1,
          processingTime: Date.now() - startTime
        }
      };
    }
  }

  /**
   * 等待DOM稳定
   */
  private static async waitForDOMStable(timeout = 2000): Promise<void> {
    return new Promise((resolve) => {
      let timer: NodeJS.Timeout;
      
      const checkStable = () => {
        clearTimeout(timer);
        timer = setTimeout(() => {
          resolve();
        }, 100);
      };

      // 监听DOM变化
      if (this.domObserver) {
        this.domObserver.disconnect();
      }
      
      this.domObserver = new MutationObserver(() => {
        this.lastDOMChange = Date.now();
        checkStable();
      });

      this.domObserver.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: false
      });

      checkStable();
      
      // 超时保护
      setTimeout(() => {
        if (this.domObserver) {
          this.domObserver.disconnect();
          this.domObserver = null;
        }
        resolve();
      }, timeout);
    });
  }

  /**
   * 从专业股票元素中提取
   */
  private static extractFromProfessionalElements(selectors: string[], source: string = 'professional_elements'): StockInfo[] {
    const stockInfos: StockInfo[] = [];
    
    selectors.forEach(selector => {
      try {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
          const stockInfo = this.extractStockInfoFromElement(element);
          if (stockInfo) {
            stockInfos.push(stockInfo);
          }
        });
      } catch (error) {
        ErrorHandler.handleError(error, { 
          context: 'extractFromProfessionalElements',
          selector 
        });
      }
    });
    
    return stockInfos;
  }

  /**
   * 从表格中提取
   */
  private static extractFromTables(selectors: string[], source: string = 'tables'): StockInfo[] {
    const stockInfos: StockInfo[] = [];
    
    selectors.forEach(selector => {
      try {
        const tables = document.querySelectorAll(selector);
        tables.forEach(table => {
          const rows = table.querySelectorAll('tr');
          rows.forEach(row => {
            const cells = row.querySelectorAll('td, th');
            cells.forEach(cell => {
              const stockInfo = this.extractStockInfoFromElement(cell);
              if (stockInfo) {
                stockInfos.push(stockInfo);
              }
            });
          });
        });
      } catch (error) {
        ErrorHandler.handleError(error, { 
          context: 'extractFromTables',
          selector 
        });
      }
    });
    
    return stockInfos;
  }

  /**
   * 从列表中提取
   */
  private static extractFromLists(selectors: string[], source: string = 'lists'): StockInfo[] {
    const stockInfos: StockInfo[] = [];
    
    selectors.forEach(selector => {
      try {
        const lists = document.querySelectorAll(selector);
        lists.forEach(list => {
          const items = list.querySelectorAll('li, .item, .stock-item');
          items.forEach(item => {
            const stockInfo = this.extractStockInfoFromElement(item);
            if (stockInfo) {
              stockInfos.push(stockInfo);
            }
          });
        });
      } catch (error) {
        ErrorHandler.handleError(error, { 
          context: 'extractFromLists',
          selector 
        });
      }
    });
    
    return stockInfos;
  }

  /**
   * 从文本模式中提取
   */
  private static extractFromTextPatterns(selectors: string[], source: string = 'text_patterns'): StockInfo[] {
    const stockInfos: StockInfo[] = [];
    
    selectors.forEach(selector => {
      try {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
          const text = element.textContent || '';
          
          // 匹配股票代码模式
          const codeMatches = text.match(/\b(\d{6})\b/g);
          if (codeMatches) {
            codeMatches.forEach(code => {
              if (TongHuaShunExtractor.isValidStockCode(code)) {
                // 尝试提取股票名称
                const nameMatch = text.match(new RegExp(`${code}\\s*([\\u4e00-\\u9fa5]+)`));
                const name = nameMatch ? nameMatch[1].trim() : '';
                
                stockInfos.push({
                  code,
                  name,
                  market: TongHuaShunExtractor.getMarketFromCode(code)
                });
              }
            });
          }
        });
      } catch (error) {
        ErrorHandler.handleError(error, { 
          context: 'extractFromTextPatterns',
          selector 
        });
      }
    });
    
    return stockInfos;
  }

  /**
   * 从单个元素提取股票信息
   */
  private static extractStockInfoFromElement(element: Element): StockInfo | null {
    try {
      // 尝试从属性获取
      let code = element.getAttribute('data-code') ||
                element.getAttribute('data-stock-code') ||
                element.getAttribute('data-symbol') ||
                '';

      // 尝试从href获取
      if (!code) {
        const href = element.getAttribute('href') || '';
        const hrefMatch = href.match(/\/stock\/(\d{6})|\/(\d{6})/);
        if (hrefMatch) {
          code = hrefMatch[1] || hrefMatch[2];
        }
      }

      // 尝试从文本内容获取
      if (!code) {
        const text = element.textContent || '';
        const textMatch = text.match(/\b(\d{6})\b/);
        if (textMatch && TongHuaShunExtractor.isValidStockCode(textMatch[1])) {
          code = textMatch[1];
        }
      }

      if (!code || !TongHuaShunExtractor.isValidStockCode(code)) {
        return null;
      }

      // 尝试获取股票名称
      let name = '';
      const nameElement = element.querySelector('.name, .stock-name, .title') ||
                         element.closest('tr')?.querySelector('.name, .stock-name, .title');
      
      if (nameElement) {
        name = nameElement.textContent?.trim() || '';
      } else {
        // 从文本中提取名称
        const text = element.textContent || '';
        const nameMatch = text.match(new RegExp(`${code}\\s*([\\u4e00-\\u9fa5]+)`));
        if (nameMatch) {
          name = nameMatch[1].trim();
        }
      }

      return {
        code,
        name,
        market: TongHuaShunExtractor.getMarketFromCode(code)
      };
    } catch (error) {
      ErrorHandler.handleError(error, { context: 'extractStockInfoFromElement' });
      return null;
    }
  }

  /**
   * 验证和清理股票信息
   */
  private static validateAndCleanStockInfos(stockInfos: StockInfo[]): StockInfo[] {
    const validInfos: StockInfo[] = [];
    const seenCodes = new Set<string>();

    stockInfos.forEach(info => {
      if (TongHuaShunExtractor.isValidStockCode(info.code) && !seenCodes.has(info.code)) {
        seenCodes.add(info.code);
        validInfos.push({
          ...info,
          name: info.name.trim(),
          market: TongHuaShunExtractor.getMarketFromCode(info.code)
        });
      }
    });

    return validInfos;
  }

  /**
   * 检查缓存
   */
  private static checkCache(codes: string[], config: ExtractionConfig): {
    cachedData: StockData[];
    uncachedCodes: string[];
  } {
    if (!config.enableCache) {
      return { cachedData: [], uncachedCodes: codes };
    }

    const cachedData: StockData[] = [];
    const uncachedCodes: string[] = [];
    const now = Date.now();

    codes.forEach(code => {
      const cacheItem = this.cache.get(code);
      if (cacheItem && now < cacheItem.expiry) {
        cachedData.push(...cacheItem.data);
      } else {
        uncachedCodes.push(code);
        // 清理过期缓存
        if (cacheItem) {
          this.cache.delete(code);
        }
      }
    });

    return { cachedData, uncachedCodes };
  }

  /**
   * 更新缓存
   */
  private static updateCache(stockData: StockData[], config: ExtractionConfig): void {
    if (!config.enableCache) return;

    const now = Date.now();
    stockData.forEach(data => {
      this.cache.set(data.code, {
        data: [data],
        timestamp: now,
        expiry: now + config.cacheExpiry
      });
    });
  }

  /**
   * 创建批次
   */
  private static createBatches<T>(items: T[], batchSize: number): T[][] {
    const batches: T[][] = [];
    for (let i = 0; i < items.length; i += batchSize) {
      batches.push(items.slice(i, i + batchSize));
    }
    return batches;
  }

  /**
   * 带重试的批次获取 - 使用增强重试机制
   */
  private static async fetchBatchWithRetry(
    codes: string[], 
    config: ExtractionConfig
  ): Promise<StockDataResponse> {
    // 创建API专用重试配置
    const retryConfig = RetryMechanism.createAPIRetryConfig({
      maxRetries: config.maxRetries,
      baseDelay: config.retryDelay,
      maxDelay: config.timeout / 2, // 最大延迟不超过超时时间的一半
      onRetry: (error: any, attempt: number, delay: number) => {
        console.log(`股票数据获取重试: 批次[${codes.slice(0, 3).join(',')}...] 第${attempt}次失败，${delay}ms后重试`);
        ErrorHandler.handleError(error, {
          context: 'fetchBatchWithRetry',
          attempt,
          codes: codes.slice(0, 5), // 只记录前5个代码避免日志过长
          totalCodes: codes.length
        });
      },
      onFinalFailure: (error: any, totalAttempts: number) => {
        console.error(`股票数据获取最终失败: 批次[${codes.slice(0, 3).join(',')}...] 经过${totalAttempts}次尝试后失败`);
      }
    });

    // 使用重试机制执行操作
    const retryResult = await RetryMechanism.executeWithRetry(async () => {
      // 添加超时控制
      const result = await Promise.race([
        TongHuaShunExtractor.fetchStockRealTimeData(codes),
        this.timeoutPromise(config.timeout)
      ]);

      if (!result.success) {
        // 将API失败转换为错误以触发重试
        const error = new Error(result.message || '获取数据失败');
        (error as any).type = ErrorType.API;
        (error as any).severity = ErrorSeverity.MEDIUM;
        throw error;
      }

      return result;
    }, retryConfig);

    if (retryResult.success && retryResult.data) {
      // 记录成功的重试统计
      if (retryResult.totalAttempts > 1) {
        console.log(`股票数据获取成功: 批次[${codes.slice(0, 3).join(',')}...] 经过${retryResult.totalAttempts}次尝试成功`);
      }
      return retryResult.data;
    } else {
      // 返回失败结果
      const errorMessage = retryResult.error?.message || '重试次数耗尽';
      console.error(`股票数据获取失败: 批次[${codes.slice(0, 3).join(',')}...] ${errorMessage}`);
      
      return {
        success: false,
        data: [],
        message: errorMessage,
        retryHistory: retryResult.retryHistory
      };
    }
  }

  /**
   * 超时Promise
   */
  private static timeoutPromise(timeout: number): Promise<never> {
    return new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error(`请求超时 (${timeout}ms)`));
      }, timeout);
    });
  }

  /**
   * 延迟函数
   */
  private static delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 清理缓存
   */
  static clearCache(): void {
    this.cache.clear();
    console.log('数据缓存已清空');
  }

  /**
   * 获取缓存统计
   */
  static getCacheStats(): { size: number; items: string[] } {
    return {
      size: this.cache.size,
      items: Array.from(this.cache.keys())
    };
  }
}