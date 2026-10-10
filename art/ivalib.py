"""Shared building blocks for the interior generators (Blender 5.2, run with blender -b --python).

Import from a generator after putting this folder on sys.path:
    sys.path.insert(0, os.path.dirname(__file__)); import ivalib as L
    L.begin("Conical1vInterior", tex_dir)
Then use L.M[...] materials and the mesh helpers. Material names match the Mk1-3 (IVA_*) so the Unity setup
tool and shared textures work unchanged; new pod-specific materials are added with L.material(...).
"""
import math
import os

import bpy  # must come before bmesh/mathutils
import bmesh
from mathutils import Matrix, Vector

COLL = None
TEX = None
M = {}
_images = {}


def begin(collection_name, tex_dir):
    global COLL, TEX
    bpy.ops.wm.read_factory_settings(use_empty=True)
    TEX = tex_dir
    COLL = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(COLL)
    _images.clear()
    M.clear()
    M.update(_standard_materials())
    return COLL


def link(obj):
    COLL.objects.link(obj)
    return obj


# ------------------------------------------------------------------ materials
def image(name, colour=True):
    key = (name, colour)
    if key not in _images:
        img = bpy.data.images.load(os.path.join(TEX, name))
        if not colour:
            img.colorspace_settings.name = "Non-Color"
        _images[key] = img
    return _images[key]


