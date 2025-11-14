# main.py
from flask import Flask, jsonify
from rif_scheduler import RIFScheduler

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    """Health check para Cloud Run"""
    return jsonify({"status": "ok"}), 200

@app.route("/", methods=["GET", "POST"])
def run_rif():
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
