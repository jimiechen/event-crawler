#!/usr/bin/env python3
"""
同花顺股票监控系统综合测试脚本
测试所有API功能和系统稳定性
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys
import time

class ComprehensiveTest:
    """综合测试类"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_prefix = "/api/v1"
        self.test_results = []
        self.client = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    def log_test(self, test_name: str, success: bool, message: str = "", data: Any = None):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        if data and not success:
            print(f"   详细信息: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    async def test_health_endpoints(self):
        """测试健康检查端点"""
        print("\n=== 健康检查测试 ===")
        
        # 基础健康检查
        try:
            response = await self.client.get(f"{self.base_url}{self.api_prefix}/health")
            success = response.status_code == 200
            data = response.json() if success else {"status_code": response.status_code, "text": response.text}
            self.log_test("基础健康检查", success, f"状态码: {response.status_code}", data)
        except Exception as e:
            self.log_test("基础健康检查", False, f"请求异常: {str(e)}")
        
        # 详细健康检查
        try:
            response = await self.client.get(f"{self.base_url}{self.api_prefix}/health/detailed")
            success = response.status_code == 200
            data = response.json() if success else {"status_code": response.status_code, "text": response.text}
            self.log_test("详细健康检查", success, f"状态码: {response.status_code}", data)
        except Exception as e:
            self.log_test("详细健康检查", False, f"请求异常: {str(e)}")
        
        # 数据库健康检查
        try:
            response = await self.client.get(f"{self.base_url}{self.api_prefix}/health/database")
            success = response.status_code == 200
            data = response.json() if success else {"status_code": response.status_code, "text": response.text}
            self.log_test("数据库健康检查", success, f"状态码: {response.status_code}", data)
        except Exception as e:
            self.log_test("数据库健康检查", False, f"请求异常: {str(e)}")
    
    async def test_stock_info_crud(self):
        """测试股票信息CRUD操作"""
        print("\n=== 股票信息CRUD测试 ===")
        
        test_stock = {
            "code": "TEST01",
            "name": "测试股票1",
            "market": "SZ",
            "industry": "测试行业"
        }
        
        # 创建股票信息
        try:
            response = await self.client.post(
                f"{self.base_url}{self.api_prefix}/stocks/info",
                json=test_stock
            )
            success = response.status_code == 200
            data = response.json() if success else {"status_code": response.status_code, "text": response.text}
            self.log_test("创建股票信息", success, f"状态码: {response.status_code}", data)
        except Exception as e:
            self.log_test("创建股票信息", False, f"请求异常: {str(e)}")
        
        # 查询单个股票信息
        try:
            response = await self.client.get(f"{self.base_url}{self.api_prefix}/stocks/info/TEST01")
            success = response.status_code == 200
            data = response.json() if success else {"status_code": response.status_code, "text": response.text}
            self.log_test("查询单个股票信息", success, f"状态码: {response.status_code}", data)
        except Exception as e:
            self.log_test("查询单个股票信息", False, f"请求异常: {str(e)}")
        
        # 查询股票信息列表
        try:
            response = await self.client.get(f"{self.base_url}{self.api_prefix}/stocks/info?limit=10")
            success = response.status_code == 200
            data = response.json() if success else {"status_code": response.status_code, "text": response.text}
            self.log_test("查询股票信息列表", success, f"状态码: {response.status_code}", data)
        except Exception as e:
            self.log_test("查询股票信息列表", False, f"请求异常: {str(e)}")
        
        # 更新股票信息
        try:
            update_data = {"name": "测试股票1(更新)", "industry": "更新行业"}
            response = await self.client.put(
                f"{self.base_url}{self.api_prefix}/stocks/info/TEST01",
                json=update_data
            )
            success = response.status_code == 200
            data = response.json() if success else {"status_code": response.status_code, "text": response.text}
            self.log_test("更新股票信息", success, f"状态码: {response.status_code}", data)
        except Exception as e:
            self.log_test("更新股票信息", False, f"请求异常: {str(e)}")
        
        # 删除股票信息
        try:
            response = await self.client.delete(f"{self.base_url}{self.api_prefix}/stocks/info/TEST01")
            success = response.status_code == 200
            data = response.json() if success else {"status_code": response.status_code, "text": response.text}
            self.log_test("删除股票信息", success, f"状态码: {response.status_code}", data)
        except Exception as e:
            self.log_test("删除股票信息", False, f"请求异常: {str(e)}")
    
    async def test_stock_data_operations(self):
        """测试股票数据操作"""
        print("\n=== 股票数据操作测试 ===")
        
        # 先创建测试股票
        test_stock = {
            "code": "TEST02",
            "name": "测试股票2",
            "market": "SH",
            "industry": "测试行业"
        }
        
        try:
            await self.client.post(f"{self.base_url}{self.api_prefix}/stocks/info", json=test_stock)
        except:
            pass  # 忽略创建错误，可能已存在
        
        # 单条数据提交
        test_data = {
            "code": "TEST02",
            "name": "测试股票2",
            "current_price": 12.50,
            "open_price": 12.30,
            "prev_close": 12.40,
            "change_amount": 0.10,
            "volume": 1000000,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}{self.api_prefix}/stocks/data",
                json=test_data
            )
            success = response.status_code == 200
            data = response.json() if success else {"status_code": response.status_code, "text": response.text}
            self.log_test("单条数据提交", success, f"状态码: {response.status_code}", data)
        except Exception as e:
            self.log_test("单条数据提交", False, f"请求异常: {str(e)}")
        
        # 批量数据提交
        batch_data = []
        for i in range(3):
            data_item = {
                "code": "TEST02",
                "name": "测试股票2",
                "current_price": 12.50 + i * 0.1,
                "volume": 1000000 + i * 100000,
                "timestamp": (datetime.now() + timedelta(minutes=i)).isoformat()
            }
            batch_data.append(data_item)
        
        try:
            response = await self.client.post(
                f"{self.base_url}{self.api_prefix}/stocks/data/batch",
                json={"data": batch_data}
            )
            success = response.status_code == 200
            data = response.json() if success else {"status_code": response.status_code, "text": response.text}
            self.log_test("批量数据提交", success, f"状态码: {response.status_code}", data)
        except Exception as e:
            self.log_test("批量数据提交", False, f"请求异常: {str(e)}")
        
        # 清理测试数据
        try:
            await self.client.delete(f"{self.base_url}{self.api_prefix}/stocks/info/TEST02")
        except:
            pass
    
    async def test_monitor_operations(self):
        """测试监控操作"""
        print("\n=== 监控操作测试 ===")
        
        # 先创建测试股票
        test_stock = {
            "code": "TEST03",
            "name": "测试股票3",
            "market": "SZ",
            "industry": "测试行业"
        }
        
        try:
            await self.client.post(f"{self.base_url}{self.api_prefix}/stocks/info", json=test_stock)
        except:
            pass
        
        # 添加监控
        monitor_data = {
            "stock_code": "TEST03",
            "priority": 1,
            "auto_create_stock": False
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}{self.api_prefix}/monitors",
                json=monitor_data
            )
            success = response.status_code == 200
            data = response.json() if success else {"status_code": response.status_code, "text": response.text}
            self.log_test("添加监控", success, f"状态码: {response.status_code}", data)
        except Exception as e:
            self.log_test("添加监控", False, f"请求异常: {str(e)}")
        
        # 查询监控列表
        try:
            response = await self.client.get(f"{self.base_url}{self.api_prefix}/monitors?limit=10")
            success = response.status_code == 200
            data = response.json() if success else {"status_code": response.status_code, "text": response.text}
            self.log_test("查询监控列表", success, f"状态码: {response.status_code}", data)
        except Exception as e:
            self.log_test("查询监控列表", False, f"请求异常: {str(e)}")
        
        # 获取监控代码列表
        try:
            response = await self.client.get(f"{self.base_url}{self.api_prefix}/monitors/codes")
            success = response.status_code == 200
            data = response.json() if success else {"status_code": response.status_code, "text": response.text}
            self.log_test("获取监控代码列表", success, f"状态码: {response.status_code}", data)
        except Exception as e:
            self.log_test("获取监控代码列表", False, f"请求异常: {str(e)}")
        
        # 更新监控
        try:
            update_data = {"priority": 2}
            response = await self.client.put(
                f"{self.base_url}{self.api_prefix}/monitors/TEST03",
                json=update_data
            )
            success = response.status_code == 200
            data = response.json() if success else {"status_code": response.status_code, "text": response.text}
            self.log_test("更新监控", success, f"状态码: {response.status_code}", data)
        except Exception as e:
            self.log_test("更新监控", False, f"请求异常: {str(e)}")
        
        # 删除监控
        try:
            response = await self.client.delete(f"{self.base_url}{self.api_prefix}/monitors/TEST03")
            success = response.status_code == 200
            data = response.json() if success else {"status_code": response.status_code, "text": response.text}
            self.log_test("删除监控", success, f"状态码: {response.status_code}", data)
        except Exception as e:
            self.log_test("删除监控", False, f"请求异常: {str(e)}")
        
        # 清理测试数据
        try:
            await self.client.delete(f"{self.base_url}{self.api_prefix}/stocks/info/TEST03")
        except:
            pass
    
    async def test_error_handling(self):
        """测试错误处理"""
        print("\n=== 错误处理测试 ===")
        
        # 测试404错误
        try:
            response = await self.client.get(f"{self.base_url}{self.api_prefix}/stocks/info/NOTEXIST")
            success = response.status_code == 404
            data = response.json() if response.status_code != 500 else {"status_code": response.status_code}
            self.log_test("404错误处理", success, f"状态码: {response.status_code}", data)
        except Exception as e:
            self.log_test("404错误处理", False, f"请求异常: {str(e)}")
        
        # 测试参数验证错误
        try:
            invalid_data = {"code": "INVALID", "name": ""}  # 缺少必填字段
            response = await self.client.post(
                f"{self.base_url}{self.api_prefix}/stocks/info",
                json=invalid_data
            )
            success = response.status_code == 422
            data = response.json() if response.status_code != 500 else {"status_code": response.status_code}
            self.log_test("参数验证错误", success, f"状态码: {response.status_code}", data)
        except Exception as e:
            self.log_test("参数验证错误", False, f"请求异常: {str(e)}")
    
    async def test_performance(self):
        """测试性能"""
        print("\n=== 性能测试 ===")
        
        # 并发请求测试
        async def single_health_check():
            try:
                response = await self.client.get(f"{self.base_url}{self.api_prefix}/health")
                return response.status_code == 200
            except:
                return False
        
        start_time = time.time()
        tasks = [single_health_check() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        success_count = sum(1 for r in results if r is True)
        total_time = end_time - start_time
        
        success = success_count >= 8  # 至少80%成功
        message = f"10个并发请求，成功{success_count}个，耗时{total_time:.2f}秒"
        self.log_test("并发性能测试", success, message)
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("测试报告")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        print("\n详细结果:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test']}")
        
        # 保存详细报告到文件
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n详细报告已保存到: {report_file}")
        
        return passed_tests == total_tests
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("开始综合测试...")
        print(f"测试目标: {self.base_url}")
        
        # 等待服务启动
        print("\n等待服务启动...")
        for i in range(10):
            try:
                response = await self.client.get(f"{self.base_url}{self.api_prefix}/health")
                if response.status_code == 200:
                    print("✅ 服务已启动")
                    break
            except:
                pass
            
            if i < 9:
                print(f"等待中... ({i+1}/10)")
                await asyncio.sleep(2)
            else:
                print("❌ 服务启动超时")
                return False
        
        # 运行测试
        await self.test_health_endpoints()
        await self.test_stock_info_crud()
        await self.test_stock_data_operations()
        await self.test_monitor_operations()
        await self.test_error_handling()
        await self.test_performance()
        
        # 生成报告
        return self.generate_report()

async def main():
    """主函数"""
    base_url = "http://localhost:8000"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    async with ComprehensiveTest(base_url) as test:
        success = await test.run_all_tests()
        
        if success:
            print("\n🎉 所有测试通过！系统运行正常。")
            sys.exit(0)
        else:
            print("\n⚠️  部分测试失败，请检查系统状态。")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())