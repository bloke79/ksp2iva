"""Mk3 cockpit (cockpit_3v_m3_crew): the Space Shuttle orbiter's crew compartment in the Mk1 cockpit's design language.

Flight deck (the stock layout): commander and pilot side by side at a three-section main panel under a glareshield
button beam, centre console between them, side consoles, hand controllers and pedals, an overhead switch panel, two
mission-specialist seats behind, an aft station under the overhead aft windows, and a round floor hatch down to the
mid-deck. Mid-deck (free-float): ladder, toilet booth, galley, round side hatch, two sleep stations, ergometer, a
forward wall of lockers and the hatch aft to the fuselage.

Usage: blender -b --python model_cockpit_mk3.py -- <spec.json> <texture_dir> <out.blend>

Generator space: Blender (x, y, z) = Unity part (x, z, y - hull_base_y). The nose is +Z, "up" is -Y, starboard is +X.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ivalib as L  # noqa: E402  (imports bpy first)
import bmesh  # noqa: E402
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

# shuttle-era finishes (as the Mk1 cockpit)
M["console"] = L.material("IVA_ShuttlePanel", tex="shuttle_panel_color.png", normal="panel_normal.png", rough=0.6, metal=0.2, normal_strength=0.4)
M["module"] = M["console"]
M["wall_cream"] = L.material("IVA_WallCream", tex="wall_cream_color.png", normal="wall_cream_normal.png", rough=0.8, metal=0.0, normal_strength=0.9)
M["glare"] = L.material("IVA_Glareshield", (0.045, 0.046, 0.05), rough=0.85)
M["seat_blue"] = L.material("IVA_SeatBlue", (0.10, 0.17, 0.42), rough=0.9, normal="canvas_normal.png", uv_scale=(5.0, 5.0), normal_strength=0.8)
M["rubber"] = L.material("IVA_Rubber", (0.05, 0.05, 0.055), rough=0.75)
M["velcro"] = L.material("IVA_Velcro", (0.38, 0.55, 0.78), rough=1.0)
M["tank"] = L.material("IVA_O2Bottle", (0.22, 0.42, 0.30), rough=0.35, metal=0.4)
M["deckplate"] = L.material("IVA_DeckPlate", tex="deckplate_color.png", normal="deckplate_normal.png", rough=0.6, metal=0.35, normal_strength=0.8)

C.setup(SPEC, wall=SPEC["wall"], ceil=SPEC["ceiling"], top=SPEC["ceiling"] + 0.05)
EYES = [Vector(s["eye"]) for s in SPEC["pose"]["seats"]]
FLOOR_Y = -0.45                    # flight-deck floor (top of the deck plates)
DECK_T = 0.06                      # flight-deck floor thickness: its underside is the mid-deck ceiling
MID_Y = 1.30                       # mid-deck floor
Z_BACK, Z_FRONT = 0.10, 2.45       # aft bulkhead, forward bulkhead (the shell's end caps)
HATCH = Vector((-1.0, FLOOR_Y, 0.42))   # interdeck hatch, port aft
HATCH_R = 0.27


def basis(right, up):
    right, up = Vector(right).normalized(), Vector(up)
    up = (up - up.project(right)).normalized()
    return L.basis(right, up, right.cross(up).normalized())


def half_width(y, z, gap=0.0):
    """Inner half-width of the hull at height y, station z (towards starboard; the hull is symmetric)."""
    p = HS.inner((0.0, y, z), (1, 0, 0), gap)
    return p.x if p is not None else 0.0


PORT = basis((0, 0, 1), (0, -1, 0))     # on the port wall facing in: right is forward
STBD = basis((0, 0, -1), (0, -1, 0))    # on the starboard wall facing in
AFT_WALL = basis((-1, 0, 0), (0, -1, 0))  # on the aft bulkhead facing forward
FWD_WALL = basis((1, 0, 0), (0, -1, 0))   # on the forward bulkhead facing aft


# ------------------------------------------------------------------ shell and decks
def slab(name, y_top, thick, z0, z1, mat, holes=(), cell=0.05, margin=0.004):
    """A deck plate across the hull at height y_top (top face), fitted to the hull at its top and bottom faces,
    with round holes (centre x, z, radius) left open. Built as strips along x, one per z step."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    nz = max(1, int(round((z1 - z0) / cell)))
    for i in range(nz):
        za, zb = z0 + (z1 - z0) * i / nz, z0 + (z1 - z0) * (i + 1) / nz
        hw = min(half_width(y, z, margin) for y in (y_top, y_top + thick) for z in (za, zb))
        if hw <= 0.05:
            continue
        nx = max(1, int(round(2 * hw / cell)))
        xs = [-hw + 2 * hw * k / nx for k in range(nx + 1)]
        for k in range(nx):
            xm, zm = (xs[k] + xs[k + 1]) / 2, (za + zb) / 2
            if any(math.hypot(xm - hx, zm - hz) < hr for hx, hz, hr in holes):
                continue
            vs = [bm.verts.new((xs[k], y_top, za)), bm.verts.new((xs[k + 1], y_top, za)),
                  bm.verts.new((xs[k + 1], y_top, zb)), bm.verts.new((xs[k], y_top, zb))]
            f = bm.faces.new(vs)
            for l in f.loops:
                l[uv].uv = (l.vert.co.x * 0.8, l.vert.co.z * 0.8)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.normal_update()
    for f in bm.faces:
        if f.normal.y > 0:
            f.normal_flip()          # top face up (-Y)
    o = L.mesh_obj(name, bm, [mat])
    L.solidify(o, thick, offset=-1.0)
    return o


