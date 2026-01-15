/**
 * DeepSeek MCP服务器
 * 实现MCP协议，提供DeepSeek工具
 */
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  deepseekTools,
  deepseekLoginTool,
  sendMessageToDeepseekTool,
  startDeepseekSessionTool,
  getDeepseekConversationsTool
} from './deepseek-tools.js';
import axios from 'axios';

// MCP API基础URL
const API_BASE_URL = process.env.MCP_API_URL || 'http://localhost:8000';

/**
 * 调用MCP API
 */
async function callMCPAPI(endpoint: string, data: any): Promise<any> {
  try {
    const response = await axios.post(`${API_BASE_URL}/mcp${endpoint}`, data, {
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: 120000 // 2分钟超时
    });
    return response.data;
  } catch (error: any) {
    console.error(`MCP API调用失败: ${endpoint}`, error.response?.data || error.message);
    throw new Error(error.response?.data?.detail || error.message);
  }
}

/**
 * 创建MCP服务器
 */
async function createServer() {
  const server = new Server(
    {
      name: 'deepseek-mcp-server',
      version: '1.0.0'
    },
    {
      capabilities: {
        tools: {}
      }
    }
  );

  // 注册工具列表处理器
  server.setRequestHandler('tools/list', {
    tools: deepseekTools
  });

  // 注册工具调用处理器
  server.setRequestHandler('tools/call', async (request: any) => {
    const { name, arguments: args } = request.params;

    try {
      switch (name) {
        case 'deepseek_login':
          return await handleDeepseekLogin(args);
        
        case 'send_message_to_deepseek':
          return await handleSendMessageToDeepseek(args);
        
        case 'start_deepseek_session':
          return await handleStartDeepseekSession(args);
        
        case 'get_deepseek_conversations':
          return await handleGetDeepseekConversations(args);
        
        default:
          throw new Error(`未知工具: ${name}`);
      }
    } catch (error: any) {
      return {
        content: [
          {
            type: 'text',
            text: `错误: ${error.message}`
          }
        ],
        isError: true
      };
    }
  });

  return server;
}

/**
 * 处理DeepSeek登录
 */
async function handleDeepSeekLogin(args: any) {
  const { email, password } = args;
  
  const result = await callMCPAPI('/deepseek/login', {
    email,
    password
  });
  
  return {
    content: [
      {
        type: 'text',
        text: result.success 
          ? `DeepSeek登录成功`
          : `DeepSeek登录失败: ${result.message || result.error}`
      }
    ]
  };
}

/**
 * 处理发送消息给DeepSeek
 */
async function handleSendMessageToDeepseek(args: any) {
  const { message, conversation_id, from_model = 'GLM4.7' } = args;
  
  const result = await callMCPAPI('/deepseek/send', {
    message,
    conversation_id,
    from_model
  });
  
  if (!result.success) {
    throw new Error(result.error || '发送消息失败');
  }
  
  return {
    content: [
      {
        type: 'text',
        text: `DeepSeek响应:\n\n${result.response}`
      }
    ],
    metadata: {
      conversation_id: result.conversation_id,
      timestamp: result.timestamp
    }
  };
}

/**
 * 处理开始新的DeepSeek会话
 */
async function handleStartDeepseekSession(args: any) {
  const { from_model = 'GLM4.7' } = args;
  
  const result = await callMCPAPI('/deepseek/session/new', {
    from_model
  });
  
  return {
    content: [
      {
        type: 'text',
        text: result.success
          ? `新会话已开始，会话ID: ${result.conversation_id}`
          : `开始新会话失败: ${result.message || result.error}`
      }
    ],
    metadata: {
      conversation_id: result.conversation_id
    }
  };
}

/**
 * 处理获取DeepSeek对话历史
 */
async function handleGetDeepseekConversations(args: any) {
  const { conversation_id } = args;
  
  const result = await callMCPAPI('/deepseek/conversations', {
    conversation_id
  });
  
  if (!result.success) {
    throw new Error(result.error || '获取对话历史失败');
  }
  
  let text = '';
  if (conversation_id) {
    const conv = result.conversation;
    text = `对话详情:\n\n` +
      `会话ID: ${conversation_id}\n` +
      `最后消息: ${conv.last_message}\n` +
      `最后响应: ${conv.last_response}\n` +
      `时间戳: ${conv.timestamp}\n` +
      `发起模型: ${conv.from_model}`;
  } else {
    const conversations = result.conversations;
    text = `活跃对话列表 (${conversations.length}个):\n\n`;
    Object.entries(conversations).forEach(([id, conv]: [string, any]) => {
      text += `- ${id}: ${conv.last_message}\n`;
    });
  }
  
  return {
    content: [
      {
        type: 'text',
        text
      }
    ]
  };
}

/**
 * 主函数
 */
async function main() {
  console.log('DeepSeek MCP服务器启动中...');
  
  const server = await createServer();
  const transport = new StdioServerTransport();
  
  await server.connect(transport);
  
  console.error('DeepSeek MCP服务器已启动');
}

// 启动服务器
main().catch((error) => {
  console.error('DeepSeek MCP服务器启动失败:', error);
  process.exit(1);
});