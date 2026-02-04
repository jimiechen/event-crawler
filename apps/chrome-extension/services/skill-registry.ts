/**
 * Skill Registry and Executor
 * Manages skill definitions and execution
 */

import { wsClient } from './websocket-client';

// Skill parameter definition
export interface SkillParameter {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  description: string;
  required: boolean;
  default?: any;
}

// Skill definition
export interface SkillDefinition {
  name: string;
  description: string;
  parameters: Record<string, SkillParameter>;
  execute: (context: SkillContext) => Promise<any>;
}

// Skill execution context
export interface SkillContext {
  parameters: Record<string, any>;
  metadata?: Record<string, any>;
}

// Skill execution result
export interface SkillResult {
  success: boolean;
  data?: any;
  error?: string;
}

/**
 * Skill Registry
 * Manages all available skills
 */
class SkillRegistry {
  private skills: Map<string, SkillDefinition> = new Map();

  /**
   * Register a skill
   */
  register(skill: SkillDefinition): void {
    this.skills.set(skill.name, skill);
    console.log(`Skill registered: ${skill.name}`);
  }

  /**
   * Get a skill by name
   */
  get(name: string): SkillDefinition | undefined {
    return this.skills.get(name);
  }

  /**
   * Get all registered skills
   */
  getAll(): SkillDefinition[] {
    return Array.from(this.skills.values());
  }

  /**
   * Execute a skill
   */
  async execute(name: string, context: SkillContext): Promise<SkillResult> {
    const skill = this.skills.get(name);
    if (!skill) {
      return {
        success: false,
        error: `Skill not found: ${name}`
      };
    }

    try {
      // Validate parameters
      const validationError = this.validateParameters(skill, context.parameters);
      if (validationError) {
        return {
          success: false,
          error: validationError
        };
      }

      // Execute skill
      const result = await skill.execute(context);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * Validate skill parameters
   */
  private validateParameters(
    skill: SkillDefinition,
    parameters: Record<string, any>
  ): string | null {
    for (const [name, param] of Object.entries(skill.parameters)) {
      if (param.required && !(name in parameters)) {
        return `Missing required parameter: ${name}`;
      }

      if (name in parameters) {
        const value = parameters[name];
        const expectedType = param.type;
        const actualType = typeof value;

        if (expectedType === 'array' && !Array.isArray(value)) {
          return `Parameter ${name} should be an array`;
        }
        if (expectedType !== 'array' && actualType !== expectedType) {
          return `Parameter ${name} should be of type ${expectedType}`;
        }
      }
    }

    return null;
  }
}

// Export singleton instance
export const skillRegistry = new SkillRegistry();

// ============================================================================
// Predefined Skills
// ============================================================================

/**
 * Helper function to find or create a tab for a platform
 */
async function findOrCreateTab(url: string, newChat = false): Promise<chrome.tabs.Tab> {
  // Query existing tabs
  const tabs = await chrome.tabs.query({ url: `${url}/*` });
  
  if (tabs.length > 0 && !newChat) {
    // Use existing tab
    const tab = tabs[0];
    await chrome.tabs.update(tab.id!, { active: true });
    return tab;
  }

  // Create new tab
  const tab = await chrome.tabs.create({
    url: newChat ? `${url}/chat/new` : url,
    active: true
  });

  // Wait for page to load
  await new Promise(resolve => setTimeout(resolve, 3000));

  return tab;
}

/**
 * Kimi Chat Skill
 */
skillRegistry.register({
  name: 'kimi_chat',
  description: '与Kimi AI进行对话，支持文本和图片',
  parameters: {
    message: {
      type: 'string',
      description: '要发送的消息文本',
      required: true
    },
    image: {
      type: 'string',
      description: '图片的base64编码（可选）',
      required: false
    },
    new_chat: {
      type: 'boolean',
      description: '是否开启新对话',
      required: false,
      default: false
    }
  },
  async execute(context) {
    const { message, image, new_chat } = context.parameters;
    
    // Find or create Kimi tab
    const tab = await findOrCreateTab('https://www.kimi.com', new_chat);

    // Inject content script if needed
    try {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id! },
        files: ['content/adapters/kimi-adapter.js']
      });
    } catch (e) {
      // Script might already be injected
    }

    // Send message to content script
    const response = await chrome.tabs.sendMessage(tab.id!, {
      action: 'send_message',
      params: { message, image }
    });

    if (!response.success) {
      throw new Error(response.error);
    }

    return {
      reply: response.reply,
      platform: 'kimi',
      timestamp: new Date().toISOString()
    };
  }
});

/**
 * DeepSeek Chat Skill
 */
skillRegistry.register({
  name: 'deepseek_chat',
  description: '与DeepSeek AI进行对话，支持文本和图片',
  parameters: {
    message: {
      type: 'string',
      description: '要发送的消息文本',
      required: true
    },
    image: {
      type: 'string',
      description: '图片的base64编码（可选）',
      required: false
    },
    new_chat: {
      type: 'boolean',
      description: '是否开启新对话',
      required: false,
      default: false
    }
  },
  async execute(context) {
    const { message, image, new_chat } = context.parameters;
    
    // Find or create DeepSeek tab
    const tab = await findOrCreateTab('https://chat.deepseek.com', new_chat);

    // Inject content script if needed
    try {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id! },
        files: ['content/adapters/deepseek-adapter.js']
      });
    } catch (e) {
      // Script might already be injected
    }

    // Send message to content script
    const response = await chrome.tabs.sendMessage(tab.id!, {
      action: 'send_message',
      params: { message, image }
    });

    if (!response.success) {
      throw new Error(response.error);
    }

    return {
      reply: response.reply,
      platform: 'deepseek',
      timestamp: new Date().toISOString()
    };
  }
});

