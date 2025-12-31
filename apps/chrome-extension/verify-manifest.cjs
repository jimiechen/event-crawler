const fs = require('fs');
const path = require('path');

const manifestPath = path.join(__dirname, '.output/chrome-mv3/manifest.json');

console.log('🔍 验证Chrome扩展manifest.json...\n');

try {
  // 检查文件是否存在
  if (!fs.existsSync(manifestPath)) {
    console.log('❌ manifest.json文件不存在');
    process.exit(1);
  }

  // 读取并解析manifest.json
  const manifestContent = fs.readFileSync(manifestPath, 'utf8');
  const manifest = JSON.parse(manifestContent);

  // 验证必要字段
  const checks = [
    { name: 'manifest_version', value: manifest.manifest_version, expected: 3 },
    { name: 'name', value: manifest.name, required: true },
    { name: 'version', value: manifest.version, required: true },
    { name: 'key', value: manifest.key, required: true },
    { name: 'permissions', value: manifest.permissions, required: true },
    { name: 'background', value: manifest.background, required: true },
  ];

  let allPassed = true;

  checks.forEach(check => {
    if (check.expected !== undefined) {
      if (check.value === check.expected) {
        console.log(`✅ ${check.name}: ${check.value}`);
      } else {
        console.log(`❌ ${check.name}: 期望 ${check.expected}, 实际 ${check.value}`);
        allPassed = false;
      }
    } else if (check.required) {
      if (check.value) {
        console.log(`✅ ${check.name}: 存在`);
      } else {
        console.log(`❌ ${check.name}: 缺失`);
        allPassed = false;
      }
    }
  });

  // 验证key字段格式
  if (manifest.key) {
    const keyLength = manifest.key.length;
    const isBase64 = /^[A-Za-z0-9+/]*={0,2}$/.test(manifest.key);
    
    console.log(`✅ key长度: ${keyLength} 字符`);
    console.log(`${isBase64 ? '✅' : '❌'} key格式: ${isBase64 ? 'Base64有效' : 'Base64无效'}`);
    
    if (!isBase64 || keyLength < 300) {
      allPassed = false;
    }
  }

  // 验证权限
  const requiredPermissions = ['nativeMessaging', 'tabs', 'activeTab', 'scripting'];
  const missingPermissions = requiredPermissions.filter(perm => 
    !manifest.permissions.includes(perm)
  );

  if (missingPermissions.length === 0) {
    console.log('✅ 必要权限: 全部存在');
  } else {
    console.log(`❌ 缺失权限: ${missingPermissions.join(', ')}`);
    allPassed = false;
  }

  console.log('\n' + '='.repeat(50));
  
  if (allPassed) {
    console.log('🎉 manifest.json验证通过！扩展应该可以正常加载。');
    console.log('\n📋 下一步操作:');
    console.log('1. 打开Chrome浏览器');
    console.log('2. 访问 chrome://extensions/');
    console.log('3. 开启"开发者模式"');
    console.log('4. 点击"加载已解压的扩展程序"');
    console.log('5. 选择目录: ' + path.dirname(manifestPath));
  } else {
    console.log('❌ manifest.json验证失败！请检查上述错误。');
    process.exit(1);
  }

} catch (error) {
  console.log('❌ 验证过程中出错:', error.message);
  process.exit(1);
}