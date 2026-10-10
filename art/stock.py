"""Stock-KSP2-style structure and dressing: chamfered ribs, ring frames and beams, colour-coded cable bundles with ties
and sockets, bolted inspection plates, ceiling light fixtures, floor hatches and foot restraints.

The stock interiors get their look from modelled detail rather than texture: every unit is a chamfered housing, thick
coloured cables loop between units, and no surface is left bare. Pieces here follow that. `Clearance` lets structure
added last (ribs, frames, plates) stop short of equipment that is already in place instead of cutting through it.
"""
import math
import random

import ivalib as L  # imports bpy first
import bmesh
import capsule as C
from mathutils import Matrix, Vector

M = L.M
CABLES = ("cable_k", "cable_r", "cable_g", "cable_y", "cable_k")


def materials():
    M["frame"] = L.material("IVA_Frame", (0.52, 0.53, 0.55), rough=0.5, metal=0.3)
    M["frame_dark"] = L.material("IVA_FrameDark", (0.10, 0.105, 0.115), rough=0.5, metal=0.4)
    M["cable_k"] = L.material("IVA_CableBlack", (0.02, 0.02, 0.022), rough=0.45)
    M["cable_r"] = L.material("IVA_CableRed", (0.42, 0.035, 0.025), rough=0.45)
    M["cable_g"] = L.material("IVA_CableGreen", (0.035, 0.28, 0.06), rough=0.45)
    M["cable_y"] = L.material("IVA_CableYellow", (0.68, 0.52, 0.04), rough=0.45)
    M["diffuser"] = L.material("IVA_LightPanel", (1.0, 0.92, 0.78), rough=0.3, emit=2.2)


# ------------------------------------------------------------------ sweeps
def chamfer_rect(w, h, c=None):
    c = min(c if c is not None else min(w, h) * 0.22, w * 0.45, h * 0.45)
    return [(-w / 2 + c, -h / 2), (w / 2 - c, -h / 2), (w / 2, -h / 2 + c), (w / 2, h / 2 - c),
            (w / 2 - c, h / 2), (-w / 2 + c, h / 2), (-w / 2, h / 2 - c), (-w / 2, -h / 2 + c)]


def sweep(name, pts, normals, profile, mat, closed=False, caps=True):
    """Extrude a 2D profile (u across, v along `normals`) along a polyline. Flat-shaded chamfers keep a hard silhouette."""
    pts = [Vector(p) for p in pts]
    normals = [Vector(n) for n in normals]
    n, m = len(pts), len(profile)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    dist = [0.0]
    for i in range(1, n):
        dist.append(dist[-1] + (pts[i] - pts[i - 1]).length)
    if closed:
        dist.append(dist[-1] + (pts[0] - pts[-1]).length)
    rings = []
    for i, p in enumerate(pts):
        t = (pts[(i + 1) % n] - pts[i - 1]) if closed else (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)])
        t.normalize()
        nn = normals[i] - t * normals[i].dot(t)
        nn.normalize()
        bb = t.cross(nn)
        rings.append([bm.verts.new(p + bb * u + nn * v) for u, v in profile])
    where = {}
    for i, ring in enumerate(rings):
        for j, v in enumerate(ring):
            where[v] = (i, j)
    for i in range(n if closed else n - 1):
        a, b2 = rings[i], rings[(i + 1) % n]
        for j in range(m):
            f = bm.faces.new((a[j], a[(j + 1) % m], b2[(j + 1) % m], b2[j]))
            for l in f.loops:
                ii, jj = where[l.vert]
                d = dist[ii] if not (closed and i == n - 1 and ii == 0) else dist[-1]
                l[uv].uv = (d * 2.0, jj * 0.05)
    if caps and not closed:
        for ring in (rings[0], rings[-1]):
            f = bm.faces.new(ring)
            for l in f.loops:
                l[uv].uv = (0.0, 0.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L.smooth(L.mesh_obj(name, bm, [mat]), 30)


def beam(name, a, b2, w, h, mat, up=(0, 0, 1), c=None):
    """Chamfered box-section beam from a to b2; h is measured along `up`."""
    return sweep(name, [a, b2], [up, up], chamfer_rect(w, h, c), mat)


def cbox(name, size, mat, loc, rot=Matrix.Identity(3), ch=0.008):
    """Box with 45-degree chamfered edges (the stock housing look)."""
    return L.box(name, size, mat, loc, rot, bevel=ch, segs=1)


def track(d):
    return Vector(d).normalized().to_track_quat("Z", "Y").to_matrix()


# ------------------------------------------------------------------ clearance: structure added last fits round equipment
class Clearance:
    SKIP = ("Shell", "Dome", "Floor", "Deck", "Stringer", "Rivet", "Rib_", "RingFrame", "DomeRib", "Plate_", "REF_",
            "IVA_", "CeilingBulkhead", "RingLight", "Bundle", "Duct")

    def __init__(self, extra_skip=(), zones=()):
        import numpy as np
        self.np = np
        self.zones = list(zones)   # callables p -> True where nothing should be built (e.g. hidden behind a bulkhead)
        import bpy
        bpy.context.view_layer.update()   # curves (rungs, rails, hoses) have no bounding box until the scene is evaluated
        lo, hi = [], []
        for o in L.COLL.objects:
            if o.type not in ("MESH", "CURVE") or o.name.startswith(self.SKIP + tuple(extra_skip)):
                continue
            cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
            a = Vector((min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs)))
            b2 = Vector((max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs)))
            if max(b2 - a) > 1.6:
                continue
            lo.append(a[:])
            hi.append(b2[:])
        self.lo = np.array(lo) if lo else np.zeros((0, 3))
        self.hi = np.array(hi) if hi else np.zeros((0, 3))

    def blocked(self, p, pad=0.01):
        np = self.np
        if any(z(p) for z in self.zones):
            return True
        q = np.array(p[:])
        return bool(np.any(np.all((self.lo - pad <= q) & (q <= self.hi + pad), axis=1)))

    def add(self, obj):
        np = self.np
        cs = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        a = [min(c[i] for c in cs) for i in range(3)]
        b2 = [max(c[i] for c in cs) for i in range(3)]
        self.lo = np.vstack([self.lo, a])
        self.hi = np.vstack([self.hi, b2])


