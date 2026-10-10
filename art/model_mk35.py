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
M["blanket"] = L.material("IVA_WallPanel", tex="wallpanel_color.png", normal="wallpanel_normal.png", rough=0.55, metal=0.3, uv_scale=(1.0, 1.0), normal_strength=0.8)
M["shell"] = L.material("IVA_SeatShell", (0.22, 0.23, 0.25), rough=0.4, metal=0.55)
M["bottle"] = L.material("IVA_Bottle", (0.22, 0.42, 0.30), rough=0.35, metal=0.4)
M["tank"] = L.material("IVA_Tank", (0.78, 0.79, 0.80), rough=0.3, metal=0.7)
M["periscope"] = L.material("IVA_Periscope", tex="periscope.png", rough=0.1, emit=1.6, emit_tex=True)
M["canvas"] = L.material("IVA_Canvas", (0.27, 0.28, 0.23), rough=0.92, normal="canvas_normal.png", uv_scale=(6.0, 6.0), normal_strength=0.8)
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
DECK_Z = 2.0                      # deck B (habitation) floor
DECK_C = 2.88                     # deck C (science and docking) floor
HOLE_B = (0.15, 0.55, 0.2, 0.62)  # ladder opening B -> C: x0, x1, y0, y1
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


# ------------------------------------------------------------------ decks: platforms, openings, ladders, ceiling lights
def platform(name, z, holes):
    """Grated deck at height z filling the hull, with rectangular openings (x0, x1, y0, y1); rim, radial beams and
    downlights on its underside (the ceiling of the deck below)."""
    import bmesh
    rr = C.r_in(z) - 0.01
    tiles = bmesh.new()
    uv = tiles.loops.layers.uv.new("UVMap")
    step = 0.1
    k = int(rr / step) + 1
    for i in range(-k, k):
        for j in range(-k, k):
            x0, y0 = i * step, j * step
            cx, cy = x0 + step / 2, y0 + step / 2
            if math.hypot(cx, cy) > rr - 0.03 or any(h[0] < cx < h[1] and h[2] < cy < h[3] for h in holes):
                continue
            vs = [tiles.verts.new((x, y, z)) for x, y in ((x0, y0), (x0 + step, y0), (x0 + step, y0 + step), (x0, y0 + step))]
            face = tiles.faces.new(vs)
            for l in face.loops:
                l[uv].uv = (l.vert.co.x * 1.5, l.vert.co.y * 1.5)
    bmesh.ops.remove_doubles(tiles, verts=tiles.verts, dist=1e-5)
    L.solidify(L.mesh_obj(name, tiles, [M["floor"]]), 0.03)
    L.tube(name + "Rim", [C.polar(2 * math.pi * j / 96, rr - 0.015, z - 0.015) for j in range(97)], 0.02, M["couchframe"])
    for k2 in range(8):
        phi = 2 * math.pi * (k2 + 0.5) / 8
        L.tube(f"{name}Beam{k2}", [C.polar(phi, 0.25, z - 0.05), C.polar(phi, rr - 0.02, z - 0.05)], 0.022, M["couchframe"])
        p = C.polar(phi + math.pi / 8, rr * 0.55, z - 0.045)
        L.cylinder(f"{name}Downlight{k2}", 0.04, 0.025, M["ring"], p, segs=20)
        L.disc(f"{name}DownlightLens{k2}", 0.03, M["light"], p - Vector((0, 0, 0.013)), Matrix.Rotation(math.pi, 3, "X"), segs=20)
    for h in holes:   # hazard-striped railing round each opening (open on the ladder side)
        x0, x1, y0, y1 = h
        P.hazard_rail(f"{name}Rail{h[0]:.2f}", [Vector((x0, y1 - 0.1, z)), Vector((x0, y1 - 0.1, z + 0.45)), Vector((x0, y0, z + 0.45)),
                                                 Vector((x1, y0, z + 0.45)), Vector((x1, y1 - 0.1, z + 0.45)), Vector((x1, y1 - 0.1, z))], 0.009)


