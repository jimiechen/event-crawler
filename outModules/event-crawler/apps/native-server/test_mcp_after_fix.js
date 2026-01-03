#!/usr/bin/env node

/**
 * 测试MCP功能 - 端口冲突解决后
 */

const { spawn } = require('child_process');
const path = require('path');

console.log('🚀 开始测试MCP功能（端口冲突已解决）...\n');

// 测试配置
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
                script: "alert('MCP测试成功！端口冲突已解决');"
            }
        }
    },
    {
        name: '导航到澳客网',
        message: {
            tool: 'chrome_navigate',
            arguments: {
                url: 'https://www.okooo.com'
            }
        }
    },
    {
        name: '获取页面标题',
        message: {
            tool: 'chrome_get_page_title',
            arguments: {}
        }
    }
];

async function testNativeHost() {
    return new Promise((resolve, reject) => {
        const nativeHostPath = path.join(__dirname, 'dist', 'index.js');
        const nativeHost = spawn('node', [nativeHostPath], {
            stdio: ['pipe', 'pipe', 'pipe']
        });

        let testIndex = 0;
        let responses = [];
        
        nativeHost.stdout.on('data', (data) => {
            const lines = data.toString().split('\n').filter(line => line.trim());
            
            for (const line of lines) {
                try {
                    const response = JSON.parse(line);
                    console.log(`📨 收到响应:`, JSON.stringify(response, null, 2));
                    responses.push(response);
                    
                    if (response.type === 'server_started') {
                        console.log('✅ MCP服务器启动成功！');
                        // 开始测试第一个工具
                        runNextTest();
                    } else if (response.type === 'tool_response') {
                        console.log(`✅ 测试 "${tests[testIndex - 1]?.name}" 成功！`);
                        runNextTest();
                    } else if (response.type === 'error_from_native_host') {
                        console.log(`❌ 错误: ${response.message}`);
                        if (response.message.includes('EADDRINUSE')) {
                            console.log('⚠️  仍然存在端口冲突！');
                        }
                    }
                } catch (e) {
                    console.log('📝 非JSON输出:', line);
                }
            }
        });

        nativeHost.stderr.on('data', (data) => {
            console.log('❌ 错误输出:', data.toString());
        });

        nativeHost.on('close', (code) => {
            console.log(`\n🏁 测试完成，退出码: ${code}`);
            resolve({ code, responses });
        });

        // 启动服务器
        console.log('📤 发送启动消息...');
        const startMessage = JSON.stringify({
            type: 'start',
            port: 56889
        }) + '\n';
        nativeHost.stdin.write(startMessage);

        function runNextTest() {
            if (testIndex < tests.length) {
                const test = tests[testIndex];
                console.log(`\n🧪 执行测试: ${test.name}`);
                console.log(`📤 发送消息:`, JSON.stringify(test.message, null, 2));
                
                const message = JSON.stringify(test.message) + '\n';
                nativeHost.stdin.write(message);
                testIndex++;
            } else {
                // 所有测试完成，停止服务器
                console.log('\n📤 发送停止消息...');
                const stopMessage = JSON.stringify({ type: 'stop' }) + '\n';
                nativeHost.stdin.write(stopMessage);
            }
        }

        // 超时处理
        setTimeout(() => {
            console.log('⏰ 测试超时');
            nativeHost.kill();
            reject(new Error('测试超时'));
        }, 30000);
    });
}

// 运行测试
testNativeHost()
    .then(result => {
        console.log('\n📊 测试结果总结:');
        console.log(`- 退出码: ${result.code}`);
        console.log(`- 响应数量: ${result.responses.length}`);
        
        const successCount = result.responses.filter(r => 
            r.type === 'server_started' || r.type === 'tool_response'
        ).length;
        const errorCount = result.responses.filter(r => 
            r.type === 'error_from_native_host'
        ).length;
        
        console.log(`- 成功响应: ${successCount}`);
        console.log(`- 错误响应: ${errorCount}`);
        
        if (errorCount === 0 && successCount > 0) {
            console.log('\n🎉 所有测试通过！MCP功能正常工作！');
        } else {
            console.log('\n⚠️  测试中发现问题，请检查上述输出');
        }
    })
    .catch(error => {
        console.error('❌ 测试失败:', error.message);
        process.exit(1);
    });