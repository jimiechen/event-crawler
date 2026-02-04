/**
 * Universal Page Controller Interface
 * Defines the contract for all platform adapters
 */

export interface PageController {
  // Page information
  getPlatform(): string;
  isReady(): boolean;
  
  // Message operations
  sendMessage(text: string, image?: string): Promise<string>;
  getLastReply(): string;
  waitForReply(timeout?: number): Promise<string>;
  
  // Image upload
  uploadImage(base64Image: string): Promise<void>;
  
  // Session management
  newChat(): Promise<void>;
  getChatHistory(): Promise<any[]>;
}

/**
 * Base Page Controller Implementation
 * Provides common functionality for all adapters
 */
export abstract class BasePageController implements PageController {
  protected observer: MutationObserver | null = null;
  protected messageCallbacks: Array<(msg: string) => void> = [];
  protected lastReply = '';

  abstract getPlatform(): string;
  abstract isReady(): boolean;
  abstract sendMessage(text: string, image?: string): Promise<string>;
  abstract uploadImage(base64Image: string): Promise<void>;
  abstract newChat(): Promise<void>;
  abstract getChatHistory(): Promise<any[]>;
  abstract getLastReply(): string;

  /**
   * Wait for reply (generic implementation)
   */
  async waitForReply(timeout = 60000): Promise<string> {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      let lastContent = '';
      let stableCount = 0;

      const checkInterval = window.setInterval(() => {
        const currentContent = this.getLastReply();
        
        if (currentContent === lastContent && currentContent.length > 0) {
          stableCount++;
          if (stableCount >= 4) { // 4 consecutive checks (2 seconds) with same content
            window.clearInterval(checkInterval);
            resolve(currentContent);
          }
        } else {
          stableCount = 0;
          lastContent = currentContent;
        }

        if (Date.now() - startTime > timeout) {
          window.clearInterval(checkInterval);
          reject(new Error('等待回复超时'));
        }
      }, 500);
    });
  }

  /**
   * Initialize MutationObserver
   */
  protected initObserver(selector: string): void {
    const target = document.querySelector(selector);
    if (!target) return;

    this.observer = new MutationObserver((mutations) => {
      const lastMessage = this.getLastReply();
      if (lastMessage && lastMessage !== this.lastReply) {
        this.lastReply = lastMessage;
        this.messageCallbacks.forEach(cb => cb(lastMessage));
      }
    });

    this.observer.observe(target, {
      childList: true,
      subtree: true,
      characterData: true
    });
  }

  /**
   * Add message listener
   */
  addMessageListener(callback: (msg: string) => void): void {
    this.messageCallbacks.push(callback);
  }

  /**
   * Remove message listener
   */
  removeMessageListener(callback: (msg: string) => void): void {
    const index = this.messageCallbacks.indexOf(callback);
    if (index > -1) {
      this.messageCallbacks.splice(index, 1);
    }
  }

  /**
   * Base64 to File conversion
   */
  protected async base64ToFile(base64: string, filename = 'image.png'): Promise<File> {
    const response = await fetch(base64);
    const blob = await response.blob();
    return new File([blob], filename, { type: blob.type || 'image/png' });
  }

  /**
   * Sleep helper
   */
  protected sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Dispose resources
   */
  dispose(): void {
    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
    }
    this.messageCallbacks = [];
  }
}

/**
 * Controller Registry
 * Manages platform-specific controllers
 */
class ControllerRegistry {
  private controllers: Map<string, new () => PageController> = new Map();

  register(platform: string, controllerClass: new () => PageController): void {
    this.controllers.set(platform, controllerClass);
  }

  create(platform: string): PageController | null {
    const ControllerClass = this.controllers.get(platform);
    if (ControllerClass) {
      return new ControllerClass();
    }
    return null;
  }

  detectPlatform(): string | null {
    const hostname = window.location.hostname;
    
    if (hostname.includes('kimi.com') || hostname.includes('moonshot.cn')) {
      return 'kimi';
    }
    if (hostname.includes('deepseek.com')) {
      return 'deepseek';
    }
    
    return null;
  }
}

export const controllerRegistry = new ControllerRegistry();
