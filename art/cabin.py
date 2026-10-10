"""Rack-wall rooms for station modules and crew cabins (Starlab, Hitchhiker, Wayfarer): ISS-style interiors where four
flat walls of equipment racks (port, starboard, ceiling, floor) run the length of a cylindrical module between two end
bulkheads with round hatches, with utility runs in the corners.

Room coordinates (Blender): X across (port -X, starboard +X), Y from the floor (-Y) to the ceiling (+Y), Z along the
module axis (aft end Z0, forward end Z1). The crew sit upright (head towards +Y) at workstations on the side walls.

Walls give frames with `frame(wall, u, v)`: u across the wall (its right as seen from inside), v up the wall, both in
metres from the wall's centre, and the basis (right, up, normal into the room) that props and modules expect.
"""
import math
import random

import ivalib as L  # imports bpy first
import capsule as C
import modules as G
import props as P
import stock as S
from mathutils import Matrix, Vector

M = L.M


class Room:
    def __init__(self, xw, yf, yc, z0, z1):
        self.xw, self.yf, self.yc, self.z0, self.z1 = xw, yf, yc, z0, z1

    @property
    def zm(self):
        return (self.z0 + self.z1) / 2

    def frame(self, wall, u, v, lift=0.0):
        """Point and basis on a wall. u: along the wall's right, v: along its up (from the wall centre)."""
        X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
        ym = (self.yf + self.yc) / 2
        if wall == "port":     # x = -xw, facing +X; right = -Z (seen from inside), up = +Y
            c, r, up, n = Vector((-self.xw, ym, self.zm)), -Z, Y, X
        elif wall == "stbd":
            c, r, up, n = Vector((self.xw, ym, self.zm)), Z, Y, -X
        elif wall == "ceil":   # up the wall = forward (+Z)
            c, r, up, n = Vector((0, self.yc, self.zm)), X, Z, -Y
        elif wall == "floor":
            c, r, up, n = Vector((0, self.yf, self.zm)), -X, Z, Y
        elif wall == "fore":
            c, r, up, n = Vector((0, ym, self.z1)), -X, Y, -Z
        elif wall == "aft":
            c, r, up, n = Vector((0, ym, self.z0)), X, Y, Z
        else:
            raise ValueError(wall)
        return c + r * u + up * v + n * lift, L.basis(r, up, n)

    def size(self, wall):
        """(width, height) of a wall."""
        h = self.yc - self.yf
        if wall in ("port", "stbd"):
            return self.z1 - self.z0, h
        if wall in ("ceil", "floor"):
            return 2 * self.xw, self.z1 - self.z0
        return 2 * self.xw, h

    def u_of_z(self, wall, z):
        """u on a side wall for a position z along the module."""
        return -(z - self.zm) if wall == "port" else (z - self.zm)


def materials():
    M["leaf"] = L.material("IVA_Leaf", (0.16, 0.42, 0.10), rough=0.6)
    M["leaf2"] = L.material("IVA_LeafLight", (0.30, 0.55, 0.16), rough=0.6)
    M["soil"] = L.material("IVA_Soil", (0.18, 0.11, 0.06), rough=0.95)
    M["fruit"] = L.material("IVA_Fruit", (0.75, 0.09, 0.06), rough=0.35)
    M["fruit2"] = L.material("IVA_FruitYellow", (0.85, 0.62, 0.10), rough=0.35)
    M["grow"] = L.material("IVA_GrowLight", (1.0, 0.55, 0.85), rough=0.3, emit=3.0)
    M["stool"] = L.material("IVA_StoolPad", (0.30, 0.11, 0.07), rough=0.8)
    M["glass_clear"] = L.material("IVA_GreenhouseGlass", (0.55, 0.62, 0.66), rough=0.05, metal=0.0)


# ------------------------------------------------------------------ the room shell: wall panels, corners, ends
def wall_panel(room, wall, name, mat=None, inset=0.0):
    w, h = room.size(wall)
    p, b = room.frame(wall, 0, 0)
    S.cbox(name, (w, h, 0.03), mat or M["blanket"], p - b.col[2] * (0.015 - inset), b, ch=0.0)


