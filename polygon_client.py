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