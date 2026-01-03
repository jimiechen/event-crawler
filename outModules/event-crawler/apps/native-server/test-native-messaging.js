const { spawn } = require('child_process');
const path = require('path');

// 发送Native Messaging格式的消息
function sendNativeMessage(host, message) {
  const messageString = JSON.stringify(message);
  const messageBuffer = Buffer.from(messageString);
  const headerBuffer = Buffer.alloc(4);
  headerBuffer.writeUInt32LE(messageBuffer.length, 0);
  
  console.log('📤 发送消息:', JSON.stringify(message));
  host.stdin.write(Buffer.concat([headerBuffer, messageBuffer]));
}

// 测试Native Messaging连接
function testNativeMessaging() {
  console.log('🔄 开始测试Native Messaging连接...');
  
  const hostPath = path.join(__dirname, 'dist', 'run_host.sh');
  const host = spawn(hostPath, [], {
    stdio: ['pipe', 'pipe', 'pipe']
  });

  let responseReceived = false;
  let buffer = Buffer.alloc(0);
  let expectedLength = -1;
  let skipTextOutput = true;

  host.stdout.on('data', (data) => {
    console.log('🔍 原始stdout数据 (长度:', data.length, '):', data);
    
    // 跳过开头的文本输出，寻找二进制消息的开始
    if (skipTextOutput) {
      // 寻找可能的二进制消息开始（4字节长度前缀）
      for (let i = 0; i <= data.length - 4; i++) {
        const possibleLength = data.readUInt32LE(i);
        // 合理的消息长度范围（10-10000字节）
        if (possibleLength > 10 && possibleLength < 10000) {
          console.log('🎯 找到可能的二进制消息开始位置:', i, '长度:', possibleLength);
          data = data.slice(i);
          skipTextOutput = false;
          break;
        }
      }
      
      if (skipTextOutput) {
        console.log('⏭️ 跳过文本输出');
        return;
      }
    }
    
    buffer = Buffer.concat([buffer, data]);
    
    // 处理Native Messaging二进制协议
    while (true) {
      if (expectedLength === -1 && buffer.length >= 4) {
        expectedLength = buffer.readUInt32LE(0);
        console.log('📏 期望消息长度:', expectedLength);
        buffer = buffer.slice(4);
      }
      
      if (expectedLength !== -1 && buffer.length >= expectedLength) {
        const messageBuffer = buffer.slice(0, expectedLength);
        buffer = buffer.slice(expectedLength);
        
        try {
          const response = JSON.parse(messageBuffer.toString());
          console.log('📨 收到响应:', JSON.stringify(response, null, 2));
          responseReceived = true;
          
          if (response.type === 'server_started') {
            console.log('✅ MCP服务器启动成功!');
            
            // 发送ping消息测试
            const pingMessage = {
              type: 'ping_from_extension'
            };
            sendNativeMessage(host, pingMessage);
          } else if (response.type === 'pong_to_extension') {
            console.log('✅ Ping-Pong测试成功!');
            
            // 测试停止
            const stopMessage = { type: 'stop' };
            sendNativeMessage(host, stopMessage);
          } else if (response.type === 'server_stopped') {
            console.log('✅ MCP服务器正常停止!');
            host.kill();
          } else if (response.type === 'error_from_native_host') {
            console.error('❌ Native Host错误:', response.payload?.message);
          }
        } catch (error) {
          console.error('❌ 解析响应失败:', error.message);
          console.log('原始数据:', messageBuffer.toString());
        }
        
        expectedLength = -1;
      } else {
        break;
      }
    }
  });

  host.stderr.on('data', (data) => {
    console.log('📝 Native Host stderr:', data.toString().trim());
  });

  host.on('close', (code) => {
    console.log(`🔚 Native Host进程结束，退出码: ${code}`);
    if (!responseReceived) {
      console.error('❌ 未收到任何响应，连接可能失败');
    }
  });

  host.on('error', (error) => {
    console.error('❌ 启动Native Host失败:', error.message);
  });

  // 等待一下让host启动
  setTimeout(() => {
    // 发送启动消息
    const startMessage = {
      type: 'start',
      payload: { port: 56889 }
    };
    
    sendNativeMessage(host, startMessage);
  }, 1000);

  // 超时处理
  setTimeout(() => {
    if (!responseReceived) {
      console.error('❌ 测试超时，未收到响应');
      host.kill();
    }
  }, 15000);
}

// 运行测试
testNativeMessaging();