def corners(room, name="Corner", depth=0.16):
    """Utility runs in the four long corners: a 45-degree closeout panel with a light strip and a cable bundle."""
    for k, (sx, sy) in enumerate(((-1, 1), (1, 1), (-1, -1), (1, -1))):
        cx = sx * room.xw
        cy = room.yc if sy > 0 else room.yf
        a = Vector((cx - sx * depth, cy, room.z0))
        b = Vector((cx, cy - sy * depth, room.z0))
        S.sweep(f"{name}{k}", [(a + b) / 2, (a + b) / 2 + Vector((0, 0, room.z1 - room.z0))],
                [Vector((-sx, -sy, 0)).normalized()] * 2, S.chamfer_rect((a - b).length, 0.03, 0.006), M["frame"])
        if sy > 0:   # ceiling corners carry the cabin light strips
            mid = (a + b) / 2 + Vector((-sx, -sy, 0)).normalized() * 0.018
            L.box(f"{name}{k}Light", (0.03, 0.03, room.z1 - room.z0 - 0.3), M["light"], mid + Vector((0, 0, (room.z1 - room.z0) / 2)),
                  Matrix.Rotation(math.radians(45 * sx), 3, "Z"))
        else:        # floor corners carry the cable bundles
            q = (a + b) / 2 + Vector((-sx, -sy, 0)).normalized() * 0.035
            S.bundle(f"{name}{k}Run", [q + Vector((0, 0, 0.2)), q + Vector((0, 0, (room.z1 - room.z0) - 0.2))], n=4, ends=(False, False))


def end_bulkhead(room, wall, name, hatch_r=0.45):
    """End wall with a round hatch (frame, door with a small window, handle, latches) and equipment round it."""
    w, h = room.size(wall)
    p, b = room.frame(wall, 0, 0)
    S.cbox(name, (w, h, 0.03), M["blanket"], p - b.col[2] * 0.015, b, ch=0.0)
    hp, hb = room.frame(wall, 0, -0.05)
    rot = L.basis(hb.col[0], hb.col[1], hb.col[2])
    ring = [hp + (hb.col[0] * math.cos(a) + hb.col[1] * math.sin(a)) * (hatch_r + 0.04) + hb.col[2] * 0.03 for a in [2 * math.pi * j / 48 for j in range(48)]]
    S.sweep(name + "HatchRing", ring, [hb.col[2]] * 48, S.chamfer_rect(0.08, 0.06), M["frame_dark"], closed=True)
    L.cylinder(name + "HatchDoor", hatch_r, 0.04, M["hatch"], hp + hb.col[2] * 0.035, rot, segs=48, bevel=0.008)
    L.cylinder(name + "HatchWindow", 0.07, 0.01, M["glass_dark"], hp + hb.col[1] * 0.2 + hb.col[2] * 0.058, rot, segs=24)
    L.torus(name + "HatchWindowRim", 0.072, 0.008, M["frame_dark"], hp + hb.col[1] * 0.2 + hb.col[2] * 0.06, rot, seg=24, mseg=6)
    L.tube(name + "HatchHandle", [hp + hb.col[0] * -0.12 + hb.col[2] * 0.055, hp + hb.col[0] * -0.12 + hb.col[2] * 0.11,
                                  hp + hb.col[0] * 0.12 + hb.col[2] * 0.11, hp + hb.col[0] * 0.12 + hb.col[2] * 0.055], 0.012, M["yellow"])
    for k in range(6):
        a = 2 * math.pi * (k + 0.5) / 6
        q = hp + (hb.col[0] * math.cos(a) + hb.col[1] * math.sin(a)) * (hatch_r - 0.03) + hb.col[2] * 0.06
        S.cbox(f"{name}HatchLatch{k}", (0.05, 0.025, 0.02), M["yellow"], q, rot @ Matrix.Rotation(a, 3, "Z"), ch=0.003)
    # equipment either side of the hatch
    for side in (-1, 1):
        u = side * (hatch_r + 0.32)
        q, qb = room.frame(wall, u, 0.25)
        G.box_unit(f"{name}Unit{side}", q + qb.col[2] * 0.06, (0.3, 0.12, 0.28), L.basis(qb.col[0], -qb.col[2], qb.col[1]), lamps_n=3)
        q, qb = room.frame(wall, u, -0.35)
        S.grille(f"{name}Vent{side}", q, qb, 0.26, 0.16, slats=7)
    q, qb = room.frame(wall, 0, hatch_r + 0.16)
    s = C.Surface(name + "Panel", q + qb.col[2] * 0.03, qb.col[0], qb.col[1], 0.5, 0.12, corner=0.015)
    s.build(M["console"], thick=0.025)
    G.grid(s, name + "Panel", 4, 1, [("annunciators", 0, 0, 2, 1, {"cols": 4, "rows": 2, "start": 2}), ("toggles", 2, 0, 1, 1, {"cols": 3}),
                                      ("lamps", 3, 0, 1, 1, {"n": 3})], border=0.01)
    s.check()


