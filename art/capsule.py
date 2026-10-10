"""Shared toolkit for the bespoke capsule interiors (model_mk1.py, model_mk13.py).

Hull shell with window cut-outs, stringers, bolted window sleeves, a side hatch, pose-fitted couches, curved console
surfaces with an overlap-checked layout, instrument helpers, and a stand-in of the game's seated kerbals for previews
(objects named REF_*, which export_interior.py leaves out).

Coordinates: metres, Blender Z up from the hull base, cabin front = -Y (= Unity part -Z), phi 0 = front, +phi = +X.
Spec angles (windows, hatch) are mirrored into Blender (phi = -angle). In part space: Unity (x, y, z) = Blender
(x, z + hull_base_y, y) once the catalogue's Yaw 180 is applied, so the spec "pose" block lines up with the game.
"""
import math
import os

import ivalib as L  # imports bpy first
import bpy
import bmesh
from mathutils import Matrix, Vector

S = {}
PROFILE = []
WALL = 0.04
Z_FLOOR = 0.08
Z_CEIL = 0.82
Z_TOP = 0.90
SEG = 112
WINDOWS = []
M = L.M


def setup(spec, wall=0.04, ceil=None, top=None, seg=112):
    global WALL, Z_FLOOR, Z_CEIL, Z_TOP, SEG
    S.clear()
    S.update(spec)
    raw = sorted((float(z), float(r)) for z, r in spec["profile"])
    # measured profiles are max-per-slice samples with small bumps; a light moving average keeps the walls fair
    PROFILE[:] = [(z, r if i in (0, len(raw) - 1) else (raw[i - 1][1] + 2 * r + raw[i + 1][1]) / 4) for i, (z, r) in enumerate(raw)]
    WALL, Z_FLOOR, SEG = wall, spec["floor"], seg
    Z_CEIL = ceil if ceil is not None else spec["ceiling"]
    Z_TOP = top if top is not None else Z_CEIL + 0.08
    WINDOWS[:] = [dict(phi=rad(-w["angle"]), z=w["z"], hw=w["half_w"], hh=w["half_h"], c=w.get("corner", 0.03), name=w.get("name", f"W{i}"))
                  for i, w in enumerate(spec.get("windows", []))]


def rad(deg):
    return math.radians(deg)


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


def phi_of(p):
    return math.atan2(p.x, -p.y)


def ang_dist(a, b):
    return abs(((a - b + math.pi) % (2 * math.pi)) - math.pi)


def frame_at(phi, z, inset):
    """Basis on a surface parallel to the wall, `inset` in from it: right (as seen from inside), up the slope, normal into the cabin."""
    tangent = Vector((-math.cos(phi), -math.sin(phi), 0))
    dz = 0.01
    up = (polar(phi, r_in(z + dz) - inset, z + dz) - polar(phi, r_in(z - dz) - inset, z - dz)).normalized()
    normal = tangent.cross(up).normalized()
    if normal.dot(Vector((-math.sin(phi), math.cos(phi), 0))) < 0:
        normal = -normal
    return polar(phi, r_in(z) - inset, z), L.basis(tangent, up, normal)


def inward(f, centre):
    """Flip bmesh faces so their normals face the pod axis."""
    for face in f:
        c = face.calc_center_median()
        if face.normal.dot(Vector((-c.x, -c.y, 0))) < 0:
            face.normal_flip()


# ------------------------------------------------------------------ windows
def window_sdf(phi, z, r_at, grow=0.0):
    best = 1e9
    for w in WINDOWS:
        s = ((phi - w["phi"] + math.pi) % (2 * math.pi) - math.pi) * r_at
        hw, hh, c = w["hw"] + grow, w["hh"] + grow, w["c"] + grow
        qx, qy = abs(s) - (hw - c), abs(z - w["z"]) - (hh - c)
        best = min(best, math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - c)
    return best


