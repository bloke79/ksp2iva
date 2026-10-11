"""Texture generator for the Mk1-3 interior.

Writes PNGs into the folder given as the first argument. Everything is drawn procedurally so
the textures can be regenerated or tweaked without any source art.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT_COND = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"


# Windows stand-ins for the DejaVu fonts (the originals were drawn on Linux)
WIN_FONTS = {"DejaVuSans-Bold.ttf": "arialbd.ttf", "DejaVuSansMono-Bold.ttf": "consolab.ttf", "DejaVuSansCondensed-Bold.ttf": "arialnb.ttf"}


def font(path, size):
    base = os.path.basename(path)
    for p in (path, os.path.join("C:/Windows/Fonts", base), os.path.join("C:/Windows/Fonts", WIN_FONTS.get(base, "arialbd.ttf")), "C:/Windows/Fonts/arialbd.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def save(img, name):
    img.save(os.path.join(OUT, name))
    print("wrote", name, img.size)


# ---------------------------------------------------------------- navball (equirectangular)
def navball(w=2048, h=1024):
    img = Image.new("RGB", (w, h))
    px = np.zeros((h, w, 3), dtype=np.float32)
    v = np.linspace(0, 1, h)[:, None]           # 0 top (zenith) .. 1 bottom (nadir)
    sky = np.array([0.20, 0.52, 0.86]); sky_hi = np.array([0.36, 0.68, 0.96])
    ground = np.array([0.55, 0.33, 0.14]); ground_lo = np.array([0.40, 0.22, 0.08])
    t_sky = np.clip(v / 0.5, 0, 1)
    t_gnd = np.clip((v - 0.5) / 0.5, 0, 1)
    col = np.where(v[..., None] < 0.5,
                   sky_hi * (1 - t_sky[..., None]) + sky * t_sky[..., None],
                   ground * (1 - t_gnd[..., None]) + ground_lo * t_gnd[..., None])
    px[:] = np.broadcast_to(col, (h, w, 3))
    img = Image.fromarray((px * 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    f = font(FONT_BOLD, 28)
    # pitch lines every 10 degrees, heavier every 30
    for pitch in range(-80, 90, 10):
        y = int((90 - pitch) / 180 * h)
        heavy = pitch % 30 == 0
        colr = (255, 255, 255) if pitch >= 0 else (255, 235, 200)
        d.line([(0, y), (w, y)], fill=colr, width=5 if heavy else 2)
        if heavy and pitch != 0:
            for k in range(8):
                x = int(k * w / 8 + w / 16)
                d.text((x, y - 34 if pitch > 0 else y + 4), f"{abs(pitch)}", fill=colr, font=f, anchor="mm" if False else None)
    # horizon
    d.line([(0, h // 2), (w, h // 2)], fill=(255, 255, 255), width=10)
    # heading meridians every 15 degrees, labelled every 45
    fh = font(FONT_BOLD, 40)
    for hd in range(0, 360, 15):
        x = int(hd / 360 * w)
        heavy = hd % 45 == 0
        d.line([(x, int(h * 0.08)), (x, int(h * 0.92))], fill=(255, 255, 255), width=4 if heavy else 2)
        if heavy:
            label = {0: "N", 90: "E", 180: "S", 270: "W"}.get(hd, str(hd))
            for y in (int(h * 0.45), int(h * 0.55)):
                d.text((x + 8, y - 22), label, fill=(255, 255, 255), font=fh)
    # pole markers
    for y, c in ((int(h * 0.02), (255, 255, 255)), (int(h * 0.98), (255, 220, 160))):
        d.rectangle([0, y - 6, w, y + 6], fill=c)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    save(img, "navball.png")


# ---------------------------------------------------------------- CRT screens
def crt_base(w, h, tint):
    img = Image.new("RGB", (w, h), (4, 10, 6))
    d = ImageDraw.Draw(img)
    return img, d


def crt_finish(img, tint):
    a = np.asarray(img).astype(np.float32) / 255.0
    h, w = a.shape[:2]
    # scanlines and vignette
    scan = 0.82 + 0.18 * (np.arange(h) % 3 != 0)[:, None]
    yy, xx = np.mgrid[0:h, 0:w]
    vig = 1 - 0.3 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) ** 2
    a = a * scan[..., None] * np.clip(vig, 0.25, 1)[..., None]
    glow = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255
    a = np.clip(a + glow * 0.6, 0, 1)
    return Image.fromarray((a * 255).astype(np.uint8))


def crt_orbit(w=768, h=512):
    g = (90, 255, 140)
    img, d = crt_base(w, h, g)
    cx, cy = w * 0.42, h * 0.52
    d.ellipse([cx - 70, cy - 70, cx + 70, cy + 70], outline=g, width=3)           # planet
    for a in range(0, 360, 30):
        r = math.radians(a)
        d.line([(cx + 70 * math.cos(r), cy + 70 * math.sin(r)), (cx + 60 * math.cos(r), cy + 60 * math.sin(r))], fill=g, width=2)
    d.ellipse([cx - 230, cy - 150, cx + 260, cy + 160], outline=g, width=2)       # orbit
    d.ellipse([cx + 248, cy - 8, cx + 272, cy + 16], fill=g)                      # craft
    d.text((cx - 222, cy - 168), "AP 112.4 km", fill=g, font=font(FONT_MONO, 22))
    d.text((cx + 120, cy + 168), "PE 78.9 km", fill=g, font=font(FONT_MONO, 22))
    f = font(FONT_MONO, 24)
    d.text((16, 12), "ORBIT  KERBIN", fill=g, font=f)
    d.text((w - 220, 12), "T+ 00:14:32", fill=g, font=f)
    d.rectangle([4, 4, w - 5, h - 5], outline=g, width=2)
    save(crt_finish(img, g), "crt_orbit.png")


def crt_data(w=768, h=512):
    a = (255, 190, 60)
    img, d = crt_base(w, h, a)
    f = font(FONT_MONO, 30)
    rows = [("ALT", "84 213 m"), ("VEL", "2 246 m/s"), ("VSPD", "+12.6 m/s"), ("G", "1.02"),
            ("dV", "1 384 m/s"), ("FUEL", "62 %"), ("O2", "98 %"), ("TEMP", "291 K")]
    for i, (k, v) in enumerate(rows):
        y = 26 + i * 58
        d.text((24, y), k, fill=a, font=f)
        d.text((w - 24, y), v, fill=a, font=f, anchor="ra")
        d.line([(24, y + 46), (w - 24, y + 46)], fill=(120, 80, 20), width=1)
    d.rectangle([4, 4, w - 5, h - 5], outline=a, width=2)
    save(crt_finish(img, a), "crt_data.png")


def crt_attitude(w=768, h=512):
    c = (120, 220, 255)
    img, d = crt_base(w, h, c)
    f = font(FONT_MONO, 24)
    # bar graphs
    for i, (label, val) in enumerate([("PITCH", 0.55), ("YAW", 0.48), ("ROLL", 0.62), ("THR", 0.8)]):
        x0 = 40 + i * 180
        d.rectangle([x0, 70, x0 + 60, 420], outline=c, width=2)
        top = 420 - int(350 * val)
        d.rectangle([x0 + 6, top, x0 + 54, 414], fill=c)
        d.text((x0 + 30, 450), label, fill=c, font=f, anchor="ma")
    d.text((24, 16), "ATTITUDE  SAS:ON  RCS:OFF", fill=c, font=f)
    d.rectangle([4, 4, w - 5, h - 5], outline=c, width=2)
    save(crt_finish(img, c), "crt_attitude.png")


# ---------------------------------------------------------------- gauges
def gauge(name, label, frac, w=512):
    img = Image.new("RGB", (w, w), (18, 18, 20))
    d = ImageDraw.Draw(img)
    c = w / 2
    d.ellipse([12, 12, w - 12, w - 12], fill=(236, 232, 220))
    d.ellipse([40, 40, w - 40, w - 40], fill=(244, 241, 232))
    start, sweep = 225, 270
    for i in range(0, 51):
        a = math.radians(start - sweep * i / 50)
        r0 = c - 52
        r1 = r0 - (40 if i % 10 == 0 else 22 if i % 5 == 0 else 12)
        d.line([(c + r0 * math.cos(a), c - r0 * math.sin(a)), (c + r1 * math.cos(a), c - r1 * math.sin(a))],
               fill=(20, 20, 20), width=6 if i % 10 == 0 else 3)
    # red zone
    for i in range(42, 51):
        a0 = math.radians(start - sweep * i / 50); a1 = math.radians(start - sweep * (i + 1) / 50)
        r = c - 60
        d.line([(c + r * math.cos(a0), c - r * math.sin(a0)), (c + r * math.cos(a1), c - r * math.sin(a1))], fill=(200, 30, 20), width=10)
    fn = font(FONT_BOLD, 40)
    for i in range(0, 6):
        a = math.radians(start - sweep * i / 5)
        r = c - 130
        d.text((c + r * math.cos(a), c - r * math.sin(a)), str(i * 2), fill=(20, 20, 20), font=fn, anchor="mm")
    d.text((c, c + 62), label, fill=(30, 30, 30), font=font(FONT_BOLD, 34), anchor="mm")
    if frac is None:          # live gauge: the needle is a separate mesh the mod turns
        save(img, name)
        return
    a = math.radians(start - sweep * frac)
    d.line([(c - 30 * math.cos(a), c + 30 * math.sin(a)), (c + (c - 80) * math.cos(a), c - (c - 80) * math.sin(a))], fill=(220, 60, 20), width=12)
    d.ellipse([c - 26, c - 26, c + 26, c + 26], fill=(30, 30, 30))
    save(img, name)


# ---------------------------------------------------------------- labels atlas (4x4 cells)
LABELS = ["ABORT", "STAGE", "SAS", "RCS", "GEAR", "LIGHTS", "BRAKES", "CHUTES",
          "ARM", "PWR", "COMM", "O2", "FUEL", "CABIN", "MASTER\nALARM", "DOCK"]


def labels(cell=256):
    n = 4
    img = Image.new("RGB", (cell * n, cell * n), (24, 24, 26))
    d = ImageDraw.Draw(img)
    f = font(FONT_COND, 54)
    for i, text in enumerate(LABELS):
        x, y = (i % n) * cell, (i // n) * cell
        d.rectangle([x + 8, y + 8, x + cell - 9, y + cell - 9], fill=(232, 230, 222))
        d.rectangle([x + 18, y + 18, x + cell - 19, y + cell - 19], outline=(30, 30, 30), width=4)
        d.multiline_text((x + cell / 2, y + cell / 2), text, fill=(20, 20, 20), font=f, anchor="mm", align="center", spacing=4)
    save(img, "labels.png")


# ---------------------------------------------------------------- quilted padding (colour + normal)
def quilt(size=1024, cells=8):
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) / size * cells
    # diamond quilt: distance to diagonal seams
    u = (xx + yy) % 1.0
    v = (xx - yy) % 1.0
    du = np.minimum(u, 1 - u)
    dv = np.minimum(v, 1 - v)
    dist = np.minimum(du, dv)                        # 0 at seam, 0.5 at pillow centre
    height = np.clip(dist / 0.5, 0, 1) ** 0.5        # puffy pillows
    # normal map from height
    gy, gx = np.gradient(height * 6.0)
    n = np.dstack([-gx, -gy, np.ones_like(height)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    nrm = ((n * 0.5 + 0.5) * 255).astype(np.uint8)
    save(Image.fromarray(nrm), "quilt_normal.png")
    base = np.array([0.74, 0.72, 0.66])
    shade = 0.82 + 0.18 * height
    seam = (dist < 0.02).astype(np.float32)
    col = base[None, None, :] * shade[..., None] * (1 - 0.35 * seam[..., None])
    noise = np.random.default_rng(1).normal(0, 0.012, (size, size, 1))
    col = np.clip(col + noise, 0, 1)
    save(Image.fromarray((col * 255).astype(np.uint8)), "quilt_color.png")


# ---------------------------------------------------------------- hazard stripes
def hazard(w=512, h=128):
    img = Image.new("RGB", (w, h), (250, 200, 20))
    d = ImageDraw.Draw(img)
    step = 64
    for x in range(-h, w + h, step):
        d.polygon([(x, h), (x + step / 2, h), (x + step / 2 + h, 0), (x + h, 0)], fill=(20, 20, 20))
    save(img, "hazard.png")


# ---------------------------------------------------------------- floor grate (colour + normal)
def grate(size=1024, holes=16):
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) / size * holes
    fx = xx % 1.0; fy = yy % 1.0
    # rounded square holes
    hx = np.abs(fx - 0.5); hy = np.abs(fy - 0.5)
    hole = (np.maximum(hx, hy) < 0.32).astype(np.float32)
    height = 1 - hole
    height = np.asarray(Image.fromarray((height * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255
    gy, gx = np.gradient(height * 4.0)
    n = np.dstack([-gx, -gy, np.ones_like(height)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    save(Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8)), "grate_normal.png")
    metal = 0.36 + 0.06 * np.random.default_rng(2).normal(0, 1, (size, size))
    col = np.clip(metal * height + 0.05 * (1 - height), 0, 1)
    rgb = np.dstack([col, col * 0.98, col * 0.95])
    save(Image.fromarray((rgb * 255).astype(np.uint8)), "grate_color.png")


# ---------------------------------------------------------------- name plate
def plate(w=1024, h=256):
    img = Image.new("RGB", (w, h), (200, 198, 190))
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, w - 11, h - 11], outline=(40, 40, 40), width=6)
    d.text((w / 2, h * 0.38), "MK1-3 COMMAND POD", fill=(30, 30, 30), font=font(FONT_BOLD, 70), anchor="mm")
    d.text((w / 2, h * 0.72), "CREW 3   |   MAX 9 G   |   KEEP HATCH CLEAR", fill=(60, 60, 60), font=font(FONT_COND, 36), anchor="mm")
    for x in (34, w - 34):
        for y in (34, h - 34):
            d.ellipse([x - 10, y - 10, x + 10, y + 10], fill=(120, 120, 120))
    save(img, "plate.png")


def cabin_reflection(w=512, h=256):
    """Lat-long environment for the interiors' own reflection probe: a dim cabin (warm lamp glow overhead, darker
    walls, near-black floor), so shiny surfaces reflect the cabin instead of the bright sky outside."""
    v = np.linspace(0, 1, h)[:, None, None]            # 0 = straight up
    u = np.linspace(0, 1, w)[None, :, None]
    top = np.array([0.36, 0.33, 0.29]); wall = np.array([0.10, 0.105, 0.115]); floor = np.array([0.025, 0.025, 0.03])
    col = np.where(v < 0.5, top * (1 - v / 0.5) + wall * (v / 0.5), wall * (1 - (v - 0.5) / 0.5) + floor * ((v - 0.5) / 0.5))
    bands = 1 + 0.08 * np.cos(u * 2 * np.pi * 8)       # stringers/panels round the walls
    px = np.clip(col * bands, 0, 1)
    px = np.broadcast_to(px, (h, w, 3))
    save(Image.fromarray((px * 255).astype(np.uint8)), "cabin_reflection.png")


# ---------------------------------------------------------------- console panel finish (colour + normal), tileable
def _tile_noise(size, scale, seed):
    """Tileable value noise: random grid upsampled with wrap-around."""
    rng = np.random.default_rng(seed)
    g = rng.random((scale, scale)).astype(np.float32)
    g = np.tile(g, (3, 3))
    big = Image.fromarray((g * 255).astype(np.uint8)).resize((size * 3, size * 3), Image.BICUBIC)
    a = np.asarray(big).astype(np.float32)[size:2 * size, size:2 * size] / 255
    return a


def panel(size=1024):
    """Dark, slightly worn console finish: low-frequency grime, fine powder-coat speckle, faint scratches."""
    grime = 0.6 * _tile_noise(size, 6, 2) + 0.4 * _tile_noise(size, 17, 3)
    speck = np.random.default_rng(4).normal(0, 1, (size, size)).astype(np.float32)
    speck = np.asarray(Image.fromarray(((speck * 0.5 + 0.5).clip(0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))).astype(np.float32) / 255
    base = np.array([0.15, 0.155, 0.16])
    col = base[None, None, :] * (0.72 + 0.4 * grime[..., None]) * (0.92 + 0.14 * speck[..., None])
    img = Image.fromarray((col.clip(0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(5)
    for _ in range(90):                      # light scratches
        x, y = rng.random(2) * size
        a = rng.random() * math.pi
        ln = 20 + rng.random() * 90
        d.line([(x, y), (x + ln * math.cos(a), y + ln * math.sin(a))], fill=(72, 74, 77), width=1)
    save(img, "panel_color.png")
    h = 0.5 * speck + 0.5 * grime
    gy, gx = np.gradient(h * 3.0)
    n = np.dstack([-gx, -gy, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    save(Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8)), "panel_normal.png")


# ---------------------------------------------------------------- KSP2-style multi-function display pages (cyan on deep blue)
MFD_BG, MFD_FG, MFD_DIM = (6, 22, 48), (110, 235, 255), (40, 120, 160)


def _mfd(w=512, h=512):
    img = Image.new("RGB", (w, h), MFD_BG)
    d = ImageDraw.Draw(img)
    d.rectangle([6, 6, w - 7, h - 7], outline=MFD_DIM, width=3)
    return img, d


def _mfd_finish(img, name):
    glow = img.filter(ImageFilter.GaussianBlur(4))
    a = np.clip(np.asarray(img).astype(np.float32) + np.asarray(glow).astype(np.float32) * 0.5, 0, 255)
    save(Image.fromarray(a.astype(np.uint8)), name)


def mfd_systems():
    img, d = _mfd()
    f = font(FONT_MONO, 26)
    d.text((24, 18), "SYS  PWR / LS", fill=MFD_FG, font=f)
    for i, (k, v) in enumerate([("EC", 0.82), ("O2", 0.97), ("H2O", 0.74), ("CO2", 0.12), ("FUEL", 0.63), ("OX", 0.61)]):
        y = 70 + i * 66
        d.text((24, y), k, fill=MFD_FG, font=f)
        d.rectangle([120, y + 4, 470, y + 34], outline=MFD_DIM, width=2)
        d.rectangle([124, y + 8, 124 + int(342 * v), y + 30], fill=MFD_FG if v > 0.2 else (255, 120, 60))
    d.text((24, 470), "BUS A NOMINAL", fill=MFD_DIM, font=font(FONT_MONO, 20))
    _mfd_finish(img, "mfd_systems.png")


def mfd_map():
    img, d = _mfd()
    for x in range(16, 512, 40):
        d.line([(x, 60), (x, 460)], fill=(20, 60, 90), width=1)
    for y in range(60, 461, 40):
        d.line([(16, y), (496, y)], fill=(20, 60, 90), width=1)
    pts = [(16 + i * 4, 265 + 120 * math.sin(i * 4 / 480 * 2 * math.pi * 1.3)) for i in range(121)]
    d.line(pts, fill=MFD_FG, width=3)
    d.ellipse([300, 160, 316, 176], fill=(255, 210, 90))
    for cx, cy, r in ((120, 360, 40), (380, 330, 30), (210, 150, 22)):
        d.ellipse([cx - r, cy - r * 0.6, cx + r, cy + r * 0.6], outline=MFD_DIM, width=2)
    d.text((24, 18), "MAP  GROUND TRACK", fill=MFD_FG, font=font(FONT_MONO, 24))
    d.text((24, 470), "LAT -0.10  LON 74.6", fill=MFD_DIM, font=font(FONT_MONO, 20))
    _mfd_finish(img, "mfd_map.png")


def mfd_engine():
    img, d = _mfd()
    d.text((24, 18), "PROP  STAGE 3", fill=MFD_FG, font=font(FONT_MONO, 24))
    d.polygon([(180, 90), (330, 90), (360, 300), (150, 300)], outline=MFD_FG, width=3)
    d.line([(255, 300), (255, 340)], fill=MFD_FG, width=3)
    d.polygon([(215, 340), (295, 340), (330, 450), (180, 450)], outline=MFD_FG, width=3)
    for k, (x, v) in enumerate(((70, 0.7), (440, 0.45))):
        d.arc([x - 40, 160, x + 40, 240], 135, 135 + int(270 * v), fill=MFD_FG, width=8)
        d.text((x, 262), ("THR", "TWR")[k], fill=MFD_FG, font=font(FONT_MONO, 20), anchor="mm")
    d.text((24, 470), "ISP 285  dV 1384", fill=MFD_DIM, font=font(FONT_MONO, 20))
    _mfd_finish(img, "mfd_engine.png")


def mfd_comms():
    img, d = _mfd()
    d.text((24, 18), "COMM  LINK", fill=MFD_FG, font=font(FONT_MONO, 24))
    cx, cy = 256, 260
    for r in (60, 120, 180):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(20, 60, 90), width=2)
    for a in range(0, 360, 45):
        d.line([(cx, cy), (cx + 180 * math.cos(math.radians(a)), cy + 180 * math.sin(math.radians(a)))], fill=(20, 60, 90), width=1)
    d.line([(cx, cy), (cx + 150, cy - 90)], fill=MFD_FG, width=4)
    d.ellipse([cx + 140, cy - 100, cx + 160, cy - 80], fill=(255, 210, 90))
    for i in range(10):
        hgt = 10 + i * 6
        d.rectangle([40 + i * 14, 480 - hgt, 50 + i * 14, 480], fill=MFD_FG if i < 7 else MFD_DIM)
    d.text((300, 455), "KSC 4.2 Mm", fill=MFD_FG, font=font(FONT_MONO, 22))
    _mfd_finish(img, "mfd_comms.png")


# ---------------------------------------------------------------- annunciator lenses (4x4 atlas), keypad keys (4x4), digit readout
ANNUNC = [("MASTER\nCAUTION", (255, 170, 40)), ("ABORT", (255, 60, 40)), ("SAS", (90, 255, 140)), ("RCS", (90, 255, 140)),
          ("GEAR", (90, 255, 140)), ("O2 LOW", (255, 170, 40)), ("EC LOW", (255, 170, 40)), ("COMM", (240, 240, 230)),
          ("STAGE\nARMED", (255, 60, 40)), ("CHUTE", (240, 240, 230)), ("DOCK", (120, 200, 255)), ("HEAT", (255, 60, 40)),
          ("FUEL\nCELL", (240, 240, 230)), ("CABIN\nPRESS", (255, 170, 40)), ("G-LIM", (255, 170, 40)), ("TGT", (120, 200, 255))]


def annunciators(cell=128):
    n = 4
    img = Image.new("RGB", (cell * n, cell * n), (8, 8, 9))
    d = ImageDraw.Draw(img)
    f = font(FONT_COND, 24)
    for i, (text, c) in enumerate(ANNUNC):
        x, y = (i % n) * cell, (i // n) * cell
        d.rectangle([x + 4, y + 4, x + cell - 5, y + cell - 5], fill=tuple(int(v * 0.18) for v in c))
        d.multiline_text((x + cell / 2, y + cell / 2), text, fill=tuple(int(v * 0.55) for v in c), font=f, anchor="mm", align="center", spacing=2)
    save(img.filter(ImageFilter.GaussianBlur(0.5)), "annunciators.png")


KEYS = ["7", "8", "9", "VERB", "4", "5", "6", "NOUN", "1", "2", "3", "+", "CLR", "0", "ENTR", "-"]


def keys(cell=128):
    n = 4
    img = Image.new("RGB", (cell * n, cell * n), (40, 40, 42))
    d = ImageDraw.Draw(img)
    for i, k in enumerate(KEYS):
        x, y = (i % n) * cell, (i // n) * cell
        d.rectangle([x + 6, y + 6, x + cell - 7, y + cell - 7], fill=(205, 203, 196))
        d.text((x + cell / 2, y + cell / 2), k, fill=(25, 25, 25), font=font(FONT_BOLD, 44 if len(k) == 1 else 26), anchor="mm")
    save(img, "keys.png")


def digits(w=512, h=256):
    img = Image.new("RGB", (w, h), (3, 12, 6))
    d = ImageDraw.Draw(img)
    for i, t in enumerate(("+00841", "-00126", "+12460")):
        d.text((w - 24, 14 + i * 80), t, fill=(100, 255, 150), font=font(FONT_MONO, 56), anchor="ra")
    for i, t in enumerate(("PROG", "VERB", "NOUN")):
        d.text((20, 30 + i * 80), t, fill=(40, 140, 80), font=font(FONT_MONO, 26))
    _mfd_finish(img, "digits.png")


def canvas(size=512, threads=48):
    """Woven fabric normal map (Nomex/Beta-cloth weave) for bags, sleeping bags and towels."""
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) / size * threads
    warp = np.sin(xx * np.pi * 2) * 0.5 + 0.5
    weft = np.sin(yy * np.pi * 2) * 0.5 + 0.5
    over = ((np.floor(xx) + np.floor(yy)) % 2).astype(np.float32)
    h = over * warp + (1 - over) * weft
    h += np.random.default_rng(7).normal(0, 0.05, h.shape)
    gy, gx = np.gradient(h * 1.5)
    n = np.dstack([-gx, -gy, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    save(Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8)), "canvas_normal.png")


def locker(size=1024, cells=4):
    """Light grey locker/equipment finish: panel seams, rivets, worn edges and grime (tileable)."""
    grime = 0.6 * _tile_noise(size, 5, 11) + 0.4 * _tile_noise(size, 19, 12)
    base = np.array([0.36, 0.37, 0.38])
    col = base[None, None, :] * (0.82 + 0.25 * grime[..., None])
    img = Image.fromarray((col.clip(0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    step = size // cells
    for i in range(cells + 1):
        for w, c in ((3, (70, 72, 72)), (1, (165, 168, 166))):
            d.line([(0, i * step + (w == 1) * 3), (size, i * step + (w == 1) * 3)], fill=tuple(int(v * 0.45) for v in c), width=w)
            d.line([(i * step + (w == 1) * 3, 0), (i * step + (w == 1) * 3, size)], fill=tuple(int(v * 0.45) for v in c), width=w)
    for i in range(cells):
        for j in range(cells):
            for (ox, oy) in ((12, 12), (step - 12, 12), (12, step - 12), (step - 12, step - 12)):
                x, y = i * step + ox, j * step + oy
                d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(70, 72, 74))
    rng = np.random.default_rng(13)
    for _ in range(60):
        x, y = rng.random(2) * size
        a = rng.random() * math.pi
        ln = 10 + rng.random() * 60
        d.line([(x, y), (x + ln * math.cos(a), y + ln * math.sin(a))], fill=(80, 82, 84), width=1)
    save(img.filter(ImageFilter.GaussianBlur(0.4)), "locker_color.png")


def wallpanel(size=1024, cells=2):
    """Dark blue-grey riveted wall closeout panels (the stock KSP2 cabin look): seams, bolts, brushed streaks, grime."""
    grime = 0.6 * _tile_noise(size, 4, 21) + 0.4 * _tile_noise(size, 15, 22)
    streak = np.asarray(Image.fromarray((np.random.default_rng(23).random((size, 8)) * 255).astype(np.uint8)).resize((size, size), Image.BICUBIC)).astype(np.float32) / 255
    base = np.array([0.40, 0.41, 0.43])
    col = base[None, None, :] * (0.8 + 0.3 * grime[..., None]) * (0.95 + 0.08 * streak[..., None])
    h = np.zeros((size, size), np.float32)
    step = size // cells
    yy, xx = np.mgrid[0:size, 0:size]
    for i in range(cells + 1):
        for a in (xx, yy):
            seam = np.abs(a - i * step) < 4
            h[seam] -= 1.0
            col[seam] *= 0.45
            near = (np.abs(a - i * step) < 26) & ~seam   # grime and a little rust along panel edges, as on the stock walls
            wear = near * (0.55 + 0.45 * grime) * (1.0 - np.abs(a - i * step) / 26.0)
            col -= (wear * 0.13)[..., None] * np.array([0.8, 1.0, 1.25])
    rng = np.random.default_rng(24)
    img = Image.fromarray((col.clip(0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    hd = Image.fromarray(((h * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8))
    dh = ImageDraw.Draw(hd)
    for i in range(cells):
        for j in range(cells):
            for (ox, oy) in ((18, 18), (step - 18, 18), (18, step - 18), (step - 18, step - 18), (step // 2, 18), (step // 2, step - 18)):
                x, y = i * step + ox, j * step + oy
                d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(58, 62, 68))
                d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(30, 32, 36))
                dh.ellipse([x - 7, y - 7, x + 7, y + 7], fill=200)
            if rng.random() < 0.6:   # stencil placard
                x, y = i * step + int(step * 0.15), j * step + int(step * (0.6 + 0.2 * rng.random()))
                d.rectangle([x, y, x + int(step * 0.3), y + 14], fill=(90, 92, 88))
                d.rectangle([x + 4, y + 4, x + int(step * 0.22), y + 9], fill=(40, 42, 44))
    save(img.filter(ImageFilter.GaussianBlur(0.5)), "wallpanel_color.png")
    ha = np.asarray(hd.filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255 + grime * 0.15
    gy, gx = np.gradient(ha * 4.0)
    n = np.dstack([-gx, -gy, np.ones_like(ha)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    save(Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8)), "wallpanel_normal.png")


def _blob(d, x, y, r, col, rng, hi=0.35, n=9, jit=0.25):
    """Irregular rounded lump with a soft highlight (food chunks, peas, fruit)."""
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        rr = r * (1 + jit * (rng.random() - 0.5) * 2)
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    d.polygon(pts, fill=tuple(int(c * 255) for c in col))
    hcol = tuple(int(min(1, c + hi * (1 - c)) * 255) for c in col)
    d.ellipse([x - r * 0.45, y - r * 0.55, x - r * 0.05, y - r * 0.2], fill=hcol)


def food(size=1024):
    """Food atlas, 2 x 2 tiles: beef stew, mash with peas, rice with vegetables, fruit cup. Drawn procedurally
    (no photos), slightly stylised to sit with the KSP2 look."""
    import random as _r
    t = size // 2
    img = Image.new("RGB", (size, size))
    rr = _r.Random(7)

    def tile_base(ox, oy, col, var, seed):
        n = 0.6 * _tile_noise(t, 6, seed) + 0.4 * _tile_noise(t, 24, seed + 1)
        a = np.array(col)[None, None, :] * (1 - var / 2 + var * n[..., None])
        img.paste(Image.fromarray((a.clip(0, 1) * 255).astype(np.uint8)), (ox, oy))

    # stew: rich red-brown gravy, beef chunks, carrot cubes, potato, peas
    tile_base(0, 0, (0.42, 0.16, 0.07), 0.35, 61)
    d = ImageDraw.Draw(img)
    for _ in range(26):
        _blob(d, rr.uniform(20, t - 20), rr.uniform(20, t - 20), rr.uniform(22, 38), (0.30, 0.13, 0.07), rr, hi=0.25)
    for _ in range(22):
        x, y, s_ = rr.uniform(15, t - 15), rr.uniform(15, t - 15), rr.uniform(12, 18)
        d.rectangle([x - s_, y - s_, x + s_, y + s_], fill=(214, 110, 28))
        d.rectangle([x - s_ * 0.6, y - s_ * 0.7, x - s_ * 0.1, y - s_ * 0.3], fill=(240, 160, 80))
    for _ in range(14):
        _blob(d, rr.uniform(20, t - 20), rr.uniform(20, t - 20), rr.uniform(18, 26), (0.85, 0.74, 0.48), rr, hi=0.3)
    for _ in range(30):
        _blob(d, rr.uniform(10, t - 10), rr.uniform(10, t - 10), 9, (0.32, 0.58, 0.16), rr, hi=0.45, jit=0.08)
    # mash with peas and a gravy pool
    tile_base(t, 0, (0.93, 0.86, 0.66), 0.18, 63)
    d = ImageDraw.Draw(img)
    for _ in range(40):
        x, y = t + rr.uniform(10, t - 10), rr.uniform(10, t - 10)
        d.arc([x - 30, y - 12, x + 30, y + 12], 200, 340, fill=(250, 244, 220), width=3)
    d.ellipse([t + 260, 60, t + 470, 250], fill=(120, 62, 28))
    d.ellipse([t + 300, 90, t + 380, 140], fill=(160, 92, 50))
    for _ in range(70):
        _blob(d, t + rr.uniform(20, 240), rr.uniform(240, t - 20), 13, (0.30, 0.60, 0.15), rr, hi=0.5, jit=0.06)
    # rice with peppers and greens
    tile_base(0, t, (0.94, 0.92, 0.84), 0.1, 65)
    d = ImageDraw.Draw(img)
    for _ in range(900):
        x, y, a = rr.uniform(0, t), t + rr.uniform(0, t), rr.uniform(0, math.pi)
        dx, dy = 9 * math.cos(a), 9 * math.sin(a)
        d.line([(x - dx, y - dy), (x + dx, y + dy)], fill=(255, 253, 244) if rr.random() < 0.6 else (214, 206, 186), width=6)
    for _ in range(26):
        x, y = rr.uniform(15, t - 15), t + rr.uniform(15, t - 15)
        d.rectangle([x - 10, y - 7, x + 10, y + 7], fill=(200, 40, 30) if rr.random() < 0.5 else (60, 140, 40))
    # fruit cup: syrup, peach slices, pineapple, cherries
    tile_base(t, t, (0.98, 0.72, 0.30), 0.2, 67)
    d = ImageDraw.Draw(img)
    for _ in range(16):
        x, y, r = t + rr.uniform(40, t - 40), t + rr.uniform(40, t - 40), rr.uniform(40, 60)
        a0 = rr.uniform(0, 360)
        d.pieslice([x - r, y - r, x + r, y + r], a0, a0 + 70, fill=(250, 150, 50))
        d.arc([x - r, y - r, x + r, y + r], a0, a0 + 70, fill=(255, 205, 120), width=6)
    for _ in range(14):
        x, y = t + rr.uniform(20, t - 20), t + rr.uniform(20, t - 20)
        d.rectangle([x - 16, y - 16, x + 16, y + 16], fill=(250, 226, 110))
    for _ in range(9):
        _blob(d, t + rr.uniform(20, t - 20), t + rr.uniform(20, t - 20), 20, (0.72, 0.05, 0.10), rr, hi=0.55, jit=0.04)
    save(img.filter(ImageFilter.GaussianBlur(1.2)), "food.png")


def food_labels(w=1024, h=512):
    """Pouch and drink-bag labels, 2 x 2 tiles: STEW, MASH, SNACKS, COFFEE. Colour band, name, a simple icon, barcode."""
    img = Image.new("RGB", (w, h), (238, 236, 228))
    d = ImageDraw.Draw(img)
    tw, th = w // 2, h // 2
    f = font(FONT_BOLD, 54)
    fs = font(FONT_COND, 26)
    items = [("STEW", (176, 52, 30)), ("MASH", (214, 160, 40)), ("SNACKS", (46, 120, 60)), ("COFFEE", (92, 58, 36))]
    notes = ["REHYDRATE / HEAT 20 MIN", "REHYDRATE / HEAT 20 MIN", "READY TO EAT", "ADD HOT WATER"]
    for i, (name, col) in enumerate(items):
        ox, oy = (i % 2) * tw, (i // 2) * th
        d.rectangle([ox + 6, oy + 6, ox + tw - 6, oy + th - 6], outline=(150, 150, 140), width=4)
        d.rectangle([ox + 6, oy + 6, ox + tw - 6, oy + 70], fill=col)
        d.text((ox + 24, oy + 18), "KERBAL FOOD SYS.", font=fs, fill=(250, 248, 240))
        d.text((ox + 24, oy + 92), name, font=f, fill=(30, 30, 30))
        d.text((ox + 24, oy + 162), notes[i], font=fs, fill=(80, 80, 76))
        cx, cy = ox + tw - 90, oy + 130
        d.ellipse([cx - 50, cy - 50, cx + 50, cy + 50], fill=col)
        d.ellipse([cx - 30, cy - 14, cx + 30, cy + 26], fill=(250, 248, 240))
        d.rectangle([cx - 34, cy - 18, cx + 34, cy - 6], fill=(250, 248, 240))
        for k in range(26):
            bw = 2 + (k * 7919) % 3 * 2
            d.rectangle([ox + 24 + k * 9, oy + th - 52, ox + 24 + k * 9 + bw, oy + th - 20], fill=(20, 20, 20))
    save(img, "food_labels.png")


def deckplate(size=1024, cells=2):
    """Solid deck plates (the stock floor look): grey plates with a tread pattern, bolted seams, and slotted grille
    inserts in alternate plates."""
    grime = 0.6 * _tile_noise(size, 5, 52) + 0.4 * _tile_noise(size, 18, 53)
    yy, xx = np.mgrid[0:size, 0:size]
    tread = ((np.sin((xx + yy) * 0.35) > 0.85) | (np.sin((xx - yy) * 0.35) > 0.85)).astype(np.float32)
    base = np.array([0.34, 0.35, 0.36])
    col = base[None, None, :] * (0.85 + 0.2 * grime[..., None]) * (1 - 0.12 * tread[..., None])
    h = 0.3 * tread
    step = size // cells
    for i in range(cells + 1):
        for a in (xx, yy):
            seam = np.abs(a - i * step) < 4
            col[seam] *= 0.35
            h[seam] -= 1.0
    img = Image.fromarray((col.clip(0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    hd = Image.fromarray(((h * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8))
    dh = ImageDraw.Draw(hd)
    for i in range(cells):
        for j in range(cells):
            x0, y0 = i * step, j * step
            for ox, oy in ((22, 22), (step - 22, 22), (22, step - 22), (step - 22, step - 22)):
                d.ellipse([x0 + ox - 8, y0 + oy - 8, x0 + ox + 8, y0 + oy + 8], fill=(70, 72, 74))
                dh.ellipse([x0 + ox - 8, y0 + oy - 8, x0 + ox + 8, y0 + oy + 8], fill=210)
            if (i + j) % 2 == 0:   # grille insert
                gx0, gy0, gx1, gy1 = x0 + step * 0.22, y0 + step * 0.3, x0 + step * 0.78, y0 + step * 0.7
                d.rectangle([gx0 - 6, gy0 - 6, gx1 + 6, gy1 + 6], fill=(46, 48, 50))
                dh.rectangle([gx0 - 6, gy0 - 6, gx1 + 6, gy1 + 6], fill=150)
                n = 9
                for k in range(n):
                    y = gy0 + (gy1 - gy0) * (k + 0.5) / n
                    d.rectangle([gx0 + 8, y - 6, gx1 - 8, y + 6], fill=(12, 12, 13))
                    dh.rectangle([gx0 + 8, y - 6, gx1 - 8, y + 6], fill=40)
    save(img.filter(ImageFilter.GaussianBlur(0.6)), "deckplate_color.png")
    ha = np.asarray(hd.filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255
    gy, gx = np.gradient(ha * 4.0)
    n = np.dstack([-gx, -gy, np.ones_like(ha)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    save(Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8)), "deckplate_normal.png")


# ---------------------------------------------------------------- shuttle-era flight deck (inspired by the orbiter's panels)
LEGENDS = ["PWR", "ON", "OFF", "AUTO", "MAN", "ARM", "SAFE", "PRI", "BKUP", "SEL", "BUS A", "BUS B", "ESS 1", "ESS 2",
           "CRT 1", "CRT 2", "MAJ FUNC", "GNC", "SM", "PL", "FLOOD", "DIM", "BRT", "TEST", "RESET", "MODE", "OPEN",
           "CLOSE", "CABIN", "FAN", "PUMP", "VENT", "LIGHTS", "RCS", "OMS", "SAS", "GEAR", "BRAKE", "TRIM", "ADI",
           "HSI", "ATT", "RATE", "ERR", "CMD", "TIMER", "EVENT", "START", "STOP", "UP", "DN", "L", "R", "FWD", "AFT"]


def shuttle_panel(size=1024, cells=4):
    """Orbiter-style switch panel finish: medium grey powder coat, sub-plates with fasteners, white stencilled
    legends and mimic lines joining switch groups. Nothing here is a real panel; it reads as one at a glance."""
    grime = 0.6 * _tile_noise(size, 5, 31) + 0.4 * _tile_noise(size, 19, 32)
    base = np.array([0.58, 0.59, 0.60])
    col = base[None, None, :] * (0.88 + 0.16 * grime[..., None])
    img = Image.fromarray((col.clip(0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(33)
    f = font(FONT_COND, 12)
    step = size // cells
    white = (244, 245, 240)
    for i in range(cells):
        for j in range(cells):
            x0, y0 = i * step, j * step
            d.rectangle([x0 + 2, y0 + 2, x0 + step - 3, y0 + step - 3], outline=(78, 80, 82), width=3)   # sub-plate seam
            for ox, oy in ((14, 14), (step - 14, 14), (14, step - 14), (step - 14, step - 14)):   # quarter-turn fasteners
                d.ellipse([x0 + ox - 6, y0 + oy - 6, x0 + ox + 6, y0 + oy + 6], fill=(150, 152, 150), outline=(70, 72, 74))
                d.line([x0 + ox - 4, y0 + oy, x0 + ox + 4, y0 + oy], fill=(60, 62, 64), width=2)
            # title band
            t = " ".join(rng.choice(LEGENDS, 2))
            d.text((x0 + 26, y0 + 22), t, fill=white, font=f)
            d.line([x0 + 24, y0 + 44, x0 + step - 26, y0 + 44], fill=white, width=2)
            # rows of switch legends with mimic brackets
            rows = int(rng.integers(2, 4))
            for r in range(rows):
                y = y0 + 60 + r * 60
                n = int(rng.integers(2, 4))
                xs = [x0 + 30 + k * (step - 60) // n for k in range(n)]
                for x in xs:
                    d.text((x, y), str(rng.choice(LEGENDS)), fill=white, font=f)
                    d.text((x, y + 24), str(rng.choice(LEGENDS)), fill=white, font=f)
                if rng.random() < 0.6 and n > 1:
                    yb = y + 44
                    d.line([xs[0] + 10, yb, xs[-1] + 10, yb], fill=white, width=2)
                    for x in xs:
                        d.line([x + 10, yb - 8, x + 10, yb], fill=white, width=2)
    save(img.filter(ImageFilter.GaussianBlur(0.4)), "shuttle_panel_color.png")


def wall_cream(size=1024, cells=2):
    """The orbiter's cabin walls: cream padded closeout panels with stitched quilting, seams and a little grime.
    (Velcro is modelled as strips beside the equipment that uses it, not printed on every panel.)"""
    grime = 0.6 * _tile_noise(size, 4, 41) + 0.4 * _tile_noise(size, 13, 42)
    base = np.array([0.80, 0.78, 0.71])
    col = base[None, None, :] * (0.9 + 0.12 * grime[..., None])
    h = np.zeros((size, size), np.float32)
    yy, xx = np.mgrid[0:size, 0:size]
    step = size // cells
    q = step // 4   # quilting
    for a in (xx, yy):
        stitch = (np.abs((a % q) - q / 2) > q / 2 - 2)
        h[stitch] -= 0.5
        col[stitch] *= 0.93
    for i in range(cells + 1):
        for a in (xx, yy):
            seam = np.abs(a - i * step) < 5
            h[seam] -= 1.0
            col[seam] *= 0.55
    img = Image.fromarray((col.clip(0, 1) * 255).astype(np.uint8))
    save(img.filter(ImageFilter.GaussianBlur(0.6)), "wall_cream_color.png")
    ha = (h - h.min()) / max(1e-6, (h.max() - h.min()))
    ha = np.asarray(Image.fromarray((ha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255
    gy, gx = np.gradient(ha * 5.0)
    n = np.dstack([-gx, -gy, np.ones_like(ha)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    save(Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8)), "wall_cream_normal.png")


ALL = {
    "navball": navball, "crt_orbit": crt_orbit, "crt_data": crt_data, "crt_attitude": crt_attitude,
    "gauge_alt": lambda: gauge("gauge_alt.png", "ALT km", 0.62),
    "gauge_press": lambda: gauge("gauge_press.png", "CABIN kPa", 0.48),
    "gauge_temp": lambda: gauge("gauge_temp.png", "TEMP x100", 0.35),
    "gauge_fuel": lambda: gauge("gauge_fuel.png", "FUEL", 0.71),
    # faces for the live gauges (needles are meshes): long hand km, short hand tens of km; outside pressure; outside temperature
    "gauge_alt_face": lambda: gauge("gauge_alt_face.png", "ALT km", None),
    "gauge_press_face": lambda: gauge("gauge_press_face.png", "ATM kPa x10", None),
    "gauge_temp_face": lambda: gauge("gauge_temp_face.png", "TEMP K x100", None),
    "cabin_reflection": cabin_reflection, "panel": panel, "canvas": canvas, "locker": locker, "wallpanel": wallpanel, "food": food, "food_labels": food_labels, "deckplate": deckplate,
    "mfd_systems": mfd_systems, "mfd_map": mfd_map, "mfd_engine": mfd_engine, "mfd_comms": mfd_comms,
    "annunciators": annunciators, "keys": keys, "digits": digits,
    "shuttle_panel": shuttle_panel, "wall_cream": wall_cream,
    "labels": labels, "quilt": quilt, "hazard": hazard, "grate": grate, "plate": plate,
}
# python texgen.py <out> [name ...]: only the named textures (default: all)
for key in (sys.argv[2:] or list(ALL)):
    ALL[key]()
