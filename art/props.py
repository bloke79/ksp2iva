"""Mission props: the kit a crew lives and works with (sleeping bags, galley, science rack, laptop, cameras, jetpacks,
tool board, cargo bags, binders, fans, a zero-g indicator...). Shared by the interior generators.

Every prop takes p (where it meets the wall or surface) and b (basis: right, up, normal pointing into the cabin), as
capsule.frame_at() returns, and builds outwards along b.col[2].
"""
import math

import ivalib as L  # imports bpy first
import modules as G
from mathutils import Matrix, Vector

M = L.M


def materials():
    M["canvas"] = M.get("canvas") or L.material("IVA_Canvas", (0.55, 0.52, 0.42), rough=0.92)
    M["sleeping"] = L.material("IVA_SleepingBag", (0.16, 0.30, 0.52), rough=0.85)
    M["foil"] = L.material("IVA_Foil", (0.80, 0.80, 0.78), rough=0.25, metal=0.9)
    M["food_red"] = L.material("IVA_FoodRed", (0.62, 0.16, 0.10), rough=0.5)
    M["food_green"] = L.material("IVA_FoodGreen", (0.26, 0.48, 0.20), rough=0.5)
    M["food_yellow"] = L.material("IVA_FoodYellow", (0.80, 0.62, 0.14), rough=0.5)
    M["goo"] = L.material("IVA_Goo", (0.25, 1.0, 0.35), rough=0.2, emit=1.2)
    M["whiteboard"] = L.material("IVA_Whiteboard", (0.90, 0.90, 0.88), rough=0.3)
    M["marker_blue"] = L.material("IVA_MarkerBlue", (0.10, 0.20, 0.70), rough=0.5)
    M["plush"] = L.material("IVA_Plush", (0.40, 0.70, 0.25), rough=0.95)
    M["towel"] = L.material("IVA_Towel", (0.78, 0.74, 0.62), rough=0.98)
    M["bungee"] = L.material("IVA_Bungee", (0.85, 0.35, 0.08), rough=0.8)
    M["jetpack"] = L.material("IVA_Jetpack", (0.82, 0.82, 0.80), rough=0.45, metal=0.2)


def _a(p, b, x, y, z=0.0):
    return p + b.col[0] * x + b.col[1] * y + b.col[2] * z


def _r(b):
    return L.basis(b.col[0], b.col[1], b.col[2])


def straps(name, p, b, w, h, d, n=2, mat=None):
    for i in range(n):
        x = (i - (n - 1) / 2) * w / max(1, n)
        L.box(f"{name}Strap{i}", (0.02, h + 0.012, d + 0.01), mat or M["strap"], _a(p, b, x, 0, d / 2), _r(b), bevel=0.003)


def cargo_bag(name, p, b, w, h, d, mat=None):
    """Soft stowage bag (cargo transfer bag) with a zip flap, handle and label."""
    L.box(name, (w, h, d), mat or M["canvas"], _a(p, b, 0, 0, d / 2), _r(b), bevel=min(w, h, d) * 0.3, segs=4)
    L.box(name + "Zip", (w * 0.85, 0.008, 0.006), M["handle"], _a(p, b, 0, h * 0.32, d + 0.001), _r(b))
    L.box(name + "Label", (min(0.08, w * 0.4), min(0.04, h * 0.3), 0.003), M["btn_soft"], _a(p, b, 0, -h * 0.1, d + 0.002), _r(b))
    L.tube(name + "Handle", [_a(p, b, -w * 0.18, h / 2 - 0.01, d * 0.6), _a(p, b, -w * 0.18, h / 2 + 0.02, d * 0.6),
                            _a(p, b, w * 0.18, h / 2 + 0.02, d * 0.6), _a(p, b, w * 0.18, h / 2 - 0.01, d * 0.6)], 0.006, M["strap"])


def sleeping_bag(name, p, b, w=0.42, h=0.78, d=0.13):
    """Sleeping restraint strapped to the wall: padded bag, pillow, zip, arm slots, wall straps."""
    L.box(name, (w, h, d), M["sleeping"], _a(p, b, 0, -0.03, d / 2), _r(b), bevel=0.05, segs=4)
    L.box(name + "Pillow", (w * 0.7, 0.13, d * 0.9), M["towel"], _a(p, b, 0, h / 2 - 0.02, d * 0.5), _r(b), bevel=0.04, segs=4)
    L.box(name + "Zip", (0.008, h * 0.75, 0.006), M["toggle"], _a(p, b, w * 0.22, -0.06, d + 0.001), _r(b))
    for y in (-h * 0.25, h * 0.15):
        L.box(f"{name}Band{y:.2f}", (w + 0.02, 0.03, d + 0.012), M["strap"], _a(p, b, 0, y, d / 2), _r(b), bevel=0.004)
    for sx in (-1, 1):
        L.box(f"{name}ArmSlot{sx}", (0.012, 0.12, 0.004), M["handle"], _a(p, b, sx * w * 0.42, h * 0.18, d + 0.001), _r(b))


