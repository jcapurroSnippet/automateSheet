# main.py
from flask import Flask, jsonify
from rif_scheduler import RIFScheduler  # importa tu clase

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def run_rif():
    try:
        scheduler = RIFScheduler()
        # asumo que tu clase tiene un método para hacer lo que venís haciendo
        scheduler.run()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        # logueás el error para verlo en Cloud Run
        print("Error en run_rif:", e)
        return jsonify({"status": "error", "detail": str(e)}), 500


# esto es útil si lo corrés local
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
