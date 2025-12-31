const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

// 发送Native Messaging格式的消息
function sendNativeMessage(host, message) {
  const messageString = JSON.stringify(message);
  const messageBuffer = Buffer.from(messageString);
  const headerBuffer = Buffer.alloc(4);
  headerBuffer.writeUInt32LE(messageBuffer.length, 0);
  
  console.log('📤 发送Native消息:', JSON.stringify(message, null, 2));
  host.stdin.write(Buffer.concat([headerBuffer, messageBuffer]));
}

// 发送MCP请求（带正确的Accept头）
function sendMCPRequest(port, method, params = {}, id = 1, sessionId = null) {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify({
      jsonrpc: '2.0',
      id: id,
      method: method,
      params: params
    });

    const headers = {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(postData),
      'Accept': 'application/json, text/event-stream',
      'User-Agent': 'MCP-Test-Client/1.0'
    };

    if (sessionId) {
      headers['mcp-session-id'] = sessionId;
    }

    const options = {
      hostname: 'localhost',
      port: port,
      path: '/mcp',
      method: 'POST',
      headers: headers
    };

    console.log(`📤 发送MCP请求到 http://localhost:${port}/mcp`);
    console.log('📦 请求数据:', postData);
    console.log('📋 请求头:', headers);

    const req = http.request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        console.log('📨 MCP响应状态:', res.statusCode);
        console.log('📨 MCP响应头:', res.headers);
        console.log('📨 MCP响应数据:', data);
        
        try {
          const response = JSON.parse(data);
          resolve({ statusCode: res.statusCode, headers: res.headers, data: response });
        } catch (error) {
          resolve({ statusCode: res.statusCode, headers: res.headers, rawData: data });
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.write(postData);
    req.end();
  });
}

