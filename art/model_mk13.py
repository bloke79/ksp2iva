"""Builds the Mk1-3 "Gumball" 3-seat pod interior in Blender.

Usage:  python3 model_mk13.py <texture_dir> <out.blend>

Coordinates: metres, Z up along the pod axis (Z=0 at the base of the pod), front of the cabin
faces -Y. The outer pod is a cone from 2.5 m across at the base to 1.25 m at the top, 1.95 m tall.
Everything is built from code so it can be regenerated and tuned.
"""
import math
import os
import sys

import bpy  # must come before bmesh/mathutils
import bmesh
from mathutils import Matrix, Vector

TEX = sys.argv[1]
OUT = sys.argv[2]

# ------------------------------------------------------------------ pod dimensions
R_BASE, R_TOP, H = 1.25, 0.625, 1.95
WALL = 0.07                 # interior wall sits this far inside the outer surface
Z_FLOOR = 0.15
Z_CEIL = 1.70               # ceiling, where the docking tunnel starts
TUNNEL_R = 0.42
SEG = 128                   # segments round the shell


def r_out(z):
    return R_BASE + (R_TOP - R_BASE) * (z / H)


def r_in(z):
    return r_out(z) - WALL


def polar(phi, r, z):
    """phi in radians, 0 = front (-Y), positive towards +X."""
    return Vector((r * math.sin(phi), -r * math.cos(phi), z))


# ------------------------------------------------------------------ scene reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
COLL = bpy.data.collections.new("Mk13Interior")
scene.collection.children.link(COLL)


def link(obj):
    COLL.objects.link(obj)
    return obj


# ------------------------------------------------------------------ materials
_images = {}


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


M = {
    "quilt": material("IVA_WallPadding", tex="quilt_color.png", normal="quilt_normal.png", rough=0.85, uv_scale=(1.0, 1.0)),
    "rib": material("IVA_Frame", (0.42, 0.43, 0.45), rough=0.45, metal=0.6),
    "ring": material("IVA_FrameDark", (0.16, 0.17, 0.19), rough=0.5, metal=0.4),
    "floor": material("IVA_FloorGrate", tex="grate_color.png", normal="grate_normal.png", rough=0.55, metal=0.6, uv_scale=(1.5, 1.5)),
    "tunnel": material("IVA_TunnelWhite", (0.86, 0.86, 0.84), rough=0.5),
    "console": material("IVA_Console", (0.10, 0.105, 0.115), rough=0.55, metal=0.2),
    "bezel": material("IVA_Bezel", (0.03, 0.03, 0.035), rough=0.35, metal=0.3),
    "cushion": material("IVA_Cushion", (0.88, 0.34, 0.05), rough=0.75, normal="quilt_normal.png", uv_scale=(2.5, 2.5), normal_strength=0.7),
    "couchframe": material("IVA_CouchFrame", (0.22, 0.23, 0.25), rough=0.4, metal=0.7),
    "strap": material("IVA_Strap", (0.12, 0.22, 0.42), rough=0.85),
    "buckle": material("IVA_Buckle", (0.75, 0.75, 0.72), rough=0.25, metal=1.0),
    "yellow": material("IVA_AccentYellow", (1.0, 0.70, 0.0), rough=0.35),
    "red": material("IVA_AccentRed", (0.82, 0.08, 0.05), rough=0.4),
    "hatch": material("IVA_Hatch", (0.62, 0.63, 0.64), rough=0.5, metal=0.3),
    "locker": material("IVA_Locker", (0.55, 0.56, 0.55), rough=0.6, metal=0.2),
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
    M["gauge_" + g] = material("IVA_Gauge_" + g, tex=f"gauge_{g}.png", rough=0.2)


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


def box(name, size, mat, loc=(0, 0, 0), rot=Matrix.Identity(3), bevel=0.0, segs=3):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    uv = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:  # simple box projection
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


def cylinder(name, radius, depth, mat, loc=(0, 0, 0), rot=Matrix.Identity(3), segs=24, bevel=0.0, cap_uv_disc=False):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=radius, radius2=radius, depth=depth)
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
    """Round tube along a 3D polyline, via a curve object converted to mesh."""
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


def wall_frame(phi, z):
    """Basis on the inner wall at (phi, z): right = tangent, up = along wall slope, normal = into cabin."""
    tangent = Vector((-math.cos(phi), -math.sin(phi), 0))   # "right" as seen from inside the cabin
    dz = 0.01
    up = (polar(phi, r_in(z + dz), z + dz) - polar(phi, r_in(z - dz), z - dz)).normalized()
    normal = tangent.cross(up).normalized()
    if normal.dot(Vector((-math.sin(phi), math.cos(phi), 0))) < 0:
        normal = -normal
    return tangent, up, normal


