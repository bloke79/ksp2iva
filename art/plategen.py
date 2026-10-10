"""Draws an interior's name plate (same layout as texgen.py's plate) with Windows fonts.

Usage: python -I plategen.py <out.png> "<TITLE>" "<subtitle>"
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

OUT, TITLE, SUB = sys.argv[1], sys.argv[2], sys.argv[3]
FONTS = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")


def font(names, size):
    for n in names:
        try:
            return ImageFont.truetype(os.path.join(FONTS, n), size)
        except OSError:
            continue
    return ImageFont.load_default()


w, h = 1024, 256
img = Image.new("RGB", (w, h), (200, 198, 190))
d = ImageDraw.Draw(img)
d.rectangle([10, 10, w - 11, h - 11], outline=(40, 40, 40), width=6)
title_font = font(["bahnschrift.ttf", "arialbd.ttf"], 74)
if hasattr(title_font, "set_variation_by_name"):
    try:
        title_font.set_variation_by_name("Bold")
    except Exception:
        pass
d.text((w / 2, h * 0.38), TITLE, fill=(30, 30, 30), font=title_font, anchor="mm")
d.text((w / 2, h * 0.72), SUB, fill=(60, 60, 60), font=font(["ARIALNB.TTF", "arialbd.ttf"], 38), anchor="mm")
for x in (34, w - 34):
    for y in (34, h - 34):
        d.ellipse([x - 10, y - 10, x + 10, y + 10], fill=(120, 120, 120))
os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
img.save(OUT)
print("wrote", OUT)