def galley(name, p, b, w=0.38, h=0.5):
    """Food station: water dispenser with hot/cold buttons and a nozzle, food warmer drawer, and a net of food packs."""
    G.plate(name + "Back", p, b, w, h, 0.012, screws=True, frame=False)
    q = _a(p, b, -w * 0.22, h * 0.18, 0.012)
    L.box(name + "Dispenser", (0.12, 0.16, 0.08), M["locker"], q + b.col[2] * 0.04, _r(b), bevel=0.008)
    L.tube(name + "Nozzle", [q + b.col[2] * 0.08 - b.col[1] * 0.04, q + b.col[2] * 0.12 - b.col[1] * 0.06, q + b.col[2] * 0.12 - b.col[1] * 0.1], 0.006, M["buckle"])
    for i, mat in enumerate((M["btn_red"], M["btn_blue"])):
        L.cylinder(f"{name}Btn{i}", 0.01, 0.01, mat, q + b.col[2] * 0.085 + b.col[0] * (-0.025 + 0.05 * i) + b.col[1] * 0.04, _r(b), segs=16)
    q = _a(p, b, w * 0.2, h * 0.18, 0.012)
    L.box(name + "Warmer", (0.14, 0.12, 0.09), M["module"], q + b.col[2] * 0.045, _r(b), bevel=0.006)
    L.box(name + "WarmerDoor", (0.12, 0.08, 0.004), M["ring"], q + b.col[2] * 0.091, _r(b))
    L.box(name + "WarmerHandle", (0.08, 0.012, 0.012), M["toggle"], q + b.col[2] * 0.097 + b.col[1] * 0.025, _r(b), bevel=0.003)
    G.lamps(name + "Lamps", q + b.col[1] * 0.075, b, 0.08, 0.025, 2)
    # food packs in a net below
    mats = (M["food_red"], M["food_green"], M["food_yellow"], M["foil"])
    for i in range(10):
        r_, c = divmod(i, 5)
        q = _a(p, b, -w * 0.38 + c * w * 0.19, -h * 0.18 - r_ * 0.09, 0.012)
        rot = _r(b) @ Matrix.Rotation(math.radians((i * 37) % 21 - 10), 3, "Z")
        L.box(f"{name}Food{i}", (0.07, 0.085, 0.02), mats[(i * 3) % 4], q + b.col[2] * (0.012 + (i % 3) * 0.006), rot, bevel=0.006)
    for k in range(6):
        y = -h * 0.08 - k * 0.04
        L.tube(f"{name}NetH{k}", [_a(p, b, -w * 0.46, y, 0.045), _a(p, b, w * 0.46, y, 0.045)], 0.0025, M["net"] if "net" in M else M["strap"])
    for k in range(9):
        x = -w * 0.44 + k * w * 0.11
        L.tube(f"{name}NetV{k}", [_a(p, b, x, -h * 0.06, 0.045), _a(p, b, x, -h * 0.48, 0.045)], 0.0025, M["net"] if "net" in M else M["strap"])


