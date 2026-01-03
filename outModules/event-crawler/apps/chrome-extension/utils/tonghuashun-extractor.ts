/**
 * 同花顺数据提取工具
 * 专门用于解析同花顺网站的各种数据格式
 */

// 股票数据接口定义
export interface StockInfo {
  code: string;
  name: string;
  market: 'sh' | 'sz' | 'unknown';
}

export interface StockData {
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

export interface StockListResponse {
  success: boolean;
  data: StockInfo[];
  message?: string;
}

export interface StockDataResponse {
  success: boolean;
  data: StockData[];
  message?: string;
}

/**
 * 同花顺数据提取器类
 */
export class TongHuaShunExtractor {
  private static readonly API_BASE = 'http://d.10jqka.com.cn';
  private static readonly QUOTE_API = 'http://q.10jqka.com.cn';
  
  /**
   * 解析JSONP响应
   */
  static parseJSONP(jsonpString: string): any {
    try {
      // 常见的JSONP包装模式
      const patterns = [
        /^[^(]*\((.*)\)[^)]*$/,  // callback(data)
        /^[^{]*(\{.*\})[^}]*$/,  // 直接JSON
        /^[^[]*(\[.*\])[^]]*$/   // 直接数组
      ];

      for (const pattern of patterns) {
        const match = jsonpString.match(pattern);
        if (match && match[1]) {
          return JSON.parse(match[1]);
        }
      }

      // 尝试直接解析
      return JSON.parse(jsonpString);
    } catch (error) {
      console.error('JSONP解析失败:', error, 'Original:', jsonpString.substring(0, 200));
      return null;
    }
  }

  /**
   * 从页面URL判断市场类型
   */
  static getMarketFromCode(code: string): 'sh' | 'sz' | 'unknown' {
    if (!code || code.length !== 6) return 'unknown';
    
    // 上海证券交易所：6开头
    if (code.startsWith('6')) return 'sh';
    
    // 深圳证券交易所：0、2、3开头
    if (code.startsWith('0') || code.startsWith('2') || code.startsWith('3')) return 'sz';
    
    return 'unknown';
  }

  /**
   * 从页面DOM中提取股票代码列表
   */
  static extractStockCodesFromDOM(): StockInfo[] {
    const stockInfos: StockInfo[] = [];
    const processedCodes = new Set<string>();

    try {
      // 多种选择器策略
      const strategies = [
        // 策略1: 从链接href中提取
        {
          selector: 'a[href*="/stock/"]',
          extractor: (element: Element) => {
            const href = element.getAttribute('href') || '';
            const match = href.match(/\/stock\/(\d{6})/);
            return match ? match[1] : null;
          }
        },
        // 策略2: 从data属性中提取
        {
          selector: '[data-code]',
          extractor: (element: Element) => {
            const code = element.getAttribute('data-code') || '';
            return code.match(/^\d{6}$/) ? code : null;
          }
        },
        // 策略3: 从class名中提取
        {
          selector: '.stock-code, .code',
          extractor: (element: Element) => {
            const text = element.textContent || '';
            const match = text.match(/(\d{6})/);
            return match ? match[1] : null;
          }
        },
        // 策略4: 从表格中提取
        {
          selector: 'td, th',
          extractor: (element: Element) => {
            const text = element.textContent || '';
            // 匹配6位数字，但排除明显不是股票代码的数字
            const match = text.match(/\b(\d{6})\b/);
            if (match) {
              const code = match[1];
              // 简单验证：股票代码应该以0、2、3、6开头
              if (/^[0236]/.test(code)) {
                return code;
              }
            }
            return null;
          }
        }
      ];

      // 执行所有策略
      strategies.forEach(strategy => {
        const elements = document.querySelectorAll(strategy.selector);
        elements.forEach(element => {
          const code = strategy.extractor(element);
          if (code && !processedCodes.has(code)) {
            processedCodes.add(code);
            
            // 尝试获取股票名称
            let name = '';
            const nameElement = element.querySelector('.name, .stock-name') || 
                               element.closest('tr')?.querySelector('.name, .stock-name') ||
                               element.parentElement?.querySelector('.name, .stock-name');
            
            if (nameElement) {
              name = nameElement.textContent?.trim() || '';
            }

            stockInfos.push({
              code,
              name,
              market: this.getMarketFromCode(code)
            });
          }
        });
      });

      console.log(`从DOM提取到 ${stockInfos.length} 个股票:`, stockInfos);
      return stockInfos;

    } catch (error) {
      console.error('从DOM提取股票代码失败:', error);
      return [];
    }
  }

