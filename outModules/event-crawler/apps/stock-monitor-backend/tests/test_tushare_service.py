import pandas as pd
import types

from app.services.tushare_service import get_daily, normalize_code


class FakePro:
    def daily(self, ts_code=None, start_date=None, end_date=None):
        data = {
            'trade_date': ['20250101', '20250102'],
            'open': [10.0, 11.0],
            'high': [12.0, 12.5],
            'low': [9.5, 10.5],
            'close': [11.0, 12.0],
            'vol': [1000, 1200],
            'amount': [100000, 120000],
        }
        return pd.DataFrame(data)


def test_normalize_code():
    assert normalize_code('000001.SZ') == '000001.SZ'
    assert normalize_code('SZ000001') == '000001.SZ'
    assert normalize_code('SH600000') == '600000.SH'
    assert normalize_code('000001') == '000001.SZ'
    assert normalize_code('600000') == '600000.SH'


def test_get_daily_monkeypatch(monkeypatch):
    from app.services import tushare_service as svc
    monkeypatch.setattr(svc, '_get_client', lambda: FakePro())
    data = get_daily('SZ000001', days=2)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]['trade_date'] == '20250101'
    assert 'volume' in data[0]