# ------------------------------------------------------------------ racks
def rack_frame(name, p, b, w, h, d=0.06):
    """The frame of an equipment rack on a wall: chamfered posts and rails with a dark back."""
    S.cbox(name + "Back", (w, h, 0.012), M["locker"], p + b.col[2] * 0.006, b, ch=0.0)   # textured rack face: seams, bolts
    for k, (cx, cy, fw, fh) in enumerate(((0, h / 2, w + 0.06, 0.05), (0, -h / 2, w + 0.06, 0.05), (w / 2, 0, 0.05, h), (-w / 2, 0, 0.05, h))):
        S.cbox(f"{name}Frame{k}", (fw, fh, d), M["frame"], p + b.col[0] * cx + b.col[1] * cy + b.col[2] * d / 2, b, ch=0.012)
    for k, cy in enumerate((h / 2 - 0.08, -h / 2 + 0.08)):
        for i in range(-3, 4):
            L.cylinder(f"{name}Bolt{k}{i}", 0.006, 0.006, M["buckle"], p + b.col[0] * (w / 2) * (i / 3.4) + b.col[1] * (cy + (0.04 if k == 0 else -0.04)) + b.col[2] * (d + 0.002), b, segs=6)


def module_panel(name, p, b, w, h, cols, rows, items, depth=0.03):
    s = C.Surface(name, p + b.col[2] * depth, b.col[0], b.col[1], w, h, corner=0.015)
    s.build(M["console"], thick=0.025)
    G.grid(s, name, cols, rows, items, border=0.012)
    s.check()
    G.housing(s, name, depth=depth)
    return s


def rack(room, wall, z, kind, name, w=0.9, seed=0):
    """One equipment rack on a side wall at position z along the module. Kinds: workstation, glovebox, freezer,
    stowage, life, comms."""
    rnd = random.Random(seed)
    W, H = room.size(wall)
    h = H - 0.12
    u = room.u_of_z(wall, z)
    p, b = room.frame(wall, u, 0)
    rack_frame(name, p, b, w, h)
    top = h / 2

    def at(v, lift=0.0, du=0.0):
        return p + b.col[0] * du + b.col[1] * v + b.col[2] * lift

    if kind in ("workstation", "comms"):
        module_panel(name + "Panel", at(top - 0.2), b, w - 0.1, 0.3, 6, 2, [
            ("mfd", 0, 0, 2, 2, {"screen": "mfd_systems" if kind == "workstation" else "mfd_comms"}), ("annunciators", 2, 0, 2, 1, {"cols": 4, "rows": 2, "start": 4 + seed % 8}),
            ("dial", 4, 0, 1, 1, {"kind": "press"}), ("dial", 5, 0, 1, 1, {"kind": "temp"}), ("toggles", 2, 1, 2, 1, {"cols": 6}), ("knobs", 4, 1, 2, 1, {"n": 3})])
        desk_v = -0.1
        module_panel(name + "Strip", at(top - 0.45), b, w - 0.1, 0.1, 6, 1, [("breakers", 0, 0, 4, 1, {"cols": 14, "rows": 2}), ("lamps", 4, 0, 2, 1, {"n": 4})], depth=0.02)
        dq = at(desk_v, 0.2)
        S.cbox(name + "Desk", (w - 0.06, 0.03, 0.36), M["module"], dq, b, ch=0.006)
        S.cbox(name + "DeskEdge", (w - 0.04, 0.035, 0.03), M["frame_dark"], dq + b.col[2] * 0.18, b, ch=0.006)
        L.box(name + "Keyboard", (0.3, 0.012, 0.12), M["module"], dq + b.col[1] * 0.021 + b.col[2] * 0.06, b, bevel=0.003)
        P.laptop(name + "Laptop", at(desk_v + 0.3, 0.0, du=-0.18), b, arm=0.22, screen="mfd_map" if kind == "workstation" else "mfd_engine")
        P.whiteboard(name + "Board", at(desk_v + 0.36, 0.0, du=0.24), b, 0.3, 0.2)
        if kind == "comms":
            P.headset(name + "Headset", at(desk_v + 0.25, 0.0, du=0.33), b)
        else:
            P.binders(name + "Binders", at(desk_v + 0.1, 0.0, du=0.33), b, n=3)
        P.drawer_stack(name + "Drawers", at(-h / 2 + 0.2, 0.0, du=w / 2 - 0.2), b, 0.28, 0.3, 3)
    elif kind == "glovebox":
        module_panel(name + "Panel", at(top - 0.15), b, w - 0.1, 0.2, 4, 1, [
            ("annunciators", 0, 0, 2, 1, {"cols": 4, "rows": 2, "start": 6}), ("lamps", 2, 0, 1, 1, {"n": 3}), ("toggles", 3, 0, 1, 1, {"cols": 3})])
        P.glovebox(name + "Glovebox", at(0.05, 0.0), b, w - 0.16, 0.42, 0.32)
        P.drawer_stack(name + "Drawers", at(-h / 2 + 0.22, 0.0), b, w - 0.2, 0.3, 3)
    elif kind == "freezer":
        for k, du in enumerate((-0.22, 0.22)):
            P.freezer(f"{name}Freezer{k}", at(0.15, 0.0, du=du), b, 0.38, 0.42, 0.28)
        P.drawer_stack(name + "Drawers", at(-h / 2 + 0.22, 0.0), b, w - 0.2, 0.3, 4)
        module_panel(name + "Panel", at(top - 0.12), b, w - 0.1, 0.16, 4, 1, [
            ("dial", 0, 0, 1, 1, {"kind": "temp"}), ("annunciators", 1, 0, 2, 1, {"cols": 4, "rows": 2, "start": 9}), ("lamps", 3, 0, 1, 1, {"n": 3})])
    elif kind == "life":
        rot = L.basis(b.col[0], -b.col[2], b.col[1])
        G.box_unit(name + "Unit0", at(0.25, 0.1), (w - 0.14, 0.2, 0.36), rot, lamps_n=3)
        G.box_unit(name + "Unit1", at(-0.2, 0.08), (w - 0.14, 0.16, 0.3), rot, vents=False, lamps_n=2)
        for k, du in enumerate((-0.2, 0.2)):
            c = at(-h / 2 + 0.2, 0.11, du=du)
            L.cylinder(f"{name}Tank{k}", 0.09, 0.3, M["tank"], c, L.basis(b.col[0], b.col[2], -b.col[1]) @ Matrix.Rotation(math.pi / 2, 3, "X"), segs=24, bevel=0.03)
        S.grille(name + "Vent", at(top - 0.1, 0.0), b, w - 0.2, 0.12)
    else:   # stowage
        P.drawer_stack(name + "Drawers", at(0.15, 0.0), b, w - 0.16, 0.5, 5)
        P.cargo_bag(name + "Bag", at(-h / 2 + 0.22, 0.0, du=-0.18), b, 0.36, 0.26, 0.2)
        P.net_with_gear(name + "Net", at(top - 0.17, 0.0), b, w - 0.16, 0.24)


