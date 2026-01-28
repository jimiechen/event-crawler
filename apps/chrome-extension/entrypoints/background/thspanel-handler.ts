// THS Panel 网络捕获状态
interface NetworkCaptureState {
  isCapturing: boolean;
  pattern: string;
  tabId?: number;
}

// 存储请求和响应的映射
interface RequestResponsePair {
  requestId: string;
  url: string;
  timestamp: string;
  hasResponse: boolean;
}

let networkCaptureState: NetworkCaptureState = {
  isCapturing: false,
  pattern: ''
};

// 用于跟踪请求和响应的映射
const requestResponseMap = new Map<string, RequestResponsePair>();

// 用于跟踪已处理的时间戳
const processedTimestamps = new Set<string>();

// 定期清理已处理时间戳的定时器
let cleanupTimer: NodeJS.Timeout | null = null;

/**
 * 提取URL中的时间戳参数
 * @param url 完整的URL
 * @returns 时间戳参数值，如果没有则返回null
 */
function extractTimestamp(url: string): string | null {
  try {
    const urlObj = new URL(url);
    // 提取 _ 时间戳参数
    const timestamp = urlObj.searchParams.get('_');
    return timestamp;
  } catch (error) {
    // 如果URL解析失败，使用正则表达式提取
    const match = url.match(/[&?]_=(\d+)/);
    return match ? match[1] : null;
  }
}

/**
 * 定期清理已处理的时间戳集合，防止内存泄漏
 */
function startPeriodicCleanup() {
  // 清理之前的定时器
  if (cleanupTimer) {
    clearInterval(cleanupTimer);
  }
  
  // 每5分钟清理一次已处理的时间戳集合
  cleanupTimer = setInterval(() => {
    const beforeSize = processedTimestamps.size;
    processedTimestamps.clear();
    console.log(`Background: 定期清理已处理时间戳集合，清理前: ${beforeSize}，清理后: ${processedTimestamps.size}`);
  }, 5 * 60 * 1000); // 5分钟
}

/**
 * 停止定期清理
 */
function stopPeriodicCleanup() {
  if (cleanupTimer) {
    clearInterval(cleanupTimer);
    cleanupTimer = null;
    console.log('Background: 已停止定期清理');
  }
}

/**
 * 初始化THS Panel监听器
 */
export function initThsPanelListener() {
  console.log('Background: 初始化 THS Panel 监听器');
  
  // 监听来自thspanel的消息
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    // 只处理包含action属性的消息，其他消息让其他监听器处理
    if (!message || typeof message.action !== 'string') {
      return false; // 不处理此消息，让其他监听器处理
    }
    
    console.log('Background: THS Panel 收到消息:', message);
    console.log('Background: 发送者信息:', sender);
    
    if (message.action === 'startNetworkCapture') {
      console.log('Background: 开始网络捕获');
      console.log('Background: 捕获模式:', message.pattern);
      console.log('Background: 目标标签页ID:', message.tabId);
      
      try {
        startNetworkCapture(message.pattern, message.tabId);
        console.log('Background: 网络捕获启动成功');
        sendResponse({ success: true });
      } catch (error: any) {
        console.error('Background: 网络捕获启动失败:', error);
        sendResponse({ success: false, error: error.message });
      }
      return true;
    } else if (message.action === 'stopNetworkCapture') {
      console.log('Background: 停止网络捕获');
      
      try {
        stopNetworkCapture();
        console.log('Background: 网络捕获停止成功');
        sendResponse({ success: true });
      } catch (error: any) {
        console.error('Background: 网络捕获停止失败:', error);
        sendResponse({ success: false, error: error.message });
      }
      return true;
    } else if (message.action === 'openThsPanel') {
      console.log('Background: 打开 THS Panel');
      console.log('Background: 目标标签页ID:', message.tabId);
      
      try {
        chrome.sidePanel.open({ tabId: message.tabId });
        console.log('Background: THS Panel 打开成功');
        sendResponse({ success: true });
      } catch (error: any) {
        console.error('Background: THS Panel 打开失败:', error);
        sendResponse({ success: false, error: error.message });
      }
      return true;
    } else if (message.action === 'getNetworkCaptureStatus') {
      console.log('Background: 获取网络捕获状态');
      
      try {
        const status = getNetworkCaptureStatus();
        console.log('Background: 网络捕获状态:', status);
        sendResponse(status);
      } catch (error: any) {
        console.error('Background: 获取网络捕获状态失败:', error);
        sendResponse({ success: false, error: error.message });
      }
      return true;
    } else {
      console.warn('Background: 未知的消息类型:', message.action);
      sendResponse({ success: false, error: '未知的消息类型' });
    }
    
    return false;
  });
  
  // 监听网络请求
  chrome.webRequest.onBeforeRequest.addListener(
    handleNetworkRequest,
    { urls: ['<all_urls>'] },
    ['requestBody']
  );
  
  // 监听网络响应
  chrome.webRequest.onCompleted.addListener(
    handleNetworkResponse,
    { urls: ['<all_urls>'] },
    ['responseHeaders']
  );
}