  /**
   * 从我的股票页面提取股票列表
   */
  static extractMyStockList(): StockInfo[] {
    try {
      // 针对"我的股票"页面的特殊处理
      const myStockSelectors = [
        '.my-stock-list .stock-item',
        '.stock-list-item',
        '.portfolio-item',
        '[data-stock-code]'
      ];

      const stockInfos: StockInfo[] = [];
      const processedCodes = new Set<string>();

      myStockSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
          // 尝试多种方式获取股票代码
          let code = element.getAttribute('data-stock-code') ||
                    element.getAttribute('data-code') ||
                    element.querySelector('.code')?.textContent?.trim() ||
                    '';

          // 从文本中提取代码
          if (!code) {
            const text = element.textContent || '';
            const match = text.match(/(\d{6})/);
            if (match) code = match[1];
          }

          if (code && code.length === 6 && !processedCodes.has(code)) {
            processedCodes.add(code);

            // 获取股票名称
            let name = element.querySelector('.name, .stock-name')?.textContent?.trim() || '';
            if (!name) {
              // 从文本中提取名称（通常在代码后面）
              const text = element.textContent || '';
              const nameMatch = text.match(/\d{6}\s*([^\d\s]+)/);
              if (nameMatch) name = nameMatch[1].trim();
            }

            stockInfos.push({
              code,
              name,
              market: this.getMarketFromCode(code)
            });
          }
        });
      });

      return stockInfos;
    } catch (error) {
      console.error('提取我的股票列表失败:', error);
      return [];
    }
  }

  /**
   * 通过API获取股票实时数据
   */
  static async fetchStockRealTimeData(stockCodes: string[]): Promise<StockDataResponse> {
    if (stockCodes.length === 0) {
      return { success: true, data: [] };
    }

    try {
      // 构建API请求参数
      const codeList = stockCodes.map(code => {
        const market = this.getMarketFromCode(code);
        return `${market}${code}`;
      }).join(',');

      // 同花顺实时数据API
      const apiUrl = `${this.API_BASE}/v6/line/hs_${codeList}/01/last.js`;
      
      console.log('请求实时数据API:', apiUrl);

      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Referer': 'http://stockpage.10jqka.com.cn/',
          'User-Agent': navigator.userAgent
        },
        credentials: 'omit'
      });

      if (!response.ok) {
        throw new Error(`API请求失败: ${response.status} ${response.statusText}`);
      }

      const jsonpText = await response.text();
      const apiData = this.parseJSONP(jsonpText);

      if (!apiData || !apiData.data) {
        console.warn('API返回数据格式异常:', apiData);
        return { success: false, data: [], message: 'API数据格式异常' };
      }

      // 解析股票数据
      const stockDataList: StockData[] = [];
      const timestamp = new Date().toISOString();

      Object.entries(apiData.data).forEach(([key, value]: [string, any]) => {
        try {
          if (!Array.isArray(value) || value.length < 11) {
            console.warn(`股票数据格式异常 ${key}:`, value);
            return;
          }

          const code = key.substring(2); // 移除市场前缀
          
          const stockData: StockData = {
            code: code,
            name: String(value[0] || ''),
            price: this.parseFloat(value[1]),
            change_amount: this.parseFloat(value[2]),
            change_percent: this.parseFloat(value[3]),
            volume: this.parseInt(value[4]),
            turnover: this.parseFloat(value[5]),
            high: this.parseFloat(value[6]),
            low: this.parseFloat(value[7]),
            open_price: this.parseFloat(value[8]),
            prev_close: this.parseFloat(value[9]),
            timestamp: timestamp
          };

          stockDataList.push(stockData);
        } catch (error) {
          console.error(`解析股票数据失败 ${key}:`, error);
        }
      });

      console.log(`成功解析 ${stockDataList.length} 条股票数据`);
      return { success: true, data: stockDataList };

    } catch (error) {
      console.error('获取股票实时数据失败:', error);
      return { 
        success: false, 
        data: [], 
        message: error instanceof Error ? error.message : '未知错误'
      };
    }
  }

  /**
   * 获取股票详细信息
   */
  static async fetchStockDetailInfo(stockCode: string): Promise<any> {
    try {
      const market = this.getMarketFromCode(stockCode);
      const fullCode = `${market}${stockCode}`;
      
      const apiUrl = `${this.QUOTE_API}/gn_detail/wap/stock/get?code=${fullCode}`;
      
      const response = await fetch(apiUrl, {
        headers: {
          'Referer': 'http://stockpage.10jqka.com.cn/',
          'User-Agent': navigator.userAgent
        }
      });

      if (response.ok) {
        const data = await response.json();
        return data;
      }
    } catch (error) {
      console.error(`获取股票详细信息失败 ${stockCode}:`, error);
    }
    
    return null;
  }

  /**
   * 安全的数字解析
   */
  private static parseFloat(value: any): number {
    const num = parseFloat(value);
    return isNaN(num) ? 0 : num;
  }

  private static parseInt(value: any): number {
    const num = parseInt(value);
    return isNaN(num) ? 0 : num;
  }

  /**
   * 验证股票代码格式
   */
  static isValidStockCode(code: string): boolean {
    return /^\d{6}$/.test(code) && /^[0236]/.test(code);
  }

  /**
   * 批量验证和清理股票代码
   */
  static cleanStockCodes(codes: string[]): string[] {
    return codes
      .map(code => code.trim())
      .filter(code => this.isValidStockCode(code))
      .filter((code, index, array) => array.indexOf(code) === index); // 去重
  }
}