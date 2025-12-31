const fs = require('fs');

// 读取HTML文件
const htmlContent = fs.readFileSync('/Users/mac/ok-mcp/app/chrome-extension/test-all-fields.html', 'utf8');

// 提取testData部分
const testDataMatch = htmlContent.match(/const testData = `([\s\S]*?)`;/);
if (!testDataMatch) {
    console.log('未找到testData');
    process.exit(1);
}

const testData = testDataMatch[1];
console.log('testData长度:', testData.length);

// 测试两队交锋容器匹配
const h2hContainerRegex = /<div[^>]*id="h2h-matches"[^>]*>([\s\S]*?)<\/div>/g;
const h2hMatch = testData.match(h2hContainerRegex);
console.log('两队交锋容器匹配结果:', h2hMatch ? '找到' : '未找到');
if (h2hMatch) {
    console.log('两队交锋容器数量:', h2hMatch.length);
    console.log('两队交锋容器内容长度:', h2hMatch[0].length);
    
    // 提取tr元素
    const trRegex = /<tr[^>]*data-matchid="([^"]+)"[^>]*>[\s\S]*?<\/tr>/g;
    const trMatches = [];
    let trMatch;
    while ((trMatch = trRegex.exec(h2hMatch[0])) !== null) {
        trMatches.push(trMatch[1]);
    }
    console.log('找到的比赛ID:', trMatches);
}

// 测试未来比赛容器匹配
const futureContainerRegex = /<div[^>]*id="future-matches"[^>]*>([\s\S]*?)<\/div>/g;
const futureMatch = testData.match(futureContainerRegex);
console.log('未来比赛容器匹配结果:', futureMatch ? '找到' : '未找到');
if (futureMatch) {
    console.log('未来比赛容器数量:', futureMatch.length);
    console.log('未来比赛容器内容长度:', futureMatch[0].length);
    
    // 提取tr元素
    const trRegex = /<tr[^>]*data-matchid="([^"]+)"[^>]*>[\s\S]*?<\/tr>/g;
    const trMatches = [];
    let trMatch;
    while ((trMatch = trRegex.exec(futureMatch[0])) !== null) {
        trMatches.push(trMatch[1]);
    }
    console.log('找到的比赛ID:', trMatches);
}