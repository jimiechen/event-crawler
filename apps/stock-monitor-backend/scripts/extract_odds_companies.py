
import re
from bs4 import BeautifulSoup
import json
import os

def extract_companies():
    html_path = "/Users/mac/StudioProjects/2026/open-citycloud-workspace/data/okooo/mobile_samples/odds_change_1314249_82.html"
    output_path = "/Users/mac/StudioProjects/2026/open-citycloud-workspace/data/okooo/config/odds_companies.json"
    
    if not os.path.exists(html_path):
        print(f"File not found: {html_path}")
        return

    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    soup = BeautifulSoup(content, 'lxml')
    companies = []
    
    # Find all company links
    links = soup.select('td.changeMenu a.changeNav')
    
    for link in links:
        pid = link.get('pid')
        # Remove invisible characters/spans from name
        # The HTML has spans like <span style="font-size:0;">!</span> which should be ignored?
        # Actually the text inside span might be garbage to prevent scraping.
        # "立<span style="font-size:0;">!</span>博" -> The "!" is hidden (font-size:0).
        # So we should only take the text nodes that are NOT inside the hidden spans, or strip the hidden spans.
        
        # Strategy: iterate over children. If child is a tag and has font-size:0, ignore.
        name_parts = []
        for child in link.children:
            if child.name == 'span':
                style = child.get('style', '')
                if 'font-size:0' in style:
                    continue
            if isinstance(child, str):
                name_parts.append(child.strip())
            else:
                # If it's a tag but not the hidden span (unlikely here based on sample), get text
                if child.name != 'span':
                    name_parts.append(child.get_text(strip=True))
        
        name = "".join(name_parts)
        if pid and name:
            companies.append({"id": pid, "name": name})
            
    # Save to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)
        
    print(f"Extracted {len(companies)} companies to {output_path}")

if __name__ == "__main__":
    extract_companies()
