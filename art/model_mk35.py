"""Mk3-5 (pod_3v_conical_crew) interior: five crew on a lower deck, an upper deck with a docking station.

Usage: blender -b --python model_mk35.py -- <spec.json> <texture_dir> <out.blend>

The game keeps the 3v's crew in the portrait booth, so the seats are ours: five couches in a row on one frame, eyes at
z 1.0, the same body pose as the Mk1-3 (spec "pose"). Above the faces hangs a five-section main display console; pedestal
consoles sit between the couches and side consoles beside the outer couches, under the two-pane side windows. Behind the
feet: environmental and power units, lockers and a ladder up through a hatch in the upper deck, a grated platform with an
equipment ring, and a docking station console under the two upper (docking) windows. The pod's windows are painted on
its hull, which isn't drawn from inside, so the openings here show the world.

Coordinates and conventions: see capsule.py.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ivalib as L  # noqa: E402  (imports bpy first)
from mathutils import Matrix, Vector  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:]
SPEC = json.load(open(ARGS[0]))
TEX, OUT = ARGS[1], ARGS[2]

L.begin(SPEC["interior"], TEX)
import capsule as C  # noqa: E402  (after begin: shares L.M)
import modules as G  # noqa: E402
import props as P  # noqa: E402
import stock as S  # noqa: E402
G.materials()

M = L.M
M["blanket"] = L.material("IVA_WallPanel", tex="wallpanel_color.png", normal="wallpanel_normal.png", rough=0.55, metal=0.3, uv_scale=(1.0, 1.0), normal_strength=0.8)
M["shell"] = L.material("IVA_SeatShell", (0.22, 0.23, 0.25), rough=0.4, metal=0.55)
M["bottle"] = L.material("IVA_Bottle", (0.22, 0.42, 0.30), rough=0.35, metal=0.4)
M["tank"] = L.material("IVA_Tank", (0.78, 0.79, 0.80), rough=0.3, metal=0.7)
M["periscope"] = L.material("IVA_Periscope", tex="periscope.png", rough=0.1, emit=1.6, emit_tex=True)
M["canvas"] = L.material("IVA_Canvas", (0.27, 0.28, 0.23), rough=0.92, normal="canvas_normal.png", uv_scale=(6.0, 6.0), normal_strength=0.8)
M["umbilical"] = L.material("IVA_Umbilical", (0.32, 0.36, 0.42), rough=0.7)
M["net"] = L.material("IVA_Net", (0.30, 0.32, 0.20), rough=0.9)
P.materials()
S.materials()
M["deckplate"] = L.material("IVA_DeckPlate", tex="deckplate_color.png", normal="deckplate_normal.png", rough=0.6, metal=0.35, normal_strength=0.8)

C.setup(SPEC, wall=SPEC["wall"], ceil=SPEC["ceiling"], top=SPEC["ceiling"] + 0.1, seg=192)
POSE = SPEC["pose"]
SEATS = POSE["seats"]
H = SPEC["hatch"]
HATCH_PHI, HATCH_HALF = C.rad(-H["angle"]), C.rad(H["half_deg"])
EYE_Z = SEATS[0]["eye"][2]
FLOOR = C.Z_FLOOR
DECK_Z = 2.0                      # upper (living and lab) deck floor
HOLE_Y0, HOLE_Y1, HOLE_HW = 1.0, 1.38, 0.3    # ladder opening in the deck, at the back of the aisle
BULK_Y, AISLE, BULK_TOP = 0.95, 0.34, 1.9     # aft equipment bulkhead: face plane, aisle half-width, top
SIDE_PHI0, SIDE_PHI1, SIDE_Z0, SIDE_Z1 = 76, 118, 0.78, 1.18


def keep_clear(phi):
    if C.ang_dist(phi, HATCH_PHI) < HATCH_HALF + C.rad(5):
        return True
    for w in C.WINDOWS:
        if C.ang_dist(phi, w["phi"]) < w["hw"] / C.r_in(w["z"]) + C.rad(5):
            return True
    return False


# ------------------------------------------------------------------ five-section main display console
MDC_Z, MDC_Y, MDC_H, MDC_W = EYE_Z + 0.44, -0.13, 0.42, 0.56


def section(name, x, tilt_deg):
    side = 1 if x > 0 else -1
    t = C.rad(tilt_deg)
    right = Vector((math.cos(t), 0, -side * math.sin(t))) if x else Vector((1, 0, 0))
    drop = abs(x) * 0.07
    return C.Surface(name, (x, MDC_Y, MDC_Z - drop), right, (0, -1, 0), MDC_W, MDC_H, bend=0.0, corner=0.04)


def build_mdc():
    secs = {0: section("MDC_C", 0.0, 0), 1: section("MDC_R1", 0.62, 8), -1: section("MDC_L1", -0.62, 8),
            2: section("MDC_R2", 1.24, 20), -2: section("MDC_L2", -1.24, 20)}
    for s in secs.values():
        s.build(M["console"], thick=0.03)
    layouts = {
        0: [("dial", 0, 0, 1, 1, {"kind": "alt"}), ("annunciators", 1, 0, 4, 1, {"cols": 8, "rows": 2}), ("dial", 5, 0, 1, 1, {"kind": "fuel"}),
            ("mfd", 0, 1, 2, 2, {"screen": "mfd_systems"}), ("navball", 2, 1, 2, 2, {}), ("mfd", 4, 1, 2, 2, {"screen": "mfd_map"}),
            ("abort", 0, 3, 1, 1, {}), ("buttons", 1, 3, 1, 1, {"n": 3}), ("toggles", 2, 3, 2, 1, {"cols": 6}), ("knobs", 4, 3, 1, 1, {"n": 2}),
            ("lamps", 5, 3, 1, 1, {"n": 3})],
        1: [("dial", 0, 0, 1, 1, {"kind": "press"}), ("dial", 1, 0, 1, 1, {"kind": "temp"}), ("annunciators", 2, 0, 2, 1, {"cols": 4, "rows": 2, "start": 4}),
            ("mfd", 0, 1, 2, 2, {"screen": "mfd_engine"}), ("keypad", 2, 1, 2, 2, {}), ("breakers", 0, 3, 4, 1, {"cols": 12, "rows": 2})],
        -1: [("knobs", 0, 0, 2, 1, {"n": 4}), ("dial", 2, 0, 1, 1, {"kind": "press"}), ("dial", 3, 0, 1, 1, {"kind": "temp"}),
             ("mfd", 0, 1, 2, 2, {"screen": "mfd_comms"}), ("screen", 2, 1, 2, 1, {"mat": "crt_orbit"}), ("toggles", 2, 2, 2, 1, {"cols": 6}),
             ("breakers", 0, 3, 2, 1, {"cols": 6, "rows": 2}), ("vent", 2, 3, 1, 1, {}), ("lamps", 3, 3, 1, 1, {"n": 3})],
        2: [("annunciators", 0, 0, 4, 1, {"cols": 8, "rows": 2, "start": 8}), ("screen", 0, 1, 2, 1, {"mat": "crt_data"}),
            ("dial", 2, 1, 1, 1, {"kind": "fuel"}), ("dial", 3, 1, 1, 1, {"kind": "press"}), ("toggles", 0, 2, 2, 1, {"cols": 6}),
            ("knobs", 2, 2, 2, 1, {"n": 4}), ("breakers", 0, 3, 4, 1, {"cols": 12, "rows": 2})],
        -2: [("mfd", 0, 0, 2, 2, {"screen": "mfd_systems"}), ("periscope", 2, 0, 2, 2, {}), ("lamps", 0, 2, 2, 1, {"n": 4}),
             ("toggles", 2, 2, 2, 1, {"cols": 6}), ("breakers", 0, 3, 4, 1, {"cols": 12, "rows": 2})],
    }
    for k, s in secs.items():
        G.grid(s, s.name, 6 if k == 0 else 4, 4, layouts[k])
        s.check()
        G.housing(s, s.name)
    # structure: seams between sections, hangers up to the deck, hood with floodlights and a handrail
    for x in (-0.93, -0.31, 0.31, 0.93):
        z = MDC_Z - abs(x) * 0.07 + 0.01
        S.beam(f"MDC_Seam{x}", Vector((x, MDC_Y - MDC_H / 2 - 0.02, z)), Vector((x, MDC_Y + MDC_H / 2 + 0.02, z)), 0.05, 0.05, M["frame"], up=(0, 0, 1))
        for k, y in enumerate((MDC_Y - 0.17, MDC_Y + 0.17)):
            S.beam(f"MDC_Hanger{x}_{k}", Vector((x, y, z + 0.02)), Vector((x, y, DECK_Z - 0.08)), 0.038, 0.038, M["frame"], up=(0, 1, 0))
            for zz in (z + 0.16, DECK_Z - 0.16):
                S.cbox(f"MDC_Collar{x}_{k}_{zz:.2f}", (0.054, 0.054, 0.035), M["frame_dark"], (x, y, zz), ch=0.006)
    hy = MDC_Y + MDC_H / 2 + 0.02
    S.cbox("MDC_Hood", (3.0, 0.04, 0.08), M["frame"], (0, hy, MDC_Z - 0.03), ch=0.012)
    aim = Vector((0, 0.45, -1)).normalized()
    for k, x in enumerate((-1.24, -0.62, 0.0, 0.62, 1.24)):
        p = Vector((x, hy + 0.01, MDC_Z - 0.08 - abs(x) * 0.07))
        L.cylinder(f"Flood_{k}", 0.022, 0.03, M["ring"], p, (-aim).to_track_quat("Z", "Y").to_matrix(), segs=20, radius2=0.017)
        L.disc(f"FloodLens_{k}", 0.014, M["light"], p + aim * 0.016, aim.to_track_quat("Z", "Y").to_matrix(), segs=20)
    L.plane("NamePlate", 0.3, 0.06, M["plate"], Vector((0, hy + 0.017, MDC_Z - 0.03)), L.basis(Vector((-1, 0, 0)), Vector((0, 0, 1)), Vector((0, 1, 0))))


# ------------------------------------------------------------------ couches, pedestals, umbilicals
PED_W, PED_Y0, PED_Y1 = 0.15, -0.06, 0.32


def build_lower_deck():
    for i, seat in enumerate(SEATS):
        C.couch(f"Couch{i}_", seat["x"], POSE, FLOOR)
    xs = sorted(s["x"] for s in SEATS)
    prof = POSE["couch"]
    for k, y in enumerate((prof[len(prof) // 4][0], prof[(3 * len(prof)) // 4][0])):
        z = min(zz for yy, zz, ww in prof if abs(yy - y) < 0.04) - 0.1
        S.beam(f"CouchFrameBeam_{k}", Vector((xs[0] - 0.16, y, z)), Vector((xs[-1] + 0.16, y, z)), 0.05, 0.06, M["frame"])
        for x in (xs[0] - 0.14, -0.31, 0.31, xs[-1] + 0.14):
            S.beam(f"CouchFrameLeg_{k}_{x:.2f}", Vector((x, y, z)), Vector((x * 1.04, y, FLOOR + 0.02)), 0.045, 0.045, M["frame"], up=(0, 1, 0))
            S.cbox(f"CouchFrameFoot_{k}_{x:.2f}", (0.09, 0.09, 0.025), M["frame_dark"], (x * 1.04, y, FLOOR + 0.0125), ch=0.008)
            for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
                L.cylinder(f"CouchFrameFootBolt_{k}_{x:.2f}_{i}", 0.006, 0.008, M["buckle"], (x * 1.04 + sx * 0.032, y + sy * 0.032, FLOOR + 0.028), segs=6)
    z0p, z1p = 0.45 + (EYE_Z - 0.718), 0.53 + (EYE_Z - 0.718)
    up_dir = Vector((0, PED_Y0 - PED_Y1, z0p - z1p)).normalized()
    slope = math.hypot(PED_Y1 - PED_Y0, z1p - z0p)
    for k, x in enumerate((-0.93, -0.31, 0.31, 0.93)):
        G.prism(f"Pedestal{k}", [(PED_Y0, FLOOR), (PED_Y1, FLOOR), (PED_Y1, z1p), (PED_Y0, z0p)], x - PED_W / 2, x + PED_W / 2, M["console"])
        top = C.Surface(f"PedestalTop{k}", (x, (PED_Y0 + PED_Y1) / 2, (z0p + z1p) / 2 + 0.004), (-1, 0, 0), up_dir, PED_W - 0.012, slope - 0.02, corner=0.01)
        G.grid(top, f"Ped{k}", 2, 4, [
            ("toggles", 0, 0, 2, 1, {"cols": 4}), ("dial", 0, 1, 1, 1, {"kind": ("press", "temp")[k % 2]}), ("knobs", 1, 1, 1, 1, {"n": 1}),
            ("lamps", 0, 2, 2, 1, {"n": 4}), ("buttons", 0, 3, 1, 1, {"n": 2}), ("toggles", 1, 3, 1, 1, {"cols": 2})], gap=0.004, border=0.004)
        top.check()
        G.vent(f"PedestalVent{k}", Vector((x, PED_Y0 - 0.001, (FLOOR + z0p) / 2)), L.basis(Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0))),
               PED_W * 0.7, (z0p - FLOOR) * 0.5, slots=8)
    # umbilicals to every suit, from the ports on the aft bulkhead
    for i, seat in enumerate(SEATS):
        x = seat["x"]
        dz = EYE_Z - 0.718
        start = Vector((UMB_X[i], BULK_Y - 0.03, FLOOR + 0.3))
        pts = [start, Vector((x - 0.25, 0.38, 0.38 + dz)), Vector((x - 0.25, 0.1, 0.5 + dz)), Vector((x - 0.2, -0.1, 0.58 + dz)), Vector((x - 0.13, -0.16, 0.6 + dz))]
        G.hose(f"Umbilical{i}", pts, r=0.018, mat=M["umbilical"])
        L.cylinder(f"UmbilicalPlug{i}", 0.026, 0.04, M["buckle"], pts[-1], (pts[-1] - pts[-2]).normalized().to_track_quat("Z", "Y").to_matrix(), segs=16)


# ------------------------------------------------------------------ aft equipment bulkhead (the shuttle mid-deck locker wall)
UMB_X = [(-0.42 if s["x"] <= 0 else 0.42) + 0.0 for s in SEATS]


def bulk_x(z):
    """Half-width of the bulkhead face at height z, where its plane meets the hull."""
    return math.sqrt(max(0.0, C.r_in(z) ** 2 - BULK_Y ** 2)) - 0.015


def bulk_frame(x, z):
    """Frame on the bulkhead face: right +X (seen from the couches), up +Z, normal towards the couches (-Y)."""
    return Vector((x, BULK_Y, z)), L.basis(Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0)))


def slab(name, side, depth=0.35):
    """One half of the bulkhead: a solid from the aisle edge to the hull, floor to BULK_TOP, front face at BULK_Y; its back
    face (depth behind) is trimmed to the hull too, so the top closes off the space behind without poking through."""
    import bmesh
    zs = [FLOOR + (BULK_TOP - FLOOR) * k / 10 for k in range(11)]
    outline = [(AISLE, FLOOR)] + [(bulk_x(z), z) for z in zs] + [(AISLE, BULK_TOP)]
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    f = [bm.verts.new((side * x, BULK_Y, z)) for x, z in outline]
    yb = BULK_Y + depth
    back = [(AISLE, FLOOR)] + [(max(AISLE + 0.01, math.sqrt(max(0.0, C.r_in(z) ** 2 - yb ** 2)) - 0.015), z) for z in zs] + [(AISLE, BULK_TOP)]
    b = [bm.verts.new((side * x, yb, z)) for x, z in back]
    faces = [bm.faces.new(f), bm.faces.new(b[::-1])]
    n = len(outline)
    for i in range(n):
        faces.append(bm.faces.new((f[i], b[i], b[(i + 1) % n], f[(i + 1) % n])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for face in bm.faces:
        nx, ny = abs(face.normal.x), abs(face.normal.y)
        for l in face.loops:
            co = l.vert.co
            l[uv].uv = ((co.x if ny >= nx else co.y) * 1.0, co.z * 1.0)
    L.mesh_obj(name, bm, [M["blanket"]])
    # trim: a frame strip along the aisle edge and the top
    L.tube(name + "Trim", [Vector((side * AISLE, BULK_Y - 0.01, FLOOR)), Vector((side * AISLE, BULK_Y - 0.01, BULK_TOP)),
                           Vector((side * bulk_x(BULK_TOP), BULK_Y - 0.01, BULK_TOP))], 0.012, M["couchframe"])


def build_bulkhead():
    slab("BulkheadL", -1)
    slab("BulkheadR", 1)
    # left: a wall of stowage lockers, every one labelled and latched
    k = 0
    for row, z in enumerate((0.25, 0.53, 0.81, 1.09, 1.37, 1.65)):
        for col, x in enumerate((-0.52, -0.84, -1.16, -1.48)):
            if abs(x) + 0.155 > bulk_x(z + 0.13) - 0.01:
                continue
            G.box_unit(f"MidLocker{k}", (x, BULK_Y - 0.035, z), (0.29, 0.07, 0.26), vents=(row == 0), lamps_n=2 if (row + col) % 3 == 0 else 0)
            p, b = bulk_frame(x, z + 0.1)
            L.box(f"MidLockerTag{k}", (0.07, 0.022, 0.002), M["btn_soft"], p + b.col[2] * 0.0745 + b.col[0] * 0.06, b)
            k += 1
    # right: avionics bay above a fold-down workstation; tanks and drawers below
    zc, h = 1.55, 0.5
    w = bulk_x(zc + h / 2) - 0.03 - AISLE - 0.02
    xc = AISLE + 0.02 + w / 2
    av = C.Surface("AvionicsBay", (xc, BULK_Y - 0.03, zc), (1, 0, 0), (0, 0, 1), w, h, corner=0.02)
    av.build(M["console"], thick=0.03)
    G.grid(av, "Avionics", 4, 2, [
        ("breakers", 0, 0, 2, 1, {"cols": 10, "rows": 2}), ("mfd", 2, 0, 1, 2, {"screen": "mfd_systems"}), ("annunciators", 3, 0, 1, 1, {"cols": 2, "rows": 3, "start": 6}),
        ("dial", 0, 1, 1, 1, {"kind": "press"}), ("toggles", 1, 1, 1, 1, {"cols": 4}), ("knobs", 3, 1, 1, 1, {"n": 2})], border=0.012)
    av.check()
    G.housing(av, "AvionicsBay", depth=0.03)
    desk_z = 0.98
    p, b = bulk_frame(0.72, desk_z)
    L.box("WorkDesk", (0.56, 0.24, 0.022), M["module"], Vector((0.72, BULK_Y - 0.12, desk_z)), bevel=0.004)
    for sx in (-1, 1):
        L.tube(f"WorkDeskStay{sx}", [Vector((0.72 + sx * 0.25, BULK_Y - 0.005, desk_z - 0.18)), Vector((0.72 + sx * 0.25, BULK_Y - 0.22, desk_z - 0.012))], 0.006, M["handle"])
    P.laptop("WorkLaptop", *bulk_frame(0.66, desk_z + 0.2), arm=0.16, screen="mfd_map")
    P.binders("WorkBinders", *bulk_frame(0.98, desk_z + 0.12), n=4)
    for k2, x in enumerate((0.5, 0.74)):   # water and oxygen
        c = Vector((x, BULK_Y - 0.12, FLOOR + 0.38))
        L.cylinder(f"AftTank{k2}", 0.1, 0.62, M["tank"], c, segs=28, bevel=0.03)
        for dz in (-0.2, 0.2):
            L.torus(f"AftTankStrap{k2}{dz}", 0.103, 0.007, M["handle"], c + Vector((0, 0, dz)), Matrix.Identity(3), seg=28, mseg=6)
        L.cylinder(f"AftTankValve{k2}", 0.018, 0.06, M["rib"], c + Vector((0, 0, 0.34)), segs=12)
    G.cables("AftTankLines", (0.5, BULK_Y - 0.12, FLOOR + 0.72), (0.74, BULK_Y - 0.12, FLOOR + 0.72), droop=0.04, n=2)
    P.drawer_stack("AftDrawers", *bulk_frame(1.12, 0.42), 0.3, 0.6, 5)
    # safety kit on the aisle side of each half
    L.cylinder("Extinguisher", 0.05, 0.34, M["extinguisher"], Vector((0.44, BULK_Y - 0.06, 1.12)), segs=24, bevel=0.01)
    L.cylinder("ExtinguisherHead", 0.022, 0.05, M["rib"], Vector((0.44, BULK_Y - 0.06, 1.31)), segs=12)
    p, b = bulk_frame(1.06, 1.12)
    L.box("FirstAid", (0.16, 0.12, 0.08), M["btn_soft"], p + b.col[2] * 0.04, b, bevel=0.008)
    L.box("FirstAidCrossH", (0.06, 0.018, 0.004), M["red"], p + b.col[2] * 0.081, b)
    L.box("FirstAidCrossV", (0.018, 0.06, 0.004), M["red"], p + b.col[2] * 0.081, b)
    # umbilical ports, low on each half
    for i, x in enumerate(sorted(set(UMB_X))):
        p, b = bulk_frame(x, FLOOR + 0.3)
        L.box(f"UmbilicalPanel{i}", (0.12, 0.1, 0.02), M["module"], p + b.col[2] * 0.01, b, bevel=0.004)
    # aisle walls back to the hull, with handholds; the ladder rises against the back wall
    import bmesh
    for side in (-1, 1):
        y1 = math.sqrt(C.r_in(FLOOR) ** 2 - AISLE ** 2)
        bm = bmesh.new()
        uv = bm.loops.layers.uv.new("UVMap")
        pts = [(BULK_Y, FLOOR), (y1, FLOOR)] + [(math.sqrt(max(0.0, C.r_in(z) ** 2 - AISLE ** 2)) - 0.01, z) for z in (0.6, 1.2, BULK_TOP)] + [(BULK_Y, BULK_TOP)]
        vs = [bm.verts.new((side * AISLE, y, z)) for y, z in pts]
        face = bm.faces.new(vs if side < 0 else vs[::-1])
        for l in face.loops:
            l[uv].uv = (l.vert.co.y, l.vert.co.z)
        L.mesh_obj(f"AisleWall{side}", bm, [M["blanket"]])
        for z in (0.7, 1.3):
            L.tube(f"AisleHandhold{side}{z}", [Vector((side * AISLE, 1.05, z)), Vector((side * (AISLE - 0.05), 1.05, z)),
                                                Vector((side * (AISLE - 0.05), 1.3, z)), Vector((side * AISLE, 1.3, z))], 0.009, M["yellow"])
    G.wall("AisleBack", [("annunciators", 180, 1.6, 0.18, 0.07, {"cols": 4, "rows": 2, "start": 12})])


# ------------------------------------------------------------------ side consoles under the two-pane windows
def build_side_consoles():
    for side in (1, -1):
        p0, p1 = (C.rad(SIDE_PHI0), C.rad(SIDE_PHI1)) if side > 0 else (-C.rad(SIDE_PHI1), -C.rad(SIDE_PHI0))
        nm = "SideConsoleR" if side > 0 else "SideConsoleL"
        band = C.Band(nm, p0, p1, SIDE_Z0, SIDE_Z1, 0.08)
        band.build(M["console"])
        mid = math.degrees((p0 + p1) / 2)
        G.band_grid(band, nm, mid, (SIDE_Z0 + SIDE_Z1) / 2, 10, 3, 0.11, 0.12, [
            ("breakers", 0, 0, 6, 1, {"cols": 18, "rows": 2}), ("annunciators", 6, 0, 4, 1, {"cols": 8, "rows": 2, "start": 8 if side > 0 else 0}),
            ("dial", 0, 1, 1, 1, {"kind": "press"}), ("dial", 1, 1, 1, 1, {"kind": "temp"}), ("mfd", 2, 1, 2, 2, {"screen": "mfd_comms" if side > 0 else "mfd_engine"}),
            ("toggles", 4, 1, 3, 1, {"cols": 9}), ("knobs", 7, 1, 3, 1, {"n": 6}),
            ("screen", 0, 2, 2, 1, {"mat": "crt_data"}), ("toggles", 4, 2, 3, 1, {"cols": 9}), ("vent", 7, 2, 3, 1, {"slots": 5}),
        ])
        band.check()


# ------------------------------------------------------------------ decks: platforms, openings, ladders, ceiling lights
def platform(name, z, holes, ceiling=False):
    """Grated deck at height z filling the hull, with rectangular openings (x0, x1, y0, y1); rim, radial beams and
    downlights on its underside (the ceiling of the deck below)."""
    import bmesh
    rr = C.r_in(z) - 0.01
    tiles = bmesh.new()
    uv = tiles.loops.layers.uv.new("UVMap")
    step = 0.1
    k = int(rr / step) + 1
    for i in range(-k, k):
        for j in range(-k, k):
            x0, y0 = i * step, j * step
            cx, cy = x0 + step / 2, y0 + step / 2
            if math.hypot(cx, cy) > rr - 0.03 or any(h[0] < cx < h[1] and h[2] < cy < h[3] for h in holes):
                continue
            vs = [tiles.verts.new((x, y, z)) for x, y in ((x0, y0), (x0 + step, y0), (x0 + step, y0 + step), (x0, y0 + step))]
            face = tiles.faces.new(vs)
            for l in face.loops:
                l[uv].uv = (l.vert.co.x * 1.0, l.vert.co.y * 1.0)
    bmesh.ops.remove_doubles(tiles, verts=tiles.verts, dist=1e-5)
    L.solidify(L.mesh_obj(name, tiles, [M.get("deckplate", M["floor"])]), 0.03)
    L.tube(name + "Rim", [C.polar(2 * math.pi * j / 96, rr - 0.015, z - 0.015) for j in range(97)], 0.02, M["couchframe"])
    for k2 in range(0 if ceiling else 8):
        phi = 2 * math.pi * (k2 + 0.5) / 8
        L.tube(f"{name}Beam{k2}", [C.polar(phi, 0.25, z - 0.05), C.polar(phi, rr - 0.02, z - 0.05)], 0.022, M["couchframe"])
        p = C.polar(phi + math.pi / 8, rr * 0.55, z - 0.045)
        L.cylinder(f"{name}Downlight{k2}", 0.04, 0.025, M["ring"], p, segs=20)
        L.disc(f"{name}DownlightLens{k2}", 0.03, M["light"], p - Vector((0, 0, 0.013)), Matrix.Rotation(math.pi, 3, "X"), segs=20)
    for h in holes:   # hazard-striped railing round each opening (open on the ladder side)
        x0, x1, y0, y1 = h
        P.hazard_rail(f"{name}Rail{h[0]:.2f}", [Vector((x0, y1 - 0.1, z)), Vector((x0, y1 - 0.1, z + 0.45)), Vector((x0, y0, z + 0.45)),
                                                 Vector((x1, y0, z + 0.45)), Vector((x1, y1 - 0.1, z + 0.45)), Vector((x1, y1 - 0.1, z))], 0.009)


def build_decks():
    platform("DeckB", DECK_Z, [(-HOLE_HW, HOLE_HW, HOLE_Y0, HOLE_Y1)], ceiling=True)
    ladder("LadderAft", 0.0, 1.3, FLOOR, DECK_Z + 0.55, 0.22)
    ladder("LadderTunnel", 0.0, 0.3, DECK_Z, C.Z_TOP - 0.08, 0.18)


# ------------------------------------------------------------------ deck B: kitchen, dining, sleep stations, hygiene, exercise
def build_hab_deck():
    D = DECK_Z
    # kitchen along the front wall: counter cabinets with a worktop, oven, galley, utensils, food lockers above
    for k, deg in enumerate((-36, -24, -12, 0, 12, 24, 36)):
        p, b = at(deg, D + 0.2, 0.0)
        P.cabinet(f"Counter{k}", p, b, 0.28, 0.38, 0.32, doors=1 if k % 2 else 2, top=M["module"])
    P.oven("Oven", *at(-18, D + 0.52, 0.08))
    P.galley("Galley", *at(10, D + 0.62, 0.0), w=0.3, h=0.42)
    P.utensil_rack("Utensils", *at(-30, D + 0.68, 0.0))
    for k, deg in enumerate((28, 38)):
        P.cabinet(f"FoodLocker{k}", *at(deg, D + 0.72, 0.0), 0.24, 0.16, 0.18, doors=1)
    P.table("DiningTable", (0.0, -0.45), r=0.26, h=0.42, floor_z=D)
    # crew quarters on the left
    for k, deg in enumerate((-100, -128)):
        P.sleep_station(f"SleepStation{k}", *at(deg, D + 0.43, 0.0), 0.5, 0.78, 0.3)
    P.drawer_stack("PersonalLockers", *at(-70, D + 0.25, 0.0), 0.3, 0.4, 4)
    P.net_with_gear("QuartersNet", *at(-70, D + 0.66, 0.0), 0.34, 0.26)
    # hygiene on the right, exercise bike on the deck
    P.toilet("Toilet", *at(100, D + 0.2, 0.0))
    P.hygiene_booth("ToiletBooth", *at(100, D + 0.55, 0.0), w=0.62, h=1.0, d=0.6)
    P.sink("Sink", *at(126, D + 0.5, 0.0))
    P.towels("Towels", *at(70, D + 0.55))
    P.bike("Bike", (0.62, 0.6), yaw=math.radians(-35), floor_z=D)
    # back wall either side of the ladder: tanks, tool board, cargo
    P.tool_board("ToolBoard", *at(140, D + 0.52), 0.32, 0.3)
    P.cargo_bag("BackBag", *at(-142, D + 1.0, 0.0), 0.28, 0.2, 0.12)
    for side in (-1, 1):
        p, b = at(158 if side > 0 else -158, D + 0.4, 0.13)
        L.cylinder(f"HabTank{side}", 0.1, 0.56, M["tank"], p, L.basis(b.col[0], b.col[2], -b.col[1]), segs=28, bevel=0.025)
        for dz in (-0.18, 0.18):
            L.torus(f"HabTankStrap{side}{dz}", 0.104, 0.006, M["handle"], p + b.col[1] * dz, L.basis(b.col[0], b.col[2], -b.col[1]), seg=28, mseg=6)
    for side in (-1, 1):
        P.fan(f"HabFan{side}", *at(side * 52, D + 0.72))
    G.wall("HabPanels", [("lamps", 52, D + 0.5, 0.12, 0.05, {"n": 3}), ("knobs", -52, D + 0.5, 0.14, 0.06, {"n": 3})])


# ------------------------------------------------------------------ upper tier of the living deck: lab and docking station
def build_lab_deck():
    D = DECK_Z
    # docking station: a wall console between the two docking windows, with a camera and binoculars
    p, b = at(0, D + 1.08, 0.04)
    s = C.Surface("DockStation", p, b.col[0], b.col[1], 0.26, 0.28, corner=0.02)
    s.build(M["console"], thick=0.03)
    G.grid(s, "Dock", 2, 2, [("navball", 0, 0, 1, 1, {}), ("mfd", 1, 0, 1, 1, {"screen": "mfd_map"}),
                             ("toggles", 0, 1, 1, 1, {"cols": 3}), ("annunciators", 1, 1, 1, 1, {"cols": 2, "rows": 2, "start": 8})], border=0.008)
    s.check()
    G.housing(s, "DockStation", depth=0.04)
    w = next(w for w in C.WINDOWS if w["name"] == "DockingR")
    p, b = at(math.degrees(w["phi"]) + 14, w["z"] + 0.02, 0.02)
    P.camera("DockCamera", p, b, lens_dir=(C.polar(w["phi"], C.r_in(w["z"]) + 0.2, w["z"]) - p))
    P.binoculars("Binoculars", *at(-math.degrees(w["phi"]) - 15, D + 1.3))
    P.headset("Headset", *at(-9, D + 1.32))
    # lab tier: glovebox, microscope shelf with a laptop, freezer, goo rack, sample drawers, whiteboard, racks
    P.glovebox("Glovebox", *at(62, D + 1.12, 0.0), 0.42, 0.3, 0.26)
    S.mount("GloveboxMount", *at(62, D + 1.12, 0.0), 0.42, 0.3)
    P.cabinet("MicroscopeBench", *at(-62, D + 0.98, 0.0), 0.36, 0.26, 0.26, doors=2, top=M["module"])
    S.mount("MicroscopeBenchMount", *at(-62, D + 0.98, 0.0), 0.36, 0.26)
    P.microscope("Microscope", *at(-58, D + 1.18, 0.06))
    P.laptop("LabLaptop", *at(-84, D + 1.25), arm=0.2, screen="mfd_systems")
    P.freezer("SampleFreezer", *at(96, D + 1.08, 0.0), 0.3, 0.3, 0.24)
    S.mount("SampleFreezerMount", *at(96, D + 1.08, 0.0), 0.3, 0.3)
    P.science_rack("GooRack", *at(-106, D + 1.15), 0.28, 0.44)
    P.drawer_stack("SampleDrawers", *at(128, D + 1.05, 0.0), 0.26, 0.32, 4)
    S.mount("SampleDrawersMount", *at(128, D + 1.05, 0.0), 0.26, 0.32)
    P.whiteboard("LabBoard", *at(-150, D + 1.25), 0.28, 0.22)
    G.wall("LabRacks", [("mfd", 158, D + 1.22, 0.2, 0.2, {"screen": "mfd_engine"}), ("breakers", -168, D + 1.25, 0.2, 0.1, {"cols": 7, "rows": 2}),
                        ("annunciators", 158, D + 0.98, 0.2, 0.08, {"cols": 6, "rows": 2, "start": 4})], inset=0.04)
    P.sample_table("SampleTable", (-0.62, 0.45), D)
    for side in (-1, 1):
        P.fan(f"LabFan{side}", *at(side * 118, D + 1.45))


def ladder(name, x, y, z0, z1, w):
    for side in (-1, 1):
        L.tube(f"{name}Rail{side}", [Vector((x + side * w / 2, y, z0)), Vector((x + side * w / 2, y, z1))], 0.01, M["rib"])
    n = int((z1 - z0) / 0.25)
    for k in range(1, n + 1):
        z = z0 + k * (z1 - z0) / (n + 1)
        L.tube(f"{name}Rung{k}", [Vector((x - w / 2, y, z)), Vector((x + w / 2, y, z))], 0.008, M["yellow"])


# ------------------------------------------------------------------ mission kit: what a crew of five lives and works with
def at(deg, z, inset=0.0):
    return C.frame_at(C.rad(deg), z, inset)


def flat(x, y, z):
    """Frame lying on a floor at (x, y, z): normal up, 'up' towards the cabin front."""
    return Vector((x, y, z)), L.basis(Vector((1, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1)))


def build_lower_kit():
    # stowage under the couches (at the head end, in front of the couch struts)
    for i, seat in enumerate(SEATS):
        P.cargo_bag(f"UnderCouchBag{i}", *flat(seat["x"], -0.48, FLOOR + 0.005), 0.34, 0.2, 0.2)
    # EVA jetpacks racked either side of the hatch
    for side in (-1, 1):
        P.jetpack(f"Jetpack{side}", *at(side * 32, 1.15))
    # camera bracketed at each upper side window, checklist binders on the back wall, handrails
    for side, wn in ((1, "SideHighR"), (-1, "SideHighL")):
        w = next(w for w in C.WINDOWS if w["name"] == wn)
        p, b = at(-math.degrees(w["phi"]) * -1 + side * 9, w["z"] + 0.12, 0.02)
        P.camera(f"WindowCamera{side}", p, b, lens_dir=(C.polar(w["phi"], C.r_in(w["z"]) + 0.2, w["z"]) - p))
    # the zero-g indicator, hanging from the console hood where the commander can see it
    P.plush("ZeroGIndicator", Vector((0.22, MDC_Y + MDC_H / 2 + 0.02, MDC_Z - 0.06)), length=0.12)


# ------------------------------------------------------------------ walls: lockers, stowage, safety kit, conduits
def build_walls():
    for side in (-1, 1):
        G.wall(f"WallFront{side}", [("breakers", side * 40, 1.7, 0.24, 0.12, {"cols": 8, "rows": 2}), ("lamps", side * 40, 1.86, 0.16, 0.05, {"n": 3})])
        for k2, z in enumerate((0.5, 0.72)):
            p, b = C.frame_at(C.rad(side * 40), z, 0.01)
            L.box(f"Bag{side}{k2}", (0.26, 0.17, 0.1), M["canvas"], p + b.col[2] * 0.05, b, bevel=0.035, segs=4)
            for sx in (-0.3, 0.3):
                L.box(f"Bag{side}{k2}Strap{sx}", (0.018, 0.18, 0.108), M["strap"], p + b.col[2] * 0.05 + b.col[0] * (0.26 * sx), b, bevel=0.003)
    for k2, (deg, z) in enumerate(((-12, 0.55), (12, 0.55))):
        p, b = C.frame_at(C.rad(deg), z, 0.13)
        rot = L.basis(b.col[1], b.col[2], b.col[0])
        L.cylinder(f"FrontTank_{k2}", 0.09, 0.34, M["tank"], p, rot, segs=28, bevel=0.012)


# ------------------------------------------------------------------ stock-style structure and dressing (built last, fits round everything)
def dome_z(r):
    """Height of the ceiling dome at radius r (inverse of capsule.build_shell's dome)."""
    R = C.r_in(C.Z_CEIL)
    c = max(-1.0, min(1.0, r / R))
    t = math.acos(c) / (math.pi / 2 * 0.92)
    return C.Z_CEIL + (C.Z_TOP - C.Z_CEIL) * math.sin(min(1.0, t) * math.pi / 2)


def build_ceiling_below_deck(clear):
    """Flight-deck ceiling: solid panelled underside of the deck, box beams, ring beam, light fixtures, cable bundles."""
    import bmesh
    D = DECK_Z
    zc = D - 0.035
    rr = C.r_in(zc) - 0.012
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    step = 0.1
    k = int(rr / step) + 1
    for i in range(-k, k):
        for j in range(-k, k):
            x0, y0 = i * step, j * step
            cx, cy = x0 + step / 2, y0 + step / 2
            if math.hypot(cx, cy) > rr - 0.03 or (-HOLE_HW < cx < HOLE_HW and HOLE_Y0 < cy < HOLE_Y1):
                continue
            vs = [bm.verts.new((x, y, zc)) for x, y in ((x0, y0), (x0, y0 + step), (x0 + step, y0 + step), (x0 + step, y0))]
            f = bm.faces.new(vs)
            for l in f.loops:
                l[uv].uv = (l.vert.co.x, l.vert.co.y)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    L.mesh_obj("DeckCeiling", bm, [M["blanket"]])
    S.beam("DeckCeilingHoleTrim", Vector((-HOLE_HW, HOLE_Y0, zc - 0.03)), Vector((HOLE_HW, HOLE_Y0, zc - 0.03)), 0.05, 0.06, M["frame_dark"])
    bz = zc - 0.045
    for k2 in range(8):
        phi = 2 * math.pi * (k2 + 0.5) / 8
        S.beam(f"CeilBeam{k2}", C.polar(phi, 0.3, bz), C.polar(phi, rr - 0.02, bz), 0.07, 0.09, M["frame"])
        for t in (0.45, 0.8):
            q = C.polar(phi, 0.3 + (rr - 0.32) * t, bz - 0.0)
            S.cbox(f"CeilBeamClamp{k2}_{t}", (0.1, 0.1, 0.06), M["frame_dark"], q, Matrix.Rotation(-phi, 3, "Z"), ch=0.01)
    ring = [C.polar(2 * math.pi * j / 72, 0.62, bz) for j in range(72)]
    S.sweep("CeilRingBeam", ring, [(0, 0, 1)] * 72, S.chamfer_rect(0.07, 0.08), M["frame"], closed=True)
    S.sweep("CeilHub", [C.polar(2 * math.pi * j / 48, 0.3, bz) for j in range(48)], [(0, 0, 1)] * 48, S.chamfer_rect(0.08, 0.1), M["frame_dark"], closed=True)
    down = Vector((0, 0, -1))
    n = 0
    for k2 in range(8):
        phi = 2 * math.pi * k2 / 8
        for r in (0.46, 1.12):
            p = C.polar(phi, r, zc)
            if -HOLE_HW - 0.2 < p.x < HOLE_HW + 0.2 and HOLE_Y0 - 0.15 < p.y < HOLE_Y1 + 0.15:
                continue
            tang = Vector((math.cos(phi), math.sin(phi), 0))
            S.light_fixture(f"CeilLight{n}", p, L.basis(tang, tang.cross(down), down), w=0.28 if r > 1 else 0.2, h=0.08)
            n += 1
    # duct round the outer ceiling edge, broken where windows, hatch and equipment are
    for side in (-1, 1):
        phis = [side * math.radians(a) for a in range(30, 150, 3)]
        zd = zc - 0.16

        def ok(phi):
            return not clear.blocked(C.polar(phi, C.r_in(zd) - 0.07, zd), 0.05)

        for r_, seg in enumerate(S.runs(phis, ok, 6)):
            G.hose(f"Duct{side}_{r_}", [C.polar(p, C.r_in(zd) - 0.075, zd) for p in seg], r=0.045, mat=M["frame"], rib_mat=M["frame_dark"])
    # cable bundles from the top of each console section up into the ceiling
    for k2, x in enumerate((-1.24, -0.62, 0.0, 0.62, 1.24)):
        z0 = MDC_Z - abs(x) * 0.07 + 0.115
        sx = 0.14 if x >= 0 else -0.14
        pts = [Vector((x + sx, MDC_Y + 0.08, z0)), Vector((x + sx * 1.1, MDC_Y + 0.12, z0 + 0.12)),
               Vector((x * 0.95 + sx * 1.3, MDC_Y + 0.4, bz - 0.12)), Vector((x * 0.9 + sx * 1.4, MDC_Y + 0.62, bz - 0.06))]
        S.bundle(f"MDC{k2}", pts, n=3 + (k2 % 2), colours=[S.CABLES[(k2 + i) % 4] for i in range(4)])
    # risers from the side consoles up the wall into the ceiling
    for side in (-1, 1):
        for k2, deg in enumerate((86, 108)):
            phi = C.rad(side * deg)
            S.bundle(f"Riser{side}{k2}", S.wall_path(phi, SIDE_Z1 + 0.1, bz - 0.12, inset=0.04, n=5), n=3, colours=["cable_k", "cable_r" if k2 else "cable_g", "cable_y"], ends=(False, False))
            S.junction(f"RiserBoxLo{side}{k2}", phi, SIDE_Z1 + 0.08)
            S.junction(f"RiserBoxHi{side}{k2}", phi, bz - 0.12)


def build_dome(clear):
    """Living-deck ceiling: docking hatch with handwheel and latches in a segmented ring, equipment cassettes round the
    upper wall, cable drops to the lab tier."""
    zh = dome_z(0.32) - 0.025
    S.sweep("TunnelRing", [Vector((0.33 * math.cos(a), 0.33 * math.sin(a), zh)) for a in [2 * math.pi * j / 64 for j in range(64)]],
            [(0, 0, 1)] * 64, S.chamfer_rect(0.07, 0.06), M["frame_dark"], closed=True)
    L.cylinder("TunnelHatch", 0.29, 0.03, M["frame"], (0, 0, zh + 0.005), segs=48, bevel=0.006)
    L.torus("TunnelHandwheel", 0.11, 0.012, M["frame_dark"], (0, 0, zh - 0.05), Matrix.Identity(3), seg=32, mseg=8)
    for k2 in range(4):
        a = k2 * math.pi / 2
        L.tube(f"TunnelSpoke{k2}", [Vector((0, 0, zh - 0.012)), Vector((0.11 * math.cos(a), 0.11 * math.sin(a), zh - 0.05))], 0.008, M["frame_dark"])
        S.cbox(f"TunnelLatch{k2}", (0.06, 0.03, 0.025), M["yellow"], Vector((0.27 * math.cos(a + 0.4), 0.27 * math.sin(a + 0.4), zh - 0.02)),
               Matrix.Rotation(a + 0.4, 3, "Z"), ch=0.004)
    for k2 in range(16):
        a = 2 * math.pi * (k2 + 0.5) / 16
        r = 0.5
        S.cbox(f"TunnelSegment{k2}", (0.2, 0.13, 0.025), M["frame"] if k2 % 2 else M["frame_dark"],
               Vector((r * math.cos(a), r * math.sin(a), dome_z(r) - 0.015)), Matrix.Rotation(a + math.pi / 2, 3, "Z"), ch=0.006)
    n = 0
    for deg in range(-165, 180, 30):
        phi = C.rad(deg)
        p, b = at(deg, C.Z_CEIL - 0.2, 0.0)
        size = (0.24, 0.12, 0.16)
        rot = L.basis(b.col[0], -b.col[2], b.col[1])
        c = p + b.col[2] * (size[1] / 2 + 0.005)
        corners = [c + b.col[0] * sx * size[0] / 2 + b.col[1] * sz * size[2] / 2 for sx in (-1, 1) for sz in (-1, 1)]
        if S.in_window(phi, C.Z_CEIL - 0.2, 0.08) or any(clear.blocked(q, 0.01) for q in corners + [c]):
            continue
        G.box_unit(f"Cassette{n}", c, size, rot, vents=n % 2 == 0, lamps_n=2)
        n += 1
    D = DECK_Z
    drops = [(70, 64, D + 1.29), (104, 98, D + 1.25), (166, 160, D + 1.34), (-12, -3, D + 1.24), (-114, -108, D + 1.39), (-70, -63, D + 1.14)]
    for k2, (a0, a1, z1) in enumerate(drops):   # each drop plugs into a junction box above its unit
        zj = z1 + 0.1
        S.bundle(f"Drop{k2}", S.wall_path(C.rad(a0), C.Z_CEIL - 0.08, zj, inset=0.04, n=5, phi1=C.rad(a1)), n=3,
                 colours=[S.CABLES[(k2 + i) % 4] for i in range(3)], ends=(True, False))
        S.junction(f"DropBox{k2}", C.rad(a1), zj)


def build_floors():
    """Floor dressing: kept to the flight-deck aisle (loose-looking hatches and foot bars on the grating read as clutter)."""
    S.foot_restraint("FootAisle", (-0.18, 0.5), (0.18, 0.5), FLOOR)


def hidden(p):
    """Behind the aft bulkhead (out of sight): build no structure there."""
    return p.y > BULK_Y + 0.02 and abs(p.x) > AISLE + 0.02 and p.z < BULK_TOP + 0.02


def build_structure():
    clear = S.Clearance(zones=[hidden])
    build_ceiling_below_deck(clear)
    build_floors()
    clear = S.Clearance(zones=[hidden])
    build_dome(clear)
    clear = S.Clearance(zones=[hidden])
    D = DECK_Z
    bays = [2 * math.pi * k2 / 16 for k2 in range(16)]
    S.wall_racks("Hab", clear, bays, D + 0.5, 0.36, 0.62, seed=5)
    S.wall_racks("Flight", clear, bays, 1.5, 0.34, 0.44, seed=6, chance=0.7)
    S.wall_racks("HabUpper", clear, [2 * math.pi * (k2 + 0.5) / 32 for k2 in range(32)], D + 1.28, 0.24, 0.28, seed=8, chance=0.9)
    clear = S.Clearance(zones=[hidden])
    S.cable_run("RunHabTop", C.Z_CEIL - 0.17, clear, seed=3)
    S.cable_run("RunHabMid", D + 0.95, clear, seed=4, n=3)
    S.cable_run("RunFlightTop", D - 0.2, clear, seed=5)
    clear = S.Clearance(zones=[hidden])
    S.ring_frame("Skirt", FLOOR + 0.05, clear, h=0.07, d=0.04)
    S.ring_frame("Cornice", D - 0.07, clear, h=0.09, d=0.05)
    S.ring_frame("HabSkirt", D + 0.05, clear, h=0.07, d=0.04)
    S.ring_frame("HabCornice", C.Z_CEIL - 0.05, clear, h=0.08, d=0.05)
    clear = S.Clearance(zones=[hidden])
    S.wall_ribs("Flight", 16, FLOOR + 0.1, D - 0.12, clear, min_len=0.55)
    S.wall_ribs("Hab", 16, D + 0.1, C.Z_CEIL - 0.1, clear, min_len=0.55)
    clear = S.Clearance(zones=[hidden])
    S.wall_plates("Flight", clear, bays, (0.35, 0.7, 1.3, 1.72), chance=0.55, seed=11)
    S.wall_plates("Hab", clear, bays, (D + 0.32, D + 0.8, D + 1.35), chance=0.5, seed=12)


# ------------------------------------------------------------------ build
C.build_shell(dome=True, ring_light=True)
bpy_floor = L.COLL.objects.get("Floor")
if bpy_floor is not None:   # solid deck plates on the flight-deck floor too
    bpy_floor.data.materials[0] = M["deckplate"]
for w in C.WINDOWS:
    C.build_window(w, depth=0.05, bolts=32)
    C.view_markers(w, standoff=0.35)
build_mdc()
build_lower_deck()
build_side_consoles()
C.build_hatch(HATCH_PHI, HATCH_HALF, H["z0"], H["z1"])
build_bulkhead()
build_decks()
build_walls()
build_hab_deck()
build_lab_deck()
build_lower_kit()
build_structure()
for i, seat in enumerate(SEATS):
    C.eye_marker(i, seat)
S.collision_markers(decks=[DECK_Z], holes=[(-HOLE_HW, HOLE_HW, HOLE_Y0, HOLE_Y1, DECK_Z)],
                    hatches=[("Tunnel", (0.0, 0.0, dome_z(0.32) - 0.25))])
ref = os.path.join(os.environ.get("IVA_REFERENCE", "C:/Games/KSP2Mods/reference"), "poses", POSE["ref_from"] + ".obj")
C.reference_kerbal_copies(ref, POSE["ref_base_y"], [(s["x"], POSE["ref_offset"][1], POSE["ref_offset"][2]) for s in SEATS])
print(f"eyes at z {EYE_Z:.3f}; console {MDC_Z - EYE_Z:.3f} m above; upper deck at {DECK_Z:.2f}; bulkhead at y {BULK_Y:.2f}")
L.save(OUT)