# ------------------------------------------------------------------ windows (openings in the shell)
class Window:
    def __init__(self, phi_deg, zc, half_w, half_h, corner):
        self.phi = math.radians(phi_deg)
        self.zc, self.hw, self.hh, self.corner = zc, half_w, half_h, corner

    def sdf(self, phi, z):
        """Signed distance in metres on the wall surface (negative inside the opening)."""
        dphi = (phi - self.phi + math.pi) % (2 * math.pi) - math.pi
        s = dphi * r_in(z)
        qx = abs(s) - (self.hw - self.corner)
        qy = abs(z - self.zc) - (self.hh - self.corner)
        out = math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0)
        return out - self.corner

    def outline(self, inset=0.0, n=64):
        """Points round the opening, on the wall surface, pushed into the cabin by `inset`."""
        pts = []
        hw, hh, c = self.hw, self.hh, self.corner
        # rounded rectangle in (s, z) parameter space
        corners = [(hw - c, hh - c, 0), (-(hw - c), hh - c, 90), (-(hw - c), -(hh - c), 180), (hw - c, -(hh - c), 270)]
        for cx, cy, a0 in corners:
            for i in range(n // 4 + 1):
                a = math.radians(a0 + 90 * i / (n // 4))
                s = cx + c * math.cos(a)
                z = self.zc + cy + c * math.sin(a)
                phi = self.phi + s / r_in(z)
                pts.append(polar(phi, r_in(z) - inset, z))
        return pts


WINDOWS = [
    Window(-19, 1.33, 0.17, 0.15, 0.06),   # forward left (rendezvous)
    Window(19, 1.33, 0.17, 0.15, 0.06),    # forward right
    Window(88, 1.05, 0.13, 0.12, 0.05),    # right side
    Window(-90, 1.02, 0.11, 0.10, 0.05),   # hatch window (left)
]
HATCH_PHI = math.radians(-90)


# ------------------------------------------------------------------ shell
def build_shell():
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rings = int((Z_CEIL - Z_FLOOR) / 0.028)
    zs = [Z_FLOOR - 0.02 + (Z_CEIL + 0.02 - (Z_FLOOR - 0.02)) * i / rings for i in range(rings + 1)]
    grid = []
    for z in zs:
        row = []
        for j in range(SEG):
            phi = 2 * math.pi * j / SEG
            row.append(bm.verts.new(polar(phi, r_in(z), z)))
        grid.append(row)
    circ = 2 * math.pi * r_in(1.0)
    for i in range(rings):
        for j in range(SEG):
            phi_c = 2 * math.pi * (j + 0.5) / SEG
            z_c = 0.5 * (zs[i] + zs[i + 1])
            if any(w.sdf(phi_c, z_c) < 0 for w in WINDOWS):
                continue
            jn = (j + 1) % SEG
            f = bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][jn], grid[i][jn]))
            for l in f.loops:
                vj = grid[i].index(l.vert) if l.vert in grid[i] else grid[i + 1].index(l.vert)
                u = (vj if not (j == SEG - 1 and vj == 0) else SEG) / SEG * circ / 0.9
                l[uv].uv = (u, l.vert.co.z / 0.9)
    bm.normal_update()
    # faces should point into the cabin
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(Vector((-c.x, -c.y, 0))) < 0:
            f.normal_flip()
    obj = mesh_obj("Shell", bm, [M["quilt"]])
    sol = obj.modifiers.new("Thickness", "SOLIDIFY")
    sol.thickness = 0.04
    sol.offset = -1.0      # grows away from the face normal, i.e. outwards
    return smooth(obj, 30)


def build_ribs():
    angles = [i * 30 for i in range(12)]
    for a in angles:
        phi = math.radians(a + 15)
        # skip ribs that would cross a window or the hatch
        if any(abs(((phi - w.phi + math.pi) % (2 * math.pi)) - math.pi) * r_in(w.zc) < w.hw + 0.06 for w in WINDOWS):
            continue
        if abs(((phi - HATCH_PHI + math.pi) % (2 * math.pi)) - math.pi) < math.radians(22):
            continue
        z0, z1 = Z_FLOOR, Z_CEIL
        p0, p1 = polar(phi, r_in(z0) - 0.03, z0), polar(phi, r_in(z1) - 0.03, z1)
        mid = (p0 + p1) / 2
        up = (p1 - p0).normalized()
        tangent = Vector((math.cos(phi), math.sin(phi), 0))
        normal = tangent.cross(up).normalized()
        box(f"Rib_{a}", (0.07, (p1 - p0).length, 0.06), M["rib"], mid, basis(tangent, up, normal), bevel=0.012)
        # cable bundle beside the rib
        off = tangent * 0.06
        tube(f"Cable_{a}", [polar(phi + 0.07, r_in(z) - 0.035, z) for z in (z0 + 0.05, 0.6, 1.1, z1 - 0.05)], 0.012, M["cable"])
    # horizontal frame rings
    for z, mat in ((0.48, M["ring"]), (Z_CEIL - 0.02, M["ring"])):
        pts = []
        for j in range(SEG + 1):
            phi = 2 * math.pi * j / SEG
            if any(w.sdf(phi, z) < 0.05 for w in WINDOWS):
                if pts:
                    tube(f"Ring_{z:.2f}_{j}", pts, 0.02, mat)
                pts = []
                continue
            pts.append(polar(phi, r_in(z) - 0.02, z))
        if len(pts) > 1:
            tube(f"Ring_{z:.2f}_end", pts, 0.02, mat)


def build_window_frames():
    for i, w in enumerate(WINDOWS):
        tube(f"WindowFrame_{i}", w.outline(inset=0.015, n=40), 0.03, M["bezel"], closed=True, bevel_res=3)
        tube(f"WindowTrim_{i}", w.outline(inset=0.02, n=40), 0.012, M["rib"], closed=True)
        # bolts round the frame
        pts = w.outline(inset=0.0, n=16)
        for k, p in enumerate(pts[::2]):
            phi = math.atan2(p.x, -p.y)
            t, u, n = wall_frame(phi, p.z)
            outward = (p - polar(w.phi, r_in(w.zc), w.zc))
            outward = (outward - n * outward.dot(n)).normalized()
            cylinder(f"Bolt_{i}_{k}", 0.008, 0.015, M["buckle"], p + n * 0.012 + outward * 0.05, basis(t, u, n), segs=8)


