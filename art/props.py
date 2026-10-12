"""Mission props: the kit a crew lives and works with (sleeping bags, galley, science rack, laptop, cameras, jetpacks,
tool board, cargo bags, binders, fans, a zero-g indicator...). Shared by the interior generators.

Every prop takes p (where it meets the wall or surface) and b (basis: right, up, normal pointing into the cabin), as
capsule.frame_at() returns, and builds outwards along b.col[2].
"""
import math

import ivalib as L  # imports bpy first
import act as A
import modules as G
from mathutils import Matrix, Vector

M = L.M


def materials():
    M["canvas"] = M.get("canvas") or L.material("IVA_Canvas", (0.27, 0.28, 0.23), rough=0.92, normal="canvas_normal.png", uv_scale=(6.0, 6.0), normal_strength=0.8)
    M["sleeping"] = L.material("IVA_SleepingBag", (0.11, 0.19, 0.33), rough=0.88, normal="canvas_normal.png", uv_scale=(6.0, 6.0), normal_strength=0.8)
    M["foil"] = L.material("IVA_Foil", (0.80, 0.80, 0.78), rough=0.25, metal=0.9)
    M["food_red"] = L.material("IVA_FoodRed", (0.62, 0.16, 0.10), rough=0.5)
    M["food_green"] = L.material("IVA_FoodGreen", (0.26, 0.48, 0.20), rough=0.5)
    M["food_yellow"] = L.material("IVA_FoodYellow", (0.80, 0.62, 0.14), rough=0.5)
    M["goo"] = L.material("IVA_Goo", (0.25, 1.0, 0.35), rough=0.2, emit=1.2)
    M["whiteboard"] = L.material("IVA_Whiteboard", (0.90, 0.90, 0.88), rough=0.3)
    M["marker_blue"] = L.material("IVA_MarkerBlue", (0.10, 0.20, 0.70), rough=0.5)
    M["plush"] = L.material("IVA_Plush", (0.40, 0.70, 0.25), rough=0.95)
    M["towel"] = L.material("IVA_Towel", (0.62, 0.59, 0.50), rough=0.98, normal="canvas_normal.png", uv_scale=(9.0, 9.0), normal_strength=1.0)
    M["bungee"] = L.material("IVA_Bungee", (0.85, 0.35, 0.08), rough=0.8)
    M["food_tex"] = L.material("IVA_Food", tex="food.png", rough=0.45)
    M["food_label"] = L.material("IVA_FoodLabels", tex="food_labels.png", rough=0.6)
    M["glass_dark"] = L.material("IVA_DarkGlass", (0.03, 0.04, 0.05), rough=0.06)
    M["jetpack"] = L.material("IVA_Jetpack", (0.82, 0.82, 0.80), rough=0.45, metal=0.2)


def _a(p, b, x, y, z=0.0):
    return p + b.col[0] * x + b.col[1] * y + b.col[2] * z


def _r(b):
    return L.basis(b.col[0], b.col[1], b.col[2])


def velcro(name, p, b, w=0.14, h=0.05):
    """A strip of blue velcro on a surface (p, b: point and basis with the normal out of the surface), for sticking
    down checklists, pens and kit in zero g. Put them where the crew work."""
    mat = M.get("velcro") or L.material("IVA_Velcro", (0.38, 0.55, 0.78), rough=1.0)
    M["velcro"] = mat
    return L.box(name, (w, h, 0.003), mat, p + b.col[2] * 0.0015, _r(b))


def straps(name, p, b, w, h, d, n=2, mat=None):
    for i in range(n):
        x = (i - (n - 1) / 2) * w / max(1, n)
        L.box(f"{name}Strap{i}", (0.02, h + 0.012, d + 0.01), mat or M["strap"], _a(p, b, x, 0, d / 2), _r(b), bevel=0.003)


def cargo_bag(name, p, b, w, h, d, mat=None):
    """Soft stowage bag (cargo transfer bag) with a zip flap, handle and label."""
    L.box(name, (w, h, d), mat or M["canvas"], _a(p, b, 0, 0, d / 2), _r(b), bevel=min(w, h, d) * 0.16, segs=3)
    L.box(name + "Zip", (w * 0.85, 0.005, 0.003), M["handle"], _a(p, b, 0, h * 0.32, d + 0.0005), _r(b))
    L.box(name + "Label", (min(0.07, w * 0.35), min(0.035, h * 0.25), 0.002), M["btn_soft"], _a(p, b, -w * 0.2, -h * 0.12, d + 0.001), _r(b))
    for sx in (-0.28, 0.28):   # webbing straps, just proud of the fabric
        L.box(f"{name}Web{sx}", (0.014, h + 0.004, d + 0.004), M["strap"], _a(p, b, w * sx, 0, d / 2), _r(b), bevel=0.001)
    L.tube(name + "Handle", [_a(p, b, -w * 0.15, h / 2 - 0.005, d * 0.6), _a(p, b, -w * 0.15, h / 2 + 0.012, d * 0.6),
                            _a(p, b, w * 0.15, h / 2 + 0.012, d * 0.6), _a(p, b, w * 0.15, h / 2 - 0.005, d * 0.6)], 0.004, M["strap"])


