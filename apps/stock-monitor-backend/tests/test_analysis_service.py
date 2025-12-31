from app.services.analysis_service import analyze_volume_price_relationship


def test_analyze_volume_price_relationship_basic():
    daily = []
    for i in range(10):
        daily.append({
            'trade_date': f'202501{str(i+1).zfill(2)}',
            'open': 10 + i * 0.2,
            'high': 10.5 + i * 0.2,
            'low': 9.5 + i * 0.2,
            'close': 10 + i * 0.2,
            'volume': 1000 + i * 50,
            'amount': 100000 + i * 5000,
        })
    result = analyze_volume_price_relationship(daily, window_size=5)
    assert isinstance(result, list)
    assert len(result) == 10
    assert 'volume_price_pattern' in result[-1]
    assert 'vp_action_hint' in result[-1]

