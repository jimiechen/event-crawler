#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行脚本
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd: list, cwd: str = None) -> int:
    """运行命令并返回退出码"""
    print(f"Running: {' '.join(cmd)}")
    if cwd:
        print(f"Working directory: {cwd}")
    
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def run_tests(test_type: str = "all", coverage: bool = False, verbose: bool = False):
    """运行测试"""
    project_root = Path(__file__).parent
    
    # 基础pytest命令
    cmd = ["python", "-m", "pytest"]
    
    # 根据测试类型添加参数
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "api":
        cmd.extend(["-m", "api"])
    elif test_type == "service":
        cmd.extend(["-m", "service"])
    elif test_type == "repository":
        cmd.extend(["-m", "repository"])
    elif test_type == "model":
        cmd.extend(["-m", "model"])
    elif test_type == "slow":
        cmd.extend(["-m", "slow"])
    elif test_type == "fast":
        cmd.extend(["-m", "not slow"])
    elif test_type != "all":
        # 运行特定测试文件
        cmd.append(f"tests/test_{test_type}.py")
    
    # 添加覆盖率报告
    if coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
    
    # 详细输出
    if verbose:
        cmd.append("-vv")
    
    # 运行测试
    return run_command(cmd, str(project_root))


def run_linting():
    """运行代码检查"""
    project_root = Path(__file__).parent
    
    print("Running code linting...")
    
    # 运行flake8
    print("\n=== Running flake8 ===")
    flake8_result = run_command([
        "python", "-m", "flake8", 
        "app", "tests",
        "--max-line-length=120",
        "--ignore=E203,W503"
    ], str(project_root))
    
    # 运行mypy
    print("\n=== Running mypy ===")
    mypy_result = run_command([
        "python", "-m", "mypy", 
        "app",
        "--ignore-missing-imports"
    ], str(project_root))
    
    return flake8_result == 0 and mypy_result == 0


def run_formatting():
    """运行代码格式化"""
    project_root = Path(__file__).parent
    
    print("Running code formatting...")
    
    # 运行black
    print("\n=== Running black ===")
    black_result = run_command([
        "python", "-m", "black", 
        "app", "tests",
        "--line-length=120"
    ], str(project_root))
    
    # 运行isort
    print("\n=== Running isort ===")
    isort_result = run_command([
        "python", "-m", "isort", 
        "app", "tests",
        "--profile=black"
    ], str(project_root))
    
    return black_result == 0 and isort_result == 0


def check_dependencies():
    """检查依赖是否安装"""
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "httpx",
        "black",
        "isort",
        "flake8",
        "mypy"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing packages: {', '.join(missing_packages)}")
        print("Please install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行测试和代码检查")
    
    parser.add_argument(
        "action",
        choices=["test", "lint", "format", "all"],
        help="要执行的操作"
    )
    
    parser.add_argument(
        "--type",
        choices=["all", "unit", "integration", "api", "service", "repository", "model", "slow", "fast"],
        default="all",
        help="测试类型"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="生成覆盖率报告"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出"
    )
    
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="检查依赖"
    )
    
    args = parser.parse_args()
    
    # 检查依赖
    if args.check_deps or args.action in ["test", "lint", "format", "all"]:
        if not check_dependencies():
            sys.exit(1)
    
    success = True
    
    if args.action == "test":
        success = run_tests(args.type, args.coverage, args.verbose) == 0
    
    elif args.action == "lint":
        success = run_linting()
    
    elif args.action == "format":
        success = run_formatting()
    
    elif args.action == "all":
        print("=== Running all checks ===")
        
        # 1. 格式化代码
        print("\n1. Formatting code...")
        format_success = run_formatting()
        
        # 2. 代码检查
        print("\n2. Linting code...")
        lint_success = run_linting()
        
        # 3. 运行测试
        print("\n3. Running tests...")
        test_success = run_tests(args.type, args.coverage, args.verbose) == 0
        
        success = format_success and lint_success and test_success
        
        # 总结
        print("\n=== Summary ===")
        print(f"Formatting: {'✓' if format_success else '✗'}")
        print(f"Linting: {'✓' if lint_success else '✗'}")
        print(f"Tests: {'✓' if test_success else '✗'}")
    
    if success:
        print("\n✓ All checks passed!")
        sys.exit(0)
    else:
        print("\n✗ Some checks failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()