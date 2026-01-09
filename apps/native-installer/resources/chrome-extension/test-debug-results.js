// 测试结果验证脚本 - 更新版本
import http from 'http';

function testDebugPage() {
    console.log('🚀 开始测试调试页面功能...');
    
    // 检查页面是否可访问
    const testUrl = 'http://localhost:8082/test-final-debug.html';
    
    http.get(testUrl, (res) => {
        let data = '';
        res.on('data', (chunk) => {
            data += chunk;
        });
        res.on('end', () => {
            console.log('✅ 页面访问成功');
            
            // 检查关键函数是否存在
            const hasExtractArrayData = data.includes('function extractArrayData');
            const hasTestFunctions = data.includes('function testFunctionExists');
            const hasRegexConfig = data.includes('const regexConfig');
            const hasTestData = data.includes('const testData');
            
            console.log('\n📋 页面内容检查:');
            console.log(`- extractArrayData 函数: ${hasExtractArrayData ? '✅' : '❌'}`);
            console.log(`- 测试函数: ${hasTestFunctions ? '✅' : '❌'}`);
            console.log(`- 配置对象: ${hasRegexConfig ? '✅' : '❌'}`);
            console.log(`- 测试数据: ${hasTestData ? '✅' : '❌'}`);
            
            if (hasExtractArrayData && hasTestFunctions && hasRegexConfig && hasTestData) {
                console.log('\n🎉 页面结构完整，所有必要组件都存在');
                console.log('\n📖 请在浏览器中手动测试:');
                console.log('1. 打开 http://localhost:8082/test-final-debug.html');
                console.log('2. 打开浏览器开发者工具 (F12)');
                console.log('3. 按顺序点击4个测试按钮');
                console.log('4. 观察页面结果和控制台日志');
                
                console.log('\n🔍 预期结果:');
                console.log('- 步骤1: 显示函数类型为 function');
                console.log('- 步骤2: 显示配置包含 home_recent 和 h2h 模块');
                console.log('- 步骤3: 提取到主队2条数据，交锋1条数据');
                console.log('- 步骤4: 显示完整的JSON结果');
                
            } else {
                console.log('\n❌ 页面结构不完整，可能存在问题');
            }
        });
    }).on('error', (err) => {
        console.log('❌ 无法访问测试页面:', err.message);
    });
}

testDebugPage();