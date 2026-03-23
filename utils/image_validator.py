import numpy as np
from PIL import Image, UnidentifiedImageError

MIN_DIMENSION = 50
MAX_DIMENSION = 5000
MIN_STD_DEV   = 10.0
PLANT_RATIO_MIN = 0.12


def _plant_ratio(arr):
    R = arr[:, :, 0]
    G = arr[:, :, 1]
    B = arr[:, :, 2]

    green = (G > R * 1.15) & (G > B * 1.15) & (G > 45)

    yellow_green = (
        (G > 75) & (R > 65) & (B < 110) &
        (G > B * 1.20) &
        (G >= R * 0.80)
    )

    olive = (G > 38) & (G > B * 1.10) & (R < 160) & (B < 105)

    plant_mask = green | yellow_green | olive
    return float(np.sum(plant_mask)) / (arr.shape[0] * arr.shape[1])


def validate_image(filepath):
    try:
        probe = Image.open(filepath)
        probe.verify()
    except (UnidentifiedImageError, Exception):
        return False, "Uploaded file is not a valid image.", [
            "Upload a JPG or PNG file",
            "Make sure the file is not corrupted or truncated",
        ]

    img = Image.open(filepath).convert("RGB")

    w, h = img.size
    if w < MIN_DIMENSION or h < MIN_DIMENSION:
        return False, (
            f"Image is too small ({w}×{h} px). "
            f"Minimum size is {MIN_DIMENSION}×{MIN_DIMENSION} pixels."
        ), [
            "Upload a larger, clearer close-up of the leaf",
            f"Minimum image size is {MIN_DIMENSION}×{MIN_DIMENSION} pixels",
        ]

    if w > MAX_DIMENSION or h > MAX_DIMENSION:
        return False, (
            f"Image is too large ({w}×{h} px). "
            f"Maximum is {MAX_DIMENSION}×{MAX_DIMENSION} pixels."
        ), [
            "Resize the image before uploading",
            f"Maximum image size is {MAX_DIMENSION}×{MAX_DIMENSION} pixels",
        ]

    arr = np.array(img.resize((224, 224)), dtype=np.float32)

    if np.std(arr) < MIN_STD_DEV:
        return False, (
            "Image appears to be blank or a solid colour. "
            "Please upload a real tomato leaf photo."
        ), [
            "Upload an actual photo of a tomato leaf",
            "Avoid blank, white, or solid-coloured images",
        ]

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
