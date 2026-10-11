"""Automatic review of a built interior, run by build_interior.ps1 after every model build. It checks for:

  clip      parts passing through each other (vertices more than DEPTH inside another closed part)
  buried    parts almost wholly inside another (wasted, or a placement bug)
  wall      parts poking out through the hull shell (seen from the part axis)
  occluded  instruments and controls facing the crew eye but mostly hidden behind something else
  views     window views (IVA_View -> IVA_ViewAt) blocked by something opaque
  floating  parts touching nothing at all
  zfight    faces of different parts in the same plane (they flicker)
  reach     controls further from the seated eye than an arm can reach (information)

It can't judge looks: the previews still need reviewing by eye, zoomed in, from every camera.

Usage: blender -b <file.blend> --python review.py -- <spec.json> <out.txt>
"""
import json
import math
import re
import sys
from collections import defaultdict

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

A = sys.argv[sys.argv.index("--") + 1:]
SPEC = json.load(open(A[0]))
OUT = A[1]
DEPTH = 0.015
REACH = 0.95
MARKER = re.compile(r"^(REF_|IVA_Col|IVA_Seat|IVA_View|IVA_Hatch|IVA_Act|IVA_Live(Axis|Mid|Zero|North|Zenith|Up|Edge|Out|To|Open)_)")
# structure that things are meant to be mounted into or against (window frames are checked like any other part)
STRUCT = re.compile(r"Shell|Floor|Wall_|Ceiling|GroundPlates|HullShell|Dome|Deck|Plate_|Rib_|RingFrame|Corner|Bulkhead|"
                    r"Panel$|Backdrop|Stringer|Rivet|Window|Glass|Sky")
GLASS = re.compile(r"glass|window|hud", re.I)
CONTROL = re.compile(r"(Plate|^MasterAlarm.*|^ThrottleHandle.*|^Rhc(Grip|Button)|^IVA_Live_Screen.*|^IVA_Live_.*navball.*|Handle.*)$")


MOUNT = re.compile(r"_(Flange|Socket|Tie)\d*$")   # fittings that seat into whatever they're fixed to


def is_struct(n):
    return bool(STRUCT.search(n)) and "Frame" not in n


def root(n):
    n = re.sub(r"^IVA_Live_(Door|Slide|Curtain|Glow|Screen|Wheel)?", "", n)
    n = re.sub(r"^Bundle_", "", n)   # a cable bundle belongs with its clamp boxes (RunLow0 / RunLow0Box1)
    return re.sub(r"__p\d+$", "", n)


def key(n):
    m = re.match(r"^(.*?\d+)", root(n))
    return m.group(1) if m else root(n)


def word_prefix(a, b):
    """Shared leading words (CamelCase or _ separated): DockWheelSpoke_3 / DockWheelHub -> DockWheel."""
    n = 0
    while n < min(len(a), len(b)) and a[n] == b[n]:
        n += 1
    if n == min(len(a), len(b)):
        return a[:n]
    while n > 0 and not (a[n].isupper() or a[n] in "_-") and not (b[n].isupper() or b[n] in "_-"):
        n -= 1
    while n > 0 and not ((a[n].isupper() or a[n] in "_-") and (b[n].isupper() or b[n] in "_-")):
        n -= 1
    return a[:n]


def related(a, b):
    ra, rb = root(a), root(b)
    return (ra.startswith(rb) or rb.startswith(ra) or key(a) == key(b)
            or len(word_prefix(ra, rb).rstrip("_-")) >= 5)   # one assembly: DockWheelSpoke / DockWheelHub


# ------------------------------------------------------------------ gather evaluated meshes
dg = bpy.context.evaluated_depsgraph_get()
objs = []
for o in bpy.data.objects:
    if o.type not in ("MESH", "CURVE") or MARKER.search(o.name) or o.hide_render:
        continue
    ev = o.evaluated_get(dg)
    try:
        me = ev.to_mesh()
    except Exception:
        continue
    if me is None or len(me.polygons) == 0:
        ev.to_mesh_clear()
        continue
    mw = o.matrix_world
    n3 = mw.to_3x3().inverted_safe().transposed()
    verts = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    pnorm = [(n3 @ p.normal).normalized() for p in me.polygons]
    pcent = [mw @ p.center for p in me.polygons]
    parea = [p.area for p in me.polygons]
    mats = " ".join(m.name for m in o.data.materials if m) if hasattr(o.data, "materials") else ""
    ev.to_mesh_clear()
    lo = Vector((min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts)))
    hi = Vector((max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts)))
    size = hi - lo
    objs.append({"name": o.name, "verts": verts, "polys": polys, "pnorm": pnorm, "pcent": pcent, "parea": parea,
                 "lo": lo, "hi": hi, "size": size, "bvh": None, "thin": min(size) < 2 * DEPTH,
                 "struct": is_struct(o.name), "glass": bool(GLASS.search(o.name) or GLASS.search(mats)),
                 "big": sorted(size)[1] > 1.0})


