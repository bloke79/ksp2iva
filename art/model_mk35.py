"""Mk3-5 (pod_3v_conical_crew) interior: five crew on a lower deck, an upper deck with a docking station.

2026-10-11 rework (PLAN.md "Mk3-5 pod rework"): the cockpits' shuttle-era finish; the aft bulkhead replaced by a toilet
compartment (port, door on the aisle) and an equipment bay (starboard), both bounded by the hull; suit hoses from floor
ports; low lockers in the front corners; the living deck laid out round a clear climb to the docking hatch.

Usage: blender -b --python model_mk35.py -- <spec.json> <texture_dir> <out.blend>

The game keeps the 3v's crew in the portrait booth, so the seats are ours: five couches in a row on one frame, eyes at
z 1.0, the same body pose as the Mk1-3 (spec "pose"). Above the faces hangs a five-section main display console; pedestal
consoles sit between the couches and side consoles beside the outer couches, under the two-pane side windows. Behind the
feet: environmental and power units, lockers and a ladder up through a hatch in the upper deck, a grated platform with an
equipment ring, and a docking station console under the two upper (docking) windows. The pod's windows are painted on
its hull, which isn't drawn from inside, so the openings here show the world.

Coordinates and conventions: see capsule.py.
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

L.begin(SPEC["interior"], TEX)
import capsule as C  # noqa: E402  (after begin: shares L.M)
import modules as G  # noqa: E402
import props as P  # noqa: E402
import stock as S  # noqa: E402
G.materials()

M = L.M
M["blanket"] = L.material("IVA_WallPanel", tex="wallpanel_color.png", normal="wallpanel_normal.png", rough=0.55, metal=0.3, uv_scale=(1.0, 1.0), normal_strength=0.8)
M["shell"] = L.material("IVA_SeatShell", (0.22, 0.23, 0.25), rough=0.4, metal=0.55)
M["bottle"] = L.material("IVA_Bottle", (0.22, 0.42, 0.30), rough=0.35, metal=0.4)
M["tank"] = L.material("IVA_Tank", (0.78, 0.79, 0.80), rough=0.3, metal=0.7)
M["periscope"] = L.material("IVA_Periscope", tex="periscope.png", rough=0.1, emit=1.6, emit_tex=True)
M["canvas"] = L.material("IVA_Canvas", (0.27, 0.28, 0.23), rough=0.92, normal="canvas_normal.png", uv_scale=(6.0, 6.0), normal_strength=0.8)
M["umbilical"] = L.material("IVA_Umbilical", (0.32, 0.36, 0.42), rough=0.7)
M["net"] = L.material("IVA_Net", (0.30, 0.32, 0.20), rough=0.9)
P.materials()
S.materials()
import cabin as K  # noqa: E402
K.materials()
M["deckplate"] = L.material("IVA_DeckPlate", tex="deckplate_color.png", normal="deckplate_normal.png", rough=0.6, metal=0.35, normal_strength=0.8)
import act as A  # noqa: E402
# shuttle-era finish, as the Mk1 and Mk3 cockpits
M["console"] = L.material("IVA_ShuttlePanel", tex="shuttle_panel_color.png", normal="panel_normal.png", rough=0.6, metal=0.2, normal_strength=0.4)
M["module"] = M["console"]
M["blanket"] = L.material("IVA_WallPadded", tex="wall_padded_color.png", normal="wall_padded_normal.png", rough=0.85, metal=0.0, normal_strength=1.0, uv_scale=(0.5, 0.5))
M["glare"] = L.material("IVA_Glareshield", (0.045, 0.046, 0.05), rough=0.85)
M["cushion"] = L.material("IVA_SeatBlue", (0.10, 0.17, 0.42), rough=0.9, normal="canvas_normal.png", uv_scale=(5.0, 5.0), normal_strength=0.8)
M["shell"] = L.material("IVA_SeatFrame", (0.42, 0.44, 0.47), rough=0.45, metal=0.5)
M["locker"] = L.material("IVA_GreyLocker", (0.40, 0.41, 0.43), rough=0.55, metal=0.15)
M["velcro"] = L.material("IVA_Velcro", (0.38, 0.55, 0.78), rough=1.0)

C.setup(SPEC, wall=SPEC["wall"], ceil=SPEC["ceiling"], top=SPEC["ceiling"] + 0.1, seg=192)
POSE = SPEC["pose"]
SEATS = POSE["seats"]
H = SPEC["hatch"]
HATCH_PHI, HATCH_HALF = C.rad(-H["angle"]), C.rad(H["half_deg"])
EYE_Z = SEATS[0]["eye"][2]
FLOOR = C.Z_FLOOR
DECK_Z = 2.0                      # upper (living and lab) deck floor
HOLE_Y0, HOLE_Y1, HOLE_HW = 1.0, 1.38, 0.3    # ladder opening in the deck, at the back of the aisle
FACE_Y, AISLE, TOP = 0.55, 0.40, 1.95        # aft rooms: front face plane, aisle half-width, top (under the deck)
HATCH_Y = 0.80                                # floor hatch down, in the aisle
DOOR_Y0, DOOR_Y1, DOOR_H = 0.62, 1.16, 1.42   # toilet door in the port aisle wall
SIDE_PHI0, SIDE_PHI1, SIDE_Z0, SIDE_Z1 = 78, 102, 0.78, 1.18


def keep_clear(phi):
    if C.ang_dist(phi, HATCH_PHI) < HATCH_HALF + C.rad(5):
        return True
    for w in C.WINDOWS:
        if C.ang_dist(phi, w["phi"]) < w["hw"] / C.r_in(w["z"]) + C.rad(5):
            return True
    return False


# ------------------------------------------------------------------ five-section main display console
MDC_Z, MDC_Y, MDC_H, MDC_W = EYE_Z + 0.44, -0.13, 0.42, 0.56


def section(name, x, tilt_deg):
    side = 1 if x > 0 else -1
    t = C.rad(tilt_deg)
    right = Vector((math.cos(t), 0, -side * math.sin(t))) if x else Vector((1, 0, 0))
    drop = abs(x) * 0.07
    return C.Surface(name, (x, MDC_Y, MDC_Z - drop), right, (0, -1, 0), MDC_W, MDC_H, bend=0.0, corner=0.04)


def build_mdc():
    secs = {0: section("MDC_C", 0.0, 0), 1: section("MDC_R1", 0.62, 8), -1: section("MDC_L1", -0.62, 8),
            2: section("MDC_R2", 1.24, 20), -2: section("MDC_L2", -1.24, 20)}
    for s in secs.values():
        s.build(M["console"], thick=0.03)
    layouts = {
        0: [("dial", 0, 0, 1, 1, {"kind": "alt"}), ("annunciators", 1, 0, 4, 1, {"cols": 8, "rows": 2}), ("dial", 5, 0, 1, 1, {"kind": "fuel"}),
            ("mfd", 0, 1, 2, 2, {"screen": "mfd_systems"}), ("navball", 2, 1, 2, 2, {}), ("mfd", 4, 1, 2, 2, {"screen": "mfd_map"}),
            ("abort", 0, 3, 1, 1, {}), ("buttons", 1, 3, 1, 1, {"n": 3}), ("toggles", 2, 3, 2, 1, {"cols": 6}), ("knobs", 4, 3, 1, 1, {"n": 2}),
            ("lamps", 5, 3, 1, 1, {"n": 3})],
        1: [("dial", 0, 0, 1, 1, {"kind": "press"}), ("dial", 1, 0, 1, 1, {"kind": "temp"}), ("annunciators", 2, 0, 2, 1, {"cols": 4, "rows": 2, "start": 4}),
            ("mfd", 0, 1, 2, 2, {"screen": "mfd_engine"}), ("keypad", 2, 1, 2, 2, {}), ("breakers", 0, 3, 4, 1, {"cols": 12, "rows": 2})],
        -1: [("knobs", 0, 0, 2, 1, {"n": 4}), ("dial", 2, 0, 1, 1, {"kind": "press"}), ("dial", 3, 0, 1, 1, {"kind": "temp"}),
             ("mfd", 0, 1, 2, 2, {"screen": "mfd_comms"}), ("screen", 2, 1, 2, 1, {"mat": "crt_orbit"}), ("toggles", 2, 2, 2, 1, {"cols": 6}),
             ("breakers", 0, 3, 2, 1, {"cols": 6, "rows": 2}), ("vent", 2, 3, 1, 1, {}), ("lamps", 3, 3, 1, 1, {"n": 3})],
        2: [("annunciators", 0, 0, 4, 1, {"cols": 8, "rows": 2, "start": 8}), ("screen", 0, 1, 2, 1, {"mat": "crt_data"}),
            ("dial", 2, 1, 1, 1, {"kind": "fuel"}), ("dial", 3, 1, 1, 1, {"kind": "press"}), ("toggles", 0, 2, 2, 1, {"cols": 6}),
            ("knobs", 2, 2, 2, 1, {"n": 4}), ("breakers", 0, 3, 4, 1, {"cols": 12, "rows": 2})],
        -2: [("mfd", 0, 0, 2, 2, {"screen": "mfd_systems"}), ("periscope", 2, 0, 2, 2, {}), ("lamps", 0, 2, 2, 1, {"n": 4}),
             ("toggles", 2, 2, 2, 1, {"cols": 6}), ("breakers", 0, 3, 4, 1, {"cols": 12, "rows": 2})],
    }
    for k, s in secs.items():
        G.grid(s, s.name, 6 if k == 0 else 4, 4, layouts[k])
        s.check()
        G.housing(s, s.name)
    # structure: seams between sections, hangers up to the deck, hood with floodlights and a handrail
    for x in (-0.93, -0.31, 0.31, 0.93):
        z = MDC_Z - abs(x) * 0.07 + 0.01
        S.beam(f"MDC_Seam{x}", Vector((x, MDC_Y - MDC_H / 2 - 0.02, z)), Vector((x, MDC_Y + MDC_H / 2 - 0.005, z)), 0.05, 0.05, M["frame"], up=(0, 0, 1))
        for k, y in enumerate((MDC_Y - 0.17, MDC_Y + 0.17)):
            top = DECK_Z - (0.17 if abs(x) < 0.5 else 0.08)   # the inner pair stop under the ceiling hub ring
            S.beam(f"MDC_Hanger{x}_{k}", Vector((x, y, z + 0.02)), Vector((x, y, top)), 0.038, 0.038, M["frame"], up=(0, 1, 0))
            for zz in (z + 0.16, top - 0.08):
                S.cbox(f"MDC_Collar{x}_{k}_{zz:.2f}", (0.054, 0.054, 0.035), M["frame_dark"], (x, y, zz), ch=0.006)
    hy = MDC_Y + MDC_H / 2 + 0.02
    S.cbox("MDC_Hood", (3.0, 0.04, 0.08), M["frame"], (0, hy, MDC_Z - 0.03), ch=0.012)
    aim = Vector((0, 0.45, -1)).normalized()
    for k, x in enumerate((-1.24, -0.62, 0.0, 0.62, 1.24)):
        p = Vector((x, hy + 0.01, MDC_Z - 0.08 - abs(x) * 0.07))
        L.cylinder(f"Flood_{k}", 0.022, 0.03, M["ring"], p, (-aim).to_track_quat("Z", "Y").to_matrix(), segs=20, radius2=0.017)
        L.disc(f"FloodLens_{k}", 0.014, M["light"], p + aim * 0.016, aim.to_track_quat("Z", "Y").to_matrix(), segs=20)
    L.plane("NamePlate", 0.3, 0.06, M["plate"], Vector((0, hy + 0.017, MDC_Z - 0.03)), L.basis(Vector((-1, 0, 0)), Vector((0, 0, 1)), Vector((0, 1, 0))))
    # button beam (the glareshield of a crew on their backs): along each section's head edge, hanging below the panel,
    # its underside carrying the warning strip and the master-alarm buttons; clear of the sight line to the top row
    for k, sct in secs.items():
        up = sct.up.normalized()
        down = -sct.right.cross(up).normalized()          # away from the crew is +n; the beam hangs towards them
        if down.z > 0:
            down = -down
        edge = sct.c + up * (sct.h / 2 + 0.02)
        rot = L.basis(sct.right, up, -down)
        S.cbox(f"Beam{sct.name}", (sct.w - 0.04, 0.05, 0.07), M["glare"], edge + down * 0.02, rot, ch=0.01)
        strip = C.Surface(f"Beam{sct.name}Strip", edge + down * 0.056, sct.right, up, sct.w - 0.06, 0.04, corner=0.005)
        strip.n = (sct.right.cross(up)).normalized()
        if strip.n.z > 0:
            strip.right = -strip.right
            strip.n = strip.right.cross(up).normalized()
        strip.build(M["console"], thick=0.006, rim=False)
        G.grid(strip, f"Beam{sct.name}Strip", 10, 1, [("buttons", 0, 0, 1, 1, {"n": 1}), ("annunciators", 1, 0, 8, 1, {"cols": 8, "rows": 1, "start": (abs(k) * 5) % 12}),
                                                     ("buttons", 9, 0, 1, 1, {"n": 1})], border=0.003, gap=0.003)
        strip.check()


# ------------------------------------------------------------------ couches, pedestals, umbilicals
PED_W, PED_Y0, PED_Y1 = 0.15, -0.06, 0.32


def build_lower_deck():
    for i, seat in enumerate(SEATS):
        C.couch(f"Couch{i}_", seat["x"], POSE, FLOOR)
    xs = sorted(s["x"] for s in SEATS)
    prof = POSE["couch"]
    for k, y in enumerate((prof[len(prof) // 4][0], prof[(3 * len(prof)) // 4][0])):
        z = min(zz for yy, zz, ww in prof if abs(yy - y) < 0.04) - 0.1
        S.beam(f"CouchFrameBeam_{k}", Vector((xs[0] - 0.16, y, z)), Vector((xs[-1] + 0.16, y, z)), 0.05, 0.06, M["frame"])
        for x in (xs[0] - 0.14, xs[-1] + 0.14):   # (the pedestals carry the frame between the couches)
            S.beam(f"CouchFrameLeg_{k}_{x:.2f}", Vector((x, y, z)), Vector((x * 1.04, y, FLOOR + 0.02)), 0.045, 0.045, M["frame"], up=(0, 1, 0))
            S.cbox(f"CouchFrameFoot_{k}_{x:.2f}", (0.09, 0.09, 0.025), M["frame_dark"], (x * 1.04, y, FLOOR + 0.0125), ch=0.008)
            for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
                L.cylinder(f"CouchFrameFootBolt_{k}_{x:.2f}_{i}", 0.006, 0.008, M["buckle"], (x * 1.04 + sx * 0.032, y + sy * 0.032, FLOOR + 0.028), segs=6)
    z0p, z1p = 0.45 + (EYE_Z - 0.718), 0.53 + (EYE_Z - 0.718)
    up_dir = Vector((0, PED_Y0 - PED_Y1, z0p - z1p)).normalized()
    slope = math.hypot(PED_Y1 - PED_Y0, z1p - z0p)
    for k, x in enumerate((-0.93, -0.31, 0.31, 0.93)):
        G.prism(f"Pedestal{k}", [(PED_Y0, FLOOR), (PED_Y1, FLOOR), (PED_Y1, z1p), (PED_Y0, z0p)], x - PED_W / 2, x + PED_W / 2, M["console"])
        top = C.Surface(f"PedestalTop{k}", (x, (PED_Y0 + PED_Y1) / 2, (z0p + z1p) / 2 + 0.004), (-1, 0, 0), up_dir, PED_W - 0.012, slope - 0.02, corner=0.01)
        G.grid(top, f"Ped{k}", 2, 4, [
            ("toggles", 0, 0, 2, 1, {"cols": 4}), ("dial", 0, 1, 1, 1, {"kind": ("press", "temp")[k % 2]}), ("knobs", 1, 1, 1, 1, {"n": 1}),
            ("lamps", 0, 2, 2, 1, {"n": 4}), ("buttons", 0, 3, 1, 1, {"n": 2}), ("toggles", 1, 3, 1, 1, {"cols": 2})], gap=0.004, border=0.004)
        top.check()
        G.vent(f"PedestalVent{k}", Vector((x, PED_Y0 - 0.001, (FLOOR + z0p) / 2)), L.basis(Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0))),
               PED_W * 0.7, (z0p - FLOOR) * 0.5, slots=8)
    # suit umbilicals: a manifold under the floor from the equipment bay; each couch has a floor port behind its foot end
    dz = EYE_Z - 0.718
    for i, seat in enumerate(SEATS):
        x = seat["x"]
        port = Vector((x - 0.1, 0.42, FLOOR))
        L.cylinder(f"UmbilicalPort{i}", 0.05, 0.02, M["frame_dark"], port + Vector((0, 0, 0.01)), segs=20, bevel=0.004)
        L.cylinder(f"UmbilicalPortCollar{i}", 0.03, 0.04, M["buckle"], port + Vector((0, 0, 0.035)), segs=16)
        pts = [port + Vector((0, 0, 0.05)), Vector((x - 0.12, 0.37, FLOOR + 0.16)), Vector((x - 0.19, 0.16, FLOOR + 0.26)),
               Vector((x - 0.2, -0.04, 0.5 + dz)), Vector((x - 0.15, -0.12, 0.58 + dz)), Vector((x - 0.13, -0.16, 0.6 + dz))]
        G.hose(f"Umbilical{i}", pts, r=0.018, mat=M["umbilical"])
        L.cylinder(f"UmbilicalPlug{i}", 0.026, 0.04, M["buckle"], pts[-1], (pts[-1] - pts[-2]).normalized().to_track_quat("Z", "Y").to_matrix(), segs=16)


# ------------------------------------------------------------------ aft rooms: toilet compartment (port) and equipment bay (starboard)
def face_x(z):
    """How far the front face (y = FACE_Y) reaches out before it meets the hull, at height z."""
    return math.sqrt(max(0.0, C.r_in(z) ** 2 - FACE_Y ** 2)) - 0.015


def aisle_y(z):
    """How far aft the aisle wall (|x| = AISLE) runs before it meets the hull, at height z."""
    return math.sqrt(max(0.0, C.r_in(z) ** 2 - AISLE ** 2)) - 0.015


def fitted_wall(name, side, kind, hole=None, thick=0.03):
    """A flat wall from the aisle corner out (or back) to the hull, floor to TOP, cut to the hull row by row.
    kind 'face': the plane y = FACE_Y; 'aisle': the plane x = side * AISLE. hole: (u0, u1, z0, z1) left open.
    Its face looks into the cabin (or the aisle); its thickness goes into the room behind."""
    import bmesh
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    nz = 18
    zs = [FLOOR + (TOP - FLOOR) * k / nz for k in range(nz + 1)]
    u0 = AISLE if kind == "face" else FACE_Y + thick + 0.002
    lim = face_x if kind == "face" else aisle_y
    for i in range(nz):
        za, zb = zs[i], zs[i + 1]
        ua, ub = lim(za), lim(zb)
        nu = max(2, int(round((max(ua, ub) - u0) / 0.06)))
        for k in range(nu):
            ta, tb = k / nu, (k + 1) / nu
            um = u0 + (ta + tb) / 2 * ((ua + ub) / 2 - u0)
            if hole and hole[0] < um < hole[1] and hole[2] < (za + zb) / 2 < hole[3]:
                continue
            q = [(u0 + ta * (ua - u0), za), (u0 + tb * (ua - u0), za), (u0 + tb * (ub - u0), zb), (u0 + ta * (ub - u0), zb)]
            if kind == "face":
                vs = [bm.verts.new((side * u, FACE_Y, z)) for u, z in q]
            else:
                vs = [bm.verts.new((side * AISLE, u, z)) for u, z in q]
            f = bm.faces.new(vs)
            for l in f.loops:
                c = l.vert.co
                l[uv].uv = ((c.x if kind == "face" else c.y) * 1.0, c.z * 1.0)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.normal_update()
    want = Vector((0, -1, 0)) if kind == "face" else Vector((-side, 0, 0))
    for f in bm.faces:
        if f.normal.dot(want) < 0:
            f.normal_flip()
    o = L.mesh_obj(name, bm, [M["blanket"]])
    L.solidify(o, thick, offset=-1.0)
    return o


def toilet_door():
    """Concertina door: a pleated screen just inside the port aisle wall, folded into a slim stack at the aft side of
    the doorway when open; F draws it across (it stretches along its track, like the curtains)."""
    w, h = DOOR_Y1 - DOOR_Y0, DOOR_H - 0.02
    x0 = -AISLE - 0.052
    zc = FLOOR + 0.01 + h / 2
    stack = 0.12                                     # folded width
    anchor = Vector((x0, DOOR_Y1 - 0.01, zc))
    n = 12
    parts = []
    for k in range(n):                               # pleats, zig-zagging across the track, modelled folded
        ya = anchor.y - stack * k / n
        yb = anchor.y - stack * (k + 1) / n
        xa, xb = x0 + (0.018 if k % 2 else -0.018), x0 + (-0.018 if k % 2 else 0.018)
        c = Vector(((xa + xb) / 2, (ya + yb) / 2, zc))
        d = Vector((xb - xa, yb - ya, 0.0))
        r = d.normalized()
        rot = L.basis(r, Vector((0, 0, 1)), r.cross(Vector((0, 0, 1))).normalized())
        parts.append(L.box(f"ToiletDoorPleat{k}", (d.length + 0.002, h, 0.006), M["locker"], c, rot, bevel=0.0015))
    post = L.box("ToiletDoorPost", (0.03, h + 0.01, 0.012), M["yellow"], Vector((x0 + 0.004, anchor.y - stack - 0.006, zc)),
                 L.basis(Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0))), bevel=0.003)
    parts.insert(0, post)
    A.curtain("ToiletDoor", parts, anchor, anchor - Vector((0, stack + 0.012, 0)), Vector((x0, DOOR_Y0 + 0.004, zc)),
              act_at=Vector((-AISLE + 0.01, DOOR_Y0 + 0.08, zc)))
    for z_ in (FLOOR + 0.008, FLOOR + DOOR_H + 0.004):   # top and bottom tracks across the doorway
        S.cbox(f"ToiletDoorTrack{z_:.2f}", (0.05, w + 0.03, 0.012), M["frame_dark"], Vector((x0, (DOOR_Y0 + DOOR_Y1) / 2, z_)), ch=0.002)
    face = L.basis(Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((1, 0, 0)))    # seen from the aisle: right is forward
    # frame round the opening on the aisle side, and the engaged/vacant sign beside it
    L.tube("ToiletDoorFrame", [Vector((-AISLE + 0.012, DOOR_Y0 - 0.012, FLOOR)), Vector((-AISLE + 0.012, DOOR_Y0 - 0.012, FLOOR + DOOR_H + 0.012)),
                               Vector((-AISLE + 0.012, DOOR_Y1 + 0.012, FLOOR + DOOR_H + 0.012)), Vector((-AISLE + 0.012, DOOR_Y1 + 0.012, FLOOR))], 0.012, M["frame"])
    sign = Vector((-AISLE + 0.006, DOOR_Y1 + 0.12, FLOOR + 1.32))
    L.box("ToiletSign", (0.14, 0.07, 0.008), M["frame"], sign, face, bevel=0.002)
    L.box("ToiletSignLamp", (0.04, 0.03, 0.006), M.get("lamp_green", M["light"]), sign + Vector((0.006, -0.04, 0)), face, bevel=0.002)


def toilet_wall_boxes():
    """Collision for the toilet's aisle wall, leaving the doorway open (the wall mesh itself is NoCol)."""
    x, t = -AISLE - 0.015, 0.02
    y_end = 1.72
    zc, hz = (FLOOR + TOP) / 2, (TOP - FLOOR) / 2
    out = [((x, (FACE_Y + DOOR_Y0) / 2, zc), (t, 0, 0), (0, (DOOR_Y0 - FACE_Y) / 2, 0), (0, 0, hz)),
           ((x, (DOOR_Y1 + y_end) / 2, zc), (t, 0, 0), (0, (y_end - DOOR_Y1) / 2, 0), (0, 0, hz))]
    za = FLOOR + DOOR_H
    out.append(((x, (DOOR_Y0 + DOOR_Y1) / 2, (za + TOP) / 2), (t, 0, 0), (0, (DOOR_Y1 - DOOR_Y0) / 2, 0), (0, 0, (TOP - za) / 2)))
    return out


