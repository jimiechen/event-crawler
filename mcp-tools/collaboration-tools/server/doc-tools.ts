/**
 * 协作文档MCP工具定义
 * 提供协作文档管理相关的MCP工具
 */

import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * 创建协作文档工具
 */
export const createCollaborationDocTool: Tool = {
  name: 'create_collaboration_doc',
  description: '创建新的协作文档',
  inputSchema: {
    type: 'object',
    properties: {
      doc_type: {
        type: 'string',
        description: '文档类型',
        enum: ['daily_progress', 'weekly_report', 'technical_review', 'test_report']
      },
      title: {
        type: 'string',
        description: '文档标题'
      },
      content: {
        type: 'string',
        description: '文档内容'
      },
      author: {
        type: 'string',
        description: '作者模型名称（GLM4.7/Gemini/DeepSeek）',
        enum: ['GLM4.7', 'Gemini', 'DeepSeek'],
        default: 'GLM4.7'
      }
    },
    required: ['doc_type', 'title', 'content']
  }
};

/**
 * 更新协作文档工具
 */
export const updateCollaborationDocTool: Tool = {
  name: 'update_collaboration_doc',
  description: '更新现有协作文档',
  inputSchema: {
    type: 'object',
    properties: {
      doc_path: {
        type: 'string',
        description: '文档路径（相对于collaboration_docs目录）'
      },
      content: {
        type: 'string',
        description: '更新后的内容'
      },
      signature: {
        type: 'string',
        description: '署名信息（格式: [时间] @ModelName: 操作描述）'
      },
      author: {
        type: 'string',
        description: '作者模型名称（GLM4.7/Gemini/DeepSeek）',
        enum: ['GLM4.7', 'Gemini', 'DeepSeek'],
        default: 'GLM4.7'
      }
    },
    required: ['doc_path', 'content']
  }
};

/**
 * 获取协作文档工具
 */
export const getCollaborationDocTool: Tool = {
  name: 'get_collaboration_doc',
  description: '获取协作文档内容',
  inputSchema: {
    type: 'object',
    properties: {
      doc_path: {
        type: 'string',
        description: '文档路径（相对于collaboration_docs目录）'
      }
    },
    required: ['doc_path']
  }
};

/**
 * 列出协作文档工具
 */
export const listCollaborationDocsTool: Tool = {
  name: 'list_collaboration_docs',
  description: '列出所有协作文档',
  inputSchema: {
    type: 'object',
    properties: {
      doc_type: {
        type: 'string',
        description: '文档类型（可选，不提供则列出所有类型）',
        enum: ['daily_progress', 'weekly_report', 'technical_review', 'test_report']
      }
    }
  }
};

/**
 * 导出所有协作工具
 */
export const collaborationTools: Tool[] = [
  createCollaborationDocTool,
  updateCollaborationDocTool,
  getCollaborationDocTool,
  listCollaborationDocsTool
];