#!/usr/bin/env node

// 简单的用户级注册脚本
const { tryRegisterUserLevelHost } = require('./dist/scripts/utils');

async function main() {
  console.log('尝试用户级注册 Native Messaging Host...');
  
  try {
    const success = await tryRegisterUserLevelHost();
    if (success) {
      console.log('✓ 用户级注册成功！');
      process.exit(0);
    } else {
      console.log('✗ 用户级注册失败');
      process.exit(1);
    }
  } catch (error) {
    console.error('注册过程中出现错误:', error.message);
    process.exit(1);
  }
}

main();