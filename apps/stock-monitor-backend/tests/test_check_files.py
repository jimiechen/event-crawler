#!/usr/bin/env python3
import requests
import json

# Test the check-files-exist API
url = "http://localhost:8000/api/v1/okooo/check-files-exist"

# Sample tasks from Redis
tasks = [
    {
        "match_id": "1320221",
        "url": "https://m.okooo.com/match/history.php?MatchID=1320221&from=%2Fjczq%2F",
        "page_type": "mobile_history",
        "filename_prefix": "history"
    },
    {
        "match_id": "1320221",
        "url": "https://m.okooo.com/match/change.php?mid=1320221&pid=84&Type=Handicap",
        "page_type": "mobile_change",
        "filename_prefix": "handicap-change"
    }
]

payload = {
    "tasks": tasks,
    "date": "2026-02-03"
}

print(f"Sending request to {url}")
print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

response = requests.post(url, json=payload)
print(f"\nResponse status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
