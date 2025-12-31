#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.stock import TonghuashunStock, WencaiStock


pytestmark = pytest.mark.api


async def _count(session, model):
    result = await session.execute(select(model))
    return len(result.scalars().all())


@pytest.mark.asyncio
async def test_ths_writes_to_ths_table_only(test_client: AsyncClient, test_session):
    sample_stock = {
        # 简化的同花顺实时数据字段，代码和若干关键指标
        "000001": {
            "name": "平安银行",
            "6": "12.30",   # 今开
            "7": "12.35",   # 现价
            "8": "12.50",   # 最高
            "9": "12.20",   # 最低
            "10": "12.40",  # 昨收
            "13": "1000000",# 成交量
            "19": "12345678",# 成交额
            "199112": "0.81" # 量比
        }
    }

    payload = {
        "source": "tonghuashun",
        "data": [
            {"hs": sample_stock, "urlTimestamp": "20250101_120000"}
        ]
    }

    resp = await test_client.post("/api/v1/stocks/tonghuashun/raw-data", json=payload)
    assert resp.status_code == 200

    ths_count = await _count(test_session, TonghuashunStock)
    wencai_count = await _count(test_session, WencaiStock)

    assert ths_count >= 1
    assert wencai_count == 0


@pytest.mark.asyncio
async def test_wencai_writes_to_wencai_table_only(test_client: AsyncClient, test_session):
    # 构造一个可解析的简易HTML表格（标准 table 结构）
    html = (
        "<table>"
        "<tr><th>序号</th><th>代码</th><th>名称</th><th>现价</th><th>成交量</th></tr>"
        "<tr><td>1</td><td>000001</td><td>平安银行</td><td>12.34</td><td>100000</td></tr>"
        "</table>"
    )

    payload = {
        "html_content": html,
        "batch_name": "测试批次",
        "crawl_url": "http://example.com"
    }

    resp = await test_client.post("/api/v1/wencai/parse", json=payload)
    assert resp.status_code == 200

    ths_count = await _count(test_session, TonghuashunStock)
    wencai_count = await _count(test_session, WencaiStock)

    assert wencai_count >= 1
    # 不应影响同花顺表
    assert ths_count >= 0