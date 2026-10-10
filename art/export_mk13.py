"""Exports the Mk1-3 interior for Unity.

Usage: python3 export_mk13.py <in.blend> <out_dir>

Writes <out_dir>/Mk13Interior.fbx (one mesh per material, plus the IVA_Seat* eye points) and
<out_dir>/materials.json describing each material for the Unity setup script.
"""
import json
import os
import sys

import bpy
from mathutils import Matrix

BLEND, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()

# ---------------------------------------------------------------- bake every mesh/curve into world-space meshes
baked = {}   # material name -> list of mesh datablocks
sources = [o for o in scene.objects if o.type in {"MESH", "CURVE"}]
for obj in sources:
    ev = obj.evaluated_get(depsgraph)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=depsgraph)
    me.transform(obj.matrix_world)
    if obj.matrix_world.determinant() < 0:
        me.flip_normals()
    mats = [s.material for s in obj.material_slots if s.material] or [None]
    name = mats[0].name if mats[0] else "IVA_Default"
    # curves come out without UVs; give them one so all joined meshes share a UV layer
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    baked.setdefault(name, []).append((me, mats))

# remove the originals
for obj in sources:
    bpy.data.objects.remove(obj, do_unlink=True)

coll = bpy.data.collections.new("Export")
scene.collection.children.link(coll)
tri_total = 0
joined_objects = []
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
    # join into one object per material
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
    joined_objects.append((j.name, tris))

for name, tris in sorted(joined_objects, key=lambda x: -x[1]):
    print(f"  {name:28s} {tris:7d} tris")
print("total triangles", tri_total)

# ---------------------------------------------------------------- root and seats
root = bpy.data.objects.new("Mk13Interior", None)
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

# ---------------------------------------------------------------- materials.json
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
            fname = os.path.basename(n.image.filepath)
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


mats = [principled_info(m) for m in bpy.data.materials if m.name.startswith("IVA_") and m.users > 0]
seats = []
for o in sorted([o for o in scene.objects if o.name.startswith("IVA_Seat")], key=lambda o: o.name):
    seats.append({"name": o.name, "position": list(o.matrix_world.translation)})
with open(os.path.join(OUT, "materials.json"), "w") as f:
    json.dump({"interior": "Mk13Interior", "address": "IVA/Interior_Mk1-3",
               "design": {"baseRadius": 1.25, "topRadius": 0.625, "height": 1.95, "seats": 3},
               "materials": mats, "seats_blender": seats}, f, indent=2)
print("materials", len(mats))

# ---------------------------------------------------------------- FBX for Unity (Y up, front = +Z in Unity)
bpy.ops.export_scene.fbx(
    filepath=os.path.join(OUT, "Mk13Interior.fbx"),
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
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "Mk13Interior_export.blend"))
print("exported", os.path.join(OUT, "Mk13Interior.fbx"))
