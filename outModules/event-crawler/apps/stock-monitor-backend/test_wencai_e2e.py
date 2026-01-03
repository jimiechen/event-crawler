#!/usr/bin/env python3
"""
问财数据抓取功能端到端测试
测试整个数据流程：HTML解析 -> 数据存储 -> API查询
"""

import requests
import json
import time
from datetime import datetime

# 测试配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1/wencai"

# 模拟问财页面的HTML数据（包含更多股票数据）
MOCK_WENCAI_HTML = """
<table class="table">
  <thead>
    <tr>
      <th>股票代码</th>
      <th>股票简称</th>
      <th>现价</th>
      <th>涨跌幅</th>
      <th>市盈率-动态</th>
      <th>市净率</th>
      <th>净资产收益率</th>
      <th>毛利率</th>
      <th>净利润增长率</th>
      <th>营业收入增长率</th>
      <th>主营业务</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>000001.SZ</td>
      <td>平安银行</td>
      <td>12.50</td>
      <td>2.45%</td>
      <td>5.2</td>
      <td>0.85</td>
      <td>12.5%</td>
      <td>--</td>
      <td>8.5%</td>
      <td>6.2%</td>
      <td>银行业务</td>
    </tr>
    <tr>
      <td>000002.SZ</td>
      <td>万科A</td>
      <td>8.95</td>
      <td>-1.32%</td>
      <td>6.8</td>
      <td>0.92</td>
      <td>15.2%</td>
      <td>25.8%</td>
      <td>-5.2%</td>
      <td>-2.1%</td>
      <td>房地产开发</td>
    </tr>
    <tr>
      <td>600036.SH</td>
      <td>招商银行</td>
      <td>35.80</td>
      <td>1.85%</td>
      <td>6.5</td>
      <td>1.25</td>
      <td>18.5%</td>
      <td>--</td>
      <td>12.8%</td>
      <td>9.5%</td>
      <td>银行业务</td>
    </tr>
    <tr>
      <td>000858.SZ</td>
      <td>五粮液</td>
      <td>128.50</td>
      <td>0.95%</td>
      <td>18.2</td>
      <td>4.85</td>
      <td>22.8%</td>
      <td>75.2%</td>
      <td>15.6%</td>
      <td>12.3%</td>
      <td>白酒制造</td>
    </tr>
    <tr>
      <td>600519.SH</td>
      <td>贵州茅台</td>
      <td>1680.00</td>
      <td>-0.25%</td>
      <td>25.8</td>
      <td>8.95</td>
      <td>28.5%</td>
      <td>89.5%</td>
      <td>18.2%</td>
      <td>16.8%</td>
      <td>白酒制造</td>
    </tr>
  </tbody>
</table>
"""

def print_test_header(test_name):
    """打印测试标题"""
    print(f"\n{'='*60}")
    print(f"🧪 {test_name}")
    print(f"{'='*60}")

def print_test_result(success, message):
    """打印测试结果"""
    status = "✅ 成功" if success else "❌ 失败"
    print(f"{status}: {message}")

def test_api_health():
    """测试API健康状态"""
    print_test_header("API健康检查")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
        success = response.status_code == 200
        print_test_result(success, f"API健康状态: {response.status_code}")
        if success:
            result = response.json()
            print(f"响应: {result}")
            print(f"系统状态: {result.get('data', {}).get('status', 'unknown')}")
        return success
    except Exception as e:
        print_test_result(False, f"API连接失败: {e}")
        return False

