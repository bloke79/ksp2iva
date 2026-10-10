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
M["blanket"] = L.material("IVA_Blanket", tex="blanket_color.png", normal="blanket_normal.png", rough=0.5, metal=0.35, uv_scale=(1.6, 1.6))
M["shell"] = L.material("IVA_SeatShell", (0.86, 0.86, 0.84), rough=0.3, metal=0.05)
M["bottle"] = L.material("IVA_Bottle", (0.22, 0.42, 0.30), rough=0.35, metal=0.4)
M["tank"] = L.material("IVA_Tank", (0.78, 0.79, 0.80), rough=0.3, metal=0.7)
M["periscope"] = L.material("IVA_Periscope", tex="periscope.png", rough=0.1, emit=1.6, emit_tex=True)
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
        L.tube(f"MDC_Seam{side}", [a, b], 0.018, M["couchframe"])
        # hangers straight up to the ceiling ring, clear of the windows' sight lines
        for k, y in enumerate((MDC_Y - 0.17, MDC_Y + 0.17)):
            C.bracket(f"MDC_Hanger{side}_{k}", Vector((side * 0.335, y, MDC_Z + 0.03)), Vector((side * 0.335, y, C.Z_CEIL + 0.03)), r=0.012)
    # back hood over the whole console
    hy = MDC_Y + MDC_H / 2 + 0.02
    L.box("MDC_Hood", (1.5, 0.03, 0.06), M["couchframe"], (0, hy, MDC_Z + 0.02), bevel=0.01)
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
        L.tube(f"CouchFrameBeam_{k}", [Vector((xs[0] - 0.14, y, z)), Vector((xs[-1] + 0.14, y, z))], 0.016, M["couchframe"])
        for x in (xs[0] - 0.14, xs[-1] + 0.14):
            L.tube(f"CouchFrameLeg_{k}_{x:.2f}", [Vector((x, y, z)), Vector((x * 1.08, y, C.Z_FLOOR + 0.005))], 0.016, M["couchframe"])
            L.cylinder(f"CouchFrameFoot_{k}_{x:.2f}", 0.03, 0.014, M["couchframe"], (x * 1.08, y, C.Z_FLOOR + 0.007))
    # attenuator struts from the frame to the walls (the Apollo couch struts)
    for side in (-1, 1):
        y = prof[len(prof) // 2][0]
        a = Vector((side * (xs[-1] + 0.14), y, 0.3))
        L.tube(f"Attenuator{side}", [a, C.polar(side * C.rad(90), C.r_in(0.42) - 0.01, 0.42)], 0.02, M["rib"])
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
    G.wall("WallFront", [("lamps", 0, 1.37, 0.12, 0.05, {"n": 3}), ("dial", 0, 1.27, 0.08, 0.08, {"kind": "press"})])


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


# ------------------------------------------------------------------ build
C.build_shell(dome=True, ring_light=True)
C.build_stringers(16, keep_clear, z1=C.Z_CEIL)
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
build_ceiling()
for i, seat in enumerate(SEATS):
    C.eye_marker(i, seat)
C.reference_kerbals(os.path.join(os.environ.get("IVA_REFERENCE", "C:/Games/KSP2Mods/reference"), "poses", SPEC["part"] + ".obj"), SPEC["hull_base_y"])
print(f"eyes at z {EYE_Z:.3f}; console {MDC_Z - EYE_Z:.3f} m above the eyes")
L.save(OUT)
