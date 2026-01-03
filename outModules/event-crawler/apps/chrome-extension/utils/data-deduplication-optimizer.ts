/**
 * 数据去重优化器
 * 基于股票代码+时间戳的智能去重策略
 */

import { StockInfo, StockData } from './tonghuashun-extractor';

// 去重配置接口
export interface DeduplicationConfig {
  // 时间窗口内的去重策略
  timeWindowMs: number; // 时间窗口大小（毫秒）
  enableTimeBasedDedup: boolean; // 是否启用基于时间的去重
  
  // 数据质量评分权重
  qualityWeights: {
    hasName: number; // 有股票名称的权重
    hasMarket: number; // 有市场信息的权重
    nameLength: number; // 名称长度权重
    sourceReliability: number; // 数据源可靠性权重
  };
  
  // 缓存配置
  enablePersistentCache: boolean; // 是否启用持久化缓存
  maxCacheSize: number; // 最大缓存条目数
  cacheExpiryMs: number; // 缓存过期时间
  
  // 去重策略
  strategy: 'latest' | 'highest_quality' | 'merge'; // 去重策略
}

// 数据项接口（包含时间戳和质量评分）
export interface TimestampedStockInfo extends StockInfo {
  timestamp: number;
  source: string; // 数据来源
  qualityScore?: number; // 数据质量评分
}

export interface TimestampedStockData extends StockData {
  timestamp: number;
  source: string;
  qualityScore?: number;
}

// 去重结果接口
export interface DeduplicationResult<T> {
  deduplicated: T[];
  duplicatesRemoved: number;
  qualityImproved: number;
  processingTime: number;
  statistics: {
    totalInput: number;
    uniqueCodes: number;
    averageQualityScore: number;
    timeWindowGroups: number;
  };
}

// 缓存项接口
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiry: number;
  accessCount: number;
  lastAccess: number;
}

/**
 * 数据去重优化器类
 */
export class DataDeduplicationOptimizer {
  private static readonly DEFAULT_CONFIG: DeduplicationConfig = {
    timeWindowMs: 60000, // 1分钟时间窗口
    enableTimeBasedDedup: true,
    qualityWeights: {
      hasName: 0.3,
      hasMarket: 0.2,
      nameLength: 0.2,
      sourceReliability: 0.3
    },
    enablePersistentCache: true,
    maxCacheSize: 1000,
    cacheExpiryMs: 300000, // 5分钟缓存
    strategy: 'highest_quality'
  };

  // 持久化缓存
  private static cache = new Map<string, CacheEntry<TimestampedStockInfo | TimestampedStockData>>();
  
  // 数据源可靠性评分
  private static readonly SOURCE_RELIABILITY: Record<string, number> = {
    'professional_elements': 0.9,
    'tables': 0.8,
    'lists': 0.7,
    'text_patterns': 0.6,
    'api_response': 1.0,
    'cache': 0.5,
    'unknown': 0.3
  };

  /**
   * 去重股票信息
   */
  static deduplicateStockInfos(
    stockInfos: TimestampedStockInfo[], 
    config: Partial<DeduplicationConfig> = {}
  ): DeduplicationResult<TimestampedStockInfo> {
    const finalConfig = { ...this.DEFAULT_CONFIG, ...config };
    const startTime = Date.now();
    
    console.log(`开始去重 ${stockInfos.length} 个股票信息...`);
    
    // 添加质量评分
    const scoredInfos = stockInfos.map(info => ({
      ...info,
      qualityScore: this.calculateQualityScore(info, finalConfig)
    }));
    
    // 执行去重
    const result = this.performDeduplication(scoredInfos, finalConfig);
    
    const processingTime = Date.now() - startTime;
    
    console.log(`去重完成: ${result.deduplicated.length}/${stockInfos.length} 保留, 耗时 ${processingTime}ms`);
    
    return {
      ...result,
      processingTime,
      statistics: {
        totalInput: stockInfos.length,
        uniqueCodes: new Set(result.deduplicated.map(info => info.code)).size,
        averageQualityScore: result.deduplicated.reduce((sum, info) => sum + (info.qualityScore || 0), 0) / result.deduplicated.length,
        timeWindowGroups: this.countTimeWindowGroups(scoredInfos, finalConfig)
      }
    };
  }

