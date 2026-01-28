import os
import json
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from glob import glob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("parser_okooo.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("OkoooParser")

DATA_DIR = "/Users/mac/StudioProjects/2026/open-citycloud-workspace/data/okooo/mobile"
OUTPUT_DIR = "/Users/mac/StudioProjects/2026/open-citycloud-workspace/data/okooo/processed"

def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)

class OkoooParser:
    def __init__(self, data_dir: str, output_dir: str):
        self.data_dir = data_dir
        self.output_dir = output_dir
        ensure_dir(self.output_dir)

    def parse_history(self, html_content: str, match_id: str = "") -> Dict[str, Any]:
        soup = BeautifulSoup(html_content, 'lxml')
        data = {
            "match_id": match_id,
            "match_info": {},
            "home_history": [],
            "away_history": [],
            "head_to_head": [],
            "future_matches": {"home": [], "away": []}
        }
        
        # Parse Match Header Info
        nav_content = soup.find('div', class_='match-nav-content')
        if nav_content:
            try:
                home_team_tag = nav_content.find('a', href=re.compile(r'/team/'))
                away_team_tag = nav_content.find_all('a', href=re.compile(r'/team/'))[-1]
                
                # Extract League from Title
                league_match = re.search(r'【(.*?)】', soup.title.string) if soup.title else None
                league = league_match.group(1) if league_match else ""

                # Extract Ranks
                divs = nav_content.find_all('div', recursive=False)
                home_rank = ""
                away_rank = ""
                if len(divs) >= 3:
                    # Home rank usually in first div
                    home_rank_tag = divs[0].find('span', class_='num')
                    if home_rank_tag:
                        home_rank = home_rank_tag.get_text(strip=True)
                    
                    # Away rank usually in third div
                    away_rank_tag = divs[2].find('span', class_='num')
                    if away_rank_tag:
                        away_rank = away_rank_tag.get_text(strip=True)

                data["match_info"] = {
                    "home_team": home_team_tag.get_text(strip=True) if home_team_tag else "",
                    "away_team": away_team_tag.get_text(strip=True) if away_team_tag else "",
                    "score_text": nav_content.find('div', class_='date').get_text(strip=True) if nav_content.find('div', class_='date') else "",
                    "league": league,
                    "home_rank": home_rank,
                    "away_rank": away_rank,
                    "match_time": "" # To be filled by crawler if not found here
                }
            except Exception as e:
                logger.warning(f"Error parsing header: {e}")

        # Helper to parse table rows
        def parse_table(section_type: str) -> List[Dict[str, Any]]:
            rows_data = []
            section = soup.find('section', attrs={'type': section_type})
            if not section:
                return rows_data
            
            # Identify "Subject Team" (Home or Away) for comparison
            subject_team_name = data["match_info"].get("home_team") if section_type == "home" else data["match_info"].get("away_team")
            
            rows = section.select('table.matchtable tr')
            for row in rows:
                try:
                    # Skip if not a data row
                    if not row.get('data-matchid'):
                        continue
                        
                    cells = row.find_all('td')
                    if len(cells) < 5:
                        continue
                        
                    # Date & League
                    league = cells[0].find('p').get_text(strip=True) if cells[0].find('p') else ""
                    date_str = cells[0].find_all('p')[1].get_text(strip=True) if len(cells[0].find_all('p')) > 1 else ""
                    
                    # Score
                    score_tag = row.find('a', href=re.compile(r'history\.php'))
                    score = score_tag.get_text(strip=True) if score_tag else ""
                    
                    # Result (Win/Draw/Loss)
                    result = cells[4].get_text(strip=True)

                    # Opponent & Rank
                    left_team_div = cells[1].find('div', class_='team-name-l')
                    left_team_name = left_team_div.find('b').get_text(strip=True)
                    left_team_rank_tag = left_team_div.find_all('i')[-1] if left_team_div.find_all('i') else None
                    left_team_rank = left_team_rank_tag.get_text(strip=True) if left_team_rank_tag else ""

                    right_team_div = cells[3].find('div', class_='team-name-r')
                    right_team_name = right_team_div.find('b').get_text(strip=True)
                    right_team_rank_tag = right_team_div.find_all('i')[0] if right_team_div.find_all('i') else None
                    right_team_rank = right_team_rank_tag.get_text(strip=True) if right_team_rank_tag else ""

                    if left_team_name == subject_team_name:
                        opponent = right_team_name
                        opponent_rank = right_team_rank
                    else:
                        opponent = left_team_name
                        opponent_rank = left_team_rank
                    
                    rows_data.append({
                        "match_id": row.get('data-matchid'),
                        "league": league,
                        "date": date_str,
                        "score": score,
                        "result": result,
                        "opponent": opponent,
                        "opponent_rank": opponent_rank
                    })
                except Exception as e:
                    pass
            return rows_data

        # Helper for Future Matches
        def parse_future_section(section) -> List[Dict[str, Any]]:
            rows_data = []
            if not section:
                return rows_data
                
            rows = section.select('table.matchtable tr')
            for row in rows:
                try:
                    if not row.get('data-matchid'): continue
                    cells = row.find_all('td')
                    if len(cells) < 5: continue
                    
                    league = cells[0].find('p').get_text(strip=True) if cells[0].find('p') else ""
                    date_str = cells[0].find_all('p')[1].get_text(strip=True) if len(cells[0].find_all('p')) > 1 else ""
                    
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
                except Exception:
                    pass
            return rows_data

        data["home_history"] = parse_table("home")
        data["away_history"] = parse_table("away")
        data["head_to_head"] = parse_table("vs")
        
        future_sections = []
        sections = soup.find_all('section', class_='matchtabbox')
        for sec in sections:
            title_div = sec.find('div', class_='titlebox')
            if title_div:
                spans = title_div.find_all('span')
                found_future = False
                for s in spans:
                    text = s.get_text(strip=True)
                    if "未来三场" in text:
                        future_sections.append(sec)
                        found_future = True
                        break
                
                if not found_future:
                     if "未来三场" in title_div.get_text(strip=True):
                          future_sections.append(sec)
        
        if len(future_sections) >= 1:
            data["future_matches"]["home"] = parse_future_section(future_sections[0])
                
        if len(future_sections) >= 2:
            data["future_matches"]["away"] = parse_future_section(future_sections[1])

        return data

    def parse_exchanges(self, html_content: str) -> Dict[str, Any]:
        """Parse exchanges.html content"""
        soup = BeautifulSoup(html_content, 'lxml')
        data = {}

        # Helper to parse tables
        def parse_table(section, headers_map):
            result_list = []
            table = section.find('table', class_='exchange-table')
            if not table:
                return result_list
            
            rows = table.find_all('tr')
            if not rows:
                return result_list

            # Skip header row
            for row in rows[1:]:
                cols = row.find_all(['td', 'th'])
                item = {}
                for idx, key in headers_map.items():
                    if idx < len(cols):
                        val = cols[idx].get_text(strip=True)
                        item[key] = val
                
                if item:
                    result_list.append(item)
            return result_list

        # 1. 竞足保存盈亏 (jczq_save)
        section = soup.find(string=re.compile("竞足保存盈亏"))
        if section:
            section_box = section.find_parent('section', class_='exchange-box')
            if section_box:
                data['jczq_save'] = parse_table(section_box, {
                    0: 'result', 1: 'index', 2: 'save_amount', 3: 'profit', 4: 'hot_cold'
                })

        # 2. 竞足人气盈亏 (jczq_popularity)
        section = soup.find(string=re.compile("竞足人气盈亏"))
        if section:
            section_box = section.find_parent('section', class_='exchange-box')
            if section_box:
                data['jczq_popularity'] = parse_table(section_box, {
                    0: 'result', 1: 'index', 2: 'popularity', 3: 'profit'
                })

        # 3. 必发交易盈亏 (betfair_transaction)
        section = soup.find(string=re.compile("必发交易盈亏"))
        if section:
            section_box = section.find_parent('section', class_='exchange-box')
            if section_box:
                data['betfair_transaction'] = parse_table(section_box, {
                    0: 'result', 1: 'index', 2: 'transaction_amount', 3: 'profit', 4: 'hot_cold'
                })

        # 4. 交易分布对比 (transaction_distribution)
        section = soup.find(string=re.compile("交易分布对比"))
        if section:
            section_box = section.find_parent('section', class_='exchange-box')
            if section_box:
                data['transaction_distribution'] = parse_table(section_box, {
                    0: 'result', 1: 'odds_99', 2: 'betfair', 3: 'jczq_order', 4: 'jczq_pop'
                })

        # 5. 五要素 (five_factors)
        section = soup.find(string=re.compile("五要素"))
        if section:
            section_box = section.find_parent('section', class_='exchange-box')
            if section_box:
                data['five_factors'] = parse_table(section_box, {
                    0: 'factor', 1: 'home_win', 2: 'draw', 3: 'home_loss', 4: 'suggestion'
                })

        return data

    def parse_game_points(self, html_content: str) -> Dict[str, Any]:
        """Parse game.html content"""
        soup = BeautifulSoup(html_content, 'lxml')
        data = {}

        # For cup matches, extract "tezheng" (characteristics)
        tezheng = soup.find('div', class_='tezheng')
        if tezheng:
            # Extract characteristics
            title = tezheng.find('p', class_='title')
            if title:
                data['title'] = title.get_text(strip=True)
            
            # Extract items
            items = []
            item_divs = tezheng.find_all('div', class_='item')
            for item in item_divs:
                p_tag = item.find('p')
                if p_tag:
                    items.append(p_tag.get_text(strip=True))
            data['characteristics'] = items
        
        return data

    def parse_form_analysis(self, html_content: str) -> Dict[str, Any]:
        """Parse form.html content"""
        soup = BeautifulSoup(html_content, 'lxml')
        data = {}

        # 1. Overview (阵容概览) - .gailai
        gailai = soup.find('div', class_='gailai')
        if gailai:
            overview = {}
            lists = gailai.find_all('div', class_='list')
            if len(lists) >= 4:
                # 0: Total Value
                val_home = lists[0].find('p', recursive=False)
                val_away = lists[0].find_all('p')[-1]
                overview['total_value'] = f"home: {val_home.get_text(strip=True) if val_home else ''}, away: {val_away.get_text(strip=True) if val_away else ''}"

                # 1: Injury Value
                inj_home = lists[1].find('p', recursive=False)
                inj_away = lists[1].find_all('p')[-1]
                overview['injury_value'] = f"home: {inj_home.get_text(strip=True) if inj_home else ''}, away: {inj_away.get_text(strip=True) if inj_away else ''}"

                # 2: Age
                age_home = lists[2].find('p', recursive=False)
                age_away = lists[2].find_all('p')[-1]
                overview['average_age'] = f"home: {age_home.get_text(strip=True) if age_home else ''}, away: {age_away.get_text(strip=True) if age_away else ''}"

                # 3: Height
                ht_home = lists[3].find('p', recursive=False)
                ht_away = lists[3].find_all('p')[-1]
                overview['average_height'] = f"home: {ht_home.get_text(strip=True) if ht_home else ''}, away: {ht_away.get_text(strip=True) if ht_away else ''}"
            
            data['overview'] = overview

        # 2. Technical Comparison (技术对比) - .jishu
        jishu = soup.find('div', class_='jishu')
        if jishu:
            tech_comp = []
            # Skip header row (first .list)
            lists = jishu.find_all('div', class_='list')
            if len(lists) > 1:
                for row in lists[1:]:
                    items = row.find_all(['p', 'span'])
                    if len(items) >= 5:
                        tech_comp.append({
                            "home_all": items[0].get_text(strip=True),
                            "home_home": items[1].get_text(strip=True),
                            "label": items[2].get_text(strip=True),
                            "away_away": items[3].get_text(strip=True),
                            "away_all": items[4].get_text(strip=True)
                        })
            data['technical_comparison'] = tech_comp

        # 3. Strength Comparison (阵容实力对比) - .shili
        shili = soup.find('div', class_='shili')
        if shili:
            strength_comp = []
            lists = shili.find_all('div', class_='list')
            # Skip header
            if len(lists) > 1:
                for row in lists[1:]:
                    home_price = row.find('div', class_='price-l')
                    xq_l = row.find('div', class_='xq-l')
                    center = row.find('div', class_='center')
                    xq_r = row.find('div', class_='xq-r')
                    away_price = row.find('div', class_='price-r')

                    if center:
                        strength_comp.append({
                            "position": center.get_text(strip=True),
                            "home_price": home_price.get_text(strip=True) if home_price else "",
                            "away_price": away_price.get_text(strip=True) if away_price else "",
                            "home_avg": xq_l.get_text(strip=True) if xq_l else "",
                            "away_avg": xq_r.get_text(strip=True) if xq_r else ""
                        })
            data['strength_comparison'] = strength_comp

        # 4. Lineup Comparison (首发阵容对比) - .shoufa
        shoufa = soup.find('div', class_='shoufa')
        if shoufa:
            lineup_comp = []
            # Skip header (.itemtitle)
            items = shoufa.find_all('div', class_='item')
            for item in items:
                if 'itemtitle' in item.get('class', []):
                    continue
                
                # list-l (home), list-r (away)
                list_l = item.find('div', class_='list-l')
                list_r = item.find('div', class_='list-r')
                
                home_data = {}
                away_data = {}
                
                if list_l:
                    num = list_l.find('div', class_='num')
                    name_div = list_l.find('div', class_='name')
                    zg = list_l.find('div', class_='zg')
                    jq = list_l.find('div', class_='jq')
                    
                    home_data['number'] = num.get_text(strip=True) if num else ""
                    home_data['assists'] = zg.get_text(strip=True) if zg else ""
                    home_data['goals'] = jq.get_text(strip=True) if jq else ""
                    
                    if name_div:
                        a_tag = name_div.find('a')
                        if a_tag:
                            home_data['name'] = a_tag.get_text(strip=True)
                            href = a_tag.get('href', '')
                            home_data['id'] = href.split('/')[-2] if href else ""
                        
                        i_tag = name_div.find('i')
                        if i_tag:
                            home_data['price'] = i_tag.get_text(strip=True)
                        
                        full_text = name_div.get_text(strip=True)
                        if i_tag:
                            full_text = full_text.replace(i_tag.get_text(strip=True), "")
                        if a_tag:
                            full_text = full_text.replace(a_tag.get_text(strip=True), "")
                        home_data['position'] = full_text.strip()
                
                if list_r:
                    num = list_r.find('div', class_='num')
                    name_div = list_r.find('div', class_='name')
                    zg = list_r.find('div', class_='zg')
                    jq = list_r.find('div', class_='jq')
                    
                    away_data['number'] = num.get_text(strip=True) if num else ""
                    away_data['assists'] = zg.get_text(strip=True) if zg else ""
                    away_data['goals'] = jq.get_text(strip=True) if jq else ""
                    
                    if name_div:
                        a_tag = name_div.find('a')
                        if a_tag:
                            away_data['name'] = a_tag.get_text(strip=True)
                            href = a_tag.get('href', '')
                            away_data['id'] = href.split('/')[-2] if href else ""
                        
                        i_tag = name_div.find('i')
                        if i_tag:
                            away_data['price'] = i_tag.get_text(strip=True)
                            
                        full_text = name_div.get_text(strip=True)
                        if i_tag:
                            full_text = full_text.replace(i_tag.get_text(strip=True), "")
                        if a_tag:
                            full_text = full_text.replace(a_tag.get_text(strip=True), "")
                        away_data['position'] = full_text.strip()

                lineup_comp.append({
                    "home": home_data,
                    "away": away_data
                })
            data['lineup_comparison'] = lineup_comp
            
        return data

    def parse_odds_change(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse bifa_odds_change.html for bifaIndex"""
        soup = BeautifulSoup(html_content, 'lxml')
        results = []
        table = soup.find('table', class_='changeTable')
        if not table:
            return results
        
        rows = table.find_all('tr')
        for row in rows:
            try:
                tds = row.find_all('td')
                if len(tds) < 2: continue
                
                # Odds
                odds_td = tds[0]
                spans = odds_td.find_all('span')
                if len(spans) >= 3:
                    win = spans[0].get_text(strip=True)
                    draw = spans[1].get_text(strip=True)
                    loss = spans[2].get_text(strip=True)
                    
                    # Time
                    time_td = tds[1]
                    time_text = time_td.get_text(strip=True)
                    
                    results.append({
                        "win": win,
                        "draw": draw,
                        "loss": loss,
                        "time": time_text
                    })
            except Exception:
                pass
        return results

    def parse_handicap_change(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse macao_handicap_change.html for macaoIndex"""
        soup = BeautifulSoup(html_content, 'lxml')
        results = []
        table = soup.find('table', class_='changeTable')
        if not table:
            return results
            
        rows = table.find_all('tr')
        for row in rows:
            try:
                tds = row.find_all('td')
                if len(tds) < 2: continue
                
                # Handicap
                handicap_td = tds[0]
                spans = handicap_td.find_all('span')
                if len(spans) >= 3:
                    home_water = spans[0].get_text(strip=True)
                    handicap = spans[1].get_text(strip=True)
                    away_water = spans[2].get_text(strip=True)
                    
                    # Time
                    time_td = tds[1]
                    time_text = time_td.get_text(strip=True)
                    
                    results.append({
                        "home_water": home_water,
                        "handicap": handicap,
                        "away_water": away_water,
                        "time": time_text
                    })
            except Exception:
                pass
        return results

    def parse_handicap(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse history_xxx_handicap.html"""
        soup = BeautifulSoup(html_content, 'lxml')
        data = []
        
        table = soup.find('table', class_='pl-table') or soup.find('table')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                company_name_tag = row.find('td', class_='company-name') or row.find('span', class_='company')
                if not company_name_tag:
                    continue
                
                company = company_name_tag.get_text(strip=True)
                tds = row.find_all('td')
                
                if len(tds) >= 3:
                    def extract_vals(td):
                        spans = td.find_all(['span', 'p'])
                        vals = [s.get_text(strip=True) for s in spans if s.get_text(strip=True)]
                        if len(vals) >= 3:
                            return {
                                "home": vals[0],
                                "line": vals[1],
                                "away": vals[2]
                            }
                        return {}

                    initial = extract_vals(tds[1])
                    latest = extract_vals(tds[2])
                    
                    if initial or latest:
                        data.append({
                            "company": company,
                            "initial": initial,
                            "latest": latest
                        })
        return data

    def parse_odds(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse history_xxx_odds.html"""
        soup = BeautifulSoup(html_content, 'lxml')
        data = []
        
        table = soup.find('table', class_='pl-table') or soup.find('table')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                company_name_tag = row.find('td', class_='company-name') or row.find('span', class_='company')
                if not company_name_tag:
                    continue
                    
                company = company_name_tag.get_text(strip=True)
                tds = row.find_all('td')
                
                if len(tds) >= 3:
                    def extract_vals(td):
                        spans = td.find_all(['span', 'p'])
                        vals = [s.get_text(strip=True) for s in spans if s.get_text(strip=True)]
                        if len(vals) >= 3:
                            return {
                                "win": vals[0],
                                "draw": vals[1],
                                "loss": vals[2]
                            }
                        return {}
                        
                    initial = extract_vals(tds[1])
                    latest = extract_vals(tds[2])
                    
                    if initial or latest:
                        data.append({
                            "company": company,
                            "initial": initial,
                            "latest": latest
                        })
        return data

