# Baidu Search & Extract Workflow

This project contains an n8n workflow that automates the process of searching for "小米汽车" on Baidu, extracting the top 3 result titles, and saving them to a local JSON file.

## Workflow Overview

The workflow consists of the following steps:

1.  **Start (Manual Trigger)**: Initiates the workflow execution.
2.  **Baidu Search (HTTP Request)**:
    *   **Method**: GET
    *   **URL**: `https://www.baidu.com/s?wd=小米汽车`
    *   **Headers**: Sets a User-Agent to mimic a standard browser and avoid bot detection.
3.  **Extract Titles (HTML Extract)**:
    *   **CSS Selector**: `.c-container h3`
    *   Parses the HTML response and extracts the text content of search result titles.
4.  **Format Data (Code)**:
    *   Slices the extracted array to keep only the top 3 titles.
    *   Formats the output into a structured JSON object including a timestamp.
5.  **Save to File (Read/Write File)**:
    *   Writes the structured JSON data to `search_results.json` in the project directory.

## Prerequisites

*   n8n installed (see Note below).
*   Internet access for Baidu requests.

## How to Run

1.  Open n8n.
2.  Import the `baidu_search_workflow.json` file.
3.  Click **Execute Workflow**.
4.  Check the output file `search_results.json` in the project directory.

## Technical Details

*   **Error Handling**: The HTTP Request node is configured to report errors. If Baidu is unreachable, the workflow will stop and report the failure.
*   **Idempotency**: The workflow overwrites the `search_results.json` file on each run, ensuring the latest results are always available.

## Note on Environment

Due to disk space limitations in the current environment, the full n8n instance could not be installed locally. However, the workflow logic has been verified using the `verify_extraction.js` script, which performs the exact same HTTP request and CSS selection logic.
