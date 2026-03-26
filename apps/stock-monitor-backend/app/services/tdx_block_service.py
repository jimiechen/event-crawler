#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通达信板块服务
使用官方API创建板块并添加股票
"""

import os
import sys
from datetime import date
from typing import List
from loguru import logger

# 添加通达信路径
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")


class TdxBlockService:
    """通达信板块服务"""
    
    def __init__(self, tdx_path: str = r"C:\new_tdx_test"):
        """
        初始化
        
        Args:
            tdx_path: 通达信安装路径
        """
        self.tdx_path = tdx_path
        self.block_path = os.path.join(tdx_path, "T0002", "blocknew")
        self._tq = None
        
    def _get_tq(self):
        """获取通达信API实例"""
        if self._tq is None:
            from tqcenter import tq
            tq.initialize(__file__)
            self._tq = tq
        return self._tq
        
    def _convert_stock_code(self, code: str) -> str:
        """
        转换股票代码为通达信板块文件格式
        
        Args:
            code: 股票代码，如 "000001.SZ", "600000.SH"
            
        Returns:
            str: 通达信格式，如 "0000001", "1600000"
        """
        if not code:
            return ""
            
        # 去掉空格
        code = code.strip()
        
        # 如果已经是通达信格式，直接返回
        if len(code) == 7 and code[0] in ['0', '1']:
            return code
            
        # 解析代码和后缀
        if '.' in code:
            parts = code.split('.')
            stock_code = parts[0]
            suffix = parts[1].upper()
        else:
            stock_code = code
            suffix = ""
            
        # 根据后缀添加前缀
        if suffix == 'SZ' or (len(stock_code) == 6 and stock_code.startswith('0')):
            # 深市股票以0开头
            return f"0{stock_code}"
        elif suffix == 'SH' or (len(stock_code) == 6 and stock_code.startswith('6')):
            # 沪市股票以1开头
            return f"1{stock_code}"
        elif suffix == 'BJ' or (len(stock_code) == 6 and stock_code.startswith('8')):
            # 北交所股票以2开头
            return f"2{stock_code}"
        else:
            # 默认处理
            return f"0{stock_code}"
    
    def _update_block_config(self, block_code: str, block_name: str) -> bool:
        """
        更新板块配置文件 (blocknew.cfg 和 blocknew.clr)
        
        Args:
            block_code: 板块代码
            block_name: 板块名称
            
        Returns:
            bool: 是否成功
        """
        try:
            config_file = os.path.join(self.block_path, "blocknew.cfg")
            clr_file = os.path.join(self.block_path, "blocknew.clr")
            
            # 读取现有配置
            existing_blocks = []
            if os.path.exists(config_file):
                with open(config_file, 'rb') as f:
                    while True:
                        name_bytes = f.read(64)
                        code_bytes = f.read(64)
                        if not name_bytes or not code_bytes:
                            break
                        name = name_bytes.rstrip(b'\x00').decode('gbk', errors='ignore')
                        code = code_bytes.rstrip(b'\x00').decode('gbk', errors='ignore')
                        if name and code:
                            existing_blocks.append((name, code))
            
            # 检查是否已存在
            for name, code in existing_blocks:
                if code == block_code:
                    logger.info(f"板块已在配置中: {block_name} ({block_code})")
                    return True
            
            # 添加新板块
            existing_blocks.append((block_name, block_code))
            
            # 写入配置文件
            with open(config_file, 'wb') as f:
                for name, code in existing_blocks:
                    name_bytes = name.encode('gbk')
                    name_padded = name_bytes + b'\x00' * (64 - len(name_bytes))
                    f.write(name_padded[:64])
                    
                    code_bytes = code.encode('gbk')
                    code_padded = code_bytes + b'\x00' * (64 - len(code_bytes))
                    f.write(code_padded[:64])
            
            # 写入颜色配置文件
            default_color = bytes([0x00] * 60 + [0xF0, 0xF8, 0x88, 0x00])
            with open(clr_file, 'wb') as f:
                for name, code in existing_blocks:
                    name_bytes = name.encode('gbk')
                    name_padded = name_bytes + b'\x00' * (64 - len(name_bytes))
                    f.write(name_padded[:64])
                    f.write(default_color)
            
            logger.info(f"更新板块配置: {block_name} ({block_code})")
            return True
            
        except Exception as e:
            logger.error(f"更新板块配置失败: {e}")
            return False
    
    def create_block(self, block_code: str, block_name: str) -> bool:
        """
        创建板块文件
        
        Args:
            block_code: 板块代码，如 "3BL260325"
            block_name: 板块名称，如 "3倍量涨停260325"
            
        Returns:
            bool: 是否成功
        """
        try:
            block_file = os.path.join(self.block_path, f"{block_code}.blk")
            
            # 如果文件不存在，创建空文件
            if not os.path.exists(block_file):
                with open(block_file, 'w', encoding='gbk') as f:
                    pass
                logger.info(f"创建板块文件: {block_file}")
            else:
                logger.info(f"板块文件已存在: {block_file}")
            
            # 更新配置文件
            self._update_block_config(block_code, block_name)
                
            return True
        except Exception as e:
            logger.error(f"创建板块文件失败: {e}")
            return False
    
    def write_stocks_to_block(self, block_code: str, stocks: List[str]) -> bool:
        """
        写入股票到板块文件
        
        Args:
            block_code: 板块代码
            stocks: 股票代码列表
            
        Returns:
            bool: 是否成功
        """
        try:
            block_file = os.path.join(self.block_path, f"{block_code}.blk")
            
            # 转换股票代码格式
            converted_stocks = []
            for stock in stocks:
                converted = self._convert_stock_code(stock)
                if converted:
                    converted_stocks.append(converted)
            
            # 写入文件
            with open(block_file, 'w', encoding='gbk') as f:
                for stock in converted_stocks:
                    f.write(f"{stock}\n")
            
            logger.info(f"写入 {len(converted_stocks)} 只股票到板块 {block_code}")
            return True
        except Exception as e:
            logger.error(f"写入板块文件失败: {e}")
            return False
    
    def read_stocks_from_block(self, block_code: str) -> List[str]:
        """
        从板块文件读取股票
        
        Args:
            block_code: 板块代码
            
        Returns:
            List[str]: 股票代码列表（标准格式）
        """
        try:
            block_file = os.path.join(self.block_path, f"{block_code}.blk")
            
            if not os.path.exists(block_file):
                return []
            
            stocks = []
            with open(block_file, 'r', encoding='gbk') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    # 转换回标准格式
                    if line[0] == '0':
                        stocks.append(f"{line[1:]}.SZ")
                    elif line[0] == '1':
                        stocks.append(f"{line[1:]}.SH")
                    elif line[0] == '2':
                        stocks.append(f"{line[1:]}.BJ")
                    else:
                        stocks.append(line[1:])
            
            return stocks
        except Exception as e:
            logger.error(f"读取板块文件失败: {e}")
            return []
    
    def create_block_and_write_stocks(self,
                                      trade_date: date,
                                      stocks: List[str],
                                      block_code: str = None) -> str:
        """
        创建板块并写入股票（使用官方API）

        Args:
            trade_date: 交易日期
            stocks: 股票代码列表
            block_code: 板块代码，默认为 3BL{YYMMDD}

        Returns:
            str: 板块代码
        """
        if block_code is None:
            block_code = f"3BL{trade_date.strftime('%y%m%d')}"

        block_name = f"3倍量涨停{trade_date.strftime('%y%m%d')}"

        try:
            import json
            tq = self._get_tq()

            # 1. 创建板块
            logger.info(f"创建通达信板块: {block_name} ({block_code})")
            result = tq.create_sector(block_code=block_code, block_name=block_name)
            
            # 解析结果 (create_sector 返回 JSON 字符串)
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    logger.error(f"解析创建板块结果失败: {result}")
                    return block_code
            
            if result.get("ErrorId") != "0":
                logger.error(f"创建板块失败: {result.get('Error')}")
                return block_code
            logger.info(f"板块创建成功: {result.get('Msg')}")

            # 2. 添加股票到板块
            if stocks:
                logger.info(f"添加 {len(stocks)} 只股票到板块 {block_code}")
                result = tq.send_user_block(block_code=block_code, stocks=stocks, show=True)
                
                # 解析结果
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except json.JSONDecodeError:
                        logger.error(f"解析添加股票结果失败: {result}")
                        return block_code
                
                if result.get("ErrorId") != "0":
                    logger.error(f"添加股票失败: {result.get('Error')}")
                else:
                    logger.info(f"股票添加成功: {result.get('Msg')}")

            return block_code

        except Exception as e:
            logger.error(f"创建板块并添加股票失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return block_code


# 便捷函数
def create_tdx_block(trade_date: date, stocks: List[str], block_code: str = None) -> str:
    """
    创建通达信板块并写入股票
    
    Args:
        trade_date: 交易日期
        stocks: 股票代码列表
        block_code: 板块代码
        
    Returns:
        str: 板块代码
    """
    service = TdxBlockService()
    return service.create_block_and_write_stocks(trade_date, stocks, block_code)
