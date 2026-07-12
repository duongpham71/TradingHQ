"""
config.py
Trading HQ - System paths and API configuration.
"""

from __future__ import annotations

import os
from pathlib import Path

from settings import (
    BAR_MINUTES,
    LOOKBACK_DAYS,
    REQUEST_TIMEOUT,
    REGULAR_SESSION_ONLY,
    MIN_PRICE,
    MIN_RELATIVE_VOLUME,
    OBV_LOOKBACK_BARS,
    EMA_FAST,
    EMA_MIDDLE,
    EMA_SLOW,
    WEIGHTS,
)


PROJECT_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = PROJECT_DIR / "output"
OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


API_KEY_ENV = "POLYGON_API_KEY"

API_KEY = os.getenv(
    API_KEY_ENV,
    "",
)

BASE_URL = os.getenv(
    "POLYGON_BASE_URL",
    "https://api.massive.com",
)


CSV_OUTPUT = OUTPUT_DIR / "scanner_results.csv"

HTML_OUTPUT = OUTPUT_DIR / "dashboard.html"