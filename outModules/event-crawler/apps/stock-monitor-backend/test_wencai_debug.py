import json
import asyncio
import aiohttp
import re

# The path to the debug file
DEBUG_FILE = "/Users/mac/ok-mcp/app/stock-monitor-backend/debug/问财原始数据包含概念和行业.txt"

# The query string specified by the user
QUERY_STRING = "2025年12月8日成交量是前一个工作日成交量的2.9倍以上，非创业版，非科创版，非ST，概念 行业"

async def extract_and_send():
    print(f"Reading debug file: {DEBUG_FILE}")
    try:
        with open(DEBUG_FILE, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print("Debug file not found!")
        return

    # Extract the JSON payload from the curl command string
    # The file content seems to be a curl command with --data-raw $'...'
    # We need to extract the content inside the single quotes after --data-raw $
    
    match = re.search(r"--data-raw \$'(.*)'", content, re.DOTALL)
    if not match:
        print("Could not extract JSON payload from file content.")
        # Fallback: try to find just the JSON part if the curl format is different
        # Or maybe the file IS the JSON content but the tool output showed it as curl?
        # Looking at the tool output, it starts with "curl ...", so it's a shell script or command log.
        # The content inside seems to be escaped.
        pass
    
    if match:
        raw_payload = match.group(1)
        # Unescape the payload
        # It seems to be a shell escaped string. We might need to handle \' and \\ etc.
        # For simplicity, let's try to parse it as JSON if possible, or clean it up.
        # However, looking at the output: "html_content":"<div..."
        # It seems standard.
        
        # A simpler way might be to just extract the html_content value directly if the JSON parsing is hard due to escaping.
        pass
        
    # Let's try to construct a new payload using the HTML content from the file.
    # Since extracting the exact JSON from a shell-escaped string can be tricky,
    # let's look for "html_content":"..." and take everything in between.
    
    # Actually, the tool output showed: --data-raw $'{"html_content":"<div data-v-75ab8652=\\"\\" ...
    # So it is a JSON string inside $'...'.
    
    # Let's try to extract the HTML content directly using regex
    # It starts with "html_content":" and ends with "}" (at the end of the string usually)
    # Be careful with escaped quotes.
    
    # Alternative: Read the file content, find the start of JSON.
    start_index = content.find('{')
    end_index = content.rfind('}')
    
    if start_index != -1 and end_index != -1:
        json_str = content[start_index:end_index+1]
        
        # The file content from the tool output shows escaping: \\" for "
        # We need to unescape it to get valid JSON.
        # Since it was inside $'...', it likely uses bash escaping.
        
        try:
            # Simple unescaping for common cases
            json_str_clean = json_str.replace('\\"', '"').replace('\\\\', '\\')
            
            # This might still be tricky if there are newlines or other chars.
            # Let's try to parse it.
            # Wait, the tool output says: --data-raw $'{"html_content":"<div ...'
            # So the outer quotes are ' and the inner content is escaped.
            
            # Let's try a different approach:
            # 1. Get the content inside $'...'
            # 2. Decode it as a string
            pass
        except Exception as e:
            print(f"Error preparing JSON: {e}")
            return
            
    # To be safe and avoid complex parsing of the curl command, let's just extract the HTML part specifically.
    # We know it starts after "html_content":" and goes until the end of the JSON object.
    
    # Actually, since I have access to the file, I can see what it really contains.
    # The tool output showed lines starting with 1->, 2-> etc.
    # Let's assume the file content is exactly what was shown.
    
    # Let's try to just grab the HTML content using a robust regex or by finding markers.
    # The HTML content starts with <div and ends with ... well, it's long.
    
    # Let's rely on Python's string manipulation.
    # The content is inside --data-raw $' ... '
    start_marker = "--data-raw $'"
    end_marker = "'" # The last single quote
    
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
    
    # Now we have the string that was inside $'...'.
    # In bash $'string', backslash escapes are interpreted.
    # We need to interpret them similarly.
    # Python's `unicode_escape` codec might be useful but it's for python string literals.
    # Bash escaping is slightly different but mostly compatible for \n, \t, etc.
    # However, \" is used for double quotes inside the JSON.
    
    # Let's try to load it as JSON.
    try:
        # We need to handle the fact that it's a JSON string.
        # The string itself is '{"html_content":"..."}'
        # But inside it, " is escaped as \" because it was inside $'...'.
        # Actually, in $'...', " doesn't need to be escaped unless it's to be literal " inside the string?
        # Wait, the output shows: "html_content":"<div data-v-75ab8652=\\"\\"
        # So it seems double quotes are escaped as \\"
        
        # Let's replace \\" with \" and then try to parse?
        # No, if it's a JSON string, it should be valid JSON.
        # The string extracted is the JSON string.
        # If the file contains \" then it means the JSON key/value contains a literal quote?
        # No, "html_content" is a key. It is surrounded by ".
        # If the file has \"html_content\", then it's escaped.
        
        # Let's just try to parse it after basic cleanup.
        payload_str = payload_str.replace(r'\"', '"')
        payload_str = payload_str.replace(r'\\', '\\')
        
        data = json.loads(payload_str)
        html_content = data.get('html_content')
        
        if not html_content:
            print("No html_content found in payload")
            return
            
        print(f"Extracted HTML content length: {len(html_content)}")
        
        # Now construct the request
        request_payload = {
            "html_content": html_content,
            "batch_name": "Debug_File_Test",
            "crawl_url": "http://debug.local",
            "query_string": QUERY_STRING
        }
        
        async with aiohttp.ClientSession() as session:
            url = "http://localhost:8000/api/v1/wencai/parse"
            print(f"Sending request to {url}...")
            async with session.post(url, json=request_payload) as response:
                print(f"Status: {response.status}")
                result = await response.json()
                print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
    except Exception as e:
        print(f"Error processing: {e}")
        # Print a snippet of payload_str to debug
        print(f"Payload snippet: {payload_str[:100]}...")

if __name__ == "__main__":
    asyncio.run(extract_and_send())