def sleeping_bag(name, p, b, w=0.42, h=0.78, d=0.13):
    """Sleeping restraint strapped to the wall: padded bag, pillow, zip, arm slots, wall straps."""
    L.box(name, (w, h, d), M["sleeping"], _a(p, b, 0, -0.03, d / 2), _r(b), bevel=0.035, segs=3)
    L.box(name + "Pillow", (w * 0.7, 0.13, d * 0.9), M["towel"], _a(p, b, 0, h / 2 - 0.02, d * 0.5), _r(b), bevel=0.04, segs=4)
    L.box(name + "Zip", (0.008, h * 0.75, 0.006), M["toggle"], _a(p, b, w * 0.22, -0.06, d + 0.001), _r(b))
    for y in (-h * 0.25, h * 0.15):
        L.box(f"{name}Band{y:.2f}", (w + 0.006, 0.018, d + 0.004), M["strap"], _a(p, b, 0, y, d / 2), _r(b), bevel=0.001)
        for sx in (-1, 1):
            L.box(f"{name}Buckle{y:.2f}{sx}", (0.022, 0.026, 0.006), M["buckle"], _a(p, b, sx * w * 0.3, y, d + 0.003), _r(b), bevel=0.001)
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
    tray = _a(p, b, 0, -0.02, arm)
    # the arm runs under the keyboard tray from a mount low on the wall, so it never crosses the screen
    base = _a(p, b, 0, -0.17, 0)
    under = tray - b.col[1] * 0.025
    elbow = base + b.col[2] * arm * 0.55 - b.col[1] * 0.02
    L.cylinder(name + "Mount", 0.025, 0.02, M["couchframe"], base + b.col[2] * 0.01, _r(b), segs=16)
    L.tube(name + "Arm", [base + b.col[2] * 0.02, elbow, under], 0.012, M["couchframe"])
    L.cylinder(name + "Pivot", 0.02, 0.02, M["couchframe"], under + b.col[1] * 0.005, L.basis(b.col[0], b.col[2], -b.col[1]), segs=16)
    up = b.col[1]
    flat = L.basis(b.col[0], b.col[2], -up)        # keyboard lies flat
    L.box(name + "Base", (0.3, 0.21, 0.02), M["module"], tray, flat, bevel=0.005)
    L.box(name + "Keys", (0.26, 0.11, 0.004), M["bezel"], tray + up * 0.011 - b.col[2] * 0.02, flat)
    lid_n = (b.col[2] * 0.35 + up * 0.0 - b.col[2] * 1.0).normalized()
    lid_rot = L.basis(b.col[0], (up * 0.94 - b.col[2] * 0.34).normalized(), (b.col[2] * 0.94 + up * 0.34).normalized())
    lid_c = tray - b.col[2] * 0.105 + up * 0.1
    L.box(name + "Lid", (0.3, 0.2, 0.012), M["module"], lid_c, lid_rot, bevel=0.004)
    A.screen(name, L.plane(name + "Screen", 0.26, 0.17, M[screen], lid_c + lid_rot.col[2] * 0.0065, lid_rot))


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
    if "whiteboard_art" in M:   # the crew's scribbles (posters.py whiteboard)
        L.plane(name + "Art", w - 0.01, h - 0.01, M["whiteboard_art"], _a(p, b, 0, 0, 0.0125), _r(b))
        L.cylinder(name + "Marker", 0.006, 0.08, M["marker_blue"], _a(p, b, w / 2 - 0.03, -h / 2 - 0.03, 0.02), L.basis(b.col[1], b.col[2], b.col[0]), segs=10)
        return
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
    """Exercise device stowed on the wall: a bar held in two clips, its bungee cords running flat down to an anchor plate."""
    L.box(name + "Plate", (0.2, 0.06, 0.02), M["couchframe"], _a(p, b, 0, -0.3, 0.01), _r(b), bevel=0.004)
    for sx in (-1, 1):
        L.tube(f"{name}Cord{sx}", [_a(p, b, sx * 0.07, -0.29, 0.022), _a(p, b, sx * 0.1, 0.0, 0.026), _a(p, b, sx * 0.12, 0.25, 0.03)], 0.006, M["bungee"])
        L.box(f"{name}Clip{sx}", (0.03, 0.04, 0.04), M["couchframe"], _a(p, b, sx * 0.15, 0.26, 0.02), _r(b), bevel=0.004)
    L.cylinder(name + "Bar", 0.014, 0.4, M["handle"], _a(p, b, 0, 0.26, 0.032), L.basis(b.col[1], b.col[2], b.col[0]), segs=12, bevel=0.003)


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


def hazard_rail(name, pts, r=0.009):
    """Handrail with yellow/black hazard stripes (every ~6 cm)."""
    pts = [Vector(q) for q in pts]
    seg = []
    for a, c in zip(pts, pts[1:]):
        n = max(1, int((c - a).length / 0.06))
        seg += [(a + (c - a) * (k / n), a + (c - a) * ((k + 1) / n)) for k in range(n)]
    for k, (a, c) in enumerate(seg):
        L.tube(f"{name}_{k}", [a, c], r, M["yellow"] if k % 2 == 0 else M["handle"], bevel_res=1)




# ------------------------------------------------------------------ hollow units (so opening a door or drawer shows an inside)
def _shell(name, p, b, w, h, d, mat, x0=0.0, y0=0.0, t=0.01, inner=None):
    """Open-fronted box: back, sides, top and bottom, w x h x d, centred at (x0, y0) on the surface; returns the parts."""
    inner = inner or mat
    zd = (d + t) / 2   # centre of the walls in front of the back
    return [L.box(name + "Back", (w, h, t), inner, _a(p, b, x0, y0, t / 2), _r(b)),
            L.box(name + "SideL", (t, h, d - t), mat, _a(p, b, x0 - w / 2 + t / 2, y0, zd), _r(b)),
            L.box(name + "SideR", (t, h, d - t), mat, _a(p, b, x0 + w / 2 - t / 2, y0, zd), _r(b)),
            L.box(name + "Top", (w - 2 * t, t, d - t), mat, _a(p, b, x0, y0 + h / 2 - t / 2, zd), _r(b)),
            L.box(name + "Bottom", (w - 2 * t, t, d - t), mat, _a(p, b, x0, y0 - h / 2 + t / 2, zd), _r(b))]


def _stowed(name, p, b, w, d, y, seed, h_max=0.12):
    """A row of stowed items standing on a shelf at height y (local), across w and within depth d: food packs, cans,
    pouches, a kit box. Returns the objects (so drawers can carry them)."""
    import random
    rnd = random.Random(seed)
    out = []
    x = -w / 2 + 0.015
    vert = L.basis(b.col[0], b.col[2], -b.col[1]) @ Matrix.Rotation(math.pi / 2, 3, "X")
    k = 0
    while True:
        kind = rnd.choice(("pack", "pack", "can", "pouch", "kit"))
        iw = {"pack": 0.05, "can": 0.045, "pouch": 0.06, "kit": 0.08}[kind] * rnd.uniform(0.85, 1.15)
        if x + iw > w / 2 - 0.015:
            break
        ih = min(h_max, {"pack": 0.09, "can": 0.08, "pouch": 0.07, "kit": 0.06}[kind] * rnd.uniform(0.8, 1.2))
        idp = min(d - 0.03, rnd.uniform(0.06, 0.12))
        cx, cz = x + iw / 2, 0.02 + idp / 2 + rnd.uniform(0, max(0.0, d - 0.05 - idp))
        if kind == "can":
            out.append(L.cylinder(f"{name}Can{k}", iw / 2, ih, rnd.choice((M["foil"], M["tank"] if "tank" in M else M["foil"])),
                                  _a(p, b, cx, y + ih / 2, cz), vert, segs=12))
        else:
            mat = {"pack": rnd.choice((M["food_red"], M["food_green"], M["food_yellow"], M["btn_soft"])),
                   "pouch": M["foil"], "kit": M["locker"]}[kind]
            out.append(L.box(f"{name}{kind.title()}{k}", (iw, ih, idp), mat, _a(p, b, cx, y + ih / 2, cz), _r(b), bevel=0.004, segs=1))
        x += iw + rnd.uniform(0.004, 0.015)
        k += 1
    return out