def runs(samples, ok, min_len=2):
    """Split a sample list into consecutive runs where ok(sample) holds."""
    out, cur = [], []
    for s in samples:
        if ok(s):
            cur.append(s)
        else:
            if len(cur) >= min_len:
                out.append(cur)
            cur = []
    if len(cur) >= min_len:
        out.append(cur)
    return out


def inward(phi):
    return Vector((-math.sin(phi), math.cos(phi), 0.0))


def in_window(phi, z, margin=0.06):
    for w in C.WINDOWS:
        if abs(z - w["z"]) < w["hh"] + margin and C.ang_dist(phi, w["phi"]) * C.r_in(z) < w["hw"] + margin:
            return True
    return False


# ------------------------------------------------------------------ hull structure
def wall_ribs(name, count, z0, z1, clear, keep_clear=None, w=0.065, d=0.045, phase=0.5, mat=None, min_len=0.35):
    """Vertical chamfered ribs on the hull, broken where windows, the hatch or equipment are in the way."""
    mat = mat or M["frame"]
    n_made = 0
    for k in range(count):
        phi = 2 * math.pi * (k + phase) / count
        if keep_clear and keep_clear(phi):
            continue
        zs = [z0 + (z1 - z0) * i / max(1, int((z1 - z0) / 0.04)) for i in range(max(1, int((z1 - z0) / 0.04)) + 1)]

        def ok(z):
            p = C.polar(phi, C.r_in(z) - d / 2, z)
            return not in_window(phi, z) and not clear.blocked(p, 0.012)

        for r, seg in enumerate(runs(zs, ok, max(3, int(min_len / 0.04) + 1))):
            pts = [C.polar(phi, C.r_in(z) - d / 2, z) for z in seg]
            sweep(f"Rib_{name}{k}_{r}", pts, [inward(phi)] * len(pts), chamfer_rect(w, d), mat)
            for zb in seg[1:-1:5]:
                p, b = C.frame_at(phi, zb, d)
                L.cylinder(f"Rib_{name}{k}_{r}Bolt{zb:.2f}", 0.005, 0.006, M["buckle"], p, b, segs=6)
            n_made += 1
    return n_made


