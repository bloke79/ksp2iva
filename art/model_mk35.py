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
G.materials()

M = L.M
M["blanket"] = L.material("IVA_Blanket", tex="blanket_color.png", normal="blanket_normal.png", rough=0.5, metal=0.35, uv_scale=(2.2, 2.2))
M["shell"] = L.material("IVA_SeatShell", (0.86, 0.86, 0.84), rough=0.3, metal=0.05)
M["bottle"] = L.material("IVA_Bottle", (0.22, 0.42, 0.30), rough=0.35, metal=0.4)
M["tank"] = L.material("IVA_Tank", (0.78, 0.79, 0.80), rough=0.3, metal=0.7)
M["periscope"] = L.material("IVA_Periscope", tex="periscope.png", rough=0.1, emit=1.6, emit_tex=True)
M["canvas"] = L.material("IVA_Canvas", (0.55, 0.52, 0.42), rough=0.92)
M["umbilical"] = L.material("IVA_Umbilical", (0.32, 0.36, 0.42), rough=0.7)
M["net"] = L.material("IVA_Net", (0.30, 0.32, 0.20), rough=0.9)
P.materials()

C.setup(SPEC, wall=SPEC["wall"], ceil=SPEC["ceiling"], top=SPEC["ceiling"] + 0.1, seg=192)
POSE = SPEC["pose"]
SEATS = POSE["seats"]
H = SPEC["hatch"]
HATCH_PHI, HATCH_HALF = C.rad(-H["angle"]), C.rad(H["half_deg"])
EYE_Z = SEATS[0]["eye"][2]
FLOOR = C.Z_FLOOR
DECK_Z = 2.15                     # upper deck platform
HOLE_Y0, HOLE_Y1, HOLE_HW = 0.45, 1.0, 0.32   # ladder opening in the deck, behind the couches
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
        L.tube(f"MDC_Seam{x}", [Vector((x, MDC_Y - MDC_H / 2 - 0.01, z)), Vector((x, MDC_Y + MDC_H / 2 + 0.01, z))], 0.018, M["couchframe"])
        for k, y in enumerate((MDC_Y - 0.17, MDC_Y + 0.17)):
            C.bracket(f"MDC_Hanger{x}_{k}", Vector((x, y, z + 0.03)), Vector((x, y, DECK_Z - 0.06)), r=0.012)
    hy = MDC_Y + MDC_H / 2 + 0.02
    L.box("MDC_Hood", (3.0, 0.03, 0.06), M["couchframe"], (0, hy, MDC_Z - 0.03), bevel=0.01)
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
        L.tube(f"CouchFrameBeam_{k}", [Vector((xs[0] - 0.14, y, z)), Vector((xs[-1] + 0.14, y, z))], 0.018, M["couchframe"])
        for x in (xs[0] - 0.14, -0.31, 0.31, xs[-1] + 0.14):
            L.tube(f"CouchFrameLeg_{k}_{x:.2f}", [Vector((x, y, z)), Vector((x * 1.04, y, FLOOR + 0.005))], 0.018, M["couchframe"])
            L.cylinder(f"CouchFrameFoot_{k}_{x:.2f}", 0.032, 0.014, M["couchframe"], (x * 1.04, y, FLOOR + 0.007))
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
    # environmental unit and power boxes behind the feet; umbilicals to every suit
    G.box_unit("ECSUnit", (0, 0.72, FLOOR + 0.16), (0.6, 0.26, 0.32), lamps_n=3)
    for side in (-1, 1):
        G.box_unit(f"PowerBox{side}", (side * 0.75, 0.7, FLOOR + 0.13), (0.3, 0.22, 0.26), lamps_n=2)
        G.cables(f"PowerCables{side}", (side * 0.75, 0.7, FLOOR + 0.26), (side * 0.3, 0.72, FLOOR + 0.32), droop=0.03, n=3)
    for i, seat in enumerate(SEATS):
        x = seat["x"]
        dz = EYE_Z - 0.718
        start = Vector((max(-0.26, min(0.26, x * 0.2)), 0.6, FLOOR + 0.32))
        pts = [start, Vector((x - 0.25, 0.38, 0.38 + dz)), Vector((x - 0.25, 0.1, 0.5 + dz)), Vector((x - 0.2, -0.1, 0.58 + dz)), Vector((x - 0.13, -0.16, 0.6 + dz))]
        G.hose(f"Umbilical{i}", pts, r=0.018, mat=M["umbilical"])
        L.cylinder(f"UmbilicalPlug{i}", 0.026, 0.04, M["buckle"], pts[-1], (pts[-1] - pts[-2]).normalized().to_track_quat("Z", "Y").to_matrix(), segs=16)


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