def build_floor_ceiling():
    rf = r_in(Z_FLOOR)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    centre = bm.verts.new((0, 0, Z_FLOOR))
    ring = [bm.verts.new(polar(2 * math.pi * j / SEG, rf, Z_FLOOR)) for j in range(SEG)]
    for j in range(SEG):
        f = bm.faces.new((centre, ring[j], ring[(j + 1) % SEG]))
        for l in f.loops:
            l[uv].uv = (l.vert.co.x, l.vert.co.y)
    bm.normal_update()
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    fl = mesh_obj("Floor", bm, [M["floor"]])
    # floor rim
    tube("FloorRim", [polar(2 * math.pi * j / 64, rf - 0.03, Z_FLOOR + 0.02) for j in range(65)], 0.03, M["ring"])

    # ceiling annulus
    rc = r_in(Z_CEIL)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    outer = [bm.verts.new(polar(2 * math.pi * j / SEG, rc, Z_CEIL)) for j in range(SEG)]
    inner = [bm.verts.new(polar(2 * math.pi * j / SEG, TUNNEL_R, Z_CEIL)) for j in range(SEG)]
    for j in range(SEG):
        jn = (j + 1) % SEG
        f = bm.faces.new((outer[j], outer[jn], inner[jn], inner[j]))
        for l in f.loops:
            l[uv].uv = (l.vert.co.x, l.vert.co.y)
    bm.normal_update()
    for f in bm.faces:
        if f.normal.z > 0:
            f.normal_flip()
    mesh_obj("Ceiling", bm, [M["quilt"]])

    # docking tunnel
    tz0, tz1 = Z_CEIL, H - 0.06
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    lo = [bm.verts.new(polar(2 * math.pi * j / 48, TUNNEL_R, tz0)) for j in range(48)]
    hi = [bm.verts.new(polar(2 * math.pi * j / 48, TUNNEL_R, tz1)) for j in range(48)]
    for j in range(48):
        jn = (j + 1) % 48
        f = bm.faces.new((lo[j], hi[j], hi[jn], lo[jn]))
        for l in f.loops:
            l[uv].uv = (j / 48, l.vert.co.z)
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(Vector((-c.x, -c.y, 0))) < 0:
            f.normal_flip()
    mesh_obj("Tunnel", bm, [M["tunnel"]])
    tube("TunnelLip", [polar(2 * math.pi * j / 48, TUNNEL_R, tz0 - 0.005) for j in range(49)], 0.025, M["ring"])
    # top hatch with wheel
    disc("TopHatch", TUNNEL_R, M["hatch"], (0, 0, tz1), Matrix.Rotation(math.pi, 3, "X"))
    torus("TopHatchWheel", 0.14, 0.014, M["yellow"], (0, 0, tz1 - 0.06), Matrix.Identity(3))
    for k in range(4):
        a = k * math.pi / 2
        tube(f"TopWheelSpoke_{k}", [(0, 0, tz1 - 0.06), (0.14 * math.cos(a), 0.14 * math.sin(a), tz1 - 0.06)], 0.009, M["yellow"])
    cylinder("TopWheelHub", 0.03, 0.05, M["handle"], (0, 0, tz1 - 0.04))
    # ladder rungs in the tunnel (towards the back)
    for k in range(3):
        z = tz0 + 0.06 + k * 0.07
        phi0, phi1 = math.radians(160), math.radians(200)
        tube(f"Rung_{k}", [polar(phi0, TUNNEL_R - 0.05, z), polar(phi0, TUNNEL_R - 0.08, z), polar(phi1, TUNNEL_R - 0.08, z), polar(phi1, TUNNEL_R - 0.05, z)], 0.012, M["yellow"])


