import numpy as np
from PIL import Image, ImageOps


def preprocess_image(image_path):
    """
    Preprocessing pipeline for InceptionV3 ONNX model.

    Matches EXACTLY the Keras tf.keras.applications.inception_v3.preprocess_input
    pipeline used during training:
      1. Open raw image (no custom enhancements — they corrupt model predictions)
      2. Fix EXIF orientation so phone photos are correctly oriented
      3. Convert to RGB (removes alpha channel, handles grayscale)
      4. Resize to 224×224 with BILINEAR (Keras ImageDataGenerator default)
      5. Normalize: (pixel / 127.5) - 1.0  →  range [-1, 1]
      6. Add batch dimension → shape (1, 224, 224, 3)

    WARNING: Do NOT add brightness/contrast/CLAHE/sharpness enhancements here.
    The model was never trained on enhanced images, so any enhancement causes
    distribution shift and biases predictions toward a single class (Early Blight).
    """
    # Step 1: Open image
    image = Image.open(image_path)

    # Step 2: Fix EXIF orientation — critical for phone camera photos
    # (ImageOps.exif_transpose is the clean Pillow way; handles all 8 orientations)
    image = ImageOps.exif_transpose(image)

    # Step 3: Convert to RGB — removes alpha (RGBA PNG), handles grayscale/CMYK
    image = image.convert("RGB")

    # Step 4: Resize to 224×224 with BILINEAR interpolation
    # (Keras ImageDataGenerator uses BILINEAR by default during training)
    image = image.resize((224, 224), Image.Resampling.BILINEAR)

    # Step 5: Float32 array, then apply InceptionV3 normalization
    # Keras formula: (x / 127.5) - 1.0  →  values in [-1, 1]
    arr = np.array(image, dtype=np.float32)
    arr = (arr / 127.5) - 1.0

    # Step 6: Add batch dimension → (1, 224, 224, 3)  [NHWC format]
    arr = np.expand_dims(arr, axis=0)

    print(f"[DEBUG] Preprocessed shape: {arr.shape}")
    print(f"[DEBUG] Value range: [{arr.min():.3f}, {arr.max():.3f}]")

    return arr
