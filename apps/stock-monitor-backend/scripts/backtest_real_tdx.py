#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实通达信环境回测脚本
直接使用通达信数据进行回测

使用方法:
1. 确保通达信客户端已启动并登录
2. 运行: python scripts/backtest_real_tdx.py
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 添加通达信Python路径
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

from datetime import date, timedelta
from typing import List
import pandas as pd
from loguru import logger

# 配置日志
logger.add("logs/backtest_real_tdx.log", rotation="10 MB")

def is_trading_day(d: date) -> bool:
    """判断是否为交易日（简化版：排除周末）"""
    return d.weekday() < 5

def get_trading_days(start_date: date, end_date: date) -> List[date]:
    """获取交易日列表"""
    trading_days = []
    current = start_date
    while current <= end_date:
        if is_trading_day(current):
            trading_days.append(current)
        current += timedelta(days=1)
    return trading_days

def get_all_stock_codes(tdx_client) -> List[str]:
    """获取所有股票代码"""
    # 生成所有A股股票代码
    stock_list = []
    
    # 深市主板 (000001-004999)
    for i in range(1, 5000):
        stock_list.append(f"{i:06d}.SZ")
    
    # 深市中小板 (002001-002999)
    for i in range(2001, 3000):
        stock_list.append(f"{i:06d}.SZ")
    
    # 深市创业板 (300001-301999)
    for i in range(300001, 302000):
        stock_list.append(f"{i:06d}.SZ")
    
    # 沪市主板 (600000-604999)
    for i in range(600000, 605000):
        stock_list.append(f"{i:06d}.SH")
    
    # 沪市科创板 (688001-689999)
    for i in range(688001, 690000):
        stock_list.append(f"{i:06d}.SH")
    
    logger.info(f"生成全量股票列表: {len(stock_list)} 只")
    return stock_list

def select_3x_volume_and_limit_up_real(data: dict, trade_date: date) -> List[str]:
    """
    使用真实数据执行3倍量+涨停组合策略选股
    
    条件：
    1. 当日成交量 >= 前一日成交量 × 3
    2. 当日涨幅达到涨停阈值
    
    Args:
        data: 通达信返回的字典格式，包含Volume, Close, Open, High, Low等
        trade_date: 交易日期，用于匹配数据
        
    Returns:
        List[str]: 选中的股票代码列表
    """
    selected = []
    
    # 检查必要字段
    required_fields = ['Volume', 'Close', 'Open', 'High', 'Low']
    for field in required_fields:
        if field not in data:
            logger.warning(f"数据中缺少{field}字段")
            return selected
    
    volume_df = data['Volume']
    close_df = data['Close']
    open_df = data['Open']
    high_df = data['High']
    low_df = data['Low']
    
    if len(volume_df) < 2:
        logger.warning(f"数据行数不足: {len(volume_df)}行，需要至少2行")
        return selected
    
    # 找到指定日期的数据
    trade_date_str = trade_date.strftime('%Y-%m-%d')
    
    # 找到交易日期在数据中的位置
    date_index = None
    for i, idx in enumerate(volume_df.index):
        if trade_date_str in str(idx):
            date_index = i
            break
    
    if date_index is None or date_index == 0:
        logger.warning(f"未找到 {trade_date} 的数据或没有前一日数据")
        return selected
    
    # 获取前一日和当日的数据
    prev_volume_row = volume_df.iloc[date_index - 1]
    today_volume_row = volume_df.iloc[date_index]
    prev_close_row = close_df.iloc[date_index - 1]
    today_close_row = close_df.iloc[date_index]
    today_open_row = open_df.iloc[date_index]
    today_high_row = high_df.iloc[date_index]
    today_low_row = low_df.iloc[date_index]
    
    actual_date = volume_df.index[date_index]
    prev_date = volume_df.index[date_index - 1]
    
    logger.info(f"  分析日期: 前日={prev_date}, 今日={actual_date}")
    
    # 涨停阈值配置
    limit_up_thresholds = {
        'SH': 9.8,   # 沪市主板
        'SZ': 9.8,   # 深市主板
        'CY': 19.8,  # 创业板
        'KC': 19.8,  # 科创板
        'BJ': 29.8,  # 北交所
    }
    
    for stock_code in volume_df.columns:
        try:
            # 获取数据
            prev_volume = prev_volume_row[stock_code]
            today_volume = today_volume_row[stock_code]
            prev_close = prev_close_row[stock_code]
            today_close = today_close_row[stock_code]
            
            # 排除无效数据
            if prev_volume <= 0 or today_volume <= 0 or prev_close <= 0:
                continue
            
            # 条件1：三倍量
            volume_ratio = today_volume / prev_volume
            if volume_ratio < 3.0:
                continue
            
            # 条件2：涨停
            change_percent = (today_close - prev_close) / prev_close * 100
            
            # 判断市场类型
            if ".SZ" in stock_code:
                if stock_code.startswith("3"):
                    market = "CY"  # 创业板
                else:
                    market = "SZ"  # 深市主板
            elif ".SH" in stock_code:
                if stock_code.startswith("688"):
                    market = "KC"  # 科创板
                else:
                    market = "SH"  # 沪市主板
            elif ".BJ" in stock_code:
                market = "BJ"  # 北交所
            else:
                market = "SH"
            
            threshold = limit_up_thresholds.get(market, 9.8)
            
            # 检查是否涨停
            is_limit_up = change_percent >= threshold
            
            # 同时满足两个条件
            if is_limit_up:
                selected.append(stock_code)
                logger.info(f"    🔥 3倍量+涨停选中: {stock_code}, 量比: {volume_ratio:.2f}, 涨幅: {change_percent:.2f}%")
                
        except Exception as e:
            continue
    
    return selected

