#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI模块
包含AI提示词和AI调用相关功能
"""

from .prompts import get_prompt, SANLONG_KLINE_PROMPT, FENXI_PROMPT, KLINE_PROMPT
from .trae_client import TraeAIClient, trae_client

__all__ = [
    "get_prompt",
    "SANLONG_KLINE_PROMPT",
    "FENXI_PROMPT",
    "KLINE_PROMPT",
    "TraeAIClient",
    "trae_client"
]