def build_shell():
    HS.build("Shell", SPEC["exterior"], SPEC["hull_base_y"], Z_BACK, Z_FRONT, wall=SPEC["wall"], dz=0.01, seg=520, wells=True,
             centre=tuple(SPEC["shell_centre"]), mat=M["wall_cream"], frame_mat=M["frame_dark"])
    holes = [(HATCH.x, HATCH.z, HATCH_R + 0.005)]
    slab("FlightDeck", FLOOR_Y, DECK_T, Z_BACK + 0.005, Z_FRONT - 0.005, M["deckplate"], holes)
    slab("MidDeckCeiling", FLOOR_Y + DECK_T, 0.015, Z_BACK + 0.005, Z_FRONT - 0.005, M["wall_cream"], holes)
    slab("MidDeck", MID_Y, 0.05, Z_BACK + 0.005, Z_FRONT - 0.005, M["deckplate"])


# ------------------------------------------------------------------ round hatch (ring, door, dogs, handle) on any surface
def round_hatch(name, c, b, r=0.27, door=True):
    """b: basis whose third column is the surface normal (towards the viewer)."""
    n = b.col[2]
    ring = [c + (b.col[0] * math.cos(2 * math.pi * j / 48) + b.col[1] * math.sin(2 * math.pi * j / 48)) * r for j in range(48)]
    S.sweep(f"{name}Ring", ring, [n] * 48, S.chamfer_rect(0.07, 0.04, 0.01), M["frame"], closed=True)
    if not door:
        return
    rot = L.basis(b.col[0], b.col[1], n)
    L.cylinder(f"{name}Door", r - 0.03, 0.035, M["hatch"], c + n * 0.012, rot, segs=48, bevel=0.006)
    L.torus(f"{name}Rim", (r - 0.03) * 0.7, 0.01, M["frame"], c + n * 0.032, rot, seg=40, mseg=8)
    L.tube(f"{name}Handle", [c + b.col[0] * -0.08 + n * 0.03, c + b.col[0] * -0.08 + n * 0.07, c + b.col[0] * 0.08 + n * 0.07,
                             c + b.col[0] * 0.08 + n * 0.03], 0.01, M["yellow"])
    for k in range(6):
        a = 2 * math.pi * (k + 0.5) / 6
        d = b.col[0] * math.cos(a) + b.col[1] * math.sin(a)
        S.cbox(f"{name}Dog{k}", (0.04, 0.02, 0.014), M["yellow"], c + d * (r - 0.055) + n * 0.034,
               L.basis(d, n.cross(d), n), ch=0.003)


