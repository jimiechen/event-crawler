// 测试数据结构的简单脚本
console.log('🔍 开始测试数据结构...');

// 模拟运行完整测试
if (typeof runCompleteTest === 'function') {
    runCompleteTest();
    
    console.log('📊 提取的数据结构:', extractedData);
    
    // 检查数据结构
    const checks = [
        { name: '主键存在', test: () => extractedData.match_id !== undefined },
        { name: '主队近期是数组', test: () => Array.isArray(extractedData.home_recent) },
        { name: '客队近期是数组', test: () => Array.isArray(extractedData.away_recent) },
        { name: '未来比赛是数组', test: () => Array.isArray(extractedData.future) },
        { name: '两队交锋是数组', test: () => Array.isArray(extractedData.h2h) },
        { name: '主队近期有数据', test: () => extractedData.home_recent && extractedData.home_recent.length > 0 },
        { name: '客队近期有数据', test: () => extractedData.away_recent && extractedData.away_recent.length > 0 },
        { name: '未来比赛有数据', test: () => extractedData.future && extractedData.future.length > 0 },
        { name: '两队交锋有数据', test: () => extractedData.h2h && extractedData.h2h.length > 0 }
    ];
    
    checks.forEach(check => {
        const result = check.test();
        console.log(`${result ? '✅' : '❌'} ${check.name}: ${result}`);
    });
    
    // 显示数组长度
    console.log('\n📈 数组长度统计:');
    console.log(`主队近期: ${extractedData.home_recent ? extractedData.home_recent.length : 0} 场`);
    console.log(`客队近期: ${extractedData.away_recent ? extractedData.away_recent.length : 0} 场`);
    console.log(`未来比赛: ${extractedData.future ? extractedData.future.length : 0} 场`);
    console.log(`两队交锋: ${extractedData.h2h ? extractedData.h2h.length : 0} 场`);
    
} else {
    console.log('❌ runCompleteTest 函数不存在');
}

console.log('✅ 测试完成');