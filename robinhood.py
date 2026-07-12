"""
robinhood.py
Trading HQ - Robinhood Daily list file helper.

This local project does not log into Robinhood and does not store
Robinhood usernames, passwords, or authentication tokens.

For now, copy the symbols from your Robinhood Daily list into:

    daily_list.txt

Put one ticker per line.
"""

from __future__ import annotations

from pathlib import Path

from watchlists import normalize_symbols


def load_symbols_from_text(
    path: str | Path = "daily_list.txt",
) -> list[str]:
    """
    Load ticker symbols from a text file.

    Supported format:

        AAPL
        NVDA
        MU

    Comma-separated symbols also work:

        AAPL, NVDA, MU
    """
    file_path = Path(path)

    if not file_path.exists():
        return []

    try:
        content = file_path.read_text(
            encoding="utf-8",
        )
    except OSError as exc:
        raise RuntimeError(
            f"Could not read watchlist file: {exc}"
        ) from exc

    raw_symbols = (
        content
        .replace(",", "\n")
        .replace(";", "\n")
        .splitlines()
    )

    return normalize_symbols(raw_symbols)


def save_symbols_to_text(
    symbols: list[str],
    path: str | Path = "daily_list.txt",
) -> Path:
    """
    Save ticker symbols into a text file,
    with one symbol per line.
    """
    file_path = Path(path)
    cleaned_symbols = normalize_symbols(symbols)

    try:
        file_path.write_text(
            "\n".join(cleaned_symbols) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise RuntimeError(
            f"Could not save watchlist file: {exc}"
        ) from exc

    return file_path