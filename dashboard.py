"""
dashboard.py
Trading HQ - HTML dashboard generator.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

import config


def create_dashboard(
    frame: pd.DataFrame,
    path: Path | None = None,
) -> Path:
    """
    Create a self-contained HTML scanner dashboard.
    """
    destination = (
        path
        if path is not None
        else config.HTML_OUTPUT
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    generated_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    if frame.empty:
        qualified_count = 0
        total_count = 0
        table_html = (
            "<p>No scanner results available.</p>"
        )

    else:
        total_count = len(frame)

        qualified_count = int(
            frame["passed"].sum()
        )

        display = frame.copy()

        boolean_columns = [
            "passed",
            "above_vwap",
            "ema_aligned",
            "obv_rising",
        ]

        for column in boolean_columns:
            if column in display.columns:
                display[column] = display[column].map(
                    {
                        True: "Yes",
                        False: "No",
                    }
                )

        table_html = display.to_html(
            index=False,
            border=0,
            classes="results",
            justify="center",
            escape=True,
        )

    html = f"""
<!doctype html>

<html lang="en">

<head>

<meta charset="utf-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>

<title>Trading HQ Dashboard</title>

<style>

body {{
    font-family:
        Arial,
        Helvetica,
        sans-serif;

    margin: 24px;

    background: #f4f6f8;

    color: #1f2937;
}}

h1 {{
    margin-bottom: 4px;
}}

.subtitle {{
    color: #6b7280;

    margin-top: 0;

    margin-bottom: 20px;
}}

.summary-grid {{
    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(180px, 1fr)
        );

    gap: 14px;

    margin-bottom: 20px;
}}

.summary-card {{
    background: white;

    padding: 16px;

    border-radius: 10px;

    box-shadow:
        0 2px 8px
        rgba(0, 0, 0, 0.08);
}}

.summary-label {{
    color: #6b7280;

    font-size: 13px;

    margin-bottom: 8px;
}}

.summary-value {{
    font-size: 26px;

    font-weight: bold;
}}

.table-card {{
    background: white;

    border-radius: 10px;

    padding: 18px;

    overflow-x: auto;

    box-shadow:
        0 2px 8px
        rgba(0, 0, 0, 0.08);
}}

.results {{
    width: 100%;

    border-collapse: collapse;

    font-size: 14px;
}}

.results th,
.results td {{
    border-bottom:
        1px solid #e5e7eb;

    padding: 9px;

    text-align: center;

    white-space: nowrap;
}}

.results th {{
    position: sticky;

    top: 0;

    background: #eef2f7;

    font-weight: bold;
}}

.results tr:hover {{
    background: #f9fafb;
}}

.footer {{
    margin-top: 16px;

    color: #6b7280;

    font-size: 12px;
}}

</style>

</head>

<body>

<h1>Trading HQ</h1>

<p class="subtitle">
Momentum scanner dashboard
</p>

<div class="summary-grid">

    <div class="summary-card">

        <div class="summary-label">
            Stocks scanned
        </div>

        <div class="summary-value">
            {total_count}
        </div>

    </div>

    <div class="summary-card">

        <div class="summary-label">
            Qualified setups
        </div>

        <div class="summary-value">
            {qualified_count}
        </div>

    </div>

    <div class="summary-card">

        <div class="summary-label">
            Generated
        </div>

        <div class="summary-value"
             style="font-size: 16px;">
            {generated_time}
        </div>

    </div>

</div>

<div class="table-card">

    {table_html}

</div>

<div class="footer">

    Trading HQ results are informational.
    Confirm live price, VWAP, volume, and risk
    before placing a trade.

</div>

</body>

</html>
"""

    destination.write_text(
        html,
        encoding="utf-8",
    )

    return destination