# ------------------------------------------------------------------ upper deck: platform, ladder, equipment ring, docking station
def build_upper_deck():
    import bmesh
    rr = C.r_in(DECK_Z) - 0.01
    # platform: grid of tiles skipping the ladder opening (keeps it simple and solid-looking)
    tiles = bmesh.new()
    uv = tiles.loops.layers.uv.new("UVMap")
    step = 0.1
    k = int(rr / step) + 1
    for i in range(-k, k):
        for j in range(-k, k):
            x0, y0 = i * step, j * step
            cx, cy = x0 + step / 2, y0 + step / 2
            if math.hypot(cx, cy) > rr - 0.03 or (abs(cx) < HOLE_HW and HOLE_Y0 < cy < HOLE_Y1):
                continue
            vs = [tiles.verts.new((x, y, DECK_Z)) for x, y in ((x0, y0), (x0 + step, y0), (x0 + step, y0 + step), (x0, y0 + step))]
            face = tiles.faces.new(vs)
            for l in face.loops:
                l[uv].uv = (l.vert.co.x * 1.5, l.vert.co.y * 1.5)
    bmesh.ops.remove_doubles(tiles, verts=tiles.verts, dist=1e-5)
    L.solidify(L.mesh_obj("DeckPlatform", tiles, [M["floor"]]), 0.03)
    L.tube("DeckRim", [C.polar(2 * math.pi * j / 96, rr - 0.015, DECK_Z - 0.015) for j in range(97)], 0.02, M["couchframe"])
    for k2 in range(8):   # radial beams under the deck
        phi = 2 * math.pi * (k2 + 0.5) / 8
        L.tube(f"DeckBeam{k2}", [C.polar(phi, 0.2, DECK_Z - 0.05), C.polar(phi, rr - 0.02, DECK_Z - 0.05)], 0.022, M["couchframe"])
    # railing round the ladder opening, and the ladders (floor -> deck behind the couches, deck -> docking tunnel)
    for x in (-HOLE_HW, HOLE_HW):
        L.tube(f"HoleRail{x}", [Vector((x, HOLE_Y0, DECK_Z)), Vector((x, HOLE_Y0, DECK_Z + 0.5)), Vector((x, HOLE_Y1 - 0.25, DECK_Z + 0.5)), Vector((x, HOLE_Y1 - 0.25, DECK_Z))], 0.014, M["yellow"])
    ladder(f"LadderLower", 0.0, HOLE_Y1 - 0.12, FLOOR + 0.5, DECK_Z + 0.6, 0.22)
    ladder(f"LadderUpper", 0.0, 0.32, DECK_Z, C.Z_TOP - 0.08, 0.2)
    # docking station: a standing console under the docking windows, facing back into the cabin
    # facing back and up towards someone standing on the deck; screen-up runs towards the windows
    up = Vector((0, -0.55, 1)).normalized()
    s = C.Surface("DockStation", (0, -0.86, DECK_Z + 0.62), (-1, 0, 0), up, 0.7, 0.36, corner=0.03)
    s.build(M["console"], thick=0.03)
    G.grid(s, "Dock", 6, 3, [
        ("mfd", 0, 0, 2, 2, {"screen": "mfd_map"}), ("navball", 2, 0, 2, 2, {}), ("mfd", 4, 0, 2, 2, {"screen": "mfd_comms"}),
        ("toggles", 0, 2, 2, 1, {"cols": 6}), ("dial", 2, 2, 1, 1, {"kind": "alt"}), ("knobs", 3, 2, 1, 1, {"n": 2}), ("annunciators", 4, 2, 2, 1, {"cols": 4, "rows": 2, "start": 8}),
    ])
    s.check()
    G.prism("DockStationBase", [(-0.95, DECK_Z), (-0.7, DECK_Z), (-0.72, DECK_Z + 0.48), (-0.98, DECK_Z + 0.52)], -0.38, 0.38, M["console"])
    # drawers in the base's back face (towards the cabin)
    face = L.basis(Vector((-1, 0, 0)), Vector((0, 0.08, 1)).normalized(), Vector((0, 1, -0.08)).normalized())
    for k in range(3):
        q = Vector((0, -0.71 + 0.005, DECK_Z + 0.09 + k * 0.13))
        L.box(f"DockDrawer{k}", (0.66, 0.11, 0.02), M["locker"], q + face.col[2] * 0.01, face, bevel=0.004)
        L.box(f"DockDrawerHandle{k}", (0.12, 0.014, 0.016), M["handle"], q + face.col[2] * 0.025, face, bevel=0.004)
        L.box(f"DockDrawerTag{k}", (0.07, 0.03, 0.003), M["btn_soft"], q + face.col[2] * 0.021 + face.col[0] * 0.24, face)
    # grab handle along the console's top edge, on two posts (so it's fixed to something)
    a, ba = s.at(-0.28, s.h / 2 - 0.01)
    c, bc = s.at(0.28, s.h / 2 - 0.01)
    L.tube("DockGrabBar", [a, a + ba.col[2] * 0.06, c + bc.col[2] * 0.06, c], 0.01, M["yellow"])