def science_rack(name, p, b, w=0.36, h=0.62):
    """Experiment rack: two goo canisters with glowing windows, a sample drawer stack, and an instrument panel."""
    G.plate(name + "Back", p, b, w, h, 0.014, frame=False)
    for i, x in enumerate((-w * 0.25, w * 0.25)):
        q = _a(p, b, x, h * 0.22, 0.014)
        rot = _r(b)
        L.cylinder(f"{name}Goo{i}", 0.055, 0.18, M["foil"], q + b.col[2] * 0.065, rot @ Matrix.Rotation(math.pi / 2, 3, "X"), segs=24, bevel=0.01)
        L.cylinder(f"{name}GooWindow{i}", 0.057, 0.05, M["goo"], q + b.col[2] * 0.065, rot @ Matrix.Rotation(math.pi / 2, 3, "X"), segs=24)
        for dy in (-0.07, 0.07):
            L.torus(f"{name}GooBand{i}{dy}", 0.058, 0.006, M["ring"], q + b.col[2] * 0.065 + b.col[1] * dy, rot @ Matrix.Rotation(math.pi / 2, 3, "X"), seg=24, mseg=6)
    for k in range(3):
        q = _a(p, b, 0, -h * 0.05 - k * 0.075, 0.014)
        L.box(f"{name}Drawer{k}", (w * 0.85, 0.065, 0.06), M["locker"], q + b.col[2] * 0.03, _r(b), bevel=0.004)
        L.box(f"{name}DrawerHandle{k}", (0.07, 0.01, 0.012), M["handle"], q + b.col[2] * 0.064, _r(b), bevel=0.003)
        L.box(f"{name}DrawerTag{k}", (0.05, 0.02, 0.002), M["btn_soft"], q + b.col[2] * 0.061 + b.col[0] * (-w * 0.28), _r(b))
    G.annunciators(name + "Status", _a(p, b, 0, -h * 0.4, 0.014), b, w * 0.8, 0.06, 4, 1, start=12)


def laptop(name, p, b, arm=0.25, screen="mfd_map"):
    """Laptop on a swing arm from the wall, lid open towards the cabin."""
    base = _a(p, b, 0, 0, 0)
    elbow = base + b.col[2] * arm * 0.6 + b.col[1] * 0.05
    tray = base + b.col[2] * arm - b.col[1] * 0.02
    L.cylinder(name + "Mount", 0.025, 0.02, M["couchframe"], base + b.col[2] * 0.01, _r(b), segs=16)
    L.tube(name + "Arm", [base + b.col[2] * 0.02, elbow, tray], 0.012, M["couchframe"])
    up = b.col[1]
    flat = L.basis(b.col[0], b.col[2], -up)        # keyboard lies flat
    L.box(name + "Base", (0.3, 0.21, 0.02), M["module"], tray, flat, bevel=0.005)
    L.box(name + "Keys", (0.26, 0.11, 0.004), M["bezel"], tray + up * 0.011 - b.col[2] * 0.02, flat)
    lid_n = (b.col[2] * 0.35 + up * 0.0 - b.col[2] * 1.0).normalized()
    lid_rot = L.basis(b.col[0], (up * 0.94 - b.col[2] * 0.34).normalized(), (b.col[2] * 0.94 + up * 0.34).normalized())
    lid_c = tray - b.col[2] * 0.105 + up * 0.1
    L.box(name + "Lid", (0.3, 0.2, 0.012), M["module"], lid_c, lid_rot, bevel=0.004)
    L.plane(name + "Screen", 0.26, 0.17, M[screen], lid_c + lid_rot.col[2] * 0.0065, lid_rot)


def camera(name, p, b, lens_dir=None):
    """Hand camera on a bracket (Hasselblad-style body, lens, film magazine)."""
    d = (lens_dir or -b.col[2]).normalized()
    rot = d.to_track_quat("Z", "Y").to_matrix()
    L.tube(name + "Bracket", [p, p + b.col[2] * 0.06, p + b.col[2] * 0.06 + b.col[1] * 0.05], 0.008, M["couchframe"])
    c = p + b.col[2] * 0.06 + b.col[1] * 0.1
    L.box(name + "Body", (0.09, 0.09, 0.09), M["toggle"], c, rot, bevel=0.008)
    L.cylinder(name + "Lens", 0.03, 0.08, M["bezel"], c + d * 0.08, rot, segs=24, bevel=0.004)
    L.box(name + "Magazine", (0.09, 0.08, 0.04), M["module"], c - d * 0.065, rot, bevel=0.005)


def jetpack(name, p, b):
    """EVA jetpack stowed on a wall mount: backpack shell, twin tanks, thruster quads, straps."""
    L.box(name + "Mount", (0.32, 0.4, 0.02), M["couchframe"], _a(p, b, 0, 0, 0.01), _r(b), bevel=0.004)
    L.box(name, (0.3, 0.38, 0.12), M["jetpack"], _a(p, b, 0, 0, 0.08), _r(b), bevel=0.03, segs=3)
    for sx in (-1, 1):
        L.cylinder(f"{name}Tank{sx}", 0.04, 0.32, M["tank"], _a(p, b, sx * 0.08, 0, 0.16), _r(b) @ Matrix.Rotation(math.pi / 2, 3, "X"), segs=20, bevel=0.012)
        for sy in (-1, 1):
            q = _a(p, b, sx * 0.17, sy * 0.17, 0.08)
            L.box(f"{name}Quad{sx}{sy}", (0.04, 0.04, 0.04), M["ring"], q, _r(b), bevel=0.005)
            L.cylinder(f"{name}Nozzle{sx}{sy}", 0.008, 0.02, M["bezel"], q + b.col[0] * sx * 0.03, L.basis(b.col[1], b.col[2], b.col[0]), segs=10)
    straps(name, p, b, 0.3, 0.4, 0.14, n=2, mat=M["strap"])


