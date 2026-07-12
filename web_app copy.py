"""
web_app.py
Trading HQ local dashboard and JSON API.
"""

from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, send_file


app = Flask(__name__)

PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "output"

DASHBOARD_FILE = OUTPUT_DIR / "dashboard.html"
RESULTS_FILE = OUTPUT_DIR / "scanner_results.csv"


@app.route("/")
def dashboard():
    """Serve the latest HTML dashboard."""
    if not DASHBOARD_FILE.exists():
        return (
            "Trading HQ dashboard not found. Run scanner.py first.",
            404,
        )

    return send_file(DASHBOARD_FILE)


@app.route("/api/results")
def api_results():
    """Return all latest scanner results as JSON."""
    if not RESULTS_FILE.exists():
        return jsonify(
            {
                "status": "error",
                "message": "scanner_results.csv not found",
            }
        ), 404

    results = pd.read_csv(RESULTS_FILE)
    results = results.where(pd.notna(results), None)

    return jsonify(
        {
            "status": "ok",
            "count": len(results),
            "results": results.to_dict(orient="records"),
        }
    )


@app.route("/api/qualified")
def api_qualified():
    """Return only stocks that passed every hard filter."""
    if not RESULTS_FILE.exists():
        return jsonify(
            {
                "status": "error",
                "message": "scanner_results.csv not found",
            }
        ), 404

    results = pd.read_csv(RESULTS_FILE)

    if "passed" in results.columns:
        passed_mask = (
            results["passed"]
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("true")
        )
        results = results[passed_mask]

    results = results.where(pd.notna(results), None)

    return jsonify(
        {
            "status": "ok",
            "count": len(results),
            "results": results.to_dict(orient="records"),
        }
    )


@app.route("/api/top20")
def api_top20():
    """Return the top 20 ranked scanner results."""
    if not RESULTS_FILE.exists():
        return jsonify(
            {
                "status": "error",
                "message": "scanner_results.csv not found",
            }
        ), 404

    results = pd.read_csv(RESULTS_FILE)

    if "rank" in results.columns:
        results = results.sort_values("rank")
    elif "score" in results.columns:
        results = results.sort_values(
            "score",
            ascending=False,
        )

    results = results.head(20)
    results = results.where(pd.notna(results), None)

    return jsonify(
        {
            "status": "ok",
            "count": len(results),
            "results": results.to_dict(orient="records"),
        }
    )


@app.route("/api/health")
def api_health():
    """Simple health check."""
    return jsonify(
        {
            "status": "ok",
            "dashboard_exists": DASHBOARD_FILE.exists(),
            "results_exists": RESULTS_FILE.exists(),
        }
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=False,
    )