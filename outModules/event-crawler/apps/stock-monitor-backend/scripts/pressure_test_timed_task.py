import asyncio
import time
import random
import httpx
from statistics import mean, median

BASE_URL = "http://127.0.0.1:8000/api"

async def get_stock_codes(client):
    """Fetch some stock codes to query history"""
    try:
        res = await client.get(f"{BASE_URL}/scores/latest?page_size=50")
        if res.status_code == 200:
            data = res.json().get("data", [])
            return [item["code"] for item in data]
    except Exception as e:
        print(f"Error fetching stock codes: {e}")
    return ["000001.SZ", "600000.SH"] # Fallback

async def stress_test_queries(client, codes, total_requests=500, concurrency=10):
    print(f"Starting pressure test: {total_requests} requests with concurrency {concurrency}...")
    
    start_time = time.time()
    latencies = []
    errors = 0
    
    semaphore = asyncio.Semaphore(concurrency)

    async def worker(requests_per_worker):
        nonlocal errors
        async with semaphore:
            for _ in range(requests_per_worker):
                t0 = time.time()
                try:
                    # Randomly choose between latest scores and history
                    choice = random.choice(["latest", "history"])
                    
                    if choice == "latest":
                        # Random filter
                        page = random.randint(1, 5)
                        pool_type = random.choice(["self_selected", "wencai", ""])
                        url = f"{BASE_URL}/scores/latest?page={page}&page_size=20"
                        if pool_type:
                            url += f"&pool_type={pool_type}"
                        
                        await client.get(url)
                    else:
                        # History
                        code = random.choice(codes)
                        await client.get(f"{BASE_URL}/scores/history/{code}")
                        
                    latencies.append((time.time() - t0) * 1000) # ms
                except Exception as e:
                    errors += 1
                    # print(f"Request failed: {e}")

    # Distribute requests
    requests_per_worker = total_requests // concurrency
    workers = [worker(requests_per_worker) for _ in range(concurrency)]
    
    await asyncio.gather(*workers)
    
    duration = time.time() - start_time
    rps = total_requests / duration
    
    print("\n=== Test Results ===")
    print(f"Total Requests: {total_requests}")
    print(f"Errors: {errors}")
    print(f"Duration: {duration:.2f}s")
    print(f"RPS: {rps:.2f}")
    if latencies:
        print(f"Latency (ms):")
        print(f"  Mean: {mean(latencies):.2f}")
        print(f"  Median: {median(latencies):.2f}")
        print(f"  Max: {max(latencies):.2f}")
        print(f"  Min: {min(latencies):.2f}")
    print("====================")

async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Get some codes
        print("Fetching initial data...")
        codes = await get_stock_codes(client)
        if not codes:
            codes = ["000001.SZ", "600000.SH"]
        print(f"Got {len(codes)} codes for testing.")
        
        # 2. Run stress test
        await stress_test_queries(client, codes, total_requests=100, concurrency=20)

if __name__ == "__main__":
    asyncio.run(main())
