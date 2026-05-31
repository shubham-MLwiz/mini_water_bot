"""
database.py — SQLite helper functions for water intake logging.

This module handles all database operations:
- Creating the table (on first run)
- Logging a water intake entry
- Querying today's total and individual entries

SQLite is Python's built-in database — no server needed, just a file (water.db).
"""

import sqlite3
from datetime import datetime, date

# Database file — created automatically in the project folder
DB_FILE = "water.db"


def get_connection():
    """Get a connection to the SQLite database.

    sqlite3.connect() opens the file if it exists, or creates it if it doesn't.
    This is called every time we need to read/write — SQLite handles this fine
    for a single-user app.
    """
    return sqlite3.connect(DB_FILE)


def init_db():
    """Create the water_log table if it doesn't exist.

    Called once when the bot starts. If the table already exists, this does nothing
    (thanks to IF NOT EXISTS).

    Columns:
    - id: auto-incrementing unique ID for each entry
    - timestamp: when the water was logged (ISO format string)
    - amount_ml: how many millilitres were consumed
    """
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS water_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            amount_ml INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def log_water(amount_ml: int) -> tuple[str, int]:
    """Log a water intake entry with current timestamp.

    Args:
        amount_ml: Amount of water in millilitres.

    Returns:
        Tuple of (formatted time string, today's new total in ml).
    """
    now = datetime.now()
    timestamp = now.isoformat()  # e.g. "2026-06-01T14:30:45.123456"

    conn = get_connection()
    conn.execute(
        "INSERT INTO water_log (timestamp, amount_ml) VALUES (?, ?)",
        (timestamp, amount_ml)
    )
    conn.commit()
    conn.close()

    # Return the time (for confirmation message) and updated total
    time_str = now.strftime("%H:%M")  # e.g. "14:30"
    total = get_today_total()
    return time_str, total


def get_today_total() -> int:
    """Get total water consumed today (in ml).

    Filters entries where the timestamp starts with today's date (YYYY-MM-DD).
    """
    today_str = date.today().isoformat()  # e.g. "2026-06-01"

    conn = get_connection()
    cursor = conn.execute(
        "SELECT COALESCE(SUM(amount_ml), 0) FROM water_log WHERE timestamp LIKE ?",
        (f"{today_str}%",)
    )
    total = cursor.fetchone()[0]
    conn.close()
    return total


def get_today_logs() -> list[tuple[str, int]]:
    """Get all individual entries for today, ordered by time.

    Returns:
        List of (time_string, amount_ml) tuples.
        e.g. [("09:15", 200), ("10:30", 300), ("12:00", 250)]
    """
    today_str = date.today().isoformat()

    conn = get_connection()
    cursor = conn.execute(
        "SELECT timestamp, amount_ml FROM water_log WHERE timestamp LIKE ? ORDER BY timestamp",
        (f"{today_str}%",)
    )
    rows = cursor.fetchall()
    conn.close()

    # Convert ISO timestamps to readable "HH:MM" format
    result = []
    for timestamp, amount in rows:
        time_str = datetime.fromisoformat(timestamp).strftime("%H:%M")
        result.append((time_str, amount))
    return result