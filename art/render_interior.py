"""Renders preview images of a generated interior (Cycles), cameras placed from the spec and seat points.

Usage: blender -b --python render_interior.py -- <in.blend> <spec.json> <out_dir> [width] [samples] [views...]
Views: seat, overview, console, side
"""
import json
import math
import os
import sys

import addon_utils
import bpy
from mathutils import Matrix, Vector

ARGS = sys.argv[sys.argv.index("--") + 1:]
BLEND, SPEC, OUT = ARGS[0], json.load(open(ARGS[1])), ARGS[2]
W = int(ARGS[3]) if len(ARGS) > 3 else 960
SAMPLES = int(ARGS[4]) if len(ARGS) > 4 else 32
VIEWS = ARGS[5:] or ["seat", "overview", "console", "side"]
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
# EEVEE by default: Matt's PC hard-crashed (fatal WHEA error) twice during long Cycles batches on 2026-10-10.
# EEVEE renders each frame in about a second with a short load burst. Set IVA_RENDER_ENGINE=CYCLES for photoreal
# stills, and IVA_RENDER_CPU=1 to keep Cycles off the GPU.
ENGINE = os.environ.get("IVA_RENDER_ENGINE", "EEVEE").upper()
if ENGINE != "CYCLES":
    scene.render.engine = "BLENDER_EEVEE"
    ee = scene.eevee
    ee.taa_render_samples = min(SAMPLES, 64)
    for attr, val in (("use_raytracing", True), ("use_shadows", True), ("use_gtao", True), ("use_bloom", True)):
        if hasattr(ee, attr):
            setattr(ee, attr, val)
    if hasattr(ee, "ray_tracing_options"):
        ee.ray_tracing_options.resolution_scale = "2"
    print("render engine EEVEE")
else:
    addon_utils.enable("cycles", default_set=True)
    scene.render.engine = "CYCLES"
try:  # Cycles only: use the GPU if one is available, unless IVA_RENDER_CPU=1
    if ENGINE != "CYCLES" or os.environ.get("IVA_RENDER_CPU") == "1":
        raise RuntimeError("no Cycles GPU setup")
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for backend in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            prefs.compute_device_type = backend
            prefs.get_devices()
            if any(d.type == backend for d in prefs.devices):
                for d in prefs.devices:
                    d.use = True
                scene.cycles.device = "GPU"
                print("render device", backend)
                break
        except Exception:
            continue
except Exception:
    pass
if ENGINE == "CYCLES":
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.max_bounces = 6
scene.render.resolution_x = W
scene.render.resolution_y = int(W * 9 / 16)
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Punchy"
scene.view_settings.exposure = 0.15

