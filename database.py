"""
database.py — SQLite storage for scraped prices.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

# Database file sits next to this module
DB_PATH = Path(__file__).parent / "prices.db"


def _connect():
    """Open a connection to the prices database."""
    return sqlite3.connect(DB_PATH)


def init_db():
    """
    Create the prices table if it does not already exist.
    Columns: time (TEXT), product_name (TEXT), price (INTEGER).
    """
    try:
        with _connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS prices (
                    time           TEXT    NOT NULL,
                    product_name   TEXT    NOT NULL,
                    price          INTEGER NOT NULL
                )
                """
            )
            conn.commit()
        print("[database] Database initialized successfully.")
    except Exception as exc:
        print(f"[database] Failed to initialize database: {exc}")


def save_price(price: int, product_name: str):
    """
    Insert a new price row with the current timestamp and product name.
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with _connect() as conn:
            conn.execute(
                "INSERT INTO prices (time, product_name, price) VALUES (?, ?, ?)",
                (timestamp, product_name, price),
            )
            conn.commit()
        print(f"[database] Saved {product_name}: Rs.{price} at {timestamp}")
    except Exception as exc:
        print(f"[database] Failed to save price: {exc}")


def get_last_price(product_name: str):
    """
    Return the most recent price for a specific product (ORDER BY rowid DESC LIMIT 1),
    or None if no data exists for that product.
    """
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT price FROM prices WHERE product_name = ? ORDER BY rowid DESC LIMIT 1",
                (product_name,)
            ).fetchone()
        return row[0] if row else None
    except Exception as exc:
        print(f"[database] Failed to get last price for {product_name}: {exc}")
        return None


def get_all_prices(product_name: str = None):
    """
    Return all price rows as a list of (time, product_name, price) tuples,
    ordered from oldest to newest.
    If product_name is provided, filter by that product only.
    """
    try:
        with _connect() as conn:
            if product_name:
                rows = conn.execute(
                    "SELECT time, product_name, price FROM prices WHERE product_name = ? ORDER BY rowid ASC",
                    (product_name,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT time, product_name, price FROM prices ORDER BY rowid ASC"
                ).fetchall()
        return rows
    except Exception as exc:
        print(f"[database] Failed to get all prices: {exc}")
        return []


def get_price_stats(product_name: str = None):
    """
    Return a dict with highest, lowest, and current (latest) price.
    If product_name is provided, get stats for that product only.
    Returns zeros / None-safe defaults if no data exists.
    """
    try:
        rows = get_all_prices(product_name)
        if not rows:
            return {"highest": None, "lowest": None, "current": None}

        prices = [r[2] for r in rows]
        return {
            "highest": max(prices),
            "lowest": min(prices),
            "current": prices[-1],
        }
    except Exception as exc:
        print(f"[database] Failed to get price stats: {exc}")
        return {"highest": None, "lowest": None, "current": None}


if __name__ == "__main__":
    # Standalone test
    init_db()
    save_price(59999, "iPhone 15")
    print("Last price (iPhone 15):", get_last_price("iPhone 15"))
    print("All prices:", get_all_prices())
    print("Stats (iPhone 15):", get_price_stats("iPhone 15"))
