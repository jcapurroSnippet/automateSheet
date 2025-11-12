# main.py
from flask import Flask, jsonify
from rif_scheduler import RIFScheduler  # importa tu clase

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def run_rif():
    scheduler = RIFScheduler()
    try:
        # asumo que tu clase tiene un método para hacer lo que venís haciendo
        success = scheduler.run()
        status_code = 200 if success else 500
        status = "ok" if success else "error"
        return jsonify({"status": status, "logs": scheduler.get_logs()}), status_code
    except Exception as e:
        # logueás el error para verlo en Cloud Run
        print("Error en run_rif:", e)
        return jsonify({"status": "error", "detail": str(e), "logs": scheduler.get_logs()}), 500


# esto es útil si lo corrés local
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
