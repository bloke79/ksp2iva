"""Exports a generated interior for Unity (generic version of export_mk13.py).

Usage: blender -b --python export_interior.py -- <in.blend> <out_dir> <spec.json>
Writes <out_dir>/<interior>.fbx (one mesh per material, plus the IVA_Seat* eye points) and
<out_dir>/materials.json for the "IVA > Set Up Interiors" editor tool.
"""
import json
import os
import sys

import bpy

ARGS = sys.argv[sys.argv.index("--") + 1:]
BLEND, OUT, SPEC = ARGS[0], ARGS[1], json.load(open(ARGS[2]))
NAME = SPEC["interior"]
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()

# ---------------------------------------------------------------- bake every mesh/curve into world-space meshes
baked = {}
sources = [o for o in scene.objects if o.type in {"MESH", "CURVE"}]
for obj in sources:
    ev = obj.evaluated_get(depsgraph)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=depsgraph)
    me.transform(obj.matrix_world)
    if obj.matrix_world.determinant() < 0:
        me.flip_normals()
    mats = [s.material for s in obj.material_slots if s.material] or [None]
    name = mats[0].name if mats[0] else "IVA_Default"
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    baked.setdefault(name, []).append((me, mats))
for obj in sources:
    bpy.data.objects.remove(obj, do_unlink=True)

coll = bpy.data.collections.new("Export")
scene.collection.children.link(coll)
tri_total = 0
joined = []
for mat_name, items in baked.items():
    objs = []
    for i, (me, mats) in enumerate(items):
        o = bpy.data.objects.new(f"{mat_name}_{i}", me)
        coll.objects.link(o)
        o.data.materials.clear()
        o.data.materials.append(bpy.data.materials.get(mat_name))
        for p in o.data.polygons:
            p.material_index = 0
        objs.append(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.name = mat_name.replace("IVA_", "Mesh_")
    j.data.name = j.name
    tris = sum(len(p.vertices) - 2 for p in j.data.polygons)
    tri_total += tris
    joined.append((j.name, tris))
for name, tris in sorted(joined, key=lambda x: -x[1])[:12]:
    print(f"  {name:28s} {tris:7d} tris")
print("total triangles", tri_total)

root = bpy.data.objects.new(NAME, None)
coll.objects.link(root)
for o in list(coll.objects):
    if o is not root:
        o.parent = root
for o in scene.objects:
    if o.name.startswith("IVA_Seat"):
        if o.name not in coll.objects:
            for c in o.users_collection:
                c.objects.unlink(o)
            coll.objects.link(o)
        mw = o.matrix_world.copy()
        o.parent = root
        o.matrix_world = mw


def principled_info(mat):
    info = {"name": mat.name, "color": [0.8, 0.8, 0.8], "metallic": 0.0, "roughness": 0.5,
            "emission": [0, 0, 0], "emissionStrength": 0.0, "texture": None, "normal": None,
            "normalStrength": 1.0, "tiling": [1.0, 1.0], "emissionFromTexture": False}
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    info["color"] = list(bsdf.inputs["Base Color"].default_value)[:3]
    info["metallic"] = bsdf.inputs["Metallic"].default_value
    info["roughness"] = bsdf.inputs["Roughness"].default_value
    info["emission"] = list(bsdf.inputs["Emission Color"].default_value)[:3]
    info["emissionStrength"] = bsdf.inputs["Emission Strength"].default_value
    for n in nt.nodes:
        if n.type == "TEX_IMAGE" and n.image:
            # filepaths are stored relative ("//textures\x.png"); bpy.path.basename handles that, the image name is the fallback
            fname = bpy.path.basename(n.image.filepath) or n.image.name
            if n.image.colorspace_settings.name == "Non-Color":
                info["normal"] = fname
            else:
                info["texture"] = fname
                info["emissionFromTexture"] = any(l.to_socket.name == "Emission Color" for l in n.outputs["Color"].links)
        if n.type == "MAPPING":
            s = n.inputs["Scale"].default_value
            info["tiling"] = [s[0], s[1]]
        if n.type == "NORMAL_MAP":
            info["normalStrength"] = n.inputs["Strength"].default_value
    return info


used = {o.data.materials[0].name for o in coll.objects if o.type == "MESH" and o.data.materials}
mats = [principled_info(m) for m in bpy.data.materials if m.name in used]
seats = [{"name": o.name, "position": list(o.matrix_world.translation)}
         for o in sorted([o for o in scene.objects if o.name.startswith("IVA_Seat")], key=lambda o: o.name)]
prof = sorted(SPEC["profile"])
# cabin light in Unity space (Blender x, y, z -> Unity -x, z, -y), with range and intensity
cl = SPEC.get("cabin_light")
cabin_light = ([-cl["position"][0], cl["position"][2], -cl["position"][1], cl.get("range", 2.6), cl.get("intensity", 1.0)]
               if cl else [0.0, 1.55, 0.0, 2.6, 1.0])
with open(os.path.join(OUT, "materials.json"), "w") as f:
    json.dump({"interior": NAME, "address": SPEC["address"],
               "design": {"part": SPEC["part"], "baseRadius": prof[0][1], "topRadius": prof[-1][1], "height": prof[-1][0], "seats": SPEC["seats"]},
               "materials": mats, "seats_blender": seats, "cabinLight": cabin_light}, f, indent=2)
print("materials", len(mats))

bpy.ops.export_scene.fbx(
    filepath=os.path.join(OUT, f"{NAME}.fbx"),
    use_selection=False,
    object_types={"MESH", "EMPTY"},
    axis_forward="-Z", axis_up="Y",
    bake_space_transform=True,
    apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_UNITS",
    mesh_smooth_type="OFF",
    use_mesh_modifiers=True,
    add_leaf_bones=False,
    path_mode="STRIP",
    embed_textures=False,
)
print("exported", os.path.join(OUT, f"{NAME}.fbx"))
