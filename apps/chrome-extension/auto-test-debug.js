// 自动测试脚本 - 用于测试 test-final-debug.html 页面
const puppeteer = require('puppeteer');

async function runDebugTests() {
    console.log('🚀 开始自动测试调试页面...');
    
    const browser = await puppeteer.launch({ 
        headless: false,
        devtools: true 
    });
    
    const page = await browser.newPage();
    
    // 监听控制台日志
    page.on('console', msg => {
        console.log(`[浏览器控制台] ${msg.type()}: ${msg.text()}`);
    });
    
    try {
        // 打开测试页面
        console.log('📖 打开测试页面...');
        await page.goto('http://localhost:8082/test-final-debug.html');
        await page.waitForSelector('#results');
        
        // 步骤1: 检查函数是否存在
        console.log('\n🔍 步骤1: 检查函数是否存在');
        await page.click('button[onclick="testFunctionExists()"]');
        await page.waitForTimeout(1000);
        
        let results = await page.$eval('#results', el => el.innerHTML);
        console.log('结果1:', results);
        
        // 步骤2: 检查数组模块配置
        console.log('\n📋 步骤2: 检查数组模块配置');
        await page.click('button[onclick="testArrayModuleConfig()"]');
        await page.waitForTimeout(1000);
        
        results = await page.$eval('#results', el => el.innerHTML);
        console.log('结果2:', results);
        
        // 步骤3: 测试数组提取
        console.log('\n🧪 步骤3: 测试数组提取');
        await page.click('button[onclick="testArrayExtraction()"]');
        await page.waitForTimeout(2000);
        
        results = await page.$eval('#results', el => el.innerHTML);
        console.log('结果3:', results);
        
        // 步骤4: 运行完整测试
        console.log('\n🎯 步骤4: 运行完整测试');
        await page.click('button[onclick="runFullTest()"]');
        await page.waitForTimeout(2000);
        
        results = await page.$eval('#results', el => el.innerHTML);
        console.log('结果4:', results);
        
        console.log('\n✅ 所有测试步骤完成！');
        
    } catch (error) {
        console.error('❌ 测试过程中发生错误:', error);
    } finally {
        // 保持浏览器打开以便查看结果
        console.log('\n📋 测试完成，浏览器将保持打开状态以便查看结果...');
        // await browser.close();
    }
}

// 检查是否安装了 puppeteer
try {
    runDebugTests();
} catch (error) {
    console.log('❌ 需要安装 puppeteer: npm install puppeteer');
    console.log('或者手动在浏览器中测试: http://localhost:8082/test-final-debug.html');
}