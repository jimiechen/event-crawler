#!/usr/bin/env python3
"""
简单的解析测试脚本
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.wencai_service import WencaiService
from bs4 import BeautifulSoup

def test_parse():
    # 读取HTML文件
    html_file = "/Users/mac/ok-mcp/app/stock-monitor-backend/debug/html_files/wencai_html_20251027_194246_21.html"
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"HTML文件大小: {len(html_content)} 字符")
        
        # 创建服务实例（不需要数据库连接来测试解析）
        service = WencaiService(None)
        
        # 测试解析
        print("开始解析...")
        result = service.parse_html_table(html_content, debug=True)
        
        print(f"解析结果: {len(result)} 条记录")
        for i, stock in enumerate(result[:3]):  # 只显示前3条
            print(f"股票 {i+1}: {stock}")
        
        # 如果没有结果，尝试直接测试div表格解析
        if len(result) == 0:
            print("\n尝试直接解析div表格...")
            soup = BeautifulSoup(html_content, 'html.parser')
            div_result = service._parse_wencai_div_table(soup, debug=True)
            print(f"div表格解析结果: {len(div_result)} 条记录")
            for i, stock in enumerate(div_result[:3]):
                print(f"div股票 {i+1}: {stock}")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parse()