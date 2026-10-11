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


_LAST = {}


def inner(p, d, gap=0.0):
    """The shell's inner face seen from p along d (after build), stood off by gap: for fittings mounted on the wall."""
    d = Vector(d).normalized()
    h = _LAST["bvh"].ray_cast(Vector(p), d, 5.0)
    if h[0] is None:
        return None
    return h[0] - d * (_LAST["wall"] + gap)


def wall_frame(p, d, gap=0.0, up=(0.0, 0.0, 1.0)):
    """Point and basis on the shell's inner face seen from p along d (after build): right, up (as near `up` as the wall
    allows) and the normal out of the wall. For flat fittings (labels, velcro, plates) laid on the hull."""
    d = Vector(d).normalized()
    h = _LAST["bvh"].ray_cast(Vector(p), d, 5.0)
    if h[0] is None:
        return None
    n = -h[1] if h[1].dot(d) > 0 else h[1]          # out of the wall, towards p
    u = Vector(up) - Vector(up).project(n)
    if u.length < 1e-4:
        u = Vector((1, 0, 0)) - Vector((1, 0, 0)).project(n)
    u = u.normalized()
    return h[0] - d * (_LAST["wall"] + gap), L.basis(u.cross(n).normalized(), u, n)


def build(name, ext_path, base, z0, z1, wall=0.04, dz=0.02, seg=120, mat=None, centre=(0.0, 0.0), frame_mat=None,
          margin=0.01, keep=None, frame_w=0.07, wells=False, well_cut=0.05, bezel=0.09):
    """Shell from z0 to z1 (generator space). Returns (shell object, list of window dicts with centre, normal, outline).
    keep(p) -> False drops a shell vertex region (for openings you build yourself).
    wells=True: for tightly curved panes, each window gets a flat dark bezel and a short tunnel out to the glass, and
    the shell is cut back behind the bezel (no stepped edge can show); otherwise frames follow the opening edges."""
    verts, faces, glass = load_exterior(ext_path, base)
    tris, tri_glass = [], []
    for f, g in zip(faces, glass):
        for k in range(1, len(f) - 1):
            tris.append((f[0], f[k], f[k + 1]))
            tri_glass.append(g)
    bvh = BVHTree.FromPolygons(verts, tris)
    _LAST.update(bvh=bvh, wall=wall + 0.015)
    cx, cy = centre
    panes = []
    if wells:
        for piece in glass_pieces(verts, faces, glass):
            pn = _pane(verts, faces, piece, cx, cy)
            if pn and z0 - 0.05 < pn["c"].z < z1 + 0.05:
                panes.append(pn)

    def in_well(p):
        for pn in panes:
            r = p - pn["c"]
            if abs(r.dot(pn["n"])) < 0.35 and _inside(pn["poly"], r.dot(pn["u"]), r.dot(pn["v"]), well_cut):
                return True
        return False
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
            if panes and in_well(mid):
                continue   # behind a window well's bezel
            if not panes and (hits_glass(mid) or any(hits_glass(v.co) for v in q)):
                continue   # a window (or its edge): left open, the frame covers the stepped edge
            if keep is not None and not keep(mid):
                continue
            f = bm.faces.new(q)
            for l, (uu, vv) in zip(f.loops, ((j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1))):
                l[uv].uv = (uu * 2 * math.pi * 0.6 / seg, zs[0] + (zs[-1] - zs[0]) * vv / nz)
    # the window openings' own edges (before the caps), for the frames: chained into loops
    ends = set(v for i in (0, nz) for v in bv[i] if v is not None)
    nxt = {}
    for e in bm.edges:
        if e.is_boundary and not (e.verts[0] in ends and e.verts[1] in ends):
            a_, b_ = e.verts
            nxt.setdefault(a_, []).append(b_)
            nxt.setdefault(b_, []).append(a_)
    loops, seen = [], set()
    for start in list(nxt):
        if start in seen or start in ends:
            continue
        loop, prev, cur = [start], None, start
        seen.add(start)
        while True:
            cand = [q for q in nxt.get(cur, []) if q is not prev and q not in seen and q not in ends]
            if not cand:
                break
            prev, cur = cur, cand[0]
            seen.add(cur)
            loop.append(cur)
        if len(loop) >= 8:
            loops.append([v.co.copy() for v in loop])
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
    # frames: a chamfered ring along each opening's edge (smoothed), so it covers the shell's stepped edge exactly
    import stock as S
    for k, pn in enumerate(panes):
        _well(f"{name}Well{k}", pn, bvh, wall, bezel, frame_mat or M["frame"])
    for k, loop in enumerate([] if panes else loops):
        pts = loop
        for _ in range(6):   # closed moving average
            m = len(pts)
            pts = [(pts[(i - 2) % m] + pts[(i - 1) % m] + pts[i] + pts[(i + 1) % m] + pts[(i + 2) % m]) / 5 for i in range(m)]
        pts = pts[::2] if len(pts) > 80 else pts
        ring, norms = [], []
        for p in pts:
            nh = bvh.find_nearest(p)
            axis_pt = Vector((cx, cy, p.z))
            n_in = (nh[1] if nh[1].dot(axis_pt - p) > 0 else -nh[1]) if nh[0] is not None else (axis_pt - p).normalized()
            ring.append(p + n_in * 0.012)
            norms.append(n_in)
        if sum(((ring[i] - ring[i - 1]).length for i in range(len(ring))), 0.0) < 0.3:
            continue
        S.sweep(f"{name}Frame{k}", ring, norms, S.chamfer_rect(frame_w, 0.035, 0.01), frame_mat or M["frame"], closed=True)
    return shell, windows


