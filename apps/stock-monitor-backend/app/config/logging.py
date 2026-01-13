#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置
"""

import sys
import os
from pathlib import Path
from loguru import logger
from .settings import get_settings


def setup_logging():
    """配置日志系统"""
    settings = get_settings()
    
    # 移除默认的日志处理器
    logger.remove()
    
    # 日志格式
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # 控制台日志
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # 文件日志（如果配置了日志文件）
    if settings.log_file:
        # 确保日志目录存在
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            settings.log_file,
            format=log_format,
            level=settings.log_level,
            rotation=settings.log_rotation,
            retention=settings.log_retention,
            compression="zip",
            backtrace=True,
            diagnose=True
        )
    
    # 错误日志文件
    if settings.log_file:
        error_log_file = str(log_path.parent / f"error_{log_path.name}")
        logger.add(
            error_log_file,
            format=log_format,
            level="ERROR",
            rotation=settings.log_rotation,
            retention=settings.log_retention,
            compression="zip",
            backtrace=True,
            diagnose=True
        )
    
    # 数据一致性日志文件
    consistency_log_path = str(log_path.parent / "data_consistency.log")
    logger.add(
        consistency_log_path,
        format=log_format,
        level="INFO",
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # 验收日志文件
    acceptance_log_path = str(log_path.parent / "acceptance.log")
    logger.add(
        acceptance_log_path,
        format=log_format,
        level="INFO",
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # 设置第三方库的日志级别
    import logging
    
    # 设置SQLAlchemy日志级别
    if settings.db_echo:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
        logging.getLogger("sqlalchemy.pool").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    
    # 设置uvicorn日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    
    # 设置FastAPI日志级别
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    logger.info(f"日志系统已配置 - 级别: {settings.log_level}")
    if settings.log_file:
        logger.info(f"日志文件: {settings.log_file}")


def get_logger(name: str = None):
    """获取日志记录器"""
    if name:
        return logger.bind(name=name)
    return logger