def tool_board(name, p, b, w=0.4, h=0.34):
    """Pegboard of tools: wrenches, screwdrivers, a hammer, pliers, tape."""
    G.plate(name + "Board", p, b, w, h, 0.01, frame=False)
    rng = [(-0.14, 0.08, 0.02, 0.16, M["toggle"]), (-0.09, 0.08, 0.016, 0.13, M["toggle"]), (-0.05, 0.08, 0.012, 0.1, M["toggle"]),
           (0.03, 0.09, 0.012, 0.14, M["red"]), (0.07, 0.09, 0.012, 0.14, M["yellow"]), (0.11, 0.09, 0.012, 0.14, M["btn_blue"]),
           (-0.12, -0.08, 0.05, 0.03, M["couchframe"]), (-0.12, -0.04, 0.012, 0.1, M["handle"])]
    for i, (x, y, tw, th, mat) in enumerate(rng):
        L.box(f"{name}Tool{i}", (tw, th, 0.012), mat, _a(p, b, x, y, 0.016), _r(b), bevel=0.003)
    L.torus(name + "Tape", 0.03, 0.012, M["toggle"], _a(p, b, 0.08, -0.08, 0.02), _r(b), seg=24, mseg=8)
    L.box(name + "Pliers", (0.02, 0.12, 0.012), M["red"], _a(p, b, -0.02, -0.07, 0.016), _r(b) @ Matrix.Rotation(0.3, 3, "Z"), bevel=0.003)


def whiteboard(name, p, b, w=0.36, h=0.26):
    """Flight-plan whiteboard with marker lines and a marker on a cord."""
    L.box(name, (w, h, 0.012), M["whiteboard"], _a(p, b, 0, 0, 0.006), _r(b), bevel=0.003)
    L.box(name + "Frame", (w + 0.02, h + 0.02, 0.008), M["couchframe"], _a(p, b, 0, 0, 0.002), _r(b), bevel=0.003)
    for k in range(5):
        L.box(f"{name}Line{k}", (w * (0.4 + 0.1 * (k % 3)), 0.006, 0.002), M["marker_blue"] if k % 2 == 0 else M["red"],
              _a(p, b, -w * 0.08, h * 0.3 - k * 0.045, 0.013), _r(b))
    L.cylinder(name + "Marker", 0.006, 0.08, M["marker_blue"], _a(p, b, w / 2 - 0.03, -h / 2 - 0.03, 0.02), L.basis(b.col[1], b.col[2], b.col[0]), segs=10)


def fan(name, p, b, r=0.07):
    """Cabin fan in a round grille."""
    L.cylinder(name + "Housing", r * 1.1, 0.05, M["locker"], _a(p, b, 0, 0, 0.025), _r(b), segs=28, bevel=0.006)
    L.disc(name + "Back", r, M["bezel"], _a(p, b, 0, 0, 0.03), _r(b), segs=28)
    for k in range(5):
        a = k * 2 * math.pi / 5
        L.box(f"{name}Blade{k}", (r * 0.8, 0.02, 0.004), M["ring"], _a(p, b, math.cos(a) * r * 0.45, math.sin(a) * r * 0.45, 0.035),
              _r(b) @ Matrix.Rotation(a, 3, "Z") @ Matrix.Rotation(0.4, 3, "X"))
    for k in range(4):
        L.torus(f"{name}Grille{k}", r * (0.3 + 0.22 * k), 0.003, M["rib"], _a(p, b, 0, 0, 0.052), _r(b), seg=28, mseg=4)


def binders(name, p, b, n=5):
    """Checklist binders standing in a wall holder."""
    L.box(name + "Holder", (0.05 * n + 0.03, 0.04, 0.2), M["couchframe"], _a(p, b, 0, -0.13, 0.1), _r(b), bevel=0.004)
    mats = (M["red"], M["btn_blue"], M["yellow"], M["btn_soft"], M["food_green"])
    for i in range(n):
        x = (i - (n - 1) / 2) * 0.05
        L.box(f"{name}{i}", (0.04, 0.26, 0.19), mats[i % len(mats)], _a(p, b, x, 0.0, 0.1), _r(b) @ Matrix.Rotation(math.radians((i % 3 - 1) * 3), 3, "Y"), bevel=0.004)


