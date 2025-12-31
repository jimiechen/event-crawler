#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare数据采集服务
"""

import os
import tushare as ts
import pandas as pd
import asyncio
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from loguru import logger
import time

class TushareRateLimiter:
    def __init__(self, calls_per_minute=45):
        self.calls_per_minute = calls_per_minute
        self.interval = 60.0 / calls_per_minute
        self.last_call_time = 0
        self.lock = asyncio.Lock()

    async def wait(self):
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_call_time
            if elapsed < self.interval:
                delay = self.interval - elapsed
                # logger.debug(f"Tushare rate limit: waiting {delay:.2f}s")
                await asyncio.sleep(delay)
            self.last_call_time = time.time()

# Global limiter instance (safe margin 45/min)
global_rate_limiter = TushareRateLimiter(calls_per_minute=45)

from app.config.settings import Settings, get_settings
from app.repositories.stock_daily_repository import StockDailyRepository
from app.database import DatabaseManager

TOKEN_FILE_PATH = "/Users/mac/ok-mcp/token/tushare.token"

def get_token_from_file() -> Optional[str]:
    """从本地文件读取Token"""
    if os.path.exists(TOKEN_FILE_PATH):
        try:
            with open(TOKEN_FILE_PATH, "r", encoding="utf-8") as f:
                token = f.read().strip()
                if token:
                    return token
        except Exception as e:
            logger.warning(f"读取Token文件失败: {e}")
    return None

class TushareService:
    def __init__(self, db_manager: DatabaseManager):
        self.settings = get_settings()
        
        # Unset proxy to avoid connection issues
        for k in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
            if k in os.environ:
                logger.info(f"Removing proxy env var {k} for Tushare service")
                os.environ.pop(k)
                
        self.db_manager = db_manager
        self.repository = StockDailyRepository(db_manager)
        self.pro = None
        self._init_tushare()

    def _init_tushare(self):
        token = self.settings.tushare_token
        if not token:
            token = get_token_from_file()
            if token:
                logger.info(f"已从 {TOKEN_FILE_PATH} 加载 Tushare Token")
        
        if token:
            # ts.set_token(token) # 避免写入本地文件导致潜在的IO问题或格式错误
            self.pro = ts.pro_api(token)
        else:
            logger.warning("未配置Tushare Token，数据采集功能将不可用")

    def _normalize_code(self, code: str) -> str:
        """标准化股票代码(移除后缀)"""
        if "." in code:
            return code.split(".")[0]
        return code

    def _add_suffix(self, code: str) -> str:
        """添加Tushare所需的后缀"""
        if "." in code:
            return code
        # 简单判断：60/68开头为SH，00/30开头为SZ，43/83/87为BJ
        if code.startswith(("60", "68")):
            return f"{code}.SH"
        elif code.startswith(("00", "30")):
            return f"{code}.SZ"
        elif code.startswith(("43", "83", "87")):
            return f"{code}.BJ"
        return code

    def get_stock_basic(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取单个股票的基本信息 (带缓存)
        """
        if not self.pro:
            return None
        
        # 尝试从缓存读取
        cache_file = os.path.join(os.path.dirname(TOKEN_FILE_PATH), "stock_basic_cache.json")
        import json
        cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
            except Exception:
                pass
        
        if code in cache:
            # Check if cache is fresh enough (e.g. 30 days) - simplified to just use it for now
            logger.info(f"Using cached stock basic info for {code}")
            return cache[code]

        try:
            # Normalize code
            ts_code = self._add_suffix(code)
            
            # Call Tushare API
            # fields: ts_code,symbol,name,area,industry,market,list_date
            df = self.pro.stock_basic(ts_code=ts_code, fields='ts_code,symbol,name,market')
            
            if df is None or df.empty:
                return None
            
            # Return the first record as dict
            result = df.iloc[0].to_dict()
            
            # Save to cache
            cache[code] = result
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.warning(f"Failed to write stock basic cache: {e}")
                
            return result
            
        except Exception as e:
            logger.error(f"获取股票 {code} 基本信息失败: {e}")
            return None

    async def get_daily(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        获取单只股票日线数据 (异步)
        """
        if not self.pro:
            return None
            
        try:
            await global_rate_limiter.wait()
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            )
            return df
        except Exception as e:
            logger.error(f"Tushare get_daily failed for {ts_code}: {e}")
            return None

    def _validate_data(self, item: Dict[str, Any]) -> bool:
        """
        数据质量校验
        校验规则：
        1. 价格必须大于0
        2. 最高价必须大于等于最低价
        3. 成交量必须大于等于0
        4. 关键字段不能为空
        """
        try:
            # 检查空值
            if any(item.get(k) is None for k in ['open', 'close', 'high', 'low', 'vol']):
                logger.warning(f"数据校验失败: 存在空值 - {item.get('code')} {item.get('trade_date')}")
                return False
                
            # 价格校验
            if item['open'] <= 0 or item['close'] <= 0 or item['high'] <= 0 or item['low'] <= 0:
                logger.warning(f"数据校验失败: 价格异常 - {item.get('code')} {item.get('trade_date')}")
                return False
                
            if item['high'] < item['low']:
                logger.warning(f"数据校验失败: 最高价小于最低价 - {item.get('code')} {item.get('trade_date')}")
                return False
                
            # 成交量校验
            if item['vol'] < 0:
                logger.warning(f"数据校验失败: 成交量为负 - {item.get('code')} {item.get('trade_date')}")
                return False
                
            # 涨跌幅异常校验 (比如单日超过25%，可能是数据错误，除了新股)
            # 这里简单校验一下开盘收盘是否偏离太远
            # if abs(item['close'] - item['open']) / item['open'] > 0.3:
            #    logger.warning(f"数据警告: 价格波动过大 - {item.get('code')}")
            
            return True
        except Exception as e:
            logger.error(f"数据校验出错: {e}")
            return False

    async def refresh_stock_pool(self) -> Dict[str, Any]:
        """
        刷新股票池 (从自选股和问财汇总)
        """
        logger.info("开始刷新股票池")
        start_time = datetime.now()
        
        await self.repository.save_task_log({
            "task_name": "refresh_stock_pool",
            "status": "running",
            "message": "Start refreshing stock pool from MonitorList and Wencai"
        })
        
        try:
            stats = await self.repository.sync_stock_pool()
            
            duration = (datetime.now() - start_time).total_seconds()
            message = f"Refreshed stock pool: Self-selected={stats.get('self_selected', 0)}, Wencai={stats.get('wencai', 0)}"
            
            await self.repository.save_task_log({
                "task_name": "refresh_stock_pool",
                "status": "success",
                "message": message,
                "duration": duration
            })
            
            return {"status": "success", "stats": stats}
            
        except Exception as e:
            logger.error(f"刷新股票池失败: {e}")
            await self.repository.save_task_log({
                "task_name": "refresh_stock_pool",
                "status": "failed",
                "message": str(e),
                "duration": (datetime.now() - start_time).total_seconds()
            })
            return {"status": "failed", "message": str(e)}

    async def sync_all_stock_info(self) -> Dict[str, Any]:
        """
        同步全市场股票基本信息 (从Tushare获取所有A股列表)
        """
        if not self.pro:
            return {"status": "failed", "message": "Tushare Token not configured"}
        
        logger.info("开始同步全市场股票基本信息")
        start_time = datetime.now()
        
        # 记录任务开始
        await self.repository.save_task_log({
            "task_name": "sync_all_stock_info",
            "status": "running",
            "message": "Start syncing all stock list from Tushare"
        })
        
        try:
            # 获取股票列表
            # list_status='L' 表示上市状态
            df = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,market,list_date')
            )
            
            if df is None or df.empty:
                logger.warning("未获取到股票列表数据")
                await self.repository.save_task_log({
                    "task_name": "sync_all_stock_info",
                    "status": "failed",
                    "message": "No data received from Tushare",
                    "duration": (datetime.now() - start_time).total_seconds()
                })
                return {"status": "failed", "message": "No data received from Tushare"}
            
            logger.info(f"获取到 {len(df)} 条股票信息")
            
            # 保存到数据库
            count = 0
            async with self.db_manager.get_session() as session:
                from app.models.stock import StockInfo
                from sqlalchemy.dialects.mysql import insert as mysql_insert
                
                # Prepare data
                data_list = []
                for _, row in df.iterrows():
                    code = row['symbol']
                    ts_code = row['ts_code']
                    # market = 'sh' if ts_code.endswith('.SH') else ('sz' if ts_code.endswith('.SZ') else 'bj' if ts_code.endswith('.BJ') else 'unknown')
                    market = ""
                    
                    data_list.append({
                        "code": code,
                        "name": row['name'],
                        "market": market,
                        "is_active": True,
                        "created_at": datetime.now(),
                        "updated_at": datetime.now()
                    })
                
                # Batch upsert
                chunk_size = 1000
                for i in range(0, len(data_list), chunk_size):
                    chunk = data_list[i:i+chunk_size]
                    stmt = mysql_insert(StockInfo).values(chunk)
                    update_dict = {
                        "name": stmt.excluded.name,
                        "market": stmt.excluded.market,
                        "is_active": stmt.excluded.is_active,
                        "updated_at": stmt.excluded.updated_at
                    }
                    on_duplicate_key_stmt = stmt.on_duplicate_key_update(**update_dict)
                    await session.execute(on_duplicate_key_stmt)
                    count += len(chunk)
                
                await session.commit()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # 记录任务结束
            await self.repository.save_task_log({
                "task_name": "sync_all_stock_info",
                "status": "success",
                "message": f"Synced {count} stocks info",
                "duration": duration
            })
                
            return {"status": "success", "count": count}
            
        except Exception as e:
            logger.error(f"同步股票基本信息失败: {e}")
            await self.repository.save_task_log({
                "task_name": "sync_all_stock_info",
                "status": "failed",
                "message": str(e),
                "duration": (datetime.now() - start_time).total_seconds()
            })
            return {"status": "failed", "message": str(e)}

    async def check_connectivity(self) -> bool:
        """检查Tushare连接状态"""
        if not self.pro:
            return False
        try:
            # Run in executor
            loop = asyncio.get_event_loop()
            # Simple query: check trade calendar for today
            today = datetime.now().strftime("%Y%m%d")
            res = await loop.run_in_executor(
                None, 
                lambda: self.pro.trade_cal(start_date=today, end_date=today)
            )
            return True # If no exception, it's connected (even if empty)
        except Exception as e:
            logger.warning(f"Tushare connectivity check failed: {e}")
            return False

    async def sync_daily_data(self, mode: str = "incremental", codes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        同步日线数据
        :param mode: "full" (全量250天) 或 "incremental" (增量)
        :param codes: 指定同步的股票代码列表，如果为None则获取所有目标股票
        """
        if not self.pro:
            return {"status": "failed", "message": "Tushare Token not configured"}

        start_time = datetime.now()
        logger.info(f"开始执行日线数据同步，模式: {mode}, 指定股票数: {len(codes) if codes else 'All'}")

        try:
            # 1. 获取目标股票列表
            target_codes = codes
            if not target_codes:
                target_codes = await self.repository.get_target_stocks()
            
            if not target_codes:
                logger.info("没有需要同步的股票")
                return {"status": "success", "message": "No target stocks"}

            total = len(target_codes)
            
            # 记录任务开始
            log_data = {
                "task_name": f"sync_daily_data_{mode}",
                "status": "running",
                "message": f"Start syncing {total} stocks"
            }
            if codes and len(codes) == 1:
                log_data["stock_code"] = codes[0]
            await self.repository.save_task_log(log_data)

            # 并发控制
            # Tushare 免费接口限制通常为每分钟50-80次
            # 为了安全，我们限制为每1.5秒一次请求
            semaphore = asyncio.Semaphore(1) 
            
            async def process_stock(code):
                async with semaphore:
                    try:
                        # 速率限制
                        await asyncio.sleep(1.5)
                        ts_code = self._add_suffix(code)
                        
                        # 确定时间范围
                        end_date_str = datetime.now().strftime("%Y%m%d")
                        start_date_str = ""
                        
                        if mode == "full":
                            # 250交易日，取365自然日作为缓冲
                            start_date = datetime.now() - timedelta(days=365) 
                            start_date_str = start_date.strftime("%Y%m%d")
                        else:
                            # 增量：取最后一天
                            last_date = await self.repository.get_latest_date(self._normalize_code(code))
                            if last_date:
                                start_date = last_date + timedelta(days=1)
                                if start_date > date.today():
                                    return 0 # 已经是最新
                                start_date_str = start_date.strftime("%Y%m%d")
                            else:
                                # 无记录，根据需求默认从配置日期开始 (默认 2025-12-22)
                                try:
                                    start_date = datetime.strptime(self.settings.tushare_incremental_start_date, "%Y-%m-%d").date()
                                except ValueError:
                                    logger.warning(f"Invalid date format in settings: {self.settings.tushare_incremental_start_date}, using default 2025-12-22")
                                    start_date = date(2025, 12, 22)
                                start_date_str = start_date.strftime("%Y%m%d")

                        # 调用Tushare
                        # 增加重试机制
                        retry_count = 3
                        df = None
                        logger.debug(f"Fetching {ts_code} from {start_date_str} to {end_date_str}")
                        for attempt in range(retry_count):
                            try:
                                df = await asyncio.get_event_loop().run_in_executor(
                                    None, 
                                    lambda: self.pro.daily(ts_code=ts_code, start_date=start_date_str, end_date=end_date_str)
                                )
                                
                                # 获取复权因子
                                if df is not None and not df.empty:
                                    adj_df = await asyncio.get_event_loop().run_in_executor(
                                        None,
                                        lambda: self.pro.adj_factor(ts_code=ts_code, start_date=start_date_str, end_date=end_date_str)
                                    )
                                    if adj_df is not None and not adj_df.empty:
                                        df = pd.merge(df, adj_df[['trade_date', 'adj_factor']], on='trade_date', how='left')
                                
                                break
                            except Exception as e:
                                err_str = str(e)
                                if "每分钟最多访问" in err_str or "visit frequency" in err_str:
                                    logger.warning(f"触发Tushare频率限制，暂停60秒... ({code})")
                                    await asyncio.sleep(60)
                                    # 重试次数不减？或者让它继续重试
                                    # 这里仅仅是sleep，下一次循环会继续尝试
                                
                                if attempt < retry_count - 1:
                                    await asyncio.sleep(1) # 重试等待
                                else:
                                    logger.warning(f"获取股票 {code} 数据失败，已重试{retry_count}次: {e}")
                                    return 0
                        
                        if df is None or df.empty:
                            return 0

                        # 数据转换与入库
                        data_list = []
                        for _, row in df.iterrows():
                            item = {
                                "code": self._normalize_code(row['ts_code']),
                                "trade_date": datetime.strptime(row['trade_date'], "%Y%m%d").date(),
                                "open": row['open'],
                                "close": row['close'],
                                "high": row['high'],
                                "low": row['low'],
                                "vol": row['vol'],
                                "amount": row['amount'],
                                "adj_factor": row['adj_factor'] if 'adj_factor' in row and pd.notna(row['adj_factor']) else None
                            }
                            if self._validate_data(item):
                                data_list.append(item)
                        
                        if data_list:
                            count = await self.repository.batch_save_daily_data(data_list)
                            logger.debug(f"Saved {count} records for {code}")
                            return count
                        return 0
                        
                    except Exception as e:
                        logger.error(f"处理股票 {code} 失败: {e}")
                        return 0

            # 创建任务列表
            tasks = [process_stock(code) for code in target_codes]
            
            # 执行任务
            results = await asyncio.gather(*tasks)
            success_count = sum(1 for r in results if r > 0)
            failed_count = total - success_count
            
            if failed_count > 0:
                logger.warning(f"同步完成，但有 {failed_count} 只股票失败")
                if failed_count > 5 and failed_count > total * 0.1: # 超过5只且超过10%失败
                    logger.error("ALERT: 股票数据同步失败率过高! 请检查Tushare Token或网络连接")

            duration = (datetime.now() - start_time).total_seconds()
            
            # 记录任务结束
            log_data = {
                "task_name": f"sync_daily_data_{mode}",
                "status": "success",
                "message": f"Synced {success_count}/{total} stocks",
                "duration": duration
            }
            if codes and len(codes) == 1:
                log_data["stock_code"] = codes[0]
            await self.repository.save_task_log(log_data)
            
            logger.info(f"日线数据同步完成，成功处理: {success_count}/{total}，耗时: {duration:.2f}s")
            return {
                "status": "success", 
                "total": total, 
                "processed": success_count, 
                "duration": duration
            }

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"日线数据同步全局失败: {e}")
            log_data = {
                "task_name": f"sync_daily_data_{mode}",
                "status": "failed",
                "message": str(e),
                "duration": duration
            }
            if codes and len(codes) == 1:
                log_data["stock_code"] = codes[0]
            await self.repository.save_task_log(log_data)
            return {"status": "failed", "message": str(e)}

    async def sync_wencai_stocks(self) -> Dict[str, Any]:
        """
        同步问财股票池数据
        """
        if not self.pro:
            return {"status": "failed", "message": "Tushare Token not configured"}
            
        logger.info("开始同步问财股票池数据")
        
        try:
            # 1. 获取问财股票列表
            # 由于repository在TushareService中是StockDailyRepository，它没有get_wencai_stock_codes方法
            # 我们需要临时使用StockRepository，或者直接在StockDailyRepository中添加类似方法
            # 也可以直接通过session查询，因为models都导入了
            
            wencai_codes = []
            async with self.repository.db_manager.get_session() as session:
                from app.models.stock import StockInfo
                from sqlalchemy import select
                # 修复: 原逻辑从WencaiStock获取，但现在StockInfo合并了，应该从StockInfo获取 source='wencai' 的
                # 或者依然从 WencaiStock 表获取? 用户说 "删除StockPool表，以及相关代码引用"，没说删除 WencaiStock
                # 但是用户又说 "问财数据页面...数据库stockinfo表股票名称是正确的"
                # 这暗示 StockInfo 现在是主表。
                # 不过，为了兼容性和正确性，我们应该从 StockInfo 获取 source='wencai' 的
                
                result = await session.execute(
                    select(StockInfo.code).where(StockInfo.source == 'wencai')
                )
                wencai_codes = list(result.scalars().all())
                
                # 如果从StockInfo没查到，尝试从WencaiStock兜底?
                if not wencai_codes:
                     from app.models.stock import WencaiStock
                     result = await session.execute(select(WencaiStock.stock_code).distinct())
                     wencai_codes = list(result.scalars().all())

            if not wencai_codes:
                logger.info("问财股票池为空")
                return {"status": "success", "message": "No wencai stocks"}
                
            # 2. 复用sync_daily_data逻辑 (默认增量)
            return await self.sync_daily_data(mode="incremental", codes=wencai_codes)
            
        except Exception as e:
            logger.error(f"同步问财股票池数据失败: {e}")
            return {"status": "failed", "message": str(e)}

def get_daily(code: str, days: int = 120):
    """
    获取日线数据 (兼容旧接口)
    """
    settings = get_settings()
    token = settings.tushare_token
    
    if not token:
        token = get_token_from_file()
    
    if not token:
        logger.warning("未配置Tushare Token")
        return []
        
    try:
        ts.set_token(token)
        pro = ts.pro_api()
        
        # Calculate start date
        end_date = datetime.now()
        start_date = end_date - timedelta(days=int(days * 1.5)) # Estimate trading days vs calendar days
        
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        
        # Normalize code
        if not code.endswith(".SZ") and not code.endswith(".SH") and not code.endswith(".BJ"):
            if code.startswith(("60", "68")):
                code = f"{code}.SH"
            elif code.startswith(("00", "30")):
                code = f"{code}.SZ"
            elif code.startswith(("43", "83", "87")):
                code = f"{code}.BJ"
                
        df = pro.daily(ts_code=code, start_date=start_str, end_date=end_str)
        if df is None or df.empty:
            return []
            
        # Convert to list of dicts
        records = df.to_dict('records')
        # Sort by date asc
        records.sort(key=lambda x: x['trade_date'])
        return records
    except Exception as e:
        logger.error(f"get_daily failed: {e}")
        return []