# ------------------------------------------------------------------ main panel: three sections under the button beam
PANEL_Y, PANEL_H, PANEL_TILT = -0.635, 0.40, 0.25     # centre height, height, lean back (up has +z)
PANEL_Z = 2.06                                        # the centre section's station
WING_A = math.radians(22)


def panel_sections():
    up = (0, -1, PANEL_TILT)
    centre = C.Surface("PanelC", (0.0, PANEL_Y, PANEL_Z), (1, 0, 0), up, 0.36, PANEL_H, corner=0.03)
    wings = {}
    for s in (-1, 1):
        right = Vector((math.cos(WING_A), 0, -s * math.sin(WING_A)))
        c = Vector((s * 0.19, PANEL_Y, PANEL_Z - 0.01)) + right * (s * 0.28)
        wings[s] = C.Surface(f"Panel{'R' if s > 0 else 'L'}", c, right, up, 0.54, PANEL_H, corner=0.03)
    return centre, wings


def build_front():
    centre, wings = panel_sections()
    centre.build(M["console"], thick=0.03)
    G.grid(centre, "PanelC", 2, 3, [("toggles", 0, 0, 2, 1, {"cols": 5}), ("mfd", 0, 1, 2, 2, {"screen": "mfd_engine"})], border=0.012)
    for s, w in wings.items():
        w.build(M["console"], thick=0.03)
        tag = "PanelR" if s > 0 else "PanelL"
        G.grid(w, tag, 6, 3, [
            ("annunciators", 0, 0, 2, 1, {"cols": 4, "rows": 2, "start": 0 if s < 0 else 8}), ("dial", 2, 0, 1, 1, {"kind": "alt"}),
            ("dial", 3, 0, 1, 1, {"kind": "press"}), ("annunciators", 4, 0, 2, 1, {"cols": 4, "rows": 2, "start": 4 if s < 0 else 12}),
            ("mfd", 0, 1, 2, 2, {"screen": "mfd_map" if s < 0 else "mfd_systems"}), ("navball", 2, 1, 2, 2, {}),
            ("mfd", 4, 1, 2, 2, {"screen": "mfd_systems" if s < 0 else "mfd_map"}),
        ], border=0.012)
        w.check()
    centre.check()
    for s_, nm in ((centre, "PanelC"), (wings[1], "PanelR"), (wings[-1], "PanelL")):
        G.housing(s_, nm, depth=0.05)
    # glareshield button beam along each section's top edge, its face carrying a warning strip with master alarms
    for s_, nm, strip in ((centre, "BeamC", False), (wings[1], "BeamR", True), (wings[-1], "BeamL", True)):
        up = s_.up.normalized()
        top = s_.c + up * (s_.h / 2)
        rot = L.basis(s_.right, Vector((0, -1, 0)) - Vector((0, -1, 0)).project(s_.right), s_.right.cross(Vector((0, -1, 0))).normalized())
        fwd = -rot.col[2] if rot.col[2].z > 0 else rot.col[2]     # towards the pilots
        beam_c = top + Vector((0, -0.032, 0)) + fwd * 0.03
        S.cbox(f"{nm}", (s_.w + 0.03, 0.06, 0.10), M["glare"], beam_c, L.basis(s_.right, Vector((0, -1, 0)), -fwd), ch=0.012)
        S.cbox(f"{nm}Cap", (s_.w + 0.05, 0.012, 0.12), M["glare"], beam_c + Vector((0, -0.034, 0)), L.basis(s_.right, Vector((0, -1, 0)), -fwd), ch=0.005)
        if strip:
            face = beam_c + fwd * 0.051
            eb = C.Surface(f"{nm}Strip", face, s_.right, (0, -1, 0), s_.w - 0.06, 0.046, corner=0.006)
            eb.build(M["console"], thick=0.008, rim=False)
            G.grid(eb, f"{nm}Strip", 10, 1, [("buttons", 0, 0, 1, 1, {"n": 1}), ("annunciators", 1, 0, 8, 1, {"cols": 8, "rows": 1, "start": 3}),
                                             ("buttons", 9, 0, 1, 1, {"n": 1})], border=0.004, gap=0.003)
            eb.check()


