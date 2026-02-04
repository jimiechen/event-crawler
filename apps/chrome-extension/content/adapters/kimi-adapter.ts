/**
 * Kimi Page Adapter
 * Controls Kimi web interface (https://www.kimi.com)
 */

import { BasePageController, controllerRegistry } from '../page-controller';

export class KimiAdapter extends BasePageController {
  // CSS Selectors for Kimi interface
  private readonly SELECTORS = {
    textarea: 'textarea[placeholder*="输入"], textarea[placeholder*="发送消息"]',
    sendButton: 'button[type="submit"], button svg[data-icon="send"]',
    uploadButton: '[aria-label="上传图片"], button[title="上传图片"]',
    fileInput: 'input[type="file"]',
    messageContainer: '.chat-container, .message-list, .kimi-chat',
    lastMessage: '.message-content:last-child, .chat-message:last-child, .kimi-message:last-child',
    newChatButton: '[aria-label="新建对话"], button:has-text("新建对话")',
    loadingIndicator: '.loading, .typing-indicator, .kimi-loading'
  };

  constructor() {
    super();
    this.init();
  }

  private init(): void {
    // Initialize observer on message container
    this.initObserver(this.SELECTORS.messageContainer);
    
    // Listen for messages from background script
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      this.handleMessage(request, sendResponse);
      return true; // Async response
    });
  }

  getPlatform(): string {
    return 'kimi';
  }

  isReady(): boolean {
    const textarea = document.querySelector(this.SELECTORS.textarea);
    return !!textarea;
  }

  /**
   * Send message to Kimi
   */
  async sendMessage(text: string, image?: string): Promise<string> {
    // Wait for page to be ready
    if (!this.isReady()) {
      throw new Error('Kimi页面未准备好，请等待页面加载完成');
    }

    // Upload image if provided
    if (image) {
      await this.uploadImage(image);
    }

    // Find and fill textarea
    const textarea = document.querySelector(this.SELECTORS.textarea) as HTMLTextAreaElement;
    if (!textarea) {
      throw new Error('未找到输入框');
    }

    // Set text value
    textarea.value = text;
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
    textarea.dispatchEvent(new Event('change', { bubbles: true }));

    // Trigger send
    const sendButton = document.querySelector(this.SELECTORS.sendButton) as HTMLButtonElement;
    if (sendButton && !sendButton.disabled) {
      sendButton.click();
    } else {
      // Fallback to Enter key
      textarea.dispatchEvent(new KeyboardEvent('keydown', {
        key: 'Enter',
        code: 'Enter',
        keyCode: 13,
        which: 13,
        bubbles: true,
        cancelable: true
      }));
    }

    // Wait for reply
    return this.waitForReply();
  }

  /**
   * Upload image using multiple strategies
   */
  async uploadImage(base64Image: string): Promise<void> {
    // Strategy 1: Direct file input manipulation
    try {
      await this.uploadViaFileInput(base64Image);
      return;
    } catch (e) {
      console.log('文件input上传失败，尝试粘贴方式:', e);
    }

    // Strategy 2: Clipboard paste simulation
    try {
      await this.uploadViaPaste(base64Image);
      return;
    } catch (e) {
      console.log('粘贴上传失败:', e);
    }

    // Strategy 3: Drag and drop simulation
    try {
      await this.uploadViaDragDrop(base64Image);
      return;
    } catch (e) {
      console.log('拖拽上传失败:', e);
      throw new Error('所有图片上传方式均失败');
    }
  }

  /**
   * Upload via file input
   */
  private async uploadViaFileInput(base64Image: string): Promise<void> {
    // Click upload button to open file dialog
    const uploadBtn = document.querySelector(this.SELECTORS.uploadButton) as HTMLElement;
    if (uploadBtn) {
      uploadBtn.click();
      await this.sleep(500);
    }

    // Find file input
    const fileInput = document.querySelector(this.SELECTORS.fileInput) as HTMLInputElement;
    if (!fileInput) {
      throw new Error('未找到文件输入框');
    }

    // Convert base64 to File
    const file = await this.base64ToFile(base64Image, 'upload.png');
    
    // Create DataTransfer and set files
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    fileInput.files = dataTransfer.files;

    // Dispatch events
    fileInput.dispatchEvent(new Event('change', { bubbles: true }));
    fileInput.dispatchEvent(new Event('input', { bubbles: true }));

    // Wait for upload to complete
    await this.waitForUploadComplete();
  }

  /**
   * Upload via clipboard paste
   */
  private async uploadViaPaste(base64Image: string): Promise<void> {
    const blob = await (await fetch(base64Image)).blob();
    const file = new File([blob], 'image.png', { type: blob.type || 'image/png' });

    // Create clipboard data
    const clipboardData = new DataTransfer();
    clipboardData.items.add(file);

    // Create paste event
    const pasteEvent = new ClipboardEvent('paste', {
      bubbles: true,
      cancelable: true,
      clipboardData
    });

    // Dispatch to textarea
    const textarea = document.querySelector(this.SELECTORS.textarea);
    if (textarea) {
      textarea.dispatchEvent(pasteEvent);
      await this.waitForUploadComplete();
    } else {
      throw new Error('未找到输入框');
    }
  }

  /**
   * Upload via drag and drop
   */
  private async uploadViaDragDrop(base64Image: string): Promise<void> {
    const blob = await (await fetch(base64Image)).blob();
    const file = new File([blob], 'image.png', { type: blob.type || 'image/png' });

    // Create drag events
    const dragEnterEvent = new DragEvent('dragenter', {
      bubbles: true,
      cancelable: true,
      dataTransfer: new DataTransfer()
    });

    const dragOverEvent = new DragEvent('dragover', {
      bubbles: true,
      cancelable: true,
      dataTransfer: new DataTransfer()
    });

    const dropEvent = new DragEvent('drop', {
      bubbles: true,
      cancelable: true,
      dataTransfer: new DataTransfer()
    });

    // Add file to drop event
    dropEvent.dataTransfer?.items.add(file);

    // Find drop target (usually the chat container or textarea)
    const dropTarget = document.querySelector(this.SELECTORS.messageContainer) ||
                       document.querySelector(this.SELECTORS.textarea);

    if (dropTarget) {
      dropTarget.dispatchEvent(dragEnterEvent);
      dropTarget.dispatchEvent(dragOverEvent);
      dropTarget.dispatchEvent(dropEvent);
      await this.waitForUploadComplete();
    } else {
      throw new Error('未找到拖放目标');
    }
  }

  /**
   * Wait for upload to complete
   */
  private async waitForUploadComplete(): Promise<void> {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      const timeout = 30000; // 30 seconds

      const checkInterval = window.setInterval(() => {
        // Check if loading indicator is gone
        const loading = document.querySelector(this.SELECTORS.loadingIndicator);
        
        if (!loading) {
          window.clearInterval(checkInterval);
          resolve();
          return;
        }

        if (Date.now() - startTime > timeout) {
          window.clearInterval(checkInterval);
          reject(new Error('图片上传超时'));
        }
      }, 500);
    });
  }

  /**
   * Get last reply from Kimi
   */
  getLastReply(): string {
    // Try multiple selectors for message content
    const selectors = [
      '.message-content:last-child',
      '.chat-message:last-child .content',
      '.kimi-message:last-child .text',
      '.message:last-child .bubble',
      '[data-testid="message-content"]:last-child'
    ];

    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element?.textContent) {
        return element.textContent.trim();
      }
    }

    return '';
  }

  /**
   * Start new chat
   */
  async newChat(): Promise<void> {
    const newChatBtn = document.querySelector(this.SELECTORS.newChatButton) as HTMLElement;
    if (newChatBtn) {
      newChatBtn.click();
      await this.sleep(1000);
    } else {
      // Fallback: navigate to new chat URL
      window.location.href = 'https://www.kimi.com/chat/new';
    }
  }

  /**
   * Get chat history
   */
  async getChatHistory(): Promise<any[]> {
    const messages: any[] = [];
    const messageElements = document.querySelectorAll('.message, .chat-message, .kimi-message');

    messageElements.forEach((el, index) => {
      const content = el.querySelector('.content, .text, .bubble')?.textContent?.trim();
      const isUser = el.classList.contains('user') || 
                     el.classList.contains('human') ||
                     el.getAttribute('data-role') === 'user';

      if (content) {
        messages.push({
          index,
          role: isUser ? 'user' : 'assistant',
          content
        });
      }
    });

    return messages;
  }

  /**
   * Handle messages from background script
   */
  private async handleMessage(request: any, sendResponse: (response: any) => void): Promise<void> {
    try {
      switch (request.action) {
        case 'send_message':
          const reply = await this.sendMessage(
            request.params.message,
            request.params.image
          );
          sendResponse({ success: true, reply });
          break;

        case 'upload_image':
          await this.uploadImage(request.params.image);
          sendResponse({ success: true });
          break;

        case 'new_chat':
          await this.newChat();
          sendResponse({ success: true });
          break;

        case 'get_history':
          const history = await this.getChatHistory();
          sendResponse({ success: true, history });
          break;

        case 'is_ready':
          sendResponse({ success: true, ready: this.isReady() });
          break;

        default:
          sendResponse({ success: false, error: 'Unknown action' });
      }
    } catch (error) {
      sendResponse({
        success: false,
        error: error instanceof Error ? error.message : String(error)
      });
    }
  }
}

// Register adapter
controllerRegistry.register('kimi', KimiAdapter);

// Auto-initialize if on Kimi page
if (window.location.hostname.includes('kimi.com') || 
    window.location.hostname.includes('moonshot.cn')) {
  const adapter = new KimiAdapter();
  console.log('Kimi adapter initialized');
  
  // Notify background script that adapter is ready
  chrome.runtime.sendMessage({
    type: 'ADAPTER_READY',
    platform: 'kimi',
    url: window.location.href
  });
}
