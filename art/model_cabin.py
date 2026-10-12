"""Station crew cabins: PPD-10 "Hitchhiker" (4 crew) and PPD-20 "Wayfarer" (8 crew), as rack rooms (see cabin.py).

Run inside Blender:  blender -b --python model_cabin.py -- <spec.json> <tex_dir> <out.blend>
The spec's "layout" picks the design. Module axis = Blender Z (hull base at 0); +Y is the ceiling.
"""
import json
import math
import os
import random
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
M["canvas"] = L.material("IVA_Canvas", (0.27, 0.28, 0.23), rough=0.92, normal="canvas_normal.png", uv_scale=(6.0, 6.0), normal_strength=0.8)
M["umbilical"] = L.material("IVA_Umbilical", (0.32, 0.36, 0.42), rough=0.7)
M["net"] = L.material("IVA_Net", (0.30, 0.32, 0.20), rough=0.9)
M["tank"] = L.material("IVA_Tank", (0.78, 0.79, 0.80), rough=0.3, metal=0.7)
P.materials()
import stock as S  # noqa: E402
S.materials()
M["deckplate"] = L.material("IVA_DeckPlate", tex="deckplate_color.png", normal="deckplate_normal.png", rough=0.6, metal=0.35, normal_strength=0.8)
import cabin as K  # noqa: E402
K.materials()

M["whiteboard_art"] = L.material("IVA_WhiteboardArt", tex="whiteboard_cabin.png", rough=0.25, metal=0.0)
C.setup(SPEC, wall=SPEC["wall"], ceil=SPEC["ceiling"], top=SPEC["ceiling"], seg=96)
LAY = SPEC["layout"]
RM = LAY["room"]
R = K.Room(xw=RM["xw"], yf=RM["yf"], yc=RM["yc"], z0=SPEC["floor"], z1=SPEC["ceiling"])
SEATS = [K.seat(s["eye"], s["fwd"], s.get("up", (0, 1, 0))) for s in LAY["seats"]]


def side_holes(wall):
    """Window openings on a side wall, from the layout's windows (dz along the module, dy across), in wall (u, v)."""
    ym = (R.yf + R.yc) / 2
    holes = []
    for w in LAY.get("windows", []):
        if w["wall"] != wall:
            continue
        sgn = -1 if wall == "port" else 1
        holes.append([(sgn * (w["z"] + dz - R.zm), w["y"] + dy - ym) for dz, dy in w["poly"]])
    return holes


def recess_holes(wall):
    """Openings in a surface for the units recessed into the standoff behind it."""
    holes = []
    for z in [q[1] for q in LAY.get("quarters", []) if q[0] == wall]:
        if wall in ("port", "stbd"):
            holes.append(K.recess_rect(R, wall, z, 0.92, min(1.5, (R.yc - R.yf) - 0.5)))
        else:
            holes.append(K.recess_rect(R, wall, z, min(1.2, 2 * R.xw - 0.5), 0.92))
    for wl, z0, z1, _ in LAY.get("hygiene", []):
        if wl == wall:
            holes.append(K.recess_rect(R, wall, (z0 + z1) / 2, z1 - z0 - 0.06, (R.yc - R.yf) - 0.14))
    return holes


def window_shell_holes():
    """Openings in the hull shell behind the window wells (capsule angle convention)."""
    out = []
    for w in LAY.get("windows", []):
        phi = math.atan2(1.0 if w["wall"] == "stbd" else -1.0, -w["y"] / 1.9)
        out.append((phi, w["z"], 0.16, 0.24))
    for poly in LAY.get("ceiling_holes", []):
        zc = sum(v for u, v in poly) / len(poly)
        out.append((math.pi, zc, 0.16, 0.18))
    return out


def build_shell():
    K.hull_shell(R, window_shell_holes())
    for wall in ("port", "stbd"):
        K.panel_with_holes(R, wall, "Wall_" + wall, side_holes(wall) + recess_holes(wall))
        for k, poly in enumerate(side_holes(wall)):
            K.window_well(R, wall, f"Well_{wall}{k}", poly, LAY["window_depth"])
    ceil_holes = [[(u, v - R.zm) for u, v in poly] for poly in LAY.get("ceiling_holes", [])]
    K.panel_with_holes(R, "ceil", "Ceiling", ceil_holes + recess_holes("ceil"))
    for k, poly in enumerate(ceil_holes):
        K.window_well(R, "ceil", f"Well_ceil{k}", poly, LAY["ceiling_well_depth"])
    K.panel_with_holes(R, "floor", "GroundPlates", recess_holes("floor"), mat=M["deckplate"])
    K.corners(R)


