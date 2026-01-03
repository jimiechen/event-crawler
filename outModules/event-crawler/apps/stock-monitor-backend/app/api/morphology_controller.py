from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..services.tushare_service import get_daily
from ..services.analysis_service import calculate_morphology, find_three_day_patterns
from ..services.analysis_log_service import save_analysis_logs


router = APIRouter(prefix="/api/morphology", tags=["K线形态分析"])


@router.post("/analyze/{code}")
async def analyze(code: str, days: Optional[int] = Query(120, ge=1, le=2000), db: AsyncSession = Depends(get_db_session)):
    daily = get_daily(code, days=days)
    morph = calculate_morphology(daily, window_size=60)
    patterns = find_three_day_patterns(daily)
    logs: List[Dict] = []
    for m in morph:
        logs.append({ 'code': code, 'trade_date': _fmt_date(m['trade_date']), 'log_type': 'morphology_analysis', 'rule_number': None, 'rule_content': None, 'vp_action_hint': None, 'details': m })
    for p in patterns:
        logs.append({ 'code': code, 'trade_date': _fmt_date(p['trade_date']), 'log_type': 'three_day_pattern', 'rule_number': None, 'rule_content': None, 'vp_action_hint': None, 'details': p })
    await save_analysis_logs(db, logs)
    return { 'code': 0, 'msg': '形态分析完成', 'count': len(logs) }


def _fmt_date(d: str) -> str:
    if not d:
        return ''
    if '-' in d:
        return d
    if len(d) == 8:
        return f"{d[0:4]}-{d[4:6]}-{d[6:8]}"
    return d