# ------------------------------------------------------------------ hatch (left side)
def build_hatch():
    phi0, phi1 = HATCH_PHI - math.radians(17), HATCH_PHI + math.radians(17)
    z0, z1 = 0.52, 1.30
    inset, thick = 0.025, 0.035
    win = WINDOWS[3]
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    ns, nz = 24, 36
    grid = [[bm.verts.new(polar(phi0 + (phi1 - phi0) * j / ns, r_in(z0 + (z1 - z0) * i / nz) - inset, z0 + (z1 - z0) * i / nz))
             for j in range(ns + 1)] for i in range(nz + 1)]
    for i in range(nz):
        for j in range(ns):
            phi_c = phi0 + (phi1 - phi0) * (j + 0.5) / ns
            z_c = z0 + (z1 - z0) * (i + 0.5) / nz
            if win.sdf(phi_c, z_c) < 0:
                continue
            f = bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
            for l in f.loops:
                l[uv].uv = (l.vert.co.y, l.vert.co.z)
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(Vector((-c.x, -c.y, 0))) < 0:
            f.normal_flip()
    obj = mesh_obj("HatchDoor", bm, [M["hatch"]])
    sol = obj.modifiers.new("Thickness", "SOLIDIFY")
    sol.thickness = thick
    add_bevel(obj, 0.008, 2)
    smooth(obj, 30)
    # perimeter seal and hinges
    edge = []
    for t in range(41):
        edge.append(polar(phi0 + (phi1 - phi0) * t / 40, r_in(z0) - inset - 0.02, z0))
    for t in range(1, 41):
        z = z0 + (z1 - z0) * t / 40
        edge.append(polar(phi1, r_in(z) - inset - 0.02, z))
    for t in range(1, 41):
        edge.append(polar(phi1 - (phi1 - phi0) * t / 40, r_in(z1) - inset - 0.02, z1))
    for t in range(1, 40):
        z = z1 - (z1 - z0) * t / 40
        edge.append(polar(phi0, r_in(z) - inset - 0.02, z))
    tube("HatchSeal", edge, 0.018, M["ring"], closed=True)
    for z in (0.65, 1.15):
        t, u, n = wall_frame(phi1, z)
        box(f"HatchHinge_{z}", (0.05, 0.1, 0.05), M["rib"], polar(phi1 + 0.02, r_in(z) - 0.07, z), basis(t, u, n), bevel=0.01)
    # wheel handle
    zc = 0.78
    t, u, n = wall_frame(HATCH_PHI, zc)
    c = polar(HATCH_PHI, r_in(zc) - 0.1, zc)
    torus("HatchWheel", 0.11, 0.013, M["yellow"], c, basis(t, u, n))
    for k in range(3):
        a = k * 2 * math.pi / 3
        tube(f"HatchSpoke_{k}", [c, c + (t * math.cos(a) + u * math.sin(a)) * 0.11], 0.008, M["yellow"])
    cylinder("HatchHub", 0.03, 0.06, M["handle"], c - n * 0.01, basis(t, u, n))
    cylinder("HatchShaft", 0.012, 0.06, M["rib"], c - n * 0.04, basis(t, u, n))
    # hazard plate under the window
    t, u, n = wall_frame(HATCH_PHI, 0.9)
    plane("HatchHazard", 0.26, 0.05, M["hazard"], polar(HATCH_PHI, r_in(0.9) - inset - 0.037, 0.9), basis(t, u, n), (0, 0, 1, 0.5))


# ------------------------------------------------------------------ console
CONSOLE_PHI = math.radians(56)
# cross-section: (distance in from the wall, height)
CONSOLE_PROFILE = [(0.0, 0.62), (0.30, 0.64), (0.40, 0.72), (0.40, 0.76), (0.22, 1.12), (0.0, 1.16)]
FACE_A, FACE_B = (0.40, 0.76), (0.22, 1.12)   # the angled face towards the crew


def console_point(phi, d, z):
    return polar(phi, r_in(z) - d, z)


def face_point(phi, t, lift=0.0):
    d = FACE_A[0] + (FACE_B[0] - FACE_A[0]) * t
    z = FACE_A[1] + (FACE_B[1] - FACE_A[1]) * t
    p = console_point(phi, d, z)
    pa = console_point(phi, *FACE_A)
    pb = console_point(phi, *FACE_B)
    up = (pb - pa).normalized()
    tangent = Vector((-math.cos(phi), -math.sin(phi), 0))   # "right" as seen by the crew
    normal = tangent.cross(up).normalized()
    if normal.dot(Vector((-math.sin(phi), math.cos(phi), 0))) < 0:
        normal = -normal
    return p + normal * lift, basis(tangent, up, normal)


def build_console():
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    ns = 64
    rows = []
    for j in range(ns + 1):
        phi = -CONSOLE_PHI + 2 * CONSOLE_PHI * j / ns
        rows.append([bm.verts.new(console_point(phi, d, z)) for d, z in CONSOLE_PROFILE])
    npf = len(CONSOLE_PROFILE)
    for j in range(ns):
        for k in range(npf - 1):
            f = bm.faces.new((rows[j][k], rows[j][k + 1], rows[j + 1][k + 1], rows[j + 1][k]))
            for l in f.loops:
                l[uv].uv = (j / ns, k / npf)
    # end caps
    for row in (rows[0], rows[-1]):
        bm.faces.new(row)
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = mesh_obj("Console", bm, [M["console"]])
    add_bevel(obj, 0.012, 3)
    smooth(obj, 30)
    # chrome edge trim along the top and front lips
    for name, (d, z) in (("ConsoleTrimTop", (0.22, 1.12)), ("ConsoleTrimFront", (0.40, 0.76))):
        tube(name, [console_point(-CONSOLE_PHI + 2 * CONSOLE_PHI * j / 48, d + 0.005, z) for j in range(49)], 0.012, M["rib"])


def console_end_panels():
    """Detail on the two flat ends of the console: circuit-breaker grid and a label plate."""
    for side in (-1, 1):
        phi = side * CONSOLE_PHI
        # the end cap lies in the plane through the pod axis at angle phi; its normal is the tangent
        t = Vector((math.cos(phi), math.sin(phi), 0)) * side
        z = 0.90
        d = 0.20
        centre = polar(phi, r_in(z) - d, z) + t * 0.004
        radial_in = Vector((-math.sin(phi), math.cos(phi), 0))
        up = Vector((0, 0, 1))
        bx = basis(radial_in * side, up, t)  # right, up, normal; right x up = normal, so text isn't mirrored
        box(f"EndPanel{side}", (0.30, 0.38, 0.01), M["ring"], centre, bx, bevel=0.004)
        for row in range(5):
            for col in range(4):
                q = centre + bx.col[0] * (-0.09 + col * 0.06) + bx.col[1] * (0.12 - row * 0.06) + t * 0.01
                cylinder(f"Breaker{side}_{row}_{col}", 0.011, 0.02, M["bezel"], q, bx, segs=12)
                cylinder(f"BreakerCap{side}_{row}_{col}", 0.006, 0.012, M["toggle"], q + t * 0.012, bx, segs=10)
        plane(f"EndLabel{side}", 0.2, 0.05, M["plate"], centre + bx.col[1] * 0.16 + t * 0.008, bx)


