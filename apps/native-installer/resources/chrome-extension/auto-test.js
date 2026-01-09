// 自动测试脚本
console.log('🚀 开始自动测试...');

// 等待页面完全加载
setTimeout(() => {
    console.log('📋 执行 runCompleteTest()...');
    if (typeof runCompleteTest === 'function') {
        runCompleteTest();
    } else {
        console.error('❌ runCompleteTest 函数未定义');
    }
}, 1000);

// 等待测试完成后显示JSON输出
setTimeout(() => {
    console.log('📋 执行 showJsonOutput()...');
    if (typeof showJsonOutput === 'function') {
        showJsonOutput();
    } else {
        console.error('❌ showJsonOutput 函数未定义');
    }
}, 3000);