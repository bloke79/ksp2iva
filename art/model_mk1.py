"""Mk1 (pod_1v_conical_crew) interior: a bespoke one-kerbal capsule built round the game's real seated pose.

Usage: blender -b --python model_mk1.py -- <spec.json> <texture_dir> <out.blend>

The game lays the kerbal on their back along the pod, head under the porthole, looking straight up at the ceiling
(spec "pose", captured in game). So the instruments are overhead: a ceiling console right above the face (navball,
attitude CRT, periscope screen) inside a crown of gauges and switches that rings the upper cone. The couch is moulded
to the captured body; the porthole sits beside the head; the explosive-bolt hatch is at the right shoulder; oxygen
bottles, a breaker box and wiring looms fill the space round the legs.

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
M["blanket"] = L.material("IVA_Blanket", tex="blanket_color.png", normal="blanket_normal.png", rough=0.5, metal=0.35, uv_scale=(1.1, 1.1))
M["shell"] = L.material("IVA_SeatShell", (0.86, 0.86, 0.84), rough=0.3, metal=0.05)
M["bottle"] = L.material("IVA_Bottle", (0.22, 0.42, 0.30), rough=0.35, metal=0.4)
M["periscope"] = L.material("IVA_Periscope", tex="periscope.png", rough=0.1, emit=1.6, emit_tex=True)

C.setup(SPEC, wall=0.04, ceil=0.80, top=0.88)
POSE = SPEC["pose"]
SEAT = POSE["seats"][0]
X0 = SEAT["x"]
WIN = C.WINDOWS[0]
H = SPEC["hatch"]
HATCH_PHI, HATCH_HALF = C.rad(-H["angle"]), C.rad(13)
HATCH_Z0, HATCH_Z1 = 0.13, 0.565
CROWN_Z0, CROWN_Z1, CROWN_INSET = 0.60, 0.785, 0.045


def keep_clear(phi):
    return C.ang_dist(phi, HATCH_PHI) < HATCH_HALF + C.rad(6) or C.ang_dist(phi, WIN["phi"]) < C.rad(14)


# ------------------------------------------------------------------ ceiling console, right above the face
def build_ceiling_console():
    # facing straight down; as seen from the couch, screen-right is +X and screen-up is the head end (-Y)
    s = C.Surface("CeilingConsole", (0.0, 0.0, 0.772), (1, 0, 0), (0, -1, 0), 0.42, 0.37, bend=0.55, corner=0.05)
    s.build(M["console"], thick=0.025)
    for k, deg in enumerate((45, 135, 225, 315)):
        a = C.rad(deg)
        p = Vector((0.17 * math.sin(a), -0.15 * math.cos(a), 0.79))
        q, _ = C.frame_at(a, 0.80, 0.0)
        C.bracket(f"CeilingBracket_{k}", p, q, r=0.009)
    G.grid(s, "Ceil", 4, 4, [
        ("dial", 0, 0, 1, 1, {"kind": "alt"}), ("annunciators", 1, 0, 2, 1, {"cols": 4, "rows": 2}), ("dial", 3, 0, 1, 1, {"kind": "press"}),
        ("periscope", 0, 1, 1, 1, {}), ("navball", 1, 1, 2, 2, {}), ("mfd", 3, 1, 1, 1, {"screen": "mfd_systems"}),
        ("dial", 0, 2, 1, 1, {"kind": "temp"}), ("screen", 3, 2, 1, 1, {"mat": "crt_att"}),
        ("toggles", 0, 3, 2, 1, {"cols": 6}), ("buttons", 2, 3, 1, 1, {"n": 3}), ("knobs", 3, 3, 1, 1, {"n": 2}),
    ], border=0.012)
    s.check()


# ------------------------------------------------------------------ crown of instruments round the upper cone
def build_crown():
    crown = C.Band("Crown", -math.pi, math.pi, CROWN_Z0, CROWN_Z1, CROWN_INSET)
    crown.build(M["console"])
    zl = CROWN_Z0 - 0.006
    L.tube("CrownLightStrip", [C.polar(2 * math.pi * j / 96, C.r_in(zl) - CROWN_INSET + 0.004, zl) for j in range(97)], 0.005, M["light"], closed=True)
    zm = (CROWN_Z0 + CROWN_Z1) / 2
    cw, ch = 0.088, 0.088
    groups = [   # centre angle, columns, modules (row 0 = top)
        (0, 4, [("annunciators", 0, 0, 4, 1, {"cols": 8, "rows": 2}), ("lamps", 0, 1, 1, 1, {"n": 3}), ("knobs", 1, 1, 2, 1, {"n": 3}), ("lamps", 3, 1, 1, 1, {"n": 3})]),
        (76, 3, [("dial", 0, 0, 1, 1, {"kind": "alt"}), ("dial", 1, 0, 1, 1, {"kind": "press"}), ("dial", 2, 0, 1, 1, {"kind": "fuel"}),
                 ("dial", 0, 1, 1, 1, {"kind": "temp"}), ("toggles", 1, 1, 2, 1, {"cols": 5})]),
        (136, 2, [("abort", 0, 0, 1, 2, {}), ("buttons", 1, 0, 1, 1, {"n": 3}), ("lamps", 1, 1, 1, 1, {"n": 3})]),
        (180, 2, [("breakers", 0, 0, 2, 1, {"cols": 7, "rows": 2}), ("vent", 0, 1, 1, 1, {"slots": 5}), ("knobs", 1, 1, 1, 1, {"n": 2})]),
        (-136, 2, [("keypad", 0, 0, 2, 2, {})]),
        (-76, 3, [("breakers", 0, 0, 3, 1, {"cols": 10, "rows": 2}), ("toggles", 0, 1, 2, 1, {"cols": 6}), ("knobs", 2, 1, 1, 1, {"n": 2})]),
    ]
    for k, (deg, cols, items) in enumerate(groups):
        G.band_grid(crown, f"Crown{k}", deg, zm, cols, 2, cw, ch, items, gap=0.005)
    crown.check()


# ------------------------------------------------------------------ equipment round the legs
def build_equipment():
    for k, z in enumerate((0.15, 0.24)):
        p, b = C.frame_at(C.rad(-128), z, 0.045)
        rot = L.basis(b.col[1], b.col[2], b.col[0])
        L.cylinder(f"O2Bottle_{k}", 0.035, 0.2, M["bottle"], p, rot, segs=24, bevel=0.006)
        L.cylinder(f"O2Valve_{k}", 0.012, 0.03, M["rib"], p + b.col[0] * 0.115, rot, segs=12)
        for s in (-0.06, 0.06):
            L.torus(f"O2Strap_{k}_{s}", 0.037, 0.004, M["handle"], p + b.col[0] * s, rot @ Matrix.Rotation(math.pi / 2, 3, "Y"), seg=24, mseg=6)
    p, b = C.frame_at(C.rad(122), 0.29, 0.04)
    L.box("BreakerBox", (0.17, 0.13, 0.06), M["locker"], p, b, bevel=0.006)
    for row in range(2):
        for col in range(4):
            q = p + b.col[2] * 0.032 + b.col[0] * (-0.054 + col * 0.036) + b.col[1] * (0.025 - row * 0.045)
            L.cylinder(f"BoxBreaker_{row}_{col}", 0.007, 0.01, M["bezel"], q, b, segs=10)
            L.cylinder(f"BoxBreakerCap_{row}_{col}", 0.004, 0.008, M["toggle"], q + b.col[2] * 0.007, b, segs=8)
    L.plane("BoxLabel", 0.11, 0.022, M["plate"], p + b.col[2] * 0.031 + b.col[1] * 0.055, b)
    for k, (dz, dr) in enumerate(((0.0, 0.0), (0.018, 0.004), (0.009, 0.016))):
        L.tube(f"Loom_{k}", [C.polar(C.rad(a), C.r_in(0.1 + dz) - 0.02 - dr, 0.1 + dz) for a in range(80, 281, 10)], 0.007, M["cable"])
    for a in range(90, 280, 36):
        p, b = C.frame_at(C.rad(a), 0.11, 0.03)
        L.box(f"LoomClamp_{a}", (0.015, 0.04, 0.03), M["rib"], p, b, bevel=0.003)
    # loom up the back wall to the crown
    L.tube("RiserLoom", [C.polar(math.pi + 0.18, C.r_in(z) - 0.02, z) for z in (0.11, 0.3, 0.45, CROWN_Z0 - 0.01)], 0.009, M["cable"])
    # grab handles either side of the porthole
    for side in (-1, 1):
        phi = WIN["phi"] + side * C.rad(24)
        a = C.polar(phi, C.r_in(0.38) - 0.03, 0.38)
        c = C.polar(phi, C.r_in(0.52) - 0.03, 0.52)
        L.tube(f"GrabHandle{side}", [C.polar(phi, C.r_in(0.38) - 0.005, 0.38), a, c, C.polar(phi, C.r_in(0.52) - 0.005, 0.52)], 0.007, M["yellow"])


# ------------------------------------------------------------------ build
C.build_shell(dome=True, ring_light=False)
C.build_stringers(10, keep_clear, z1=CROWN_Z0)
C.build_window(WIN, depth=0.035)
C.view_markers(WIN, standoff=0.2)
build_ceiling_console()
build_crown()
C.couch("Couch", X0, POSE, C.Z_FLOOR)
C.build_hatch(HATCH_PHI, HATCH_HALF, HATCH_Z0, HATCH_Z1)
build_equipment()
C.eye_marker(0, SEAT)
C.reference_kerbals(os.path.join(os.environ.get("IVA_REFERENCE", "C:/Games/KSP2Mods/reference"), "poses", SPEC["part"] + ".obj"), SPEC["hull_base_y"])
e = Vector(SEAT["eye"])
print(f"eye at {e.x:.3f}, {e.y:.3f}, {e.z:.3f}; ceiling console {0.772 - e.z:.3f} m above the eye")
L.save(OUT)
