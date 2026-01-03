const http = require('http');

// 直接通过调试页面API测试获取tabs功能
async function testTabsDirectAPI() {
    console.log('🚀 直接通过MCP API测试获取tabs功能...\n');
    
    let sessionId = null;
    
    try {
        // 1. 初始化MCP连接
        console.log('1. 初始化MCP连接...');
        const initResponse = await sendMCPRequestWithSession({
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
            console.log(`✅ 获取到 ${toolsResponse.result.tools.length} 个工具`);
            
            // 查找tabs相关工具
            const tabsTools = toolsResponse.result.tools.filter(tool => 
                tool.name.toLowerCase().includes('tab') || 
                tool.name.toLowerCase().includes('window')
            );
            
            console.log('\n📋 Tabs相关工具:');
            tabsTools.forEach(tool => {
                console.log(`   - ${tool.name}: ${tool.description || '无描述'}`);
            });
            console.log();
        } else {
            console.log('❌ 获取工具列表失败:', toolsResponse);
            return;
        }
        
        // 3. 测试获取windows和tabs
        console.log('3. 测试获取所有浏览器tabs...');
        const getTabsResponse = await sendMCPRequest({
            jsonrpc: "2.0",
            id: 3,
            method: "tools/call",
            params: {
                name: "chrome_get_windows_and_tabs",
                arguments: {}
            }
        }, sessionId);
        
        if (getTabsResponse.result) {
            console.log('✅ 成功获取浏览器tabs信息!');
            
            try {
                const tabsData = JSON.parse(getTabsResponse.result.content[0].text);
                console.log(`\n📊 浏览器状态统计:`);
                console.log(`   窗口数量: ${tabsData.windowCount}`);
                console.log(`   标签页总数: ${tabsData.tabCount}`);
                
                console.log(`\n📑 详细标签页信息:`);
                tabsData.windows.forEach((window, windowIndex) => {
                    console.log(`\n🪟 窗口 ${windowIndex + 1} (ID: ${window.windowId}):`);
                    window.tabs.forEach((tab, tabIndex) => {
                        const activeFlag = tab.active ? ' [活跃]' : '';
                        console.log(`   ${tabIndex + 1}. ID: ${tab.tabId}${activeFlag}`);
                        console.log(`      标题: ${tab.title || '无标题'}`);
                        console.log(`      URL: ${tab.url || '无URL'}`);
                        console.log();
                    });
                });
                
                // 生成简化的tabs列表
                console.log(`\n📋 简化标签页列表:`);
                let globalTabIndex = 1;
                tabsData.windows.forEach(window => {
                    window.tabs.forEach(tab => {
                        const activeFlag = tab.active ? ' ⭐' : '';
                        console.log(`${globalTabIndex}. [${tab.tabId}] ${tab.title}${activeFlag}`);
                        globalTabIndex++;
                    });
                });
                
            } catch (parseError) {
                console.log('解析响应数据失败:', parseError.message);
                console.log('原始响应数据:', getTabsResponse.result.content[0].text);
            }
        } else if (getTabsResponse.error) {
            console.log('❌ 获取tabs失败:', getTabsResponse.error.message);
        } else {
            console.log('❌ 获取tabs响应异常:', getTabsResponse);
        }
        
        console.log('\n🎉 测试完成!');
        
    } catch (error) {
        console.error('❌ 测试过程中出现错误:', error.message);
        console.error('错误堆栈:', error.stack);
    }
}

// 发送MCP请求的辅助函数（通过调试页面的代理路径）
async function sendMCPRequest(data, sessionId = null) {
    return new Promise((resolve, reject) => {
        const postData = JSON.stringify(data);
        
        const options = {
            hostname: 'localhost',
            port: 3000,
            path: '/extension-mcp/mcp',  // 使用调试页面的代理路径
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/event-stream',
                'Content-Length': Buffer.byteLength(postData),
                ...(sessionId && { 'mcp-session-id': sessionId })
            },
            timeout: 30000
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
                                const jsonData = line.substring(6); // 移除 "data: " 前缀
                                const jsonResponse = JSON.parse(jsonData);
                                // 提取sessionId并返回
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
                        // 提取sessionId并返回
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

// 专门处理会话的函数
async function sendMCPRequestWithSession(data) {
    return sendMCPRequest(data);
}

// 运行测试
testTabsDirectAPI().catch(console.error);