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
    "labels": labels, "quilt": quilt, "hazard": hazard, "grate": grate, "plate": plate,
}
# python texgen.py <out> [name ...]: only the named textures (default: all)
for key in (sys.argv[2:] or list(ALL)):
    ALL[key]()