# ------------------------------------------------------------------ centre console between the front seats
def build_centre_console():
    z0, z1, top_y = 1.20, 1.86, -0.72
    S.cbox("CentreConsole", (0.32, FLOOR_Y - top_y - 0.02, z1 - z0), M["frame"], Vector((0.0, (FLOOR_Y + top_y) / 2 + 0.01, (z0 + z1) / 2)), ch=0.015)
    s = C.Surface("CentreTop", (0.0, top_y - 0.002, (z0 + z1) / 2), (1, 0, 0), (0, 0, 1), 0.30, z1 - z0 - 0.02, corner=0.012)
    s.build(M["console"], thick=0.015, rim=False)
    G.grid(s, "Centre", 1, 4, [("mfd", 0, 0, 1, 1, {"screen": "mfd_engine"}), ("keypad", 0, 1, 1, 1, {}),
                               ("toggles", 0, 2, 1, 1, {"cols": 4}), ("breakers", 0, 3, 1, 1, {"cols": 6, "rows": 2})], border=0.008)
    s.check()
    for k, sx in enumerate((-1, 1)):   # speed-brake / throttle levers on the console's flanks, one per pilot
        q = Vector((sx * 0.175, top_y + 0.06, 1.42))
        S.cbox(f"ThrottleSlot{k}", (0.03, 0.09, 0.16), M["frame_dark"], q, ch=0.004)
        L.tube(f"ThrottleLever{k}", [q + Vector((sx * 0.01, 0, 0)), q + Vector((sx * 0.06, -0.09, 0.0))], 0.006, M["toggle"])
        L.box(f"ThrottleHandle{k}", (0.03, 0.024, 0.04), M["rubber"], q + Vector((sx * 0.065, -0.10, 0.0)), bevel=0.006)


# ------------------------------------------------------------------ side consoles outboard of the front seats
def build_side_consoles():
    z0, z1, top_y = 1.15, 1.80, -0.76
    for side in (-1, 1):
        x_out = min(half_width(y, z, 0.02) for y in (top_y, FLOOR_Y) for z in (z0, z1))
        x_in = 0.78
        x = side * (x_in + x_out) / 2
        w = x_out - x_in
        S.cbox(f"SideConsole{side}", (w, FLOOR_Y - top_y, z1 - z0), M["frame"], Vector((x, (FLOOR_Y + top_y) / 2, (z0 + z1) / 2)), ch=0.012)
        s = C.Surface(f"SideTop{side}", (x, top_y - 0.002, (z0 + z1) / 2), (1, 0, 0), (0, 0, 1), w - 0.02, z1 - z0 - 0.02, corner=0.01)
        s.build(M["console"], thick=0.015, rim=False)
        items = [("toggles", 0, 0, 2, 1, {"cols": 4}), ("annunciators", 0, 1, 1, 1, {"cols": 2, "rows": 2, "start": 6}),
                 ("knobs", 1, 1, 1, 1, {"n": 2}), ("breakers", 0, 2, 2, 1, {"cols": 8, "rows": 2}), ("keypad", 0, 3, 2, 1, {})]
        G.grid(s, f"Side{side}", 2, 4, items, border=0.008)
        s.check()


