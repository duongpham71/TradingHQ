"""
ranking.py
Trading HQ - Momentum Scoring Engine
"""

from __future__ import annotations

import math
import config


def grade_from_score(score: float) -> str:
    """
    Convert numeric score into a letter grade.
    """

    if score >= 95:
        return "A+"

    if score >= 90:
        return "A"

    if score >= 85:
        return "A-"

    if score >= 80:
        return "B+"

    if score >= 75:
        return "B"

    if score >= 70:
        return "B-"

    if score >= 60:
        return "C"

    return "D"


def calculate_score(metrics: dict) -> float:
    """
    Trading HQ Momentum Score
    Maximum = 100
    """

    score = 0.0

    weights = config.WEIGHTS

    ####################################################
    # Price above VWAP
    ####################################################

    if metrics["above_vwap"]:
        score += weights["above_vwap"]

    ####################################################
    # OBV Accumulation
    ####################################################

    if metrics["obv_rising"]:
        score += weights["obv_rising"]

    ####################################################
    # EMA Alignment
    ####################################################

    if metrics["ema_aligned"]:
        score += weights["ema_alignment"]

    ####################################################
    # Relative Volume
    ####################################################

    rvol = metrics["rvol"]

    if (
        isinstance(rvol, (float, int))
        and not math.isnan(float(rvol))
    ):

        score += (
            weights["relative_volume"]
            * min(
                float(rvol) / config.MIN_RELATIVE_VOLUME,
                1.0,
            )
        )

    ####################################################
    # Intraday Momentum
    ####################################################

    session_change = float(
        metrics.get("session_change", 0)
    )

    if session_change > 0:

        score += (
            weights["price_momentum"]
            * min(session_change / 0.05, 1.0)
        )

    ####################################################
    # ATR Volatility
    ####################################################

    atr_percent = float(
        metrics.get("atr_percent", 0)
    )

    if atr_percent > 0:

        score += (
            weights["volatility"]
            * min(atr_percent / 0.04, 1.0)
        )

    return round(min(score, 100), 1)


def hard_filter_pass(metrics: dict) -> bool:
    """
    Strict Trading HQ filters.
    """

    rvol = metrics["rvol"]

    volume_pass = (
        isinstance(rvol, (float, int))
        and not math.isnan(float(rvol))
        and float(rvol)
        >= config.MIN_RELATIVE_VOLUME
    )

    return (

        metrics["price"] > config.MIN_PRICE

        and metrics["above_vwap"]

        and metrics["ema_aligned"]

        and metrics["obv_rising"]

        and volume_pass

    )


def failure_reasons(metrics: dict) -> list[str]:
    """
    Explain why a stock failed.
    """

    reasons = []

    if metrics["price"] <= config.MIN_PRICE:
        reasons.append("Price below $10")

    if not metrics["above_vwap"]:
        reasons.append("Below VWAP")

    if not metrics["ema_aligned"]:
        reasons.append("EMA alignment failed")

    if not metrics["obv_rising"]:
        reasons.append("OBV not rising")

    rvol = metrics["rvol"]

    if (
        not isinstance(rvol, (float, int))
        or math.isnan(float(rvol))
        or float(rvol)
        < config.MIN_RELATIVE_VOLUME
    ):
        reasons.append("Relative Volume below threshold")

    return reasons