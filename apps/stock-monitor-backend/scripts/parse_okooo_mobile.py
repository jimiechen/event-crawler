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

    def parse_history(self, html_content: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html_content, 'lxml')
        data = {
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

                data["match_info"] = {
                    "home_team": home_team_tag.get_text(strip=True) if home_team_tag else "",
                    "away_team": away_team_tag.get_text(strip=True) if away_team_tag else "",
                    "score_text": nav_content.find('div', class_='date').get_text(strip=True) if nav_content.find('div', class_='date') else "",
                    "league": league
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
            # section_type "home" means Home Team's history, so Subject is Home Team.
            # section_type "away" means Away Team's history, so Subject is Away Team.
            subject_team_name = data["match_info"].get("home_team") if section_type == "home" else data["match_info"].get("away_team")
            
            rows = section.select('table.matchtable tr')
            for row in rows:
                try:
                    # Skip if not a data row (some might be headers or hidden)
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
                    # Left Team
                    left_team_div = cells[1].find('div', class_='team-name-l')
                    left_team_name = left_team_div.find('b').get_text(strip=True)
                    left_team_rank_tag = left_team_div.find_all('i')[-1] if left_team_div.find_all('i') else None
                    left_team_rank = left_team_rank_tag.get_text(strip=True) if left_team_rank_tag else ""

                    # Right Team
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
                    logger.warning(f"Error parsing row in {section_type}: {e}")
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
        
        # Future matches
        # Strategy: Find all sections with "未来三场"
        
        future_sections = []
        sections = soup.find_all('section', class_='matchtabbox')
        for sec in sections:
            title_div = sec.find('div', class_='titlebox')
            if title_div:
                # Check all spans
                spans = title_div.find_all('span')
                found_future = False
                for s in spans:
                    text = s.get_text(strip=True)
                    if "未来三场" in text:
                        future_sections.append(sec)
                        found_future = True
                        break
                
                # If not found in spans, check the whole div text
                if not found_future:
                     if "未来三场" in title_div.get_text(strip=True):
                          future_sections.append(sec)
        
        if len(future_sections) >= 1:
            data["future_matches"]["home"] = parse_future_section(future_sections[0])
                
        if len(future_sections) >= 2:
            data["future_matches"]["away"] = parse_future_section(future_sections[1])

        return data

    def parse_handicap(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'lxml')
        data = []
        
        table = soup.find('section', id='pankou')
        if not table:
            return data
            
        rows = table.select('table.matchtable tbody tr')
        for row in rows:
            try:
                cells = row.find_all('td')
                if len(cells) < 4:
                    continue
                
                company = cells[0].get_text(strip=True).replace('定制', '').replace('取消排序', '')
                
                # Initial Odds
                init_cell = cells[1]
                init_odds = {
                    "home": init_cell.find('span', attrs={'type': 'zhu'}).get_text(strip=True) if init_cell.find('span', attrs={'type': 'zhu'}) else "",
                    "pan": init_cell.find('em', attrs={'type': 'chu'}).get_text(strip=True) if init_cell.find('em', attrs={'type': 'chu'}) else "",
                    "away": init_cell.find('span', attrs={'type': 'ke'}).get_text(strip=True) if init_cell.find('span', attrs={'type': 'ke'}) else ""
                }
                
                # Latest Odds
                curr_cell = cells[2]
                curr_odds = {
                    "home": curr_cell.find('span', attrs={'type': 'xinzhu'}).get_text(strip=True) if curr_cell.find('span', attrs={'type': 'xinzhu'}) else "",
                    "pan": curr_cell.find('em', attrs={'type': 'xin'}).get_text(strip=True) if curr_cell.find('em', attrs={'type': 'xin'}) else "",
                    "away": curr_cell.find('span', attrs={'type': 'xinke'}).get_text(strip=True) if curr_cell.find('span', attrs={'type': 'xinke'}) else ""
                }
                
                data.append({
                    "company": company,
                    "initial": init_odds,
                    "latest": curr_odds
                })
            except Exception as e:
                logger.warning(f"Error parsing handicap row: {e}")
                
        return data

    def parse_odds(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'lxml')
        data = []
        
        table = soup.find('section', id='Odds')
        if not table:
            return data
            
        rows = table.select('table.matchtable tbody tr')
        for row in rows:
            try:
                cells = row.find_all('td')
                if len(cells) < 4:
                    continue
                    
                company = cells[0].get_text(strip=True)
                
                # Initial Odds
                init_cell = cells[1]
                init_odds = {
                    "win": init_cell.find('span', attrs={'type': 'sheng'}).get_text(strip=True) if init_cell.find('span', attrs={'type': 'sheng'}) else "",
                    "draw": init_cell.find('span', attrs={'type': 'ping'}).get_text(strip=True) if init_cell.find('span', attrs={'type': 'ping'}) else "",
                    "loss": init_cell.find('span', attrs={'type': 'fu'}).get_text(strip=True) if init_cell.find('span', attrs={'type': 'fu'}) else ""
                }
                
                # Latest Odds
                curr_cell = cells[2]
                curr_odds = {
                    "win": curr_cell.find('span', attrs={'type': 'xinsheng'}).get_text(strip=True) if curr_cell.find('span', attrs={'type': 'xinsheng'}) else "",
                    "draw": curr_cell.find('span', attrs={'type': 'xinping'}).get_text(strip=True) if curr_cell.find('span', attrs={'type': 'xinping'}) else "",
                    "loss": curr_cell.find('span', attrs={'type': 'xinfu'}).get_text(strip=True) if curr_cell.find('span', attrs={'type': 'xinfu'}) else ""
                }
                
                data.append({
                    "company": company,
                    "initial": init_odds,
                    "latest": curr_odds
                })
            except Exception as e:
                logger.warning(f"Error parsing odds row: {e}")
                
        return data

    def parse_form(self, html_content: str) -> Dict[str, Any]:
        """
        Parse form (lineup/technical/strength) data.
        """
        soup = BeautifulSoup(html_content, 'lxml')
        data = {
            "overview": {},
            "technical_comparison": [],
            "strength_comparison": [],
            "lineup_comparison": [],
            "expected_injuries": {"home": [], "away": []}
        }
        
        try:
            # 1. Overview (Gailai)
            gailai = soup.find('div', class_='gailai')
            if gailai:
                lists = gailai.find_all('div', class_='list')
                if len(lists) >= 3:
                    # Value
                    val_p = lists[0].find_all('p')
                    if len(val_p) >= 2:
                        home_val = val_p[0].get_text(strip=True)
                        away_val = val_p[1].get_text(strip=True)
                        data["overview"]["total_value"] = f"home: {home_val}, away: {away_val}"
                    
                    # Injury
                    inj_p = lists[1].find_all('p')
                    if len(inj_p) >= 2:
                        home_inj = inj_p[0].get_text(strip=True)
                        away_inj = inj_p[1].get_text(strip=True)
                        data["overview"]["injury_value"] = f"home: {home_inj}, away: {away_inj}"

                    # Age
                    age_p = lists[2].find_all('p')
                    if len(age_p) >= 2:
                        home_age = age_p[0].get_text(strip=True)
                        away_age = age_p[1].get_text(strip=True)
                        data["overview"]["average_age"] = f"home: {home_age}, away: {away_age}"
                    
                    # Height (if available)
                    if len(lists) > 3:
                        height_p = lists[3].find_all('p')
                        if len(height_p) >= 2:
                            home_height = height_p[0].get_text(strip=True)
                            away_height = height_p[1].get_text(strip=True)
                            data["overview"]["average_height"] = f"home: {home_height}, away: {away_height}"

            # 2. Technical Comparison (Jishu)
            jishu = soup.find('div', class_='jishu')
            if jishu:
                lists = jishu.find_all('div', class_='list')
                # First list is header, skip it
                for item in lists[1:]:
                    ps = item.find_all('p')
                    span = item.find('span')
                    if len(ps) >= 4 and span:
                        label = span.get_text(strip=True)
                        home_all = ps[0].get_text(strip=True)
                        home_home = ps[1].get_text(strip=True)
                        away_away = ps[2].get_text(strip=True)
                        away_all = ps[3].get_text(strip=True)
                        data["technical_comparison"].append({
                            "label": label,
                            "home_all": home_all,
                            "home_home": home_home,
                            "away_away": away_away,
                            "away_all": away_all
                        })

            # 3. Strength Comparison (Shili)
            shili = soup.find('div', class_='shili')
            if shili:
                lists = shili.find_all('div', class_='list')
                # Skip header
                for item in lists[1:]:
                    center = item.find('div', class_='center')
                    if not center: continue
                    position = center.get_text(strip=True)
                    
                    price_l = item.find('div', class_='price-l')
                    price_r = item.find('div', class_='price-r')
                    xq_l = item.find('div', class_='xq-l')
                    xq_r = item.find('div', class_='xq-r')
                    
                    data["strength_comparison"].append({
                        "position": position,
                        "home_price": price_l.get_text(strip=True) if price_l else "",
                        "away_price": price_r.get_text(strip=True) if price_r else "",
                        "home_avg": xq_l.get_text(strip=True) if xq_l else "",
                        "away_avg": xq_r.get_text(strip=True) if xq_r else ""
                    })

            # 4. Starting Lineup Comparison (Shoufa)
            shoufa = soup.find('div', class_='shoufa')
            if shoufa:
                items = shoufa.find_all('div', class_='item')
                # Skip header (class itemtitle)
                for item in items:
                    if 'itemtitle' in item.get('class', []):
                        continue
                    
                    # Left (Home)
                    list_l = item.find('div', class_='list-l')
                    home_player = {}
                    if list_l:
                        name_div = list_l.find('div', class_='name')
                        if name_div:
                            # Extract name, price, id
                            a_tag = name_div.find('a')
                            i_tag = name_div.find('i')
                            if a_tag:
                                home_player['name'] = a_tag.get_text(strip=True)
                                home_player['id'] = a_tag.get('href', '').split('/')[-2] if a_tag.get('href') else ""
                            
                            if i_tag:
                                home_player['price'] = i_tag.get_text(strip=True)
                            
                            # Position is text between a tag (inside em) and i tag?
                            # Structure: <em><a>Name</a></em>Position<i>Price</i>
                            # Use get_text and remove name/price to find position?
                            full_text = name_div.get_text(strip=True)
                            name_text = home_player.get('name', '')
                            price_text = home_player.get('price', '')
                            # Simple clean up
                            position_text = full_text.replace(name_text, '').replace(price_text, '').strip()
                            home_player['position'] = position_text

                        num_div = list_l.find('div', class_='num')
                        if num_div:
                            home_player['number'] = num_div.get_text(strip=True)
                        
                        zg_div = list_l.find('div', class_='zg')
                        if zg_div:
                            home_player['assists'] = zg_div.get_text(strip=True)

                        jq_div = list_l.find('div', class_='jq')
                        if jq_div:
                            home_player['goals'] = jq_div.get_text(strip=True)

                    # Right (Away)
                    list_r = item.find('div', class_='list-r')
                    away_player = {}
                    if list_r:
                        name_div = list_r.find('div', class_='name')
                        if name_div:
                            a_tag = name_div.find('a')
                            i_tag = name_div.find('i')
                            if a_tag:
                                away_player['name'] = a_tag.get_text(strip=True)
                                away_player['id'] = a_tag.get('href', '').split('/')[-2] if a_tag.get('href') else ""
                            
                            if i_tag:
                                away_player['price'] = i_tag.get_text(strip=True)
                            
                            full_text = name_div.get_text(strip=True)
                            name_text = away_player.get('name', '')
                            price_text = away_player.get('price', '')
                            position_text = full_text.replace(name_text, '').replace(price_text, '').strip()
                            away_player['position'] = position_text

                        num_div = list_r.find('div', class_='num')
                        if num_div:
                            away_player['number'] = num_div.get_text(strip=True)
                        
                        zg_div = list_r.find('div', class_='zg')
                        if zg_div:
                            away_player['assists'] = zg_div.get_text(strip=True)

                        jq_div = list_r.find('div', class_='jq')
                        if jq_div:
                            away_player['goals'] = jq_div.get_text(strip=True)
                    
                    data["lineup_comparison"].append({
                        "home": home_player,
                        "away": away_player
                    })

            # 5. Expected Injuries (Shangting)
            shangting_divs = soup.find_all('div', class_='shangting')
            if len(shangting_divs) >= 2:
                # Home
                home_shangting = shangting_divs[0]
                home_items = home_shangting.find_all('div', class_='item')
                for item in home_items:
                    if 'itemtitle' in item.get('class', []): continue
                    # Parse item
                    # Based on structure, it might have .name, .price, .list
                    # But sample said "No data". I'll implement robust check.
                    # If structure is like lineup items:
                    # <div class="item"><div class="name">...</div>...</div>
                    # Web reference #2:
                    # <div class="item"><div class="name">Name</div><div class="price">Val</div>...</div>
                    player = {}
                    name_div = item.find('div', class_='name')
                    if name_div: player['name'] = name_div.get_text(strip=True)
                    price_div = item.find('div', class_='price')
                    if price_div: player['price'] = price_div.get_text(strip=True)
                    
                    # Status/Record
                    list_div = item.find('div', class_='list')
                    if list_div:
                        player['status'] = list_div.get_text(strip=True)
                    
                    if player:
                        data["expected_injuries"]["home"].append(player)

                # Away
                away_shangting = shangting_divs[1]
                away_items = away_shangting.find_all('div', class_='item')
                for item in away_items:
                    if 'itemtitle' in item.get('class', []): continue
                    player = {}
                    name_div = item.find('div', class_='name')
                    if name_div: player['name'] = name_div.get_text(strip=True)
                    price_div = item.find('div', class_='price')
                    if price_div: player['price'] = price_div.get_text(strip=True)
                    list_div = item.find('div', class_='list')
                    if list_div: player['status'] = list_div.get_text(strip=True)
                    if player:
                        data["expected_injuries"]["away"].append(player)

        except Exception as e:
            logger.warning(f"Error parsing form data: {e}")
        
        return data

    def parse_game(self, html_content: str, home_team: str, away_team: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html_content, 'lxml')
        data = {
            "points_table": []
        }
        
        try:
            # Only extracting "Latest" (Total) points for now as 6-match is not in the DOM
            table = soup.find('table', class_='table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) < 9:
                        continue
                    
                    team_name = cells[1].get_text(strip=True)
                    
                    # Check if row belongs to home or away team
                    # If names are not provided, we might skip filtering or return all?
                    # User requested "only 2 teams data".
                    if home_team and away_team:
                        if home_team not in team_name and away_team not in team_name:
                            continue
                    
                    item = {
                        "rank": cells[0].get_text(strip=True),
                        "team": team_name,
                        "played": cells[2].get_text(strip=True),
                        "won": cells[3].get_text(strip=True),
                        "drawn": cells[4].get_text(strip=True),
                        "lost": cells[5].get_text(strip=True),
                        "goals_for": cells[6].get_text(strip=True),
                        "goals_against": cells[7].get_text(strip=True),
                        "points": cells[8].get_text(strip=True)
                    }
                    data["points_table"].append(item)
        except Exception as e:
            logger.warning(f"Error parsing game data: {e}")
            
        return data

    def parse_exchanges(self, html_content: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html_content, 'lxml')
        data = {
            "jczq_save": [],
            "jczq_popularity": [],
            "betfair_transaction": [],
            "transaction_distribution": [],
            "five_factors": []
        }
        
        def parse_exchange_table(section_title_keyword, keys):
            try:
                # Find section by title
                titles = soup.find_all('div', class_='exchange-title')
                target_section = None
                for t in titles:
                    if section_title_keyword in t.get_text():
                        target_section = t.find_parent('section')
                        break
                
                if not target_section:
                    return []
                    
                rows_data = []
                table = target_section.find('table', class_='exchange-table')
                if table:
                    rows = table.find_all('tr')
                    # Skip header
                    for row in rows[1:]:
                        cells = row.find_all('td')
                        if not cells: continue
                        
                        item = {}
                        # Mapping logic based on keys list
                        # First cell is usually Row Label (Win/Draw/Loss) or Factor Name
                        item[keys[0]] = cells[0].get_text(strip=True)
                        
                        for i, key in enumerate(keys[1:], 1):
                            if i < len(cells):
                                item[key] = cells[i].get_text(strip=True)
                        
                        rows_data.append(item)
                return rows_data
            except Exception as e:
                logger.warning(f"Error parsing exchange table {section_title_keyword}: {e}")
                return []

        # 1. Jczq Save (竞足保存盈亏)
        data["jczq_save"] = parse_exchange_table("竞足保存盈亏", ["result", "index", "save_amount", "profit", "hot_cold"])

        # 2. Jczq Popularity (竞足人气盈亏)
        data["jczq_popularity"] = parse_exchange_table("竞足人气盈亏", ["result", "index", "popularity", "profit"])

        # 3. Betfair Transaction (必发交易盈亏)
        data["betfair_transaction"] = parse_exchange_table("必发交易盈亏", ["result", "index", "transaction_amount", "profit", "hot_cold"])

        # 4. Transaction Distribution (交易分布对比)
        data["transaction_distribution"] = parse_exchange_table("交易分布对比", ["result", "odds_99", "betfair", "jczq_order", "jczq_pop"])

        # 5. Five Factors (五要素)
        data["five_factors"] = parse_exchange_table("五要素", ["factor", "home_win", "draw", "home_loss", "suggestion"])
        
        return data

    def parse_odds_change(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Parse odds change history (e.g. for Bifa/Betfair).
        Structure: Win | Draw | Loss | Time
        HTML Structure: table.changeTable -> tr -> td[0] (3 spans) | td[1] (Time)
        """
        soup = BeautifulSoup(html_content, 'lxml')
        data = []
        try:
            # Look for the change table
            table = soup.find('table', class_='changeTable')
            if not table:
                # Fallback: sometimes it might be just matchtable? But checking html shows changeTable.
                table = soup.find('table', class_='matchtable')
                
            if not table:
                return data

            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 2:
                    continue

                # First cell contains the odds values in spans
                # <td><span>1.26</span><span class="fontblue">7.60</span><span>12.00</span></td>
                odds_cell = cells[0]
                odds_spans = odds_cell.find_all('span')
                
                # We expect at least 3 spans for Win, Draw, Loss
                if len(odds_spans) < 3:
                    continue
                
                win = odds_spans[0].get_text(strip=True)
                draw = odds_spans[1].get_text(strip=True)
                loss = odds_spans[2].get_text(strip=True)
                
                # Second cell contains time
                # <td class="timetd jsChangeContent" time="01-27 01:28">赛前2分钟</td>
                time_cell = cells[1]
                time_str = time_cell.get_text(strip=True)

                # Basic validation: check if odds are numeric (allowing for '.' and empty strings)
                # Note: values can be empty or "-" sometimes
                if not (win or draw or loss):
                    continue

                data.append({
                    "win": win,
                    "draw": draw,
                    "loss": loss,
                    "time": time_str
                })
        except Exception as e:
            logger.warning(f"Error parsing odds change: {e}")
        return data

    def parse_handicap_change(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Parse handicap change history (e.g. for Macao).
        Structure: Home | Handicap | Away | Time
        HTML Structure: table.changeTable -> tr -> td[0] (3 spans) | td[1] (Time)
        """
        soup = BeautifulSoup(html_content, 'lxml')
        data = []
        try:
            # Look for the change table
            table = soup.find('table', class_='changeTable')
            if not table:
                table = soup.find('table', class_='matchtable')
            
            if not table:
                return data

            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 2:
                    continue

                # First cell contains the handicap values in spans
                # <td><span class="fontblue">1.62</span><span>球半</span><span class="fontred2">2.16</span></td>
                handicap_cell = cells[0]
                spans = handicap_cell.find_all('span')
                
                if len(spans) < 3:
                    continue
                
                home_water = spans[0].get_text(strip=True)
                handicap = spans[1].get_text(strip=True)
                away_water = spans[2].get_text(strip=True)
                
                # Second cell contains time
                time_cell = cells[1]
                time_str = time_cell.get_text(strip=True)

                if not (home_water or handicap or away_water):
                    continue

                data.append({
                    "home_water": home_water,
                    "handicap": handicap,
                    "away_water": away_water,
                    "time": time_str
                })
        except Exception as e:
            logger.warning(f"Error parsing handicap change: {e}")
        return data


    def process_all(self):
        # Find all files
        files = glob(os.path.join(self.data_dir, "*.html"))
        
        # Group by Match ID
        # Filename format: type_matchid_timestamp.html or type_matchid.html
        # Special case: game_recent_matchid.html
        matches = {}
        for f in files:
            basename = os.path.basename(f)
            parts = basename.split('_')
            if len(parts) < 2:
                continue
            
            page_type = parts[0]
            
            # Handle game_recent
            if page_type == "game" and len(parts) > 2 and parts[1] == "recent":
                page_type = "gamerecent"
                match_id_part = parts[2]
            else:
                match_id_part = parts[1]
                
            match_id = match_id_part.split('.')[0]
            
            if match_id not in matches:
                matches[match_id] = {}
            
            matches[match_id][page_type] = f

        logger.info(f"Found {len(matches)} matches to process.")
        
        success_count = 0
        fail_count = 0
        
        for match_id, files_map in matches.items():
            try:
                match_data = {"match_id": match_id}
                
                # Parse History first to get basic info (including team names)
                if "history" in files_map:
                    with open(files_map["history"], 'r', encoding='utf-8') as f:
                        match_data.update(self.parse_history(f.read()))
                
                # Parse Handicap
                if "handicap" in files_map:
                    with open(files_map["handicap"], 'r', encoding='utf-8') as f:
                        match_data["handicap"] = self.parse_handicap(f.read())
                        
                # Parse Odds
                if "odds" in files_map:
                    with open(files_map["odds"], 'r', encoding='utf-8') as f:
                        match_data["euro_odds"] = self.parse_odds(f.read())
                
                # Parse Form
                if "form" in files_map:
                    with open(files_map["form"], 'r', encoding='utf-8') as f:
                        match_data["form_analysis"] = self.parse_form(f.read())
                        
                # Parse Game (Points)
                # Requires home/away team names for filtering
                if "game" in files_map:
                    home_team = match_data.get("match_info", {}).get("home_team", "")
                    away_team = match_data.get("match_info", {}).get("away_team", "")
                    with open(files_map["game"], 'r', encoding='utf-8') as f:
                        match_data["game_points"] = self.parse_game(f.read(), home_team, away_team)

                # Parse Game Recent (6-match Points)
                if "gamerecent" in files_map:
                    home_team = match_data.get("match_info", {}).get("home_team", "")
                    away_team = match_data.get("match_info", {}).get("away_team", "")
                    with open(files_map["gamerecent"], 'r', encoding='utf-8') as f:
                        match_data["game_points_recent"] = self.parse_game(f.read(), home_team, away_team)

                # Parse Game Points (Complete)
                if "game" in files_map:
                    home_team = match_data.get("match_info", {}).get("home_team", "")
                    away_team = match_data.get("match_info", {}).get("away_team", "")
                    with open(files_map["game"], 'r', encoding='utf-8') as f:
                        match_data["game_points_total"] = self.parse_game(f.read(), home_team, away_team)

                # Parse Exchanges
                if "exchanges" in files_map:
                    with open(files_map["exchanges"], 'r', encoding='utf-8') as f:
                        match_data["exchanges"] = self.parse_exchanges(f.read())
                
                # Save to JSON
                output_file = os.path.join(self.output_dir, f"{match_id}.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(match_data, f, ensure_ascii=False, indent=2)
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to process match {match_id}: {e}")
                fail_count += 1
                
        logger.info(f"Processing complete. Success: {success_count}, Failed: {fail_count}")
        return success_count, fail_count

if __name__ == "__main__":
    parser = OkoooParser(DATA_DIR, OUTPUT_DIR)
    parser.process_all()