def build_aft_rooms():
    # living spaces in a plain light finish (the switch-panel texture stays on the flight deck's consoles)
    M["module"] = L.material("IVA_MidPanel", (0.62, 0.63, 0.64), rough=0.55, metal=0.2)
    fitted_wall("ToiletFace", -1, "face")
    fitted_wall("NoColToiletAisleWall", -1, "aisle", hole=(DOOR_Y0, DOOR_Y1, FLOOR - 0.01, FLOOR + DOOR_H))
    fitted_wall("BayFace", 1, "face")
    fitted_wall("BayAisleWall", 1, "aisle")
    for side in (-1, 1):   # trim on the aisle corners and along the tops
        L.tube(f"AftCorner{side}", [Vector((side * AISLE, FACE_Y, FLOOR)), Vector((side * AISLE, FACE_Y, TOP))], 0.016, M["frame"])
    toilet_door()
    # inside the compartment: toilet on the floor at the back, wash point, towels, handholds, light, vent
    P.toilet("Toilet", *at(-150, FLOOR + 0.2, 0.025))
    P.sink("ToiletSink", *at(-118, FLOOR + 0.95, 0.0))
    P.towels("ToiletTowels", *at(-134, FLOOR + 1.3, 0.0))
    for k, (deg, z) in enumerate(((-140, FLOOR + 0.75), (-128, FLOOR + 1.05))):
        (pa, ba), (pb, bb) = at(deg, z, 0.012), at(deg + 8, z, 0.012)
        L.tube(f"ToiletGrip{k}", [pa, pa + ba.col[2] * 0.05, pb + bb.col[2] * 0.05, pb], 0.009, M["yellow"])
    S.light_fixture("ToiletLight", Vector((-0.85, 0.95, TOP - 0.01)), L.basis(Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, -1))), w=0.22, h=0.07)
    G.vent("ToiletVent", Vector((-0.75, FACE_Y + 0.031, 1.65)), L.basis(Vector((-1, 0, 0)), Vector((0, 0, 1)), Vector((0, 1, 0))), 0.24, 0.12, slots=6)
    # front of the toilet compartment, facing the couches: lockers and a fire extinguisher
    face = L.basis(Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0)))
    k = 0
    for row, z in enumerate((0.48, 0.76, 1.04, 1.32, 1.60)):
        for col in range(4):
            x = -AISLE - 0.18 - col * 0.31
            if abs(x) + 0.16 > face_x(z + 0.13) - 0.01:
                continue
            G.box_unit(f"FaceLocker{k}", (x, FACE_Y - 0.035, z), (0.29, 0.07, 0.26), vents=False, lamps_n=0)
            L.box(f"FaceLockerTag{k}", (0.07, 0.022, 0.002), M["btn_soft"], Vector((x + 0.06, FACE_Y - 0.0715, z + 0.1)), face)
            k += 1
    L.cylinder("Extinguisher", 0.05, 0.34, M["extinguisher"], Vector((AISLE - 0.065, 1.47, 1.05)), segs=24, bevel=0.01)
    L.cylinder("ExtinguisherHead", 0.022, 0.05, M["rib"], Vector((AISLE - 0.065, 1.47, 1.245)), segs=12)
    # equipment bay face: ECS and power panel above, CO2 cartridge drawers and lockers below
    zc, h = 1.6, 0.46
    w = face_x(zc + h / 2) - 0.03 - AISLE - 0.03
    xc = AISLE + 0.03 + w / 2
    ecs = C.Surface("EcsPanel", (xc, FACE_Y - 0.03, zc), (1, 0, 0), (0, 0, 1), w, h, corner=0.02)
    ecs.build(M["console"], thick=0.03)
    G.grid(ecs, "Ecs", 4, 3, [
        ("annunciators", 0, 0, 2, 1, {"cols": 6, "rows": 2, "start": 4}), ("dial", 2, 0, 1, 1, {"kind": "press"}), ("dial", 3, 0, 1, 1, {"kind": "temp"}),
        ("mfd", 0, 1, 2, 2, {"screen": "mfd_systems"}), ("toggles", 2, 1, 2, 1, {"cols": 6}), ("breakers", 2, 2, 2, 1, {"cols": 8, "rows": 2})], border=0.012)
    ecs.check()
    G.housing(ecs, "EcsPanel", depth=0.03)
    P.drawer_stack("Co2Drawers", Vector((AISLE + 0.2, FACE_Y, 1.02)), face, 0.3, 0.5, 4)
    k = 0
    for row, z in enumerate((0.48, 0.76, 1.04)):
        for col in range(3):
            x = AISLE + 0.52 + col * 0.31
            if x + 0.16 > face_x(z + 0.13) - 0.01 or (row == 2 and col == 0):
                continue
            G.box_unit(f"BayLocker{k}", (x, FACE_Y - 0.035, z), (0.29, 0.07, 0.26), vents=(row == 0), lamps_n=2 if row == 0 else 0)
            k += 1
    # the aisle: comms station on the starboard wall, handholds both sides, first aid
    s = C.Surface("CommsStation", (AISLE - 0.03, 0.98, 1.5), (0, -1, 0), (0, 0, 1), 0.44, 0.28, corner=0.015)
    s.build(M["console"], thick=0.025)
    G.grid(s, "Comms", 4, 2, [("mfd", 0, 0, 2, 2, {"screen": "mfd_comms"}), ("keypad", 2, 0, 1, 2, {}),
                              ("annunciators", 3, 0, 1, 1, {"cols": 2, "rows": 2, "start": 10}), ("toggles", 3, 1, 1, 1, {"cols": 3})], border=0.01)
    s.check()
    G.housing(s, "CommsStation", depth=0.02)
    P.headset("CommsHeadset", Vector((AISLE - 0.005, 1.25, 1.3)), L.basis(Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((-1, 0, 0))))
    P.velcro("ToiletVelcro", *at(-126, FLOOR + 1.55, 0.0))
    poster("PosterDuna", "duna", *at(-143, 1.68, 0.0), w=0.2, h=0.3)
    P.velcro("CommsVelcro", Vector((AISLE - 0.001, 0.72, 1.5)), L.basis(Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((-1, 0, 0))), w=0.05, h=0.14)
    for side in (-1, 1):
        y0, y1 = (DOOR_Y1 + 0.05, DOOR_Y1 + 0.3) if side < 0 else (0.62, 0.86)
        for z in (0.8, 1.45):
            L.tube(f"AisleHandhold{side}{z}", [Vector((side * AISLE, y0, z)), Vector((side * (AISLE - 0.05), y0, z)),
                                                Vector((side * (AISLE - 0.05), y1, z)), Vector((side * AISLE, y1, z))], 0.009, M["yellow"])
    L.box("FirstAid", (0.16, 0.12, 0.08), M["btn_soft"], Vector((AISLE - 0.04, 1.25, 0.95)), L.basis(Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((-1, 0, 0))), bevel=0.008)
    L.box("FirstAidCrossH", (0.06, 0.018, 0.004), M["red"], Vector((AISLE - 0.081, 1.25, 0.95)), L.basis(Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((-1, 0, 0))))
    L.box("FirstAidCrossV", (0.018, 0.06, 0.004), M["red"], Vector((AISLE - 0.0812, 1.25, 0.95)), L.basis(Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((-1, 0, 0))))


