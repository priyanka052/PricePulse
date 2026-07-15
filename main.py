"""
main.py — Core PricePulse agent.
Wires scraper → database → notifier into a single monitoring run.
"""

from datetime import datetime

from database import get_last_price, init_db, save_price
from notifier import send_alert
from scraper import get_price


def run_agent():
    """
    Execute one full monitoring cycle:
    1. Ensure DB exists
    2. Scrape current price
    3. Compare with previous price and alert on drop
    4. Save the new price
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'=' * 50}")
    print(f"[main] PricePulse agent run — {timestamp}")
    print(f"{'=' * 50}")

    try:
        # Step 1: initialize database
        init_db()

        # Step 2: remember previous price BEFORE saving the new one
        previous = get_last_price()
        print(f"[main] Previous price: {f'Rs.{previous}' if previous is not None else 'none (first run)'}")

        # Step 3: scrape current price
        latest = get_price()
        if latest is None:
            print("[main] Could not retrieve price. Skipping this cycle.")
            return

        print(f"[main] Latest scraped price: Rs.{latest}")

        # Step 4: detect drop and notify
        if previous is not None and latest < previous:
            print(f"[main] Price drop detected! Rs.{previous} → Rs.{latest}")
            send_alert(previous, latest)
        elif previous is not None and latest > previous:
            print(f"[main] Price increased: Rs.{previous} → Rs.{latest}")
        elif previous is not None:
            print("[main] Price unchanged.")
        else:
            print("[main] First price recorded — no comparison yet.")

        # Step 5: persist
        save_price(latest)
        print(f"[main] Agent cycle complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as exc:
        print(f"[main] Agent run failed: {exc}")


if __name__ == "__main__":
    run_agent()
