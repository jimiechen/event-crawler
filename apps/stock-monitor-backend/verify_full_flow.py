import json
import asyncio
import aiohttp
import re
import sys

from datetime import datetime as dt

DEBUG_FILE = "/Users/mac/ok-mcp/app/stock-monitor-backend/debug/问财原始数据包含概念和行业.txt"
# Use today's date to verify dynamic tag logic
today_str = dt.now().strftime('%Y年%m月%d日')
today_iso = dt.now().strftime('%Y-%m-%d')
QUERY_STRING = f"{today_str}成交量是前一个工作日成交量的2.9倍以上，非创业版，非科创版，非ST，概念 行业"

async def verify_full_flow():
    print(f"Reading debug file: {DEBUG_FILE}")
    try:
        with open(DEBUG_FILE, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print("Debug file not found!")
        return

    # Extract content logic (copied from test_wencai_debug.py)
    start_marker = "--data-raw $'"
    end_marker = "'" 
    
    s_idx = content.find(start_marker)
    if s_idx == -1:
        print("Could not find start marker")
        return
    
    s_idx += len(start_marker)
    e_idx = content.rfind(end_marker)
    
    if e_idx == -1 or e_idx <= s_idx:
        print("Could not find end marker")
        return
        
    payload_str = content[s_idx:e_idx]
    
    try:
        payload_str = payload_str.replace(r'\"', '"')
        payload_str = payload_str.replace(r'\\', '\\')
        
        data = json.loads(payload_str)
        html_content = data.get('html_content')
        
        if not html_content:
            print("No html_content found in payload")
            return
            
        print(f"Extracted HTML content length: {len(html_content)}")
        
        # 1. Send Parse Request
        request_payload = {
            "html_content": html_content,
            "batch_name": "Verify_Flow_Test",
            "crawl_url": "http://verify.local",
            "query_string": QUERY_STRING
        }
        
        async with aiohttp.ClientSession() as session:
            # Step 1: Parse and Create Batch
            url_parse = "http://localhost:8000/api/v1/wencai/parse"
            print(f"\n[Step 1] Sending request to {url_parse}...")
            async with session.post(url_parse, json=request_payload) as response:
                print(f"Status: {response.status}")
                result = await response.json()
                
                if response.status != 200:
                    print(f"Error: {result}")
                    return

                # BaseResponse structure: { success, data, message }
                data = result.get('data', {})
                batch_id = data.get('batch_id')
                print(f"Batch created with ID: {batch_id}")
                
                if not batch_id:
                    print(f"No batch_id returned! Full result: {result}")
                    return

            # Step 2: Get Batch Info (Verify Tags)
            url_batch = f"http://localhost:8000/api/v1/wencai/batches/{batch_id}"
            print(f"\n[Step 2] Fetching batch info from {url_batch}...")
            async with session.get(url_batch) as response:
                print(f"Status: {response.status}")
                batch_info = await response.json()
                # batch_info structure: {"id": ..., "batch_name": ..., "tags": ...} 
                # or maybe wrapped in {"data": ...} depending on API design. 
                # Let's inspect it.
                print(f"Batch Info Response: {json.dumps(batch_info, indent=2, ensure_ascii=False)}")
                
                # Check tags
                tags_raw = batch_info.get('tags')
                # If wrapped in data
                if not tags_raw and 'data' in batch_info:
                    tags_raw = batch_info['data'].get('tags')
                
                print(f"\n[Verification] Checking tags...")
                if tags_raw:
                    # Parse JSON string if needed
                    if isinstance(tags_raw, str):
                        try:
                            tags = json.loads(tags_raw)
                        except json.JSONDecodeError:
                            print(f"❌ Failed to parse tags JSON: {tags_raw}")
                            tags = {}
                    else:
                        tags = tags_raw

                    print(f"Tags parsed: {json.dumps(tags, indent=2, ensure_ascii=False)}")
                    
                    # Check structure
                    structure = tags.get('structure', {})
                    vol_tags = structure.get('volume', [])
                    date_tags = structure.get('date', [])
                    
                    has_volume = any(t.get('value') == '2.9' for t in vol_tags)
                    
                    # Check dynamic date
                    has_date = False
                    is_dynamic = False
                    for t in date_tags:
                        if t.get('value') == today_iso:
                            has_date = True
                            if t.get('is_dynamic'):
                                is_dynamic = True
                    
                    if has_volume:
                        print("✅ Volume tag verified: 2.9倍")
                    else:
                        print(f"❌ Volume tag missing! Found: {vol_tags}")
                        
                    if has_date:
                        print(f"✅ Date tag verified: {today_iso}")
                        if is_dynamic:
                             print("✅ Date tag is correctly marked as DYNAMIC")
                        else:
                             print("❌ Date tag is NOT marked as dynamic (expected true for today)")
                    else:
                        print(f"❌ Date tag missing! Expected {today_iso}, Found: {date_tags}")
                else:
                    print("❌ No tags found in batch info!")

            # Step 3: Get Stocks (Verify Data Output)
            url_stocks = f"http://localhost:8000/api/v1/wencai/stocks?batch_id={batch_id}"
            print(f"\n[Step 3] Fetching stocks from {url_stocks}...")
            async with session.get(url_stocks) as response:
                print(f"Status: {response.status}")
                stocks_result = await response.json()
                # Assuming returns list or {"data": [...]}
                
                stocks = stocks_result
                if isinstance(stocks_result, dict) and 'data' in stocks_result:
                    stocks = stocks_result['data']
                    
                print(f"Stocks count: {len(stocks)}")
                if len(stocks) > 0:
                    print(f"Example stock: {stocks[0].get('stock_name')} ({stocks[0].get('stock_code')})")
                    print("✅ Stocks retrieval verified")
                else:
                    print("❌ No stocks found!")

            # Step 4: Get Concepts (Verify Concept Cloud Data)
            url_concepts = "http://localhost:8000/api/v1/wencai/concepts"
            print(f"\n[Step 4] Fetching concepts from {url_concepts}...")
            async with session.get(url_concepts) as response:
                print(f"Status: {response.status}")
                concepts_result = await response.json()
                
                concepts = concepts_result.get('data', [])
                print(f"Concepts count: {len(concepts)}")
                
                if len(concepts) > 0:
                    first_concept = concepts[0]
                    print(f"Top concept: {first_concept.get('name')}, Count: {first_concept.get('count')}, AvgChange: {first_concept.get('avg_change')}")
                    print(f"Associated stocks (first 3): {json.dumps(first_concept.get('stocks')[:3], ensure_ascii=False)}")
                    print("✅ Concept cloud data verified")
                else:
                    print("❌ No concepts found!")

    except Exception as e:
        print(f"Error processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_full_flow())