# ------------------------------------------------------------------ seats and plants
def stool(name, hip, facing, floor_y):
    """Fold-down workstation stool under a kerbal's hips: post to the floor, a pad, a foot bar."""
    f = Vector(facing).normalized()
    top = Vector((hip[0], hip[1] - 0.06, hip[2]))
    S.cbox(name + "Pad", (0.26, 0.04, 0.24), M["stool"], top, ch=0.012)
    S.beam(name + "Post", top - Vector((0, 0.02, 0)), Vector((top.x, floor_y + 0.02, top.z)), 0.04, 0.04, M["frame"], up=(1, 0, 0))
    S.cbox(name + "Base", (0.16, 0.025, 0.16), M["frame_dark"], (top.x, floor_y + 0.0125, top.z), ch=0.006)
    bar = top + f * 0.42
    L.tube(name + "FootBar", [Vector((bar.x - 0.0, floor_y + 0.005, bar.z - 0.18)), Vector((bar.x, floor_y + 0.06, bar.z - 0.18)),
                              Vector((bar.x, floor_y + 0.06, bar.z + 0.18)), Vector((bar.x, floor_y + 0.005, bar.z + 0.18))], 0.01, M["yellow"])


def seat(eye, facing, up=(0, 1, 0)):
    """Seat entry for capsule.eye_marker: eye point, view direction and view up."""
    return {"eye": list(eye), "fwd": list(facing), "up": list(up)}


def hip_of(eye, facing, up=(0, 1, 0)):
    """Where the kerbal's hips go for an eye point (the portrait-booth seated pose: eye 0.518 up, 0.149 forward)."""
    return Vector(eye) - Vector(up).normalized() * 0.518 - Vector(facing).normalized() * 0.149


