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
    Columns: time (TEXT), price (INTEGER).
    """
    try:
        with _connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS prices (
                    time  TEXT    NOT NULL,
                    price INTEGER NOT NULL
                )
                """
            )
            conn.commit()
        print("[database] Database initialized successfully.")
    except Exception as exc:
        print(f"[database] Failed to initialize database: {exc}")


def save_price(price: int):
    """
    Insert a new price row with the current timestamp.
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with _connect() as conn:
            conn.execute(
                "INSERT INTO prices (time, price) VALUES (?, ?)",
                (timestamp, price),
            )
            conn.commit()
        print(f"[database] Saved price Rs.{price} at {timestamp}")
    except Exception as exc:
        print(f"[database] Failed to save price: {exc}")


def get_last_price():
    """
    Return the most recent price (ORDER BY rowid DESC LIMIT 1),
    or None if the table is empty.
    """
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT price FROM prices ORDER BY rowid DESC LIMIT 1"
            ).fetchone()
        return row[0] if row else None
    except Exception as exc:
        print(f"[database] Failed to get last price: {exc}")
        return None


def get_all_prices():
    """
    Return all price rows as a list of (time, price) tuples,
    ordered from oldest to newest.
    """
    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT time, price FROM prices ORDER BY rowid ASC"
            ).fetchall()
        return rows
    except Exception as exc:
        print(f"[database] Failed to get all prices: {exc}")
        return []


def get_price_stats():
    """
    Return a dict with highest, lowest, and current (latest) price.
    Returns zeros / None-safe defaults if no data exists.
    """
    try:
        rows = get_all_prices()
        if not rows:
            return {"highest": None, "lowest": None, "current": None}

        prices = [r[1] for r in rows]
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
    save_price(59999)
    print("Last price:", get_last_price())
    print("All prices:", get_all_prices())
    print("Stats:", get_price_stats())
