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

M = L.M
M["blanket"] = L.material("IVA_Blanket", tex="blanket_color.png", normal="blanket_normal.png", rough=0.42, metal=0.6, uv_scale=(1.6, 1.6))
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
        for k, y in enumerate((MDC_Y - 0.17, MDC_Y + 0.17)):
            top = Vector((side * 0.335, y, MDC_Z + 0.03))
            phi = math.atan2(side * 0.6, -y)
            C.bracket(f"MDC_Hanger{side}_{k}", top, C.frame_at(phi, MDC_Z + 0.2, 0.0)[0], r=0.012)
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

    # --- centre (commander): flight instruments; screen-up is the head end (-Y)
    s = centre
    p, b = s.at(0.0, 0.0)
    s.reserve("Navball", 0.0, 0.0, 0.07, 0.07)
    C.navball("Navball", p, b, r=0.058)
    for nm, u, mat in (("Attitude", -0.175, M["crt_att"]), ("Orbit", 0.175, M["crt_orbit"])):
        p, b = s.at(u, 0.03)
        s.reserve(nm + "CRT", u, 0.02, 0.06, 0.055)
        C.crt(nm, p, b, mat, w=0.115, h=0.085)
    s.reserve("Telelights", 0.0, 0.145, 0.045, 0.01)
    C.lamps("Telelight", [s.at(-0.03 + 0.02 * k, 0.145) for k in range(4)])
    for k, (u, g) in enumerate(((-0.13, "alt"), (0.13, "fuel"))):
        p, b = s.at(u, 0.145)
        s.reserve("TopGauge_" + g, u, 0.145, 0.027, 0.027)
        C.gauge("TopGauge_" + g, p, b, g)
    s.reserve("EventTimer", 0.0, -0.105, 0.045, 0.016)
    p, b = s.at(0.0, -0.105)
    L.box("EventTimer", (0.09, 0.032, 0.008), M["bezel"], p, b, bevel=0.003)
    L.plane("EventTimerDigits", 0.08, 0.022, M["crt_data"], p + b.col[2] * 0.0045, b, (0.05, 0.62, 0.95, 0.78))
    s.reserve("SeqButtons", 0.0, -0.155, 0.06, 0.014)
    C.push_buttons("SeqButton", [s.at(-0.045 + 0.03 * k, -0.155) for k in range(4)])
    s.reserve("Abort", -0.2, -0.13, 0.0375, 0.055)
    p, b = s.at(-0.2, -0.125)
    C.abort_handle("Abort", p, b)
    s.reserve("NamePlate", 0.19, -0.15, 0.06, 0.015)
    p, b = s.at(0.19, -0.15)
    L.plane("NamePlate", 0.12, 0.03, M["plate"], p + b.col[2] * 0.002, b)
    s.reserve("ModeToggles", 0.19, -0.1, 0.05, 0.018)
    C.toggles("ModeToggle", [s.at(0.16 + 0.02 * k, -0.1) for k in range(4)])
    s.reserve("EdgeHazard", 0.0, -0.19, 0.1, 0.008, margin=0.002)
    p, b = s.at(0.0, -0.19)
    L.plane("MDC_Hazard", 0.2, 0.016, M["hazard"], p + b.col[2] * 0.002, b, (0, 0, 1, 0.25))
    s.check()

    # --- right wing (seat over +X): systems - power, fuel, pressures
    s = wings[1]
    for k, g in enumerate(("press", "temp", "fuel")):
        u = -0.13 + 0.13 * k
        p, b = s.at(u, 0.1)
        s.reserve("Gauge_" + g, u, 0.1, 0.03, 0.03)
        C.gauge("WingRGauge_" + g, p, b, g, r=0.026)
    p, b = s.at(0.0, -0.035)
    s.reserve("DataCRT", 0.0, -0.045, 0.06, 0.055)
    C.crt("WingRData", p, b, M["crt_data"], w=0.115, h=0.085)
    s.reserve("Breakers", 0.0, -0.16, 0.11, 0.012)
    C.breakers("WingRBreaker", [s.at(-0.1 + 0.025 * k, -0.16) for k in range(9)])
    s.reserve("TogglesL", -0.16, -0.04, 0.03, 0.03)
    C.toggles("WingRToggleA", [s.at(-0.175 + 0.017 * k, -0.035) for k in range(3)])
    s.reserve("TogglesR", 0.16, -0.04, 0.03, 0.03)
    C.toggles("WingRToggleB", [s.at(0.145 + 0.017 * k, -0.035) for k in range(3)])
    s.check()

    # --- left wing (seat over -X): navigation and comms
    s = wings[-1]
    p, b = s.at(0.0, 0.03)
    s.reserve("Periscope", 0.0, 0.03, 0.06, 0.06)
    C.periscope("WingLPeriscope", p, b, r=0.048)
    for k, (u, g) in enumerate(((-0.15, "alt"), (0.15, "press"))):
        p, b = s.at(u, 0.09)
        s.reserve("Gauge_" + g, u, 0.09, 0.027, 0.027)
        C.gauge("WingLGauge_" + g, p, b, g)
    s.reserve("Comms", -0.15, -0.03, 0.04, 0.03)
    p, b = s.at(-0.15, -0.03)
    L.box("CommsPanel", (0.08, 0.06, 0.006), M["bezel"], p, b, bevel=0.003)
    for k in range(2):
        L.cylinder(f"CommsKnob_{k}", 0.011, 0.012, M["toggle"], p + b.col[0] * (-0.02 + 0.04 * k) + b.col[2] * 0.008, b, segs=16, bevel=0.002)
    s.reserve("Lamps", 0.15, -0.03, 0.04, 0.01)
    C.lamps("WingLLamp", [s.at(0.12 + 0.02 * k, -0.03) for k in range(4)])
    s.reserve("Dimmers", 0.0, -0.12, 0.06, 0.016)
    for k in range(4):
        p, b = s.at(-0.045 + 0.03 * k, -0.12)
        L.cylinder(f"WingLDimmer_{k}", 0.01, 0.012, M["bezel"], p + b.col[2] * 0.006, b, segs=16, bevel=0.002)
        L.box(f"WingLDimmerPtr_{k}", (0.002, 0.01, 0.003), M["toggle"], p + b.col[2] * 0.013 + b.col[1] * 0.003, b)
    s.reserve("Toggles", 0.0, -0.17, 0.1, 0.018)
    C.toggles("WingLToggle", [s.at(-0.085 + 0.017 * k, -0.17) for k in range(11)])
    s.check()


