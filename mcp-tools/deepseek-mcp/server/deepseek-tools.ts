/**
 * DeepSeek MCP工具定义
 * 提供DeepSeek对话相关的MCP工具
 */

import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * DeepSeek登录工具
 */
export const deepseekLoginTool: Tool = {
  name: 'deepseek_login',
  description: '登录DeepSeek账号',
  inputSchema: {
    type: 'object',
    properties: {
      email: {
        type: 'string',
        description: 'DeepSeek账号邮箱'
      },
      password: {
        type: 'string',
        description: 'DeepSeek账号密码'
      }
    },
    required: ['email', 'password']
  }
};

/**
 * 发送消息给DeepSeek工具
 */
export const sendMessageToDeepseekTool: Tool = {
  name: 'send_message_to_deepseek',
  description: '发送消息给DeepSeek并获取响应',
  inputSchema: {
    type: 'object',
    properties: {
      message: {
        type: 'string',
        description: '要发送给DeepSeek的消息内容'
      },
      conversation_id: {
        type: 'string',
        description: '对话ID（可选，如果不提供则使用当前对话）'
      },
      from_model: {
        type: 'string',
        description: '发起模型名称（GLM4.7/Gemini）',
        enum: ['GLM4.7', 'Gemini'],
        default: 'GLM4.7'
      }
    },
    required: ['message']
  }
};

/**
 * 开始新的DeepSeek会话工具
 */
export const startDeepseekSessionTool: Tool = {
  name: 'start_deepseek_session',
  description: '开始新的DeepSeek对话会话',
  inputSchema: {
    type: 'object',
    properties: {
      from_model: {
        type: 'string',
        description: '发起模型名称（GLM4.7/Gemini）',
        enum: ['GLM4.7', 'Gemini'],
        default: 'GLM4.7'
      }
    }
  }
};

/**
 * 获取DeepSeek对话历史工具
 */
export const getDeepseekConversationsTool: Tool = {
  name: 'get_deepseek_conversations',
  description: '获取DeepSeek对话历史',
  inputSchema: {
    type: 'object',
    properties: {
      conversation_id: {
        type: 'string',
        description: '对话ID（可选，如果不提供则返回所有对话）'
      }
    }
  }
};

/**
 * 导出所有DeepSeek工具
 */
export const deepseekTools: Tool[] = [
  deepseekLoginTool,
  sendMessageToDeepseekTool,
  startDeepseekSessionTool,
  getDeepseekConversationsTool
];