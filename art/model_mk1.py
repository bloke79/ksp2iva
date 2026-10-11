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
import stock as S  # noqa: E402
S.materials()
M["deckplate"] = L.material("IVA_DeckPlate", tex="deckplate_color.png", normal="deckplate_normal.png", rough=0.6, metal=0.35, normal_strength=0.8)

M = L.M
M["blanket"] = L.material("IVA_WallPanel", tex="wallpanel_color.png", normal="wallpanel_normal.png", rough=0.55, metal=0.3, uv_scale=(1.0, 1.0), normal_strength=0.8)
M["shell"] = L.material("IVA_SeatShell", (0.22, 0.23, 0.25), rough=0.4, metal=0.55)
M["bottle"] = L.material("IVA_Bottle", (0.22, 0.42, 0.30), rough=0.35, metal=0.4)
M["canvas"] = L.material("IVA_Canvas", (0.27, 0.28, 0.23), rough=0.92, normal="canvas_normal.png", uv_scale=(6.0, 6.0), normal_strength=0.8)
M["umbilical"] = L.material("IVA_Umbilical", (0.32, 0.36, 0.42), rough=0.7)
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
        S.beam(f"CeilingBracket_{k}", p, q, 0.026, 0.026, M["frame"], up=(0, 0, 1))
    G.grid(s, "Ceil", 4, 4, [
        ("dial", 0, 0, 1, 1, {"kind": "alt"}), ("annunciators", 1, 0, 2, 1, {"cols": 4, "rows": 2}), ("dial", 3, 0, 1, 1, {"kind": "press"}),
        ("periscope", 0, 1, 1, 1, {}), ("navball", 1, 1, 2, 2, {}), ("mfd", 3, 1, 1, 1, {"screen": "mfd_systems"}),
        ("dial", 0, 2, 1, 1, {"kind": "temp"}), ("screen", 3, 2, 1, 1, {"mat": "crt_att"}),
        ("toggles", 0, 3, 2, 1, {"cols": 6}), ("buttons", 2, 3, 1, 1, {"n": 3}), ("knobs", 3, 3, 1, 1, {"n": 2}),
    ], border=0.012)
    s.check()
    G.housing(s, "Ceil", depth=0.055)
    for k, deg in enumerate((20, 200)):   # cable runs from the console housing out to the crown
        a = s.c + s.n * -0.04 + Vector((0.12 * math.sin(C.rad(deg)), -0.12 * math.cos(C.rad(deg)), 0.0))
        e = C.frame_at(C.rad(deg), CROWN_Z1 + 0.005, CROWN_INSET)[0]
        S.bundle(f"CeilCables{k}", [a, (a + e) / 2 + Vector((0, 0, 0.012)), e], n=3, r=0.007, colours=[S.CABLES[(k + i) % 4] for i in range(3)])


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
        (-136, 2, [("keypad", 0, 1, 2, 1, {})]),   # lower row: the ceiling console's corner is above the upper one
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
    S.bundle("Loom", [C.polar(C.rad(a), C.r_in(0.11) - 0.03, 0.11) for a in range(80, 281, 20)], n=4, r=0.0075, ends=(True, True))
    for a in range(90, 280, 36):
        p, b = C.frame_at(C.rad(a), 0.11, 0.03)
        L.box(f"LoomClamp_{a}", (0.015, 0.04, 0.03), M["rib"], p, b, bevel=0.003)
    # loom up the back wall to the crown
    S.bundle("RiserLoom", [C.polar(math.pi + 0.18, C.r_in(z) - 0.03, z) for z in (0.13, 0.3, 0.45, CROWN_Z0 - 0.02)], n=3, r=0.008,
             colours=["cable_k", "cable_r", "cable_y"])
    # grab handles either side of the porthole
    for side in (-1, 1):
        phi = WIN["phi"] + side * C.rad(24)
        a = C.polar(phi, C.r_in(0.38) - 0.03, 0.38)
        c = C.polar(phi, C.r_in(0.52) - 0.03, 0.52)
        L.tube(f"GrabHandle{side}", [C.polar(phi, C.r_in(0.38) - 0.005, 0.38), a, c, C.polar(phi, C.r_in(0.52) - 0.005, 0.52)], 0.007, M["yellow"])


