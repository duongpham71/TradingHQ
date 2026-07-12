"""
config.py
Trading HQ system configuration.
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
    DYNAMIC_MARKET_SCAN,
    TOP_RESULTS_LIMIT,
    MARKET_PREFILTER_LIMIT,
    MIN_DAILY_VOLUME,
    MIN_SESSION_GAIN_PERCENT,
    MIN_INTRADAY_RANGE_PERCENT,
    MAX_TICKER_LENGTH,
)


PROJECT_DIR = Path(__file__).resolve().parent


# Polygon / Massive API
API_KEY_ENV = "POLYGON_API_KEY"
API_KEY = os.getenv(API_KEY_ENV, "POAK3yvI4e2ZgUhZfwyfwoqTStfaumfm")

BASE_URL = os.getenv(
    "POLYGON_BASE_URL",
    "https://api.massive.com",
)


# Cloud/local output storage
OUTPUT_DIR = Path(
    os.getenv(
        "TRADINGHQ_DATA_DIR",
        str(PROJECT_DIR / "output"),
    )
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# Generated files
CSV_OUTPUT = OUTPUT_DIR / "scanner_results.csv"
HTML_OUTPUT = OUTPUT_DIR / "dashboard.html"
