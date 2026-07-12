"""
indicators.py
Technical indicator calculations for Trading HQ.
"""

from __future__ import annotations

import math

import pandas as pd

import config


def add_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    """
    Add EMA, OBV, session VWAP, ATR, and short-term return columns.
    """
    data = frame.copy()

    # Exponential moving averages
    for span in (
        config.EMA_FAST,
        config.EMA_MIDDLE,
        config.EMA_SLOW,
    ):
        data[f"ema_{span}"] = data["close"].ewm(
            span=span,
            adjust=False,
        ).mean()

    # On-Balance Volume
    price_change = data["close"].diff()

    direction = price_change.map(
        lambda value: 1 if value > 0 else (-1 if value < 0 else 0)
    )

    data["obv"] = (
        direction * data["volume"]
    ).fillna(0).cumsum()

    # Session VWAP
    typical_price = (
        data["high"]
        + data["low"]
        + data["close"]
    ) / 3.0

    data["price_x_volume"] = (
        typical_price * data["volume"]
    )

    grouped = data.groupby(
        "session_date",
        sort=False,
    )

    data["session_cum_volume"] = (
        grouped["volume"].cumsum()
    )

    data["session_cum_pv"] = (
        grouped["price_x_volume"].cumsum()
    )

    data["session_vwap"] = (
        data["session_cum_pv"]
        / data["session_cum_volume"]
    )

    # ATR-style volatility calculation
    previous_close = data["close"].shift(1)

    true_range = pd.concat(
        [
            data["high"] - data["low"],
            (data["high"] - previous_close).abs(),
            (data["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    data["atr_14"] = true_range.rolling(
        14,
        min_periods=5,
    ).mean()

    # Five-bar price momentum
    data["return_5"] = data["close"].pct_change(5)

    return data


def calculate_relative_volume(
    data: pd.DataFrame,
) -> float:
    """
    Compare the latest session's cumulative volume with the
    average cumulative volume of prior sessions at the same bar count.
    """
    sessions = sorted(
        data["session_date"].unique()
    )

    if len(sessions) < 2:
        return math.nan

    latest_session = sessions[-1]

    today = data[
        data["session_date"] == latest_session
    ]

    completed_bars = len(today)

    prior_totals: list[float] = []

    for session_date in sessions[:-1]:
        prior = data[
            data["session_date"] == session_date
        ].head(completed_bars)

        if len(prior) == completed_bars:
            prior_totals.append(
                float(prior["volume"].sum())
            )

    if not prior_totals:
        return math.nan

    average_prior_volume = (
        sum(prior_totals)
        / len(prior_totals)
    )

    if average_prior_volume <= 0:
        return math.nan

    current_volume = float(
        today["volume"].sum()
    )

    return current_volume / average_prior_volume


def obv_is_rising(
    data: pd.DataFrame,
    bars: int | None = None,
) -> bool:
    """
    Return True when recent OBV is stronger in the second half
    of the lookback window than in the first half.
    """
    bars = bars or config.OBV_LOOKBACK_BARS

    recent = data.tail(bars)

    if len(recent) < 4:
        return False

    midpoint = len(recent) // 2

    first_half = recent["obv"].iloc[
        :midpoint
    ].mean()

    second_half = recent["obv"].iloc[
        midpoint:
    ].mean()

    return bool(
        second_half > first_half
    )


def latest_session_change(
    data: pd.DataFrame,
) -> float:
    """
    Return the latest session percentage change from first bar
    open to last bar close.
    """
    latest_date = data[
        "session_date"
    ].iloc[-1]

    session = data[
        data["session_date"] == latest_date
    ]

    if len(session) < 2:
        return 0.0

    first_open = float(
        session["open"].iloc[0]
    )

    last_close = float(
        session["close"].iloc[-1]
    )

    if first_open == 0:
        return 0.0

    return (
        last_close / first_open
    ) - 1.0