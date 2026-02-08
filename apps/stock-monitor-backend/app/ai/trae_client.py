#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trae CLI AI 客户端
用于调用 Trae CLI 进行图像识别分析
"""

import json
import base64
import asyncio
import tempfile
import os
from typing import Dict, Any, Optional
from loguru import logger


class TraeAIClient:
    """Trae AI 客户端"""
    
    def __init__(self, model: str = "kimi-k2.5"):
        self.model = model
        self.timeout = 60  # 超时时间60秒
    
    async def analyze_image(
        self, 
        image_base64: str, 
        prompt: str,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用 Trae CLI 分析图片
        
        Args:
            image_base64: Base64编码的图片数据
            prompt: AI提示词
            model: 模型名称，默认 kimi-k2.5
            
        Returns:
            AI分析结果字典
        """
        use_model = model or self.model
        
        try:
            # 将base64保存为临时文件
            image_path = await self._save_base64_to_temp(image_base64)
            
            # 构建 trae chat 命令
            # 格式: trae chat -a <image_path> "<prompt>"
            cmd = [
                "trae", "chat",
                "-a", image_path,
                prompt
            ]
            
            logger.info(f"调用 Trae CLI: model={use_model}, image={image_path}")
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # 等待完成，带超时
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                logger.error("Trae CLI 调用超时")
                raise TimeoutError("AI分析超时")
            
            # 检查错误
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "未知错误"
                logger.error(f"Trae CLI 错误: {error_msg}")
                raise RuntimeError(f"AI调用失败: {error_msg}")
            
            # 解析输出
            output = stdout.decode('utf-8', errors='ignore')
            logger.debug(f"Trae CLI 输出: {output[:500]}...")
            
            # 从输出中提取JSON
            result = self._extract_json_from_output(output)
            
            # 清理临时文件
            await self._cleanup_temp_file(image_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Trae AI 分析失败: {e}")
            # 返回默认结果
            return self._get_default_result()
    
    async def _save_base64_to_temp(self, image_base64: str) -> str:
        """将base64图片保存为临时文件"""
        # 移除可能的data URI前缀
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        # 解码
        image_data = base64.b64decode(image_base64)
        
        # 创建临时文件
        fd, path = tempfile.mkstemp(suffix='.png')
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(image_data)
            return path
        except Exception as e:
            os.close(fd)
            raise e
    
    async def _cleanup_temp_file(self, path: str):
        """清理临时文件"""
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")
    
    def _extract_json_from_output(self, output: str) -> Dict[str, Any]:
        """从Trae CLI输出中提取JSON"""
        try:
            # 尝试直接解析整个输出
            return json.loads(output)
        except json.JSONDecodeError:
            pass
        
        # 尝试从文本中提取JSON块
        import re
        
        # 查找 ```json ... ``` 格式
        json_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_pattern, output, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # 查找 { ... } 格式
        json_pattern = r'\{[\s\S]*?"stock_code"[\s\S]*?\}'
        matches = re.findall(json_pattern, output)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # 如果都失败了，返回解析后的文本
        logger.warning("无法从输出中提取JSON，返回原始文本")
        return {
            "raw_output": output,
            "parse_error": True
        }
    
    def _get_default_result(self) -> Dict[str, Any]:
        """获取默认结果"""
        return {
            "stock_code": "",
            "stock_name": "",
            "price": 0,
            "change_percent": 0,
            "sanlong": {
                "trend_alert": 0,
                "volume_alert": 0,
                "mid_alert": 0,
                "short_alert": 0,
                "alert_count": 0,
                "all_red": False
            },
            "kd_signals": {
                "has_k_signal_today": False,
                "has_d_signal_today": False,
                "k_signal_count": 0,
                "d_signal_count": 0
            },
            "pattern": "unknown",
            "pattern_confidence": 0,
            "analysis_text": "AI分析失败，返回默认结果"
        }


# 全局客户端实例
trae_client = TraeAIClient()
