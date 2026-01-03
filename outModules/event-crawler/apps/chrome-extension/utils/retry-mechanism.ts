/**
 * 重试机制工具类
 * 实现指数退避重试算法，支持多种重试策略
 */

import { ErrorHandler, ErrorType, ErrorSeverity } from './error-handler';

/**
 * 重试配置接口
 */
export interface RetryConfig {
  /** 最大重试次数 */
  maxRetries: number;
  /** 基础延迟时间（毫秒） */
  baseDelay: number;
  /** 最大延迟时间（毫秒） */
  maxDelay: number;
  /** 退避倍数 */
  backoffMultiplier: number;
  /** 是否启用抖动 */
  enableJitter: boolean;
  /** 抖动范围（0-1） */
  jitterRange: number;
  /** 重试条件函数 */
  shouldRetry?: (error: any, attempt: number) => boolean;
  /** 重试前回调 */
  onRetry?: (error: any, attempt: number, delay: number) => void;
  /** 最终失败回调 */
  onFinalFailure?: (error: any, totalAttempts: number) => void;
}

/**
 * 重试结果接口
 */
export interface RetryResult<T> {
  /** 是否成功 */
  success: boolean;
  /** 结果数据 */
  data?: T;
  /** 错误信息 */
  error?: Error;
  /** 总尝试次数 */
  totalAttempts: number;
  /** 总耗时（毫秒） */
  totalTime: number;
  /** 重试历史 */
  retryHistory: RetryAttempt[];
}

/**
 * 重试尝试记录
 */
export interface RetryAttempt {
  /** 尝试次数 */
  attempt: number;
  /** 开始时间 */
  startTime: number;
  /** 结束时间 */
  endTime: number;
  /** 是否成功 */
  success: boolean;
  /** 错误信息 */
  error?: string;
  /** 延迟时间 */
  delay?: number;
}

/**
 * 重试机制类
 */
export class RetryMechanism {
  /** 默认配置 */
  private static readonly DEFAULT_CONFIG: RetryConfig = {
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: 30000,
    backoffMultiplier: 2,
    enableJitter: true,
    jitterRange: 0.1,
    shouldRetry: (error: any, attempt: number) => {
      // 默认重试条件：网络错误、超时错误、5xx服务器错误
      if (error?.type === ErrorType.NETWORK || 
          error?.type === ErrorType.TIMEOUT ||
          (error?.statusCode && error.statusCode >= 500)) {
        return true;
      }
      
      // 对于其他错误，只在前2次尝试时重试
      return attempt <= 2;
    }
  };

  /**
   * 执行带重试的异步操作
   */
  static async executeWithRetry<T>(
    operation: () => Promise<T>,
    config: Partial<RetryConfig> = {}
  ): Promise<RetryResult<T>> {
    const finalConfig = { ...this.DEFAULT_CONFIG, ...config };
    const retryHistory: RetryAttempt[] = [];
    const startTime = Date.now();
    
    let lastError: Error | null = null;
    let attempt = 0;

    while (attempt <= finalConfig.maxRetries) {
      const attemptStartTime = Date.now();
      
      try {
        console.log(`执行操作，尝试次数: ${attempt + 1}/${finalConfig.maxRetries + 1}`);
        
        const result = await operation();
        
        const attemptEndTime = Date.now();
        retryHistory.push({
          attempt: attempt + 1,
          startTime: attemptStartTime,
          endTime: attemptEndTime,
          success: true
        });

        // 成功，返回结果
        return {
          success: true,
          data: result,
          totalAttempts: attempt + 1,
          totalTime: Date.now() - startTime,
          retryHistory
        };
        
      } catch (error) {
        const attemptEndTime = Date.now();
        lastError = error instanceof Error ? error : new Error(String(error));
        
        retryHistory.push({
          attempt: attempt + 1,
          startTime: attemptStartTime,
          endTime: attemptEndTime,
          success: false,
          error: lastError.message
        });

        // 记录错误
        ErrorHandler.handleError(lastError, {
          context: 'RetryMechanism.executeWithRetry',
          attempt: attempt + 1,
          maxRetries: finalConfig.maxRetries
        });

        // 检查是否应该重试
        if (attempt >= finalConfig.maxRetries || 
            (finalConfig.shouldRetry && !finalConfig.shouldRetry(lastError, attempt + 1))) {
          break;
        }

        // 计算延迟时间
        const delay = this.calculateDelay(attempt, finalConfig);
        retryHistory[retryHistory.length - 1].delay = delay;

        // 调用重试前回调
        if (finalConfig.onRetry) {
          finalConfig.onRetry(lastError, attempt + 1, delay);
        }

        console.log(`操作失败，${delay}ms 后进行第 ${attempt + 2} 次尝试...`);
        
        // 等待延迟
        await this.delay(delay);
        
        attempt++;
      }
    }

    // 所有重试都失败了
    if (finalConfig.onFinalFailure && lastError) {
      finalConfig.onFinalFailure(lastError, attempt);
    }

    ErrorHandler.handleError(lastError || new Error('重试机制失败'), {
      context: 'RetryMechanism.executeWithRetry.FinalFailure',
      totalAttempts: attempt,
      maxRetries: finalConfig.maxRetries
    });

    return {
      success: false,
      error: lastError || new Error('重试机制失败'),
      totalAttempts: attempt,
      totalTime: Date.now() - startTime,
      retryHistory
    };
  }