def build_front_lockers():
    """Low lockers in the two front corners, below the side windows' sills, clear of the route to the EVA hatch."""
    poster("PosterSafety", "safety", *at(45, 1.62, 0.0), w=0.22, h=0.33)      # either side of the EVA hatch
    poster("PosterStaging", "staging", *at(-45, 1.62, 0.0), w=0.22, h=0.33)
    for side in (-1, 1):   # velcro above the lockers and beside the side consoles, where checklists go
        P.velcro(f"FrontVelcro{side}", *at(side * 39, 0.86, 0.0))
        P.velcro(f"SideVelcro{side}", *at(side * 108, 1.32, 0.0))
    k = 0
    for side in (-1, 1):
        for deg in (29, 39, 49):
            for z in (0.42, 0.64):
                p, b = at(side * deg, z, 0.0)
                d = 0.26
                L.box(f"FrontLocker{k}", (0.27, 0.2, d), M["locker"], p + b.col[2] * (d / 2 + 0.005), b, bevel=0.006)
                L.box(f"FrontLockerLatch{k}", (0.05, 0.016, 0.012), M["handle"], p + b.col[2] * (d + 0.011) + b.col[1] * 0.06, b, bevel=0.003)
                L.box(f"FrontLockerTag{k}", (0.07, 0.02, 0.002), M["btn_soft"], p + b.col[2] * (d + 0.0062) - b.col[1] * 0.05, b)
                k += 1