# ------------------------------------------------------------------ hand controllers and pedals, per pilot (as the Mk1)
def build_controls():
    for i, eye in enumerate(EYES[:2]):
        base = Vector((eye.x, FLOOR_Y, eye.z + 0.09))
        S.cbox(f"RhcBox{i}", (0.10, 0.12, 0.12), M["frame_dark"], base + Vector((0, -0.06, 0)), ch=0.01)
        L.cylinder(f"RhcBoot{i}", 0.035, 0.06, M["rubber"], base + Vector((0, -0.15, 0)), basis((1, 0, 0), (0, 0, 1)), segs=16, radius2=0.025)
        grip = [base + Vector((0, -0.18, 0)), base + Vector((0, -0.28, 0.01)), base + Vector((0, -0.33, -0.01))]
        L.tube(f"RhcGrip{i}", grip, 0.022, M["rubber"])
        L.cylinder(f"RhcButton{i}", 0.008, 0.01, M["red"], base + Vector((0.0, -0.345, 0.0)), basis((1, 0, 0), (0, 0, 1)), segs=10)
        for sx in (-1, 1):
            q = Vector((eye.x + sx * 0.12, FLOOR_Y - 0.16, eye.z + 0.02))
            L.box(f"Pedal{i}{sx}", (0.08, 0.15, 0.02), M["frame_dark"], q, basis((1, 0, 0), (0, -1, 0.35)), bevel=0.004)
            L.box(f"PedalStrap{i}{sx}", (0.085, 0.02, 0.025), M["strap"], q + Vector((0, -0.03, -0.012)), basis((1, 0, 0), (0, -1, 0.35)), bevel=0.003)
            L.tube(f"PedalRail{i}{sx}", [Vector((eye.x + sx * 0.12, FLOOR_Y - 0.01, eye.z - 0.08)), Vector((eye.x + sx * 0.12, FLOOR_Y - 0.01, eye.z + 0.14))], 0.008, M["frame"])


# ------------------------------------------------------------------ seats: the Mk1 cockpit's shuttle seat at each eye
def build_seat(tag, eye):
    """Mk1 seat, moved so its eye matches: Mk1 eye (0, -0.182, 1.083), its floor 0.33, back plane at z 0.58."""
    o = Vector((eye.x, eye.y + 0.182, eye.z - 1.083))
    F = 0.33
    V = lambda x, y, z: o + Vector((x, y, z))
    back = basis((-1, 0, 0), (0, -1, -0.10))
    up = back.col[1]
    origin = V(0.0, F - 0.04, 0.58)
    S.cbox(f"{tag}Plinth", (0.30, 0.06, 0.34), M["frame_dark"], V(0, F - 0.03, 0.78), ch=0.012)
    S.cbox(f"{tag}BackPlate", (0.40, 0.66, 0.025), M["frame"], origin + up * 0.33 - back.col[2] * 0.03, back, ch=0.006)
    for sx in (-1, 1):
        rail = origin + Vector((sx * 0.215, 0, 0)) + up * 0.31 - back.col[2] * 0.01
        S.cbox(f"{tag}Rail{sx}", (0.04, 0.64, 0.08), M["frame"], rail, back, ch=0.008)
        for k in range(3):
            S.cbox(f"{tag}RailSlot{sx}{k}", (0.042, 0.1, 0.03), M["frame_dark"], rail + up * (-0.18 + k * 0.17) + back.col[2] * 0.03, back, ch=0.006)
        arm = V(sx * 0.215, F - 0.17, 0.80)
        S.cbox(f"{tag}Armrest{sx}", (0.05, 0.035, 0.30), M["frame"], arm, ch=0.008)
        S.cbox(f"{tag}ArmPad{sx}", (0.045, 0.02, 0.24), M["seat_blue"], arm + Vector((0, -0.026, 0.0)), ch=0.008)
        S.cbox(f"{tag}ArmPost{sx}", (0.04, 0.14, 0.04), M["frame"], arm + Vector((0, 0.09, 0.08)), ch=0.006)
        L.tube(f"{tag}Handle{sx}", [arm + Vector((sx * 0.02, 0.0, 0.12)), arm + Vector((sx * 0.02, -0.05, 0.15)), arm + Vector((sx * 0.02, -0.05, 0.22))],
               0.008, M["yellow"])
    for k in range(3):
        S.cbox(f"{tag}BackCushion{k}", (0.34, 0.165, 0.06), M["seat_blue"], origin + up * (0.10 + k * 0.175), back, ch=0.022)
    for k, dz in enumerate((0.0, 0.17)):
        S.cbox(f"{tag}PanCushion{k}", (0.34, 0.06, 0.16), M["seat_blue"], V(0, F - 0.09, 0.69 + dz), ch=0.022)
    hr = origin + up * 0.72 + back.col[2] * 0.02
    S.cbox(f"{tag}Headrest", (0.20, 0.13, 0.07), M["seat_blue"], hr, back, ch=0.025)
    for sx in (-1, 1):
        S.cbox(f"{tag}HeadrestWing{sx}", (0.06, 0.13, 0.08), M["seat_blue"], hr + Vector((sx * 0.12, 0, 0)) + back.col[2] * 0.03,
               back @ Matrix.Rotation(-sx * 0.35, 3, "Y"), ch=0.022)
    S.cbox(f"{tag}HeadrestBack", (0.30, 0.15, 0.03), M["frame"], hr - back.col[2] * 0.05, back, ch=0.006)
    for sx in (-1, 1):
        L.box(f"{tag}Harness{sx}", (0.045, 0.46, 0.006), M["strap"], origin + Vector((sx * 0.09, 0, 0)) + up * 0.3 + back.col[2] * 0.034, back)
    L.box(f"{tag}LapBelt", (0.34, 0.045, 0.006), M["strap"], V(0, F - 0.125, 0.72), basis((1, 0, 0), (0, 0, 1)))
    L.cylinder(f"{tag}Buckle", 0.03, 0.01, M["buckle"], V(0, F - 0.13, 0.72), basis((1, 0, 0), (0, 0, 1)), segs=16)


