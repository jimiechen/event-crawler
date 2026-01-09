#!/usr/bin/env python3
"""
问财API完整测试脚本
测试所有问财相关的API接口
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1/wencai"

# 测试用的HTML数据
TEST_HTML = """
<table>
<thead>
<tr>
<th>股票代码</th>
<th>股票简称</th>
<th>最新价</th>
<th>涨跌额</th>
<th>涨跌幅</th>
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
<th>60日涨跌幅</th>
<th>年初至今涨跌幅</th>
<th>所属同花顺行业</th>
<th>公司地址</th>
<th>主营业务</th>
</tr>
</thead>
<tbody>
<tr>
<td>000001.SZ</td>
<td>平安银行</td>
<td>10.50</td>
<td>0.24</td>
<td>2.34%</td>
<td>4567.89万</td>
<td>47.98亿</td>
<td>3.45%</td>
<td>10.60</td>
<td>10.20</td>
<td>10.30</td>
<td>10.26</td>
<td>1.23</td>
<td>0.24%</td>
<td>5.67</td>
<td>0.89</td>
<td>2034.57亿</td>
<td>2034.57亿</td>
<td>12.34%</td>
<td>-5.67%</td>
<td>银行</td>
<td>广东省深圳市</td>
<td>银行业务</td>
</tr>
<tr>
<td>000002.SZ</td>
<td>万科A</td>
<td>8.90</td>
<td>-0.11</td>
<td>-1.23%</td>
<td>2345.68万</td>
<td>20.88亿</td>
<td>2.34%</td>
<td>9.10</td>
<td>8.80</td>
<td>9.00</td>
<td>9.01</td>
<td>0.89</td>
<td>0.21%</td>
<td>8.90</td>
<td>1.23</td>
<td>987.65亿</td>
<td>987.65亿</td>
<td>-8.90%</td>
<td>-12.34%</td>
<td>房地产开发</td>
<td>广东省深圳市</td>
<td>房地产开发</td>
</tr>
<tr>
<td>000858.SZ</td>
<td>五粮液</td>
<td>128.50</td>
<td>2.30</td>
<td>1.82%</td>
<td>1234.56万</td>
<td>158.90亿</td>
<td>4.56%</td>
<td>130.00</td>
<td>125.00</td>
<td>126.20</td>
<td>126.20</td>
<td>1.45</td>
<td>0.32%</td>
<td>25.60</td>
<td>4.20</td>
<td>4956.78亿</td>
<td>4956.78亿</td>
<td>15.60%</td>
<td>8.90%</td>
<td>白酒</td>
<td>四川省宜宾市</td>
<td>白酒生产销售</td>
</tr>
</tbody>
</table>
"""

def test_parse_html():
    """测试HTML解析接口"""
    print("🧪 测试HTML解析接口...")
    
    url = f"{BASE_URL}/parse"
    data = {
        "html_content": TEST_HTML,
        "batch_name": "完整测试批次"
    }
    
    response = requests.post(url, json=data)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 解析成功: {result['message']}")
        print(f"批次ID: {result['data']['batch_id']}")
        print(f"总记录数: {result['data']['total_records']}")
        print(f"成功记录数: {result['data']['success_records']}")
        print(f"失败记录数: {result['data']['failed_records']}")
        return result['data']['batch_id']
    else:
        print(f"❌ 解析失败: {response.text}")
        return None

def test_get_batches():
    """测试获取批次列表"""
    print("\n🧪 测试获取批次列表...")
    
    url = f"{BASE_URL}/batches"
    response = requests.get(url)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 获取成功: {result['message']}")
        batches = result['data']
        for batch in batches[:3]:  # 显示前3个批次
            print(f"  批次ID: {batch['id']}, 状态: {batch['status']}, 记录数: {batch['total_records']}")
        return batches
    else:
        print(f"❌ 获取失败: {response.text}")
        return []

def test_get_batch_detail(batch_id):
    """测试获取批次详情"""
    print(f"\n🧪 测试获取批次详情 (ID: {batch_id})...")
    
    url = f"{BASE_URL}/batches/{batch_id}"
    response = requests.get(url)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 获取成功: {result['message']}")
        batch = result['data']
        print(f"  批次名称: {batch['batch_name']}")
        print(f"  状态: {batch['status']}")
        print(f"  开始时间: {batch['started_at']}")
        print(f"  总记录数: {batch['total_records']}")
        print(f"  成功记录数: {batch['success_records']}")
        return batch
    else:
        print(f"❌ 获取失败: {response.text}")
        return None

def test_get_stocks():
    """测试获取股票数据"""
    print("\n🧪 测试获取股票数据...")
    
    url = f"{BASE_URL}/stocks?limit=5"
    response = requests.get(url)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 获取成功: {result['message']}")
        stocks = result['data']
        for stock in stocks[:3]:  # 显示前3只股票
            print(f"  {stock['stock_code']} {stock['stock_name']}: {stock['current_price']} ({stock['price_change_percent']})")
        return stocks
    else:
        print(f"❌ 获取失败: {response.text}")
        return []

def test_get_latest_stocks():
    """测试获取最新股票数据"""
    print("\n🧪 测试获取最新股票数据...")
    
    url = f"{BASE_URL}/stocks/latest?limit=10"
    response = requests.get(url)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 获取成功: {result['message']}")
        stocks = result['data']
        for stock in stocks:
            print(f"  {stock['stock_code']} {stock['stock_name']}: {stock['current_price']} (批次: {stock['crawl_batch_id']})")
        return stocks
    else:
        print(f"❌ 获取失败: {response.text}")
        return []

def test_get_stats():
    """测试获取统计信息"""
    print("\n🧪 测试获取统计信息...")
    
    url = f"{BASE_URL}/stats?days=7"
    response = requests.get(url)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 获取成功: {result['message']}")
        stats = result['data']
        print(f"  总批次数: {stats['total_batches']}")
        print(f"  总记录数: {stats['total_records']}")
        print(f"  成功记录数: {stats['total_success']}")
        print(f"  失败记录数: {stats['total_failed']}")
        print(f"  总体成功率: {stats['overall_success_rate']}%")
        return stats
    else:
        print(f"❌ 获取失败: {response.text}")
        return None

def test_search_stock():
    """测试按股票代码搜索"""
    print("\n🧪 测试按股票代码搜索...")
    
    url = f"{BASE_URL}/stocks?stock_code=000001&limit=5"
    response = requests.get(url)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 搜索成功: {result['message']}")
        stocks = result['data']
        for stock in stocks:
            print(f"  {stock['stock_code']} {stock['stock_name']}: {stock['current_price']} (时间: {stock['created_at']})")
        return stocks
    else:
        print(f"❌ 搜索失败: {response.text}")
        return []

def main():
    """主测试函数"""
    print("🚀 开始问财API完整测试")
    print("=" * 50)
    
    # 1. 测试HTML解析
    batch_id = test_parse_html()
    
    # 等待一秒确保数据保存完成
    time.sleep(1)
    
    # 2. 测试获取批次列表
    batches = test_get_batches()
    
    # 3. 测试获取批次详情
    if batch_id:
        test_get_batch_detail(batch_id)
    elif batches:
        test_get_batch_detail(batches[0]['id'])
    
    # 4. 测试获取股票数据
    test_get_stocks()
    
    # 5. 测试获取最新股票数据
    test_get_latest_stocks()
    
    # 6. 测试获取统计信息
    test_get_stats()
    
    # 7. 测试按股票代码搜索
    test_search_stock()
    
    print("\n" + "=" * 50)
    print("🎉 问财API完整测试完成！")

if __name__ == "__main__":
    main()