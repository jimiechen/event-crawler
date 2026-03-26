#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书数据同步服务
TDD Step 2: 实现代码 (绿)
"""

import asyncio
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from loguru import logger


class FeishuSyncService:
    """
    飞书数据同步服务
    
    功能:
    1. 同步选股结果到飞书多维表格
    2. 同步截图到飞书文档
    3. 批量同步
    4. 数据格式转换
    5. 重试机制
    """
    
    # 默认配置
    DEFAULT_BATCH_SIZE = 50
    DEFAULT_MAX_RETRIES = 3
    
    def __init__(self, 
                 feishu_client=None,
                 batch_size: int = None,
                 max_retries: int = None):
        """
        初始化飞书同步服务
        
        Args:
            feishu_client: 飞书客户端实例
            batch_size: 批量同步大小
            max_retries: 最大重试次数
        """
        self.feishu_client = feishu_client
        self.batch_size = batch_size or self.DEFAULT_BATCH_SIZE
        self.max_retries = max_retries or self.DEFAULT_MAX_RETRIES
    
    async def sync_selection_to_feishu(self, 
                                       selection_data: List[Dict[str, Any]],
                                       batch_size: int = None) -> Dict[str, Any]:
        """
        同步选股结果到飞书多维表格
        
        Args:
            selection_data: 选股数据列表
            batch_size: 批量大小
            
        Returns:
            Dict: {
                "status": "success"|"partial"|"failed",
                "synced_count": int,
                "failed_count": int,
                "sync_time": datetime
            }
        """
        if not selection_data:
            return {
                "status": "success",
                "synced_count": 0,
                "failed_count": 0,
                "sync_time": datetime.now()
            }
        
        batch_size = batch_size or self.batch_size
        
        try:
            if self.feishu_client is None:
                logger.error("飞书客户端未初始化")
                return {
                    "status": "failed",
                    "synced_count": 0,
                    "failed_count": len(selection_data),
                    "sync_time": datetime.now()
                }
            
            synced_count = 0
            failed_count = 0
            
            # 分批处理
            for i in range(0, len(selection_data), batch_size):
                batch = selection_data[i:i + batch_size]
                
                # 转换数据格式
                records = [self.transform_selection_data(item) for item in batch]
                
                # 同步数据
                result = await self._sync_batch_with_retry(records)
                
                if result["status"] == "success":
                    synced_count += len(batch)
                else:
                    failed_count += len(batch)
            
            # 确定整体状态
            if failed_count == 0:
                status = "success"
            elif synced_count > 0:
                status = "partial"
            else:
                status = "failed"
            
            return {
                "status": status,
                "synced_count": synced_count,
                "failed_count": failed_count,
                "sync_time": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"同步选股结果到飞书失败: {e}")
            return {
                "status": "failed",
                "synced_count": 0,
                "failed_count": len(selection_data),
                "sync_time": datetime.now()
            }
    
    async def _sync_batch_with_retry(self, records: List[Dict]) -> Dict[str, Any]:
        """
        批量同步数据（带重试）
        
        Args:
            records: 记录列表
            
        Returns:
            Dict: 同步结果
        """
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                result = self.feishu_client.add_records(records)
                
                if result.get("status") == "success":
                    return result
                
                last_error = result.get("error")
                retries += 1
                
                if retries < self.max_retries:
                    logger.warning(f"同步失败，{retries}秒后重试 ({retries}/{self.max_retries})")
                    await asyncio.sleep(retries)
                    
            except Exception as e:
                last_error = str(e)
                retries += 1
                
                if retries < self.max_retries:
                    logger.warning(f"同步异常，{retries}秒后重试 ({retries}/{self.max_retries}): {e}")
                    await asyncio.sleep(retries)
        
        logger.error(f"同步失败，已达到最大重试次数 ({self.max_retries})")
        return {
            "status": "failed",
            "error": last_error
        }
    
    async def sync_screenshots_to_feishu(self, 
                                          screenshot_paths: List[str]) -> Dict[str, Any]:
        """
        同步截图到飞书
        
        Args:
            screenshot_paths: 截图文件路径列表
            
        Returns:
            Dict: {
                "status": "success"|"partial"|"failed",
                "uploaded_count": int,
                "failed_count": int
            }
        """
        if not screenshot_paths:
            return {
                "status": "success",
                "uploaded_count": 0,
                "failed_count": 0
            }
        
        try:
            if self.feishu_client is None:
                logger.error("飞书客户端未初始化")
                return {
                    "status": "failed",
                    "uploaded_count": 0,
                    "failed_count": len(screenshot_paths)
                }
            
            uploaded_count = 0
            failed_count = 0
            
            for path in screenshot_paths:
                try:
                    result = self.feishu_client.upload_file(path)
                    
                    if result.get("status") == "success":
                        uploaded_count += 1
                        logger.info(f"截图上传成功: {path}")
                    else:
                        failed_count += 1
                        logger.error(f"截图上传失败: {path}")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"截图上传异常: {path}, 错误: {e}")
            
            # 确定整体状态
            if failed_count == 0:
                status = "success"
            elif uploaded_count > 0:
                status = "partial"
            else:
                status = "failed"
            
            return {
                "status": status,
                "uploaded_count": uploaded_count,
                "failed_count": failed_count
            }
            
        except Exception as e:
            logger.error(f"同步截图到飞书失败: {e}")
            return {
                "status": "failed",
                "uploaded_count": 0,
                "failed_count": len(screenshot_paths)
            }
    
    async def sync_screenshots_with_metadata(self, 
                                              screenshots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        同步截图并附带元数据
        
        Args:
            screenshots: 截图数据列表，包含 path, stock_code, ai_analysis 等
            
        Returns:
            Dict: 同步结果
        """
        if not screenshots:
            return {
                "status": "success",
                "uploaded_count": 0,
                "failed_count": 0
            }
        
        try:
            uploaded_count = 0
            failed_count = 0
            
            for screenshot in screenshots:
                try:
                    path = screenshot.get("path")
                    
                    # 上传文件
                    result = self.feishu_client.upload_file(path)
                    
                    if result.get("status") == "success":
                        uploaded_count += 1
                        logger.info(f"截图上传成功: {path}")
                        
                        # TODO: 可以在这里添加元数据关联
                    else:
                        failed_count += 1
                        logger.error(f"截图上传失败: {path}")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"截图上传异常: {e}")
            
            # 确定整体状态
            if failed_count == 0:
                status = "success"
            elif uploaded_count > 0:
                status = "partial"
            else:
                status = "failed"
            
            return {
                "status": status,
                "uploaded_count": uploaded_count,
                "failed_count": failed_count
            }
            
        except Exception as e:
            logger.error(f"同步截图到飞书失败: {e}")
            return {
                "status": "failed",
                "uploaded_count": 0,
                "failed_count": len(screenshots)
            }
    
    def validate_selection_data(self, data: Dict[str, Any]) -> bool:
        """
        验证选股数据
        
        Args:
            data: 选股数据
            
        Returns:
            bool: 是否有效
        """
        required_fields = ["stock_code"]
        
        for field in required_fields:
            if field not in data or data[field] is None:
                return False
        
        return True
    
    def transform_selection_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换选股数据格式
        
        Args:
            data: 原始选股数据
            
        Returns:
            Dict: 飞书多维表格格式
        """
        fields = {
            "股票代码": data.get("stock_code", ""),
            "股票名称": data.get("stock_name", ""),
            "选股策略": data.get("strategy", ""),
            "收盘价": data.get("close_price", 0),
            "日期": data.get("date", date.today()).isoformat() if isinstance(data.get("date"), date) else str(data.get("date", "")),
        }
        
        # 根据策略添加特定字段
        if data.get("strategy") == "3x_volume":
            fields["量比"] = data.get("volume_ratio", 0)
        elif data.get("strategy") == "limit_up":
            fields["涨跌幅"] = data.get("change_percent", 0)
        
        return {"fields": fields}
    
    def transform_screenshot_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换截图数据格式
        
        Args:
            data: 原始截图数据
            
        Returns:
            Dict: 飞书文档格式
        """
        stock_code = data.get("stock_code", "")
        ai_analysis = data.get("ai_analysis", {})
        
        return {
            "title": f"{stock_code} 截图分析",
            "content": {
                "股票代码": stock_code,
                "AI分析": ai_analysis
            }
        }
