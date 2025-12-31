from starlette.testclient import TestClient
import types

from app.main import app


def test_daily_endpoint(monkeypatch):
    from app.services import tushare_service as svc
    def fake_get_daily(code, start_date=None, end_date=None, days=None):
        return [
            {'trade_date': '20250101', 'open': 10, 'high': 12, 'low': 9.5, 'close': 11, 'volume': 1000, 'amount': 100000},
            {'trade_date': '20250102', 'open': 11, 'high': 12.5, 'low': 10.5, 'close': 12, 'volume': 1200, 'amount': 120000},
        ]
    monkeypatch.setattr(svc, 'get_daily', fake_get_daily)
    client = TestClient(app)
    r = client.get('/api/stock/daily/000001.SZ?days=2')
    assert r.status_code == 200
    data = r.json()
    assert data['success'] is True
    assert isinstance(data['data'], list)
    assert len(data['data']) == 2