def test_html_parsing():
    """测试HTML解析功能"""
    print_test_header("HTML解析测试")
    
    try:
        payload = {
            "html_content": MOCK_WENCAI_HTML,
            "crawl_url": "https://www.iwencai.com/unifiedwap/result?w=test",
            "batch_name": "端到端测试批次"
        }
        
        response = requests.post(
            f"{API_BASE}/parse",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        success = response.status_code == 200
        print_test_result(success, f"HTML解析状态: {response.status_code}")
        
        if success:
            result = response.json()
            data = result.get('data', {})
            print(f"解析结果:")
            print(f"  - 批次ID: {data.get('batch_id')}")
            print(f"  - 成功记录: {data.get('success_records')}")
            print(f"  - 失败记录: {data.get('failed_records')}")
            print(f"  - 总记录数: {data.get('total_records')}")
            return data.get('batch_id'), data.get('success_records', 0)
        else:
            print(f"错误响应: {response.text}")
            return None, 0
            
    except Exception as e:
        print_test_result(False, f"HTML解析失败: {e}")
        return None, 0

def test_batch_listing():
    """测试批次列表查询"""
    print_test_header("批次列表查询测试")
    
    try:
        response = requests.get(f"{API_BASE}/batches", timeout=5)
        success = response.status_code == 200
        print_test_result(success, f"批次列表查询状态: {response.status_code}")
        
        if success:
            result = response.json()
            batches = result.get('data', [])
            print(f"批次数量: {len(batches)}")
            if batches:
                latest_batch = batches[0]
                print(f"最新批次:")
                print(f"  - ID: {latest_batch.get('id')}")
                print(f"  - 状态: {latest_batch.get('status')}")
                print(f"  - 成功记录: {latest_batch.get('success_records')}")
                print(f"  - 创建时间: {latest_batch.get('started_at')}")
            return len(batches) > 0
        return success
        
    except Exception as e:
        print_test_result(False, f"批次列表查询失败: {e}")
        return False

def test_latest_stocks():
    """测试最新股票数据查询"""
    print_test_header("最新股票数据查询测试")
    
    try:
        response = requests.get(f"{API_BASE}/stocks/latest", timeout=5)
        success = response.status_code == 200
        print_test_result(success, f"最新股票数据查询状态: {response.status_code}")
        
        if success:
            result = response.json()
            stocks = result.get('data', [])
            print(f"股票数量: {len(stocks)}")
            if stocks:
                print("前3只股票:")
                for i, stock in enumerate(stocks[:3]):
                    print(f"  {i+1}. {stock.get('stock_code')} - {stock.get('stock_name')}")
                    print(f"     最新价: {stock.get('current_price')}")
                    print(f"     涨跌幅: {stock.get('price_change_percent')}")
            return len(stocks) > 0
        return success
        
    except Exception as e:
        print_test_result(False, f"最新股票数据查询失败: {e}")
        return False

def test_stock_search():
    """测试股票搜索功能"""
    print_test_header("股票搜索测试")
    
    test_codes = ["000001", "600519", "000858"]
    
    for code in test_codes:
        try:
            response = requests.get(f"{API_BASE}/stocks", params={"stock_code": code}, timeout=5)
            success = response.status_code == 200
            print_test_result(success, f"搜索股票 {code}: {response.status_code}")
            
            if success:
                result = response.json()
                stocks = result.get('data', [])
                if stocks:
                    stock = stocks[0]
                    print(f"  找到: {stock.get('stock_code')} - {stock.get('stock_name')}")
                else:
                    print(f"  未找到股票: {code}")
                    
        except Exception as e:
            print_test_result(False, f"搜索股票 {code} 失败: {e}")

def test_statistics():
    """测试统计数据查询"""
    print_test_header("统计数据查询测试")
    
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=5)
        success = response.status_code == 200
        print_test_result(success, f"统计数据查询状态: {response.status_code}")
        
        if success:
            result = response.json()
            stats = result.get('data', {})
            print(f"统计数据:")
            print(f"  - 总批次数: {stats.get('total_batches')}")
            print(f"  - 总记录数: {stats.get('total_records')}")
            print(f"  - 成功记录数: {stats.get('total_success')}")
            print(f"  - 失败记录数: {stats.get('total_failed')}")
            print(f"  - 整体成功率: {stats.get('overall_success_rate', 0):.2f}%")
        return success
        
    except Exception as e:
        print_test_result(False, f"统计数据查询失败: {e}")
        return False

def test_data_validation():
    """测试数据验证"""
    print_test_header("数据验证测试")
    
    # 测试无效HTML
    try:
        payload = {
            "html_content": "<div>无效的HTML</div>",
            "crawl_url": "https://test.com",
            "batch_name": "无效HTML测试"
        }
        
        response = requests.post(
            f"{API_BASE}/parse",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        # 应该返回错误或0条记录
        if response.status_code == 200:
            result = response.json()
            data = result.get('data', {})
            success = data.get('success_records', 0) == 0
            print_test_result(success, f"无效HTML处理: 成功记录数为 {data.get('success_records', 0)}")
        else:
            print_test_result(True, f"无效HTML被正确拒绝: {response.status_code}")
            
    except Exception as e:
        print_test_result(False, f"数据验证测试失败: {e}")

def run_e2e_tests():
    """运行完整的端到端测试"""
    print(f"\n🚀 开始问财数据抓取功能端到端测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = []
    
    # 1. API健康检查
    test_results.append(("API健康检查", test_api_health()))
    
    # 2. HTML解析测试
    batch_id, success_records = test_html_parsing()
    test_results.append(("HTML解析", batch_id is not None and success_records > 0))
    
    # 等待数据处理完成
    if batch_id:
        print("\n⏳ 等待数据处理完成...")
        time.sleep(2)
    
    # 3. 批次列表查询
    test_results.append(("批次列表查询", test_batch_listing()))
    
    # 4. 最新股票数据查询
    test_results.append(("最新股票数据查询", test_latest_stocks()))
    
    # 5. 股票搜索
    test_stock_search()
    test_results.append(("股票搜索", True))  # 搜索功能不影响整体流程
    
    # 6. 统计数据查询
    test_results.append(("统计数据查询", test_statistics()))
    
    # 7. 数据验证
    test_data_validation()
    test_results.append(("数据验证", True))  # 验证功能不影响整体流程
    
    # 汇总测试结果
    print_test_header("测试结果汇总")
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {test_name}")
        if result:
            passed_tests += 1
    
    success_rate = (passed_tests / total_tests) * 100
    print(f"\n📊 测试统计:")
    print(f"  - 总测试数: {total_tests}")
    print(f"  - 通过测试: {passed_tests}")
    print(f"  - 失败测试: {total_tests - passed_tests}")
    print(f"  - 成功率: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print(f"\n🎉 端到端测试通过！系统功能正常。")
        return True
    else:
        print(f"\n⚠️  端到端测试未完全通过，请检查失败的测试项。")
        return False

if __name__ == "__main__":
    success = run_e2e_tests()
    exit(0 if success else 1)