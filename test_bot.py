"""
test_bot.py — Simple tests to verify bot components work correctly.

Run with: python test_bot.py
These test the database and parsing logic WITHOUT needing Telegram.
"""

import os
import re
import sys

# Use a test database file (not your real one)
os.environ["BOT_TOKEN"] = "fake-token"
os.environ["CHAT_ID"] = "123456"

from database import init_db, log_water, get_today_total, get_today_logs, DB_FILE

# Override DB to use a test file
import database
database.DB_FILE = "test_water.db"

# Clean up any previous test DB
if os.path.exists("test_water.db"):
    os.remove("test_water.db")


def test_database():
    """Test database operations."""
    print("Testing database...")
    
    # Init should create the table without error
    init_db()
    print("  ✓ init_db() works")
    
    # Initially, total should be 0
    assert get_today_total() == 0, "Expected 0 for empty DB"
    print("  ✓ get_today_total() returns 0 for empty DB")
    
    # Log some water
    time_str, total = log_water(200)
    assert total == 200, f"Expected 200, got {total}"
    assert time_str is not None
    print(f"  ✓ log_water(200) → total={total}, time={time_str}")
    
    # Log more
    time_str, total = log_water(300)
    assert total == 500, f"Expected 500, got {total}"
    print(f"  ✓ log_water(300) → total={total}")
    
    # Check today's logs
    logs = get_today_logs()
    assert len(logs) == 2, f"Expected 2 entries, got {len(logs)}"
    assert logs[0][1] == 200  # first entry amount
    assert logs[1][1] == 300  # second entry amount
    print(f"  ✓ get_today_logs() returns {len(logs)} entries")
    
    print("  ALL DATABASE TESTS PASSED ✓\n")


def test_parsing():
    """Test the regex patterns used for parsing water intake."""
    print("Testing message parsing...")
    
    # The same regex patterns from bot.py
    def parse_amount(text: str) -> int | None:
        text = text.strip().lower()
        match = re.search(r'(\d+)\s*ml\b', text)
        if not match:
            match = re.search(r'\b(\d+)\b', text)
        if match:
            return int(match.group(1))
        return None
    
    # Test cases: (input, expected_amount)
    test_cases = [
        ("drank 200 ml", 200),
        ("200ml", 200),
        ("200 ml", 200),
        ("just had 300 ml", 300),
        ("drank 500ml just now", 500),
        ("250", 250),
        ("I had 150 ml of water", 150),
        ("hello", None),         # No number
        ("good morning", None),  # No number
    ]
    
    for text, expected in test_cases:
        result = parse_amount(text)
        assert result == expected, f"FAILED: parse('{text}') → {result}, expected {expected}"
        status = "✓" if result == expected else "✗"
        print(f"  {status} \"{text}\" → {result}")
    
    print("  ALL PARSING TESTS PASSED ✓\n")


def test_summary_keywords():
    """Test that summary keywords are correctly identified."""
    print("Testing summary keyword detection...")
    
    summary_keywords = ["how much", "total", "summary", "status", "progress", "lagging", "behind"]
    
    # Should trigger summary
    should_match = [
        "how much today",
        "what's my total",
        "show me my progress",
        "am I lagging behind",
        "status",
    ]
    
    # Should NOT trigger summary (should be parsed as intake)
    should_not_match = [
        "drank 200 ml",
        "250ml",
        "hello",
        "200",
    ]
    
    for text in should_match:
        matched = any(kw in text.lower() for kw in summary_keywords)
        assert matched, f"FAILED: '{text}' should trigger summary"
        print(f"  ✓ \"{text}\" → triggers summary")
    
    for text in should_not_match:
        matched = any(kw in text.lower() for kw in summary_keywords)
        assert not matched, f"FAILED: '{text}' should NOT trigger summary"
        print(f"  ✓ \"{text}\" → does NOT trigger summary")
    
    print("  ALL KEYWORD TESTS PASSED ✓\n")


if __name__ == "__main__":
    print("=" * 50)
    print("  WATER REMINDER BOT — TEST SUITE")
    print("=" * 50 + "\n")
    
    test_database()
    test_parsing()
    test_summary_keywords()
    
    # Clean up test DB
    if os.path.exists("test_water.db"):
        os.remove("test_water.db")
    
    print("=" * 50)
    print("  ALL TESTS PASSED ✓")
    print("=" * 50)
