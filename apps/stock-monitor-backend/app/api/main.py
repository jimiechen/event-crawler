#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同花顺股票监控系统 - FastAPI服务器
接收Chrome插件传来的股票数据
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import asyncio
import sys
import os
import json
import redis

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.services.stock_data_service import StockDataService, StockInfo, StockData
from app.utils.database_pool import init_database, close_database
from app.utils.data_deduplication import init_deduplication_manager
from app.config.settings import get_settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 获取配置
settings = get_settings()

# 初始化Redis客户端
redis_client = None
try:
    if settings.redis_url:
        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    else:
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=True
        )
    # 测试连接
    redis_client.ping()
    logger.info("Redis连接成功")
except Exception as e:
    logger.warning(f"Redis连接失败: {e}")
    redis_client = None

# 创建FastAPI应用
app = FastAPI(
    title="同花顺股票监控系统API",
    description="接收Chrome插件传来的股票数据",
    version="1.0.0"
)

# 注册爬虫控制器
try:
    from . import crawler_controller
    app.include_router(crawler_controller.router)
except ImportError:
    logger.warning("未找到爬虫控制器，跳过注册")

# 注册Cookie控制器
try:
    from . import cookie_controller
    app.include_router(cookie_controller.router)
except ImportError:
    logger.warning("未找到Cookie控制器，跳过注册")

# 注册定时任务控制器
try:
    from . import timed_task_controller
    app.include_router(timed_task_controller.router)
except ImportError:
    logger.warning("未找到定时任务控制器，跳过注册")

# 注册作业控制器 (JobController)
try:
    from . import job_controller
    app.include_router(job_controller.router)
except ImportError as e:
    logger.warning(f"未找到作业控制器，跳过注册: {e}")

# 注册测试工具控制器
try:
    from . import test_tool_controller
    app.include_router(test_tool_controller.router)
except ImportError:
    logger.warning("未找到测试工具控制器，跳过注册")

# 注册问财控制器
try:
    from . import wencai_controller
    app.include_router(wencai_controller.router)
except ImportError as e:
    logger.warning(f"未找到问财控制器，跳过注册: {e}")

# 注册股票同步控制器
try:
    from . import stock_sync_controller
    app.include_router(stock_sync_controller.router)
except ImportError as e:
    logger.warning(f"未找到股票同步控制器，跳过注册: {e}")

# 注册排名控制器
try:
    from . import ranking_controller
    app.include_router(ranking_controller.router)
except ImportError as e:
    logger.warning(f"未找到排名控制器，跳过注册: {e}")

# 注册测试页面控制器
try:
    from . import test_page_controller
    app.include_router(test_page_controller.router)
except ImportError as e:
    logger.warning(f"未找到测试页面控制器，跳过注册: {e}")

# 注册MCP控制器
# try:
from . import mcp_controller
app.include_router(mcp_controller.router)
# except ImportError as e:
#     logger.warning(f"未找到MCP控制器，跳过注册: {e}")

# 注册Okooo解析控制器
try:
    from . import okooo_parser_controller
    app.include_router(okooo_parser_controller.router)
    logger.info("Okooo解析控制器注册成功")
except ImportError as e:
    logger.warning(f"未找到Okooo解析控制器，跳过注册: {e}")

# 注册通达信选股控制器
try:
    from . import tdx_selection_controller
    app.include_router(tdx_selection_controller.router)
    logger.info("通达信选股控制器注册成功")
except ImportError as e:
    logger.warning(f"未找到通达信选股控制器，跳过注册: {e}")

# 注册通达信日线数据控制器
try:
    from . import tdx_daily_controller
    app.include_router(tdx_daily_controller.router)
    logger.info("通达信日线数据控制器注册成功")
except ImportError as e:
    logger.warning(f"未找到通达信日线数据控制器，跳过注册: {e}")

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
stock_service: Optional[StockDataService] = None


