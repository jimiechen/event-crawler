# -*- coding: utf-8 -*-

import re
import logging
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class OkoooParser:
    """
    Okooo页面解析器
    负责解析各类Okooo页面的HTML内容
    """

    @staticmethod
    def parse_history(html_content: str) -> Dict[str, Any]:
        """
        解析历史战绩页面
        """
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

    @staticmethod
    def parse_handicap(html_content: str) -> List[Dict[str, Any]]:
        """
        解析亚盘页面
        """
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

    @staticmethod
    def parse_odds(html_content: str) -> List[Dict[str, Any]]:
        """
        解析欧赔页面
        """
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

    @staticmethod
    def parse_form(html_content: str) -> Dict[str, Any]:
        """
        解析阵容/分析页面
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

                    if home_player or away_player:
                        data["lineup_comparison"].append({
                            "home": home_player,
                            "away": away_player
                        })

        except Exception as e:
            logger.warning(f"Error parsing form data: {e}")
            
        return data
