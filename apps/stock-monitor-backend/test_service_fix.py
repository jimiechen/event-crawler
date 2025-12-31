#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP服务修复验证脚本
用于测试http://localhost:8001/的访问，验证AttributeError修复效果
"""

import requests
import json
import sys
import time
from typing import Dict, Any

class ServiceFixTester:
    """服务修复测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        """
        初始化测试器
        
        Args:
            base_url: 服务基础URL
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{status} {test_name}")
        if details:
            print(f"   详情: {details}")
        print()
    
    def test_root_path(self) -> bool:
        """测试根路径访问"""
        try:
            response = self.session.get(f"{self.base_url}/")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict) and "name" in data:
                        self.log_test(
                            "根路径访问测试", 
                            True, 
                            f"状态码: {response.status_code}, 响应: {json.dumps(data, ensure_ascii=False, indent=2)}"
                        )
                        return True
                    else:
                        self.log_test(
                            "根路径访问测试", 
                            False, 
                            f"响应格式异常: {response.text[:200]}"
                        )
                        return False
                except json.JSONDecodeError:
                    self.log_test(
                        "根路径访问测试", 
                        False, 
                        f"JSON解析失败: {response.text[:200]}"
                    )
                    return False
            else:
                self.log_test(
                    "根路径访问测试", 
                    False, 
                    f"HTTP状态码: {response.status_code}, 响应: {response.text[:200]}"
                )
                return False
                
        except requests.exceptions.ConnectionError:
            self.log_test(
                "根路径访问测试", 
                False, 
                "连接被拒绝 - 服务器可能未启动"
            )
            return False
        except Exception as e:
            self.log_test(
                "根路径访问测试", 
                False, 
                f"异常: {str(e)}"
            )
            return False
    
    def test_health_check(self) -> bool:
        """测试健康检查接口"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/health")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict) and "status" in data:
                        self.log_test(
                            "健康检查接口测试", 
                            True, 
                            f"状态码: {response.status_code}, 健康状态: {data.get('status')}"
                        )
                        return True
                    else:
                        self.log_test(
                            "健康检查接口测试", 
                            False, 
                            f"响应格式异常: {response.text[:200]}"
                        )
                        return False
                except json.JSONDecodeError:
                    self.log_test(
                        "健康检查接口测试", 
                        False, 
                        f"JSON解析失败: {response.text[:200]}"
                    )
                    return False
            else:
                self.log_test(
                    "健康检查接口测试", 
                    False, 
                    f"HTTP状态码: {response.status_code}, 响应: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "健康检查接口测试", 
                False, 
                f"异常: {str(e)}"
            )
            return False
    
    def test_static_files(self) -> bool:
        """测试静态文件访问"""
        try:
            response = self.session.get(f"{self.base_url}/static/index.html")
            
            if response.status_code == 200:
                content = response.text
                if "html" in content.lower() and len(content) > 100:
                    self.log_test(
                        "静态文件访问测试", 
                        True, 
                        f"状态码: {response.status_code}, 内容长度: {len(content)}"
                    )
                    return True
                else:
                    self.log_test(
                        "静态文件访问测试", 
                        False, 
                        f"内容格式异常: {content[:200]}"
                    )
                    return False
            else:
                self.log_test(
                    "静态文件访问测试", 
                    False, 
                    f"HTTP状态码: {response.status_code}, 响应: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "静态文件访问测试", 
                False, 
                f"异常: {str(e)}"
            )
            return False
    
    def test_api_endpoints(self) -> bool:
        """测试API端点"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/stocks?page=1&size=5")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        self.log_test(
                            "API端点测试", 
                            True, 
                            f"状态码: {response.status_code}, 股票API正常"
                        )
                        return True
                    else:
                        self.log_test(
                            "API端点测试", 
                            False, 
                            f"响应格式异常: {response.text[:200]}"
                        )
                        return False
                except json.JSONDecodeError:
                    self.log_test(
                        "API端点测试", 
                        False, 
                        f"JSON解析失败: {response.text[:200]}"
                    )
                    return False
            else:
                self.log_test(
                    "API端点测试", 
                    False, 
                    f"HTTP状态码: {response.status_code}, 响应: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "API端点测试", 
                False, 
                f"异常: {str(e)}"
            )
            return False
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("🚀 开始HTTP服务修复验证测试...")
        print(f"🎯 目标服务: {self.base_url}")
        print("=" * 50)
        
        tests = [
            ("根路径访问", self.test_root_path),
            ("健康检查接口", self.test_health_check),
            ("静态文件访问", self.test_static_files),
            ("API端点", self.test_api_endpoints)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            if test_func():
                passed += 1
        
        print("=" * 50)
        print(f"📊 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有测试通过！服务修复成功！")
            return True
        else:
            print("⚠️ 部分测试失败，需要进一步检查")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        return {
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": total - passed,
                "success_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%"
            },
            "details": self.test_results,
            "overall_success": passed == total
        }

def main():
    """主函数"""
    print("🔧 HTTP服务修复验证脚本")
    print("用于测试 http://localhost:8001/ 的访问")
    print()
    
    tester = ServiceFixTester()
    success = tester.run_all_tests()
    
    # 生成详细报告
    report = tester.generate_report()
    
    print("\n📋 详细报告:")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    
    # 返回适当的退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()