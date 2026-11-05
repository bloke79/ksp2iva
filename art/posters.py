"""Crew posters for the cabin walls, drawn entirely here (no game art): whimsical travel posters, safety notices and
in-jokes from a kerbal space programme. Writes poster_<name>.png (512 x 768) into the given folder.

Usage: python -I posters.py <out_dir> [name ...]
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 512, 768
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
CREAM = (245, 235, 210)


def font(sz):
    for f in ("C:/Windows/Fonts/impact.ttf", "C:/Windows/Fonts/bahnschrift.ttf", "C:/Windows/Fonts/arialbd.ttf"):
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            continue
    return ImageFont.load_default()


def title(d, text, y, sz, fill=CREAM):
    f = font(sz)
    d.text(((W - d.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)


def stars(d, rng, n=140):
    for _ in range(n):
        x, y = rng.integers(0, W), rng.integers(0, H)
        r = rng.choice([0, 0, 0, 1])
        v = int(rng.integers(150, 255))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(v, v, v))


def frame(img, col=CREAM):
    ImageDraw.Draw(img).rectangle([6, 6, W - 7, H - 7], outline=col, width=4)
    return img


def sphere(d, cx, cy, r, col, lx=0.35, ly=0.3):
    for k in range(int(r), 0, -2):
        t = k / r
        c = tuple(int(min(255, v * (0.55 + 0.6 * (1 - t)))) for v in col)
        ox, oy = int(-lx * (1 - t) * r), int(-ly * (1 - t) * r)
        d.ellipse([cx - k + ox, cy - k + oy, cx + k + ox, cy + k + oy], fill=c)


def rocket(d, x, y, s, body=(235, 225, 205), fins=(200, 70, 50), flame=True):
    d.polygon([(x, y - 70 * s), (x - 16 * s, y - 30 * s), (x + 16 * s, y - 30 * s)], fill=body)
    d.rectangle([x - 16 * s, y - 30 * s, x + 16 * s, y + 40 * s], fill=body)
    d.polygon([(x - 16 * s, y + 10 * s), (x - 32 * s, y + 46 * s), (x - 16 * s, y + 40 * s)], fill=fins)
    d.polygon([(x + 16 * s, y + 10 * s), (x + 32 * s, y + 46 * s), (x + 16 * s, y + 40 * s)], fill=fins)
    d.ellipse([x - 7 * s, y - 22 * s, x + 7 * s, y - 8 * s], fill=(90, 150, 200))
    if flame:
        d.polygon([(x - 10 * s, y + 40 * s), (x + 10 * s, y + 40 * s), (x, y + 95 * s)], fill=(250, 170, 50))


GREEN, GREEN_DK, GREEN_SH = (176, 208, 64), (96, 130, 30), (150, 182, 50)
SUIT, SUIT_DK, SUIT_LN, RED_TRIM = (238, 236, 230), (150, 150, 146), (200, 198, 192), (200, 60, 50)
HAIR = (78, 52, 34)


def kerbal(d, cx, cy, r, mood="grin", helmet=True, look=(0, 0), body=False, hair=None):
    """A cartoon kerbal, our own flat drawing after the game's look: a tall rounded-rectangle head, big round googly
    eyes towards the sides, a simple curved smile; a big bubble helmet with a white rim and red trim; a stubby white
    suit with big gloves and boots. hair: None, 'bob' or 'slick'. r is the head's half-width; (cx, cy) its centre."""
    lw = max(2, int(r * 0.06))
    hh = r * 1.2                                    # half-height of the head
    hr = r * 1.75                                   # helmet radius
    hcy = cy - r * 0.05
    if body:
        ty = hcy + hr * 0.85 if helmet else cy + hh - r * 0.15   # top of the suit: under the helmet ring, or the chin
        for sx in (-1, 1):                          # legs and boots
            lx = cx + sx * r * 0.55
            d.rounded_rectangle([lx - r * 0.42, ty + r * 1.2, lx + r * 0.42, ty + r * 1.95], radius=r * 0.2, fill=SUIT, outline=SUIT_DK, width=lw)
            d.rounded_rectangle([lx - r * 0.5, ty + r * 1.8, lx + r * 0.5, ty + r * 2.15], radius=r * 0.15, fill=(60, 62, 66))
            d.line([(lx - r * 0.4, ty + r * 1.55), (lx + r * 0.4, ty + r * 1.55)], fill=RED_TRIM, width=int(r * 0.07))
        d.rounded_rectangle([cx - r * 1.25, ty, cx + r * 1.25, ty + r * 1.45], radius=r * 0.45, fill=SUIT, outline=SUIT_DK, width=lw)
        for sx in (-1, 1):                          # arms and big gloves
            sh = (cx + sx * r * 1.1, ty + r * 0.35)
            hand = (cx + sx * r * 1.6, ty + r * 1.05)
            d.line([sh, hand], fill=SUIT, width=int(r * 0.55))
            d.line([sh, hand], fill=SUIT_DK, width=1)
            d.ellipse([hand[0] - r * 0.36, hand[1] - r * 0.3, hand[0] + r * 0.36, hand[1] + r * 0.4], fill=SUIT, outline=SUIT_DK, width=lw)
        d.rounded_rectangle([cx - r * 0.45, ty + r * 0.35, cx + r * 0.45, ty + r * 0.85], radius=r * 0.08, fill=(72, 76, 82))
        for k, col in enumerate(((230, 70, 60), (250, 200, 70), (90, 200, 120))):
            bx = cx - r * 0.22 + k * r * 0.22
            d.ellipse([bx - r * 0.06, ty + r * 0.54, bx + r * 0.06, ty + r * 0.66], fill=col)
        d.ellipse([cx - r * 1.2, ty - r * 0.2, cx + r * 1.2, ty + r * 0.3], fill=SUIT_LN, outline=SUIT_DK, width=lw)   # neck ring
    if helmet:                                      # the inside of the bubble behind the head
        d.ellipse([cx - hr, hcy - hr, cx + hr, hcy + hr], fill=(70, 84, 96))
    # head: a tall rounded rectangle, shaded down one side
    d.rounded_rectangle([cx - r, cy - hh, cx + r, cy + hh], radius=r * 0.5, fill=GREEN, outline=GREEN_DK, width=lw)
    d.rounded_rectangle([cx + r * 0.45, cy - hh + r * 0.25, cx + r - lw, cy + hh - r * 0.25], radius=r * 0.3, fill=GREEN_SH)
    if hair == "bob":
        d.rounded_rectangle([cx - r * 1.08, cy - hh - r * 0.12, cx + r * 1.08, cy - hh + r * 0.5], radius=r * 0.45, fill=HAIR)
        d.rounded_rectangle([cx - r * 1.1, cy - hh + r * 0.1, cx - r * 0.75, cy + r * 0.2], radius=r * 0.2, fill=HAIR)
        d.rounded_rectangle([cx + r * 0.75, cy - hh + r * 0.1, cx + r * 1.1, cy + r * 0.2], radius=r * 0.2, fill=HAIR)
    elif hair == "slick":
        d.rounded_rectangle([cx - r * 1.0, cy - hh - r * 0.15, cx + r * 1.0, cy - hh + r * 0.35], radius=r * 0.35, fill=HAIR)
    # eyes: big round googly discs, set out towards the edges, one a little higher than the other
    for sx, dy in ((-1, 0.0), (1, -0.06)):
        ex, ey = cx + sx * r * 0.5, cy - r * (0.2 - dy)
        er = r * 0.36
        d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(252, 252, 250), outline=(60, 60, 60), width=max(1, lw // 2))
        pr = r * 0.1
        px, py = ex + look[0] * er * 0.45, ey + look[1] * er * 0.45
        d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(20, 20, 20))
    # mouth
    if mood == "grin":
        d.chord([cx - r * 0.62, cy + r * 0.18, cx + r * 0.62, cy + r * 0.82], 10, 170, fill=(70, 25, 30), outline=(60, 30, 20), width=lw)
        d.chord([cx - r * 0.3, cy + r * 0.56, cx + r * 0.3, cy + r * 0.84], 200, 340, fill=(225, 110, 120))
    elif mood == "smile":
        d.arc([cx - r * 0.6, cy + r * 0.05, cx + r * 0.6, cy + r * 0.62], 25, 155, fill=(50, 40, 20), width=lw)
    elif mood == "worried":
        d.line([(cx - r * 0.45, cy + r * 0.55), (cx - r * 0.15, cy + r * 0.47), (cx + r * 0.15, cy + r * 0.55), (cx + r * 0.45, cy + r * 0.47)],
               fill=(60, 30, 20), width=lw)
    elif mood == "oh":
        d.ellipse([cx - r * 0.2, cy + r * 0.3, cx + r * 0.2, cy + r * 0.78], fill=(70, 25, 30), outline=(60, 30, 20), width=lw)
    if helmet:   # bubble rim with red trim, little lamps, and a glint on the glass
        d.ellipse([cx - hr, hcy - hr, cx + hr, hcy + hr], outline=(245, 245, 242), width=max(3, int(r * 0.16)))
        for sx in (-1, 1):
            a = math.radians(-50 * sx)
            tx, ty_ = cx + hr * math.sin(-a) * -1, hcy - hr * math.cos(a)
            d.rounded_rectangle([tx - r * 0.2, ty_ - r * 0.12, tx + r * 0.2, ty_ + r * 0.12], radius=r * 0.06, fill=RED_TRIM)
            d.ellipse([cx + sx * hr - r * 0.13, hcy - r * 0.3, cx + sx * hr + r * 0.13, hcy - r * 0.04], fill=(70, 72, 76))
        d.arc([cx - hr * 0.86, hcy - hr * 0.86, cx + hr * 0.86, hcy + hr * 0.86], 205, 245, fill=(255, 255, 255), width=max(2, int(r * 0.08)))