  /**
   * 批量执行带重试的操作
   */
  static async executeBatchWithRetry<T, R>(
    items: T[],
    operation: (item: T) => Promise<R>,
    config: Partial<RetryConfig> = {},
    batchSize = 5
  ): Promise<{
    successful: Array<{ item: T; result: R; attempts: number }>;
    failed: Array<{ item: T; error: Error; attempts: number }>;
    totalTime: number;
  }> {
    const startTime = Date.now();
    const successful: Array<{ item: T; result: R; attempts: number }> = [];
    const failed: Array<{ item: T; error: Error; attempts: number }> = [];

    // 分批处理
    const batches = this.createBatches(items, batchSize);
    
    for (let batchIndex = 0; batchIndex < batches.length; batchIndex++) {
      const batch = batches[batchIndex];
      
      console.log(`处理批次 ${batchIndex + 1}/${batches.length}，包含 ${batch.length} 个项目`);
      
      // 并行处理批次内的项目
      const batchPromises = batch.map(async (item) => {
        const result = await this.executeWithRetry(
          () => operation(item),
          config
        );
        
        if (result.success && result.data !== undefined) {
          successful.push({
            item,
            result: result.data,
            attempts: result.totalAttempts
          });
        } else {
          failed.push({
            item,
            error: result.error || new Error('未知错误'),
            attempts: result.totalAttempts
          });
        }
      });

      await Promise.all(batchPromises);
      
      // 批次间延迟
      if (batchIndex < batches.length - 1) {
        await this.delay(200);
      }
    }

    const totalTime = Date.now() - startTime;
    
    console.log(`批量操作完成: 成功 ${successful.length}，失败 ${failed.length}，耗时 ${totalTime}ms`);
    
    return {
      successful,
      failed,
      totalTime
    };
  }

  /**
   * 计算指数退避延迟时间
   */
  private static calculateDelay(attempt: number, config: RetryConfig): number {
    // 基础指数退避
    let delay = config.baseDelay * Math.pow(config.backoffMultiplier, attempt);
    
    // 限制最大延迟
    delay = Math.min(delay, config.maxDelay);
    
    // 添加抖动
    if (config.enableJitter) {
      const jitter = delay * config.jitterRange * (Math.random() * 2 - 1);
      delay += jitter;
    }
    
    // 确保延迟为正数
    return Math.max(delay, 0);
  }

  /**
   * 延迟函数
   */
  private static delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
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
   * 创建网络请求专用的重试配置
   */
  static createNetworkRetryConfig(options: Partial<RetryConfig> = {}): RetryConfig {
    return {
      ...this.DEFAULT_CONFIG,
      maxRetries: 5,
      baseDelay: 500,
      maxDelay: 10000,
      backoffMultiplier: 1.5,
      shouldRetry: (error: any, attempt: number) => {
        // 网络错误总是重试
        if (error?.type === ErrorType.NETWORK || 
            error?.type === ErrorType.TIMEOUT) {
          return true;
        }
        
        // 5xx 服务器错误重试
        if (error?.statusCode && error.statusCode >= 500) {
          return true;
        }
        
        // 429 限流错误重试
        if (error?.statusCode === 429) {
          return true;
        }
        
        // 其他错误不重试
        return false;
      },
      onRetry: (error: any, attempt: number, delay: number) => {
        console.log(`网络请求重试: 第${attempt}次尝试失败 (${error?.message || '未知错误'})，${delay}ms后重试`);
      },
      ...options
    };
  }

  /**
   * 创建API请求专用的重试配置
   */
  static createAPIRetryConfig(options: Partial<RetryConfig> = {}): RetryConfig {
    return {
      ...this.DEFAULT_CONFIG,
      maxRetries: 3,
      baseDelay: 1000,
      maxDelay: 8000,
      backoffMultiplier: 2,
      shouldRetry: (error: any, attempt: number) => {
        // API错误根据状态码判断
        if (error?.statusCode) {
          // 4xx 客户端错误通常不重试（除了429）
          if (error.statusCode >= 400 && error.statusCode < 500) {
            return error.statusCode === 429; // 只重试限流错误
          }
          
          // 5xx 服务器错误重试
          if (error.statusCode >= 500) {
            return true;
          }
        }
        
        // 网络和超时错误重试
        return error?.type === ErrorType.NETWORK || error?.type === ErrorType.TIMEOUT;
      },
      onRetry: (error: any, attempt: number, delay: number) => {
        console.log(`API请求重试: 第${attempt}次尝试失败 (状态码: ${error?.statusCode || 'N/A'})，${delay}ms后重试`);
      },
      ...options
    };
  }

  /**
   * 创建数据处理专用的重试配置
   */
  static createDataProcessingRetryConfig(options: Partial<RetryConfig> = {}): RetryConfig {
    return {
      ...this.DEFAULT_CONFIG,
      maxRetries: 2,
      baseDelay: 500,
      maxDelay: 2000,
      backoffMultiplier: 2,
      enableJitter: false, // 数据处理不需要抖动
      shouldRetry: (error: any, attempt: number) => {
        // 只重试临时性错误
        return error?.type === ErrorType.TEMPORARY || 
               error?.type === ErrorType.NETWORK ||
               attempt <= 1; // 最多重试1次
      },
      onRetry: (error: any, attempt: number, delay: number) => {
        console.log(`数据处理重试: 第${attempt}次尝试失败，${delay}ms后重试`);
      },
      ...options
    };
  }
}