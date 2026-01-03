const crypto = require('crypto');

// 从manifest.json读取key
const fs = require('fs');
const path = require('path');

const manifestPath = path.join(__dirname, '.output/chrome-mv3/manifest.json');
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));

const publicKey = manifest.key;

console.log('🔑 Chrome扩展Key:', publicKey);
console.log('📏 Key长度:', publicKey.length);

// 计算扩展ID
function calculateExtensionId(publicKeyPem) {
  try {
    // 解码Base64公钥
    const publicKeyDer = Buffer.from(publicKeyPem, 'base64');
    
    // 计算SHA256哈希
    const hash = crypto.createHash('sha256').update(publicKeyDer).digest();
    
    // 取前16字节
    const first16Bytes = hash.slice(0, 16);
    
    // 转换为扩展ID (a-p字符映射)
    const chars = 'abcdefghijklmnop';
    let extensionId = '';
    
    for (let i = 0; i < 16; i++) {
      const byte = first16Bytes[i];
      extensionId += chars[byte >> 4] + chars[byte & 0x0f];
    }
    
    return extensionId;
  } catch (error) {
    console.error('计算扩展ID时出错:', error);
    return null;
  }
}

const calculatedId = calculateExtensionId(publicKey);

console.log('\n📊 扩展ID计算结果:');
console.log('🆔 计算得出的扩展ID:', calculatedId);
console.log('🎯 预期的扩展ID:     eakanlceigandmpclfckaiamlihkjbeg');
console.log('👤 用户报告的扩展ID:   gmpnjjgkjcnaeeadhdknpnicehnalppo');

console.log('\n🔍 匹配检查:');
console.log('✅ 与预期ID匹配:', calculatedId === 'eakanlceigandmpclfckaiamlihkjbeg' ? '是' : '否');
console.log('❌ 与用户报告ID匹配:', calculatedId === 'gmpnjjgkjcnaeeadhdknpnicehnalppo' ? '是' : '否');

if (calculatedId === 'eakanlceigandmpclfckaiamlihkjbeg') {
  console.log('\n🎉 扩展ID配置正确！');
  console.log('💡 如果用户看到不同的ID，可能是因为:');
  console.log('   1. 浏览器中加载了旧版本的扩展');
  console.log('   2. 需要重新加载扩展');
  console.log('   3. 浏览器缓存问题');
} else {
  console.log('\n⚠️  扩展ID不匹配，需要检查配置');
}