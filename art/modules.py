"""Panel modules for the interiors: bolted instrument plates in the KSP2 cockpit style (multi-function displays ringed
with buttons, annunciator grids, keypads, dial plates, knob rows, toggle banks, breaker panels, vent grilles), and a
grid layout that places them on a console Surface or a wall Band with an overlap check.

All module functions take p (centre, on the panel surface) and b (basis: right, up, normal towards the viewer).
"""
import math

import ivalib as L  # imports bpy first
import capsule as C
from mathutils import Matrix, Vector

M = L.M


def materials():
    """Module materials (call after L.begin). Replaces the plain console material with the textured one."""
    import bpy
    old = M.get("console")
    if old is not None:
        bpy.data.materials.remove(old)
    M["console"] = L.material("IVA_Console", tex="panel_color.png", normal="panel_normal.png", rough=0.62, metal=0.25, uv_scale=(1.0, 1.0), normal_strength=0.6)
    M["module"] = L.material("IVA_ModulePlate", (0.055, 0.058, 0.062), rough=0.5, metal=0.45)
    M["key_cap"] = L.material("IVA_Keys", tex="keys.png", rough=0.5)
    M["annunc"] = L.material("IVA_Annunciators", tex="annunciators.png", rough=0.25, emit=0.9, emit_tex=True)
    M["digits"] = L.material("IVA_Digits", tex="digits.png", rough=0.15, emit=1.6, emit_tex=True)
    M["btn_soft"] = L.material("IVA_SoftKey", (0.78, 0.78, 0.74), rough=0.55)
    for k in ("systems", "map", "engine", "comms"):
        M["mfd_" + k] = L.material("IVA_MFD_" + k, tex=f"mfd_{k}.png", rough=0.12, emit=1.8, emit_tex=True)


def _at(p, b, x, y, z=0.0):
    return p + b.col[0] * x + b.col[1] * y + b.col[2] * z


def tag(name, q, b, w, h=0.007):
    """Strip of label tape (plain: no words to get wrong)."""
    L.box(name, (w, h, 0.0008), M["btn_soft"], q + b.col[2] * 0.0004, b)


def plate(name, p, b, w, h, depth=0.008, screws=True):
    L.box(name, (w, h, depth), M["module"], _at(p, b, 0, 0, depth / 2), b, bevel=min(0.003, depth * 0.4))
    if screws:
        for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
            L.cylinder(f"{name}Screw{i}", 0.0028, 0.002, M["buckle"], _at(p, b, sx * (w / 2 - 0.007), sy * (h / 2 - 0.007), depth + 0.001), b, segs=8)
    return depth


def mfd(name, p, b, w, h, screen):
    """Multi-function display: screen in a deep bezel, soft keys along the top and bottom, rockers down the sides."""
    d = plate(name + "Plate", p, b, w, h, 0.012)
    s = min(w, h) * 0.66
    L.box(name + "Bezel", (s + 0.01, s + 0.01, 0.006), M["bezel"], _at(p, b, 0, 0, d + 0.003), b, bevel=0.002)
    L.plane(name + "Screen", s, s, M[screen], _at(p, b, 0, 0, d + 0.0065), b)
    kw = s / 5 * 0.7
    for row in (-1, 1):
        for i in range(5):
            x = (i - 2) * s / 5
            L.box(f"{name}Key{row}_{i}", (kw, 0.008, 0.005), M["btn_soft"], _at(p, b, x, row * (s / 2 + 0.014), d + 0.0025), b, bevel=0.0015)
    for col in (-1, 1):
        for i in range(4):
            y = (i - 1.5) * s / 4.5
            L.box(f"{name}Rock{col}_{i}", (0.007, kw * 0.9, 0.005), M["btn_soft"], _at(p, b, col * (s / 2 + 0.013), y, d + 0.0025), b, bevel=0.0015)
    for i, sx in enumerate((-1, 1)):
        L.cylinder(f"{name}Knob{i}", 0.006, 0.008, M["bezel"], _at(p, b, sx * (w / 2 - 0.014), -(h / 2 - 0.014), d + 0.004), b, segs=12, bevel=0.0015)


