"""
Tests for utils/image_validator.py

Run from the project root:
    python test_validator.py

Each test synthesises an image in memory, saves it to a temp file, and
calls validate_image().  No real photos are needed.
"""

import os
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

# Ensure 'utils' is importable when executed from the project directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.image_validator import validate_image


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _save_rgb(arr: np.ndarray, path: str) -> str:
    """Clamp array to [0,255], save as JPEG, return the path."""
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    Image.fromarray(arr, "RGB").save(path, "JPEG")
    return path


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestImageValidator(unittest.TestCase):
    """5 representative validation scenarios."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        print("\n" + "=" * 60)
        print("  Image Validator — Test Results")
        print("=" * 60)

    @classmethod
    def tearDownClass(cls):
        print("=" * 60)

    def _path(self, name: str) -> str:
        return os.path.join(self.tmp, name)

    # ------------------------------------------------------------------
    # 1. Solid green image — should PASS
    # ------------------------------------------------------------------
    def test_01_solid_green_passes(self):
        """Green image (with noise so std-dev > blank threshold) → accepted."""
        rng = np.random.default_rng(0)
        # R=30, G=160, B=30  →  G strongly dominant → all green pixels
        arr = np.full((200, 200, 3), [30, 160, 30], dtype=np.float32)
        arr += rng.uniform(-18, 18, arr.shape)   # adds enough variance

        path = _save_rgb(arr, self._path("01_green.jpg"))
        valid, msg, tips = validate_image(path)

        status = "PASS ✓" if valid else f"FAIL ✗  — {msg}"
        print(f"  [1] Solid green image   → {status}")
        self.assertTrue(valid, f"Expected acceptance but got: {msg}")

    # ------------------------------------------------------------------
    # 2. Solid red image — should FAIL
    # ------------------------------------------------------------------
    def test_02_solid_red_fails(self):
        """Red image with no plant-coloured pixels → rejected."""
        rng = np.random.default_rng(1)
        # R=210, G=30, B=30  →  no condition in plant mask can fire
        arr = np.full((200, 200, 3), [210, 30, 30], dtype=np.float32)
        arr += rng.uniform(-18, 18, arr.shape)

        path = _save_rgb(arr, self._path("02_red.jpg"))
        valid, msg, tips = validate_image(path)

        status = "PASS ✓" if valid else f"FAIL ✗  — {msg}"
        print(f"  [2] Solid red image     → {status}")
        self.assertFalse(valid, "Solid-red image should have been rejected")

    # ------------------------------------------------------------------
    # 3. Synthetic tomato leaf — should PASS
    # ------------------------------------------------------------------
    def test_03_tomato_leaf_passes(self):
        """Green leaf base with brownish Early-Blight spots → accepted."""
        rng = np.random.default_rng(2)
        # Leaf base: R=35, G=155, B=40
        arr = np.full((224, 224, 3), [35, 155, 40], dtype=np.float32)
        arr += rng.uniform(-22, 22, arr.shape)

        # Scatter 12 brownish disease spots
        y_idx, x_idx = np.ogrid[:224, :224]
        for _ in range(12):
            cx, cy = rng.integers(20, 204, size=2)
            radius = int(rng.integers(6, 20))
            mask = (x_idx - cx) ** 2 + (y_idx - cy) ** 2 <= radius ** 2
            arr[mask] = [110, 75, 25]   # brown blight spot

        path = _save_rgb(arr, self._path("03_tomato_leaf.jpg"))
        valid, msg, tips = validate_image(path)

        status = "PASS ✓" if valid else f"FAIL ✗  — {msg}"
        print(f"  [3] Real tomato leaf    → {status}")
        self.assertTrue(valid, f"Tomato leaf should be accepted but got: {msg}")

    # ------------------------------------------------------------------
    # 4. Cat-like image — should FAIL
    # ------------------------------------------------------------------
    def test_04_cat_image_fails(self):
        """Neutral grey tones (simulating a cat photo) → rejected."""
        rng = np.random.default_rng(3)
        # R ≈ G ≈ B  (grey, no channel dominant)
        # Base 130-200 keeps B well above 110, preventing 'olive' from firing.
        base = rng.uniform(130, 200, (200, 200)).astype(np.float32)
        arr = np.stack([
            base + rng.uniform(-8, 8, (200, 200)),   # R ≈ base
            base + rng.uniform(-8, 8, (200, 200)),   # G ≈ base
            base + rng.uniform(-8, 8, (200, 200)),   # B ≈ base
        ], axis=-1)

        path = _save_rgb(arr, self._path("04_cat.jpg"))
        valid, msg, tips = validate_image(path)

        status = "PASS ✓" if valid else f"FAIL ✗  — {msg}"
        print(f"  [4] Cat image           → {status}")
        self.assertFalse(valid, "Cat-like grey image should be rejected")

    # ------------------------------------------------------------------
    # 5. Yellowed / diseased leaf — should PASS
    # ------------------------------------------------------------------
    def test_05_yellowed_leaf_passes(self):
        """Yellow-green tones (diseased / yellowing tomato leaf) → accepted."""
        rng = np.random.default_rng(4)
        # R=160, G=185, B=40:  satisfies yellow_green mask (G >> B, G>70, R>60, B<130)
        arr = np.full((200, 200, 3), [160, 185, 40], dtype=np.float32)
        arr += rng.uniform(-18, 18, arr.shape)

        path = _save_rgb(arr, self._path("05_yellow_leaf.jpg"))
        valid, msg, tips = validate_image(path)

        status = "PASS ✓" if valid else f"FAIL ✗  — {msg}"
        print(f"  [5] Yellowed leaf       → {status}")
        self.assertTrue(valid, f"Yellowed leaf should be accepted but got: {msg}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
