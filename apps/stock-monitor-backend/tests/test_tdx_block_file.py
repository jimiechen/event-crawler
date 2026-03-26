#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试通达信板块文件
直接读写板块文件
"""

import os

# 通达信板块文件路径
block_path = r"C:\new_tdx_test\T0002\blocknew"

print("=" * 60)
print("测试通达信板块文件")
print("=" * 60)

# 1. 列出所有板块文件
print("\n1. 板块文件列表:")
try:
    files = os.listdir(block_path)
    block_files = [f for f in files if f.endswith('.blk')]
    print(f"   找到 {len(block_files)} 个板块文件")
    for f in block_files[:10]:
        print(f"   - {f}")
except Exception as e:
    print(f"   错误: {e}")

# 2. 检查我们创建的板块文件
print("\n2. 检查 3BL260325.blk 文件:")
block_file = os.path.join(block_path, "3BL260325.blk")
try:
    if os.path.exists(block_file):
        with open(block_file, 'r', encoding='gbk') as f:
            content = f.read()
        print(f"   文件存在，内容:")
        print(f"   {content}")
    else:
        print(f"   文件不存在: {block_file}")
except Exception as e:
    print(f"   错误: {e}")

# 3. 检查其他板块文件格式
print("\n3. 检查其他板块文件格式:")
try:
    for f in block_files[:3]:
        filepath = os.path.join(block_path, f)
        with open(filepath, 'r', encoding='gbk') as fobj:
            lines = fobj.readlines()[:5]
        print(f"   {f}:")
        for line in lines:
            print(f"     {line.strip()}")
except Exception as e:
    print(f"   错误: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
