const fetch = require('node-fetch');

async function testGetWindowsAndTabs() {
    console.log('🚀 开始测试获取浏览器tabs功能...\n');
    
    const startTime = Date.now();
    
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
        
        console.log('✅ MCP初始化成功!');
        console.log('协议版本:', initResponse.protocolVersion);
        
        // 提取sessionId
        const sessionId = initResponse.sessionId;
        console.log('会话ID:', sessionId);
        
        // 2. 获取工具列表
        console.log('\n2️⃣ 获取工具列表...');
        const toolsResponse = await sendMCPRequestWithSession('tools/list', {}, sessionId);
        console.log('✅ 获取到', toolsResponse.tools.length, '个工具');
        
        // 查找get_windows_and_tabs工具
        const getTabsTool = toolsResponse.tools.find(tool => tool.name === 'get_windows_and_tabs');
        if (!getTabsTool) {
            console.log('❌ 未找到get_windows_and_tabs工具');
            console.log('可用工具:', toolsResponse.tools.map(t => t.name).join(', '));
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
        
        console.log('✅ get_windows_and_tabs调用成功!');
        console.log('响应时间:', responseTime + 'ms');
        
        // 4. 分析返回结果
        console.log('\n4️⃣ 分析返回结果...');
        
        if (tabsResponse.content && tabsResponse.content.length > 0) {
            const result = tabsResponse.content[0];
            
            if (result.type === 'text') {
                try {
                    const tabsData = JSON.parse(result.text);
                    
                    console.log('📊 浏览器窗口和标签页统计:');
                    console.log('窗口数量:', tabsData.length);
                    
                    let totalTabs = 0;
                    tabsData.forEach((window, windowIndex) => {
                        console.log(`\n🪟 窗口 ${windowIndex + 1} (ID: ${window.id}):`);
                        console.log('  - 标签页数量:', window.tabs.length);
                        console.log('  - 窗口状态:', window.state);
                        console.log('  - 是否聚焦:', window.focused);
                        
                        totalTabs += window.tabs.length;
                        
                        window.tabs.forEach((tab, tabIndex) => {
                            console.log(`  📄 标签页 ${tabIndex + 1}:`);
                            console.log(`    - ID: ${tab.id}`);
                            console.log(`    - 标题: ${tab.title}`);
                            console.log(`    - URL: ${tab.url}`);
                            console.log(`    - 活跃状态: ${tab.active ? '是' : '否'}`);
                            console.log(`    - 固定状态: ${tab.pinned ? '是' : '否'}`);
                        });
                    });
                    
                    console.log(`\n📈 总计: ${tabsData.length} 个窗口, ${totalTabs} 个标签页`);
                    
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
        timeout: 30000
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
        timeout: 30000
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
testGetWindowsAndTabs();