# ------------------------------------------------------------------ side consoles under the two-pane windows
def build_side_consoles():
    for side in (1, -1):
        p0, p1 = (C.rad(SIDE_PHI0), C.rad(SIDE_PHI1)) if side > 0 else (-C.rad(SIDE_PHI1), -C.rad(SIDE_PHI0))
        nm = "SideConsoleR" if side > 0 else "SideConsoleL"
        band = C.Band(nm, p0, p1, SIDE_Z0, SIDE_Z1, 0.08)
        band.build(M["console"])
        mid = math.degrees((p0 + p1) / 2)
        G.band_grid(band, nm, mid, (SIDE_Z0 + SIDE_Z1) / 2, 10, 3, 0.11, 0.12, [
            ("breakers", 0, 0, 6, 1, {"cols": 18, "rows": 2}), ("annunciators", 6, 0, 4, 1, {"cols": 8, "rows": 2, "start": 8 if side > 0 else 0}),
            ("dial", 0, 1, 1, 1, {"kind": "press"}), ("dial", 1, 1, 1, 1, {"kind": "temp"}), ("mfd", 2, 1, 2, 2, {"screen": "mfd_comms" if side > 0 else "mfd_engine"}),
            ("toggles", 4, 1, 3, 1, {"cols": 9}), ("knobs", 7, 1, 3, 1, {"n": 6}),
            ("screen", 0, 2, 2, 1, {"mat": "crt_data"}), ("toggles", 4, 2, 3, 1, {"cols": 9}), ("vent", 7, 2, 3, 1, {"slots": 5}),
        ])
        band.check()


