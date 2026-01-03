from typing import Optional, List, Dict
import os
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..services.tushare_service import get_daily
from ..services.analysis_service import analyze_volume_price_relationship, calculate_morphology, find_three_day_patterns, analyze_rules
from ..services.analysis_log_service import save_analysis_logs, get_analysis_logs, delete_analysis_logs


router = APIRouter(prefix="/api/trading-rules", tags=["交易规则与形态"])


@router.post("/analyze/{code}")
async def analyze(code: str, days: Optional[int] = Query(120, ge=1, le=2000), db: AsyncSession = Depends(get_db_session)):
    daily = get_daily(code, days=days)
    vp = analyze_volume_price_relationship(daily, window_size=60)
    morph = calculate_morphology(daily, window_size=60)
    patterns = find_three_day_patterns(daily)
    rules = analyze_rules(daily)
    logs: List[Dict] = []
    for r in vp:
        logs.append({ 'code': code, 'trade_date': _fmt_date(r['trade_date']), 'log_type': 'volume_price_analysis', 'rule_number': None, 'rule_content': None, 'vp_action_hint': r.get('vp_action_hint'), 'details': {
            'volume_status': r.get('volume_status'), 'price_status': r.get('price_status'), 'position_label': r.get('position_label'), 'price_change_pct': r.get('price_change_pct'), 'vol_ma5': r.get('vol_ma5'), 'vol_ma10': r.get('vol_ma10')
        } })
    for m in morph:
        logs.append({ 'code': code, 'trade_date': _fmt_date(m['trade_date']), 'log_type': 'morphology_analysis', 'rule_number': None, 'rule_content': None, 'vp_action_hint': None, 'details': m })
    for p in patterns:
        logs.append({ 'code': code, 'trade_date': _fmt_date(p['trade_date']), 'log_type': 'three_day_pattern', 'rule_number': None, 'rule_content': None, 'vp_action_hint': None, 'details': p })
    for a in rules:
        logs.append({ 'code': code, 'trade_date': _fmt_date(a['trade_date']), 'log_type': 'rule_match', 'rule_number': a.get('rule_number'), 'rule_content': a.get('rule_content'), 'vp_action_hint': a.get('vp_action_hint'), 'details': a.get('details') })
    if os.getenv('DEMO_MODE'):
        return { 'code': 0, 'msg': '分析完成', 'count': len(logs), 'logs': logs }
    await save_analysis_logs(db, logs)
    return { 'code': 0, 'msg': '分析完成', 'count': len(logs) }


@router.get("/logs/{code}")
async def get_logs(code: str, start_date: Optional[str] = Query(None), end_date: Optional[str] = Query(None), db: AsyncSession = Depends(get_db_session)):
    if os.getenv('DEMO_MODE') and start_date and end_date:
        import datetime as dt
        s = dt.datetime.strptime(start_date, '%Y-%m-%d')
        e = dt.datetime.strptime(end_date, '%Y-%m-%d')
        days = max(1, (e - s).days + 1)
        daily = get_daily(code, days=days)
        vp = analyze_volume_price_relationship(daily, window_size=60)
        morph = calculate_morphology(daily, window_size=60)
        patterns = find_three_day_patterns(daily)
        rules = analyze_rules(daily)
        logs: List[Dict] = []
        for r in vp:
            d = _fmt_date(r['trade_date'])
            if d >= start_date and d <= end_date:
                logs.append({ 'code': code, 'trade_date': d, 'log_type': 'volume_price_analysis', 'rule_number': None, 'rule_content': None, 'vp_action_hint': r.get('vp_action_hint'), 'details': {
                    'volume_status': r.get('volume_status'), 'price_status': r.get('price_status'), 'position_label': r.get('position_label'), 'price_change_pct': r.get('price_change_pct'), 'vol_ma5': r.get('vol_ma5'), 'vol_ma10': r.get('vol_ma10')
                } })
        for m in morph:
            d = _fmt_date(m['trade_date'])
            if d >= start_date and d <= end_date:
                logs.append({ 'code': code, 'trade_date': d, 'log_type': 'morphology_analysis', 'rule_number': None, 'rule_content': None, 'vp_action_hint': None, 'details': m })
        for p in patterns:
            d = _fmt_date(p['trade_date'])
            if d >= start_date and d <= end_date:
                logs.append({ 'code': code, 'trade_date': d, 'log_type': 'three_day_pattern', 'rule_number': None, 'rule_content': None, 'vp_action_hint': None, 'details': p })
        for a in rules:
            d = _fmt_date(a['trade_date'])
            if d >= start_date and d <= end_date:
                logs.append({ 'code': code, 'trade_date': d, 'log_type': 'rule_match', 'rule_number': a.get('rule_number'), 'rule_content': a.get('rule_content'), 'vp_action_hint': a.get('vp_action_hint'), 'details': a.get('details') })
        return { 'code': 0, 'msg': 'ok', 'logs': logs }
    data = await get_analysis_logs(db, code, start_date, end_date)
    return { 'code': 0, 'msg': 'ok', 'logs': data }


@router.delete("/logs/{code}")
async def clear_logs(code: str, start_date: Optional[str] = Query(None), end_date: Optional[str] = Query(None), db: AsyncSession = Depends(get_db_session)):
    deleted = await delete_analysis_logs(db, code, start_date, end_date)
    return { 'code': 0, 'msg': '已清空', 'deleted': deleted }


def _fmt_date(d: str) -> str:
    if not d:
        return ''
    if '-' in d:
        return d
    if len(d) == 8:
        return f"{d[0:4]}-{d[4:6]}-{d[6:8]}"
    return d
