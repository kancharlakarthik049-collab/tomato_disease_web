import os
import uuid
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from utils.model_loader import load_model
from utils.predictor import predict_disease
from utils.image_validator import validate_image

app = Flask(__name__)
CORS(app)

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"status": "error", "message": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"status": "error", "message": "Invalid file type. Use JPG, JPEG, or PNG"}), 400

    filepath = None
    try:
        filename = str(uuid.uuid4()) + "_" + secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Reject suspiciously tiny files (< 5 KB)
        if os.path.getsize(filepath) < 5 * 1024:
            os.remove(filepath)
            return jsonify({
                "status": "rejected",
                "confidence_level": "none",
                "message": "File is too small to be a valid image (< 5 KB).",
                "tips": ["Upload a real photo of a tomato leaf, not a thumbnail"],
                "disease_name": None,
                "confidence": 0
            }), 422

        # Validate image content before running the model
        is_valid, error_msg, tips = validate_image(filepath)
        if not is_valid:
            os.remove(filepath)
            return jsonify({
                "status": "rejected",
                "confidence_level": "none",
                "message": error_msg,
                "tips": tips,
                "disease_name": None,
                "confidence": 0
            }), 422

        result = predict_disease(filepath)

        if os.path.exists(filepath):
            os.remove(filepath)

        if result["status"] == "rejected":
            return jsonify(result), 422

        return jsonify(result)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"status": "error", "message": str(e)}), 500

# Load model at startup
with app.app_context():
    load_model()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