# ---------------------------------------------------------------- world: space, stars, a planet below (as render_mk13.py)
world = bpy.data.worlds.new("Space")
scene.world = world
world.use_nodes = True
nt = world.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputWorld")
coord = nt.nodes.new("ShaderNodeTexCoord")
dot = nt.nodes.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"
dot.inputs[1].default_value = (0.25, 0.55, 0.80)
nt.links.new(coord.outputs["Generated"], dot.inputs[0])
ramp_mask = nt.nodes.new("ShaderNodeValToRGB")
ramp_mask.color_ramp.elements[0].position = 0.0; ramp_mask.color_ramp.elements[0].color = (1, 1, 1, 1)
ramp_mask.color_ramp.elements[1].position = 0.02; ramp_mask.color_ramp.elements[1].color = (0, 0, 0, 1)
nt.links.new(dot.outputs["Value"], ramp_mask.inputs["Fac"])
noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 6.0; noise.inputs["Detail"].default_value = 8.0
nt.links.new(coord.outputs["Generated"], noise.inputs["Vector"])
planet_ramp = nt.nodes.new("ShaderNodeValToRGB")
planet_ramp.color_ramp.elements[0].position = 0.45; planet_ramp.color_ramp.elements[0].color = (0.04, 0.16, 0.42, 1)
planet_ramp.color_ramp.elements[1].position = 0.62; planet_ramp.color_ramp.elements[1].color = (0.9, 0.93, 0.97, 1)
nt.links.new(noise.outputs["Fac"], planet_ramp.inputs["Fac"])
glow_ramp = nt.nodes.new("ShaderNodeValToRGB")
glow_ramp.color_ramp.elements[0].position = 0.0; glow_ramp.color_ramp.elements[0].color = (0.35, 0.6, 1.0, 1)
glow_ramp.color_ramp.elements[1].position = 0.12; glow_ramp.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1)
absdot = nt.nodes.new("ShaderNodeMath"); absdot.operation = "ABSOLUTE"
nt.links.new(dot.outputs["Value"], absdot.inputs[0])
nt.links.new(absdot.outputs["Value"], glow_ramp.inputs["Fac"])
vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 90.0; vor.feature = "F1"
nt.links.new(coord.outputs["Generated"], vor.inputs["Vector"])
star_ramp = nt.nodes.new("ShaderNodeValToRGB")
star_ramp.color_ramp.elements[0].position = 0.0; star_ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
star_ramp.color_ramp.elements[1].position = 0.06; star_ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
nt.links.new(vor.outputs["Distance"], star_ramp.inputs["Fac"])
add_glow = nt.nodes.new("ShaderNodeMix"); add_glow.data_type = "RGBA"; add_glow.blend_type = "ADD"
add_glow.inputs["Factor"].default_value = 1.0
nt.links.new(star_ramp.outputs["Color"], add_glow.inputs["A"])
nt.links.new(glow_ramp.outputs["Color"], add_glow.inputs["B"])
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
nt.links.new(ramp_mask.outputs["Color"], mix.inputs["Factor"])
nt.links.new(add_glow.outputs["Result"], mix.inputs["A"])
nt.links.new(planet_ramp.outputs["Color"], mix.inputs["B"])
bg = nt.nodes.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = 1.2
nt.links.new(mix.outputs["Result"], bg.inputs["Color"])
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

# ---------------------------------------------------------------- geometry from the spec
prof = sorted(SPEC["profile"])
zf, zc = SPEC["floor"], SPEC["ceiling"]
span = zc - zf


