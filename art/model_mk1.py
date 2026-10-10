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

M = L.M
M["blanket"] = L.material("IVA_Blanket", tex="blanket_color.png", normal="blanket_normal.png", rough=0.42, metal=0.6, uv_scale=(1.1, 1.1))
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
    s = C.Surface("CeilingConsole", (0.0, 0.0, 0.772), (1, 0, 0), (0, -1, 0), 0.42, 0.37, bend=0.55, corner=0.09)
    s.build(M["console"], thick=0.025)
    # brackets from the console back to the crown
    for k, deg in enumerate((45, 135, 225, 315)):
        a = C.rad(deg)
        p = Vector((0.17 * math.sin(a), -0.15 * math.cos(a), 0.79))
        q, _ = C.frame_at(a, 0.80, 0.0)
        C.bracket(f"CeilingBracket_{k}", p, q, r=0.009)

    p, b = s.at(0.0, 0.0)
    s.reserve("Navball", 0.0, 0.0, 0.058, 0.058)
    C.navball("Navball", p, b, r=0.046)

    p, b = s.at(0.128, 0.012)
    s.reserve("AttitudeCRT", 0.128, 0.002, 0.045, 0.045)
    C.crt("Attitude", p, b, M["crt_att"])

    p, b = s.at(-0.128, 0.004)
    s.reserve("Periscope", -0.128, 0.004, 0.052, 0.052)
    C.periscope("Periscope", p, b, r=0.042)

    s.reserve("Telelights", 0.0, 0.125, 0.032, 0.01)
    C.lamps("Telelight", [s.at(-0.02 + 0.02 * k, 0.125) for k in range(3)])
    s.reserve("Clock", -0.1, 0.105, 0.024, 0.024)
    p, b = s.at(-0.1, 0.105)
    C.gauge("Clock", p, b, "press", r=0.02)
    s.reserve("EventTimer", 0.1, 0.105, 0.035, 0.014)
    p, b = s.at(0.1, 0.105)
    L.box("EventTimer", (0.07, 0.028, 0.008), M["bezel"], p, b, bevel=0.003)
    L.plane("EventTimerDigits", 0.06, 0.018, M["crt_data"], p + b.col[2] * 0.0045, b, (0.05, 0.62, 0.95, 0.78))

    s.reserve("SeqButtons", 0.0, -0.097, 0.044, 0.014)
    C.push_buttons("SeqButton", [s.at(x, -0.097) for x in (-0.03, 0.0, 0.03)])
    s.reserve("NamePlate", 0.0, -0.148, 0.06, 0.015)
    p, b = s.at(0.0, -0.148)
    L.plane("NamePlate", 0.12, 0.03, M["plate"], p + b.col[2] * 0.002, b)
    s.reserve("ModeToggles", 0.125, -0.085, 0.036, 0.018)
    C.toggles("ModeToggle", [s.at(0.1 + 0.017 * k, -0.085) for k in range(4)])
    s.reserve("DimmerKnobs", -0.125, -0.085, 0.036, 0.016)
    for k in range(3):
        p, b = s.at(-0.15 + 0.025 * k, -0.085)
        L.cylinder(f"DimmerKnob_{k}", 0.009, 0.012, M["bezel"], p + b.col[2] * 0.006, b, segs=16, bevel=0.002)
        L.box(f"DimmerPointer_{k}", (0.002, 0.009, 0.003), M["toggle"], p + b.col[2] * 0.013 + b.col[1] * 0.003, b)
    s.check()


