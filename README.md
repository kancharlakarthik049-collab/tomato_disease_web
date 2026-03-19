# Crop Disease Identification System

A full-stack web application for identifying tomato crop diseases using an InceptionV3 deep learning model trained on the Plant Village Tomato Disease dataset.

## Features
- Upload tomato leaf images and get instant AI-powered disease diagnosis
- 10 disease classes supported
- Treatment and prevention tips for each disease
- Modern, responsive UI (Bootstrap 5, custom CSS, Google Fonts)
- Deployable to Render.com

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd crop-disease-identification
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Download the model:**
   - Place your `inceptionv3_tomato.h5` model in the `model/` folder, or set up Google Drive download in `app.py`.
4. **Run the app locally:**
   ```bash
   python app.py
   ```
5. **Open in browser:**
   - Go to [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Deployment
- Ready for Render.com deployment (see `render.yaml`, `Procfile`, `runtime.txt`)

## Notes
- The model file (`inceptionv3_tomato.h5`) is not included in the repo. See `model/README.md` for instructions.
- All uploads are stored temporarily and not committed.
