#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试澳客爬虫的按日期存档功能
"""

import logging
import os
import sys
import asyncio

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 模拟数据库会话类
class MockDBSession:
    def execute(self, *args, **kwargs):
        return self
    
    async def commit(self):
        pass
    
    async def close(self):
        pass

async def test_archive_function():
    """测试按日期存档功能"""
    logger.info("开始测试澳客爬虫的按日期存档功能")
    
    try:
        # 添加项目根目录到Python路径
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'apps', 'stock-monitor-backend'))
        
        # 导入爬虫类
        from app.crawler.okooo_crawler import OkoooCrawler
        
        # 创建模拟数据库会话
        mock_db = MockDBSession()
        
        # 初始化爬虫
        crawler = OkoooCrawler(mock_db)
        
        # 测试1: 测试save_raw_html方法
        logger.info("测试1: 测试save_raw_html方法")
        
        # 创建测试HTML内容
        test_html = """
        <html>
        <body>
            <div class="match-container">
                <div class="match-item">
                    <a href="/match/history.php?MatchID=123456" class="match-link">日001 澳超 西悉尼 1-0 珀斯光</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        test_url = "https://www.okooo.com/jingcai/"
        test_match_id = "123456"
        
        # 测试保存原始HTML
        raw_html_path = crawler.save_raw_html(test_html, test_match_id, test_url)
        logger.info(f"保存原始HTML的路径: {raw_html_path}")
        
        # 验证文件是否存在
        if os.path.exists(raw_html_path):
            logger.info(f"原始HTML文件已成功保存: {raw_html_path}")
            # 检查文件名格式
            filename = os.path.basename(raw_html_path)
            logger.info(f"原始HTML文件名: {filename}")
            # 检查文件名是否以matchid开头
            if filename.startswith(f"{test_match_id}_"):
                logger.info(f"原始HTML文件名正确，以matchid开头")
            else:
                logger.warning(f"原始HTML文件名不以matchid开头")
        else:
            logger.error(f"原始HTML文件保存失败")
        
        # 测试2: 测试save_markdown方法
        logger.info("\n测试2: 测试save_markdown方法")
        
        # 创建测试Markdown内容
        test_md = "日001,澳超,西悉尼,1-0,珀斯光,胜,1.82,平,3.70,负,3.25,-1,胜,3.50,平,3.65,负,1.76"
        
        # 生成英文标识
        identifier = crawler.generate_english_identifier(test_url)
        
        # 测试保存Markdown
        markdown_path = crawler.save_markdown(test_md, test_match_id, identifier, test_url)
        logger.info(f"保存Markdown的路径: {markdown_path}")
        
        # 验证文件是否存在
        if os.path.exists(markdown_path):
            logger.info(f"Markdown文件已成功保存: {markdown_path}")
            # 检查文件名格式
            filename = os.path.basename(markdown_path)
            logger.info(f"Markdown文件名: {filename}")
            # 检查文件名是否以matchid开头
            if filename.startswith(f"{test_match_id}_"):
                logger.info(f"Markdown文件名正确，以matchid开头")
            else:
                logger.warning(f"Markdown文件名不以matchid开头")
        else:
            logger.error(f"Markdown文件保存失败")
        
        # 测试3: 测试文件路径结构
        logger.info("\n测试3: 测试文件路径结构")
        
        # 检查路径是否包含日期目录
        if raw_html_path:
            raw_html_dir = os.path.dirname(raw_html_path)
            logger.info(f"原始HTML目录: {raw_html_dir}")
            # 检查目录是否包含raw_html和日期
            if "raw_html" in raw_html_dir:
                logger.info(f"原始HTML目录包含raw_html子目录")
            else:
                logger.warning(f"原始HTML目录不包含raw_html子目录")
        
        if markdown_path:
            markdown_dir = os.path.dirname(markdown_path)
            logger.info(f"Markdown目录: {markdown_dir}")
            # 检查目录是否包含markdown和日期
            if "markdown" in markdown_dir:
                logger.info(f"Markdown目录包含markdown子目录")
            else:
                logger.warning(f"Markdown目录不包含markdown子目录")
        
        logger.info("按日期存档功能测试完成")
        
    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_archive_function())