def drawer_stack(name, p, b, w=0.3, h=0.4, n=4, live=True):
    """Stack of labelled stowage drawers in a frame."""
    d = 0.22
    dh = h / n
    if not live:
        L.box(name + "Frame", (w + 0.02, h + 0.02, d), M["module"], _a(p, b, 0, 0, d / 2), _r(b), bevel=0.003)
    else:
        _shell(name + "Frame", p, b, w + 0.02, h + 0.02, d, M["module"], inner=M.get("frame_dark", M["module"]))
        for k in range(1, n):
            L.box(f"{name}Runner{k}", (w, 0.006, d - 0.01), M["module"], _a(p, b, 0, h / 2 - dh * k, d / 2), _r(b))
    for k in range(n):
        y = h / 2 - dh * (k + 0.5)
        parts = [L.box(f"{name}Drawer{k}", (w - 0.01, dh - 0.008, 0.012), M["locker"], _a(p, b, 0, y, d + 0.006), _r(b), bevel=0.002),
                 L.box(f"{name}Pull{k}", (0.06, 0.01, 0.014), M["handle"], _a(p, b, 0, y + dh * 0.15, d + 0.018), _r(b), bevel=0.002),
                 L.box(f"{name}Tag{k}", (0.05, 0.018, 0.002), M["btn_soft"], _a(p, b, -w * 0.3, y, d + 0.013), _r(b))]
        if live:
            # the tray behind the front: sides, back and bottom, with things stowed in it
            tw, th, td = w - 0.03, dh - 0.03, d - 0.04
            ty = y - (dh - 0.008) / 2 + 0.006
            for sx in (-1, 1):
                parts.append(L.box(f"{name}Tray{k}Side{sx}", (0.006, th, td), M["locker"], _a(p, b, sx * (tw / 2 - 0.003), ty + th / 2, d - td / 2), _r(b)))
            parts.append(L.box(f"{name}Tray{k}Back", (tw, th, 0.006), M["locker"], _a(p, b, 0, ty + th / 2, d - td + 0.003), _r(b)))
            parts.append(L.box(f"{name}Tray{k}Bottom", (tw, 0.006, td), M["locker"], _a(p, b, 0, ty, d - td / 2), _r(b)))
            for o in _stowed(f"{name}Tray{k}", _a(p, b, 0, 0, d - td), b, tw - 0.02, td, ty + 0.003, seed=hash(name) % 997 + k, h_max=th - 0.01):
                parts.append(o)
        if live:
            A.slide(f"{name}_{k}", parts, b.col[2] * min(0.16, d * 0.7), act_at=_a(p, b, 0, y, d + 0.02))


def gear_rack(name, p, b, w=0.32, h=0.42):
    """Open rack: shelves with stowed gear (canisters, a soft case, cable coils, a kit box)."""
    d = 0.2
    for k, y in enumerate((-h / 2, 0.0, h / 2)):
        L.box(f"{name}Shelf{k}", (w, 0.012, d), M["module"], _a(p, b, 0, y, d / 2), _r(b), bevel=0.002)
    for sx in (-1, 1):
        L.box(f"{name}Side{sx}", (0.012, h, d), M["module"], _a(p, b, sx * w / 2, 0, d / 2), _r(b), bevel=0.002)
    vert = L.basis(b.col[0], b.col[2], -b.col[1]) @ Matrix.Rotation(math.pi / 2, 3, "X")
    for k, x in enumerate((-0.11, -0.05, 0.01)):
        L.cylinder(f"{name}Can{k}", 0.025, 0.12, M["foil"] if k % 2 else M["tank"], _a(p, b, x, -h / 4 + 0.006, d * 0.5), vert, segs=16, bevel=0.004)
    L.box(name + "Case", (0.09, 0.1, 0.14), M["canvas"], _a(p, b, 0.1, -h / 4 + 0.006, d * 0.5), _r(b), bevel=0.015)
    for k in range(2):
        L.torus(f"{name}Coil{k}", 0.045, 0.008, M["cable"], _a(p, b, -0.08 + 0.1 * k, h / 4, d * 0.5), L.basis(b.col[0], b.col[2], -b.col[1]), seg=24, mseg=6)
    L.box(name + "Kit", (0.1, 0.07, 0.12), M["locker"], _a(p, b, 0.1, h / 4 - 0.04, d * 0.5), _r(b), bevel=0.004)


# ------------------------------------------------------------------ habitation and lab furniture
def cabinet(name, p, b, w, h, d, doors=2, top=None, live=True):
    """Wall cabinet/counter unit with doors, pulls and an optional worktop; hollow inside, with a shelf and stowage."""
    if not live:
        L.box(name, (w, h, d), M["locker"], _a(p, b, 0, 0, d / 2), _r(b), bevel=0.003)
    else:
        _shell(name, p, b, w, h, d, M["locker"], inner=M.get("frame_dark", M["module"]))
        if h > 0.22:
            L.box(name + "Shelf", (w - 0.02, 0.008, d - 0.02), M["locker"], _a(p, b, 0, 0, d / 2), _r(b))
            _stowed(name + "Upper", p, b, w - 0.03, d - 0.01, 0.004, seed=hash(name) % 991, h_max=h / 2 - 0.03)
            _stowed(name + "Lower", p, b, w - 0.03, d - 0.01, -h / 2 + 0.01, seed=hash(name) % 991 + 7, h_max=h / 2 - 0.03)
        else:
            _stowed(name + "Inside", p, b, w - 0.03, d - 0.01, -h / 2 + 0.01, seed=hash(name) % 991, h_max=h - 0.04)
    dw = w / doors
    for k in range(doors):
        x = -w / 2 + dw * (k + 0.5)
        sgn = 1 if k % 2 == 0 else -1   # the pull's side; the hinge is on the other
        leaf = L.box(f"{name}Door{k}", (dw - 0.012, h - 0.02, 0.006), M["locker"], _a(p, b, x, 0, d + 0.003), _r(b), bevel=0.001)
        pull = L.box(f"{name}Pull{k}", (0.012, 0.06, 0.012), M["handle"], _a(p, b, x + (dw / 2 - 0.03) * sgn, h * 0.25, d + 0.012), _r(b), bevel=0.002)
        if live:
            A.hinge(f"{name}_{k}", [leaf, pull], _a(p, b, x - sgn * (dw / 2 - 0.006), 0, d + 0.003), b.col[1],
                    _a(p, b, x + sgn * (dw / 2 - 0.006), 0, d + 0.003), b.col[2], act_at=_a(p, b, x, 0, d + 0.01))
    if top:
        L.box(name + "Top", (w + 0.02, 0.025, d + 0.03), top, _a(p, b, 0, h / 2 + 0.0125, d / 2 + 0.01), _r(b), bevel=0.004)