def r_in(z):
    for (z0, r0), (z1, r1) in zip(prof, prof[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / max(1e-6, z1 - z0) - SPEC.get("wall", 0.07)
    return prof[-1][1] - SPEC.get("wall", 0.07)


con = SPEC.get("console") or {"z0": zf + span * 0.55, "height": span * 0.3, "depth": span * 0.25}
con_mid_z = con["z0"] + con["height"] * 0.55
con_r = r_in(con_mid_z) - con["depth"] * 0.7
k = max(0.4, min(1.6, span / 1.55))      # size relative to the Mk1-3 cabin

# ---------------------------------------------------------------- lights, scaled to the cabin
sun_data = bpy.data.lights.new("Sun", "SUN"); sun_data.energy = 4.5; sun_data.angle = math.radians(0.6)
sun = bpy.data.objects.new("Sun", sun_data); scene.collection.objects.link(sun)
sun.matrix_world = Matrix.Translation((0, 0, 3)) @ (Vector((0.35, -0.75, 0.55)).to_track_quat("Z", "Y").to_matrix().to_4x4())
for i, pl in enumerate(SPEC.get("preview_lights", [])):   # bespoke cabins place their own lamps (loc, dir, energy W, size m)
    ld = bpy.data.lights.new(f"Preview{i}", "AREA"); ld.energy = pl["energy"]; ld.size = pl.get("size", 0.3); ld.color = (1.0, 0.93, 0.82)
    lo = bpy.data.objects.new(f"Preview{i}", ld); scene.collection.objects.link(lo)
    lo.matrix_world = Matrix.Translation(pl["loc"]) @ Vector(pl["dir"]).to_track_quat("-Z", "Y").to_matrix().to_4x4()
for i, (y, f, energy, size) in enumerate([] if "preview_lights" in SPEC else ((0.1, 0.92, 32, 0.8), (-0.4, 0.75, 18, 0.5), (0.5, 0.68, 12, 0.6))):
    ld = bpy.data.lights.new(f"Cabin{i}", "AREA"); ld.energy = energy * k * k; ld.size = size * k; ld.color = (1.0, 0.93, 0.82)
    lo = bpy.data.objects.new(f"Cabin{i}", ld); scene.collection.objects.link(lo)
    lo.location = (0, y * k, zf + span * f)
    lo.rotation_euler = (math.pi, 0, 0)
if "preview_lights" not in SPEC:
    ld = bpy.data.lights.new("ConsoleGlow", "AREA"); ld.energy = 6 * k * k; ld.size = 0.8 * k; ld.color = (0.6, 0.85, 1.0)
    lo = bpy.data.objects.new("ConsoleGlow", ld); scene.collection.objects.link(lo)
    lo.matrix_world = Matrix.Translation((0, -con_r * 0.6, con_mid_z)) @ (Vector((0, 1, 0.4)).to_track_quat("-Z", "Y").to_matrix().to_4x4())


def camera(name, loc, target, fov_deg, up=None):
    cd = bpy.data.cameras.new(name)
    cd.angle = math.radians(fov_deg)
    cd.clip_start = 0.01
    co = bpy.data.objects.new(name, cd)
    scene.collection.objects.link(co)
    d = (Vector(target) - Vector(loc)).normalized()
    if up is None:
        rot = d.to_track_quat("-Z", "Y").to_matrix()
    else:  # explicit screen-up, e.g. a kerbal lying on their back sees the head end at the top of the view
        z = -d
        x = Vector(up).cross(z).normalized()
        rot = Matrix((x, z.cross(x), z)).transposed()
    co.matrix_world = Matrix.Translation(loc) @ rot.to_4x4()
    return co


seats = sorted([o for o in scene.objects if o.name.startswith("IVA_Seat")], key=lambda o: o.name)
eye0 = seats[0].matrix_world.translation.copy()
eye_side = (seats[-1] if len(seats) > 1 else seats[0]).matrix_world.translation.copy()
console_target = Vector((0.0, -con_r, con_mid_z))
back = r_in(zc - span * 0.1) * 0.75
views = {
    "seat": camera("CamSeat", eye0, eye0 + Vector((0, -1, 0.12)), 80),
    "overview": camera("CamOverview", Vector((0.1 * k, back, zc - span * 0.1)), Vector((0.0, -con_r * 0.8, zf + span * 0.4)), 100),
    "console": camera("CamConsole", Vector((0.0, -con_r * 0.25, con_mid_z + span * 0.08)), console_target, 62),
    "side": camera("CamSide", eye_side, eye_side + Vector((-0.6 if eye_side.x > 0 else 0.6, -0.8, 0.15)), 85),
}
# bespoke designs can place their own cameras: "cameras": {view: {loc, target, fov}}
for v, c in SPEC.get("cameras", {}).items():
    views[v] = camera("Cam_" + v, Vector(c["loc"]), Vector(c["target"]), c.get("fov", 80), c.get("up"))
if not ARGS[5:] and "cameras" in SPEC:
    VIEWS = list(SPEC["cameras"].keys())
part = SPEC["part"]
for v in VIEWS:
    hide = SPEC.get("cameras", {}).get(v, {}).get("hide", [])   # e.g. your own head in an eye view, as the game hides it
    for o in scene.objects:
        if o.name.startswith("REF_"):
            o.hide_render = any(o.name.startswith(h) for h in hide)
    scene.camera = views[v]
    scene.render.filepath = os.path.join(OUT, f"{part}_{v}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", v)
