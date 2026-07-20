"""
main.py — Core PricePulse agent.
Wires scraper → database → notifier into a single monitoring run.
Supports multiple products via config.json.
"""

import json
from datetime import datetime
from pathlib import Path

from database import get_last_price, init_db, save_price
from notifier import send_alert
from scraper import get_price

# Load product URLs from config
CONFIG_PATH = Path(__file__).parent / "config.json"

def load_products():
    """Load products from config.json."""
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        return config.get("products", [])
    except Exception as exc:
        print(f"[main] Failed to load config.json: {exc}")
        return []


def run_agent():
    """
    Execute one full monitoring cycle for all products:
    1. Ensure DB exists
    2. For each product:
       a. Scrape current price
       b. Compare with previous price and alert on drop
       c. Save the new price
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'=' * 50}")
    print(f"[main] PricePulse agent run — {timestamp}")
    print(f"{'=' * 50}")

    try:
        # Step 1: initialize database
        init_db()

        # Step 2: load all products from config
        products = load_products()
        if not products:
            print("[main] No products configured in config.json. Skipping.")
            return

        # Step 3: monitor each product
        for product in products:
            product_name = product.get("name")
            product_url = product.get("url")

            if not product_name or not product_url:
                print("[main] Skipping product with missing name or URL.")
                continue

            print(f"\n[main] Monitoring: {product_name}")

            # Remember previous price BEFORE saving the new one
            previous = get_last_price(product_name)
            print(f"[main] Previous price: {f'Rs.{previous}' if previous is not None else 'none (first run)'}")

            # Scrape current price
            latest = get_price(product_url)
            if latest is None:
                print(f"[main] Could not retrieve price for {product_name}. Skipping.")
                continue

            print(f"[main] Latest scraped price: Rs.{latest}")

            # Detect drop and notify
            if previous is not None and latest < previous:
                print(f"[main] Price drop detected! Rs.{previous} → Rs.{latest}")
                send_alert(product_name, previous, latest)
            elif previous is not None and latest > previous:
                print(f"[main] Price increased: Rs.{previous} → Rs.{latest}")
            elif previous is not None:
                print("[main] Price unchanged.")
            else:
                print("[main] First price recorded — no comparison yet.")

            # Persist the new price
            save_price(latest, product_name)

        print(f"\n[main] Agent cycle complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as exc:
        print(f"[main] Agent run failed: {exc}")


if __name__ == "__main__":
    run_agent()