/**
 * Upload Image Skill
 */
skillRegistry.register({
  name: 'upload_image',
  description: '上传图片到AI平台',
  parameters: {
    platform: {
      type: 'string',
      description: '目标平台 (kimi 或 deepseek)',
      required: true
    },
    image_data: {
      type: 'string',
      description: '图片的base64编码',
      required: true
    }
  },
  async execute(context) {
    const { platform, image_data } = context.parameters;
    
    const url = platform === 'kimi' 
      ? 'https://www.kimi.com' 
      : 'https://chat.deepseek.com';
    
    const tab = await findOrCreateTab(url);

    // Inject appropriate adapter
    const adapterFile = `content/adapters/${platform}-adapter.js`;
    try {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id! },
        files: [adapterFile]
      });
    } catch (e) {
      // Script might already be injected
    }

    // Upload image
    const response = await chrome.tabs.sendMessage(tab.id!, {
      action: 'upload_image',
      params: { image: image_data }
    });

    if (!response.success) {
      throw new Error(response.error);
    }

    return {
      success: true,
      platform,
      timestamp: new Date().toISOString()
    };
  }
});

/**
 * New Chat Skill
 */
skillRegistry.register({
  name: 'new_chat',
  description: '在指定平台开启新对话',
  parameters: {
    platform: {
      type: 'string',
      description: '目标平台 (kimi 或 deepseek)',
      required: true
    }
  },
  async execute(context) {
    const { platform } = context.parameters;
    
    const url = platform === 'kimi' 
      ? 'https://www.kimi.com' 
      : 'https://chat.deepseek.com';
    
    const tab = await findOrCreateTab(url, true);

    // Inject appropriate adapter
    const adapterFile = `content/adapters/${platform}-adapter.js`;
    try {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id! },
        files: [adapterFile]
      });
    } catch (e) {
      // Script might already be injected
    }

    // Start new chat
    const response = await chrome.tabs.sendMessage(tab.id!, {
      action: 'new_chat'
    });

    if (!response.success) {
      throw new Error(response.error);
    }

    return {
      success: true,
      platform,
      tab_id: tab.id,
      timestamp: new Date().toISOString()
    };
  }
});

/**
 * Get Chat History Skill
 */
skillRegistry.register({
  name: 'get_chat_history',
  description: '获取当前对话历史',
  parameters: {
    platform: {
      type: 'string',
      description: '目标平台 (kimi 或 deepseek)',
      required: true
    }
  },
  async execute(context) {
    const { platform } = context.parameters;
    
    const url = platform === 'kimi' 
      ? 'https://www.kimi.com' 
      : 'https://chat.deepseek.com';
    
    const tabs = await chrome.tabs.query({ url: `${url}/*` });
    
    if (tabs.length === 0) {
      throw new Error(`No ${platform} tab found`);
    }

    const tab = tabs[0];

    // Get history
    const response = await chrome.tabs.sendMessage(tab.id!, {
      action: 'get_history'
    });

    if (!response.success) {
      throw new Error(response.error);
    }

    return {
      history: response.history,
      platform,
      timestamp: new Date().toISOString()
    };
  }
});

/**
 * Analyze Image Skill (using backend OCR)
 */
skillRegistry.register({
  name: 'analyze_image',
  description: '使用OCR或视觉模型分析图片',
  parameters: {
    image_data: {
      type: 'string',
      description: '图片的base64编码',
      required: true
    },
    mode: {
      type: 'string',
      description: '分析模式 (ocr 或 vision)',
      required: false,
      default: 'ocr'
    },
    prompt: {
      type: 'string',
      description: '视觉分析提示词（vision模式）',
      required: false,
      default: '描述这张图片'
    }
  },
  async execute(context) {
    const { image_data, mode, prompt } = context.parameters;
    
    // Call backend API
    const BACKEND_URL = 'http://localhost:8000';
    
    if (mode === 'ocr') {
      const response = await fetch(`${BACKEND_URL}/api/ocr/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: image_data })
      });
      
      const result = await response.json();
      return {
        text: result.text,
        mode: 'ocr'
      };
    } else {
      const response = await fetch(`${BACKEND_URL}/api/ocr/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: image_data, prompt })
      });
      
      const result = await response.json();
      return {
        analysis: result.analysis,
        mode: 'vision'
      };
    }
  }
});

/**
 * Get Prompt Template Skill
 */
skillRegistry.register({
  name: 'get_prompt',
  description: '获取提示词模板',
  parameters: {
    name: {
      type: 'string',
      description: '提示词模板名称',
      required: true
    }
  },
  async execute(context) {
    const { name } = context.parameters;
    
    const BACKEND_URL = 'http://localhost:8000';
    const response = await fetch(`${BACKEND_URL}/api/prompts/by-name/${name}`);
    
    if (!response.ok) {
      throw new Error(`Prompt not found: ${name}`);
    }
    
    const result = await response.json();
    return result.prompt;
  }
});

/**
 * List Prompts Skill
 */
skillRegistry.register({
  name: 'list_prompts',
  description: '列出所有提示词模板',
  parameters: {
    category: {
      type: 'string',
      description: '分类筛选',
      required: false
    },
    tags: {
      type: 'string',
      description: '标签筛选（逗号分隔）',
      required: false
    }
  },
  async execute(context) {
    const { category, tags } = context.parameters;
    
    const BACKEND_URL = 'http://localhost:8000';
    let url = `${BACKEND_URL}/api/prompts/`;
    
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (tags) params.append('tags', tags);
    
    if (params.toString()) {
      url += `?${params.toString()}`;
    }
    
    const response = await fetch(url);
    const result = await response.json();
    
    return {
      prompts: result.prompts,
      total: result.prompts.length
    };
  }
});
