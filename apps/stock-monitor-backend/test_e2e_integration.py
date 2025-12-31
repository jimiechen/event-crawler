#!/usr/bin/env python3
"""
端到端集成测试脚本
测试Chrome插件到HTML页面的完整数据流
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# 测试配置
BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v1"

class E2EIntegrationTest:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, message: str = "", data: Any = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
    async def test_health_check(self):
        """测试健康检查接口"""
        try:
            async with self.session.get(f"{API_BASE}/health") as response:
                data = await response.json()
                success = response.status == 200 and data.get("success", False)
                self.log_test("健康检查", success, f"状态码: {response.status}", data)
                return success
        except Exception as e:
            self.log_test("健康检查", False, f"请求失败: {str(e)}")
            return False
    
    async def test_chrome_plugin_data_submission(self):
        """测试Chrome插件数据提交"""
        # 模拟Chrome插件发送的数据
        test_data = {
            "data_list": [
                {
                    "stock_code": "999001",
                    "price": 15.67,
                    "close_price": 15.67,
                    "open_price": 15.56,
                    "high_price": 15.89,
                    "low_price": 15.45,
                    "volume": 1234567,
                    "amount": 19345678.90,
                    "change_percent": 2.34,
                    "trade_date": "2025-10-16",
                    "data_time": datetime.now().isoformat()
                },
                {
                    "stock_code": "999002",
                    "price": 8.23,
                    "close_price": 8.23,
                    "open_price": 8.34,
                    "high_price": 8.45,
                    "low_price": 8.12,
                    "volume": 987654,
                    "amount": 8123456.78,
                    "change_percent": -1.23,
                    "trade_date": "2025-10-16",
                    "data_time": datetime.now().isoformat()
                }
            ]
        }
        
        try:
            async with self.session.post(
                f"{API_BASE}/stocks/data/batch",
                json=test_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                data = await response.json()
                success = response.status == 200 and data.get("success", False)
                self.log_test("Chrome插件数据提交", success, f"状态码: {response.status}", data)
                return success
        except Exception as e:
            self.log_test("Chrome插件数据提交", False, f"请求失败: {str(e)}")
            return False
    
    async def test_stock_info_creation(self):
        """测试股票信息创建"""
        test_stocks = [
            {"stock_code": "999001", "stock_name": "测试股票001", "market": "SZ"},
            {"stock_code": "999002", "stock_name": "测试股票002", "market": "SZ"}
        ]
        
        success_count = 0
        for stock in test_stocks:
            try:
                async with self.session.post(
                    f"{API_BASE}/stocks/info",
                    json=stock,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    data = await response.json()
                    if response.status == 200 and data.get("success", False):
                        success_count += 1
            except Exception as e:
                print(f"创建股票信息失败 {stock['stock_code']}: {str(e)}")
        
        success = success_count >= len(test_stocks)
        self.log_test("股票信息创建", success, f"成功创建 {success_count}/{len(test_stocks)} 条记录")
        return success
    
    async def test_stock_search_api(self):
        """测试股票搜索API"""
        test_cases = [
            {"q": "999", "expected_min": 2},
            {"q": "000", "expected_min": 1},
            {"q": "平安", "expected_min": 1}
        ]
        
        success_count = 0
        for case in test_cases:
            try:
                async with self.session.get(
                    f"{API_BASE}/stocks/search",
                    params={"q": case["q"], "limit": 10}
                ) as response:
                    data = await response.json()
                    if (response.status == 200 and 
                        data.get("success", False) and 
                        len(data.get("data", [])) >= case["expected_min"]):
                        success_count += 1
                        print(f"  搜索 '{case['q']}': 找到 {len(data.get('data', []))} 条结果")
                    else:
                        print(f"  搜索 '{case['q']}' 失败: {data.get('message', '未知错误')}")
            except Exception as e:
                print(f"  搜索 '{case['q']}' 异常: {str(e)}")
        
        success = success_count == len(test_cases)
        self.log_test("股票搜索API", success, f"通过 {success_count}/{len(test_cases)} 个测试用例")
        return success
    
    async def test_stock_list_api(self):
        """测试股票列表API"""
        try:
            async with self.session.get(
                f"{API_BASE}/stocks",
                params={"page": 1, "size": 20}
            ) as response:
                data = await response.json()
                success = (response.status == 200 and 
                          data.get("success", False) and 
                          len(data.get("data", [])) > 0)
                self.log_test("股票列表API", success, 
                            f"状态码: {response.status}, 返回 {len(data.get('data', []))} 条记录")
                return success
        except Exception as e:
            self.log_test("股票列表API", False, f"请求失败: {str(e)}")
            return False
    
    async def test_static_file_access(self):
        """测试静态文件访问"""
        try:
            async with self.session.get(f"{BASE_URL}/static/index.html") as response:
                content = await response.text()
                success = (response.status == 200 and 
                          "同花顺股票监控系统" in content and 
                          len(content) > 1000)
                self.log_test("静态文件访问", success, 
                            f"状态码: {response.status}, 内容长度: {len(content)}")
                return success
        except Exception as e:
            self.log_test("静态文件访问", False, f"请求失败: {str(e)}")
            return False
    
    async def test_data_flow_integrity(self):
        """测试数据流完整性"""
        print("\n🔄 开始数据流完整性测试...")
        
        # 1. 提交测试数据
        await self.test_chrome_plugin_data_submission()
        await asyncio.sleep(1)  # 等待数据处理
        
        # 2. 创建股票信息
        await self.test_stock_info_creation()
        await asyncio.sleep(1)
        
        # 3. 验证数据可以通过API查询到
        search_success = await self.test_stock_search_api()
        list_success = await self.test_stock_list_api()
        
        success = search_success and list_success
        self.log_test("数据流完整性", success, "Chrome插件 -> 数据库 -> API -> HTML页面")
        return success
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始端到端集成测试...")
        print("=" * 60)
        
        # 基础功能测试
        await self.test_health_check()
        await self.test_static_file_access()
        
        # 数据流测试
        await self.test_data_flow_integrity()
        
        # 生成测试报告
        return self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 测试报告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        print("\n" + "=" * 60)
        
        # 保存详细报告
        report_file = f"e2e_test_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        print(f"📄 详细报告已保存到: {report_file}")
        
        return passed_tests == total_tests

async def main():
    """主函数"""
    async with E2EIntegrationTest() as tester:
        success = await tester.run_all_tests()
        return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit_code = 0 if success else 1
        print(f"\n🏁 测试完成，退出码: {exit_code}")
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n💥 测试执行异常: {str(e)}")
        exit(1)