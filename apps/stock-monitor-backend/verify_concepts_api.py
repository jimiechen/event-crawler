import asyncio
import aiohttp
import json

async def verify_concepts():
    url = "http://localhost:8000/api/v1/wencai/concepts"
    print(f"Sending request to {url}...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    concepts = data.get('data', [])
                    print(f"Total concepts found: {len(concepts)}")
                    
                    if concepts:
                        print("\nTop 5 concepts:")
                        for i, concept in enumerate(concepts[:5]):
                            print(f"{i+1}. {concept.get('name')} (Count: {concept.get('count')}, Avg Change: {concept.get('avg_change')}%)")
                            # Verify if stocks are included
                            stocks = concept.get('stocks', [])
                            print(f"   Stocks count: {len(stocks)}")
                            if stocks:
                                print(f"   Example stock: {stocks[0]['name']} ({stocks[0]['code']}) Change: {stocks[0]['change']}%")
                    else:
                        print("No concepts found in response.")
                else:
                    print(f"Error: {await response.text()}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_concepts())
