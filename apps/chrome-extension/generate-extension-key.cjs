const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

// 生成RSA密钥对
const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
  modulusLength: 2048,
  publicKeyEncoding: {
    type: 'spki',
    format: 'der'
  },
  privateKeyEncoding: {
    type: 'pkcs8',
    format: 'pem'
  }
});

// 将公钥转换为base64格式
const publicKeyBase64 = publicKey.toString('base64');

console.log('生成的Chrome扩展Key:');
console.log(publicKeyBase64);

// 计算扩展ID
const sha256 = crypto.createHash('sha256');
sha256.update(publicKey);
const hash = sha256.digest();

// 取前16字节并转换为扩展ID格式
const extensionId = Array.from(hash.slice(0, 16))
  .map(byte => String.fromCharCode(97 + (byte % 26))) // 转换为a-p字符
  .join('');

console.log('\n对应的扩展ID:');
console.log(extensionId);

// 更新.env文件
const envPath = path.join(__dirname, '.env');
let envContent = '';

if (fs.existsSync(envPath)) {
  envContent = fs.readFileSync(envPath, 'utf8');
}

// 更新或添加CHROME_EXTENSION_KEY
const keyLine = `CHROME_EXTENSION_KEY=${publicKeyBase64}`;
const lines = envContent.split('\n');
let keyUpdated = false;

for (let i = 0; i < lines.length; i++) {
  if (lines[i].startsWith('CHROME_EXTENSION_KEY=')) {
    lines[i] = keyLine;
    keyUpdated = true;
    break;
  }
}

if (!keyUpdated) {
  lines.push('# Chrome Extension Key - 确保扩展ID固定');
  lines.push(keyLine);
}

fs.writeFileSync(envPath, lines.join('\n'));
console.log('\n✅ .env文件已更新');

// 保存私钥（可选，用于开发）
const privateKeyPath = path.join(__dirname, 'extension-private-key.pem');
fs.writeFileSync(privateKeyPath, privateKey);
console.log('✅ 私钥已保存到 extension-private-key.pem');

console.log('\n注意：请将 extension-private-key.pem 添加到 .gitignore 中，不要提交到版本控制系统！');