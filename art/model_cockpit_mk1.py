"""Mk1 cockpit (cockpit_1v_m1_crew): a single-seat flight deck in the stock layout, finished in the style of the Space
Shuttle era (grey switch panels with white legends, square glass displays, a dark glareshield, blue seat cushions, cream
padded walls with velcro patches).

Usage: blender -b --python model_cockpit_mk1.py -- <spec.json> <texture_dir> <out.blend>

Generator space as everywhere: Blender (x, y, z) = Unity part (x, z, y - hull_base_y). For this cockpit that means the
nose is +Z, the canopy is -Y (the pilot's "up") and the floor is +Y. The pilot's eye is the stock IVA EyeTransform.
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
import capsule as C  # noqa: E402
import modules as G  # noqa: E402
G.materials()
M = L.M
import stock as S  # noqa: E402
S.materials()
import props as P  # noqa: E402
P.materials()
import cabin as K  # noqa: E402
import hullshell as HS  # noqa: E402

# shuttle-era finishes
M["console"] = L.material("IVA_ShuttlePanel", tex="shuttle_panel_color.png", normal="panel_normal.png", rough=0.6, metal=0.2, normal_strength=0.4)
M["module"] = M["console"]
M["wall_cream"] = L.material("IVA_WallCream", tex="wall_cream_color.png", normal="wall_cream_normal.png", rough=0.8, metal=0.0, normal_strength=0.9)
M["glare"] = L.material("IVA_Glareshield", (0.045, 0.046, 0.05), rough=0.85)
M["seat_blue"] = L.material("IVA_SeatBlue", (0.10, 0.17, 0.42), rough=0.9, normal="canvas_normal.png", uv_scale=(5.0, 5.0), normal_strength=0.8)
M["rubber"] = L.material("IVA_Rubber", (0.05, 0.05, 0.055), rough=0.75)
M["velcro"] = L.material("IVA_Velcro", (0.38, 0.55, 0.78), rough=1.0)
M["hud_glass"] = L.material("IVA_HudGlass", (0.35, 0.55, 0.45), rough=0.05, metal=0.0)
M["tank"] = L.material("IVA_O2Bottle", (0.22, 0.42, 0.30), rough=0.35, metal=0.4)
M["deckplate"] = L.material("IVA_DeckPlate", tex="deckplate_color.png", normal="deckplate_normal.png", rough=0.6, metal=0.35, normal_strength=0.8)

C.setup(SPEC, wall=SPEC["wall"], ceil=SPEC["ceiling"], top=2.06)
EYE = Vector(SPEC["pose"]["seats"][0]["eye"])
FLOOR_Y = 0.33                     # the deck (belly side)
Z_BACK, Z_FRONT = 0.02, 2.08       # cabin length along the nose axis


def basis(right, up):
    right, up = Vector(right).normalized(), Vector(up)
    up = (up - up.project(right)).normalized()
    return L.basis(right, up, right.cross(up).normalized())


# ------------------------------------------------------------------ shell from the real exterior, with the windows open
def build_shell():
    HS.build("Shell", SPEC["exterior"], SPEC["hull_base_y"], Z_BACK, Z_FRONT, wall=SPEC["wall"], dz=0.01, seg=220, wells=True, bezel=0.06,
             centre=(0.0, -0.02), mat=M["wall_cream"], frame_mat=M["frame_dark"])
    S.cbox("Deck", (0.80, 0.03, Z_FRONT - 0.12), M["deckplate"], Vector((0.0, FLOOR_Y + 0.015, (Z_FRONT + 0.08) / 2)), ch=0.0)


# ------------------------------------------------------------------ main panel, glareshield beam
# The nose narrows fast (inner half-width ~0.30 m at the panel top), so the panel sits back at z ~1.47 with its top just
# under eye level, and the glareshield is a beam along the panel top carrying the warning strip, facing the pilot.
PANEL_C = Vector((0.0, -0.03, 1.47))
PANEL_UP = Vector((0.0, -1.0, 0.35))


def build_front():
    s = C.Surface("MainPanel", PANEL_C, (1, 0, 0), PANEL_UP, 0.52, 0.30, corner=0.03)
    s.build(M["console"], thick=0.03)
    G.grid(s, "Main", 6, 3, [
        ("annunciators", 0, 0, 2, 1, {"cols": 4, "rows": 2}), ("dial", 2, 0, 1, 1, {"kind": "alt"}), ("dial", 3, 0, 1, 1, {"kind": "press"}),
        ("annunciators", 4, 0, 2, 1, {"cols": 4, "rows": 2, "start": 8}),
        ("mfd", 0, 1, 2, 2, {"screen": "mfd_map"}), ("navball", 2, 1, 2, 2, {}), ("mfd", 4, 1, 2, 2, {"screen": "mfd_systems"}),
    ], border=0.012)
    s.check()
    G.housing(s, "MainPanel", depth=0.05)
    # glareshield beam: sits on the panel top and reaches back towards the pilot; its face carries the eyebrow strip
    up = s.up.normalized()
    top = PANEL_C + up * (s.h / 2)
    beam_c = Vector((0.0, top.y - 0.035, top.z - 0.035))
    S.cbox("Glareshield", (0.48, 0.06, 0.11), M["glare"], beam_c, ch=0.012)
    S.cbox("GlareshieldCap", (0.50, 0.012, 0.13), M["glare"], beam_c + Vector((0, -0.034, 0.0)), ch=0.005)
    face = beam_c + Vector((0, 0, -0.056))
    eb = C.Surface("Eyebrow", face, (1, 0, 0), (0, -1, 0), 0.44, 0.048, corner=0.006)
    eb.build(M["console"], thick=0.008, rim=False)
    G.grid(eb, "Eyebrow", 10, 1, [("buttons", 0, 0, 1, 1, {"n": 1}), ("annunciators", 1, 0, 8, 1, {"cols": 8, "rows": 1, "start": 3}),
                                  ("buttons", 9, 0, 1, 1, {"n": 1})], border=0.004, gap=0.003)
    eb.check()
    return s


# ------------------------------------------------------------------ centre pedestal below the panel, between the knees
def build_pedestal():
    S.cbox("Pedestal", (0.28, 0.20, 0.16), M["frame"], Vector((0.0, FLOOR_Y - 0.10, 1.545)), ch=0.015)
    face_up = Vector((0.0, -0.6, 0.8))
    s = C.Surface("PedestalFace", (0.0, 0.225, 1.385), (1, 0, 0), face_up, 0.26, 0.17, corner=0.012)
    s.build(M["console"], thick=0.02)
    G.grid(s, "Ped", 2, 1, [("keypad", 0, 0, 1, 1, {}), ("mfd", 1, 0, 1, 1, {"screen": "mfd_engine"})], border=0.008)
    s.check()
    S.cbox("PedestalKick", (0.26, 0.06, 0.11), M["frame_dark"], Vector((0.0, FLOOR_Y - 0.03, 1.415)), ch=0.008)


# ------------------------------------------------------------------ hand controller and rudder pedals
def build_controls():
    base = Vector((0.0, FLOOR_Y, 1.17))
    S.cbox("RhcBox", (0.10, 0.12, 0.12), M["frame_dark"], base + Vector((0, -0.06, 0)), ch=0.01)
    L.cylinder("RhcBoot", 0.035, 0.06, M["rubber"], base + Vector((0, -0.15, 0)), basis((1, 0, 0), (0, 0, 1)), segs=16, radius2=0.025)
    grip = [base + Vector((0, -0.18, 0)), base + Vector((0, -0.28, 0.01)), base + Vector((0, -0.33, -0.01))]
    L.tube("RhcGrip", grip, 0.022, M["rubber"])
    L.cylinder("RhcButton", 0.008, 0.01, M["red"], base + Vector((0.0, -0.345, 0.0)), basis((1, 0, 0), (0, 0, 1)), segs=10)
    for sx in (-1, 1):   # rudder pedals on their rails
        q = Vector((sx * 0.12, 0.17, 1.10))
        L.box(f"Pedal{sx}", (0.08, 0.15, 0.02), M["frame_dark"], q, basis((1, 0, 0), (0, -1, 0.35)), bevel=0.004)
        L.box(f"PedalStrap{sx}", (0.085, 0.02, 0.025), M["strap"], q + Vector((0, -0.03, -0.012)), basis((1, 0, 0), (0, -1, 0.35)), bevel=0.003)
        L.tube(f"PedalRail{sx}", [Vector((sx * 0.12, FLOOR_Y - 0.01, 1.0)), Vector((sx * 0.12, FLOOR_Y - 0.01, 1.22))], 0.008, M["frame"])


# ------------------------------------------------------------------ side consoles: throttle quadrant left, comms right
# They stop at z 1.19: further forward the hull is narrower than the consoles.
SC_Z0, SC_Z1, SC_X, SC_W = 0.71, 1.19, 0.37, 0.15


def build_side_consoles():
    zc, ln = (SC_Z0 + SC_Z1) / 2, SC_Z1 - SC_Z0
    for side in (-1, 1):
        x = side * SC_X
        # upper box full width; the plinth under it is inset from the hull side, which narrows towards the floor
        S.cbox(f"SideConsole{side}", (SC_W, 0.14, ln), M["frame"], Vector((x, 0.14, zc)), ch=0.012)
        S.cbox(f"SideConsolePlinth{side}", (SC_W - 0.08, 0.125, ln), M["frame"], Vector((x - side * 0.04, 0.2725, zc)), ch=0.01)
        s = C.Surface(f"SideTop{side}", (x, 0.068, zc), (1, 0, 0), (0, 0, 1), SC_W - 0.01, ln - 0.02, corner=0.01)
        s.build(M["console"], thick=0.015, rim=False)
        if side < 0:   # row 1 is left clear for the throttle quadrant
            items = [("toggles", 0, 0, 1, 1, {"cols": 3}), ("annunciators", 0, 2, 1, 1, {"cols": 2, "rows": 3, "start": 5}),
                     ("breakers", 0, 3, 1, 1, {"cols": 4, "rows": 2})]
        else:
            items = [("keypad", 0, 0, 1, 1, {}), ("toggles", 0, 1, 1, 1, {"cols": 3}), ("knobs", 0, 2, 1, 1, {"n": 2}),
                     ("breakers", 0, 3, 1, 1, {"cols": 4, "rows": 2})]
        G.grid(s, f"Side{side}", 1, 4, items, border=0.008)
        s.check()
        # the inner face, towards the pilot's legs: a second switch panel, like the orbiter's side walls
        f = C.Surface(f"SideFace{side}", (x - side * (SC_W / 2 + 0.001), 0.20, zc), (0, 0, -side), (0, -1, 0), ln - 0.08, 0.2, corner=0.01)
        f.build(M["console"], thick=0.012)
        G.grid(f, f"SideFace{side}", 3, 2, [("breakers", 0, 0, 2, 1, {"cols": 6, "rows": 2}), ("toggles", 2, 0, 1, 1, {"cols": 3}),
                                            ("vent", 0, 1, 1, 1, {"slots": 4}), ("lamps", 1, 1, 1, 1, {"n": 3}), ("knobs", 2, 1, 1, 1, {"n": 2})],
               border=0.01)
        f.check()
    # throttle quadrant in the left console's second row
    rh = (ln - 0.02 - 2 * 0.008) / 4
    q = Vector((-SC_X, 0.055, zc + (ln - 0.02) / 2 - 0.008 - rh * 1.5))
    S.cbox("ThrottleSlot", (0.11, 0.012, 0.11), M["frame_dark"], q, ch=0.004)
    for k, dx in enumerate((-0.025, 0.025)):
        L.tube(f"ThrottleLever{k}", [q + Vector((dx, 0, -0.02)), q + Vector((dx, -0.09, 0.0))], 0.006, M["toggle"])
        L.box(f"ThrottleHandle{k}", (0.03, 0.022, 0.03), M["rubber"], q + Vector((dx, -0.1, 0.0)), bevel=0.006)


# ------------------------------------------------------------------ seat: shuttle-style, blue cushions on a dark frame
def build_seat():
    """Shuttle-style seat: a frame of two side rails and a back plate, segmented blue cushions, a winged headrest,
    armrests with grips, a harness, and the yellow-and-black seat handles."""
    zb = 0.58                                   # back plane at the cushion face
    back = basis((-1, 0, 0), (0, -1, -0.10))     # leaning back a little; normal +Z, towards the panel
    up = back.col[1]
    origin = Vector((0.0, FLOOR_Y - 0.04, zb))  # bottom of the back
    S.cbox("SeatPlinth", (0.30, 0.06, 0.34), M["frame_dark"], Vector((0, FLOOR_Y - 0.03, 0.78)), ch=0.012)
    S.cbox("SeatBackPlate", (0.40, 0.66, 0.025), M["frame_dark"], origin + up * 0.33 - back.col[2] * 0.03, back, ch=0.006)
    for sx in (-1, 1):   # side rails up the back, with lightening slots, and the armrests
        rail = origin + Vector((sx * 0.215, 0, 0)) + up * 0.31 - back.col[2] * 0.01
        S.cbox(f"SeatRail{sx}", (0.04, 0.64, 0.08), M["frame"], rail, back, ch=0.008)
        for k in range(3):
            S.cbox(f"SeatRailSlot{sx}{k}", (0.042, 0.1, 0.03), M["frame_dark"], rail + up * (-0.18 + k * 0.17) + back.col[2] * 0.03, back, ch=0.006)
        arm = Vector((sx * 0.215, FLOOR_Y - 0.17, 0.80))
        S.cbox(f"Armrest{sx}", (0.05, 0.035, 0.30), M["frame"], arm, ch=0.008)
        S.cbox(f"ArmPad{sx}", (0.045, 0.02, 0.24), M["seat_blue"], arm + Vector((0, -0.026, 0.0)), ch=0.008)
        S.cbox(f"ArmPost{sx}", (0.04, 0.14, 0.04), M["frame"], arm + Vector((0, 0.09, 0.08)), ch=0.006)
        L.tube(f"SeatHandle{sx}", [arm + Vector((sx * 0.02, 0.0, 0.12)), arm + Vector((sx * 0.02, -0.05, 0.15)), arm + Vector((sx * 0.02, -0.05, 0.22))],
               0.008, M["yellow"])
    for k in range(3):   # back cushions, stacked
        S.cbox(f"SeatBackCushion{k}", (0.34, 0.165, 0.06), M["seat_blue"], origin + up * (0.10 + k * 0.175) + back.col[2] * 0.0, back, ch=0.022)
    for k, dz in enumerate((0.0, 0.17)):   # pan cushions
        S.cbox(f"SeatPanCushion{k}", (0.34, 0.06, 0.16), M["seat_blue"], Vector((0, FLOOR_Y - 0.09, 0.69 + dz)), ch=0.022)
    # winged headrest
    hr = origin + up * 0.72 + back.col[2] * 0.02
    S.cbox("Headrest", (0.20, 0.13, 0.07), M["seat_blue"], hr, back, ch=0.025)
    for sx in (-1, 1):
        S.cbox(f"HeadrestWing{sx}", (0.06, 0.13, 0.08), M["seat_blue"], hr + Vector((sx * 0.12, 0, 0)) + back.col[2] * 0.03,
               back @ Matrix.Rotation(-sx * 0.35, 3, "Y"), ch=0.022)
    S.cbox("HeadrestBack", (0.30, 0.15, 0.03), M["frame_dark"], hr - back.col[2] * 0.05, back, ch=0.006)
    for sx in (-1, 1):   # shoulder harness
        L.box(f"Harness{sx}", (0.045, 0.46, 0.006), M["strap"], origin + Vector((sx * 0.09, 0, 0)) + up * 0.3 + back.col[2] * 0.034, back)
    L.box("LapBelt", (0.34, 0.045, 0.006), M["strap"], Vector((0, FLOOR_Y - 0.125, 0.72)), basis((1, 0, 0), (0, 0, 1)))
    L.cylinder("HarnessBuckle", 0.03, 0.01, M["buckle"], Vector((0, FLOOR_Y - 0.13, 0.72)), basis((1, 0, 0), (0, 0, 1)), segs=16)
    L.tube("EjectLoop", [Vector((-0.05, FLOOR_Y - 0.12, 1.0)), Vector((-0.05, FLOOR_Y - 0.17, 1.04)), Vector((0.05, FLOOR_Y - 0.17, 1.04)),
                         Vector((0.05, FLOOR_Y - 0.12, 1.0))], 0.008, M["yellow"])


# ------------------------------------------------------------------ behind the seat: avionics bay, stowage, safety kit
def build_aft():
    hz = Vector((0.0, -0.08, Z_BACK + 0.035))
    ring = [hz + Vector((math.cos(2 * math.pi * j / 48), math.sin(2 * math.pi * j / 48), 0)) * 0.27 for j in range(48)]
    S.sweep("AftHatchRing", ring, [Vector((0, 0, 1))] * 48, S.chamfer_rect(0.07, 0.04, 0.01), M["frame"], closed=True)
    L.cylinder("AftHatchDoor", 0.24, 0.035, M["hatch"], hz + Vector((0, 0, 0.012)), segs=48, bevel=0.006)
    L.torus("AftHatchRim", 0.17, 0.01, M["frame"], hz + Vector((0, 0, 0.032)), Matrix.Identity(3), seg=40, mseg=8)
    L.tube("AftHatchHandle", [hz + Vector((-0.08, 0.0, 0.03)), hz + Vector((-0.08, 0.0, 0.07)), hz + Vector((0.08, 0.0, 0.07)), hz + Vector((0.08, 0.0, 0.03))],
           0.01, M["yellow"])
    for k in range(6):
        a_ = 2 * math.pi * (k + 0.5) / 6
        S.cbox(f"AftHatchDog{k}", (0.04, 0.02, 0.014), M["yellow"], hz + Vector((math.cos(a_), math.sin(a_), 0)) * 0.215 + Vector((0, 0, 0.034)),
               Matrix.Rotation(a_, 3, "Z"), ch=0.003)
    for sx in (-1, 1):
        s = C.Surface(f"AftPanel{sx}", (sx * 0.38, -0.05, Z_BACK + 0.03), (-1, 0, 0), (0, -1, 0), 0.16, 0.34, corner=0.012)
        s.build(M["console"], thick=0.02)
        G.grid(s, f"Aft{sx}", 1, 3, [("breakers", 0, 0, 1, 1, {"cols": 4, "rows": 3}), ("annunciators", 0, 1, 1, 1, {"cols": 2, "rows": 2}),
                                     ("toggles", 0, 2, 1, 1, {"cols": 3})], border=0.008)
        s.check()
    for k, (x, z) in enumerate(((-0.17, 0.30), (0.17, 0.30))):   # stowage bags under and behind the seat
        P.cargo_bag(f"StowBag{k}", Vector((x, FLOOR_Y - 0.002, z)), basis((1, 0, 0), (0, 0, 1)), 0.26, 0.24, 0.16)
    upright = Matrix.Rotation(math.pi / 2, 3, "X")   # cylinder axis along the pilot's up/down
    L.cylinder("Extinguisher", 0.04, 0.3, M["red"], Vector((0.46, 0.0, 0.42)), upright, segs=20, bevel=0.01)
    L.cylinder("O2Bottle", 0.045, 0.32, M["tank"], Vector((-0.46, 0.02, 0.42)), upright, segs=20, bevel=0.012)
    for sx in (-1, 1):   # yellow grab bars along the canopy sills, below the side-window frames, on standoffs off the wall
        zs = [0.55 + 0.75 * k / 10 for k in range(11)]
        pts = [HS.inner((0, -0.08, z), (sx, 0, 0), gap=0.045) for z in zs]
        L.tube(f"SillBar{sx}", pts, 0.012, M["yellow"])
        for k in (0, 7, 10):
            L.tube(f"SillBarFoot{sx}{k}", [pts[k], HS.inner((0, -0.08, zs[k]), (sx, 0, 0), gap=0.002)], 0.008, M["frame"])
    # cable runs along the walls, clipped just off the shell
    for sx in (-1, 1):
        run = [HS.inner((0, -0.03, 0.22 + 0.33 * k / 4), (sx, 0, 0), gap=0.016) for k in range(5)]
        S.bundle(f"SillCables{sx}", run + [Vector((sx * 0.43, 0.06, 0.62)), Vector((sx * 0.41, 0.12, 0.66)), Vector((sx * 0.41, 0.12, 0.69))],
                 n=3, r=0.008)   # down into the back of the side console


def build_velcro():
    """Velcro strips on the side walls, where checklists and pens get stuck down."""
    for sx in (-1, 1):
        for k, (y, z) in enumerate(((0.0, 0.45), (-0.2, 0.35))):
            fr = HS.wall_frame((0.0, y, z), (sx, 0, 0), 0.004, up=(0, -1, 0))
            if fr:
                P.velcro(f"WallVelcro{sx}{k}", fr[0], fr[1], w=0.12, h=0.04)


def build_lights_and_markers():
    S.light_fixture("DomeLight", Vector((0.0, -0.55, 0.45)), basis((1, 0, 0), (0, 0, 1)), w=0.16, h=0.06)
    K.view("Windscreen", (0.0, -0.30, 1.30), (0.0, -0.45, 2.4))
    K.view("Left", (-0.25, -0.25, 1.0), (-1.2, -0.6, 1.0))
    K.view("Right", (0.25, -0.25, 1.0), (1.2, -0.6, 1.0))
    for i, seat in enumerate(SPEC["pose"]["seats"]):
        C.eye_marker(i, seat)


build_shell()
build_front()
build_pedestal()
build_controls()
build_side_consoles()
build_seat()
build_aft()
build_velcro()
build_lights_and_markers()
S.collision_markers(hatches=[("Aft", (0.0, 0.0, Z_BACK + 0.25))])
import surfaces  # noqa: E402  (detail textures on plain painted, brushed and fabric materials)
if not os.environ.get("IVA_NO_DETAIL"):
    surfaces.apply()
L.save(OUT)
