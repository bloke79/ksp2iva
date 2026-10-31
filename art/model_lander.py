"""Lander cans (pod_1v/2v/3v_lander_crew): gravity layouts, the part axis up, a real floor.

Usage: blender -b --python model_lander.py -- <spec.json> <texture_dir> <out.blend>

Generator space as everywhere: Blender (x, y, z) = Unity part (x, z, y - hull_base_y); z is up the part (and up under
gravity), -Y the cabin's front. The shell is measured from the extracted exterior (hullshell.py). The windows are
painted on the hull (no glass mesh), so the shell is opened where the spec's windows are; the exterior is one-sided, so
the openings show the world. Crew live in the portrait booth and sit upright at our seat points (UprightCrew).

Spec "lander" block: kind ("1v", "2v", "3v"), windows [[x0, x1, z0, z1, side]] (side -1 front, +1 back), hatch
{side, w, z0, z1}, top_r (docking hatch in the ceiling), floor, ceiling.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ivalib as L  # noqa: E402  (imports bpy first)
from mathutils import Matrix, Vector  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:]
SPEC = json.load(open(ARGS[0]))
TEX, OUT = ARGS[1], ARGS[2]
LAY = SPEC["lander"]
KIND = LAY["kind"]

L.begin(SPEC["interior"], TEX)
import capsule as C  # noqa: E402
import modules as G  # noqa: E402
G.materials()
M = L.M
import stock as S  # noqa: E402
S.materials()
import props as P  # noqa: E402
P.materials()
import cabin as K  # noqa: E402
K.materials()
import hullshell as HS  # noqa: E402
import act as A  # noqa: E402

# the cockpits' finish: grey legend panels, padded grey walls, grey lockers, blue seats
M["console"] = L.material("IVA_ShuttlePanel", tex="shuttle_panel_color.png", normal="panel_normal.png", rough=0.6, metal=0.2, normal_strength=0.4)
M["module"] = L.material("IVA_MidPanel", (0.62, 0.63, 0.64), rough=0.55, metal=0.2)
M["blanket"] = L.material("IVA_WallPadded", tex="wall_padded_color.png", normal="wall_padded_normal.png", rough=0.85, metal=0.0,
                          normal_strength=1.0, uv_scale=(0.5, 0.5))
M["locker"] = L.material("IVA_GreyLocker", (0.40, 0.41, 0.43), rough=0.55, metal=0.15)
M["seat_blue"] = L.material("IVA_SeatBlue", (0.10, 0.17, 0.42), rough=0.9, normal="canvas_normal.png", uv_scale=(5.0, 5.0), normal_strength=0.8)
M["rubber"] = L.material("IVA_Rubber", (0.05, 0.05, 0.055), rough=0.75)
M["velcro"] = L.material("IVA_Velcro", (0.38, 0.55, 0.78), rough=1.0)
M["tank"] = L.material("IVA_Tank", (0.78, 0.79, 0.80), rough=0.3, metal=0.7)
M["jetpack"] = L.material("IVA_Jetpack", (0.82, 0.82, 0.80), rough=0.5, metal=0.2)
M["canvas"] = L.material("IVA_Canvas", (0.27, 0.28, 0.23), rough=0.92, normal="canvas_normal.png", uv_scale=(6.0, 6.0), normal_strength=0.8)
M["umbilical"] = L.material("IVA_Umbilical", (0.32, 0.36, 0.42), rough=0.7)
M["deckplate"] = L.material("IVA_DeckPlate", tex="deckplate_color.png", normal="deckplate_normal.png", rough=0.6, metal=0.35, normal_strength=0.8)
M["whiteboard_art"] = L.material("IVA_WhiteboardArt", tex="whiteboard.png", rough=0.25, metal=0.0)

C.setup(SPEC, wall=SPEC["wall"], ceil=LAY["ceiling"], top=LAY["ceiling"] + 0.02)
FLOOR, CEIL = LAY["floor"], LAY["ceiling"]
DECK = FLOOR + 0.019   # top of the deck plate, where floor-standing things start
SEATS = SPEC["pose"]["seats"]
UP = Vector((0, 0, 1))
WINDOWS = LAY["windows"]


def basis(right, up):
    right, up = Vector(right).normalized(), Vector(up)
    up = (up - up.project(right)).normalized()
    return L.basis(right, up, right.cross(up).normalized())


def wall(x, y, z, gap=0.0):
    """Point and basis on the shell's inner face, looking out from the axis towards (x, y) at height z; up is +z."""
    d = Vector((x, y, 0.0))
    return HS.wall_frame((0.0, 0.0, z), d, gap, up=(0, 0, 1))


def reach(x, y, z, gap=0.0):
    """How far out the shell is from the axis towards (x, y) at height z (the inner face, less gap)."""
    p = HS.inner((0.0, 0.0, z), (x, y, 0.0), gap)
    return Vector((p.x, p.y, 0.0)).length if p is not None else 0.0


def ceiling_at(x, y, gap=0.0):
    """Height of the shell's inner face straight above (x, y)."""
    p = HS.inner((x, y, DECK + 0.3), (0, 0, 1), gap)
    return p.z if p is not None else CEIL


def in_window(p, grow=0.0):
    for x0, x1, z0, z1, side in WINDOWS:
        if p.y * side > 0.2 and x0 - grow < p.x < x1 + grow and z0 - grow < p.z < z1 + grow:
            return True
    return False


