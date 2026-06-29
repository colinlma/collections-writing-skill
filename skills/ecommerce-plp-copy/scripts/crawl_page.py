"""
Crawl a single ecommerce page and extract its visible text content.
Uses Playwright with a real-browser user agent to handle JavaScript-rendered pages.

Usage:
    python3 scripts/crawl_page.py <url> <output_file> [--links <links_file>]

    --links <links_file>  also write every anchor href on the page (absolute,
                          deduped) as a JSON list. Use this on a PLP crawl to
                          discover the PDP URLs to crawl next.

For batch crawling, run multiple instances in parallel:
    python3 scripts/crawl_page.py "https://store.com/collections/page1" /tmp/crawl_1.txt &
    python3 scripts/crawl_page.py "https://store.com/collections/page2" /tmp/crawl_2.txt &
    wait
"""

import asyncio
import sys
import json
import argparse

from playwright.async_api import async_playwright


async def crawl(url: str, output_file: str, links_file: str | None = None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-http2"])
        page = await browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        links = []
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(5000)
            text = await page.evaluate("() => document.body.innerText")
            if links_file:
                # Absolute hrefs of every anchor on the page (deduped, order-preserved)
                links = await page.evaluate(
                    "() => Array.from(document.querySelectorAll('a[href]'))"
                    ".map(a => a.href)"
                )
        except Exception as e:
            text = f"ERROR: {str(e)}"

        await browser.close()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)

        if links_file:
            seen, unique = set(), []
            for h in links:
                if h and h not in seen:
                    seen.add(h)
                    unique.append(h)
            with open(links_file, "w", encoding="utf-8") as f:
                json.dump(unique, f, indent=2)
            print(f"Crawled {url} -> {len(text)} chars, {len(unique)} links")
        else:
            print(f"Crawled {url} -> {len(text)} chars")


def main():
    parser = argparse.ArgumentParser(description="Crawl a page's rendered text (and optionally its links).")
    parser.add_argument("url")
    parser.add_argument("output_file")
    parser.add_argument("--links", dest="links_file", default=None,
                        help="Also write all anchor hrefs (absolute, deduped) to this JSON file.")
    args = parser.parse_args()
    asyncio.run(crawl(args.url, args.output_file, args.links_file))


if __name__ == "__main__":
    main()
