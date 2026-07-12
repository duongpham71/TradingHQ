"""
web_app.py
Trading HQ local dashboard, scanner control, and JSON API.
"""

from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path
import config
import traceback

import pandas as pd
from flask import Flask, jsonify, redirect, render_template_string, send_file, url_for


app = Flask(__name__)

PROJECT_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = config.OUTPUT_DIR
DASHBOARD_FILE = config.HTML_OUTPUT
RESULTS_FILE = config.CSV_OUTPUT
SCAN_LOG_FILE = OUTPUT_DIR / "web_scan_log.txt"

SCANNER_FILE = PROJECT_DIR / "scanner.py"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

scan_lock = threading.Lock()
scan_status = {
    "running": False,
    "message": "Ready",
}


HOME_PAGE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <title>Trading HQ</title>

    <style>
        body {
            margin: 0;
            font-family: Arial, Helvetica, sans-serif;
            background: #f4f6f8;
            color: #1f2937;
        }

        .toolbar {
            position: sticky;
            top: 0;
            z-index: 10;
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            background: white;
            border-bottom: 1px solid #d1d5db;
        }

        .title {
            font-size: 20px;
            font-weight: bold;
            flex: 1;
        }

        .status {
            font-size: 13px;
            color: #6b7280;
        }

        button {
            border: 0;
            border-radius: 8px;
            padding: 11px 16px;
            font-size: 15px;
            font-weight: bold;
            cursor: pointer;
            background: #111827;
            color: white;
        }

        button:disabled {
            cursor: not-allowed;
            opacity: 0.55;
        }

        iframe {
            width: 100%;
            height: calc(100vh - 70px);
            border: 0;
            background: white;
        }

        .error {
            margin: 20px;
            padding: 16px;
            border-radius: 8px;
            background: #fee2e2;
            color: #991b1b;
        }
    </style>
</head>

<body>

<div class="toolbar">
    <div class="title">Trading HQ</div>

    <div id="status" class="status">
        {{ status_message }}
    </div>

    <button
        id="scanButton"
        type="button"
        onclick="runScan()"
        {% if scan_running %}disabled{% endif %}
    >
        {% if scan_running %}
            Scanning...
        {% else %}
            Refresh Scan
        {% endif %}
    </button>
</div>

{% if dashboard_exists %}
    <iframe
        id="dashboardFrame"
        src="{{ url_for('dashboard_file') }}?v={{ version }}"
    ></iframe>
{% else %}
    <div class="error">
        Dashboard not found. Tap Refresh Scan to generate it.
    </div>
{% endif %}

<script>
async function runScan() {
    const button = document.getElementById("scanButton");
    const status = document.getElementById("status");

    button.disabled = true;
    button.textContent = "Scanning...";
    status.textContent = "Scanner is running...";

    try {
        const response = await fetch("/api/run-scan", {
            method: "POST"
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.message || "Scanner failed."
            );
        }

        status.textContent = result.message || "Scan completed.";

        const frame = document.getElementById("dashboardFrame");

        if (frame) {
            frame.src = "/dashboard-file?v=" + Date.now();
        } else {
            window.location.reload();
        }
    } catch (error) {
        status.textContent = error.message;
        alert("Trading HQ error: " + error.message);
    } finally {
        button.disabled = false;
        button.textContent = "Refresh Scan";
    }
}
</script>

