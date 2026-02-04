/**
 * MCP Content Script
 * Injected into Kimi and DeepSeek pages
 */

import { KimiAdapter } from '@/content/adapters/kimi-adapter';
import { DeepSeekAdapter } from '@/content/adapters/deepseek-adapter';

// Detect platform and initialize appropriate adapter
function initializeAdapter() {
  const hostname = window.location.hostname;
  
  console.log('[MCP] Content script loaded on:', hostname);
  
  if (hostname.includes('kimi.com') || hostname.includes('moonshot.cn')) {
    console.log('[MCP] Initializing Kimi adapter');
    const adapter = new KimiAdapter();
    
    // Notify background script
    chrome.runtime.sendMessage({
      type: 'ADAPTER_READY',
      platform: 'kimi',
      url: window.location.href
    });
    
    return adapter;
  }
  
  if (hostname.includes('deepseek.com')) {
    console.log('[MCP] Initializing DeepSeek adapter');
    const adapter = new DeepSeekAdapter();
    
    // Notify background script
    chrome.runtime.sendMessage({
      type: 'ADAPTER_READY',
      platform: 'deepseek',
      url: window.location.href
    });
    
    return adapter;
  }
  
  console.log('[MCP] No adapter for this page');
  return null;
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeAdapter);
} else {
  initializeAdapter();
}

// Also listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('[MCP] Content script received message:', request);
  
  // Forward to adapter if needed
  // The adapters register their own listeners, so this is just for logging
  
  return true;
});
