"""
watchlists.py
Trading HQ - Watchlist definitions and symbol cleanup.
"""

from __future__ import annotations


# Fallback Daily list.
# The scanner will use daily_list.txt first when that file exists.
DAILY_LIST = [
    "AAPL",
    "NVDA",
    "MU",
    "AMD",
    "PLTR",
]


# Small testing list.
TEST_LIST = [
    "AAPL",
    "NVDA",
    "MU",
    "AMD",
    "PLTR",
]


def normalize_symbols(symbols: list[str]) -> list[str]:
    """
    Clean ticker symbols.

    - Removes spaces
    - Converts to uppercase
    - Removes duplicates
    - Preserves the original order
    """
    seen: set[str] = set()
    cleaned_symbols: list[str] = []

    for symbol in symbols:
        cleaned = symbol.strip().upper()

        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            cleaned_symbols.append(cleaned)

    return cleaned_symbols


def get_watchlist(name: str = "daily") -> list[str]:
    """
    Return a named watchlist.
    """
    normalized_name = name.strip().lower()

    if normalized_name in {
        "daily",
        "daily list",
        "robinhood",
    }:
        return normalize_symbols(DAILY_LIST)

    if normalized_name in {
        "test",
        "sample",
    }:
        return normalize_symbols(TEST_LIST)

    raise ValueError(
        f"Unknown watchlist: {name}"
    )