const http = require('http');

// 只测试获取工具列表
async function testToolsList() {
    console.log('🚀 测试获取MCP工具列表...\n');
    
    let sessionId = null;
    
    try {
        // 1. 初始化MCP连接
        console.log('1. 初始化MCP连接...');
        const initResponse = await sendMCPRequest({
            jsonrpc: "2.0",
            id: 1,
            method: "initialize",
            params: {
                protocolVersion: "2024-11-05",
                capabilities: {},
                clientInfo: {
                    name: "test-client",
                    version: "1.0.0"
                }
            }
        });
        
        if (initResponse.result) {
            console.log('✅ MCP初始化成功');
            console.log(`   协议版本: ${initResponse.result.protocolVersion}`);
            console.log(`   服务器信息: ${initResponse.result.serverInfo?.name || 'Unknown'}`);
            sessionId = initResponse.sessionId;
            if (sessionId) {
                console.log(`   会话ID: ${sessionId}`);
            }
            console.log();
        } else {
            console.log('❌ MCP初始化失败:', initResponse);
            return;
        }
        
        // 2. 获取工具列表
        console.log('2. 获取工具列表...');
        const toolsResponse = await sendMCPRequest({
            jsonrpc: "2.0",
            id: 2,
            method: "tools/list",
            params: {}
        }, sessionId);
        
        if (toolsResponse.result && toolsResponse.result.tools) {
            console.log(`✅ 获取到 ${toolsResponse.result.tools.length} 个工具\n`);
            
            // 显示所有工具
            console.log('📋 所有可用工具:');
            toolsResponse.result.tools.forEach((tool, index) => {
                console.log(`   ${index + 1}. ${tool.name}`);
                if (tool.description) {
                    console.log(`      描述: ${tool.description}`);
                }
                console.log();
            });
            
            // 查找tabs相关工具
            const tabsTools = toolsResponse.result.tools.filter(tool => 
                tool.name.toLowerCase().includes('tab') || 
                tool.name.toLowerCase().includes('window')
            );
            
            console.log('🔍 Tabs/Windows相关工具:');
            tabsTools.forEach(tool => {
                console.log(`   ✨ ${tool.name}: ${tool.description || '无描述'}`);
            });
            
            // 查找其他有用的工具
            const otherUsefulTools = toolsResponse.result.tools.filter(tool => 
                tool.name.toLowerCase().includes('chrome') ||
                tool.name.toLowerCase().includes('navigate') ||
                tool.name.toLowerCase().includes('page') ||
                tool.name.toLowerCase().includes('title')
            );
            
            console.log('\n🌐 其他Chrome相关工具:');
            otherUsefulTools.forEach(tool => {
                if (!tool.name.toLowerCase().includes('tab') && !tool.name.toLowerCase().includes('window')) {
                    console.log(`   🔧 ${tool.name}: ${tool.description || '无描述'}`);
                }
            });
            
        } else {
            console.log('❌ 获取工具列表失败:', toolsResponse);
            return;
        }
        
        console.log('\n🎉 工具列表测试完成!');
        console.log('\n💡 要获取浏览器tabs，可以使用以下工具:');
        console.log('   - get_windows_and_tabs: 获取所有浏览器窗口和标签页');
        console.log('   - chrome_close_tabs: 关闭指定的标签页');
        console.log('   - search_tabs_content: 搜索标签页内容');
        
    } catch (error) {
        console.error('❌ 测试过程中出现错误:', error.message);
        console.error('错误堆栈:', error.stack);
    }
}

// 发送MCP请求的辅助函数
async function sendMCPRequest(data, sessionId = null) {
    return new Promise((resolve, reject) => {
        const postData = JSON.stringify(data);
        
        const options = {
            hostname: 'localhost',
            port: 3000,
            path: '/extension-mcp/mcp',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/event-stream',
                'Content-Length': Buffer.byteLength(postData),
                ...(sessionId && { 'mcp-session-id': sessionId })
            },
            timeout: 10000
        };
        
        const req = http.request(options, (res) => {
            let responseData = '';
            
            res.on('data', (chunk) => {
                responseData += chunk;
            });
            
            res.on('end', () => {
                try {
                    // 检查是否是SSE格式
                    if (responseData.startsWith('event: message\ndata: ')) {
                        // 解析SSE格式
                        const lines = responseData.split('\n');
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                const jsonData = line.substring(6);
                                const jsonResponse = JSON.parse(jsonData);
                                const result = {
                                    ...jsonResponse,
                                    sessionId: res.headers['mcp-session-id']
                                };
                                resolve(result);
                                return;
                            }
                        }
                        reject(new Error(`SSE格式解析失败: ${responseData}`));
                    } else {
                        // 普通JSON格式
                        const jsonResponse = JSON.parse(responseData);
                        const result = {
                            ...jsonResponse,
                            sessionId: res.headers['mcp-session-id']
                        };
                        resolve(result);
                    }
                } catch (parseError) {
                    reject(new Error(`解析响应失败: ${parseError.message}, 响应内容: ${responseData}`));
                }
            });
        });
        
        req.on('error', (error) => {
            reject(new Error(`HTTP请求失败: ${error.message}`));
        });
        
        req.on('timeout', () => {
            req.destroy();
            reject(new Error('HTTP请求超时'));
        });
        
        req.write(postData);
        req.end();
    });
}

// 运行测试
testToolsList().catch(console.error);