def instrument_panel():
    # navball, centre
    p, b = face_point(0.0, 0.42, lift=0.0)
    n = b.col[2]
    sph = bpy.data.meshes.new("Navball")
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=0.105, calc_uvs=True)
    bm.to_mesh(sph)
    bm.free()
    nav = bpy.data.objects.new("Navball", sph)
    link(nav)
    nav.data.materials.append(M["navball"])
    # tilt so the horizon faces the crew, heading slightly rotated for interest
    nav.matrix_world = Matrix.Translation(p + n * 0.02) @ Matrix.Rotation(math.radians(-8), 4, "X") @ Matrix.Rotation(math.radians(25), 4, "Z")
    smooth(nav, 90)
    torus("NavballBezel", 0.118, 0.022, M["bezel"], p + n * 0.035, b)
    torus("NavballRing", 0.135, 0.008, M["rib"], p + n * 0.03, b)
    # heading marker
    # KSP-style orange chevron marking the craft's nose
    for side in (-1, 1):
        arm = basis((b.col[0] * math.cos(math.radians(35)) + b.col[1] * side * math.sin(math.radians(35))).normalized(),
                    (b.col[1] * math.cos(math.radians(35)) - b.col[0] * side * math.sin(math.radians(35))).normalized(), b.col[2])
        box(f"NavballChevron{side}", (0.05, 0.01, 0.008), M["btn_amber"], p + n * 0.128 + b.col[0] * side * 0.019 - b.col[1] * 0.012, arm)
    box("NavballDot", (0.012, 0.012, 0.008), M["btn_amber"], p + n * 0.128, b)

    # screens either side
    for phi_deg, mat, name in ((-24, M["crt_data"], "ScreenData"), (24, M["crt_orbit"], "ScreenOrbit"), (-44, M["crt_att"], "ScreenAttitude")):
        phi = math.radians(phi_deg)
        p, b = face_point(phi, 0.55, lift=0.006)
        w, h = (0.26, 0.17) if abs(phi_deg) < 30 else (0.18, 0.12)
        box(name + "Bezel", (w + 0.045, h + 0.045, 0.03), M["bezel"], p - b.col[2] * 0.008, b, bevel=0.008)
        plane(name, w, h, mat, p + b.col[2] * 0.0085, b)
        # softkeys under the screen
        for k in range(5):
            u = -w / 2 + w * (k + 0.5) / 5
            q = p + b.col[0] * u - b.col[1] * (h / 2 + 0.035)
            box(f"{name}_Key{k}", (0.03, 0.018, 0.012), M["bezel"], q, b, bevel=0.003)

    # gauges on the right wing
    for k, (g, t) in enumerate((("alt", 0.72), ("press", 0.32), ("temp", 0.72), ("fuel", 0.32))):
        phi = math.radians(40 + (k // 2) * 9)
        p, b = face_point(phi, t, lift=0.004)
        disc(f"Gauge_{g}", 0.048, M["gauge_" + g], p + b.col[2] * 0.006, b)
        torus(f"GaugeBezel_{g}", 0.052, 0.008, M["bezel"], p + b.col[2] * 0.006, b, seg=32, mseg=8)

    # toggle switch banks with guards, lower row
    for bank, phi_deg in enumerate((-12, 10)):
        for k in range(6):
            phi = math.radians(phi_deg + k * 2.6)
            p, b = face_point(phi, 0.12, lift=0.0)
            box(f"ToggleBase_{bank}_{k}", (0.02, 0.03, 0.012), M["bezel"], p + b.col[2] * 0.004, b, bevel=0.002)
            lever = basis(b.col[0], (b.col[1] * 0.5 + b.col[2]).normalized(), (b.col[2] * 0.5 - b.col[1]).normalized())
            cylinder(f"Toggle_{bank}_{k}", 0.004, 0.04, M["toggle"], p + b.col[2] * 0.02 + b.col[1] * 0.006, lever, segs=10)
            if k in (0, 5):
                # flip guard
                tube(f"Guard_{bank}_{k}", [p - b.col[0] * 0.014, p - b.col[0] * 0.014 + b.col[2] * 0.035,
                                          p + b.col[0] * 0.014 + b.col[2] * 0.035, p + b.col[0] * 0.014], 0.003, M["red"])

    # big buttons: abort (red), stage (amber), plus labels from the atlas
    cells = {"ABORT": 0, "STAGE": 1, "SAS": 2, "RCS": 3, "GEAR": 4, "LIGHTS": 5, "BRAKES": 6, "CHUTES": 7}
    buttons = [("ABORT", -34, 0.18, M["btn_red"], 0.03), ("STAGE", 34, 0.12, M["btn_amber"], 0.03),
               ("SAS", -5, 0.88, M["btn_green"], 0.016), ("RCS", 0, 0.88, M["btn_green"], 0.016),
               ("GEAR", 5, 0.88, M["btn_amber"], 0.016), ("LIGHTS", 10, 0.88, M["btn_blue"], 0.016),
               ("BRAKES", -10, 0.88, M["btn_red"], 0.016), ("CHUTES", 15, 0.88, M["btn_amber"], 0.016)]
    for label, phi_deg, t, mat, radius in buttons:
        phi = math.radians(phi_deg)
        p, b = face_point(phi, t, lift=0.0)
        cylinder(f"Btn_{label}_Collar", radius + 0.008, 0.012, M["bezel"], p + b.col[2] * 0.004, b, segs=24)
        cylinder(f"Btn_{label}", radius, 0.016 if radius > 0.02 else 0.012, mat, p + b.col[2] * 0.012, b, segs=24, bevel=0.003)
        i = cells[label]
        u0, v1 = (i % 4) / 4, 1 - (i // 4) / 4
        lw = 0.06 if radius > 0.02 else 0.034
        plane(f"Label_{label}", lw, lw * 0.5, M["labels"], p - b.col[1] * (radius + 0.026) + b.col[2] * 0.003, b,
              (u0 + 0.02, v1 - 0.25 + 0.06, u0 + 0.23, v1 - 0.06))
    # hazard stripe round the abort button
    p, b = face_point(math.radians(-34), 0.18)
    torus("AbortHazardRing", 0.05, 0.006, M["yellow"], p + b.col[2] * 0.006, b, seg=32, mseg=6)
    # name plate on the console top
    p, b = face_point(0.0, 0.97, lift=0.004)
    plane("NamePlate", 0.28, 0.07, M["plate"], p, b)


# ------------------------------------------------------------------ couches
# Side profile of the couch cushion in the couch's local (y, z): legs at the front (-y), head at the back.
COUCH_PROFILE = [(-0.58, -0.16), (-0.42, -0.06), (-0.22, 0.02), (0.00, 0.03), (0.14, 0.05),
                 (0.24, 0.16), (0.34, 0.40), (0.42, 0.62), (0.46, 0.78)]
COUCH_THICK = 0.09
COUCH_TAPER = [0.95, 1.0, 1.0, 1.0, 1.0, 0.96, 0.86, 0.74, 0.68]   # backrest narrows towards the head
COUCH_W = 0.46
COUCH_PIVOT_Y = -0.50          # couches fan out round this point (towards the console)


def sweep_profile(name, profile, thick, width, mat, xform, bevel=0.03, bolster=0.0, taper=None):
    """Extrudes a side profile (list of (y, z)) across x, as a cushion of the given thickness.
    With bolster > 0 the outer edges are raised to make a bucket seat."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    n = len(profile)
    # offset the profile downwards along its normal to give thickness
    top, bot = [], []
    for i, (y, z) in enumerate(profile):
        a = profile[max(i - 1, 0)]
        b = profile[min(i + 1, n - 1)]
        ty, tz = b[0] - a[0], b[1] - a[1]
        l = math.hypot(ty, tz) or 1
        ny, nz = tz / l, -ty / l          # normal pointing "down/back" from the sitting surface
        top.append((y, z))
        bot.append((y + ny * thick, z + nz * thick))
    lift = [bolster, 0.0, 0.0, bolster]
    tp = taper or [1.0] * n

    def xs_at(i):
        hw = width * tp[i] / 2
        return [-hw, -hw + 0.06, hw - 0.06, hw]
    grid_top = [[bm.verts.new((x, y, z + lf)) for x, lf in zip(xs_at(i), lift)] for i, (y, z) in enumerate(top)]
    grid_bot = [[bm.verts.new((x, y, z)) for x in (xs_at(i)[0], xs_at(i)[3])] for i, (y, z) in enumerate(bot)]
    for i in range(n - 1):
        for k in range(3):
            f = bm.faces.new((grid_top[i][k], grid_top[i][k + 1], grid_top[i + 1][k + 1], grid_top[i + 1][k]))
        f = bm.faces.new((grid_bot[i][1], grid_bot[i][0], grid_bot[i + 1][0], grid_bot[i + 1][1]))
        bm.faces.new((grid_top[i][0], grid_top[i + 1][0], grid_bot[i + 1][0], grid_bot[i][0]))
        bm.faces.new((grid_top[i + 1][3], grid_top[i][3], grid_bot[i][1], grid_bot[i + 1][1]))
    for i in (0, n - 1):
        bm.faces.new((grid_top[i][0], grid_top[i][1], grid_top[i][2], grid_top[i][3], grid_bot[i][1], grid_bot[i][0]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        for l in f.loops:
            l[uv].uv = (l.vert.co.x + 0.5, l.vert.co.y + l.vert.co.z)
    # subdivide for smoother bevels
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges], cuts=1, use_grid_fill=True)
    obj = mesh_obj(name, bm, [mat])
    obj.matrix_world = xform
    if bevel:
        add_bevel(obj, bevel, 3)
    return smooth(obj, 60)


def couch_xform(pivot, yaw):
    """Couch local -> world. The couch's local origin is the seat; it pivots about COUCH_PIVOT_Y."""
    rot = Matrix.Rotation(yaw, 4, "Z")
    return Matrix.Translation(Vector(pivot)) @ rot @ Matrix.Translation((0, -COUCH_PIVOT_Y, 0))


def couch(name, pivot, yaw, scale=1.0):
    xf = couch_xform(pivot, yaw) @ Matrix.Scale(scale, 4)
    w = 0.46
    sweep_profile(name + "_Cushion", COUCH_PROFILE, COUCH_THICK, w, M["cushion"], xf, bevel=0.025, bolster=0.06, taper=COUCH_TAPER)
    # headrest pad
    hp = [(0.40, 0.66), (0.47, 0.86)]
    sweep_profile(name + "_Headrest", hp, 0.07, 0.26, M["cushion"], xf @ Matrix.Translation((0, -0.05, 0.02)), bevel=0.02)
    # metal side frames following the profile, under the cushion
    for side in (-1, 1):
        pts = [xf @ Vector((side * (w * t / 2 - 0.02), y + 0.03, z - COUCH_THICK - 0.02)) for (y, z), t in zip(COUCH_PROFILE, COUCH_TAPER)]
        x = side * (w / 2 - 0.02)
        tube(name + f"_Frame{side}", pts, 0.02 * scale, M["couchframe"])
        # struts down to the floor
        for (y0, z0) in ((-0.30, -0.08), (0.20, 0.0)):
            top_p = xf @ Vector((x, y0, z0 - COUCH_THICK - 0.02))
            foot = Vector((top_p.x, top_p.y, Z_FLOOR + 0.01))
            tube(name + f"_Strut{side}_{y0}", [top_p, foot], 0.022 * scale, M["couchframe"])
            cylinder(name + f"_Foot{side}_{y0}", 0.04 * scale, 0.02, M["couchframe"], foot + Vector((0, 0, 0.01)))
        # armrest
        box(name + f"_Arm{side}", (0.05, 0.30, 0.045), M["couchframe"],
            xf @ Vector((side * (w / 2 + 0.035), 0.0, 0.20)), (xf.to_3x3().normalized()), bevel=0.012)
        tube(name + f"_ArmPost{side}", [xf @ Vector((side * (w / 2 + 0.035), 0.08, 0.18)), xf @ Vector((side * (w / 2 + 0.02), 0.12, 0.02))], 0.012, M["couchframe"])
    # harness: two shoulder straps down the backrest, a lap belt and a central buckle
    for side in (-1, 1):
        pts = [xf @ Vector((side * 0.09, y - 0.012, z + 0.012)) for (y, z) in COUCH_PROFILE[4:]]
        tube(name + f"_Shoulder{side}", pts, 0.012 * scale, M["strap"], bevel_res=1)
    lap = [xf @ Vector((x, 0.02, 0.07)) for x in (-w / 2, -0.12, 0.0, 0.12, w / 2)]
    tube(name + "_Lap", lap, 0.013 * scale, M["strap"], bevel_res=1)
    box(name + "_Buckle", (0.07, 0.04, 0.02), M["buckle"], xf @ Vector((0, 0.01, 0.085)), xf.to_3x3().normalized(), bevel=0.006)


def seat_eye(pivot, yaw, scale=1.0):
    """Where a seated kerbal's eyes are."""
    return couch_xform(pivot, yaw) @ Matrix.Scale(scale, 4) @ Vector((0.0, 0.26, 0.70))


def couch_points(pivot, yaw, scale):
    """Sample points over the whole couch (cushion top and bottom, both edges, frame)."""
    xf = couch_xform(pivot, yaw) @ Matrix.Scale(scale, 4)
    pts = []
    for (y, z), t in zip(COUCH_PROFILE, COUCH_TAPER):
        hw = COUCH_W * t / 2 + 0.04    # include frame and armrests
        for x in (-hw, 0.0, hw):
            pts.append(xf @ Vector((x, y, z + 0.06)))
            pts.append(xf @ Vector((x, y, z - COUCH_THICK - 0.04)))
    return pts


def inside_couch(p, pivot, yaw, scale, margin=0.02):
    """Is world point p inside the couch's volume (approximately)?"""
    inv = (couch_xform(pivot, yaw) @ Matrix.Scale(scale, 4)).inverted()
    q = inv @ p
    ys = [y for y, _ in COUCH_PROFILE]
    if not (ys[0] - margin <= q.y <= ys[-1] + margin):
        return False
    # interpolate the profile height and width at q.y
    for i in range(len(COUCH_PROFILE) - 1):
        (y0, z0), (y1, z1) = COUCH_PROFILE[i], COUCH_PROFILE[i + 1]
        if y0 <= q.y <= y1:
            t = (q.y - y0) / max(1e-6, y1 - y0)
            zc = z0 + (z1 - z0) * t
            hw = COUCH_W * (COUCH_TAPER[i] + (COUCH_TAPER[i + 1] - COUCH_TAPER[i]) * t) / 2 + 0.04
            return abs(q.x) < hw + margin / scale and zc - COUCH_THICK - 0.06 < q.z < zc + 0.10
    return False


def layout_fits(layout, scale):
    for pivot, yaw in layout:
        for p in couch_points(pivot, yaw, scale):
            if math.hypot(p.x, p.y) > r_in(p.z) - 0.03 or p.z > Z_CEIL - 0.06 or p.z < Z_FLOOR + 0.02:
                return False
            # keep clear of the console in front
            phi = math.atan2(p.x, -p.y)
            if abs(phi) < CONSOLE_PHI + 0.05 and p.z < 1.16 and math.hypot(p.x, p.y) > r_in(p.z) - 0.43:
                return False
    for i in range(len(layout)):
        for j in range(len(layout)):
            if i != j and any(inside_couch(p, *layout[j], scale) for p in couch_points(*layout[i], scale)):
                return False
    return True


def couch_layout():
    """Searches for the largest couches, fanned round a pivot towards the console, that fit the cone."""
    seat_z = Z_FLOOR + 0.40
    for scale in (1.0, 0.95, 0.9, 0.85, 0.8, 0.75):
        for py in (-0.20, -0.26, -0.32, -0.38, -0.44):
            for fan in (-12, -6, 0, 6, 12, 18):
                for spread in (0.62, 0.56, 0.50, 0.46):
                    layout = [((0.0, py, seat_z), 0.0)]
                    for side in (-1, 1):
                        layout.append(((side * spread * scale, py, seat_z), side * math.radians(fan)))
                    if layout_fits(layout, scale):
                        return layout, scale
    print("WARNING: no couch layout fits; using the smallest")
    return layout, scale


def build_couches():
    layout, scale = couch_layout()
    eyes = []
    for i, (pivot, yaw) in enumerate(layout):
        couch(f"Couch{i}", pivot, yaw, scale)
        eyes.append((seat_eye(pivot, yaw, scale), yaw))
    print("couch scale", scale, "layout", [(tuple(round(v, 2) for v in c), round(math.degrees(y))) for c, y in layout])
    return eyes


# ------------------------------------------------------------------ lockers, rails, lights, details
def build_lockers():
    # curved locker bank along the back wall, under the couches' backs
    phi0, phi1 = math.radians(120), math.radians(240)
    profile = [(0.0, Z_FLOOR + 0.02), (0.18, Z_FLOOR + 0.02), (0.18, 0.42), (0.0, 0.44)]
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    ns = 48
    rows = [[bm.verts.new(polar(phi0 + (phi1 - phi0) * j / ns, r_in(z) - d, z)) for d, z in profile] for j in range(ns + 1)]
    for j in range(ns):
        for k in range(len(profile) - 1):
            f = bm.faces.new((rows[j][k], rows[j][k + 1], rows[j + 1][k + 1], rows[j + 1][k]))
            for l in f.loops:
                l[uv].uv = (j / ns, k / 4)
    for row in (rows[0], rows[-1]):
        bm.faces.new(row)
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = mesh_obj("Lockers", bm, [M["locker"]])
    add_bevel(obj, 0.008, 2)
    smooth(obj, 30)
    # door seams and handles
    for k in range(7):
        phi = phi0 + (phi1 - phi0) * (k + 0.5) / 7
        z = 0.30
        t, u, n = wall_frame(phi, z)
        p = polar(phi, r_in(z) - 0.185, z)
        box(f"LockerHandle_{k}", (0.07, 0.015, 0.02), M["handle"], p, basis(t, u, n), bevel=0.005)
        if k:
            phs = phi0 + (phi1 - phi0) * k / 7
            tube(f"LockerSeam_{k}", [polar(phs, r_in(Z_FLOOR + 0.03) - 0.182, Z_FLOOR + 0.03), polar(phs, r_in(0.41) - 0.182, 0.41)], 0.004, M["handle"])


def build_rails_and_lights():
    # yellow grab rails above the side windows
    for phi_deg, z in ((60, 1.38), (-60, 1.38), (130, 1.2), (-130, 1.2)):
        phi = math.radians(phi_deg)
        pts = []
        for k in range(9):
            ph = phi + math.radians(-14 + 28 * k / 8)
            off = 0.06 if 0 < k < 8 else 0.0
            pts.append(polar(ph, r_in(z) - off - 0.01, z))
        tube(f"Rail_{phi_deg}", pts, 0.014, M["yellow"])
    # light strips round the ceiling
    for k in range(6):
        phi = math.radians(k * 60 + 30)
        z = Z_CEIL - 0.08
        t, u, n = wall_frame(phi, z)
        p = polar(phi, r_in(z) - 0.02, z)
        box(f"LightHousing_{k}", (0.32, 0.05, 0.035), M["ring"], p, basis(t, u, n), bevel=0.008)
        box(f"LightStrip_{k}", (0.28, 0.025, 0.01), M["light"], p + n * 0.018, basis(t, u, n))
    # fire extinguisher on the right wall, behind the side window
    phi, z = math.radians(118), 0.8
    t, u, n = wall_frame(phi, z)
    p = polar(phi, r_in(z) - 0.08, z)
    cylinder("Extinguisher", 0.045, 0.32, M["extinguisher"], p, basis(t, u.cross(t).normalized(), u), segs=24, bevel=0.01)
    cylinder("ExtinguisherTop", 0.02, 0.05, M["handle"], p + u * 0.18, basis(t, u.cross(t).normalized(), u), segs=16)
    box("ExtinguisherClamp", (0.11, 0.02, 0.03), M["rib"], p - n * 0.02, basis(t, u, n))
    # checklist panel on the left wall, in front of the hatch
    phi, z = math.radians(-55), 0.95
    t, u, n = wall_frame(phi, z)
    plane("PlateLeft", 0.22, 0.055, M["plate"], polar(phi, r_in(z) - 0.012, z), basis(t, u, n))


# ------------------------------------------------------------------ build
build_shell()
build_ribs()
build_window_frames()
build_floor_ceiling()
build_hatch()
build_console()
console_end_panels()
instrument_panel()
eyes = build_couches()
build_lockers()
build_rails_and_lights()

# seat eye markers (empties) for the game: IVA_Seat0..2
for i, (p, yaw) in enumerate(eyes):
    e = bpy.data.objects.new(f"IVA_Seat{i}", None)
    e.empty_display_type = "ARROWS"
    e.empty_display_size = 0.1
    e.matrix_world = Matrix.Translation(p) @ Matrix.Rotation(yaw, 4, "Z")
    link(e)

bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("objects", len(COLL.objects), "saved", OUT)