# ------------------------------------------------------------------ decks: platforms, openings, ladders, ceiling lights
def round_tiles(bm, uv, rr, z, step, skip, down=False):
    import bmesh
    """Square deck tiles filling a circle of radius rr at height z, the edge cells clipped to the circle (outside corners
    pulled in onto it), so the deck's edge is round rather than stepped. skip(cx, cy): leave a cell out (openings)."""
    k = int(rr / step) + 2
    vs = {}

    def vert(i, j):
        if (i, j) not in vs:
            x, y = i * step, j * step
            r = math.hypot(x, y)
            if r > rr:
                x, y = x * rr / r, y * rr / r
            vs[(i, j)] = bm.verts.new((x, y, z))
        return vs[(i, j)]
    for i in range(-k, k):
        for j in range(-k, k):
            cs = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            if all(math.hypot(a * step, b * step) >= rr for a, b in cs):
                continue
            cx, cy = (i + 0.5) * step, (j + 0.5) * step
            if skip(cx, cy):
                continue
            q = [vert(a, b) for a, b in (cs[::-1] if down else cs)]
            if len({v.co.to_tuple(5) for v in q}) < 3:
                continue
            try:
                f = bm.faces.new(q)
            except ValueError:
                continue
            for l in f.loops:
                l[uv].uv = (l.vert.co.x, l.vert.co.y)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges)


def platform(name, z, holes, ceiling=False):
    """Grated deck at height z filling the hull, with rectangular openings (x0, x1, y0, y1); rim, radial beams and
    downlights on its underside (the ceiling of the deck below)."""
    import bmesh
    rr = C.r_in(z) - 0.01
    tiles = bmesh.new()
    uv = tiles.loops.layers.uv.new("UVMap")
    round_tiles(tiles, uv, rr - 0.012, z, 0.1, lambda cx, cy: any(h[0] < cx < h[1] and h[2] < cy < h[3] for h in holes))
    L.solidify(L.mesh_obj(name, tiles, [M.get("deckplate", M["floor"])]), 0.03)
    L.tube(name + "Rim", [C.polar(2 * math.pi * j / 96, rr - 0.015, z - 0.015) for j in range(97)], 0.02, M["couchframe"])
    for k2 in range(0 if ceiling else 8):
        phi = 2 * math.pi * (k2 + 0.5) / 8
        L.tube(f"{name}Beam{k2}", [C.polar(phi, 0.25, z - 0.05), C.polar(phi, rr - 0.02, z - 0.05)], 0.022, M["couchframe"])
        p = C.polar(phi + math.pi / 8, rr * 0.55, z - 0.045)
        L.cylinder(f"{name}Downlight{k2}", 0.04, 0.025, M["ring"], p, segs=20)
        L.disc(f"{name}DownlightLens{k2}", 0.03, M["light"], p - Vector((0, 0, 0.013)), Matrix.Rotation(math.pi, 3, "X"), segs=20)
    for h in holes:   # hazard-striped railing round each opening (open on the ladder side)
        x0, x1, y0, y1 = h
        P.hazard_rail(f"{name}Rail{h[0]:.2f}", [Vector((x0, y1 - 0.1, z)), Vector((x0, y1 - 0.1, z + 0.45)), Vector((x0, y0, z + 0.45)),
                                                 Vector((x1, y0, z + 0.45)), Vector((x1, y1 - 0.1, z + 0.45)), Vector((x1, y1 - 0.1, z))], 0.009)


def build_decks():
    platform("DeckB", DECK_Z, [(-HOLE_HW, HOLE_HW, HOLE_Y0, HOLE_Y1)], ceiling=True)
    ladder("LadderAft", 0.0, 1.3, FLOOR, DECK_Z + 0.55, 0.22)
    S.round_floor_hatch("Aft", 0.0, HATCH_Y, FLOOR, r=0.27, hinge=(0.0, 1.0))   # down to the modules below (handwheel, lid opens down)
    ladder("LadderTunnel", 0.0, 0.3, DECK_Z, C.Z_TOP - 0.08, 0.18)


def poster(name, tex, p, b, w=0.24, h=0.36):
    """A crew poster on a wall (p, b from at()): a thin dark backing board and the print."""
    key = "poster_" + tex
    if key not in M:
        M[key] = L.material(f"IVA_Poster_{tex.capitalize()}", tex=f"poster_{tex}.png", rough=0.7, metal=0.0)
    L.box(name + "Board", (w + 0.02, h + 0.02, 0.006), M["frame_dark"], p + b.col[2] * 0.003, b, bevel=0.002)
    L.plane(name, w, h, M[key], p + b.col[2] * 0.0065, b)