  /**
   * 去重股票数据
   */
  static deduplicateStockData(
    stockData: TimestampedStockData[], 
    config: Partial<DeduplicationConfig> = {}
  ): DeduplicationResult<TimestampedStockData> {
    const finalConfig = { ...this.DEFAULT_CONFIG, ...config };
    const startTime = Date.now();
    
    console.log(`开始去重 ${stockData.length} 个股票数据...`);
    
    // 添加质量评分
    const scoredData = stockData.map(data => ({
      ...data,
      qualityScore: this.calculateDataQualityScore(data, finalConfig)
    }));
    
    // 执行去重
    const result = this.performDeduplication(scoredData, finalConfig);
    
    const processingTime = Date.now() - startTime;
    
    console.log(`去重完成: ${result.deduplicated.length}/${stockData.length} 保留, 耗时 ${processingTime}ms`);
    
    return {
      ...result,
      processingTime,
      statistics: {
        totalInput: stockData.length,
        uniqueCodes: new Set(result.deduplicated.map(data => data.code)).size,
        averageQualityScore: result.deduplicated.reduce((sum, data) => sum + (data.qualityScore || 0), 0) / result.deduplicated.length,
        timeWindowGroups: this.countTimeWindowGroups(scoredData, finalConfig)
      }
    };
  }

  /**
   * 执行去重逻辑
   */
  private static performDeduplication<T extends TimestampedStockInfo | TimestampedStockData>(
    items: T[], 
    config: DeduplicationConfig
  ): { deduplicated: T[]; duplicatesRemoved: number; qualityImproved: number } {
    const groups = new Map<string, T[]>();
    
    // 按股票代码分组
    items.forEach(item => {
      const key = item.code;
      if (!groups.has(key)) {
        groups.set(key, []);
      }
      groups.get(key)!.push(item);
    });
    
    const deduplicated: T[] = [];
    let duplicatesRemoved = 0;
    let qualityImproved = 0;
    
    // 处理每个分组
    groups.forEach((groupItems, code) => {
      if (groupItems.length === 1) {
        deduplicated.push(groupItems[0]);
        return;
      }
      
      duplicatesRemoved += groupItems.length - 1;
      
      // 应用时间窗口去重
      const timeWindowGroups = config.enableTimeBasedDedup 
        ? this.groupByTimeWindow(groupItems, config.timeWindowMs)
        : [groupItems];
      
      timeWindowGroups.forEach(windowGroup => {
        const selected = this.selectBestItem(windowGroup, config);
        if (selected) {
          // 检查是否有质量提升
          const originalQuality = windowGroup[0].qualityScore || 0;
          const selectedQuality = selected.qualityScore || 0;
          if (selectedQuality > originalQuality) {
            qualityImproved++;
          }
          
          deduplicated.push(selected);
        }
      });
    });
    
    return { deduplicated, duplicatesRemoved, qualityImproved };
  }

  /**
   * 按时间窗口分组
   */
  private static groupByTimeWindow<T extends { timestamp: number }>(
    items: T[], 
    windowMs: number
  ): T[][] {
    // 按时间戳排序
    const sorted = items.sort((a, b) => a.timestamp - b.timestamp);
    const groups: T[][] = [];
    let currentGroup: T[] = [];
    let windowStart = 0;
    
    sorted.forEach(item => {
      if (currentGroup.length === 0) {
        currentGroup = [item];
        windowStart = item.timestamp;
      } else if (item.timestamp - windowStart <= windowMs) {
        currentGroup.push(item);
      } else {
        groups.push(currentGroup);
        currentGroup = [item];
        windowStart = item.timestamp;
      }
    });
    
    if (currentGroup.length > 0) {
      groups.push(currentGroup);
    }
    
    return groups;
  }

