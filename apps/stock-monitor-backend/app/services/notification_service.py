#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知服务
负责发送各种渠道的通知（桌面、邮件、日志等）
"""

import os
import subprocess
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.config.logging import get_logger

# 配置日志
logger = get_logger(__name__)

class NotificationService:
    """通知服务"""
    
    def __init__(self):
        self.enabled_channels = {
            'desktop': True,
            'log': True,
            'email': False  # 默认关闭邮件，直到配置完成
        }
    
    async def send_alert(self, title: str, message: str, level: str = 'info', data: Optional[Dict] = None):
        """
        发送告警
        
        Args:
            title: 标题
            message: 内容
            level: 级别 (info, warning, error, critical)
            data: 附加数据
        """
        timestamp = datetime.now().isoformat()
        full_message = f"[{level.upper()}] {title}: {message}"
        
        # 1. 日志通知 (总是发送)
        if self.enabled_channels['log']:
            self._send_log(level, full_message, data)
            
        # 2. 桌面通知 (High/Critical级别 或 显式启用)
        if self.enabled_channels['desktop'] and level in ['warning', 'error', 'critical']:
            self._send_desktop_notification(title, message)
            
        # 3. 邮件通知 (Critical级别)
        if self.enabled_channels['email'] and level in ['critical']:
            # TODO: 实现邮件发送逻辑
            pass
            
    def _send_log(self, level: str, message: str, data: Optional[Dict]):
        """发送日志"""
        log_func = getattr(logger, level, logger.info)
        if data:
            log_func(f"{message} | Data: {data}")
        else:
            log_func(message)
            
    def _send_desktop_notification(self, title: str, message: str):
        """
        发送macOS桌面通知
        使用 osascript
        """
        try:
            # 转义双引号
            safe_title = title.replace('"', '\\"')
            safe_message = message.replace('"', '\\"')
            
            # 构建AppleScript命令
            cmd = f'''display notification "{safe_message}" with title "{safe_title}"'''
            
            subprocess.run(['osascript', '-e', cmd], check=False)
            logger.debug(f"桌面通知已发送: {title}")
        except Exception as e:
            logger.error(f"发送桌面通知失败: {e}")

# 单例实例
notification_service = NotificationService()