# ------------------------------------------------------------------ overhead switch panel above the front seats
def build_overhead():
    """Sloped with the roof, ahead of the front seats' heads, so the pilots read it looking up and forward."""
    z0, z1, w = 1.56, 1.98, 0.96
    up = Vector((0.0, -0.46, -1.0)).normalized()          # screen-up runs aft and up the roof
    zc = (z0 + z1) / 2
    corners = [HS.inner((x, -1.0, z), (0, -1, 0), 0.07) for x in (-w / 2, 0.0, w / 2) for z in (z0, z1)]
    # put the panel's plane under the lowest roof point at each end
    yc = max(c.y + (zc - c.z) * (-up.y / -up.z) for c in corners)
    s = C.Surface("Overhead", (0.0, yc, zc), (1, 0, 0), up, w, (z1 - z0) / abs(up.z), corner=0.03)
    s.build(M["console"], thick=0.025)
    G.grid(s, "Over", 6, 3, [
        ("breakers", 0, 0, 2, 1, {"cols": 8, "rows": 2}), ("annunciators", 2, 0, 2, 1, {"cols": 4, "rows": 2, "start": 2}),
        ("breakers", 4, 0, 2, 1, {"cols": 8, "rows": 2}),
        ("toggles", 0, 1, 2, 1, {"cols": 5}), ("screen", 2, 1, 2, 1, {"mat": "crt_data"}), ("toggles", 4, 1, 2, 1, {"cols": 5}),
        ("knobs", 0, 2, 1, 1, {"n": 2}), ("breakers", 1, 2, 4, 1, {"cols": 14, "rows": 2}), ("knobs", 5, 2, 1, 1, {"n": 2}),
    ], border=0.012)
    s.check()
    G.housing(s, "Overhead", depth=0.04)


