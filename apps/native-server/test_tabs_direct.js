const fetch = require('node-fetch');

async function testTabsDirect() {
    console.log('🚀 直接测试获取浏览器tabs功能...\n');
    
    try {
        console.log('📞 直接调用Chrome扩展获取tabs...');
        
        // 模拟Chrome扩展的调用方式
        const response = await fetch('http://localhost:3000/extension-mcp/mcp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                id: Date.now(),
                method: 'tools/call',
                params: {
                    name: 'get_windows_and_tabs',
                    arguments: {}
                }
            }),
            timeout: 15000
        });

        console.log('响应状态:', response.status);
        console.log('响应头:', Object.fromEntries(response.headers.entries()));
        
        const responseText = await response.text();
        console.log('原始响应长度:', responseText.length);
        console.log('原始响应前500字符:', responseText.substring(0, 500));
        
        // 尝试解析响应
        if (responseText.includes('event: message')) {
            console.log('\n✅ 检测到SSE格式响应');
            const lines = responseText.split('\n');
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const jsonData = line.substring(6);
                    console.log('SSE数据:', jsonData);
                    try {
                        const result = JSON.parse(jsonData);
                        console.log('\n📊 解析结果:');
                        
                        if (result.result && result.result.content) {
                            const content = result.result.content[0];
                            if (content.type === 'text') {
                                const tabsData = JSON.parse(content.text);
                                
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
                                    });
                                });
                                
                                console.log(`\n🎯 总结:`);
                                console.log(`   - 总窗口数: ${tabsData.length}`);
                                console.log(`   - 总标签页数: ${totalTabs}`);
                                
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
                                
                                return; // 成功解析，退出
                            }
                        }
                        
                        console.log('完整解析结果:', JSON.stringify(result, null, 2));
                    } catch (e) {
                        console.log('解析SSE数据失败:', e.message);
                        console.log('原始SSE数据:', jsonData);
                    }
                }
            }
        } else {
            console.log('尝试解析为JSON...');
            try {
                const result = JSON.parse(responseText);
                console.log('JSON解析结果:', JSON.stringify(result, null, 2));
            } catch (e) {
                console.log('JSON解析失败:', e.message);
                console.log('响应内容:', responseText);
            }
        }
        
    } catch (error) {
        console.log('❌ 测试失败:', error.message);
        
        if (error.code === 'ECONNREFUSED') {
            console.log('💡 提示: 前端服务器可能未启动，请检查端口3000');
        } else if (error.message.includes('timeout')) {
            console.log('💡 提示: 请求超时，可能是Chrome扩展未响应');
        }
        
        console.log('错误详情:', error);
    }
}

// 运行测试
testTabsDirect()