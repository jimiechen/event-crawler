import os
import json
import re
import logging
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup

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
            
            subject_team_name = data["match_info"].get("home_team") if section_type == "home" else data["match_info"].get("away_team")
            
            rows = section.select('table.matchtable tr')
            for row in rows:
                try:
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

    def parse_form_analysis(self, html_content: str) -> Dict[str, Any]:
        """解析球队阵容 (form) -> form_analysis"""
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
                for item in items:
                    if 'itemtitle' in item.get('class', []):
                        continue
                    
                    # Left (Home)
                    list_l = item.find('div', class_='list-l')
                    home_player = {}
                    if list_l:
                        name_div = list_l.find('div', class_='name')
                        if name_div:
                            a_tag = name_div.find('a')
                            i_tag = name_div.find('i')
                            if a_tag:
                                home_player['name'] = a_tag.get_text(strip=True)
                                home_player['id'] = a_tag.get('href', '').split('/')[-2] if a_tag.get('href') else ""
                            
                            if i_tag:
                                home_player['price'] = i_tag.get_text(strip=True)
                            
                            full_text = name_div.get_text(strip=True)
                            name_text = home_player.get('name', '')
                            price_text = home_player.get('price', '')
                            position_text = full_text.replace(name_text, '').replace(price_text, '').strip()
                            home_player['position'] = position_text

                        num_div = list_l.find('div', class_='num')
                        if num_div: home_player['number'] = num_div.get_text(strip=True)
                        zg_div = list_l.find('div', class_='zg')
                        if zg_div: home_player['assists'] = zg_div.get_text(strip=True)
                        jq_div = list_l.find('div', class_='jq')
                        if jq_div: home_player['goals'] = jq_div.get_text(strip=True)

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
                        if num_div: away_player['number'] = num_div.get_text(strip=True)
                        zg_div = list_r.find('div', class_='zg')
                        if zg_div: away_player['assists'] = zg_div.get_text(strip=True)
                        jq_div = list_r.find('div', class_='jq')
                        if jq_div: away_player['goals'] = jq_div.get_text(strip=True)
                    
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
                    player = {}
                    name_div = item.find('div', class_='name')
                    if name_div: player['name'] = name_div.get_text(strip=True)
                    price_div = item.find('div', class_='price')
                    if price_div: player['price'] = price_div.get_text(strip=True)
                    
                    list_div = item.find('div', class_='list')
                    if list_div: player['status'] = list_div.get_text(strip=True)
                    
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
            logger.warning(f"Error parsing form: {e}")
            
        return data

    def parse_bifa_odds_change(self, html_content: str) -> List[Dict[str, Any]]:
        """解析必发赔率变化 (bifaIndex)"""
        soup = BeautifulSoup(html_content, 'lxml')
        changes = []
        
        table = soup.find('table', class_='changeTable')
        if not table:
            return changes
            
        rows = table.find_all('tr')
        for row in rows:
            try:
                time_cell = row.find('td', class_='jsChangeContent')
                if not time_cell: continue
                
                time_val = time_cell.get_text(strip=True)
                
                odds_cell = row.find('td')
                if not odds_cell: continue
                    
                spans = odds_cell.find_all('span')
                if len(spans) >= 3:
                    win = spans[0].get_text(strip=True)
                    draw = spans[1].get_text(strip=True)
                    loss = spans[2].get_text(strip=True)
                    
                    changes.append({
                        "win": win,
                        "draw": draw,
                        "loss": loss,
                        "time": time_val
                    })
            except Exception as e:
                logger.warning(f"Error parsing bifa odds row: {e}")
                
        return changes

    def parse_macao_handicap_change(self, html_content: str) -> List[Dict[str, Any]]:
        """解析澳门盘口变化 (macaoIndex)"""
        soup = BeautifulSoup(html_content, 'lxml')
        changes = []
        
        table = soup.find('table', class_='changeTable')
        if not table:
            return changes
            
        rows = table.find_all('tr')
        for row in rows:
            try:
                time_cell = row.find('td', class_='jsChangeContent')
                if not time_cell: continue
                    
                time_val = time_cell.get_text(strip=True)
                
                odds_cell = row.find('td')
                if not odds_cell: continue
                    
                spans = odds_cell.find_all('span')
                if len(spans) >= 3:
                    home_water = spans[0].get_text(strip=True)
                    handicap = spans[1].get_text(strip=True)
                    away_water = spans[2].get_text(strip=True)
                    
                    changes.append({
                        "home_water": home_water,
                        "handicap": handicap,
                        "away_water": away_water,
                        "time": time_val
                    })
            except Exception as e:
                logger.warning(f"Error parsing macao handicap row: {e}")
                
        return changes

    def parse_game_points(self, html_content: str) -> List[Dict[str, Any]]:
        """解析积分榜 (game_points)"""
        soup = BeautifulSoup(html_content, 'lxml')
        points = []
        
        table_div = soup.find('div', class_='sai-table')
        if not table_div:
            return points
            
        table = table_div.find('table', class_='table')
        if not table:
            return points
            
        rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')
        for row in rows:
            try:
                cells = row.find_all('td')
                if len(cells) < 9: continue
                    
                rank = cells[0].get_text(strip=True)
                team = cells[1].get_text(strip=True)
                played = cells[2].get_text(strip=True)
                won = cells[3].get_text(strip=True)
                drawn = cells[4].get_text(strip=True)
                lost = cells[5].get_text(strip=True)
                goals_for = cells[6].get_text(strip=True)
                goals_against = cells[7].get_text(strip=True)
                pts = cells[8].get_text(strip=True)
                
                points.append({
                    "rank": rank,
                    "team": team,
                    "played": played,
                    "won": won,
                    "drawn": drawn,
                    "lost": lost,
                    "goals_for": goals_for,
                    "goals_against": goals_against,
                    "points": pts
                })
            except Exception as e:
                logger.warning(f"Error parsing game points row: {e}")
                
        return points

    def parse_exchanges(self, html_content: str) -> Dict[str, Any]:
        """解析交易盈亏 (exchanges)"""
        soup = BeautifulSoup(html_content, 'lxml')
        data = {
            "jczq_save": {},
            "jczq_popularity": {},
            "bifa_transaction": {},
            "transaction_distribution": [],
            "tips": [],
            "five_elements": []
        }
        
        try:
            # 1. 竞足保存盈亏
            canvas_save = soup.find('canvas', id='exchangeChart_Baocun')
            if canvas_save:
                data["jczq_save"] = {
                    "home": canvas_save.get('home'),
                    "draw": canvas_save.get('draw'),
                    "away": canvas_save.get('away')
                }
            
            # 2. 竞足人气盈亏
            canvas_pop = soup.find('canvas', id='exchangeChart_Renqi')
            if canvas_pop:
                data["jczq_popularity"] = {
                    "home": canvas_pop.get('home'),
                    "draw": canvas_pop.get('draw'),
                    "away": canvas_pop.get('away')
                }
                
            # 3. 必发交易盈亏
            canvas_bifa = soup.find('canvas', id='exchangeChart_Bifa')
            if canvas_bifa:
                data["bifa_transaction"] = {
                    "home": canvas_bifa.get('home'),
                    "draw": canvas_bifa.get('draw'),
                    "away": canvas_bifa.get('away')
                }
                
            # 4. 交易分布对比 & Tips & Five Elements
            sections = soup.find_all('section', class_='exchange-box')
            for sec in sections:
                title = sec.find('div', class_='exchange-title')
                if not title: continue
                
                title_text = title.get_text(strip=True)
                
                if "交易分布对比" in title_text:
                    table = sec.find('table', class_='exchange-table')
                    if table:
                        rows = table.find_all('tr')
                        for row in rows[1:]:
                            cells = row.find_all('td')
                            if len(cells) >= 5:
                                data["transaction_distribution"].append({
                                    "result": cells[0].get_text(strip=True),
                                    "avg_99": cells[1].get_text(strip=True),
                                    "bifa": cells[2].get_text(strip=True),
                                    "jczq_bet": cells[3].get_text(strip=True),
                                    "jczq_pop": cells[4].get_text(strip=True)
                                })
                                
                elif "小澳提点" in title_text:
                    paragraphs = sec.find_all('p', class_='paragraph')
                    for p in paragraphs:
                        data["tips"].append(p.get_text(strip=True))
                        
                elif "五要素" in title_text:
                    table = sec.find('table', class_='exchange-table')
                    if table:
                        rows = table.find_all('tr')
                        for row in rows[1:]:
                            cells = row.find_all('td')
                            if len(cells) >= 5:
                                data["five_elements"].append({
                                    "element": cells[0].get_text(strip=True),
                                    "home_win": cells[1].get_text(strip=True),
                                    "draw": cells[2].get_text(strip=True),
                                    "home_loss": cells[3].get_text(strip=True),
                                    "suggestion": cells[4].get_text(strip=True)
                                })

        except Exception as e:
            logger.warning(f"Error parsing exchanges: {e}")
            
        return data

    def process_directory(self, dir_path: str) -> Dict[str, Any]:
        """Process all HTML files in a directory and aggregate data"""
        logger.info(f"Processing directory: {dir_path}")
        
        match_id = os.path.basename(dir_path)
        combined_data = {
            "match_id": match_id
        }
        
        # 1. Parse history.html (Base)
        history_path = os.path.join(dir_path, "history.html")
        if os.path.exists(history_path):
            with open(history_path, 'r', encoding='utf-8', errors='ignore') as f:
                history_data = self.parse_history(f.read())
                combined_data.update(history_data)
        
        # 2. Parse handicap.html
        handicap_path = os.path.join(dir_path, "handicap.html")
        if os.path.exists(handicap_path):
            with open(handicap_path, 'r', encoding='utf-8', errors='ignore') as f:
                combined_data["handicap"] = self.parse_handicap(f.read())
        else:
             combined_data["handicap"] = []

        # 3. Parse odds.html
        odds_path = os.path.join(dir_path, "odds.html")
        if os.path.exists(odds_path):
            with open(odds_path, 'r', encoding='utf-8', errors='ignore') as f:
                combined_data["euro_odds"] = self.parse_odds(f.read())
        else:
            combined_data["euro_odds"] = []

        # 6. 球队阵容 (Form Analysis)
        form_html_path = os.path.join(dir_path, "form.html")
        if os.path.exists(form_html_path):
            with open(form_html_path, 'r', encoding='utf-8') as f:
                combined_data["form_analysis"] = self.parse_form_analysis(f.read())
        else:
            combined_data["form_analysis"] = {}
                
        # 5. Parse bifa_odds_change.html
        bifa_path = os.path.join(dir_path, "bifa_odds_change.html")
        if os.path.exists(bifa_path):
            with open(bifa_path, 'r', encoding='utf-8', errors='ignore') as f:
                combined_data["bifaIndex"] = self.parse_bifa_odds_change(f.read())
        else:
            combined_data["bifaIndex"] = []

        # 6. Parse macao_handicap_change.html
        macao_path = os.path.join(dir_path, "macao_handicap_change.html")
        if os.path.exists(macao_path):
            with open(macao_path, 'r', encoding='utf-8', errors='ignore') as f:
                combined_data["macaoIndex"] = self.parse_macao_handicap_change(f.read())
        else:
            combined_data["macaoIndex"] = []

        # 7. Parse game.html (Points)
        game_path = os.path.join(dir_path, "game.html")
        if os.path.exists(game_path):
            with open(game_path, 'r', encoding='utf-8', errors='ignore') as f:
                points = self.parse_game_points(f.read())
                combined_data["game_points"] = points
                combined_data["game_points_recent"] = points 
                combined_data["game_points_total"] = points
        else:
            combined_data["game_points"] = []
            combined_data["game_points_recent"] = []
            combined_data["game_points_total"] = []

        # 8. Parse exchanges.html
        exchanges_path = os.path.join(dir_path, "exchanges.html")
        if os.path.exists(exchanges_path):
            with open(exchanges_path, 'r', encoding='utf-8', errors='ignore') as f:
                combined_data["exchanges"] = self.parse_exchanges(f.read())
        else:
            combined_data["exchanges"] = {}

        return combined_data

    def process_date_match(self, date_str: str, match_id: str) -> Dict[str, Any]:
        """
        处理指定日期和比赛ID的目录（支持 matches/{日期}/{比赛ID}/ 结构）
        
        Args:
            date_str: 日期 (YYYY-MM-DD)
            match_id: 比赛ID
        
        Returns:
            解析后的数据字典
        """
        dir_path = os.path.join(self.data_dir, date_str, match_id)
        logger.info(f"Processing: {date_str}/{match_id}")
        
        if not os.path.exists(dir_path):
            raise FileNotFoundError(f"目录不存在: {dir_path}")
        
        combined_data = {
            "match_id": match_id,
            "parse_date": date_str
        }
        
        # 辅助函数：查找文件（支持两种命名格式）
        def find_file(*filenames):
            for filename in filenames:
                filepath = os.path.join(dir_path, filename)
                if os.path.exists(filepath):
                    return filepath
            return None
        
        # 1. Parse history - 支持 history_{match_id}.html 或 history.html
        history_path = find_file(f"history_{match_id}.html", "history.html")
        if history_path:
            with open(history_path, 'r', encoding='utf-8', errors='ignore') as f:
                history_data = self.parse_history(f.read())
                combined_data.update(history_data)
        
        # 2. Parse handicap - 支持 handicap_{match_id}.html 或 handicap.html
        handicap_path = find_file(f"handicap_{match_id}.html", "handicap.html")
        if handicap_path:
            with open(handicap_path, 'r', encoding='utf-8', errors='ignore') as f:
                combined_data["handicap"] = self.parse_handicap(f.read())
        else:
            combined_data["handicap"] = []
        
        # 3. Parse odds - 支持 odds_{match_id}.html 或 odds.html
        odds_path = find_file(f"odds_{match_id}.html", "odds.html")
        if odds_path:
            with open(odds_path, 'r', encoding='utf-8', errors='ignore') as f:
                combined_data["euro_odds"] = self.parse_odds(f.read())
        else:
            combined_data["euro_odds"] = []
        
        # 4. Parse form - 支持 form_{match_id}.html 或 form.html
        form_path = find_file(f"form_{match_id}.html", "form.html")
        if form_path:
            with open(form_path, 'r', encoding='utf-8') as f:
                combined_data["form_analysis"] = self.parse_form_analysis(f.read())
        else:
            combined_data["form_analysis"] = {}
        
        # 5. Parse exchanges - 支持 exchanges_{match_id}.html 或 exchanges.html
        exchanges_path = find_file(f"exchanges_{match_id}.html", "exchanges.html")
        if exchanges_path:
            with open(exchanges_path, 'r', encoding='utf-8', errors='ignore') as f:
                combined_data["exchanges"] = self.parse_exchanges(f.read())
        else:
            combined_data["exchanges"] = {}
        
        # 6. Parse bifa_change - 支持 bifa_change_{match_id}.html (必发指数)
        bifa_change_path = find_file(f"bifa_change_{match_id}.html", "bifa_change.html")
        if bifa_change_path:
            with open(bifa_change_path, 'r', encoding='utf-8', errors='ignore') as f:
                combined_data["bifaIndex"] = self.parse_bifa_odds_change(f.read())
        else:
            combined_data["bifaIndex"] = []
        
        # 7. Parse odds_change - 支持 odds_change_{match_id}.html (澳门指数/欧赔变化)
        odds_change_path = find_file(f"odds_change_{match_id}.html", "odds_change.html")
        if odds_change_path:
            with open(odds_change_path, 'r', encoding='utf-8', errors='ignore') as f:
                combined_data["macaoIndex"] = self.parse_bifa_odds_change(f.read())
        else:
            combined_data["macaoIndex"] = []
        
        # 7. Parse table - 支持 table_{match_id}.html 或 table.html
        table_path = find_file(f"table_{match_id}.html", "table.html")
        if table_path:
            with open(table_path, 'r', encoding='utf-8', errors='ignore') as f:
                points = self.parse_game_points(f.read())
                combined_data["game_points"] = points
                combined_data["game_points_recent"] = points
                combined_data["game_points_total"] = points
        else:
            combined_data["game_points"] = []
            combined_data["game_points_recent"] = []
            combined_data["game_points_total"] = []
        
        return combined_data
    
    def save_result(self, date_str: str, match_id: str, data: Dict) -> str:
        """
        保存解析结果到 processed/{日期}/ 目录
        
        Args:
            date_str: 日期 (YYYY-MM-DD)
            match_id: 比赛ID
            data: 解析后的数据
        
        Returns:
            输出文件路径
        """
        output_dir = os.path.join(self.output_dir, date_str)
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f"{match_id}.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return output_path

if __name__ == "__main__":
    parser = OkoooParser(DATA_DIR, OUTPUT_DIR)
    
    # Target directories
    target_dirs = [
        "/Users/mac/StudioProjects/2026/open-citycloud-workspace/data/okooo/batch_html/1320145",
        "/Users/mac/StudioProjects/2026/open-citycloud-workspace/data/okooo/batch_html/1320144",
        "/Users/mac/StudioProjects/2026/open-citycloud-workspace/data/okooo/batch_html/1314467"
    ]
    
    for dir_path in target_dirs:
        if os.path.exists(dir_path):
            try:
                data = parser.process_directory(dir_path)
                
                # Save to JSON
                output_file = os.path.join(OUTPUT_DIR, f"{data['match_id']}.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    
                logger.info(f"Successfully processed {dir_path} -> {output_file}")
            except Exception as e:
                logger.error(f"Failed to process {dir_path}: {e}")
        else:
            logger.warning(f"Directory not found: {dir_path}")
