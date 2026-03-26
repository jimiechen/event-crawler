#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书通知服务
TDD Step 2: 实现代码 (绿)
"""

import asyncio
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from loguru import logger


class FeishuNotificationService:
    """
    飞书通知服务
    
    功能:
    1. 发送群消息 (支持Markdown格式)
    2. 创建任务卡片
    3. 发送告警通知
    4. 发送每日报告
    5. 重试机制
    """
    
    # 默认配置
    DEFAULT_CHAT_ID = "oc_xxx"  # 默认群聊ID
    DEFAULT_OPERATOR_IDS = ["ou_xxx"]  # 默认操作员ID列表
    DEFAULT_MAX_RETRIES = 3  # 默认最大重试次数
    
    def __init__(self, 
                 feishu_client=None,
                 default_chat_id: str = None,
                 operator_ids: List[str] = None,
                 max_retries: int = None):
        """
        初始化飞书通知服务
        
        Args:
            feishu_client: 飞书客户端实例
            default_chat_id: 默认群聊ID
            operator_ids: 操作员ID列表
            max_retries: 最大重试次数
        """
        self.feishu_client = feishu_client
        self.default_chat_id = default_chat_id or self.DEFAULT_CHAT_ID
        self.operator_ids = operator_ids or self.DEFAULT_OPERATOR_IDS
        self.max_retries = max_retries or self.DEFAULT_MAX_RETRIES
    
    async def send_group_message(self,
                                  chat_id: str,
                                  message: str,
                                  at_users: List[str] = None) -> Dict[str, Any]:
        """
        发送群消息
        
        Args:
            chat_id: 群聊ID
            message: 消息内容 (支持Markdown)
            at_users: @用户列表
            
        Returns:
            Dict: {"status": "success"|"failed", "message_id": str, "error": str}
        """
        try:
            if self.feishu_client is None:
                logger.error("飞书客户端未初始化")
                return {"status": "failed", "error": "飞书客户端未初始化"}
            
            # 调用飞书API发送消息
            result = self.feishu_client.send_group_message(
                chat_id=chat_id,
                message=message,
                at_users=at_users or []
            )
            
            if result.get("status") == "success":
                logger.info(f"群消息发送成功: {result.get('message_id')}")
            else:
                logger.error(f"群消息发送失败: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"发送群消息时出错: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def create_task_card(self,
                                title: str,
                                content: str,
                                assignee: str = None,
                                deadline: str = None) -> Dict[str, Any]:
        """
        创建任务卡片
        
        Args:
            title: 任务标题
            content: 任务内容
            assignee: 负责人ID
            deadline: 截止时间
            
        Returns:
            Dict: {"status": "success"|"failed", "task_card_id": str, "error": str}
        """
        try:
            if self.feishu_client is None:
                logger.error("飞书客户端未初始化")
                return {"status": "failed", "error": "飞书客户端未初始化"}
            
            # 调用飞书API创建任务卡片
            result = self.feishu_client.create_task_card(
                title=title,
                content=content,
                assignee=assignee,
                deadline=deadline
            )
            
            if result.get("status") == "success":
                logger.info(f"任务卡片创建成功: {result.get('task_card_id')}")
            else:
                logger.error(f"任务卡片创建失败: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"创建任务卡片时出错: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def notify_operator(self,
                               sync_result: Dict[str, Any],
                               chat_id: str = None,
                               at_users: List[str] = None,
                               create_task_card: bool = True) -> Dict[str, Any]:
        """
        通知操作员
        
        Args:
            sync_result: 数据同步检查结果
            chat_id: 群聊ID
            at_users: @用户列表
            create_task_card: 是否创建任务卡片
            
        Returns:
            Dict: {"status": "success"|"failed", "message_id": str, "task_card_id": str}
        """
        chat_id = chat_id or self.default_chat_id
        at_users = at_users or self.operator_ids
        
        # 构建告警消息
        message = self._build_alert_message(sync_result)
        
        # 发送群消息
        message_result = await self.send_group_message(
            chat_id=chat_id,
            message=message,
            at_users=at_users
        )
        
        # 创建任务卡片
        task_card_result = None
        if create_task_card and sync_result.get("action_required"):
            task_card_result = await self.create_task_card(
                title=f"盘后数据同步异常 - {datetime.now().strftime('%Y-%m-%d')}",
                content=sync_result.get("message", "数据同步失败，需要人工处理"),
                assignee=at_users[0] if at_users else None,
                deadline=(datetime.now().replace(hour=16, minute=0, second=0)).strftime("%Y-%m-%d %H:%M:%S")
            )
        
        return {
            "status": message_result.get("status"),
            "message_id": message_result.get("message_id"),
            "task_card_id": task_card_result.get("task_card_id") if task_card_result else None
        }
    
    def _build_alert_message(self, sync_result: Dict[str, Any]) -> str:
        """
        构建告警消息
        
        Args:
            sync_result: 数据同步检查结果
            
        Returns:
            str: Markdown格式的告警消息
        """
        checks = sync_result.get("checks", {})
        
        message = f"""
