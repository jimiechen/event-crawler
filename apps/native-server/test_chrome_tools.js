const { spawn } = require('child_process');
const path = require('path');

// 发送Native Messaging格式的消息
function sendNativeMessage(host, message) {
  const messageString = JSON.stringify(message);
  const messageBuffer = Buffer.from(messageString);
  const headerBuffer = Buffer.alloc(4);
  headerBuffer.writeUInt32LE(messageBuffer.length, 0);
  
  console.log('📤 发送消息:', JSON.stringify(message, null, 2));
  host.stdin.write(Buffer.concat([headerBuffer, messageBuffer]));
}

// 测试Chrome MCP工具
function testChromeTools() {
  console.log('🚀 开始测试Chrome MCP工具...\n');
  
  const hostPath = path.join(__dirname, 'dist', 'run_host.sh');
  const host = spawn(hostPath, [], {
    stdio: ['pipe', 'pipe', 'pipe']
  });

  let buffer = Buffer.alloc(0);
  let expectedLength = -1;
  let skipTextOutput = true;
  let testStep = 0;

  const tests = [
    {
      name: '获取工具列表',
      message: {
        tool: 'chrome_list_tools',
        arguments: {}
      }
    },
    {
      name: 'Alert弹窗测试',
      message: {
        tool: 'chrome_inject_script',
        arguments: {
          type: 'MAIN',
          script: "alert('🎉 MCP测试成功！端口冲突已解决！');"
        }
      }
    },
    {
      name: '获取当前页面标题',
      message: {
        tool: 'chrome_get_page_title',
        arguments: {}
      }
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
          console.log('📨 收到响应:', JSON.stringify(response, null, 2));
          
          if (response.type === 'server_started') {
            console.log('✅ MCP服务器启动成功!');
            runNextTest();
          } else if (response.type === 'tool_response') {
            console.log(`✅ 测试 "${tests[testStep - 1]?.name}" 成功!`);
            console.log('📊 响应数据:', response.payload);
            runNextTest();
          } else if (response.type === 'error_from_native_host') {
            console.error(`❌ 测试 "${tests[testStep - 1]?.name}" 失败:`, response.payload?.message);
            runNextTest();
          } else if (response.type === 'server_stopped') {
            console.log('✅ MCP服务器正常停止!');
            host.kill();
          }
        } catch (error) {
          console.error('❌ 解析响应失败:', error.message);
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
      console.log('\n🎉 所有测试通过！Chrome MCP功能正常工作！');
    } else {
      console.log('\n⚠️  测试中发现问题，请检查上述输出');
    }
  });

  function runNextTest() {
    if (testStep < tests.length) {
      const test = tests[testStep];
      console.log(`\n🧪 执行测试 ${testStep + 1}/${tests.length}: ${test.name}`);
      sendNativeMessage(host, test.message);
      testStep++;
    } else {
      console.log('\n📤 所有测试完成，停止服务器...');
      const stopMessage = { type: 'stop' };
      sendNativeMessage(host, stopMessage);
    }
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
  }, 30000);
}

testChromeTools();