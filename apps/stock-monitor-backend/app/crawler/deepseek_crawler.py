"""
DeepSeek网页版爬虫
使用Playwright实现自动登录和消息交互
"""
import asyncio
import json
import time
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from markdownify import markdownify as md
from playwright.async_api import async_playwright, Page, BrowserContext, Browser, Error as PlaywrightError
from sqlalchemy.ext.asyncio import AsyncSession
from .base import CrawlerBase

logger = logging.getLogger(__name__)


from app.services.cookie_service import CookieService

class DeepSeekCrawler(CrawlerBase):
    """DeepSeek网页版爬虫"""
    
    # 常量定义
    USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
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
        # 优先读取环境变量配置
        env_headless = os.getenv("MCP_HEADLESS", "true").lower() == "true"
        # 如果参数显式传入（非默认True），则使用参数，否则使用环境变量
        actual_headless = headless if headless is False else env_headless

        # 检查现有资源状态
        if DeepSeekCrawler._shared_browser:
            if not DeepSeekCrawler._shared_browser.is_connected():
                logger.warning("检测到浏览器连接断开，正在清理资源...")
                await self.close()
            elif DeepSeekCrawler._shared_page and DeepSeekCrawler._shared_page.is_closed():
                logger.warning("检测到页面已关闭，正在清理资源...")
                await self.close()

        # 如果共享页面已存在且有效，直接复用
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
            if DeepSeekCrawler._shared_page and not DeepSeekCrawler._shared_page.is_closed():
                await self.start(actual_headless)
                return

        try:
            DeepSeekCrawler._is_initializing = True
            
            # 双重检查
            if DeepSeekCrawler._shared_page and not DeepSeekCrawler._shared_page.is_closed():
                self.page = DeepSeekCrawler._shared_page
                return

            logger.info(f"初始化新的浏览器实例 (Headless: {actual_headless})...")
            
            # 获取平台配置和会话
            session_data = await self.get_best_session()
            
            # 如果没有找到会话，尝试从 CookieService (ChromeCookie) 加载
            # 这允许复用主项目中已有的 Cookie 存储机制
            if not session_data:
                try:
                    cookie_service = CookieService(self.db)
                    # 尝试多种域名匹配
                    cookies = await cookie_service.get_cookies('deepseek.com')
                    if not cookies:
                        cookies = await cookie_service.get_cookies('chat.deepseek.com')
                    
                    if cookies:
                        logger.info("从 CookieService (ChromeCookie) 加载到历史会话数据")
                        session_data = {
                            "cookies_json": cookies, # 已经是 list 对象
                            "user_agent": self.USER_AGENT
                        }
                except Exception as e:
                    logger.warning(f"尝试从 CookieService 加载会话失败: {e}")
            
            # 启动 Playwright
            if not DeepSeekCrawler._shared_playwright:
                DeepSeekCrawler._shared_playwright = await async_playwright().start()
            self.playwright = DeepSeekCrawler._shared_playwright
            
            args = [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
            ]
            
            # 如果有 session 数据，尝试按配置启动
            # 如果没有 session 数据，强制有头启动进行登录
            should_be_headless = actual_headless
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
                "user_agent": self.USER_AGENT
            }
            
            # 尝试加载会话状态 (Cookies + LocalStorage)
            session_storage_data = {}
            
            if session_data and session_data.get('cookies_json'):
                try:
                    # 兼容处理：可能是 JSON 字符串，也可能是对象
                    raw_data = session_data['cookies_json']
                    if isinstance(raw_data, str):
                        state_data = json.loads(raw_data)
                    else:
                        state_data = raw_data
                    
                    # 检查数据格式
                    if isinstance(state_data, list):
                        # ... (keep existing code for list) ...
                        # 旧格式：仅 Cookies 列表 -> 转换为 Storage State 格式
                        logger.info("检测到旧版 Cookies 格式，正在转换...")
                        # 过滤并修正 cookie
                        valid_cookies = []
                        for c in state_data:
                            domain = c.get('domain', '')
                            if not domain:
                                domain = '.deepseek.com'
                            
                            cookie = {
                                'name': c['name'],
                                'value': c['value'],
                                'domain': domain,
                                'path': c.get('path', '/')
                            }
                            valid_cookies.append(cookie)
                        
                        context_options["storage_state"] = {
                            "cookies": valid_cookies,
                            "origins": []
                        }
                    elif isinstance(state_data, dict):
                        # 新格式：完整 Storage State
                        logger.info("加载完整会话状态 (Cookies + LocalStorage)")
                        
                        # 提取 SessionStorage (Playwright 不支持直接通过 storage_state 注入)
                        if 'sessionStorage' in state_data:
                            session_storage_data = state_data.pop('sessionStorage')
                            logger.info(f"提取到 SessionStorage: {len(session_storage_data)} 项")
                            
                        context_options["storage_state"] = state_data
                        
                except Exception as e:
                    logger.error(f"解析会话数据失败: {e}")
            
            if not DeepSeekCrawler._shared_context:
                DeepSeekCrawler._shared_context = await self.browser.new_context(**context_options)
            self.context = DeepSeekCrawler._shared_context
            
            # 注入反爬脚本
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            # 注入 SessionStorage
            if session_storage_data:
                try:
                    ss_script = f"""
                    (function() {{
                        try {{
                            const ss = {json.dumps(session_storage_data)};
                            for (const [key, value] of Object.entries(ss)) {{
                                window.sessionStorage.setItem(key, value);
                            }}
                            console.log('SessionStorage injected:', Object.keys(ss).length);
                        }} catch (e) {{
                            console.error('SessionStorage injection failed:', e);
                        }}
                    }})();
                    """
                    await self.context.add_init_script(ss_script)
                    logger.info("SessionStorage 注入脚本已添加")
                except Exception as e:
                    logger.error(f"构建 SessionStorage 注入脚本失败: {e}")
            
            # 旧的 Cookie 注入代码已移除，由 storage_state 接管

            if not DeepSeekCrawler._shared_page:
                DeepSeekCrawler._shared_page = await self.context.new_page()
            self.page = DeepSeekCrawler._shared_page
            
            # 访问主页 (带错误重试)
            try:
                logger.info(f"访问 {self.base_url}")
                await self.page.goto(self.base_url)
            except PlaywrightError as e:
                if "closed" in str(e).lower():
                    logger.error("浏览器意外关闭，尝试重置资源并重试...")
                    await self.close()
                    # 释放锁以便递归调用
                    DeepSeekCrawler._is_initializing = False
                    await self.start(headless=actual_headless)
                    return
                raise e
            
            # 检查登录状态
            try:
                # 等待网络空闲，确保重定向完成
                # 使用 try-except 包裹，避免网络超时导致整个流程失败
                try:
                    await self.page.wait_for_load_state("networkidle", timeout=15000)
                except Exception as e:
                    logger.warning(f"等待页面加载超时 (非致命): {e}")
                
                await self.page.wait_for_timeout(2000)
                
                # 增强的登录检查逻辑：不再仅依赖 URL，而是检查页面元素
                is_logged_in = False
                try:
                    # 尝试寻找聊天输入框或特定的聊天界面元素
                    # DeepSeek 聊天界面通常包含 textarea
                    await self.page.wait_for_selector("textarea", timeout=5000)
                    is_logged_in = True
                    logger.info("检测到聊天输入框，确认为已登录状态")
                except Exception:
                    # 如果找不到 textarea，检查是否在登录页
                    url = self.page.url
                    if "login" in url or "sign" in url:
                        logger.warning(f"检测到登录页 URL: {url}")
                    else:
                        logger.warning(f"未检测到聊天输入框，当前 URL: {url}")
                
                if not is_logged_in:
                    logger.warning("Token 可能过期或未登录，需要手动登录")
                    if should_be_headless:
                        # 如果是无头模式但需要登录，则重启为有头模式
                        logger.info("切换到有头模式进行登录...")
                        # 关闭当前资源
                        await self.close()
                        DeepSeekCrawler._is_initializing = False # 重置标志
                        # 重新启动（递归调用）
                        await self.start(headless=False)
                        return
                    
                    # 等待用户手动登录
                    await self._wait_for_manual_login()
                    
                    # 登录成功后，自动关闭有头浏览器并切换回配置的模式（通常是无头）
                    logger.info("登录成功，正在切换到后台运行模式...")
                    await self.close()
                    DeepSeekCrawler._is_initializing = False
                    # 读取配置决定是否无头（默认True）
                    env_headless = os.getenv("MCP_HEADLESS", "true").lower() == "true"
                    await self.start(headless=env_headless)
                    return
                else:
                    logger.info("会话有效，登录成功")
                    
                    # 如果是从 CookieService 加载的（session_data 为伪造的），
                    # 或者为了保险起见，我们可以更新一次数据库中的会话，确保它是最新的
                    # 这样下次启动就能直接读库，不需要再依赖 CookieService
                    if not session_data or not session_data.get('cookies_json') or isinstance(session_data.get('cookies_json'), list):
                        logger.info("正在刷新并保存当前会话状态...")
                        try:
                            # 获取完整会话状态
                            storage_state = await self.context.storage_state()
                            
                            # 获取 SessionStorage
                            try:
                                session_storage = await self.page.evaluate("""() => {
                                    const items = {};
                                    try {
                                        for (let i = 0; i < sessionStorage.length; i++) {
                                            const key = sessionStorage.key(i);
                                            if (key) {
                                                items[key] = sessionStorage.getItem(key);
                                            }
                                        }
                                    } catch (e) {
                                        console.error('Failed to read sessionStorage:', e);
                                    }
                                    return items;
                                }""")
                                storage_state['sessionStorage'] = session_storage
                            except Exception as e:
                                logger.warning(f"刷新会话时获取 SessionStorage 失败: {e}")
                                
                            # 过滤并保存
                            cookies = storage_state.get('cookies', [])
                            valid_cookies = []
                            for cookie in cookies:
                                if 'deepseek.com' in cookie.get('domain', ''):
                                    valid_cookies.append(cookie)
                            
                            if not valid_cookies:
                                valid_cookies = cookies
                                
                            storage_state['cookies'] = valid_cookies
                            
                            await self.session_service.upsert_session(
                                platform_id=self.platform_id,
                                user_id="default_user",
                                account_name="DeepSeek User",
                                cookies=storage_state,
                                user_agent=self.USER_AGENT
                            )
                            logger.info("会话状态已刷新并保存")
                        except Exception as e:
                            logger.error(f"刷新会话状态失败: {e}")

            except Exception as e:
                logger.error(f"登录检查异常: {e}")
                if should_be_headless:
                    # 如果检查过程中出错且是无头模式，尝试切换到有头模式让用户看看发生了什么
                    logger.info("检查异常，切换到有头模式...")
                    await self.close()
                    DeepSeekCrawler._is_initializing = False
                    await self.start(headless=False)
                    return
                    
        finally:
            DeepSeekCrawler._is_initializing = False

    async def _wait_for_manual_login(self):
        """等待手动登录并保存会话"""
        logger.info("请在浏览器中手动登录...")
        try:
            # 改进等待逻辑：等待聊天界面核心元素出现，而不仅仅是 URL 变化
            # 有时候 URL 变了但页面还是空白或加载中
            try:
                await self.page.wait_for_selector("textarea", timeout=300000)
                logger.info("检测到聊天输入框，登录成功！")
            except Exception as e:
                logger.warning(f"等待聊天界面超时，尝试检查 URL... {e}")
                # 降级方案：检查 URL
                await self.page.wait_for_url(lambda url: "login" not in url and "chat.deepseek.com" in url, timeout=60000)
                logger.info("检测到 URL 符合预期，假定登录成功")
            
            # 等待 Cookie 和 Storage 稳定
            await self.page.wait_for_timeout(5000)
            
            # 获取完整会话状态 (Cookies + LocalStorage)
            storage_state = await self.context.storage_state()
            
            # 获取 SessionStorage
            try:
                session_storage = await self.page.evaluate("""() => {
                    const items = {};
                    try {
                        for (let i = 0; i < sessionStorage.length; i++) {
                            const key = sessionStorage.key(i);
                            if (key) {
                                items[key] = sessionStorage.getItem(key);
                            }
                        }
                    } catch (e) {
                        console.error('Failed to read sessionStorage:', e);
                    }
                    return items;
                }""")
                storage_state['sessionStorage'] = session_storage
                logger.info(f"获取到 SessionStorage: {len(session_storage)} 项")
            except Exception as e:
                logger.error(f"获取 SessionStorage 失败: {e}")
            
            # 过滤 Cookies (保留 deepseek 相关)
            cookies = storage_state.get('cookies', [])
            valid_cookies = []
            for cookie in cookies:
                if 'deepseek.com' in cookie.get('domain', ''):
                    valid_cookies.append(cookie)
            
            if not valid_cookies:
                logger.warning("未获取到 deepseek 相关 cookie，尝试保存所有 cookie")
                valid_cookies = cookies
                
            storage_state['cookies'] = valid_cookies
            
            # 保存到数据库
            # 如果没有 user_id，暂时使用默认值
            await self.session_service.upsert_session(
                platform_id=self.platform_id,
                user_id="default_user",
                account_name="DeepSeek User",
                cookies=storage_state, # 传递完整状态字典
                user_agent=self.USER_AGENT # 使用统一 User Agent
            )
            
            ls_count = 0
            if 'origins' in storage_state:
                for origin in storage_state['origins']:
                    ls_count += len(origin.get('localStorage', []))
                    
            ss_count = len(storage_state.get('sessionStorage', {}))
            
            logger.info(f"会话已保存到数据库 (Cookies: {len(valid_cookies)}, LocalStorage: {ls_count}, SessionStorage: {ss_count})")
            logger.info(f"Cookie Domains: {list(set([c.get('domain') for c in valid_cookies]))}")
            
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

    async def crawl(self, *args, **kwargs) -> Dict[str, Any]:
        """
        实现抽象基类的 crawl 方法
        DeepSeek 爬虫主要通过 MCP 工具调用特定方法，此方法作为占位符或通用入口
        """
        if not self.page:
            await self.start()
        return {"status": "ok", "message": "DeepSeek crawler is ready. Use MCP tools to interact."}

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
            # 如果不是 latest，尝试导航到特定会话
            if chat_id and chat_id != "latest":
                target_url = f"{self.base_url}/a/chat/s/{chat_id}"
                if self.page.url != target_url:
                    logger.info(f"正在导航到会话: {target_url}")
                    await self.page.goto(target_url)
                    await self.page.wait_for_load_state("networkidle")
            
            await self.page.wait_for_load_state("domcontentloaded")
            await self.page.wait_for_timeout(2000)
            
            # 获取内容
            try:
                # 尝试定位主要内容区域，避免包含侧边栏
                # DeepSeek 的聊天内容通常在 id="root" 下的某个深层 div
                # 我们尝试获取包含 markdown 类的父级容器
                
                content = await self.page.evaluate("""() => {
                    // 策略：找到所有 .ds-markdown 的父容器
                    const markdowns = document.querySelectorAll('.ds-markdown');
                    if (markdowns.length > 0) {
                        // 找到包含所有对话的容器
                        // 通常是 markdowns[0] 的几个父级以上
                        // 这里简化：直接提取所有 markdown 元素的内容拼接，或者提取 main 标签
                        
                        // 尝试1: 提取 main
                        const main = document.querySelector('div[id="root"]'); // DeepSeek 通常在 root 下
                        if (main) return main.innerHTML;
                    }
                    return document.body.innerHTML;
                }""")
            except Exception:
                content = await self.page.content()
                
            # 转 Markdown
            # 过滤掉一些导航栏等噪音 (markdownify 会处理一部分，但我们可以预处理)
            markdown_content = md(content, heading_style="ATX")
            
            # 简单的后处理清理
            lines = markdown_content.split('\n')
            cleaned_lines = []
            for line in lines:
                # 过滤掉常见的导航文本
                if "New Chat" in line or "Search" in line or "History" in line:
                    continue
                cleaned_lines.append(line)
                
            return '\n'.join(cleaned_lines)
            
        except Exception as e:
            logger.error(f"读取会话失败: {e}")
            return f"Error: {str(e)}"

    async def send_message(self, message: str, chat_id: Optional[str] = None) -> str:
        """发送消息并获取回复"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                if not self.page or self.page.is_closed():
                    logger.info("页面未初始化或已关闭，正在启动...")
                    await self.start()
                
                # 双重检查
                if not self.page:
                    raise Exception("无法初始化浏览器页面")

                # 定位输入框
                textarea = self.page.locator("textarea")
                try:
                    await textarea.wait_for(state="visible", timeout=10000)
                except Exception as e:
                    # 如果找不到输入框，可能是页面崩溃或未登录
                    logger.warning(f"未找到输入框 (尝试 {attempt+1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        logger.info("尝试刷新页面...")
                        try:
                            await self.page.reload()
                            await self.page.wait_for_load_state("networkidle", timeout=10000)
                        except:
                            # 刷新失败，强制重启
                            await self.close()
                            continue
                    else:
                        raise e
                
                await textarea.fill(message)
                await textarea.press("Enter")
                
                logger.info("消息已发送，等待回复...")
                
                # 等待回复生成
                reply = await self._wait_for_reply()
                return reply
                
            except Exception as e:
                logger.error(f"发送消息失败 (尝试 {attempt+1}): {e}")
                if "closed" in str(e).lower() or "target" in str(e).lower():
                    # 浏览器关闭错误，强制重置
                    await self.close()
                
                if attempt == max_retries - 1:
                    return f"Error: {str(e)}"
                
                # 等待后重试
                await asyncio.sleep(2)

    async def _wait_for_reply(self) -> str:
        """等待并获取回复内容"""
        # 策略：
        # 1. 初始等待，让消息上屏
        # 2. 循环检查最后一条消息的内容变化
        # 3. 如果内容连续一段时间（如 2秒）未变，且不为空，则认为结束
        
        await self.page.wait_for_timeout(1000)  # 等待消息上屏
        
        last_text = ""
        stable_count = 0
        max_retries = 120  # 最多等待 60 秒
        check_interval = 0.5
        
        for _ in range(max_retries):
            current_text = await self._get_last_message_content()
            
            # 过滤掉空的或只是 "..." 的状态
            if not current_text.strip():
                await asyncio.sleep(check_interval)
                continue
                
            if current_text == last_text:
                stable_count += 1
            else:
                stable_count = 0
                last_text = current_text
                
            # 连续 4 次 (2秒) 内容未变，认为生成结束
            if stable_count >= 4:
                return md(current_text, heading_style="ATX")
                
            await asyncio.sleep(check_interval)
            
        return md(last_text, heading_style="ATX") if last_text else "Error: Timeout waiting for reply."

    async def _get_last_message_content(self) -> str:
        """获取最后一条消息的内容"""
        try:
            # DeepSeek 的消息通常在 div 中，且包含特定的 class 或结构
            # 这里尝试几种策略
            
            # 策略 1: 查找所有可能的 markdown 容器
            # 假设 DeepSeek 使用 markdown 渲染，通常会有 markdown 类
            # 注意：选择器需要根据实际 DOM 调整
            
            # 尝试获取所有非空的 div，且包含文本长度大于 0
            # 这是一个比较宽泛的搜索，可能会包含用户消息
            # 通常 AI 回复在用户消息之后
            
            # 我们可以假设 AI 的回复是最后一个包含大量文本的块
            # 或者更准确地，查找最后一条非用户消息
            
            # 这里的选择器是推测性的，基于常见的 Chat UI 结构
            # 1. 尝试找最后一个 markdown 块
            elements = await self.page.locator(".ds-markdown, .markdown-body").all()
            if elements:
                return await elements[-1].inner_html()
            
            # 2. 兜底：获取最后一个主要文本容器
            # 排除输入框、侧边栏等
            # 查找所有段落或 div
            # 这是一个非常粗略的实现
            content = await self.page.evaluate("""
                () => {
                    // 获取所有包含文本的 div
                    const divs = Array.from(document.querySelectorAll('div'));
                    // 过滤出可能是消息气泡的元素 (排除太短的或输入框相关的)
                    const candidates = divs.filter(d => {
                        const text = d.innerText;
                        return text && text.length > 5 && !d.querySelector('textarea');
                    });
                    if (candidates.length > 0) {
                        return candidates[candidates.length - 1].innerHTML;
                    }
                    return "";
                }
            """)
            return content
            
        except Exception as e:
            logger.warning(f"获取最后一条消息失败: {e}")
            return ""