def annunciators(name, p, b, w, h, cols, rows, start=0):
    """Grid of backlit caution/warning lenses (atlas cells from texgen.annunciators)."""
    d = plate(name + "Plate", p, b, w, h, 0.008)
    cw, ch = (w - 0.016) / cols, (h - 0.016) / rows
    for r in range(rows):
        for c in range(cols):
            k = (start + r * cols + c) % 16
            u0, v1 = (k % 4) / 4, 1 - (k // 4) / 4
            x, y = -w / 2 + 0.008 + cw * (c + 0.5), h / 2 - 0.008 - ch * (r + 0.5)
            L.box(f"{name}Cell{r}_{c}", (cw * 0.92, ch * 0.9, 0.004), M["bezel"], _at(p, b, x, y, d + 0.002), b, bevel=0.001)
            L.plane(f"{name}Lens{r}_{c}", cw * 0.82, ch * 0.78, M["annunc"], _at(p, b, x, y, d + 0.0042), b, (u0 + 0.01, v1 - 0.24, u0 + 0.24, v1 - 0.01))


def keypad(name, p, b, w, h):
    """DSKY-style keypad: three-line digit readout over a 4x4 key grid."""
    d = plate(name + "Plate", p, b, w, h, 0.01)
    dh = h * 0.3
    L.box(name + "DisplayBezel", (w - 0.016, dh, 0.005), M["bezel"], _at(p, b, 0, h / 2 - 0.008 - dh / 2, d + 0.0025), b, bevel=0.0015)
    L.plane(name + "Display", w - 0.024, dh - 0.008, M["digits"], _at(p, b, 0, h / 2 - 0.008 - dh / 2, d + 0.0052), b)
    kh = (h - dh - 0.024) / 4
    kw = (w - 0.016) / 4
    for i in range(16):
        r, c = divmod(i, 4)
        x, y = -w / 2 + 0.008 + kw * (c + 0.5), h / 2 - 0.016 - dh - kh * (r + 0.5)
        L.box(f"{name}Key{i}", (kw * 0.84, kh * 0.84, 0.006), M["module"], _at(p, b, x, y, d + 0.003), b, bevel=0.0015)
        u0, v1 = (i % 4) / 4, 1 - (i // 4) / 4
        L.plane(f"{name}Cap{i}", kw * 0.74, kh * 0.74, M["key_cap"], _at(p, b, x, y, d + 0.0062), b, (u0 + 0.02, v1 - 0.23, u0 + 0.23, v1 - 0.02))


def dial(name, p, b, w, h, kind, r=None):
    d = plate(name + "Plate", p, b, w, h, 0.008)
    r = r or min(w, h) * 0.36
    C.gauge(name, _at(p, b, 0, 0.004, d), b, kind, r=r)
    tag(name + "Tag", _at(p, b, 0, -h / 2 + 0.009, d), b, w * 0.55)


def knobs(name, p, b, w, h, n):
    d = plate(name + "Plate", p, b, w, h, 0.008)
    for i in range(n):
        x = -w / 2 + w * (i + 0.5) / n
        q = _at(p, b, x, 0.004, d)
        L.torus(f"{name}Ring{i}", 0.011, 0.0012, M["toggle"], q + b.col[2] * 0.0008, b, seg=24, mseg=4)
        L.cylinder(f"{name}Knob{i}", 0.0075, 0.012, M["bezel"], q + b.col[2] * 0.006, b, segs=16, bevel=0.002)
        ang = math.radians(40 * ((i * 7) % 5 - 2))
        L.box(f"{name}Ptr{i}", (0.0018, 0.008, 0.002), M["toggle"], q + b.col[2] * 0.0125 + (b.col[1] * math.cos(ang) - b.col[0] * math.sin(ang)) * 0.003,
              L.basis(b.col[0] * math.cos(ang) + b.col[1] * math.sin(ang), b.col[1] * math.cos(ang) - b.col[0] * math.sin(ang), b.col[2]))
    tag(name + "Tag", _at(p, b, 0, -h / 2 + 0.008, d), b, w * 0.7)


def toggles(name, p, b, w, h, cols, rows=1):
    d = plate(name + "Plate", p, b, w, h, 0.008)
    pts = []
    for r in range(rows):
        for c in range(cols):
            x = -w / 2 + w * (c + 0.5) / cols
            y = (h / 2 - 0.006) - (h - 0.012) * (r + 0.5) / rows
            pts.append((_at(p, b, x, y, d), b))
    C.toggles(name, pts, guard_ends=True)


def breakers(name, p, b, w, h, cols, rows):
    d = plate(name + "Plate", p, b, w, h, 0.008)
    pts = []
    for r in range(rows):
        y = (h / 2 - 0.008) - (h - 0.016) * (r + 0.5) / rows
        for c in range(cols):
            pts.append((_at(p, b, -w / 2 + w * (c + 0.5) / cols, y + 0.002, d), b))
        tag(f"{name}Tag{r}", _at(p, b, 0, y - (h - 0.016) / rows * 0.36, d), b, w * 0.88, 0.005)
    C.breakers(name, pts)


def lamps(name, p, b, w, h, n):
    d = plate(name + "Plate", p, b, w, h, 0.006)
    C.lamps(name, [(_at(p, b, -w / 2 + w * (i + 0.5) / n, 0, d), b) for i in range(n)])


def buttons(name, p, b, w, h, n):
    d = plate(name + "Plate", p, b, w, h, 0.006)
    C.push_buttons(name, [(_at(p, b, -w / 2 + w * (i + 0.5) / n, 0, d), b) for i in range(n)])


def vent(name, p, b, w, h, slots=6):
    d = plate(name + "Plate", p, b, w, h, 0.006)
    for i in range(slots):
        y = -h / 2 + h * (i + 0.5) / slots
        L.box(f"{name}Slot{i}", (w * 0.8, h / slots * 0.45, 0.003), M["ring"], _at(p, b, 0, y, d + 0.0005), b)


def screen(name, p, b, w, h, mat):
    """Plain screen module (for the existing CRT pages)."""
    d = plate(name + "Plate", p, b, w, h, 0.01)
    C.crt(name, _at(p, b, 0, 0.006, d), b, M[mat], w=w * 0.82, h=h * 0.7, keys=4)


def navball(name, p, b, w, h):
    d = plate(name + "Plate", p, b, w, h, 0.012)
    r = min(w, h) * 0.34
    L.torus(name + "Collar", r * 1.28, r * 0.12, M["bezel"], _at(p, b, 0, 0, d + 0.002), b, seg=40, mseg=8)
    C.navball(name, _at(p, b, 0, 0, d), b, r=r)


def periscope(name, p, b, w, h):
    d = plate(name + "Plate", p, b, w, h, 0.01)
    C.periscope(name, _at(p, b, 0, 0, d), b, r=min(w, h) * 0.36)


def abort(name, p, b, w, h):
    d = plate(name + "Plate", p, b, w, h, 0.006)
    C.abort_handle(name, _at(p, b, 0, 0, d), b)


KINDS = {"mfd": mfd, "annunciators": annunciators, "keypad": keypad, "dial": dial, "knobs": knobs, "toggles": toggles,
         "breakers": breakers, "lamps": lamps, "buttons": buttons, "vent": vent, "screen": screen, "navball": navball,
         "abort": abort, "periscope": periscope}


def grid(surface, name, cols, rows, items, gap=0.006, border=0.014):
    """Lay modules out on a Surface in a cols x rows grid. items: (kind, col, row, col_span, row_span, kwargs);
    row 0 is the top (screen-up). Each module is reserved on the surface, so overlaps and overhangs are reported."""
    cw, ch = (surface.w - 2 * border) / cols, (surface.h - 2 * border) / rows
    for i, (kind, c, r, cs, rs, kw) in enumerate(items):
        u = -surface.w / 2 + border + cw * (c + cs / 2)
        v = surface.h / 2 - border - ch * (r + rs / 2)
        w, h = cw * cs - gap, ch * rs - gap
        surface.reserve(f"{name}_{kind}{i}", u, v, w / 2 - 0.004, h / 2 - 0.004, margin=0.0)
        p, b = surface.at(u, v)
        KINDS[kind](f"{name}_{kind}{i}", p, b, w, h, **kw)


def band_grid(band, name, centre_deg, z_mid, cols, rows, cell_w, cell_h, items, gap=0.006):
    """The same on a wall Band: cells cell_w (arc metres) x cell_h, centred on centre_deg / z_mid."""
    for i, (kind, c, r, cs, rs, kw) in enumerate(items):
        s = -cols * cell_w / 2 + cell_w * (c + cs / 2)
        z = z_mid + rows * cell_h / 2 - cell_h * (r + rs / 2)
        w, h = cell_w * cs - gap, cell_h * rs - gap
        deg = band.deg(s, z, centre_deg)
        band.reserve(f"{name}_{kind}{i}", deg, z, w / 2 - 0.004, h / 2 - 0.004, margin=0.0)
        p, b = C.frame_at(C.rad(deg), z, band.inset + 0.012)
        KINDS[kind](f"{name}_{kind}{i}", p, b, w, h, **kw)


def wall(name, items, inset=0.03):
    """Wall-mounted equipment: items (kind, deg, z, w, h, kwargs), each a module facing into the cabin."""
    for i, (kind, deg, z, w, h, kw) in enumerate(items):
        p, b = C.frame_at(C.rad(deg), z, inset)
        L.box(f"{name}_{kind}{i}Box", (w + 0.01, h + 0.01, inset - 0.004), M["locker"], p - b.col[2] * (inset / 2), b, bevel=0.004)
        KINDS[kind](f"{name}_{kind}{i}", p, b, w, h, **kw)


def conduit(name, pts, r=0.008, clamps=True):
    """Cable conduit along wall points, with clamps."""
    L.tube(name, pts, r, M["ring"])
    if clamps:
        for k, q in enumerate(pts[1:-1]):
            L.sphere(f"{name}Clamp{k}", r * 1.6, M["rib"], q, u=10, v=6)