# ------------------------------------------------------------------ shell, floor, windows, hatches
def build_shell():
    HS.build("Shell", SPEC["exterior"], SPEC["hull_base_y"], FLOOR, CEIL, wall=SPEC["wall"], dz=0.02, seg=200,
             centre=(0.0, 0.0), mat=M["blanket"], frame_mat=M["frame_dark"], keep=lambda p: not in_window(p))
    # deck plates on the floor, fitted to the shell
    import bmesh
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    n = 96
    ring = []
    for j in range(n):
        a = 2 * math.pi * j / n
        r = reach(math.sin(a), -math.cos(a), FLOOR + 0.03, 0.005)
        ring.append(bm.verts.new((r * math.sin(a), -r * math.cos(a), FLOOR + 0.017)))
    c = bm.verts.new((0, 0, FLOOR + 0.017))
    for j in range(n):
        f = bm.faces.new((c, ring[j], ring[(j + 1) % n]))
        for l in f.loops:
            l[uv].uv = (l.vert.co.x, l.vert.co.y)
    bm.normal_update()
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    L.solidify(L.mesh_obj("DeckFloor", bm, [M["deckplate"]]), 0.012, offset=-1.0)   # top at FLOOR + 0.017
    import bpy
    for o in [o for o in bpy.data.objects if o.name.startswith("ShellFrame")]:   # the shell's own cut-edge frames: the wells' flanges do this
        bpy.data.objects.remove(o, do_unlink=True)
    for k, w in enumerate(WINDOWS):
        window_well(f"Window{k}", *w)
        x0, x1, z0, z1, side = w[:5]
        xc, zc = (x0 + x1) / 2, (z0 + z1) / 2
        if x1 - x0 > 0.15:
            K.view(f"Window{k}", (xc * 0.5, side * 0.3, zc), (xc * 2.0, side * 3.0, zc - 0.2))


def window_well(name, x0, x1, z0, z1, side, *rest):
    """A recess from the cabin lining out to the painted pane: four tunnel sides from the shell to the pane's plane
    (LAY glass_y), and a dark flange on the lining round the opening that covers the shell's stepped cut edge."""
    import bmesh
    gy = LAY["glass_y"]
    def at_shell(x, z):
        p = HS.inner((0.0, 0.0, z), (x, side, 0.0), 0.012)   # just inside the lining, behind the flange
        return p if p is not None else Vector((x, side * 0.8, z))
    corners = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    bm = bmesh.new()
    inner = [bm.verts.new(at_shell(x, z)) for x, z in corners]
    outer = [bm.verts.new((x, gy - side * 0.01, z)) for x, z in corners]
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((inner[i], inner[j], outer[j], outer[i]))
    bm.normal_update()
    c = Vector(((x0 + x1) / 2, 0.0, (z0 + z1) / 2))
    for f in bm.faces:   # facing into the tunnel
        m = f.calc_center_median()
        if f.normal.dot(Vector((c.x - m.x, 0.0, c.z - m.z))) < 0:
            f.normal_flip()
    o = L.mesh_obj(name + "Well", bm, [M["frame_dark"]])
    L.solidify(o, 0.01, offset=-1.0)
    g = 0.035   # flange on the lining, overlapping the cut by g
    for k, (xa, za, xb, zb) in enumerate(((x0 - g - 0.03, z0 - g - 0.03, x1 + g + 0.03, z0 + g), (x0 - g - 0.03, z1 - g, x1 + g + 0.03, z1 + g + 0.03),
                                          (x0 - g - 0.03, z0, x0 + g, z1), (x1 - g, z0, x1 + g + 0.03, z1))):
        xm, zm = (xa + xb) / 2, (za + zb) / 2
        fr = HS.wall_frame((0.0, 0.0, zm), (xm, side, 0.0), -0.012, up=(0, 0, 1))
        if fr:
            S.cbox(f"{name}Flange{k}", (xb - xa, zb - za, 0.02), M["frame_dark"], fr[0], fr[1], ch=0.006)


def round_hatch(name, c, b, r=0.27):
    """b: basis whose third column is the surface normal (towards the viewer)."""
    n = b.col[2]
    ring = [c + (b.col[0] * math.cos(2 * math.pi * j / 48) + b.col[1] * math.sin(2 * math.pi * j / 48)) * r for j in range(48)]
    S.sweep(f"{name}Ring", ring, [n] * 48, S.chamfer_rect(0.07, 0.04, 0.01), M["frame"], closed=True)
    rot = L.basis(b.col[0], b.col[1], n)
    L.cylinder(f"{name}Door", r - 0.03, 0.035, M["hatch"], c + n * 0.012, rot, segs=48, bevel=0.006)
    L.torus(f"{name}Rim", (r - 0.03) * 0.7, 0.01, M["frame"], c + n * 0.032, rot, seg=40, mseg=8)
    L.tube(f"{name}Handle", [c + b.col[0] * -0.08 + n * 0.03, c + b.col[0] * -0.08 + n * 0.07, c + b.col[0] * 0.08 + n * 0.07,
                             c + b.col[0] * 0.08 + n * 0.03], 0.01, M["yellow"])
    for k in range(6):
        a = 2 * math.pi * (k + 0.5) / 6
        d = b.col[0] * math.cos(a) + b.col[1] * math.sin(a)
        S.cbox(f"{name}Dog{k}", (0.04, 0.02, 0.014), M["yellow"], c + d * (r - 0.055) + n * 0.034, L.basis(d, n.cross(d), n), ch=0.003)