def ring_frame(name, z, clear, h=0.07, d=0.045, mat=None, phi0=0.0, phi1=2 * math.pi, step_deg=2.0):
    """Horizontal chamfered frame round the hull at height z, broken at windows and equipment."""
    mat = mat or M["frame"]
    n = max(4, int(math.degrees(phi1 - phi0) / step_deg))
    phis = [phi0 + (phi1 - phi0) * i / n for i in range(n + 1)]
    full = abs(phi1 - phi0 - 2 * math.pi) < 1e-6

    def ok(phi):
        return not in_window(phi, z, 0.04) and not clear.blocked(C.polar(phi, C.r_in(z) - d / 2, z), 0.01)

    segs = runs(phis[:-1] if full else phis, ok, max(3, int(12 / step_deg)))
    if full and len(segs) == 1 and len(segs[0]) == n:
        pts = [C.polar(p, C.r_in(z) - d / 2, z) for p in segs[0]]
        return sweep(f"RingFrame_{name}", pts, [inward(p) for p in segs[0]], chamfer_rect(h, d), mat, closed=True)
    for r, seg in enumerate(segs):
        pts = [C.polar(p, C.r_in(z) - d / 2, z) for p in seg]
        sweep(f"RingFrame_{name}_{r}", pts, [inward(p) for p in seg], chamfer_rect(h, d), mat)


def inspection_plate(name, p, b, w, h, mat=None, bolts=True):
    mat = mat or M["frame"]
    cbox(name, (w, h, 0.012), mat, p + b.col[2] * 0.006, b, ch=0.004)
    cbox(name + "Inset", (w * 0.7, h * 0.62, 0.004), M["frame_dark"], p + b.col[2] * 0.0135, b, ch=0.0015)
    if bolts:
        for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
            q = p + b.col[0] * sx * (w / 2 - 0.016) + b.col[1] * sy * (h / 2 - 0.016) + b.col[2] * 0.014
            L.cylinder(f"{name}Bolt{i}", 0.0055, 0.005, M["buckle"], q, b, segs=6)


def wall_plates(name, clear, bays, zs, size=(0.17, 0.13), chance=0.5, seed=7, inset=0.004):
    """Bolted inspection plates on free stretches of wall (between ribs), seeded so builds are repeatable."""
    rnd = random.Random(seed)
    k = 0
    for phi in bays:
        for z in zs:
            if rnd.random() > chance:
                continue
            w, h = size[0] * rnd.uniform(0.8, 1.3), size[1] * rnd.uniform(0.8, 1.4)
            p, b = C.frame_at(phi, z, inset)
            # a grid over the plate at two depths, so thin things in front of the wall (rungs, rails, cables) are caught too
            probe = [p + b.col[0] * sx * w / 2 + b.col[1] * sy * h / 2 + b.col[2] * dz
                     for sx in (-1, -0.5, 0, 0.5, 1) for sy in (-1, -0.5, 0, 0.5, 1) for dz in (0.01, 0.06)]
            if in_window(phi, z, 0.1) or any(clear.blocked(q, 0.015) for q in probe):
                continue
            inspection_plate(f"Plate_{name}{k}", p, b, w, h)
            k += 1
    return k


# ------------------------------------------------------------------ cables
def catmull(pts, step=0.035):
    pts = [Vector(p) for p in pts]
    if len(pts) < 3:
        a, b2 = pts[0], pts[-1]
        n = max(2, int((b2 - a).length / step))
        return [a.lerp(b2, i / n) for i in range(n + 1)]
    ext = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        n = max(2, int((p2 - p1).length / step))
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    out.append(pts[-1])
    return out


def frames_along(path):
    """Parallel-transport frames (tangent, normal, binormal) along a path."""
    ts = []
    for i in range(len(path)):
        t = path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]
        ts.append(t.normalized())
    ref = Vector((0, 0, 1)) if abs(ts[0].z) < 0.9 else Vector((1, 0, 0))
    nn = (ref - ts[0] * ref.dot(ts[0])).normalized()
    out = []
    for i, t in enumerate(ts):
        nn = (nn - t * nn.dot(t)).normalized()
        out.append((t, nn, t.cross(nn)))
    return out


def bundle(name, pts, n=4, r=0.0095, colours=None, tie_every=0.26, ends=(True, True)):
    """A bundle of n coloured cables following key points, with ties along it and socket ends."""
    colours = colours or CABLES[:n]
    path = catmull(pts)
    fr = frames_along(path)
    spread = r * 1.25 if n > 1 else 0.0
    for k in range(n):
        a = 2 * math.pi * k / n + 0.4
        off = [nn * math.cos(a) * spread + bb * math.sin(a) * spread for _, nn, bb in fr]
        L.tube(f"Bundle_{name}_{k}", [p + o for p, o in zip(path, off)], r, M[colours[k % len(colours)]], bevel_res=1)
    run = 0.0
    for i in range(1, len(path) - 1):
        run += (path[i] - path[i - 1]).length
        if run >= tie_every:
            run = 0.0
            L.cylinder(f"Bundle_{name}_Tie{i}", spread + r * 1.35, 0.016, M["frame_dark"], path[i], track(fr[i][0]), segs=10)
    for e, (i, sgn) in enumerate(((0, 1), (len(path) - 1, -1))):
        if not ends[e]:
            continue
        t = fr[i][0] * sgn
        L.cylinder(f"Bundle_{name}_Socket{e}", spread + r * 1.8, 0.05, M["frame"], path[i] - t * 0.012, track(t), segs=12, bevel=0.003)
        L.cylinder(f"Bundle_{name}_Flange{e}", spread + r * 2.8, 0.008, M["frame_dark"], path[i] - t * 0.036, track(t), segs=12)


