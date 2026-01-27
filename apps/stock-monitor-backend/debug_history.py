
import os
import re
from bs4 import BeautifulSoup

def parse_history(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    data = {
        "future_matches": {"home": [], "away": []}
    }
    
    # Helper for Future Matches
    def parse_future_section(section):
        rows_data = []
        if not section:
            return rows_data
            
        rows = section.select('table.matchtable tr')
        for row in rows:
            try:
                # if not row.get('data-matchid'): continue # This check might be too strict if data-matchid is missing? 
                # In sample it has data-matchid="1314256"
                
                cells = row.find_all('td')
                if len(cells) < 5: continue
                
                league = cells[0].find('p').get_text(strip=True) if cells[0].find('p') else ""
                # Handle multiple <p> tags
                ps = cells[0].find_all('p')
                date_str = ""
                if len(ps) > 1:
                    date_str = ps[1].get_text(strip=True)
                
                left_team = cells[1].get_text(strip=True)
                right_team = cells[3].get_text(strip=True)
                interval = cells[4].get_text(strip=True)
                
                rows_data.append({
                    "league": league,
                    "date": date_str,
                    "home_team": left_team,
                    "away_team": right_team,
                    "interval": interval
                })
            except Exception as e:
                print(f"Error row: {e}")
                pass
        return rows_data

    future_sections = []
    # Try finding all sections first
    sections = soup.find_all('section')
    print(f"Total sections found: {len(sections)}")
    
    for sec in sections:
        title_div = sec.find('div', class_='titlebox')
        if title_div:
            # Check all spans
            spans = title_div.find_all('span')
            found_future = False
            for s in spans:
                text = s.get_text(strip=True)
                print(f"Span text: {text}")
                if "未来三场" in text:
                    future_sections.append(sec)
                    found_future = True
                    break
            
            # If not found in spans, check the whole div text
            if not found_future:
                 if "未来三场" in title_div.get_text(strip=True):
                      future_sections.append(sec)
    
    print(f"Future sections found: {len(future_sections)}")

    if len(future_sections) >= 1:
        data["future_matches"]["home"] = parse_future_section(future_sections[0])
            
    if len(future_sections) >= 2:
        data["future_matches"]["away"] = parse_future_section(future_sections[1])

    return data

with open('/Users/mac/StudioProjects/2026/open-citycloud-workspace/data/okooo/mobile_samples/history_1314249.html', 'r') as f:
    content = f.read()
    result = parse_history(content)
    print("Result:", result)