def _outline(verts, faces, piece):
    """Outer boundary of a glass patch, in order: the convex hull of its vertices projected onto the pane's plane.
    (Walking boundary edges zig-zags on panes modelled with two layers or a rim; the panes are convex.)"""
    pts = {}
    for fi in piece:
        for i in faces[fi]:
            pts[tuple(round(c, 4) for c in verts[i])] = verts[i]
    pts = list(pts.values())
    if len(pts) < 3:
        return []
    c = sum(pts, Vector()) / len(pts)
    nsum = Vector()
    for fi in piece:
        f = faces[fi]
        nsum += (verts[f[1]] - verts[f[0]]).cross(verts[f[2]] - verts[f[0]])
    if nsum.length < 1e-9:
        return []
    n = nsum.normalized()
    u = (Vector((0, 0, 1)) - Vector((0, 0, 1)).project(n))
    if u.length < 1e-3:
        u = Vector((1, 0, 0)) - Vector((1, 0, 0)).project(n)
    u = u.normalized()
    v = n.cross(u)
    flat = sorted(((((p - c).dot(u)), ((p - c).dot(v)), p) for p in pts), key=lambda t: (t[0], t[1]))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for q in flat:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0:
            lower.pop()
        lower.append(q)
    for q in reversed(flat):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0:
            upper.pop()
        upper.append(q)
    hull = lower[:-1] + upper[:-1]
    # resample long edges so the frame sweep and the edge snapping have points every few centimetres
    out = []
    for a_, b_ in zip(hull, hull[1:] + hull[:1]):
        pa, pb = a_[2], b_[2]
        k = max(1, int((pb - pa).length / 0.03))
        for t in range(k):
            out.append(pa.lerp(pb, t / k))
    return out


