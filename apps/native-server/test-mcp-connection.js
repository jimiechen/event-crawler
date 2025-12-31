#!/usr/bin/env node

const http = require('http');
const { URL } = require('url');
const net = require('net');

// MCP测试配置
const MCP_URL = 'http://127.0.0.1:56889/mcp';
const TIMEOUT = 5000; // 5秒超时

// 颜色输出函数
const colors = {
  green: (text) => `\x1b[32m${text}\x1b[0m`,
  red: (text) => `\x1b[31m${text}\x1b[0m`,
  yellow: (text) => `\x1b[33m${text}\x1b[0m`,
  blue: (text) => `\x1b[34m${text}\x1b[0m`,
  cyan: (text) => `\x1b[36m${text}\x1b[0m`,
};

// 日志函数
function log(level, message, data = null) {
  const timestamp = new Date().toISOString();
  const prefix = `[${timestamp}] [${level.toUpperCase()}]`;

  switch (level) {
    case 'info':
      console.log(colors.blue(prefix), message);
      break;
    case 'success':
      console.log(colors.green(prefix), message);
      break;
    case 'error':
      console.log(colors.red(prefix), message);
      break;
    case 'warn':
      console.log(colors.yellow(prefix), message);
      break;
    default:
      console.log(prefix, message);
  }

  if (data) {
    console.log(colors.cyan('Data:'), JSON.stringify(data, null, 2));
  }
}

