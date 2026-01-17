
import json
import os

try:
    with open('chat_content.json', 'r') as f:
        data = json.load(f)
        content = data.get('content', '')
    
    # Simple cleanup if needed, but let's just save it first
    output_path = '/Users/mac/StudioProjects/open-citycloud/.trae/documents/deepseek_chat_a41b487d.md'
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(content)
        
    print(f"Successfully saved to {output_path}")
    
except Exception as e:
    print(f"Error saving file: {e}")
