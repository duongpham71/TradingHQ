import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = Path(
    os.getenv(
        "TRADINGHQ_DATA_DIR",
        str(PROJECT_DIR / "output"),
    )
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

CSV_OUTPUT = OUTPUT_DIR / "scanner_results.csv"
HTML_OUTPUT = OUTPUT_DIR / "dashboard.html"