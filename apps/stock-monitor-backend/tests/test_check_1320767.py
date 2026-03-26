#!/usr/bin/env python3
import requests
import json

# Test the check-files-exist API with 1320767
url = "http://localhost:8000/api/v1/okooo/check-files-exist"

# Sample task for 1320767
tasks = [
    {
        "match_id": "1320767",
        "url": "https://m.okooo.com/match/history.php?MatchID=1320767",
        "page_type": "mobile_form",
        "filename_prefix": "form"
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
