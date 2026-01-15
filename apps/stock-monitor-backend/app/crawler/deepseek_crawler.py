"""
DeepSeek网页版爬虫
使用Playwright实现自动登录和消息交互
"""
import asyncio
import json
import time
import logging
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Page, BrowserContext
from .base import CrawlerBase

logger = logging.getLogger(__name__)


class DeepSeekCrawler(CrawlerBase):
    """DeepSeek网页版爬虫"""
    
    def __init__(self, db, platform_id: str = "deepseek"):
        super().__init__(db, platform_id)
        self.base_url = "https://chat.deepseek.com"
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.session_cookie = None
        self.is_logged_in = False
        self.playwright = None
        
    async def initialize(self):
        """初始化浏览器"""
        try:
            self.playwright = await async_playwright().start()
            browser_type = self.playwright.chromium
            
            launch_options = {
                "headless": False,  # 非headless模式以便调试
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox"
                ]
            }
            
            self.browser = await browser_type.launch(**launch_options)
            logger.info("DeepSeek浏览器初始化成功")
            return True
        except Exception as e:
            logger.error(f"浏览器初始化失败: {str(e)}")
            return False
    
    async def login(self, email: str, password: str) -> bool:
        """登录DeepSeek"""
        try:
            # 创建新的上下文
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            
            self.page = await self.context.new_page()
            await self.page.goto(self.base_url, wait_until="networkidle", timeout=30000)
            
            # 等待页面加载并点击登录按钮
            await self.page.wait_for_selector("button:has-text('登录')", timeout=10000)
            await self.page.click("button:has-text('登录')")
            
            # 等待登录表单出现
            await self.page.wait_for_selector("input[type='email']", timeout=5000)
            
            # 输入邮箱
            await self.page.fill("input[type='email']", email)
            
            # 点击下一步
            await self.page.click("button:has-text('下一步')")
            
            # 等待密码输入框出现
            await self.page.wait_for_selector("input[type='password']", timeout=5000)
            
            # 输入密码
            await self.page.fill("input[type='password']", password)
            
            # 点击登录
            await self.page.click("button:has-text('登录')")
            
            # 等待登录成功（检测聊天界面）
            await self.page.wait_for_selector(".chat-container, textarea[placeholder*='输入']", timeout=15000)
            
            # 保存会话cookie
            cookies = await self.context.cookies()
            self.session_cookie = cookies
            
            self.is_logged_in = True
            logger.info("DeepSeek登录成功")
            return True
            
        except Exception as e:
            logger.error(f"登录失败: {str(e)}")
            await self.screenshot("login_error")
            return False
    
    async def send_message(self, message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """发送消息到DeepSeek并获取响应"""
        if not self.is_logged_in:
            raise Exception("请先登录DeepSeek")
        
        try:
            # 查找消息输入框
            textarea = await self.page.wait_for_selector("textarea[placeholder*='输入'], textarea[placeholder*='message']", timeout=5000)
            
            # 输入消息
            await textarea.fill(message)
            
            # 点击发送按钮（查找包含发送图标的按钮）
            send_button = await self.page.wait_for_selector("button:has(svg) >> nth=-1", timeout=5000)
            await send_button.click()
            
            # 等待响应
            response = await self._wait_for_response()
            
            return {
                "success": True,
                "response": response,
                "conversation_id": conversation_id or str(int(time.time())),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"发送消息失败: {str(e)}")
            await self.screenshot("send_error")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _wait_for_response(self, timeout: int = 60000) -> str:
        """等待DeepSeek响应"""
        start_time = time.time()
        last_response = ""
        
        while time.time() - start_time < timeout / 1000:
            try:
                # 查找最新的响应消息（尝试多种选择器）
                response_elements = await self.page.query_selector_all(
                    ".message-content:last-child, .assistant-message:last-child, [role='assistant']:last-child"
                )
                
                if response_elements:
                    latest_response = await response_elements[-1].text_content()
                    if latest_response and latest_response != last_response:
                        # 等待一段时间，确保响应完整
                        await asyncio.sleep(2)
                        final_response = await response_elements[-1].text_content()
                        if final_response == latest_response:  # 响应稳定
                            return final_response.strip()
                        last_response = latest_response
                
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"等待响应时出错: {str(e)}")
                await asyncio.sleep(1)
        
        raise TimeoutError("等待响应超时")
    
    async def start_new_conversation(self) -> bool:
        """开始新的对话"""
        try:
            # 尝试多种新对话按钮选择器
            new_chat_btn = await self.page.wait_for_selector(
                "button:has-text('新对话'), button:has-text('New Chat'), button[aria-label*='new']",
                timeout=5000
            )
            await new_chat_btn.click()
            await self.page.wait_for_selector("textarea[placeholder*='输入'], textarea[placeholder*='message']", timeout=5000)
            logger.info("开始新对话成功")
            return True
        except Exception as e:
            logger.error(f"开始新对话失败: {str(e)}")
            return False
    
    async def get_conversation_history(self) -> list:
        """获取对话历史"""
        try:
            history = []
            conversation_items = await self.page.query_selector_all(
                ".conversation-item, .chat-item, [role='conversation']"
            )
            
            for item in conversation_items:
                title = await item.text_content()
                history.append({"title": title})
            
            logger.info(f"获取到 {len(history)} 个对话历史")
            return history
        except Exception as e:
            logger.error(f"获取对话历史失败: {str(e)}")
            return []
    
    async def close(self):
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("DeepSeek浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器失败: {str(e)}")
    
    async def screenshot(self, name: str):
        """截图用于调试"""
        try:
            if self.page:
                screenshot_path = f"debug_deepseek_{name}_{int(time.time())}.png"
                await self.page.screenshot(path=screenshot_path)
                logger.info(f"截图已保存: {screenshot_path}")
        except Exception as e:
            logger.error(f"截图失败: {str(e)}")