# Pydantic模型定义
class StockInfoModel(BaseModel):
    """股票信息模型"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    market: Optional[str] = Field(None, description="市场类型")


class StockDataModel(BaseModel):
    """股票数据模型"""
    code: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    price: Optional[float] = Field(None, description="当前价格")
    change: Optional[float] = Field(None, description="涨跌额")
    change_percent: Optional[float] = Field(None, description="涨跌幅")
    volume: Optional[int] = Field(None, description="成交量")
    turnover: Optional[float] = Field(None, description="成交额")
    high: Optional[float] = Field(None, description="最高价")
    low: Optional[float] = Field(None, description="最低价")
    open_price: Optional[float] = Field(None, description="开盘价")
    close_price: Optional[float] = Field(None, description="收盘价")
    timestamp: Optional[datetime] = Field(None, description="数据时间戳")
    source_url: Optional[str] = Field(None, description="数据来源URL")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="原始数据")


class BatchStockDataModel(BaseModel):
    """批量股票数据模型"""
    stocks: List[StockDataModel] = Field(..., description="股票数据列表")
    source: Optional[str] = Field(None, description="数据来源")
    timestamp: Optional[datetime] = Field(None, description="批次时间戳")


class ResponseModel(BaseModel):
    """通用响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")


# 启动和关闭事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global stock_service
    try:
        # 初始化数据库连接池
        db_pool = await init_database()
        logger.info("数据库连接池初始化成功")
        
        # 初始化数据去重管理器
        init_deduplication_manager(db_pool)
        logger.info("数据去重管理器初始化成功")
        
        # 初始化股票数据服务
        stock_service = StockDataService()
        logger.info("股票数据服务初始化成功")

        # 启动定时任务调度器
        try:
            from app.services.scheduler_service import scheduler_service
            scheduler_service.start()
            logger.info("定时任务调度器启动成功")
        except ImportError as e:
            logger.warning(f"定时任务调度器导入失败: {e}")
        except Exception as e:
            logger.warning(f"定时任务调度器启动失败: {e}")
        
        logger.info("同花顺股票监控系统API启动成功")
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    try:
        # 关闭数据库连接池
        await close_database()
        logger.info("数据库连接池已关闭")
        
        logger.info("同花顺股票监控系统API已关闭")
        
    except Exception as e:
        logger.error(f"应用关闭失败: {e}")


# API路由定义
@app.get("/", response_model=ResponseModel)
async def root():
    """根路径"""
    return ResponseModel(
        success=True,
        message="同花顺股票监控系统API运行正常",
        data={"version": "1.0.0", "status": "running"}
    )


