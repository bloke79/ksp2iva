"""Surface detail for the generated interiors: swaps plain-colour materials for textured ones (a neutral detail texture
tinted by the original colour, so one texture serves every grey), and gives the affected meshes world-scale UVs so the
detail is the same size everywhere.

Detail textures (texgen.py): detail_painted (painted metal: orange peel, mottling, smudges, fine scratches) and
detail_brushed (brushed metal: directional grain, scratches). One texture tile covers 0.5 m.
"""
import ivalib as L  # imports bpy first
import bmesh
import bpy
from mathutils import Vector

# material name -> detail kind
DEFAULT = {
    "IVA_GreyLocker": "painted", "IVA_MidLocker": "painted", "IVA_MidPanel": "painted", "IVA_SeatFrame": "painted",
    "IVA_FrameDark": "painted", "IVA_Frame": "brushed", "IVA_CouchFrame": "brushed", "IVA_Locker": "painted",
    "IVA_Hatch": "painted", "IVA_SeatShell": "painted", "IVA_Jetpack": "painted", "IVA_Bottle": "painted",
    "IVA_Glareshield": "painted", "IVA_ModulePlate": "painted", "IVA_Tank": "brushed",
    "IVA_Soil": "fabric", "IVA_Leaf": "painted", "IVA_LeafLight": "painted",
    "IVA_Canvas": "fabric", "IVA_SleepingBag": "fabric", "IVA_Towel": "fabric", "IVA_StoolPad": "fabric",
}
TILE = 0.5   # metres per texture tile


def _info(mat):
    b = mat.node_tree.nodes.get("Principled BSDF")
    if b is None:
        return None
    if any(n.type == "TEX_IMAGE" for n in mat.node_tree.nodes):
        return None   # already textured
    return (tuple(b.inputs["Base Color"].default_value)[:3], b.inputs["Roughness"].default_value, b.inputs["Metallic"].default_value)


def world_uvs(obj):
    """Planar UVs from world position by each face's dominant axis, in TILE-sized units."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.active or bm.loops.layers.uv.new("UVMap")
    mw = obj.matrix_world
    n3 = mw.to_3x3().inverted_safe().transposed()
    for f in bm.faces:
        n = (n3 @ f.normal)
        ax = max(range(3), key=lambda i: abs(n[i]))
        a, b = [(1, 2), (0, 2), (0, 1)][ax]
        for l in f.loops:
            w = mw @ l.vert.co
            l[uv].uv = (w[a] / TILE, w[b] / TILE)
    bm.to_mesh(me)
    bm.free()


def apply(kinds=None):
    kinds = kinds or DEFAULT
    swap = {}
    for m in list(bpy.data.materials):
        if m.name in kinds and m.node_tree is not None:
            inf = _info(m)
            if inf is None:
                continue
            col, rough, metal = inf
            k = kinds[m.name]
            swap[m.name] = L.material(m.name + "Detail", col, rough=rough, metal=metal, tex=f"detail_{k}_color.png",
                                      normal=f"detail_{k}_normal.png", normal_strength=1.4, tint=True)
    n = 0
    for o in L.COLL.objects:
        if o.type != "MESH" or not o.data.materials:
            continue
        hit = False
        for i, m in enumerate(o.data.materials):
            if m is not None and m.name in swap:
                o.data.materials[i] = swap[m.name]
                hit = True
        if hit:
            world_uvs(o)
            n += 1
    print(f"surfaces: {len(swap)} materials detailed on {n} objects")