def build_furniture():
    """Zero g: crew quarters on any surface, galley, hygiene compartment, railed tables, ergometer, lounge consoles,
    and a foot loop under every crew position (no chairs)."""
    ym = (R.yf + R.yc) / 2
    for k, (wall, z) in enumerate(LAY.get("quarters", [])):
        K.quarters_recessed(R, wall, z, f"Quarters{k}")
    for k, (wall, z0, z1) in enumerate(LAY.get("galley", [])):
        K.counter_run(R, wall, z0, z1, f"Galley{k}")
    for k, (wall, z0, z1, d) in enumerate(LAY.get("hygiene", [])):
        K.hygiene_recessed(R, wall, z0, z1, f"Hygiene{k}", height=(R.yc - R.yf) - 0.14)
    for k, (wall, z, kind) in enumerate(LAY.get("racks", [])):
        K.rack(R, wall, z, kind, f"Rack_{wall}{k}", w=LAY.get("rack_w"), seed=k + 3)
    for k, (wall, z, across) in enumerate(LAY.get("tables", [])):
        K.rail_table(f"Table{k}", *K.bay_frame(R, wall, z, across))
    for k, (wall, z, across, flip) in enumerate(LAY.get("ergometers", [])):
        p, b = K.bay_frame(R, wall, z, across)
        if flip:
            b = L.basis(-b.col[0], -b.col[1], b.col[2])
        K.ergometer(f"Ergometer{k}", p, b)
    for k, (wall, z0, z1) in enumerate(LAY.get("ledges", [])):   # console under a row of windows
        u0, u1 = R.u_of_z(wall, z0), R.u_of_z(wall, z1)
        p, b = R.frame(wall, (u0 + u1) / 2, R.yf + 0.3 - ym)
        S.cbox(f"Ledge{k}", (abs(u1 - u0), 0.04, 0.22), M["module"], p + b.col[2] * 0.11, b, ch=0.008)
        S.cbox(f"LedgeFace{k}", (abs(u1 - u0), 0.26, 0.02), M["locker"], p - b.col[1] * 0.15 + b.col[2] * 0.21, b, ch=0.004)
        P.binoculars(f"LedgeBinoculars{k}", p + b.col[1] * 0.04 + b.col[2] * 0.1 + b.col[0] * 0.25, b)
        P.camera(f"LedgeCamera{k}", p + b.col[1] * 0.09 + b.col[2] * 0.12 - b.col[0] * 0.3, b)
        L.tube(f"LedgeRail{k}", [p + b.col[1] * 0.12 + b.col[2] * 0.05 - b.col[0] * abs(u1 - u0) * 0.45, p + b.col[1] * 0.12 + b.col[2] * 0.25 - b.col[0] * abs(u1 - u0) * 0.45,
                                 p + b.col[1] * 0.12 + b.col[2] * 0.25 + b.col[0] * abs(u1 - u0) * 0.45, p + b.col[1] * 0.12 + b.col[2] * 0.05 + b.col[0] * abs(u1 - u0) * 0.45],
               0.011, M["yellow"])
    K.foot_loops(R, SEATS)


def build_ceiling():
    down = Vector((0, -1, 0))
    clear = S.Clearance(zones=[K.kept_out])
    n = max(2, int((R.z1 - R.z0) / 0.5))
    for side in (-1, 1):
        x = side * (R.xw - 0.24)
        for k in range(n):
            z = R.z0 + (R.z1 - R.z0) * (k + 0.5) / n
            if any(clear.blocked(Vector((x + dx, R.yc - 0.03, z + dz)), 0.02) for dx in (-0.06, 0.06) for dz in (-0.14, 0, 0.14)):
                continue
            S.light_fixture(f"CeilLight{side}_{k}", Vector((x, R.yc, z)), L.basis(Vector((0, 0, 1)), Vector((1, 0, 0)), down), w=0.22, h=0.07)
    for k, z in enumerate(LAY.get("ceiling_vents", [])):
        p, b = R.frame("ceil", 0, z - R.zm)
        S.grille(f"CeilVent{k}", p, b, 0.42, 0.18, slats=8)
    for k, z in enumerate(LAY.get("ceiling_nets", [])):
        p, b = R.frame("ceil", 0.0, z - R.zm)
        P.net_with_gear(f"CeilNet{k}", p, b, 0.5, 0.35)
    for k, z in enumerate(LAY.get("floor_bags", [])):
        p, b = R.frame("floor", 0.45 * (1 if k % 2 else -1), z - R.zm)
        P.cargo_bag(f"FloorBag{k}", p, b, 0.4, 0.3, 0.2)


# ------------------------------------------------------------------ build
build_shell()
build_furniture()
DOORWAYS = [K.partition(R, z, f"Partition{k}", door_w=w, door_h=h) for k, (z, w, h) in enumerate(LAY.get("partitions", []))]
_clear = S.Clearance(zones=[K.kept_out])
PST = ("kerbin", "munholiday", "struts", "missing") if SPEC["seats"] > 4 else ("mun", "eve", "jool", "lostpart")
eva_at = K.end_bulkhead(R, "aft", "AftEnd", hatch_r=LAY.get("hatch_r", 0.45), clear=_clear, eva=True, posters=PST[:2])
K.end_bulkhead(R, "fore", "ForeEnd", hatch_r=LAY.get("hatch_r", 0.45), clear=_clear, posters=PST[2:])
build_ceiling()
K.dress_room(R, seed=len(SEATS))
for k, v in enumerate(LAY.get("views", [])):
    K.view(v["name"], v["from"], v["at"])
for i, s in enumerate(SEATS):
    C.eye_marker(i, s)
S.collision_markers(decks=[d[4] for d in DOORWAYS], holes=DOORWAYS,
                    hatches=[("Aft", (0.0, -0.1, R.z0 + 0.25)), ("Fore", (0.0, -0.1, R.z1 - 0.25))] + ([("Side", tuple(eva_at))] if eva_at else []))
print(f"{SPEC['name']}: room x +-{R.xw}, y {R.yf}..{R.yc}, z {R.z0}..{R.z1}; {len(SEATS)} seats")
import surfaces  # noqa: E402  (detail textures on plain painted, brushed and fabric materials)
if not os.environ.get("IVA_NO_DETAIL"):
    surfaces.apply()
L.save(OUT)
