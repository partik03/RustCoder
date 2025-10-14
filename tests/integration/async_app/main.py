"""Async application using asyncio and aiohttp."""

import asyncio
import aiohttp
from typing import List, Dict


async def fetch_url(session: aiohttp.ClientSession, url: str) -> Dict[str, str]:
    """Fetch a URL and return status."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
            status = response.status
            return {"url": url, "status": str(status), "success": status == 200}
    except Exception as e:
        return {"url": url, "status": "error", "error": str(e), "success": False}


async def fetch_multiple(urls: List[str]) -> List[Dict[str, str]]:
    """Fetch multiple URLs concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results


async def process_data(data: List[int]) -> int:
    """Process data asynchronously (simulated with sleep)."""
    await asyncio.sleep(0.1)  # Simulate async work
    total = sum(data)
    return total


async def main():
    """Main async function."""
    # Example 1: Fetch URLs
    urls = [
        "https://httpbin.org/status/200",
        "https://httpbin.org/status/404",
        "https://httpbin.org/delay/1",
    ]
    
    print("Fetching URLs...")
    results = await fetch_multiple(urls)
    
    for result in results:
        status = "✓" if result.get("success") else "✗"
        print(f"{status} {result['url']}: {result['status']}")
    
    # Example 2: Process data
    print("\nProcessing data...")
    data = [1, 2, 3, 4, 5]
    total = await process_data(data)
    print(f"Sum: {total}")
    
    print("\nAll tasks completed!")


if __name__ == "__main__":
    asyncio.run(main())