# ------------------------------------------------------------------ filling the cabin: hip pedestals, umbilical, stowage
def build_fill():
    slope_up = Vector((0, -1, 0))
    for side, y0, y1 in ((1, -0.08, 0.2), (-1, -0.08, 0.12)):
        x0, x1 = (0.25, 0.37) if side > 0 else (-0.37, -0.25)
        z0, z1 = 0.30, 0.345
        G.prism(f"HipConsole{side}", [(y0, C.Z_FLOOR), (y1, C.Z_FLOOR), (y1, z1), (y0, z0)], x0, x1, M["console"])
        up = Vector((0, y0 - y1, z0 - z1)).normalized()
        top = C.Surface(f"HipTop{side}", ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2 + 0.004), (-1, 0, 0), up, (x1 - x0) - 0.012,
                        math.hypot(y1 - y0, z1 - z0) - 0.016, corner=0.01)
        rows = [("toggles", 0, 0, 2, 1, {"cols": 3}), ("lamps", 0, 1, 2, 1, {"n": 3}), ("dial", 0, 2, 1, 1, {"kind": "temp" if side > 0 else "press"}),
                ("knobs", 1, 2, 1, 1, {"n": 1})]
        if y1 - y0 > 0.25:
            rows.append(("buttons", 0, 3, 2, 1, {"n": 3}))
        G.grid(top, f"Hip{side}", 2, 4 if y1 - y0 > 0.25 else 3, rows, gap=0.004, border=0.004)
        top.check()
        p, b = Vector(((x0 + x1) / 2, y0 - 0.001, (C.Z_FLOOR + z0) / 2)), L.basis(Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0)))
        G.vent(f"HipVent{side}", p, b, (x1 - x0) * 0.7, (z0 - C.Z_FLOOR) * 0.5, slots=5)

    # compact environmental unit low at the back-left, and the suit umbilical to the kerbal's chest
    p, b = C.frame_at(C.rad(-158), 0.11, 0.075)
    G.box_unit("ECSUnit", p, (0.17, 0.12, 0.13), L.basis(b.col[0], -b.col[2], b.col[1]), lamps_n=2)
    G.hose("Umbilical", [p + b.col[2] * 0.05 + Vector((0, 0, 0.06)), Vector((-0.22, 0.2, 0.3)), Vector((-0.21, 0.03, 0.36)), Vector((-0.15, -0.04, 0.37))],
           r=0.015, mat=M["umbilical"])

    # stowage bags low on the front wall, either side of the head; first-aid kit and extinguisher on the side walls
    for side in (-1, 1):
        p, b = C.frame_at(C.rad(side * 28), 0.2, 0.01)
        L.box(f"Bag{side}", (0.16, 0.12, 0.07), M["canvas"], p + b.col[2] * 0.035, b, bevel=0.025, segs=4)
        for sx in (-0.3, 0.3):
            L.box(f"Bag{side}Strap{sx}", (0.016, 0.13, 0.078), M["strap"], p + b.col[2] * 0.035 + b.col[0] * (0.16 * sx), b, bevel=0.003)
    p, b = C.frame_at(C.rad(108), 0.46, 0.04)
    L.box("FirstAid", (0.12, 0.09, 0.06), M["btn_soft"], p, b, bevel=0.006)
    L.box("FirstAidCrossH", (0.045, 0.014, 0.004), M["red"], p + b.col[2] * 0.031, b)
    L.box("FirstAidCrossV", (0.014, 0.045, 0.004), M["red"], p + b.col[2] * 0.031, b)
    p, b = C.frame_at(C.rad(-104), 0.45, 0.05)
    L.cylinder("Extinguisher", 0.04, 0.2, M["extinguisher"], p, L.basis(b.col[0], b.col[2], -b.col[1]), segs=24, bevel=0.008)
    L.cylinder("ExtinguisherHead", 0.017, 0.04, M["rib"], p + b.col[1] * 0.12, L.basis(b.col[0], b.col[2], -b.col[1]), segs=12)
    for dz in (-0.05, 0.05):
        L.torus(f"ExtinguisherClamp{dz}", 0.043, 0.004, M["handle"], p + b.col[1] * dz, L.basis(b.col[0], b.col[2], -b.col[1]), seg=24, mseg=6)


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


# ------------------------------------------------------------------ stock-style structure (built last, fits round everything)
def build_structure():
    clear = S.Clearance()
    S.ring_frame("Skirt", C.Z_FLOOR + 0.04, clear, h=0.05, d=0.03)
    clear = S.Clearance()
    S.wall_ribs("Wall", 10, C.Z_FLOOR + 0.07, CROWN_Z0 - 0.02, clear, w=0.045, d=0.035, min_len=0.22)
    clear = S.Clearance()
    S.wall_plates("Wall", clear, [2 * math.pi * k / 10 for k in range(10)], (0.24, 0.44), size=(0.11, 0.09), chance=0.6, seed=14)


# ------------------------------------------------------------------ build
C.build_shell(dome=True, ring_light=False)
deck_floor()
C.build_window(WIN, depth=0.035)
C.view_markers(WIN, standoff=0.2)
build_ceiling_console()
build_crown()
C.couch("Couch", X0, POSE, C.Z_FLOOR)
C.build_hatch(HATCH_PHI, HATCH_HALF, HATCH_Z0, HATCH_Z1)
build_equipment()
build_fill()
build_structure()
S.collision_markers(min_size=0.12)
C.eye_marker(0, SEAT)
C.reference_kerbals(os.path.join(os.environ.get("IVA_REFERENCE", "C:/Games/KSP2Mods/reference"), "poses", SPEC["part"] + ".obj"), SPEC["hull_base_y"])
e = Vector(SEAT["eye"])
print(f"eye at {e.x:.3f}, {e.y:.3f}, {e.z:.3f}; ceiling console {0.772 - e.z:.3f} m above the eye")
L.save(OUT)