def plant(name, base, rnd, h=0.22, fruit=True):
    """A small crop plant: a stem with leaves and a few fruit."""
    base = Vector(base)
    L.tube(name + "Stem", [base, base + Vector((0, h * 0.5, 0)), base + Vector((rnd.uniform(-0.02, 0.02), h, rnd.uniform(-0.02, 0.02)))], 0.006, M["leaf"])
    for k in range(7):
        t = 0.3 + 0.7 * k / 7
        a = rnd.uniform(0, 2 * math.pi)
        q = base + Vector((math.cos(a) * 0.05, h * t, math.sin(a) * 0.05))
        rot = Matrix.Rotation(a, 3, "Y") @ Matrix.Rotation(rnd.uniform(-0.5, 0.5), 3, "X")
        L.sphere(f"{name}Leaf{k}", 0.045, M["leaf" if k % 2 else "leaf2"], q, rot @ Matrix.Diagonal((1.0, 0.18, 0.55)).to_3x3(), u=10, v=5)
    if fruit:
        for k in range(rnd.randint(1, 3)):
            a = rnd.uniform(0, 2 * math.pi)
            L.sphere(f"{name}Fruit{k}", 0.018, M["fruit" if rnd.random() < 0.6 else "fruit2"],
                     base + Vector((math.cos(a) * 0.04, h * rnd.uniform(0.4, 0.8), math.sin(a) * 0.04)), u=10, v=6)


def greenhouse(room, name, x0, x1, z0, z1, depth, seed=3):
    """Greenhouse bay above a ceiling window: grow-light panels, plant trays, water lines, a glass pane."""
    rnd = random.Random(seed)
    yc = room.yc
    ytop = yc + depth
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    w, l = x1 - x0, z1 - z0
    # bay walls (inside faces), grow lights in the roof
    S.cbox(name + "Roof", (w + 0.06, 0.02, l + 0.06), M["frame"], (cx, ytop + 0.01, cz), ch=0.0)
    for k, sx in enumerate((-1, 1)):
        S.cbox(f"{name}Side{k}", (0.02, depth, l + 0.06), M["frame"], (cx + sx * (w / 2 + 0.02), yc + depth / 2, cz), ch=0.0)
        S.cbox(f"{name}End{k}", (w + 0.06, depth, 0.02), M["frame"], (cx, yc + depth / 2, cz + sx * (l / 2 + 0.02)), ch=0.0)
    for k in range(3):
        z = z0 + l * (k + 0.5) / 3
        S.cbox(f"{name}Grow{k}", (w - 0.1, 0.012, l / 3 - 0.12), M["grow"], (cx, ytop - 0.01, z), ch=0.002)
    # plant trays on both sides of a centre walkway strip, plants growing towards the cabin (down)
    for side in (-1, 1):
        tx = cx + side * w * 0.27
        S.cbox(f"{name}Tray{side}", (w * 0.4, 0.05, l - 0.1), M["frame_dark"], (tx, ytop - 0.06, cz), ch=0.008)
        S.cbox(f"{name}Soil{side}", (w * 0.36, 0.01, l - 0.16), M["soil"], (tx, ytop - 0.09, cz), ch=0.0)
        L.tube(f"{name}Water{side}", [Vector((tx + side * w * 0.17, ytop - 0.04, z0 + 0.05)), Vector((tx + side * w * 0.17, ytop - 0.04, z1 - 0.05))], 0.008, M["umbilical"])
        n = int((l - 0.2) / 0.16)
        for i in range(n):
            for j in (-1, 1):
                q = Vector((tx + j * w * 0.09, ytop - 0.09, z0 + 0.15 + i * (l - 0.3) / max(1, n - 1)))
                # grow downwards: build upright then flip (plants hang from the trays in the roof)
                pl_base = q
                h = rnd.uniform(0.14, 0.24)
                L.tube(f"{name}P{side}{i}{j}Stem", [pl_base, pl_base - Vector((0, h, 0))], 0.006, M["leaf"])
                for k in range(6):
                    a = rnd.uniform(0, 2 * math.pi)
                    lq = pl_base - Vector((-math.cos(a) * 0.045, h * (0.3 + 0.7 * k / 6), -math.sin(a) * 0.045))
                    L.sphere(f"{name}P{side}{i}{j}Leaf{k}", 0.042, M["leaf" if k % 2 else "leaf2"], lq,
                             Matrix.Rotation(a, 3, "Y") @ Matrix.Diagonal((1.0, 0.2, 0.55)).to_3x3(), u=10, v=5)
                if rnd.random() < 0.6:
                    L.sphere(f"{name}P{side}{i}{j}Fruit", 0.02, M["fruit" if rnd.random() < 0.6 else "fruit2"],
                             pl_base - Vector((0.03, h * 0.7, 0.0)), u=10, v=6)
    # window frame in the ceiling and a thin glass pane (seen through: kept very transparent-looking by being dark-clear)
    S.sweep(name + "Frame", [Vector((x0 - 0.04, yc - 0.01, z0 - 0.04)), Vector((x1 + 0.04, yc - 0.01, z0 - 0.04)), Vector((x1 + 0.04, yc - 0.01, z1 + 0.04)),
                             Vector((x0 - 0.04, yc - 0.01, z1 + 0.04))], [Vector((0, 1, 0))] * 4, S.chamfer_rect(0.07, 0.05), M["frame_dark"], closed=True)
    for k in range(1, 3):
        z = z0 + l * k / 3
        S.beam(f"{name}Mullion{k}", Vector((x0, yc - 0.005, z)), Vector((x1, yc - 0.005, z)), 0.04, 0.03, M["frame_dark"])


