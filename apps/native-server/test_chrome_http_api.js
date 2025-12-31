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

// 发送HTTP请求到MCP服务器
function sendHttpRequest(port, tool, args) {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify({
      tool: tool,
      arguments: args
    });

    const options = {
      hostname: 'localhost',
      port: port,
      path: '/mcp/call',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    };

    console.log(`📤 发送HTTP请求到 http://localhost:${port}/mcp/call`);
    console.log('📦 请求数据:', postData);

    const req = http.request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          console.log('📨 HTTP响应:', JSON.stringify(response, null, 2));
          resolve(response);
        } catch (error) {
          console.log('📨 原始响应:', data);
          reject(new Error(`解析响应失败: ${error.message}`));
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

// 测试Chrome MCP HTTP API
async function testChromeHttpApi() {
  console.log('🚀 开始测试Chrome MCP HTTP API...\n');
  
  const hostPath = path.join(__dirname, 'dist', 'run_host.sh');
  const host = spawn(hostPath, [], {
    stdio: ['pipe', 'pipe', 'pipe']
  });

  let buffer = Buffer.alloc(0);
  let expectedLength = -1;
  let skipTextOutput = true;
  let serverPort = null;

  const tests = [
    {
      name: '获取工具列表',
      tool: 'chrome_list_tools',
      args: {}
    },
    {
      name: 'Alert弹窗测试',
      tool: 'chrome_inject_script',
      args: {
        type: 'MAIN',
        script: "alert('🎉 MCP HTTP API测试成功！端口冲突已解决！');"
      }
    },
    {
      name: '获取当前页面标题',
      tool: 'chrome_get_page_title',
      args: {}
    }
  ];

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
            runHttpTests();
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
      console.log('\n🎉 Chrome MCP HTTP API测试完成！');
    } else {
      console.log('\n⚠️  测试中发现问题，请检查上述输出');
    }
  });

  async function runHttpTests() {
    console.log('\n🌐 开始HTTP API测试...');
    
    for (let i = 0; i < tests.length; i++) {
      const test = tests[i];
      console.log(`\n🧪 执行测试 ${i + 1}/${tests.length}: ${test.name}`);
      
      try {
        const response = await sendHttpRequest(serverPort, test.tool, test.args);
        console.log(`✅ 测试 "${test.name}" 成功!`);
      } catch (error) {
        console.error(`❌ 测试 "${test.name}" 失败:`, error.message);
      }
      
      // 等待一秒再执行下一个测试
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    console.log('\n📤 所有HTTP测试完成，停止服务器...');
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
  }, 60000);
}

testChromeHttpApi().catch(console.error);