#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问财数据服务
处理问财数据的解析、存储和查询
"""

import re
import json
import aiofiles
import hashlib
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup
from decimal import Decimal, InvalidOperation
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, bindparam, select
from app.models.stock import WencaiStock, WencaiCrawlBatch

from app.config.logging import get_logger
from .tag_service import TagService
from .tag_management_service import TagManagementService
from .stock_service import StockService
from .local_data_service import LocalDataService
from ..api.tag_schemas import TagCreate, TagUpdate
from app.services.tushare_service import TushareService
from app.database import db_manager
import asyncio

logger = get_logger(__name__)

class WencaiService:
    """问财数据服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tag_mgmt_service = TagManagementService(db)
        self.stock_service = StockService(db)

    async def get_batch_by_name(self, batch_name: str) -> Optional[WencaiCrawlBatch]:
        """
        根据批次名称获取批次信息
        """
        stmt = select(WencaiCrawlBatch).where(WencaiCrawlBatch.batch_name == batch_name).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_stocks_by_batch(self, batch_id: int) -> List[WencaiStock]:
        """
        根据批次ID获取该批次的所有股票
        """
        stmt = select(WencaiStock).where(WencaiStock.crawl_batch_id == str(batch_id))
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def save_stocks(self, stocks: List[Dict[str, Any]], batch_id: int = None) -> None:
        """
        保存爬取到的股票信息到数据库 (StockInfo & WencaiStock)
        并触发基础分计算
        """
        from app.services.volume_analysis_service import VolumeAnalysisService
        
        for stock_data in stocks:
            try:
                stock_code = stock_data.get('stock_code')
                stock_name = stock_data.get('stock_name')
                
                if not stock_code:
                    continue
                    
                # 2. 如果提供了 batch_id，保存到 WencaiStock (爬虫记录)
                if batch_id:
                    # check if exists in current batch
                    stmt = select(WencaiStock).where(
                        WencaiStock.crawl_batch_id == str(batch_id),
                        WencaiStock.stock_code == stock_code
                    )
                    res = await self.db.execute(stmt)
                    if not res.scalar_one_or_none():
                        # Determine is_active status (inherit from previous latest or default to True)
                        prev_stmt = select(WencaiStock.is_active).where(
                            WencaiStock.stock_code == stock_code
                        ).order_by(WencaiStock.id.desc()).limit(1)
                        prev_res = await self.db.execute(prev_stmt)
                        prev_status = prev_res.scalar_one_or_none()
                        is_active = True if prev_status is None else prev_status

                        wencai_stock = WencaiStock(
                            crawl_batch_id=str(batch_id),
                            stock_code=stock_code,
                            stock_name=stock_name,
                            latest_price=stock_data.get('latest_price'),
                            change_percent=stock_data.get('change_percent'),
                            is_active=is_active
                        )
                        self.db.add(wencai_stock)
                
                # 3. 触发基础分计算 (如果是新入库或尚未计算)
                # 无论是否新股，只要上榜问财，就应该检查是否需要计算/更新基础分
                # 这里我们触发一次 "Historical Baseline" 计算，针对 "今天" (或上榜日)
                # 但 VolumeAnalysisService.calculate_historical_baseline 是计算 target_date 的 baseline
                # 我们应该使用当前日期作为 target_date
                
                target_date = date.today()
                # 如果 stock_data 中包含日期 (回溯模式)，使用该日期
                if 'date' in stock_data:
                    if isinstance(stock_data['date'], str):
                        target_date = datetime.strptime(stock_data['date'], "%Y-%m-%d").date()
                    elif isinstance(stock_data['date'], date):
                        target_date = stock_data['date']
                
                # 异步触发计算，或者同步等待？为了数据一致性，建议同步等待或放入队列
                # 这里直接调用，注意性能
                # 只有当没有分数记录时才强制计算基础分? 
                # 用户要求: "问财上榜就入库计算基础分"
                
                # 检查是否已有分数
                from app.models.stock_daily import StockScoreResult
                score_stmt = select(StockScoreResult).where(
                    StockScoreResult.code == stock_code,
                    StockScoreResult.trade_date == target_date
                )
                score_res = await self.db.execute(score_stmt)
                if not score_res.scalar_one_or_none():
                    logger.info(f"Triggering baseline calculation for {stock_code} on {target_date}")
                    # 我们不仅要计算 baseline，还要计算当天的 total_score (baseline + daily)
                    # 但这里我们只负责 "入库计算基础分" (baseline)
                    # 完整的评分逻辑通常由 RuleEngineService 处理
                    # 但为了满足 "First Day" 逻辑，我们需要确保 Baseline 被计算并保存
                    
                    baseline = await VolumeAnalysisService.calculate_historical_baseline(stock_code, target_date, self.db)
                    
                    # 如果有 daily_score (从 volume analysis)，也应该加上
                    # 但这里我们可能没有 daily data loaded yet via Vectorized Engine for just this stock
                    # 简单起见，先保存 baseline 作为 accumulated_score (如果 daily_score 为 0)
                    # 实际上，calculate_historical_baseline 返回的是 "past 250 days sum"
                    # 这就是 accumulated_score 的一部分 (excluding today)
                    
                    # 构造 StockScoreResult
                    # 注意：calculate_historical_baseline 内部其实没有保存 StockScoreResult，它只是返回数值
                    # 我们需要保存它
                    
                    new_score = StockScoreResult(
                        code=stock_code,
                        trade_date=target_date,
                        accumulated_score=baseline,
                        total_score=baseline, # Compat
                        daily_score=0, # 暂无今日动态分
                        pool_type='wencai'
                    )
                    self.db.add(new_score)
                    
            except Exception as e:
                logger.error(f"Error saving stock {stock_data.get('stock_code')}: {e}")
        
        await self.db.commit()

    def parse_html_table(self, html_content: str, debug: bool = False) -> List[Dict[str, Any]]:
        """
        解析问财HTML表格数据
        
        Args:
            html_content: 问财页面HTML内容
            debug: 是否输出详细调试信息
            
        Returns:
            解析后的股票数据列表
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            if debug:
                logger.info(f"HTML内容长度: {len(html_content)} 字符")
                logger.info(f"HTML前500字符: {html_content[:500]}")
            
            # 首先尝试查找标准的table结构
            tables = soup.find_all('table')
            if debug:
                logger.info(f"找到 {len(tables)} 个标准table元素")
            
            # 如果找到标准table，尝试使用原有逻辑
            if tables:
                standard_result = self._parse_standard_table(soup, debug)
                if standard_result:  # 如果标准表格解析有结果，返回
                    return standard_result
            
            # 如果没有标准table或标准table解析无结果，尝试解析问财的div-based表格结构
            if debug:
                logger.info("尝试解析问财div-based表格结构")
            
            return self._parse_wencai_div_table(soup, debug)
            
        except Exception as e:
            logger.error(f"解析HTML表格失败: {e}")
            return []
    
    def _parse_standard_table(self, soup, debug: bool = False) -> List[Dict[str, Any]]:
        """解析标准HTML table结构"""
        table = soup.find('table')
        if not table:
            return []
        
        # 获取表头
        headers = []
        header_row = table.find('tr')
        if header_row:
            for th in header_row.find_all(['th', 'td']):
                headers.append(th.get_text(strip=True))
        
        if not headers:
            if debug:
                logger.warning("未找到表头")
            return []
        
        if debug:
            logger.info(f"找到表头: {headers}")
        
        # 解析数据行
        parsed_data = []
        rows = table.find_all('tr')[1:]  # 跳过表头
        
        for row_idx, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            if len(cells) < len(headers):
                continue
            
            try:
                row_data = {}
                for i, cell in enumerate(cells[:len(headers)]):
                    if i < len(headers):
                        cell_text = cell.get_text(strip=True)
                        row_data[headers[i]] = cell_text
                
                stock_data = self._convert_row_data(row_data)
                if stock_data:
                    parsed_data.append(stock_data)
                        
            except Exception as e:
                if debug:
                    logger.warning(f"解析第{row_idx + 1}行数据失败: {e}")
                continue
        
        return parsed_data
    
    def _parse_wencai_div_table(self, soup, debug: bool = False) -> List[Dict[str, Any]]:
        """解析问财的div-based表格结构"""
        # 查找包含股票数据的行
        data_rows = soup.find_all('tr', {'data-v-41d36628': True})
        
        if debug:
            logger.info(f"找到 {len(data_rows)} 个数据行")
        
        if not data_rows:
            # 尝试其他可能的选择器
            data_rows = soup.find_all('tr')
            if debug:
                logger.info(f"使用通用tr选择器找到 {len(data_rows)} 个行")
        
        parsed_data = []
        
        for row_idx, row in enumerate(data_rows):
            try:
                # 查找所有td元素
                cells = row.find_all('td')
                
                if len(cells) < 5:  # 至少需要5个单元格才可能是有效的股票数据行
                    continue
                
                if debug and row_idx < 3:
                    logger.info(f"第{row_idx + 1}行有 {len(cells)} 个单元格")
                
                # 提取股票数据
                stock_data = self._extract_wencai_stock_data(cells, row_idx, debug)
                
                if stock_data:
                    # 添加原始HTML数据
                    stock_data['raw_data'] = str(row)
                    parsed_data.append(stock_data)
                    if debug and row_idx < 3:
                        logger.info(f"第{row_idx + 1}行解析成功: {stock_data}")
                
            except Exception as e:
                if debug:
                    logger.warning(f"解析第{row_idx + 1}行失败: {e}")
                continue
        
        logger.info(f"成功解析 {len(parsed_data)} 条股票数据")
        return parsed_data
    
    def _extract_wencai_stock_data(self, cells, row_idx: int, debug: bool = False) -> Optional[Dict[str, Any]]:
        """从问财表格行中提取股票数据"""
        try:
            if len(cells) < 5:
                return None
            
            # 根据实际HTML结构提取数据
            # 跳过序号和复选框列，从第3列开始是股票代码
            stock_code = None
            stock_name = None
            current_price = None
            change_percent = None
            turnover = None
            volume = None
            concept = None
            industry = None
            
            # 查找股票代码（通常是6位数字）
            for i, cell in enumerate(cells):
                cell_text = cell.get_text(strip=True)
                
                # 股票代码模式：6位数字
                if re.match(r'^\d{6}$', cell_text):
                    stock_code = cell_text
                    
                    # 股票名称通常在股票代码的下一列
                    if i + 1 < len(cells):
                        name_cell = cells[i + 1]
                        # 查找链接文本作为股票名称
                        name_link = name_cell.find('a')
                        if name_link:
                            stock_name = name_link.get_text(strip=True)
                        else:
                            stock_name = name_cell.get_text(strip=True)
                    
                    # 价格信息通常在股票名称后面的几列
                    if i + 2 < len(cells):
                        price_cell = cells[i + 2]
                        price_text = price_cell.get_text(strip=True)
                        if re.match(r'^\d+\.?\d*$', price_text):
                            current_price = price_text
                    
                    # 涨跌幅
                    if i + 3 < len(cells):
                        change_cell = cells[i + 3]
                        change_text = change_cell.get_text(strip=True)
                        if '%' in change_text or '+' in change_text or '-' in change_text:
                            change_percent = change_text

                    # 概念 (通常在第8列，即i+5)
                    if i + 5 < len(cells):
                        concept_cell = cells[i + 5]
                        concept_text = concept_cell.get_text(strip=True)
                        # 简单的验证：概念通常包含【】或;
                        if '【' in concept_text or ';' in concept_text:
                            concept = concept_text
                    
                    # 行业 (通常在最后一列)
                    if len(cells) > 0:
                        industry_text = cells[-1].get_text(strip=True)
                        if '-' in industry_text:
                            industry = industry_text

                    # 尝试查找成交量和成交额 (根据调试文件，可能在i+12和i+13)
                    # 简单的启发式搜索：寻找带有"万"或"亿"的数字
                    found_vol_turn = False
                    for j in range(i + 6, len(cells)):
                        txt = cells[j].get_text(strip=True)
                        if ('万' in txt or '亿' in txt) and re.match(r'^[\d\.,]+[万亿]$', txt):
                            if not volume:
                                volume = txt
                            elif not turnover:
                                turnover = txt
                                found_vol_turn = True
                                break
                    
                    # 如果没找到，回退到旧逻辑(虽然可能不准确)
                    if not found_vol_turn:
                        # 成交量
                        if i + 4 < len(cells):
                            volume_cell = cells[i + 4]
                            volume_text = volume_cell.get_text(strip=True)
                            if volume_text and volume_text != '--':
                                # 只有当它看起来像成交量时才使用(不包含概念文本)
                                if not ('【' in volume_text or ';' in volume_text):
                                    volume = volume_text
                        
                        # 成交额
                        if i + 5 < len(cells):
                            turnover_cell = cells[i + 5]
                            turnover_text = turnover_cell.get_text(strip=True)
                            if turnover_text and turnover_text != '--':
                                if not ('【' in turnover_text or ';' in turnover_text):
                                    turnover = turnover_text
                    
                    break  # 找到股票代码后退出循环
            
            # 如果没有找到股票代码，尝试按位置提取
            if not stock_code and len(cells) >= 5:
                # 假设第3列是股票代码，第4列是股票名称
                if len(cells) > 2:
                    potential_code = cells[2].get_text(strip=True)
                    if re.match(r'^\d{6}$', potential_code):
                        stock_code = potential_code
                        
                        if len(cells) > 3:
                            name_cell = cells[3]
                            name_link = name_cell.find('a')
                            if name_link:
                                stock_name = name_link.get_text(strip=True)
                            else:
                                stock_name = name_cell.get_text(strip=True)
                        
                        if len(cells) > 4:
                            price_text = cells[4].get_text(strip=True)
                            if re.match(r'^\d+\.?\d*$', price_text):
                                current_price = price_text
                        
                        if len(cells) > 5:
                            change_text = cells[5].get_text(strip=True)
                            if '%' in change_text or '+' in change_text or '-' in change_text:
                                change_percent = change_text
            
            if debug:
                logger.info(f"行 {row_idx}: 股票代码={stock_code}, 名称={stock_name}, 价格={current_price}, 涨跌幅={change_percent}")
            
            # 验证必要字段
            if not stock_code or not stock_name:
                if debug:
                    logger.warning(f"行 {row_idx}: 缺少必要字段 - 代码: {stock_code}, 名称: {stock_name}")
                return None
            
            return {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'current_price': self._parse_decimal(current_price) if current_price else None,
                'price_change': None,  # 涨跌额，暂时设为None
                'price_change_percent': self._parse_decimal(change_percent) if change_percent else None,
                'volume': self._parse_volume(volume) if volume else None,
                'turnover': self._parse_decimal(turnover) if turnover else None,
                'amplitude': None,
                'highest_price': None,
                'lowest_price': None,
                'opening_price': None,
                'previous_close': None,
                'volume_ratio': None,
                'turnover_rate': None,
                'pe_ratio': None,
                'pb_ratio': None,
                'total_market_value': None,
                'circulating_market_value': None,
                'speed_60_days': None,
                'speed_year_to_date': None,
                'company_address': None,
                'business_scope': None,
                'concept': concept,
                'industry': industry
            }
            
        except Exception as e:
            if debug:
                logger.error(f"提取股票数据时出错 (行 {row_idx}): {str(e)}")
            return None
    
    def _convert_row_data(self, row_data: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        转换行数据为标准格式
        
        Args:
            row_data: 原始行数据
            
        Returns:
            标准格式的股票数据
        """
        try:
            # 字段映射关系
            field_mapping = {
                '股票代码': 'stock_code',
                '股票简称': 'stock_name',
                '现价': 'current_price',
                '涨跌额': 'price_change',
                '涨跌幅': 'price_change_percent',
                '成交量': 'volume',
                '成交额': 'turnover',
                '振幅': 'amplitude',
                '最高': 'highest_price',
                '最低': 'lowest_price',
                '今开': 'opening_price',
                '昨收': 'previous_close',
                '量比': 'volume_ratio',
                '换手率': 'turnover_rate',
                '市盈率-动态': 'pe_ratio',
                '市盈率(动态)': 'pe_ratio',
                '市净率': 'pb_ratio',
                '总市值': 'total_market_value',
                '流通市值': 'circulating_market_value',
                '60日涨跌幅': 'speed_60_days',
                '年初至今涨跌幅': 'speed_year_to_date',
                '净资产收益率': 'roe',
                '毛利率': 'gross_profit_margin',
                '净利润增长率': 'net_profit_growth_rate',
                '营业收入增长率': 'revenue_growth_rate',
                '公司地址': 'company_address',
                '主营业务': 'business_scope',
                '经营范围': 'business_scope'
            }
            
            converted_data = {}
            
            # 转换字段
            for original_field, standard_field in field_mapping.items():
                value = row_data.get(original_field, '')
                
                if not value or value == '--' or value == '-':
                    converted_data[standard_field] = None
                    continue
                
                # 根据字段类型进行转换
                if standard_field in ['stock_code', 'stock_name', 'company_address', 'business_scope']:
                    # 字符串字段
                    converted_data[standard_field] = value
                elif standard_field == 'volume':
                    # 成交量字段（整数）
                    converted_data[standard_field] = self._parse_volume(value)
                else:
                    # 数值字段
                    converted_data[standard_field] = self._parse_decimal(value)
            
            # 验证必需字段
            if not converted_data.get('stock_code') or not converted_data.get('stock_name'):
                logger.warning(f"缺少必需字段: {converted_data}")
                return None
            
            # 验证股票代码格式
            stock_code = converted_data.get('stock_code', '')
            if not re.match(r'^\d{6}$', stock_code):
                logger.warning(f"股票代码格式无效: {stock_code}")
                return None
            
            # 验证股票名称
            stock_name = converted_data.get('stock_name', '')
            if len(stock_name) < 2 or len(stock_name) > 20:
                logger.warning(f"股票名称长度无效: {stock_name}")
                return None
            
            # 验证价格数据的合理性
            current_price = converted_data.get('current_price')
            if current_price is not None:
                if current_price <= 0 or current_price > 10000:
                    logger.warning(f"股票价格异常: {current_price}")
                    return None
            
            # 清理股票代码
            stock_code = converted_data['stock_code']
            if isinstance(stock_code, str):
                # 处理不同格式的股票代码
                # 格式1: 000001.SZ -> 000001
                # 格式2: SZ000001 -> 000001
                # 格式3: 000001 -> 000001
                
                if '.' in stock_code:
                    # 000001.SZ 格式
                    stock_code = stock_code.split('.')[0]
                elif re.match(r'^[A-Z]{2}\d{6}$', stock_code):
                    # SZ000001 格式
                    stock_code = stock_code[2:]
                
                # 确保是6位数字
                if len(stock_code) == 6 and stock_code.isdigit():
                    converted_data['stock_code'] = stock_code
                else:
                    logger.warning(f"无效的股票代码: {stock_code}")
                    return None
            
            return converted_data
            
        except Exception as e:
            logger.error(f"转换行数据失败: {e}")
            return None
    
    def _parse_decimal(self, value: str) -> Optional[Decimal]:
        """解析数值字段"""
        try:
            if not value or value in ['--', '-', '']:
                return None
            
            # 移除百分号和其他符号
            clean_value = re.sub(r'[%,\s]', '', value)
            
            # 处理单位（万、亿等）
            if '万' in value:
                clean_value = clean_value.replace('万', '')
                multiplier = 10000
            elif '亿' in value:
                clean_value = clean_value.replace('亿', '')
                multiplier = 100000000
            else:
                multiplier = 1
            
            # 转换为Decimal
            decimal_value = Decimal(clean_value) * multiplier
            return decimal_value
            
        except (ValueError, InvalidOperation):
            # logger.warning(f"无法解析数值: {value}")
            return None
    

    
    async def create_crawl_batch(self, batch_name: str, crawl_url: Optional[str] = None, file_name: Optional[str] = None, query_string: Optional[str] = None) -> int:
        """
        创建抓取批次
        
        Args:
            batch_name: 批次名称
            crawl_url: 抓取URL
            file_name: 文件名，用于索引
            query_string: 原始查询条件
            
        Returns:
            批次ID
        """
        # Local imports to avoid circular dependency or context issues
        from app.repositories.tag_repository import TagRepository
        from app.models.tag_management import StockTagInfo, OperationLog, BatchTagRelation
        import json
        import urllib.parse
        from urllib.parse import urlparse, parse_qs

        try:
            # 1. 尝试从URL自动解析query_string (如果未提供)
            if not query_string and crawl_url:
                try:
                    parsed = urlparse(crawl_url)
                    qs = parse_qs(parsed.query)
                    
                    # 常见的参数名
                    extracted_query = None
                    if 'w' in qs:
                        extracted_query = qs['w'][0]
                    elif 'question' in qs:
                        extracted_query = qs['question'][0]
                    elif 'query' in qs:
                        extracted_query = qs['query'][0]
                        
                    if extracted_query:
                        # 有可能已经是解码的，或者是URL编码的
                        # 尝试解码，如果是已经解码的也不会出错(除非包含%)
                        try:
                            query_string = urllib.parse.unquote(extracted_query)
                        except:
                            query_string = extracted_query
                        logger.info(f"从URL解析出query_string: {query_string}")
                except Exception as e:
                    logger.warning(f"从URL提取query_string失败: {e}")

            # 使用文件名和当前日期作为索引
            current_date = datetime.now().strftime('%Y-%m-%d')
            indexed_batch_name = f"{file_name}_{current_date}" if file_name else batch_name
            
            # 2. 解析标签并处理关联
            tags_json_str = None
            tag_ids = []
            
            # 解析日期用于存储到 query_date
            query_date = None
            
            if query_string:
                # 尝试解析 query_date (YYYY年MM月DD日)
                date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', query_string)
                if date_match:
                    try:
                        year, month, day = date_match.groups()
                        query_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        logger.info(f"从查询条件提取到日期: {query_date}")
                    except Exception as e:
                        logger.warning(f"解析日期失败: {e}")

                try:
                    # 解析查询字符串
                    tags_data = TagService.parse_query(query_string)
                    parsed_tags = []
                    
                    # 初始化TagRepository
                    tag_repo = TagRepository(self.db)
                    
                    # 处理日期标签
                    for date_tag in tags_data.get('date', []):
                        tag_name = date_tag['value']
                        # 检查标签是否存在
                        existing_tag = await tag_repo.get_by_name(tag_name)
                        if not existing_tag:
                            # 创建新标签
                            new_tag = StockTagInfo(name=tag_name, score=0.0)
                            await self.db.add(new_tag)
                            await self.db.flush() # 获取ID
                            existing_tag = new_tag
                            
                            # 记录创建日志
                            op_log = OperationLog(
                                operator="system",
                                action="create",
                                target_type="tag",
                                target_id=str(existing_tag.id),
                                details={"name": tag_name, "source": "wencai_batch", "type": "date"}
                            )
                            await self.db.add(op_log)
                        
                        parsed_tags.append({
                            "id": existing_tag.id,
                            "name": existing_tag.name,
                            "type": "date"
                        })
                        tag_ids.append(existing_tag.id)

                    # 处理量能标签 (如: 三倍量)
                    # 只有当包含volume标签且数值符合要求时才创建/关联
                    for vol_tag in tags_data.get('volume', []):
                        tag_value = vol_tag['value']
                        try:
                            val_float = float(tag_value)
                            # 用户提到 "成交量的2.9倍"，关联标签三倍量
                            if val_float >= 2.9:
                                tag_name = "三倍量"
                                existing_tag = await tag_repo.get_by_name(tag_name)
                                
                                # 仅关联已存在的标签，不自动创建
                                if existing_tag:
                                    # 避免重复添加
                                    if existing_tag.id not in tag_ids:
                                        parsed_tags.append({
                                            "id": existing_tag.id,
                                            "name": existing_tag.name,
                                            "type": "volume"
                                        })
                                        tag_ids.append(existing_tag.id)
                        except:
                            pass

                    # 补充解析: 直接匹配字符串，防止 parse_query 解析失败
                    if "成交量的2.9倍" in query_string:
                        tag_name = "三倍量"
                        # 检查是否已在列表中
                        already_added = False
                        for t in parsed_tags:
                            if t['name'] == tag_name:
                                already_added = True
                                break
                        
                        if not already_added:
                            existing_tag = await tag_repo.get_by_name(tag_name)
                            
                            # 仅关联已存在的标签，不自动创建
                            if existing_tag and existing_tag.id not in tag_ids:
                                parsed_tags.append({
                                    "id": existing_tag.id,
                                    "name": existing_tag.name,
                                    "type": "volume"
                                })
                                tag_ids.append(existing_tag.id)

                    # 序列化为JSON存储 (虽然数据库可能没tags字段，但保留在变量中用于日志)
                    if parsed_tags:
                        tags_json_str = json.dumps(parsed_tags, ensure_ascii=False)
                        
                except Exception as e:
                    logger.warning(f"解析查询条件或关联标签失败: {e}")
                    # 不阻断主流程，但记录错误
            
            # 3. 插入批次记录
            # 注意：数据库中字段名为 query_condition 而不是 query_string
            sql = """
            INSERT INTO wencai_crawl_batches (
                batch_name, crawl_url, status, started_at, total_records, 
                success_records, failed_records, created_by, query_condition, query_date, tags
            )
            VALUES (
                :batch_name, :crawl_url, 'processing', NOW(), 0, 
                0, 0, 'system', :query_string, :query_date, :tags
            )
            """
            
            result = await self.db.execute(
                text(sql),
                {
                    'batch_name': indexed_batch_name,
                    'crawl_url': crawl_url,
                    'query_string': query_string,
                    'query_date': query_date,
                    'tags': tags_json_str
                }
            )
            
            batch_id = result.lastrowid
            
            # 4. 建立批次与标签的关联关系
            if tag_ids:
                # 插入关联表
                for tag_id in tag_ids:
                    # 使用ORM添加关联
                    relation = BatchTagRelation(
                        batch_id=batch_id,
                        tag_id=tag_id
                    )
                    self.db.add(relation)
                
                # 记录关联日志
                op_log = OperationLog(
                    operator="system",
                    action="associate",
                    target_type="batch_tags",
                    target_id=str(batch_id),
                    details={"tag_ids": tag_ids, "tags_json": tags_json_str}
                )
                self.db.add(op_log)
            
            # 5. 提交事务 (原子性保证：标签创建、批次插入、关联建立、日志记录都在同一事务)
            await self.db.commit()
            
            logger.info(f"创建抓取批次成功: {batch_id}, 索引名称: {indexed_batch_name}, 关联标签数: {len(tag_ids)}")
            return batch_id
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建抓取批次失败: {e}")
            raise
    
    async def save_wencai_stocks(self, batch_id: int, stocks_data: List[Dict[str, Any]]) -> Tuple[int, int, List[str]]:
        """
        保存问财股票数据到数据库 - 只保存4个核心字段
        
        Args:
            batch_id: 批次ID
            stocks_data: 股票数据列表
            
        Returns:
            (成功数量, 失败数量, 错误信息列表)
        """
        success_count = 0
        failed_count = 0
        errors = []
        
        try:
            for stock_data in stocks_data:
                try:
                    stock_code = stock_data.get('stock_code')
                    stock_name = stock_data.get('stock_name')

                    # 验证必要字段
                    if not stock_code or not stock_name:
                        error_msg = f"缺少必要字段: stock_code={stock_code}, stock_name={stock_name}"
                        errors.append(error_msg)
                        failed_count += 1
                        continue
                    
                    # 尝试从本地加载历史数据 (按需加载)
                    try:
                        # 2. 加载日线数据 (近250天)
                        local_daily = await LocalDataService.get_daily_data(stock_code, limit=250)
                        if local_daily:
                            await self.stock_service.stock_daily_repo.batch_save_daily_data(local_daily)
                            
                    except Exception as local_e:
                        # 仅记录警告，不阻断主流程
                        logger.warning(f"加载本地数据失败 {stock_code}: {local_e}")

                    # 生成数据哈希值（只使用4个核心字段）
                    data_hash = self._generate_data_hash(stock_data)
                    
                    # 使用 INSERT IGNORE 避免重复键错误
                    # 传入额外的字段用于存储
                    await self._insert_dedup_record_ignore(
                        stock_code, 
                        data_hash, 
                        batch_id,
                        stock_name=stock_name,
                        current_price=stock_data.get('current_price'),
                        change_percent=stock_data.get('price_change_percent')
                    )
                    
                    # 插入股票数据（只保存4个核心字段）
                    await self._insert_wencai_stock(batch_id, stock_data)
                    
                    # 插入概念关联数据
                    concept_str = stock_data.get('concept')
                    if concept_str:
                        concepts = [c.strip() for c in concept_str.replace('【', '').replace('】', '').split(';') if c.strip()]
                        await self._insert_stock_concepts(batch_id, stock_code, concepts)
                    
                    success_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    error_msg = f"保存股票 {stock_data.get('stock_code', 'unknown')} 失败: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
            
            # 同步保存到 StockDailyTemp (供缠论分析使用)
            try:
                from app.services.pattern_analysis_service import PatternAnalysisService
                pattern_service = PatternAnalysisService(self.db)
                
                # 转换数据格式
                temp_data_list = []
                for stock in stocks_data:
                    if not stock.get('stock_code'): continue
                    
                    temp_data_list.append({
                        "code": stock.get('stock_code'),
                        "trade_date": datetime.now().date(),
                        "open": stock.get('opening_price'),
                        "close": stock.get('current_price'),
                        "high": stock.get('highest_price'),
                        "low": stock.get('lowest_price'),
                        "volume": stock.get('volume'),
                        "amount": stock.get('turnover'),
                        "turnover": stock.get('turnover_rate'),
                        "industry": stock.get('industry'),
                        "concept": stock.get('concept')
                    })
                
                if temp_data_list:
                    saved_temp = await pattern_service.save_temp_data(temp_data_list, source="wencai_crawl")
                    logger.info(f"同步了 {saved_temp} 条数据到临时表")
                    
            except Exception as e:
                logger.error(f"同步临时表失败: {e}")
                # 不阻断主流程
            
            await self.db.commit()
            
            logger.info(f"批次 {batch_id} 保存完成: 成功 {success_count}, 失败 {failed_count}")
            return success_count, failed_count, errors
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"保存问财股票数据失败: {e}")
            raise
    
    def _generate_data_hash(self, stock_data: Dict[str, Any]) -> str:
        """生成数据哈希值用于去重 - 只使用4个核心字段"""
        # 只使用4个核心字段生成哈希
        key_fields = ['stock_code', 'stock_name', 'current_price', 'volume']
        hash_data = {}
        
        for field in key_fields:
            value = stock_data.get(field)
            if value is not None:
                hash_data[field] = str(value)
        
        hash_string = '|'.join(f"{k}:{v}" for k, v in sorted(hash_data.items()))
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    async def _is_duplicate_data(self, stock_code: str, data_hash: str) -> bool:
        """检查数据是否重复"""
        try:
            sql = """
            SELECT COUNT(*) as count FROM wencai_data_dedup 
            WHERE stock_code = :stock_code AND data_hash = :data_hash
            """
            
            result = await self.db.execute(
                text(sql),
                {'stock_code': stock_code, 'data_hash': data_hash}
            )
            
            row = result.fetchone()
            return row['count'] > 0 if row else False
            
        except Exception as e:
            logger.error(f"保存股票数据失败: {e}")
            return False
    
    def _parse_volume(self, volume_str: str) -> Optional[int]:
        """解析成交量字符串，返回整数"""
        if not volume_str:
            return None
        
        try:
            # 移除空格和特殊字符
            volume_str = volume_str.strip().replace(',', '')
            
            # 处理万、亿单位
            if '万' in volume_str:
                number = re.findall(r'[\d.]+', volume_str)[0]
                return int(float(number) * 10000)
            elif '亿' in volume_str:
                number = re.findall(r'[\d.]+', volume_str)[0]
                return int(float(number) * 100000000)
            else:
                # 直接数字
                number = re.findall(r'[\d.]+', volume_str)
                if number:
                    return int(float(number[0]))
                    
        except (ValueError, IndexError):
            pass
        
        return None
    
    async def get_batch_data(self, batch_id: int) -> List[Any]:
        """获取批次数据"""
        try:
            sql = "SELECT * FROM wencai_stocks WHERE crawl_batch_id = :batch_id"
            result = await self.db.execute(text(sql), {"batch_id": batch_id})
            return result.fetchall()
        except Exception as e:
            logger.error(f"获取批次数据失败: {e}")
            return []

    async def get_stocks_by_batch(self, batch_id: int) -> List[WencaiStock]:
        """获取批次的所有股票 (ORM对象)"""
        try:
            stmt = select(WencaiStock).where(WencaiStock.crawl_batch_id == str(batch_id))
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取批次股票失败: {e}")
            return []

    async def _insert_wencai_stock(self, batch_id: int, stock_data: Dict[str, Any]):
        """插入问财股票数据 - 保存核心字段及概念、行业、原始数据"""
        
        # Determine is_active status
        stock_code = stock_data.get('stock_code')
        is_active = True
        if stock_code:
             prev_stmt = select(WencaiStock.is_active).where(
                 WencaiStock.stock_code == stock_code
             ).order_by(WencaiStock.id.desc()).limit(1)
             prev_res = await self.db.execute(prev_stmt)
             prev_status = prev_res.scalar_one_or_none()
             is_active = True if prev_status is None else prev_status

        sql = """
        INSERT INTO wencai_stocks (
            stock_code, stock_name, current_price, volume, crawl_batch_id, concept, industry, raw_data, price_change_percent, is_active
        ) VALUES (
            :stock_code, :stock_name, :current_price, :volume, :crawl_batch_id, :concept, :industry, :raw_data, :price_change_percent, :is_active
        )
        """
        
        # 提取字段
        core_params = {
            'stock_code': stock_code,
            'stock_name': stock_data.get('stock_name'),
            'current_price': stock_data.get('current_price'),
            'volume': stock_data.get('volume'),
            'crawl_batch_id': batch_id,
            'concept': stock_data.get('concept'),
            'industry': stock_data.get('industry'),
            'raw_data': stock_data.get('raw_data'),
            'price_change_percent': stock_data.get('price_change_percent'),
            'is_active': is_active
        }
        
        await self.db.execute(text(sql), core_params)
        
    async def _insert_stock_concepts(self, batch_id: int, stock_code: str, concepts: List[str]):
        """插入股票概念关联数据"""
        if not concepts:
            return
            
        sql = """
        INSERT INTO stock_concepts (stock_code, concept_name, crawl_batch_id)
        VALUES (:stock_code, :concept_name, :crawl_batch_id)
        """
        
        values = [
            {'stock_code': stock_code, 'concept_name': c, 'crawl_batch_id': batch_id}
            for c in concepts
        ]
        
        await self.db.execute(text(sql), values)

    async def get_concept_statistics(self, start_date: Optional[str] = None, end_date: Optional[str] = None, keyword: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取概念统计数据
        :param start_date: 开始日期 (YYYY-MM-DD)
        :param end_date: 结束日期 (YYYY-MM-DD)
        :param keyword: 概念名称模糊搜索
        """
        try:
            batch_ids = []
            
            # 构建批次查询SQL
            batch_sql = "SELECT id, started_at FROM wencai_crawl_batches WHERE status='completed'"
            params = {}
            
            if start_date:
                batch_sql += " AND DATE(started_at) >= :start_date"
                params['start_date'] = start_date
            
            if end_date:
                batch_sql += " AND DATE(started_at) <= :end_date"
                params['end_date'] = end_date
                
            batch_sql += " ORDER BY id DESC"
            
            # 如果没有指定日期，默认只取最新的一个批次（保持原有逻辑用于默认展示）
            # 但是用户需求是"默认显示起始都是今天的日期的概念"，这将在Controller层处理，这里只负责按条件查询
            # 如果Controller传了today作为start和end，这里就会查today的所有批次
            # 如果什么都没传，为了兼容性，我们还是取最新的一个？
            # 或者返回空？
            # 既然是底层服务，灵活一点：如果不传日期，取最新的一个批次
            if not start_date and not end_date:
                batch_sql += " LIMIT 1"
                
            batch_result = await self.db.execute(text(batch_sql), params)
            batches = batch_result.fetchall()
            
            if not batches:
                return []
                
            batch_map = {row.id: row.started_at for row in batches}
            batch_ids = list(batch_map.keys())
            
            if not batch_ids:
                return []

            # 获取隐藏的概念列表
            try:
                hidden_sql = "SELECT concept_name FROM hidden_concepts"
                hidden_result = await self.db.execute(text(hidden_sql))
                hidden_concepts = {row[0] for row in hidden_result.fetchall()}
            except Exception as e:
                logger.warning(f"获取隐藏概念失败，可能是表不存在: {e}")
                hidden_concepts = set()
                
            # 从关联表查询数据
            # 关联日期标签和概念，不计算涨幅，只统计数量
            sql = """
            SELECT sc.concept_name, sti.name as date_tag, ws.stock_code, ws.stock_name
            FROM stock_concepts sc
            JOIN wencai_stocks ws ON sc.stock_code = ws.stock_code AND sc.crawl_batch_id = ws.crawl_batch_id
            JOIN batch_tag_relations btr ON sc.crawl_batch_id = btr.batch_id
            JOIN stock_tags_info sti ON btr.tag_id = sti.id
            WHERE sc.crawl_batch_id IN :batch_ids
            AND sti.tag_type = 'date'
            """
            params = {'batch_ids': batch_ids}
            
            if keyword:
                sql += " AND sc.concept_name LIKE :keyword"
                params['keyword'] = f"%{keyword}%"
            
            # 执行查询
            if len(batch_ids) == 1:
                sql = sql.replace("IN :batch_ids", "= :batch_id")
                params = {'batch_id': batch_ids[0]}
                if keyword:
                    params['keyword'] = f"%{keyword}%"
            
            result = await self.db.execute(text(sql).bindparams(bindparam('batch_ids', expanding=True)), params) if len(batch_ids) > 1 else await self.db.execute(text(sql), params)
            
            rows = result.fetchall()
            
            # 聚合数据: Key = (date_tag, concept_name)
            concepts_map = {}
            
            for row in rows:
                concept_name = row.concept_name
                date_tag = row.date_tag
                
                # 过滤隐藏概念
                if concept_name in hidden_concepts:
                    continue
                
                key = (date_tag, concept_name)
                
                stock_info = {
                    'code': row.stock_code,
                    'name': row.stock_name
                }
                
                if key not in concepts_map:
                    concepts_map[key] = {
                        'name': concept_name,
                        'stocks': [],
                        'count': 0,
                        'date': date_tag
                    }
                
                # 去重股票
                existing_codes = {s['code'] for s in concepts_map[key]['stocks']}
                if stock_info['code'] not in existing_codes:
                    concepts_map[key]['stocks'].append(stock_info)
                    concepts_map[key]['count'] += 1
            
            # 格式化结果
            result_list = []
            for data in concepts_map.values():
                result_list.append(data)
            
            # 排序: 日期倒序, 数量倒序
            result_list.sort(key=lambda x: (x['date'], x['count']), reverse=True)
            
            return result_list
        
        except Exception as e:
            logger.error(f"获取概念统计失败: {e}")
            return []

    async def hide_concept(self, concept_name: str) -> bool:
        """
        隐藏指定概念
        """
        try:
            # Check if already hidden
            check_sql = "SELECT id FROM hidden_concepts WHERE concept_name = :name"
            result = await self.db.execute(text(check_sql), {"name": concept_name})
            if result.scalar():
                logger.info(f"概念 '{concept_name}' 已经是隐藏状态")
                return True

            insert_sql = "INSERT INTO hidden_concepts (concept_name) VALUES (:name)"
            await self.db.execute(text(insert_sql), {"name": concept_name})
            await self.db.commit()
            
            logger.info(f"概念 '{concept_name}' 已隐藏")
            return True
        except Exception as e:
            logger.error(f"隐藏概念失败: {e}")
            raise e
    
    async def _insert_dedup_record_ignore(self, stock_code: str, data_hash: str, batch_id: int, 
                                          stock_name: str = None, 
                                          current_price: float = None, 
                                          change_percent: float = None):
        """插入去重记录 - 使用 INSERT IGNORE 避免重复键错误"""
        sql = """
        INSERT IGNORE INTO wencai_data_dedup (
            stock_code, data_hash, crawl_batch_id, 
            stock_name, current_price, change_percent
        )
        VALUES (
            :stock_code, :data_hash, :crawl_batch_id,
            :stock_name, :current_price, :change_percent
        )
        """
        
        await self.db.execute(
            text(sql),
            {
                'stock_code': stock_code,
                'data_hash': data_hash,
                'crawl_batch_id': batch_id,
                'stock_name': stock_name,
                'current_price': current_price,
                'change_percent': change_percent
            }
        )
    
    async def update_batch_status(self, batch_id: int, status: str, total_records: int, 
                                success_records: int, failed_records: int, 
                                error_message: Optional[str] = None):
        """更新批次状态"""
        try:
            sql = """
            UPDATE wencai_crawl_batches 
            SET status = :status, total_records = :total_records, 
                success_records = :success_records, failed_records = :failed_records,
                error_message = :error_message, completed_at = NOW()
            WHERE id = :batch_id
            """
            
            await self.db.execute(
                text(sql),
                {
                    'batch_id': batch_id,
                    'status': status,
                    'total_records': total_records,
                    'success_records': success_records,
                    'failed_records': failed_records,
                    'error_message': error_message
                }
            )
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"更新批次状态失败: {e}")
            # 不再抛出异常，以免掩盖原始错误

    async def process_batch_data(self, batch_id: int):
        """
        处理抓取批次数据：
        1. 解析query_string提取日期和标签
        2. 创建/获取标签
        3. 更新stock_info表
        4. 建立股票与标签的关联
        """
        from urllib.parse import unquote, urlparse, parse_qs

        logger.info(f"开始处理批次 {batch_id} 的数据...")
        
        try:
            # 1. 获取批次信息
            batch_sql = "SELECT * FROM wencai_crawl_batches WHERE id = :batch_id"
            result = await self.db.execute(text(batch_sql), {'batch_id': batch_id})
            batch = result.fetchone()
            
            if not batch:
                raise ValueError(f"批次 {batch_id} 不存在")
            
            # 转换 mapping 到 dict
            batch_data = dict(batch._mapping)
            # 注意：数据库字段是 query_condition
            query_string = batch_data.get('query_condition', '') or batch_data.get('query_string', '') or ''
            crawl_url = batch_data.get('crawl_url', '') or ''
            
            # 如果 query_string 为空，尝试从 crawl_url 提取
            if not query_string and crawl_url:
                try:
                    logger.info(f"query_string为空，尝试从URL提取: {crawl_url}")
                    # 处理可能被多次编码的URL
                    decoded_url = unquote(crawl_url)
                    parsed_url = urlparse(decoded_url)
                    query_params = parse_qs(parsed_url.query)
                    
                    # 尝试常见的查询参数名
                    for param in ['w', 'question', 'query', 'txt', 'q']:
                        if param in query_params:
                            query_string = query_params[param][0]
                            logger.info(f"成功从URL参数 '{param}' 提取 query_string: {query_string}")
                            break
                except Exception as e:
                    logger.warning(f"解析URL失败: {e}")
            
            logger.info(f"最终使用的 query_string: {query_string}")
            
            # 2. 解析日期和特殊标签
            tags_to_apply = []
            
            # 2.1 解析日期 (xxxx年xx月xx日 或 xxxx-xx-xx)
            date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', query_string)
            if not date_match:
                date_match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', query_string)
            
            date_tag_name = None
            if date_match:
                year, month, day = date_match.groups()
                # 格式化为 YYYY-MM-DD
                try:
                    date_obj = date(int(year), int(month), int(day))
                    date_tag_name = date_obj.strftime('%Y-%m-%d')
                    tags_to_apply.append(date_tag_name)
                except ValueError as e:
                    logger.warning(f"日期格式无效: {e}")
            
            # 2.2 解析 "成交量的2.9倍" -> "三倍量"
            if "成交量的2.9倍" in query_string:
                tags_to_apply.append("三倍量")
            
            # 3. 准备标签ID
            tag_ids = []
            for tag_name in tags_to_apply:
                try:
                    # 检查标签是否存在，不存在则创建
                    existing_tag = await self.tag_mgmt_service.repository.get_by_name(tag_name)
                    if existing_tag:
                        tag_ids.append(existing_tag.id)
                    else:
                        # 只有日期标签允许自动创建
                        is_date_tag = re.match(r'^\d{4}-\d{2}-\d{2}$', tag_name)
                        if is_date_tag:
                            # 创建新标签
                            logger.info(f"创建新标签: {tag_name}")
                            new_tag_data = TagCreate(name=tag_name, score=0)
                            new_tag = await self.tag_mgmt_service.create_tag(new_tag_data, operator="system_batch_process")
                            tag_ids.append(new_tag.id)
                        else:
                            logger.info(f"标签 {tag_name} 不存在且不是日期标签，跳过创建")
                except Exception as e:
                    logger.error(f"处理标签 {tag_name} 失败: {e}")
            
            if not tag_ids:
                logger.info("没有需要关联的标签，跳过标签关联步骤")
            else:
                # 建立批次与标签的关联
                for t_id in tag_ids:
                    try:
                        check_rel_sql = "SELECT id FROM batch_tag_relations WHERE batch_id = :batch_id AND tag_id = :tag_id"
                        rel_exists = await self.db.execute(text(check_rel_sql), {'batch_id': batch_id, 'tag_id': t_id})
                        if not rel_exists.scalar():
                            insert_rel_sql = "INSERT INTO batch_tag_relations (batch_id, tag_id) VALUES (:batch_id, :tag_id)"
                            await self.db.execute(text(insert_rel_sql), {'batch_id': batch_id, 'tag_id': t_id})
                    except Exception as e:
                        logger.error(f"建立批次标签关联失败 (batch_id={batch_id}, tag_id={t_id}): {e}")
            
            # 4. 获取该批次的股票列表
            stocks_sql = """
            SELECT stock_code, stock_name 
            FROM wencai_stocks 
            WHERE crawl_batch_id = :batch_id
            ORDER BY stock_code ASC
            """
            result = await self.db.execute(text(stocks_sql), {'batch_id': batch_id})
            stocks = result.fetchall()
            
            logger.info(f"批次包含 {len(stocks)} 只股票，开始处理 stock_info 和 标签关联...")
            
            processed_count = 0
            
            # 5. 处理每只股票
            # 为了防止死锁，按股票代码排序处理 (SQL已经排序)
            
            # 使用嵌套事务或分批提交来减少锁持有时间? 
            # 这里我们尽量在一个大事务中完成，但是如果太慢，可以考虑分批。
            # 鉴于 "任一环节失败时应回滚整个操作"，我们必须保持在一个事务中。
            
            for stock_row in stocks:
                stock_code = stock_row.stock_code
                stock_name = stock_row.stock_name
                
                try:
                    # 5.2 关联标签
                    if tag_ids:
                        for t_id in tag_ids:
                            await self.tag_mgmt_service.associate_stocks(tag_id=t_id, stock_codes=[stock_code], operator="system")
                            
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"处理股票 {stock_code} 失败: {e}")
                    raise e
            
            # 提交事务
            await self.db.commit()
            logger.info(f"批次 {batch_id} 数据处理完成，共处理 {processed_count} 只股票")

            # 6. 触发评分计算 (Trigger Scoring)
            # 如果查询包含日期，则计算该日期的评分；否则计算今日
            try:
                from app.services.rule_engine_service import RuleEngineService
                
                scoring_date = None
                if date_match: # Re-use regex match from earlier
                     try:
                        year, month, day = date_match.groups()
                        scoring_date = date(int(year), int(month), int(day))
                     except:
                        pass
                
                if not scoring_date:
                    scoring_date = date.today()
                    
                # logger.info(f"触发评分计算，目标日期: {scoring_date}")
                
                # 使用 db_manager 因为 RuleEngineService 需要它
                # rule_service = RuleEngineService(db_manager)
                
                # 异步运行评分，不阻塞当前请求太久 (或者根据需求阻塞)
                # 既然是后台处理，我们可以 await 它，或者 create_task
                # 为了保证数据一致性，建议 await，但如果是长任务，可能需要优化
                # 这里选择 create_task 以避免超时，但要注意日志追踪
                # Update: User wants to verify result, so maybe await is better for debug scripts?
                # But in production this might be slow.
                # Let's use await for now as batch processing is already heavy.
                
                # await rule_service.calculate_daily_scores(target_date=scoring_date, force=True)
                # logger.info(f"评分计算任务已完成: {scoring_date}")
                
            except Exception as e:
                logger.error(f"触发评分计算失败: {e}")

            # 触发增量同步任务(后台运行) - Disabled by user request for verification
            # try:
            #     ts_service = TushareService(db_manager)
            #     asyncio.create_task(ts_service.sync_daily_data(mode="incremental"))
            #     logger.info("已触发后台增量同步任务")
            # except Exception as e:
            #     logger.error(f"触发增量同步任务失败: {e}")
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"处理批次 {batch_id} 数据失败，已回滚: {e}")
            raise e
    
    async def get_batch_info(self, batch_id: int) -> Optional[Dict[str, Any]]:
        """获取批次信息，包含关联的标签"""
        try:
            # 1. 获取批次基本信息
            sql = """
            SELECT * FROM wencai_crawl_batches WHERE id = :batch_id
            """
            
            result = await self.db.execute(text(sql), {'batch_id': batch_id})
            row = result.fetchone()
            
            if not row:
                return None
            
            batch_info = dict(row._mapping)
            
            # 2. 获取关联的标签
            tag_sql = """
            SELECT t.id, t.name, t.tag_type, t.score
            FROM stock_tags_info t
            JOIN batch_tag_relations r ON t.id = r.tag_id
            WHERE r.batch_id = :batch_id
            """
            
            tag_result = await self.db.execute(text(tag_sql), {'batch_id': batch_id})
            tags = [dict(r._mapping) for r in tag_result.fetchall()]
            
            batch_info['tags'] = tags
            
            # 3. 合并 tags 字段中的标签 (JSON column)
            col_tags_raw = batch_info.get('tags_column') or batch_info.get('tags') # 数据库字段名为 tags，但上面已经用了 tags 变量名
            # 注意：batch_info 是从 SELECT * FROM wencai_crawl_batches 获取的，所以包含 tags 字段
            # 但是上面代码把 tags 键覆盖为了关联表查询结果
            # 所以我们需要重新从 row 中获取 tags 字段，或者在覆盖前保存
            
            # 让我们重新看下代码逻辑
            # batch_info = dict(row._mapping) -> 这里 batch_info['tags'] 是数据库列的值
            # tags = ... -> 这里 tags 是关联表结果
            # batch_info['tags'] = tags -> 这里覆盖了
            
            # 修正逻辑：
            # 1. 保存数据库列的值
            db_col_tags = row._mapping.get('tags')
            
            # 2. 合并
            final_tags = tags # start with relational tags
            seen_tag_names = {t['name'] for t in tags}
            
            col_tags_list = []
            if db_col_tags:
                if isinstance(db_col_tags, str):
                    try:
                        col_tags_list = json.loads(db_col_tags)
                    except json.JSONDecodeError:
                        col_tags_list = []
                elif isinstance(db_col_tags, list):
                    col_tags_list = db_col_tags
            
            for tag in col_tags_list:
                tag_name = tag.get('name')
                if tag_name and tag_name not in seen_tag_names:
                    # 适配格式
                    new_tag = {
                        'id': tag.get('id'),
                        'name': tag_name,
                        'tag_type': tag.get('type') or tag.get('tag_type'),
                        'score': tag.get('score')
                    }
                    final_tags.append(new_tag)
                    seen_tag_names.add(tag_name)
            
            batch_info['tags'] = final_tags
            
            return batch_info
            
        except Exception as e:
            logger.error(f"获取批次信息失败: {e}")
            return None
    
    async def get_latest_wencai_stocks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最新的问财股票数据"""
        try:
            sql = """
            SELECT * FROM v_latest_wencai_stocks 
            ORDER BY batch_time DESC, stock_code ASC
            LIMIT :limit
            """
            
            result = await self.db.execute(text(sql), {'limit': limit})
            rows = result.fetchall()
            
            return [dict(row._mapping) for row in rows]
            
        except Exception as e:
            logger.error(f"获取最新问财股票数据失败: {e}")
            return []

    async def sync_batch_stocks_to_pool(self, batch_id: int) -> Dict[str, Any]:
        """
        同步批次股票到监控池，并打标签
        """
        from .monitor_service import MonitorService
        monitor_service = MonitorService(self.db)
        
        # 1. Get batch info for date
        sql_batch = "SELECT * FROM wencai_crawl_batches WHERE id = :batch_id"
        result_batch = await self.db.execute(text(sql_batch), {'batch_id': batch_id})
        batch = result_batch.fetchone()
        
        if not batch:
            return {'total': 0, 'success': 0, 'failed': 0, 'errors': ['Batch not found']}
            
        batch_data = dict(batch._mapping)
        
        # Determine date: query_date > created_at
        batch_date = batch_data.get('query_date')
        if not batch_date:
            created_at = batch_data.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                     batch_date = created_at[:10]
                elif isinstance(created_at, datetime):
                    batch_date = created_at.strftime('%Y-%m-%d')
        
        if not batch_date:
            batch_date = datetime.now().strftime('%Y-%m-%d')

        # 2. Get stocks from wencai_data_dedup (more complete raw data)
        # Using DISTINCT stock_code to avoid processing same stock multiple times
        sql_stocks = """
        SELECT DISTINCT stock_code, stock_name 
        FROM wencai_data_dedup 
        WHERE crawl_batch_id = :batch_id
        """
        result_stocks = await self.db.execute(text(sql_stocks), {'batch_id': batch_id})
        stock_data_list = [{'code': row[0], 'name': row[1]} for row in result_stocks.fetchall() if row[0]]
        
        if not stock_data_list:
            # Fallback to wencai_stocks if dedup is empty
            sql_stocks_v2 = """
            SELECT DISTINCT stock_code, stock_name 
            FROM wencai_stocks 
            WHERE crawl_batch_id = :batch_id
            """
            result_stocks_v2 = await self.db.execute(text(sql_stocks_v2), {'batch_id': batch_id})
            stock_data_list = [{'code': row[0], 'name': row[1]} for row in result_stocks_v2.fetchall() if row[0]]

        if not stock_data_list:
             return {'total': 0, 'success': 0, 'failed': 0, 'errors': ['No stocks found in batch']}

        # 3. Process
        success_count = 0
        failed_count = 0
        errors = []
        
        # Prepare tags
        tags_to_add = [
            TagCreate(name=str(batch_date), tag_type='date', score=0),
            TagCreate(name='三倍量', tag_type='calculation', score=0)
        ]
        
        for stock_item in stock_data_list:
            code = stock_item['code']
            name = stock_item['name']
            try:
                # Add to monitor (auto_create_stock=True handles stock_info creation)
                # Priority 5 as default
                try:
                    await monitor_service.add_monitor(
                        stock_code=code, 
                        priority=5, 
                        auto_create_stock=True,
                        stock_name=name
                    )
                except Exception as e:
                    # Ignore if already exists (though add_monitor usually handles it, but just in case)
                    if "Duplicate" not in str(e) and "already exists" not in str(e):
                         logger.warning(f"Add monitor failed for {code}: {e}")
                         # Continue to add tags even if monitor add fails (e.g. already monitored)
                
                # Add tags
                await self.tag_mgmt_service.add_tags_to_stock(stock_code=code, tags=tags_to_add, operator="batch_sync")
                
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"{code}: {str(e)}")
        
        await self.db.commit()
                
        return {
            'total': len(stock_data_list),
            'success': success_count,
            'failed': failed_count,
            'errors': errors
        }