def build_decks():
    platform("DeckB", DECK_Z, [(-HOLE_HW, HOLE_HW, HOLE_Y0, HOLE_Y1)])
    platform("DeckC", DECK_C, [HOLE_B])
    ladder("LadderAB", 0.0, HOLE_Y1 - 0.12, FLOOR + 0.5, DECK_Z + 0.55, 0.22)
    ladder("LadderBC", (HOLE_B[0] + HOLE_B[1]) / 2, HOLE_B[3] - 0.06, DECK_Z, DECK_C + 0.5, 0.2)
    ladder("LadderTunnel", 0.0, 0.3, DECK_C, C.Z_TOP - 0.08, 0.18)


# ------------------------------------------------------------------ deck B: kitchen, dining, sleep stations, hygiene, exercise
def build_hab_deck():
    D = DECK_Z
    # kitchen along the front wall: counter cabinets with a worktop, oven, galley, utensils, food lockers above
    for k, deg in enumerate((-36, -24, -12, 0, 12, 24, 36)):
        p, b = at(deg, D + 0.2, 0.0)
        P.cabinet(f"Counter{k}", p, b, 0.28, 0.38, 0.32, doors=1 if k % 2 else 2, top=M["module"])
    P.oven("Oven", *at(-18, D + 0.52, 0.08))
    P.galley("Galley", *at(10, D + 0.62, 0.0), w=0.3, h=0.42)
    P.utensil_rack("Utensils", *at(-30, D + 0.68, 0.0))
    for k, deg in enumerate((28, 38)):
        P.cabinet(f"FoodLocker{k}", *at(deg, D + 0.72, 0.0), 0.24, 0.16, 0.18, doors=1)
    P.table("DiningTable", (0.0, -0.45), r=0.26, h=0.42, floor_z=D)
    # crew quarters on the left
    for k, deg in enumerate((-100, -128)):
        P.sleep_station(f"SleepStation{k}", *at(deg, D + 0.43, 0.0), 0.5, 0.78, 0.3)
    P.drawer_stack("PersonalLockers", *at(-70, D + 0.25, 0.0), 0.3, 0.4, 4)
    P.net_with_gear("QuartersNet", *at(-70, D + 0.66, 0.0), 0.34, 0.26)
    # hygiene on the right, exercise bike on the deck
    P.toilet("Toilet", *at(100, D + 0.2, 0.0))
    P.sink("Sink", *at(126, D + 0.5, 0.0))
    P.towels("Towels", *at(70, D + 0.55))
    P.bike("Bike", (0.82, 0.22), yaw=0.0, floor_z=D)
    # back wall round the ladder: stowage nets, cargo, tanks, tool board
    P.net_with_gear("BackNet", *at(165, D + 0.5, 0.0), 0.4, 0.3)
    P.cargo_bag("BackBag", *at(196, D + 0.3, 0.0), 0.3, 0.2, 0.12)
    P.tool_board("ToolBoard", *at(148, D + 0.52), 0.32, 0.3)
    for side in (-1, 1):
        p, b = at(side * 175 if side > 0 else -158, D + 0.4, 0.13)
        L.cylinder(f"HabTank{side}", 0.1, 0.56, M["tank"], p, L.basis(b.col[0], b.col[2], -b.col[1]), segs=28, bevel=0.025)
        for dz in (-0.18, 0.18):
            L.torus(f"HabTankStrap{side}{dz}", 0.104, 0.006, M["handle"], p + b.col[1] * dz, L.basis(b.col[0], b.col[2], -b.col[1]), seg=28, mseg=6)
    for side in (-1, 1):
        P.fan(f"HabFan{side}", *at(side * 52, D + 0.72))
    G.wall("HabPanels", [("lamps", 52, D + 0.5, 0.12, 0.05, {"n": 3}), ("knobs", -52, D + 0.5, 0.14, 0.06, {"n": 3})])


