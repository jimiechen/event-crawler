(function () {
  // Prevent duplicate initialization
  if (window.__NETWORK_MONITOR_INITIALIZED__) return;
  window.__NETWORK_MONITOR_INITIALIZED__ = true;

  // Configuration
  const CONFIG = {
    enabled: true,
    logLevel: 'INFO', // DEBUG, INFO, WARN, ERROR
    filters: {
      urls: [], // Array of strings or RegExps
      types: ['xhr', 'fetch'], // 'xhr', 'fetch'
      minDuration: 0
    }
  };

  // Expose configuration globally
  window.__NETWORK_MONITOR_CONFIG__ = CONFIG;

  // Logging Utility
  const logger = {
    debug: (...args) => {
      if (['DEBUG'].includes(CONFIG.logLevel)) {
        console.groupCollapsed(`%c[NetMonitor DEBUG] ${args[0]}`, 'color: gray; font-weight: normal;');
        console.log(...args.slice(1));
        console.groupEnd();
      }
    },
    info: (...args) => {
      if (['DEBUG', 'INFO'].includes(CONFIG.logLevel)) {
        console.groupCollapsed(`%c[NetMonitor] ${args[0]}`, 'color: #2196F3; font-weight: bold;');
        console.log(...args.slice(1));
        console.groupEnd();
      }
    },
    warn: (...args) => {
      if (['DEBUG', 'INFO', 'WARN'].includes(CONFIG.logLevel)) {
        console.groupCollapsed(`%c[NetMonitor WARN] ${args[0]}`, 'color: #FF9800; font-weight: bold;');
        console.warn(...args.slice(1));
        console.groupEnd();
      }
    },
    error: (...args) => {
      if (['DEBUG', 'INFO', 'WARN', 'ERROR'].includes(CONFIG.logLevel)) {
        // Use console.group to auto-expand errors for better visibility
        console.group(`%c[NetMonitor ERROR] ${args[0]}`, 'color: #F44336; font-weight: bold;');
        console.error(...args.slice(1));
        console.groupEnd();
      }
    },
    matchFound: (...args) => {
      console.groupCollapsed(`%c[TARGET MATCHED] ${args[0]}`, 'background: #FF5722; color: white; padding: 2px 5px; border-radius: 2px; font-weight: bold;');
      console.log(...args.slice(1));
      console.groupEnd();
    }
  };

  function shouldLog(url, type) {
    if (!CONFIG.enabled) return false;
    if (CONFIG.filters.types.length && !CONFIG.filters.types.includes(type)) return false;
    
    try {
      const fullUrl = new URL(url, window.location.href).href;
      if (CONFIG.filters.urls.length) {
        const match = CONFIG.filters.urls.some(pattern => {
          if (pattern instanceof RegExp) return pattern.test(fullUrl);
          return fullUrl.includes(pattern);
        });
        if (!match) return false;
      }
    } catch (e) {
      return false;
    }
    
    return true;
  }

  function isTargetMatch(url) {
    try {
      const fullUrl = new URL(url, window.location.href).href;
      return fullUrl.includes('m.okooo.com/match/');
    } catch (e) {
      return false;
    }
  }

  // Performance Monitoring
  const perfMetrics = new Map();
  const perfObserver = new PerformanceObserver((list) => {
    list.getEntries().forEach((entry) => {
      if (entry.initiatorType === 'xmlhttprequest' || entry.initiatorType === 'fetch') {
        perfMetrics.set(entry.name, entry);
      }
    });
  });
  perfObserver.observe({ entryTypes: ['resource'] });

  // Hook XMLHttpRequest
  const originalXHROpen = XMLHttpRequest.prototype.open;
  const originalXHRSend = XMLHttpRequest.prototype.send;

  XMLHttpRequest.prototype.open = function (method, url) {
    this._monitor_method = method;
    this._monitor_url = url;
    this._monitor_startTime = performance.now();
    return originalXHROpen.apply(this, arguments);
  };

  XMLHttpRequest.prototype.send = function (body) {
    if (!shouldLog(this._monitor_url, 'xhr')) {
      return originalXHRSend.apply(this, arguments);
    }

    const method = this._monitor_method;
    const url = this._monitor_url;
    const startTime = performance.now();

    logger.debug(`🚀 XHR Start: ${method} ${url}`, {
      body,
      timestamp: new Date().toISOString()
    });

    const monitorStart = performance.now();

    const onFinish = (type) => {
      const duration = performance.now() - startTime;
      const monitorOverhead = performance.now() - monitorStart; // Rough overhead estimate
      
      let fullUrl = url;
      try { fullUrl = new URL(url, window.location.href).href; } catch(e){}
      
      const perfEntry = perfMetrics.get(fullUrl);
      
      // Get Response Data
      let responseData = null;
      try {
        if (this.responseType === '' || this.responseType === 'text') {
            responseData = this.responseText;
        } else if (this.responseType === 'json') {
            responseData = this.response;
        } else {
            responseData = `[${this.responseType}] (Binary/Blob data not shown)`;
        }
      } catch (e) {
        responseData = `[Error reading response] ${e.message}`;
      }

      const stats = {
        status: this.status,
        statusText: this.statusText,
        duration: perfEntry ? perfEntry.duration : duration,
        size: perfEntry ? perfEntry.transferSize : (this.response ? (this.response.length || 0) : 0),
        overhead: monitorOverhead,
        perfEntry: perfEntry || 'Not found in PerformanceObserver',
        responseBody: responseData
      };

      if (type === 'error' || this.status >= 400) {
        if (isTargetMatch(url)) {
          logger.matchFound(`❌ TARGET XHR Failed: ${method} ${url}`, stats);
        } else {
          logger.error(`❌ XHR Failed: ${method} ${url}`, stats);
        }
      } else {
        logger.info(`✅ XHR Completed: ${method} ${url}`, stats);
        
        if (isTargetMatch(url)) {
          logger.matchFound(`🎯 XHR MATCH: ${url}`, stats);
        }
      }
    };

    this.addEventListener('load', () => onFinish('load'));
    this.addEventListener('error', () => onFinish('error'));
    this.addEventListener('abort', () => onFinish('abort'));

    return originalXHRSend.apply(this, arguments);
  };

  // Hook Fetch
  const originalFetch = window.fetch;
  window.fetch = async function (input, init) {
    let url = input;
    if (input instanceof Request) url = input.url;
    
    const method = (init && init.method) || (input instanceof Request && input.method) || 'GET';
    
    if (!shouldLog(url, 'fetch')) {
      return originalFetch.apply(this, arguments);
    }

    const startTime = performance.now();
    logger.debug(`🚀 Fetch Start: ${method} ${url}`, {
      init,
      timestamp: new Date().toISOString()
    });

    const monitorStart = performance.now();

    try {
      const response = await originalFetch.apply(this, arguments);
      const clonedResponse = response.clone();
      
      const duration = performance.now() - startTime;
      const monitorOverhead = performance.now() - monitorStart - duration; // Attempt to subtract wait time
      
      let fullUrl = url;
      try { fullUrl = new URL(url, window.location.href).href; } catch(e){}

      const perfEntry = perfMetrics.get(fullUrl);
      
      // Read response body asynchronously
      clonedResponse.text().then(text => {
        const stats = {
            status: response.status,
            statusText: response.statusText,
            url: fullUrl,
            requestMethod: method,
            requestBody: init ? init.body : undefined,
            duration: perfEntry ? perfEntry.duration : duration,
            size: perfEntry ? perfEntry.transferSize : (response.headers.get('content-length') || text.length),
            overhead: Math.max(0, monitorOverhead),
            responseBody: text.substring(0, 10000) + (text.length > 10000 ? '... (truncated)' : '')
        };

        if (!response.ok) {
            if (isTargetMatch(url)) {
                logger.matchFound(`❌ TARGET Fetch Failed: ${method} ${url}`, stats);
            } else {
                logger.error(`❌ Fetch Failed: ${method} ${url}`, stats);
            }
        } else {
            logger.info(`✅ Fetch Completed: ${method} ${url}`, stats);
            
            if (isTargetMatch(url)) {
                logger.matchFound(`🎯 Fetch MATCH: ${url}`, stats);
            }
        }
      }).catch(err => {
         logger.error(`⚠️ Failed to read fetch body: ${url}`, err);
      });

      return response;
    } catch (error) {
      logger.error(`🔥 Fetch Error: ${method} ${url}`, error);
      throw error;
    }
  };

  console.log('%c[NetworkMonitor] Initialized', 'background: #4CAF50; color: white; padding: 2px 5px; border-radius: 2px;');
})();