# ------------------------------------------------------------------ crown of instruments round the upper cone
def build_crown():
    crown = C.Band("Crown", -math.pi, math.pi, CROWN_Z0, CROWN_Z1, CROWN_INSET)
    crown.build(M["console"])
    # under-lit lower edge
    zl = CROWN_Z0 - 0.006
    C.L.tube("CrownLightStrip", [C.polar(2 * math.pi * j / 96, C.r_in(zl) - CROWN_INSET + 0.004, zl) for j in range(97)], 0.005, M["light"], closed=True)
    zm = (CROWN_Z0 + CROWN_Z1) / 2

    # right of the view (+X): flight gauges in a 2x2 block
    for g, (deg, z) in zip(("alt", "press", "temp", "fuel"), ((78, zm + 0.04), (78, zm - 0.04), (102, zm + 0.04), (102, zm - 0.04))):
        p, b = C.frame_at(C.rad(deg), z, CROWN_INSET + 0.012)
        crown.reserve("Gauge_" + g, deg, z, 0.026, 0.026)
        C.gauge("Gauge_" + g, p, b, g)
    # behind the right hand: the abort T-handle
    deg = 140
    p, b = C.frame_at(C.rad(deg), zm + 0.012, CROWN_INSET + 0.012)
    crown.reserve("Abort", deg, zm, 0.0375, 0.07)
    C.abort_handle("Abort", p, b, label=C.frame_at(C.rad(deg), zm - 0.05, CROWN_INSET + 0.012))
    # left of the view (-X): toggle bank and breakers
    crown.reserve("Toggles", -90, zm + 0.03, 0.05, 0.02)
    C.toggles("Toggle", [crown.at(0.017 * (k - 2.5), zm + 0.03, centre_deg=-90) for k in range(6)])
    crown.reserve("Breakers", -90, zm - 0.04, 0.05, 0.012)
    C.breakers("Breaker", [crown.at(0.022 * (k - 2), zm - 0.04, centre_deg=-90) for k in range(5)])
    # behind the left hand: the sequencer panel
    crown.reserve("Sequencer", -140, zm, 0.045, 0.045)
    p, b = C.frame_at(C.rad(-140), zm, CROWN_INSET + 0.012)
    L.box("SequencerPlate", (0.09, 0.09, 0.006), M["bezel"], p, b, bevel=0.003)
    C.lamps("SeqLamp", [(p + b.col[0] * (-0.027 + 0.018 * k) + b.col[1] * 0.025 + b.col[2] * 0.004, b) for k in range(4)])
    C.push_buttons("SeqArm", [(p + b.col[0] * (-0.022 + 0.022 * k) - b.col[1] * 0.018 + b.col[2] * 0.003, b) for k in range(3)])
    # above the porthole (front), and over the feet (back): placards
    crown.reserve("CrownPlate", 0, zm, 0.06, 0.016)
    p, b = C.frame_at(0.0, zm, CROWN_INSET + 0.012)
    L.plane("CrownPlate", 0.12, 0.03, M["plate"], p + b.col[2] * 0.002, b)
    crown.reserve("Hazard", 180, zm, 0.08, 0.018)
    p, b = C.frame_at(math.pi, zm, CROWN_INSET + 0.012)
    L.plane("CrownHazard", 0.16, 0.035, M["hazard"], p + b.col[2] * 0.002, b, (0, 0, 1, 0.5))
    # right-front, beside the hatch: cabin pressure pair
    for k, (deg, g) in enumerate(((37, "press"), (52, "temp"))):
        p, b = C.frame_at(C.rad(deg), zm, CROWN_INSET + 0.012)
        crown.reserve("Cabin_" + g, deg, zm, 0.024, 0.024)
        C.gauge(f"CabinGauge_{k}", p, b, g, r=0.019)
    # left-front: comms panel
    crown.reserve("Comms", -42, zm, 0.04, 0.03)
    p, b = C.frame_at(C.rad(-42), zm, CROWN_INSET + 0.012)
    L.box("CommsPanel", (0.08, 0.06, 0.006), M["bezel"], p, b, bevel=0.003)
    for k in range(2):
        L.cylinder(f"CommsKnob_{k}", 0.011, 0.012, M["toggle"], p + b.col[0] * (-0.02 + 0.04 * k) + b.col[2] * 0.008, b, segs=16, bevel=0.002)
    L.plane("CommsLabel", 0.06, 0.012, M["labels"], p - b.col[1] * 0.02 + b.col[2] * 0.004, b, (0.02, 0.81, 0.23, 0.94))
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