/**
 * 开始网络捕获
 */
function startNetworkCapture(pattern: string, tabId?: number) {
  console.log('Background: 开始网络捕获:', pattern, 'Tab ID:', tabId);
  
  networkCaptureState.isCapturing = true;
  networkCaptureState.pattern = pattern;
  networkCaptureState.tabId = tabId;
  
  // 清空之前的数据
  const previousSize = requestResponseMap.size;
  requestResponseMap.clear();
  processedTimestamps.clear();
  console.log('Background: 清空之前的请求响应映射，之前有', previousSize, '条记录');
  
  // 启动定期清理
  startPeriodicCleanup();
  
  console.log('Background: 网络捕获监听器已设置完成');
}

/**
 * 停止网络捕获
 */
function stopNetworkCapture() {
  console.log('Background: 停止网络捕获');
  console.log('Background: 停止前状态 - isCapturing:', networkCaptureState.isCapturing);
  console.log('Background: 停止前状态 - pattern:', networkCaptureState.pattern);
  console.log('Background: 停止前状态 - tabId:', networkCaptureState.tabId);
  console.log('Background: 停止前请求响应映射大小:', requestResponseMap.size);
  
  networkCaptureState.isCapturing = false;
  networkCaptureState.pattern = '';
  networkCaptureState.tabId = undefined;
  
  // 停止定期清理
  stopPeriodicCleanup();
  
  // 清空请求响应映射和已处理时间戳集合
  requestResponseMap.clear();
  processedTimestamps.clear();
  
  console.log('Background: 网络捕获已停止');
  console.log('Background: 停止后状态 - isCapturing:', networkCaptureState.isCapturing);
  console.log('Background: 停止后请求响应映射大小:', requestResponseMap.size);
  console.log('Background: 已清理所有缓存数据');
}

/**
 * 获取网络捕获状态
 */
function getNetworkCaptureStatus() {
  return {
    isCapturing: networkCaptureState.isCapturing,
    pattern: networkCaptureState.pattern,
    tabId: networkCaptureState.tabId
  };
}

/**
 * 处理网络请求
 */
function handleNetworkRequest(details: chrome.webRequest.WebRequestBodyDetails) {
  if (!networkCaptureState.isCapturing) return;
  
  const url = details.url;
  
  // console.log('Background: 检查网络请求:', url);
  // console.log('Background: 当前监听pattern:', networkCaptureState.pattern);
  
  // 检查是否是同花顺相关的URL
  const isTonghuashunUrl = (url.includes('multimarketreal'));
  
  if (!isTonghuashunUrl) {
    return;
  }
  
  // console.log('Background: 捕获到同花顺网络请求:', url);
  
  // 记录请求信息
  const requestId = details.requestId;
  const timestamp = new Date().toISOString();
  
  requestResponseMap.set(requestId, {
    requestId,
    url,
    timestamp,
    hasResponse: false
  });
  
  // console.log('Background: 已记录请求:', requestId, '总请求数:', requestResponseMap.size);
}

/**
 * 处理网络响应
 */
function handleNetworkResponse(details: chrome.webRequest.WebResponseCacheDetails) {
  if (!networkCaptureState.isCapturing) return;
  
  const url = details.url;
  
  // console.log('Background: 检查网络响应:', url);
  
  // 检查是否是同花顺相关的URL

  // (url.includes('t.10jqka.com.cn') && (
  //   url.includes('userPersonal') || 
  //   url.includes('getSelfStockWithMarket') ||
  //   url.includes('multimarketreal')
  // )) ||
  // (url.includes('d.10jqka.com.cn') && 
  const isTonghuashunUrl = (url.includes('multimarketreal'));
  
  if (!isTonghuashunUrl) {
    return;
  }
  
  console.log('Background: 捕获到同花顺网络响应:', url);
  
  // 提取时间戳进行去重检查
  const timestamp = extractTimestamp(url);
  
  if (!timestamp) {
    console.log('Background: URL中没有时间戳参数，跳过处理:', url);
    return;
  }
  
  // 检查是否已经处理过相同的时间戳
  if (processedTimestamps.has(timestamp)) {
    console.log('Background: 时间戳已处理，跳过重复请求:', timestamp);
    return;
  }
  
  // 标记时间戳为已处理
  processedTimestamps.add(timestamp);
  
  const requestId = details.requestId;
  const requestInfo = requestResponseMap.get(requestId);
  
  if (requestInfo && !requestInfo.hasResponse) {
    // 标记已处理响应，避免重复
    requestInfo.hasResponse = true;
    
    console.log('Background: 开始获取响应数据:', url);
    
    // 尝试获取响应数据
    fetchResponseData(url, details.tabId, requestInfo.timestamp);
    
    // 清理已处理的请求记录（可选，避免内存泄漏）
    setTimeout(() => {
      requestResponseMap.delete(requestId);
      console.log('Background: 清理请求记录:', requestId);
    }, 5000);
  } else {
    console.log('Background: 请求信息不存在或已处理:', requestId, !!requestInfo, requestInfo?.hasResponse);
  }
}