def oven(name, p, b, w=0.2, h=0.16, d=0.18):
    """Food warmer/oven with a window, dial and status lamps; a lit cavity with a meal pouch behind the door."""
    cw = w * 0.7
    _shell(name + "Cavity", p, b, cw, h, d, M["module"], x0=-w * 0.1 - 0.0, inner=M.get("frame_dark", M["module"]))
    L.box(name + "Controls", (w * 0.25 - 0.002, h, d), M["module"], _a(p, b, w * 0.375 + 0.001, 0, d / 2), _r(b), bevel=0.004)
    L.box(name + "Rack", (cw - 0.03, 0.004, d - 0.03), M["buckle"], _a(p, b, -w * 0.1, -h * 0.15, d / 2), _r(b))
    L.box(name + "Meal", (cw * 0.55, 0.025, d * 0.5), M["foil"], _a(p, b, -w * 0.1, -h * 0.15 + 0.015, d / 2), _r(b), bevel=0.008, segs=1)
    L.box(name + "CavityLamp", (0.03, 0.004, 0.02), M["light"], _a(p, b, -w * 0.1, h / 2 - 0.012, d * 0.3), _r(b))
    leaf = L.box(name + "Door", (w * 0.7, h * 0.75, 0.006), M["ring"], _a(p, b, -w * 0.1, 0, d + 0.003), _r(b), bevel=0.002)
    window = L.box(name + "Window", (w * 0.5, h * 0.45, 0.002), M["crt_data"], _a(p, b, -w * 0.1, 0.005, d + 0.0065), _r(b))
    A.hinge(name, [leaf, window], _a(p, b, -w * 0.45, 0, d + 0.003), b.col[1], _a(p, b, w * 0.25, 0, d + 0.003), b.col[2],
            act_at=_a(p, b, -w * 0.1, 0, d + 0.01))
    L.cylinder(name + "Dial", 0.014, 0.012, M["toggle"], _a(p, b, w * 0.38, h * 0.2, d + 0.006), _r(b), segs=16, bevel=0.002)
    G.lamps(name + "Lamps", _a(p, b, w * 0.38, -h * 0.2, d), b, 0.04, 0.03, 2)


def utensil_rack(name, p, b, w=0.24):
    """Velcro strip with spoons, scissors, drink bags and a cup."""
    L.box(name, (w, 0.05, 0.006), M["strap"], _a(p, b, 0, 0, 0.003), _r(b))
    for i, (x, mat) in enumerate(((-0.09, M["toggle"]), (-0.07, M["toggle"]), (-0.04, M["red"]))):
        L.box(f"{name}Tool{i}", (0.012, 0.11, 0.006), mat, _a(p, b, x, -0.02, 0.009), _r(b), bevel=0.002)
    for i, x in enumerate((0.01, 0.06)):
        L.box(f"{name}DrinkBag{i}", (0.045, 0.07, 0.015), M["foil"], _a(p, b, x, -0.01, 0.012), _r(b), bevel=0.008)
    L.cylinder(name + "Cup", 0.02, 0.05, M["btn_soft"], _a(p, b, 0.1, -0.005, 0.025), L.basis(b.col[0], b.col[2], -b.col[1]), segs=16, bevel=0.003)


def table(name, centre, r=0.28, h=0.42, floor_z=0.0):
    """Wardroom table in the stock style: chamfered grey top with a dark inset and rim, chamfered column on a bolted
    base, one meal tray strapped down with soft pouches and a drink bag (all matte, so nothing glares under the light)."""
    frame = M.get("frame", M["module"])
    dark = M.get("frame_dark", M["module"])
    c = Vector(centre)
    top = floor_z + h
    L.cylinder(name + "Top", r, 0.035, frame, (c.x, c.y, top), segs=8, bevel=0.012)
    L.cylinder(name + "Inset", r * 0.82, 0.006, dark, (c.x, c.y, top + 0.019), segs=8)
    L.torus(name + "Rail", r + 0.05, 0.011, M["yellow"], (c.x, c.y, top + 0.04), Matrix.Identity(3), seg=40, mseg=8)
    for k in range(6):
        a_ = 2 * math.pi * k / 6
        L.cylinder(f"{name}RailPost{k}", 0.008, 0.04, frame, (c.x + (r + 0.05) * math.cos(a_), c.y + (r + 0.05) * math.sin(a_), top + 0.02), segs=8)
    L.box(name + "Column", (0.09, 0.09, h - 0.04), frame, (c.x, c.y, floor_z + (h - 0.04) / 2 + 0.02), bevel=0.02, segs=1)
    L.box(name + "Base", (0.26, 0.26, 0.03), dark, (c.x, c.y, floor_z + 0.015), bevel=0.01, segs=1)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        L.cylinder(f"{name}BaseBolt{k}", 0.009, 0.008, M["buckle"], (c.x + 0.09 * math.cos(a), c.y + 0.09 * math.sin(a), floor_z + 0.034), segs=6)
    # meal tray: strapped down, four food containers (stew, mash and peas, rice, fruit), a labelled snack pouch,
    # a coffee bag with a straw, cutlery on a velcro strip
    tiles = {"stew": (0, 0.5, 0.5, 1), "mash": (0.5, 0.5, 1, 1), "rice": (0, 0, 0.5, 0.5), "fruit": (0.5, 0, 1, 0.5)}
    labels = {"stew": (0, 0.5, 0.5, 1), "mash": (0.5, 0.5, 1, 1), "snacks": (0, 0, 0.5, 0.5), "coffee": (0.5, 0, 1, 0.5)}
    rot = Matrix.Rotation(0.5, 3, "Z")
    q = Vector((c.x, c.y, top + 0.024))
    L.box(name + "Tray", (0.32, 0.22, 0.012), dark, q, rot, bevel=0.004, segs=1)
    for sx in (-1, 1):
        L.box(f"{name}TrayStrap{sx}", (0.018, 0.24, 0.014), M["strap"], q + rot @ Vector((sx * 0.15, 0, 0.002)), rot, bevel=0.003)
    for k, (key, x, y) in enumerate((("stew", -0.095, 0.048), ("mash", -0.005, 0.048), ("rice", -0.095, -0.045), ("fruit", -0.005, -0.045))):
        cw, ch, cd = 0.082, 0.078, 0.022
        cq = q + rot @ Vector((x, y, 0.006 + cd / 2))
        L.box(f"{name}Cup{k}", (cw, ch, cd), frame, cq, rot, bevel=0.006, segs=1)
        for e, (ex, ey, ew, eh) in enumerate(((0, ch / 2 - 0.003, cw, 0.006), (0, -ch / 2 + 0.003, cw, 0.006), (cw / 2 - 0.003, 0, 0.006, ch), (-cw / 2 + 0.003, 0, 0.006, ch))):
            L.box(f"{name}Cup{k}Rim{e}", (ew, eh, 0.006), frame, cq + rot @ Vector((ex, ey, cd / 2 + 0.002)), rot)
        L.plane(f"{name}Food{k}", cw - 0.012, ch - 0.012, M["food_tex"], cq + rot @ Vector((0, 0, cd / 2 + 0.001)), rot, uv_rect=tiles[key])
    # snack pouch and coffee bag with printed labels
    for k, (key, x, y, w_, h_, mat) in enumerate((("snacks", 0.1, 0.048, 0.07, 0.08, M["foil"]), ("coffee", 0.1, -0.045, 0.07, 0.085, M["canvas"]))):
        pq = q + rot @ Vector((x, y, 0.016))
        L.box(f"{name}Pouch{k}", (w_, h_, 0.02), mat, pq, rot, bevel=0.008)
        L.plane(f"{name}Label{k}", w_ * 0.86, h_ * 0.5, M["food_label"], pq + rot @ Vector((0, -h_ * 0.08, 0.0105)), rot @ Matrix.Rotation(math.pi / 2, 3, "Z"), uv_rect=labels[key])
    L.tube(name + "Straw", [q + rot @ Vector((0.1, -0.088, 0.025)), q + rot @ Vector((0.1, -0.115, 0.045))], 0.003, M["red"])
    # cutlery on a velcro strip along the tray edge
    L.box(name + "Velcro", (0.2, 0.014, 0.003), M["strap"], q + rot @ Vector((-0.05, -0.098, 0.0075)), rot)
    L.box(name + "SpoonHandle", (0.09, 0.008, 0.004), M["buckle"], q + rot @ Vector((-0.09, -0.098, 0.011)), rot, bevel=0.002)
    L.cylinder(name + "SpoonBowl", 0.012, 0.005, M["buckle"], q + rot @ Vector((-0.03, -0.098, 0.011)), rot, segs=16, bevel=0.002)
    L.box(name + "ForkHandle", (0.09, 0.008, 0.004), M["buckle"], q + rot @ Vector((-0.06, -0.083, 0.011)), rot, bevel=0.002)
    for t_ in (-1, 0, 1):
        L.box(f"{name}ForkTine{t_}", (0.025, 0.0025, 0.003), M["buckle"], q + rot @ Vector((0.0, -0.083 + t_ * 0.004, 0.011)), rot)

