"""Inner shell for parts that aren't bodies of revolution (cockpits, landers, the rover cab): measured from the part's
real exterior with rays cast out from its axis, pulled in by the wall thickness, and cut wherever the exterior has
glass, with a chamfered frame round each window.

Exterior: extract_pods.py OBJ (Unity part space with x negated), converted to generator space as everywhere else:
Blender (x, y, z) = (ux, uz, uy - base). The part axis is Blender z.
"""
import math
from collections import defaultdict

import ivalib as L  # imports bpy first
import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

M = L.M


def load_exterior(path, base, glass_words=("glass", "window", "seethrough")):
    """Returns (verts, faces, is_glass per face)."""
    verts, faces, glass, group = [], [], [], ""
    for line in open(path):
        if line.startswith("v "):
            x, y, z = map(float, line.split()[1:4])
            verts.append(Vector((-x, z, y - base)))
        elif line.startswith("g ") or line.startswith("usemtl "):
            group = line.split(None, 1)[1].strip().lower()
        elif line.startswith("f "):
            faces.append([int(t.split("/")[0]) - 1 for t in line.split()[1:]])
            glass.append(any(w in group for w in glass_words))
    return verts, faces, glass


def glass_pieces(verts, faces, glass):
    """Connected glass patches: list of (face index list)."""
    parent = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    key = {}
    for f, g in zip(faces, glass):
        if not g:
            continue
        for i in f:
            k = tuple(round(c, 4) for c in verts[i])
            if k in key:
                parent[find(i)] = find(key[k])
            else:
                key[k] = i
        for i in f[1:]:
            parent[find(i)] = find(f[0])
    pieces = defaultdict(list)
    for fi, (f, g) in enumerate(zip(faces, glass)):
        if g:
            pieces[find(f[0])].append(fi)
    return [p for p in pieces.values() if len(p) >= 2]