// HTTP请求函数
function makeRequest(url, method = 'GET', data = null, headers = {}) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname + urlObj.search,
      method: method,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json, text/event-stream',
        'User-Agent': 'MCP-Test-Client/1.0',
        ...headers,
      },
      timeout: TIMEOUT,
    };

    if (data && method !== 'GET') {
      const postData = JSON.stringify(data);
      options.headers['Content-Length'] = Buffer.byteLength(postData);
    }

    const req = http.request(options, (res) => {
      let body = '';

      res.on('data', (chunk) => {
        body += chunk;
      });

      res.on('end', () => {
        try {
          const response = {
            statusCode: res.statusCode,
            statusMessage: res.statusMessage,
            headers: res.headers,
            body: body,
            data: null,
          };

          // 尝试解析JSON
          if (body) {
            try {
              response.data = JSON.parse(body);
            } catch (e) {
              // 如果不是JSON，保持原始body
            }
          }

          resolve(response);
        } catch (error) {
          reject(error);
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.on('timeout', () => {
      req.destroy();
      reject(new Error(`Request timeout after ${TIMEOUT}ms`));
    });

    if (data && method !== 'GET') {
      req.write(JSON.stringify(data));
    }

    req.end();
  });
}

// 测试基本连接
async function testBasicConnection() {
  log('info', '测试基本HTTP连接...');

  try {
    const response = await makeRequest(MCP_URL);

    if (response.statusCode === 200) {
      log('success', '基本连接成功', {
        statusCode: response.statusCode,
        statusMessage: response.statusMessage,
        contentType: response.headers['content-type'],
      });
      return true;
    } else if (
      response.statusCode === 400 &&
      response.data &&
      response.data.error &&
      response.data.error.includes('MCP session ID')
    ) {
      log('success', 'MCP服务器正常运行（需要session ID）', {
        statusCode: response.statusCode,
        message: response.data.error,
      });
      return true;
    } else {
      log('warn', `连接成功但状态码异常: ${response.statusCode}`, response);
      return false;
    }
  } catch (error) {
    log('error', '基本连接失败', {
      message: error.message,
      code: error.code,
      errno: error.errno,
    });
    return false;
  }
}

// 解析SSE数据
function parseSSEData(sseText) {
  const lines = sseText.split('\n');
  let eventType = null;
  let data = null;

  for (const line of lines) {
    if (line.startsWith('event: ')) {
      eventType = line.substring(7);
    } else if (line.startsWith('data: ')) {
      try {
        data = JSON.parse(line.substring(6));
      } catch (e) {
        // 忽略解析错误
      }
    }
  }

  return { eventType, data };
}

// 测试MCP初始化
async function testMCPInitialize() {
  log('info', '测试MCP初始化请求...');

  const initRequest = {
    jsonrpc: '2.0',
    id: 1,
    method: 'initialize',
    params: {
      protocolVersion: '2024-11-05',
      capabilities: {
        roots: {
          listChanged: true,
        },
        sampling: {},
      },
      clientInfo: {
        name: 'test-client',
        version: '1.0.0',
      },
    },
  };

  try {
    const response = await makeRequest(MCP_URL, 'POST', initRequest);

    if (response.statusCode === 200) {
      const sessionId = response.headers['mcp-session-id'];

      if (response.headers['content-type'] === 'text/event-stream' && response.body) {
        // 解析SSE响应
        const sseData = parseSSEData(response.body);
        if (sseData.data && sseData.data.result) {
          log('success', 'MCP初始化成功（SSE模式）', {
            sessionId: sessionId,
            serverInfo: sseData.data.result.serverInfo,
            capabilities: sseData.data.result.capabilities,
          });
          return { sessionId, result: sseData.data.result };
        }
      } else if (response.data) {
        log('success', 'MCP初始化成功', response.data);
        return { sessionId, result: response.data.result };
      }

      log('error', 'MCP初始化响应格式异常', response);
      return null;
    } else {
      log('error', 'MCP初始化失败', response);
      return null;
    }
  } catch (error) {
    log('error', 'MCP初始化请求失败', {
      message: error.message,
      code: error.code,
    });
    return null;
  }
}

// 测试工具列表
async function testToolsList(sessionId) {
  log('info', '测试工具列表请求...');

  const toolsRequest = {
    jsonrpc: '2.0',
    id: 2,
    method: 'tools/list',
    params: {},
  };

  try {
    const response = await makeRequest(MCP_URL, 'POST', toolsRequest, {
      'MCP-Session-ID': sessionId,
    });

    if (response.statusCode === 200) {
      if (response.headers['content-type'] === 'text/event-stream' && response.body) {
        // 解析SSE响应
        const sseData = parseSSEData(response.body);
        if (sseData.data && sseData.data.result) {
          log('success', '工具列表获取成功（SSE模式）', {
            tools: sseData.data.result.tools || [],
          });
          return sseData.data.result;
        }
      } else if (response.data) {
        log('success', '工具列表获取成功', response.data);
        return response.data.result;
      }

      log('error', '工具列表响应格式异常', response);
      return null;
    } else {
      log('error', '工具列表获取失败', response);
      return null;
    }
  } catch (error) {
    log('error', '工具列表请求失败', {
      message: error.message,
      code: error.code,
    });
    return null;
  }
}

// 网络诊断
async function networkDiagnostics() {
  log('info', '开始网络诊断...');

  return new Promise((resolve) => {
    const socket = new net.Socket();
    const timeout = 3000;

    socket.setTimeout(timeout);

    socket.on('connect', () => {
      log('success', '端口56889可访问');
      socket.destroy();
      resolve(true);
    });

    socket.on('timeout', () => {
      log('error', '端口连接超时');
      socket.destroy();
      resolve(false);
    });

    socket.on('error', (error) => {
      log('error', '端口连接失败', {
        message: error.message,
        code: error.code,
      });
      resolve(false);
    });

    socket.connect(56889, '127.0.0.1');
  });
}

// 主测试函数
async function runTests() {
  console.log(colors.cyan('='.repeat(60)));
  console.log(colors.cyan('           MCP连接测试脚本'));
  console.log(colors.cyan('='.repeat(60)));
  console.log();

  const results = {
    networkDiagnostics: false,
    basicConnection: false,
    mcpInitialize: false,
    toolsList: false,
  };

  // 1. 网络诊断
  results.networkDiagnostics = await networkDiagnostics();
  console.log();

  // 2. 基本连接测试
  results.basicConnection = await testBasicConnection();
  console.log();

  // 3. MCP初始化测试
  let sessionId = null;
  if (results.basicConnection) {
    const initResult = await testMCPInitialize();
    results.mcpInitialize = !!initResult;
    if (initResult && initResult.sessionId) {
      sessionId = initResult.sessionId;
    }
    console.log();

    // 4. 工具列表测试
    if (results.mcpInitialize && sessionId) {
      const toolsResult = await testToolsList(sessionId);
      results.toolsList = !!toolsResult;
      console.log();
    }
  }

  // 输出测试结果摘要
  console.log(colors.cyan('='.repeat(60)));
  console.log(colors.cyan('           测试结果摘要'));
  console.log(colors.cyan('='.repeat(60)));

  Object.entries(results).forEach(([test, passed]) => {
    const status = passed ? colors.green('✓ 通过') : colors.red('✗ 失败');
    const testName = {
      networkDiagnostics: '网络诊断',
      basicConnection: '基本连接',
      mcpInitialize: 'MCP初始化',
      toolsList: '工具列表',
    }[test];

    console.log(`${testName.padEnd(15)} ${status}`);
  });

  console.log();

  const passedCount = Object.values(results).filter(Boolean).length;
  const totalCount = Object.keys(results).length;

  if (passedCount === totalCount) {
    log('success', `所有测试通过! (${passedCount}/${totalCount})`);
  } else {
    log('warn', `部分测试失败 (${passedCount}/${totalCount})`);

    console.log();
    console.log(colors.yellow('故障排除建议:'));

    if (!results.networkDiagnostics) {
      console.log('• 检查MCP服务器是否在56889端口运行');
      console.log('• 运行: node start-http-server.js');
    }

    if (!results.basicConnection) {
      console.log('• 检查HTTP服务器配置');
      console.log('• 检查防火墙设置');
      console.log('• 查看服务器日志');
    }
  }

  console.log();
}

// 运行测试
if (require.main === module) {
  runTests().catch((error) => {
    log('error', '测试运行失败', {
      message: error.message,
      stack: error.stack,
    });
    process.exit(1);
  });
}

module.exports = {
  makeRequest,
  testBasicConnection,
  testMCPInitialize,
  testToolsList,
  networkDiagnostics,
  runTests,
};
