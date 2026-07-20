"""
scraper.py — Fetches product price from a Flipkart URL.
Uses requests + BeautifulSoup with retry logic.
"""

import re
import time

import requests
from bs4 import BeautifulSoup

# ============================================================
# NOTE: Product URLs are now configured in config.json
# The get_price() function accepts a URL parameter
# ============================================================

# Full Chrome User-Agent to reduce chance of being blocked
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


def get_price(url: str):
    """
    Scrape the product price from the given Flipkart URL.
    Retries up to 3 times with a 5-second delay if the request fails.
    Returns an integer price, or None if the price cannot be found.
    """
    if not url:
        print("[scraper] No URL provided.")
        return None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"[scraper] Attempt {attempt}/{MAX_RETRIES} — fetching price...")
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            page_text = soup.get_text(separator=" ")

            # Find first ₹ price pattern like ₹59,999 or ₹1299
            match = re.search(r"₹[\d,]+", page_text)
            if match:
                raw = match.group(0)
                # Strip ₹ and commas → integer
                price = int(raw.replace("₹", "").replace(",", ""))
                print(f"[scraper] Price found: Rs.{price}")
                return price

            print("[scraper] Price pattern not found on page.")
            return None

        except requests.exceptions.RequestException as exc:
            print(f"[scraper] Request failed (attempt {attempt}): {exc}")
            if attempt < MAX_RETRIES:
                print(f"[scraper] Retrying in {RETRY_DELAY_SECONDS}s...")
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                print("[scraper] All retries exhausted. Returning None.")
                return None
        except Exception as exc:
            print(f"[scraper] Unexpected error: {exc}")
            return None

    return None


if __name__ == "__main__":
    # Standalone test — requires a URL
    test_url = "https://www.flipkart.com/apple-iphone-15-blue-128-gb/p/itmbf14ef54f645d"
    result = get_price(test_url)
    if result is not None:
        print(f"Scraped price: Rs.{result}")
    else:
        print("Could not scrape price.")
