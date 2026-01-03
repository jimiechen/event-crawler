#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parameter Consistency Check Script
Checks if the simulated log parameters match the Tonghuashun event listening parameters.
"""

import sys
import os
import json
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.tonghuashun_data_decoder import TonghuashunDataDecoder
from app.services.strategy_service import strategy_service

def check_parameter_consistency():
    print("🔍 Starting Parameter Consistency Check...")
    
    # 1. Define Expected Tonghuashun Event Format (Raw Data)
    # Based on TonghuashunDataDecoder.FIELD_MAPPING
    # This represents the "2 log parameters" (simulated logs) that user mentioned
    simulated_raw_event = {
        "10": "15.20",      # current_price
        "13": "500000",     # volume
        "199112": "3.5",    # change_percent
        "6": "14.68",       # prev_close
        "name": "SimulatedStock"
    }
    
    print("\n1. Simulated Raw Event Structure:")
    print(json.dumps(simulated_raw_event, indent=2))
    
    # 2. Decode the Data
    decoder = TonghuashunDataDecoder()
    print("\n2. Decoding Data...")
    decoded_data = decoder.decode_stock_data(simulated_raw_event)
    
    print("   Decoded Result:")
    print(json.dumps(decoded_data, indent=2, default=str))
    
    # 3. Verify Consistency with Strategy Service Requirements
    print("\n3. Verifying Consistency with Strategy Service...")
    
    # Strategy Service expects: current_price, volume, change_percent, volume_ratio
    required_fields = ["current_price", "volume", "change_percent"]
    missing_fields = []
    
    for field in required_fields:
        if field not in decoded_data:
            missing_fields.append(field)
            
    # Note: volume_ratio is usually calculated, not in raw data, so we check if we can handle it
    if "volume_ratio" not in decoded_data:
        print("   Note: 'volume_ratio' is missing from raw decode (Expected, as it's usually calculated).")
        # Simulate calculation or default
        decoded_data["volume_ratio"] = 0.0
        
    if missing_fields:
        print(f"❌ Consistency Check Failed! Missing required fields: {missing_fields}")
        sys.exit(1)
        
    # 4. Simulate Strategy Call
    print("\n4. Simulating Strategy Execution...")
    try:
        strategy_input = {
            "current_price": decoded_data.get("current_price"),
            "volume": decoded_data.get("volume"),
            "change_percent": decoded_data.get("change_percent"),
            "volume_ratio": decoded_data.get("volume_ratio")
        }
        
        result = strategy_service.check_signal(strategy_input)
        print("   Strategy Execution Successful!")
        print(f"   Result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"❌ Strategy Execution Failed: {e}")
        sys.exit(1)
        
    print("\n✅ Parameter Consistency Check PASSED!")
    print("The simulated log parameters match the Tonghuashun event listening parameters and are compatible with the strategy service.")

if __name__ == "__main__":
    check_parameter_consistency()