def eva_hatch():
    """The EVA hatch where the stock part has its airlock: a rounded-rectangle door in a frame, a lever, grab rails."""
    h = LAY["hatch"]
    side, w, z0, z1 = h["side"], h["w"], h["z0"], h["z1"]
    zc = (z0 + z1) / 2
    # flat on the wall where it is closest across the hatch's width (the lining is curved, recessed round the airlock)
    near = min((HS.inner((0.0, 0.0, z), (x, side, 0.0), 0.0) for x in (-w / 2 - 0.17, 0.0, w / 2 + 0.17) for z in (z0 - 0.05, zc, z1 + 0.05)),
               key=lambda q: abs(q.y))
    fr = wall(0.0, side, zc, 0.03)
    p, b = fr
    p = Vector((0.0, near.y - side * 0.03, zc))
    b = L.basis(Vector((side, 0, 0)), Vector((0, 0, 1)), Vector((0, -side, 0)))
    r_, u, n = b.col[0], b.col[1], b.col[2]
    rot = L.basis(r_, u, n)
    hh = z1 - z0
    S.cbox("EvaHatchFrame", (w + 0.1, hh + 0.1, 0.05), M["frame"], p + n * 0.0, rot, ch=0.03)
    S.cbox("EvaHatchDoor", (w, hh, 0.04), M["hatch"], p + n * 0.035, rot, ch=0.04)
    S.cbox("EvaHatchPanel", (w - 0.1, hh * 0.5, 0.01), M["frame_dark"], p + n * 0.058 + u * hh * 0.12, rot, ch=0.02)
    L.box("EvaHatchWindow", (w * 0.4, 0.1, 0.006), M["glass_dark"], p + n * 0.064 + u * hh * 0.3, rot, bevel=0.002)
    hub = p + n * 0.06 - u * hh * 0.18
    L.cylinder("EvaHatchHub", 0.035, 0.03, M["buckle"], hub, rot, segs=16, bevel=0.004)
    S.cbox("EvaHatchLever", (0.2, 0.035, 0.02), M["yellow"], hub + n * 0.025 + r_ * 0.07, rot, ch=0.006)
    for sx in (-1, 1):
        q = p + r_ * sx * (w / 2 + 0.12) + n * 0.01
        L.tube(f"EvaHatchRail{sx}", [q - u * hh * 0.3, q - u * hh * 0.3 + n * 0.07, q + u * hh * 0.3 + n * 0.07, q + u * hh * 0.3], 0.011, M["yellow"])
    L.box("EvaHatchSign", (0.18, 0.05, 0.006), M["red"], p + n * 0.03 + u * (hh / 2 + 0.09), rot, bevel=0.002)
    for sx in (-1, 1):   # hazard stripes up both jambs
        L.plane(f"EvaHatchHazard{sx}", hh * 0.9, 0.035, M["hazard"], p + n * 0.0255 + r_ * sx * (w / 2 + 0.025), rot @ Matrix.Rotation(math.pi / 2, 3, "Z"), (0, 0, hh * 0.9 / 0.17, 0.5))
        # (laid along the jamb, the stripes at the same scale as the capsule hatch plates)
    return p + n * 0.3


def top_hatch():
    z = CEIL - 0.005
    c = Vector((0.0, 0.0, z))
    round_hatch("TopHatch", c, L.basis(Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, -1))), r=LAY["top_r"])
    for sx in (-1, 1):   # grab handles to pull yourself up into the tunnel
        q = Vector((sx * (LAY["top_r"] + 0.12), 0.0, z))
        L.tube(f"TopHatchRail{sx}", [q + Vector((0, -0.18, 0)), q + Vector((0, -0.18, -0.07)), q + Vector((0, 0.18, -0.07)), q + Vector((0, 0.18, 0))],
               0.011, M["yellow"])
    return c - Vector((0, 0, 0.3))


# ------------------------------------------------------------------ crew stations
def lander_seat(tag, eye, fwd):
    """An LM-style perch: a padded seat pan and short backrest on a post from the floor, armrests, a harness. The
    kerbal sits upright with the eye at `eye` (portrait-booth pose: hips 0.518 below and 0.149 behind the eye)."""
    f = Vector(fwd).normalized()
    r = f.cross(UP).normalized()
    hip = Vector(eye) - UP * 0.518 - f * 0.149
    rot = L.basis(r, f, UP)                     # seat pan: right, forward, up
    S.cbox(f"{tag}Pan", (0.36, 0.34, 0.07), M["seat_blue"], hip - UP * 0.04 + f * 0.04, rot, ch=0.02)
    S.cbox(f"{tag}PanFrame", (0.38, 0.36, 0.03), M["frame_dark"], hip - UP * 0.09 + f * 0.04, rot, ch=0.008)
    post_h = hip.z - 0.1 - DECK
    S.cbox(f"{tag}Post", (0.08, 0.08, post_h), M["frame"], Vector((hip.x, hip.y, DECK + post_h / 2)) + f * 0.04, rot, ch=0.01)
    S.cbox(f"{tag}Foot", (0.3, 0.26, 0.02), M["frame_dark"], Vector((hip.x, hip.y, DECK + 0.01)) + f * 0.04, rot, ch=0.006)
    back = L.basis(r, UP, -f)
    S.cbox(f"{tag}Back", (0.34, 0.42, 0.06), M["seat_blue"], hip + UP * 0.26 - f * 0.15, back, ch=0.02)
    S.cbox(f"{tag}BackFrame", (0.36, 0.44, 0.025), M["frame_dark"], hip + UP * 0.26 - f * 0.19, back, ch=0.006)
    S.cbox(f"{tag}BackStrut", (0.05, 0.05, 0.3), M["frame"], hip + UP * 0.02 - f * 0.18, rot, ch=0.006)
    for sx in (-1, 1):
        S.cbox(f"{tag}Arm{sx}", (0.05, 0.26, 0.04), M["frame"], hip + r * sx * 0.22 + UP * 0.14 + f * 0.04, rot, ch=0.008)
        S.cbox(f"{tag}ArmPad{sx}", (0.045, 0.22, 0.02), M["seat_blue"], hip + r * sx * 0.22 + UP * 0.17 + f * 0.04, rot, ch=0.006)
        L.box(f"{tag}Harness{sx}", (0.045, 0.006, 0.4), M["strap"], hip + r * sx * 0.09 + UP * 0.26 - f * 0.115, rot)
    return hip


def panel(name, p, b, w, h, items, cols, rows, depth=0.04, housing=True):
    s = C.Surface(name, p + b.col[2] * 0.03, b.col[0], b.col[1], w, h, corner=0.02)
    s.build(M["console"], thick=0.025)
    G.grid(s, name, cols, rows, items, border=0.012)
    s.check()
    if housing:
        G.housing(s, name, depth=depth)
    else:   # just a backing plate (where the lining bulges in behind)
        S.cbox(name + "Back", (w + 0.024, h + 0.024, 0.012), M["frame"], s.c - s.n * 0.031, L.basis(s.right, s.up, s.n), ch=0.004)
    return s


DESCENT = [("annunciators", 0, 0, 2, 1, {"cols": 4, "rows": 2}), ("dial", 2, 0, 1, 1, {"kind": "alt"}),
           ("navball", 0, 1, 2, 2, {}), ("dial", 2, 1, 1, 1, {"kind": "press"}), ("toggles", 2, 2, 1, 1, {"cols": 3}),
           ("buttons", 0, 3, 1, 1, {"n": 2}), ("abort", 1, 3, 1, 1, {}), ("knobs", 2, 3, 1, 1, {"n": 2})]