# ------------------------------------------------------------------ walls with openings, window wells, tables, views
def panel_with_holes(room, wall, name, holes=(), mat=None, step=0.1, thick=0.03):
    """A wall built from tiles, leaving out tiles inside any hole. holes: polygons [(u, v), ...] in wall coordinates."""
    import bmesh
    w, h = room.size(wall)
    p0, b = room.frame(wall, 0, 0)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")

    def inside(poly, u, v):
        c = False
        for (u1, v1), (u2, v2) in zip(poly, poly[1:] + poly[:1]):
            if (v1 > v) != (v2 > v) and u < (u2 - u1) * (v - v1) / (v2 - v1) + u1:
                c = not c
        return c

    boxes = [(min(u for u, v in poly) - step, max(u for u, v in poly) + step, min(v for u, v in poly) - step, max(v for u, v in poly) + step) for poly in holes]

    def tile(u0, v0, u1, v1):
        vs = [bm.verts.new(p0 + b.col[0] * u + b.col[1] * v) for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]
        f = bm.faces.new(vs)
        for l in f.loops:
            q = l.vert.co - p0
            l[uv].uv = (q.dot(b.col[0]), q.dot(b.col[1]))

    nu, nv = int(round(w / step)), int(round(h / step))
    for i in range(nu):
        for j in range(nv):
            u0, v0 = -w / 2 + i * w / nu, -h / 2 + j * h / nv
            u1, v1 = u0 + w / nu, v0 + h / nv
            if any(bu0 < (u0 + u1) / 2 < bu1 and bv0 < (v0 + v1) / 2 < bv1 for bu0, bu1, bv0, bv1 in boxes):
                k = 5   # near a hole: finer tiles so the opening's edge follows its outline
                for a_ in range(k):
                    for c_ in range(k):
                        su0, sv0 = u0 + (u1 - u0) * a_ / k, v0 + (v1 - v0) * c_ / k
                        su1, sv1 = su0 + (u1 - u0) / k, sv0 + (v1 - v0) / k
                        if not any(inside(poly, (su0 + su1) / 2, (sv0 + sv1) / 2) for poly in holes):
                            tile(su0, sv0, su1, sv1)
                continue
            tile(u0, v0, u1, v1)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.normal_update()
    for f in bm.faces:
        if f.normal.dot(b.col[2]) < 0:
            f.normal_flip()
    o = L.mesh_obj(name, bm, [mat or M["blanket"]])
    L.solidify(o, thick, offset=-1.0)
    return o


def window_well(room, wall, name, poly, depth, glass=None):
    """A tube through the wall from a polygon opening (wall coordinates u, v) out to `depth` behind the wall, with a
    chamfered frame round it on the room side and an optional dark-glass rim at the far end."""
    p0, b = room.frame(wall, 0, 0)
    pts = [p0 + b.col[0] * u + b.col[1] * v for u, v in poly]
    n = len(pts)
    for k in range(n):
        a, c = pts[k], pts[(k + 1) % n]
        mid = (a + c) / 2 - b.col[2] * depth / 2
        along = (c - a)
        side = along.normalized()
        rot = L.basis(side, -b.col[2], side.cross(-b.col[2]))
        L.box(f"{name}Side{k}", (along.length, depth, 0.012), M["frame_dark"], mid, rot)
    ring = [q + b.col[2] * 0.012 for q in pts]
    centre = sum(ring, Vector()) / n
    ring = [centre + (q - centre) * 1.0 for q in ring]
    S.sweep(name + "Frame", ring, [b.col[2]] * n, S.chamfer_rect(0.06, 0.03, 0.008), M["frame"], closed=True)
    for k, q in enumerate(ring):
        L.cylinder(f"{name}Bolt{k}", 0.007, 0.006, M["buckle"], q + b.col[2] * 0.018 + (centre - q).normalized() * 0.0, b, segs=6)


