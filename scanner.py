"""Main command-line scanner for Trading HQ."""
from __future__ import annotations
from alerts import run_alerts
from settings import validate_settings

import argparse
import math
import sys
from typing import Any

import pandas as pd

import config
from dashboard import create_dashboard
from indicators import (
    add_indicators,
    calculate_relative_volume,
    latest_session_change,
    obv_is_rising,
)
from polygon_client import MarketDataError, PolygonClient
from ranking import (
    calculate_score,
    failure_reasons,
    grade_from_score,
    hard_filter_pass,
)
from report import build_report, print_report, save_csv
from robinhood import load_symbols_from_text
from watchlists import get_watchlist, normalize_symbols


def analyze_ticker(
    ticker: str,
    client: PolygonClient,
) -> dict[str, Any]:
    """Fetch data, calculate indicators, score the setup, and return one row."""
    bars = client.fetch_bars(ticker)
    bars = add_indicators(bars)

    if bars.empty:
        raise ValueError("No usable bars after indicator calculation.")

    latest = bars.iloc[-1]

    price = float(latest["close"])
    vwap = float(latest["session_vwap"])
    ema_9 = float(latest[f"ema_{config.EMA_FAST}"])
    ema_20 = float(latest[f"ema_{config.EMA_MIDDLE}"])
    ema_50 = float(latest[f"ema_{config.EMA_SLOW}"])

    rvol = calculate_relative_volume(bars)
    session_change = latest_session_change(bars)

    atr_value = latest.get("atr_14", 0.0)
    atr = float(atr_value) if pd.notna(atr_value) else 0.0
    atr_percent = atr / price if price else 0.0

    metrics: dict[str, Any] = {
        "ticker": ticker,
        "price": price,
        "vwap": vwap,
        "rvol": rvol,
        "ema_9": ema_9,
        "ema_20": ema_20,
        "ema_50": ema_50,
        "above_vwap": price > vwap,
        "ema_aligned": ema_9 > ema_20 > ema_50,
        "obv_rising": obv_is_rising(bars),
        "session_change": session_change,
        "atr_percent": atr_percent,
    }

    score = calculate_score(metrics)
    passed = hard_filter_pass(metrics)
    reasons = failure_reasons(metrics)

    return {
        "ticker": ticker,
        "score": score,
        "grade": grade_from_score(score),
        "price": round(price, 2),
        "vwap": round(vwap, 2),
        "rvol": (
            round(float(rvol), 2)
            if isinstance(rvol, (int, float))
            and not math.isnan(float(rvol))
            else None
        ),
        "ema_9": round(ema_9, 2),
        "ema_20": round(ema_20, 2),
        "ema_50": round(ema_50, 2),
        "above_vwap": bool(metrics["above_vwap"]),
        "ema_aligned": bool(metrics["ema_aligned"]),
        "obv_rising": bool(metrics["obv_rising"]),
        "session_change_pct": round(session_change * 100, 2),
        "atr_pct": round(atr_percent * 100, 2),
        "passed": passed,
        "reason": "QUALIFIED" if passed else "; ".join(reasons),
        "last_bar_et": latest["timestamp"].strftime("%Y-%m-%d %H:%M ET"),
    }


def parse_args() -> argparse.Namespace:
    """Read command-line options."""
    parser = argparse.ArgumentParser(
        description="Trading HQ momentum scanner"
    )

    parser.add_argument(
        "--watchlist",
        default="daily",
        help="Named watchlist from watchlists.py, such as daily or test.",
    )

    parser.add_argument(
        "--symbols",
        nargs="*",
        help="Optional explicit tickers, for example: --symbols MU NVDA PLTR",
    )

    parser.add_argument(
        "--robinhood-file",
        default="daily_list.txt",
        help="Text file containing one ticker per line.",
    )

    return parser.parse_args()


def resolve_symbols(
    args: argparse.Namespace,
    client: PolygonClient,
) -> list[str]:
    """
    Use explicit command-line symbols first.

    Otherwise dynamically pull momentum candidates from Massive.
    Fall back to daily_list.txt only when dynamic scanning is disabled.
    """
    if args.symbols:
        return normalize_symbols(args.symbols)

    if config.DYNAMIC_MARKET_SCAN:
        print("Loading dynamic market universe from Massive...")

        symbols = client.fetch_market_candidates()

        print(
            f"Massive prefilter selected "
            f"{len(symbols)} candidates."
        )

        return symbols

    file_symbols = load_symbols_from_text(
        args.robinhood_file
    )

    if file_symbols:
        return file_symbols

    return get_watchlist(args.watchlist)


def main() -> int:
    """Run the Trading HQ scanner."""

    try:
        validate_settings()
    except ValueError as exc:
        print(
            f"SETTINGS ERROR: {exc}",
            file=sys.stderr,
        )
        return 1

    args = parse_args()

    try:
        client = PolygonClient()
    except MarketDataError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    try:
        symbols = resolve_symbols(args, client)
    except MarketDataError as exc:
        print(
            f"UNIVERSE ERROR: {exc}",
            file=sys.stderr,
        )
        return 1

    if not symbols:
        print(
            "ERROR: Dynamic scan found no candidates.",
            file=sys.stderr,
        )
        return 1

    print("Trading HQ dynamic market scanner")
    print(f"Endpoint: {client.base_url}")
    print(f"Candidates: {len(symbols)}\n")

    rows: list[dict[str, Any]] = []

    for ticker in symbols:
        try:
            rows.append(
                analyze_ticker(ticker, client)
            )
            print(f"{ticker}: completed")
        except (
            MarketDataError,
            ValueError,
            KeyError,
            TypeError,
        ) as exc:
            print(
                f"{ticker}: ERROR - {exc}",
                file=sys.stderr,
            )

    report = build_report(rows)

    # Keep only the best 20 after full indicator analysis.
    report = report.head(
        config.TOP_RESULTS_LIMIT
    ).copy()

    # Rebuild rank after truncation.
    if not report.empty:
        report["rank"] = range(
            1,
            len(report) + 1,
        )

    print_report(report)

    if report.empty:
        return 2

    csv_path = save_csv(report)
    html_path = create_dashboard(report)

    print(f"\nSaved CSV: {csv_path}")
    print(f"Saved dashboard: {html_path}")

    return 0

    """Run the Trading HQ scanner."""
    try:
        validate_settings()
    except ValueError as exc:
        print(f"SETTINGS ERROR: {exc}", file=sys.stderr)
        return 1
    
    args = parse_args()
    symbols = resolve_symbols(args)

    if not symbols:
        print("ERROR: No symbols found.", file=sys.stderr)
        return 1

    try:
        client = PolygonClient()
    except MarketDataError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("Trading HQ scanner")
    print(f"Endpoint: {client.base_url}")
    print(f"Tickers: {', '.join(symbols)}\n")

    rows: list[dict[str, Any]] = []

    for ticker in symbols:
        try:
            row = analyze_ticker(ticker, client)
            rows.append(row)
            print(f"{ticker}: completed")
        except (MarketDataError, ValueError, KeyError, TypeError) as exc:
            print(f"{ticker}: ERROR - {exc}", file=sys.stderr)

    report = build_report(rows)
    print_report(report)

    if report.empty:
        print("\nNo valid results were produced.", file=sys.stderr)
        return 2

    csv_path = save_csv(report)
    html_path = create_dashboard(report)
    
    run_alerts()
    
    print(f"\nSaved CSV: {csv_path}")
    print(f"Saved dashboard: {html_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())