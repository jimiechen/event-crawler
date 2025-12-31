const fetch = require('node-fetch');

async function testTabsSimple() {
    console.log('🚀 简单测试获取浏览器tabs功能...\n');
    
    try {
        // 直接调用工具，不需要初始化
        console.log('📞 直接调用get_windows_and_tabs工具...');
        
        const response = await fetch('http://127.0.0.1:56889/mcp', {
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
        console.log('原始响应:', responseText);
        
        // 尝试解析响应
        if (responseText.includes('event: message')) {
            console.log('检测到SSE格式响应');
            const lines = responseText.split('\n');
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const jsonData = line.substring(6);
                    console.log('SSE数据:', jsonData);
                    try {
                        const result = JSON.parse(jsonData);
                        console.log('解析结果:', JSON.stringify(result, null, 2));
                    } catch (e) {
                        console.log('解析SSE数据失败:', e.message);
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
            }
        }
        
    } catch (error) {
        console.log('❌ 测试失败:', error.message);
        if (error.code === 'ECONNREFUSED') {
            console.log('💡 提示: MCP服务器可能未启动，请检查端口56889');
        }
    }
}

// 运行测试
testTabsSimple()