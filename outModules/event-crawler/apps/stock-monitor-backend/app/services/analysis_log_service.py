from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def save_volume_price_logs(session: AsyncSession, code: str, analysis: List[Dict]) -> int:
    if not analysis:
        return 0
    count = 0
    for row in analysis:
        trade_date = str(row.get('trade_date'))
        position_label = row.get('position_label')
        volume_status = row.get('volume_status')
        price_status = row.get('price_status')
        volume_price_pattern = row.get('volume_price_pattern')
        vp_action_hint = row.get('vp_action_hint')
        details = {
            'price_change_pct': row.get('price_change_pct'),
            'volume_change_pct': row.get('volume_change_pct'),
            'vol_ma5': row.get('vol_ma5'),
            'vol_ma10': row.get('vol_ma10'),
            'position_label': position_label,
            'volume_status': volume_status,
            'price_status': price_status,
        }
        sql = text(
            """
            INSERT INTO volume_price_logs
            (code, trade_date, position_label, volume_status, price_status, volume_price_pattern, vp_action_hint, details)
            VALUES (:code, STR_TO_DATE(:trade_date, '%Y%m%d'), :position_label, :volume_status, :price_status, :volume_price_pattern, :vp_action_hint, CAST(:details AS JSON))
            ON DUPLICATE KEY UPDATE 
                position_label=VALUES(position_label),
                volume_status=VALUES(volume_status),
                price_status=VALUES(price_status),
                volume_price_pattern=VALUES(volume_price_pattern),
                vp_action_hint=VALUES(vp_action_hint),
                details=VALUES(details)
            """
        )
        await session.execute(sql, {
            'code': code,
            'trade_date': trade_date,
            'position_label': position_label,
            'volume_status': volume_status,
            'price_status': price_status,
            'volume_price_pattern': volume_price_pattern,
            'vp_action_hint': vp_action_hint,
            'details': json_dumps(details)
        })
        count += 1
    await session.commit()
    return count


def json_dumps(obj: Dict) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


async def get_volume_price_logs(session: AsyncSession, code: str, start_date: Optional[str], end_date: Optional[str]) -> List[Dict]:
    where = ["code = :code"]
    params = {'code': code}
    if start_date:
        where.append("trade_date >= STR_TO_DATE(:start_date, '%Y-%m-%d')")
        params['start_date'] = start_date
    if end_date:
        where.append("trade_date <= STR_TO_DATE(:end_date, '%Y-%m-%d')")
        params['end_date'] = end_date
    sql = text(f"SELECT code, DATE_FORMAT(trade_date, '%Y-%m-%d') AS trade_date, position_label, volume_status, price_status, volume_price_pattern, vp_action_hint, details, created_at FROM volume_price_logs WHERE {' AND '.join(where)} ORDER BY trade_date")
    rows = (await session.execute(sql, params)).mappings().all()
    result: List[Dict] = []
    for r in rows:
        d = r['details'] if isinstance(r['details'], dict) else None
        result.append({
            'code': r['code'],
            'trade_date': r['trade_date'],
            'position_label': r['position_label'],
            'volume_status': r['volume_status'],
            'price_status': r['price_status'],
            'volume_price_pattern': r['volume_price_pattern'],
            'vp_action_hint': r['vp_action_hint'],
            'details': d
        })
    return result


async def delete_volume_price_logs(session: AsyncSession, code: str, start_date: Optional[str], end_date: Optional[str]) -> int:
    where = ["code = :code"]
    params = {'code': code}
    if start_date:
        where.append("trade_date >= STR_TO_DATE(:start_date, '%Y-%m-%d')")
        params['start_date'] = start_date
    if end_date:
        where.append("trade_date <= STR_TO_DATE(:end_date, '%Y-%m-%d')")
        params['end_date'] = end_date
    sql = text(f"DELETE FROM volume_price_logs WHERE {' AND '.join(where)}")
    result = await session.execute(sql, params)
    await session.commit()
    return result.rowcount if hasattr(result, 'rowcount') else 0


async def save_analysis_logs(session: AsyncSession, logs: List[Dict]) -> int:
    if not logs:
        return 0
    count = 0
    for log in logs:
        sql = text(
            """
            INSERT INTO analysis_logs
            (code, trade_date, log_type, rule_number, rule_content, vp_action_hint, details)
            VALUES (:code, STR_TO_DATE(:trade_date, '%Y-%m-%d'), :log_type, :rule_number, :rule_content, :vp_action_hint, CAST(:details AS JSON))
            ON DUPLICATE KEY UPDATE 
                rule_content=VALUES(rule_content),
                vp_action_hint=VALUES(vp_action_hint),
                details=VALUES(details)
            """
        )
        await session.execute(sql, {
            'code': log.get('code'),
            'trade_date': log.get('trade_date'),
            'log_type': log.get('log_type'),
            'rule_number': log.get('rule_number'),
            'rule_content': log.get('rule_content'),
            'vp_action_hint': log.get('vp_action_hint'),
            'details': json_dumps(log.get('details') or {})
        })
        count += 1
    await session.commit()
    return count


async def get_analysis_logs(session: AsyncSession, code: str, start_date: Optional[str], end_date: Optional[str]) -> List[Dict]:
    where = ["code = :code"]
    params = {'code': code}
    if start_date:
        where.append("trade_date >= STR_TO_DATE(:start_date, '%Y-%m-%d')")
        params['start_date'] = start_date
    if end_date:
        where.append("trade_date <= STR_TO_DATE(:end_date, '%Y-%m-%d')")
        params['end_date'] = end_date
    sql = text(f"SELECT code, DATE_FORMAT(trade_date, '%Y-%m-%d') AS trade_date, log_type, rule_number, rule_content, vp_action_hint, details, created_at FROM analysis_logs WHERE {' AND '.join(where)} ORDER BY trade_date")
    rows = (await session.execute(sql, params)).mappings().all()
    result: List[Dict] = []
    for r in rows:
        d = r['details'] if isinstance(r['details'], dict) else None
        result.append({
            'code': r['code'],
            'trade_date': r['trade_date'],
            'log_type': r['log_type'],
            'rule_number': r['rule_number'],
            'rule_content': r['rule_content'],
            'vp_action_hint': r['vp_action_hint'],
            'details': d
        })
    return result


async def delete_analysis_logs(session: AsyncSession, code: str, start_date: Optional[str], end_date: Optional[str]) -> int:
    where = ["code = :code"]
    params = {'code': code}
    if start_date:
        where.append("trade_date >= STR_TO_DATE(:start_date, '%Y-%m-%d')")
        params['start_date'] = start_date
    if end_date:
        where.append("trade_date <= STR_TO_DATE(:end_date, '%Y-%m-%d')")
        params['end_date'] = end_date
    sql = text(f"DELETE FROM analysis_logs WHERE {' AND '.join(where)}")
    result = await session.execute(sql, params)
    await session.commit()
    return result.rowcount if hasattr(result, 'rowcount') else 0