// 测试完整的MCP流程
async function testFinalMCP() {
  console.log('🚀 开始最终MCP测试（端口冲突已解决）...\n');
  
  const hostPath = path.join(__dirname, 'dist', 'run_host.sh');
  const host = spawn(hostPath, [], {
    stdio: ['pipe', 'pipe', 'pipe']
  });

  let buffer = Buffer.alloc(0);
  let expectedLength = -1;
  let skipTextOutput = true;
  let serverPort = null;
  let sessionId = null;

  host.stdout.on('data', (data) => {
    // 跳过开头的文本输出，寻找二进制消息的开始
    if (skipTextOutput) {
      for (let i = 0; i <= data.length - 4; i++) {
        const possibleLength = data.readUInt32LE(i);
        if (possibleLength > 10 && possibleLength < 10000) {
          data = data.slice(i);
          skipTextOutput = false;
          break;
        }
      }
      
      if (skipTextOutput) {
        return;
      }
    }
    
    buffer = Buffer.concat([buffer, data]);
    
    // 处理Native Messaging二进制协议
    while (true) {
      if (expectedLength === -1 && buffer.length >= 4) {
        expectedLength = buffer.readUInt32LE(0);
        buffer = buffer.slice(4);
      }
      
      if (expectedLength !== -1 && buffer.length >= expectedLength) {
        const messageBuffer = buffer.slice(0, expectedLength);
        buffer = buffer.slice(expectedLength);
        
        try {
          const response = JSON.parse(messageBuffer.toString());
          console.log('📨 Native响应:', JSON.stringify(response, null, 2));
          
          if (response.type === 'server_started') {
            console.log('✅ MCP服务器启动成功!');
            serverPort = response.payload.port;
            runMCPTests();
          } else if (response.type === 'server_stopped') {
            console.log('✅ MCP服务器正常停止!');
            host.kill();
          }
        } catch (error) {
          console.error('❌ 解析Native响应失败:', error.message);
        }
        
        expectedLength = -1;
      } else {
        break;
      }
    }
  });

  host.stderr.on('data', (data) => {
    console.log('❌ 错误输出:', data.toString());
  });

  host.on('close', (code) => {
    console.log(`\n🏁 测试完成，退出码: ${code}`);
    
    if (code === 0) {
      console.log('\n🎉 最终MCP测试完成！');
    } else {
      console.log('\n⚠️  测试中发现问题，请检查上述输出');
    }
  });

  async function runMCPTests() {
    console.log('\n🌐 开始MCP协议测试...');
    
    try {
      // 1. 初始化MCP连接
      console.log('\n🧪 步骤1: MCP初始化');
      const initResponse = await sendMCPRequest(serverPort, 'initialize', {
        protocolVersion: '2024-11-05',
        capabilities: {
          roots: { listChanged: true },
          sampling: {}
        },
        clientInfo: {
          name: 'test-client',
          version: '1.0.0'
        }
      });
      
      if (initResponse.statusCode === 200) {
        console.log('✅ MCP初始化成功!');
        sessionId = initResponse.headers['mcp-session-id'];
        console.log('📋 Session ID:', sessionId);
      } else {
        console.log('❌ MCP初始化失败');
        return;
      }
      
      // 等待一秒
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 2. 获取工具列表
      console.log('\n🧪 步骤2: 获取工具列表');
      const toolsResponse = await sendMCPRequest(serverPort, 'tools/list', {}, 2, sessionId);
      
      if (toolsResponse.statusCode === 200) {
        console.log('✅ 获取工具列表成功!');
        if (toolsResponse.data && toolsResponse.data.result && toolsResponse.data.result.tools) {
          console.log('🔧 可用工具:', toolsResponse.data.result.tools.map(t => t.name));
        }
      } else {
        console.log('❌ 获取工具列表失败');
      }
      
      // 等待一秒
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 3. 调用Chrome工具 - Alert
      console.log('\n🧪 步骤3: 调用Chrome Alert工具');
      const alertResponse = await sendMCPRequest(serverPort, 'tools/call', {
        name: 'chrome_inject_script',
        arguments: {
          type: 'MAIN',
          script: "alert('🎉 最终MCP测试成功！端口冲突已彻底解决！Chrome扩展正常工作！');"
        }
      }, 3, sessionId);
      
      if (alertResponse.statusCode === 200) {
        console.log('✅ Chrome Alert工具调用成功!');
        if (alertResponse.data && alertResponse.data.result) {
          console.log('📊 Alert结果:', alertResponse.data.result);
        }
      } else {
        console.log('❌ Chrome Alert工具调用失败');
      }
      
      // 等待一秒
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 4. 获取页面标题
      console.log('\n🧪 步骤4: 获取页面标题');
      const titleResponse = await sendMCPRequest(serverPort, 'tools/call', {
        name: 'chrome_get_page_title',
        arguments: {}
      }, 4, sessionId);
      
      if (titleResponse.statusCode === 200) {
        console.log('✅ 获取页面标题成功!');
        if (titleResponse.data && titleResponse.data.result) {
          console.log('📄 页面标题:', titleResponse.data.result.content);
        }
      } else {
        console.log('❌ 获取页面标题失败');
      }
      
      // 等待一秒
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 5. 导航测试
      console.log('\n🧪 步骤5: 导航到澳客网');
      const navResponse = await sendMCPRequest(serverPort, 'tools/call', {
        name: 'chrome_navigate',
        arguments: {
          url: 'https://www.okooo.com'
        }
      }, 5, sessionId);
      
      if (navResponse.statusCode === 200) {
        console.log('✅ 导航到澳客网成功!');
        
        // 等待页面加载
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // 获取新页面标题
        console.log('\n🧪 步骤6: 获取澳客网页面标题');
        const newTitleResponse = await sendMCPRequest(serverPort, 'tools/call', {
          name: 'chrome_get_page_title',
          arguments: {}
        }, 6, sessionId);
        
        if (newTitleResponse.statusCode === 200 && newTitleResponse.data && newTitleResponse.data.result) {
          console.log('✅ 获取澳客网页面标题成功!');
          console.log('📄 澳客网标题:', newTitleResponse.data.result.content);
        }
      } else {
        console.log('❌ 导航到澳客网失败');
      }
      
    } catch (error) {
      console.error('❌ MCP测试过程中发生错误:', error.message);
    }
    
    console.log('\n📤 所有MCP测试完成，停止服务器...');
    const stopMessage = { type: 'stop' };
    sendNativeMessage(host, stopMessage);
  }

  // 启动服务器
  console.log('📤 启动MCP服务器...');
  const startMessage = {
    type: 'start',
    payload: { port: 56889 }
  };
  sendNativeMessage(host, startMessage);

  // 超时处理
  setTimeout(() => {
    console.log('⏰ 测试超时');
    host.kill();
  }, 90000); // 增加到90秒
}

testFinalMCP().catch(console.error);