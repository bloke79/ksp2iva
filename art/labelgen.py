"""Drawer label atlas for the lander cans: silly stencilled labels on grey plates, 4 x 8 cells.

Usage: python -I labelgen.py <texture_dir>   (writes drawer_labels.png; model_lander.py picks cells by LABELS index)
"""
import os
import sys


LABELS = ["FOOD", "NOT FOOD", "SNACKS", "MORE SNACKS", "SOCKS", "ROCKS", "MORE ROCKS", "ROCKS (DO NOT EAT)",
          "SCIENCE", "SCIENCE?", "MORE SCIENCE", "JUNK", "SPARE BOLTS", "TOOLS", "BOARD GAMES", "BEDS",
          "SPARE PARTS", "DUCT TAPE", "JEB'S SNACKS", "EMERGENCY SNACKS", "MYSTERY", "FIRST AID", "SPACE", "PARTS",
          "WATER", "OXYGEN?", "MANUALS (UNREAD)", "SAMPLES", "DO NOT OPEN", "HELMETS", "MAPS", "SPOONS"]
COLS, ROWS = 4, 8
CW, CH = 512, 128


def font(sz):
    from PIL import ImageFont
    for f in ("C:/Windows/Fonts/bahnschrift.ttf", "C:/Windows/Fonts/arialbd.ttf"):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def main(out_dir):
    from PIL import Image, ImageDraw   # here, so Blender can import LABELS without Pillow
    img = Image.new("RGB", (COLS * CW, ROWS * CH), (205, 207, 210))
    d = ImageDraw.Draw(img)
    for i, t in enumerate(LABELS):
        x0, y0 = (i % COLS) * CW, (i // COLS) * CH
        d.rectangle([x0, y0, x0 + CW - 1, y0 + CH - 1], fill=(214, 216, 219), outline=(70, 72, 76), width=6)
        d.rectangle([x0 + 12, y0 + 12, x0 + CW - 13, y0 + CH - 13], outline=(150, 152, 156), width=2)
        for sx in (x0 + 26, x0 + CW - 26):   # rivets
            d.ellipse([sx - 6, y0 + CH / 2 - 6, sx + 6, y0 + CH / 2 + 6], fill=(120, 122, 126))
        sz = 64
        while sz > 20:
            f = font(sz)
            if d.textlength(t, font=f) < CW - 90:
                break
            sz -= 2
        tw = d.textlength(t, font=f)
        d.text((x0 + CW / 2 - tw / 2, y0 + CH / 2 - sz * 0.62), t, fill=(38, 40, 44), font=f)
    path = os.path.join(out_dir, "drawer_labels.png")
    img.save(path)
    print("wrote", path)


if __name__ == "__main__":
    main(sys.argv[1])