def sleep_station(name, p, b, w=0.5, h=0.8, d=0.32):
    """Crew quarters: framed booth, sleeping bag on the back wall, half-drawn curtain, reading lamp, locker, photo."""
    t = 0.02
    for sx in (-1, 1):
        L.box(f"{name}Side{sx}", (t, h, d), M["module"], _a(p, b, sx * (w / 2 - t / 2), 0, d / 2), _r(b), bevel=0.003)
    for sy in (-1, 1):
        L.box(f"{name}Cap{sy}", (w - 2 * t, t, d), M["module"], _a(p, b, 0, sy * (h / 2 - t / 2), d / 2), _r(b), bevel=0.003)
    sleeping_bag(name + "Bag", _a(p, b, 0, -0.02, 0.0), b, w * 0.75, h * 0.85, 0.11)
    L.cylinder(name + "CurtainRod", 0.006, w, M["buckle"], _a(p, b, 0, h / 2 - 0.04, d - 0.01), L.basis(b.col[1], b.col[2], b.col[0]), segs=10)
    parts = [L.box(name + "Curtain", (w * 0.38, h * 0.88, 0.01), M["towel"], _a(p, b, -w * 0.29, -0.02, d - 0.012), _r(b), bevel=0.004)]
    for k in range(4):
        parts.append(L.box(f"{name}Fold{k}", (0.012, h * 0.86, 0.016), M["towel"], _a(p, b, -w * 0.46 + k * 0.045, -0.02, d - 0.006), _r(b), bevel=0.004))
    A.curtain(name, parts, _a(p, b, -w / 2 + 0.02, -0.02, d - 0.012), _a(p, b, -w * 0.1, -0.02, d - 0.012),
              _a(p, b, w / 2 - 0.02, -0.02, d - 0.012), act_at=_a(p, b, -w * 0.25, 0.0, d))
    L.cylinder(name + "Lamp", 0.025, 0.03, M["ring"], _a(p, b, w * 0.3, h / 2 - 0.06, 0.05), L.basis(b.col[0], -b.col[2], b.col[1]), segs=16)
    A.glow(name, L.disc(name + "LampGlow", 0.02, M["light"], _a(p, b, w * 0.3, h / 2 - 0.0765, 0.05), L.basis(b.col[0], b.col[2], -b.col[1]), segs=20),
           act_at=_a(p, b, w * 0.3, h / 2 - 0.08, 0.06))
    L.box(name + "Locker", (0.12, 0.1, 0.08), M["locker"], _a(p, b, w * 0.28, -h * 0.3, 0.15), _r(b), bevel=0.003)
    L.box(name + "Photo", (0.06, 0.08, 0.002), M["crt_orbit"], _a(p, b, -w * 0.05, h * 0.2, 0.115), _r(b))


def toilet(name, p, b):
    """Waste management station: cabinet with a seat ring, suction hose, handholds."""
    cabinet(name + "Body", p, b, 0.36, 0.38, 0.3, doors=1, live=False)
    seat = _a(p, b, 0, 0.2, 0.17)
    A.target("Flush", name, _a(p, b, 0, 0.2, 0.3))
    L.torus(name + "Seat", 0.1, 0.02, M["btn_soft"], seat, L.basis(b.col[0], b.col[2], -b.col[1]), seg=28, mseg=8)
    L.tube(name + "Hose", [_a(p, b, 0.15, 0.0, 0.3), _a(p, b, 0.22, 0.05, 0.36), _a(p, b, 0.2, 0.2, 0.32)], 0.018, M.get("umbilical", M["handle"]))
    for sx in (-1, 1):
        L.tube(f"{name}Grip{sx}", [_a(p, b, sx * 0.2, 0.25, 0.0), _a(p, b, sx * 0.2, 0.25, 0.08), _a(p, b, sx * 0.2, 0.45, 0.08), _a(p, b, sx * 0.2, 0.45, 0.0)], 0.008, M["yellow"])


