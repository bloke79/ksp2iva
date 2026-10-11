"""Renders a stock KSP2 interior (extracted OBJ, reference only) from the same cameras as one of our specs, so the two
can be compared side by side. Nothing from the stock interior ships; this is a review aid.

Usage: blender -b --python render_stock.py -- <stock.obj> <spec.json> <out_dir> [width] [views...]
The OBJ is extract_pods.py output (Unity part space, x negated); it's placed in generator space with the spec's
hull_base_y, as our own interior is.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

A = sys.argv[sys.argv.index("--") + 1:]
OBJ, SPEC, OUT = A[0], json.load(open(A[1])), A[2]
W = int(A[3]) if len(A) > 3 else 1280
VIEWS = A[4:] or list(SPEC["cameras"])
os.makedirs(OUT, exist_ok=True)
base = SPEC["hull_base_y"]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=OBJ, forward_axis="Y", up_axis="Z")   # no axis conversion: raw OBJ coordinates
# raw OBJ (-ux, uy, uz) -> generator (ux, uz, uy - base)
T = Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, -base), (0, 0, 0, 1)))
for o in bpy.context.scene.objects:
    if o.type == "MESH":
        o.data.transform(T)
        o.data.flip_normals()   # the x mirror flips the winding
        for m in o.data.materials:
            if m and m.node_tree:
                for n in m.node_tree.nodes:
                    if n.type == "BSDF_PRINCIPLED":
                        n.inputs["Roughness"].default_value = 0.6
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = W, W * 9 // 16
w = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.35, 0.45, 0.6, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.8
sc.world = w
for i, pl in enumerate(SPEC.get("preview_lights", [])):
    ld = bpy.data.lights.new(f"L{i}", "AREA")
    ld.energy = pl["energy"] * 20
    ld.size = pl.get("size", 0.3)
    lo = bpy.data.objects.new(f"L{i}", ld)
    lo.location = Vector(pl["loc"])
    lo.rotation_euler = Vector(pl["dir"]).to_track_quat("-Z", "Y").to_euler()
    sc.collection.objects.link(lo)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
cam.data.clip_start = 0.01
sc.collection.objects.link(cam)
sc.camera = cam
for v in VIEWS:
    c = SPEC["cameras"][v]
    eye, tgt = Vector(c["loc"]), Vector(c["target"])
    f = (tgt - eye).normalized()
    up = Vector(c.get("up", (0, 0, 1)))
    r = f.cross(up).normalized()
    u = r.cross(f)
    cam.matrix_world = Matrix.Translation(eye) @ Matrix((r, u, -f)).transposed().to_4x4()
    cam.data.angle = math.radians(c.get("fov", 90))
    sc.render.filepath = os.path.join(OUT, f"stock_{v}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", v)
