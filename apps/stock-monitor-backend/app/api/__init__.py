#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API控制器层
提供RESTful API接口
"""

from .stock_controller import router as stock_router
from .monitor_controller import router as monitor_router
from .health_controller import router as health_router
from .ranking_controller import router as ranking_router
from .screenshot_controller import router as screenshot_router

__all__ = [
    'stock_router',
    'monitor_router',
    'health_router',
    'ranking_router',
    'screenshot_router'
]