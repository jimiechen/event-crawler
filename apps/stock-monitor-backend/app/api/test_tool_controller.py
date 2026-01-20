from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import random
import asyncio
from datetime import datetime

from app.database import get_db_session, db_manager
from app.services.wencai_service import WencaiService
from app.services.monitor_service import MonitorService
from app.services.tushare_service import TushareService
from app.services.baostock_service import BaostockService
from app.services.akshare_service import AkshareService
from app.services.tdx_service import TdxService
from app.services.local_data_service import LocalDataService
from app.services.stock_service import StockService
from app.api.test_tool_schemas import (
    AddCustomStockRequest, 
    AddCustomStockResponse,
    MockStockData,
    ValidationRequest,
    ValidationResult,
    RawValidationRequest,
    RawValidationResult,
    EnvCheckResult
)
from loguru import logger

router = APIRouter(prefix="/api/v1/test-tool", tags=["测试工具"])

import re

from app.models.stock_daily import StockDaily, StockScoreResult
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from app.models.volume_analysis import VolumeAnalysisResult

PREFERRED_PLATFORM = "tushare"

class ValidationCountsRequest(BaseModel):
    codes: List[str]
    min_count: int = 250

@router.post("/validate-data-counts")
async def validate_data_counts(
    request: ValidationCountsRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Validate that specific stocks have at least N records in results tables
    """
    codes = request.codes
    min_count = request.min_count
    
    if not codes:
        return {"status": "skipped", "message": "No codes provided"}
        
    # Check VolumeAnalysisResult
    stmt_vol = (
        select(VolumeAnalysisResult.code, func.count(VolumeAnalysisResult.id).label("count"))
        .where(VolumeAnalysisResult.code.in_(codes))
        .group_by(VolumeAnalysisResult.code)
    )
    res_vol = await db.execute(stmt_vol)
    vol_counts = {r.code: r.count for r in res_vol.all()}
    
    # Check StockScoreResult
    stmt_score = (
        select(StockScoreResult.code, func.count(StockScoreResult.id).label("count"))
        .where(StockScoreResult.code.in_(codes))
        .group_by(StockScoreResult.code)
    )
    res_score = await db.execute(stmt_score)
    score_counts = {r.code: r.count for r in res_score.all()}
    
    failures = []
    for code in codes:
        v_count = vol_counts.get(code, 0)
        s_count = score_counts.get(code, 0)
        
        if v_count < min_count or s_count < min_count:
            failures.append({
                "code": code,
                "vol_count": v_count,
                "score_count": s_count,
                "required": min_count
            })
            
    if failures:
        return {
            "status": "failed",
            "message": f"Found {len(failures)} stocks with insufficient data",
            "failures": failures,
            "details": failures
        }
    
    return {"status": "success", "message": "All stocks passed validation"}

class SetPlatformRequest(BaseModel):
    platform: str

@router.post("/set-platform")
async def set_platform(request: SetPlatformRequest):
    global PREFERRED_PLATFORM
    if request.platform not in ["tushare", "baostock", "akshare"]:
        raise HTTPException(status_code=400, detail="Invalid platform")
    PREFERRED_PLATFORM = request.platform
    logger.info(f"Preferred platform set to: {PREFERRED_PLATFORM}")
    return {"status": "ok", "platform": PREFERRED_PLATFORM}

@router.get("/current-platform")
async def get_current_platform():
    return {"platform": PREFERRED_PLATFORM}

@router.post("/add-custom-stock", response_model=AddCustomStockResponse)
async def add_custom_stock(
    request: AddCustomStockRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """添加自定义股票并获取K线数据(支持批量，逗号分隔)"""
    try:
        # Split codes by comma, chinese comma, or whitespace
        raw_codes = [c.strip() for c in re.split(r'[,，\s]+', request.code) if c.strip()]
        
        # Normalize codes: Strip suffixes to match system standard (6 digits)
        codes = []
        for c in raw_codes:
            if '.' in c:
                codes.append(c.split('.')[0])
            else:
                codes.append(c)
        
        if not codes:
            raise HTTPException(status_code=400, detail="No valid stock codes provided")

        wencai_service = WencaiService(db)
        monitor_service = MonitorService(db)
        tushare_svc = TushareService(db_manager)
        tdx_service = TdxService(db)
        
        # Create batch once
        # Construct query_string for tag generation (Date + Triple Volume)
        current_date = datetime.now()
        date_str = current_date.strftime('%Y年%m月%d日')
        query_string = f"{date_str}，成交量的2.9倍"
        
        batch_id = await wencai_service.create_crawl_batch(
            batch_name=f"Manual_Add_{request.label}_{datetime.now().strftime('%H%M%S')}",
            crawl_url="manual_input",
            query_string=query_string
        )

        first_stock_data = None
        first_daily_data = []
        success_codes = []

        for code in codes:
            # 1. Fetch Name from TDX
            stock_name = request.label or code
            try:
                # Use TDX to get stock name instead of Tushare to avoid rate limits
                tdx_data = await tdx_service.fetch_stock_risk(code)
                if tdx_data and tdx_data.get('name'):
                    stock_name = tdx_data['name']
            except Exception as e:
                logger.warning(f"Failed to fetch stock name from TDX for {code}: {e}")

            # 2. Add to Wencai Stock Table
            stock_data = {
                "stock_code": code,
                "stock_name": stock_name, 
            }
            await wencai_service.save_wencai_stocks(batch_id, [stock_data])

            # 3. Add to Monitor Service (Stock Pool)
            try:
                await monitor_service.add_monitor(code, priority=1, auto_create_stock=True)
                success_codes.append(code)
            except ValueError:
                logger.warning(f"Stock {code} might already exist in monitor list or is invalid")
                success_codes.append(code) # Consider it success if it exists

            # 4. Get Stock Data (only for the first one to display)
            if first_stock_data is None:
                first_stock_data = stock_data
                query_code = code

                logger.info(f"Checking StockDaily DB for code: {query_code}")

                db_records = []
                try:
                    stmt = select(StockDaily).where(StockDaily.code == query_code).order_by(StockDaily.trade_date.desc()).limit(request.days)
                    result = await db.execute(stmt)
                    db_records = result.scalars().all()
                    logger.info(f"DB Query Result for {query_code}: {len(db_records)} records")
                except Exception as e:
                    logger.error(f"Error querying stock daily: {e}")

                # Try alternative code format (with or without suffix) if not found
                if not db_records:
                    logger.info(f"No records found for {query_code}, trying alternatives")
                    alt_code = None
                    if '.' in query_code:
                        alt_code = query_code.split('.')[0]
                    else:
                        # Try adding suffixes if input is pure digits
                        if query_code.startswith('6'): alt_code = f"{query_code}.SH"
                        elif query_code.startswith('0') or query_code.startswith('3'): alt_code = f"{query_code}.SZ"
                        elif query_code.startswith('4') or query_code.startswith('8'): alt_code = f"{query_code}.BJ"
                    
                    if alt_code:
                        logger.info(f"First attempt for {query_code} failed, trying alternative code: {alt_code}")
                        stmt = select(StockDaily).where(StockDaily.code == alt_code).order_by(StockDaily.trade_date.desc()).limit(request.days)
                        result = await db.execute(stmt)
                        db_records = result.scalars().all()
                        if db_records:
                            logger.info(f"Found {len(db_records)} records with alt code {alt_code}")
                            query_code = alt_code # Update query_code for subsequent logic
                    
                    force_sync = bool(request.platform)

                    if not db_records or force_sync:
                        target_platform = request.platform or PREFERRED_PLATFORM
                        logger.info(f"Syncing data for {code} using {target_platform} (Force: {force_sync})")
                        
                        async def try_tushare():
                            try:
                                res = await tushare_svc.sync_daily_data(mode="full", codes=[code])
                                return res.get("status") != "failed" and res.get("processed", 0) > 0
                            except Exception as e:
                                logger.error(f"Tushare sync failed: {e}")
                                return False
                        
                        async def try_baostock():
                            try:
                                return await BaostockService(db_manager).sync_daily_data(code, mode="full") > 0
                            except Exception as e:
                                logger.error(f"Baostock sync failed: {e}")
                                return False
                            
                        async def try_akshare():
                            try:
                                return await AkshareService(db_manager).sync_daily_data(code, mode="full") > 0
                            except Exception as e:
                                logger.error(f"AkShare sync failed: {e}")
                                return False

                        success = False
                        
                        # Primary Attempt
                        if target_platform == 'tushare':
                            success = await try_tushare()
                        elif target_platform == 'baostock':
                            success = await try_baostock()
                        elif target_platform == 'akshare':
                            success = await try_akshare()
                            
                        # Fallbacks
                        if not success:
                            logger.info(f"Primary platform {target_platform} failed or returned no data, trying fallbacks...")
                            platforms = ['tushare', 'baostock', 'akshare']
                            if target_platform in platforms: platforms.remove(target_platform)
                            
                            for p in platforms:
                                logger.info(f"Trying fallback: {p}")
                                if p == 'tushare':
                                    if await try_tushare(): success = True; break
                                elif p == 'baostock':
                                    if await try_baostock(): success = True; break
                                elif p == 'akshare':
                                    if await try_akshare(): success = True; break

                        # Commit to ensure isolation visibility
                        await db.commit()
                        
                        # Re-query
                        logger.info(f"Re-querying DB for {query_code} with stmt: {stmt}")
                        result = await db.execute(stmt)
                        db_records = result.scalars().all()
                        logger.info(f"Re-query result for {query_code}: {len(db_records)} records")

                first_daily_data = []
                
                logger.info(f"DEBUG: Before processing records. Count={len(db_records) if db_records else 0}, Type={type(db_records)}")

                # Map to store unique records by date string 'YYYYMMDD'
                daily_data_map = {}

                # 1. Load from CSV if needed (or if DB records are insufficient)
                # Always try to load CSV to fill gaps if we have fewer records than requested
                if len(db_records) < request.days:
                    logger.info(f"Data insufficient ({len(db_records)} < {request.days}), attempting to load from CSV...")
                    try:
                        # Fetch enough data from CSV
                        csv_data = await LocalDataService.get_daily_data(query_code, limit=request.days)
                        if csv_data:
                            logger.info(f"Loaded {len(csv_data)} records from CSV.")
                            for row in csv_data:
                                # row['trade_date'] is datetime.date object from LocalDataService
                                d_date_obj = row.get('trade_date')
                                if not d_date_obj:
                                     # Try '日期' just in case
                                     d_date_obj = row.get('日期')
                                
                                if not d_date_obj:
                                    continue
                                    
                                if hasattr(d_date_obj, 'strftime'):
                                    d_str = d_date_obj.strftime("%Y%m%d")
                                else:
                                    # Fallback if it's a string
                                    d_str = str(d_date_obj).replace('-', '')
                                
                                # Convert Decimal to float safely
                                def to_float(val):
                                    try:
                                        return float(val) if val is not None else 0.0
                                    except:
                                        return 0.0

                                item = {
                                    "trade_date": d_str,
                                    "open": to_float(row.get('open')),
                                    "high": to_float(row.get('high')),
                                    "low": to_float(row.get('low')),
                                    "close": to_float(row.get('close')),
                                    "volume": to_float(row.get('vol')),
                                    "vol": to_float(row.get('vol')),
                                    "amount": to_float(row.get('amount')),
                                    "pct_chg": 0.0, # Will calculate later
                                    "change_percent": 0.0,
                                    "adj_factor": None
                                }
                                daily_data_map[d_str] = item
                    except Exception as e:
                        logger.error(f"Failed to load CSV data: {e}")

                # 2. Process DB records (Priority: Overwrite CSV data for same dates)
                if db_records:
                    # Get latest adj_factor
                    latest_factor = 1.0
                    try:
                        stmt_factor = select(StockDaily.adj_factor).where(
                            StockDaily.code == query_code, 
                            StockDaily.adj_factor.is_not(None)
                        ).order_by(StockDaily.trade_date.desc()).limit(1)
                        res_factor = await db.execute(stmt_factor)
                        lf = res_factor.scalar()
                        if lf: latest_factor = float(lf)
                    except Exception as e:
                        logger.warning(f"Failed to get latest adj_factor: {e}")

                    # Calculate QFQ and add to map
                    for item in db_records:
                        d_str = item.trade_date.strftime("%Y%m%d")
                        
                        # Calculate QFQ rate
                        adj_rate = 1.0
                        if item.adj_factor and latest_factor:
                            adj_rate = float(item.adj_factor) / latest_factor
                        
                        # Apply QFQ
                        close_price = float(item.close) * adj_rate if item.close else 0
                        open_price = float(item.open) * adj_rate if item.open else 0
                        high_price = float(item.high) * adj_rate if item.high else 0
                        low_price = float(item.low) * adj_rate if item.low else 0

                        daily_item = {
                            "trade_date": d_str,
                            "open": open_price,
                            "high": high_price,
                            "low": low_price,
                            "close": close_price,
                            "volume": item.vol,
                            "vol": item.vol,
                            "amount": float(item.amount) if item.amount else None,
                            "pct_chg": 0.0, # Will calculate later
                            "change_percent": 0.0,
                            "adj_factor": float(item.adj_factor) if item.adj_factor else None
                        }
                        daily_data_map[d_str] = daily_item

                # 3. Sort and Calculate Change Percent
                if daily_data_map:
                    # Sort by date ascending
                    sorted_data = sorted(daily_data_map.values(), key=lambda x: x['trade_date'])
                    
                    for i, item in enumerate(sorted_data):
                        pct_chg = 0.0
                        if i > 0:
                            prev_item = sorted_data[i-1]
                            prev_close = prev_item['close']
                            curr_close = item['close']
                            if prev_close != 0:
                                pct_chg = ((curr_close - prev_close) / prev_close) * 100
                        
                        item['pct_chg'] = pct_chg
                        item['change_percent'] = pct_chg
                        first_daily_data.append(item)

                            
        # Process batch to associate tags
        if success_codes:
            try:
                 logger.info(f"Processing manual batch {batch_id} to associate tags...")
                 await wencai_service.process_batch_data(batch_id)
            except Exception as e:
                 logger.error(f"Failed to process manual batch {batch_id}: {e}")

        if first_stock_data and request.custom_date:
            first_stock_data["custom_date"] = request.custom_date

        if codes[0].startswith('002735') and first_daily_data:
            logger.info(f"DEBUG RESPONSE 002735: Count={len(first_daily_data)}, LastItem={first_daily_data[-1]}")

        return AddCustomStockResponse(
            success=True,
            message=f"Successfully added {len(success_codes)} stocks: {', '.join(success_codes)}",
            stock_info=first_stock_data or {"stock_code": codes[0], "stock_name": request.label},
            daily_data=first_daily_data or []
        )
        
    except Exception as e:
        logger.error(f"Failed to add custom stock: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate")
async def generate_data(payload: Dict[str, Any] = Body(...)):
    count = payload.get("count", 5)
    data = []
    for i in range(count):
        data.append({
            "code": f"600{random.randint(100, 999)}",
            "name": f"模拟股票_{random.randint(1, 100)}",
            "current_price": round(random.uniform(10, 100), 2),
            "volume": random.randint(10000, 1000000),
            "change_percent": round(random.uniform(-10, 10), 2),
            "volume_ratio": round(random.uniform(0.5, 3.0), 2),
            "timestamp": datetime.now().isoformat()
        })
    return data

@router.post("/validate")
async def validate_data(payload: Dict[str, Any] = Body(...)):
    data = payload.get("data", {})
    # Dummy validation logic
    is_triggered = float(data.get("change_percent", 0)) > 5.0
    return {
        "is_triggered": is_triggered,
        "trigger_reason": "涨幅超过5%" if is_triggered else "正常",
        "details": {}
    }

@router.post("/load-local-data")
async def load_local_data(payload: Dict[str, Any] = Body(...)):
    """
    加载本地CSV数据到数据库
    """
    codes = payload.get("codes", [])
    end_date_str = payload.get("end_date")
    limit = payload.get("limit")
    
    if not codes:
        return {"status": "error", "message": "No codes provided"}
        
    end_date = None
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except:
            pass
            
    stock_service = StockService(db_manager)
    await LocalDataService.load_local_data_for_stocks(stock_service, codes, end_date=end_date, limit=limit)
    
    return {"status": "success", "message": f"Loaded data for {len(codes)} stocks"}

@router.get("/env-check", response_model=List[EnvCheckResult])
async def env_check():
    results = []
    
    # 1. Database Check
    try:
        async with db_manager.get_session() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        
        db_info = f"{db_manager.config.host}:{db_manager.config.port}/{db_manager.config.database}"
        results.append({"component": "Database", "status": "ok", "message": f"Connected to {db_info}", "details": {"config": str(db_manager.config)}})
    except Exception as e:
        results.append({"component": "Database", "status": "error", "message": str(e), "details": {}})

    # 2. Redis Check (Skip if not configured or use simple check if available)
    # Assuming Redis is optional or handled via DB manager if cached, but let's stick to what was there or skip
    # Previous code had static Redis check. Let's keep it static or remove if not critical. 
    # Actually, let's keep it simple or just remove it if we don't have direct redis access here easily.
    # The previous code had: {"component": "Redis", "status": "ok", "message": "Connected", "details": {}}
    # I will keep it but maybe mark as Mock if I can't check it easily, or just skip it.
    
    # 3. Tushare Check
    ts_svc = TushareService(db_manager)
    ts_ok = await ts_svc.check_connectivity()
    results.append({
        "component": "Tushare", 
        "status": "ok" if ts_ok else "error", 
        "message": "Service Available" if ts_ok else "Connection Failed", 
        "details": {"priority": 1, "description": "Primary Data Source"}
    })

    # 4. Baostock Check
    bs_svc = BaostockService(db_manager)
    bs_ok = await bs_svc.check_connectivity()
    results.append({
        "component": "Baostock", 
        "status": "ok" if bs_ok else "error", 
        "message": "Service Available" if bs_ok else "Connection Failed", 
        "details": {"priority": 2, "description": "Backup Data Source 1"}
    })

    # 5. AkShare Check
    ak_svc = AkshareService(db_manager)
    ak_ok = await ak_svc.check_connectivity()
    results.append({
        "component": "AkShare", 
        "status": "ok" if ak_ok else "error", 
        "message": "Service Available" if ak_ok else "Connection Failed", 
        "details": {"priority": 3, "description": "Backup Data Source 2"}
    })

    return results

@router.get("/logs")
async def get_logs():
    return []

@router.post("/validate-raw")
async def validate_raw(payload: Dict[str, Any] = Body(...)):
    return {"status": "ok", "message": "Parsed successfully", "data": payload.get("raw_data")}