@app.get("/health", response_model=ResponseModel)
async def health_check():
    """健康检查"""
    try:
        # 检查数据库连接
        from app.utils.database_pool import get_pool_status
        db_status = await get_pool_status()
        
        return ResponseModel(
            success=True,
            message="系统健康状态良好",
            data={
                "database": db_status,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@app.get("/api/v1/health", response_model=ResponseModel)
async def health_check_v1():
    """健康检查 (V1 API)"""
    return await health_check()


@app.post("/api/stocks/info", response_model=ResponseModel)
async def receive_stock_info(stocks: List[StockInfoModel]):
    """接收股票信息数据"""
    try:
        if not stock_service:
            raise HTTPException(status_code=500, detail="股票数据服务未初始化")
        
        # 转换为内部数据格式
        stock_list = []
        for stock in stocks:
            stock_list.append({
                'code': stock.code,
                'name': stock.name,
                'market': stock.market or 'unknown'
            })
        
        # 同步股票信息到数据库
        count = await stock_service.sync_stock_info(stock_list)
        
        logger.info(f"接收到股票信息: {len(stocks)} 条，同步成功: {count} 条")
        
        return ResponseModel(
            success=True,
            message=f"股票信息同步成功，共处理 {count} 条数据",
            data={"processed_count": count, "total_count": len(stocks)}
        )
        
    except Exception as e:
        logger.error(f"接收股票信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理股票信息失败: {str(e)}")





@app.post("/api/v1/stock/data", response_model=ResponseModel)
async def receive_stock_data(batch_data: BatchStockDataModel):
    """接收股票实时数据"""
    try:
        if not stock_service:
            raise HTTPException(status_code=500, detail="股票数据服务未初始化")
        
        # 转换为内部数据格式
        stock_data_list = []
        for stock in batch_data.stocks:
            stock_data = {
                'code': stock.code,
                'name': stock.name or '',
                'price': stock.price or 0,
                'change_amount': stock.change or 0,
                'change_percent': stock.change_percent or 0,
                'volume': stock.volume or 0,
                'turnover': stock.turnover or 0,
                'high': stock.high or 0,
                'low': stock.low or 0,
                'open_price': stock.open_price or 0,
                'prev_close': stock.close_price or 0,
                'timestamp': stock.timestamp or datetime.now()
            }
            stock_data_list.append(stock_data)
        
        # 直接存储股票数据
        result = await stock_service.store_stock_data(stock_data_list)
        
        logger.info(f"接收到股票数据: {len(batch_data.stocks)} 条，存储结果: {result}")
        
        return ResponseModel(
            success=result['success'],
            message=f"股票数据处理完成，共接收 {len(batch_data.stocks)} 条，存储 {result['stored_count']} 条，重复 {result['duplicate_count']} 条",
            data={
                "received_count": len(batch_data.stocks),
                "stored_count": result['stored_count'],
                "duplicate_count": result['duplicate_count'],
                "source": batch_data.source
            }
        )
        
    except Exception as e:
        logger.error(f"接收股票数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理股票数据失败: {str(e)}")


@app.get("/api/stocks/monitor", response_model=ResponseModel)
async def get_monitor_stocks():
    """获取监控股票列表"""
    try:
        if not stock_service:
            raise HTTPException(status_code=500, detail="股票数据服务未初始化")
        
        stock_codes = await stock_service.get_monitor_stock_list()
        
        stock_list = []
        for stock_code in stock_codes:
            stock_list.append({
                'code': stock_code,
                'name': '',  # 暂时为空，后续可以从stock_info表获取
                'is_active': True,
                'created_at': None
            })
        
        return ResponseModel(
            success=True,
            message=f"获取监控股票列表成功，共 {len(stock_list)} 只股票",
            data=stock_list
        )
        
    except Exception as e:
        logger.error(f"获取监控股票列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取监控股票列表失败: {str(e)}")


@app.post("/api/stocks/monitor/{stock_code}", response_model=ResponseModel)
async def add_monitor_stock(stock_code: str):
    """添加监控股票"""
    try:
        if not stock_service:
            raise HTTPException(status_code=500, detail="股票数据服务未初始化")
        
        success = await stock_service.add_monitor_stock(stock_code)
        
        if success:
            return ResponseModel(
                success=True,
                message=f"股票 {stock_code} 添加到监控列表成功",
                data={"stock_code": stock_code}
            )
        else:
            return ResponseModel(
                success=False,
                message=f"股票 {stock_code} 添加到监控列表失败",
                data={"stock_code": stock_code}
            )
        
    except Exception as e:
        logger.error(f"添加监控股票失败: {e}")
        raise HTTPException(status_code=500, detail=f"添加监控股票失败: {str(e)}")


@app.delete("/api/stocks/monitor/{stock_code}", response_model=ResponseModel)
async def remove_monitor_stock(stock_code: str):
    """移除监控股票"""
    try:
        if not stock_service:
            raise HTTPException(status_code=500, detail="股票数据服务未初始化")
        
        success = await stock_service.remove_monitor_stock(stock_code)
        
        if success:
            return ResponseModel(
                success=True,
                message=f"股票 {stock_code} 从监控列表移除成功",
                data={"stock_code": stock_code}
            )
        else:
            return ResponseModel(
                success=False,
                message=f"股票 {stock_code} 从监控列表移除失败",
                data={"stock_code": stock_code}
            )
        
    except Exception as e:
        logger.error(f"移除监控股票失败: {e}")
        raise HTTPException(status_code=500, detail=f"移除监控股票失败: {str(e)}")


@app.get("/api/stock/data/{stock_code}", response_model=ResponseModel)
async def get_stock_data(stock_code: str):
    """获取指定股票的历史数据"""
    try:
        if not stock_service:
            raise HTTPException(status_code=500, detail="股票数据服务未初始化")
        
        # 获取股票数据
        stock_data = await stock_service.get_stock_data_by_code(stock_code)
        
        return ResponseModel(
            success=True,
            message=f"获取股票 {stock_code} 数据成功",
            data=stock_data
        )
        
    except Exception as e:
        logger.error(f"获取股票数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取股票数据失败: {str(e)}")


@app.get("/api/stats", response_model=ResponseModel)
async def get_statistics():
    """获取系统统计信息"""
    try:
        if not stock_service:
            raise HTTPException(status_code=500, detail="股票数据服务未初始化")
        
        stats = await stock_service.get_statistics()
        
        return ResponseModel(
            success=True,
            message="获取统计信息成功",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@app.post("/api/tonghuashun/raw-data", response_model=ResponseModel)
async def receive_tonghuashun_raw_data(raw_data: List[Dict[str, Any]]):
    """接收同花顺原始网络数据"""
    try:
        if not stock_service:
            raise HTTPException(status_code=500, detail="股票数据服务未初始化")
        
        # 过滤同花顺相关的数据
        tonghuashun_data = []
        for item in raw_data:
            url = item.get('url', '')
            if ('t.10jqka.com.cn' in url and 
                ('userPersonal' in url or 'getSelfStockWithMarket' in url)):
                tonghuashun_data.append(item)
        
        if not tonghuashun_data:
            return ResponseModel(
                success=True,
                message="未发现同花顺相关数据",
                data={"processed_count": 0, "total_count": len(raw_data)}
            )
        
        # 处理同花顺数据
        logger.info(f"开始处理同花顺数据，共 {len(tonghuashun_data)} 条")
        
        result = await stock_service.process_tonghuashun_raw_data(tonghuashun_data)
        
        logger.info(f"同花顺数据处理结果: {result}")
        
        return ResponseModel(
            success=True,
            message=f"同花顺数据处理完成，接收 {len(tonghuashun_data)} 条，解析 {result.get('parsed_stocks', 0)} 只股票，存储 {result.get('stored_count', 0)} 条",
            data={
                "received_count": len(tonghuashun_data),
                "processed_count": result.get('processed_items', 0),
                "total_count": len(raw_data),
                "stored_count": result.get('stored_count', 0),
                "parsed_stocks_count": result.get('parsed_stocks', 0)
            }
        )
        
    except Exception as e:
        logger.error(f"接收同花顺原始数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理同花顺原始数据失败: {str(e)}")


@app.delete("/api/test-data/clear")
async def clear_test_data():
    """清空测试数据"""
    try:
        from app.services.stock_data_service import StockDataService
        
        service = StockDataService()
        result = await service.clear_test_data()
        
        if result['success']:
            return ResponseModel(
                success=True,
                message=result['message'],
                data={
                    "deleted_stock_data": result['deleted_stock_data'],
                    "deleted_dedup_logs": result['deleted_dedup_logs'],
                    "deleted_tonghuashun_data": result['deleted_tonghuashun_data']
                }
            )
        else:
            return ResponseModel(
                success=False,
                message=f"清空测试数据失败: {result['error']}"
            )
    except Exception as e:
        logger.error(f"清空测试数据失败: {e}")
        return ResponseModel(
            success=False,
            message=f"清空测试数据失败: {str(e)}"
        )





# 主函数
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )