import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/v1/tags"

def print_res(res):
    print(f"Status: {res.status_code}")
    try:
        print(json.dumps(res.json(), indent=2, ensure_ascii=False))
    except:
        print(res.text)

def main():
    print("--- 1. Create Tag ---")
    tag_data = {"name": "TestTag_HighGrowth", "score": 5.0}
    res = requests.post(BASE_URL, json=tag_data)
    print_res(res)
    if res.status_code == 200 and res.json().get('success'):
        tag_id = res.json()['data']['id']
    else:
        # If exists from previous run, try to get it
        print("Tag might exist, fetching list...")
        res = requests.get(BASE_URL, params={"name": "TestTag_HighGrowth"})
        items = res.json()['data']['items']
        if items:
            tag_id = items[0]['id']
            print(f"Found existing tag ID: {tag_id}")
        else:
            print("Failed to get tag ID")
            return

    print("\n--- 2. Update Tag ---")
    update_data = {"score": 4.5}
    res = requests.put(f"{BASE_URL}/{tag_id}", json=update_data)
    print_res(res)

    print("\n--- 3. Batch Import ---")
    batch_data = [
        {"name": "TestTag_LowVal", "score": 3.0},
        {"name": "TestTag_Tech", "score": 4.0}
    ]
    res = requests.post(f"{BASE_URL}/batch", json=batch_data)
    print_res(res)

    print("\n--- 4. Associate Stocks ---")
    stock_codes = ["600000", "000001"]
    res = requests.post(f"{BASE_URL}/{tag_id}/stocks", json={"stock_codes": stock_codes, "tag_id": tag_id})
    print_res(res)

    print("\n--- 5. Get Tag Stocks ---")
    res = requests.get(f"{BASE_URL}/{tag_id}/stocks")
    print_res(res)

    print("\n--- 6. Get Stock Tags ---")
    res = requests.get(f"{BASE_URL}/stocks/600000")
    print_res(res)

    print("\n--- 7. Operation Logs ---")
    res = requests.get(f"{BASE_URL}/logs")
    print_res(res)
    
    print("\n--- 8. Delete Tag ---")
    # Clean up
    res = requests.delete(f"{BASE_URL}/{tag_id}")
    print_res(res)
    
    # Clean up others
    res = requests.get(BASE_URL, params={"name": "TestTag"})
    items = res.json()['data']['items']
    for item in items:
        requests.delete(f"{BASE_URL}/{item['id']}")

if __name__ == "__main__":
    main()
