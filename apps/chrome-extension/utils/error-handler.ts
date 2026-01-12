/**
 * 错误处理工具类
 * 提供分类错误处理和统一的错误管理机制
 */

// 错误类型枚举
export enum ErrorType {
  NETWORK = 'NETWORK',
  API = 'API', 
  PARSING = 'PARSING',
  SYSTEM = 'SYSTEM',
  DOM = 'DOM',
  TIMEOUT = 'TIMEOUT',
  VALIDATION = 'VALIDATION',
  TEMPORARY = 'TEMPORARY'
}

// 错误严重级别
export enum ErrorSeverity {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

// 错误信息接口
export interface ErrorInfo {
  type: ErrorType;
  severity: ErrorSeverity;
  message: string;
  originalError?: Error;
  context?: any;
  timestamp: number;
  retryable: boolean;
  retryCount?: number;
  maxRetries?: number;
}

// 错误处理结果
export interface ErrorHandleResult {
  shouldRetry: boolean;
  retryDelay: number;
  errorMessage: string;
  logLevel: 'error' | 'warn' | 'info';
}

/**
 * 错误处理器类
 */
export class ErrorHandler {
  private static errorHistory: ErrorInfo[] = [];
  private static readonly MAX_ERROR_HISTORY = 100;

  /**
   * 处理错误
   */
  static handleError(error: Error | any, context?: any): ErrorHandleResult {
    const errorInfo = this.classifyError(error, context);
    this.logError(errorInfo);
    this.addToHistory(errorInfo);
    
    return this.getHandleStrategy(errorInfo);
  }

  /**
   * 分类错误
   */
  private static classifyError(error: Error | any, context?: any): ErrorInfo {
    const timestamp = Date.now();
    let type: ErrorType;
    let severity: ErrorSeverity;
    let retryable = false;
    let message = '';

    // 根据错误特征进行分类
    if (error instanceof TypeError && error.message.includes('fetch')) {
      // 网络错误
      type = ErrorType.NETWORK;
      severity = ErrorSeverity.MEDIUM;
      retryable = true;
      message = '网络连接失败';
    } else if (error instanceof Error && error.message.includes('timeout')) {
      // 超时错误
      type = ErrorType.TIMEOUT;
      severity = ErrorSeverity.MEDIUM;
      retryable = true;
      message = '请求超时';
    } else if (error?.status >= 400 && error?.status < 500) {
      // API客户端错误
      type = ErrorType.API;
      severity = error.status === 401 || error.status === 403 ? ErrorSeverity.HIGH : ErrorSeverity.MEDIUM;
      retryable = error.status === 429; // 只有限流错误可重试
      message = `API错误 (${error.status})`;
    } else if (error?.status >= 500) {
      // API服务器错误
      type = ErrorType.API;
      severity = ErrorSeverity.HIGH;
      retryable = true;
      message = `服务器错误 (${error.status})`;
    } else if (error instanceof SyntaxError || error?.message?.includes('JSON')) {
      // 解析错误
      type = ErrorType.PARSING;
      severity = ErrorSeverity.MEDIUM;
      retryable = false;
      message = '数据解析失败';
    } else if (error?.message?.includes('DOM') || error?.message?.includes('querySelector')) {
      // DOM错误
      type = ErrorType.DOM;
      severity = ErrorSeverity.LOW;
      retryable = true;
      message = 'DOM元素访问失败';
    } else {
      // 系统错误
      type = ErrorType.SYSTEM;
      severity = ErrorSeverity.HIGH;
      retryable = false;
      message = '系统异常';
    }

    return {
      type,
      severity,
      message,
      originalError: error instanceof Error ? error : new Error(String(error)),
      context,
      timestamp,
      retryable,
      retryCount: context?.retryCount || 0,
      maxRetries: context?.maxRetries || 3
    };
  }

