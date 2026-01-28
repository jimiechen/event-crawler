import json
import os
import time
import random
import sys
import logging
import re
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup

# Add script directory to path to import parser
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from parse_okooo_mobile import OkoooParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("batch_crawl.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BatchCrawl")

# Constants
DATA_DIR = "/Users/mac/StudioProjects/2026/open-citycloud-workspace/data/okooo"
PROCESSED_DIR = os.path.join(DATA_DIR, "processed_samples")
TEMP_HTML_DIR = os.path.join(DATA_DIR, "batch_html")
USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"
]

def random_sleep(min_seconds=2, max_seconds=5):
    time.sleep(random.uniform(min_seconds, max_seconds))

def fetch_html(page: Page, url: str, output_path: str, force_reload=False) -> str:
    if os.path.exists(output_path) and not force_reload:
        logger.info(f"File already exists: {output_path}")
        with open(output_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    logger.info(f"Fetching: {url}")
    try:
        # Randomize User-Agent
        user_agent = random.choice(USER_AGENTS)
        page.set_extra_http_headers({
            "User-Agent": user_agent,
            "Referer": "https://m.okooo.com/",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
        })
        
        response = page.goto(url, wait_until="domcontentloaded", timeout=60000)
        if not response:
            return None

        # Check for WAF
        if "Verification" in page.title() or "滑块" in page.content():
            logger.warning(f"WAF detected for {url}. Waiting and retrying...")
            time.sleep(5)
            page.reload(wait_until="domcontentloaded")
            if "Verification" in page.title():
                 logger.error(f"WAF blocked access to {url}")
                 return None

        # Human-like interaction
        page.mouse.move(random.randint(100, 300), random.randint(100, 500))
        page.mouse.wheel(0, random.randint(100, 500))
        random_sleep(2, 4)
        
        content = page.content()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return content
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None

def get_match_list(page: Page) -> List[Dict[str, str]]:
    url = "https://m.okooo.com/jczq/"
    output_path = os.path.join(TEMP_HTML_DIR, "match_list.html")
    html = fetch_html(page, url, output_path)
    if not html:
        return []

    soup = BeautifulSoup(html, 'lxml')
    matches = []
    
    # Strategy: Find all match items with class 'listItem'
    match_items = soup.find_all('div', class_='listItem')
    
    if not match_items:
        logger.info("No match items found by class 'listItem', trying fallback...")
        # Fallback to finding links directly
        links = soup.find_all('a', href=re.compile(r'MatchID=(\d+)'))
        seen_ids = set()
        for link in links:
            mid_match = re.search(r'MatchID=(\d+)', link['href'])
            if mid_match:
                mid = mid_match.group(1)
                if mid not in seen_ids:
                    matches.append({"id": mid, "time": ""})
                    seen_ids.add(mid)
    else:
        current_date = ""
        # Try to find date in headers if items are grouped
        # The structure seems to be: header, content(items), header, content(items)...
        # But parsing flat list of items might be easier.
        
        for item in match_items:
            try:
                # Extract Match ID from history link
                history_link = item.find('a', href=re.compile(r'history\.php'))
                if not history_link:
                    continue
                
                mid_match = re.search(r'MatchID=(\d+)', history_link['href'])
                if not mid_match:
                    continue
                
                mid = mid_match.group(1)
                
                # Extract Time
                time_tag = item.find('time', class_='timetxt')
                match_time = time_tag.get_text(strip=True) if time_tag else ""
                
                # If match_time is empty, maybe try to find date from previous header?
                # For now, leave as is.
                
                matches.append({
                    "id": mid,
                    "time": match_time
                })
            except Exception as e:
                logger.warning(f"Error parsing match item: {e}")

    logger.info(f"Found {len(matches)} matches")
    # Filter for specific missing matches if needed, or process all
    target_ids = ["1314467", "1320144", "1320145"]
    filtered_matches = [m for m in matches if m['id'] in target_ids]
    if filtered_matches:
        logger.info(f"Filtered to target matches: {target_ids}")
        return filtered_matches
    
    return matches[:40] # Return up to 40

def process_match(page: Page, parser: OkoooParser, match: Dict[str, str], failed_tasks: List[Dict[str, Any]]):
    mid = match['id']
    match_time = match['time']
    logger.info(f"Processing Match {mid}...")
    
    match_dir = os.path.join(TEMP_HTML_DIR, mid)
    os.makedirs(match_dir, exist_ok=True)
    
    # 1. Fetch History Page (Main Data Source)
    history_url = f"https://m.okooo.com/match/history.php?MatchID={mid}&from=%2Fjczq%2F"
    history_path = os.path.join(match_dir, "history.html")
    history_html = fetch_html(page, history_url, history_path)
    
    if not history_html:
        failed_tasks.append({"type": "history", "match": match, "url": history_url})
        return

    # Parse basic data
    try:
        # Pass match_id to parse_history
        data = parser.parse_history(history_html, match_id=mid)
        if not data["match_info"].get("match_time"):
            data["match_info"]["match_time"] = match_time
    except Exception as e:
        logger.error(f"Error parsing history for {mid}: {e}")
        failed_tasks.append({"type": "history_parse", "match": match, "url": history_url})
        return

    # 1.1 Fetch Exchanges (Ying Kui)
    exchanges_url = f"https://m.okooo.com/match/exchanges.php?MatchID={mid}&from=%2Fjczq%2F"
    exchanges_path = os.path.join(match_dir, "exchanges.html")
    exchanges_html = fetch_html(page, exchanges_url, exchanges_path)
    if exchanges_html:
        try:
            data["exchanges"] = parser.parse_exchanges(exchanges_html)
        except AttributeError:
             logger.warning("parse_exchanges not implemented yet")
        except Exception as e:
            logger.error(f"Error parsing exchanges for {mid}: {e}")

    # 1.2 Fetch Game Points (Ji Fen)
    game_url = f"https://m.okooo.com/match/game.php?MatchID={mid}&from=%2Fjczq%2F"
    game_path = os.path.join(match_dir, "game.html")
    game_html = fetch_html(page, game_url, game_path)
    if game_html:
        try:
            data["game_points"] = parser.parse_game_points(game_html)
        except AttributeError:
             logger.warning("parse_game_points not implemented yet")
        except Exception as e:
            logger.error(f"Error parsing game points for {mid}: {e}")

    # 1.3 Fetch Form Analysis (Zhen Rong)
    form_url = f"https://m.okooo.com/match/form.php?MatchID={mid}&from=%2Fjczq%2F"
    form_path = os.path.join(match_dir, "form.html")
    form_html = fetch_html(page, form_url, form_path)
    if form_html:
        try:
            data["form_analysis"] = parser.parse_form_analysis(form_html)
        except AttributeError:
             logger.warning("parse_form_analysis not implemented yet")
        except Exception as e:
            logger.error(f"Error parsing form analysis for {mid}: {e}")

    # 2. Fetch Bifa Index (Odds Change)
    bifa_url = f"https://m.okooo.com/match/change.php?mid={mid}&pid=19&Type=odds"
    bifa_path = os.path.join(match_dir, "bifa_odds_change.html")
    bifa_html = fetch_html(page, bifa_url, bifa_path)
    if bifa_html:
        data["bifaIndex"] = parser.parse_odds_change(bifa_html)
    else:
        failed_tasks.append({"type": "odds", "match": match, "url": bifa_url})

    # 3. Fetch Macao Index (Handicap Change)
    macao_url = f"https://m.okooo.com/match/change.php?mid={mid}&pid=84&Type=Handicap"
    macao_path = os.path.join(match_dir, "macao_handicap_change.html")
    macao_html = fetch_html(page, macao_url, macao_path)
    if macao_html:
        data["macaoIndex"] = parser.parse_handicap_change(macao_html)
    else:
        failed_tasks.append({"type": "handicap", "match": match, "url": macao_url})

    # 4. Enrich History Items (Limit to 2 per section)
    history_keys = ["home_history", "away_history", "head_to_head"]
    for key in history_keys:
        items = data.get(key, [])
        for i, item in enumerate(items[:2]):
            h_mid = item.get("match_id")
            if not h_mid: continue
            
            # Handicap
            h_url = f"https://m.okooo.com/match/handicap.php?MatchID={h_mid}&from=%2Fjczq%2F"
            h_path = os.path.join(match_dir, f"history_{h_mid}_handicap.html")
            h_html = fetch_html(page, h_url, h_path)
            if h_html:
                item["handicap"] = parser.parse_handicap(h_html)
                
            # Odds
            o_url = f"https://m.okooo.com/match/odds.php?MatchID={h_mid}&from=%2Fjczq%2F"
            o_path = os.path.join(match_dir, f"history_{h_mid}_odds.html")
            o_html = fetch_html(page, o_url, o_path)
            if o_html:
                item["euro_odds"] = parser.parse_odds(o_html)

    # Save Result
    output_file = os.path.join(PROCESSED_DIR, f"{mid}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {mid}.json")

def main():
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)
        
    parser = OkoooParser(DATA_DIR, PROCESSED_DIR)
    failed_tasks = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 390, 'height': 844},
            user_agent=random.choice(USER_AGENTS)
        )
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            window.chrome = { runtime: {} };
        """)
        
        page = context.new_page()
        
        try:
            page.goto("https://m.okooo.com/", timeout=60000)
            random_sleep()
        except Exception:
            pass
            
        matches = get_match_list(page)
        if not matches:
            logger.error("No matches found to crawl.")
        else:
            logger.info(f"Starting batch crawl for {len(matches)} matches...")
            
            for i, match in enumerate(matches):
                logger.info(f"[{i+1}/{len(matches)}] Processing {match['id']}")
                process_match(page, parser, match, failed_tasks)
                random_sleep(1, 3)
            
            # Retry Logic
            if failed_tasks:
                logger.info(f"Retrying {len(failed_tasks)} failed tasks...")
                # Write to file first
                with open("failed_tasks.json", "w", encoding="utf-8") as f:
                     json.dump(failed_tasks, f, ensure_ascii=False, indent=2)
                
                for task in failed_tasks:
                    mid = task['match']['id']
                    task_type = task['type']
                    url = task['url']
                    logger.info(f"Retrying {task_type} for {mid}...")
                    
                    match_dir = os.path.join(TEMP_HTML_DIR, mid)
                    os.makedirs(match_dir, exist_ok=True)
                    
                    html_path = os.path.join(match_dir, f"retry_{task_type}.html")
                    html = fetch_html(page, url, html_path)
                    
                    if html:
                        json_path = os.path.join(PROCESSED_DIR, f"{mid}.json")
                        
                        if task_type == 'history':
                            try:
                                data = parser.parse_history(html)
                                if not data["match_info"].get("match_time"):
                                    data["match_info"]["match_time"] = task['match']['time']
                                # If history retry succeeds, we might want to try odds/handicap too if they were missing?
                                # But for now just save history.
                                with open(json_path, 'w', encoding='utf-8') as f:
                                    json.dump(data, f, ensure_ascii=False, indent=2)
                                logger.info(f"Retry successful for {mid} history")
                            except Exception as e:
                                logger.error(f"Error parsing history retry for {mid}: {e}")
                                
                        elif os.path.exists(json_path):
                            # Load existing and update
                            try:
                                with open(json_path, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                
                                if task_type == 'odds':
                                    data["bifaIndex"] = parser.parse_odds_change(html)
                                elif task_type == 'handicap':
                                    data["macaoIndex"] = parser.parse_handicap_change(html)
                                    
                                with open(json_path, 'w', encoding='utf-8') as f:
                                    json.dump(data, f, ensure_ascii=False, indent=2)
                                logger.info(f"Retry successful for {mid} {task_type}")
                            except Exception as e:
                                logger.error(f"Error updating data for {mid}: {e}")
                                
        browser.close()

if __name__ == "__main__":
    main()
