#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新指定板块股票的今天收盘价和成交量
通过备注字段中的板块名称来过滤
"""

import sys
import os
import time
from datetime import date
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

import requests
from loguru import logger


class SectorPriceUpdater:
    """板块价格更新器"""
    
    def __init__(self, sector_filter: str = None):
        self