def material(name, colour=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, tex=None, normal=None,
             emit=0.0, emit_tex=False, uv_scale=None, normal_strength=1.0):
    m = bpy.data.materials.new(name)
    if m.node_tree is None:  # node trees are always on from Blender 6; use_nodes is deprecated in 5.x
        m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    mapping = None
    if uv_scale:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = (uv_scale[0], uv_scale[1], 1)
        nt.links.new(tc.outputs["UV"], mapping.inputs["Vector"])
    if tex:
        ti = nt.nodes.new("ShaderNodeTexImage")
        ti.image = image(tex)
        if mapping:
            nt.links.new(mapping.outputs["Vector"], ti.inputs["Vector"])
        nt.links.new(ti.outputs["Color"], bsdf.inputs["Base Color"])
        if emit_tex:
            nt.links.new(ti.outputs["Color"], bsdf.inputs["Emission Color"])
    if normal:
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = image(normal, colour=False)
        if mapping:
            nt.links.new(mapping.outputs["Vector"], tn.inputs["Vector"])
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = normal_strength
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    if emit > 0:
        if not emit_tex:
            bsdf.inputs["Emission Color"].default_value = (*colour, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit
    return m


def _standard_materials():
    d = {
        "rib": material("IVA_Frame", (0.42, 0.43, 0.45), rough=0.45, metal=0.6),
        "ring": material("IVA_FrameDark", (0.16, 0.17, 0.19), rough=0.5, metal=0.4),
        "floor": material("IVA_FloorGrate", tex="grate_color.png", normal="grate_normal.png", rough=0.55, metal=0.6, uv_scale=(1.5, 1.5)),
        "console": material("IVA_Console", (0.10, 0.105, 0.115), rough=0.55, metal=0.2),
        "bezel": material("IVA_Bezel", (0.03, 0.03, 0.035), rough=0.35, metal=0.3),
        "cushion": material("IVA_Cushion", (0.30, 0.11, 0.07), rough=0.75, normal="quilt_normal.png", uv_scale=(2.5, 2.5), normal_strength=0.7),
        "couchframe": material("IVA_CouchFrame", (0.22, 0.23, 0.25), rough=0.4, metal=0.7),
        "strap": material("IVA_Strap", (0.12, 0.22, 0.42), rough=0.85),
        "buckle": material("IVA_Buckle", (0.75, 0.75, 0.72), rough=0.25, metal=1.0),
        "yellow": material("IVA_AccentYellow", (1.0, 0.70, 0.0), rough=0.35),
        "red": material("IVA_AccentRed", (0.82, 0.08, 0.05), rough=0.4),
        "hatch": material("IVA_Hatch", (0.62, 0.63, 0.64), rough=0.5, metal=0.3),
        "locker": material("IVA_Locker", tex="locker_color.png", normal="panel_normal.png", rough=0.62, metal=0.15, uv_scale=(1.5, 1.5), normal_strength=0.5),
        "handle": material("IVA_Handle", (0.08, 0.08, 0.08), rough=0.4),
        "light": material("IVA_LightStrip", (1.0, 0.92, 0.78), rough=0.3, emit=6.0),
        "btn_red": material("IVA_ButtonRed", (1.0, 0.15, 0.08), rough=0.3, emit=0.35),
        "btn_green": material("IVA_ButtonGreen", (0.2, 1.0, 0.35), rough=0.3, emit=0.35),
        "btn_amber": material("IVA_ButtonAmber", (1.0, 0.62, 0.08), rough=0.3, emit=0.35),
        "btn_blue": material("IVA_ButtonBlue", (0.2, 0.55, 1.0), rough=0.3, emit=0.35),
        "toggle": material("IVA_Toggle", (0.85, 0.85, 0.85), rough=0.2, metal=1.0),
        "navball": material("IVA_Navball", tex="navball.png", rough=0.25, emit=0.6, emit_tex=True),
        "crt_orbit": material("IVA_ScreenOrbit", tex="crt_orbit.png", rough=0.15, emit=2.2, emit_tex=True),
        "crt_data": material("IVA_ScreenData", tex="crt_data.png", rough=0.15, emit=2.2, emit_tex=True),
        "crt_att": material("IVA_ScreenAttitude", tex="crt_attitude.png", rough=0.15, emit=2.2, emit_tex=True),
        "labels": material("IVA_Labels", tex="labels.png", rough=0.6),
        "plate": material("IVA_Plate", tex="plate.png", rough=0.4, metal=0.5),
        "hazard": material("IVA_Hazard", tex="hazard.png", rough=0.5),
        "extinguisher": material("IVA_Extinguisher", (0.75, 0.05, 0.04), rough=0.3, metal=0.2),
        "cable": material("IVA_Cable", (0.05, 0.05, 0.05), rough=0.6),
    }
    for g in ("alt", "press", "temp", "fuel"):
        d["gauge_" + g] = material("IVA_Gauge_" + g, tex=f"gauge_{g}.png", rough=0.2)
    for g in ("alt", "press", "temp"):          # live gauges: face only, the needle is a mesh
        d["gauge_face_" + g] = material("IVA_GaugeFace_" + g, tex=f"gauge_{g}_face.png", rough=0.2)
    d["needle"] = material("IVA_Needle", (0.85, 0.22, 0.06), rough=0.35)
    return d


# ------------------------------------------------------------------ mesh helpers
def mesh_obj(name, bm, mat_list):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    for m in mat_list:
        obj.data.materials.append(m)
    return link(obj)


def smooth(obj, angle=35):
    for p in obj.data.polygons:
        p.use_smooth = True
    try:
        obj.data.set_sharp_from_angle(angle=math.radians(angle))
    except Exception:
        pass
    return obj


def add_bevel(obj, width=0.01, segs=3):
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = segs
    mod.limit_method = "ANGLE"
    mod.harden_normals = False
    return obj


def solidify(obj, thickness, offset=-1.0):
    sol = obj.modifiers.new("Thickness", "SOLIDIFY")
    sol.thickness = thickness
    sol.offset = offset
    return obj


def box(name, size, mat, loc=(0, 0, 0), rot=Matrix.Identity(3), bevel=0.0, segs=3):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    uv = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            co = l.vert.co
            a, b = [(1, 2), (0, 2), (0, 1)][ax]
            l[uv].uv = (co[a] + 0.5, co[b] + 0.5)
    obj = mesh_obj(name, bm, [mat])
    obj.matrix_world = Matrix.Translation(Vector(loc)) @ rot.to_4x4()
    if bevel > 0:
        add_bevel(obj, bevel, segs)
    return smooth(obj)


def cylinder(name, radius, depth, mat, loc=(0, 0, 0), rot=Matrix.Identity(3), segs=24, bevel=0.0, radius2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=radius,
                          radius2=radius if radius2 is None else radius2, depth=depth)
    uv = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for l in f.loops:
            co = l.vert.co
            if abs(f.normal.z) > 0.9:
                l[uv].uv = (0.5 + 0.5 * co.x / radius, 0.5 + 0.5 * co.y / radius)
            else:
                l[uv].uv = ((math.atan2(co.y, co.x) / (2 * math.pi)) % 1.0, co.z / depth + 0.5)
    obj = mesh_obj(name, bm, [mat])
    obj.matrix_world = Matrix.Translation(Vector(loc)) @ rot.to_4x4()
    if bevel > 0:
        add_bevel(obj, bevel, 2)
    return smooth(obj, 50)


def sphere(name, radius, mat, loc, rot=Matrix.Identity(3), u=24, v=12):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=radius, calc_uvs=True)
    bm.to_mesh(me)
    bm.free()
    obj = link(bpy.data.objects.new(name, me))
    obj.data.materials.append(mat)
    obj.matrix_world = Matrix.Translation(Vector(loc)) @ rot.to_4x4()
    return smooth(obj, 90)