def sink(name, p, b):
    """Hygiene station: basin with a water nozzle, mirror, soap."""
    L.box(name + "Panel", (0.34, 0.4, 0.012), M["module"], _a(p, b, 0, 0, 0.006), _r(b), bevel=0.003)
    L.box(name + "Mirror", (0.22, 0.16, 0.004), M["glass_dark"], _a(p, b, 0, 0.1, 0.014), _r(b), bevel=0.002)
    L.cylinder(name + "Basin", 0.08, 0.06, M["toggle"], _a(p, b, 0, -0.1, 0.08), L.basis(b.col[0], b.col[2], -b.col[1]), segs=28, radius2=0.06)
    A.target("Wash", name, _a(p, b, 0, -0.05, 0.1))
    L.tube(name + "Tap", [_a(p, b, 0, -0.03, 0.012), _a(p, b, 0, -0.03, 0.08), _a(p, b, 0, -0.06, 0.09)], 0.006, M["buckle"])
    L.box(name + "Soap", (0.04, 0.06, 0.025), M["food_green"], _a(p, b, 0.13, -0.08, 0.025), _r(b), bevel=0.006)



def bike(name, centre, yaw=0.0, floor_z=0.0):
    """Zero-g cycle ergometer bolted to the deck (no seat, like the real ones): chamfered base frame with bolted feet,
    enclosed flywheel housing, cranks with strapped pedals, a post with a display and grab bar."""
    frame = M.get("frame", M["module"])
    dark = M.get("frame_dark", M["module"])
    c = Vector((centre[0], centre[1], 0.0))
    R = Matrix.Rotation(yaw, 3, "Z")

    def w(x, y, z):
        return c + R @ Vector((x, y, z)) + Vector((0, 0, floor_z))
    for sx in (-1, 1):
        L.box(f"{name}Rail{sx}", (0.05, 0.62, 0.04), dark, w(sx * 0.13, 0, 0.02), R, bevel=0.01, segs=1)
        for sy in (-1, 1):
            L.box(f"{name}Foot{sx}{sy}", (0.09, 0.08, 0.02), dark, w(sx * 0.13, sy * 0.27, 0.01), R, bevel=0.006, segs=1)
            L.cylinder(f"{name}Bolt{sx}{sy}", 0.008, 0.008, M["buckle"], w(sx * 0.13 + 0.025, sy * 0.27, 0.024), segs=6)
    for sy in (-0.22, 0.22):
        L.box(f"{name}Cross{sy}", (0.3, 0.05, 0.04), dark, w(0, sy, 0.03), R, bevel=0.01, segs=1)
    # flywheel housing: a chamfered drum box with a side cover and vent
    L.box(name + "Housing", (0.16, 0.36, 0.3), frame, w(0, 0.0, 0.2), R, bevel=0.04, segs=1)
    for sx in (-1, 1):
        L.cylinder(f"{name}Cover{sx}", 0.1, 0.012, dark, w(sx * 0.085, 0.0, 0.2), R @ Matrix.Rotation(math.pi / 2, 3, "Y"), segs=28, bevel=0.003)
        L.cylinder(f"{name}Hub{sx}", 0.025, 0.03, M["buckle"], w(sx * 0.1, 0.0, 0.2), R @ Matrix.Rotation(math.pi / 2, 3, "Y"), segs=16)
        # crank arm and strapped pedal, opposite each other
        a = 0.9 if sx > 0 else 0.9 + math.pi
        tip = (sx * 0.125, 0.11 * math.cos(a), 0.2 + 0.11 * math.sin(a))
        L.box(f"{name}Crank{sx}", (0.018, 0.12, 0.026), M["buckle"], w(sx * 0.115, 0.055 * math.cos(a), 0.2 + 0.055 * math.sin(a)), R @ Matrix.Rotation(-a + math.pi / 2, 3, "X"), bevel=0.005, segs=1)
        L.box(f"{name}Pedal{sx}", (0.09, 0.05, 0.018), dark, w(tip[0] + sx * 0.04, tip[1], tip[2]), R, bevel=0.005, segs=1)
        L.box(f"{name}Strap{sx}", (0.07, 0.03, 0.025), M["strap"], w(tip[0] + sx * 0.04, tip[1], tip[2] + 0.02), R, bevel=0.008)
    # post with display and grab bar
    L.box(name + "Post", (0.06, 0.06, 0.42), frame, w(0, -0.2, 0.52), R @ Matrix.Rotation(-0.15, 3, "X"), bevel=0.012, segs=1)
    L.box(name + "Console", (0.18, 0.1, 0.05), dark, w(0, -0.24, 0.76), R @ Matrix.Rotation(-0.7, 3, "X"), bevel=0.01, segs=1)
    L.box(name + "Display", (0.12, 0.06, 0.004), M["crt_data"], w(0, -0.222, 0.785), R @ Matrix.Rotation(-0.7, 3, "X"))
    L.tube(name + "Bar", [w(-0.18, -0.2, 0.7), w(-0.18, -0.24, 0.74), w(0.18, -0.24, 0.74), w(0.18, -0.2, 0.7)], 0.012, M["handle"])


