"""
Prepare a portrait photo for clean ASCII conversion.

Preferred path (best quality): rembg background removal + CLAHE local contrast.
Fallback path (Pillow only): grayscale + contrast + white matte — good enough for
GitHub avatars and studio-ish photos.

    python scripts/prep_photo.py [input.jpg] [output.png]
"""
import os
import sys

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.jpg")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")


def prep_with_rembg(path):
    import cv2
    import numpy as np
    from rembg import remove

    cut = remove(Image.open(path).convert("RGBA"))
    rgb = np.array(cut.convert("RGB"))
    alpha = np.array(cut.split()[-1])

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.6, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    gray = cv2.convertScaleAbs(gray, alpha=1.05, beta=18)

    mask = (alpha.astype(np.float32) / 255.0)
    mask = cv2.GaussianBlur(mask, (0, 0), 1.0)
    out = gray.astype(np.float32) * mask + 255.0 * (1.0 - mask)
    out = np.clip(out, 0, 255).astype(np.uint8)
    Image.fromarray(out, mode="L").save(OUT)
    return out.shape


def prep_simple(path):
    """Pillow-only prep: square-ish crop toward face center, contrast, white pad."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = max(0, (h - side) // 2 - side // 10)  # bias slightly up for faces
    im = im.crop((left, top, left + side, min(top + side, h)))
    if im.size[1] < side:
        canvas = Image.new("RGB", (side, side), (255, 255, 255))
        canvas.paste(im, (0, (side - im.size[1]) // 2))
        im = canvas

    gray = ImageOps.grayscale(im)
    gray = ImageEnhance.Contrast(gray).enhance(1.45)
    gray = ImageEnhance.Brightness(gray).enhance(1.08)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=2))
    # soft vignette-to-white so corners become spaces in the ASCII ramp
    gray = gray.resize((512, 512), Image.LANCZOS)
    gray.save(OUT)
    return gray.size


if __name__ == "__main__":
    try:
        shape = prep_with_rembg(INP)
        print("wrote", OUT, shape, "(rembg+clahe)")
    except Exception as exc:
        print(f"rembg path unavailable ({exc}); using Pillow fallback")
        shape = prep_simple(INP)
        print("wrote", OUT, shape, "(pillow)")