def bvh(o):
    if o["bvh"] is None:
        o["bvh"] = BVHTree.FromPolygons(o["verts"], o["polys"])
    return o["bvh"]


def inside_depth(p, o):
    hit = bvh(o).find_nearest(p)
    if hit[0] is None:
        return 0.0
    loc, nrm, _, dist = hit
    return dist if (p - loc).dot(nrm) < 0 else -dist


def boxes_touch(a, b, pad=0.0):
    return all(a["lo"][k] - pad <= b["hi"][k] and b["lo"][k] - pad <= a["hi"][k] for k in range(3))


report = defaultdict(list)

# ------------------------------------------------------------------ clip and buried (non-structural parts)
parts = [o for o in objs if not o["struct"] and max(o["size"]) >= 0.02 and not MOUNT.search(o["name"])]
parts.sort(key=lambda o: o["lo"].x)
for i, a in enumerate(parts):
    for b in parts[i + 1:]:
        if b["lo"].x > a["hi"].x:
            break
        if not boxes_touch(a, b) or related(a["name"], b["name"]):
            continue
        for x, y in ((a, b), (b, a)):
            if y["thin"]:
                continue
            lo, hi = y["lo"], y["hi"]
            cands = [v for v in x["verts"] if all(lo[k] + DEPTH < v[k] < hi[k] - DEPTH for k in range(3))]
            if not cands:
                continue
            step = max(1, len(cands) // 300)
            depths = [inside_depth(v, y) for v in cands[::step]]
            deep = [d for d in depths if d > DEPTH]
            if len(deep) >= 3:
                frac = len(deep) * step / len(x["verts"])
                c = sum(cands, Vector()) / len(cands)
                cat = "buried" if frac > 0.9 else "clip"
                report[cat].append((max(deep), f"{x['name']} {'inside' if cat == 'buried' else 'through'} {y['name']}: "
                                               f"{max(deep) * 100:.1f} cm deep, {frac:.0%} of it, at ({c.x:.2f}, {c.y:.2f}, {c.z:.2f})"))
                break

# ------------------------------------------------------------------ through the hull wall (rays out from the part axis)
walls = [o for o in objs if o["struct"] and o["big"] and not re.search(r"Floor|Deck|Ceiling|Bulkhead|Plate_|Backdrop|Sky", o["name"])]
if walls:
    wv, wt = [], []
    for o in walls:
        base = len(wv)
        wv += o["verts"]
        wt += [tuple(base + i for i in p) for p in o["polys"]]
    wall_bvh = BVHTree.FromPolygons(wv, wt)
    cx, cy = SPEC.get("shell_centre", (0.0, 0.0))
    for o in parts:
        step = max(1, len(o["verts"]) // 150)
        worst, at = 0.0, None
        for p in o["verts"][::step]:
            org = Vector((cx, cy, p.z))
            d = p - org
            if d.length < 0.05:
                continue
            h = wall_bvh.ray_cast(org, d.normalized(), d.length)
            if h[0] is not None and abs(h[1].z) < 0.7:   # end caps don't count: the ray runs along them
                past = d.length - h[3]
                if past > worst:
                    worst, at = past, p
        if worst > (0.05 if "Frame" in o["name"] else 0.012):   # window frames overlap the wall by design
            report["wall"].append((worst, f"{o['name']} pokes {worst * 100:.1f} cm through the hull at ({at.x:.2f}, {at.y:.2f}, {at.z:.2f})"))

# ------------------------------------------------------------------ one BVH of everything opaque, for sight lines
sv, st, sowner = [], [], []
for idx, o in enumerate(objs):
    if o["glass"]:
        continue
    base = len(sv)
    sv += o["verts"]
    for p in o["polys"]:
        for k in range(1, len(p) - 1):
            st.append((base + p[0], base + p[k], base + p[k + 1]))
            sowner.append(idx)
scene_bvh = BVHTree.FromPolygons(sv, st)


def blocker(eye, p, me_name):
    """First opaque part between eye and p that isn't p's own assembly (None if the line is clear)."""
    d = p - eye
    h = scene_bvh.ray_cast(eye, d.normalized(), d.length - 0.004)
    if h[0] is None:
        return None
    n = objs[sowner[h[2]]]["name"]
    if related(n, me_name):
        return None
    return n


# seated crew eyes from the spec pose (the cameras named eye* sit at the same points)
seats = [st for st in SPEC.get("pose", {}).get("seats", []) if "eye" in st]
eyes = [Vector(st["eye"]) for st in seats]
fwds = [Vector(st.get("fwd", (0, 0, 1))).normalized() for st in seats]
LOOK = math.cos(math.radians(110))   # how far round a seated kerbal can look
seated = bool(eyes)

# ------------------------------------------------------------------ occluded controls, and reach
if seated:
    for o in objs:
        if o["struct"] or not CONTROL.search(o["name"]):
            continue
        best, best_eye, blockers = -1.0, None, defaultdict(int)
        for eye, fwd in zip(eyes, fwds):
            mid = (o["lo"] + o["hi"]) / 2
            if fwd.dot((mid - eye).normalized()) < LOOK:
                continue   # behind the seat: seen only when floating about
            faces = [(c, n, a) for c, n, a in zip(o["pcent"], o["pnorm"], o["parea"]) if n.dot(eye - c) > 0.15 * (eye - c).length]
            if not faces or min((c - eye).length for c, _, _ in faces) > 2.0:
                continue
            faces.sort(key=lambda f: -f[2])
            samples = faces[:24]
            vis = 0.0
            for c, n, a in samples:
                b = blocker(eye, c + n * 0.003, o["name"])
                if b is None:
                    vis += 1
                else:
                    blockers[b] += 1
            frac = vis / len(samples)
            if frac > best:
                best, best_eye = frac, eye
        if best_eye is None:
            continue
        if best < 0.5:
            top = ", ".join(n for n, _ in sorted(blockers.items(), key=lambda kv: -kv[1])[:3])
            report["occluded"].append((1 - best, f"{o['name']} only {best:.0%} visible from the eye; hidden by {top}"))
        c = (o["lo"] + o["hi"]) / 2
        dist = min((c - e).length for e in eyes)
        if dist > REACH and not o["name"].startswith("IVA_Live"):
            report["reach"].append((dist, f"{o['name']} is {dist:.2f} m from the eye"))

# ------------------------------------------------------------------ window views
for e in bpy.data.objects:
    if e.name.startswith("IVA_View_"):
        at = bpy.data.objects.get("IVA_ViewAt_" + e.name[len("IVA_View_"):])
        if at:
            b = blocker(e.matrix_world.translation, at.matrix_world.translation, "")
            if b:
                report["views"].append((1, f"{e.name} looks straight into {b}"))

# ------------------------------------------------------------------ floating parts
for o in parts:
    if not any(q is not o and boxes_touch(o, q, 0.006) for q in objs):
        report["floating"].append((max(o["size"]), f"{o['name']} touches nothing (centre {((o['lo'] + o['hi']) / 2).to_tuple(2)})"))

# ------------------------------------------------------------------ z-fighting (coplanar overlapping faces of different parts)
buckets = defaultdict(list)
for o in objs:
    for c, n, a, poly in zip(o["pcent"], o["pnorm"], o["parea"], o["polys"]):
        if a < 2e-4:
            continue
        d = n.dot(c)
        buckets[(round(n.x, 2), round(n.y, 2), round(n.z, 2), round(d / 0.003))].append((o, n, d, poly, c))


def overlap(f, g):
    fv = [f[0]["verts"][i] for i in f[3]]
    gv = [g[0]["verts"][i] for i in g[3]]
    u = (fv[1] - fv[0]).normalized()
    v = f[1].cross(u)

    def box(vs):
        us, ws = [x.dot(u) for x in vs], [x.dot(v) for x in vs]
        return min(us), max(us), min(ws), max(ws)
    a, b = box(fv), box(gv)
    ou, ov = min(a[1], b[1]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[2], b[2])
    return ou * ov if ou > 0.004 and ov > 0.004 else 0.0


zf = {}
for k, fl in buckets.items():
    cands = fl + buckets.get((k[0], k[1], k[2], k[3] + 1), [])
    for f in fl:
        for g in cands:
            if g[0] is f[0] or related(f[0]["name"], g[0]["name"]):
                continue
            if f[1].dot(g[1]) < 0.999 or abs(f[2] - g[2]) > 0.0003:
                continue
            a = overlap(f, g)
            pk = tuple(sorted((f[0]["name"], g[0]["name"])))
            if a > 1e-4 and a > zf.get(pk, (0,))[0]:
                zf[pk] = (a, f[4])
for (a, b), (area, c) in zf.items():
    report["zfight"].append((area, f"{a} / {b}: {area * 1e4:.0f} cm2 coplanar at ({c.x:.2f}, {c.y:.2f}, {c.z:.2f})"))

# ------------------------------------------------------------------ write
ORDER = ["clip", "wall", "buried", "occluded", "views", "floating", "zfight", "reach"]
with open(OUT, "w") as f:
    for cat in ORDER:
        items = sorted(report[cat], reverse=True)
        f.write(f"== {cat} ({len(items)})\n")
        for _, line in items:
            f.write(f"  {line}\n")
print("REVIEW " + "  ".join(f"{c} {len(report[c])}" for c in ORDER))