def glovebox(name, p, b, w=0.5, h=0.38, d=0.32):
    """Science glovebox in the stock style: chamfered grey cabinet, dark glass window onto a lit work tray, two ringed
    glove ports with short gloves, a control strip along the top and a base shelf."""
    frame = M.get("frame", M["module"])
    dark = M.get("frame_dark", M["module"])
    L.box(name, (w, h, d), frame, _a(p, b, 0, 0, d / 2), _r(b), bevel=0.02, segs=1)
    # recessed window: dark frame, dark glass, a lit tray and sample jars just behind it
    L.box(name + "WindowFrame", (w * 0.84, h * 0.5, 0.016), dark, _a(p, b, 0, h * 0.14, d + 0.004), _r(b), bevel=0.006, segs=1)
    L.box(name + "Glass", (w * 0.76, h * 0.42, 0.004), M["glass_dark"], _a(p, b, 0, h * 0.14, d + 0.013), _r(b))
    L.box(name + "TrayLight", (w * 0.6, 0.008, 0.004), M["light"], _a(p, b, 0, h * 0.14 + h * 0.19, d + 0.012), _r(b))
    for k, x in enumerate((-0.1, -0.03, 0.05)):
        L.cylinder(f"{name}Jar{k}", 0.018, 0.04, M["goo"] if k == 1 else M["foil"], _a(p, b, x * w / 0.5, h * 0.02, d + 0.008),
                   L.basis(b.col[0], b.col[2], -b.col[1]), segs=14)
    # glove ports: chamfered collar rings with short gloves
    for sx in (-1, 1):
        q = _a(p, b, sx * w * 0.22, -h * 0.26, d)
        L.cylinder(f"{name}Port{sx}", 0.048, 0.03, dark, q + b.col[2] * 0.01, _r(b), segs=20, bevel=0.008)
        L.torus(f"{name}PortRing{sx}", 0.046, 0.007, M["buckle"], q + b.col[2] * 0.026, _r(b), seg=24, mseg=6)
        L.cylinder(f"{name}Glove{sx}", 0.032, 0.05, M["canvas"], q + b.col[2] * 0.05, _r(b), segs=14, bevel=0.012)
    # control strip along the top, base shelf, side handles
    L.box(name + "Strip", (w * 0.9, 0.04, 0.03), dark, _a(p, b, 0, h / 2 - 0.035, d + 0.006), _r(b), bevel=0.006, segs=1)
    G.lamps(name + "Lamps", _a(p, b, -w * 0.2, h / 2 - 0.035, d + 0.021), b, 0.12, 0.022, 4)
    G.toggles(name + "Switches", _a(p, b, w * 0.2, h / 2 - 0.035, d + 0.021), b, 0.12, 0.03, 3)
    L.box(name + "Shelf", (w + 0.04, 0.025, d + 0.06), dark, _a(p, b, 0, -h / 2 - 0.0125, d / 2 + 0.03), _r(b), bevel=0.006, segs=1)
    for sx in (-1, 1):
        L.tube(f"{name}Handle{sx}", [_a(p, b, sx * (w / 2), h * 0.25, d * 0.6), _a(p, b, sx * (w / 2 + 0.035), h * 0.25, d * 0.6),
                                      _a(p, b, sx * (w / 2 + 0.035), -h * 0.25, d * 0.6), _a(p, b, sx * (w / 2), -h * 0.25, d * 0.6)], 0.008, M["handle"])


def microscope(name, p, b):
    """Bench microscope with slides."""
    base = _a(p, b, 0, -0.06, 0.12)
    L.box(name + "Base", (0.14, 0.04, 0.12), M["btn_soft"], base, _r(b), bevel=0.006)
    L.tube(name + "Arm", [base + b.col[2] * 0.04, base + b.col[1] * 0.16 + b.col[2] * 0.03], 0.016, M["btn_soft"])
    L.cylinder(name + "Tube", 0.022, 0.12, M["bezel"], base + b.col[1] * 0.14 - b.col[2] * 0.02, L.basis(b.col[0], b.col[2], -b.col[1]) @ Matrix.Rotation(0.4, 3, "X"), segs=20)
    L.cylinder(name + "Eyepiece", 0.014, 0.05, M["handle"], base + b.col[1] * 0.2 + b.col[2] * 0.01, L.basis(b.col[0], b.col[2], -b.col[1]) @ Matrix.Rotation(0.6, 3, "X"), segs=16)
    for k in range(3):
        L.box(f"{name}Slide{k}", (0.06, 0.003, 0.025), M["btn_blue"], base + b.col[0] * 0.12 + b.col[2] * (-0.03 + 0.03 * k) - b.col[1] * 0.015, _r(b))


def freezer(name, p, b, w=0.36, h=0.42, d=0.3):
    """Sample freezer in the stock style: chamfered grey body, dark insulated door with a gasket, readout strip,
    a lever latch and a vent."""
    frame = M.get("frame", M["module"])
    dark = M.get("frame_dark", M["module"])
    dw, dh, dy = w * 0.8, h * 0.66, -0.03
    _shell(name + "Inner", p, b, dw, dh, d, M["btn_soft"], y0=dy)
    top_h = h / 2 - (dy + dh / 2)
    bot_h = (dy - dh / 2) + h / 2
    L.box(name + "TopBlock", (w, top_h, d), frame, _a(p, b, 0, h / 2 - top_h / 2, d / 2), _r(b), bevel=0.01, segs=1)
    L.box(name + "BottomBlock", (w, bot_h, d), frame, _a(p, b, 0, -h / 2 + bot_h / 2, d / 2), _r(b), bevel=0.01, segs=1)
    for sx in (-1, 1):
        L.box(f"{name}Cheek{sx}", ((w - dw) / 2, dh, d), frame, _a(p, b, sx * (w / 2 - (w - dw) / 4), dy, d / 2), _r(b), bevel=0.006, segs=1)
    vert = L.basis(b.col[0], b.col[2], -b.col[1]) @ Matrix.Rotation(math.pi / 2, 3, "X")
    for r_ in range(2):
        ry = dy - dh / 2 + 0.02 + r_ * dh / 2
        L.box(f"{name}Rack{r_}", (dw - 0.03, 0.005, d - 0.04), M["buckle"], _a(p, b, 0, ry, d / 2), _r(b))
        for i in range(int((dw - 0.06) / 0.03)):
            L.cylinder(f"{name}Tube{r_}_{i}", 0.008, min(0.09, dh / 2 - 0.04), M["food_red"] if (i + r_) % 3 == 0 else M["btn_soft"],
                       _a(p, b, -dw / 2 + 0.04 + i * 0.03, ry + min(0.09, dh / 2 - 0.04) / 2 + 0.003, d * 0.55), vert, segs=8)
    L.box(name + "Gasket", (w * 0.84, h * 0.7, 0.01), M["handle"], _a(p, b, 0, -0.03, d + 0.004), _r(b), bevel=0.004, segs=1)
    leaf = L.box(name + "Door", (w * 0.8, h * 0.66, 0.02), dark, _a(p, b, 0, -0.03, d + 0.014), _r(b), bevel=0.008, segs=1)
    L.box(name + "ReadoutStrip", (w * 0.84, 0.05, 0.012), dark, _a(p, b, 0, h / 2 - 0.045, d + 0.006), _r(b), bevel=0.004, segs=1)
    L.box(name + "Readout", (0.07, 0.025, 0.003), M["crt_data"], _a(p, b, -w * 0.2, h / 2 - 0.045, d + 0.0135), _r(b))
    G.lamps(name + "Lamps", _a(p, b, w * 0.18, h / 2 - 0.045, d + 0.012), b, 0.08, 0.02, 3)
    latch = L.box(name + "Latch", (0.03, 0.12, 0.025), M["handle"], _a(p, b, w * 0.3, -0.03, d + 0.036), _r(b), bevel=0.006, segs=1)
    A.hinge(name, [leaf, latch], _a(p, b, -w * 0.4, -0.03, d + 0.014), b.col[1], _a(p, b, w * 0.4, -0.03, d + 0.014), b.col[2],
            act_at=_a(p, b, 0, -0.03, d + 0.03))
    L.box(name + "Vent", (w * 0.5, 0.03, 0.006), M["handle"], _a(p, b, 0, -h / 2 + 0.03, d + 0.003), _r(b))


