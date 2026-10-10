"""Extra textures for the Mk1 (1v) interior: insulation blanket and periscope view.

Usage: python -I texgen_mk1.py <out_dir>
Writes blanket_color.png, blanket_normal.png, periscope.png.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
FONTS = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")


def font(name, size):
    try:
        return ImageFont.truetype(os.path.join(FONTS, name), size)
    except OSError:
        return ImageFont.load_default()


def blanket(size=1024, cols=3, rows=4):
    """Aluminised insulation blanket: large crinkled foil panels with soft stitched seams and quilting lines."""
    rng = np.random.default_rng(7)
    y, x = np.mgrid[0:size, 0:size].astype(np.float32) / size

    def smooth_noise(n, interp=Image.BICUBIC):
        return np.asarray(Image.fromarray((rng.random((n, n)) * 255).astype(np.uint8)).resize((size, size), interp), np.float32) / 255

    crinkle = smooth_noise(160, Image.BILINEAR) * 0.6 + smooth_noise(64) * 0.4      # fine foil wrinkles
    billow = smooth_noise(6)                                                        # broad puffiness
    # panel grid (texture tiles seamlessly at these counts)
    px, py = x * cols, y * rows
    fx, fy = px - np.floor(px), py - np.floor(py)
    pid = (np.floor(px) + np.floor(py) * cols).astype(int)
    tint = rng.uniform(-0.035, 0.035, cols * rows)[pid]
    seam_d = np.minimum(np.minimum(fx, 1 - fx) / cols, np.minimum(fy, 1 - fy) / rows)   # distance to a seam (texture units)
    seam = np.clip(1 - seam_d / 0.006, 0, 1)
    pillow = np.clip(seam_d / 0.05, 0, 1) ** 0.5                                    # panels bulge away from the seams
    # quilting: diagonal stitch lines every ~1/6 of a panel
    q = (np.abs(((px + py * cols / rows) * 3) % 1 - 0.5) < 0.012) | (np.abs(((px - py * cols / rows) * 3) % 1 - 0.5) < 0.012)
    stitch = q.astype(np.float32) * (1 - seam)
    base = 0.50 + tint + 0.045 * (crinkle - 0.5) + 0.06 * (billow - 0.5) + 0.05 * pillow
    base = base * (1 - 0.35 * seam) * (1 - 0.18 * stitch)
    col = np.stack([base * 0.95, base * 0.96, base * 0.99], -1)
    Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, "blanket_color.png"))
    h = pillow * 0.8 + crinkle * 0.22 + billow * 0.3 - stitch * 0.25 - seam * 0.5
    gy, gx = np.gradient(h)
    n = np.stack([-gx * 18, -gy * 18, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8)).save(os.path.join(OUT, "blanket_normal.png"))
    print("wrote blanket_color.png, blanket_normal.png")


def periscope(size=512):
    """Wide-angle periscope view: Kerbin's limb, clouds, black sky, reticle and drift lines, inside a dark ring."""
    img = Image.new("RGB", (size, size), (2, 3, 6))
    px = np.zeros((size, size, 3), np.float32)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    cx = cy = size / 2
    r = np.hypot(xx - cx, yy - cy) / (size / 2)
    # fisheye: planet occupies the lower part with a curved horizon
    horizon = cy * 0.55 + ((xx - cx) / size) ** 2 * size * 0.9
    planet = yy > horizon
    rng = np.random.default_rng(3)
    cloud = np.asarray(Image.fromarray((rng.random((32, 32)) * 255).astype(np.uint8)).resize((size, size), Image.BICUBIC), np.float32) / 255
    cloud2 = np.asarray(Image.fromarray((rng.random((96, 96)) * 255).astype(np.uint8)).resize((size, size), Image.BICUBIC), np.float32) / 255
    c = np.clip((cloud * 0.7 + cloud2 * 0.3 - 0.45) * 3, 0, 1)
    ocean = np.array([0.05, 0.22, 0.52])
    land = np.array([0.18, 0.36, 0.14])
    landmask = np.clip((cloud2 - 0.62) * 8, 0, 1)
    surf = ocean * (1 - landmask[..., None]) + land * landmask[..., None]
    surf = surf * (1 - c[..., None]) + np.array([0.92, 0.94, 0.97]) * c[..., None]
    px[planet] = surf[planet]
    # atmosphere glow along the limb
    d = np.abs(yy - horizon)
    glow = np.exp(-d / (size * 0.02))
    px += glow[..., None] * np.array([0.25, 0.5, 1.0]) * 0.8
    # stars in the black sky
    stars = (rng.random((size, size)) > 0.9975) & ~planet
    px[stars] = 0.9
    # vignette and circular aperture
    px *= np.clip(1.15 - r ** 3, 0, 1)[..., None]
    px[r > 0.97] = 0.02
    img = Image.fromarray((np.clip(px, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
    d = ImageDraw.Draw(img)
    green = (120, 255, 150)
    d.line([(cx, cy - size * 0.36), (cx, cy + size * 0.36)], fill=green, width=2)
    d.line([(cx - size * 0.36, cy), (cx + size * 0.36, cy)], fill=green, width=2)
    for k in range(1, 4):
        rr = size * 0.11 * k
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=green, width=1)
    for k in range(-3, 4):  # drift lines
        x = cx + k * size * 0.08
        d.line([(x, cy + size * 0.05), (x, cy + size * 0.30)], fill=(90, 200, 120), width=1)
    d.text((cx + size * 0.05, cy - size * 0.33), "RETRO VIEW", fill=green, font=font("consolab.ttf", 22))
    d.text((cx - size * 0.33, cy + size * 0.30), "DRIFT", fill=green, font=font("consolab.ttf", 18))
    d.ellipse([4, 4, size - 5, size - 5], outline=(20, 22, 25), width=10)
    img.save(os.path.join(OUT, "periscope.png"))
    print("wrote periscope.png")


blanket()
periscope()
