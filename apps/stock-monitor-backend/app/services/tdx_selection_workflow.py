#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通达信选股工作流服务
整合选股、数据库同步、飞书通知等功能
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal
from loguru import logger

from app.services.tdx_to_wencai_service import TdxToWencaiService
from app.services.tdx_block_service import TdxBlockService
from app.services.stock_selector import StockSelector
from app.services.feishu_client import FeishuClient


class TdxSelectionWorkflow:
    """
    通达信选股工作流
    
    职责：
    1. 执行选股策略
    2. 获取股票详细信息
    3. 同步结果到数据库（区分问财来源）
    4. 发送飞书通知
    """
    
    def __init__(
        self,
        tdx_client,
        feishu_client: Optional[FeishuClient] = None
    ):
        """
        初始化工作流
        
        Args:
            tdx_client: 通达信客户端
            feishu_client: 飞书客户端
        """
        self.tdx_client = tdx_client
        self.feishu_client = feishu_client
        self.selector = StockSelector()
        
    async def execute_selection(
        self,
        trade_date: date,
        sector_code: str,
        sector_name: str = "",
        stock_list: Optional[List[str]] = None,
        skip_screenshot: bool = False
    ) -> Dict[str, Any]:
        """
        执行选股工作流
        
        Args:
            trade_date: 交易日期
            sector_code: 板块代码
            sector_name: 板块名称
            stock_list: 股票列表，默认获取全市场
            skip_screenshot: 是否跳过截图
            
        Returns:
            Dict: 执行结果
        """
        logger.info(f"开始TDX选股工作流: {trade_date}, 板块: {sector_code}")
        
        wencai_batch_id = None
        selected_codes = []  # 提前声明，供 _get_stock_pool 使用
        
        try:
            # 1. 获取市场数据
            if stock_list is None:
                # 获取全市场股票列表
                stock_list = self._get_all_stocks()
            
            logger.info(f"获取 {len(stock_list)} 只股票的数据")
            
            # 获取K线数据 - 使用start_time和end_time获取特定日期数据
            # 为了计算量比，需要获取前两天数据（前一天和当天）
            start_time = (trade_date - timedelta(days=5)).strftime('%Y%m%d')
            end_time = trade_date.strftime('%Y%m%d')
            
            logger.info(f"获取K线数据: {start_time} 至 {end_time}")
            
            market_data = self.tdx_client.get_market_data(
                field_list=['Open', 'High', 'Low', 'Close', 'Volume', 'Amount'],
                stock_list=stock_list,
                period='1d',
                start_time=start_time,
                end_time=end_time,
                dividend_type='front',
                fill_data=True
            )
            
            # 2. 执行选股策略
            selected_codes = self.selector.select_3x_volume_and_limit_up(
                market_data=market_data,
                trade_date=trade_date
            )
            
            logger.info(f"选股完成: 选中 {len(selected_codes)} 只股票")
            
            # 3. 获取选中股票的详细信息
            selected_stocks = self._build_stock_details(
                selected_codes=selected_codes,
                market_data=market_data,
                trade_date=trade_date
            )
            
            # 4. 创建通达信板块并写入股票（直接操作板块文件）
            try:
                logger.info(f"创建通达信板块: {sector_code}")
                block_service = TdxBlockService()
                block_service.create_block_and_write_stocks(
                    trade_date=trade_date,
                    stocks=selected_codes,
                    block_code=sector_code
                )
                logger.info(f"成功创建通达信板块并写入 {len(selected_codes)} 只股票: {sector_code}")
            except Exception as e:
                logger.warning(f"创建通达信板块失败: {e}，继续执行数据库同步")
            
            # 5. 保存选股结果到数据库（问财表结构）
            async with TdxToWencaiService() as service:
                # 创建批次
                wencai_batch_id = await service.create_tdx_batch(
                    trade_date=trade_date,
                    sector_code=sector_code
                )
                
                # 保存选股结果
                saved_count = await service.save_tdx_selection_results(
                    batch_id=wencai_batch_id,
                    trade_date=trade_date,
                    selected_stocks=selected_stocks
                )
            
            logger.info(f"保存选股结果完成: {saved_count} 条记录")
            
            # 5.5 同步选股结果到飞书多维表格
            if self.feishu_client and self.feishu_client.app_token and self.feishu_client.table_id:
                try:
                    logger.info("同步选股结果到飞书多维表格...")
                    await self._sync_to_bitable(
                        trade_date=trade_date,
                        selected_stocks=selected_stocks
                    )
                    logger.info("飞书多维表格同步完成")
                except Exception as e:
                    logger.warning(f"同步到飞书多维表格失败: {e}")
            
            # 6. 同步250天日线数据到stock_daily表
            logger.info(f"同步 {len(selected_codes)} 只股票的250天日线数据...")
            from app.services.tdx_daily_data_service import TdxDailyDataService
            daily_service = TdxDailyDataService(self.tdx_client)
            sync_result = await daily_service.sync_daily_data_for_selection(
                stock_codes=selected_codes,
                end_date=trade_date,
                batch_id=wencai_batch_id,
                days=250
            )
            logger.info(f"日线数据同步完成: {sync_result['total_synced']} 条记录")
            
            # 7. 计算量价得分 (复用现有VolumeAnalysisService)
            logger.info("计算量价得分...")
            from app.services.volume_analysis_service import VolumeAnalysisService
            from app.database import db_manager
            
            async with db_manager.get_session() as session:
                for stock_code in selected_codes:
                    try:
                        code = stock_code.split('.')[0] if '.' in stock_code else stock_code
                        await VolumeAnalysisService.generate_daily_tags(
                            code=code,
                            target_date=trade_date,
                            session=session
                        )
                    except Exception as e:
                        logger.warning(f"计算 {stock_code} 得分失败: {e}")
            
            # 8. 截图功能（通达信和天龙博弈）- 只为符合地量条件的股票截图
            screenshot_paths = []
            if skip_screenshot:
                logger.info("⏭️ 跳过截图步骤（skip_screenshot=True）")
            else:
                try:
                    from app.services.screenshot_service import ScreenshotService
                    screenshot_service = ScreenshotService()
                    
                    # 获取股票池所有股票（包括历史选中的活跃股票）
                    logger.info("获取股票池所有股票...")
                    stock_pool = await self._get_stock_pool(selected_codes)
                    
                    # 筛选符合地量条件的股票
                    logger.info("筛选符合地量条件的股票...")
                    low_volume_stocks = await self._filter_low_volume_stocks(
                        stock_pool=stock_pool,
                        trade_date=trade_date
                    )
                    
                    if not low_volume_stocks:
                        logger.info("没有符合地量条件的股票，跳过截图")
                    else:
                        logger.info(f"开始为 {len(low_volume_stocks)} 只地量股票截图...")
                        for i, stock_code in enumerate(low_volume_stocks, 1):
                            try:
                                logger.info(f"[{i}/{len(low_volume_stocks)}] 截图: {stock_code}")
                                
                                # 通达信截图
                                result_tdx = screenshot_service.capture_tdx_screenshot(
                                    stock_code=stock_code.split('.')[0] if '.' in stock_code else stock_code,
                                    trade_date=trade_date,
                                    no_launch=True
                                )
                                if result_tdx.get('success'):
                                    screenshot_paths.append({
                                        'stock_code': stock_code,
                                        'path': result_tdx.get('screenshot_path'),
                                        'type': 'tdx',
                                        'success': True
                                    })
                                    logger.info(f"通达信截图成功: {stock_code}")
                                else:
                                    screenshot_paths.append({
                                        'stock_code': stock_code,
                                        'path': None,
                                        'type': 'tdx',
                                        'success': False,
                                        'error': result_tdx.get('error', '未知错误')
                                    })
                                    logger.warning(f"通达信截图失败: {stock_code} - {result_tdx.get('error')}")
                                
                                # 天龙博弈截图
                                result_tlby = screenshot_service.capture_tlby_screenshot(
                                    stock_code=stock_code.split('.')[0] if '.' in stock_code else stock_code,
                                    trade_date=trade_date,
                                    no_launch=True,
                                    analyze_sanlong=False
                                )
                                if result_tlby.get('success'):
                                    screenshot_paths.append({
                                        'stock_code': stock_code,
                                        'path': result_tlby.get('daily_image'),
                                        'type': 'tlby',
                                        'success': True
                                    })
                                    logger.info(f"天龙博弈截图成功: {stock_code}")
                                else:
                                    screenshot_paths.append({
                                        'stock_code': stock_code,
                                        'path': None,
                                        'type': 'tlby',
                                        'success': False,
                                        'error': result_tlby.get('error', '未知错误')
                                    })
                                    logger.warning(f"天龙博弈截图失败: {stock_code} - {result_tlby.get('error')}")
                                
                            except Exception as e:
                                logger.warning(f"截图异常 {stock_code}: {e}")
                                screenshot_paths.append({
                                    'stock_code': stock_code,
                                    'path': None,
                                    'type': 'tdx',
                                    'success': False,
                                    'error': str(e)
                                })
                        
                        success_count = len([p for p in screenshot_paths if p.get('success')])
                        logger.info(f"截图完成: 成功 {success_count}/{len(screenshot_paths)} 张")
                except Exception as e:
                    logger.warning(f"截图服务失败: {e}")
            
            # 9. 发送飞书通知（选股结果）
            if self.feishu_client:
                try:
                    result = self.feishu_client.send_selection_report(
                        trade_date=trade_date,
                        sector_code=sector_code,
                        selected_stocks=selected_stocks,
                        source="tdx"
                    )
                    
                    if result.get("message", {}).get("status") == "success":
                        logger.info("选股结果飞书通知发送成功")
                    else:
                        logger.warning(f"选股结果飞书通知发送失败: {result}")
                except Exception as e:
                    logger.error(f"发送选股结果飞书通知失败: {e}")
            
            # 10. 发送截图状态通知
            if self.feishu_client and screenshot_paths:
                try:
                    screenshot_result = self.feishu_client.send_screenshot_status(
                        trade_date=trade_date,
                        sector_code=sector_code,
                        screenshot_results=screenshot_paths,
                        total_stocks=len(selected_codes)
                    )
                    
                    if screenshot_result.get("status") == "success":
                        logger.info("截图状态飞书通知发送成功")
                    else:
                        logger.warning(f"截图状态飞书通知发送失败: {screenshot_result}")
                except Exception as e:
                    logger.error(f"发送截图状态飞书通知失败: {e}")
            
            return {
                "status": "success",
                "wencai_batch_id": wencai_batch_id,
                "trade_date": trade_date,
                "sector_code": sector_code,
                "selected_count": len(selected_stocks),
                "saved_count": saved_count,
                "selected_stocks": selected_stocks
            }
                
        except Exception as e:
            logger.error(f"选股工作流执行失败: {e}")
            
            # 发送错误通知
            if self.feishu_client:
                try:
                    self.feishu_client.send_error_notification(
                        job_name=f"通达信三倍量+涨停选股",
                        error_message=str(e),
                        source="tdx"
                    )
                except Exception as notify_error:
                    logger.error(f"发送错误通知失败: {notify_error}")
            
            return {
                "status": "failed",
                "reason": str(e),
                "wencai_batch_id": wencai_batch_id
            }
    
    async def _get_stock_pool(self, selected_codes: List[str]) -> List[str]:
        """
        获取股票池中的所有股票
        包括今日选中的股票和历史选中的活跃股票
        
        Args:
            selected_codes: 今日选中的股票代码列表
            
        Returns:
            List[str]: 股票代码列表
        """
        from app.database import db_manager
        from sqlalchemy import select, distinct
        from app.models.stock import WencaiStock
        
        stock_pool = set()
        
        # 1. 添加今日选中的股票
        stock_pool.update(selected_codes)
        
        # 2. 从数据库获取历史选中的活跃股票
        try:
            async with db_manager.get_session() as session:
                # 获取所有is_active=True的股票
                stmt = select(distinct(WencaiStock.stock_code)).where(
                    WencaiStock.is_active == True
                )
                result = await session.execute(stmt)
                active_stocks = result.scalars().all()
                stock_pool.update(active_stocks)
                logger.info(f"从数据库获取到 {len(active_stocks)} 只活跃股票")
        except Exception as e:
            logger.warning(f"获取活跃股票失败: {e}")
        
        stock_list = list(stock_pool)
        logger.info(f"股票池总计: {len(stock_list)} 只股票")
        return stock_list
    
    async def _filter_low_volume_stocks(
        self,
        stock_pool: List[str],
        trade_date: date
    ) -> List[str]:
        """
        筛选符合地量条件的股票
        
        地量定义：当日成交量低于过去N天的最小成交量
        检查周期：60日、30日、20日、10日、5日（取最长满足条件的周期）
        
        Args:
            stock_pool: 股票池
            trade_date: 交易日期
            
        Returns:
            List[str]: 符合地量条件的股票代码列表
        """
        from app.database import db_manager
        from app.services.stock_data_manager import StockDataManager
        
        low_volume_stocks = []
        stock_data_manager = StockDataManager(db_manager)
        
        # 地量检查周期（从长到短）
        low_vol_windows = [60, 30, 20, 10, 5]
        
        logger.info(f"开始检查 {len(stock_pool)} 只股票的地量条件...")
        
        for stock_code in stock_pool:
            try:
                # 提取纯代码（去掉.SZ/.SH后缀）
                code = stock_code.split('.')[0] if '.' in stock_code else stock_code
                
                # 获取历史数据（需要足够多的历史数据来判断地量）
                # 获取 trade_date 前 70 天的数据（确保有足够数据判断60日地量）
                start_date = trade_date - timedelta(days=70)
                daily_data = await stock_data_manager.get_stock_data(
                    code=code,
                    start_date=start_date,
                    end_date=trade_date,
                    sync_if_missing=False
                )
                
                if not daily_data or len(daily_data) < 2:
                    continue
                
                # 按日期排序
                daily_data = sorted(daily_data, key=lambda x: x.trade_date)
                
                # 确保最后一条是目标日期
                if daily_data[-1].trade_date != trade_date:
                    continue
                
                # 获取当日成交量
                current_vol = float(daily_data[-1].vol or 0)
                if current_vol <= 0:
                    continue
                
                # 检查是否满足地量条件
                is_low_volume = False
                for window in low_vol_windows:
                    if len(daily_data) < window + 1:
                        continue
                    
                    # 获取过去 window 天的成交量（不包含当天）
                    past_records = daily_data[-(window + 1):-1]
                    if not past_records:
                        continue
                    
                    past_vols = [float(d.vol or 0) for d in past_records]
                    min_past_vol = min(past_vols)
                    
                    # 地量条件：当日成交量 < 过去N天最小成交量
                    if current_vol < min_past_vol:
                        is_low_volume = True
                        logger.debug(f"{stock_code} 符合{window}日地量条件: 当日成交量={current_vol}, 过去{window}天最小={min_past_vol}")
                        break  # 取最长周期即可
                
                if is_low_volume:
                    low_volume_stocks.append(stock_code)
                    
            except Exception as e:
                logger.warning(f"检查地量条件失败 {stock_code}: {e}")
                continue
        
        logger.info(f"地量筛选完成: {len(low_volume_stocks)}/{len(stock_pool)} 只股票符合地量条件")
        return low_volume_stocks
    
    def _get_all_stocks(self) -> List[str]:
        """获取全市场股票列表"""
        try:
            # 从通达信获取全部A股 - 无参数调用获取所有股票
            stocks = self.tdx_client.get_stock_list()
            
            # 转换为标准格式
            result = []
            for stock in stocks:
                # 如果返回的是字典，提取 Code
                if isinstance(stock, dict):
                    code = stock.get('Code', '')
                # 如果返回的是字符串，直接使用
                elif isinstance(stock, str):
                    code = stock
                else:
                    continue
                    
                if code:
                    result.append(code)
            
            logger.info(f"从通达信获取到 {len(result)} 只A股")
            return result
        except Exception as e:
            logger.warning(f"获取全市场股票列表失败: {e}，使用默认列表")
            # 返回一些默认股票用于测试
            return [
                "000001.SZ", "000002.SZ", "000063.SZ", "000100.SZ", "000333.SZ",
                "000568.SZ", "000651.SZ", "000725.SZ", "000768.SZ", "000858.SZ",
                "600000.SH", "600009.SH", "600016.SH", "600028.SH", "600030.SH",
                "600031.SH", "600036.SH", "600048.SH", "600050.SH", "600104.SH",
                "600276.SH", "600309.SH", "600406.SH", "600436.SH", "600519.SH",
                "600547.SH", "600570.SH", "600585.SH", "600588.SH", "600690.SH",
                "600703.SH", "600745.SH", "600809.SH", "600837.SH", "600887.SH",
                "601012.SH", "601066.SH", "601088.SH", "601138.SH", "601166.SH",
                "601211.SH", "601288.SH", "601318.SH", "601398.SH", "601601.SH",
                "601628.SH", "601668.SH", "601688.SH", "601766.SH", "601857.SH",
                "601888.SH", "601899.SH", "601919.SH", "601995.SH", "603019.SH",
                "603259.SH", "603288.SH", "603501.SH", "603658.SH", "603986.SH"
            ]
    
    def _build_stock_details(
        self,
        selected_codes: List[str],
        market_data: Dict,
        trade_date: date
    ) -> List[Dict[str, Any]]:
        """
        构建选中股票的详细信息
        
        Args:
            selected_codes: 选中的股票代码列表
            market_data: 市场数据
            trade_date: 交易日期
            
        Returns:
            List[Dict]: 股票详细信息列表
        """
        result = []
        
        volume_df = market_data.get('Volume')
        close_df = market_data.get('Close')
        open_df = market_data.get('Open')
        high_df = market_data.get('High')
        low_df = market_data.get('Low')
        amount_df = market_data.get('Amount')
        
        for code in selected_codes:
            try:
                # 获取数据
                if len(volume_df) >= 2:
                    prev_volume = float(volume_df.iloc[-2][code])
                    today_volume = float(volume_df.iloc[-1][code])
                else:
                    continue
                
                if len(close_df) >= 2:
                    prev_close = float(close_df.iloc[-2][code])
                    today_close = float(close_df.iloc[-1][code])
                else:
                    continue
                
                today_open = float(open_df.iloc[-1][code]) if open_df is not None else None
                today_high = float(high_df.iloc[-1][code]) if high_df is not None else None
                today_low = float(low_df.iloc[-1][code]) if low_df is not None else None
                today_amount = float(amount_df.iloc[-1][code]) if amount_df is not None else None
                
                # 计算量比和涨跌幅
                volume_ratio = today_volume / prev_volume if prev_volume > 0 else 0
                change_percent = (today_close - prev_close) / prev_close * 100 if prev_close > 0 else 0
                
                # 获取股票名称
                stock_name = self._get_stock_name(code)
                
                # 获取涨停价
                limit_up_price = self._calculate_limit_up_price(prev_close, code)
                
                stock_detail = {
                    "stock_code": code,
                    "stock_name": stock_name,
                    "open_price": today_open,
                    "close_price": today_close,
                    "high_price": today_high,
                    "low_price": today_low,
                    "prev_close": prev_close,
                    "volume": int(today_volume),
                    "prev_volume": int(prev_volume),
                    "volume_ratio": round(volume_ratio, 4),
                    "amount": today_amount,
                    "change_percent": round(change_percent, 4),
                    "limit_up_price": limit_up_price,
                    "is_limit_up": True,
                    "source": "tdx"
                }
                
                result.append(stock_detail)
                
            except Exception as e:
                logger.warning(f"构建股票详情失败 {code}: {e}")
                continue
        
        # 按涨跌幅排序
        result.sort(key=lambda x: x.get("change_percent", 0), reverse=True)
        
        return result
    
    def _get_stock_name(self, code: str) -> str:
        """获取股票名称"""
        try:
            # 使用通达信API获取股票信息
            stock_info = self.tdx_client.get_stock_info(code)
            if stock_info and stock_info.get("ErrorId") == "0":
                name = stock_info.get("Name", "")
                if name:
                    return name
        except Exception as e:
            logger.warning(f"获取股票名称失败 {code}: {e}")
        
        # 如果获取失败，返回代码
        return code
    
    def _calculate_limit_up_price(self, prev_close: float, code: str) -> float:
        """计算涨停价"""
        # 判断市场类型
        if ".SZ" in code:
            if code.startswith("3"):
                threshold = 19.8  # 创业板
            else:
                threshold = 9.8   # 深市主板
        elif ".SH" in code:
            if code.startswith("688"):
                threshold = 19.8  # 科创板
            else:
                threshold = 9.8   # 沪市主板
        elif ".BJ" in code:
            threshold = 29.8      # 北交所
        else:
            threshold = 9.8
        
        return round(prev_close * (1 + threshold / 100), 3)
    
    async def _sync_to_bitable(
        self,
        trade_date: date,
        selected_stocks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        同步选股结果到飞书多维表格
        
        步骤：
        1. 添加新记录（入池数据）
        2. 更新所有记录的最新价格和形态判断
        
        Args:
            trade_date: 交易日期
            selected_stocks: 选中的股票列表
            
        Returns:
            Dict: 同步结果
        """
        import time
        
        logger.info(f"开始同步 {len(selected_stocks)} 只股票到飞书多维表格...")
        
        # 1. 添加新记录到飞书表格
        date_timestamp = int(time.mktime(trade_date.timetuple())) * 1000
        
        new_records = []
        for stock in selected_stocks:
            code = stock.get('stock_code', '')
            if '.' in code:
                code = code.split('.')[0]
            
            record = {
                "股票代码": code,
                "股票名称": stock.get('stock_name', ''),
                "入池日期": date_timestamp,
                "入池开盘价": float(stock.get('open_price', 0) or 0),
                "入池收盘价": float(stock.get('close_price', 0) or 0),
                "入池最高价": float(stock.get('high_price', 0) or 0),
                "成交量": float(stock.get('volume', 0) or 0),
                "3倍量确认": True,
                "5日地量": False,
                "10日地量": False,
                "20日地量": False,
                "30日地量": False,
                "60日地量": False,
                "突破最高价": False,
                "突破收盘价": False,
                "突破告警": False,
                "底分型": False,
                "阳包阴": False,
                "形态得分": 0,
                "备注": f"量比:{round(stock.get('volume_ratio', 0), 2)}, 涨幅:{round(stock.get('change_percent', 0), 2)}%, 选股日期:{trade_date.strftime('%m%d')}"
            }
            new_records.append(record)
        
        # 批量添加记录
        if new_records:
            add_result = self.feishu_client.add_records_to_bitable(new_records)
            logger.info(f"添加 {len(new_records)} 条新记录到飞书表格: {add_result.get('status')}")
        
        # 2. 更新所有记录的最新价格和形态判断
        logger.info("更新所有记录的最新价格和形态判断...")
        update_result = await self._update_bitable_records(trade_date)
        
        return {
            "added_count": len(new_records),
            "update_result": update_result
        }
    
    async def _update_bitable_records(self, trade_date: date) -> Dict[str, int]:
        """
        更新飞书多维表格中所有记录的最新价格和形态判断
        
        Args:
            trade_date: 交易日期
            
        Returns:
            Dict: 更新统计
        """
        import requests
        import time
        import pandas as pd
        
        # 获取所有记录
        all_records = self._get_all_bitable_records()
        if not all_records:
            logger.warning("飞书表格中没有记录需要更新")
            return {"total": 0, "success": 0, "failed": 0}
        
        logger.info(f"从飞书表格获取到 {len(all_records)} 条记录，开始更新...")
        
        # 准备更新数据
        update_records = []
        
        for record in all_records:
            try:
                parsed = self._parse_bitable_record(record)
                stock_code = parsed["stock_code"]
                
                if not stock_code:
                    continue
                
                # 转换股票代码格式
                if stock_code.startswith('6'):
                    stock_code_full = f"{stock_code}.SH"
                else:
                    stock_code_full = f"{stock_code}.SZ"
                
                # 从通达信获取历史数据
                df = self._get_stock_history_data(stock_code_full, days=60)
                
                if df is None or len(df) == 0:
                    logger.warning(f"无法获取 {stock_code} 的历史数据")
                    continue
                
                # 计算更新字段
                update_fields = self._calculate_update_fields(parsed, df, trade_date)
                
                if update_fields:
                    update_records.append({
                        "record_id": parsed["record_id"],
                        "fields": update_fields
                    })
                    
            except Exception as e:
                logger.warning(f"处理记录失败: {e}")
                continue
        
        # 批量更新
        if update_records:
            result = self._batch_update_bitable_records(update_records)
            logger.info(f"更新完成: 总计 {result['total']}, 成功 {result['success']}, 失败 {result['failed']}")
            return result
        else:
            return {"total": 0, "success": 0, "failed": 0}
    
    def _get_all_bitable_records(self) -> List[Dict[str, Any]]:
        """从飞书多维表格获取所有记录"""
        import requests
        
        access_token = self.feishu_client._get_access_token()
        if not access_token:
            return []
        
        all_records = []
        page_token = None
        page_size = 500
        
        while True:
            url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_client.app_token}/tables/{self.feishu_client.table_id}/records/search"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {"page_size": page_size}
            if page_token:
                data["page_token"] = page_token
            
            try:
                response = requests.post(url, headers=headers, json=data, timeout=30)
                result = response.json()
                
                if result.get("code") == 0:
                    records = result.get("data", {}).get("items", [])
                    all_records.extend(records)
                    
                    has_more = result.get("data", {}).get("has_more", False)
                    if not has_more:
                        break
                    
                    page_token = result.get("data", {}).get("page_token")
                    if not page_token:
                        break
                else:
                    logger.error(f"查询记录失败: {result}")
                    break
                    
            except Exception as e:
                logger.error(f"查询记录异常: {e}")
                break
        
        return all_records
    
    def _parse_bitable_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """解析飞书记录"""
        fields = record.get("fields", {})
        record_id = record.get("record_id", "")
        
        # 解析股票代码（文本字段返回列表）
        stock_code_field = fields.get("股票代码", "")
        if isinstance(stock_code_field, list) and len(stock_code_field) > 0:
            stock_code = stock_code_field[0].get("text", "") if isinstance(stock_code_field[0], dict) else str(stock_code_field[0])
        else:
            stock_code = str(stock_code_field) if stock_code_field else ""
        
        # 解析股票名称
        stock_name_field = fields.get("股票名称", "")
        if isinstance(stock_name_field, list) and len(stock_name_field) > 0:
            stock_name = stock_name_field[0].get("text", "") if isinstance(stock_name_field[0], dict) else str(stock_name_field[0])
        else:
            stock_name = str(stock_name_field) if stock_name_field else ""
        
        # 解析入池数据
        pool_high = fields.get("入池最高价", 0)
        pool_close = fields.get("入池收盘价", 0)
        
        return {
            "record_id": record_id,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "pool_high": float(pool_high) if pool_high else 0,
            "pool_close": float(pool_close) if pool_close else 0,
        }
    
    def _get_stock_history_data(self, stock_code_full: str, days: int = 60):
        """从通达信获取股票历史数据"""
        try:
            import pandas as pd
            
            data_dict = self.tdx_client.get_market_data(
                field_list=['Open', 'High', 'Low', 'Close', 'Volume', 'Amount'],
                stock_list=[stock_code_full],
                period='1d',
                count=days,
                dividend_type='front',
                fill_data=True
            )
            
            close_df = data_dict.get('Close')
            if close_df is None or close_df.empty:
                return None
            
            df_data = {
                'Open': data_dict.get('Open')[stock_code_full] if data_dict.get('Open') is not None else None,
                'High': data_dict.get('High')[stock_code_full] if data_dict.get('High') is not None else None,
                'Low': data_dict.get('Low')[stock_code_full] if data_dict.get('Low') is not None else None,
                'Close': close_df[stock_code_full],
                'Volume': data_dict.get('Volume')[stock_code_full] if data_dict.get('Volume') is not None else None,
                'Amount': data_dict.get('Amount')[stock_code_full] if data_dict.get('Amount') is not None else None,
            }
            
            df = pd.DataFrame(df_data)
            df.index = close_df.index
            
            # 单位转换
            df['Volume'] = df['Volume'] / 100  # 股 → 手
            df['Amount'] = df['Amount'] / 1000  # 元 → 千元
            
            return df
            
        except Exception as e:
            logger.error(f"获取 {stock_code_full} 历史数据失败: {e}")
            return None
    
    def _calculate_update_fields(self, parsed: Dict[str, Any], df, trade_date: date) -> Dict[str, Any]:
        """计算更新字段"""
        if df is None or len(df) == 0:
            return None
        
        # 获取最新数据
        latest_close = float(df['Close'].iloc[-1])
        latest_volume = float(df['Volume'].iloc[-1])
        latest_high = float(df['High'].iloc[-1])
        latest_low = float(df['Low'].iloc[-1])
        latest_open = float(df['Open'].iloc[-1])
        
        # 获取历史成交量列表
        volumes = df['Volume'].tolist()
        
        # 计算地量标志
        low_volume_flags = self._calculate_low_volume_flags(volumes)
        
        # 计算形态标志
        pattern_flags = self._calculate_pattern_flags(df)
        
        # 计算突破标志
        breakout_flags = self._calculate_breakout_flags(
            latest_close,
            parsed["pool_high"],
            parsed["pool_close"]
        )
        
        # 计算形态得分
        score = 0
        if low_volume_flags["5日地量"]: score += 1
        if low_volume_flags["10日地量"]: score += 1
        if low_volume_flags["20日地量"]: score += 1
        if pattern_flags["底分型"]: score += 2
        if pattern_flags["阳包阴"]: score += 2
        if breakout_flags["突破最高价"]: score += 3
        if breakout_flags["突破收盘价"]: score += 1
        
        # 构建更新字段
        date_str = trade_date.strftime('%Y-%m-%d')
        
        return {
            "最新日期": date_str,
            "最新收盘价": latest_close,
            "最新成交量": latest_volume,
            "5日地量": bool(low_volume_flags["5日地量"]),
            "10日地量": bool(low_volume_flags["10日地量"]),
            "20日地量": bool(low_volume_flags["20日地量"]),
            "30日地量": bool(low_volume_flags["30日地量"]),
            "60日地量": bool(low_volume_flags["60日地量"]),
            "突破最高价": bool(breakout_flags["突破最高价"]),
            "突破收盘价": bool(breakout_flags["突破收盘价"]),
            "突破告警": bool(breakout_flags["突破告警"]),
            "底分型": bool(pattern_flags["底分型"]),
            "阳包阴": bool(pattern_flags["阳包阴"]),
            "形态得分": int(score),
            "备注": f"更新于{trade_date.strftime('%m%d')}, 收盘:{latest_close:.2f}, 最高:{latest_high:.2f}, 最低:{latest_low:.2f}, 得分:{int(score)}"
        }
    
    def _calculate_low_volume_flags(self, volumes: List[float]) -> Dict[str, bool]:
        """计算地量标志"""
        if not volumes or len(volumes) < 2:
            return {"5日地量": False, "10日地量": False, "20日地量": False, "30日地量": False, "60日地量": False}
        
        latest_volume = volumes[-1]
        result = {}
        
        for days, name in [(5, "5日地量"), (10, "10日地量"), (20, "20日地量"), (30, "30日地量"), (60, "60日地量")]:
            if len(volumes) >= days + 1:
                past_volumes = volumes[-(days+1):-1]
                avg_volume = sum(past_volumes) / len(past_volumes)
                result[name] = latest_volume < avg_volume * 0.8
            else:
                result[name] = False
        
        return result
    
    def _calculate_pattern_flags(self, df) -> Dict[str, bool]:
        """计算形态标志"""
        if df is None or len(df) < 3:
            return {"底分型": False, "阳包阴": False}
        
        result = {}
        
        # 底分型判断
        low_2days_ago = df['Low'].iloc[-3]
        low_1day_ago = df['Low'].iloc[-2]
        low_today = df['Low'].iloc[-1]
        result["底分型"] = low_1day_ago < low_2days_ago and low_1day_ago < low_today
        
        # 阳包阴判断
        if len(df) >= 2:
            open_yesterday = df['Open'].iloc[-2]
            close_yesterday = df['Close'].iloc[-2]
            open_today = df['Open'].iloc[-1]
            close_today = df['Close'].iloc[-1]
            
            yesterday_yin = close_yesterday < open_yesterday
            today_yang = close_today > open_today
            result["阳包阴"] = yesterday_yin and today_yang and open_today <= close_yesterday and close_today >= open_yesterday
        else:
            result["阳包阴"] = False
        
        return result
    
    def _calculate_breakout_flags(self, latest_close: float, pool_high: float, pool_close: float) -> Dict[str, bool]:
        """计算突破标志"""
        result = {}
        
        result["突破最高价"] = latest_close > pool_high if pool_high > 0 else False
        result["突破收盘价"] = latest_close > pool_close if pool_close > 0 else False
        
        if pool_close > 0:
            change_pct = (latest_close - pool_close) / pool_close * 100
            result["突破告警"] = result["突破最高价"] and change_pct > 3
        else:
            result["突破告警"] = False
        
        return result
    
    def _batch_update_bitable_records(self, records: List[Dict[str, Any]], batch_size: int = 9) -> Dict[str, int]:
        """批量更新飞书表格记录"""
        import requests
        import time
        
        total = len(records)
        success_count = 0
        failed_count = 0
        
        logger.info(f"开始批量更新 {total} 条记录，每批 {batch_size} 条...")
        
        for i in range(0, total, batch_size):
            batch = records[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            logger.info(f"  处理第 {batch_num}/{total_batches} 批，{len(batch)} 条记录...")
            
            for record in batch:
                record_id = record["record_id"]
                fields = record["fields"]
                
                if self._update_single_bitable_record(record_id, fields):
                    success_count += 1
                else:
                    failed_count += 1
                
                time.sleep(0.1)
            
            if i + batch_size < total:
                time.sleep(0.5)
        
        return {"total": total, "success": success_count, "failed": failed_count}
    
    def _update_single_bitable_record(self, record_id: str, fields: Dict[str, Any]) -> bool:
        """更新单条飞书表格记录"""
        import requests
        
        access_token = self.feishu_client._get_access_token()
        if not access_token:
            return False
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_client.app_token}/tables/{self.feishu_client.table_id}/records/{record_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        data = {"fields": fields}
        
        try:
            response = requests.put(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if result.get("code") == 0:
                return True
            else:
                logger.error(f"更新记录 {record_id} 失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"更新记录 {record_id} 异常: {e}")
            return False


# 便捷函数
async def run_tdx_selection_workflow(
    tdx_client,
    trade_date: Optional[date] = None,
    sector_code: Optional[str] = None,
    feishu_client: Optional[FeishuClient] = None
) -> Dict[str, Any]:
    """
    运行通达信选股工作流
    
    Args:
        tdx_client: 通达信客户端
        trade_date: 交易日期，默认为今天
        sector_code: 板块代码，默认为 3BL{MMDD}
        feishu_client: 飞书客户端
        
    Returns:
        Dict: 执行结果
    """
    if trade_date is None:
        trade_date = date.today()
    
    if sector_code is None:
        # 板块代码格式: 3BL260201 (年份后两位+月份+日期)
        sector_code = f"3BL{trade_date.strftime('%y%m%d')}"
    
    workflow = TdxSelectionWorkflow(
        tdx_client=tdx_client,
        feishu_client=feishu_client
    )
    
    return await workflow.execute_selection(
        trade_date=trade_date,
        sector_code=sector_code
    )
