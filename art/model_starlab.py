"""OSL-25 "Starlab" orbital lab interior: an ISS-style rack room with a greenhouse in the ceiling.

Run inside Blender:  blender -b --python model_starlab.py -- <spec.json> <tex_dir> <out.blend>
The module axis is Blender Z (hull base at 0); the greenhouse bay is on the +Y side, so +Y is the ceiling. Three crew
sit upright at workstations on the side walls.
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
R = K.Room(xw=0.95, yf=-0.92, yc=0.68, z0=SPEC["floor"], z1=SPEC["ceiling"])
GH_X, GH_Z0, GH_Z1, GH_DEPTH = 0.6, 1.25, 3.45, 0.42      # greenhouse window/bay (under the real greenhouse pod)
RACK_Z = (1.35, 2.35, 3.35)
SEATS = [K.seat((-0.33, 0.05, RACK_Z[0]), (-1, 0, 0)), K.seat((0.33, 0.05, RACK_Z[1]), (1, 0, 0)),
         K.seat((0.15, 0.42, 2.0), (0, 1, 0), (0, 0, 1))]   # C floats face-up under the greenhouse, feet on the ceiling aft of it


def build_walls():
    # side walls and floor are solid panels; the ceiling has the greenhouse window cut out of it
    for wall in ("port", "stbd"):
        K.wall_panel(R, wall, "Wall_" + wall)
    p, b = R.frame("floor", 0, 0)
    S.cbox("GroundPlates", (2 * R.xw, 0.03, R.z1 - R.z0), M["deckplate"], p - Vector((0, 0.015, 0)), ch=0.0)
    yc = R.yc + 0.015
    for k, (x0, x1, z0, z1) in enumerate(((-R.xw, -GH_X, R.z0, R.z1), (GH_X, R.xw, R.z0, R.z1), (-GH_X, GH_X, R.z0, GH_Z0), (-GH_X, GH_X, GH_Z1, R.z1))):
        S.cbox(f"Ceiling{k}", (x1 - x0, 0.03, z1 - z0), M["blanket"], ((x0 + x1) / 2, yc, (z0 + z1) / 2), ch=0.0)
    K.corners(R)
    K.end_bulkhead(R, "aft", "AftEnd")
    K.end_bulkhead(R, "fore", "ForeEnd")


def build_racks():
    kinds = {("port", 0): "workstation", ("port", 1): "glovebox", ("port", 2): "comms",
             ("stbd", 0): "freezer", ("stbd", 1): "workstation", ("stbd", 2): "life"}
    for (wall, i), kind in kinds.items():
        K.rack(R, wall, RACK_Z[i], kind, f"Rack_{wall}{i}", seed=i * 7 + (wall == "stbd"))


def build_ceiling():
    K.greenhouse(R, "Greenhouse", -GH_X, GH_X, GH_Z0, GH_Z1, GH_DEPTH)
    down = Vector((0, -1, 0))
    for side in (-1, 1):
        x = side * 0.8
        for k, z in enumerate((0.95, 1.55, 2.15, 2.75, 3.35, 3.85)):
            S.light_fixture(f"CeilLight{side}_{k}", Vector((x, R.yc, z)), L.basis(Vector((0, 0, 1)), Vector((1, 0, 0)), down), w=0.22, h=0.07)
        S.bundle(f"CeilRun{side}", [Vector((side * 0.68, R.yc - 0.04, R.z0 + 0.15)), Vector((side * 0.68, R.yc - 0.04, R.z1 - 0.15))], n=4, ends=(False, False))
    for k, z in enumerate((0.9, 3.8)):
        p, b = R.frame("ceil", 0, z - R.zm)
        S.grille(f"CeilVent{k}", p, b, 0.5, 0.2, slats=8)


def build_floor():
    """Zero g: no chairs. Racks down the middle of the floor (stowage, experiments, tools), foot loops for the crew."""
    for k, (z, kind) in enumerate(((RACK_Z[0], "stowage"), (RACK_Z[1], "experiment"), (RACK_Z[2], "tools"))):
        K.rack(R, "floor", z, kind, f"Rack_floor{k}", w=0.6, h=0.85, seed=20 + k)
    K.foot_loops(R, SEATS)


# ------------------------------------------------------------------ build
build_walls()
build_racks()
build_ceiling()
build_floor()
K.dress(R, walls=("aft", "fore"), seed=3)
for i, s in enumerate(SEATS):
    C.eye_marker(i, s)
S.collision_markers(hatches=[("Aft", (0.0, -0.1, R.z0 + 0.25)), ("Fore", (0.0, -0.1, R.z1 - 0.25))])
print(f"room x +-{R.xw}, y {R.yf}..{R.yc}, z {R.z0}..{R.z1}; {len(SEATS)} seats")
L.save(OUT)
