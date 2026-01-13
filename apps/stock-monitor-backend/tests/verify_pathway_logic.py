import asyncio
from datetime import date, timedelta
from typing import List, Dict, Any
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.services.pathway_engine import PathwayVolumePriceEngine

def test_pathway_logic():
    print("Testing Pathway Logic...")
    
    # Mock Engine (DB session not needed for calculate_tags)
    engine = PathwayVolumePriceEngine(None)
    
    # --- Case 1: 3x Volume ---
    print("\nCase 1: 3x Volume")
    history_vol = [
        {'trade_date': date(2025, 1, 2), 'vol': 3000, 'close': 10.0, 'open': 10.0, 'high': 10.0, 'low': 10.0}, # Today
        {'trade_date': date(2025, 1, 1), 'vol': 1000, 'close': 10.0, 'open': 10.0, 'high': 10.0, 'low': 10.0}, # Yesterday
    ]
    tags = engine.calculate_tags(history_vol)
    tag_names = [t['name'] for t in tags]
    print(f"Tags: {tag_names}")
    assert '3倍量' in tag_names
    print("PASS")

    # --- Case 2: Limit Up ---
    print("\nCase 2: Limit Up")
    history_limit = [
        {'trade_date': date(2025, 1, 2), 'vol': 1000, 'close': 11.0, 'open': 10.0, 'high': 11.0, 'low': 10.0}, # Today (11.0)
        {'trade_date': date(2025, 1, 1), 'vol': 1000, 'close': 10.0, 'open': 10.0, 'high': 10.0, 'low': 10.0}, # Yesterday (10.0)
    ]
    # 11.0 / 10.0 - 1 = 0.1 > 0.095
    tags = engine.calculate_tags(history_limit)
    tag_names = [t['name'] for t in tags]
    print(f"Tags: {tag_names}")
    assert '涨停' in tag_names
    print("PASS")

    # --- Case 3: Low Volume (Strict) ---
    print("\nCase 3: Low Volume (Strict)")
    # Need 6 days for 5-day low volume
    # Today: 50. Past 5 days: [100, 100, 100, 100, 100] -> min 100. 50 < 100.
    history_low = [
        {'trade_date': date(2025, 1, 6), 'vol': 50, 'close': 10.0, 'open': 10.0, 'high': 10.0, 'low': 10.0}, # Today
        {'trade_date': date(2025, 1, 5), 'vol': 100, 'close': 10.0, 'open': 10.0, 'high': 10.0, 'low': 10.0},
        {'trade_date': date(2025, 1, 4), 'vol': 100, 'close': 10.0, 'open': 10.0, 'high': 10.0, 'low': 10.0},
        {'trade_date': date(2025, 1, 3), 'vol': 100, 'close': 10.0, 'open': 10.0, 'high': 10.0, 'low': 10.0},
        {'trade_date': date(2025, 1, 2), 'vol': 100, 'close': 10.0, 'open': 10.0, 'high': 10.0, 'low': 10.0},
        {'trade_date': date(2025, 1, 1), 'vol': 100, 'close': 10.0, 'open': 10.0, 'high': 10.0, 'low': 10.0},
    ]
    tags = engine.calculate_tags(history_low)
    tag_names = [t['name'] for t in tags]
    print(f"Tags: {tag_names}")
    assert '5日地量' in tag_names
    # Also check ratio: 50 < avg(100)*0.6 = 60. So '地量比率' should also be there.
    assert '地量比率' in tag_names
    print("PASS")

    # --- Case 4: Bullish Engulfing ---
    print("\nCase 4: Bullish Engulfing")
    # Yesterday: Down (Open 10, Close 9). Today: Up (Open 8.5, Close 10.5) -> Envelopes yesterday
    history_engulf = [
        {'trade_date': date(2025, 1, 2), 'vol': 1000, 'close': 10.5, 'open': 8.5, 'high': 10.5, 'low': 8.5}, # Today
        {'trade_date': date(2025, 1, 1), 'vol': 1000, 'close': 9.0, 'open': 10.0, 'high': 10.0, 'low': 9.0}, # Yesterday
    ]
    tags = engine.calculate_tags(history_engulf)
    tag_names = [t['name'] for t in tags]
    print(f"Tags: {tag_names}")
    assert '阳包阴' in tag_names
    print("PASS")

    print("\nAll tests passed!")

if __name__ == "__main__":
    test_pathway_logic()
