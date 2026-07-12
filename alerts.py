"""
alerts.py
Trading HQ - Alert Engine
"""
from __future__ import annotations

try:
    from winotify import Notification
    WINDOWS_NOTIFICATIONS = True
except ImportError:
    WINDOWS_NOTIFICATIONS = False
    
from pathlib import Path
import pandas as pd


PREVIOUS_RESULTS = Path("output/previous_results.csv")
CURRENT_RESULTS = Path("output/scanner_results.csv")

def send_windows_notification(title: str, message: str) -> None:
    """Display a Windows desktop notification."""
    if not WINDOWS_NOTIFICATIONS:
        return

    toast = Notification(
        app_id="Trading HQ",
        title=title,
        msg=message,
        duration="short",
    )

    toast.show()
    
def load_results(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(path)


def save_current(frame: pd.DataFrame) -> None:
    PREVIOUS_RESULTS.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame.to_csv(
        PREVIOUS_RESULTS,
        index=False,
    )


def find_new_alerts(
    current: pd.DataFrame,
    previous: pd.DataFrame,
) -> list[str]:
    """
    Return alert messages for newly qualified stocks.
    """

    alerts = []

    if previous.empty:
        for _, row in current[current["passed"]].iterrows():
            alerts.append(
                f"✅ {row['ticker']} QUALIFIED "
                f"(Score {row['score']})"
            )
        return alerts

    previous_passed = {
        ticker
        for ticker in previous[
            previous["passed"] == True
        ]["ticker"]
    }

    for _, row in current.iterrows():

        if not row["passed"]:
            continue

        if row["ticker"] not in previous_passed:

            alerts.append(
                f"🚀 NEW SETUP: "
                f"{row['ticker']} "
                f"(Score {row['score']})"
            )

    return alerts


def run_alerts() -> None:

    current = load_results(CURRENT_RESULTS)

    if current.empty:
        print("No scanner results found.")
        return

    previous = load_results(PREVIOUS_RESULTS)

    alerts = find_new_alerts(
        current,
        previous,
    )

    if alerts:

        print("\n==============================")
        print(" TRADING HQ ALERTS")
        print("==============================")

        for alert in alerts:
            print(alert)
            send_windows_notification(
                "Trading HQ Alert",
                alert,
            )
    else:

        print("No new alerts.")

    save_current(current)


if __name__ == "__main__":
    run_alerts()