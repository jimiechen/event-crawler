#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试MCP连接
"""

import asyncio
import aiohttp
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mcp_connection():
    """测试MCP服务器连接"""
    mcp_server_url = "http://localhost:56889/mcp"
    
    # 简单的ping请求
    ping_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "ping"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            logger.info(f"连接到MCP服务器: {mcp_server_url}")
            
            async with session.post(
                mcp_server_url,
                json=ping_request,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                logger.info(f"响应状态: {response.status}")
                logger.info(f"响应头: {dict(response.headers)}")
                
                response_text = await response.text()
                logger.info(f"响应内容: {response_text}")
                
                if response.status == 200:
                    logger.info("✓ MCP服务器连接正常")
                    return True
                else:
                    logger.error(f"✗ MCP服务器响应错误: {response.status}")
                    return False
                    
    except Exception as e:
        logger.error(f"✗ MCP连接失败: {e}")
        return False

async def test_tools_list():
    """测试获取工具列表"""
    mcp_server_url = "http://localhost:56889/mcp"
    
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            logger.info("获取工具列表...")
            
            async with session.post(
                mcp_server_url,
                json=tools_request,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                logger.info(f"响应状态: {response.status}")
                
                response_text = await response.text()
                logger.info(f"工具列表响应: {response_text}")
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        tools = data.get('result', {}).get('tools', [])
                        logger.info(f"✓ 可用工具数量: {len(tools)}")
                        for tool in tools:
                            logger.info(f"  - {tool.get('name', 'Unknown')}")
                        return True
                    except json.JSONDecodeError as e:
                        logger.error(f"✗ 解析工具列表失败: {e}")
                        return False
                else:
                    logger.error(f"✗ 获取工具列表失败: {response.status}")
                    return False
                    
    except Exception as e:
        logger.error(f"✗ 获取工具列表异常: {e}")
        return False

async def main():
    """主测试函数"""
    logger.info("开始MCP连接诊断...")
    logger.info("=" * 50)
    
    # 测试基本连接
    connection_ok = await test_mcp_connection()
    
    if connection_ok:
        # 测试工具列表
        tools_ok = await test_tools_list()
        
        if tools_ok:
            logger.info("✓ MCP服务器功能正常")
        else:
            logger.error("✗ MCP工具列表获取失败")
    else:
        logger.error("✗ MCP服务器连接失败")
    
    logger.info("=" * 50)
    logger.info("MCP连接诊断完成")

if __name__ == "__main__":
    asyncio.run(main())