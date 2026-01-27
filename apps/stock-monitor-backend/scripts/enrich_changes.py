import json
import os
import time
import random
import sys
import logging
from playwright.sync_api import sync_playwright

# Add script directory to path to import parser
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from parse_okooo_mobile import OkoooParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = "/Users/mac/StudioProjects/2026/open-citycloud-workspace/data/okooo"
PROCESSED_FILE = os.path.join(DATA_DIR, "processed_samples", "1314249.json")
TEMP_HTML_DIR = os.path.join(DATA_DIR, "mobile_changes")
USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"
]

def random_sleep(min_seconds=2, max_seconds=5):
    time.sleep(random.uniform(min_seconds, max_seconds))

def fetch_html(page, url, output_path):
    if os.path.exists(output_path):
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
        
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
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

def enrich_changes():
    if not os.path.exists(PROCESSED_FILE):
        logger.error(f"File not found: {PROCESSED_FILE}")
        return

    with open(PROCESSED_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Initialize parser
    OUTPUT_DIR = os.path.join(DATA_DIR, "processed_samples")
    parser = OkoooParser(DATA_DIR, OUTPUT_DIR)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 390, 'height': 844},
            user_agent=random.choice(USER_AGENTS)
        )
        
        # Add stealth script
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            window.chrome = { runtime: {} };
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: 'granted' }) :
                    originalQuery(parameters)
            );
        """)
        
        page = context.new_page()
        
        # Prime session
        logger.info("Priming session by visiting homepage...")
        try:
            page.goto("https://m.okooo.com/", timeout=60000)
            random_sleep(2, 4)
        except Exception as e:
            logger.warning(f"Failed to load homepage: {e}")

        # 1. Bifa Index (Odds Change)
        # Using match 1314249 for consistency
        bifa_url = "https://m.okooo.com/match/change.php?mid=1314249&pid=19&Type=odds"
        bifa_path = os.path.join(TEMP_HTML_DIR, "1314249", "bifa_odds_change.html")
        
        logger.info("Fetching Bifa Index...")
        bifa_html = fetch_html(page, bifa_url, bifa_path)
        if bifa_html:
            bifa_data = parser.parse_odds_change(bifa_html)
            data["bifaIndex"] = bifa_data
            logger.info(f"Added {len(bifa_data)} bifaIndex records")
        
        # 2. Macao Index (Handicap Change)
        macao_url = "https://m.okooo.com/match/change.php?mid=1314249&pid=84&Type=Handicap"
        macao_path = os.path.join(TEMP_HTML_DIR, "1314249", "macao_handicap_change.html")
        
        logger.info("Fetching Macao Index...")
        macao_html = fetch_html(page, macao_url, macao_path)
        if macao_html:
            macao_data = parser.parse_handicap_change(macao_html)
            data["macaoIndex"] = macao_data
            logger.info(f"Added {len(macao_data)} macaoIndex records")
            
        browser.close()

    # Final Save
    with open(PROCESSED_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Completed enrichment. Updated file: {PROCESSED_FILE}")

if __name__ == "__main__":
    enrich_changes()
