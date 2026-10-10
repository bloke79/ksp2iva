"""Measures a pod's window glass from the extracted hull OBJ and prints spec "windows" entries (generator space).

Usage: python -I window_extract.py <hull.obj> <hull_base_y>
The OBJ is extract_pods.py output (Unity part space with x negated). Each connected glass piece becomes one window:
centre angle (spec convention: angle = -phi, phi 0 = cabin front -Y, +phi = +X), centre height, half width (arc at the
glass), half height (vertical), and the glass radius so window sleeves can run out to it.
"""
import math
import sys
from collections import defaultdict

path, base = sys.argv[1], float(sys.argv[2])
verts, faces, group = [], [], None
for line in open(path):
    if line.startswith("v "):
        x, y, z = map(float, line.split()[1:4])
        verts.append((-x, z, y - base))            # OBJ (-ux, uy, uz) -> Blender (ux, uz, uy - base)
    elif line.startswith("g "):
        group = line[2:].strip()
    elif line.startswith("f ") and "glass" in group:
        faces.append([int(t.split("/")[0]) - 1 for t in line.split()[1:]])

parent = {}


def find(a):
    while parent.setdefault(a, a) != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


for f in faces:
    for v in f[1:]:
        parent[find(v)] = find(f[0])
pieces = defaultdict(set)
for f in faces:
    for v in f:
        pieces[find(f[0])].add(v)

for vs in sorted(pieces.values(), key=lambda s: -len(s)):
    pts = [verts[i] for i in vs]
    phis = [math.atan2(x, -y) for x, y, z in pts]
    c = math.atan2(sum(math.sin(p) for p in phis), sum(math.cos(p) for p in phis))
    d = [((p - c + math.pi) % (2 * math.pi)) - math.pi for p in phis]
    rs = [math.hypot(x, y) for x, y, z in pts]
    zs = [z for x, y, z in pts]
    r = sum(rs) / len(rs)
    zc = (min(zs) + max(zs)) / 2
    zm = sum(zs) / len(zs)
    var = sum((z - zm) ** 2 for z in zs) or 1e-9
    dr = sum((z - zm) * (q - r) for z, q in zip(zs, rs)) / var       # glass radius change per metre of height (tilt)
    r = r + dr * (zc - zm)
    print(f'{{"angle": {-math.degrees(c):.1f}, "z": {zc:.3f}, "half_w": {(max(d) - min(d)) / 2 * r:.3f}, "half_h": {(max(zs) - min(zs)) / 2:.3f}, '
          f'"glass_r": {r:.3f}, "glass_dr": {dr:.3f}, "verts": {len(pts)}}}')