# ------------------------------------------------------------------ sleep pods: crew quarters fitted into the cone
def sleep_pod(name, p0, p1, z0, z1, depth=0.4):
    """A private sleeping pod between wall angles p0..p1 (degrees) and heights z0..z1: two side walls, a floor and a roof
    from the hull in to `depth`, and a front frame leaning with the cone round a curtained opening. The hull is its back
    wall, so nothing can poke through. Inside: a sleeping bag, a reading lamp (F toggles it), a small locker."""
    import bmesh
    a0, a1 = C.rad(p0), C.rad(p1)
    nphi, nz = 8, 10
    phis = [a0 + (a1 - a0) * i / nphi for i in range(nphi + 1)]
    zs = [z0 + (z1 - z0) * k / nz for k in range(nz + 1)]

    def H(phi, z):
        return C.polar(phi, C.r_in(z) - 0.012, z)

    def I(phi, z):
        return C.polar(phi, C.r_in(z) - depth, z)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    quads = []
    for phi in (a0, a1):                                   # side walls
        for k in range(nz):
            quads.append([H(phi, zs[k]), I(phi, zs[k]), I(phi, zs[k + 1]), H(phi, zs[k + 1])])
    for z in (z0, z1):                                     # floor and roof
        for i in range(nphi):
            quads.append([H(phis[i], z), H(phis[i + 1], z), I(phis[i + 1], z), I(phis[i], z)])
    jamb = 0.05 / max(0.3, C.r_in((z0 + z1) / 2) - depth)   # 5 cm jambs, in radians
    sill, header = 0.07, 0.1
    for i in range(nphi):                                   # front frame: sill and header
        for za, zb in ((z0, z0 + sill), (z1 - header, z1)):
            quads.append([I(phis[i], za), I(phis[i + 1], za), I(phis[i + 1], zb), I(phis[i], zb)])
    for pa, pb in ((a0, a0 + jamb), (a1 - jamb, a1)):       # jambs
        for k in range(nz):
            za, zb = max(zs[k], z0 + sill), min(zs[k + 1], z1 - header)
            if zb > za:
                quads.append([I(pa, za), I(pb, za), I(pb, zb), I(pa, zb)])
    for q in quads:
        f = bm.faces.new([bm.verts.new(v) for v in q])
        for l in f.loops:
            l[uv].uv = (l.vert.co.x + l.vert.co.y, l.vert.co.z)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    o = L.mesh_obj(name + "Pod", bm, [M["locker"]])
    L.solidify(o, 0.018, offset=0.0)
    mid, zm = (p0 + p1) / 2, (z0 + z1) / 2
    width = 2 * (C.r_in(zm) - depth) * math.sin((a1 - a0) / 2)
    # inside: the bag on the hull, a locker above it, the lamp under the roof
    P.sleeping_bag(name + "Bag", *at(mid, z0 + 0.06 + (z1 - z0 - 0.3) / 2, 0.03), w=min(0.38, width - 0.04), h=z1 - z0 - 0.36, d=0.11)
    P.cabinet(name + "Locker", *at(mid, z1 - 0.13, 0.025), min(0.24, width - 0.1), 0.12, 0.12, doors=1)
    lamp_p, lamp_b = at(mid + (p1 - p0) * 0.28, z1 - 0.03, 0.2)
    L.cylinder(name + "Lamp", 0.025, 0.03, M["ring"], lamp_p, segs=16)
    A.glow(name, L.disc(name + "LampGlow", 0.02, M["light"], lamp_p - Vector((0, 0, 0.016)), Matrix.Rotation(math.pi, 3, "X"), segs=20),
           act_at=lamp_p - Vector((0, 0, 0.03)))
    # curtain across the opening: hangs from a rod under the header, drawn open towards the first jamb
    fa, fb = I(a0 + jamb, zm), I(a1 - jamb, zm)
    across = fb - fa
    across.z = 0.0
    across = across.normalized()
    pf, bf = at(mid, zm, depth + 0.02)
    up = (bf.col[1] - bf.col[1].project(across)).normalized()
    n = across.cross(up).normalized()
    if n.dot(Vector((-pf.x, -pf.y, 0.0))) < 0:
        n = -n                                   # out of the pod, towards the cabin
    cb = L.basis(across, up, n)
    span = (fb - fa).length
    ch = (z1 - header) - (z0 + sill) - 0.02
    left = (fa + fb) / 2 - across * (span / 2 - 0.01)
    L.cylinder(name + "CurtainRod", 0.005, span, M["buckle"], (fa + fb) / 2 + up * (ch / 2 + 0.006) - n * 0.012, L.basis(up, n, across), segs=10)
    parts = [L.box(name + "Curtain", (span * 0.32, ch, 0.008), M["towel"], left + across * (span * 0.16) - n * 0.012, cb, bevel=0.003)]
    for k in range(3):
        parts.append(L.box(f"{name}Fold{k}", (0.012, ch * 0.98, 0.014), M["towel"], left + across * (0.02 + k * 0.04) - n * 0.008, cb, bevel=0.003))
    A.curtain(name, parts, left, left + across * span * 0.32, left + across * (span - 0.02), act_at=(fa + fb) / 2 - n * 0.04)
    # a velcro strip and a name tag on the header, outside
    P.velcro(name + "Velcro", *at(p1 - (p1 - p0) * 0.2, z1 + 0.12, 0.0), w=0.12, h=0.04)


# ------------------------------------------------------------------ living deck: docking and science forward, berths on the sides, galley aft
def build_living_deck():
    D = DECK_Z
    # docking station: a console band leaning with the cone under the two docking windows, hand controllers, foot loops
    band = C.Band("DockStation", C.rad(-28), C.rad(28), D + 0.5, D + 0.92, 0.06)
    band.build(M["console"])
    G.band_grid(band, "DockStation", 0.0, D + 0.71, 8, 3, 0.14, 0.13, [
        ("mfd", 0, 0, 2, 2, {"screen": "mfd_comms"}), ("navball", 2, 0, 2, 2, {}), ("mfd", 4, 0, 2, 2, {"screen": "mfd_map"}),
        ("annunciators", 6, 0, 2, 1, {"cols": 4, "rows": 2, "start": 8}), ("keypad", 6, 1, 2, 2, {}),
        ("toggles", 0, 2, 3, 1, {"cols": 8}), ("knobs", 3, 2, 1, 1, {"n": 2}), ("breakers", 4, 2, 2, 1, {"cols": 6, "rows": 2})])
    band.check()
    for k, deg in enumerate((-9, 9)):   # translation and rotation hand controllers under the console
        p, b = at(deg, D + 0.42, 0.12)
        S.cbox(f"DockRhcBase{k}", (0.08, 0.06, 0.08), M["frame_dark"], p, b, ch=0.008)
        L.tube(f"DockRhcGrip{k}", [p + b.col[2] * 0.03, p + b.col[2] * 0.09 + b.col[1] * 0.02, p + b.col[2] * 0.12 + b.col[1] * 0.05], 0.018, M["rubber"] if "rubber" in M else M["frame_dark"])
    for k, x in enumerate((-0.22, 0.22)):
        K.foot_loop(f"DockFootLoop{k}", Vector((x, -0.78, D + 0.012)), Vector((0, 0, 1)), Vector((1, 0, 0)))
    w = next(w for w in C.WINDOWS if w["name"] == "DockingR")
    p, b = at(math.degrees(w["phi"]) + 14, w["z"] + 0.02, 0.02)
    P.camera("DockCamera", p, b, lens_dir=(C.polar(w["phi"], C.r_in(w["z"]) + 0.2, w["z"]) - p))
    P.binoculars("Binoculars", *at(-44, D + 0.98, 0.02))
    P.headset("Headset", *at(-40, D + 0.66, 0.02))
    # science: the glovebox forward on the starboard side
    P.glovebox("Glovebox", *at(52, D + 0.36, 0.05), 0.42, 0.3, 0.26)
    S.mount("GloveboxMount", *at(52, D + 0.36, 0.05), 0.42, 0.3)
    # exercise: the ergometer on the deck, front port
    K.ergometer("Ergometer", Vector((-0.78, -0.52, D + 0.015)), L.basis(Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))))
    # crew quarters: five sleep pods, three to starboard and two to port, the crew lockers between them and the galley
    for k, (pa, pb) in enumerate(((70.5, 92.8), (93.8, 116.2), (117.2, 139.5), (-97.8, -75.0), (-121.5, -98.8))):
        sleep_pod(f"Berth{k}", min(pa, pb), max(pa, pb), D + 0.03, D + 0.86)
    P.drawer_stack("CrewLockers", *at(-130, D + 0.3, 0.02), 0.28, 0.42, 4)
    # galley aft-port, pantry aft-starboard, either side of the ladder hole; a fold-out table by the galley
    P.galley("Galley", *at(-151, D + 0.34, 0.05), w=0.36, h=0.46)
    P.oven("Oven", *at(-151, D + 0.78, 0.08))
    P.utensil_rack("Utensils", *at(-138, D + 0.86, 0.0))
    K.rail_table("FoldTable", Vector((-0.36, 0.66, D + 0.01)), L.basis(Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))), w=0.42, l=0.34, stand=0.5)
    P.cabinet("Pantry", *at(151, D + 0.3, 0.035), 0.34, 0.46, 0.3, doors=2)
    P.cabinet("FoodLocker", *at(151, D + 0.78, 0.04), 0.28, 0.2, 0.2, doors=1)
    M["whiteboard_art"] = L.material("IVA_WhiteboardArt", tex="whiteboard.png", rough=0.25, metal=0.0)
    P.whiteboard("Board", *at(140, D + 1.1, 0.02), 0.33, 0.22)
    poster("PosterMun", "mun", *at(104, D + 1.12, 0.0))
    poster("PosterKerbin", "kerbin", *at(-98, D + 1.12, 0.0))
    poster("PosterCrew", "crew", *at(-166, D + 1.02, 0.0), w=0.2, h=0.3)
    poster("PosterBoosters", "boosters", *at(-62, D + 1.12, 0.0), w=0.2, h=0.3)
    poster("PosterMinmus", "minmus", *at(62, D + 1.12, 0.0), w=0.2, h=0.3)
    for k, (deg, z) in enumerate(((-34, D + 0.72), (34, D + 0.72), (64, D + 0.66), (-140, D + 0.9), (162, D + 0.62), (-62, D + 0.6))):
        P.velcro(f"LivingVelcro{k}", *at(deg, z, 0.0))


