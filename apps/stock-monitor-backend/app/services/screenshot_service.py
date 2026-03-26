#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
截图服务
整合通达信测试版和天龙博弈截图skill
"""

import os
import subprocess
import json
import re
from datetime import date
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger


class ScreenshotService:
    """
    截图服务
    调用外部skill脚本进行截图
    """
    
    def __init__(self):
        """初始化截图服务"""
        # Skill脚本路径
        self.tdx_script_path = Path(r"d:\agentsTeam\skills\nanobot\tdx-test-screenshot\scripts\tdx_test_screenshot.py")
        self.tlby_script_path = Path(r"d:\agentsTeam\skills\nanobot\tlby-automation\scripts\tlby_auto.py")
        
        # 默认输出目录
        self.output_dir = Path("./screenshots")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _extract_json_from_output(self, output: str) -> Optional[Dict]:
        """
        从脚本输出中提取JSON结果
        
        Args:
            output: 脚本输出字符串
            
        Returns:
            Dict: 解析后的JSON数据
        """
        # 查找 ###NANOBOT_OUTPUT_START###...###NANOBOT_OUTPUT_END### 标记
        pattern = r'###NANOBOT_OUTPUT_START###(.*?)###NANOBOT_OUTPUT_END###'
        match = re.search(pattern, output, re.DOTALL)
        
        if match:
            try:
                json_str = match.group(1)
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                return None
        
        return None
    
    def capture_tdx_screenshot(self, 
                               stock_code: str,
                               trade_date: Optional[date] = None,
                               output_dir: Optional[str] = None,
                               no_launch: bool = True) -> Dict:
        """
        截取通达信测试版截图
        
        Args:
            stock_code: 股票代码（如 000001）
            trade_date: 交易日期
            output_dir: 输出目录
            no_launch: 是否跳过启动软件
            
        Returns:
            Dict: {
                "success": bool,
                "screenshot_path": str,
                "stock_code": str
            }
        """
        if trade_date is None:
            trade_date = date.today()
        
        if output_dir is None:
            output_dir = str(self.output_dir / trade_date.strftime("%Y%m%d") / "tdx")
        
        logger.info(f"开始截取通达信截图: {stock_code}")
        
        # 构建命令
        cmd = [
            "python",
            str(self.tdx_script_path),
            "--code", stock_code,
            "--output-dir", output_dir
        ]
        
        if no_launch:
            cmd.append("--no-launch")
        
        try:
            # 执行脚本
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=60
            )
            
            # 解析输出
            output = result.stdout + result.stderr
            json_result = self._extract_json_from_output(output)
            
            if json_result and json_result.get("success"):
                screenshot_path = json_result.get("screenshot_image")
                logger.info(f"通达信截图成功: {screenshot_path}")
                return {
                    "success": True,
                    "screenshot_path": screenshot_path,
                    "stock_code": stock_code,
                    "raw_output": output
                }
            else:
                logger.error(f"通达信截图失败: {output}")
                return {
                    "success": False,
                    "screenshot_path": None,
                    "stock_code": stock_code,
                    "error": output,
                    "raw_output": output
                }
                
        except subprocess.TimeoutExpired:
            logger.error("通达信截图超时")
            return {
                "success": False,
                "screenshot_path": None,
                "stock_code": stock_code,
                "error": "timeout"
            }
        except Exception as e:
            logger.error(f"通达信截图异常: {e}")
            return {
                "success": False,
                "screenshot_path": None,
                "stock_code": stock_code,
                "error": str(e)
            }
    
    def capture_tlby_screenshot(self,
                                stock_code: str,
                                trade_date: Optional[date] = None,
                                output_dir: Optional[str] = None,
                                no_launch: bool = True,
                                analyze_sanlong: bool = False) -> Dict:
        """
        截取天龙博弈截图
        
        Args:
            stock_code: 股票代码（如 002735）
            trade_date: 交易日期
            output_dir: 输出目录
            no_launch: 是否跳过启动软件
            analyze_sanlong: 是否使用AI分析三龙聚首指标
            
        Returns:
            Dict: {
                "success": bool,
                "intraday_path": str,
                "daily_path": str,
                "analysis_path": str,
                "stock_code": str
            }
        """
        if trade_date is None:
            trade_date = date.today()
        
        if output_dir is None:
            output_dir = str(self.output_dir / trade_date.strftime("%Y%m%d") / "tlby")
        
        logger.info(f"开始截取天龙博弈截图: {stock_code}")
        
        # 构建命令
        cmd = [
            "python",
            str(self.tlby_script_path),
            "--code", stock_code,
            "--output-dir", output_dir
        ]
        
        if no_launch:
            cmd.append("--no-launch")
        
        if analyze_sanlong:
            cmd.append("--analyze-sanlong")
        
        try:
            # 执行脚本
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=120  # 天龙博弈需要更长时间
            )
            
            # 解析输出
            output = result.stdout + result.stderr
            json_result = self._extract_json_from_output(output)
            
            if json_result and json_result.get("success"):
                intraday_path = json_result.get("intraday_image")
                daily_path = json_result.get("daily_image")
                analysis_path = json_result.get("analysis_md")
                
                logger.info(f"天龙博弈截图成功: {stock_code}")
                logger.info(f"  分时图: {intraday_path}")
                logger.info(f"  日K线: {daily_path}")
                
                return {
                    "success": True,
                    "intraday_path": intraday_path,
                    "daily_path": daily_path,
                    "analysis_path": analysis_path,
                    "stock_code": stock_code,
                    "raw_output": output
                }
            else:
                logger.error(f"天龙博弈截图失败: {output}")
                return {
                    "success": False,
                    "intraday_path": None,
                    "daily_path": None,
                    "analysis_path": None,
                    "stock_code": stock_code,
                    "error": output,
                    "raw_output": output
                }
                
        except subprocess.TimeoutExpired:
            logger.error("天龙博弈截图超时")
            return {
                "success": False,
                "intraday_path": None,
                "daily_path": None,
                "analysis_path": None,
                "stock_code": stock_code,
                "error": "timeout"
            }
        except Exception as e:
            logger.error(f"天龙博弈截图异常: {e}")
            return {
                "success": False,
                "intraday_path": None,
                "daily_path": None,
                "analysis_path": None,
                "stock_code": stock_code,
                "error": str(e)
            }
    
    def batch_capture_tlby_screenshots(self,
                                       stock_codes: List[str],
                                       trade_date: Optional[date] = None,
                                       output_dir: Optional[str] = None,
                                       no_launch: bool = True) -> List[str]:
        """
        批量截取天龙博弈截图
        
        Args:
            stock_codes: 股票代码列表
            trade_date: 交易日期
            output_dir: 输出目录
            no_launch: 是否跳过启动软件（只启动一次）
            
        Returns:
            List[str]: 成功截图的文件路径列表
        """
        if trade_date is None:
            trade_date = date.today()
        
        if output_dir is None:
            output_dir = str(self.output_dir / trade_date.strftime("%Y%m%d") / "tlby")
        
        logger.info(f"开始批量截图，共 {len(stock_codes)} 只股票")
        
        screenshot_paths = []
        
        for i, stock_code in enumerate(stock_codes):
            logger.info(f"\n[{i+1}/{len(stock_codes)}] 处理股票: {stock_code}")
            
            # 第一个股票需要启动软件，后续不需要
            current_no_launch = no_launch if i > 0 else False
            
            result = self.capture_tlby_screenshot(
                stock_code=stock_code,
                trade_date=trade_date,
                output_dir=output_dir,
                no_launch=current_no_launch
            )
            
            if result["success"]:
                if result.get("daily_path"):
                    screenshot_paths.append(result["daily_path"])
                # 暂停一下，避免操作过快
                import time
                time.sleep(2)
            else:
                logger.warning(f"股票 {stock_code} 截图失败")
        
        logger.info(f"\n批量截图完成，成功 {len(screenshot_paths)}/{len(stock_codes)} 只")
        return screenshot_paths
    
    def validate_screenshot(self, screenshot_path: str) -> bool:
        """
        验证截图文件是否存在且有效
        
        Args:
            screenshot_path: 截图文件路径
            
        Returns:
            bool: 是否有效
        """
        from pathlib import Path
        path = Path(screenshot_path)
        return path.exists() and path.is_file() and path.stat().st_size > 0
    
    def get_screenshot_info(self, screenshot_path: str) -> Dict:
        """
        获取截图文件信息
        
        Args:
            screenshot_path: 截图文件路径
            
        Returns:
            Dict: 文件信息
        """
        from pathlib import Path
        path = Path(screenshot_path)
        
        if not path.exists():
            return {"exists": False}
        
        stat = path.stat()
        return {
            "exists": True,
            "path": str(path),
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime
        }