# ------------------------------------------------------------------ deck C: science lab and docking station
def build_lab_deck():
    D = DECK_C
    # docking station: a low console between the two docking windows, with a camera and binoculars
    up = Vector((0, -0.4, 1)).normalized()
    s = C.Surface("DockStation", (0, -0.86, D + 0.24), (-1, 0, 0), up, 0.3, 0.26, corner=0.02)
    s.build(M["console"], thick=0.03)
    G.grid(s, "Dock", 2, 2, [("navball", 0, 0, 1, 1, {}), ("mfd", 1, 0, 1, 1, {"screen": "mfd_map"}),
                             ("toggles", 0, 1, 1, 1, {"cols": 3}), ("annunciators", 1, 1, 1, 1, {"cols": 2, "rows": 2, "start": 8})], border=0.008)
    s.check()
    G.prism("DockStationBase", [(-0.98, D), (-0.78, D), (-0.8, D + 0.16), (-1.0, D + 0.2)], -0.16, 0.16, M["console"])
    w = next(w for w in C.WINDOWS if w["name"] == "DockingR")
    p, b = at(math.degrees(w["phi"]) + 14, w["z"] + 0.02, 0.02)
    P.camera("DockCamera", p, b, lens_dir=(C.polar(w["phi"], C.r_in(w["z"]) + 0.2, w["z"]) - p))
    P.binoculars("Binoculars", *at(-math.degrees(w["phi"]) - 15, D + 0.4))
    # lab: glovebox, microscope bench with a laptop, freezer, goo rack, experiment racks, sample table
    P.glovebox("Glovebox", *at(62, D + 0.25, 0.0), 0.42, 0.32, 0.28)
    P.cabinet("MicroscopeBench", *at(-62, D + 0.16, 0.0), 0.36, 0.3, 0.28, doors=2, top=M["module"])
    P.microscope("Microscope", *at(-58, D + 0.36, 0.06))
    P.laptop("LabLaptop", *at(-80, D + 0.48), arm=0.24, screen="mfd_systems")
    P.freezer("SampleFreezer", *at(100, D + 0.22, 0.0), 0.3, 0.36, 0.26)
    P.science_rack("GooRack", *at(-104, D + 0.32), 0.3, 0.5)
    P.drawer_stack("SampleDrawers", *at(135, D + 0.22, 0.0), 0.28, 0.36, 4)
    P.whiteboard("LabBoard", *at(-140, D + 0.4), 0.3, 0.22)
    G.wall("LabRacks", [("mfd", 160, D + 0.42, 0.2, 0.2, {"screen": "mfd_engine"}), ("breakers", -165, D + 0.3, 0.24, 0.11, {"cols": 8, "rows": 2}),
                        ("annunciators", 160, D + 0.18, 0.2, 0.08, {"cols": 6, "rows": 2, "start": 4})], inset=0.04)
    P.sample_table("SampleTable", (-0.4, -0.25), D)
    P.headset("Headset", *at(-35, D + 0.45))
    for side in (-1, 1):
        P.fan(f"LabFan{side}", *at(side * 120, D + 0.62))


def ladder(name, x, y, z0, z1, w):
    for side in (-1, 1):
        L.tube(f"{name}Rail{side}", [Vector((x + side * w / 2, y, z0)), Vector((x + side * w / 2, y, z1))], 0.01, M["rib"])
    n = int((z1 - z0) / 0.25)
    for k in range(1, n + 1):
        z = z0 + k * (z1 - z0) / (n + 1)
        L.tube(f"{name}Rung{k}", [Vector((x - w / 2, y, z)), Vector((x + w / 2, y, z))], 0.008, M["yellow"])


# ------------------------------------------------------------------ mission kit: what a crew of five lives and works with
def at(deg, z, inset=0.0):
    return C.frame_at(C.rad(deg), z, inset)


def flat(x, y, z):
    """Frame lying on a floor at (x, y, z): normal up, 'up' towards the cabin front."""
    return Vector((x, y, z)), L.basis(Vector((1, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1)))


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
        P.hazard_rail(f"Handrail{side}", [a, a2, c2, c], 0.009)
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
build_decks()
build_walls()
build_hab_deck()
build_lab_deck()
build_lower_kit()
for i, seat in enumerate(SEATS):
    C.eye_marker(i, seat)
ref = os.path.join(os.environ.get("IVA_REFERENCE", "C:/Games/KSP2Mods/reference"), "poses", POSE["ref_from"] + ".obj")
C.reference_kerbal_copies(ref, POSE["ref_base_y"], [(s["x"], POSE["ref_offset"][1], POSE["ref_offset"][2]) for s in SEATS])
print(f"eyes at z {EYE_Z:.3f}; console {MDC_Z - EYE_Z:.3f} m above; decks at {DECK_Z:.2f} and {DECK_C:.2f}")
L.save(OUT)
