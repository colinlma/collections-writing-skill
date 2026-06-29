"""
Crawl a single ecommerce page and extract its visible text content.
Uses Playwright with a real-browser user agent to handle JavaScript-rendered pages.

Usage:
    python3 scripts/crawl_page.py <url> <output_file>

For batch crawling, run multiple instances in parallel:
    python3 scripts/crawl_page.py "https://store.com/collections/page1" /tmp/crawl_1.txt &
    python3 scripts/crawl_page.py "https://store.com/collections/page2" /tmp/crawl_2.txt &
    wait
"""

import asyncio
import sys
import json

from playwright.async_api import async_playwright


async def crawl(url: str, output_file: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-http2"])
        page = await browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(5000)
            text = await page.evaluate("() => document.body.innerText")
        except Exception as e:
            text = f"ERROR: {str(e)}"

        await browser.close()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"Crawled {url} -> {len(text)} chars")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 crawl_page.py <url> <output_file>")
        sys.exit(1)

    url = sys.argv[1]
    output = sys.argv[2]
    asyncio.run(crawl(url, output))