def table(name, x, z, floor_y, h=0.62, r=0.32):
    """Wardroom table standing on the floor (+Y up): chamfered octagonal top, column, bolted base, a meal tray."""
    top = floor_y + h
    rotY = Matrix.Rotation(-math.pi / 2, 3, "X")   # cylinder axis Z -> Y
    L.cylinder(name + "Top", r, 0.035, M["frame"], (x, top, z), rotY, segs=8, bevel=0.012)
    L.cylinder(name + "Inset", r * 0.82, 0.006, M["frame_dark"], (x, top + 0.019, z), rotY, segs=8)
    S.cbox(name + "Column", (0.09, h - 0.04, 0.09), M["frame"], (x, floor_y + (h - 0.04) / 2 + 0.02, z), ch=0.02)
    S.cbox(name + "Base", (0.26, 0.03, 0.26), M["frame_dark"], (x, floor_y + 0.015, z), ch=0.01)
    rot = Matrix.Rotation(0.4, 3, "Y")
    q = Vector((x, top + 0.024, z))
    L.box(name + "Tray", (0.3, 0.012, 0.2), M["frame_dark"], q, rot, bevel=0.004, segs=1)
    tiles = ((0, 0.5, 0.5, 1), (0.5, 0.5, 1, 1), (0, 0, 0.5, 0.5), (0.5, 0, 1, 0.5))
    face_up = rot @ Matrix.Rotation(-math.pi / 2, 3, "X")
    for k, (dx, dz) in enumerate(((-0.07, -0.045), (0.03, -0.045), (-0.07, 0.045), (0.03, 0.045))):
        cq = q + rot @ Vector((dx, 0.017, dz))
        L.box(f"{name}Cup{k}", (0.08, 0.022, 0.075), M["frame"], cq, rot, bevel=0.006, segs=1)
        L.plane(f"{name}Food{k}", 0.068, 0.063, M["food_tex"], cq + Vector((0, 0.0115, 0)), face_up, uv_rect=tiles[k])
    L.box(name + "Drink", (0.05, 0.015, 0.08), M["canvas"], q + rot @ Vector((0.11, 0.012, 0)), rot, bevel=0.006)


def view(name, frm, at):
    """Window view markers for the B key: camera position and the point it looks at."""
    import bpy
    for nm, p in ((f"IVA_View_{name}", frm), (f"IVA_ViewAt_{name}", at)):
        e = bpy.data.objects.new(nm, None)
        e.empty_display_size = 0.02
        e.location = Vector(p)
        L.link(e)


def sleep_wall(room, wall, z, name, w=0.78):
    """A crew sleep station on a side wall, centred at position z along the module."""
    p, b = room.frame(wall, room.u_of_z(wall, z), 0.0)
    P.sleep_station(name, p, b, w, room.size(wall)[1] - 0.2, 0.32)


def counter_run(room, wall, z0, z1, name, h=0.5):
    """Galley counter along a side wall from z0 to z1: cabinets with a worktop, an oven, a galley unit, food lockers."""
    n = max(1, int((z1 - z0) / 0.36))
    w = (z1 - z0) / n
    ym = (room.yf + room.yc) / 2
    for k in range(n):
        z = z0 + w * (k + 0.5)
        p, b = room.frame(wall, room.u_of_z(wall, z), room.yf + h / 2 - ym)
        P.cabinet(f"{name}Cab{k}", p, b, w - 0.01, h, 0.4, doors=1 if k % 2 else 2, top=M["module"])
    zc = (z0 + z1) / 2
    P.oven(name + "Oven", *room.frame(wall, room.u_of_z(wall, zc - w / 2), room.yf + h + 0.25 - ym))
    P.galley(name + "Galley", *room.frame(wall, room.u_of_z(wall, zc + w / 2), room.yf + h + 0.3 - ym), w=0.3, h=0.4)
    for k, z in enumerate((z0 + w * 0.5, z1 - w * 0.5)):
        P.cabinet(f"{name}Locker{k}", *room.frame(wall, room.u_of_z(wall, z), room.yc - 0.25 - ym), w - 0.02, 0.3, 0.3, doors=1)


# ------------------------------------------------------------------ dressing: fill bare wall with structure and kit
def _box_at(name, p, b, w=0.1, h=0.12, d=0.07):
    S.cbox(name, (w, h, d), M["frame"], p + b.col[2] * d / 2, b, ch=0.01)
    S.cbox(name + "Lid", (w * 0.8, h * 0.8, 0.008), M["frame_dark"], p + b.col[2] * (d + 0.003), b, ch=0.002)


