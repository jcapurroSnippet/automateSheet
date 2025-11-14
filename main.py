# main.py
from flask import Flask, jsonify
"""
main.py - Flask entrypoint

Note: import of RIFScheduler is performed lazily inside the request handler to avoid
heavy imports (pandas, etc.) at worker startup which can cause memory spikes and
worker timeouts in constrained environments like Cloud Run.
"""

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    """Health check para Cloud Run"""
    return jsonify({"status": "ok"}), 200

@app.route("/", methods=["GET", "POST"])
def run_rif():
    # Import here to keep worker startup light (avoid loading pandas, etc. at import time)
    from rif_scheduler import RIFScheduler
    scheduler = RIFScheduler()
    try:
        success = scheduler.run()
        status_code = 200 if success else 500
        status = "ok" if success else "error"
        return jsonify({"status": status, "logs": scheduler.get_logs()}), status_code
    except Exception as e:
        print("Error en run_rif:", e)
        return jsonify({"status": "error", "detail": str(e), "logs": scheduler.get_logs()}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

