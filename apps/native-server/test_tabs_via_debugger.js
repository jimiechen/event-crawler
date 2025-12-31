const http = require('http');

// 通过调试页面API测试获取tabs功能
async function testTabsViaDebugger() {
    console.log('🚀 通过调试页面API测试获取tabs功能...\n');
    
    try {
        // 1. 测试获取工具列表
        console.log('1. 获取工具列表...');
        const toolsResponse = await sendDebuggerRequest('/api/tools');
        
        if (toolsResponse.success) {
            console.log(`✅ 获取到 ${toolsResponse.tools.length} 个工具`);
            
            // 查找tabs相关工具
            const tabsTools = toolsResponse.tools.filter(tool => 
                tool.name.toLowerCase().includes('tab') || 
                tool.name.toLowerCase().includes('window')
            );
            
            console.log('\n📋 Tabs相关工具:');
            tabsTools.forEach(tool => {
                console.log(`   - ${tool.name}: ${tool.description || '无描述'}`);
            });
            console.log();
        } else {
            console.log('❌ 获取工具列表失败:', toolsResponse.error);
            return;
        }
        
        // 2. 测试获取windows和tabs
        console.log('2. 测试获取所有浏览器tabs...');
        const getTabsResponse = await sendDebuggerRequest('/api/call-tool', {
            method: 'POST',
            body: JSON.stringify({
                tool: 'chrome_get_windows_and_tabs',
                arguments: {}
            })
        });
        
        if (getTabsResponse.success) {
            console.log('✅ 成功获取浏览器tabs信息!');
            
            try {
                const tabsData = typeof getTabsResponse.result === 'string' 
                    ? JSON.parse(getTabsResponse.result) 
                    : getTabsResponse.result;
                
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
                console.log('原始响应数据:', getTabsResponse.result);
            }
        } else {
            console.log('❌ 获取tabs失败:', getTabsResponse.error);
        }
        
        console.log('\n🎉 测试完成!');
        
    } catch (error) {
        console.error('❌ 测试过程中出现错误:', error.message);
        console.error('错误堆栈:', error.stack);
    }
}

// 发送调试页面API请求的辅助函数
async function sendDebuggerRequest(path, options = {}) {
    return new Promise((resolve, reject) => {
        const requestOptions = {
            hostname: 'localhost',
            port: 3000,
            path: path,
            method: options.method || 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            timeout: 10000
        };
        
        const req = http.request(requestOptions, (res) => {
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
        
        if (options.body) {
            req.write(options.body);
        }
        
        req.end();
    });
}

// 运行测试
testTabsViaDebugger().catch(console.error);