def wall_posts(room, wall, clear, spacing=0.55, name="Post"):
    """Vertical chamfered posts on a side wall (the room's ribs), stopping short of anything on the wall."""
    w, h = room.size(wall)
    n = int(w / spacing)
    for i in range(1, n):
        u = -w / 2 + w * i / n
        vs = [-h / 2 + 0.08 + (h - 0.16) * k / 40 for k in range(41)]

        def ok(v):
            p, b = room.frame(wall, u, v)
            return not clear.blocked(p + b.col[2] * 0.025, 0.012)

        for r, seg in enumerate(S.runs(vs, ok, 10)):
            a, b_ = room.frame(wall, u, seg[0])[0], room.frame(wall, u, seg[-1])[0]
            nrm = room.frame(wall, u, 0)[1].col[2]
            S.beam(f"{name}_{wall}{i}_{r}", a + nrm * 0.022, b_ + nrm * 0.022, 0.06, 0.044, M["frame"], up=nrm)


def wall_run(room, wall, v, clear, name, inset=0.05):
    """Horizontal cable bundle along a wall at height v, ending in junction boxes where something is in the way."""
    w, _ = room.size(wall)
    us = [-w / 2 + 0.1 + (w - 0.2) * k / 60 for k in range(61)]

    def pt(u):
        p, b = room.frame(wall, u, v)
        return p + b.col[2] * inset

    def ok(u):
        return not clear.blocked(pt(u), 0.04)

    for r, seg in enumerate(S.runs(us, ok, 8)):
        if seg[-1] - seg[0] < 0.5:
            continue
        S.bundle(f"{name}{r}", [pt(u) for u in seg[::4] + [seg[-1]]], n=4, ends=(False, False))
        for e, u in enumerate((seg[0], seg[-1])):
            p, b = room.frame(wall, u, v)
            _box_at(f"{name}{r}Box{e}", p, b)


def dress(room, walls=("port", "stbd", "aft", "fore", "ceil"), cell=0.42, seed=1, name="Dress"):
    """Fill bare stretches of wall with stock-style kit: bolted plates, equipment boxes, small panels, grilles."""
    rnd = random.Random(seed)
    clear = S.Clearance()
    k = 0
    for wall in walls:
        w, h = room.size(wall)
        nu, nv = max(1, int(w / cell)), max(1, int(h / cell))
        for i in range(nu):
            for j in range(nv):
                u, v = -w / 2 + (i + 0.5) * w / nu, -h / 2 + (j + 0.5) * h / nv
                p, b = room.frame(wall, u, v)
                kind = rnd.random()
                sw, sh = (0.3, 0.22) if kind < 0.45 else (0.26, 0.2)
                probe = [p + b.col[0] * su * (sw / 2 + 0.03) + b.col[1] * sv * (sh / 2 + 0.03) + b.col[2] * dz
                         for su in (-1, 0, 1) for sv in (-1, 0, 1) for dz in (0.02, 0.12)]
                if any(clear.blocked(q, 0.01) for q in probe):
                    continue
                nm = f"{name}_{wall}{k}"
                if kind < 0.4:
                    S.inspection_plate("Plate_" + nm, p, b, sw, sh)
                elif kind < 0.65:
                    G.box_unit(nm, p + b.col[2] * 0.05, (sw, 0.1, sh), L.basis(b.col[0], -b.col[2], b.col[1]), vents=rnd.random() < 0.5, lamps_n=2)
                elif kind < 0.85:
                    module_panel(nm, p, b, sw + 0.06, sh * 0.6, 2, 1, [("annunciators", 0, 0, 1, 1, {"cols": 2, "rows": 2, "start": rnd.randint(0, 10)}),
                                                                        ("toggles", 1, 0, 1, 1, {"cols": 3})], depth=0.02)
                else:
                    S.grille(nm, p, b, sw, sh)
                k += 1
    return k


def dress_room(room, seed=1):
    """The full stock-style pass for a rack room: posts and cable runs on the side walls, then kit on bare wall."""
    clear = S.Clearance()
    for wall in ("port", "stbd"):
        wall_posts(room, wall, clear, name="Post")
    clear = S.Clearance()
    for wall in ("port", "stbd"):
        wall_run(room, wall, room.size(wall)[1] / 2 - 0.16, clear, f"Run_{wall}")
    return dress(room, seed=seed)
