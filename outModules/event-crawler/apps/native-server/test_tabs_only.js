const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

function sendNativeMessage(host, message) {
  const messageString = JSON.stringify(message);
  const messageBuffer = Buffer.from(messageString);
  const headerBuffer = Buffer.alloc(4);
  headerBuffer.writeUInt32LE(messageBuffer.length, 0);
  
  console.log('📤 发送Native消息:', JSON.stringify(message, null, 2));
  host.stdin.write(Buffer.concat([headerBuffer, messageBuffer]));
}

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

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          resolve({ statusCode: res.statusCode, headers: res.headers, data: response });
        } catch (error) {
          resolve({ statusCode: res.statusCode, headers: res.headers, rawData: data });
        }
      });
    });

    req.on('error', (error) => { reject(error); });
    req.write(postData);
    req.end();
  });
}

async function testTabs() {
  console.log('🚀 开始测试获取浏览器tabs功能...\n');
  
  const hostPath = path.join(__dirname, 'dist', 'run_host.sh');
  const host = spawn(hostPath, [], { stdio: ['pipe', 'pipe', 'pipe'] });

  let buffer = Buffer.alloc(0);
  let expectedLength = -1;
  let skipTextOutput = true;
  let serverPort = null;
  let sessionId = null;

  host.stdout.on('data', (data) => {
    if (skipTextOutput) {
      for (let i = 0; i <= data.length - 4; i++) {
        const possibleLength = data.readUInt32LE(i);
        if (possibleLength > 10 && possibleLength < 10000) {
          data = data.slice(i);
          skipTextOutput = false;
          break;
        }
      }
      if (skipTextOutput) return;
    }
    
    buffer = Buffer.concat([buffer, data]);
    
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
            runTests();
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
  });

  async function runTests() {
    try {
      // 1. 初始化
      console.log('\n🧪 步骤1: MCP初始化');
      const initResponse = await sendMCPRequest(serverPort, 'initialize', {
        protocolVersion: '2024-11-05',
        capabilities: { roots: { listChanged: true }, sampling: {} },
        clientInfo: { name: 'tabs-test-client', version: '1.0.0' }
      });
      
      if (initResponse.statusCode === 200) {
        console.log('✅ MCP初始化成功!');
        sessionId = initResponse.headers['mcp-session-id'];
      } else {
        console.log('❌ MCP初始化失败');
        return;
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 2. 获取工具列表
      console.log('\n🧪 步骤2: 获取工具列表');
      const toolsResponse = await sendMCPRequest(serverPort, 'tools/list', {}, 2, sessionId);
      
      if (toolsResponse.statusCode === 200 && toolsResponse.data && toolsResponse.data.result) {
        const tools = toolsResponse.data.result.tools;
        console.log('✅ 可用工具:', tools.map(t => t.name));
        
        // 查找tabs相关工具
        const tabsTools = tools.filter(tool => 
          tool.name.toLowerCase().includes('tab') || 
          tool.name.toLowerCase().includes('window') ||
          tool.name.includes('get_tabs') ||
          tool.name.includes('list_tabs')
        );
        
        if (tabsTools.length > 0) {
          console.log('🎯 发现Tabs相关工具:', tabsTools.map(t => t.name));
        } else {
          console.log('⚠️  未发现专门的tabs工具');
        }
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 3. 通过脚本注入获取tabs信息
      console.log('\n🧪 步骤3: 通过脚本注入获取tabs信息');
      
      const tabsScript = `
        console.log('🔍 开始获取tabs信息...');
        
        const result = {
          chromeApiAvailable: typeof chrome !== 'undefined',
          tabsApiAvailable: typeof chrome !== 'undefined' && !!chrome.tabs,
          currentPage: {
            title: document.title,
            url: window.location.href,
            timestamp: new Date().toISOString()
          }
        };
        
        // 尝试获取tabs信息
        if (result.tabsApiAvailable) {
          console.log('✅ chrome.tabs API可用，尝试获取所有标签页...');
          chrome.tabs.query({}, (tabs) => {
            const tabsInfo = tabs.map(tab => ({
              id: tab.id,
              title: tab.title,
              url: tab.url,
              active: tab.active,
              windowId: tab.windowId
            }));
            console.log('🎯 所有标签页:', tabsInfo);
            result.tabs = tabsInfo;
          });
        } else {
          console.log('❌ chrome.tabs API不可用');
        }
        
        // 在页面上显示结果
        const resultDiv = document.createElement('div');
        resultDiv.id = 'tabs-test-result';
        resultDiv.style.cssText = 'position:fixed;top:10px;right:10px;background:#fff;border:3px solid #007bff;padding:15px;z-index:9999;max-width:500px;max-height:400px;overflow:auto;font-family:monospace;font-size:12px;box-shadow:0 4px 8px rgba(0,0,0,0.3);border-radius:8px;';
        
        resultDiv.innerHTML = \`
          <h3 style="margin:0 0 10px 0;color:#007bff;">🎯 Tabs功能测试结果</h3>
          <div><strong>Chrome API状态:</strong></div>
          <div style="color:\${result.chromeApiAvailable ? 'green' : 'red'};">
            Chrome API: \${result.chromeApiAvailable ? '✅ 可用' : '❌ 不可用'}
          </div>
          <div style="color:\${result.tabsApiAvailable ? 'green' : 'red'};">
            Tabs API: \${result.tabsApiAvailable ? '✅ 可用' : '❌ 不可用'}
          </div>
          <div style="margin-top:10px;"><strong>当前页面信息:</strong></div>
          <pre style="margin:5px 0;background:#f8f9fa;padding:8px;border-radius:4px;overflow:auto;font-size:10px;">\${JSON.stringify(result.currentPage, null, 2)}</pre>
          <div style="margin-top:10px;color:#666;font-size:10px;">
            💡 如果Tabs API不可用，可能是因为脚本运行在content script环境中，而不是background script环境。
          </div>
        \`;
        
        // 移除之前的结果
        const existing = document.getElementById('tabs-test-result');
        if (existing) existing.remove();
        
        document.body.appendChild(resultDiv);
        
        console.log('📊 测试结果:', result);
        return result;
      `;
      
      const scriptResponse = await sendMCPRequest(serverPort, 'tools/call', {
        name: 'chrome_inject_script',
        arguments: {
          type: 'MAIN',
          script: tabsScript
        }
      }, 3, sessionId);
      
      if (scriptResponse.statusCode === 200) {
        console.log('✅ 脚本注入成功!');
        if (scriptResponse.data && scriptResponse.data.result) {
          console.log('📊 脚本执行结果:', JSON.stringify(scriptResponse.data.result, null, 2));
        }
      } else {
        console.log('❌ 脚本注入失败');
        console.log('响应:', scriptResponse);
      }
      
    } catch (error) {
      console.error('❌ 测试过程中发生错误:', error.message);
    }
    
    console.log('\n📤 测试完成，停止服务器...');
    setTimeout(() => {
      const stopMessage = { type: 'stop' };
      sendNativeMessage(host, stopMessage);
    }, 3000);
  }

  // 启动服务器
  console.log('📤 启动MCP服务器...');
  const startMessage = { type: 'start', payload: { port: 56889 } };
  sendNativeMessage(host, startMessage);

  // 超时处理
  setTimeout(() => {
    console.log('⏰ 测试超时');
    host.kill();
  }, 30000);
}

testTabs().catch(console.error);