# Crop Disease Identification System

A full-stack web application for identifying tomato crop diseases using an InceptionV3 deep learning model (exported to ONNX format) trained on the Plant Village Tomato Disease dataset.

## Features
- Upload tomato leaf images and get instant AI-powered disease diagnosis
- 10 disease classes supported (9 diseases + healthy)
- Confidence-based results with high (≥70%) and medium (≥45%) thresholds
- Treatment and prevention tips for each detected disease
- Green-leaf validation to reject non-leaf images
- Modern, responsive UI (Bootstrap 5, custom CSS, Google Fonts)
- Deployable to Render.com

## Technology Stack
- **Runtime:** Python 3.11.9
- **Web Framework:** Flask 2.3.3 with Flask-CORS 4.0.0
- **Model Inference:** ONNX Runtime 1.17.1
- **Image Processing:** Pillow 10.2.0, NumPy 1.26.4
- **Server:** Gunicorn 21.2.0
- **Deployment:** Render.com

## Requirements

**Python 3.11.9 is required.** The following packages are pinned for compatibility:

| Package | Version |
|---------|---------|
| Flask | 2.3.3 |
| Flask-Cors | 4.0.0 |
| gunicorn | 21.2.0 |
| numpy | 1.26.4 |
| onnxruntime | 1.17.1 |
| Pillow | 10.2.0 |
| Werkzeug | 2.3.7 |
| Jinja2 | 3.1.2 |

See `requirements.txt` for the full pinned dependency list.

## Project Structure

```
tomato_disease_web/
├── app.py                  # Flask application and API routes
├── requirements.txt        # Pinned Python dependencies (Python 3.11)
├── runtime.txt             # Python version for deployment (python-3.11.9)
├── Procfile                # Gunicorn start command for Render.com
├── render.yaml             # Render.com service configuration
├── model/
│   ├── README.md           # Instructions for placing the model file
│   └── inceptionv3_tomato.onnx  # ONNX model (not committed – see model/README.md)
├── utils/
│   ├── model_loader.py     # ONNX Runtime session loader
│   ├── predictor.py        # Disease prediction logic and class metadata
│   └── preprocessor.py     # Image preprocessing pipeline
├── templates/
│   ├── base.html           # Base HTML template
│   ├── index.html          # Upload page
│   ├── result.html         # Prediction result page
│   ├── about.html          # About page
│   ├── 404.html            # 404 error page
│   └── 500.html            # 500 error page
├── static/                 # CSS, JS, and image assets
└── uploads/                # Temporary upload directory (not committed)
```

## Supported Disease Classes

| Class | Display Name |
|-------|-------------|
| Tomato_Bacterial_Spot | Bacterial Spot |
| Tomato_Early_Blight | Early Blight |
| Tomato_Late_Blight | Late Blight |
| Tomato_Leaf_Mold | Leaf Mold |
| Tomato_Septoria_Leaf_Spot | Septoria Leaf Spot |
| Tomato_Spider_Mites | Spider Mites |
| Tomato_Target_Spot | Target Spot |
| Tomato_Tomato_Yellow_Leaf_Curl_Virus | Yellow Leaf Curl Virus |
| Tomato_Tomato_mosaic_virus | Mosaic Virus |
| Tomato_healthy | Healthy Plant |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Serve the upload/home page |
| GET | `/about` | Serve the about page |
| GET | `/health` | Health check — returns `{"status": "ok"}` |
| POST | `/predict` | Accept a leaf image and return a disease prediction |

### POST `/predict`

**Request:** `multipart/form-data` with field `file` containing a JPG, JPEG, or PNG image (max 16 MB).

**Response (success):**
```json
{
  "status": "success",
  "confidence_level": "high",
  "disease_name": "Tomato_Early_Blight",
  "display_name": "Early Blight",
  "confidence": 92.35,
  "description": "...",
  "symptoms": ["..."],
  "treatment": ["..."],
  "prevention": ["..."]
}
```

**Response (rejected / low confidence):**
```json
{
  "status": "rejected",
  "confidence_level": "low",
  "message": "❌ Image not recognized as tomato leaf.",
  "confidence": 28.5,
  "tips": ["..."]
}
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd tomato_disease_web
   ```
2. **Create and activate a Python 3.11 virtual environment:**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Add the ONNX model:**
   - Place `inceptionv3_tomato.onnx` in the `model/` folder.
   - See `model/README.md` for details.
5. **Run the app locally:**
   ```bash
   python app.py
   ```
6. **Open in browser:**
   - Go to [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Deployment

The app is pre-configured for **Render.com** free tier deployment:

- `render.yaml` — defines the web service (Python 3.11.9, Singapore region)
- `Procfile` — Gunicorn start command: `gunicorn app:app --workers 1 --timeout 120 --bind 0.0.0.0:$PORT`
- `runtime.txt` — specifies `python-3.11.9`

Push to your connected Render.com repository to trigger an automatic deploy.

## Notes
- The model file (`inceptionv3_tomato.onnx`) is not included in the repository. See `model/README.md` for instructions.
- All uploaded images are processed in memory and deleted immediately after prediction.
- Maximum upload size is 16 MB.
