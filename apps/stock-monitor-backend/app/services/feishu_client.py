#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书客户端服务
使用飞书SDK进行消息发送、多维表格操作等
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import date
from loguru import logger

# 加载环境变量
from dotenv import load_dotenv
env_path = Path(r"d:\agentsTeam\.env.winbot")
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"已加载环境变量: {env_path}")
else:
    load_dotenv()
    logger.info("已加载默认环境变量")


class FeishuClient:
    """
    飞书客户端
    封装飞书开放平台API
    """
    
    def __init__(self):
        """初始化飞书客户端"""
        self.app_id = os.getenv("FEISHU_APP_ID", "")
        self.app_secret = os.getenv("FEISHU_APP_SECRET", "")
        self.group_chat_id = os.getenv("FEISHU_GROUP_CHAT_ID", "")
        self.user_openid = os.getenv("FEISHU_USER_OPENID", "")
        self.app_token = os.getenv("FEISHU_APP_TOKEN", "")
        self.table_id = os.getenv("FEISHU_TABLE_ID", "")
        
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
        
        logger.info(f"飞书客户端配置:")
        logger.info(f"  App ID: {self.app_id[:10]}..." if self.app_id else "  App ID: 未配置")
        logger.info(f"  Group Chat ID: {self.group_chat_id}")
        logger.info(f"  App Token: {self.app_token[:10]}..." if self.app_token else "  App Token: 未配置")
        logger.info(f"  Table ID: {self.table_id}")
    
    def _get_access_token(self) -> Optional[str]:
        """获取访问令牌"""
        import time
        
        # 检查是否过期
        if self.access_token and self.token_expires_at:
            if time.time() < self.token_expires_at - 300:  # 提前5分钟刷新
                return self.access_token
        
        # 获取新的token
        try:
            import requests
            
            url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
            headers = {"Content-Type": "application/json"}
            data = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            result = response.json()
            
            if result.get("code") == 0:
                self.access_token = result.get("tenant_access_token")
                expires_in = result.get("expires_in", 7200)
                self.token_expires_at = time.time() + expires_in
                logger.info("✅ 获取飞书访问令牌成功")
                return self.access_token
            else:
                logger.error(f"❌ 获取飞书访问令牌失败: {result}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取飞书访问令牌异常: {e}")
            return None
    
    def send_group_message(self, 
                          content: str,
                          msg_type: str = "text") -> Dict[str, Any]:
        """
        发送群消息
        
        Args:
            content: 消息内容
            msg_type: 消息类型 (text/markdown/image)
            
        Returns:
            Dict: 发送结果
        """
        if not self.group_chat_id:
            logger.warning("未配置群聊ID，跳过发送消息")
            return {"status": "skipped", "reason": "no_group_chat_id"}
        
        access_token = self._get_access_token()
        if not access_token:
            return {"status": "failed", "reason": "no_access_token"}
        
        try:
            import requests
            
            url = "https://open.feishu.cn/open-apis/im/v1/messages"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # 构建消息内容
            if msg_type == "text":
                msg_content = {"text": content}
            elif msg_type == "markdown":
                msg_content = {"text": content}  # 飞书markdown也是text类型
            else:
                msg_content = {"text": content}
            
            params = {"receive_id_type": "chat_id"}
            data = {
                "receive_id": self.group_chat_id,
                "msg_type": msg_type,
                "content": json.dumps(msg_content)
            }
            
            response = requests.post(url, headers=headers, json=data, params=params, timeout=10)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"✅ 发送群消息成功")
                return {"status": "success", "message_id": result.get("data", {}).get("message_id")}
            else:
                logger.error(f"❌ 发送群消息失败: {result}")
                return {"status": "failed", "reason": result}
                
        except Exception as e:
            logger.error(f"❌ 发送群消息异常: {e}")
            return {"status": "failed", "reason": str(e)}
    
    def create_task_card(self,
                         task_title: str,
                         task_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建任务卡片
        
        Args:
            task_title: 任务标题
            task_content: 任务内容
            
        Returns:
            Dict: 创建结果
        """
        if not self.group_chat_id:
            return {"status": "skipped", "reason": "no_group_chat_id"}
        
        access_token = self._get_access_token()
        if not access_token:
            return {"status": "failed", "reason": "no_access_token"}
        
        try:
            import requests
            
            # 构建任务卡片消息
            card_content = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {
                            "tag": "plain_text",
                            "content": task_title
                        },
                        "template": "red"
                    },
                    "elements": []
                }
            }
            
            # 添加任务详情
            for key, value in task_content.items():
                card_content["card"]["elements"].append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**{key}**: {value}"
                    }
                })
            
            # 发送卡片消息
            url = "https://open.feishu.cn/open-apis/im/v1/messages"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            params = {"receive_id_type": "chat_id"}
            data = {
                "receive_id": self.group_chat_id,
                "msg_type": "interactive",
                "content": json.dumps(card_content)
            }
            
            response = requests.post(url, headers=headers, json=data, params=params, timeout=10)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"✅ 创建任务卡片成功: {task_title}")
                return {"status": "success", "message_id": result.get("data", {}).get("message_id")}
            else:
                logger.error(f"❌ 创建任务卡片失败: {result}")
                return {"status": "failed", "reason": result}
                
        except Exception as e:
            logger.error(f"❌ 创建任务卡片异常: {e}")
            return {"status": "failed", "reason": str(e)}
    
    def add_records_to_bitable(self,
                               records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        添加记录到飞书多维表格
        
        Args:
            records: 记录列表
            
        Returns:
            Dict: 添加结果
        """
        if not self.app_token or not self.table_id:
            logger.warning("未配置多维表格，跳过添加记录")
            return {"status": "skipped", "reason": "no_bitable_config"}
        
        access_token = self._get_access_token()
        if not access_token:
            return {"status": "failed", "reason": "no_access_token"}
        
        try:
            import requests
            
            url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/batch_create"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "records": [{"fields": record} for record in records]
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"✅ 添加 {len(records)} 条记录到多维表格成功")
                return {
                    "status": "success",
                    "count": len(records)
                }
            else:
                logger.error(f"❌ 添加记录失败: {result}")
                return {"status": "failed", "reason": result}
                
        except Exception as e:
            logger.error(f"❌ 添加记录异常: {e}")
            return {"status": "failed", "reason": str(e)}
    
    def upload_file(self, file_path: str) -> Dict[str, Any]:
        """
        上传文件到飞书
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict: 上传结果
        """
        access_token = self._get_access_token()
        if not access_token:
            return {"status": "failed", "reason": "no_access_token"}
        
        try:
            import requests
            
            url = "https://open.feishu.cn/open-apis/im/v1/files"
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            files = {
                "file": open(file_path, "rb")
            }
            
            data = {
                "file_name": Path(file_path).name,
                "file_type": "image"
            }
            
            response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
            result = response.json()
            
            if result.get("code") == 0:
                file_token = result.get("data", {}).get("file_token")
                logger.info(f"✅ 文件上传成功: {file_token}")
                return {"status": "success", "file_token": file_token}
            else:
                logger.error(f"❌ 文件上传失败: {result}")
                return {"status": "failed", "reason": result}
                
        except Exception as e:
            logger.error(f"❌ 文件上传异常: {e}")
            return {"status": "failed", "reason": str(e)}
    
    def send_selection_report(self,
                              trade_date: date,
                              sector_code: str,
                              selected_stocks: List[Dict[str, Any]],
                              source: str = "tdx") -> Dict[str, Any]:
        """
        发送选股报告到飞书
        消息格式参考: d:\agentsTeam\nanobot-src\nanobot\cron\service.py
        
        Args:
            trade_date: 交易日期
            sector_code: 板块代码
            selected_stocks: 选中的股票列表
            source: 数据来源 (tdx/wencai)
            
        Returns:
            Dict: 发送结果
        """
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 数据来源标识
        source_display = "通达信" if source == "tdx" else "问财"
        
        # 提取股票数量
        stock_count = len(selected_stocks)
        
        # 构建执行结果摘要
        if selected_stocks:
            stock_list_text = []
            for i, stock in enumerate(selected_stocks[:10], 1):  # 最多显示10只
                # 支持两种字段名格式
                code = stock.get('stock_code', '') or stock.get('code', '')
                name = stock.get('stock_name', '') or stock.get('name', '')
                ratio = stock.get('volume_ratio', 0)
                change = stock.get('change_percent', 0)
                stock_list_text.append(f"{i}. {code} {name} | 量比:{ratio:.2f} | 涨幅:{change:.2f}%")
            
            if len(selected_stocks) > 10:
                stock_list_text.append(f"... 等共 {stock_count} 只股票")
            
            result_text = f"发现 {stock_count} 只符合条件的股票\n\n" + "\n".join(stock_list_text)
        else:
            result_text = "未找到符合条件的股票"
        
        # 构建消息内容 - 参考 service.py 的 _format_stock_notification 格式
        content = f"""📈 定时任务执行完成

📋 **任务**：{source_display}三倍量+涨停选股
⏰ **时间**：{current_time}
✅ **状态**：成功

📊 **执行结果**：
{result_text}

📎 **数据已同步到飞书多维表格**

---

💡 **可用指令**：
• `@winbot 检查任务` - 立即检查飞书任务
• `@winbot 查询三倍量` - 执行3倍量选股
• `@winbot 分析股票 <代码>` - 分析指定股票
• `@winbot 帮助` - 显示完整帮助信息"""
        
        # 发送群消息（使用text类型）
        msg_result = self.send_group_message(content, msg_type="text")
        
        # 添加到多维表格（如果有配置）
        if selected_stocks and self.app_token and self.table_id:
            records = [
                {
                    "日期": str(trade_date),
                    "板块代码": sector_code,
                    "股票代码": s.get('stock_code', '') or s.get('code', ''),
                    "股票名称": s.get('stock_name', '') or s.get('name', ''),
                    "量比": str(round(s.get('volume_ratio', 0), 2)),
                    "涨幅": str(round(s.get('change_percent', 0), 2)),
                    "来源": source_display
                }
                for s in selected_stocks
            ]
            
            table_result = self.add_records_to_bitable(records)
        else:
            table_result = {"status": "skipped", "reason": "no_bitable_config or no stocks"}
        
        return {
            "message": msg_result,
            "table": table_result
        }
    
    def send_error_notification(self,
                                job_name: str,
                                error_message: str,
                                source: str = "tdx") -> Dict[str, Any]:
        """
        发送错误通知到飞书
        消息格式参考: d:\agentsTeam\nanobot-src\nanobot\cron\service.py
        
        Args:
            job_name: 任务名称
            error_message: 错误信息
            source: 数据来源
            
        Returns:
            Dict: 发送结果
        """
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 截断错误信息如果太长
        if len(error_message) > 300:
            error_message = error_message[:300] + "\n... (已截断)"
        
        content = f"""❌ 定时任务执行失败

📋 **任务**：{job_name}
⏰ **时间**：{current_time}
🔴 **状态**：失败

💥 **错误信息**：
```
{error_message}
```

🔧 **建议**：
1. 检查相关服务是否正常（通达信/天龙博弈）
2. 查看详细日志排查问题
3. 手动执行或等待下次定时任务"""
        
        return self.send_group_message(content, msg_type="text")
    
    def send_batch_status_report(self,
                                  batch_id: str,
                                  trade_date: date,
                                  sector_code: str,
                                  status: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送批次状态报告
        
        Args:
            batch_id: 批次ID
            trade_date: 交易日期
            sector_code: 板块代码
            status: 状态字典
            
        Returns:
            Dict: 发送结果
        """
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 状态图标映射
        status_icons = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌"
        }
        
        data_sync = status.get("data_sync_status", "pending")
        selection = status.get("selection_status", "pending")
        screenshot = status.get("screenshot_status", "pending")
        feishu = status.get("feishu_sync_status", "pending")
        
        content = f"""📊 TDX选股批次状态更新

📋 **批次**：{batch_id}
📅 **日期**：{trade_date}
🏷️ **板块**：{sector_code}
⏰ **时间**：{current_time}

📈 **执行进度**：
{status_icons.get(data_sync, '⏳')} 数据同步: {data_sync}
{status_icons.get(selection, '⏳')} 选股执行: {selection}
{status_icons.get(screenshot, '⏳')} 截图生成: {screenshot}
{status_icons.get(feishu, '⏳')} 飞书同步: {feishu}

---

💡 **可用指令**：
• `@winbot 检查任务` - 立即检查飞书任务
• `@winbot 查询三倍量` - 执行3倍量选股
• `@winbot 分析股票 <代码>` - 分析指定股票"""
        
        return self.send_group_message(content, msg_type="text")


# 全局飞书客户端实例
feishu_client: Optional[FeishuClient] = None


def get_feishu_client() -> FeishuClient:
    """获取飞书客户端单例"""
    global feishu_client
    if feishu_client is None:
        feishu_client = FeishuClient()
    return feishu_client


def init_feishu_client() -> FeishuClient:
    """初始化飞书客户端"""
    client = FeishuClient()
    
    # 测试连接
    if client.app_id and client.app_secret:
        token = client._get_access_token()
        if token:
            logger.info("✅ 飞书客户端初始化成功")
            global feishu_client
            feishu_client = client
            return client
        else:
            logger.warning("⚠️ 飞书客户端初始化失败，但会继续运行")
            return client
    else:
        logger.warning("⚠️ 未配置飞书凭证，跳过初始化")
        return client


if __name__ == "__main__":
    # 测试飞书客户端
    client = init_feishu_client()
    
    # 发送测试消息
    result = client.send_group_message("🧪 飞书客户端测试消息", msg_type="text")
    print(f"\n发送结果: {result}")
