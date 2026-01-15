/**
 * 协作文档MCP服务器
 * 实现MCP协议，提供协作文档管理工具
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  collaborationTools,
  createCollaborationDocTool,
  updateCollaborationDocTool,
  getCollaborationDocTool,
  listCollaborationDocsTool
} from './doc-tools.js';
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
      timeout: 60000 // 1分钟超时
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
      name: 'collaboration-mcp-server',
      version: '1.0.0'
    },
    {
      capabilities: {
        tools: {}
      }
    }
  );

  // 注册工具列表处理器
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: collaborationTools
    };
  });

  // 注册工具调用处理器
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments } = request.params;

    try {
      switch (name) {
        case 'create_collaboration_doc':
          return await handleCreateCollaborationDoc(arguments);
        
        case 'update_collaboration_doc':
          return await handleUpdateCollaborationDoc(arguments);
        
        case 'get_collaboration_doc':
          return await handleGetCollaborationDoc(arguments);
        
        case 'list_collaboration_docs':
          return await handleListCollaborationDocs(arguments);
        
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
 * 处理创建协作文档
 */
async function handleCreateCollaborationDoc(args: any) {
  const { doc_type, title, content, author = 'GLM4.7' } = args;
  
  const result = await callMCPAPI('/collaboration/doc/create', {
    doc_type,
    title,
    content,
    author
  });
  
  if (!result.success) {
    throw new Error(result.error || '创建文档失败');
  }
  
  return {
    content: [
      {
        type: 'text',
        text: `文档创建成功:\n\n` +
          `文件路径: ${result.filepath}\n` +
          `文件名: ${result.filename}`
      }
    ]
  };
}

/**
 * 处理更新协作文档
 */
async function handleUpdateCollaborationDoc(args: any) {
  const { doc_path, content, signature, author = 'GLM4.7' } = args;
  
  const result = await callMCPAPI('/collaboration/doc/update', {
    doc_path,
    content,
    signature,
    author
  });
  
  if (!result.success) {
    throw new Error(result.error || '更新文档失败');
  }
  
  return {
    content: [
      {
        type: 'text',
        text: `文档更新成功:\n\n` +
          `文件路径: ${result.filepath}\n` +
          `备份路径: ${result.backup}`
      }
    ]
  };
}

/**
 * 处理获取协作文档
 */
async function handleGetCollaborationDoc(args: any) {
  const { doc_path } = args;
  
  const result = await callMCPAPI(`/collaboration/doc/${doc_path}`, {});
  
  if (!result.success) {
    throw new Error(result.error || '获取文档失败');
  }
  
  return {
    content: [
      {
        type: 'text',
        text: result.content
      }
    ],
    metadata: {
      filepath: result.filepath,
      metadata: result.metadata
    }
  };
}

/**
 * 处理列出协作文档
 */
async function handleListCollaborationDocs(args: any) {
  const { doc_type } = args;
  
  const result = await callMCPAPI('/collaboration/docs', {
    doc_type
  });
  
  if (!result.success) {
    throw new Error(result.error || '列出文档失败');
  }
  
  let text = `协作文档列表 (${result.count}个):\n\n`;
  result.documents.forEach((doc: any) => {
    text += `- ${doc.name}\n`;
    text += `  路径: ${doc.path}\n`;
    text += `  类型: ${doc.type}\n`;
    text += `  修改时间: ${new Date(doc.modified * 1000).toLocaleString('zh-CN')}\n\n`;
  });
  
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
  console.log('协作文档MCP服务器启动中...');
  
  const server = await createServer();
  const transport = new StdioServerTransport();
  
  await server.connect(transport);
  
  console.error('协作文档MCP服务器已启动');
}

// 启动服务器
main().catch((error) => {
  console.error('协作文档MCP服务器启动失败:', error);
  process.exit(1);
});