def wall_path(phi, z0, z1, inset=0.05, n=6, phi1=None):
    """Key points down/up the hull wall (optionally drifting in angle), for cable runs."""
    phi1 = phi if phi1 is None else phi1
    return [C.polar(phi + (phi1 - phi) * i / n, C.r_in(z0 + (z1 - z0) * i / n) - inset, z0 + (z1 - z0) * i / n) for i in range(n + 1)]


# ------------------------------------------------------------------ fittings
def light_fixture(name, p, b, w=0.3, h=0.09):
    """Ceiling light: chamfered housing with an emissive diffuser, facing along b's normal."""
    cbox(name, (w + 0.04, h + 0.04, 0.05), M["frame_dark"], p + b.col[2] * 0.025, b, ch=0.01)
    cbox(name + "Diffuser", (w, h, 0.008), M["diffuser"], p + b.col[2] * 0.052, b, ch=0.002)
    for sx in (-1, 1):
        L.cylinder(f"{name}Clip{sx}", 0.006, 0.012, M["buckle"], p + b.col[0] * sx * (w / 2 + 0.008) + b.col[2] * 0.052, b, segs=6)


def floor_hatch(name, centre, z, w=0.42, h=0.34, yaw=0.0):
    rot = Matrix.Rotation(yaw, 3, "Z")
    c = Vector((centre[0], centre[1], z))
    cbox(name + "Frame", (w + 0.05, h + 0.05, 0.016), M["frame_dark"], c + Vector((0, 0, 0.008)), rot, ch=0.006)
    cbox(name, (w, h, 0.012), M["frame"], c + Vector((0, 0, 0.014)), rot, ch=0.004)
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        q = c + rot @ Vector((sx * (w / 2 - 0.03), sy * (h / 2 - 0.03), 0.021))
        cbox(f"{name}Latch{i}", (0.035, 0.018, 0.008), M["yellow"], q, rot, ch=0.002)
    L.tube(name + "Handle", [c + rot @ Vector((-0.06, 0, 0.02)), c + rot @ Vector((-0.06, 0, 0.04)), c + rot @ Vector((0.06, 0, 0.04)),
                             c + rot @ Vector((0.06, 0, 0.02))], 0.006, M["handle"])


def foot_restraint(name, a, b2, z):
    """Low yellow loop bar on the floor (zero-g foot loop)."""
    a, b2 = Vector((a[0], a[1], z)), Vector((b2[0], b2[1], z))
    L.tube(name, [a, a + Vector((0, 0, 0.05)), b2 + Vector((0, 0, 0.05)), b2], 0.009, M["yellow"])
    for k, q in enumerate((a, b2)):
        L.cylinder(f"{name}Foot{k}", 0.02, 0.012, M["frame_dark"], q + Vector((0, 0, 0.006)), segs=10)


def grille(name, p, b, w, h, slats=8):
    cbox(name, (w, h, 0.012), M["frame_dark"], p + b.col[2] * 0.006, b, ch=0.003)
    for i in range(slats):
        y = -h / 2 + h * (i + 0.5) / slats
        L.box(f"{name}Slat{i}", (w * 0.86, h / slats * 0.45, 0.006), M["frame"], p + b.col[1] * y + b.col[2] * 0.014, b)


def cable_run(name, z, clear, phi0=0.0, phi1=2 * math.pi, inset=0.06, n=4, min_len=0.5, seed=3):
    """Horizontal cable bundle round the hull at height z, ending in sockets where equipment or windows interrupt it."""
    rnd = random.Random(seed)
    phis = [phi0 + (phi1 - phi0) * i / 180 for i in range(181)]

    def ok(phi):
        return not in_window(phi, z, 0.06) and not clear.blocked(C.polar(phi, C.r_in(z) - inset, z), 0.03)

    k = 0
    for seg in runs(phis, ok, 3):
        if (seg[-1] - seg[0]) * C.r_in(z) < min_len:
            continue
        pts = [C.polar(p, C.r_in(z) - inset, z + 0.012 * math.sin(p * 9)) for p in seg[::3] + [seg[-1]]]
        cols = list(CABLES[:4])
        rnd.shuffle(cols)
        bundle(f"{name}{k}", pts, n=n, colours=cols, ends=(False, False))
        for e, phi in enumerate((seg[0], seg[-1])):
            junction(f"{name}{k}Box{e}", phi, z)
        k += 1