  /**
   * 选择最佳项目
   */
  private static selectBestItem<T extends { timestamp: number; qualityScore?: number }>(
    items: T[], 
    config: DeduplicationConfig
  ): T | null {
    if (items.length === 0) return null;
    if (items.length === 1) return items[0];
    
    switch (config.strategy) {
      case 'latest':
        return items.reduce((latest, current) => 
          current.timestamp > latest.timestamp ? current : latest
        );
        
      case 'highest_quality':
        return items.reduce((best, current) => 
          (current.qualityScore || 0) > (best.qualityScore || 0) ? current : best
        );
        
      case 'merge':
        return this.mergeItems(items);
        
      default:
        return items[0];
    }
  }

  /**
   * 合并项目（保留最佳属性）
   */
  private static mergeItems<T extends TimestampedStockInfo | TimestampedStockData>(items: T[]): T {
    if (items.length === 1) return items[0];
    
    // 选择质量最高的作为基础
    const base = items.reduce((best, current) => 
      (current.qualityScore || 0) > (best.qualityScore || 0) ? current : best
    );
    
    // 合并属性
    const merged = { ...base };
    
    // 选择最新的时间戳
    merged.timestamp = Math.max(...items.map(item => item.timestamp));
    
    // 选择最好的名称（如果是StockInfo）
    if ('name' in merged) {
      const bestName = items
        .filter(item => 'name' in item && item.name && item.name.trim())
        .reduce((best, current) => {
          const currentName = (current as any).name;
          const bestName = (best as any).name;
          return currentName.length > bestName.length ? current : best;
        }, base);
      
      if ('name' in bestName) {
        (merged as any).name = (bestName as any).name;
      }
    }
    
    // 重新计算质量评分
    merged.qualityScore = Math.max(...items.map(item => item.qualityScore || 0));
    
    return merged;
  }

  /**
   * 计算股票信息质量评分
   */
  private static calculateQualityScore(
    info: TimestampedStockInfo, 
    config: DeduplicationConfig
  ): number {
    const weights = config.qualityWeights;
    let score = 0;
    
    // 有名称加分
    if (info.name && info.name.trim()) {
      score += weights.hasName;
      
      // 名称长度加分（合理长度范围）
      const nameLength = info.name.trim().length;
      if (nameLength >= 2 && nameLength <= 10) {
        score += weights.nameLength * (nameLength / 10);
      }
    }
    
    // 有市场信息加分
    if (info.market && info.market !== 'unknown') {
      score += weights.hasMarket;
    }
    
    // 数据源可靠性加分
    const sourceScore = this.SOURCE_RELIABILITY[info.source] || this.SOURCE_RELIABILITY['unknown'];
    score += weights.sourceReliability * sourceScore;
    
    return Math.min(score, 1.0); // 限制在0-1范围内
  }

  /**
   * 计算股票数据质量评分
   */
  private static calculateDataQualityScore(
    data: TimestampedStockData, 
    config: DeduplicationConfig
  ): number {
    const weights = config.qualityWeights;
    let score = 0;
    
    // 有名称加分
    if (data.name && data.name.trim()) {
      score += weights.hasName;
    }
    
    // 有价格数据加分
    if (data.price !== undefined && data.price > 0) {
      score += 0.3;
    }
    
    // 有涨跌幅数据加分
    if (data.change !== undefined) {
      score += 0.2;
    }
    
    // 数据源可靠性加分
    const sourceScore = this.SOURCE_RELIABILITY[data.source] || this.SOURCE_RELIABILITY['unknown'];
    score += weights.sourceReliability * sourceScore;
    
    return Math.min(score, 1.0);
  }