def controls(tag, hip, fwd, side_throttle=-1):
    """Hand controller on one armrest, throttle on the other (the LM's arrangement)."""
    f = Vector(fwd).normalized()
    r = f.cross(UP).normalized()
    for k, sx in enumerate((-side_throttle, side_throttle)):
        base = hip + r * sx * 0.22 + UP * 0.2 + f * 0.14
        if k == 0:
            L.cylinder(f"{tag}RhcBoot", 0.03, 0.04, M["rubber"], base, L.basis(r, f, UP), segs=16)
            L.tube(f"{tag}RhcGrip", [base, base + UP * 0.1 + f * 0.01, base + UP * 0.13 + f * 0.03], 0.018, M["rubber"])
            L.cylinder(f"{tag}RhcButton", 0.007, 0.01, M["red"], base + UP * 0.145 + f * 0.035, L.basis(r, f, UP), segs=10)
        else:
            S.cbox(f"{tag}ThrottleSlot", (0.05, 0.12, 0.02), M["frame_dark"], base, L.basis(r, f, UP), ch=0.004)
            L.tube(f"{tag}ThrottleLever", [base, base + UP * 0.09 + f * 0.02], 0.006, M["toggle"])
            S.cbox(f"{tag}ThrottleHandle", (0.03, 0.04, 0.03), M["rubber"], base + UP * 0.1 + f * 0.025, L.basis(r, f, UP), ch=0.006)


def poster(name, tex, fr, w=0.2, h=0.3):
    if fr is None:
        return
    K.poster(name, tex, fr[0], fr[1], w, h)


# ------------------------------------------------------------------ fitted furniture (the KSP1 lander-can look)
import labelgen  # noqa: E402
M["labels"] = L.material("IVA_DrawerLabels", tex="drawer_labels.png", rough=0.6, metal=0.0)


def face_basis(r):
    """right r (horizontal) -> basis (right, up, normal towards the viewer)"""
    r = Vector(r).normalized()
    return L.basis(r, UP, r.cross(UP).normalized())


def label(name, text, p, b, w):
    i = labelgen.LABELS.index(text)
    c, r = i % labelgen.COLS, i // labelgen.COLS
    uv = (c / labelgen.COLS, 1 - (r + 1) / labelgen.ROWS, (c + 1) / labelgen.COLS, 1 - r / labelgen.ROWS)
    L.box(name + "Plate", (w + 0.008, w / 4 + 0.008, 0.003), M["frame_dark"], p + b.col[2] * 0.0015, b, bevel=0.001)
    L.plane(name, w, w / 4, M["labels"], p + b.col[2] * 0.0032, b, uv)


