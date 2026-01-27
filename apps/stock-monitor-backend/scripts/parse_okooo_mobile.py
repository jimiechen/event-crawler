import os
import json
import re
import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict
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

    def parse_match_info(self, soup):
        info = {}
        # Basic parsing from title or meta if available
        if soup.title:
            title = soup.title.string
            league_match = re.search(r'【(.*?)】', title)
            if league_match:
                info['league'] = league_match.group(1)
        
        # Parse match nav content for teams and ranks
        nav = soup.find('div', class_='match-nav-content')
        if nav:
            # Home
            home_div = nav.find('div')
            if home_div:
                home_a = home_div.find('a')
                if home_a: info['home_team'] = home_a.get_text(strip=True)
                home_span = home_div.find('span', class_='num')
                if home_span: info['home_rank'] = home_span.get_text(strip=True).strip('[]')
            
            # Away
            away_div = nav.find_all('div')[-1]
            if away_div:
                away_a = away_div.find('a')
                if away_a: info['away_team'] = away_a.get_text(strip=True)
                away_span = away_div.find('span', class_='num')
                if away_span: info['away_rank'] = away_span.get_text(strip=True).strip('[]')
            
            # Score/Time
            date_div = nav.find('div', class_='date')
            if date_div:
                info['score_text'] = date_div.get_text(strip=True)

        return info

    def parse_history(self, soup) -> Dict[str, Any]:
        """
        Parse history page to extract match history and future matches.
        """
        history_data = {
            'home_history': [],
            'away_history': [],
            'future_matches': {'home': [], 'away': []},
            'head_to_head': []
        }
        
        try:
            # Identify Home/Away Teams
            match_info = self.parse_match_info(soup)
            home_team = match_info.get('home_team', '')
            away_team = match_info.get('away_team', '')

            # Parse Match Tables
            tables = soup.find_all('section', class_='jsMatchTableBox')
            for section in tables:
                section_type = section.get('type') # home or away
                
                rows = section.find_all('tr')
                parsed_rows = []
                for row in rows:
                    if row.get('class') and 'nolink' in row.get('class'):
                        # History Row
                        match_date = row.find('p', class_='gray9').get_text(strip=True) if row.find('p', class_='gray9') else ''
                        league = row.find('p', style=re.compile('width')).get_text(strip=True) if row.find('p', style=re.compile('width')) else ''
                        
                        score_cell = row.find('td', class_='team-score')
                        score = score_cell.get_text(strip=True) if score_cell else ''
                        
                        # Determine Opponent
                        team_l = row.find('div', class_='team-name-l')
                        team_r = row.find('div', class_='team-name-r')
                        
                        l_name = team_l.find('b').get_text(strip=True) if team_l else ''
                        r_name = team_r.find('b').get_text(strip=True) if team_r else ''
                        
                        entry = {
                            'date': match_date,
                            'league': league,
                            'score': score,
                            'home_team': l_name,
                            'away_team': r_name
                        }
                        
                        # Post-process opponent
                        current_team = home_team if section_type == 'home' else away_team
                        if current_team:
                            if l_name == current_team:
                                entry['opponent'] = r_name
                            else:
                                entry['opponent'] = l_name
                        
                        parsed_rows.append(entry)

                if section_type == 'home':
                    history_data['home_history'] = parsed_rows
                elif section_type == 'away':
                    history_data['away_history'] = parsed_rows

            # Parse Future Matches (Usually in sections with titles like "未来赛程")
            # Note: The provided sample might not have this section explicitly marked with a class, 
            # so we look for "未来" in titlebox
            title_boxes = soup.find_all('div', class_='titlebox')
            for box in title_boxes:
                if '未来' in box.get_text():
                    section = box.find_parent('section')
                    if section:
                        rows = section.find_all('tr')
                        future_rows = []
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) >= 3:
                                date = cols[0].get_text(strip=True)
                                event = cols[1].get_text(strip=True) if len(cols) > 1 else ''
                                # Home/Away logic for future matches is tricky without explicit columns
                                # Assuming col 2 is opponent
                                opponent = cols[2].get_text(strip=True) if len(cols) > 2 else ''
                                
                                future_rows.append({
                                    'date': date,
                                    'event': event,
                                    'opponent': opponent
                                })
                        
                        if home_team and home_team in box.get_text():
                             history_data['future_matches']['home'] = future_rows
                        elif away_team and away_team in box.get_text():
                             history_data['future_matches']['away'] = future_rows

        except Exception as e:
            logger.error(f"Error parsing history: {str(e)}")
            
        return history_data

    def parse_form(self, soup):
        """
        Parse form (lineups and injuries).
        """
        form_data = {
            'lineups': {'home': [], 'away': []},
            'injuries': {'home': [], 'away': []},
        }
        
        try:
            # Parse Lineups (.shoufa)
            shoufa_div = soup.find('div', class_='shoufa')
            if shoufa_div:
                # Iterate items
                items = shoufa_div.find_all('div', class_='item')
                for item in items:
                    if 'itemtitle' in item.get('class', []): continue
                    
                    # Parse Left (Home)
                    list_l = item.find('div', class_='list-l')
                    if list_l:
                        name_div = list_l.find('div', class_='name')
                        if name_div:
                            name = name_div.find('a').get_text(strip=True) if name_div.find('a') else name_div.get_text(strip=True)
                            num = list_l.find('div', class_='num').get_text(strip=True) if list_l.find('div', class_='num') else ''
                            form_data['lineups']['home'].append({'name': name, 'number': num})

                    # Parse Right (Away)
                    list_r = item.find('div', class_='list-r')
                    if list_r:
                        name_div = list_r.find('div', class_='name')
                        if name_div:
                            name = name_div.find('a').get_text(strip=True) if name_div.find('a') else name_div.get_text(strip=True)
                            num = list_r.find('div', class_='num').get_text(strip=True) if list_r.find('div', class_='num') else ''
                            form_data['lineups']['away'].append({'name': name, 'number': num})

            # Parse Injuries (.shangting)
            shangting_div = soup.find('div', class_='shangting')
            if shangting_div:
                # Check for "No Data"
                if shangting_div.find(class_='match-data-no'):
                    form_data['injuries_note'] = "No Data"
                else:
                    # Implement logic if data exists (similar structure to lineups usually)
                    pass

        except Exception as e:
            logger.error(f"Error parsing form: {str(e)}")
            
        return form_data

    def parse_game(self, soup):
        """
        Parse game (standings/points).
        """
        game_data = {
            'recent_6_match_points': []
        }
        
        try:
            # Look for table inside .sai-table
            tables = soup.find_all('table', class_='table')
            for table in tables:
                headers = [th.get_text(strip=True) for th in table.find_all('th')]
                if '排名' in headers and '积分' in headers:
                    rows = table.find_all('tr')[1:] # Skip header
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 9:
                            game_data['recent_6_match_points'].append({
                                'rank': cols[0].get_text(strip=True),
                                'team': cols[1].get_text(strip=True),
                                'matches': cols[2].get_text(strip=True),
                                'won': cols[3].get_text(strip=True),
                                'draw': cols[4].get_text(strip=True),
                                'lost': cols[5].get_text(strip=True),
                                'goals': cols[6].get_text(strip=True),
                                'miss': cols[7].get_text(strip=True),
                                'points': cols[8].get_text(strip=True)
                            })
        except Exception as e:
            logger.error(f"Error parsing game: {str(e)}")
            
        return game_data

    def parse_exchanges(self, soup):
        """
        Parse exchanges data.
        """
        exchange_data = {'five_factors': {}}
        try:
            exchange_box = soup.find_all('div', class_='exchange-box')
            for box in exchange_box:
                title = box.find('div', class_='exchange-title')
                if title and '五要素' in title.get_text():
                    table = box.find('table', class_='exchange-table')
                    if table:
                        rows = table.find_all('tr')
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) >= 4 and '交锋' in cols[0].get_text():
                                exchange_data['five_factors']['head_to_head'] = {
                                    'home_win_prob': cols[1].get_text(strip=True),
                                    'draw_prob': cols[2].get_text(strip=True),
                                    'away_win_prob': cols[3].get_text(strip=True)
                                }
        except Exception as e:
            logger.error(f"Error parsing exchanges: {str(e)}")
        return exchange_data

    def parse_odds_change(self, soup):
        """
        Parse odds change history.
        """
        odds_changes = []
        try:
            change_table = soup.find('table', class_='changeTable')
            if change_table:
                rows = change_table.find_all('tr')
                for row in rows:
                    time_td = row.find('td', class_='timetd')
                    if time_td:
                        time_val = time_td.get('time')
                        odds_td = row.find('td')
                        odds_spans = odds_td.find_all('span')
                        if len(odds_spans) >= 3:
                            odds_changes.append({
                                'time': time_val,
                                'home_win': odds_spans[0].get_text(strip=True),
                                'draw': odds_spans[1].get_text(strip=True),
                                'away_win': odds_spans[2].get_text(strip=True)
                            })
        except Exception as e:
            logger.error(f"Error parsing odds change: {str(e)}")
        return odds_changes

    def parse_handicap(self, soup) -> List[Dict[str, Any]]:
        data = []
        table = soup.find('section', id='pankou')
        if not table: return data
        
        rows = table.select('table.matchtable tbody tr')
        for row in rows:
            try:
                cells = row.find_all('td')
                if len(cells) < 4: continue
                
                company = cells[0].get_text(strip=True).replace('定制', '').replace('取消排序', '')
                
                # Helper to safely get text
                def get_text(elem, attr_type):
                    found = elem.find(['span', 'em'], attrs={'type': attr_type})
                    return found.get_text(strip=True) if found else ""

                init_cell = cells[1]
                init_odds = {
                    "home": get_text(init_cell, 'zhu'),
                    "pan": get_text(init_cell, 'chu'),
                    "away": get_text(init_cell, 'ke')
                }
                
                curr_cell = cells[2]
                curr_odds = {
                    "home": get_text(curr_cell, 'xinzhu'),
                    "pan": get_text(curr_cell, 'xin'),
                    "away": get_text(curr_cell, 'xinke')
                }
                
                data.append({
                    "company": company,
                    "initial": init_odds,
                    "latest": curr_odds
                })
            except Exception as e:
                logger.warning(f"Error parsing handicap row: {e}")
        return data

    def process_all(self):
        """
        Process all HTML files in the data directory.
        """
        logger.info("Starting batch processing...")
        match_files = defaultdict(dict)
        
        for root, dirs, files in os.walk(self.data_dir):
            for file in files:
                if not file.endswith('.html'): continue
                
                parts = file.replace('.html', '').split('_')
                
                if len(parts) == 1 and parts[0].isdigit():
                    mid = parts[0]
                    match_files[mid]['base'] = os.path.join(root, file)
                elif len(parts) >= 2:
                    type_name = parts[0]
                    mid = parts[1]
                    if type_name == 'odds' and len(parts) == 4 and parts[1] == 'change':
                         # odds_change_MID_PID
                         mid = parts[2]
                         pid = parts[3]
                         if 'odds_change' not in match_files[mid]: match_files[mid]['odds_change'] = []
                         match_files[mid]['odds_change'].append(os.path.join(root, file))
                    else:
                        match_files[mid][type_name] = os.path.join(root, file)

        for mid, files in match_files.items():
            logger.info(f"Processing Match ID: {mid}")
            match_data = {}
            
            # Base/Info
            if 'base' in files:
                with open(files['base'], 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    match_data['match_info'] = self.parse_match_info(soup)
                    match_data['handicap'] = self.parse_handicap(soup)

            # History
            if 'history' in files:
                with open(files['history'], 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    match_data.update(self.parse_history(soup))

            # Form
            if 'form' in files:
                with open(files['form'], 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    match_data['form'] = self.parse_form(soup)

            # Game
            if 'game' in files or 'game_recent' in files:
                game_file = files.get('game_recent', files.get('game'))
                if game_file:
                    with open(game_file, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f.read(), 'html.parser')
                        match_data['game'] = self.parse_game(soup)

            # Exchanges
            if 'exchanges' in files:
                with open(files['exchanges'], 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    match_data['exchanges'] = self.parse_exchanges(soup)

            # Odds Changes
            if 'odds_change' in files:
                match_data['odds_changes'] = []
                for odds_file in files['odds_change']:
                    with open(odds_file, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f.read(), 'html.parser')
                        filename = os.path.basename(odds_file)
                        pid_match = re.search(r'odds_change_\d+_(\d+)\.html', filename)
                        pid = pid_match.group(1) if pid_match else "unknown"
                        
                        data = self.parse_odds_change(soup)
                        match_data['odds_changes'].append({
                            'company_id': pid,
                            'changes': data
                        })

            # Save
            output_file = os.path.join(self.output_dir, f"{mid}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(match_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved data to {output_file}")

if __name__ == '__main__':
    parser = OkoooParser(DATA_DIR, OUTPUT_DIR)
    parser.process_all()
