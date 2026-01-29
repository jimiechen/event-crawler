export default defineContentScript({
  matches: ['<all_urls>'],
  runAt: 'document_start',
  main() {
    // 注入网络监听脚本
    try {
      const script = document.createElement('script');
      script.src = chrome.runtime.getURL('inject-scripts/network-monitor.js');
      script.onload = function() {
        (this as any).remove();
      };
      (document.head || document.documentElement).appendChild(script);
      console.log('网络监听脚本注入成功');
    } catch (e) {
      console.error('网络监听脚本注入失败:', e);
    }

    // 监听来自thspanel的消息
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      if (message.action === 'checkLogin') {
        // 检查同花顺登录状态
        const isLoggedIn = checkTonghuashunLogin();
        sendResponse({ isLoggedIn });
        return true;
      }
      
      if (message.action === 'getWebContent') {
        // 获取网页内容
        const content = getPageContent();
        sendResponse({ content });
        return true;
      }
      
      if (message.action === 'clickLogin') {
        // 点击登录按钮
        const success = clickLoginButton();
        sendResponse({ success });
        return true;
      }
      
      if (message.action === 'EXTRACT_LINKS_BY_XPATH') {
        // 使用 XPath 提取链接
        const result = extractLinksByXPath(message.xpath, message.selector);
        sendResponse(result);
        return true;
      }
      
      if (message.action === 'GET_PAGE_HTML') {
        // 获取完整页面 HTML
        const html = getPageHtml();
        sendResponse({ success: true, html });
        return true;
      }
    });
  },
});

// 检查同花顺登录状态
function checkTonghuashunLogin(): boolean {
  try {
    // 根据用户提供的退出按钮来检测登录状态
    // 如果存在退出按钮，则表示已登录
    const exitButton = document.querySelector('a.banner-exit[data-statid="sns_my_timeline.tuichu"]');
    if (exitButton && exitButton.textContent && exitButton.textContent.includes('退出')) {
      console.log('检测到退出按钮，用户已登录');
      return true;
    }
    
    // 备用检测方式：通过class名称检测
    const exitButtonByClass = document.querySelector('a.banner-exit');
    if (exitButtonByClass && exitButtonByClass.textContent && exitButtonByClass.textContent.includes('退出')) {
      console.log('通过class检测到退出按钮，用户已登录');
      return true;
    }
    
    // 如果没有找到退出按钮，则认为未登录
    console.log('未检测到退出按钮，用户未登录');
    return false;
  } catch (error) {
    console.error('检查登录状态失败:', error);
    return false;
  }
}

// 获取页面内容
function getPageContent(): string {
  try {
    // 获取页面标题和主要内容
    const title = document.title;
    const bodyText = document.body.innerText;
    
    // 限制内容长度避免过大
    const maxLength = 5000;
    const truncatedText = bodyText.length > maxLength 
      ? bodyText.substring(0, maxLength) + '...（内容已截断）'
      : bodyText;
    
    return `页面标题: ${title}\n\n页面内容:\n${truncatedText}`;
  } catch (error) {
    console.error('获取页面内容失败:', error);
    return '获取页面内容失败';
  }
}

// 点击登录按钮
function clickLoginButton(): boolean {
  try {
    const loginSelectors = [
      'a[href*="login"]',
      'button[class*="login"]',
      '.login-btn',
      '.login-link',
      '[data-action="login"]'
    ];
    
    for (const selector of loginSelectors) {
      const element = document.querySelector(selector) as HTMLElement;
      if (element && element.offsetParent !== null) {
        element.click();
        return true;
      }
    }
    
    return false;
  } catch (error) {
    console.error('点击登录按钮失败:', error);
    return false;
  }
}

// 使用 XPath 或选择器提取链接
function extractLinksByXPath(xpath?: string, selector?: string): { success: boolean; urls: string[]; ids: string[] } {
  const urls: string[] = [];
  const ids: string[] = [];
  
  try {
    // 首先尝试 XPath
    if (xpath) {
      const iterator = document.evaluate(
        xpath,
        document,
        null,
        XPathResult.ORDERED_NODE_ITERATOR_TYPE,
        null
      );
      
      let node = iterator.iterateNext();
      let foundCount = 0;
      while (node && foundCount < 100) { // 限制最多100个
        const anchor = node as HTMLAnchorElement;
        if (anchor.href) {
          urls.push(anchor.href);
          // 尝试提取父元素的 ID
          const parent = anchor.parentElement;
          const id = parent?.id || '';
          ids.push(id);
        }
        node = iterator.iterateNext();
        foundCount++;
      }
      
      if (urls.length > 0) {
        console.log(`[Okooo] 通过 XPath 提取到 ${urls.length} 个链接`);
        return { success: true, urls, ids };
      }
    }
    
    // 备用：使用 CSS 选择器
    if (selector) {
      const elements = document.querySelectorAll(selector);
      elements.forEach((el, index) => {
        const anchor = el as HTMLAnchorElement;
        if (anchor.href) {
          urls.push(anchor.href);
          const parent = anchor.parentElement;
          const id = parent?.id || `unknown-${index}`;
          ids.push(id);
        }
      });
      
      if (urls.length > 0) {
        console.log(`[Okooo] 通过选择器提取到 ${urls.length} 个链接`);
        return { success: true, urls, ids };
      }
    }
    
    console.log('[Okooo] 未找到任何链接');
    return { success: false, urls: [], ids: [] };
    
  } catch (error) {
    console.error('[Okooo] 提取链接失败:', error);
    return { success: false, urls: [], ids: [] };
  }
}

// 获取页面完整 HTML
function getPageHtml(): string {
  try {
    const html = document.documentElement.outerHTML;
    console.log(`[Okooo] 获取页面 HTML，大小: ${html.length} 字符`);
    return html;
  } catch (error) {
    console.error('[Okooo] 获取 HTML 失败:', error);
    return '';
  }
}
