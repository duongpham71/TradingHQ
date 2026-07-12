"""
polygon_client.py
Trading HQ - Polygon/Massive API Client
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import requests

import config


EASTERN = ZoneInfo("America/New_York")


class MarketDataError(RuntimeError):
    """Raised when market data cannot be retrieved."""


class PolygonClient:
    """Simple Polygon/Massive REST client."""

    def __init__(self):
        self.api_key = config.API_KEY
        self.base_url = config.BASE_URL
        self.timeout = config.REQUEST_TIMEOUT

        if not self.api_key:
            raise MarketDataError(
                "POLYGON_API_KEY was not found."
            )

    def fetch_bars(self, ticker: str) -> pd.DataFrame:
        """
        Download recent aggregate bars.
        """

        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=config.LOOKBACK_DAYS)

        url = (
            f"{self.base_url}/v2/aggs/ticker/"
            f"{ticker}/range/"
            f"{config.BAR_MINUTES}/minute/"
            f"{start_date}/{end_date}"
        )

        params = {
            "adjusted": "true",
            "sort": "asc",
            "limit": 50000,
            "apiKey": self.api_key,
        }

        response = requests.get(
            url,
            params=params,
            timeout=self.timeout,
        )

        if response.status_code == 401:
            raise MarketDataError("Invalid API key.")

        if response.status_code == 403:
            raise MarketDataError(
                "Your Polygon plan does not include this data."
            )

        if response.status_code == 429:
            raise MarketDataError(
                "Polygon rate limit exceeded."
            )

        response.raise_for_status()

        payload = response.json()

        if "results" not in payload:
            raise MarketDataError(
                "No market data returned."
            )

        df = pd.DataFrame(payload["results"])

        df.rename(
            columns={
                "t": "timestamp",
                "o": "open",
                "h": "high",
                "l": "low",
                "c": "close",
                "v": "volume",
                "vw": "provider_vwap",
            },
            inplace=True,
        )

        df["timestamp"] = (
            pd.to_datetime(
                df["timestamp"],
                unit="ms",
                utc=True,
            )
            .dt.tz_convert(EASTERN)
        )

        df = df[
            [
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ]
        ]

        df["session_date"] = df["timestamp"].dt.date

        return df.reset_index(drop=True)
    
    def fetch_market_candidates(
    self,
    limit: int | None = None,
) -> list[str]:
    """
    Pull the full U.S. stock snapshot and return the strongest
    liquid momentum candidates for detailed intraday analysis.
    """
    limit = limit or config.MARKET_PREFILTER_LIMIT

    url = (
        f"{self.base_url}"
        "/v2/snapshot/locale/us/markets/stocks/tickers"
    )

    params = {
        "include_otc": "false",
        "apiKey": self.api_key,
    }

    try:
        response = self.session.get(
            url,
            params=params,
            timeout=max(self.timeout, 60),
        )
    except requests.RequestException as exc:
        raise MarketDataError(
            f"Market snapshot network error: {exc}"
        ) from exc

    if response.status_code == 401:
        raise MarketDataError("API key rejected.")

    if response.status_code == 403:
        raise MarketDataError(
            "Your Massive plan does not permit the full market snapshot."
        )

    if response.status_code == 429:
        raise MarketDataError("Massive API rate limit reached.")

    try:
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise MarketDataError(
            f"Invalid market snapshot response: {exc}"
        ) from exc

    snapshots = payload.get("tickers", [])

    if not snapshots:
        raise MarketDataError(
            "Full market snapshot returned no tickers."
        )

    candidates: list[dict[str, float | str]] = []

    for item in snapshots:
        ticker = str(item.get("ticker", "")).strip().upper()

        day = item.get("day") or {}
        previous_day = item.get("prevDay") or {}

        price = float(
            day.get("c")
            or item.get("lastTrade", {}).get("p")
            or 0
        )

        open_price = float(day.get("o") or 0)
        high = float(day.get("h") or 0)
        low = float(day.get("l") or 0)
        volume = float(day.get("v") or 0)
        vwap = float(day.get("vw") or 0)

        previous_close = float(
            previous_day.get("c") or 0
        )

        if not ticker or not ticker.isalpha():
            continue

        if len(ticker) > config.MAX_TICKER_LENGTH:
            continue

        if price <= config.MIN_PRICE:
            continue

        if volume < config.MIN_DAILY_VOLUME:
            continue

        if open_price <= 0 or high <= 0 or low <= 0:
            continue

        if vwap > 0 and price <= vwap:
            continue

        session_gain = (
            ((price / previous_close) - 1.0) * 100.0
            if previous_close > 0
            else ((price / open_price) - 1.0) * 100.0
        )

        intraday_range = (
            ((high - low) / low) * 100.0
            if low > 0
            else 0.0
        )

        if session_gain < config.MIN_SESSION_GAIN_PERCENT:
            continue

        if intraday_range < config.MIN_INTRADAY_RANGE_PERCENT:
            continue

        # Broad prefilter score. Detailed scoring happens later.
        liquidity_score = min(volume / 5_000_000, 3.0)
        momentum_score = max(session_gain, 0.0)
        range_score = min(intraday_range, 20.0) * 0.25

        prefilter_score = (
            momentum_score
            + liquidity_score
            + range_score
        )

        candidates.append(
            {
                "ticker": ticker,
                "prefilter_score": prefilter_score,
                "session_gain": session_gain,
                "volume": volume,
            }
        )

    candidates.sort(
        key=lambda row: (
            float(row["prefilter_score"]),
            float(row["volume"]),
        ),
        reverse=True,
    )

    return [
        str(row["ticker"])
        for row in candidates[:limit]
    ]