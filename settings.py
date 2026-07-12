"""
settings.py
User-adjustable Trading HQ scanner settings.
"""

from __future__ import annotations

# Dynamic market scan
DYNAMIC_MARKET_SCAN = True

TOP_RESULTS_LIMIT = 20

# Number of snapshot candidates that receive full indicator analysis
MARKET_PREFILTER_LIMIT = 60

# Broad-market prefilters
MIN_DAILY_VOLUME = 500_000
MIN_SESSION_GAIN_PERCENT = 0.0
MIN_INTRADAY_RANGE_PERCENT = 2.0

# Exclude unusual ticker formats such as warrants and preferred shares
MAX_TICKER_LENGTH = 5


# ============================================================
# MARKET DATA
# ============================================================

BAR_MINUTES = 5

LOOKBACK_DAYS = 8

REQUEST_TIMEOUT = 30

REGULAR_SESSION_ONLY = True


# ============================================================
# HARD FILTERS
# ============================================================

MIN_PRICE = 10.0

MIN_RELATIVE_VOLUME = 2.0

OBV_LOOKBACK_BARS = 10


# ============================================================
# MOVING AVERAGES
# ============================================================

EMA_FAST = 9

EMA_MIDDLE = 20

EMA_SLOW = 50


# ============================================================
# MOMENTUM SCORE WEIGHTS
# Total should equal 100.
# ============================================================

WEIGHTS = {
    "above_vwap": 20,
    "obv_rising": 20,
    "ema_alignment": 15,
    "relative_volume": 25,
    "price_momentum": 10,
    "volatility": 10,
}


# ============================================================
# SCORE AND GRADE SETTINGS
# ============================================================

GRADE_THRESHOLDS = {
    "A+": 90,
    "A": 85,
    "A-": 80,
    "B+": 75,
    "B": 70,
    "C": 60,
    "D": 0,
}


# Minimum score required for a watch alert.
MIN_ALERT_SCORE = 85.0

# Alert when a stock improves by this many points.
SCORE_JUMP_ALERT = 10.0


# ============================================================
# TARGET AND RISK SETTINGS
# ============================================================

MIN_REWARD_RISK_RATIO = 2.0

STOP_ATR_MULTIPLIER = 1.0

TARGET_1_ATR_MULTIPLIER = 1.5

TARGET_2_ATR_MULTIPLIER = 2.5

TARGET_3_ATR_MULTIPLIER = 4.0


# ============================================================
# MOMENTUM POTENTIAL
# ============================================================

MIN_SESSION_CHANGE = 0.0

TEN_PERCENT_POTENTIAL_THRESHOLD = 0.10

MIN_ATR_PERCENT_FOR_HIGH_MOMENTUM = 0.03


# ============================================================
# SCANNER OUTPUT
# ============================================================

TOP_RESULTS_LIMIT = 20

SHOW_FAILED_STOCKS = True

SAVE_CSV = True

SAVE_HTML_DASHBOARD = True


# ============================================================
# ALERT SETTINGS
# ============================================================

ENABLE_ALERTS = True

ALERT_NEWLY_QUALIFIED_ONLY = True

ALERT_SCORE_IMPROVEMENTS = True

ALERT_GRADE_IMPROVEMENTS = True

ENABLE_WINDOWS_NOTIFICATIONS = False

ENABLE_SOUND_ALERT = False


# ============================================================
# AUTOMATION SETTINGS
# ============================================================

SCAN_INTERVAL_MINUTES = 5

MARKET_TIMEZONE = "America/New_York"

MARKET_OPEN_TIME = "09:30"

MARKET_CLOSE_TIME = "16:00"

RUN_PREMARKET = False

PREMARKET_START_TIME = "04:00"

RUN_AFTER_HOURS = False

AFTER_HOURS_END_TIME = "20:00"


# ============================================================
# VALIDATION
# ============================================================

def validate_settings() -> None:
    """Validate important settings when the program starts."""

    if MIN_PRICE < 0:
        raise ValueError("MIN_PRICE cannot be negative.")

    if MIN_RELATIVE_VOLUME <= 0:
        raise ValueError(
            "MIN_RELATIVE_VOLUME must be greater than zero."
        )

    if not (
        EMA_FAST < EMA_MIDDLE < EMA_SLOW
    ):
        raise ValueError(
            "EMA periods must satisfy "
            "EMA_FAST < EMA_MIDDLE < EMA_SLOW."
        )

    if sum(WEIGHTS.values()) != 100:
        raise ValueError(
            "Momentum score weights must add up to 100."
        )

    if TOP_RESULTS_LIMIT <= 0:
        raise ValueError(
            "TOP_RESULTS_LIMIT must be greater than zero."
        )

    if SCAN_INTERVAL_MINUTES <= 0:
        raise ValueError(
            "SCAN_INTERVAL_MINUTES must be greater than zero."
        )