  /**
   * 计算时间窗口分组数量
   */
  private static countTimeWindowGroups<T extends { timestamp: number; code: string }>(
    items: T[], 
    config: DeduplicationConfig
  ): number {
    if (!config.enableTimeBasedDedup) return 0;
    
    const codeGroups = new Map<string, T[]>();
    items.forEach(item => {
      if (!codeGroups.has(item.code)) {
        codeGroups.set(item.code, []);
      }
      codeGroups.get(item.code)!.push(item);
    });
    
    let totalGroups = 0;
    codeGroups.forEach(groupItems => {
      const timeGroups = this.groupByTimeWindow(groupItems, config.timeWindowMs);
      totalGroups += timeGroups.length;
    });
    
    return totalGroups;
  }

  /**
   * 缓存管理
   */
  static addToCache<T extends TimestampedStockInfo | TimestampedStockData>(
    key: string, 
    data: T, 
    config: Partial<DeduplicationConfig> = {}
  ): void {
    const finalConfig = { ...this.DEFAULT_CONFIG, ...config };
    
    if (!finalConfig.enablePersistentCache) return;
    
    // 检查缓存大小限制
    if (this.cache.size >= finalConfig.maxCacheSize) {
      this.evictOldestEntries(Math.floor(finalConfig.maxCacheSize * 0.1)); // 清理10%
    }
    
    const now = Date.now();
    this.cache.set(key, {
      data,
      timestamp: now,
      expiry: now + finalConfig.cacheExpiryMs,
      accessCount: 1,
      lastAccess: now
    });
  }

  /**
   * 从缓存获取
   */
  static getFromCache<T extends TimestampedStockInfo | TimestampedStockData>(
    key: string
  ): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;
    
    const now = Date.now();
    if (now > entry.expiry) {
      this.cache.delete(key);
      return null;
    }
    
    // 更新访问统计
    entry.accessCount++;
    entry.lastAccess = now;
    
    return entry.data as T;
  }

  /**
   * 清理过期缓存条目
   */
  private static evictOldestEntries(count: number): void {
    const entries = Array.from(this.cache.entries())
      .sort(([, a], [, b]) => a.lastAccess - b.lastAccess);
    
    for (let i = 0; i < Math.min(count, entries.length); i++) {
      this.cache.delete(entries[i][0]);
    }
    
    console.log(`清理了 ${Math.min(count, entries.length)} 个缓存条目`);
  }

  /**
   * 获取缓存统计
   */
  static getCacheStats(): {
    size: number;
    maxSize: number;
    hitRate: number;
    averageAge: number;
  } {
    const now = Date.now();
    let totalAccess = 0;
    let totalAge = 0;
    
    this.cache.forEach(entry => {
      totalAccess += entry.accessCount;
      totalAge += now - entry.timestamp;
    });
    
    return {
      size: this.cache.size,
      maxSize: this.DEFAULT_CONFIG.maxCacheSize,
      hitRate: this.cache.size > 0 ? totalAccess / this.cache.size : 0,
      averageAge: this.cache.size > 0 ? totalAge / this.cache.size : 0
    };
  }

  /**
   * 清空缓存
   */
  static clearCache(): void {
    this.cache.clear();
    console.log('去重缓存已清空');
  }

  /**
   * 创建带时间戳的股票信息
   */
  static createTimestampedStockInfo(
    stockInfo: StockInfo, 
    source: string, 
    timestamp?: number
  ): TimestampedStockInfo {
    return {
      ...stockInfo,
      timestamp: timestamp || Date.now(),
      source
    };
  }

  /**
   * 创建带时间戳的股票数据
   */
  static createTimestampedStockData(
    stockData: StockData, 
    source: string, 
    timestamp?: number
  ): TimestampedStockData {
    return {
      ...stockData,
      timestamp: timestamp || Date.now(),
      source
    };
  }
}