def bank(name, c, r, w, h, rows, gap=0.022):
    """A locker bank fitted to the hull: a flat front w x h (bottom centre c, right r horizontal, facing r x up), its
    body running back to the shell's inner face so no wall shows behind it. rows (bottom up): (share of h, cells);
    a cell is a label text (a drawer), "door:<label>" (a cupboard door) or None (left plain for the caller: its
    centre, size and basis come back in a list)."""
    import bmesh
    b = face_basis(r)
    r, n = b.col[0], b.col[2]
    c = Vector(c)
    nu, nv = 12, 10
    top = min(ceiling_at(*(c + r * (-w / 2 + w * i / 8)).xy, 0.006) for i in range(9)) - c.z
    if top < h:
        h = top

    def ray(q):
        hit = HS.inner(q, -n, gap)
        return (hit - q).dot(-n) if hit is not None else 1.6

    def depth(q):   # the nearest wall a little above and below too (the lining curves in between rows and at the floor)
        zs = [z for z in (q.z - 0.06, q.z, q.z + 0.06) if z >= DECK + 0.04] or [DECK + 0.04]
        d = min(ray(Vector((q.x, q.y, z))) for z in zs)
        if q.z < DECK + 0.04:
            d -= 0.06
        return max(0.03, min(1.6, d))
    bm = bmesh.new()
    F = [[bm.verts.new(c + r * (-w / 2 + w * i / nu) + UP * (h * j / nv)) for j in range(nv + 1)] for i in range(nu + 1)]
    thin = min((depth(v.co), tuple(round(t, 2) for t in v.co)) for col in F for v in col)
    if thin[0] < 0.06:
        print(f"WARNING bank {name}: only {thin[0] * 100:.0f} cm deep at {thin[1]}")
    B = [[bm.verts.new(v.co - n * depth(v.co)) for v in col] for col in F]
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((F[i][j], F[i + 1][j], F[i + 1][j + 1], F[i][j + 1]))
            bm.faces.new((B[i][j], B[i][j + 1], B[i + 1][j + 1], B[i + 1][j]))
    for j in range(nv):
        bm.faces.new((F[0][j], F[0][j + 1], B[0][j + 1], B[0][j]))
        bm.faces.new((F[nu][j], B[nu][j], B[nu][j + 1], F[nu][j + 1]))
    for i in range(nu):
        bm.faces.new((F[i][0], B[i][0], B[i + 1][0], F[i + 1][0]))
        bm.faces.new((F[i][nv], F[i + 1][nv], B[i + 1][nv], B[i][nv]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    uv = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for lp in f.loops:
            q = lp.vert.co
            lp[uv].uv = (q.x + q.y, q.z) if abs(f.normal.z) < 0.7 else (q.x, q.y)
    L.mesh_obj(name, bm, [M["module"]])
    # trim round the front
    for k, (dx, dz, sw, sh) in enumerate(((0, h - 0.012, w, 0.024), (-w / 2 + 0.012, h / 2, 0.024, h), (w / 2 - 0.012, h / 2, 0.024, h))):
        S.cbox(f"{name}Trim{k}", (sw, sh, 0.012), M["frame_dark"], c + r * dx + UP * dz + n * 0.006, b, ch=0.003)
    S.cbox(f"{name}Kick", (w - 0.05, 0.05, 0.01), M["rubber"], c + UP * 0.03 + n * 0.005, b, ch=0.002)
    blanks = []
    z = 0.06   # drawers start above the kick strip and stop under the top trim, inside the side trims
    for share, cells in rows:
        rh = (h - 0.06 - 0.026) * share
        cw = (w - 0.052) / len(cells)
        for k, cell in enumerate(cells):
            q = c + r * (-w / 2 + 0.026 + cw * (k + 0.5)) + UP * (z + rh / 2)
            tag = f"{name}R{int(z * 100)}C{k}"
            if cell is None:
                blanks.append((q, cw - 0.02, rh - 0.02, b))
                continue
            door = cell.startswith("door:")
            text = cell[5:] if door else cell
            S.cbox(tag, (cw - 0.014, rh - 0.014, 0.016), M["locker"], q + n * 0.008, b, ch=0.004)
            lw = min(cw * 0.62, 0.2)
            lz = rh / 2 - 0.04 - lw / 8 if door else min(0.05, rh * 0.18)
            label(tag + "Label", text, q + n * 0.016 + UP * lz, b, lw)
            if door:   # tall door: a vertical bar handle at the free edge
                hq = q + n * 0.016 + r * (cw / 2 - 0.05)
                L.tube(tag + "Handle", [hq - UP * 0.1, hq - UP * 0.1 + n * 0.03, hq + UP * 0.1 + n * 0.03, hq + UP * 0.1], 0.008, M["handle"])
            else:      # drawer: a bar pull under the label
                hq = q + n * 0.016 - UP * min(0.04, rh * 0.18)
                hw = min(0.07, cw * 0.3)
                L.tube(tag + "Pull", [hq - r * hw, hq - r * hw + n * 0.025, hq + r * hw + n * 0.025, hq + r * hw], 0.007, M["handle"])
        z += rh
    return blanks


def face_panel(name, blank, items, cols, rows):
    q, w, h, b = blank
    s = C.Surface(name, q + b.col[2] * 0.025, b.col[0], b.col[1], w, h, corner=0.015)
    s.build(M["console"], thick=0.025)
    G.grid(s, name, cols, rows, items, border=0.01)
    s.check()
    return s


def ladder(name, x, y, facing, z0, z1, half=0.17):
    """Floor-to-ceiling ladder: two rails, rungs every 25 cm, foot and head plates. facing: +1/-1 along y."""
    for sx in (-1, 1):
        q = Vector((x + sx * half, y, 0))
        L.cylinder(f"{name}Rail{sx}", 0.018, z1 - z0 - 0.006, M["frame"], q + UP * ((z0 + z1) / 2), segs=16)
        for e, zz in enumerate((z0 + 0.008, z1 - 0.009)):
            S.cbox(f"{name}Plate{sx}{e}", (0.07, 0.07, 0.012), M["frame_dark"], q + UP * zz, ch=0.003)
    k = 0
    zr = z0 + 0.25
    while zr < z1 - 0.12:
        a, bb = Vector((x - half, y, zr)), Vector((x + half, y, zr))
        L.tube(f"{name}Rung{k}", [a, bb], 0.013, M["handle"])
        zr += 0.25
        k += 1


def pole(name, x, y, z0, z1):
    """The Mk1 can's climbing pole: one column with pegs either side."""
    q = Vector((x, y, 0))
    L.cylinder(name, 0.028, z1 - z0 - 0.006, M["frame"], q + UP * ((z0 + z1) / 2), segs=20)
    for e, zz in enumerate((z0 + 0.008, z1 - 0.009)):
        L.cylinder(f"{name}Flange{e}", 0.06, 0.012, M["frame_dark"], q + UP * zz, segs=20)
    for k, zz in enumerate([z0 + 0.22 + 0.2 * i for i in range(int((z1 - z0 - 0.3) / 0.2))]):
        sx = 1 if k % 2 == 0 else -1
        L.tube(f"{name}Peg{k}", [q + UP * zz + Vector((sx * 0.02, 0, 0)), q + UP * zz + Vector((sx * 0.1, 0, 0))], 0.013, M["handle"])
        L.cylinder(f"{name}PegEnd{k}", 0.02, 0.02, M["rubber"], q + UP * zz + Vector((sx * 0.11, 0, 0)), L.basis(Vector((0, 1, 0)), UP, Vector((sx, 0, 0))), segs=12)


def extinguisher(name, p, b):
    """Red fire extinguisher in a wall bracket. p, b: wall point and basis (normal out of the wall)."""
    n, r = b.col[2], b.col[0]
    c = p + n * 0.06
    L.cylinder(name, 0.045, 0.26, M["red"], c, segs=20, bevel=0.012)
    L.cylinder(name + "Valve", 0.018, 0.05, M["frame_dark"], c + UP * 0.15, segs=12)
    L.tube(name + "Handle", [c + UP * 0.17, c + UP * 0.19 + n * 0.05], 0.007, M["frame_dark"])
    L.tube(name + "Hose", [c + UP * 0.16 + r * 0.02, c + UP * 0.12 + r * 0.06, c - UP * 0.05 + r * 0.055], 0.006, M["rubber"])
    S.cbox(name + "Bracket", (0.05, 0.22, 0.012), M["frame"], c - n * 0.051, b, ch=0.002)
    for k, zz in enumerate((-0.07, 0.07)):
        L.torus(f"{name}Band{k}", 0.047, 0.004, M["frame"], c + UP * zz, L.basis(Vector((1, 0, 0)), Vector((0, 1, 0)), UP), seg=24, mseg=6)


def helmet(name, c, facing):
    """A spare helmet sitting on a shelf: white shell, dark visor, neck ring."""
    f = Vector(facing).normalized()
    L.sphere(name, 0.12, M["jetpack"], c + UP * 0.14)
    L.sphere(name + "Visor", 0.105, M["glass_dark"], c + UP * 0.15 + f * 0.03)
    L.torus(name + "Ring", 0.095, 0.016, M["frame"], c + UP * 0.03, L.basis(Vector((1, 0, 0)), Vector((0, 1, 0)), UP), seg=32, mseg=8)


# ------------------------------------------------------------------ the three layouts
H_FULL = CEIL - DECK - 0.012


def build_1v():
    eye, fwd = Vector(SEATS[0]["eye"]), Vector(SEATS[0]["fwd"])
    hip = lander_seat("Seat0", eye, fwd)
    controls("Seat0", hip, fwd)
    # descent panels on the two angled front walls, either side of the window; a low console under the window
    for sx in (-1, 1):   # on the lining's pillars either side of the window, facing in (the Mk1 can's panels are right in front)
        items = DESCENT if sx < 0 else [("mfd", 0, 0, 2, 2, {"screen": "mfd_map"}), ("dial", 2, 0, 1, 1, {"kind": "fuel"}),
                                        ("annunciators", 2, 1, 1, 1, {"cols": 2, "rows": 2, "start": 8}),
                                        ("toggles", 0, 2, 3, 1, {"cols": 6}), ("breakers", 0, 3, 3, 1, {"cols": 9, "rows": 2})]
        a = math.radians(150.0)
        d = Vector((sx * math.sin(a), math.cos(a), 0.0))
        c = d * 0.565 + UP * 0.8
        b = face_basis(UP.cross(-d))
        panel(f"Descent{sx}", c - b.col[2] * 0.03, b, 0.26, 0.42, items, 3, 4, housing=False)
        top = min(ceiling_at(*(c + b.col[0] * u).xy, 0.01) for u in (-0.14, 0.0, 0.14))
        fh = top - (c.z + 0.222)   # a cover plate from the panel up to the ceiling, over the lining's pillar
        if fh > 0.03:
            S.cbox(f"Descent{sx}Fascia", (0.284, fh, 0.012), M["frame"], c + UP * (0.222 + fh / 2) - b.col[2] * 0.031, b, ch=0.004)
    yc = -reach(0, -1, 0.25, 0.02) + 0.14
    S.cbox("Console", (0.34, 0.24, 0.2), M["frame"], Vector((0, yc, DECK + 0.1)), ch=0.012)
    s = C.Surface("ConsoleTop", (0, yc - 0.01, DECK + 0.205), (-1, 0, 0), (0, -1, 0.5), 0.32, 0.2, corner=0.012)
    s.build(M["console"], thick=0.015, rim=False)
    G.grid(s, "ConsoleTop", 2, 1, [("keypad", 0, 0, 1, 1, {}), ("toggles", 1, 0, 1, 1, {"cols": 3})], border=0.008)
    s.check()
    # overhead switches just above the helmet, in front of the top hatch
    zc = min(ceiling_at(x, y) for x in (-0.21, 0.21) for y in (-0.55, -0.39))
    S.cbox("OverheadBox", (0.42, 0.16, 0.05), M["frame"], Vector((0, -0.47, zc - 0.028)), ch=0.008)
    o = C.Surface("Overhead", (0, -0.47, zc - 0.07), (-1, 0, 0), (0, 1, 0.25), 0.38, 0.13, corner=0.01)
    o.build(M["console"], thick=0.015, rim=False)
    G.grid(o, "Overhead", 3, 1, [("toggles", 0, 0, 2, 1, {"cols": 6}), ("lamps", 2, 0, 1, 1, {"n": 3})], border=0.008)
    o.check()
    # drawer stacks either side of the seat, floor to ceiling; their top cells carry the side panels
    bl = bank("BankL", (-0.36, -0.1, DECK), (0, 1, 0), 0.56, H_FULL, [(0.36, ["SOCKS"]), (0.3, ["FOOD", "SNACKS"]), (0.34, [None])])
    face_panel("SideL", bl[0], [("knobs", 0, 0, 1, 1, {"n": 2}), ("lamps", 1, 0, 1, 1, {"n": 3}), ("breakers", 0, 1, 2, 1, {"cols": 6, "rows": 2})], 2, 2)
    br = bank("BankR", (0.36, -0.1, DECK), (0, -1, 0), 0.56, H_FULL, [(0.36, ["ROCKS"]), (0.3, ["SCIENCE", "SPARE BOLTS"]), (0.34, [None])])
    face_panel("SideR", br[0], [("dial", 0, 0, 1, 1, {"kind": "press"}), ("dial", 1, 0, 1, 1, {"kind": "temp"}), ("toggles", 0, 1, 2, 1, {"cols": 5})], 2, 2)
    # aft: a helmet shelf and the extinguisher to the left of the hatch, a tall locker to the right
    bank("ShelfL", (-0.36, 0.38, DECK), (0, 1, 0), 0.32, 0.5, [(1.0, ["door:HELMETS"])])
    helmet("Helmet", Vector((-0.5, 0.38, DECK + 0.5)), (1, 0.2, 0))   # on the shelf top
    fr = wall(-1, 0.45, 1.0, 0.005)
    if fr:
        extinguisher("Extinguisher", fr[0], fr[1])
    bank("LockerR", (0.36, 0.38, DECK), (0, -1, 0), 0.32, H_FULL, [(1.0, ["door:MYSTERY"])])
    pole("Pole", -0.16, 0.34, DECK, ceiling_at(-0.16, 0.34))   # beside the hatch, not in front of it


def build_2v():
    for i, st in enumerate(SEATS):
        hip = lander_seat(f"Seat{i}", Vector(st["eye"]), Vector(st["fwd"]))
        controls(f"Seat{i}", hip, st["fwd"], side_throttle=-1 if i == 0 else 1)
    # descent panels on the curved wall either side of the window bay, centre stack between the stations
    for sx in (-1, 1):
        fr = wall(sx * 0.62, -1.0, 0.8, 0.05)
        if fr:
            items = DESCENT if sx < 0 else [("mfd", 0, 0, 2, 2, {"screen": "mfd_engine"}), ("dial", 2, 0, 1, 1, {"kind": "fuel"}),
                                            ("annunciators", 2, 1, 1, 1, {"cols": 2, "rows": 2, "start": 6}),
                                            ("toggles", 0, 2, 3, 1, {"cols": 6}), ("breakers", 0, 3, 3, 1, {"cols": 9, "rows": 2})]
            panel(f"Descent{sx}", fr[0], fr[1], 0.42, 0.55, items, 3, 4, depth=0.02)
    yc = -0.85
    S.cbox("CentreStack", (0.26, 0.32, 0.55), M["frame"], Vector((0, yc, DECK + 0.275)), ch=0.012)
    s = C.Surface("CentreTop", (0, yc - 0.01, DECK + 0.555), (-1, 0, 0), (0, -1, 0.4), 0.24, 0.3, corner=0.012)
    s.build(M["console"], thick=0.015, rim=False)
    G.grid(s, "CentreTop", 1, 3, [("mfd", 0, 0, 1, 1, {"screen": "mfd_systems"}), ("keypad", 0, 1, 1, 1, {}),
                                  ("toggles", 0, 2, 1, 1, {"cols": 4})], border=0.008)
    s.check()
    # side consoles at the elbows: life support port, radar and comms starboard
    b = bank("ConsoleL", (-0.72, -0.62, DECK), (0, 1, 0), 0.42, H_FULL, [(0.5, ["TOOLS"]), (0.5, [None])])
    face_panel("LifeSupport", b[0], [("dial", 0, 0, 1, 1, {"kind": "press"}), ("dial", 1, 0, 1, 1, {"kind": "temp"}),
                                     ("lamps", 0, 1, 1, 1, {"n": 3}), ("toggles", 1, 1, 1, 1, {"cols": 3})], 2, 2)
    b = bank("ConsoleR", (0.72, -0.62, DECK), (0, -1, 0), 0.42, H_FULL, [(0.5, ["FIRST AID"]), (0.5, [None])])
    face_panel("Radar", b[0], [("screen", 0, 0, 2, 1, {"mat": "crt_data"}), ("knobs", 0, 1, 1, 1, {"n": 2}),
                               ("annunciators", 1, 1, 1, 1, {"cols": 2, "rows": 2, "start": 10})], 2, 2)
    # right behind the seats, the ladder up to the docking hatch
    ladder("Ladder", 0.0, LAY["top_r"] + 0.08, 1, DECK, ceiling_at(0.0, LAY["top_r"] + 0.08))
    # the aisle back to the EVA hatch, between drawer banks
    b = bank("BankL", (-0.5, 0.45, DECK), (0, 1, 0), 1.1, H_FULL,
             [(0.3, ["BOARD GAMES", "SOCKS", "BEDS"]), (0.3, ["FOOD", "NOT FOOD", "SNACKS"]), (0.4, ["SPOONS", None, "MAPS"])])
    q, w, h, bb = b[0]
    P.whiteboard("Board", q, bb, w - 0.02, min(h, 0.3))
    b = bank("BankR", (0.5, 0.45, DECK), (0, -1, 0), 1.1, H_FULL,
             [(0.32, ["ROCKS", "MORE ROCKS", "ROCKS (DO NOT EAT)"]), (0.4, ["SCIENCE?", None]), (0.28, ["JUNK", None, "DUCT TAPE"])])
    q, w, h, bb = b[0]
    P.glovebox("Glovebox", q, bb, w - 0.04, h - 0.04, 0.24)
    q, w, h, bb = b[1]
    K.poster("PosterStruts", "struts", q, bb, min(w, h * 0.66) * 0.75, h * 0.8)


def build_3v():
    for i, st in enumerate(SEATS):
        hip = lander_seat(f"Seat{i}", Vector(st["eye"]), Vector(st["fwd"]))
        if i < 2:
            controls(f"Seat{i}", hip, st["fwd"], side_throttle=-1 if i == 0 else 1)
    # the main panel under the window band (+y), sloping up towards the windows
    s = C.Surface("MainPanel", (0, 1.55, 0.6), (1, 0, 0), (0, 0.55, 1), 1.3, 0.4, corner=0.03)
    s.build(M["console"], thick=0.03)
    G.grid(s, "Main", 8, 3, [
        ("annunciators", 0, 0, 2, 1, {"cols": 4, "rows": 2}), ("dial", 2, 0, 1, 1, {"kind": "alt"}), ("navball", 3, 0, 2, 2, {}),
        ("dial", 5, 0, 1, 1, {"kind": "press"}), ("annunciators", 6, 0, 2, 1, {"cols": 4, "rows": 2, "start": 8}),
        ("mfd", 0, 1, 2, 2, {"screen": "mfd_map"}), ("toggles", 2, 1, 1, 1, {"cols": 2}), ("knobs", 2, 2, 1, 1, {"n": 2}),
        ("keypad", 3, 2, 2, 1, {}), ("toggles", 5, 1, 1, 1, {"cols": 2}), ("buttons", 5, 2, 1, 1, {"n": 2}),
        ("mfd", 6, 1, 2, 2, {"screen": "mfd_systems"})], border=0.012)
    s.check()
    # open-backed: end cheeks carry it (a solid housing would swallow the navball, which sits deep behind the face)
    for sx in (-1, 1):
        S.cbox(f"MainPanelCheek{sx}", (0.04, s.h + 0.03, 0.14), M["frame"], s.c + s.right * sx * (s.w / 2 + 0.02) - s.n * 0.06,
               L.basis(s.right, s.up, s.n), ch=0.008)
    S.cbox("MainPanelBase", (1.2, 0.16, 0.6), M["frame"], Vector((0, 1.76, DECK + 0.3)), ch=0.015)
    # centre console between the front seats
    S.cbox("CentreConsole", (0.22, 0.6, 0.5), M["frame"], Vector((0, 0.95, DECK + 0.25)), ch=0.012)
    t = C.Surface("CentreTop", (0, 0.95, DECK + 0.505), (1, 0, 0), (0, 1, 0), 0.2, 0.58, corner=0.01)
    t.build(M["console"], thick=0.015, rim=False)
    G.grid(t, "CentreTop", 1, 3, [("keypad", 0, 0, 1, 1, {}), ("toggles", 0, 1, 1, 1, {"cols": 3}), ("knobs", 0, 2, 1, 1, {"n": 2})], border=0.008)
    t.check()
    # side consoles at the front seats' elbows, each topped with a sloping panel
    for sx, name, items in ((-1, "LifeSupport", [("dial", 0, 0, 1, 1, {"kind": "press"}), ("dial", 1, 0, 1, 1, {"kind": "temp"}),
                                                  ("lamps", 2, 0, 1, 1, {"n": 3}), ("mfd", 0, 1, 2, 1, {"screen": "mfd_comms"}),
                                                  ("knobs", 2, 1, 1, 1, {"n": 2})]),
                            (1, "Radar", [("screen", 0, 0, 2, 1, {"mat": "crt_data"}), ("lamps", 2, 0, 1, 1, {"n": 3}),
                                          ("breakers", 0, 1, 2, 1, {"cols": 8, "rows": 2}), ("toggles", 2, 1, 1, 1, {"cols": 3})])):
        bank(f"Console{sx}", (sx * 0.95, 0.9, DECK), (0, -sx, 0), 0.7, 0.68, [(1.0, ["TOOLS", "SPARE PARTS"] if sx < 0 else ["WATER", "OXYGEN?"])])
        top = C.Surface(name, (sx * 1.12, 0.9, DECK + 0.8), (0, -sx, 0), (sx, 0, 0.6), 0.62, 0.34, corner=0.015)
        top.build(M["console"], thick=0.02)
        G.grid(top, name, 3, 2, items, border=0.01)
        top.check()
    # port: the galley nook (counter, splashback with the oven, cupboards over); starboard: the toilet cubby
    bank("GalleyCounter", (-1.05, 0.0, DECK), (0, 1, 0), 1.08, 0.74, [(1.0, ["SPOONS", "FOOD", "NOT FOOD"])])
    S.cbox("GalleyWorktop", (0.34, 1.06, 0.03), M["frame"], Vector((-1.2, 0.0, DECK + 0.755)), ch=0.006)
    sb = bank("GalleySplash", (-1.36, 0.0, DECK + 0.77), (0, 1, 0), 1.08, 0.38, [(1.0, [None, None])])
    P.oven("GalleyOven", sb[0][0] - UP * 0.02, sb[0][3], w=0.26, h=0.18, d=0.16)
    P.utensil_rack("GalleyRack", sb[1][0], sb[1][3], w=0.3)
    bank("GalleyCupboard", (-1.15, 0.0, DECK + 1.15), (0, 1, 0), 1.08, 0.4, [(1.0, ["JEB'S SNACKS", "EMERGENCY SNACKS", "MORE SNACKS"])])
    sci = bank("Science", (0.95, 0.0, DECK), (0, -1, 0), 1.0, 1.3,
               [(0.3, ["ROCKS", "MORE ROCKS", "ROCKS (DO NOT EAT)"]), (0.4, [None, None]), (0.3, ["SCIENCE", "SCIENCE?", "JUNK"])])
    q, w, h, bb = sci[0]
    P.whiteboard("Board", q, bb, w - 0.04, h - 0.06)
    q, w, h, bb = sci[1]
    P.glovebox("Glovebox", q, bb, w - 0.04, h - 0.06, 0.2)
    # the ladder behind the rear seats, then the aisle to the EVA hatch between lockers
    ladder("Ladder", 0.0, -(LAY["top_r"] + 0.08), -1, DECK, ceiling_at(0.0, -(LAY["top_r"] + 0.08)))
    bank("AftL", (-0.45, -0.85, DECK), (0, 1, 0), 0.6, 1.3, [(0.3, ["BEDS", "SOCKS"]), (0.35, ["FOOD", "MAPS"]), (0.35, ["BOARD GAMES", "MANUALS (UNREAD)"])])
    bank("SuitL", (-0.45, -1.3, DECK), (0, 1, 0), 0.3, 1.12, [(1.0, ["door:HELMETS"])], gap=0.04)
    K.hygiene_room("Toilet", Vector((0.95, -0.9, DECK + 0.03 + 0.6)), L.basis(Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((-1, 0, 0))),
                   0.7, 1.2, 0.5, door_w=0.5, door_h=1.05)
    bank("NookR", (0.45, -1.35, DECK), (0, -1, 0), 0.2, 1.12, [(1.0, ["door:MAPS"])], gap=0.04)
    K.poster("PosterSafety", "safety", Vector((0.7, -0.535, DECK + 0.85)), face_basis((-1, 0, 0)), 0.24, 0.34)   # on the toilet's side
    # the end of the port aft lockers faces the cabin: a poster on it
    xe = min(abs(HS.inner((0.0, -0.56, z), (-1, 0, 0), 0.03).x) for z in (0.75, 1.15))
    K.poster("PosterMinmus", "minmus", Vector((-(0.45 + xe) / 2, -0.55, DECK + 0.95)), face_basis((-1, 0, 0)), 0.26, 0.38)


def lights():
    xs = {"1v": [(0.0, -0.66), (0.0, 0.6)], "2v": [(-0.45, -0.45), (0.45, -0.45), (0.0, 0.75)],
          "3v": [(-0.55, 0.75), (0.55, 0.75), (0.0, -1.0), (0.0, 0.5), (-0.95, 0.0), (0.95, -0.2), (0.0, 1.25)]}[KIND]
    for k, (x, y) in enumerate(xs):
        fr = HS.wall_frame((x, y, DECK + 0.5), (0, 0, 1), 0.004, up=(0, 1, 0))
        if fr:
            S.light_fixture(f"CeilLight{k}", fr[0], fr[1], w=0.24, h=0.07)


# ------------------------------------------------------------------ build
build_shell()
eva_at = eva_hatch()
top_at = top_hatch()
{"1v": build_1v, "2v": build_2v, "3v": build_3v}[KIND]()
lights()
for i, st in enumerate(SEATS):
    C.eye_marker(i, st)
def hull_radius(z):
    """The lining's nearest approach at a height (it isn't round everywhere: pillars, the window recesses)."""
    z = min(max(z, DECK + 0.05), CEIL - 0.03)
    rs = [reach(math.sin(a), math.cos(a), z) for a in [2 * math.pi * k / 48 for k in range(48)]]
    rs = [r for r in rs if r > 0.2]
    return min(rs) if rs else 0.5


S.collision_markers(hatches=[("Side", tuple(eva_at)), ("Tunnel", tuple(top_at))], hull=hull_radius,
                    floors=[((0.0, 0.0, DECK), (0.0, 0.0, 1.0))])
import surfaces  # noqa: E402
if not os.environ.get("IVA_NO_DETAIL"):
    surfaces.apply()
L.save(OUT)
