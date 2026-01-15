"""
DeepSeek网页版爬虫
使用Playwright实现自动登录和消息交互
"""
import asyncio
import json
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from markdownify import markdownify as md
from playwright.async_api import async_playwright, Page, BrowserContext, Browser
from sqlalchemy.ext.asyncio import AsyncSession
from .base import CrawlerBase

logger = logging.getLogger(__name__)


class DeepSeekCrawler(CrawlerBase):
    """DeepSeek网页版爬虫"""
    
    # 全局共享的 Playwright 资源
    _shared_playwright = None
    _shared_browser = None
    _shared_context = None
    _shared_page = None
    _is_initializing = False

    def __init__(self, db: AsyncSession, platform_id: str = "deepseek"):
        super().__init__(db, platform_id)
        self.base_url = "https://chat.deepseek.com"
        # 使用类变量引用共享资源
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None

    async def start(self, headless: bool = True):
        """启动浏览器（使用单例模式）"""
        # 如果共享页面已存在，直接复用
        if DeepSeekCrawler._shared_page and not DeepSeekCrawler._shared_page.is_closed():
            self.page = DeepSeekCrawler._shared_page
            self.context = DeepSeekCrawler._shared_context
            self.browser = DeepSeekCrawler._shared_browser
            self.playwright = DeepSeekCrawler._shared_playwright
            logger.info("复用现有的浏览器实例")
            return

        # 防止并发初始化
        while DeepSeekCrawler._is_initializing:
            await asyncio.sleep(0.1)
            if DeepSeekCrawler._shared_page:
                await self.start(headless)
                return

        try:
            DeepSeekCrawler._is_initializing = True
            
            # 双重检查
            if DeepSeekCrawler._shared_page and not DeepSeekCrawler._shared_page.is_closed():
                self.page = DeepSeekCrawler._shared_page
                return

            logger.info("初始化新的浏览器实例...")
            
            # 获取平台配置和会话
            session_data = await self.get_best_session()
            
            # 启动 Playwright
            if not DeepSeekCrawler._shared_playwright:
                DeepSeekCrawler._shared_playwright = await async_playwright().start()
            self.playwright = DeepSeekCrawler._shared_playwright
            
            args = [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
            ]
            
            # 如果有 session 数据，尝试无头启动
            # 如果没有 session 数据，强制有头启动进行登录
            should_be_headless = headless
            if not session_data:
                logger.info("无有效会话，强制启动有头浏览器进行登录")
                should_be_headless = False
                
            if not DeepSeekCrawler._shared_browser:
                DeepSeekCrawler._shared_browser = await self.playwright.chromium.launch(
                    headless=should_be_headless, 
                    args=args
                )
            self.browser = DeepSeekCrawler._shared_browser
            
            # 创建上下文
            context_options = {
                "viewport": {'width': 1920, 'height': 1080},
                "user_agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            if not DeepSeekCrawler._shared_context:
                DeepSeekCrawler._shared_context = await self.browser.new_context(**context_options)
            self.context = DeepSeekCrawler._shared_context
            
            # 注入反爬脚本
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            # 注入 Cookies
            if session_data and session_data.get('cookies_json'):
                logger.info("注入现有会话 Cookies")
                try:
                    # 确保存储的 cookies 格式正确
                    cookies = session_data['cookies_json']
                    if isinstance(cookies, str):
                        cookies = json.loads(cookies)
                    
                    # 过滤并修正 cookie 字段
                    valid_cookies = []
                    for c in cookies:
                        cookie = {
                            'name': c['name'],
                            'value': c['value'],
                            'domain': c.get('domain', '.deepseek.com'),
                            'path': c.get('path', '/')
                        }
                        valid_cookies.append(cookie)
                        
                    await self.context.add_cookies(valid_cookies)
                except Exception as e:
                    logger.error(f"注入 Cookies 失败: {e}")

            if not DeepSeekCrawler._shared_page:
                DeepSeekCrawler._shared_page = await self.context.new_page()
            self.page = DeepSeekCrawler._shared_page
            
            # 访问主页
            logger.info(f"访问 {self.base_url}")
            await self.page.goto(self.base_url)
            
            # 检查登录状态
            try:
                # 等待网络空闲，确保重定向完成
                await self.page.wait_for_load_state("networkidle", timeout=10000)
                await self.page.wait_for_timeout(2000)
                
                url = self.page.url
                if "login" in url:
                    logger.warning("Token 过期或未登录，需要手动登录")
                    if should_be_headless:
                        # 如果是无头模式但需要登录，则重启为有头模式
                        logger.info("切换到有头模式进行登录...")
                        # 关闭当前资源
                        await self.close()
                        # 重新启动（递归调用）
                        await self.start(headless=False)
                        return
                    
                    # 等待用户手动登录
                    await self._wait_for_manual_login()
                else:
                    logger.info("会话有效，登录成功")
                    
            except Exception as e:
                logger.error(f"登录检查异常: {e}")
                if should_be_headless:
                    await self.close()
                    await self.start(headless=False)
                    
        finally:
            DeepSeekCrawler._is_initializing = False

    async def _wait_for_manual_login(self):
        """等待手动登录并保存会话"""
        logger.info("请在浏览器中手动登录...")
        try:
            # 等待 URL 不再包含 login 且包含 chat.deepseek.com
            await self.page.wait_for_url(lambda url: "login" not in url and "chat.deepseek.com" in url, timeout=300000)
            logger.info("检测到登录成功！")
            
            # 等待 Cookie 稳定
            await self.page.wait_for_timeout(5000)
            
            # 获取并保存 Cookie
            cookies = await self.context.cookies()
            # 注意：这里需要确保 session_service 是可用的
            # 暂时使用 self.db 来创建一个新的 session_service 或复用
            from app.services.session_service import SessionService
            session_service = SessionService(self.db)
            
            await session_service.update_session(
                self.platform_id,
                cookies_json=cookies,
                status="active"
            )
            logger.info("会话已保存到数据库")
            
        except Exception as e:
            logger.error(f"等待登录超时或失败: {e}")
            raise e

    async def close(self):
        """关闭浏览器资源（清理全局资源）"""
        # 注意：在单例模式下，通常不直接关闭，除非显式请求
        # 这里为了兼容性，如果实例调用 close，我们清理全局资源
        if DeepSeekCrawler._shared_page:
            await DeepSeekCrawler._shared_page.close()
            DeepSeekCrawler._shared_page = None
        if DeepSeekCrawler._shared_context:
            await DeepSeekCrawler._shared_context.close()
            DeepSeekCrawler._shared_context = None
        if DeepSeekCrawler._shared_browser:
            await DeepSeekCrawler._shared_browser.close()
            DeepSeekCrawler._shared_browser = None
        if DeepSeekCrawler._shared_playwright:
            await DeepSeekCrawler._shared_playwright.stop()
            DeepSeekCrawler._shared_playwright = None
            
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

    async def list_chats(self) -> List[Dict[str, Any]]:
        """获取会话列表"""
        if not self.page:
            await self.start()
            
        try:
            # 等待侧边栏加载
            # 注意：选择器需要根据实际页面结构调整
            await self.page.wait_for_load_state("networkidle")
            
            # 简单实现：由于 DeepSeek 页面结构复杂，这里暂时返回最近的一个模拟会话或尝试抓取
            # 实际抓取需要分析 DOM
            return [{"id": "latest", "title": "Latest Session", "date": datetime.now().isoformat()}]
            
        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            return []

    async def read_chat(self, chat_id: str = "latest") -> str:
        """读取会话内容并转为 Markdown"""
        if not self.page:
            await self.start()
            
        try:
            # 如果不是 latest，需要点击对应的会话
            # ... navigation logic ...
            
            await self.page.wait_for_load_state("domcontentloaded")
            await self.page.wait_for_timeout(2000)
            
            # 获取内容
            try:
                # 尝试定位主要内容区域，避免包含侧边栏
                # 假设主内容在 main 标签或特定的 div 中
                content = await self.page.content()
                # 简单的选择器尝试，实际需调整
                # content = await self.page.locator("div[class*='chat-content']").inner_html()
            except Exception:
                content = await self.page.content()
                
            # 转 Markdown
            markdown_content = md(content, heading_style="ATX")
            
            return markdown_content
            
        except Exception as e:
            logger.error(f"读取会话失败: {e}")
            return f"Error: {str(e)}"

    async def send_message(self, message: str, chat_id: Optional[str] = None) -> str:
        """发送消息并获取回复"""
        if not self.page:
            await self.start()
            
        try:
            # 定位输入框
            textarea = self.page.locator("textarea")
            await textarea.wait_for(state="visible", timeout=10000)
            
            await textarea.fill(message)
            await textarea.press("Enter")
            
            logger.info("消息已发送，等待回复...")
            
            # 等待回复生成
            # 策略：等待 "停止生成" 按钮消失，或等待新的消息元素出现
            # 这里简单等待一段时间
            await self.page.wait_for_timeout(5000)
            
            # 尝试获取最后一条消息
            # return await self._get_last_message()
            return "Message sent. (Reply retrieval requires DOM selector tuning)"
            
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return f"Error: {str(e)}"