def ladder(name, x, y, z0, z1, w):
    for side in (-1, 1):
        L.tube(f"{name}Rail{side}", [Vector((x + side * w / 2, y, z0)), Vector((x + side * w / 2, y, z1))], 0.01, M["rib"])
    n = int((z1 - z0) / 0.25)
    for k in range(1, n + 1):
        z = z0 + k * (z1 - z0) / (n + 1)
        L.tube(f"{name}Rung{k}", [Vector((x - w / 2, y, z)), Vector((x + w / 2, y, z))], 0.008, M["yellow"])


# ------------------------------------------------------------------ mission kit: what a crew of five lives and works with
def at(deg, z, inset=0.0):
    return C.frame_at(C.rad(deg), z, inset)


def flat(x, y, z):
    """Frame lying on a floor at (x, y, z): normal up, 'up' towards the cabin front."""
    return Vector((x, y, z)), L.basis(Vector((1, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1)))


def build_lower_kit():
    # stowage under the couches (at the head end, in front of the couch struts)
    for i, seat in enumerate(SEATS):
        P.cargo_bag(f"UnderCouchBag{i}", *flat(seat["x"], -0.48, FLOOR + 0.005), 0.34, 0.2, 0.2)
    # EVA jetpacks racked either side of the hatch
    for side in (-1, 1):
        P.jetpack(f"Jetpack{side}", *at(side * 32, 1.15, 0.015))
    # camera bracketed at each upper side window, checklist binders on the back wall, handrails
    for side, wn in ((1, "SideHighR"), (-1, "SideHighL")):
        w = next(w for w in C.WINDOWS if w["name"] == wn)
        p, b = at(-math.degrees(w["phi"]) * -1 + side * 9, w["z"] + 0.12, 0.02)
        P.camera(f"WindowCamera{side}", p, b, lens_dir=(C.polar(w["phi"], C.r_in(w["z"]) + 0.2, w["z"]) - p))
    # the zero-g indicator, hanging from the console hood where the commander can see it
    P.plush("ZeroGIndicator", Vector((0.22, MDC_Y + MDC_H / 2 + 0.02, MDC_Z - 0.06)), length=0.12)


# ------------------------------------------------------------------ walls: lockers, stowage, safety kit, conduits
def build_walls():
    """(Retired: the front corners now hold the low lockers.)"""
    return
    for side in (-1, 1):
        G.wall(f"WallFront{side}", [("breakers", side * 40, 1.7, 0.24, 0.12, {"cols": 8, "rows": 2}), ("lamps", side * 40, 1.86, 0.16, 0.05, {"n": 3})])
        for k2, z in enumerate((0.5, 0.72)):
            p, b = C.frame_at(C.rad(side * 40), z, 0.01)
            L.box(f"Bag{side}{k2}", (0.26, 0.17, 0.1), M["canvas"], p + b.col[2] * 0.05, b, bevel=0.035, segs=4)
            for sx in (-0.3, 0.3):
                L.box(f"Bag{side}{k2}Strap{sx}", (0.018, 0.18, 0.108), M["strap"], p + b.col[2] * 0.05 + b.col[0] * (0.26 * sx), b, bevel=0.003)
    for k2, (deg, z) in enumerate(((-12, 0.55), (12, 0.55))):
        p, b = C.frame_at(C.rad(deg), z, 0.13)
        rot = L.basis(b.col[1], b.col[2], b.col[0])
        L.cylinder(f"FrontTank_{k2}", 0.09, 0.34, M["tank"], p, rot, segs=28, bevel=0.012)


# ------------------------------------------------------------------ stock-style structure and dressing (built last, fits round everything)
def dome_z(r):
    """Height of the ceiling dome at radius r (inverse of capsule.build_shell's dome)."""
    R = C.r_in(C.Z_CEIL)
    c = max(-1.0, min(1.0, r / R))
    t = math.acos(c) / (math.pi / 2 * 0.92)
    return C.Z_CEIL + (C.Z_TOP - C.Z_CEIL) * math.sin(min(1.0, t) * math.pi / 2)


def build_ceiling_below_deck(clear):
    """Flight-deck ceiling: solid panelled underside of the deck, box beams, ring beam, light fixtures, cable bundles."""
    import bmesh
    D = DECK_Z
    zc = D - 0.035
    rr = C.r_in(zc) - 0.012
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    round_tiles(bm, uv, rr, zc, 0.1, lambda cx, cy: -HOLE_HW < cx < HOLE_HW and HOLE_Y0 < cy < HOLE_Y1, down=True)
    L.mesh_obj("DeckCeiling", bm, [M["blanket"]])
    S.beam("DeckCeilingHoleTrim", Vector((-HOLE_HW, HOLE_Y0, zc - 0.034)), Vector((HOLE_HW, HOLE_Y0, zc - 0.034)), 0.05, 0.06, M["frame_dark"])
    bz = zc - 0.045
    for k2 in range(8):
        phi = 2 * math.pi * (k2 + 0.5) / 8
        S.beam(f"CeilBeam{k2}", C.polar(phi, 0.3, bz), C.polar(phi, rr - 0.02, bz), 0.07, 0.09, M["frame"])
        for t in (0.45, 0.8):
            q = C.polar(phi, 0.3 + (rr - 0.32) * t, bz - 0.0)
            if hidden(q):
                continue
            S.cbox(f"CeilBeamClamp{k2}_{t}", (0.1, 0.1, 0.06), M["frame_dark"], q, Matrix.Rotation(-phi, 3, "Z"), ch=0.01)
    ring = [C.polar(2 * math.pi * j / 72, 0.62, bz) for j in range(72)]
    S.sweep("CeilRingBeam", ring, [(0, 0, 1)] * 72, S.chamfer_rect(0.07, 0.08), M["frame"], closed=True)
    S.sweep("CeilBeamHub", [C.polar(2 * math.pi * j / 48, 0.3, bz) for j in range(48)], [(0, 0, 1)] * 48, S.chamfer_rect(0.08, 0.1), M["frame_dark"], closed=True)
    down = Vector((0, 0, -1))
    n = 0
    for k2 in range(8):
        phi = 2 * math.pi * k2 / 8
        for r in (0.46, 1.12):
            p = C.polar(phi, r, zc - 0.006)
            if -HOLE_HW - 0.2 < p.x < HOLE_HW + 0.2 and HOLE_Y0 - 0.15 < p.y < HOLE_Y1 + 0.15:
                continue
            if abs(p.x) > AISLE - 0.1 and p.y > FACE_Y - 0.1:   # over the aft rooms (the toilet has its own light)
                continue
            tang = Vector((math.cos(phi), math.sin(phi), 0))
            S.light_fixture(f"CeilLight{n}", p, L.basis(tang, tang.cross(down), down), w=0.28 if r > 1 else 0.2, h=0.08)
            n += 1
    # duct round the outer ceiling edge, broken where windows, hatch and equipment are
    for side in (-1, 1):
        phis = [side * math.radians(a) for a in range(30, 150, 3)]
        zd = zc - 0.16

        def ok(phi):
            return not clear.blocked(C.polar(phi, C.r_in(zd) - 0.07, zd), 0.05)

        for r_, seg in enumerate(S.runs(phis, ok, 6)):
            G.hose(f"Duct{side}_{r_}", [C.polar(p, C.r_in(zd) - 0.075, zd) for p in seg], r=0.045, mat=M["frame"], rib_mat=M["frame_dark"])


