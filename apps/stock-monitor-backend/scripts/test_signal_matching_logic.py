
import pytest
import asyncio
from typing import Dict, Any, List
from app.services.ai_decision_service import AIDecisionService, AIDecisionConfig

# Mock classes to avoid full instantiation with DB dependencies if possible
# But AIDecisionService.__init__ is lightweight.

def test_ai_decision_service_match_signals():
    # 1. Setup Service
    config = AIDecisionConfig(api_key="mock", base_url="mock", model="mock")
    service = AIDecisionService(config)

    # 2. Mock Stock Context
    stock_context = {
        "stock_code": "000001",
        "current_price": 10.5,
        "change_percent": 6.2,
        "volume": 100000,
        "ma5": 10.2,
        "ma20": 9.8,
        "tags": [
            {"name": "3倍量", "score": 300},
            {"name": "平台突破", "score": 400}
        ]
    }

    # 3. Mock Active Signals
    active_signals = [
        # Type A: Tag-based
        {
            "name": "Volume Spike",
            "description": "3x Volume detected",
            "trigger_condition": {
                "source": "ashare_quant",
                "tag": "3倍量"
            }
        },
        # Type B: Metric-based
        {
            "name": "Big Drop",
            "description": "Price dropped more than 5%",
            "trigger_condition": {
                "metric": "change_percent",
                "operator": "<",
                "value": -5.0
            }
        },
        {
            "name": "Big Rise",
            "description": "Price rose more than 5%",
            "trigger_condition": {
                "metric": "change_percent",
                "operator": ">",
                "value": 5.0
            }
        },
        # Type C: Technical Indicator
        {
            "name": "Above MA20",
            "description": "Price is above 20-day moving average",
            "trigger_condition": {
                "metric": "current_price",
                "operator": ">",
                "compare_metric": "ma20"
            }
        },
        # Type D: Simple Value Comparison
        {
            "name": "Price > 10",
            "description": "Price is above 10",
            "trigger_condition": {
                "metric": "current_price",
                "operator": ">",
                "value": 10.0
            }
        }
    ]

    # 4. Run Matching using the Service Method
    # Note: _match_signals is protected, but we can access it for testing
    triggered = service._match_signals(stock_context, active_signals)
    
    print("Triggered Signals:", triggered.keys())
    
    # 5. Assertions
    assert "Volume Spike" in triggered
    assert "Big Rise" in triggered
    assert "Price > 10" in triggered
    assert "Above MA20" in triggered
    assert "Big Drop" not in triggered
    
    # Verify content of triggered signal
    assert triggered["Big Rise"]["value"] == 6.2
    assert triggered["Big Rise"]["operator"] == ">"
    assert triggered["Big Rise"]["threshold"] == 5.0
    
    assert triggered["Above MA20"]["threshold"] == 9.8

if __name__ == "__main__":
    test_ai_decision_service_match_signals()
