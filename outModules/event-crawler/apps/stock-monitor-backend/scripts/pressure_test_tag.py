
import asyncio
import time
import random
import httpx
from statistics import mean, median

BASE_URL = "http://127.0.0.1:8000/api/v1/tags"

async def create_tags(client, count=50):
    print(f"Creating {count} tags...")
    tags = []
    for i in range(count):
        name = f"PerfTag_{i}_{int(time.time())}"
        score = round(random.uniform(1.0, 10.0), 2)
        try:
            res = await client.post(BASE_URL, json={"name": name, "score": score})
            if res.status_code == 200 and res.json().get("success"):
                tags.append(res.json()["data"]["id"])
        except Exception as e:
            print(f"Error creating tag: {e}")
    print(f"Created {len(tags)} tags.")
    return tags

async def associate_stocks(client, tag_ids, stock_count=20):
    print(f"Associating tags with {stock_count} stocks...")
    stocks = [f"STK{i:05d}" for i in range(stock_count)]
    
    tasks = []
    for tag_id in tag_ids:
        # Associate each tag with a random subset of stocks
        selected_stocks = random.sample(stocks, k=random.randint(1, 5))
        tasks.append(client.post(f"{BASE_URL}/{tag_id}/stocks", json={
            "stock_codes": selected_stocks,
            "tag_id": tag_id
        }))
    
    await asyncio.gather(*tasks)
    print("Association complete.")
    return stocks

async def query_stock_performance(client, stocks, total_requests=1000, concurrency=10):
    print(f"Starting pressure test: {total_requests} requests with concurrency {concurrency}...")
    
    start_time = time.time()
    latencies = []
    
    semaphore = asyncio.Semaphore(concurrency)

    async def worker():
        async with semaphore:
            for _ in range(total_requests // concurrency):
                stock = random.choice(stocks)
                t0 = time.time()
                try:
                    await client.get(f"{BASE_URL}/stocks/{stock}")
                    latencies.append((time.time() - t0) * 1000) # ms
                except Exception as e:
                    print(f"Request failed: {e}")

    workers = [worker() for _ in range(concurrency)]
    await asyncio.gather(*workers)
    
    duration = time.time() - start_time
    rps = total_requests / duration
    
    print("\n=== Test Results ===")
    print(f"Total Requests: {total_requests}")
    print(f"Duration: {duration:.2f}s")
    print(f"RPS: {rps:.2f}")
    print(f"Latency (ms):")
    print(f"  Mean: {mean(latencies):.2f}")
    print(f"  Median: {median(latencies):.2f}")
    print(f"  Max: {max(latencies):.2f}")
    print(f"  Min: {min(latencies):.2f}")
    print("====================")

async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Setup data
        tags = await create_tags(client)
        stocks = await associate_stocks(client, tags)
        
        # Run test
        await query_stock_performance(client, stocks)
        
        # Cleanup (Optional, but good for repeatability if we delete them)
        # For now we leave them or soft delete them
        # await cleanup(client, tags)

if __name__ == "__main__":
    asyncio.run(main())