def sample_table(name, centre, floor_z):
    """Small lab table with a sample container under an inspection lamp, and notes."""
    c = Vector(centre)
    L.box(name + "Top", (0.5, 0.36, 0.025), M["module"], (c.x, c.y, floor_z + 0.4), bevel=0.004)
    for sx in (-1, 1):
        for sy in (-1, 1):
            L.tube(f"{name}Leg{sx}{sy}", [Vector((c.x + sx * 0.22, c.y + sy * 0.15, floor_z)), Vector((c.x + sx * 0.22, c.y + sy * 0.15, floor_z + 0.39))], 0.012, M["couchframe"])
    L.cylinder(name + "Sample", 0.05, 0.08, M["goo"], (c.x - 0.08, c.y, floor_z + 0.452), segs=24, bevel=0.006)
    L.cylinder(name + "SampleCap", 0.052, 0.02, M["foil"], (c.x - 0.08, c.y, floor_z + 0.5), segs=24, bevel=0.004)
    L.tube(name + "LampArm", [Vector((c.x + 0.18, c.y + 0.1, floor_z + 0.41)), Vector((c.x + 0.16, c.y + 0.08, floor_z + 0.7)), Vector((c.x - 0.05, c.y, floor_z + 0.68))], 0.008, M["couchframe"])
    L.cylinder(name + "LampHead", 0.045, 0.04, M["ring"], (c.x - 0.07, c.y, floor_z + 0.66), segs=20, radius2=0.03)
    L.disc(name + "LampLens", 0.04, M["light"], (c.x - 0.07, c.y, floor_z + 0.639), Matrix.Rotation(math.pi, 3, "X"), segs=20)
    L.box(name + "Notes", (0.12, 0.16, 0.004), M["whiteboard"], (c.x + 0.14, c.y - 0.06, floor_z + 0.415), Matrix.Rotation(0.2, 3, "Z"))


def net_with_gear(name, p, b, w=0.4, h=0.3):
    """Stowage net stretched over the wall with gear behind it."""
    mats = (M["canvas"], M["foil"], M["food_yellow"], M["btn_soft"], M["food_red"])
    for k in range(5):
        L.box(f"{name}Item{k}", (0.07 + 0.02 * (k % 2), 0.08, 0.04), mats[k], _a(p, b, -w * 0.38 + k * w * 0.19, -0.02 + 0.03 * (k % 2), 0.025),
              _r(b) @ Matrix.Rotation(((k * 13) % 9 - 4) * 0.05, 3, "Z"), bevel=0.01)
    netm = M.get("net", M["strap"])
    for k in range(5):
        y = -h / 2 + k * h / 4
        L.tube(f"{name}NetH{k}", [_a(p, b, -w / 2, y, 0.05), _a(p, b, w / 2, y, 0.05)], 0.0025, netm)
    for k in range(7):
        x = -w / 2 + k * w / 6
        L.tube(f"{name}NetV{k}", [_a(p, b, x, -h / 2, 0.05), _a(p, b, x, h / 2, 0.05)], 0.0025, netm)
    for sx in (-1, 1):
        for sy in (-1, 1):
            L.sphere(f"{name}Hook{sx}{sy}", 0.008, M["buckle"], _a(p, b, sx * w / 2, sy * h / 2, 0.05), u=8, v=4)


def hygiene_booth(name, p, b, w=0.62, h=1.05, d=0.58):
    """Private hygiene compartment round a toilet: side walls, a roof and a closed door with a handle, a vacant/engaged
    lamp, a sign and a vent louvre. p is the middle of the booth on the wall."""
    frame = M.get("frame", M["module"])
    dark = M.get("frame_dark", M["module"])
    for sx in (-1, 1):
        L.box(f"{name}Side{sx}", (0.03, h, d), M["locker"], _a(p, b, sx * (w / 2 - 0.015), 0, d / 2), _r(b), bevel=0.004, segs=1)
        L.box(f"{name}Post{sx}", (0.05, h + 0.02, 0.05), frame, _a(p, b, sx * (w / 2 - 0.025), 0, d - 0.01), _r(b), bevel=0.012, segs=1)
    L.box(name + "Roof", (w, 0.03, d), M["locker"], _a(p, b, 0, h / 2 - 0.015, d / 2), _r(b), bevel=0.004, segs=1)
    L.box(name + "Header", (w + 0.02, 0.06, 0.05), frame, _a(p, b, 0, h / 2 - 0.02, d - 0.01), _r(b), bevel=0.012, segs=1)
    door = _a(p, b, 0, -0.015, d - 0.005)
    L.box(name + "Door", (w - 0.1, h - 0.1, 0.03), M["locker"], door, _r(b), bevel=0.006, segs=1)
    L.box(name + "DoorPanel", (w - 0.2, h * 0.45, 0.006), dark, door + b.col[1] * h * 0.12 + b.col[2] * 0.017, _r(b), bevel=0.002)
    for i in range(6):   # vent louvre low in the door
        L.box(f"{name}Louvre{i}", (w - 0.24, 0.012, 0.01), dark, door - b.col[1] * (h * 0.3 + i * 0.022) + b.col[2] * 0.018, _r(b))
    L.tube(name + "Handle", [door + b.col[0] * (w / 2 - 0.1) + b.col[1] * 0.08 + b.col[2] * 0.015,
                             door + b.col[0] * (w / 2 - 0.1) + b.col[1] * 0.08 + b.col[2] * 0.05,
                             door + b.col[0] * (w / 2 - 0.1) - b.col[1] * 0.08 + b.col[2] * 0.05,
                             door + b.col[0] * (w / 2 - 0.1) - b.col[1] * 0.08 + b.col[2] * 0.015], 0.009, M["yellow"])
    sign = door + b.col[1] * (h / 2 - 0.15) + b.col[2] * 0.02
    L.box(name + "Sign", (0.16, 0.07, 0.008), frame, sign, _r(b), bevel=0.002)
    L.box(name + "SignLamp", (0.04, 0.03, 0.006), M["lamp_green"] if "lamp_green" in M else M["light"], sign + b.col[0] * 0.045 + b.col[2] * 0.006, _r(b), bevel=0.002)
    L.box(name + "SignTag", (0.07, 0.025, 0.004), M["btn_soft"], sign - b.col[0] * 0.03 + b.col[2] * 0.006, _r(b))