def build_dome(clear):
    """Living-deck ceiling: docking hatch with handwheel and latches in a segmented ring, equipment cassettes round the
    upper wall, cable drops to the lab tier."""
    zh = dome_z(0.32) - 0.025
    S.sweep("TunnelRing", [Vector((0.33 * math.cos(a), 0.33 * math.sin(a), zh)) for a in [2 * math.pi * j / 64 for j in range(64)]],
            [(0, 0, 1)] * 64, S.chamfer_rect(0.07, 0.06), M["frame_dark"], closed=True)
    L.cylinder("TunnelHatch", 0.29, 0.03, M["frame"], (0, 0, zh + 0.005), segs=48, bevel=0.006)
    L.torus("TunnelHandwheel", 0.11, 0.012, M["frame_dark"], (0, 0, zh - 0.05), Matrix.Identity(3), seg=32, mseg=8)
    for k2 in range(4):
        a = k2 * math.pi / 2
        L.tube(f"TunnelSpoke{k2}", [Vector((0, 0, zh - 0.012)), Vector((0.11 * math.cos(a), 0.11 * math.sin(a), zh - 0.05))], 0.008, M["frame_dark"])
        S.cbox(f"TunnelLatch{k2}", (0.06, 0.03, 0.025), M["yellow"], Vector((0.27 * math.cos(a + 0.4), 0.27 * math.sin(a + 0.4), zh - 0.02)),
               Matrix.Rotation(a + 0.4, 3, "Z"), ch=0.004)
    for k2 in range(16):
        a = 2 * math.pi * (k2 + 0.5) / 16
        r = 0.5
        radial = Vector((math.cos(a), math.sin(a), 0.0))
        slope = Vector((radial.x * 0.02, radial.y * 0.02, dome_z(r + 0.01) - dome_z(r - 0.01))).normalized()   # down the dome, outward
        tang = Vector((-math.sin(a), math.cos(a), 0.0))
        nrm = tang.cross(slope).normalized()
        if nrm.z > 0:
            nrm = -nrm                                   # out of the dome, into the cabin
        S.cbox(f"TunnelSegment{k2}", (0.16, 0.12, 0.022), M["frame"] if k2 % 2 else M["frame_dark"],
               Vector((r * math.cos(a), r * math.sin(a), dome_z(r))) + nrm * 0.02, L.basis(tang, slope, -nrm), ch=0.005)


def build_flight_floor():
    """The floor between the couch heads and the front wall: tie-down tracks, flush stowage lids, strapped bags; and
    handrails under the deck above, for pulling yourself along overhead."""
    for sx in (-1, 1):   # tie-down tracks either side of the route to the EVA hatch
        x = sx * 0.6
        S.cbox(f"FloorTrack{sx}", (0.045, 0.95, 0.012), M["frame_dark"], Vector((x, -1.0, FLOOR + 0.006)), ch=0.002)
        for k in range(8):
            L.cylinder(f"FloorTrackBolt{sx}_{k}", 0.008, 0.006, M["buckle"], Vector((x, -1.42 + k * 0.12, FLOOR + 0.014)), segs=8)
    for k, (x, y) in enumerate(((-0.82, -0.98), (0.0, -1.2), (0.82, -0.98))):   # flush stowage lids with recessed pulls
        S.cbox(f"FloorLid{k}", (0.42, 0.3, 0.008), M["locker"], Vector((x, y, FLOOR + 0.004)), ch=0.002)
        S.cbox(f"FloorLidPull{k}", (0.12, 0.03, 0.006), M["frame_dark"], Vector((x, y - 0.1, FLOOR + 0.0095)), ch=0.002)
        L.box(f"FloorLidTag{k}", (0.08, 0.025, 0.002), M["btn_soft"], Vector((x, y + 0.08, FLOOR + 0.009)))
    up = L.basis(Vector((1, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1)))
    for sx in (-1, 1):   # bags strapped down on the tracks
        P.cargo_bag(f"FloorBag{sx}", Vector((sx * 0.6, -0.75, FLOOR + 0.008)), up, 0.26, 0.2, 0.15)
    zr = DECK_Z - 0.035 - 0.2
    for sx in (-1, 1):   # overhead handrails, fore-aft over the route
        x = sx * 0.47
        L.tube(f"OverheadRail{sx}", [Vector((x, -0.92, DECK_Z - 0.035)), Vector((x, -0.92, zr)), Vector((x, 0.16, zr)), Vector((x, 0.16, DECK_Z - 0.035))],
               0.013, M["yellow"])


def build_floors():
    """Floor dressing: none for now (the aisle between the couch feet and the bulkhead is the floor hatch)."""


def hidden(p):
    """Inside the aft rooms (dressed on their own): build no structure there."""
    return p.y > FACE_Y - 0.02 and abs(p.x) > AISLE - 0.02 and p.z < TOP + 0.04


def build_structure():
    clear = S.Clearance(zones=[hidden])
    build_ceiling_below_deck(clear)
    build_floors()
    clear = S.Clearance(zones=[hidden])
    build_dome(clear)
    clear = S.Clearance(zones=[hidden])
    D = DECK_Z
    bays = [2 * math.pi * k2 / 16 for k2 in range(16)]
    clear = S.Clearance(zones=[hidden])
    S.ring_frame("Skirt", FLOOR + 0.05, clear, h=0.07, d=0.04)
    S.ring_frame("Cornice", D - 0.07, clear, h=0.09, d=0.05)
    S.ring_frame("HabSkirt", D + 0.05, clear, h=0.07, d=0.04)
    S.ring_frame("HabCornice", C.Z_CEIL - 0.05, clear, h=0.08, d=0.05)
    clear = S.Clearance(zones=[hidden])
    S.wall_ribs("Flight", 16, FLOOR + 0.1, D - 0.12, clear, min_len=0.55)
    S.wall_ribs("Hab", 16, D + 0.1, C.Z_CEIL - 0.1, clear, min_len=0.55)
    clear = S.Clearance(zones=[hidden])
    S.wall_plates("Flight", clear, bays, (0.35, 0.7, 1.3, 1.72), chance=0.55, seed=11)
    S.wall_plates("Hab", clear, bays, (D + 0.32, D + 0.8, D + 1.35), chance=0.5, seed=12)


# ------------------------------------------------------------------ build
C.build_shell(dome=True, ring_light=True)
bpy_floor = L.COLL.objects.get("Floor")
if bpy_floor is not None:   # solid deck plates on the flight-deck floor too
    bpy_floor.data.materials[0] = M["deckplate"]
for w in C.WINDOWS:
    C.build_window(w, depth=0.05, bolts=32)
    C.view_markers(w, standoff=0.35)
build_mdc()
build_lower_deck()
build_side_consoles()
C.build_hatch(HATCH_PHI, HATCH_HALF, H["z0"], H["z1"])
build_aft_rooms()
build_front_lockers()
build_decks()
build_living_deck()
build_lower_kit()
build_flight_floor()
build_structure()
import surfaces  # noqa: E402
if not os.environ.get("IVA_NO_DETAIL"):
    surfaces.apply()
for i, seat in enumerate(SEATS):
    C.eye_marker(i, seat)
S.collision_markers(decks=[DECK_Z], holes=[(-HOLE_HW, HOLE_HW, HOLE_Y0, HOLE_Y1, DECK_Z)], boxes=toilet_wall_boxes(),
                    hatches=[("Tunnel", (0.0, 0.0, dome_z(0.32) - 0.25)), ("Aft", (0.0, HATCH_Y, FLOOR + 0.2))],
                    floors=[((0.0, 0.0, FLOOR), (0.0, 0.0, 1.0))])
ref = os.path.join(os.environ.get("IVA_REFERENCE", "C:/Games/KSP2Mods/reference"), "poses", POSE["ref_from"] + ".obj")
C.reference_kerbal_copies(ref, POSE["ref_base_y"], [(s["x"], POSE["ref_offset"][1], POSE["ref_offset"][2]) for s in SEATS])
print(f"eyes at z {EYE_Z:.3f}; console {MDC_Z - EYE_Z:.3f} m above; upper deck at {DECK_Z:.2f}; aft rooms from y {FACE_Y:.2f}")
L.save(OUT)
