const fetch = require('node-fetch');

async function testGetTabsFinal() {
    console.log('🚀 最终测试获取浏览器tabs功能...\n');
    
    const startTime = Date.now();
    let sessionId = null;
    
    try {
        // 1. 初始化MCP连接
        console.log('1️⃣ 初始化MCP连接...');
        const initResponse = await sendMCPRequest('initialize', {
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
        
        sessionId = initResponse.sessionId;
        console.log('✅ MCP初始化成功! 会话ID:', sessionId);
        
        // 2. 获取工具列表确认get_windows_and_tabs可用
        console.log('\n2️⃣ 确认get_windows_and_tabs工具可用...');
        const toolsResponse = await sendMCPRequestWithSession('tools/list', {}, sessionId);
        
        const getTabsTool = toolsResponse.tools.find(tool => tool.name === 'get_windows_and_tabs');
        if (!getTabsTool) {
            console.log('❌ 未找到get_windows_and_tabs工具');
            return;
        }
        
        console.log('✅ 找到get_windows_and_tabs工具');
        console.log('工具描述:', getTabsTool.description);
        
        // 3. 调用get_windows_and_tabs工具
        console.log('\n3️⃣ 调用get_windows_and_tabs工具...');
        const callStartTime = Date.now();
        
        const tabsResponse = await sendMCPRequestWithSession('tools/call', {
            name: 'get_windows_and_tabs',
            arguments: {}
        }, sessionId);
        
        const callEndTime = Date.now();
        const responseTime = callEndTime - callStartTime;
        
        console.log('✅ get_windows_and_tabs调用完成!');
        console.log('响应时间:', responseTime + 'ms');
        
        // 4. 分析返回结果
        console.log('\n4️⃣ 分析返回结果...');
        console.log('完整响应:', JSON.stringify(tabsResponse, null, 2));
        
        if (tabsResponse.content && tabsResponse.content.length > 0) {
            const result = tabsResponse.content[0];
            
            if (result.type === 'text') {
                try {
                    const tabsData = JSON.parse(result.text);
                    
                    console.log('\n📊 浏览器窗口和标签页详细信息:');
                    console.log('窗口数量:', tabsData.length);
                    
                    let totalTabs = 0;
                    tabsData.forEach((window, windowIndex) => {
                        console.log(`\n🪟 窗口 ${windowIndex + 1}:`);
                        console.log('  - 窗口ID:', window.id);
                        console.log('  - 窗口状态:', window.state);
                        console.log('  - 是否聚焦:', window.focused);
                        console.log('  - 标签页数量:', window.tabs.length);
                        
                        totalTabs += window.tabs.length;
                        
                        window.tabs.forEach((tab, tabIndex) => {
                            console.log(`\n  📄 标签页 ${tabIndex + 1}:`);
                            console.log(`    - ID: ${tab.id}`);
                            console.log(`    - 标题: ${tab.title}`);
                            console.log(`    - URL: ${tab.url}`);
                            console.log(`    - 活跃状态: ${tab.active ? '✅ 活跃' : '⭕ 非活跃'}`);
                            console.log(`    - 固定状态: ${tab.pinned ? '📌 已固定' : '📄 未固定'}`);
                            console.log(`    - 窗口ID: ${tab.windowId}`);
                            console.log(`    - 索引: ${tab.index}`);
                        });
                    });
                    
                    console.log(`\n🎯 总结:`);
                    console.log(`   - 总窗口数: ${tabsData.length}`);
                    console.log(`   - 总标签页数: ${totalTabs}`);
                    console.log(`   - 响应时间: ${responseTime}ms`);
                    
                    // 显示活跃标签页
                    const activeTabs = [];
                    tabsData.forEach(window => {
                        window.tabs.forEach(tab => {
                            if (tab.active) {
                                activeTabs.push({
                                    id: tab.id,
                                    title: tab.title,
                                    url: tab.url,
                                    windowId: tab.windowId
                                });
                            }
                        });
                    });
                    
                    console.log(`\n🎯 当前活跃标签页 (${activeTabs.length}个):`);
                    activeTabs.forEach((tab, index) => {
                        console.log(`   ${index + 1}. [ID:${tab.id}] ${tab.title}`);
                        console.log(`      URL: ${tab.url}`);
                    });
                    
                } catch (parseError) {
                    console.log('❌ 解析返回数据失败:', parseError.message);
                    console.log('原始数据:', result.text);
                }
            } else {
                console.log('返回内容类型:', result.type);
                console.log('返回内容:', result);
            }
        } else {
            console.log('❌ 未获取到有效的返回内容');
            console.log('完整响应:', JSON.stringify(tabsResponse, null, 2));
        }
        
    } catch (error) {
        console.log('❌ 测试失败:', error.message);
        
        if (error.message.includes('timeout')) {
            console.log('💡 提示: 请求超时，可能是Chrome扩展未响应');
            console.log('   - 请确认Chrome扩展已安装并启用');
            console.log('   - 请确认Chrome浏览器正在运行');
        } else if (error.message.includes('ECONNREFUSED')) {
            console.log('💡 提示: 无法连接到MCP服务器');
            console.log('   - 请确认MCP服务器正在运行在端口56889');
        }
        
        console.log('错误详情:', error);
    }
    
    const endTime = Date.now();
    console.log(`\n⏱️ 总测试时间: ${endTime - startTime}ms`);
}

async function sendMCPRequest(method, params) {
    const response = await fetch('http://127.0.0.1:56889/mcp', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            jsonrpc: '2.0',
            id: Date.now(),
            method: method,
            params: params
        }),
        timeout: 15000
    });

    const responseText = await response.text();
    
    // 处理SSE格式响应
    if (responseText.includes('event: message')) {
        const lines = responseText.split('\n');
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const jsonData = line.substring(6);
                const result = JSON.parse(jsonData);
                
                // 提取sessionId
                if (response.headers.get('mcp-session-id')) {
                    result.sessionId = response.headers.get('mcp-session-id');
                }
                
                return result.result || result;
            }
        }
    }
    
    // 处理普通JSON响应
    const result = JSON.parse(responseText);
    
    // 提取sessionId
    if (response.headers.get('mcp-session-id')) {
        result.sessionId = response.headers.get('mcp-session-id');
    }
    
    return result.result || result;
}

async function sendMCPRequestWithSession(method, params, sessionId) {
    const headers = {
        'Content-Type': 'application/json',
    };
    
    if (sessionId) {
        headers['mcp-session-id'] = sessionId;
    }
    
    const response = await fetch('http://127.0.0.1:56889/mcp', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
            jsonrpc: '2.0',
            id: Date.now(),
            method: method,
            params: params
        }),
        timeout: 15000
    });

    const responseText = await response.text();
    
    // 处理SSE格式响应
    if (responseText.includes('event: message')) {
        const lines = responseText.split('\n');
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const jsonData = line.substring(6);
                return JSON.parse(jsonData).result;
            }
        }
    }
    
    // 处理普通JSON响应
    const result = JSON.parse(responseText);
    return result.result || result;
}

// 运行测试
testGetTabsFinal();