def _pane(verts, faces, piece, cx, cy):
    """A glass pane: centre, outward normal, in-plane axes and its outline as a convex polygon in (u, v)."""
    pts = {}
    for fi in piece:
        for i in faces[fi]:
            pts[tuple(round(c, 4) for c in verts[i])] = verts[i]
    pts = list(pts.values())
    if len(pts) < 3:
        return None
    nsum = Vector()
    for fi in piece:
        f = faces[fi]
        nsum += (verts[f[1]] - verts[f[0]]).cross(verts[f[2]] - verts[f[0]])
    if nsum.length < 1e-9:
        return None
    c = sum(pts, Vector()) / len(pts)
    n = nsum.normalized()
    if n.dot(Vector((c.x - cx, c.y - cy, 0))) < 0:
        n = -n
    c = c + n * max((p - c).dot(n) for p in pts)         # on the outer face of the glass
    u = Vector((0, 0, 1)) - Vector((0, 0, 1)).project(n)
    if u.length < 1e-3:
        u = Vector((1, 0, 0)) - Vector((1, 0, 0)).project(n)
    u = u.normalized()
    v = n.cross(u)
    flat = sorted(((p - c).dot(u), (p - c).dot(v)) for p in pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for q in flat:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0:
            lower.pop()
        lower.append(q)
    for q in reversed(flat):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0:
            upper.pop()
        upper.append(q)
    hull = lower[:-1] + upper[:-1]
    mu = sum(a for a, b in hull) / len(hull)
    mv = sum(b for a, b in hull) / len(hull)
    c = c + u * mu + v * mv
    hull = [(a - mu, b - mv) for a, b in hull]
    poly = []
    for (a1, b1), (a2, b2) in zip(hull, hull[1:] + hull[:1]):
        k = max(1, int(math.hypot(a2 - a1, b2 - b1) / 0.03))
        for t in range(k):
            poly.append((a1 + (a2 - a1) * t / k, b1 + (b2 - b1) * t / k))
    return {"c": c, "n": n, "u": u, "v": v, "poly": poly}


def _grow(poly, e):
    out = []
    for a, b in poly:
        r = math.hypot(a, b)
        f = (r + e) / r if r > 1e-6 else 1.0
        out.append((a * f, b * f))
    return out


def _inside(poly, a, b, e=0.0):
    """Point in a convex polygon centred on the origin, grown by e."""
    pg = _grow(poly, e) if e else poly
    sgn = 0
    for (a1, b1), (a2, b2) in zip(pg, pg[1:] + pg[:1]):
        cr = (a2 - a1) * (b - b1) - (b2 - b1) * (a - a1)
        if abs(cr) < 1e-12:
            continue
        if sgn == 0:
            sgn = 1 if cr > 0 else -1
        elif (cr > 0) != (sgn > 0):
            return False
    return True


def _well(name, pn, bvh, wall, bezel, mat):
    """Window well: a tunnel from the glass in to a flat bezel, the bezel ring, and a skirt from the bezel's outer
    edge back to the shell wherever the hull curves away behind it."""
    c, n, u, v, poly = pn["c"], pn["n"], pn["u"], pn["v"], pn["poly"]
    outer = _grow(poly, bezel)

    def P(a, b, d):
        return c + u * a + v * b + n * d
    shell_d = []
    for a, b in outer:
        h = bvh.ray_cast(P(a, b, 0.6), -n, 2.0)
        shell_d.append(((h[0] - c).dot(n) if h[0] is not None else -wall) - wall - 0.015)
    d1 = min(min(shell_d), -wall - 0.02) - 0.008
    d0 = -wall * 0.4
    bm = bmesh.new()
    r0 = [bm.verts.new(P(a, b, d0)) for a, b in poly]
    r1 = [bm.verts.new(P(a, b, d1)) for a, b in poly]
    r2 = [bm.verts.new(P(a, b, d1)) for a, b in outer]
    r3 = [bm.verts.new(P(a, b, d)) for (a, b), d in zip(outer, shell_d)]
    m = len(poly)
    for ra, rb in ((r0, r1), (r1, r2), (r2, r3)):
        for i in range(m):
            j = (i + 1) % m
            try:
                bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
            except ValueError:
                pass
    bm.normal_update()
    for f in bm.faces:
        cc = f.calc_center_median()
        axis_d = (cc - c) - n * (cc - c).dot(n)
        want = -axis_d if abs(f.normal.dot(n)) < 0.5 else -n
        if f.normal.dot(want) < 0:
            f.normal_flip()
    o = L.mesh_obj(name, bm, [mat])
    L.solidify(o, 0.008, offset=1.0)
    return o
