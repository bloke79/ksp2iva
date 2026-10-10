"""Mk1 (pod_1v_conical_crew) interior: a bespoke one-kerbal capsule.

Usage: blender -b --python model_mk1.py -- <spec.json> <texture_dir> <out.blend>

The pod is only ~0.96 m tall inside, so the kerbal lies reclined on a moulded form-fit couch with their head
towards the rear wall, looking straight at a horseshoe instrument panel that wraps round the front with the
porthole set into its centre (the classic one-man capsule layout). Walls are aluminised insulation blanket on
slim stringers; oxygen bottles, a breaker box and wiring looms fill the back; the side hatch is ringed with
explosive bolts; a ring light sits in the domed ceiling.

Coordinates as model_capsule.py: metres, Z up from the hull base, cabin front = -Y, phi 0 = front, +phi = +X.
Spec angles (windows, hatch) are relative to the cabin front and mirrored into Blender (phi = -angle).
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ivalib as L  # noqa: E402  (imports bpy first)
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:]
SPEC = json.load(open(ARGS[0]))
TEX, OUT = ARGS[1], ARGS[2]

L.begin(SPEC["interior"], TEX)
M = L.M
M["blanket"] = L.material("IVA_Blanket", tex="blanket_color.png", normal="blanket_normal.png", rough=0.42, metal=0.6, uv_scale=(1.1, 1.1))
M["shell"] = L.material("IVA_SeatShell", (0.86, 0.86, 0.84), rough=0.3, metal=0.05)
M["bottle"] = L.material("IVA_Bottle", (0.22, 0.42, 0.30), rough=0.35, metal=0.4)
M["periscope"] = L.material("IVA_Periscope", tex="periscope.png", rough=0.1, emit=1.6, emit_tex=True)

_raw = sorted((float(z), float(r)) for z, r in SPEC["profile"])
# the measured profile is a max-per-slice sample with small bumps; a light moving average keeps walls fair
PROFILE = [(z, r if i in (0, len(_raw) - 1) else (_raw[i - 1][1] + 2 * r + _raw[i + 1][1]) / 4) for i, (z, r) in enumerate(_raw)]
WALL = 0.04
Z_FLOOR = SPEC["floor"]
Z_CEIL = 0.82
Z_TOP = 0.90
SEG = 112


def r_out(z):
    if z <= PROFILE[0][0]:
        return PROFILE[0][1]
    for (z0, r0), (z1, r1) in zip(PROFILE, PROFILE[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / max(1e-6, z1 - z0)
    return PROFILE[-1][1]


def r_in(z):
    return r_out(z) - WALL


def polar(phi, r, z):
    return Vector((r * math.sin(phi), -r * math.cos(phi), z))


def rad(deg):
    return math.radians(deg)


def ang_dist(a, b):
    return abs(((a - b + math.pi) % (2 * math.pi)) - math.pi)


def frame_at(phi, z, inset):
    """Basis on a surface parallel to the wall, `inset` in from it: right (as seen from inside), up along the slope, normal into the cabin."""
    tangent = Vector((-math.cos(phi), -math.sin(phi), 0))
    dz = 0.01
    up = (polar(phi, r_in(z + dz) - inset, z + dz) - polar(phi, r_in(z - dz) - inset, z - dz)).normalized()
    normal = tangent.cross(up).normalized()
    if normal.dot(Vector((-math.sin(phi), math.cos(phi), 0))) < 0:
        normal = -normal
    return polar(phi, r_in(z) - inset, z), L.basis(tangent, up, normal)


# ------------------------------------------------------------------ openings
W = SPEC["windows"][0]
WIN_PHI = rad(-W["angle"])
WIN_Z, WIN_HW, WIN_HH, WIN_C = W["z"], W["half_w"], W["half_h"], W.get("corner", 0.03)
H = SPEC["hatch"]
HATCH_PHI = rad(-H["angle"])
HATCH_HALF = rad(13)
HATCH_Z0, HATCH_Z1 = 0.13, 0.60


def window_sdf(phi, z, r_at, grow=0.0):
    s = ((phi - WIN_PHI + math.pi) % (2 * math.pi) - math.pi) * r_at
    hw, hh, c = WIN_HW + grow, WIN_HH + grow, WIN_C + grow
    qx, qy = abs(s) - (hw - c), abs(z - WIN_Z) - (hh - c)
    return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - c


def window_outline(inset, grow=0.0, n=48):
    pts = []
    hw, hh, c = WIN_HW + grow, WIN_HH + grow, WIN_C + grow
    for cx, cy, a0 in ((hw - c, hh - c, 0), (-(hw - c), hh - c, 90), (-(hw - c), -(hh - c), 180), (hw - c, -(hh - c), 270)):
        for i in range(n // 4 + 1):
            a = rad(a0 + 90 * i / (n // 4))
            z = WIN_Z + cy + c * math.sin(a)
            pts.append(polar(WIN_PHI + (cx + c * math.cos(a)) / (r_in(z) - inset), r_in(z) - inset, z))
    return pts


# ------------------------------------------------------------------ shell, ceiling dome, floor
def build_shell():
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rings = 40
    zs = [Z_FLOOR - 0.01 + (Z_CEIL + 0.02 - Z_FLOOR) * i / rings for i in range(rings + 1)]
    grid = [[bm.verts.new(polar(2 * math.pi * j / SEG, r_in(z), z)) for j in range(SEG)] for z in zs]
    circ = 2 * math.pi * r_in(0.45)
    for i in range(rings):
        for j in range(SEG):
            pc, zc = 2 * math.pi * (j + 0.5) / SEG, (zs[i] + zs[i + 1]) / 2
            if window_sdf(pc, zc, r_in(zc), grow=0.018) < 0:
                continue
            jn = (j + 1) % SEG
            f = bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][jn], grid[i][jn]))
            for l in f.loops:
                vj = grid[i].index(l.vert) if l.vert in grid[i] else grid[i + 1].index(l.vert)
                u = (vj if not (j == SEG - 1 and vj == 0) else SEG) / SEG * circ / 0.5
                l[uv].uv = (u, l.vert.co.z / 0.5)
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(Vector((-c.x, -c.y, 0))) < 0:
            f.normal_flip()
    L.smooth(L.solidify(L.mesh_obj("Shell", bm, [M["blanket"]]), 0.02), 30)

    # domed ceiling up to the parachute bulkhead
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rings_d = 8
    rows = []
    for i in range(rings_d + 1):
        t = i / rings_d
        z = Z_CEIL + (Z_TOP - Z_CEIL) * math.sin(t * math.pi / 2)
        r = r_in(Z_CEIL) * math.cos(t * math.pi / 2 * 0.92)
        rows.append([bm.verts.new(polar(2 * math.pi * j / SEG, r, z)) for j in range(SEG)])
    for i in range(rings_d):
        for j in range(SEG):
            jn = (j + 1) % SEG
            f = bm.faces.new((rows[i][j], rows[i][jn], rows[i + 1][jn], rows[i + 1][j]))
            for l in f.loops:
                l[uv].uv = (l.vert.co.x * 2, l.vert.co.y * 2)
    bm.normal_update()
    for f in bm.faces:
        if f.normal.z > 0:
            f.normal_flip()
    L.smooth(L.mesh_obj("Dome", bm, [M["blanket"]]), 40)
    top_r = r_in(Z_CEIL) * math.cos(math.pi / 2 * 0.92)
    L.disc("ChuteBulkhead", top_r + 0.002, M["ring"], (0, 0, Z_TOP - 0.002), Matrix.Rotation(math.pi, 3, "X"))
    for k in range(6):
        a = k * math.pi / 3
        L.cylinder(f"ChuteBolt_{k}", 0.006, 0.01, M["buckle"], (top_r * 0.7 * math.cos(a), top_r * 0.7 * math.sin(a), Z_TOP - 0.006), segs=8)
    # ring light round the dome
    zl = Z_CEIL + 0.03
    L.torus("RingLightHousing", r_in(zl) - 0.07, 0.016, M["ring"], (0, 0, zl), Matrix.Identity(3), seg=64, mseg=10)
    L.torus("RingLight", r_in(zl) - 0.07, 0.008, M["light"], (0, 0, zl - 0.012), Matrix.Identity(3), seg=64, mseg=8)

    # dished floor bulkhead with a grate
    rf = r_in(Z_FLOOR)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    centre = bm.verts.new((0, 0, Z_FLOOR - 0.02))
    ring = [bm.verts.new(polar(2 * math.pi * j / SEG, rf, Z_FLOOR)) for j in range(SEG)]
    for j in range(SEG):
        f = bm.faces.new((centre, ring[j], ring[(j + 1) % SEG]))
        for l in f.loops:
            l[uv].uv = (l.vert.co.x * 2, l.vert.co.y * 2)
    bm.normal_update()
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    L.mesh_obj("Floor", bm, [M["floor"]])
    L.tube("FloorRim", [polar(2 * math.pi * j / 64, rf - 0.012, Z_FLOOR + 0.008) for j in range(65)], 0.012, M["ring"])


def ribbon(name, phi, z0, z1, half_w, inset, mat, thick=0.006, steps=16):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rows = []
    for i in range(steps + 1):
        z = z0 + (z1 - z0) * i / steps
        r = r_in(z) - inset
        rows.append((bm.verts.new(polar(phi - half_w / r, r, z)), bm.verts.new(polar(phi + half_w / r, r, z))))
    for i in range(steps):
        f = bm.faces.new((rows[i][0], rows[i][1], rows[i + 1][1], rows[i + 1][0]))
        for l in f.loops:
            l[uv].uv = (0.5, l.vert.co.z)
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(Vector((-c.x, -c.y, 0))) < 0:
            f.normal_flip()
    return L.smooth(L.solidify(L.mesh_obj(name, bm, [mat]), thick), 30)


def build_stringers():
    for k in range(10):
        phi = 2 * math.pi * (k + 0.5) / 10
        if ang_dist(phi, HATCH_PHI) < HATCH_HALF + rad(6):
            continue
        if ang_dist(phi, WIN_PHI) < rad(14):
            continue
        ribbon(f"Stringer_{k}", phi, Z_FLOOR, Z_CEIL, 0.011, 0.004, M["rib"])
        # rivet line
        for i in range(6):
            z = Z_FLOOR + 0.06 + i * (Z_CEIL - Z_FLOOR - 0.12) / 5
            p, b = frame_at(phi, z, 0.011)
            L.cylinder(f"Rivet_{k}_{i}", 0.0035, 0.004, M["buckle"], p, b, segs=8)


# ------------------------------------------------------------------ horseshoe instrument panel
P_FROM, P_TO = rad(-72), rad(40)      # Blender phi; the hatch side (+X) is kept clear
P_Z0, P_Z1 = 0.24, 0.66
P_INSET = 0.05


def panel_point(deg, z, lift=0.0):
    p, b = frame_at(rad(deg), z, P_INSET + 0.012 + lift)
    return p, b


def build_panel():
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    ns, nz = 96, 32
    grid = [[bm.verts.new(polar(P_FROM + (P_TO - P_FROM) * j / ns, r_in(P_Z0 + (P_Z1 - P_Z0) * i / nz) - P_INSET, P_Z0 + (P_Z1 - P_Z0) * i / nz))
             for j in range(ns + 1)] for i in range(nz + 1)]
    for i in range(nz):
        for j in range(ns):
            pc = P_FROM + (P_TO - P_FROM) * (j + 0.5) / ns
            zc = P_Z0 + (P_Z1 - P_Z0) * (i + 0.5) / nz
            if window_sdf(pc, zc, r_in(zc) - P_INSET, grow=0.012) < 0:
                continue
            f = bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
            for l in f.loops:
                l[uv].uv = (j / ns, i / nz)
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(Vector((-c.x, -c.y, 0))) < 0:
            f.normal_flip()
    L.smooth(L.solidify(L.mesh_obj("Panel", bm, [M["console"]]), 0.022), 30)
    # chrome edge trims
    for name, z in (("PanelTrimTop", P_Z1), ("PanelTrimBottom", P_Z0)):
        L.tube(name, [polar(P_FROM + (P_TO - P_FROM) * j / 64, r_in(z) - P_INSET - 0.004, z) for j in range(65)], 0.008, M["rib"])
    for name, phi in (("PanelEndL", P_FROM), ("PanelEndR", P_TO)):
        L.tube(name, [polar(phi, r_in(z) - P_INSET - 0.004, z) for z in (P_Z0, (P_Z0 + P_Z1) / 2, P_Z1)], 0.008, M["rib"])
        # side cheek closing the gap to the wall
        bm = bmesh.new()
        uv = bm.loops.layers.uv.new("UVMap")
        vs = [bm.verts.new(polar(phi, r_in(z) - d, z)) for z, d in ((P_Z0, 0.0), (P_Z0, P_INSET), (P_Z1, P_INSET), (P_Z1, 0.0))]
        f = bm.faces.new(vs)
        for l in f.loops:
            l[uv].uv = (l.vert.co.x, l.vert.co.z)
        L.mesh_obj(name + "Cheek", bm, [M["console"]])
    # window sleeve: loft from the panel opening back to the hull opening, with a bolted frame
    outer = window_outline(-0.035, grow=0.004, n=48)   # runs out through the hull opening
    inner = window_outline(P_INSET, grow=0.012, n=48)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    a = [bm.verts.new(p) for p in outer]
    b = [bm.verts.new(p) for p in inner]
    n = len(a)
    for i in range(n):
        f = bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
        for l in f.loops:
            l[uv].uv = (i / n, 0 if l.vert in a else 1)
    bm.normal_update()
    L.smooth(L.mesh_obj("WindowSleeve", bm, [M["bezel"]]), 40)
    L.tube("WindowFrame", window_outline(P_INSET + 0.006, grow=0.016, n=48), 0.011, M["rib"], closed=True)
    for k, p in enumerate(window_outline(P_INSET + 0.012, grow=0.03, n=24)[::2]):
        phi = math.atan2(p.x, -p.y)
        q, bb = frame_at(phi, p.z, P_INSET + 0.012)
        L.cylinder(f"WindowBolt_{k}", 0.004, 0.008, M["buckle"], p, bb, segs=8)


# Footprints on the panel, in (degrees round the axis, height): every instrument reserves its outline plus a margin,
# and the porthole (opening + frame + bolt ring) is a keep-out zone. Overlaps are reported, not silently drawn.
FOOT = []
MARGIN = 0.008


def panel_r(z):
    return r_in(z) - P_INSET - 0.012


def reserve(name, deg, z, half_w, half_h):
    hd = math.degrees((half_w + MARGIN) / panel_r(z))
    FOOT.append((name, deg - hd, deg + hd, z - half_h - MARGIN, z + half_h + MARGIN))


def check_layout():
    problems = []
    lo, hi = math.degrees(P_FROM), math.degrees(P_TO)
    for n, d0, d1, z0, z1 in FOOT:
        if d0 < lo or d1 > hi or z0 < P_Z0 or z1 > P_Z1:
            problems.append(f"{n} runs off the panel ({d0:.1f}..{d1:.1f} deg, z {z0:.3f}..{z1:.3f})")
    for i, a in enumerate(FOOT):
        for b in FOOT[i + 1:]:
            if a[1] < b[2] and b[1] < a[2] and a[3] < b[4] and b[3] < a[4]:
                problems.append(f"{a[0]} overlaps {b[0]}")
    for n, d0, d1, z0, z1 in FOOT:
        print(f"   foot {n:14s} {d0:6.1f}..{d1:6.1f} deg  z {z0:.3f}..{z1:.3f}")
    print("panel layout:", "OK, no overlaps" if not problems else "PROBLEMS")
    for p in problems:
        print("  ", p)
    return problems


def at(s_m, z):
    """Panel angle (deg) for an arc distance s_m (metres) from the panel centre line at height z."""
    return math.degrees(s_m / panel_r(z))


def build_instruments():
    # porthole keep-out: opening + frame (grow 0.016 + tube 0.011) + bolt ring (grow 0.03 + bolt 0.004)
    reserve("Porthole", 0.0, WIN_Z, WIN_HW + 0.036, WIN_HH + 0.036)

    # --- negative side (on the right as seen from the couch): navball over periscope, clock, gauges, abort, breakers
    deg = at(-0.185, 0.47)
    p, b = panel_point(deg, 0.47)
    reserve("Navball", deg, 0.47, 0.053, 0.053)
    L.sphere("Navball", 0.04, M["navball"], p + b.col[2] * 0.012, b @ Matrix.Rotation(rad(25), 3, "Z"), u=40, v=20)
    L.torus("NavballBezel", 0.045, 0.008, M["bezel"], p + b.col[2] * 0.014, b, seg=40)
    for side in (-1, 1):
        L.box(f"NavballChevron{side}", (0.018, 0.004, 0.003), M["btn_amber"], p + b.col[2] * 0.052 + b.col[0] * side * 0.007 - b.col[1] * 0.004,
              L.basis((b.col[0] * math.cos(rad(35)) + b.col[1] * side * math.sin(rad(35))).normalized(),
                      (b.col[1] * math.cos(rad(35)) - b.col[0] * side * math.sin(rad(35))).normalized(), b.col[2]))
    deg = at(-0.21, 0.325)
    p, b = panel_point(deg, 0.325)
    reserve("Periscope", deg, 0.325, 0.06, 0.06)
    L.disc("PeriscopeScreen", 0.041, M["periscope"], p + b.col[2] * 0.004, b)
    L.torus("PeriscopeBezel", 0.045, 0.006, M["bezel"], p + b.col[2] * 0.004, b, seg=40)
    L.torus("PeriscopeHood", 0.05, 0.009, M["console"], p + b.col[2] * 0.012, b, seg=40, mseg=8)
    deg = at(-0.185, 0.605)
    p, b = panel_point(deg, 0.605)
    reserve("Clock", deg, 0.605, 0.027, 0.027)
    L.disc("Clock", 0.02, M["gauge_press"], p + b.col[2] * 0.003, b)
    L.torus("ClockBezel", 0.023, 0.004, M["bezel"], p + b.col[2] * 0.003, b, seg=28, mseg=6)
    for g, (sx, z) in zip(("alt", "press", "temp", "fuel"), ((-0.292, 0.515), (-0.292, 0.432), (-0.366, 0.515), (-0.366, 0.432))):
        deg = at(sx, z)
        p, b = panel_point(deg, z)
        reserve("Gauge_" + g, deg, z, 0.028, 0.028)
        L.disc(f"Gauge_{g}", 0.022, M["gauge_" + g], p + b.col[2] * 0.003, b)
        L.torus(f"GaugeBezel_{g}", 0.024, 0.004, M["bezel"], p + b.col[2] * 0.003, b, seg=32, mseg=8)
    deg = at(-0.335, 0.33)
    p, b = panel_point(deg, 0.33)
    reserve("Abort", deg, 0.32, 0.0375, 0.053)
    L.plane("AbortPlate", 0.075, 0.055, M["hazard"], p + b.col[2] * 0.002, b, (0, 0, 1, 1))
    L.cylinder("AbortShaft", 0.006, 0.05, M["rib"], p + b.col[2] * 0.026, b, segs=12)
    # the T bar lies across the panel: cylinder axis (local Z) along the panel's right vector
    L.cylinder("AbortTee", 0.009, 0.075, M["red"], p + b.col[2] * 0.052, L.basis(b.col[1], b.col[2], b.col[0]), segs=16, bevel=0.002)
    p2, b2 = panel_point(at(-0.335, 0.277), 0.277)
    L.plane("AbortLabel", 0.05, 0.02, M["labels"], p2 + b2.col[2] * 0.002, b2, (0.02, 0.81, 0.23, 0.94))
    breakers = [-0.43 - k * 0.022 for k in range(3)]
    reserve("Breakers", at((breakers[0] + breakers[-1]) / 2, 0.29), 0.29, 0.011 + 0.022, 0.011)
    for k, sx in enumerate(breakers):
        p, b = panel_point(at(sx, 0.29), 0.29)
        L.cylinder(f"Breaker_{k}", 0.006, 0.01, M["bezel"], p, b, segs=10)
        L.cylinder(f"BreakerCap_{k}", 0.0035, 0.008, M["toggle"], p + b.col[2] * 0.007, b, segs=8)

    # --- positive side (on the left from the couch, up to the hatch): CRT, status lights, toggle bank
    deg = at(0.172, 0.50)
    p, b = panel_point(deg, 0.50)
    reserve("AttitudeCRT", deg, 0.487, 0.045, 0.054)
    L.box("AttitudeBezel", (0.09, 0.066, 0.014), M["bezel"], p, b, bevel=0.004)
    L.plane("AttitudeScreen", 0.077, 0.053, M["crt_att"], p + b.col[2] * 0.0075, b)
    for k in range(4):
        L.box(f"AttitudeKey_{k}", (0.013, 0.008, 0.006), M["bezel"], p - b.col[1] * 0.044 + b.col[0] * (-0.027 + k * 0.018), b, bevel=0.0015)
    lamps = (M["btn_green"], M["btn_amber"], M["btn_red"])
    reserve("Telelights", at(0.16, 0.612), 0.612, 0.03, 0.01)
    for k, mat in enumerate(lamps):
        p, b = panel_point(at(0.14 + k * 0.02, 0.612), 0.612)
        L.box(f"Telelight_{k}", (0.017, 0.016, 0.006), M["bezel"], p, b, bevel=0.002)
        L.box(f"TelelightLens_{k}", (0.013, 0.011, 0.004), mat, p + b.col[2] * 0.004, b, bevel=0.0015)
    toggles = [0.158 + k * 0.016 for k in range(5)]
    reserve("Toggles", at(0.19, 0.335), 0.335, 0.04, 0.02)
    for k, sx in enumerate(toggles):
        p, b = panel_point(at(sx, 0.33), 0.33)
        L.box(f"ToggleBase_{k}", (0.012, 0.018, 0.006), M["bezel"], p, b, bevel=0.0015)
        lever = L.basis(b.col[0], (b.col[1] * 0.5 + b.col[2]).normalized(), (b.col[2] * 0.5 - b.col[1]).normalized())
        L.cylinder(f"Toggle_{k}", 0.0025, 0.022, M["toggle"], p + b.col[2] * 0.011 + b.col[1] * 0.004, lever, segs=8)
        if k in (0, len(toggles) - 1):
            L.tube(f"Guard_{k}", [p - b.col[0] * 0.009, p - b.col[0] * 0.009 + b.col[2] * 0.02,
                                  p + b.col[0] * 0.009 + b.col[2] * 0.02, p + b.col[0] * 0.009], 0.002, M["red"])

    # --- above and below the porthole: name plate, sequence buttons
    p, b = panel_point(0, 0.632)
    reserve("NamePlate", 0, 0.632, 0.06, 0.015)
    L.plane("NamePlate", 0.12, 0.03, M["plate"], p + b.col[2] * 0.002, b)
    reserve("SeqButtons", 0, 0.27, 0.044, 0.014)
    for k, (sx, mat) in enumerate(((-0.03, M["btn_amber"]), (0.0, M["btn_green"]), (0.03, M["btn_blue"]))):
        p, b = panel_point(at(sx, 0.27), 0.27)
        L.cylinder(f"SeqCollar_{k}", 0.014, 0.008, M["bezel"], p + b.col[2] * 0.003, b, segs=20)
        L.cylinder(f"SeqButton_{k}", 0.009, 0.01, mat, p + b.col[2] * 0.008, b, segs=20, bevel=0.002)
    check_layout()


# ------------------------------------------------------------------ form-fit couch
HIP = Vector((0.0, -0.04, 0.19))
# The surface the kerbal lies on, feet -> head, in (y, z) world coordinates (x is across the couch).
COUCH = [(-0.40, 0.12), (-0.34, 0.20), (-0.28, 0.27), (-0.16, 0.235), (-0.04, 0.19), (0.07, 0.25), (0.17, 0.32), (0.25, 0.39), (0.32, 0.45)]
TAPER = [0.55, 0.6, 0.66, 0.85, 1.0, 1.0, 1.0, 0.92, 0.66]
COUCH_W = 0.34


def sweep(name, profile, thick, width, mat, taper, bolster=0.0, x_off=0.0, bevel=0.012):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    n = len(profile)
    top, bot = [], []
    for i, (y, z) in enumerate(profile):
        a, b = profile[max(i - 1, 0)], profile[min(i + 1, n - 1)]
        ty, tz = b[0] - a[0], b[1] - a[1]
        l = math.hypot(ty, tz) or 1
        ny, nz = tz / l, -ty / l           # points away from the sitting surface (down/back)
        top.append((y, z))
        bot.append((y + ny * thick, z + nz * thick))

    def xs(i):
        hw = width * taper[i] / 2
        return [-hw, -hw + 0.05, hw - 0.05, hw]
    lift = [bolster, 0.0, 0.0, bolster]
    gt = [[bm.verts.new((x + x_off, y, z + lf)) for x, lf in zip(xs(i), lift)] for i, (y, z) in enumerate(top)]
    gb = [[bm.verts.new((x + x_off, y, z)) for x in (xs(i)[0], xs(i)[3])] for i, (y, z) in enumerate(bot)]
    for i in range(n - 1):
        for q in range(3):
            bm.faces.new((gt[i][q], gt[i][q + 1], gt[i + 1][q + 1], gt[i + 1][q]))
        bm.faces.new((gb[i][1], gb[i][0], gb[i + 1][0], gb[i + 1][1]))
        bm.faces.new((gt[i][0], gt[i + 1][0], gb[i + 1][0], gb[i][0]))
        bm.faces.new((gt[i + 1][3], gt[i][3], gb[i][1], gb[i + 1][1]))
    for i in (0, n - 1):
        bm.faces.new((gt[i][0], gt[i][1], gt[i][2], gt[i][3], gb[i][1], gb[i][0]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        for l in f.loops:
            l[uv].uv = (l.vert.co.x + 0.5, l.vert.co.y + l.vert.co.z)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=1, use_grid_fill=True)
    obj = L.mesh_obj(name, bm, [mat])
    if bevel:
        L.add_bevel(obj, bevel, 3)
    return L.smooth(obj, 60)


def surface_normal(i):
    a, b = COUCH[max(i - 1, 0)], COUCH[min(i + 1, len(COUCH) - 1)]
    ty, tz = b[0] - a[0], b[1] - a[1]
    l = math.hypot(ty, tz)
    return Vector((0, -tz / l, ty / l))     # up/away from the couch surface (towards the kerbal)


def build_couch():
    # moulded fibreglass shell under a padded liner, high side bolsters
    sweep("CouchShell", [(y + 0.0, z - 0.035) for y, z in COUCH], 0.025, COUCH_W + 0.07, M["shell"], TAPER, bolster=0.13, bevel=0.01)
    sweep("CouchLiner", COUCH, 0.035, COUCH_W, M["cushion"], TAPER, bolster=0.085, bevel=0.014)
    # headrest pad
    hy, hz = COUCH[-1]
    sweep("Headrest", [(hy - 0.05, hz - 0.03), (hy + 0.02, hz + 0.03)], 0.04, 0.17, M["cushion"], [1, 1], bevel=0.01)
    # supports: two struts from the shell to the floor, one to the back wall
    for x in (-0.11, 0.11):
        for (y, z) in (COUCH[3], COUCH[5]):
            top = Vector((x, y + 0.02, z - 0.07))
            L.tube(f"CouchStrut_{x}_{y}", [top, Vector((x, y + 0.02, Z_FLOOR + 0.005))], 0.011, M["couchframe"])
            L.cylinder(f"CouchFoot_{x}_{y}", 0.022, 0.012, M["couchframe"], (x, y + 0.02, Z_FLOOR + 0.006))
    by, bz = COUCH[7]
    L.tube("CouchBackStrut", [Vector((0, by + 0.05, bz - 0.05)), polar(math.pi, r_in(bz - 0.08) - 0.01, bz - 0.08)], 0.012, M["couchframe"])
    # harness: shoulder straps, lap belt, buckle
    for side in (-1, 1):
        L.tube(f"Shoulder{side}", [Vector((side * 0.06, y, z + 0.006)) + surface_normal(i) * 0.012 for i, (y, z) in enumerate(COUCH) if i >= 4], 0.006, M["strap"], bevel_res=1)
    ly, lz = COUCH[4]
    L.tube("LapBelt", [Vector((x, ly - 0.01, lz + 0.045)) for x in (-0.16, -0.07, 0, 0.07, 0.16)], 0.007, M["strap"], bevel_res=1)
    L.box("Buckle", (0.04, 0.025, 0.012), M["buckle"], (0, ly - 0.01, lz + 0.05), bevel=0.003)
    # armrests; hand controller on the right, rotary selector on the left
    for side in (-1, 1):
        x = side * 0.205
        L.box(f"Armrest{side}", (0.04, 0.24, 0.03), M["couchframe"], (x, -0.07, 0.29), bevel=0.008)
        L.box(f"ArmPad{side}", (0.034, 0.2, 0.012), M["cushion"], (x, -0.07, 0.31), bevel=0.004)
        L.tube(f"ArmPost{side}", [Vector((x, 0.02, 0.28)), Vector((side * 0.17, 0.04, 0.2))], 0.008, M["couchframe"])
    L.cylinder("StickBase", 0.022, 0.02, M["bezel"], (0.205, -0.15, 0.325), segs=20)
    L.tube("StickBoot", [Vector((0.205, -0.15, 0.33)), Vector((0.205, -0.152, 0.36))], 0.011, M["handle"])
    L.sphere("StickGrip", 0.019, M["handle"], (0.205, -0.154, 0.383))
    L.box("StickTrigger", (0.008, 0.012, 0.016), M["red"], (0.205, -0.172, 0.378), bevel=0.002)
    L.cylinder("SelectorKnob", 0.016, 0.018, M["bezel"], (-0.205, -0.15, 0.33), segs=16, bevel=0.003)
    L.box("SelectorPointer", (0.004, 0.018, 0.004), M["toggle"], (-0.205, -0.157, 0.341))


def couch_fit_report():
    worst = 1e9
    for i, ((y, z), t) in enumerate(zip(COUCH, TAPER)):
        hw = (COUCH_W + 0.07) * t / 2
        for x in (-hw, 0, hw):
            for dz in (-0.07, 0.09):
                p = Vector((x, y, z + dz))
                worst = min(worst, r_in(p.z) - math.hypot(p.x, p.y))
    print(f"couch clearance to wall (min): {worst * 100:.1f} cm")
    return worst


# ------------------------------------------------------------------ hatch with explosive bolts
def build_hatch():
    phi0, phi1 = HATCH_PHI - HATCH_HALF, HATCH_PHI + HATCH_HALF
    z0, z1, inset, c = HATCH_Z0, HATCH_Z1, 0.018, 0.05
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    ns, nz = 24, 30
    grid = [[bm.verts.new(polar(phi0 + (phi1 - phi0) * j / ns, r_in(z0 + (z1 - z0) * i / nz) - inset, z0 + (z1 - z0) * i / nz)) for j in range(ns + 1)] for i in range(nz + 1)]
    for i in range(nz):
        for j in range(ns):
            f = bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
            for l in f.loops:
                l[uv].uv = (j / ns, i / nz)
    bm.normal_update()
    for f in bm.faces:
        cc = f.calc_center_median()
        if f.normal.dot(Vector((-cc.x, -cc.y, 0))) < 0:
            f.normal_flip()
    L.smooth(L.add_bevel(L.solidify(L.mesh_obj("HatchDoor", bm, [M["hatch"]]), 0.025), 0.006, 2), 30)
    edge = [polar(phi0 + (phi1 - phi0) * t / 30, r_in(z0) - inset - 0.012, z0) for t in range(31)]
    edge += [polar(phi1, r_in(z0 + (z1 - z0) * t / 30) - inset - 0.012, z0 + (z1 - z0) * t / 30) for t in range(1, 31)]
    edge += [polar(phi1 - (phi1 - phi0) * t / 30, r_in(z1) - inset - 0.012, z1) for t in range(1, 31)]
    edge += [polar(phi0, r_in(z1 - (z1 - z0) * t / 30) - inset - 0.012, z1 - (z1 - z0) * t / 30) for t in range(1, 30)]
    L.tube("HatchSeal", edge, 0.01, M["ring"], closed=True)
    for k, p in enumerate(edge[::5]):
        phi = math.atan2(p.x, -p.y)
        q, b = frame_at(phi, p.z, inset + 0.02)
        L.cylinder(f"HatchBolt_{k}", 0.006, 0.014, M["buckle"], q, b, segs=8)
        L.cylinder(f"HatchBoltCap_{k}", 0.004, 0.006, M["red"], q + b.col[2] * 0.009, b, segs=8)
    # release: yellow T-handle in a recess, hazard stripe, label
    zc = (z0 + z1) / 2
    p, b = frame_at(HATCH_PHI, zc, inset + 0.03)
    L.box("HatchRecess", (0.09, 0.06, 0.012), M["bezel"], p, b, bevel=0.004)
    L.cylinder("HatchReleaseShaft", 0.005, 0.03, M["rib"], p + b.col[2] * 0.016, b, segs=10)
    L.cylinder("HatchReleaseTee", 0.008, 0.07, M["yellow"], p + b.col[2] * 0.032, L.basis(b.col[1], b.col[2], b.col[0]), segs=14, bevel=0.002)
    p, b = frame_at(HATCH_PHI, zc + 0.1, inset + 0.028)
    L.plane("HatchHazard", 0.17, 0.035, M["hazard"], p, b, (0, 0, 1, 0.5))


# ------------------------------------------------------------------ equipment round the back
def build_equipment():
    # oxygen bottles strapped to the left-rear wall
    for k, z in enumerate((0.17, 0.26)):
        phi = rad(-128)
        p, b = frame_at(phi, z, 0.045)
        L.cylinder(f"O2Bottle_{k}", 0.035, 0.2, M["bottle"], p, L.basis(b.col[1], b.col[2], b.col[0]), segs=24, bevel=0.006)
        L.cylinder(f"O2Valve_{k}", 0.012, 0.03, M["rib"], p + b.col[0] * 0.115, L.basis(b.col[1], b.col[2], b.col[0]), segs=12)
        for s in (-0.06, 0.06):
            L.torus(f"O2Strap_{k}_{s}", 0.037, 0.004, M["handle"], p + b.col[0] * s, L.basis(b.col[1], b.col[2], b.col[0]) @ Matrix.Rotation(math.pi / 2, 3, "Y"), seg=24, mseg=6)
    # breaker box on the right-rear wall
    p, b = frame_at(rad(128), 0.3, 0.04)
    L.box("BreakerBox", (0.19, 0.13, 0.06), M["locker"], p, b, bevel=0.006)
    for row in range(2):
        for col in range(5):
            q = p + b.col[2] * 0.032 + b.col[0] * (-0.068 + col * 0.034) + b.col[1] * (0.025 - row * 0.045)
            L.cylinder(f"BoxBreaker_{row}_{col}", 0.007, 0.01, M["bezel"], q, b, segs=10)
            L.cylinder(f"BoxBreakerCap_{row}_{col}", 0.004, 0.008, M["toggle"], q + b.col[2] * 0.007, b, segs=8)
    q = p + b.col[2] * 0.031 + b.col[1] * 0.055
    L.plane("BoxLabel", 0.12, 0.022, M["plate"], q, b)
    # wiring looms round the back at floor level, clamped to the stringers
    for k, (dz, dr) in enumerate(((0.0, 0.0), (0.018, 0.004), (0.009, 0.016))):
        L.tube(f"Loom_{k}", [polar(rad(a), r_in(0.13 + dz) - 0.02 - dr, 0.13 + dz) for a in range(80, 281, 10)], 0.007, M["cable"])
    for a in range(90, 280, 36):
        p, b = frame_at(rad(a), 0.14, 0.03)
        L.box(f"LoomClamp_{a}", (0.015, 0.04, 0.03), M["rib"], p, b, bevel=0.003)
    # two small spot lamps high on the side walls
    for side in (-1, 1):
        phi = rad(side * 100)
        p, b = frame_at(phi, 0.72, 0.03)
        L.cylinder(f"SpotHousing{side}", 0.022, 0.03, M["ring"], p, b, segs=20, radius2=0.018)
        L.disc(f"SpotLens{side}", 0.016, M["light"], p + b.col[2] * 0.0155, b, segs=20)


# ------------------------------------------------------------------ build
build_shell()
build_stringers()
build_panel()
build_instruments()
build_couch()
couch_fit_report()
build_hatch()
build_equipment()

# eye point: just above the headrest, along the couch surface normal
hy, hz = COUCH[-1]
eye = Vector((0, hy, hz)) + surface_normal(len(COUCH) - 1) * 0.085 + Vector((0, -0.03, 0))
print(f"eye at y {eye.y:.3f} z {eye.z:.3f}; wall clearance {r_in(eye.z) - abs(eye.y):.3f} m; ceiling clearance {Z_CEIL - eye.z:.3f} m")
L.seat_marker(0, eye)
L.save(OUT)
