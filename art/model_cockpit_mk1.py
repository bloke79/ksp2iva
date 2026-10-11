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
    HS.build("Shell", SPEC["exterior"], SPEC["hull_base_y"], Z_BACK, Z_FRONT, wall=SPEC["wall"], dz=0.015, seg=160,
             centre=(0.0, -0.02), mat=M["wall_cream"], frame_mat=M["frame_dark"])
    S.cbox("Deck", (0.80, 0.03, Z_FRONT - 0.12), M["deckplate"], Vector((0.0, FLOOR_Y + 0.015, (Z_FRONT + 0.08) / 2)), ch=0.0)


# ------------------------------------------------------------------ glareshield, main panel, eyebrow, HUD
PANEL_C = Vector((0.0, -0.03, 1.60))
PANEL_UP = Vector((0.0, -1.0, 0.38))


def build_front():
    s = C.Surface("MainPanel", PANEL_C, (1, 0, 0), PANEL_UP, 0.58, 0.38, corner=0.02)
    s.build(M["console"], thick=0.03)
    G.grid(s, "Main", 6, 4, [
        ("annunciators", 0, 0, 2, 1, {"cols": 4, "rows": 2}), ("dial", 2, 0, 1, 1, {"kind": "alt"}), ("dial", 3, 0, 1, 1, {"kind": "press"}),
        ("annunciators", 4, 0, 2, 1, {"cols": 4, "rows": 2, "start": 8}),
        ("mfd", 0, 1, 2, 2, {"screen": "mfd_map"}), ("navball", 2, 1, 2, 2, {}), ("mfd", 4, 1, 2, 2, {"screen": "mfd_systems"}),
        ("toggles", 0, 3, 2, 1, {"cols": 5}), ("knobs", 2, 3, 2, 1, {"n": 4}), ("toggles", 4, 3, 2, 1, {"cols": 5}),
    ], border=0.012)
    s.check()
    G.housing(s, "MainPanel", depth=0.1)
    # glareshield: a dark hood over the panel with the eyebrow strip on its lip
    top = PANEL_C + s.up * (s.h / 2)
    hood = top + Vector((0, -0.018, -0.05))
    S.cbox("Glareshield", (0.64, 0.036, 0.20), M["glare"], hood + Vector((0, 0, 0.04)), ch=0.012)
    S.cbox("GlareshieldLip", (0.66, 0.05, 0.03), M["glare"], hood + Vector((0, 0.005, -0.06)), ch=0.012)
    eb = C.Surface("Eyebrow", hood + Vector((0, 0.03, -0.076)), (1, 0, 0), (0, -1, 0.1), 0.5, 0.045, corner=0.006)
    eb.build(M["console"], thick=0.012)
    G.grid(eb, "Eyebrow", 6, 1, [("buttons", 0, 0, 1, 1, {"n": 1}), ("annunciators", 1, 0, 4, 1, {"cols": 8, "rows": 1, "start": 3}),
                                 ("buttons", 5, 0, 1, 1, {"n": 1})], border=0.004, gap=0.003)
    for sx in (-1, 1):   # master alarm: red push-lights at each end
        L.box(f"MasterAlarm{sx}", (0.034, 0.024, 0.012), M["red"], hood + Vector((sx * 0.22, 0.03, -0.088)), bevel=0.003)
    # HUD combiner on the hood centre
    hq = hood + Vector((0, -0.04, -0.02))
    for sx in (-1, 1):
        L.tube(f"HudPost{sx}", [hq + Vector((sx * 0.065, 0.0, 0.0)), hq + Vector((sx * 0.065, -0.09, -0.03))], 0.005, M["frame_dark"])
    L.plane("HudGlass", 0.12, 0.08, M["hud_glass"], hq + Vector((0, -0.05, -0.02)), basis((1, 0, 0), (0, -1, -0.45)))
    S.cbox("HudBase", (0.17, 0.02, 0.06), M["glare"], hq + Vector((0, 0.005, 0.0)), ch=0.005)
    # panel floodlights under the hood
    for sx in (-1, 1):
        L.cylinder(f"Floodlight{sx}", 0.012, 0.03, M["light"], hood + Vector((sx * 0.27, 0.025, -0.02)), basis((1, 0, 0), (0, 0, 1)), segs=10)
    return s


