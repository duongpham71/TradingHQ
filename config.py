import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent

API_KEY_ENV = "POLYGON_API_KEY"
API_KEY = os.getenv(API_KEY_ENV, "POAK3yvI4e2ZgUhZfwyfwoqTStfaumfm")

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
