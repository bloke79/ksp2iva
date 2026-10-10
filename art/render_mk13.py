"""Renders preview images of the Mk1-3 interior.

Usage: python3 render_mk13.py <in.blend> <out_dir> [width] [samples] [views...]
Views: seat, overview, left, console
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

BLEND, OUT = sys.argv[1], sys.argv[2]
W = int(sys.argv[3]) if len(sys.argv) > 3 else 960
SAMPLES = int(sys.argv[4]) if len(sys.argv) > 4 else 48
VIEWS = sys.argv[5:] or ["seat", "overview", "left", "console", "couches"]
os.makedirs(OUT, exist_ok=True)

import addon_utils
addon_utils.enable("cycles", default_set=True)
bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"
scene.cycles.max_bounces = 6
scene.render.resolution_x = W
scene.render.resolution_y = int(W * 9 / 16)
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Punchy"
scene.view_settings.exposure = 0.15

# ---------------------------------------------------------------- world: space, stars, a planet below
world = bpy.data.worlds.new("Space")
scene.world = world
world.use_nodes = True
nt = world.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputWorld")
coord = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(coord.outputs["Generated"], sep.inputs["Vector"])
# planet mask: directions below a tilted horizon
dot = nt.nodes.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"
dot.inputs[1].default_value = (0.25, 0.55, 0.80)          # horizon tilted so the planet shows through the front windows
nt.links.new(coord.outputs["Generated"], dot.inputs[0])
ramp_mask = nt.nodes.new("ShaderNodeValToRGB")
ramp_mask.color_ramp.elements[0].position = 0.0
ramp_mask.color_ramp.elements[0].color = (1, 1, 1, 1)
ramp_mask.color_ramp.elements[1].position = 0.02
ramp_mask.color_ramp.elements[1].color = (0, 0, 0, 1)
nt.links.new(dot.outputs["Value"], ramp_mask.inputs["Fac"])
# planet surface: blue ocean with cloud noise
noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 6.0; noise.inputs["Detail"].default_value = 8.0
nt.links.new(coord.outputs["Generated"], noise.inputs["Vector"])
planet_ramp = nt.nodes.new("ShaderNodeValToRGB")
planet_ramp.color_ramp.elements[0].position = 0.45; planet_ramp.color_ramp.elements[0].color = (0.04, 0.16, 0.42, 1)
planet_ramp.color_ramp.elements[1].position = 0.62; planet_ramp.color_ramp.elements[1].color = (0.9, 0.93, 0.97, 1)
nt.links.new(noise.outputs["Fac"], planet_ramp.inputs["Fac"])
# atmosphere glow near the horizon
glow_ramp = nt.nodes.new("ShaderNodeValToRGB")
glow_ramp.color_ramp.elements[0].position = 0.0; glow_ramp.color_ramp.elements[0].color = (0.35, 0.6, 1.0, 1)
glow_ramp.color_ramp.elements[1].position = 0.12; glow_ramp.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1)
absdot = nt.nodes.new("ShaderNodeMath"); absdot.operation = "ABSOLUTE"
nt.links.new(dot.outputs["Value"], absdot.inputs[0])
nt.links.new(absdot.outputs["Value"], glow_ramp.inputs["Fac"])
# stars
vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 90.0
vor.feature = "F1"
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

# ---------------------------------------------------------------- lights
sun_data = bpy.data.lights.new("Sun", "SUN"); sun_data.energy = 4.5; sun_data.angle = math.radians(0.6)
sun = bpy.data.objects.new("Sun", sun_data); scene.collection.objects.link(sun)
# shine down through the forward-right window
sun.matrix_world = Matrix.Translation((0, 0, 3)) @ (Vector((0.35, -0.75, 0.55)).to_track_quat("Z", "Y").to_matrix().to_4x4())
for i, (loc, energy, size) in enumerate((((0, 0.1, 1.55), 32, 0.8), ((0, -0.4, 1.3), 18, 0.5), ((0, 0.5, 1.2), 12, 0.6))):
    ld = bpy.data.lights.new(f"Cabin{i}", "AREA"); ld.energy = energy; ld.size = size; ld.color = (1.0, 0.93, 0.82)
    lo = bpy.data.objects.new(f"Cabin{i}", ld); scene.collection.objects.link(lo)
    lo.location = loc
    lo.rotation_euler = (math.pi, 0, 0)   # face down
# cool console glow
ld = bpy.data.lights.new("ConsoleGlow", "AREA"); ld.energy = 6; ld.size = 0.8; ld.color = (0.6, 0.85, 1.0)
lo = bpy.data.objects.new("ConsoleGlow", ld); scene.collection.objects.link(lo)
lo.matrix_world = Matrix.Translation((0, -0.55, 0.95)) @ (Vector((0, 1, 0.4)).to_track_quat("-Z", "Y").to_matrix().to_4x4())


# ---------------------------------------------------------------- cameras
def camera(name, loc, target, fov_deg):
    cd = bpy.data.cameras.new(name)
    cd.angle = math.radians(fov_deg)
    cd.clip_start = 0.01
    co = bpy.data.objects.new(name, cd)
    scene.collection.objects.link(co)
    d = (Vector(target) - Vector(loc)).normalized()
    co.matrix_world = Matrix.Translation(loc) @ d.to_track_quat("-Z", "Y").to_matrix().to_4x4()
    return co


seat0 = bpy.data.objects["IVA_Seat0"].matrix_world.translation.copy()
seat1 = bpy.data.objects["IVA_Seat1"].matrix_world.translation.copy()
views = {
    "seat": camera("CamSeat", seat0, seat0 + Vector((0, -1, 0.18)), 80),
    "overview": camera("CamOverview", Vector((0.15, 0.55, 1.55)), Vector((0.0, -0.45, 0.65)), 100),
    "left": camera("CamLeft", seat1, seat1 + Vector((0.25, -0.75, 0.1)), 80),
    "console": camera("CamConsole", Vector((0.0, -0.1, 1.05)), Vector((0.0, -0.75, 0.88)), 62),
    "couches": camera("CamCouches", Vector((0.1, -0.5, 1.48)), Vector((0.0, 0.15, 0.66)), 86),
}

for v in VIEWS:
    scene.camera = views[v]
    scene.render.filepath = os.path.join(OUT, f"mk13_{v}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", v)
