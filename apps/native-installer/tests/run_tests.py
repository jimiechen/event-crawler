#!/usr/bin/env python3
import sys
import os
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.tests_dir = self.project_root / 'tests'
        self.reports_dir = self.tests_dir / 'test_reports'
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def run_unit_tests(self):
        """运行单元测试"""
        print("\n" + "=" * 60)
        print("运行单元测试")
        print("=" * 60)
        
        test_file = self.tests_dir / 'test_installer.py'
        
        if not test_file.exists():
            print(f"❌ 单元测试文件不存在: {test_file}")
            return False
        
        try:
            result = subprocess.run(
                [sys.executable, str(test_file)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            success = result.returncode == 0
            if success:
                print("\n✅ 单元测试完成")
            else:
                print(f"\n❌ 单元测试失败，返回码: {result.returncode}")
            
            return success
            
        except subprocess.TimeoutExpired:
            print("❌ 单元测试超时")
            return False
        except Exception as e:
            print(f"❌ 单元测试执行失败: {e}")
            return False
    
    def run_acceptance_tests(self):
        """运行验收测试"""
        print("\n" + "=" * 60)
        print("运行验收测试")
        print("=" * 60)
        
        test_file = self.tests_dir / 'acceptance_test_installer.py'
        
        if not test_file.exists():
            print(f"❌ 验收测试文件不存在: {test_file}")
            return False
        
        try:
            result = subprocess.run(
                [sys.executable, str(test_file)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            success = result.returncode == 0
            if success:
                print("\n✅ 验收测试完成")
            else:
                print(f"\n❌ 验收测试失败，返回码: {result.returncode}")
            
            return success
            
        except subprocess.TimeoutExpired:
            print("❌ 验收测试超时")
            return False
        except Exception as e:
            print(f"❌ 验收测试执行失败: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 60)
        print("运行完整测试套件")
        print("=" * 60)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = {
            'unit_tests': self.run_unit_tests(),
            'acceptance_tests': self.run_acceptance_tests(),
        }
        
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(1 for v in results.values() if v)
        failed_tests = total_tests - passed_tests
        
        print(f"单元测试: {'✅ 通过' if results['unit_tests'] else '❌ 失败'}")
        print(f"验收测试: {'✅ 通过' if results['acceptance_tests'] else '❌ 失败'}")
        print(f"\n总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"通过率: {(passed_tests/total_tests*100):.1f}%")
        
        all_passed = all(results.values())
        
        if all_passed:
            print("\n🎉 所有测试通过！")
        else:
            print("\n⚠️ 部分测试失败，请查看详细日志")
        
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        return all_passed
    
    def run_specific_test(self, test_type: str):
        """运行特定类型的测试"""
        if test_type == 'unit':
            return self.run_unit_tests()
        elif test_type == 'acceptance':
            return self.run_acceptance_tests()
        elif test_type == 'all':
            return self.run_all_tests()
        else:
            print(f"❌ 未知的测试类型: {test_type}")
            print("支持的测试类型: unit, acceptance, all")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='StockMonitor 打包解决方案测试运行器',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'test_type',
        nargs='?',
        choices=['unit', 'acceptance', 'all'],
        default='all',
        help='测试类型: unit（单元测试）, acceptance（验收测试）, all（所有测试）'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出'
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    success = runner.run_specific_test(args.test_type)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()