def rack(name, p, b, w, h, seed=0):
    """Wall equipment rack: chamfered frame round a stack of units (boxes, grilles, plates)."""
    import modules as G
    rnd = random.Random(seed)
    d = 0.09
    for i, (cx, cy, fw, fh) in enumerate(((0, h / 2, w + 0.05, 0.05), (0, -h / 2, w + 0.05, 0.05), (w / 2, 0, 0.05, h), (-w / 2, 0, 0.05, h))):
        cbox(f"{name}Frame{i}", (fw, fh, d), M["frame"], p + b.col[0] * cx + b.col[1] * cy + b.col[2] * d / 2, b, ch=0.012)
    cbox(name + "Back", (w, h, 0.01), M["frame_dark"], p + b.col[2] * 0.005, b, ch=0.0)
    n = 2 if h < 0.5 else 3
    uh = (h - 0.02) / n
    for i in range(n):
        cy = h / 2 - 0.01 - uh * (i + 0.5)
        q = p + b.col[1] * cy
        kind = rnd.choice(("box", "box", "grille", "plate"))
        if kind == "box":
            rot = L.basis(b.col[0], -b.col[2], b.col[1])
            G.box_unit(f"{name}Unit{i}", q + b.col[2] * 0.045, (w - 0.03, 0.07, uh - 0.025), rot, vents=rnd.random() < 0.5, lamps_n=rnd.choice((0, 2, 3)))
        elif kind == "grille":
            grille(f"{name}Grille{i}", q + b.col[2] * 0.02, b, w - 0.05, uh - 0.04, slats=7)
        else:
            inspection_plate(f"{name}Panel{i}", q + b.col[2] * 0.02, b, w - 0.04, uh - 0.03)


def wall_racks(name, clear, bays, z, w, h, inset=0.0, seed=5, chance=0.85):
    rnd = random.Random(seed)
    k = 0
    for phi in bays:
        if rnd.random() > chance:
            continue
        p, b = C.frame_at(phi, z, inset)
        corners = [p + b.col[0] * sx * (w / 2 + 0.03) + b.col[1] * sy * (h / 2 + 0.03) + b.col[2] * dz for sx in (-1, 0, 1) for sy in (-1, 0, 1) for dz in (0.02, 0.09)]
        if in_window(phi, z, h / 2 + 0.05) or any(clear.blocked(q, 0.01) for q in corners):
            continue
        rack(f"Rack_{name}{k}", p, b, w, h, seed=seed * 31 + k)
        k += 1
    return k


def junction(name, phi, z, w=0.11, h=0.12, d=0.075):
    """Wall junction box that cable bundles plug into (so no bundle ends in mid-air)."""
    p, b = C.frame_at(phi, z, 0.0)
    cbox(name, (w, h, d), M["frame"], p + b.col[2] * d / 2, b, ch=0.01)
    cbox(name + "Lid", (w * 0.8, h * 0.8, 0.008), M["frame_dark"], p + b.col[2] * (d + 0.003), b, ch=0.002)
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        L.cylinder(f"{name}Bolt{i}", 0.005, 0.005, M["buckle"], p + b.col[0] * sx * w * 0.32 + b.col[1] * sy * h * 0.32 + b.col[2] * (d + 0.008), b, segs=6)


def mount(name, p, b, w, h, rail_ext=0.08):
    """Seat-track mounting rails on the wall above and below a wall unit, with a back plate, so it reads as fixed in place."""
    cbox(name + "Back", (w + 0.04, h + 0.04, 0.016), M["frame_dark"], p + b.col[2] * 0.008, b, ch=0.004)
    for k, sy in enumerate((-1, 1)):
        q = p + b.col[1] * sy * (h / 2 + 0.035)
        cbox(f"{name}Rail{k}", (w + 2 * rail_ext, 0.035, 0.03), M["frame"], q + b.col[2] * 0.015, b, ch=0.006)
        for i in range(-2, 3):
            L.cylinder(f"{name}Rail{k}Bolt{i}", 0.005, 0.005, M["buckle"], q + b.col[0] * i * (w + 2 * rail_ext) * 0.22 + b.col[2] * 0.032, b, segs=6)