def build(name, ext_path, base, z0, z1, wall=0.04, dz=0.02, seg=120, mat=None, centre=(0.0, 0.0), frame_mat=None,
          margin=0.01, keep=None):
    """Shell from z0 to z1 (generator space). Returns (shell object, list of window dicts with centre, normal, outline).
    keep(p) -> False drops a shell vertex region (for openings you build yourself)."""
    verts, faces, glass = load_exterior(ext_path, base)
    tris, tri_glass = [], []
    for f, g in zip(faces, glass):
        for k in range(1, len(f) - 1):
            tris.append((f[0], f[k], f[k + 1]))
            tri_glass.append(g)
    bvh = BVHTree.FromPolygons(verts, tris)
    cx, cy = centre
    nz = max(2, int(round((z1 - z0) / dz)))
    zs = [z0 + (z1 - z0) * i / nz for i in range(nz + 1)]
    grid = []
    for z in zs:
        row = []
        o = Vector((cx, cy, z))
        for j in range(seg):
            phi = 2 * math.pi * j / seg
            d = Vector((math.sin(phi), -math.cos(phi), 0.0))
            hit = bvh.ray_cast(o, d, 5.0)
            if hit[0] is None:
                row.append(None)
                continue
            loc, nrm, idx, dist = hit
            n_in = nrm if nrm.dot(d) < 0 else -nrm
            row.append(loc + n_in * wall)
        grid.append(row)
    def hits_glass(p):
        d = Vector((p.x - cx, p.y - cy, 0.0))
        if d.length < 1e-6:
            return False
        h = bvh.ray_cast(Vector((cx, cy, p.z)), d.normalized(), 5.0)
        return h[0] is not None and tri_glass[h[2]]

    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    bv = [[bm.verts.new(p) if p is not None else None for p in row] for row in grid]
    for i in range(nz):
        for j in range(seg):
            jn = (j + 1) % seg
            q = [bv[i][j], bv[i][jn], bv[i + 1][jn], bv[i + 1][j]]
            if any(v is None for v in q):
                continue
            mid = sum((v.co for v in q), Vector()) / 4
            if hits_glass(mid) or any(hits_glass(v.co) for v in q):
                continue   # a window (or its edge): left open, the frame covers the stepped edge
            if keep is not None and not keep(mid):
                continue
            f = bm.faces.new(q)
            for l, (uu, vv) in zip(f.loops, ((j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1))):
                l[uv].uv = (uu * 2 * math.pi * 0.6 / seg, zs[0] + (zs[-1] - zs[0]) * vv / nz)
    # end caps: the first and last rings filled (fan from their centre)
    for i in (0, nz):
        ring = [v for v in bv[i] if v is not None]
        if len(ring) < 3:
            continue
        cv = bm.verts.new(sum((v.co for v in ring), Vector()) / len(ring))
        for j in range(len(ring)):
            try:
                f = bm.faces.new((ring[j], ring[(j + 1) % len(ring)], cv))
                for l in f.loops:
                    l[uv].uv = (l.vert.co.x, l.vert.co.y)
            except ValueError:
                pass
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.normal_update()
    zc = (zs[0] + zs[-1]) / 2
    for f in bm.faces:   # facing in, towards the middle of the axis
        c = f.calc_center_median()
        if f.normal.dot(Vector((cx, cy, zc)) - c) < 0:
            f.normal_flip()
    shell = L.mesh_obj(name, bm, [mat or M["blanket"]])
    L.solidify(shell, 0.015, offset=1.0)

    windows = []
    for k, piece in enumerate(glass_pieces(verts, faces, glass)):
        pts = [verts[i] for fi in piece for i in faces[fi]]
        c = sum(pts, Vector()) / len(pts)
        if not (z0 - 0.05 < c.z < z1 + 0.05):
            continue
        nsum = Vector()
        for fi in piece:
            f = faces[fi]
            nsum += (verts[f[1]] - verts[f[0]]).cross(verts[f[2]] - verts[f[0]])
        n = nsum.normalized()
        if n.dot(Vector((c.x - cx, c.y - cy, 0))) < 0:
            n = -n                                      # outward
        outline = _outline(verts, faces, piece)
        if len(outline) >= 3:
            windows.append({"centre": c, "normal": n, "outline": outline})
    # frames: a chamfered ring on the inner face round each opening
    import stock as S
    for k, w in enumerate(windows):
        n, c = w["normal"], w["centre"]
        ring = []
        for p in w["outline"]:
            q = p + (p - c).normalized() * (margin + 0.012)
            hit = bvh.ray_cast(q - n * 0.4, n, 0.6)   # back onto the hull, then in by the wall
            base_p = (hit[0] if hit[0] is not None else q) - n * (wall + 0.012)
            ring.append(base_p)
        S.sweep(f"{name}Frame{k}", ring, [-n] * len(ring), S.chamfer_rect(0.07, 0.035, 0.01), frame_mat or M["frame"], closed=True)
    return shell, windows


def _outline(verts, faces, piece):
    """Boundary loop of a glass patch (positions, in order)."""
    edges = defaultdict(int)
    key = {}

    def k(i):
        p = tuple(round(c, 4) for c in verts[i])
        key.setdefault(p, verts[i])
        return p
    for fi in piece:
        f = faces[fi]
        for a in range(len(f)):
            e = tuple(sorted((k(f[a]), k(f[(a + 1) % len(f)]))))
            edges[e] += 1
    bound = [e for e, c in edges.items() if c == 1]
    if not bound:
        return []
    nxt = defaultdict(list)
    for a, b in bound:
        nxt[a].append(b)
        nxt[b].append(a)
    # the longest loop
    best = []
    seen = set()
    for start in list(nxt):
        if start in seen:
            continue
        loop, prev, cur = [start], None, start
        seen.add(start)
        while True:
            cand = [q for q in nxt[cur] if q != prev and q not in seen]
            if not cand:
                break
            prev, cur = cur, cand[0]
            seen.add(cur)
            loop.append(cur)
        if len(loop) > len(best):
            best = loop
    return [key[p] for p in best]