# ------------------------------------------------------------------ side consoles beside the outer couches
def build_side_consoles():
    for side in (1, -1):
        p0, p1 = (SIDE_PHI0, SIDE_PHI1) if side > 0 else (-SIDE_PHI1, -SIDE_PHI0)
        nm = "SideConsoleR" if side > 0 else "SideConsoleL"
        band = C.Band(nm, p0, p1, SIDE_Z0, SIDE_Z1, 0.07)
        band.build(M["console"])
        for z in (SIDE_Z0, SIDE_Z1):     # end cheeks
            pass
        mid = math.degrees((p0 + p1) / 2)
        zc = (SIDE_Z0 + SIDE_Z1) / 2
        # breaker grid (upper), toggle row, a gauge pair and a placard
        rows = [(zc + 0.11, "Breakers"), (zc + 0.05, "Breakers2")]
        for z, key in rows:
            band.reserve(nm + key, mid, z, 0.21, 0.012)
            C.breakers(nm + key, [band.at(0.025 * (k - 8), z, centre_deg=mid) for k in range(17)])
        band.reserve(nm + "Toggles", mid - side * 8, zc - 0.035, 0.1, 0.02)
        C.toggles(nm + "Toggle", [band.at(0.018 * (k - 5), zc - 0.035, centre_deg=mid - side * 8) for k in range(11)])
        for k, g in enumerate(("temp", "press")):
            d = mid + side * 10 + k * 7 * side
            p, b = C.frame_at(C.rad(d), zc - 0.035, 0.082)
            band.reserve(nm + "Gauge" + g, d, zc - 0.035, 0.024, 0.024)
            C.gauge(f"{nm}Gauge_{g}", p, b, g, r=0.02)
        band.reserve(nm + "Plate", mid, zc - 0.12, 0.06, 0.015)
        p, b = C.frame_at(C.rad(mid), zc - 0.12, 0.082)
        L.plane(nm + "Plate", 0.12, 0.03, M["plate"], p + b.col[2] * 0.002, b)
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
build_ceiling()
for i, seat in enumerate(SEATS):
    C.eye_marker(i, seat)
C.reference_kerbals(os.path.join(os.environ.get("IVA_REFERENCE", "C:/Games/KSP2Mods/reference"), "poses", SPEC["part"] + ".obj"), SPEC["hull_base_y"])
print(f"eyes at z {EYE_Z:.3f}; console {MDC_Z - EYE_Z:.3f} m above the eyes")
L.save(OUT)
