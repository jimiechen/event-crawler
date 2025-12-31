const { spawn } = require('child_process');
const http = require('http');

// 测试获取浏览器所有tabs的名称和ID
async function testGetTabs() {
    console.log('🚀 开始测试获取浏览器tabs功能...\n');
    
    let nativeProcess = null;
    
    try {
        // 1. 启动Native Messaging Host
        console.log('1. 启动Native Messaging Host...');
        nativeProcess = spawn('node', ['dist/native-messaging-host.js'], {
            cwd: process.cwd(),
            stdio: ['pipe', 'pipe', 'pipe']
        });
        
        // 监听进程输出
        nativeProcess.stdout.on('data', (data) => {
            console.log('Native Host输出:', data.toString());
        });
        
        nativeProcess.stderr.on('data', (data) => {
            console.log('Native Host错误:', data.toString());
        });
        
        // 等待服务器启动
        await new Promise(resolve => setTimeout(resolve, 3000));
        console.log('✅ Native Messaging Host启动成功\n');
        
        // 2. 初始化MCP连接
        console.log('2. 初始化MCP连接...');
        try {
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
                console.log(`   服务器信息: ${initResponse.result.serverInfo?.name || 'Unknown'}\n`);
            } else {
                console.log('❌ MCP初始化失败:', initResponse);
                return;
            }
        } catch (initError) {
            console.log('❌ MCP初始化异常:', initError.message);
            return;
        }
        
        // 3. 获取工具列表
        console.log('3. 获取工具列表...');
        try {
            const toolsResponse = await sendMCPRequest({
                jsonrpc: "2.0",
                id: 2,
                method: "tools/list",
                params: {}
            });
            
            if (toolsResponse.result && toolsResponse.result.tools) {
                console.log(`✅ 获取到 ${toolsResponse.result.tools.length} 个工具`);
                
                // 查找tabs相关工具
                const tabsTools = toolsResponse.result.tools.filter(tool => 
                    tool.name.toLowerCase().includes('tab') || 
                    tool.name.toLowerCase().includes('window')
                );
                
                console.log('📋 Tabs相关工具:');
                tabsTools.forEach(tool => {
                    console.log(`   - ${tool.name}: ${tool.description || '无描述'}`);
                });
                console.log();
            } else {
                console.log('❌ 获取工具列表失败:', toolsResponse);
                return;
            }
        } catch (toolsError) {
            console.log('❌ 获取工具列表异常:', toolsError.message);
            return;
        }
        
        // 4. 测试获取windows和tabs
        console.log('4. 测试获取所有浏览器tabs...');
        try {
            const getTabsResponse = await sendMCPRequest({
                jsonrpc: "2.0",
                id: 3,
                method: "tools/call",
                params: {
                    name: "chrome_get_windows_and_tabs",
                    arguments: {}
                }
            });
            
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
        } catch (tabsError) {
            console.log('❌ 获取tabs异常:', tabsError.message);
        }
        
        console.log('\n🎉 测试完成!');
        
    } catch (error) {
        console.error('❌ 测试过程中出现错误:', error.message);
        console.error('错误堆栈:', error.stack);
    } finally {
        // 清理资源
        if (nativeProcess) {
            console.log('\n🧹 清理资源...');
            nativeProcess.kill();
        }
    }
}

// 发送MCP请求的辅助函数
async function sendMCPRequest(data) {
    return new Promise((resolve, reject) => {
        const postData = JSON.stringify(data);
        
        const options = {
            hostname: 'localhost',
            port: 56889,
            path: '/mcp',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/event-stream',
                'Content-Length': Buffer.byteLength(postData)
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
                    const jsonResponse = JSON.parse(responseData);
                    resolve(jsonResponse);
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
testGetTabs().catch(console.error);