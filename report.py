"""
report.py
Trading HQ - Console and CSV reporting.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

import config


DISPLAY_COLUMNS = [
    "rank",
    "ticker",
    "score",
    "grade",
    "price",
    "vwap",
    "rvol",
    "ema_9",
    "ema_20",
    "ema_50",
    "above_vwap",
    "ema_aligned",
    "obv_rising",
    "session_change_pct",
    "atr_pct",
    "passed",
    "reason",
    "last_bar_et",
]


def build_report(
    rows: list[dict[str, object]],
) -> pd.DataFrame:
    """
    Build and rank the final scanner report.
    """
    frame = pd.DataFrame(rows)

    if frame.empty:
        return frame

    frame = frame.sort_values(
        by=[
            "passed",
            "score",
            "rvol",
            "ticker",
        ],
        ascending=[
            False,
            False,
            False,
            True,
        ],
        na_position="last",
    ).reset_index(drop=True)

    frame.insert(
        0,
        "rank",
        range(1, len(frame) + 1),
    )

    return frame


def print_report(
    frame: pd.DataFrame,
) -> None:
    """
    Print scanner results in the terminal.
    """
    if frame.empty:
        print(
            "No stocks were successfully processed."
        )
        return

    available_columns = [
        column
        for column in DISPLAY_COLUMNS
        if column in frame.columns
    ]

    print("\nRESULTS")

    print(
        frame[
            available_columns
        ].to_string(
            index=False,
        )
    )

    qualified = frame[
        frame["passed"] == True
    ]

    print(
        f"\nQualified: "
        f"{len(qualified)} of {len(frame)}"
    )

    if qualified.empty:
        print(
            "No stocks passed every hard rule. "
            "This can be a valid result."
        )
    else:
        print("\nQUALIFIED SETUPS")

        for _, row in qualified.iterrows():
            print(
                f"{int(row['rank'])}. "
                f"{row['ticker']} "
                f"| Score: {row['score']} "
                f"| Grade: {row['grade']}"
            )


def save_csv(
    frame: pd.DataFrame,
    path: Path | None = None,
) -> Path:
    """
    Save scanner results to CSV.
    """
    destination = (
        path
        if path is not None
        else config.CSV_OUTPUT
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame.to_csv(
        destination,
        index=False,
    )

    return destination