def backtest_single_day(tdx_client, trade_date: date):
    """单日回测"""
    logger.info(f"\n{'='*60}")
    logger.info(f"回测日期: {trade_date}")
    logger.info(f"{'='*60}")
    
    # 1. 获取股票列表
    logger.info("Step 1: 获取股票列表")
    stock_codes = get_all_stock_codes(tdx_client)
    logger.info(f"  获取到 {len(stock_codes)} 只股票")
    
    # 2. 获取市场数据（获取交易日前后几天的数据）
    logger.info("Step 2: 获取市场数据")
    try:
        # 计算日期范围（前后各3天，确保能获取到交易日数据）
        start_date = trade_date - timedelta(days=5)
        end_date = trade_date + timedelta(days=1)
        
        logger.info(f"  获取数据范围: {start_date} 至 {end_date}")
        
        data = tdx_client.get_market_data(
            field_list=['Volume', 'Close', 'Open', 'High', 'Low'],
            stock_list=stock_codes,
            period='1d',
            start_time=start_date.strftime('%Y%m%d'),
            end_time=end_date.strftime('%Y%m%d'),
            dividend_type='front'
        )
        
        logger.info(f"  数据类型: {type(data)}")
        
        if isinstance(data, dict):
            logger.info(f"  数据键: {list(data.keys())}")
            if 'Volume' in data:
                volume_df = data['Volume']
                logger.info(f"  Volume数据形状: {volume_df.shape}")
                logger.info(f"  Volume数据日期: {list(volume_df.index)}")
                logger.info(f"  Volume数据列数: {len(volume_df.columns)}")
        else:
            logger.warning(f"  未知数据类型: {type(data)}")
            return
        
    except Exception as e:
        logger.error(f"  获取数据失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. 执行3倍量+涨停选股
    logger.info("Step 3: 执行3倍量+涨停选股")
    selected = select_3x_volume_and_limit_up_real(data, trade_date)
    logger.info(f"  选中 {len(selected)} 只3倍量股票")
    
    # 4. 生成板块名称
    # 板块代码格式: 3BL260201 (年份后两位+月份+日期)
    sector_code = f"3BL{trade_date.strftime('%y%m%d')}"
    sector_name = f"3倍量涨停{trade_date.strftime('%y%m%d')}"
    
    logger.info(f"Step 4: 创建板块")
    logger.info(f"  板块代码: {sector_code}")
    logger.info(f"  板块名称: {sector_name}")
    
    # 5. 创建板块并发送股票
    if selected:
        try:
            # 创建板块
            result = tdx_client.create_sector(sector_code, sector_name)
            logger.info(f"  板块创建结果: {result}")
            
            # 发送股票到板块
            result = tdx_client.send_user_block(sector_code, selected)
            logger.info(f"  发送股票结果: {result}")
            logger.info(f"  成功发送 {len(selected)} 只股票到板块")
        except Exception as e:
            logger.error(f"  创建板块或发送股票失败: {e}")
    else:
        logger.info("  没有选中的股票，跳过板块创建")
    
    logger.info(f"{'='*60}\n")
    
    return {
        'date': trade_date,
        'sector_code': sector_code,
        'selected_count': len(selected),
        'selected_stocks': selected
    }

def main():
    """主函数"""
    logger.info("="*60)
    logger.info("真实通达信环境回测")
    logger.info("="*60)
    
    # 导入通达信模块
    try:
        from tqcenter import tq
        logger.info("✅ 通达信模块加载成功")
    except ImportError as e:
        logger.error(f"❌ 通达信模块加载失败: {e}")
        logger.error("请确保:")
        logger.error("1. 通达信已安装在 C:\\new_tdx_test")
        logger.error("2. 通达信客户端已启动")
        return
    
    # 初始化连接
    try:
        tq.initialize(__file__)
        logger.info("✅ 通达信连接初始化成功")
    except Exception as e:
        logger.error(f"❌ 通达信连接失败: {e}")
        return
    
    # 测试连接
    try:
        data = tq.get_market_data(
            field_list=['Close'],
            stock_list=['000001.SZ'],
            period='1d',
            count=1
        )
        logger.info(f"✅ 连接测试成功，获取到数据: {type(data)}")
    except Exception as e:
        logger.error(f"❌ 连接测试失败: {e}")
        return
    
    # 回测日期范围 - 从2026年2月1日开始
    start_date = date(2026, 2, 1)
    end_date = date(2026, 3, 25)
    trading_days = get_trading_days(start_date, end_date)
    
    logger.info(f"\n回测日期: {start_date} 至 {end_date}")
    logger.info(f"交易日数量: {len(trading_days)}")
    
    # 执行回测（测试前10个交易日）
    test_dates = trading_days[:10]
    
    # 执行回测
    results = []
    for i, trade_date in enumerate(test_dates):
        logger.info(f"\n[{i+1}/{len(test_dates)}] 处理日期: {trade_date}")
        result = backtest_single_day(tq, trade_date)
        if result:
            results.append(result)
        
        # 暂停一下，避免请求过快
        import time
        time.sleep(1)
    
    # 输出统计结果
    logger.info("\n" + "="*60)
    logger.info("回测统计")
    logger.info("="*60)
    logger.info(f"回测范围: {start_date} 至 {end_date}")
    logger.info(f"总交易日: {len(trading_days)}")
    logger.info(f"本次测试: {len(test_dates)} 天")
    logger.info(f"成功执行: {len(results)}")
    
    total_selected = sum(r['selected_count'] for r in results)
    logger.info(f"总选中股票数: {total_selected}")
    
    if results:
        avg = total_selected / len(results)
        logger.info(f"平均每日选中: {avg:.2f} 只")
    
    logger.info("\n每日详细结果:")
    for r in results:
        status_icon = "🔥" if r['selected_count'] > 0 else "➖"
        logger.info(f"  {status_icon} {r['date']}: {r['sector_code']} - {r['selected_count']}只")
        if r['selected_stocks']:
            logger.info(f"      选中: {r['selected_stocks']}")
    
    logger.info("="*60)

if __name__ == "__main__":
    main()
