#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理旧板块文件，只保留 3BL26xxxx 格式的新板块
"""

import os

block_path = r"C:\new_tdx_test\T0002\blocknew"

print("=" * 60)
print("清理旧板块文件")
print("=" * 60)

# 获取所有3BL开头的板块文件
files = [f for f in os.listdir(block_path) if f.startswith('3BL') and f.endswith('.blk')]

print(f"\n找到 {len(files)} 个3BL板块文件")

# 保留 3BL26xxxx 格式的新板块，删除旧板块
kept = []
deleted = []

for f in files:
    # 提取日期部分
    code = f.replace('.blk', '')
    
    # 检查是否是新格式 (3BL26xxxx)
    if len(code) == 9 and code.startswith('3BL26'):
        kept.append(f)
    else:
        # 删除旧板块
        filepath = os.path.join(block_path, f)
        try:
            os.remove(filepath)
            deleted.append(f)
            print(f"  删除旧板块: {f}")
        except Exception as e:
            print(f"  删除失败 {f}: {e}")

print(f"\n保留的新板块: {len(kept)} 个")
for f in kept:
    print(f"  - {f}")

print(f"\n删除的旧板块: {len(deleted)} 个")

print("\n" + "=" * 60)
print("清理完成，请重启通达信客户端！")
print("=" * 60)
