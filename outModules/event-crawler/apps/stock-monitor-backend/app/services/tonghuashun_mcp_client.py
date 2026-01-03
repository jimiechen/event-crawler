#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同花顺MCP客户端封装
提供Chrome MCP服务的调用接口，用于抓取同花顺股票数据
"""

import json
import re
import hashlib
import requests
import aiohttp
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
from urllib.parse import urljoin, urlparse

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TongHuaShunMCPClient:
    """
    同花顺MCP客户端
    封装Chrome MCP服务调用，提供同花顺数据抓取功能
    基于成功的SimpleMCPClient实现
    """
    
    def __init__(self, mcp_server_url: str = "http://localhost:56889/mcp", session_id: str = None):
        """
        初始化MCP客户端
        
        Args:
            mcp_server_url: MCP服务器地址
            session_id: MCP会话ID，如果为None则自动生成
        """
        self.mcp_server_url = mcp_server_url
        self.session_id = session_id or self._generate_session_id()
        self.request_id = 1
        self.session = requests.Session()
        self.connected = False
        
        # 设置默认超时
        self.session.timeout = 30
        
        # 同花顺相关配置
        self.base_urls = {
            'user_stocks': 'https://t.10jqka.com.cn/newcircle/user/userPersonal/?from=finance&tab=zx###',
            'stock_api': 'https://d.10jqka.com.cn/multimarketreal/hs/',
            'stock_detail': 'https://stockpage.10jqka.com.cn/'
        }
        
        # 数据解析正则表达式
        self.patterns = {
            'stock_code': r'"([0-9]{6})"',
            'stock_name': r'"([^"]+)"',
            'current_price': r'"([0-9]+\.?[0-9]*)"',
            'change_percent': r'"([-+]?[0-9]+\.?[0-9]*)"',
            'volume': r'"([0-9]+)"',
            'turnover': r'"([0-9]+\.?[0-9]*)"'
        }
        
        logger.info(f"TongHuaShunMCPClient initialized with session_id: {self.session_id}")
    
    def _generate_session_id(self) -> str:
        """
        生成会话ID
        
        Returns:
            str: 会话ID
        """
        timestamp = str(int(datetime.now().timestamp() * 1000))
        return f"ths_session_{timestamp}"
    
    async def chrome_get_web_content(self, url: str, wait_time: int = 5000, timeout: int = 30000, 
                                   html_content: bool = True, text_content: bool = False) -> Dict[str, Any]:
        """
        调用Chrome MCP的chrome_get_web_content工具
        
        Args:
            url: 目标URL
            wait_time: 等待时间（毫秒）
            timeout: 超时时间（毫秒）
            html_content: 是否获取HTML内容
            text_content: 是否获取文本内容
            
        Returns:
            Dict: 工具调用结果
            
        Raises:
            Exception: 调用失败时抛出异常
        """
        logger.info(f"调用chrome_get_web_content: {url}")
        
        tool_call_request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {
                "name": "chrome_get_web_content",
                "arguments": {
                    "url": url,
                    "htmlContent": html_content,
                    "textContent": text_content,
                    "wait_time": wait_time,
                    "timeout": timeout
                }
            }
        }
        
        self.request_id += 1
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream',
            'User-Agent': 'TongHuaShun-Monitor/1.0',
            'MCP-Session-ID': self.session_id
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.mcp_server_url,
                    json=tool_call_request,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout/1000 + 10)
                ) as response:
                    
                    logger.info(f"响应状态: {response.status}")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"HTTP错误 {response.status}: {error_text}")
                        raise Exception(f"HTTP错误 {response.status}: {error_text}")
                    
                    response_text = await response.text()
                    logger.info(f"原始响应数据长度: {len(response_text)}")
                    
                    # 解析响应
                    tool_result = await self._parse_mcp_response(response_text)
                    
                    if tool_result:
                        logger.info("成功获取页面内容")
                        content_length = len(tool_result.get('content', '')) if tool_result.get('content') else 0
                        logger.info(f"内容长度: {content_length}")
                        return tool_result
                    else:
                        raise Exception("工具执行错误或响应格式异常")
                        
        except Exception as error:
            logger.error(f"获取页面内容失败: {str(error)}")
            raise
    
    async def _parse_mcp_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        解析MCP响应数据
        
        Args:
            response_text: 响应文本
            
        Returns:
            Optional[Dict]: 解析后的结果
        """
        tool_result = None
        
        if 'event: message' in response_text:
            # 解析SSE格式
            logger.info("检测到SSE格式响应，开始解析...")
            lines = response_text.split('\n')
            
            for line in lines:
                if line.startswith('data: '):
                    try:
                        json_data = json.loads(line[6:])
                        if json_data.get('result') and not json_data['result'].get('isError'):
                            tool_result = json_data['result']
                            logger.info("找到有效的SSE结果")
                            
                            # 检查并解析content字段
                            if tool_result.get('content') and isinstance(tool_result['content'], list):
                                for content_item in tool_result['content']:
                                    if content_item.get('type') == 'text' and content_item.get('text'):
                                        try:
                                            # 尝试解析text字段中的JSON
                                            text_data = json.loads(content_item['text'])
                                            if text_data.get('htmlContent'):
                                                tool_result['content'] = text_data['htmlContent']
                                                logger.info("成功提取htmlContent字符串")
                                                break
                                        except json.JSONDecodeError:
                                            # 如果不是JSON，直接使用text内容
                                            tool_result['content'] = content_item['text']
                                            logger.info("使用text内容作为htmlContent")
                                            break
                            break
                    except json.JSONDecodeError as e:
                        logger.warning(f"SSE行解析失败，继续尝试下一行: {e}")
                        continue
        else:
            # 尝试直接解析JSON
            logger.info("尝试直接解析JSON格式响应...")
            try:
                response_data = json.loads(response_text)
                if response_data.get('result') and not response_data['result'].get('isError'):
                    tool_result = response_data['result']
                    logger.info("找到有效的JSON结果")
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                raise Exception(f"JSON解析失败: {e}")
        
        return tool_result
    
    async def get_user_stock_list(self) -> Dict[str, Any]:
        """
        获取用户自选股列表页面
        
        Returns:
            Dict: 页面内容和解析结果
        """
        logger.info("获取用户自选股列表")
        
        try:
            result = await self.chrome_get_web_content(
                url=self.base_urls['user_stocks'],
                wait_time=8000,  # 增加等待时间以确保页面完全加载
                timeout=45000
            )
            
            html_content = result.get('content', '')
            
            # 解析页面中的股票信息
            stocks = self._parse_stock_list_from_html(html_content)
            
            return {
                'success': True,
                'html_content': html_content,
                'stocks': stocks,
                'total_count': len(stocks)
            }
            
        except Exception as e:
            logger.error(f"获取用户自选股列表失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'html_content': '',
                'stocks': [],
                'total_count': 0
            }
    
    def _parse_stock_list_from_html(self, html_content: str) -> List[Dict[str, Any]]:
        """
        从HTML内容中解析股票列表
        
        Args:
            html_content: HTML内容
            
        Returns:
            List[Dict]: 股票信息列表
        """
        stocks = []
        
        try:
            # 查找股票代码模式
            stock_code_pattern = r'data-code="([0-9]{6})"'
            stock_codes = re.findall(stock_code_pattern, html_content)
            
            # 查找股票名称模式
            stock_name_pattern = r'<span[^>]*class="[^"]*name[^"]*"[^>]*>([^<]+)</span>'
            stock_names = re.findall(stock_name_pattern, html_content)
            
            # 组合股票信息
            for i, code in enumerate(stock_codes):
                stock_info = {
                    'code': code,
                    'name': stock_names[i] if i < len(stock_names) else f'股票{code}',
                    'market': 'SH' if code.startswith(('60', '68', '90')) else 'SZ'
                }
                stocks.append(stock_info)
                
            logger.info(f"从HTML中解析出 {len(stocks)} 只股票")
            
        except Exception as e:
            logger.error(f"解析股票列表失败: {e}")
        
        return stocks
    
    async def get_stock_realtime_data(self, stock_codes: List[str]) -> Dict[str, Any]:
        """
        获取股票实时数据
        
        Args:
            stock_codes: 股票代码列表
            
        Returns:
            Dict: 实时数据结果
        """
        logger.info(f"获取股票实时数据: {stock_codes}")
        
        # 构建API URL
        codes_param = ','.join([f'{code}.SH' if code.startswith(('60', '68', '90')) else f'{code}.SZ' for code in stock_codes])
        api_url = f"{self.base_urls['stock_api']}?codes={codes_param}&_={int(datetime.now().timestamp() * 1000)}"
        
        try:
            result = await self.chrome_get_web_content(
                url=api_url,
                wait_time=3000,
                timeout=20000,
                html_content=False,
                text_content=True
            )
            
            content = result.get('content', '')
            
            # 解析JSONP响应
            stock_data = self._parse_jsonp_response(content)
            
            return {
                'success': True,
                'raw_content': content,
                'stock_data': stock_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取股票实时数据失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'raw_content': '',
                'stock_data': [],
                'timestamp': datetime.now().isoformat()
            }
    
    def _parse_jsonp_response(self, content: str) -> List[Dict[str, Any]]:
        """
        解析JSONP响应数据
        
        Args:
            content: JSONP响应内容
            
        Returns:
            List[Dict]: 解析后的股票数据
        """
        stock_data = []
        
        try:
            # 移除JSONP包装，提取JSON数据
            # 典型格式: callback({"data": [...]})
            json_match = re.search(r'\((.+)\)$', content.strip())
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)
                
                # 提取股票数据
                if 'data' in data and isinstance(data['data'], list):
                    for item in data['data']:
                        if isinstance(item, list) and len(item) >= 6:
                            stock_info = {
                                'code': item[0] if len(item) > 0 else '',
                                'name': item[1] if len(item) > 1 else '',
                                'current_price': float(item[2]) if len(item) > 2 and item[2] else 0.0,
                                'change_amount': float(item[3]) if len(item) > 3 and item[3] else 0.0,
                                'change_percent': float(item[4]) if len(item) > 4 and item[4] else 0.0,
                                'volume': int(item[5]) if len(item) > 5 and item[5] else 0,
                                'turnover': float(item[6]) if len(item) > 6 and item[6] else 0.0,
                                'timestamp': datetime.now().isoformat()
                            }
                            stock_data.append(stock_info)
                            
            logger.info(f"解析出 {len(stock_data)} 条股票数据")
            
        except Exception as e:
            logger.error(f"解析JSONP响应失败: {e}")
            logger.debug(f"原始内容: {content[:500]}...")
        
        return stock_data
    
    def generate_data_hash(self, data: Union[str, Dict, List]) -> str:
        """
        生成数据的SHA256哈希值，用于去重
        
        Args:
            data: 要计算哈希的数据
            
        Returns:
            str: SHA256哈希值
        """
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        else:
            data_str = str(data)
        
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()
    
    async def monitor_stock_data(self, stock_codes: List[str], interval: int = 30) -> None:
        """
        监控股票数据变化
        
        Args:
            stock_codes: 要监控的股票代码列表
            interval: 监控间隔（秒）
        """
        logger.info(f"开始监控股票数据: {stock_codes}, 间隔: {interval}秒")
        
        while True:
            try:
                # 获取实时数据
                result = await self.get_stock_realtime_data(stock_codes)
                
                if result['success']:
                    # 处理数据（这里可以添加数据存储逻辑）
                    logger.info(f"获取到 {len(result['stock_data'])} 条股票数据")
                    
                    # 打印部分数据用于调试
                    for stock in result['stock_data'][:3]:  # 只打印前3条
                        logger.info(f"股票: {stock['name']}({stock['code']}) 价格: {stock['current_price']} 涨跌: {stock['change_percent']}%")
                else:
                    logger.error(f"获取股票数据失败: {result['error']}")
                
                # 等待下一次监控
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("监控被用户中断")
                break
            except Exception as e:
                logger.error(f"监控过程中发生错误: {e}")
                await asyncio.sleep(interval)

# 使用示例
if __name__ == "__main__":
    async def main():
        # 创建MCP客户端
        client = TongHuaShunMCPClient()
        
        try:
            # 获取用户自选股列表
            stock_list_result = await client.get_user_stock_list()
            print(f"获取自选股结果: {stock_list_result['success']}")
            print(f"股票数量: {stock_list_result['total_count']}")
            
            if stock_list_result['stocks']:
                # 获取前5只股票的实时数据
                codes = [stock['code'] for stock in stock_list_result['stocks'][:5]]
                realtime_result = await client.get_stock_realtime_data(codes)
                print(f"获取实时数据结果: {realtime_result['success']}")
                
                if realtime_result['success']:
                    for stock in realtime_result['stock_data']:
                        print(f"{stock['name']}({stock['code']}): {stock['current_price']} ({stock['change_percent']}%)")
        
        except Exception as e:
            print(f"测试失败: {e}")
    
    # 运行测试
    asyncio.run(main())