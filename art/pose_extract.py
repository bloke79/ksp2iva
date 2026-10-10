"""Derives couch-fitting numbers from a seated-kerbal pose capture and writes them into a pod spec's "pose" block.

Usage: python -I pose_extract.py <pose.obj> <stock_interior.json> <spec.json>

<pose.obj> is written by the mod's pose dump (CustomInterior.DumpPoses): posed kerbal meshes in part space, Unity axes,
one group per seat/mesh, with "# seat N eye x y z fwd x y z" lines. <stock_interior.json> is dump_kerbals.py output for
the pod's stock interior prefab (stick, throttle and pedal anchors). Neither file is game art that ships; only the
numbers below go into the spec. Output is in the generator's Blender space: x = Unity x, y = Unity z, z = Unity y - hull base.
"""
import json
import re
import sys

import numpy as np

pose_path, stock_path, spec_path = sys.argv[1:4]
spec = json.load(open(spec_path))
base = spec["hull_base_y"]


def to_b(p):
    return [round(p[0], 4), round(p[2], 4), round(p[1] - base, 4)]


seats, groups, cur = [], {}, None
for line in open(pose_path):
    if line.startswith("# seat"):
        n = list(map(float, re.findall(r"-?\d+\.\d+", line)))
        seats.append({"eye": to_b(n[0:3]), "fwd": [round(n[3], 3), round(n[5], 3), round(n[4], 3)]})
    elif line.startswith("g "):
        cur = line[2:].strip()
        groups[cur] = []
    elif line.startswith("v "):
        groups[cur].append(to_b(list(map(float, line.split()[1:]))))

# couch profile from seat 0 (every seat uses the same prefab pose, offset sideways)
x0 = seats[0]["eye"][0]
v = np.array([p for g, vs in groups.items() if g.startswith("seat0") for p in vs])
v[:, 0] -= x0
y0, y1 = v[:, 1].min(), v[:, 1].max()
STEP = 0.03
prof = []
for y in np.arange(y0 - 0.01, y1 + 0.011, STEP):
    s = v[(v[:, 1] >= y - STEP) & (v[:, 1] < y + STEP)]
    if len(s) == 0:
        continue
    z = s[:, 2].min()
    contact = s[s[:, 2] < z + 0.05]
    prof.append([float(y), float(z), float(np.percentile(np.abs(contact[:, 0]), 98) * 2)])
prof = np.array(prof)
# lower envelope, lightly smoothed, so no bump of the body pokes through the cushion
z = prof[:, 1]
zs = np.minimum.reduce([np.roll(z, 1), z, np.roll(z, -1)])
zs[0], zs[-1] = z[0], z[-1]
zs = np.convolve(np.pad(zs, 1, mode="edge"), [0.25, 0.5, 0.25], mode="valid")
zs = np.minimum(zs, z)
prof[:, 1] = zs - 0.012
stock = {r["path"].split("/")[-1]: r["pos"] for r in json.load(open(stock_path)) if r["path"].endswith(("bone_control_r_joystick", "bone_control_l_throttle", "bone_pedal_l_slide"))
         and "(1)" not in r["path"] and "(2)" not in r["path"]}
# hands: the arm clusters outside the torso; the fist is the top of each cluster, the elbow its lowest point
suit = np.array([p for g, vs in groups.items() if g == "seat0_mesh_spacesuit_01" for p in vs])
suit[:, 0] -= x0
hands = {}
for side, sel in (("right", suit[:, 0] > 0.15), ("left", suit[:, 0] < -0.15)):
    h = suit[sel]
    zc = h[:, 2].max() - 0.3 * (h[:, 2].max() - h[:, 2].min())
    fist = h[h[:, 2] >= zc].mean(0)
    hands[side] = {"fist": [round(float(c), 3) for c in fist], "elbow_z": round(float(h[:, 2].min()), 3),
                   "y": [round(float(h[:, 1].min()), 3), round(float(h[:, 1].max()), 3)]}
head = np.array([p for g, vs in groups.items() if g.startswith("seat0") and "head" in g for p in vs])
spec["pose"] = {
    "_source": "pose capture (mod pose dump) + stock interior anchors; regenerate with pose_extract.py",
    "seats": [{"x": s["eye"][0], "eye": s["eye"], "fwd": s["fwd"]} for s in seats],
    "couch": [[round(a, 3), round(b, 3), round(c, 3)] for a, b, c in prof],
    "head": {"y": [round(float(head[:, 1].min()), 3), round(float(head[:, 1].max()), 3)],
             "z": [round(float(head[:, 2].min()), 3), round(float(head[:, 2].max()), 3)]},
    "body": {"y": [round(float(y0), 3), round(float(y1), 3)], "z_top": round(float(v[:, 2].max()), 3),
             "half_x": round(float(np.abs(v[:, 0]).max()), 3)},
    "hands": hands,
    "stick": [round(c - (x0 if i == 0 else 0), 3) for i, c in enumerate(to_b(stock["bone_control_r_joystick"]))],
    "throttle": [round(c - (x0 if i == 0 else 0), 3) for i, c in enumerate(to_b(stock["bone_control_l_throttle"]))],
    "pedals": [round(c - (x0 if i == 0 else 0), 3) for i, c in enumerate(to_b(stock["bone_pedal_l_slide"]))],
}
json.dump(spec, open(spec_path, "w"), indent=1)
print("pose:", len(seats), "seat(s); couch", len(prof), "samples; eye", seats[0]["eye"], "fwd", seats[0]["fwd"])
for a, b, c in prof:
    print(f"  y {a:+.3f}  z {b:.3f}  w {c:.3f}")
