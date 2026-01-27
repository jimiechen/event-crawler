# Findings

## Phase 2 Findings (Data Extraction)
- **Data Structure Consistency**: The mobile version of Okooo pages (`/mobile/`) follows a consistent DOM structure, making `BeautifulSoup` parsing reliable.
- **Data Fragmentation**: Complete match data is distributed across three distinct page types:
    1.  **History Page**: Contains basic match info (Team names, League, Time) and historical performance (Recent matches for Home/Away).
    2.  **Handicap Page**: Contains Asian Handicap odds from multiple bookmakers.
    3.  **Odds Page**: Contains European (1x2) odds from multiple bookmakers.
- **Data Integrity**: All 40 crawled matches successfully yielded data across all three categories.
- **Odds Volatility**: The data includes both "Initial" and "Latest" odds, which is crucial for analyzing market movement.
- **Team Names**: Team names are consistent across pages, simplifying the merging process.
- **HTML Structure Quirks**:
    - **Handicap Values**: The actual handicap values ("pan") are hidden in `<em>` tags with `type="chu"` (initial) and `type="xin"` (latest), rather than the expected `<span>` tags.
    - **League Name**: The league name is often missing from the main match info block in the body but can be reliably extracted from the `<title>` tag (e.g., "Team A vs Team B 【League Name】").
    - **Opponent Identification**: In history tables, the opponent is not explicitly labeled. It must be inferred by checking which team (Home or Away column) matches the current subject team.
    - **Points Data**: "Game" page usually shows total points. "6-match" points require a specific URL parameter (`type=recent`).
    - **Exchanges Data**: Contains 5 distinct sub-tables (Save, Popularity, Betfair, Distribution, Five Elements). "Five Elements" is critical for prediction suggestions.
    - **Form Data**: Rich in lineup details (value, age, height) and technical stats (shots, goals, possession), which are valuable for feature engineering.

## Project Context
- **Project**: Stock Monitor Backend / Event Crawler
- **Target**: Okooo (澳客网)
- **Goal**: Crawl match history, process data, vectorise, and integrate.

## Technical Details
- **Base URL**: `https://www.okooo.com/match/history.php?MatchID={match_id}`
- **Existing Crawler**: `app/crawler/okooo_crawler.py`
- **Encoding Issue**: Source HTML declares GBK but might be saved/read as UTF-8, causing mojibake.
- **Match IDs**: User provided a list of ~40 match IDs for Phase 1.

## User Input Data
- **Batch Name**: `OkoooCrawl_20260126_212810`
- **Total Matches**: 40
- **Sample IDs**: 1307926, 1302755, etc.

## Decisions
- Will modify/extend `okooo_crawler.py` to support batch crawling by ID.
- Will enforce UTF-8 encoding during file save/read to fix mojibake.