# ------------------------------------------------------------------ aft flight deck: station under the aft windows, stowage, hatch
def build_aft_flight_deck():
    s = C.Surface("AftStation", (0.0, -1.52, Z_BACK + 0.02), (-1, 0, 0), (0, -1, 0), 0.96, 0.30, corner=0.02)
    s.build(M["console"], thick=0.02)
    G.grid(s, "AftSta", 6, 2, [("mfd", 0, 0, 2, 2, {"screen": "mfd_comms"}), ("annunciators", 2, 0, 2, 1, {"cols": 4, "rows": 2, "start": 6}),
                               ("toggles", 2, 1, 2, 1, {"cols": 5}), ("mfd", 4, 0, 2, 2, {"screen": "mfd_map"})], border=0.01)
    s.check()
    # stowage cabinet in the starboard aft corner, opposite the hatch
    hw = min(half_width(y, z, 0.02) for y in (FLOOR_Y, FLOOR_Y - 0.6) for z in (Z_BACK + 0.05, 0.75))
    P.cabinet("FlightLocker", Vector((hw - 0.18, FLOOR_Y, 0.44)), STBD,
              0.56, 0.6, 0.34, doors=2)
    # interdeck hatch in the floor
    round_hatch("DeckHatch", HATCH + Vector((0, -0.002, 0)), L.basis(Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0))), r=HATCH_R + 0.03, door=False)
    rails = [Vector((HATCH.x + sx * 0.2, FLOOR_Y, HATCH.z - 0.28)) for sx in (-1, 1)]
    for k, r in enumerate(rails):   # grab handles either side of the hatch, up from the floor
        L.tube(f"DeckHatchGrab{k}", [r, r + Vector((0, -0.12, 0)), r + Vector((0, -0.12, 0.12)), r + Vector((0, 0, 0.12))], 0.012, M["yellow"])


# ------------------------------------------------------------------ flight-deck walls: grab bars, cables, kit
def build_flight_walls():
    for sx in (-1, 1):
        zs = [0.25 + 1.0 * k / 10 for k in range(11)]
        pts = [HS.inner((0, -1.15, z), (sx, 0, 0), 0.045) for z in zs]
        L.tube(f"SillBar{sx}", pts, 0.012, M["yellow"])
        for k in (0, 5, 10):
            L.tube(f"SillBarFoot{sx}{k}", [pts[k], HS.inner((0, -1.15, zs[k]), (sx, 0, 0), 0.01)], 0.008, M["frame"])
        S.bundle(f"WallCables{sx}", [HS.inner((0, -0.62, 0.2 + 0.9 * k / 6), (sx, 0, 0), 0.016) for k in range(7)], n=3, r=0.008)
    upright = Matrix.Rotation(math.pi / 2, 3, "X")
    hw = half_width(FLOOR_Y - 0.3, 0.95, 0.06)
    L.cylinder("Extinguisher", 0.04, 0.3, M["red"], Vector((hw, FLOOR_Y - 0.17, 0.95)), upright, segs=20, bevel=0.01)