def ladder(name, x, y, z0, z1, w):
    for side in (-1, 1):
        L.tube(f"{name}Rail{side}", [Vector((x + side * w / 2, y, z0)), Vector((x + side * w / 2, y, z1))], 0.014, M["rib"])
    n = int((z1 - z0) / 0.25)
    for k in range(1, n + 1):
        z = z0 + k * (z1 - z0) / (n + 1)
        L.tube(f"{name}Rung{k}", [Vector((x - w / 2, y, z)), Vector((x + w / 2, y, z))], 0.011, M["yellow"])


# ------------------------------------------------------------------ mission kit: what a crew of five lives and works with
def at(deg, z, inset=0.0):
    return C.frame_at(C.rad(deg), z, inset)


def flat(x, y, z):
    """Frame lying on a floor at (x, y, z): normal up, 'up' towards the cabin front."""
    return Vector((x, y, z)), L.basis(Vector((1, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1)))


def build_upper_kit():
    D = DECK_Z
    # living: sleeping bags either side of the docking station, galley at the back, hygiene kit
    for side in (-1, 1):
        P.sleeping_bag(f"SleepingBag{side}", *at(side * 50, D + 0.47))
    P.galley("Galley", *at(180, D + 0.45))
    P.towels("Hygiene", *at(-143, D + 0.5))
    P.bungee("Exerciser", *at(-33, D + 0.42))
    # work: science rack, laptop station with whiteboard and headset, tool board
    P.science_rack("ScienceRack", *at(78, D + 0.4))
    P.laptop("Laptop", *at(-78, D + 0.62), arm=0.28, screen="mfd_map")
    P.whiteboard("FlightPlan", *at(-78, D + 0.92))
    P.headset("Headset", *at(-66, D + 0.62))
    P.tool_board("ToolBoard", *at(143, D + 0.5))
    # supplies: lockers with cargo bags above, gas tanks, cargo bags strapped to the deck
    for side in (-1, 1):
        for phi in (105, 128):
            p, b = at(side * phi, D + 0.28, 0.12)
            G.box_unit(f"UpperLocker{side}{phi}", p, (0.3, 0.2, 0.36), L.basis(b.col[0], -b.col[2], b.col[1]), lamps_n=2)
            P.cargo_bag(f"UpperBag{side}{phi}", *at(side * phi, D + 0.68), 0.28, 0.2, 0.14)
        p, b = at(side * 161, D + 0.4, 0.14)
        L.cylinder(f"UpperTank{side}", 0.12, 0.6, M["tank"], p, L.basis(b.col[0], b.col[2], -b.col[1]), segs=28, bevel=0.03)
        for dz in (-0.2, 0.2):
            L.torus(f"UpperTankStrap{side}{dz}", 0.125, 0.006, M["handle"], p + b.col[1] * dz, L.basis(b.col[0], b.col[2], -b.col[1]), seg=28, mseg=6)
        for k in range(2):
            P.cargo_bag(f"DeckBag{side}{k}", *flat(side * (0.75 + 0.02 * k), 0.15 + k * 0.32, D + 0.015), 0.34, 0.28, 0.18)
            L.box(f"DeckBagStrap{side}{k}", (0.38, 0.03, 0.2), M["strap"], (side * (0.75 + 0.02 * k), 0.15 + k * 0.32, D + 0.11), bevel=0.004)
    # docking: binoculars by the windows, a camera bracketed at the right docking window
    P.binoculars("Binoculars", *at(33, D + 0.45))
    w = next(w for w in C.WINDOWS if w["name"] == "DockingR")
    p, b = at(math.degrees(w["phi"]) + 8, w["z"] - 0.24, 0.02)
    P.camera("DockCamera", p, b, lens_dir=(C.polar(w["phi"], C.r_in(w["z"]) + 0.2, w["z"]) - p))
    # high ring: avionics panels and cabin fans above everything
    G.wall("UpperHigh", [
        ("breakers", 62, D + 1.05, 0.26, 0.12, {"cols": 9, "rows": 2}), ("annunciators", -62, D + 1.05, 0.22, 0.09, {"cols": 6, "rows": 2, "start": 2}),
        ("vent", 100, D + 1.0, 0.22, 0.12, {"slots": 6}), ("knobs", -100, D + 1.0, 0.22, 0.08, {"n": 4}),
        ("lamps", 145, D + 1.0, 0.16, 0.05, {"n": 4}), ("breakers", -145, D + 1.0, 0.22, 0.11, {"cols": 8, "rows": 2}),
    ])
    for side in (-1, 1):
        P.fan(f"CabinFan{side}", *at(side * 122, D + 0.98))


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
    P.binders("Checklists", *at(180, 1.0, 0.0))
    for side in (-1, 1):
        a, _ = at(side * 145, 0.9, 0.0)
        c, _ = at(side * 145, 1.3, 0.0)
        a2, _ = at(side * 145, 0.9, 0.05)
        c2, _ = at(side * 145, 1.3, 0.05)
        L.tube(f"Handrail{side}", [a, a2, c2, c], 0.012, M["yellow"])
    # the zero-g indicator, hanging from the console hood where the commander can see it
    P.plush("ZeroGIndicator", Vector((0.22, MDC_Y + MDC_H / 2 + 0.02, MDC_Z - 0.06)), length=0.12)