## ⚠️ 盘后数据同步异常

**检查时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**检查结果**:
- 客户端在线: {'✅' if checks.get('client_online') else '❌'}
- 数据完整: {'✅' if checks.get('data_complete') else '❌'}
- 时间戳有效: {'✅' if checks.get('timestamp_valid') else '❌'}
- 数据合理: {'✅' if checks.get('data_reasonable') else '❌'}

**异常原因**:
{sync_result.get('message', '未知错误')}

**建议操作**:
1. 检查通达信客户端是否启动
2. 检查网络连接
3. 手动触发数据同步
4. 如问题持续，请联系技术支持

@{' @'.join(self.operator_ids)}
        """
        return message.strip()
    
    async def send_alert(self,
                         level: str,
                         title: str,
                         message: str,
                         chat_id: str = None) -> Dict[str, Any]:
        """
        发送告警
        
        Args:
            level: 告警级别 (info, warning, error)
            title: 告警标题
            message: 告警内容
            chat_id: 群聊ID
            
        Returns:
            Dict: {"status": "success"|"failed", "message_id": str}
        """
        chat_id = chat_id or self.default_chat_id
        
        # 根据级别选择图标
        icon_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌"
        }
        icon = icon_map.get(level, "ℹ️")
        
        # 构建告警消息
        alert_message = f"""
## {icon} {title}

{message}

**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return await self.send_group_message(
            chat_id=chat_id,
            message=alert_message.strip()
        )
    
    async def send_daily_report(self,
                                 chat_id: str,
                                 report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送每日选股报告
        
        Args:
            chat_id: 群聊ID
            report_data: 报告数据
            
        Returns:
            Dict: {"status": "success"|"failed", "message_id": str}
        """
        date_str = report_data.get("date", date.today()).strftime("%Y-%m-%d")
        sector_code = report_data.get("sector_code", "")
        sector_name = report_data.get("sector_name", "")
        selected_count = report_data.get("selected_count", 0)
        strategies = report_data.get("strategies", {})
        
        # 构建报告消息
        message = f"""
## 📊 {date_str} 每日选股报告

**板块信息**:
- 板块代码: {sector_code}
- 板块名称: {sector_name}

**选股结果**:
- 总选中: {selected_count} 只

**策略分布**:
- 三倍量: {strategies.get('3x_volume', 0)} 只
- 涨停: {strategies.get('limit_up', 0)} 只
- 缺口: {strategies.get('gap', 0)} 只

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return await self.send_group_message(
            chat_id=chat_id,
            message=message.strip()
        )
    
    def should_notify_operator(self, check_result: Dict[str, Any]) -> bool:
        """
        判断是否需要通知操作员
        
        Args:
            check_result: 检查结果
            
        Returns:
            bool: 是否需要通知
        """
        return check_result.get("action_required", False)
    
    async def send_group_message_with_retry(self,
                                            chat_id: str,
                                            message: str,
                                            at_users: List[str] = None) -> Dict[str, Any]:
        """
        发送群消息（带重试）
        
        Args:
            chat_id: 群聊ID
            message: 消息内容
            at_users: @用户列表
            
        Returns:
            Dict: {"status": "success"|"failed", "message_id": str, "retries": int}
        """
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                result = await self.send_group_message(
                    chat_id=chat_id,
                    message=message,
                    at_users=at_users
                )
                
                if result.get("status") == "success":
                    result["retries"] = retries
                    return result
                
                last_error = result.get("error")
                retries += 1
                
                if retries < self.max_retries:
                    logger.warning(f"发送消息失败，{retries}秒后重试 ({retries}/{self.max_retries})")
                    await asyncio.sleep(retries)  # 指数退避
                    
            except Exception as e:
                last_error = str(e)
                retries += 1
                
                if retries < self.max_retries:
                    logger.warning(f"发送消息异常，{retries}秒后重试 ({retries}/{self.max_retries}): {e}")
                    await asyncio.sleep(retries)
        
        logger.error(f"发送消息失败，已达到最大重试次数 ({self.max_retries})")
        return {
            "status": "failed",
            "error": last_error,
            "retries": retries
        }