def disc(name, radius, mat, loc, rot, segs=48):
    bm = bmesh.new()
    verts = [bm.verts.new((radius * math.cos(2 * math.pi * i / segs), radius * math.sin(2 * math.pi * i / segs), 0)) for i in range(segs)]
    f = bm.faces.new(verts)
    uv = bm.loops.layers.uv.new("UVMap")
    for l in f.loops:
        l[uv].uv = (0.5 + 0.5 * l.vert.co.x / radius, 0.5 + 0.5 * l.vert.co.y / radius)
    obj = mesh_obj(name, bm, [mat])
    obj.matrix_world = Matrix.Translation(Vector(loc)) @ rot.to_4x4()
    return obj


def plane(name, w, h, mat, loc, rot, uv_rect=(0, 0, 1, 1)):
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in ((-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0))]
    f = bm.faces.new(vs)
    uv = bm.loops.layers.uv.new("UVMap")
    u0, v0, u1, v1 = uv_rect
    for l, (u, v) in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
        l[uv].uv = (u, v)
    obj = mesh_obj(name, bm, [mat])
    obj.matrix_world = Matrix.Translation(Vector(loc)) @ rot.to_4x4()
    return obj


def torus(name, major, minor, mat, loc, rot, seg=32, mseg=8):
    bm = bmesh.new()
    rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ring = []
        for j in range(mseg):
            b = 2 * math.pi * j / mseg
            r = major + minor * math.cos(b)
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), minor * math.sin(b))))
        rings.append(ring)
    for i in range(seg):
        for j in range(mseg):
            a, b = rings[i][j], rings[(i + 1) % seg][j]
            c, d = rings[(i + 1) % seg][(j + 1) % mseg], rings[i][(j + 1) % mseg]
            bm.faces.new((a, b, c, d))
    bm.normal_update()
    obj = mesh_obj(name, bm, [mat])
    obj.matrix_world = Matrix.Translation(Vector(loc)) @ rot.to_4x4()
    return smooth(obj, 80)


def tube(name, points, radius, mat, closed=False, bevel_res=2):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = bevel_res
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for p, co in zip(sp.points, points):
        p.co = (co[0], co[1], co[2], 1)
    sp.use_cyclic_u = closed
    obj = bpy.data.objects.new(name, cu)
    link(obj)
    obj.data.materials.append(mat)
    return obj


def basis(right, up, normal):
    return Matrix((right, up, normal)).transposed()


def seat_marker(index, loc, yaw=0.0, pitch=0.0):
    """IVA_Seat<n> eye point for the game (identity rotation = looking at the cabin front, -Y)."""
    e = bpy.data.objects.new(f"IVA_Seat{index}", None)
    e.empty_display_type = "ARROWS"
    e.empty_display_size = 0.08
    e.matrix_world = Matrix.Translation(Vector(loc)) @ Matrix.Rotation(yaw, 4, "Z") @ Matrix.Rotation(pitch, 4, "X")
    return link(e)


def save(path):
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print("objects", len(COLL.objects), "saved", path)
