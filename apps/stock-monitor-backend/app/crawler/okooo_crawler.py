#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
澳客爬虫
基于Playwright实现，支持Cookie注入和数据抓取
"""

import asyncio
import logging
import json
import random
import re
import time
import os
import urllib.parse
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Page, BrowserContext
from sqlalchemy.ext.asyncio import AsyncSession

# 导入爬虫基类
from app.crawler.base import CrawlerBase

# 添加环境变量支持
from dotenv import load_dotenv
# 添加HTML转Markdown支持
from markdownify import markdownify
# 添加哈希生成支持
import hashlib

# 加载.env文件
load_dotenv()

logger = logging.getLogger(__name__)

class OkoooCrawler(CrawlerBase):
    def __init__(self, db: AsyncSession):
        super().__init__(db, 'okooo')
        # 澳客竞彩页面URL
        self.base_url = "https://www.okooo.com/jingcai/"
        # 从环境变量获取Markdown保存路径，默认为当前目录下的markdown目录
        self.markdown_save_path = os.getenv("MARKDOWN_SAVE_PATH", os.path.join(os.getcwd(), "markdown"))
        
    async def crawl(self, *args, **kwargs) -> Dict[str, Any]:
        """
        爬取方法（实现基类抽象方法）
        """
        return await self.fetch_and_parse(*args, **kwargs)

    def generate_english_identifier(self, url: str) -> str:
        """
        生成URL的英文标识（使用MD5哈希）
        :param url: 要生成标识的URL
        :return: URL的MD5哈希值作为英文标识
        """
        # 使用MD5哈希算法生成URL的唯一标识
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        return url_hash
    
    def html_to_markdown(self, html_content: str) -> str:
        """
        将HTML转换为Markdown格式，使用逗号分隔
        :param html_content: HTML内容
        :return: 转换后的Markdown内容
        """
        try:
            # 使用BeautifulSoup清理HTML结构，移除所有脚本、样式和不需要的标签
            from bs4 import BeautifulSoup
            
            # 解析HTML
            soup = BeautifulSoup(html_content, 'lxml')
            
            # 移除所有脚本和样式标签
            for tag in soup(['script', 'style', 'noscript', 'iframe', 'link', 'meta', 'title', 'head', 'nav', 'footer', 'header']):
                tag.decompose()
            
            # 移除注释
            for comment in soup.find_all(string=lambda text: isinstance(text, str) and text.strip() == ''):
                comment.decompose()
            
            # 获取清理后的文本内容
            text_content = soup.get_text(separator=' ', strip=True)
            
            # 清理多余的空白字符
            cleaned_text = re.sub(r'\s+', ' ', text_content)
            
            # 将文本内容转换为逗号分隔的格式
            # 1. 按比赛编号分割内容，匹配多种比赛编号格式（日001、北001、周001等）
            match_parts = re.split(r'([\u4e00-\u9fa5]\d{3})', cleaned_text)
            
            # 2. 处理每个比赛项目
            match_lines = []
            for i in range(1, len(match_parts), 2):
                if i + 1 < len(match_parts):
                    match_id = match_parts[i]
                    match_info = match_parts[i+1].strip()
                    
                    # 确保匹配到的是有效的比赛编号
                    if len(match_id) == 4 and re.search(r'\d{3}$', match_id):
                        # 3. 将比赛信息转换为逗号分隔格式
                        # 替换空格为逗号，但保留比分、赔率等关键信息的格式
                        formatted_info = match_info
                        
                        # 处理比分，确保格式正确
                        formatted_info = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1-\2', formatted_info)
                        
                        # 处理赔率，确保格式正确
                        formatted_info = re.sub(r'(胜|平|负)\s+(\d+\.\d+)', r'\1 \2', formatted_info)
                        
                        # 处理让球，确保格式正确，并添加逗号分隔
                        formatted_info = re.sub(r'(\d+\.\d+)([-+]\d+)', r'\1,\2', formatted_info)
                        formatted_info = re.sub(r'(\+|-)\s*(\d+)', r'\1\2', formatted_info)
                        
                        # 替换空格为逗号，实现单行逗号分隔
                        formatted_info = re.sub(r'\s+', ',', formatted_info)
                        
                        # 4. 组合比赛编号和信息
                        match_line = f"{match_id},{formatted_info}"
                        match_lines.append(match_line)
            
            # 如果没有匹配到比赛项目，尝试直接提取文本内容
            if not match_lines:
                logger.info("没有匹配到比赛项目，直接返回清理后的文本内容")
                # 移除多余的空白字符，保留基本结构
                formatted_info = re.sub(r'\s+', ' ', cleaned_text)
                return formatted_info
            
            # 5. 组合成最终的Markdown内容
            final_md = '\n'.join(match_lines)
            
            # 移除连续的逗号
            final_md = re.sub(r',{2,}', ',', final_md)
            
            # 移除开头和结尾的空白
            final_md = final_md.strip()
            
            return final_md
        except Exception as e:
            logger.error(f"HTML to Markdown conversion failed: {e}")
            return ""

    
    def save_raw_html(self, html_content: str, match_id: str, url: str) -> str:
        """
        保存原始HTML内容到本地文件，按日期存档
        :param html_content: 原始HTML内容
        :param match_id: 比赛ID
        :param url: 原始URL
        :return: 保存的文件路径
        """
        try:
            # 获取当前日期，用于创建目录
            current_date = time.strftime('%Y-%m-%d', time.localtime())
            
            # 构建保存路径：BASE_PATH/raw_html/YYYY-MM-DD/
            raw_html_path = os.path.join(self.markdown_save_path, "raw_html", current_date)
            os.makedirs(raw_html_path, exist_ok=True)
            
            # 生成文件名：matchid_identifier.html
            timestamp = int(time.time())
            identifier = self.generate_english_identifier(url)
            filename = f"{match_id}_{identifier}_{timestamp}.html"
            file_path = os.path.join(raw_html_path, filename)
            
            # 修复编码声明，防止乱码 (Mojibake)
            # 替换 <meta charset="GBK"> 或类似的声明为 utf-8
            fixed_content = re.sub(r'<meta[^>]*charset=["\']?gbk["\']?[^>]*>', '<meta charset="utf-8">', html_content, flags=re.IGNORECASE)
            # 也可以处理 gb2312 等
            fixed_content = re.sub(r'charset=["\']?gb2312["\']?', 'charset="utf-8"', fixed_content, flags=re.IGNORECASE)
            
            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)
            
            logger.info(f"原始HTML文件已保存到: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"保存原始HTML文件失败: {e}")
            return None
    
    def save_markdown(self, md_content: str, match_id: str, identifier: str, url: str) -> str:
        """
        保存Markdown内容到本地文件，按日期存档
        :param md_content: Markdown内容
        :param match_id: 比赛ID，作为文件名第一位
        :param identifier: 英文标识
        :param url: 原始URL
        :return: 保存的文件路径
        """
        try:
            # 获取当前日期，用于创建目录
            current_date = time.strftime('%Y-%m-%d', time.localtime())
            
            # 构建保存路径：BASE_PATH/markdown/YYYY-MM-DD/
            markdown_path = os.path.join(self.markdown_save_path, "markdown", current_date)
            os.makedirs(markdown_path, exist_ok=True)
            
            # 生成文件名：matchid_identifier.md
            timestamp = int(time.time())
            filename = f"{match_id}_{identifier}_{timestamp}.md"
            file_path = os.path.join(markdown_path, filename)
            
            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                # 添加URL和生成时间作为文件头部
                f.write(f"# 澳客竞彩页面\n\n")
                f.write(f"**原始URL**: {url}\n\n")
                f.write(f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\n\n")
                f.write(md_content)
            
            logger.info(f"Markdown文件已保存到: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"保存Markdown文件失败: {e}")
            return None

    async def fetch_and_parse(self, query: str = None, batch_name: str = None, debug_url: str = None) -> Dict[str, Any]:
        """
        执行抓取并解析
        :param query: 搜索条件
        :param batch_name: 批次名称
        :param debug_url: 调试URL，如果提供则直接访问该URL
        """
        # 构建访问URL
        if debug_url:
            current_url = debug_url
        else:
            current_url = self.base_url
            if query:
                current_url = f"{self.base_url}?w={urllib.parse.quote(query)}"
        
        html_content = await self.fetch_page_source(query, debug_url=debug_url)
        
        if not html_content:
            logger.error("Failed to fetch page content")
            return {"status": "failed", "error": "Fetch failed"}

        # 创建批次名称
        if not batch_name:
            import datetime
            batch_name = f"OkoooCrawl_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 解析页面内容
        parsed_data = self.parse_page_content(html_content)
        
        # 生成英文标识
        english_identifier = self.generate_english_identifier(current_url)
        logger.info(f"Generated English identifier for URL {current_url}: {english_identifier}")
        
        # 添加英文标识到解析数据
        for item in parsed_data:
            item["english_identifier"] = english_identifier
        
        # 提取match_id，用于文件名
        match_id = "default"
        
        # 0. 优先从 URL 中提取 MatchID
        # 支持两种格式: ?MatchID=123456 或 /match/123456/
        url_match = re.search(r'(?:MatchID=|/match/)(\d+)', current_url, re.IGNORECASE)
        if url_match:
            match_id = url_match.group(1)
        # 1. 从解析数据中获取第一个match_id (Fallback)
        elif parsed_data and "match_id" in parsed_data[0]:
            match_id = parsed_data[0]["match_id"]
        else:
            # 2. 尝试从HTML内容中提取match_id (Last resort)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'lxml')
            match_link = soup.find('a', href=lambda href: href and 'MatchID=' in href)
            if match_link:
                match_id_match = re.search(r'MatchID=(\d+)', match_link.get('href', ''))
                if match_id_match:
                    match_id = match_id_match.group(1)
        
        logger.info(f"Using match_id for file naming: {match_id}")
        
        # 保存原始HTML文件
        raw_html_path = self.save_raw_html(html_content, match_id, current_url)
        
        # 将HTML转换为Markdown
        md_content = self.html_to_markdown(html_content)
        
        # 保存Markdown文件，使用match_id作为文件名第一位
        markdown_file_path = self.save_markdown(md_content, match_id, english_identifier, current_url)
        
        return {
            "status": "success",
            "batch_name": batch_name,
            "total": len(parsed_data),
            "data": parsed_data,
            "match_id": match_id,
            "english_identifier": english_identifier,
            "raw_html_path": raw_html_path,
            "markdown_file_path": markdown_file_path
        }

    async def fetch_page_source(self, query: str = None, debug_url: str = None) -> Optional[str]:
        """
        使用Playwright获取页面源码
        :param query: 搜索条件
        :param debug_url: 调试URL，如果提供则直接访问该URL
        """
        context = None
        browser = None
        
        try:
            # 使用基类方法创建浏览器上下文
            context, session, browser = await self.create_browser_context()
            page = await context.new_page()
            
            # 打印当前Cookie信息（调试功能）
            cookies = await context.cookies()
            logger.info(f"========== 调试信息：当前Cookie ==========")
            for cookie in cookies:
                logger.info(f"  {cookie['name']}: {cookie['value'][:50]}..." if len(cookie['value']) > 50 else f"  {cookie['name']}: {cookie['value']}")
            logger.info(f"========== 共 {len(cookies)} 个Cookie ==========")
            
            # 如果提供了debug_url，直接访问
            if debug_url:
                logger.info(f"使用调试URL: {debug_url}")
                logger.info(f"导航到URL: {debug_url}, 等待条件: domcontentloaded, 超时时间: 60000ms")
                await page.goto(debug_url, wait_until='domcontentloaded', timeout=60000)
            else:
                # 访问澳客竞彩页面
                url = self.base_url
                if query:
                    url = f"{self.base_url}?w={urllib.parse.quote(query)}"
                logger.info(f"访问URL: {url}")
                logger.info(f"导航到URL: {url}, 等待条件: domcontentloaded, 超时时间: 60000ms")
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            # 等待页面加载
            await asyncio.sleep(5)
            
            # 生成截图
            screenshot_name = f"debug_okooo_{int(time.time())}.png"
            screenshot_path = os.path.abspath(screenshot_name)
            await page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"截图已保存到: {screenshot_path}")
            
            # 获取页面内容
            content = await page.content()
            
            logger.info(f"Page content length: {len(content)} characters")
            
            # 保存HTML用于调试，方便分析反爬问题
            debug_html_name = f"debug_okooo_content_{int(time.time())}.html"
            debug_html_path = os.path.abspath(debug_html_name)
            with open(debug_html_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"HTML内容已保存到: {debug_html_path}")
            
            # 反爬检查 - 针对移动端页面调整检查逻辑
            has_robot = "robot" in content.lower()
            has_captcha = "验证码" in content
            has_okooo = "okooo" in content.lower()
            
            logger.info(f"Anti-crawler check results - robot: {has_robot}, captcha: {has_captcha}, has_okooo: {has_okooo}")
            
            # 调整反爬检查逻辑：如果页面包含okooo标识，即使有robot字样，也可能是正常页面
            # 只在确实检测到验证码或完全不包含okooo标识时才判断为反爬
            if has_captcha or (not has_okooo and has_robot):
                logger.warning("Detected anti-crawler mechanism")
                logger.debug(f"Anti-crawler content snippet: {content[:1000]}")
                return None
            elif has_robot:
                logger.info("Found 'robot' in content but page appears to be legitimate (contains 'okooo'), continuing...")
            
            # 同步最新的Cookies回数据库
            await self.sync_session(context, session)

            return content
            
        except Exception as e:
            logger.error(f"Playwright error: {e}")
            return None
        finally:
            # 清理资源
            if context:
                await context.close()
            if browser:
                await browser.close()

    def parse_page_content(self, html_content: str) -> List[Dict[str, Any]]:
        """
        解析澳客页面内容
        :param html_content: 页面HTML内容
        :return: 解析后的数据列表
        """
        parsed_data = []
        
        try:
            from bs4 import BeautifulSoup
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'lxml')
            
            # 查找所有包含MatchID的链接，这些链接指向比赛详情页
            match_links = soup.find_all('a', href=lambda href: href and '/match/history.php?MatchID=' in href)
            
            logger.info(f"Found {len(match_links)} match links")
            
            # 提取MatchID的正则表达式
            match_id_pattern = re.compile(r'MatchID=(\d+)')
            
            # 查找所有比赛行元素
            # 假设比赛信息在tr或div标签中，包含比赛相关信息
            match_elements = soup.find_all(['tr', 'div'], class_=re.compile(r'.*match.*|.*game.*|.*event.*'))
            
            logger.info(f"Found {len(match_elements)} potential match elements")
            
            # 首先提取所有MatchID
            match_ids = []
            for link in match_links:
                href = link.get('href', '')
                match = match_id_pattern.search(href)
                if match:
                    match_id = match.group(1)
                    if match_id not in match_ids:
                        match_ids.append(match_id)
            
            logger.info(f"Extracted {len(match_ids)} unique match IDs")
            
            # 提取比赛信息，包括队伍名称、比分等
            # 使用正则表达式直接从HTML中提取所有比赛相关信息
            # 查找包含比赛比分的模式，例如 "*西悉尼* 1-0 *珀斯光*"
            score_pattern = re.compile(r'\*([^\*]+)\*\s*(\d+-\d+|VS)\s*\*([^\*]+)\*')
            matches_with_scores = score_pattern.findall(html_content)
            
            logger.info(f"Found {len(matches_with_scores)} matches with scores")
            
            # 合并MatchID和比赛信息
            for i, (home_team, score, away_team) in enumerate(matches_with_scores):
                match_data = {
                    "match_id": match_ids[i] if i < len(match_ids) else f"unknown_{i}",
                    "home_team": home_team.strip(),
                    "score": score.strip(),
                    "away_team": away_team.strip(),
                    "english_identifier": ""
                }
                parsed_data.append(match_data)
            
            # 如果没有通过上述方式提取到数据，尝试另一种方式
            if not parsed_data:
                # 直接从HTML中提取所有MatchID
                all_match_ids = match_id_pattern.findall(html_content)
                logger.info(f"Directly extracted {len(all_match_ids)} match IDs")
                
                # 去重
                unique_match_ids = list(set(all_match_ids))
                logger.info(f"Unique match IDs: {len(unique_match_ids)}")
                
                # 为每个MatchID创建一个基本的数据条目
                for match_id in unique_match_ids:
                    parsed_data.append({
                        "match_id": match_id,
                        "english_identifier": ""
                    })
            
            if not parsed_data:
                logger.warning("No match data parsed from page content. Possibly page structure changed.")
                # 保存HTML用于调试
                with open("debug_okooo.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info("Saved failed HTML to debug_okooo.html")
            else:
                logger.info(f"Successfully parsed {len(parsed_data)} match records")
                # 打印前3条记录用于调试
                for i, record in enumerate(parsed_data[:3]):
                    logger.debug(f"Match record {i+1}: {record}")
            
        except Exception as e:
            logger.error(f"Error parsing page content: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        return parsed_data

    async def check_login_status(self, url: str = None, nickname_xpath: str = None) -> Dict[str, Any]:
        """
        检查澳客登录状态
        """
        context = None
        session = None
        browser = None
        
        try:
            platform_config = await self.get_platform_config()
            if not platform_config:
                return {"logged_in": False, "message": "平台配置不存在"}
            
            # 使用默认URL或提供的URL
            check_url = url or self.base_url
            
            # 创建浏览器上下文
            context, session, browser = await self.create_browser_context()
            page = await context.new_page()
            
            try:
                # 访问检查URL
                await page.goto(check_url, wait_until='networkidle', timeout=30000)
                
                # 根据页面特征判断登录状态
                # 澳客公开数据不需要登录，所以这里简单检查页面是否正常加载
                page_title = await page.title()
                
                if "okooo" in page_title.lower():
                    # 更新会话验证状态
                    if session and session.get('id'):
                        await self.session_service.verify_session(session['id'], True)
                    
                    return {
                        "logged_in": True,
                        "message": "登录成功",
                        "nickname": "Guest User"  # 澳客公开数据不需要登录
                    }
                else:
                    # 更新会话验证状态
                    if session and session.get('id'):
                        await self.session_service.verify_session(session['id'], False)
                    
                    return {
                        "logged_in": False,
                        "message": "未检测到登录状态"
                    }
            
            except Exception as e:
                logger.error(f"登录状态检查失败: {e}")
                return {
                    "logged_in": False,
                    "message": f"检查失败: {str(e)}"
                }
            finally:
                if browser:
                    await browser.close()
        
        except Exception as e:
            logger.error(f"登录状态检查异常: {e}")
            return {
                "logged_in": False,
                "message": f"检查异常: {str(e)}"
            }