# ------------------------------------------------------------------ centre pedestal with the keyboard, between the knees
def build_pedestal():
    S.cbox("Pedestal", (0.30, FLOOR_Y + 0.02, 0.26), M["frame"], Vector((0.0, (FLOOR_Y + 0.0) / 2 + 0.03, 1.60)), ch=0.015)
    s = C.Surface("PedestalFace", (0.0, 0.10, 1.465), (1, 0, 0), (0, -1, 0.22), 0.27, 0.22, corner=0.012)
    s.build(M["console"], thick=0.02)
    G.grid(s, "Ped", 2, 2, [("keypad", 0, 0, 1, 2, {}), ("mfd", 1, 0, 1, 1, {"screen": "mfd_engine"}), ("toggles", 1, 1, 1, 1, {"cols": 3})], border=0.008)
    s.check()


# ------------------------------------------------------------------ hand controller and rudder pedals
def build_controls():
    base = Vector((0.0, FLOOR_Y, 1.30))
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
def build_side_consoles():
    for side in (-1, 1):
        x = side * 0.40
        S.cbox(f"SideConsole{side}", (0.16, 0.26, 0.82), M["frame"], Vector((x, 0.20, 1.12)), ch=0.012)
        s = C.Surface(f"SideTop{side}", (x, 0.068, 1.12), (1, 0, 0), (0, 0, 1), 0.15, 0.80, corner=0.01)
        s.build(M["console"], thick=0.015)
        if side < 0:
            items = [("toggles", 0, 0, 1, 1, {"cols": 3}), ("annunciators", 0, 1, 1, 1, {"cols": 2, "rows": 3, "start": 5}),
                     ("breakers", 0, 3, 1, 1, {"cols": 4, "rows": 2}), ("knobs", 0, 4, 1, 1, {"n": 2})]
        else:
            items = [("keypad", 0, 0, 1, 1, {}), ("toggles", 0, 1, 1, 1, {"cols": 3}), ("knobs", 0, 2, 1, 1, {"n": 2}),
                     ("breakers", 0, 3, 1, 1, {"cols": 4, "rows": 2}), ("toggles", 0, 4, 1, 1, {"cols": 3})]
        G.grid(s, f"Side{side}", 1, 5, items, border=0.008)
        s.check()
        # the inner face, towards the pilot's legs: a second switch panel and a stowage net, like the orbiter's side walls
        f = C.Surface(f"SideFace{side}", (x - side * 0.081, 0.20, 1.12), (0, 0, -side), (0, -1, 0), 0.74, 0.2, corner=0.01)
        f.build(M["console"], thick=0.012)
        G.grid(f, f"SideFace{side}", 4, 2, [("breakers", 0, 0, 2, 1, {"cols": 8, "rows": 2}), ("toggles", 2, 0, 2, 1, {"cols": 6}),
                                            ("vent", 0, 1, 1, 1, {"slots": 5}), ("lamps", 1, 1, 1, 1, {"n": 3}), ("knobs", 2, 1, 2, 1, {"n": 4})],
               border=0.01)
        f.check()
    # throttle quadrant in the left console's middle row
    q = Vector((-0.40, 0.055, 1.12))
    S.cbox("ThrottleSlot", (0.11, 0.012, 0.15), M["frame_dark"], q, ch=0.004)
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
        P.cargo_bag(f"StowBag{k}", Vector((x, FLOOR_Y, z)), basis((1, 0, 0), (0, 0, -1)), 0.26, 0.24, 0.16)
    upright = Matrix.Rotation(math.pi / 2, 3, "X")   # cylinder axis along the pilot's up/down
    L.cylinder("Extinguisher", 0.04, 0.3, M["red"], Vector((0.46, 0.0, 0.42)), upright, segs=20, bevel=0.01)
    L.cylinder("O2Bottle", 0.045, 0.32, M["tank"], Vector((-0.46, 0.02, 0.42)), upright, segs=20, bevel=0.012)
    for sx in (-1, 1):   # hazard-striped grab bars along the canopy sills (the stock touch)
        L.tube(f"SillBar{sx}", [Vector((sx * 0.47, -0.18, 0.55)), Vector((sx * 0.44, -0.20, 0.62)), Vector((sx * 0.44, -0.20, 1.30)),
                                Vector((sx * 0.47, -0.18, 1.36))], 0.012, M["yellow"])
    # cable runs along the sills
    for sx in (-1, 1):
        S.bundle(f"SillCables{sx}", [Vector((sx * 0.5, -0.05, 0.1)), Vector((sx * 0.52, -0.06, 0.8)), Vector((sx * 0.5, -0.08, 1.5))], n=3, r=0.008)


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
build_lights_and_markers()
S.collision_markers(hatches=[("Aft", (0.0, 0.0, Z_BACK + 0.25))])
L.save(OUT)
