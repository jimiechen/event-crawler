#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试问财API接口
"""

import requests
import json

# 测试HTML内容（从webcai.txt文件中提取的示例）
test_html = """
<table class="table">
<thead>
<tr>
<th>股票代码</th>
<th>股票简称</th>
<th>现价</th>
<th>涨跌幅</th>
<th>涨跌额</th>
<th>成交量</th>
<th>成交额</th>
<th>振幅</th>
<th>最高</th>
<th>最低</th>
<th>今开</th>
<th>昨收</th>
<th>量比</th>
<th>换手率</th>
<th>市盈率-动态</th>
<th>市净率</th>
<th>总市值</th>
<th>流通市值</th>
<th>净资产收益率</th>
<th>毛利率</th>
<th>净利润增长率</th>
<th>营业收入增长率</th>
<th>公司地址</th>
<th>主营业务</th>
</tr>
</thead>
<tbody>
<tr>
<td>000001.SZ</td>
<td>平安银行</td>
<td>10.50</td>
<td>2.34%</td>
<td>0.24</td>
<td>45678900</td>
<td>479827000</td>
<td>3.45%</td>
<td>10.60</td>
<td>10.20</td>
<td>10.30</td>
<td>10.26</td>
<td>1.23</td>
<td>0.24%</td>
<td>5.67</td>
<td>0.89</td>
<td>203456789000</td>
<td>203456789000</td>
<td>12.34%</td>
<td>45.67%</td>
<td>8.90%</td>
<td>12.34%</td>
<td>广东省深圳市</td>
<td>银行业务</td>
</tr>
<tr>
<td>000002.SZ</td>
<td>万科A</td>
<td>8.90</td>
<td>-1.23%</td>
<td>-0.11</td>
<td>23456789</td>
<td>208765432</td>
<td>2.34%</td>
<td>9.10</td>
<td>8.80</td>
<td>9.00</td>
<td>9.01</td>
<td>0.89</td>
<td>0.21%</td>
<td>7.89</td>
<td>1.23</td>
<td>98765432100</td>
<td>98765432100</td>
<td>10.23%</td>
<td>23.45%</td>
<td>5.67%</td>
<td>8.90%</td>
<td>广东省深圳市</td>
<td>房地产开发</td>
</tr>
</tbody>
</table>
"""

def test_parse_wencai_html():
    """测试解析问财HTML接口"""
    url = "http://localhost:8000/api/v1/wencai/parse"
    
    payload = {
        "html_content": test_html,
        "source_url": "https://www.iwencai.com/unifiedwap/result?w=test"
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ 解析成功，共解析到 {len(data['data']['stocks'])} 只股票")
                return data['data']['batch_id']
            else:
                print(f"❌ 解析失败: {data.get('message')}")
        else:
            print(f"❌ 请求失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    return None

def test_get_batch_info(batch_id):
    """测试获取批次信息接口"""
    if not batch_id:
        print("❌ 没有有效的批次ID")
        return
        
    url = f"http://localhost:8000/api/v1/wencai/batches/{batch_id}"
    
    try:
        response = requests.get(url)
        print(f"\n批次信息查询:")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def test_get_latest_stocks():
    """测试获取最新股票数据接口"""
    url = "http://localhost:8000/api/v1/wencai/stocks/latest"
    
    try:
        response = requests.get(url)
        print(f"\n最新股票数据查询:")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def test_get_stats():
    """测试获取统计信息接口"""
    url = "http://localhost:8000/api/v1/wencai/stats"
    
    try:
        response = requests.get(url)
        print(f"\n统计信息查询:")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    print("🧪 开始测试问财API接口...")
    
    # 测试解析HTML
    batch_id = test_parse_wencai_html()
    
    # 测试获取批次信息
    test_get_batch_info(batch_id)
    
    # 测试获取最新股票数据
    test_get_latest_stocks()
    
    # 测试获取统计信息
    test_get_stats()
    
    print("\n🎉 测试完成！")