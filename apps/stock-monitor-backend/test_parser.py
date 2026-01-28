
import logging
from app.crawler.okooo.parser import OkoooParser

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_parse_bjdc():
    file_path = "/Users/mac/StudioProjects/2026/open-citycloud-workspace/okooo_bjdc.html"
    try:
        with open(file_path, 'r', encoding='gbk') as f: # meta charset says GBK
            html = f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()

    parser = OkoooParser()
    
    print("--- Testing parse_mobile_match_list ---")
    matches = parser.parse_mobile_match_list(html)
    print(f"Found {len(matches)} matches")
    for m in matches:
        print(m)

if __name__ == "__main__":
    test_parse_bjdc()
