#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同花顺数据字段解码器
处理同花顺原始数据的字段映射和解密
"""

from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime
from loguru import logger


class TonghuashunDataDecoder:
    """同花顺数据解码器"""
    
    # 字段映射配置 - 将数字字段ID映射到有意义的字段名
    FIELD_MAPPING = {
        # 基础价格字段
        "6": "prev_close",         # 昨收价
        "7": "open_price",         # 开盘价
        "8": "high_price",         # 最高价
        "9": "low_price",          # 最低价
        "10": "current_price",     # 当前价格
        
        # 成交量和成交额
        "13": "volume",            # 成交量
        "19": "turnover",          # 成交额
        
        # 涨跌幅相关
        "199112": "change_percent", # 涨跌幅(%)
        "264648": "change_amount",  # 涨跌额
        
        # 其他指标
        "526792": "amplitude",      # 振幅
        "1968584": "turnover_rate", # 换手率
        "2034120": "pe_ratio",      # 市盈率
        "3541450": "market_cap",    # 总市值
        
        # 基础信息
        "name": "stock_name",       # 股票名称
    }
    
    # 字段类型配置
    FIELD_TYPES = {
        "current_price": "decimal",
        "prev_close": "decimal", 
        "open_price": "decimal",
        "high_price": "decimal",
        "low_price": "decimal",
        "volume": "int",
        "turnover": "decimal",
        "change_percent": "decimal",
        "change_amount": "decimal",
        "amplitude": "decimal",
        "turnover_rate": "decimal",
        "pe_ratio": "decimal",
        "market_cap": "decimal",
        "stock_name": "string",
    }
    
    def __init__(self):
        """初始化解码器"""
        self.logger = logger
        
    def decode_stock_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解码单只股票的原始数据
        
        Args:
            raw_data: 原始股票数据，格式如：
                {
                    "6": "9.65",
                    "7": "9.61", 
                    "8": "9.67",
                    "9": "9.40",
                    "10": "9.40",
                    "13": "7199100.00",
                    "19": "68172919.00",
                    "199112": "-2.591",
                    "264648": "-0.250",
                    "526792": "2.798",
                    "1968584": "1.604",
                    "2034120": "",
                    "3541450": "5033981100.000",
                    "name": "赛摩智能"
                }
                
        Returns:
            Dict: 解码后的数据
        """
        try:
            self.logger.info(f"🔧 开始解码单只股票数据")
            self.logger.info(f"📊 原始数据字段数量: {len(raw_data)}")
            self.logger.info(f"📋 原始数据字段: {list(raw_data.keys())[:20]}{'...' if len(raw_data) > 20 else ''}")
            
            decoded_data = {}
            mapped_fields = 0
            unknown_fields = 0
            conversion_errors = 0
            
            # 遍历原始数据进行字段映射
            for field_id, value in raw_data.items():
                # 获取映射的字段名
                field_name = self.FIELD_MAPPING.get(field_id)
                
                if field_name:
                    mapped_fields += 1
                    # 转换数据类型
                    try:
                        converted_value = self._convert_field_value(field_name, value)
                        decoded_data[field_name] = converted_value
                        self.logger.debug(f"✅ 字段映射成功: {field_id} -> {field_name} = {converted_value}")
                    except Exception as e:
                        conversion_errors += 1
                        self.logger.warning(f"⚠️ 字段 {field_name} (ID: {field_id}) 转换失败: {value}, 错误: {e}")
                        decoded_data[field_name] = value
                else:
                    unknown_fields += 1
                    # 未知字段保留原样，但记录日志
                    self.logger.warning(f"❓ 未知字段ID: {field_id}, 值: {value}")
                    decoded_data[f"unknown_field_{field_id}"] = value
            
            # 添加解码时间戳
            decoded_data["decoded_at"] = datetime.now().isoformat()
            
            self.logger.info(f"🎯 解码统计: 映射字段 {mapped_fields}, 未知字段 {unknown_fields}, 转换错误 {conversion_errors}")
            self.logger.info(f"✅ 解码后字段数量: {len(decoded_data)}")
            self.logger.info(f"📋 解码后字段: {list(decoded_data.keys())[:20]}{'...' if len(decoded_data) > 20 else ''}")
            
            return decoded_data
            
        except Exception as e:
            self.logger.error(f"💥 解码股票数据失败: {e}, 原始数据: {raw_data}")
            import traceback
            self.logger.error(f"📋 错误堆栈: {traceback.format_exc()}")
            raise
    
    def decode_batch_data(self, raw_batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        批量解码同花顺原始数据
        
        Args:
            raw_batch_data: 原始批量数据，可能的格式：
                1. 新格式（带hs包装）：
                {
                    "hs": {
                        "300466": {
                            "6": "9.65",
                            "7": "9.61",
                            ...
                            "name": "赛摩智能"
                        }
                    }
                }
                2. 直接格式（无hs包装）：
                {
                    "300466": {
                        "6": "9.65",
                        "7": "9.61",
                        ...
                        "name": "赛摩智能"
                    }
                }
                
        Returns:
            Dict: 解码后的批量数据
        """
        try:
            self.logger.info(f"🔍 开始批量解码同花顺数据")
            self.logger.info(f"🔍 raw_batch_data 类型: {type(raw_batch_data)}")
            
            decoded_batch = {
                "success": True,
                "decoded_stocks": {},
                "total_count": 0,
                "failed_count": 0,
                "errors": [],
                "decoded_at": datetime.now().isoformat()
            }
            
            # 处理不同格式的数据
            if isinstance(raw_batch_data, list):
                # 列表格式：[["000001", "平安银行", "10.50", ...], ["000002", "万科A", "25.30", ...]]
                self.logger.info(f"✅ 检测到列表格式数据，包含 {len(raw_batch_data)} 只股票")
                
                for i, stock_array in enumerate(raw_batch_data):
                    try:
                        if not isinstance(stock_array, list) or len(stock_array) < 2:
                            error_msg = f"股票数据格式错误: {stock_array}"
                            self.logger.error(f"❌ {error_msg}")
                            decoded_batch["failed_count"] += 1
                            decoded_batch["errors"].append(error_msg)
                            continue
                        
                        stock_code = stock_array[0]
                        stock_name = stock_array[1] if len(stock_array) > 1 else ""
                        
                        self.logger.info(f"🔧 解码股票 {i+1}/{len(raw_batch_data)}: {stock_code} ({stock_name})")
                        self.logger.info(f"📊 原始数据长度: {len(stock_array)}")
                        
                        # 将列表格式转换为字典格式进行解码
                        stock_dict = self._convert_array_to_dict(stock_array)
                        self.logger.info(f"📋 转换后的字典: {stock_dict}")
                        
                        # 解码单只股票数据
                        decoded_stock = self.decode_stock_data(stock_dict)
                        self.logger.info(f"✅ 股票 {stock_code} 解码成功")
                        
                        # 添加股票代码
                        decoded_stock["stock_code"] = stock_code
                        
                        # 存储解码结果
                        decoded_batch["decoded_stocks"][stock_code] = decoded_stock
                        decoded_batch["total_count"] += 1
                        
                    except Exception as e:
                        error_msg = f"解码股票 {stock_code if 'stock_code' in locals() else i} 失败: {e}"
                        self.logger.error(f"💥 {error_msg}")
                        import traceback
                        self.logger.error(f"📋 错误堆栈: {traceback.format_exc()}")
                        decoded_batch["failed_count"] += 1
                        decoded_batch["errors"].append(error_msg)
                        
            elif isinstance(raw_batch_data, dict):
                # 字典格式：原有的处理逻辑
                # 获取股票数据部分 - 支持两种格式
                if "hs" in raw_batch_data:
                    # 新格式：有hs包装
                    hs_data = raw_batch_data.get("hs", {})
                    self.logger.info(f"✅ 检测到新格式数据（带hs包装），包含 {len(hs_data)} 只股票")
                else:
                    # 直接格式：无hs包装
                    hs_data = raw_batch_data
                    self.logger.info(f"✅ 检测到直接格式数据（无hs包装），包含 {len(hs_data)} 只股票")
                
                self.logger.info(f"📋 股票代码列表: {list(hs_data.keys())[:10]}{'...' if len(hs_data) > 10 else ''}")
                
                for i, (stock_code, stock_raw_data) in enumerate(hs_data.items()):
                    try:
                        self.logger.info(f"🔧 解码股票 {i+1}/{len(hs_data)}: {stock_code}")
                        self.logger.info(f"📊 原始数据字段: {list(stock_raw_data.keys()) if isinstance(stock_raw_data, dict) else type(stock_raw_data)}")
                        
                        # 解码单只股票数据
                        decoded_stock = self.decode_stock_data(stock_raw_data)
                        self.logger.info(f"✅ 股票 {stock_code} 解码成功")
                        
                        # 添加股票代码
                        decoded_stock["stock_code"] = stock_code
                        
                        # 存储解码结果
                        decoded_batch["decoded_stocks"][stock_code] = decoded_stock
                        decoded_batch["total_count"] += 1
                        
                    except Exception as e:
                        error_msg = f"解码股票 {stock_code} 失败: {e}"
                        self.logger.error(f"💥 {error_msg}")
                        import traceback
                        self.logger.error(f"📋 错误堆栈: {traceback.format_exc()}")
                        decoded_batch["failed_count"] += 1
                        decoded_batch["errors"].append(error_msg)
            else:
                error_msg = f"不支持的数据格式: {type(raw_batch_data)}"
                self.logger.error(f"❌ {error_msg}")
                decoded_batch["success"] = False
                decoded_batch["errors"].append(error_msg)
                return decoded_batch
            
            self.logger.info(f"🎯 批量解码完成: 成功 {decoded_batch['total_count']} 只，失败 {decoded_batch['failed_count']} 只")
            
            return decoded_batch
            
        except Exception as e:
            self.logger.error(f"💥 批量解码失败: {e}")
            import traceback
            self.logger.error(f"📋 错误堆栈: {traceback.format_exc()}")
            return {
                "success": False,
                "decoded_stocks": {},
                "total_count": 0,
                "failed_count": 0,
                "errors": [str(e)],
                "decoded_at": datetime.now().isoformat()
            }
    
    def _convert_field_value(self, field_name: str, value: Any) -> Any:
        """
        根据字段类型转换值
        
        Args:
            field_name: 字段名
            value: 原始值
            
        Returns:
            转换后的值
        """
        try:
            # 处理空值
            if value is None or value == "":
                return None
                
            # 获取字段类型
            field_type = self.FIELD_TYPES.get(field_name, "string")
            
            if field_type == "decimal":
                return Decimal(str(value)) if value else Decimal('0')
            elif field_type == "int":
                return int(float(value)) if value else 0
            elif field_type == "string":
                return str(value)
            else:
                return value
                
        except (ValueError, TypeError) as e:
            self.logger.warning(f"字段 {field_name} 值转换失败: {value} -> {field_type}, 错误: {e}")
            return value
    
    def get_field_mapping(self) -> Dict[str, str]:
        """获取字段映射配置"""
        return self.FIELD_MAPPING.copy()
    
    def add_field_mapping(self, field_id: str, field_name: str, field_type: str = "string") -> None:
        """
        添加新的字段映射
        
        Args:
            field_id: 原始字段ID
            field_name: 映射的字段名
            field_type: 字段类型
        """
        self.FIELD_MAPPING[field_id] = field_name
        self.FIELD_TYPES[field_name] = field_type
        self.logger.info(f"添加字段映射: {field_id} -> {field_name} ({field_type})")
    
    def _convert_array_to_dict(self, stock_array: List[Any]) -> Dict[str, Any]:
        """
        将列表格式的股票数据转换为字典格式
        
        Args:
            stock_array: 列表格式的股票数据，如 ["000001", "平安银行", "10.50", "10.45", ...]
            
        Returns:
            Dict: 字典格式的股票数据
        """
        try:
            # 基本的字段映射（根据位置）
            # 这是根据同花顺数据的常见格式推测的
            stock_dict = {}
            
            if len(stock_array) > 0:
                stock_dict["stock_code"] = stock_array[0]  # 股票代码
            if len(stock_array) > 1:
                stock_dict["name"] = stock_array[1]  # 股票名称
            if len(stock_array) > 2:
                stock_dict["10"] = stock_array[2]  # 当前价格
            if len(stock_array) > 3:
                stock_dict["6"] = stock_array[3]   # 昨收价
            if len(stock_array) > 4:
                stock_dict["8"] = stock_array[4]   # 最高价
            if len(stock_array) > 5:
                stock_dict["9"] = stock_array[5]   # 最低价
            if len(stock_array) > 6:
                stock_dict["13"] = stock_array[6]  # 成交量
            if len(stock_array) > 7:
                stock_dict["19"] = stock_array[7]  # 成交额
                
            # 如果有更多字段，按顺序映射到其他字段ID
            # 这里可以根据实际数据格式进行调整
            
            self.logger.info(f"🔄 数组转字典: {len(stock_array)} 个字段 -> {len(stock_dict)} 个映射字段")
            return stock_dict
            
        except Exception as e:
            self.logger.error(f"❌ 数组转字典失败: {e}")
            return {"name": "转换失败"}

    def validate_decoded_data(self, decoded_data: Dict[str, Any]) -> bool:
        """
        验证解码后的数据完整性
        
        Args:
            decoded_data: 解码后的数据
            
        Returns:
            bool: 验证结果
        """
        try:
            # 检查必要字段
            required_fields = ["stock_code", "stock_name", "current_price"]
            
            for field in required_fields:
                if field not in decoded_data or decoded_data[field] is None:
                    self.logger.warning(f"缺少必要字段: {field}")
                    return False
            
            # 检查价格字段的合理性
            current_price = decoded_data.get("current_price")
            if current_price and current_price <= 0:
                self.logger.warning(f"当前价格不合理: {current_price}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"验证解码数据失败: {e}")
            return False


# 创建全局解码器实例
tonghuashun_decoder = TonghuashunDataDecoder()


def decode_tonghuashun_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    便捷函数：解码同花顺原始数据
    
    Args:
        raw_data: 原始数据
        
    Returns:
        解码后的数据
    """
    return tonghuashun_decoder.decode_batch_data(raw_data)


if __name__ == "__main__":
    # 测试解码器
    test_data = {
        "hs": {
            "300466": {
                "6": "9.65",
                "7": "9.61", 
                "8": "9.67",
                "9": "9.40",
                "10": "9.40",
                "13": "7199100.00",
                "19": "68172919.00",
                "199112": "-2.591",
                "264648": "-0.250",
                "526792": "2.798",
                "1968584": "1.604",
                "2034120": "",
                "3541450": "5033981100.000",
                "name": "赛摩智能"
            }
        }
    }
    
    decoder = TonghuashunDataDecoder()
    result = decoder.decode_batch_data(test_data)
    
    print("解码结果:")
    print(f"成功: {result['success']}")
    print(f"总数: {result['total_count']}")
    print(f"失败: {result['failed_count']}")
    
    if result['decoded_stocks']:
        for stock_code, stock_data in result['decoded_stocks'].items():
            print(f"\n股票 {stock_code}:")
            for field, value in stock_data.items():
                print(f"  {field}: {value}")