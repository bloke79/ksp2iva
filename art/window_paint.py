"""Finds painted (opaque) windows on a hull by their texture colour and prints spec "windows" entries.

Usage: python -I window_paint.py <hull.obj> <texture.png> <hull_base_y> [r g b tolerance]
For pods whose windows are part of the hull texture (no separate glass mesh), e.g. pod_3v_conical_crew: faces whose
texel at the UV centroid is close to the window colour (default amber) are grouped into connected windows.
"""
import math
import sys
from collections import defaultdict

import numpy as np
from PIL import Image

obj, tex, base = sys.argv[1], sys.argv[2], float(sys.argv[3])
target = np.array([float(v) for v in sys.argv[4:7]]) if len(sys.argv) > 6 else np.array([200.0, 140.0, 30.0])
tol = float(sys.argv[7]) if len(sys.argv) > 7 else 70.0
img = np.asarray(Image.open(tex).convert("RGB")).astype(np.float32)
H, W = img.shape[:2]
V, T, F = [], [], []
for line in open(obj):
    if line.startswith("v "):
        x, y, z = map(float, line.split()[1:4])
        V.append((-x, z, y - base))
    elif line.startswith("vt "):
        T.append(tuple(map(float, line.split()[1:3])))
    elif line.startswith("f "):
        F.append([tuple(int(i) - 1 for i in t.split("/")[:2]) for t in line.split()[1:]])
hits = []
for f in F:
    u = sum(T[t][0] for _, t in f) / len(f)
    v = sum(T[t][1] for _, t in f) / len(f)
    c = img[int((1 - v % 1.0) * (H - 1)), int((u % 1.0) * (W - 1))]
    if np.linalg.norm(c - target) < tol:
        hits.append([vi for vi, _ in f])
parent = {}


def find(a):
    while parent.setdefault(a, a) != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


key = {}
for f in hits:
    for vi in f:
        k = tuple(round(c, 4) for c in V[vi])
        key.setdefault(k, vi)
for f in hits:
    ks = [key[tuple(round(c, 4) for c in V[vi])] for vi in f]
    for k in ks[1:]:
        parent[find(k)] = find(ks[0])
groups = defaultdict(set)
for f in hits:
    for vi in f:
        groups[find(key[tuple(round(c, 4) for c in V[vi])])].add(vi)
print(f"{len(hits)} window faces in {len(groups)} pieces")
for vs in sorted(groups.values(), key=lambda s: -len(s)):
    pts = [V[i] for i in vs]
    phis = [math.atan2(x, -y) for x, y, z in pts]
    c = math.atan2(sum(math.sin(p) for p in phis), sum(math.cos(p) for p in phis))
    d = [((p - c + math.pi) % (2 * math.pi)) - math.pi for p in phis]
    rs = [math.hypot(x, y) for x, y, z in pts]
    zs = [z for x, y, z in pts]
    r = sum(rs) / len(rs)
    print(f'{{"angle": {-math.degrees(c):.1f}, "z": {(min(zs) + max(zs)) / 2:.3f}, "half_w": {(max(d) - min(d)) / 2 * r:.3f}, '
          f'"half_h": {(max(zs) - min(zs)) / 2:.3f}, "glass_r": {r:.3f}, "verts": {len(pts)}}}')
