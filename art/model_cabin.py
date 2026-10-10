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

C.setup(SPEC, wall=SPEC["wall"], ceil=SPEC["ceiling"], top=SPEC["ceiling"], seg=96)
LAY = SPEC["layout"]
RM = LAY["room"]
R = K.Room(xw=RM["xw"], yf=RM["yf"], yc=RM["yc"], z0=SPEC["floor"], z1=SPEC["ceiling"])
SEATS = [K.seat(s["eye"], s["fwd"]) for s in LAY["seats"]]


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


def build_shell():
    for wall in ("port", "stbd"):
        K.panel_with_holes(R, wall, "Wall_" + wall, side_holes(wall))
        for k, poly in enumerate(side_holes(wall)):
            K.window_well(R, wall, f"Well_{wall}{k}", poly, LAY["window_depth"])
    ceil_holes = [[(u, v - R.zm) for u, v in poly] for poly in LAY.get("ceiling_holes", [])]
    K.panel_with_holes(R, "ceil", "Ceiling", ceil_holes)
    for k, poly in enumerate(ceil_holes):
        K.window_well(R, "ceil", f"Well_ceil{k}", poly, LAY["ceiling_well_depth"])
    p, b = R.frame("floor", 0, 0)
    S.cbox("GroundPlates", (2 * R.xw, 0.03, R.z1 - R.z0), M["deckplate"], p - Vector((0, 0.015, 0)), ch=0.0)
    K.corners(R)
    K.end_bulkhead(R, "aft", "AftEnd", hatch_r=LAY.get("hatch_r", 0.45))
    K.end_bulkhead(R, "fore", "ForeEnd", hatch_r=LAY.get("hatch_r", 0.45))


def build_furniture():
    ym = (R.yf + R.yc) / 2
    for k, (wall, z) in enumerate(LAY.get("sleep", [])):
        K.sleep_wall(R, wall, z, f"Sleep{k}")
    for k, (wall, z0, z1) in enumerate(LAY.get("galley", [])):
        K.counter_run(R, wall, z0, z1, f"Galley{k}")
    for k, (wall, z) in enumerate(LAY.get("toilet", [])):
        P.toilet(f"Toilet{k}", *R.frame(wall, R.u_of_z(wall, z), R.yf + 0.2 - ym))
        P.hygiene_booth(f"ToiletBooth{k}", *R.frame(wall, R.u_of_z(wall, z), R.yf + 0.56 - ym), w=0.64, h=1.08, d=min(0.6, R.xw - 0.42))
    for k, (wall, z) in enumerate(LAY.get("sink", [])):
        P.sink(f"Sink{k}", *R.frame(wall, R.u_of_z(wall, z), 0.05))
        P.towels(f"Towels{k}", *R.frame(wall, R.u_of_z(wall, z + 0.3), 0.1))
    for k, (wall, z, kind) in enumerate(LAY.get("racks", [])):
        K.rack(R, wall, z, kind, f"Rack_{wall}{k}", w=LAY.get("rack_w", 0.8), seed=k + 3)
    for k, (x, z) in enumerate(LAY.get("tables", [])):
        K.table(f"Table{k}", x, z, R.yf, h=0.62)
    for k, (wall, z0, z1) in enumerate(LAY.get("ledges", [])):   # window-seat ledge under a row of windows
        u0, u1 = R.u_of_z(wall, z0), R.u_of_z(wall, z1)
        p, b = R.frame(wall, (u0 + u1) / 2, R.yf + 0.3 - ym)
        S.cbox(f"Ledge{k}", (abs(u1 - u0), 0.04, 0.22), M["module"], p + b.col[2] * 0.11, b, ch=0.008)
        S.cbox(f"LedgeFace{k}", (abs(u1 - u0), 0.26, 0.02), M["locker"], p - b.col[1] * 0.15 + b.col[2] * 0.21, b, ch=0.004)
        P.binoculars(f"LedgeBinoculars{k}", p + b.col[1] * 0.04 + b.col[2] * 0.1 + b.col[0] * 0.25, b)
        P.camera(f"LedgeCamera{k}", p + b.col[1] * 0.09 + b.col[2] * 0.12 - b.col[0] * 0.3, b)
    for i, s in enumerate(SEATS):
        K.stool(f"Stool{i}", K.hip_of(s["eye"], s["fwd"]), s["fwd"], R.yf)


def build_ceiling():
    down = Vector((0, -1, 0))
    n = max(2, int((R.z1 - R.z0) / 0.6))
    for side in (-1, 1):
        x = side * (R.xw - 0.22)
        for k in range(n):
            z = R.z0 + (R.z1 - R.z0) * (k + 0.5) / n
            S.light_fixture(f"CeilLight{side}_{k}", Vector((x, R.yc, z)), L.basis(Vector((0, 0, 1)), Vector((1, 0, 0)), down), w=0.22, h=0.07)
        S.bundle(f"CeilRun{side}", [Vector((side * (R.xw - 0.38), R.yc - 0.04, R.z0 + 0.15)), Vector((side * (R.xw - 0.38), R.yc - 0.04, R.z1 - 0.15))], n=4,
                 ends=(False, False))
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
build_ceiling()
K.dress_room(R, seed=len(SEATS))
for k, v in enumerate(LAY.get("views", [])):
    K.view(v["name"], v["from"], v["at"])
for i, s in enumerate(SEATS):
    C.eye_marker(i, s)
S.collision_markers(hatches=[("Aft", (0.0, -0.1, R.z0 + 0.25)), ("Fore", (0.0, -0.1, R.z1 - 0.25))])
print(f"{SPEC['name']}: room x +-{R.xw}, y {R.yf}..{R.yc}, z {R.z0}..{R.z1}; {len(SEATS)} seats")
L.save(OUT)