def plush(name, top, length=0.16):
    """Zero-g indicator: a little green plush kerbal on a string."""
    bottom = top - Vector((0, 0, length))
    L.tube(name + "String", [top, bottom], 0.0015, M["handle"])
    L.sphere(name + "Body", 0.025, M["plush"], bottom - Vector((0, 0, 0.03)), u=16, v=8)
    L.sphere(name + "Head", 0.03, M["plush"], bottom - Vector((0, 0, 0.0)), u=16, v=8)
    for sx in (-1, 1):
        L.sphere(f"{name}Eye{sx}", 0.006, M["btn_soft"], bottom + Vector((sx * 0.01, -0.027, 0.005)), u=8, v=4)


def towels(name, p, b):
    """Hygiene kit: towels on a rail, water and wipe bags."""
    L.tube(name + "Rail", [_a(p, b, -0.15, 0.1, 0), _a(p, b, -0.15, 0.1, 0.05), _a(p, b, 0.15, 0.1, 0.05), _a(p, b, 0.15, 0.1, 0)], 0.007, M["buckle"])
    for i, x in enumerate((-0.08, 0.06)):
        L.box(f"{name}Towel{i}", (0.11, 0.24, 0.016), M["towel"], _a(p, b, x, -0.01, 0.05), _r(b), bevel=0.006)
    for i, x in enumerate((-0.09, 0.0, 0.09)):
        L.box(f"{name}Bag{i}", (0.07, 0.1, 0.03), M["foil"], _a(p, b, x, -0.2, 0.02), _r(b), bevel=0.012)


def bungee(name, p, b):
    """Exercise device: bar on two bungee cords anchored to a wall plate."""
    L.box(name + "Plate", (0.2, 0.06, 0.02), M["couchframe"], _a(p, b, 0, -0.3, 0.01), _r(b), bevel=0.004)
    for sx in (-1, 1):
        L.tube(f"{name}Cord{sx}", [_a(p, b, sx * 0.07, -0.3, 0.02), _a(p, b, sx * 0.16, 0.05, 0.06), _a(p, b, sx * 0.17, 0.25, 0.05)], 0.006, M["bungee"])
    L.cylinder(name + "Bar", 0.014, 0.4, M["handle"], _a(p, b, 0, 0.26, 0.05), L.basis(b.col[1], b.col[2], b.col[0]), segs=12, bevel=0.003)


def binoculars(name, p, b):
    for sx in (-1, 1):
        L.cylinder(f"{name}Barrel{sx}", 0.022, 0.12, M["bezel"], _a(p, b, sx * 0.027, 0, 0.04), L.basis(b.col[0], b.col[2], -b.col[1]), segs=16, bevel=0.003)
    L.box(name + "Bridge", (0.05, 0.03, 0.02), M["module"], _a(p, b, 0, 0, 0.04), _r(b))
    L.tube(name + "Strap", [_a(p, b, -0.05, 0.05, 0.04), _a(p, b, 0, 0.12, 0.01), _a(p, b, 0.05, 0.05, 0.04)], 0.004, M["strap"])


def headset(name, p, b):
    """Comms headset hanging on a hook, with a coiled cord."""
    L.tube(name + "Hook", [p, _a(p, b, 0, 0, 0.05), _a(p, b, 0, 0.02, 0.05)], 0.005, M["buckle"])
    c = _a(p, b, 0, -0.06, 0.05)
    L.torus(name + "Band", 0.06, 0.007, M["handle"], c, L.basis(b.col[0], b.col[2], b.col[1]) @ Matrix.Rotation(0.0, 3, "Z"), seg=24, mseg=6)
    for sx in (-1, 1):
        L.cylinder(f"{name}Cup{sx}", 0.03, 0.025, M["module"], c + b.col[0] * sx * 0.06 - b.col[1] * 0.02, L.basis(b.col[1], b.col[2], b.col[0]), segs=20, bevel=0.006)
    L.tube(name + "Cord", [c - b.col[1] * 0.04 + b.col[0] * 0.06 + b.col[2] * 0.0 * k for k in range(1)] + [_a(p, b, 0.08, -0.25, 0.03), _a(p, b, 0.02, -0.4, 0.01)], 0.004, M["handle"])