# ------------------------------------------------------------------ walls: lockers, stowage, safety kit, conduits
def build_walls():
    G.wall("WallBack", [
        ("breakers", 150, 1.0, 0.3, 0.14, {"cols": 10, "rows": 2}), ("vent", 210, 1.0, 0.3, 0.14, {"slots": 7}),
        ("annunciators", 140, 1.55, 0.2, 0.08, {"cols": 6, "rows": 2, "start": 2}), ("knobs", 220, 1.55, 0.2, 0.07, {"n": 4}),
    ])
    for k2, phi in enumerate((160, 180, 200)):
        p, b = C.frame_at(C.rad(phi), 1.5, 0.1)
        G.box_unit(f"BackLocker{k2}", p, (0.32, 0.18, 0.5), L.basis(b.col[0], -b.col[2], b.col[1]), lamps_n=2)
    for side in (-1, 1):
        G.wall(f"WallFront{side}", [("breakers", side * 40, 1.7, 0.24, 0.12, {"cols": 8, "rows": 2}), ("lamps", side * 40, 1.86, 0.16, 0.05, {"n": 3})])
        for k2, z in enumerate((0.5, 0.72)):
            p, b = C.frame_at(C.rad(side * 40), z, 0.01)
            L.box(f"Bag{side}{k2}", (0.26, 0.17, 0.1), M["canvas"], p + b.col[2] * 0.05, b, bevel=0.035, segs=4)
            for sx in (-0.3, 0.3):
                L.box(f"Bag{side}{k2}Strap{sx}", (0.018, 0.18, 0.108), M["strap"], p + b.col[2] * 0.05 + b.col[0] * (0.26 * sx), b, bevel=0.003)
        G.conduit(f"Riser{side}", [C.polar(C.rad(side * 132), C.r_in(z) - 0.014, z) for z in (FLOOR + 0.02, 0.8, 1.5, DECK_Z - 0.05)])
    p, b = C.frame_at(C.rad(128), 1.4, 0.07)
    L.cylinder("Extinguisher", 0.05, 0.34, M["extinguisher"], p, L.basis(b.col[0], b.col[2], -b.col[1]), segs=24, bevel=0.01)
    L.cylinder("ExtinguisherHead", 0.022, 0.05, M["rib"], p + b.col[1] * 0.19, L.basis(b.col[0], b.col[2], -b.col[1]), segs=12)
    p, b = C.frame_at(C.rad(-128), 1.4, 0.05)
    L.box("FirstAid", (0.18, 0.13, 0.09), M["btn_soft"], p, b, bevel=0.008)
    L.box("FirstAidCrossH", (0.07, 0.02, 0.004), M["red"], p + b.col[2] * 0.046, b)
    L.box("FirstAidCrossV", (0.02, 0.07, 0.004), M["red"], p + b.col[2] * 0.046, b)
    for k2, (deg, z) in enumerate(((-12, 0.55), (12, 0.55))):
        p, b = C.frame_at(C.rad(deg), z, 0.13)
        rot = L.basis(b.col[1], b.col[2], b.col[0])
        L.cylinder(f"FrontTank_{k2}", 0.09, 0.34, M["tank"], p, rot, segs=28, bevel=0.012)


# ------------------------------------------------------------------ build
C.build_shell(dome=True, ring_light=True)
C.build_stringers(20, keep_clear, z1=C.Z_CEIL)
for w in C.WINDOWS:
    C.build_window(w, depth=0.05, bolts=32)
    C.view_markers(w, standoff=0.35)
build_mdc()
build_lower_deck()
build_side_consoles()
C.build_hatch(HATCH_PHI, HATCH_HALF, H["z0"], H["z1"])
build_upper_deck()
build_walls()
build_upper_kit()
build_lower_kit()
for i, seat in enumerate(SEATS):
    C.eye_marker(i, seat)
ref = os.path.join(os.environ.get("IVA_REFERENCE", "C:/Games/KSP2Mods/reference"), "poses", POSE["ref_from"] + ".obj")
C.reference_kerbal_copies(ref, POSE["ref_base_y"], [(s["x"], POSE["ref_offset"][1], POSE["ref_offset"][2]) for s in SEATS])
print(f"eyes at z {EYE_Z:.3f}; console {MDC_Z - EYE_Z:.3f} m above; deck at {DECK_Z:.2f}")
L.save(OUT)