</body>
</html>
"""


@app.route("/")
def home():
    """Show the mobile-friendly dashboard wrapper."""
    version = (
        int(DASHBOARD_FILE.stat().st_mtime)
        if DASHBOARD_FILE.exists()
        else 0
    )

    return render_template_string(
        HOME_PAGE,
        dashboard_exists=DASHBOARD_FILE.exists(),
        scan_running=scan_status["running"],
        status_message=scan_status["message"],
        version=version,
    )


@app.route("/dashboard-file")
def dashboard_file():
    """Serve the generated dashboard HTML."""
    if not DASHBOARD_FILE.exists():
        return (
            "Trading HQ dashboard not found. Run scanner.py first.",
            404,
        )

    return send_file(
        DASHBOARD_FILE,
        max_age=0,
    )


@app.route("/api/run-scan", methods=["POST"])
def api_run_scan():
    """Run scanner.py and return its completion status."""
    if not SCANNER_FILE.exists():
        return jsonify(
            {
                "status": "error",
                "message": "scanner.py was not found.",
            }
        ), 404

    if not scan_lock.acquire(blocking=False):
        return jsonify(
            {
                "status": "busy",
                "message": "A scan is already running.",
            }
        ), 409

    scan_status["running"] = True
    scan_status["message"] = "Scanner is running..."

    try:
        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )
        scanner_environment = os.environ.copy()

        scanner_environment["TRADINGHQ_DATA_DIR"] = str(
            OUTPUT_DIR
        )

        completed = subprocess.run(
            [
                sys.executable,
                str(SCANNER_FILE),
            ],
            cwd=str(PROJECT_DIR),
            env=scanner_environment,
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )

        log_content = (
            f"OUTPUT_DIR: {OUTPUT_DIR}\n"
            f"RESULTS_FILE: {RESULTS_FILE}\n"
            f"RESULTS_EXISTS: {RESULTS_FILE.exists()}\n"
            f"RETURN_CODE: {completed.returncode}\n\n"
            "STDOUT\n"
            "======\n"
            f"{completed.stdout}\n\n"
            "STDERR\n"
            "======\n"
            f"{completed.stderr}\n"
        )

        SCAN_LOG_FILE.write_text(
            log_content,
            encoding="utf-8",
        )

        if completed.returncode != 0:
            error_message = (
                completed.stderr.strip()
                or completed.stdout.strip()
                or f"Scanner exited with code {completed.returncode}."
            )

            scan_status["message"] = "Scan failed."

            return jsonify(
                {
                    "status": "error",
                    "message": error_message,
                }
            ), 500

        if not RESULTS_FILE.exists():
            scan_status["message"] = "Scan completed, but results are missing."

            return jsonify(
                {
                    "status": "error",
                    "message": (
                        "scanner_results.csv was not created. "
                        "Check output/web_scan_log.txt."
                    ),
                }
            ), 500

        scan_status["message"] = "Scan completed successfully."

        return jsonify(
            {
                "status": "ok",
                "message": "Scan completed successfully.",
            }
        )

    except subprocess.TimeoutExpired:
        scan_status["message"] = "Scanner timed out."

        return jsonify(
            {
                "status": "error",
                "message": "Scanner exceeded the 180-second timeout.",
            }
        ), 504

    except OSError as exc:
        scan_status["message"] = "Could not start scanner."

        return jsonify(
            {
                "status": "error",
                "message": f"Could not start scanner: {exc}",
            }
        ), 500
    
    except Exception as exc:
        error_trace = traceback.format_exc()

        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        SCAN_LOG_FILE.write_text(
            "UNHANDLED WEB APP ERROR\n"
            "=======================\n"
            f"{error_trace}\n",
            encoding="utf-8",
        )

        scan_status["message"] = "Unhandled scan error."

        return jsonify(
            {
                "status": "error",
                "message": str(exc),
                "traceback": error_trace,
            }
        ), 500
    
    finally:
        scan_status["running"] = False
        scan_lock.release()


@app.route("/api/results")
def api_results():
    """Return all latest scanner results."""
    results = read_results()

    if results is None:
        return jsonify(
            {
                "status": "error",
                "message": "scanner_results.csv not found",
            }
        ), 404

    return jsonify(
        {
            "status": "ok",
            "count": len(results),
            "results": dataframe_records(results),
        }
    )


@app.route("/api/qualified")
def api_qualified():
    """Return only fully qualified scanner results."""
    results = read_results()

    if results is None:
        return jsonify(
            {
                "status": "error",
                "message": "scanner_results.csv not found",
            }
        ), 404

    if "passed" in results.columns:
        passed_mask = (
            results["passed"]
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("true")
        )

        results = results[passed_mask]

    return jsonify(
        {
            "status": "ok",
            "count": len(results),
            "results": dataframe_records(results),
        }
    )


@app.route("/api/top20")
def api_top20():
    """Return the top 20 ranked results."""
    results = read_results()

    if results is None:
        return jsonify(
            {
                "status": "error",
                "message": "scanner_results.csv not found",
            }
        ), 404

    if "rank" in results.columns:
        results = results.sort_values("rank")
    elif "score" in results.columns:
        results = results.sort_values(
            "score",
            ascending=False,
        )

    results = results.head(20)

    return jsonify(
        {
            "status": "ok",
            "count": len(results),
            "results": dataframe_records(results),
        }
    )


@app.route("/api/health")
def api_health():
    return jsonify({
        "status": "ok",
        "output_dir": str(OUTPUT_DIR),
        "results_file": str(RESULTS_FILE),
        "dashboard_file": str(DASHBOARD_FILE),
        "dashboard_exists": DASHBOARD_FILE.exists(),
        "results_exists": RESULTS_FILE.exists(),
        "scanner_exists": SCANNER_FILE.exists(),
        "scan_running": scan_status["running"],
        "scan_message": scan_status["message"],
    })


def read_results() -> pd.DataFrame | None:
    """Read the latest CSV safely."""
    if not RESULTS_FILE.exists():
        return None

    try:
        return pd.read_csv(RESULTS_FILE)
    except (OSError, pd.errors.ParserError):
        return None


def dataframe_records(frame: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame into JSON-safe records."""
    cleaned = frame.astype(object).where(
        pd.notna(frame),
        None,
    )

    return cleaned.to_dict(
        orient="records",
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=False,
        threaded=True,
    )

@app.route("/api/scan-log")
def api_scan_log():
    if not SCAN_LOG_FILE.exists():
        return jsonify({
            "status": "error",
            "message": "No scan log exists yet.",
        }), 404

    return send_file(
        SCAN_LOG_FILE,
        mimetype="text/plain",
        max_age=0,
    )

if __name__ == "__main__":
    import os

    port = int(os.getenv("PORT", "8000"))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        threaded=True,
    )

