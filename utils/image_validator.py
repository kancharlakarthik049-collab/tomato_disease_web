import numpy as np
from PIL import Image, UnidentifiedImageError

MIN_DIMENSION = 50       # pixels — reject tiny icons/thumbnails
MAX_DIMENSION = 5000     # pixels — reject unreasonably large images
MIN_STD_DEV   = 10.0    # reject blank / solid-colour images
PLANT_RATIO_MIN = 0.12  # 12% of pixels must look plant-like


def _plant_ratio(arr):
    """
    Return the fraction of pixels that look like a plant leaf.
    Covers: healthy green, yellowing/diseased leaves (Yellow Leaf Curl,
    Early Blight), and olive/shadowed green areas.
    """
    R = arr[:, :, 0]
    G = arr[:, :, 1]
    B = arr[:, :, 2]

    # Healthy green
    green = (G > R * 1.05) & (G > B * 1.05) & (G > 40)

    # Yellowing / diseased (Yellow Leaf Curl Virus, Early Blight yellowing)
    yellow_green = (G > 70) & (R > 60) & (B < 130) & (G > B * 1.15)

    # Olive / dark-green shadowed areas
    olive = (G > 35) & (G > B) & (R < 180) & (B < 110)

    plant_mask = green | yellow_green | olive
    return float(np.sum(plant_mask)) / (arr.shape[0] * arr.shape[1])


def validate_image(filepath):
    """
    Run all pre-flight checks on an uploaded image file.

    Returns:
        (True,  None,          [])          — image is valid
        (False, error_message, [tip, ...])  — image was rejected
    """
    # ── 1. Open and verify it is a real image ─────────────────────────────
    try:
        probe = Image.open(filepath)
        probe.verify()          # detects corrupt / truncated files
    except (UnidentifiedImageError, Exception):
        return False, "Uploaded file is not a valid image.", [
            "Upload a JPG or PNG file",
            "Make sure the file is not corrupted or truncated",
        ]

    # Re-open after verify() (verify() closes the file internally)
    img = Image.open(filepath).convert("RGB")

    # ── 2. Dimension check ───────────────────────────────────────────────
    w, h = img.size
    if w < MIN_DIMENSION or h < MIN_DIMENSION:
        return False, (
            f"Image is too small ({w}\u00d7{h} px). "
            f"Minimum size is {MIN_DIMENSION}\u00d7{MIN_DIMENSION} pixels."
        ), [
            "Upload a larger, clearer close-up of the leaf",
            f"Minimum image size is {MIN_DIMENSION}\u00d7{MIN_DIMENSION} pixels",
        ]

    if w > MAX_DIMENSION or h > MAX_DIMENSION:
        return False, (
            f"Image is too large ({w}\u00d7{h} px). "
            f"Maximum is {MAX_DIMENSION}\u00d7{MAX_DIMENSION} pixels."
        ), [
            "Resize the image before uploading",
            f"Maximum image size is {MAX_DIMENSION}\u00d7{MAX_DIMENSION} pixels",
        ]

    # ── 3. Resize to working size for content checks ─────────────────────
    arr = np.array(img.resize((224, 224)), dtype=np.float32)

    # ── 4. Blank / solid-colour check ────────────────────────────────────
    if np.std(arr) < MIN_STD_DEV:
        return False, (
            "Image appears to be blank or a solid colour. "
            "Please upload a real tomato leaf photo."
        ), [
            "Upload an actual photo of a tomato leaf",
            "Avoid blank, white, or solid-coloured images",
        ]

    # ── 5. Plant-leaf colour check ───────────────────────────────────────
    ratio = _plant_ratio(arr)
    print(f"[validator] plant_ratio={ratio:.3f}")

    if ratio < PLANT_RATIO_MIN:
        return False, (
            f"No plant leaf detected in this image "
            f"(plant pixels: {ratio * 100:.1f}%). "
            "Please upload a tomato leaf image."
        ), [
            "Make sure the leaf fills most of the frame",
            "Use natural daylight for best results",
            "Avoid dark, blurry, or heavily shadowed images",
            "The image should show a green or yellowed tomato leaf",
            "Diseased leaves with spots are fine — just ensure the leaf is visible",
        ]

    return True, None, []
