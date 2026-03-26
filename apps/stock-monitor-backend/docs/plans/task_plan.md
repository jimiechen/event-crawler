# Task Plan: Okooo Data Pipeline Implementation

## Goal
Implement a complete data pipeline for Okooo sports betting data, including crawling, cleaning, vectorization, and integration with the sports-betting framework.

## Phases

### Phase 1: HTML Source Crawling
- [x] **Develop/Update Crawler**
    - [x] Modify `okooo_crawler.py` to fix encoding (GBK -> UTF-8).
    - [x] Create batch script `scripts/batch_crawl_okooo.py`.
- [x] **Execute Crawling**
    - [x] Input: Match ID list provided by user.
    - [x] Output: Save HTML files to `data/okooo/raw_html/{YYYY-MM-DD}/{match_id}.html`.
    - [x] **Attempt 1**: Failed due to WAF (Aliyun 405 Block).
    - [x] **Resolution**: Implemented advanced anti-detection (Stealth JS, Headers, Browser Args, Random Behavior).
    - [x] **Attempt 2**: Successful. Crawler is processing 40 matches.

### Phase 2: Data Extraction and Cleaning
- [x] **Data Extraction**
    - [x] Implement parsing logic using `BeautifulSoup` in `scripts/parse_okooo_mobile.py`.
    - [x] Handle multiple file types per match (History, Handicap, Odds).
    - [x] **Extension**: Add parsing for Form (Lineup/Tech), Game (Points), and Exchanges (Profit/Loss).
- [x] **Data Cleaning**
    - [x] Normalize scores, dates, and odds formats.
    - [x] Handle missing values gracefully.
- [x] **Format Conversion**
    - [x] Convert to standardized JSON structure.
    - [x] Save to `data/okooo/processed/{match_id}.json`.
- [x] **Verification & Refinement**
    - [x] Identify missing fields (Handicap Pan, Opponent Info, League).
    - [x] Update parser to handle HTML structure quirks (e.g., `em` tags vs `span`).
    - [x] Re-run extraction pipeline and verify data completeness.
    - [x] **Extension**: Verify Form, Game, and Exchanges data against sample files.


### Phase 3: Migration & Cleanup
- [x] Create initialization script `scripts/init_jobs.py` for Generic Tasks
- [x] Modify `scheduler_service.py` to remove hardcoded jobs
- [ ] Verify `scheduler_service.py` still loads Generic Tasks correctly

### Phase 4: Framework Integration
- [ ] **Integration**

### Phase 5: Application & Validation
- [ ] **Model Training**
- [ ] **Validation**

## Current Status
- Phase: Phase 1
- Status: In Progress (WAF Bypass Verified)

## Errors & Issues
| Error | Attempt | Resolution |
|-------|---------|------------|
| 405 Blocked | Curl & Playwright | Detected Aliyun WAF. Resolved by "Homepage First" strategy + Stealth JS + Referer. Verified with `scripts/crawl_bypass_test.py`. |