# ------------------------------------------------------------------ mid-deck
def build_mid_deck():
    # ladder from the interdeck hatch down to the floor, against the aft side of the opening
    lz = HATCH.z - HATCH_R + 0.03
    for sx in (-1, 1):
        L.tube(f"LadderRail{sx}", [Vector((HATCH.x + sx * 0.17, FLOOR_Y + DECK_T, lz)), Vector((HATCH.x + sx * 0.17, MID_Y, lz))], 0.016, M["frame"])
    for k in range(6):
        y = FLOOR_Y + DECK_T + 0.22 + k * 0.26
        L.tube(f"LadderRung{k}", [Vector((HATCH.x - 0.17, y, lz)), Vector((HATCH.x + 0.17, y, lz))], 0.012, M["yellow"])
    round_hatch("DeckHatchBelow", Vector((HATCH.x, FLOOR_Y + DECK_T + 0.017, HATCH.z)), L.basis(Vector((1, 0, 0)), Vector((0, 0, -1)), Vector((0, 1, 0))),
                r=HATCH_R + 0.03, door=False)

    # port wall: toilet booth, galley, side hatch
    def on_port(z, y, depth=0.0):
        return Vector((-half_width(y, z, 0.01) + depth, y, z))
    yb = MID_Y - 0.62
    back_x = -min(half_width(y, z, 0.03) for y in (MID_Y - 0.02, yb - 0.6) for z in (0.66, 1.26))
    P.hygiene_booth("Toilet", Vector((back_x, yb, 0.96)), PORT, w=0.6, h=1.22, d=0.56)
    gx = -min(half_width(y, z, 0.04) for y in (0.18, 0.76) for z in (1.32, 1.80))
    P.galley("Galley", Vector((gx, 0.47, 1.56)), PORT, w=0.46, h=0.54)
    hc = on_port(2.05, 0.45, 0.0)
    round_hatch("SideHatch", hc + Vector((0.09, 0, 0)), PORT, r=0.26)

    # starboard wall: two sleep stations and the ergometer aft
    sx_ = min(half_width(y, z, 0.01) for y in (MID_Y - 0.02, MID_Y - 1.17) for z in (1.0, 2.1))
    for k, z in enumerate((1.30, 1.84)):
        P.sleep_station(f"Sleep{k}", Vector((sx_, MID_Y - 0.6, z)), STBD, w=0.52, h=1.15, d=0.32)
    K.ergometer("Ergometer", Vector((0.72, MID_Y, 0.52)), L.basis(Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0))))

    # forward wall of lockers (the orbiter's middeck lockers), fitted row by row to the hull
    zf = Z_FRONT - 0.03
    rows = 6
    y0, y1 = FLOOR_Y + DECK_T + 0.06, MID_Y - 0.06
    rh = (y1 - y0) / rows
    k = 0
    for r in range(rows):
        yc = y0 + rh * (r + 0.5)
        hw = min(half_width(yc - rh / 2, zf, 0.03), half_width(yc + rh / 2, zf, 0.03))
        n = int((2 * hw) // 0.27)
        if n < 1:
            continue
        cw = 2 * hw / n
        for c in range(n):
            x = -hw + cw * (c + 0.5)
            p = Vector((x, yc, zf))
            L.box(f"FwdLocker{k}", (cw - 0.02, rh - 0.02, 0.04), M["locker"], p - Vector((0, 0, 0.02)), FWD_WALL, bevel=0.006)
            for lx in (-1, 1):
                L.box(f"FwdLockerLatch{k}{lx}", (0.03, 0.016, 0.012), M["handle"], p + Vector((lx * (cw / 2 - 0.05), -(rh / 2 - 0.03), -0.045)), FWD_WALL, bevel=0.003)
            L.plane(f"FwdLockerLabel{k}", 0.07, 0.018, M["labels"], p + Vector((0, 0.0, -0.0412)), L.basis(Vector((-1, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, -1))),
                    (0.02, 0.81, 0.23, 0.94))
            k += 1

    # fuselage hatch on the aft bulkhead, mid-deck height
    round_hatch("AftHatch", Vector((0.0, 0.48, Z_BACK + 0.04)), AFT_WALL, r=0.34)
    # lights along the mid-deck ceiling
    for k, z in enumerate((0.6, 1.4, 2.1)):
        S.light_fixture(f"MidLight{k}", Vector((0.0, FLOOR_Y + DECK_T + 0.02, z)), L.basis(Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, 1, 0))), w=0.4, h=0.08)


def build_lights_and_markers():
    S.light_fixture("DomeLight", Vector((0.0, HS.inner((0, -1.0, 0.55), (0, -1, 0), 0.03).y, 0.55)), basis((1, 0, 0), (0, 0, 1)), w=0.3, h=0.08)
    K.view("Windscreen", (0.0, -1.0, 1.6), (0.0, -1.2, 3.0))
    K.view("Left", (-0.5, -1.0, 1.5), (-1.8, -1.2, 1.5))
    K.view("Right", (0.5, -1.0, 1.5), (1.8, -1.2, 1.5))
    for i, seat in enumerate(SPEC["pose"]["seats"]):
        C.eye_marker(i, seat)


build_shell()
build_front()
build_centre_console()
build_side_consoles()
build_controls()
for i, eye in enumerate(EYES):
    build_seat(f"Seat{i}", eye)
build_overhead()
build_aft_flight_deck()
build_flight_walls()
build_mid_deck()
build_lights_and_markers()
S.collision_markers(hatches=[("Aft", (0.0, 0.48, Z_BACK + 0.3)), ("Side", (-1.0, 0.45, 2.05)), ("Deck", (HATCH.x, FLOOR_Y, HATCH.z))])
L.save(OUT)
