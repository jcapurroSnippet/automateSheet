# main.py
from flask import Flask, jsonify, render_template, request
"""
main.py - Flask entrypoint

Note: import of RIFScheduler is performed lazily inside the request handler to avoid
heavy imports (pandas, etc.) at worker startup which can cause memory spikes and
worker timeouts in constrained environments like Cloud Run.
"""

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB max upload


def _build_sheet_ops():
    """Crea una instancia de SheetOperations autenticada."""
    from auth import GoogleSheetsAuth
    from sheet_operations import SheetOperations

    auth = GoogleSheetsAuth()
    service = auth.authenticate()
    creds = auth.get_credentials()
    return SheetOperations(service, credentials=creds)


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


@app.route("/upload", methods=["GET"])
def upload_page():
    """Página web para gestionar imágenes de los programas RIF."""
    from image_uploader import ImageUploader

    try:
        sheet_ops = _build_sheet_ops()
    except Exception as e:
        print("Error de autenticación:", e)
        sheet_ops = None

    uploader = ImageUploader(sheet_ops)
    programs = uploader.get_programs()

    return render_template('upload.html', programs=programs)


@app.route("/api/upload-image", methods=["POST"])
def api_upload_image():
    """API para subir imágenes a GCS y actualizar el sheet META."""
    from image_uploader import ImageUploader

    program_id = request.form.get('program_id')
    if not program_id:
        return jsonify({"error": "program_id es requerido"}), 400

    image_1x1 = request.files.get('image_1x1')
    images_additional = request.files.getlist('images_additional')
    images_additional = [f for f in images_additional if f.filename]

    if not (image_1x1 and image_1x1.filename) and not images_additional:
        return jsonify({"error": "No se seleccionaron archivos"}), 400

    try:
        sheet_ops = _build_sheet_ops()
        uploader = ImageUploader(sheet_ops)
        results = uploader.upload_and_update(
            program_id,
            image_1x1 if image_1x1 and image_1x1.filename else None,
            images_additional or None,
        )
        return jsonify({"status": "ok", "results": results})
    except Exception as e:
        print("Error en upload:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