/**
 * 获取响应数据
 */
async function fetchResponseData(url: string, tabId?: number, originalTimestamp?: string) {
  try {
    // 使用fetch获取数据（注意：这可能受到CORS限制）
    const response = await fetch(url);
    const text = await response.text();
    
    // 解析JSONP响应
    const jsonpData = parseJsonpResponse(text);
    
    // 提取URL中的时间戳参数
    const urlTimestamp = extractTimestamp(url);
    
    // 发送数据到thspanel，包含时间戳参数
    chrome.runtime.sendMessage({
      action: 'networkData',
      url,
      response: jsonpData,
      timestamp: originalTimestamp || new Date().toISOString(),
      urlTimestamp: urlTimestamp, // 添加URL中的时间戳参数
      requestId: `${url}_${originalTimestamp || Date.now()}` // 添加唯一标识
    });
    
  } catch (error) {
    console.error('获取响应数据失败:', error);
    
    // 提取URL中的时间戳参数
    const urlTimestamp = extractTimestamp(url);
    
    // 发送错误信息到thspanel
    chrome.runtime.sendMessage({
      action: 'networkData',
      url,
      response: { error: '获取数据失败: ' + error },
      timestamp: originalTimestamp || new Date().toISOString(),
      urlTimestamp: urlTimestamp, // 添加URL中的时间戳参数
      requestId: `${url}_${originalTimestamp || Date.now()}_error`
    });
  }
}

/**
 * 解析JSONP响应
 */
function parseJsonpResponse(text: string): any {
  try {
    // 匹配JSONP格式: callback(data)
    const match = text.match(/^\w+\((.+)\)$/);
    if (match) {
      return JSON.parse(match[1]);
    }
    
    // 如果不是JSONP格式，尝试直接解析JSON
    return JSON.parse(text);
  } catch (error) {
    console.error('解析JSONP响应失败:', error);
    return { error: '解析失败', raw: text.substring(0, 500) };
  }
}

/**
 * 打开THS Panel
 */
async function openThsPanel() {
  try {
    // 创建新标签页并打开thspanel
    const tab = await chrome.tabs.create({
      url: chrome.runtime.getURL('thspanel/index.html')
    });
    console.log('打开THS Panel:', tab.id);
  } catch (error) {
    console.error('打开THS Panel失败:', error);
  }
}

/**
 * 使用Chrome Debugger API获取网络数据（备用方案）
 */
export async function enableNetworkDomainForTab(tabId: number) {
  try {
    // 附加调试器
    await chrome.debugger.attach({ tabId }, '1.3');
    
    // 启用网络域
    await chrome.debugger.sendCommand({ tabId }, 'Network.enable');
    
    // 监听网络事件
    chrome.debugger.onEvent.addListener((source, method, params) => {
      if (source.tabId === tabId && method === 'Network.responseReceived') {
        handleDebuggerNetworkResponse(source.tabId!, params);
      }
    });
    
    console.log('为标签页启用网络调试:', tabId);
  } catch (error) {
    console.error('启用网络调试失败:', error);
  }
}

/**
 * 处理调试器网络响应
 */
async function handleDebuggerNetworkResponse(tabId: number, params: any) {
  try {
    const url = params.response?.url;
    if (!url || !url.includes(networkCaptureState.pattern)) return;
    
    // 获取响应体
    const response = (await chrome.debugger.sendCommand(
      { tabId },
      'Network.getResponseBody',
      { requestId: params.requestId }
    )) as any;
    
    if (response && response.body) {
      const jsonpData = parseJsonpResponse(response.body);
      
      // 发送数据到thspanel
      chrome.runtime.sendMessage({
        action: 'networkData',
        url,
        response: jsonpData,
        timestamp: new Date().toISOString()
      });
    }
  } catch (error) {
    console.error('处理调试器网络响应失败:', error);
  }
}