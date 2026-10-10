"""Mk1-3 "Gumball" (pod_2v_conical_crew) interior, built round the game's three seated kerbals.

Usage: blender -b --python model_mk13.py -- <spec.json> <texture_dir> <out.blend>

The game lays the crew side by side on their backs (x = 0 and +/-0.622), heads to the front under the windows,
looking straight up. So, Apollo-style: a three-section main display console hangs above the faces, each wing angled
to its kerbal; side consoles sit on the walls beside the outer couches, within reach; the couches are moulded to the
captured poses and tied into one frame; lockers fill the back wall under the hatch, tanks and a stowage net the front
wall behind the heads; a docking hatch and ring light close the ceiling.

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
G.materials()
M = L.M
import stock as S  # noqa: E402
S.materials()
M["deckplate"] = L.material("IVA_DeckPlate", tex="deckplate_color.png", normal="deckplate_normal.png", rough=0.6, metal=0.35, normal_strength=0.8)

M = L.M
M["blanket"] = L.material("IVA_WallPanel", tex="wallpanel_color.png", normal="wallpanel_normal.png", rough=0.55, metal=0.3, uv_scale=(1.0, 1.0), normal_strength=0.8)
M["shell"] = L.material("IVA_SeatShell", (0.22, 0.23, 0.25), rough=0.4, metal=0.55)
M["bottle"] = L.material("IVA_Bottle", (0.22, 0.42, 0.30), rough=0.35, metal=0.4)
M["tank"] = L.material("IVA_Tank", (0.78, 0.79, 0.80), rough=0.3, metal=0.7)
M["periscope"] = L.material("IVA_Periscope", tex="periscope.png", rough=0.1, emit=1.6, emit_tex=True)
M["canvas"] = L.material("IVA_Canvas", (0.27, 0.28, 0.23), rough=0.92, normal="canvas_normal.png", uv_scale=(6.0, 6.0), normal_strength=0.8)
M["umbilical"] = L.material("IVA_Umbilical", (0.32, 0.36, 0.42), rough=0.7)
M["net"] = L.material("IVA_Net", (0.30, 0.32, 0.20), rough=0.9)

C.setup(SPEC, wall=SPEC["wall"], ceil=SPEC["ceiling"], top=SPEC["ceiling"] + 0.1, seg=160)
POSE = SPEC["pose"]
SEATS = POSE["seats"]
H = SPEC["hatch"]
HATCH_PHI, HATCH_HALF = C.rad(-H["angle"]), C.rad(H["half_deg"])
EYE_Z = SEATS[0]["eye"][2]
SIDE_PHI0, SIDE_PHI1, SIDE_Z0, SIDE_Z1 = C.rad(86), C.rad(128), 0.50, 0.84
LOCKER_PHI0, LOCKER_PHI1 = C.rad(148), C.rad(212)


def keep_clear(phi):
    if C.ang_dist(phi, HATCH_PHI) < HATCH_HALF + C.rad(5):
        return True
    for w in C.WINDOWS:
        if C.ang_dist(phi, w["phi"]) < w["hw"] / C.r_in(w["z"]) + C.rad(5):
            return True
    return False


# ------------------------------------------------------------------ main display console above the crew
MDC_Z, MDC_Y, MDC_H = 1.16, -0.13, 0.42
WING_TILT = C.rad(15)


def wing(side):
    """Outer section over seat +/-1: inner edge high, outer edge lower, following the cone."""
    right = Vector((math.cos(WING_TILT), 0, -side * math.sin(WING_TILT)))
    return C.Surface(f"MDC_Wing{'R' if side > 0 else 'L'}", (side * 0.6, MDC_Y, MDC_Z - 0.075), right, (0, -1, 0), 0.46, MDC_H, bend=0.0, corner=0.04)


def build_mdc():
    centre = C.Surface("MDC_Centre", (0.0, MDC_Y, MDC_Z), (1, 0, 0), (0, -1, 0), 0.6, MDC_H, bend=1.4, corner=0.04)
    wings = {1: wing(1), -1: wing(-1)}
    for s in (centre, wings[1], wings[-1]):
        s.build(M["console"], thick=0.03)
    # structure: seam beams between the sections, hangers up to the wall
    for side in (-1, 1):
        a = Vector((side * 0.335, MDC_Y - MDC_H / 2 - 0.01, MDC_Z + 0.01))
        b = Vector((side * 0.335, MDC_Y + MDC_H / 2 + 0.01, MDC_Z + 0.01))
        S.beam(f"MDC_Seam{side}", a, b, 0.045, 0.045, M["frame"])
        # hangers straight up to the ceiling ring, clear of the windows' sight lines
        for k, y in enumerate((MDC_Y - 0.17, MDC_Y + 0.17)):
            S.beam(f"MDC_Hanger{side}_{k}", Vector((side * 0.335, y, MDC_Z + 0.03)), Vector((side * 0.335, y, C.Z_CEIL + 0.03)), 0.034, 0.034, M["frame"], up=(0, 1, 0))
            S.cbox(f"MDC_Collar{side}_{k}", (0.05, 0.05, 0.03), M["frame_dark"], (side * 0.335, y, MDC_Z + 0.14), ch=0.006)
    # back hood over the whole console
    hy = MDC_Y + MDC_H / 2 + 0.02
    S.cbox("MDC_Hood", (1.5, 0.04, 0.07), M["frame"], (0, hy, MDC_Z + 0.02), ch=0.012)
    # floodlights under the hood's back edge, aimed down the couches (out of the crew's line of sight)
    aim = Vector((0, 0.45, -1)).normalized()
    for k, x in enumerate((-0.6, -0.2, 0.2, 0.6)):
        p = Vector((x, hy + 0.01, MDC_Z - 0.03))
        rot = (-aim).to_track_quat("Z", "Y").to_matrix()
        L.cylinder(f"Flood_{k}", 0.022, 0.03, M["ring"], p, rot, segs=20, radius2=0.017)
        L.disc(f"FloodLens_{k}", 0.014, M["light"], p + aim * 0.016, aim.to_track_quat("Z", "Y").to_matrix(), segs=20)

    # Modules on a grid per section (row 0 is the head end, screen-up). Commander in the middle: flight;
    # right wing: propulsion and systems; left wing: comms and navigation.
    G.grid(centre, "MDC_C", 6, 4, [
        ("dial", 0, 0, 1, 1, {"kind": "alt"}), ("annunciators", 1, 0, 4, 1, {"cols": 8, "rows": 2}), ("dial", 5, 0, 1, 1, {"kind": "fuel"}),
        ("mfd", 0, 1, 2, 2, {"screen": "mfd_systems"}), ("navball", 2, 1, 2, 2, {}), ("mfd", 4, 1, 2, 2, {"screen": "mfd_map"}),
        ("abort", 0, 3, 1, 1, {}), ("buttons", 1, 3, 1, 1, {"n": 3}), ("toggles", 2, 3, 2, 1, {"cols": 6}),
        ("knobs", 4, 3, 1, 1, {"n": 2}), ("lamps", 5, 3, 1, 1, {"n": 3}),
    ])
    G.grid(wings[1], "MDC_R", 4, 4, [
        ("dial", 0, 0, 1, 1, {"kind": "press"}), ("dial", 1, 0, 1, 1, {"kind": "temp"}), ("annunciators", 2, 0, 2, 1, {"cols": 4, "rows": 2, "start": 4}),
        ("mfd", 0, 1, 2, 2, {"screen": "mfd_engine"}), ("keypad", 2, 1, 2, 2, {}),
        ("breakers", 0, 3, 4, 1, {"cols": 12, "rows": 2}),
    ])
    G.grid(wings[-1], "MDC_L", 4, 4, [
        ("knobs", 0, 0, 2, 1, {"n": 4}), ("dial", 2, 0, 1, 1, {"kind": "press"}), ("dial", 3, 0, 1, 1, {"kind": "temp"}),
        ("mfd", 0, 1, 2, 2, {"screen": "mfd_comms"}), ("screen", 2, 1, 2, 1, {"mat": "crt_orbit"}), ("toggles", 2, 2, 2, 1, {"cols": 6}),
        ("breakers", 0, 3, 2, 1, {"cols": 6, "rows": 2}), ("vent", 2, 3, 1, 1, {}), ("lamps", 3, 3, 1, 1, {"n": 3}),
    ])
    for s_ in (centre, wings[1], wings[-1]):
        s_.check()
    for s_, nm in ((centre, "MDC_C"), (wings[1], "MDC_R"), (wings[-1], "MDC_L")):
        G.housing(s_, nm)
    # name plate on the hood
    L.plane("NamePlate", 0.24, 0.05, M["plate"], Vector((0, MDC_Y + MDC_H / 2 + 0.006, MDC_Z + 0.02)), L.basis(Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0))))


# ------------------------------------------------------------------ side consoles beside the outer couches
def build_side_consoles():
    for side in (1, -1):
        p0, p1 = (SIDE_PHI0, SIDE_PHI1) if side > 0 else (-SIDE_PHI1, -SIDE_PHI0)
        nm = "SideConsoleR" if side > 0 else "SideConsoleL"
        band = C.Band(nm, p0, p1, SIDE_Z0, SIDE_Z1, 0.07)
        band.build(M["console"])
        mid = math.degrees((p0 + p1) / 2)
        zc = (SIDE_Z0 + SIDE_Z1) / 2
        G.band_grid(band, nm, mid, zc, 6, 3, 0.105, 0.105, [
            ("breakers", 0, 0, 4, 1, {"cols": 12, "rows": 2}), ("annunciators", 4, 0, 2, 1, {"cols": 4, "rows": 2, "start": 8 if side > 0 else 12}),
            ("dial", 0, 1, 1, 1, {"kind": "press"}), ("dial", 1, 1, 1, 1, {"kind": "temp"}), ("toggles", 2, 1, 2, 1, {"cols": 6}),
            ("knobs", 4, 1, 2, 1, {"n": 4}),
            ("screen", 0, 2, 2, 1, {"mat": "crt_data"}), ("toggles", 2, 2, 2, 1, {"cols": 6, "rows": 1}), ("vent", 4, 2, 2, 1, {"slots": 5}),
        ])
        band.check()


# ------------------------------------------------------------------ couches on one frame
def build_couches():
    for i, seat in enumerate(SEATS):
        C.couch(f"Couch{i}_", seat["x"], POSE, C.Z_FLOOR)
    xs = sorted(s["x"] for s in SEATS)
    prof = POSE["couch"]
    for k, y in enumerate((prof[len(prof) // 4][0], prof[(3 * len(prof)) // 4][0])):
        z = min(zz for yy, zz, ww in prof if abs(yy - y) < 0.04) - 0.1
        S.beam(f"CouchFrameBeam_{k}", Vector((xs[0] - 0.16, y, z)), Vector((xs[-1] + 0.16, y, z)), 0.045, 0.055, M["frame"])
        for x in (xs[0] - 0.14, xs[-1] + 0.14):
            S.beam(f"CouchFrameLeg_{k}_{x:.2f}", Vector((x, y, z)), Vector((x * 1.08, y, C.Z_FLOOR + 0.02)), 0.042, 0.042, M["frame"], up=(0, 1, 0))
            S.cbox(f"CouchFrameFoot_{k}_{x:.2f}", (0.085, 0.085, 0.024), M["frame_dark"], (x * 1.08, y, C.Z_FLOOR + 0.012), ch=0.008)
    # attenuator struts from the frame to the walls (the Apollo couch struts)
    for side in (-1, 1):
        y = prof[len(prof) // 2][0]
        a = Vector((side * (xs[-1] + 0.14), y, 0.3))
        S.beam(f"Attenuator{side}", a, C.polar(side * C.rad(90), C.r_in(0.42) - 0.01, 0.42), 0.04, 0.04, M["frame"], up=(0, 1, 0))
        L.cylinder(f"AttenuatorSleeve{side}", 0.028, 0.12, M["couchframe"], (a + C.polar(side * C.rad(90), C.r_in(0.42) - 0.01, 0.42)) / 2,
                   Vector((side, 0, 0.1)).to_track_quat("Z", "Y").to_matrix(), segs=20)


# ------------------------------------------------------------------ back wall: lockers under the hatch, ladder rungs
def build_back_wall():
    n = 5
    span = LOCKER_PHI1 - LOCKER_PHI0
    for k in range(n):
        phi = LOCKER_PHI0 + span * (k + 0.5) / n
        for row, (z, h) in enumerate(((0.36, 0.26), (0.66, 0.26))):
            p, b = C.frame_at(phi, z, 0.06)
            w = span / n * C.r_in(z) - 0.02
            L.box(f"Locker_{k}_{row}", (w, h, 0.05), M["locker"], p, b, bevel=0.006)
            L.box(f"LockerLatch_{k}_{row}", (0.05, 0.016, 0.012), M["handle"], p + b.col[2] * 0.03 + b.col[1] * (h / 2 - 0.035), b, bevel=0.003)
            L.plane(f"LockerLabel_{k}_{row}", 0.07, 0.018, M["labels"], p + b.col[2] * 0.026 - b.col[1] * (h / 2 - 0.03), b, (0.02, 0.81, 0.23, 0.94))
    for k, z in enumerate((0.88, 0.98, 1.08)):
        a, b_ = C.polar(math.pi - 0.12, C.r_in(z) - 0.005, z), C.polar(math.pi + 0.12, C.r_in(z) - 0.005, z)
        m1, m2 = C.polar(math.pi - 0.1, C.r_in(z) - 0.05, z), C.polar(math.pi + 0.1, C.r_in(z) - 0.05, z)
        L.tube(f"Rung_{k}", [a, m1, m2, b_], 0.01, M["yellow"])


# ------------------------------------------------------------------ front wall behind the heads: tanks, stowage net
def build_front_wall():
    for k, (deg, z) in enumerate(((-16, 0.3), (16, 0.3), (0, 0.48))):
        p, b = C.frame_at(C.rad(deg), z, 0.1)
        rot = L.basis(b.col[1], b.col[2], b.col[0])
        L.cylinder(f"FrontTank_{k}", 0.075, 0.28, M["tank"] if k < 2 else M["bottle"], p, rot, segs=28, bevel=0.012)
        for s in (-0.09, 0.09):
            L.torus(f"FrontTankStrap_{k}_{s}", 0.078, 0.005, M["handle"], p + b.col[0] * s, rot @ Matrix.Rotation(math.pi / 2, 3, "Y"), seg=28, mseg=6)
        L.cylinder(f"FrontTankValve_{k}", 0.014, 0.04, M["rib"], p + b.col[0] * 0.16, rot, segs=12)
    # stowage net between the lower windows, at the commander's head end
    pts = []
    for i in range(7):
        for j in range(5):
            pts.append((C.rad(-30 + 10 * i), 0.62 + 0.06 * j))
    for i in range(7):
        L.tube(f"NetV_{i}", [C.polar(C.rad(-30 + 10 * i), C.r_in(0.62 + 0.06 * j) - 0.035, 0.62 + 0.06 * j) for j in range(5)], 0.004, M["net"])
    for j in range(5):
        L.tube(f"NetH_{j}", [C.polar(C.rad(-30 + 10 * i), C.r_in(0.62 + 0.06 * j) - 0.035, 0.62 + 0.06 * j) for i in range(7)], 0.004, M["net"])
    for i in (0, 6):
        for j in (0, 4):
            phi, z = C.rad(-30 + 10 * i), 0.62 + 0.06 * j
            L.sphere(f"NetHook_{i}_{j}", 0.01, M["buckle"], C.polar(phi, C.r_in(z) - 0.03, z), u=10, v=6)


# ------------------------------------------------------------------ filling the cabin: pedestals, umbilicals, cables, equipment
PED_X, PED_W, PED_Y0, PED_Y1, PED_Z0, PED_Z1 = 0.325, 0.15, -0.06, 0.32, 0.45, 0.53


def build_fill():
    up_dir = Vector((0, PED_Y0 - PED_Y1, PED_Z0 - PED_Z1)).normalized()
    slope = math.hypot(PED_Y1 - PED_Y0, PED_Z1 - PED_Z0)
    for side in (-1, 1):
        x = side * PED_X
        # pedestal console between the couches, at hand height, top sloping towards the crew's heads
        G.prism(f"Pedestal{side}", [(PED_Y0, C.Z_FLOOR), (PED_Y1, C.Z_FLOOR), (PED_Y1, PED_Z1), (PED_Y0, PED_Z0)], x - PED_W / 2, x + PED_W / 2, M["console"])
        top = C.Surface(f"PedestalTop{side}", (x, (PED_Y0 + PED_Y1) / 2, (PED_Z0 + PED_Z1) / 2 + 0.004), (-1, 0, 0), up_dir, PED_W - 0.012, slope - 0.02, corner=0.01)
        G.grid(top, f"Ped{side}", 2, 4, [
            ("toggles", 0, 0, 2, 1, {"cols": 4}), ("dial", 0, 1, 1, 1, {"kind": "press" if side > 0 else "temp"}), ("knobs", 1, 1, 1, 1, {"n": 1}),
            ("lamps", 0, 2, 2, 1, {"n": 4}), ("buttons", 0, 3, 1, 1, {"n": 2}), ("toggles", 1, 3, 1, 1, {"cols": 2}),
        ], gap=0.004, border=0.004)
        top.check()
        p, b = Vector((x, PED_Y0 - 0.001, (C.Z_FLOOR + PED_Z0) / 2)), L.basis(Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0)))
        G.vent(f"PedestalVent{side}", p, b, PED_W * 0.7, (PED_Z0 - C.Z_FLOOR) * 0.6, slots=7)
        # cable runs from the back of the console housing up across the ceiling to the wall (out of the crew's view)
        end = C.polar(C.rad(side * 128), C.r_in(1.42) - 0.04, 1.42)
        S.bundle(f"CeilingCables{side}", [Vector((side * 0.5, MDC_Y + MDC_H / 2 + 0.03, MDC_Z + 0.1)), Vector((side * 0.62, MDC_Y + 0.4, MDC_Z + 0.25)), end],
                 n=4, colours=["cable_k", "cable_r", "cable_g", "cable_y"], ends=(True, False))
        S.junction(f"CeilingCablesBox{side}", C.rad(side * 128), 1.42)

    # equipment behind the feet: environmental control unit and two battery/junction boxes
    G.box_unit("ECSUnit", (0, 0.66, C.Z_FLOOR + 0.12), (0.52, 0.22, 0.24), lamps_n=3)
    for side in (-1, 1):
        G.box_unit(f"PowerBox{side}", (side * 0.6, 0.6, C.Z_FLOOR + 0.1), (0.24, 0.2, 0.2), lamps_n=2)
        G.cables(f"PowerCables{side}", (side * 0.6, 0.6, C.Z_FLOOR + 0.2), (side * 0.3, 0.66, C.Z_FLOOR + 0.24), droop=0.03, n=3)

    # suit umbilicals: ribbed hoses from the ECS unit to each kerbal's suit connector (left side of the chest)
    for i, seat in enumerate(SEATS):
        x = seat["x"]
        start = Vector((max(-0.22, min(0.22, x * 0.35)), 0.56, C.Z_FLOOR + 0.24))
        pts = [start, Vector((x - 0.25, 0.38, 0.38)), Vector((x - 0.25, 0.1, 0.5)), Vector((x - 0.2, -0.1, 0.58)), Vector((x - 0.13, -0.16, 0.6))]
        G.hose(f"Umbilical{i}", pts, r=0.018, mat=M["umbilical"])
        L.cylinder(f"UmbilicalPlug{i}", 0.026, 0.04, M["buckle"], pts[-1], (pts[-1] - pts[-2]).normalized().to_track_quat("Z", "Y").to_matrix(), segs=16)

    # handrail along the console hood and diagonal braces from the ceiling ring to the hood ends
    hy = MDC_Y + MDC_H / 2 + 0.05
    L.tube("HoodRail", [Vector((-0.7, hy, MDC_Z - 0.04)), Vector((-0.7, hy + 0.04, MDC_Z - 0.04)), Vector((0.7, hy + 0.04, MDC_Z - 0.04)), Vector((0.7, hy, MDC_Z - 0.04))], 0.006, M["yellow"])
    for side in (-1, 1):
        S.beam(f"HoodBrace{side}", Vector((side * 0.74, MDC_Y + MDC_H / 2, MDC_Z + 0.02)), C.frame_at(C.rad(side * 150), C.Z_CEIL - 0.06, 0.01)[0], 0.034, 0.034, M["frame"], up=(0, 0, 1))


# ------------------------------------------------------------------ stowage and safety kit on the walls
def bag(name, phi_deg, z, w, h, d):
    """Soft stowage bag strapped to the wall."""
    p, b = C.frame_at(C.rad(phi_deg), z, 0.01)
    L.box(name, (w, h, d), M["canvas"], p + b.col[2] * (d / 2), b, bevel=min(d, h) * 0.35, segs=4)
    for sx in (-0.3, 0.3):
        L.box(f"{name}Strap{sx}", (0.018, h + 0.01, d + 0.008), M["strap"], p + b.col[2] * (d / 2) + b.col[0] * (w * sx), b, bevel=0.003)
    L.box(f"{name}Flap", (w * 0.8, h * 0.28, 0.012), M["canvas"], p + b.col[2] * (d + 0.004) + b.col[1] * (h * 0.3), b, bevel=0.005)
    L.box(f"{name}Tag", (0.05, 0.02, 0.003), M["btn_soft"], p + b.col[2] * (d + 0.011) + b.col[1] * (h * 0.3), b)


def build_stowage():
    for side in (-1, 1):
        bag(f"BagLow{side}", side * 40, 0.34, 0.22, 0.15, 0.09)
        bag(f"BagHigh{side}", side * 42, 0.53, 0.18, 0.13, 0.08)
    # fire extinguisher (right) and first-aid box (left), between the side consoles and the lockers
    p, b = C.frame_at(C.rad(141), 0.95, 0.06)
    rot = L.basis(b.col[0], b.col[1], b.col[2])
    L.cylinder("Extinguisher", 0.045, 0.3, M["extinguisher"], p, L.basis(b.col[0], b.col[2], -b.col[1]), segs=24, bevel=0.01)
    L.cylinder("ExtinguisherHead", 0.02, 0.05, M["rib"], p + b.col[1] * 0.17, L.basis(b.col[0], b.col[2], -b.col[1]), segs=12)
    for dz in (-0.08, 0.08):
        L.torus(f"ExtinguisherClamp{dz}", 0.048, 0.005, M["handle"], p + b.col[1] * dz, L.basis(b.col[0], b.col[2], -b.col[1]), seg=24, mseg=6)
    p, b = C.frame_at(C.rad(-141), 0.95, 0.045)
    L.box("FirstAid", (0.16, 0.12, 0.08), M["btn_soft"], p, b, bevel=0.008)
    L.box("FirstAidCrossH", (0.06, 0.018, 0.004), M["red"], p + b.col[2] * 0.041, b)
    L.box("FirstAidCrossV", (0.018, 0.06, 0.004), M["red"], p + b.col[2] * 0.041, b)
    # checklist board with clipped pages, beside the left side console
    p, b = C.frame_at(C.rad(-80), 0.62, 0.015)
    L.box("ChecklistBoard", (0.13, 0.18, 0.008), M["couchframe"], p, b, bevel=0.002)
    L.box("ChecklistPages", (0.11, 0.15, 0.003), M["btn_soft"], p + b.col[2] * 0.005 - b.col[1] * 0.008, b)
    L.box("ChecklistClip", (0.05, 0.015, 0.012), M["buckle"], p + b.col[2] * 0.008 + b.col[1] * 0.08, b, bevel=0.002)
    # upper cone between the rendezvous windows and the hatch: avionics boxes and an air duct
    G.wall("WallUpper", [
        ("breakers", 75, 1.32, 0.16, 0.1, {"cols": 6, "rows": 2}), ("vent", -75, 1.32, 0.16, 0.1, {"slots": 6}),
        ("lamps", 112, 1.4, 0.1, 0.045, {"n": 3}), ("annunciators", -112, 1.4, 0.12, 0.06, {"cols": 4, "rows": 2, "start": 8}),
    ])
    for side in (-1, 1):
        G.hose(f"AirDuct{side}", [C.frame_at(C.rad(side * 95), 1.5, 0.03)[0], Vector((side * 0.62, MDC_Y + 0.05, MDC_Z + 0.16)), Vector((side * 0.6, MDC_Y, MDC_Z + 0.06))],
               r=0.028, mat=M["umbilical"])


# ------------------------------------------------------------------ wall equipment: junction boxes, breaker boxes, conduits
def build_wall_equipment():
    G.wall("WallBack", [
        ("breakers", 158, 0.98, 0.16, 0.11, {"cols": 6, "rows": 2}), ("vent", 202, 0.98, 0.14, 0.11, {"slots": 6}),
        ("lamps", 160, 1.12, 0.1, 0.045, {"n": 3}), ("knobs", 200, 1.12, 0.1, 0.05, {"n": 2}),
    ])
    for side in (1, -1):
        G.wall(f"WallSide{side}", [
            ("breakers", side * 107, 0.33, 0.22, 0.1, {"cols": 8, "rows": 2}),
            ("annunciators", side * 118, 1.0, 0.13, 0.07, {"cols": 4, "rows": 2, "start": 4 if side > 0 else 0}),
            ("vent", side * 140, 0.33, 0.12, 0.1, {"slots": 5}),
        ])
        # conduits: one up the wall behind the side console, one round under the hatch
        G.conduit(f"ConduitRiser{side}", [C.polar(C.rad(side * 135), C.r_in(z) - 0.012, z) for z in (C.Z_FLOOR + 0.02, 0.5, 0.9, 1.3, C.Z_CEIL - 0.02)])
    G.conduit("ConduitBack", [C.polar(C.rad(a), C.r_in(1.15) - 0.012, 1.15) for a in range(135, 226, 15)], r=0.007)
    G.conduit("ConduitBack2", [C.polar(C.rad(a), C.r_in(1.17) - 0.014, 1.17) for a in range(135, 226, 15)], r=0.005, clamps=False)
    G.wall("WallFront", [("lamps", 0, 1.37, 0.12, 0.05, {"n": 3}), ("dial", 0, 1.27, 0.08, 0.08, {"kind": "press"}),
                         ("breakers", 0, 1.12, 0.2, 0.1, {"cols": 7, "rows": 2}), ("knobs", 0, 0.99, 0.2, 0.07, {"n": 4}),
                         ("toggles", -11, 0.91, 0.1, 0.06, {"cols": 3}), ("lamps", 11, 0.91, 0.1, 0.05, {"n": 3})])
    G.conduit("ConduitFront", [C.polar(0.0, C.r_in(z) - 0.012, z) for z in (C.Z_FLOOR + 0.02, 0.3, 0.6, 0.86)], r=0.007)


# ------------------------------------------------------------------ ceiling: docking hatch with a wheel
def build_ceiling():
    z = C.Z_TOP - 0.004
    L.torus("DockHatchRim", 0.27, 0.02, M["rib"], (0, 0, z - 0.01), Matrix.Identity(3), seg=48, mseg=10)
    L.disc("DockHatch", 0.26, M["hatch"], (0, 0, z - 0.008), Matrix.Rotation(math.pi, 3, "X"))
    L.torus("DockHatchWheel", 0.11, 0.009, M["yellow"], (0, 0, z - 0.06), Matrix.Identity(3), seg=40, mseg=8)
    for k in range(4):
        a = k * math.pi / 2
        L.tube(f"DockWheelSpoke_{k}", [Vector((0, 0, z - 0.03)), Vector((0.11 * math.cos(a), 0.11 * math.sin(a), z - 0.06))], 0.006, M["yellow"])
    L.cylinder("DockWheelHub", 0.025, 0.04, M["rib"], (0, 0, z - 0.03), segs=20)


def dome_z(r):
    """Height of the ceiling dome at radius r (inverse of capsule.build_shell's dome)."""
    R = C.r_in(C.Z_CEIL)
    c = max(-1.0, min(1.0, r / R))
    t = math.acos(c) / (math.pi / 2 * 0.92)
    return C.Z_CEIL + (C.Z_TOP - C.Z_CEIL) * math.sin(min(1.0, t) * math.pi / 2)


def deck_floor():
    f = L.COLL.objects.get("Floor")
    if f is not None:   # solid deck plates instead of grating
        f.data.materials[0] = M["deckplate"]


# ------------------------------------------------------------------ stock-style structure and dressing (built last, fits round everything)
def build_structure():
    D = C.Z_CEIL
    clear = S.Clearance()
    # segmented ring round the docking hatch, equipment boxes round the top of the wall
    for k in range(12):
        a = 2 * math.pi * (k + 0.5) / 12
        r = 0.4
        S.cbox(f"HatchSegment{k}", (0.17, 0.11, 0.022), M["frame"] if k % 2 else M["frame_dark"],
               Vector((r * math.cos(a), r * math.sin(a), dome_z(r) - 0.014)), Matrix.Rotation(a + math.pi / 2, 3, "Z"), ch=0.005)
    n = 0
    for deg in range(-165, 180, 30):
        phi = C.rad(deg)
        p, b = C.frame_at(phi, D - 0.17, 0.0)
        size = (0.2, 0.1, 0.13)
        rot = L.basis(b.col[0], -b.col[2], b.col[1])
        c = p + b.col[2] * (size[1] / 2 + 0.005)
        corners = [c + b.col[0] * sx * size[0] / 2 + b.col[1] * sz * size[2] / 2 for sx in (-1, 1) for sz in (-1, 1)]
        if S.in_window(phi, D - 0.17, 0.08) or any(clear.blocked(q, 0.01) for q in corners + [c]):
            continue
        G.box_unit(f"Cassette{n}", c, size, rot, vents=n % 2 == 0, lamps_n=2)
        n += 1
    clear = S.Clearance()
    S.cable_run("RunLow", C.Z_FLOOR + 0.22, clear, seed=3, n=3)
    S.cable_run("RunHigh", D - 0.36, clear, seed=4)
    clear = S.Clearance()
    S.ring_frame("Skirt", C.Z_FLOOR + 0.05, clear, h=0.06, d=0.035)
    S.ring_frame("Cornice", D - 0.05, clear, h=0.07, d=0.045)
    clear = S.Clearance()
    S.wall_ribs("Wall", 16, C.Z_FLOOR + 0.1, D - 0.1, clear, w=0.055, d=0.04, min_len=0.4)
    clear = S.Clearance()
    S.wall_plates("Wall", clear, [2 * math.pi * k / 16 for k in range(16)], (0.3, 0.65, 1.05, 1.4), size=(0.15, 0.11), chance=0.5, seed=13)


# ------------------------------------------------------------------ build
C.build_shell(dome=True, ring_light=True)
deck_floor()
for w in C.WINDOWS:
    C.build_window(w, depth=0.04, bolts=32)
    C.view_markers(w, standoff=0.3)
build_mdc()
build_side_consoles()
build_couches()
C.build_hatch(HATCH_PHI, HATCH_HALF, H["z0"], H["z1"])
build_back_wall()
build_front_wall()
build_wall_equipment()
build_fill()
build_stowage()
build_ceiling()
build_structure()
S.collision_markers(hatches=[("Docking", (0.0, 0.0, C.Z_TOP - 0.25))])
for i, seat in enumerate(SEATS):
    C.eye_marker(i, seat)
C.reference_kerbals(os.path.join(os.environ.get("IVA_REFERENCE", "C:/Games/KSP2Mods/reference"), "poses", SPEC["part"] + ".obj"), SPEC["hull_base_y"])
print(f"eyes at z {EYE_Z:.3f}; console {MDC_Z - EYE_Z:.3f} m above the eyes")
L.save(OUT)
