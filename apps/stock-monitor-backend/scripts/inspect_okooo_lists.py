
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.crawler.okooo.downloader import OkoooDownloader

async def main():
    downloader = OkoooDownloader(headless=True, is_mobile=True)
    
    urls = [
        "https://m.okooo.com/jczq/",
        "https://m.okooo.com/bjdc/"
    ]
    
    try:
        for url in urls:
            print(f"Downloading {url}...")
            content = await downloader.download(url)
            if content:
                filename = f"okooo_{url.split('/')[-2]}.html"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Saved to {filename}")
            else:
                print(f"Failed to download {url}")
    finally:
        await downloader.close()

if __name__ == "__main__":
    asyncio.run(main())