  /**
   * 获取处理策略
   */
  private static getHandleStrategy(errorInfo: ErrorInfo): ErrorHandleResult {
    const { type, severity, retryable, retryCount = 0, maxRetries = 3 } = errorInfo;
    
    let shouldRetry = false;
    let retryDelay = 1000; // 默认1秒
    let logLevel: 'error' | 'warn' | 'info' = 'error';

    if (retryable && retryCount < maxRetries) {
      shouldRetry = true;
      
      // 根据错误类型设置重试延迟
      switch (type) {
        case ErrorType.NETWORK:
          retryDelay = Math.min(1000 * Math.pow(2, retryCount), 10000); // 指数退避，最大10秒
          break;
        case ErrorType.API:
          retryDelay = Math.min(2000 * Math.pow(2, retryCount), 30000); // 指数退避，最大30秒
          break;
        case ErrorType.TIMEOUT:
          retryDelay = Math.min(3000 * Math.pow(2, retryCount), 15000); // 指数退避，最大15秒
          break;
        case ErrorType.DOM:
          retryDelay = 2000; // DOM错误固定2秒重试
          break;
        default:
          retryDelay = 1000;
      }
    }

    // 根据严重级别设置日志级别
    switch (severity) {
      case ErrorSeverity.LOW:
        logLevel = 'info';
        break;
      case ErrorSeverity.MEDIUM:
        logLevel = 'warn';
        break;
      case ErrorSeverity.HIGH:
      case ErrorSeverity.CRITICAL:
        logLevel = 'error';
        break;
    }

    return {
      shouldRetry,
      retryDelay,
      errorMessage: errorInfo.message,
      logLevel
    };
  }

  /**
   * 记录错误日志
   */
  private static logError(errorInfo: ErrorInfo): void {
    const { type, severity, message, originalError, context, timestamp } = errorInfo;
    const timeStr = new Date(timestamp).toISOString();
    
    const logMessage = `[${timeStr}] [${type}] [${severity}] ${message}`;
    const logDetails = {
      error: originalError?.message,
      stack: originalError?.stack,
      context
    };

    switch (severity) {
      case ErrorSeverity.LOW:
        console.info(logMessage, logDetails);
        break;
      case ErrorSeverity.MEDIUM:
        console.warn(logMessage, logDetails);
        break;
      case ErrorSeverity.HIGH:
      case ErrorSeverity.CRITICAL:
        console.error(logMessage, logDetails);
        break;
    }
  }

  /**
   * 添加到错误历史
   */
  private static addToHistory(errorInfo: ErrorInfo): void {
    this.errorHistory.push(errorInfo);
    
    // 保持历史记录数量限制
    if (this.errorHistory.length > this.MAX_ERROR_HISTORY) {
      this.errorHistory.shift();
    }
  }

  /**
   * 获取错误统计
   */
  static getErrorStats(): {
    total: number;
    byType: Record<ErrorType, number>;
    bySeverity: Record<ErrorSeverity, number>;
    recent: ErrorInfo[];
  } {
    const byType = {} as Record<ErrorType, number>;
    const bySeverity = {} as Record<ErrorSeverity, number>;

    // 初始化计数器
    Object.values(ErrorType).forEach(type => byType[type] = 0);
    Object.values(ErrorSeverity).forEach(severity => bySeverity[severity] = 0);

    // 统计错误
    this.errorHistory.forEach(error => {
      byType[error.type]++;
      bySeverity[error.severity]++;
    });

    // 获取最近10条错误
    const recent = this.errorHistory.slice(-10);

    return {
      total: this.errorHistory.length,
      byType,
      bySeverity,
      recent
    };
  }

  /**
   * 清除错误历史
   */
  static clearHistory(): void {
    this.errorHistory = [];
  }

  /**
   * 检查是否应该停止重试
   */
  static shouldStopRetrying(errorType: ErrorType, consecutiveErrors: number): boolean {
    switch (errorType) {
      case ErrorType.NETWORK:
        return consecutiveErrors >= 5; // 网络错误最多重试5次
      case ErrorType.API:
        return consecutiveErrors >= 3; // API错误最多重试3次
      case ErrorType.PARSING:
        return true; // 解析错误不重试
      case ErrorType.DOM:
        return consecutiveErrors >= 10; // DOM错误可以多重试几次
      case ErrorType.SYSTEM:
        return consecutiveErrors >= 2; // 系统错误最多重试2次
      case ErrorType.TIMEOUT:
        return consecutiveErrors >= 4; // 超时错误最多重试4次
      default:
        return consecutiveErrors >= 3;
    }
  }
}

/**
 * 错误处理装饰器
 */
export function withErrorHandling<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  context?: any
): T {
  return (async (...args: any[]) => {
    try {
      return await fn(...args);
    } catch (error) {
      const result = ErrorHandler.handleError(error, { ...context, functionName: fn.name });
      
      if (result.shouldRetry) {
        // 可以在这里实现自动重试逻辑
        console.log(`函数 ${fn.name} 将在 ${result.retryDelay}ms 后重试`);
      }
      
      throw error; // 重新抛出错误，让调用者决定如何处理
    }
  }) as T;
}