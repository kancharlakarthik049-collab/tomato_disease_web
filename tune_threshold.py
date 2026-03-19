"""
Threshold tuning for PLANT_RATIO_MIN in image_validator.py

Tests thresholds [0.10, 0.15, 0.20, 0.25] against 8 representative image
types that span the full spectrum from healthy leaf → dead leaf → non-plant.

Run from project root:
    python tune_threshold.py
"""

import os
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import utils.image_validator as validator_mod
from utils.image_validator import validate_image

THRESHOLDS = [0.10, 0.15, 0.20, 0.25]

# ── Helpers ──────────────────────────────────────────────────────────────────

def _save(arr, path):
    np.clip(arr, 0, 255, out=arr)
    Image.fromarray(arr.astype(np.uint8), "RGB").save(path, "JPEG", quality=95)
    return path


def _blend(base, spot, frac, size=224, seed=0):
    """
    Return (H,W,3) float32 array: `frac` of pixels set to `spot`, rest `base`.
    Small per-pixel noise is added so the image never fails the blank/std check.
    """
    rng = np.random.default_rng(seed)
    arr = np.full((size, size, 3), base, dtype=np.float32)
    n_spot = int(size * size * frac)
    idx = rng.choice(size * size, n_spot, replace=False)
    rows, cols = np.unravel_index(idx, (size, size))
    arr[rows, cols] = spot
    arr += rng.uniform(-12, 12, arr.shape)   # variance so std-dev > 10
    return arr


# ── Synthetic test images ─────────────────────────────────────────────────────
# Each entry: (name, ndarray, expected_result)
#   expected_result: True = should be accepted, False = should be rejected

def build_test_cases(tmp):
    cases = []

    # 1. Healthy tomato leaf — solid green, ~95% plant pixels
    arr = _blend([35, 155, 40], [35, 155, 40], 0.0, seed=1)    # all-green
    cases.append(("Healthy tomato leaf      ", arr, True))

    # 2. Early Blight leaf — 70% green + 30% brown disease spots
    arr = _blend([35, 155, 40], [130, 85, 25], 0.30, seed=2)
    cases.append(("Early Blight leaf (30%)  ", arr, True))

    # 3. Late Blight leaf — 20% green + 80% very dark brown/black lesions
    arr = _blend([35, 140, 42], [60, 38, 18], 0.80, seed=3)
    cases.append(("Late Blight leaf (80%)   ", arr, True))

    # 4. Near-dead leaf — only ~8% green, rest dark brown
    arr = _blend([100, 60, 22], [40, 130, 45], 0.08, seed=4)
    cases.append(("Near-dead leaf (8% green)", arr, True))  # marginal

    # 5. Yellow Leaf Curl Virus — ~80% yellow-green (R=160, G=185, B=40)
    arr = _blend([160, 185, 40], [170, 170, 35], 0.20, seed=5)
    cases.append(("Yellow Leaf Curl Virus   ", arr, True))

    # 6. Solid red — no plant pixels at all
    arr = _blend([210, 30, 30], [200, 40, 35], 0.0, seed=6)
    cases.append(("Solid red image          ", arr, False))

    # 7. Indoor cat — neutral grey (R≈G≈B, no channel dominant)
    base = np.full((224, 224), 155, dtype=np.float32)
    rng7 = np.random.default_rng(7)
    arr = np.stack([
        base + rng7.uniform(-12, 12, (224, 224)),
        base + rng7.uniform(-12, 12, (224, 224)),
        base + rng7.uniform(-12, 12, (224, 224)),
    ], axis=-1)
    cases.append(("Indoor cat (grey)        ", arr, False))

    # 8. Outdoor cat on grass — 15% pixels are green grass, 85% grey cat
    #    Green grass pixels can satisfy plant-colour conditions → borderline
    arr = _blend([158, 158, 158], [38, 148, 42], 0.15, seed=8)
    cases.append(("Outdoor cat on grass 15% ", arr, False))

    # Save all to temp files
    records = []
    for i, (name, arr, expected) in enumerate(cases):
        path = os.path.join(tmp, f"img_{i+1:02d}.jpg")
        _save(arr, path)
        records.append((name, path, expected))
    return records


# ── Pre-compute plant ratios (threshold-independent) ─────────────────────────

def _compute_ratio(path):
    img = Image.open(path).convert("RGB").resize((224, 224))
    arr = np.array(img, dtype=np.float32)
    return validator_mod._plant_ratio(arr)


# ── Run tuning ────────────────────────────────────────────────────────────────

def run():
    tmp = tempfile.mkdtemp()
    records = build_test_cases(tmp)

    print("\n" + "=" * 72)
    print("  PLANT_RATIO_MIN Threshold Tuning")
    print("=" * 72)

    # Show intrinsic plant ratios once
    print("\n  Image plant-pixel ratios (threshold-independent):")
    print(f"  {'Image':<28}  {'Ratio':>6}  {'Expected'}")
    print("  " + "-" * 50)
    ratios = {}
    for name, path, expected in records:
        r = _compute_ratio(path)
        ratios[path] = r
        exp_str = "PASS" if expected else "FAIL"
        print(f"  {name}  {r*100:5.1f}%  {exp_str}")

    # Scorecard per threshold
    print("\n" + "=" * 72)
    print("  Results per threshold")
    print("=" * 72)

    best_score = -1
    best_thresh = None
    best_summary = {}

    for thresh in THRESHOLDS:
        validator_mod.PLANT_RATIO_MIN = thresh
        tp = fp = tn = fn = 0
        details = []
        for name, path, expected in records:
            valid, msg, _ = validate_image(path)
            correct = (valid == expected)
            if expected and valid:     tp += 1
            elif expected and not valid:   fn += 1
            elif not expected and not valid:  tn += 1
            else:                      fp += 1
            details.append((name, expected, valid, correct))

        score = tp + tn          # higher = better
        # Penalty for false positives (non-plants accepted) doubles weight
        weighted = tp + tn - 2 * fp

        print(f"\n  Threshold = {thresh}")
        print(f"  {'Image':<28}  {'Expected':<9}  {'Got':<9}  {'OK?'}")
        print("  " + "-" * 60)
        for name, expected, got, ok in details:
            exp_str = "PASS" if expected else "FAIL"
            got_str = "PASS" if got else "FAIL"
            tick = "✓" if ok else "✗"
            print(f"  {name}  {exp_str:<9}  {got_str:<9}  {tick}")
        print(f"\n  TP={tp}  TN={tn}  FP={fp}  FN={fn}  "
              f"score={score}/8  weighted_score={weighted}")

        if weighted > best_score:
            best_score = weighted
            best_thresh = thresh
            best_summary = {"tp": tp, "tn": tn, "fp": fp, "fn": fn}

    # Recommendation
    print("\n" + "=" * 72)
    print(f"  RECOMMENDATION: PLANT_RATIO_MIN = {best_thresh}")
    print(f"  Weighted score {best_score}  "
          f"(TP={best_summary['tp']} TN={best_summary['tn']} "
          f"FP={best_summary['fp']} FN={best_summary['fn']})")
    print(f"  Reasoning: false positives (non-plants accepted as leaf)")
    print(f"  counted double — better to reject a borderline leaf than")
    print(f"  to diagnose a cat photo as a disease.")
    print("=" * 72 + "\n")

    return best_thresh


if __name__ == "__main__":
    best = run()