def crew(rng):
    img = Image.new("RGB", (W, H), (225, 120, 40))
    d = ImageDraw.Draw(img)
    for k in range(12):
        d.pieslice([-W, -H // 2, 2 * W, int(H * 1.4)], k * 30, k * 30 + 15, fill=(235, 145, 60))
    kerbal(d, W // 2, int(H * 0.38), 68, "grin", helmet=True, body=True, hair="bob")
    title(d, "KERBAL", 26, 92, (30, 30, 40))
    title(d, "ASTRONAUT CORPS", 128, 38, (30, 30, 40))
    title(d, "FOR SCIENCE!", H - 100, 64, (250, 245, 230))
    return frame(img)


def boosters(rng):
    img = Image.new("RGB", (W, H), (238, 214, 160))
    d = ImageDraw.Draw(img)
    for k in range(14):
        d.pieslice([-W, int(H * 0.1), 2 * W, int(H * 1.6)], k * 26, k * 26 + 13, fill=(244, 226, 180))
    cx, cy = W // 2, int(H * 0.56)
    for dx in (-150, -114, -78, -42, 42, 78, 114, 150):   # an unreasonable number of boosters
        by = cy + 40 + abs(dx) * 0.4
        d.rectangle([cx + dx - 14, by - 120, cx + dx + 14, by + 60], fill=(235, 235, 235), outline=(60, 60, 60), width=3)
        d.polygon([(cx + dx - 14, by - 120), (cx + dx + 14, by - 120), (cx + dx, by - 150)], fill=(200, 70, 50))
        d.polygon([(cx + dx - 10, by + 60), (cx + dx + 10, by + 60), (cx + dx, by + 120)], fill=(250, 170, 50))
    rocket(d, cx, cy - 40, 2.0)
    kerbal(d, cx, cy - 92, 11, "grin", helmet=False)
    title(d, "MOAR", 30, 96, (60, 40, 30))
    title(d, "BOOSTERS", 120, 96, (200, 70, 50))
    title(d, "IT WORKED LAST TIME*", H - 112, 34, (60, 40, 30))
    title(d, "*IT DID NOT WORK LAST TIME", H - 66, 22, (120, 80, 60))
    return frame(img, (60, 40, 30))


def eve(rng):
    img = Image.new("RGB", (W, H), (24, 10, 34))
    d = ImageDraw.Draw(img)
    stars(d, rng)
    sphere(d, W // 2, int(H * 0.5), W * 0.38, (170, 90, 210))
    for k in range(5):
        y = int(H * 0.5) - 120 + k * 60
        d.arc([W // 2 - 190, y - 30, W // 2 + 190, y + 30], 200, 340, fill=(205, 160, 230), width=4)
    title(d, "EVE", 40, 130, (230, 200, 255))
    title(d, "COME FOR THE PURPLE.", H - 140, 38, (230, 200, 255))
    title(d, "STAY FOREVER.", H - 92, 38, (255, 230, 120))
    return frame(img)


def jool(rng):
    img = Image.new("RGB", (W, H), (8, 16, 12))
    d = ImageDraw.Draw(img)
    stars(d, rng)
    sphere(d, W // 2 + 40, int(H * 0.55), W * 0.42, (120, 200, 60))
    for k in range(6):
        y = int(H * 0.55) - 150 + k * 55
        d.arc([W // 2 + 40 - 215, y - 22, W // 2 + 40 + 215, y + 22], 190, 350, fill=(90, 160, 50), width=6)
    for (mx, my, mr, col) in ((70, 260, 22, (210, 200, 170)), (110, 420, 16, (170, 160, 150)), (60, 560, 28, (120, 170, 200)),
                              (150, 640, 12, (200, 150, 110)), (40, 340, 9, (190, 190, 190))):
        sphere(d, mx, my, mr, col)
    title(d, "JOOL", 30, 120, (200, 245, 150))
    title(d, "SYSTEM TOURS", 160, 40, (200, 245, 150))
    title(d, "FIVE MOONS. NO SURFACE.", H - 112, 32, (230, 240, 220))
    title(d, "PLEASE DO NOT TRY TO LAND", H - 68, 22, (200, 230, 170))
    return frame(img)


def minmus(rng):
    img = Image.new("RGB", (W, H), (14, 22, 30))
    d = ImageDraw.Draw(img)
    stars(d, rng)
    sphere(d, W // 2, int(H * 0.5), W * 0.34, (150, 230, 200))
    for _ in range(6):
        x, y = W // 2 + rng.integers(-110, 110), int(H * 0.5) + rng.integers(-110, 110)
        d.ellipse([x - 40, y - 18, x + 40, y + 18], fill=(200, 250, 230))
    # a scoop of ice cream sitting on top
    d.polygon([(W // 2 - 26, int(H * 0.5) - 190), (W // 2 + 26, int(H * 0.5) - 190), (W // 2, int(H * 0.5) - 120)], fill=(210, 160, 100))
    title(d, "MINMUS", 40, 110, (190, 255, 225))
    title(d, "NOW IN MINT", H - 140, 46, (255, 255, 255))
    title(d, "DO NOT LICK THE SURFACE", H - 80, 26, (190, 255, 225))
    return frame(img)


def staging(rng):
    img = Image.new("RGB", (W, H), (32, 60, 92))
    d = ImageDraw.Draw(img)
    for x in range(0, W, 32):
        d.line([(x, 0), (x, H)], fill=(42, 74, 108))
    for y in range(0, H, 32):
        d.line([(0, y), (W, y)], fill=(42, 74, 108))
    cx = W // 2
    for top, hh, num in ((-60, 40, "4"), (30, 100, "3"), (130, 100, "2"), (230, 110, "1")):
        y0 = 300 + top
        d.rectangle([cx - 46, y0, cx + 46, y0 + hh - 6], outline=(235, 240, 250), width=4)
        d.ellipse([cx + 70, y0 + hh / 2 - 24, cx + 118, y0 + hh / 2 + 24], outline=(250, 200, 80), width=4)
        f = font(34)
        d.text((cx + 94 - d.textlength(num, font=f) / 2, y0 + hh / 2 - 22), num, font=f, fill=(250, 200, 80))
    d.polygon([(cx - 46, 240), (cx + 46, 240), (cx, 176)], outline=(235, 240, 250), width=4)
    d.text((cx - 160, 210), "?!", font=font(70), fill=(250, 120, 90))   # the parachute is in stage 1. again.
    title(d, "CHECK YOUR", 30, 60, (235, 240, 250))
    title(d, "STAGING", 92, 60, (250, 200, 80))
    title(d, "BEFORE YOU PRESS SPACE", H - 70, 30, (235, 240, 250))
    return frame(img, (235, 240, 250))


def struts(rng):
    img = Image.new("RGB", (W, H), (232, 196, 60))
    d = ImageDraw.Draw(img)
    cx = W // 2
    d.rectangle([cx - 40, 240, cx + 40, 600], fill=(240, 240, 240), outline=(30, 30, 30), width=4)
    for k in range(9):
        y0 = 260 + k * 38
        d.line([(cx - 40, y0), (cx - 140, y0 + 60)], fill=(30, 30, 30), width=6)
        d.line([(cx + 40, y0), (cx + 140, y0 + 60)], fill=(30, 30, 30), width=6)
        d.line([(cx - 140, y0 + 60), (cx + 140, y0 + 60)], fill=(30, 30, 30), width=3)
    d.rectangle([cx - 160, 250, cx - 130, 640], fill=(240, 240, 240), outline=(30, 30, 30), width=4)
    d.rectangle([cx + 130, 250, cx + 160, 640], fill=(240, 240, 240), outline=(30, 30, 30), width=4)
    title(d, "WHEN IN DOUBT", 40, 64, (30, 30, 30))
    title(d, "ADD STRUTS", 120, 84, (180, 40, 30))
    title(d, "THEN ADD MORE STRUTS", H - 90, 36, (30, 30, 30))
    return frame(img, (30, 30, 30))


def mun_holiday(rng):
    img = Image.new("RGB", (W, H), (12, 12, 28))
    d = ImageDraw.Draw(img)
    stars(d, rng, 120)
    sphere(d, 400, 150, 60, (60, 120, 200), lx=-0.3)                        # Kerbin hanging in the sky
    d.rectangle([0, 470, W, H], fill=(150, 148, 142))                       # the grey beach
    for _ in range(14):
        x, y, r = rng.integers(0, W), rng.integers(480, H - 40), rng.integers(8, 30)
        d.ellipse([x - r, y - r * 0.35, x + r, y + r * 0.35], fill=(128, 126, 120))
    # deckchair and umbrella
    d.line([(150, 640), (250, 540)], fill=(80, 60, 40), width=8)
    d.line([(250, 640), (170, 560)], fill=(80, 60, 40), width=8)
    d.polygon([(165, 560), (255, 540), (230, 620), (150, 640)], fill=(220, 80, 70))
    d.line([(330, 650), (330, 420)], fill=(200, 200, 200), width=6)
    d.pieslice([230, 360, 430, 480], 180, 360, fill=(250, 210, 70))
    kerbal(d, 203, 505, 18, "smile", helmet=True, body=True, hair="slick")
    title(d, "HOLIDAY ON THE MUN", 40, 58)
    title(d, "NO ATMOSPHERE. NO CROWDS.", H - 110, 30, (40, 30, 30))
    title(d, "BRING YOUR OWN AIR", H - 66, 26, (60, 40, 40))
    return frame(img)


def lost_part(rng):
    img = Image.new("RGB", (W, H), (240, 236, 222))
    d = ImageDraw.Draw(img)
    title(d, "LOST:", 30, 90, (30, 30, 30))
    title(d, "ONE (1) PART", 130, 50, (30, 30, 30))
    d.rectangle([126, 220, 386, 470], outline=(30, 30, 30), width=4)
    # the missing part: a lonely fuel tank, drawn as a photo
    d.rectangle([136, 230, 376, 460], fill=(120, 150, 180))
    d.rectangle([216, 260, 296, 430], fill=(235, 235, 235), outline=(40, 40, 40), width=3)
    d.line([(216, 300), (296, 300)], fill=(40, 40, 40), width=2)
    d.line([(216, 390), (296, 390)], fill=(40, 40, 40), width=2)
    title(d, "LAST SEEN DURING STAGING", 495, 30, (30, 30, 30))
    title(d, "ANSWERS TO 'WHERE DID IT GO'", 540, 26, (90, 90, 90))
    title(d, "REWARD: SNACKS", 600, 40, (180, 50, 40))
    for k in range(7):   # tear-off tabs
        x = 30 + k * 66
        d.rectangle([x, H - 80, x + 56, H - 14], outline=(80, 80, 80), width=2)
        d.text((x + 10, H - 72), "VAB", font=font(18), fill=(60, 60, 60))
    return frame(img, (60, 60, 60))


def safety_third(rng):
    img = Image.new("RGB", (W, H), (250, 210, 40))
    d = ImageDraw.Draw(img)
    for k in range(-H, W, 60):   # hazard stripes, top and bottom
        d.polygon([(k, 0), (k + 30, 0), (k + 30 + 40, 40), (k + 40, 40)], fill=(30, 30, 30))
        d.polygon([(k, H - 40), (k + 30, H - 40), (k + 30 + 40, H), (k + 40, H)], fill=(30, 30, 30))
    title(d, "SAFETY", 60, 110, (30, 30, 30))
    title(d, "THIRD", 170, 110, (190, 40, 30))
    kerbal(d, W // 2, 380, 62, "oh", helmet=False, look=(0, 1), body=True)
    # a lit SRB right in front of the face
    d.rectangle([W // 2 - 26, 520, W // 2 + 26, 650], fill=(235, 235, 235), outline=(30, 30, 30), width=4)
    d.polygon([(W // 2 - 18, 520), (W // 2 + 18, 520), (W // 2, 470)], fill=(250, 150, 40))
    title(d, "(SCIENCE IS FIRST. FUN IS SECOND.)", H - 92, 22, (30, 30, 30))
    return img


def missing_kerbal(rng):
    img = Image.new("RGB", (W, H), (236, 232, 220))
    d = ImageDraw.Draw(img)
    title(d, "HAVE YOU SEEN", 30, 54, (30, 30, 30))
    title(d, "THIS KERBAL?", 92, 54, (180, 40, 30))
    d.rectangle([116, 170, 396, 450], fill=(200, 210, 220), outline=(30, 30, 30), width=4)
    kerbal(d, W // 2, 315, 50, "smile", helmet=True, look=(1, -1))
    title(d, "LAST SEEN: EVA, 'JUST POPPING OUT'", 470, 24, (30, 30, 30))
    title(d, "ORBIT: DECAYING (PROBABLY)", 510, 24, (30, 30, 30))
    title(d, "DO NOT FEED SNACKS", 560, 36, (180, 40, 30))
    title(d, "HE WILL FOLLOW YOU HOME", 610, 26, (90, 90, 90))
    return frame(img, (60, 60, 60))


def whiteboard(rng):
    """The crew's whiteboard (768 x 512): a scribbled Mun transfer, a snack rota, a doodle and a safety counter."""
    w, h = 768, 512
    img = Image.new("RGB", (w, h), (246, 247, 244))
    d = ImageDraw.Draw(img)
    try:
        hand = lambda sz: ImageFont.truetype("C:/Windows/Fonts/Inkfree.ttf", sz)
        hand(10)
    except OSError:
        hand = font
    BLUE, RED, GRN, BLK = (30, 70, 170), (190, 40, 40), (30, 130, 60), (40, 40, 45)
    for _ in range(30):   # ghosts of old scribbles
        x, y = rng.integers(0, w), rng.integers(0, h)
        d.line([(x, y), (x + rng.integers(20, 120), y + rng.integers(-8, 8))], fill=(232, 234, 230), width=3)

    def wob(pts, col, width=4):
        q = [(x + rng.normal(0, 1.2), y + rng.normal(0, 1.2)) for x, y in pts]
        d.line(q, fill=col, width=width, joint="curve")

    d.text((24, 14), "MUN MISSION v7", font=hand(40), fill=BLUE)
    d.line([(24, 62), (300, 60)], fill=BLUE, width=3)
    # transfer diagram
    cx, cy = 200, 280
    wob([(cx + 30 * math.cos(t / 20 * 6.283), cy + 30 * math.sin(t / 20 * 6.283)) for t in range(21)], GRN, 5)
    d.text((cx - 28, cy - 12), "K", font=hand(26), fill=GRN)
    wob([(cx + 150 * math.cos(t / 60 * 6.283), cy + 150 * math.sin(t / 60 * 6.283)) for t in range(61)], BLK, 2)
    mx, my = cx + 150 * math.cos(-0.6), cy + 150 * math.sin(-0.6)
    wob([(mx + 14 * math.cos(t / 14 * 6.283), my + 14 * math.sin(t / 14 * 6.283)) for t in range(15)], BLK, 4)
    d.text((mx + 16, my - 30), "Mun", font=hand(24), fill=BLK)
    for k in range(0, 40, 2):   # dashed transfer ellipse
        a0, a1 = math.pi * k / 40, math.pi * (k + 1) / 40
        p0 = (cx - 45 + 100 * math.cos(math.pi - a0) * -1, cy + 70 * math.sin(math.pi - a0) * -1)
        p1 = (cx - 45 + 100 * math.cos(math.pi - a1) * -1, cy + 70 * math.sin(math.pi - a1) * -1)
        d.line([p0, p1], fill=RED, width=4)
    d.text((cx - 60, cy + 92), "dv = ???", font=hand(34), fill=RED)
    d.text((cx + 70, cy + 100), "(Bill: 'enough')", font=hand(22), fill=RED)
    # snack rota
    x0 = 430
    d.text((x0, 20), "SNACK ROTA", font=hand(32), fill=BLK)
    for k, (who, what) in enumerate((("Jeb", "ALL OF THEM"), ("Bill", "crackers"), ("Bob", "crackers?"), ("Val", "fuel bar"))):
        y = 66 + k * 38
        d.text((x0, y), f"{who} - {what}", font=hand(26), fill=BLUE if k else RED)
        d.line([(x0, y + 34), (x0 + 300, y + 34)], fill=(200, 205, 215), width=1)
    d.line([(x0 + 70, 80), (x0 + 220, 80)], fill=RED, width=3)   # someone crossed Jeb's out
    # days since last explosion
    bx, by = 450, 250
    d.rectangle([bx, by, bx + 290, by + 110], outline=BLK, width=4)
    d.text((bx + 12, by + 8), "DAYS SINCE LAST", font=hand(26), fill=BLK)
    d.text((bx + 12, by + 38), "EXPLOSION:", font=hand(26), fill=BLK)
    d.text((bx + 190, by + 22), "0", font=hand(80), fill=RED)
    d.text((bx + 186, by + 4), "3", font=hand(40), fill=(215, 215, 215))   # the old number, half rubbed out
    # doodled kerbal
    kx, ky = 640, 440
    d.rounded_rectangle([kx - 26, ky - 34, kx + 26, ky + 34], radius=16, outline=GRN, width=4)
    for ex in (-11, 11):
        d.ellipse([kx + ex - 9, ky - 20, kx + ex + 9, ky - 2], outline=BLK, width=3)
        d.ellipse([kx + ex - 2, ky - 13, kx + ex + 3, ky - 8], fill=BLK)
    d.arc([kx - 16, ky - 4, kx + 16, ky + 22], 20, 160, fill=BLK, width=3)
    d.text((kx - 110, ky - 14), "me ->", font=hand(26), fill=GRN)
    # don't touch
    d.text((40, 440), "DO NOT TOUCH THE", font=hand(28), fill=RED)
    d.text((40, 472), "BIG RED BUTTON (Jeb)", font=hand(28), fill=RED)
    return img


def _board():
    w, h = 768, 512
    img = Image.new("RGB", (w, h), (246, 247, 244))
    d = ImageDraw.Draw(img)

    def hand(sz):
        try:
            return ImageFont.truetype("C:/Windows/Fonts/Inkfree.ttf", sz)
        except OSError:
            return font(sz)
    return img, d, hand, (30, 70, 170), (190, 40, 40), (30, 130, 60), (40, 40, 45)


def whiteboard_lab(rng):
    img, d, hand, BLUE, RED, GRN, BLK = _board()
    d.text((24, 14), "EXPERIMENT LOG", font=hand(40), fill=BLUE)
    d.line([(24, 62), (330, 60)], fill=BLUE, width=3)
    rows = (("Goo #3", "it moved", RED), ("Seed tray B", "sprouted!", GRN), ("Materials bay", "DO NOT OPEN", RED),
            ("Crystal growth", "pretty", BLUE), ("Bob's sandwich", "day 41", BLK))
    for k, (what, note, col) in enumerate(rows):
        y = 80 + k * 46
        d.text((30, y), what, font=hand(28), fill=BLK)
        d.text((250, y), note, font=hand(28), fill=col)
        d.line([(28, y + 40), (430, y + 40)], fill=(205, 210, 220), width=1)
    # crop growth chart
    x0, y0 = 470, 300
    d.line([(x0, y0), (x0, 80), ], fill=BLK, width=3)
    d.line([(x0, y0), (740, y0)], fill=BLK, width=3)
    for k, hgt in enumerate((30, 55, 70, 120, 190)):
        d.rectangle([x0 + 20 + k * 52, y0 - hgt, x0 + 56 + k * 52, y0], outline=GRN, width=4)
    d.text((x0 + 10, 40), "TOMATO HEIGHT", font=hand(26), fill=GRN)
    d.text((x0 + 200, y0 + 8), "weeks", font=hand(22), fill=BLK)
    d.text((30, 330), "MYSTERY GOO:", font=hand(34), fill=RED)
    d.text((30, 372), "DO NOT TASTE (again)", font=hand(34), fill=RED)
    d.text((30, 440), "- signed, management", font=hand(24), fill=BLK)
    d.ellipse([560, 360, 700, 470], outline=GRN, width=4)   # a petri dish with something in it
    for _ in range(6):
        x, y = 600 + rng.integers(-20, 60), 390 + rng.integers(0, 50)
        d.ellipse([x - 8, y - 8, x + 8, y + 8], outline=GRN, width=3)
    return img


def whiteboard_cabin(rng):
    img, d, hand, BLUE, RED, GRN, BLK = _board()
    d.text((24, 14), "CABIN RULES", font=hand(40), fill=BLUE)
    d.line([(24, 62), (270, 60)], fill=BLUE, width=3)
    for k, (t, col) in enumerate((("1. Quiet hours 22:00-06:00", BLK), ("2. Strap down your snacks", BLK),
                                  ("3. No EVA in pyjamas", RED), ("4. Whoever took my socks:", BLK), ("    I know it was you, Jeb", RED))):
        d.text((30, 80 + k * 42), t, font=hand(28), fill=col)
    # bunk rota grid
    x0, y0 = 470, 30
    d.text((x0, y0), "BUNK ROTA", font=hand(30), fill=GRN)
    names = ("Jeb", "Bill", "Bob", "Val")
    for k in range(5):
        d.line([(x0, y0 + 50 + k * 40), (x0 + 270, y0 + 50 + k * 40)], fill=BLK, width=2)
    for j in range(4):
        d.line([(x0 + j * 90, y0 + 50), (x0 + j * 90, y0 + 210)], fill=BLK, width=2)
    for k, n in enumerate(names):
        d.text((x0 + 8, y0 + 56 + k * 40), n, font=hand(24), fill=BLUE)
        for j in (1, 2):
            if rng.random() < 0.7:
                d.text((x0 + 8 + j * 90 + 20, y0 + 52 + k * 40), "x", font=hand(28), fill=RED)
    # noughts and crosses, abandoned mid-game
    gx, gy = 120, 330
    for k in (1, 2):
        d.line([(gx + k * 50, gy), (gx + k * 50, gy + 150)], fill=BLK, width=3)
        d.line([(gx, gy + k * 50), (gx + 150, gy + k * 50)], fill=BLK, width=3)
    for (i, j, t) in ((0, 0, "X"), (1, 1, "O"), (2, 0, "X"), (1, 0, "O"), (0, 2, "X")):
        d.text((gx + 12 + i * 50, gy + 2 + j * 50), t, font=hand(40), fill=RED if t == "X" else BLUE)
    d.text((gx + 170, gy + 50), "<- Bill, your move", font=hand(26), fill=BLK)
    d.text((460, 440), "Movie night: Thursday", font=hand(28), fill=GRN)
    return img


def whiteboard_flight(rng):
    img, d, hand, BLUE, RED, GRN, BLK = _board()
    d.text((24, 14), "RE-ENTRY CHECKLIST", font=hand(40), fill=BLUE)
    d.line([(24, 62), (400, 60)], fill=BLUE, width=3)
    items = ("Heat shield: still there?", "Pointy end forward", "Payload bay doors: CLOSED", "Wheels: down (later)",
             "Snacks stowed", "Panic: optional")
    for k, t in enumerate(items):
        y = 80 + k * 44
        d.rectangle([30, y + 6, 54, y + 30], outline=BLK, width=3)
        if k != 3:
            d.line([(32, y + 18), (40, y + 28), (58, y + 2)], fill=GRN, width=4)
        d.text((68, y), t, font=hand(28), fill=RED if k == 2 else BLK)
    # a doodled shuttle gliding in
    sx, sy = 560, 300
    d.polygon([(sx - 110, sy + 10), (sx + 60, sy - 6), (sx + 110, sy + 6), (sx + 60, sy + 20)], outline=BLK, width=3)
    d.polygon([(sx - 40, sy + 12), (sx + 10, sy + 70), (sx + 40, sy + 18)], outline=BLK, width=3)
    d.polygon([(sx - 100, sy + 8), (sx - 90, sy - 40), (sx - 70, sy + 6)], outline=BLK, width=3)
    for k in range(4):
        d.arc([sx - 200 - k * 30, sy - 60 - k * 20, sx - 60 + k * 30, sy + 80 + k * 20], 150, 210, fill=RED, width=3)
    d.text((440, 400), "glide ratio: 'optimistic'", font=hand(26), fill=RED)
    d.text((30, 440), "LANDING SPEED: less than Jeb thinks", font=hand(28), fill=BLUE)
    return img


ALL = {"whiteboard": whiteboard, "whiteboard_lab": whiteboard_lab, "whiteboard_cabin": whiteboard_cabin,
       "whiteboard_flight": whiteboard_flight, "crew": crew, "boosters": boosters, "eve": eve, "jool": jool, "minmus": minmus, "staging": staging, "struts": struts,
       "munholiday": mun_holiday, "lostpart": lost_part, "safety": safety_third, "missing": missing_kerbal}

if __name__ == "__main__":
    rng = np.random.default_rng(81)
    for key in (sys.argv[2:] or list(ALL)):
        img = ALL[key](rng)
        path = os.path.join(OUT, f"{'' if key.startswith('whiteboard') else 'poster_'}{key}.png")
        img.save(path)
        print("wrote", path)
