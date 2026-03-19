import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def enhance_image(img):
    img_array = np.array(img, dtype=np.float32)
    mean_brightness = np.mean(img_array)

    if mean_brightness < 80:
        brightness_factor = 1.5
    elif mean_brightness > 180:
        brightness_factor = 0.8
    else:
        brightness_factor = 1.1

    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(brightness_factor)

    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)

    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.2)

    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(2.0)

    img = img.filter(ImageFilter.UnsharpMask(
        radius=2,
        percent=150,
        threshold=3
    ))

    return img


def smart_crop(img):
    img_array = np.array(img)
    height, width = img_array.shape[:2]

    r = img_array[:, :, 0].astype(float)
    g = img_array[:, :, 1].astype(float)
    b = img_array[:, :, 2].astype(float)

    plant_mask = (
        (g > r * 0.9) |
        (g > b * 0.9) |
        ((g > 40) & (g > r * 0.8))
    )

    row_has_plant = np.any(plant_mask, axis=1)
    col_has_plant = np.any(plant_mask, axis=0)

    if np.any(row_has_plant) and np.any(col_has_plant):
        rows = np.where(row_has_plant)[0]
        cols = np.where(col_has_plant)[0]

        top = max(0, rows[0] - 10)
        bottom = min(height, rows[-1] + 10)
        left = max(0, cols[0] - 10)
        right = min(width, cols[-1] + 10)

        crop_height = bottom - top
        crop_width = right - left

        if (crop_height > height * 0.3 and
                crop_width > width * 0.3):
            img = img.crop((left, top, right, bottom))

    return img


def clahe_enhance(img):
    img_array = np.array(img, dtype=np.uint8)
    result = np.zeros_like(img_array)

    for channel in range(3):
        ch = img_array[:, :, channel]

        hist, bins = np.histogram(ch.flatten(), 256, [0, 256])

        clip_limit = int(ch.size * 0.01)
        excess = np.sum(np.maximum(hist - clip_limit, 0))
        hist = np.minimum(hist, clip_limit)
        hist += excess // 256

        cdf = hist.cumsum()
        cdf_min = cdf[cdf > 0].min()
        total_pixels = ch.size

        lut = np.round(
            (cdf - cdf_min) / (total_pixels - cdf_min) * 255
        ).astype(np.uint8)
        lut = np.clip(lut, 0, 255)

        result[:, :, channel] = lut[ch]

    return Image.fromarray(result)


def normalize_colors(img):
    img_array = np.array(img, dtype=np.float32)

    for channel in range(3):
        ch = img_array[:, :, channel]
        ch_min = np.percentile(ch, 2)
        ch_max = np.percentile(ch, 98)

        if ch_max > ch_min:
            img_array[:, :, channel] = np.clip(
                (ch - ch_min) / (ch_max - ch_min) * 255,
                0, 255
            )

    return Image.fromarray(img_array.astype(np.uint8))


def preprocess_image(image_path):
    print(f"Preprocessing: {image_path}")

    img = Image.open(image_path).convert("RGB")
    original_size = img.size
    print(f"Original size: {original_size}")

    img = normalize_colors(img)
    img = smart_crop(img)
    print(f"After crop: {img.size}")

    img = clahe_enhance(img)
    img = enhance_image(img)

    img = img.resize((224, 224), Image.LANCZOS)

    img_array = np.array(img, dtype=np.float32)
    img_array = (img_array / 127.5) - 1.0
    img_array = np.expand_dims(img_array, axis=0)

    print(f"Final shape: {img_array.shape}")
    print(f"Value range: [{img_array.min():.2f}, {img_array.max():.2f}]")

    return img_array
