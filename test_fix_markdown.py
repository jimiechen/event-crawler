#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的Markdown生成功能
"""

import logging
import os
import sys

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_html_to_markdown():
    """测试修复后的HTML转Markdown功能"""
    logger.info("开始测试修复后的HTML转Markdown功能")
    
    try:
        # 添加项目根目录到Python路径
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'apps', 'stock-monitor-backend'))
        
        # 导入必要的库
        from bs4 import BeautifulSoup
        import re
        import hashlib
        import time
        
        # 模拟修复后的html_to_markdown方法
        def html_to_markdown(html_content: str) -> str:
            try:
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
        
        # 测试1: 使用之前保存的北单页面HTML
        logger.info("测试1: 使用之前保存的北单页面HTML")
        
        # 读取北单页面的HTML文件
        html_file = "/Users/mac/StudioProjects/2026/open-citycloud-workspace/python/event-crawler/data/okooo/raw_html/2026-01-26/1320761_72b892b0c5950c0e7103d1f876c6a03b_1769436885.html"
        
        if os.path.exists(html_file):
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            logger.info(f"读取HTML文件，长度: {len(html_content)} 字符")
            
            # 转换为Markdown
            md_content = html_to_markdown(html_content)
            logger.info(f"Markdown转换完成，长度: {len(md_content)} 字符")
            
            if md_content:
                logger.info(f"Markdown内容:\n{md_content[:500]}...")
                # 保存修复后的Markdown文件
                save_path = "/Users/mac/StudioProjects/2026/open-citycloud-workspace/python/event-crawler/data/okooo/markdown/2026-01-26/test_fix.md"
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(f"# 澳客竞彩页面\n\n")
                    f.write(f"**测试URL**: https://m.okooo.com/bjdc/\n\n")
                    f.write(f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\n\n")
                    f.write(md_content)
                logger.info(f"修复后的Markdown已保存到: {save_path}")
            else:
                logger.error("Markdown转换结果为空")
        else:
            logger.error(f"HTML文件不存在: {html_file}")
        
        # 测试2: 使用包含不同比赛编号格式的HTML
        logger.info("\n测试2: 使用包含不同比赛编号格式的HTML")
        
        # 创建测试HTML内容，包含日001、北001、周001等不同格式的比赛编号
        test_html = """
        <html>
        <body>
            <div class="match-container">
                <div class="match-item">日001 澳超 西悉尼 1-0 珀斯光 0 胜 1.82 平 3.70 负 3.25 -1 胜 3.50 平 3.65 负 1.76</div>
                <div class="match-item">北001 英超 曼城 2-1 利物浦 0 胜 1.65 平 3.80 负 4.20 -1 胜 3.20 平 3.50 负 1.90</div>
                <div class="match-item">周001 德甲 拜仁 3-0 多特蒙德 0 胜 1.35 平 4.80 负 7.50 -2 胜 2.65 平 4.20 负 2.20</div>
            </div>
        </body>
        </html>
        """
        
        md_content = html_to_markdown(test_html)
        logger.info(f"测试HTML转换的Markdown内容:\n{md_content}")
        
        # 测试3: 使用空内容测试备选方案
        logger.info("\n测试3: 使用空内容测试备选方案")
        
        empty_html = "<html><body><div class='match-container'>没有比赛数据</div></body></html>"
        md_content = html_to_markdown(empty_html)
        logger.info(f"空内容HTML转换的Markdown内容: '{md_content}'")
        
        logger.info("HTML转Markdown功能测试完成")
        
    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_html_to_markdown()