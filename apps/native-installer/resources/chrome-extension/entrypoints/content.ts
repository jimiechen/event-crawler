export default defineContentScript({
  matches: ['<all_urls>'],
  main() {
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
    });
  },
});

// 检查同花顺登录状态
function checkTonghuashunLogin(): boolean {
  try {
    // 检查是否在同花顺域名
    if (!window.location.hostname.includes('10jqka.com.cn')) {
      return false;
    }
    
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
      if (element && element.offsetParent !== null) { // 确保元素可见
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