def window_outline(w, inset, grow=0.0, n=48):
    pts = []
    hw, hh, c = w["hw"] + grow, w["hh"] + grow, w["c"] + grow
    for cx, cy, a0 in ((hw - c, hh - c, 0), (-(hw - c), hh - c, 90), (-(hw - c), -(hh - c), 180), (hw - c, -(hh - c), 270)):
        for i in range(n // 4 + 1):
            a = rad(a0 + 90 * i / (n // 4))
            z = w["z"] + cy + c * math.sin(a)
            pts.append(polar(w["phi"] + (cx + c * math.cos(a)) / (r_in(z) - inset), r_in(z) - inset, z))
    return pts


def build_window(w, depth=0.035, bolts=24, frame_mat=None):
    """Sleeve from the hull opening in to `depth` inside the wall, with a bolted frame ring."""
    outer = window_outline(w, -0.035, grow=0.004)
    inner = window_outline(w, depth, grow=0.012)
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
    L.smooth(L.mesh_obj(f"WindowSleeve_{w['name']}", bm, [M["bezel"]]), 40)
    L.tube(f"WindowFrame_{w['name']}", window_outline(w, depth + 0.006, grow=0.016), 0.011, frame_mat or M["rib"], closed=True)
    for k, p in enumerate(window_outline(w, depth + 0.012, grow=0.03, n=bolts)[::2]):
        q, bb = frame_at(phi_of(p), p.z, depth + 0.012)
        L.cylinder(f"WindowBolt_{w['name']}_{k}", 0.004, 0.008, M["buckle"], p, bb, segs=8)


# ------------------------------------------------------------------ shell, dome, floor
def build_shell(dome=True, ring_light=True, bulkhead="chute"):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rings = max(24, int((Z_CEIL - Z_FLOOR) / 0.02))
    zs = [Z_FLOOR - 0.01 + (Z_CEIL + 0.02 - Z_FLOOR) * i / rings for i in range(rings + 1)]
    grid = [[bm.verts.new(polar(2 * math.pi * j / SEG, r_in(z), z)) for j in range(SEG)] for z in zs]
    circ = 2 * math.pi * r_in((Z_FLOOR + Z_CEIL) / 2)
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
    inward(bm.faces, None)
    L.smooth(L.solidify(L.mesh_obj("Shell", bm, [M["blanket"]]), 0.02), 30)

    if dome:
        bm = bmesh.new()
        uv = bm.loops.layers.uv.new("UVMap")
        rows = []
        for i in range(9):
            t = i / 8
            z = Z_CEIL + (Z_TOP - Z_CEIL) * math.sin(t * math.pi / 2)
            r = r_in(Z_CEIL) * math.cos(t * math.pi / 2 * 0.92)
            rows.append([bm.verts.new(polar(2 * math.pi * j / SEG, r, z)) for j in range(SEG)])
        for i in range(8):
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
        L.disc("CeilingBulkhead", top_r + 0.002, M["ring"], (0, 0, Z_TOP - 0.002), Matrix.Rotation(math.pi, 3, "X"))
        for k in range(6):
            a = k * math.pi / 3
            L.cylinder(f"CeilingBolt_{k}", 0.006, 0.01, M["buckle"], (top_r * 0.7 * math.cos(a), top_r * 0.7 * math.sin(a), Z_TOP - 0.006), segs=8)
    if ring_light:
        zl = Z_CEIL + 0.03
        L.torus("RingLightHousing", r_in(zl) - 0.07, 0.016, M["ring"], (0, 0, zl), Matrix.Identity(3), seg=64, mseg=10)
        L.torus("RingLight", r_in(zl) - 0.07, 0.008, M["light"], (0, 0, zl - 0.012), Matrix.Identity(3), seg=64, mseg=8)

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
    inward(bm.faces, None)
    return L.smooth(L.solidify(L.mesh_obj(name, bm, [mat]), thick), 30)


def build_stringers(count, keep_clear, z0=None, z1=None, half_w=0.011, rivets=6):
    """Wall stringers with rivet lines; keep_clear(phi) -> True skips one (windows, hatch, consoles)."""
    z0 = Z_FLOOR if z0 is None else z0
    z1 = Z_CEIL if z1 is None else z1
    for k in range(count):
        phi = 2 * math.pi * (k + 0.5) / count
        if keep_clear(phi):
            continue
        ribbon(f"Stringer_{k}", phi, z0, z1, half_w, 0.004, M["rib"])
        for i in range(rivets):
            z = z0 + 0.06 + i * (z1 - z0 - 0.12) / max(1, rivets - 1)
            p, b = frame_at(phi, z, half_w)
            L.cylinder(f"Rivet_{k}_{i}", 0.0035, 0.004, M["buckle"], p, b, segs=8)


# ------------------------------------------------------------------ hatch
def build_hatch(phi_c, half, z0, z1, inset=0.018, handle_z=None, name="Hatch"):
    phi0, phi1 = phi_c - half, phi_c + half
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
    inward(bm.faces, None)
    L.smooth(L.add_bevel(L.solidify(L.mesh_obj(name + "Door", bm, [M["hatch"]]), 0.025), 0.006, 2), 30)
    edge = [polar(phi0 + (phi1 - phi0) * t / 30, r_in(z0) - inset - 0.012, z0) for t in range(31)]
    edge += [polar(phi1, r_in(z0 + (z1 - z0) * t / 30) - inset - 0.012, z0 + (z1 - z0) * t / 30) for t in range(1, 31)]
    edge += [polar(phi1 - (phi1 - phi0) * t / 30, r_in(z1) - inset - 0.012, z1) for t in range(1, 31)]
    edge += [polar(phi0, r_in(z1 - (z1 - z0) * t / 30) - inset - 0.012, z1 - (z1 - z0) * t / 30) for t in range(1, 30)]
    L.tube(name + "Seal", edge, 0.01, M["ring"], closed=True)
    for k, p in enumerate(edge[::5]):
        q, b = frame_at(phi_of(p), p.z, inset + 0.02)
        L.cylinder(f"{name}Bolt_{k}", 0.006, 0.014, M["buckle"], q, b, segs=8)
        L.cylinder(f"{name}BoltCap_{k}", 0.004, 0.006, M["red"], q + b.col[2] * 0.009, b, segs=8)
    zc = (z0 + z1) / 2 if handle_z is None else handle_z
    p, b = frame_at(phi_c, zc, inset + 0.03)
    L.box(name + "Recess", (0.09, 0.06, 0.012), M["bezel"], p, b, bevel=0.004)
    L.cylinder(name + "ReleaseShaft", 0.005, 0.03, M["rib"], p + b.col[2] * 0.016, b, segs=10)
    L.cylinder(name + "ReleaseTee", 0.008, 0.07, M["yellow"], p + b.col[2] * 0.032, L.basis(b.col[1], b.col[2], b.col[0]), segs=14, bevel=0.002)
    p, b = frame_at(phi_c, min(z1 - 0.05, zc + 0.1), inset + 0.028)
    L.plane(name + "Hazard", min(0.17, 2 * half * r_in(zc) * 0.8), 0.035, M["hazard"], p, b, (0, 0, 1, 0.5))


# ------------------------------------------------------------------ wall band panel (a strip of the cone wall)
class Band:
    """Instrument band following the wall between z0 and z1, from phi_from to phi_to (radians), `inset` from the wall."""

    def __init__(self, name, phi_from, phi_to, z0, z1, inset, cut=None):
        self.name, self.p0, self.p1, self.z0, self.z1, self.inset = name, phi_from, phi_to, z0, z1, inset
        self.cut = cut or (lambda phi, z: False)
        self.foot = []

    def r(self, z):
        return r_in(z) - self.inset - 0.012

    def at(self, s_m, z, lift=0.0, centre_deg=0.0):
        """Point and basis at arc distance s_m from centre_deg, height z."""
        deg = centre_deg + math.degrees(s_m / self.r(z))
        return frame_at(rad(deg), z, self.inset + 0.012 + lift)

    def deg(self, s_m, z, centre_deg=0.0):
        return centre_deg + math.degrees(s_m / self.r(z))

    def reserve(self, name, deg, z, half_w, half_h, margin=0.008):
        hd = math.degrees((half_w + margin) / self.r(z))
        self.foot.append((name, deg - hd, deg + hd, z - half_h - margin, z + half_h + margin))

    def build(self, mat, trims=True, thick=0.022):
        bm = bmesh.new()
        uv = bm.loops.layers.uv.new("UVMap")
        span = self.p1 - self.p0
        ns = max(24, int(abs(span) / (2 * math.pi) * 160))
        nz = max(8, int((self.z1 - self.z0) / 0.015))
        full = abs(abs(span) - 2 * math.pi) < 1e-6
        cols = ns if full else ns + 1
        grid = [[bm.verts.new(polar(self.p0 + span * j / ns, r_in(self.z0 + (self.z1 - self.z0) * i / nz) - self.inset, self.z0 + (self.z1 - self.z0) * i / nz))
                 for j in range(cols)] for i in range(nz + 1)]
        for i in range(nz):
            for j in range(ns):
                pc = self.p0 + span * (j + 0.5) / ns
                zc = self.z0 + (self.z1 - self.z0) * (i + 0.5) / nz
                if window_sdf(pc, zc, r_in(zc) - self.inset, grow=0.012) < 0 or self.cut(pc, zc):
                    continue
                jn = (j + 1) % cols
                f = bm.faces.new((grid[i][j], grid[i][jn], grid[i + 1][jn], grid[i + 1][j]))
                for l in f.loops:
                    l[uv].uv = (j / ns * abs(span) * 0.5, i / nz)
        bm.normal_update()
        inward(bm.faces, None)
        L.smooth(L.solidify(L.mesh_obj(self.name, bm, [mat]), thick), 30)
        if trims:
            for nm, z in (("TrimTop", self.z1), ("TrimBottom", self.z0)):
                L.tube(self.name + nm, [polar(self.p0 + span * j / 96, r_in(z) - self.inset - 0.004, z) for j in range(97)], 0.008, M["rib"], closed=full)

    def check(self):
        problems = []
        lo, hi = sorted((math.degrees(self.p0), math.degrees(self.p1)))
        full = hi - lo >= 359.9
        for n, d0, d1, z0, z1 in self.foot:
            if (not full and (d0 < lo or d1 > hi)) or z0 < self.z0 or z1 > self.z1:
                problems.append(f"{n} runs off {self.name} ({d0:.1f}..{d1:.1f} deg, z {z0:.3f}..{z1:.3f})")
        for i, a in enumerate(self.foot):
            for b in self.foot[i + 1:]:
                if a[1] < b[2] and b[1] < a[2] and a[3] < b[4] and b[3] < a[4]:
                    problems.append(f"{a[0]} overlaps {b[0]}")
        print(f"{self.name} layout:", "OK, no overlaps" if not problems else "PROBLEMS")
        for p in problems:
            print("  ", p)
        return problems


# ------------------------------------------------------------------ free-hanging curved console surface
class Surface:
    """A console panel: centre C, axes right/up and normal (towards the viewer), size w x h, optionally bent round its
    `up` axis with radius `bend` (concave towards the viewer). Instruments go at (u, v) in metres from the centre."""

    def __init__(self, name, centre, right, up, w, h, bend=0.0, corner=0.03):
        self.name = name
        self.c = Vector(centre)
        self.right = Vector(right).normalized()
        self.up = (Vector(up) - Vector(up).project(self.right)).normalized()
        self.n = self.right.cross(self.up).normalized()
        self.w, self.h, self.bend, self.corner = w, h, bend, corner
        self.foot = []

    def at(self, u, v, lift=0.0):
        if self.bend:
            a = u / self.bend
            p = self.c + self.right * self.bend * math.sin(a) + self.n * self.bend * (1 - math.cos(a)) + self.up * v
            r = self.right * math.cos(a) + self.n * math.sin(a)
            nn = self.n * math.cos(a) - self.right * math.sin(a)
        else:
            p, r, nn = self.c + self.right * u + self.up * v, self.right, self.n
        return p + nn * lift, L.basis(r, self.up, nn)

    def inside(self, u, v, grow=0.0):
        hw, hh, c = self.w / 2 + grow, self.h / 2 + grow, self.corner + grow
        qx, qy = abs(u) - (hw - c), abs(v) - (hh - c)
        return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - c <= 0

    def build(self, mat, thick=0.03, rim=True, rim_mat=None, nu=40, nv=30):
        bm = bmesh.new()
        uv = bm.loops.layers.uv.new("UVMap")
        grid = {}
        for i in range(nv + 1):
            for j in range(nu + 1):
                u, v = -self.w / 2 + self.w * j / nu, -self.h / 2 + self.h * i / nv
                grid[i, j] = bm.verts.new(self.at(u, v)[0])
        for i in range(nv):
            for j in range(nu):
                uc, vc = -self.w / 2 + self.w * (j + 0.5) / nu, -self.h / 2 + self.h * (i + 0.5) / nv
                if not self.inside(uc, vc):
                    continue
                f = bm.faces.new((grid[i, j], grid[i, j + 1], grid[i + 1, j + 1], grid[i + 1, j]))
                for l in f.loops:
                    l[uv].uv = (l.vert.co.dot(self.right) * 2, l.vert.co.dot(self.up) * 2)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        bm.normal_update()
        for f in bm.faces:
            if f.normal.dot(self.n) < 0:
                f.normal_flip()
        L.smooth(L.add_bevel(L.solidify(L.mesh_obj(self.name, bm, [mat]), thick), 0.004, 2), 40)
        if rim:
            pts = []
            hw, hh, c = self.w / 2 - 0.004, self.h / 2 - 0.004, self.corner
            for cx, cy, a0 in ((hw - c, hh - c, 0), (-(hw - c), hh - c, 90), (-(hw - c), -(hh - c), 180), (hw - c, -(hh - c), 270)):
                for k in range(7):
                    a = rad(a0 + 90 * k / 6)
                    pts.append(self.at(cx + c * math.cos(a), cy + c * math.sin(a), 0.004)[0])
            L.tube(self.name + "Rim", pts, 0.008, rim_mat or M["rib"], closed=True)

    def reserve(self, name, u, v, half_w, half_h, margin=0.008):
        self.foot.append((name, u - half_w - margin, u + half_w + margin, v - half_h - margin, v + half_h + margin))

    def check(self):
        problems = []
        for n, u0, u1, v0, v1 in self.foot:
            if not all(self.inside(u, v, grow=-0.006) for u in (u0, u1) for v in (v0, v1)):
                problems.append(f"{n} runs off {self.name} (u {u0:.3f}..{u1:.3f}, v {v0:.3f}..{v1:.3f})")
        for i, a in enumerate(self.foot):
            for b in self.foot[i + 1:]:
                if a[1] < b[2] and b[1] < a[2] and a[3] < b[4] and b[3] < a[4]:
                    problems.append(f"{a[0]} overlaps {b[0]}")
        print(f"{self.name} layout:", "OK, no overlaps" if not problems else "PROBLEMS")
        for p in problems:
            print("  ", p)
        return problems


# ------------------------------------------------------------------ instruments (p = point on the panel, b = its basis)
def navball(name, p, b, r=0.04):
    L.sphere(name, r, M["navball"], p + b.col[2] * r * 0.3, b @ Matrix.Rotation(rad(25), 3, "Z"), u=40, v=20)
    L.torus(name + "Bezel", r * 1.12, r * 0.2, M["bezel"], p + b.col[2] * r * 0.35, b, seg=40)
    for side in (-1, 1):
        L.box(f"{name}Chevron{side}", (r * 0.45, r * 0.1, r * 0.075), M["btn_amber"], p + b.col[2] * r * 1.3 + b.col[0] * side * r * 0.17 - b.col[1] * r * 0.1,
              L.basis((b.col[0] * math.cos(rad(35)) + b.col[1] * side * math.sin(rad(35))).normalized(),
                      (b.col[1] * math.cos(rad(35)) - b.col[0] * side * math.sin(rad(35))).normalized(), b.col[2]))


def gauge(name, p, b, kind, r=0.022):
    L.disc(name, r, M["gauge_" + kind], p + b.col[2] * 0.003, b)
    L.torus(name + "Bezel", r * 1.09, r * 0.18, M["bezel"], p + b.col[2] * 0.003, b, seg=32, mseg=8)


def crt(name, p, b, mat, w=0.09, h=0.066, keys=4):
    L.box(name + "Bezel", (w, h, 0.014), M["bezel"], p, b, bevel=0.004)
    L.plane(name + "Screen", w - 0.013, h - 0.013, mat, p + b.col[2] * 0.0075, b)
    for k in range(keys):
        L.box(f"{name}Key_{k}", (0.013, 0.008, 0.006), M["bezel"], p - b.col[1] * (h / 2 + 0.011) + b.col[0] * (-(keys - 1) * 0.009 + k * 0.018), b, bevel=0.0015)


def periscope(name, p, b, r=0.041):
    L.disc(name + "Screen", r, M["periscope"], p + b.col[2] * 0.004, b)
    L.torus(name + "Bezel", r * 1.1, 0.006, M["bezel"], p + b.col[2] * 0.004, b, seg=40)
    L.torus(name + "Hood", r * 1.22, 0.009, M["console"], p + b.col[2] * 0.012, b, seg=40, mseg=8)


def toggles(name, points, guard_ends=True):
    for k, (p, b) in enumerate(points):
        L.box(f"{name}Base_{k}", (0.012, 0.018, 0.006), M["bezel"], p, b, bevel=0.0015)
        lever = L.basis(b.col[0], (b.col[1] * 0.5 + b.col[2]).normalized(), (b.col[2] * 0.5 - b.col[1]).normalized())
        L.cylinder(f"{name}_{k}", 0.0025, 0.022, M["toggle"], p + b.col[2] * 0.011 + b.col[1] * 0.004, lever, segs=8)
        if guard_ends and k in (0, len(points) - 1):
            L.tube(f"{name}Guard_{k}", [p - b.col[0] * 0.009, p - b.col[0] * 0.009 + b.col[2] * 0.02,
                                       p + b.col[0] * 0.009 + b.col[2] * 0.02, p + b.col[0] * 0.009], 0.002, M["red"])


def breakers(name, points):
    for k, (p, b) in enumerate(points):
        L.cylinder(f"{name}_{k}", 0.006, 0.01, M["bezel"], p, b, segs=10)
        L.cylinder(f"{name}Cap_{k}", 0.0035, 0.008, M["toggle"], p + b.col[2] * 0.007, b, segs=8)


def lamps(name, points):
    mats = (M["btn_green"], M["btn_amber"], M["btn_red"], M["btn_blue"])
    for k, (p, b) in enumerate(points):
        L.box(f"{name}_{k}", (0.017, 0.016, 0.006), M["bezel"], p, b, bevel=0.002)
        L.box(f"{name}Lens_{k}", (0.013, 0.011, 0.004), mats[k % len(mats)], p + b.col[2] * 0.004, b, bevel=0.0015)


def push_buttons(name, points):
    mats = (M["btn_amber"], M["btn_green"], M["btn_blue"], M["btn_red"])
    for k, (p, b) in enumerate(points):
        L.cylinder(f"{name}Collar_{k}", 0.014, 0.008, M["bezel"], p + b.col[2] * 0.003, b, segs=20)
        L.cylinder(f"{name}_{k}", 0.009, 0.01, mats[k % len(mats)], p + b.col[2] * 0.008, b, segs=20, bevel=0.002)


def abort_handle(name, p, b, label=None):
    L.plane(name + "Plate", 0.075, 0.055, M["hazard"], p + b.col[2] * 0.002, b, (0, 0, 1, 1))
    L.cylinder(name + "Shaft", 0.006, 0.05, M["rib"], p + b.col[2] * 0.026, b, segs=12)
    L.cylinder(name + "Tee", 0.009, 0.075, M["red"], p + b.col[2] * 0.052, L.basis(b.col[1], b.col[2], b.col[0]), segs=16, bevel=0.002)
    if label:
        lp, lb = label
        L.plane(name + "Label", 0.05, 0.02, M["labels"], lp + lb.col[2] * 0.002, lb, (0.02, 0.81, 0.23, 0.94))


def bracket(name, a, b_pt, r=0.012, mat=None):
    L.tube(name, [Vector(a), Vector(b_pt)], r, mat or M["couchframe"])
    L.sphere(name + "EndA", r * 1.5, mat or M["couchframe"], Vector(a), u=12, v=6)
    L.sphere(name + "EndB", r * 1.5, mat or M["couchframe"], Vector(b_pt), u=12, v=6)


# ------------------------------------------------------------------ pose-fitted couch
def sweep(name, top, thick, widths, mat, bolster=0.0, x_off=0.0, bevel=0.012, rim=0.05):
    """Solid strip along a (y, z) profile: `top` surface with its width per point, `thick` below, raised side bolsters."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    n = len(top)
    bot = []
    for i, (y, z) in enumerate(top):
        a, b = top[max(i - 1, 0)], top[min(i + 1, n - 1)]
        ty, tz = b[0] - a[0], b[1] - a[1]
        l = math.hypot(ty, tz) or 1
        bot.append((y + tz / l * thick, z - ty / l * thick))

    def xs(i):
        hw = widths[i] / 2
        return [-hw, -hw + rim, hw - rim, hw]
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
            l[uv].uv = (l.vert.co.x - x_off + 0.5, l.vert.co.y + l.vert.co.z)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=1, use_grid_fill=True)
    obj = L.mesh_obj(name, bm, [mat])
    if bevel:
        L.add_bevel(obj, bevel, 3)
    return L.smooth(obj, 60)


def resample(profile, step=0.04):
    """Even resampling of a (y, z, w) profile, keeping both ends."""
    ys = [p[0] for p in profile]
    out = []
    y = ys[0]
    while y < ys[-1] + 1e-6:
        for a, b in zip(profile, profile[1:]):
            if a[0] <= y <= b[0]:
                t = (y - a[0]) / max(1e-6, b[0] - a[0])
                out.append(tuple(a[k] + (b[k] - a[k]) * t for k in range(3)))
                break
        y += step
    if out[-1][0] < ys[-1] - 1e-4:
        out.append(tuple(profile[-1]))
    return out


def couch(tag, x0, pose, z_floor, armrests=True, struts=None, liner_mat=None):
    """Moulded couch under a seated kerbal. pose = spec["pose"]; x0 = the seat's x. The cushion follows the captured
    body underside (already offset for clearance), the head sits in a winged cradle, the hands get armrests ending at the
    stock stick/throttle anchors, and the feet a footrest. Returns the profile used."""
    prof = resample(pose["couch"], 0.035)
    head_y = pose["head"]["y"]
    top = [(y, z) for y, z, w in prof]
    widths = [max(0.24, min(0.34, w + 0.05)) for y, z, w in prof]
    sweep(f"{tag}Liner", top, 0.035, widths, liner_mat or M["cushion"], bolster=0.06, x_off=x0, bevel=0.012)
    shell = [(y, z - 0.03) for y, z in top]
    sweep(f"{tag}Shell", shell, 0.03, [w + 0.06 for w in widths], M["shell"], bolster=0.11, x_off=x0, bevel=0.01, rim=0.06)
    # head cradle wings either side of the helmet
    hz0, hz1 = pose["head"]["z"]
    hy0, hy1 = head_y
    for side in (-1, 1):
        x = x0 + side * 0.165
        L.box(f"{tag}HeadWing{side}", (0.035, (hy1 - hy0) * 0.75, (hz1 - hz0) * 0.42), M["shell"],
              (x, hy0 + (hy1 - hy0) * 0.45, hz0 + (hz1 - hz0) * 0.2), bevel=0.012)
        L.box(f"{tag}HeadPad{side}", (0.012, (hy1 - hy0) * 0.6, (hz1 - hz0) * 0.3), M["cushion"],
              (x - side * 0.022, hy0 + (hy1 - hy0) * 0.45, hz0 + (hz1 - hz0) * 0.2), bevel=0.005)
    # struts from the shell to the floor
    ys = struts or [top[len(top) // 4][0], top[(3 * len(top)) // 4][0]]
    for y in ys:
        z = min(zz for yy, zz in shell if abs(yy - y) < 0.04) - 0.04
        for side in (-1, 1):
            a = Vector((x0 + side * 0.09, y, z))
            L.tube(f"{tag}Strut_{side}_{y:.2f}", [a, Vector((x0 + side * 0.12, y, z_floor + 0.005))], 0.012, M["couchframe"])
            L.cylinder(f"{tag}StrutFoot_{side}_{y:.2f}", 0.024, 0.012, M["couchframe"], (x0 + side * 0.12, y, z_floor + 0.006))
        L.tube(f"{tag}CrossTube_{y:.2f}", [Vector((x0 - 0.1, y, z + 0.005)), Vector((x0 + 0.1, y, z + 0.005))], 0.01, M["couchframe"])
    # harness: shoulder straps over the chest, lap belt at the hips
    chest = [(y, z) for y, z in top if head_y[1] - 0.02 <= y <= head_y[1] + 0.16]
    hips = min(top, key=lambda t: abs(t[0] - (head_y[1] + 0.2)))
    for side in (-1, 1):
        if len(chest) >= 2:
            L.tube(f"{tag}Shoulder{side}", [Vector((x0 + side * 0.06, y, z + 0.05)) for y, z in chest], 0.006, M["strap"], bevel_res=1)
    L.tube(f"{tag}LapBelt", [Vector((x0 + x, hips[0], hips[1] + 0.03 + 0.03 * (1 - abs(x) / 0.15))) for x in (-0.15, -0.07, 0, 0.07, 0.15)], 0.007, M["strap"], bevel_res=1)
    if armrests:
        # armrest under each elbow; a controller on an arm from the armrest's far end up into the fist
        # (right: rotation hand controller with trigger; left: translation T-grip)
        low = min(z for y, z in shell)
        for side, key in ((1, "right"), (-1, "left")):
            hd = pose["hands"][key]
            fx, fy, fz = hd["fist"]
            ez = hd["elbow_z"]
            x = x0 + fx
            L.box(f"{tag}Armrest{side}", (0.05, 0.2, 0.03), M["couchframe"], (x + side * 0.006, fy - 0.01, ez - 0.032), bevel=0.008)
            L.box(f"{tag}ArmPad{side}", (0.042, 0.17, 0.012), M["cushion"], (x + side * 0.006, fy - 0.01, ez - 0.011), bevel=0.004)
            L.tube(f"{tag}ArmPost{side}", [Vector((x, fy - 0.08, ez - 0.045)), Vector((x0 + side * 0.12, fy - 0.1, low - 0.02))], 0.009, M["couchframe"])
            base = Vector((x + side * 0.012, fy + 0.085, ez - 0.012))
            L.box(f"{tag}ControllerBase{side}", (0.05, 0.05, 0.035), M["bezel"], base, bevel=0.006)
            L.tube(f"{tag}ControllerBoot{side}", [base + Vector((0, 0, 0.015)), Vector((x, fy + 0.06, fz - 0.07)), Vector((x, fy + 0.02, fz - 0.03))], 0.011, M["handle"])
            if side > 0:
                L.cylinder(f"{tag}StickGrip", 0.017, 0.07, M["handle"], (x, fy, fz), segs=16, bevel=0.006)
                L.box(f"{tag}StickTrigger", (0.008, 0.012, 0.016), M["red"], (x - 0.014, fy - 0.012, fz + 0.02), bevel=0.002)
                L.cylinder(f"{tag}StickHat", 0.006, 0.01, M["toggle"], (x, fy, fz + 0.04), segs=10)
            else:
                L.box(f"{tag}TranslationGrip", (0.028, 0.06, 0.03), M["handle"], (x, fy, fz), bevel=0.01)
                L.cylinder(f"{tag}TranslationStem", 0.008, 0.06, M["toggle"], (x, fy, fz - 0.035), segs=12)
    # footplate square to the legs, just past the soles, on a post down to the couch shell
    fy = pose["body"]["y"][1] + 0.018
    fz0, fz1 = top[-1][1] - 0.01, top[-1][1] + 0.1
    L.box(f"{tag}Footplate", (0.22, 0.014, fz1 - fz0), M["couchframe"], (x0, fy, (fz0 + fz1) / 2), bevel=0.004)
    L.box(f"{tag}FootGrip", (0.2, 0.006, fz1 - fz0 - 0.02), M["floor"], (x0, fy - 0.009, (fz0 + fz1) / 2), bevel=0.002)
    L.tube(f"{tag}FootPost", [Vector((x0, fy + 0.012, fz0 + 0.02)), Vector((x0, fy + 0.04, z_floor + 0.005))], 0.012, M["couchframe"])
    return top


def view_markers(w, standoff=0.28, drop=0.0):
    """Window view for the mod's window key: IVA_View_<name> is where the camera goes, IVA_ViewAt_<name> what it looks at
    (the middle of the glass). Positions only, so no axis conventions are involved in the export."""
    z = w["z"]
    for name, p in ((f"IVA_View_{w['name']}", polar(w["phi"], r_in(z) - standoff, z - drop)), (f"IVA_ViewAt_{w['name']}", polar(w["phi"], r_in(z) + 0.03, z))):
        e = bpy.data.objects.new(name, None)
        e.empty_display_type = "SPHERE"
        e.empty_display_size = 0.02
        e.location = p
        L.link(e)


def eye_marker(index, seat):
    """IVA_Seat<n> fallback eye point at the game's eye, looking along its forward (the game's own eye is used when found)."""
    e, f = Vector(seat["eye"]), Vector(seat["fwd"])
    pitch = math.atan2(-f.z, -f.y)        # identity looks along -Y; Rx(pitch) takes (0,-1,0) to (0,-cos,-sin)
    return L.seat_marker(index, e, 0.0, pitch)


# ------------------------------------------------------------------ preview-only stand-ins of the game's kerbals
def reference_kerbals(pose_obj, base_y):
    """Imports the captured seated kerbals (Unity part space) as REF_* objects so previews show what the game draws."""
    if not pose_obj or not os.path.exists(pose_obj):
        print("no pose reference at", pose_obj)
        return []
    suit = L.material("REF_Suit", (0.85, 0.86, 0.88), rough=0.6)
    skin = L.material("REF_Skin", (0.45, 0.75, 0.3), rough=0.5)
    out, verts, faces, name = [], [], [], None

    def flush():
        if name and verts:
            me = bpy.data.meshes.new("REF_" + name)
            me.from_pydata(verts, [], faces)
            me.validate()
            obj = bpy.data.objects.new("REF_" + name, me)
            obj.data.materials.append(skin if "head" in name else suit)
            L.link(obj)
            for poly in me.polygons:
                poly.use_smooth = True
            out.append(obj)
    base_idx = 1
    for line in open(pose_obj):
        if line.startswith("g "):
            flush()
            base_idx += len(verts)
            name, verts, faces = line[2:].strip(), [], []
        elif line.startswith("v "):
            x, y, z = map(float, line.split()[1:])
            verts.append((x, z, y - base_y))
        elif line.startswith("f "):
            faces.append([int(t) - base_idx for t in line.split()[1:]][::-1])   # Unity -> Blender is a mirror: keep normals outward
    flush()
    return out
