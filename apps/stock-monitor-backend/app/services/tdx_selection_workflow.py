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
        stock_list: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        执行选股工作流
        
        Args:
            trade_date: 交易日期
            sector_code: 板块代码
            sector_name: 板块名称
            stock_list: 股票列表，默认获取全市场
            
        Returns:
            Dict: 执行结果
        """
        logger.info(f"开始TDX选股工作流: {trade_date}, 板块: {sector_code}")
        
        wencai_batch_id = None
        
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
            
            # 5. 截图功能（通达信和天龙博弈）
            screenshot_paths = []
            try:
                from app.services.screenshot_service import ScreenshotService
                screenshot_service = ScreenshotService()
                
                logger.info(f"开始为 {len(selected_codes)} 只股票截图...")
                for stock_code in selected_codes[:5]:  # 最多截图前5只
                    try:
                        # 通达信截图
                        result = screenshot_service.capture_tdx_screenshot(
                            stock_code=stock_code.split('.')[0],  # 去掉后缀
                            trade_date=trade_date,
                            no_launch=True
                        )
                        if result.get('success'):
                            screenshot_paths.append({
                                'stock_code': stock_code,
                                'path': result.get('screenshot_path'),
                                'type': 'tdx'
                            })
                            logger.info(f"截图成功: {stock_code}")
                    except Exception as e:
                        logger.warning(f"截图失败 {stock_code}: {e}")
                
                logger.info(f"截图完成: {len(screenshot_paths)} 张")
            except Exception as e:
                logger.warning(f"截图服务失败: {e}")
            
            # 6. 保存选股结果到数据库（问财表结构）
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
            
            # 7. 同步250天日线数据到stock_daily表
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
            
            # 8. 计算量价得分 (复用现有VolumeAnalysisService)
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
