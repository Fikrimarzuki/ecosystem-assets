"""Render fixed-camera previews of a character GLB for side-by-side comparison.

Usage:
  blender -b --factory-startup --python scripts/blender/render_previews.py -- <in.glb> <out_dir> <label>

Every model gets identical cameras, lights, world and resolution, derived from
fixed constants (not from the model's own bounds), so candidates line up
pixel-for-pixel with the source. Two looks per view:
  textured — EEVEE, original materials (what the asset looks like)
  clay     — Workbench, flat grey, no textures (what the geometry looks like)
Read-only with respect to the GLB.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

# Fixed framing for a ~1.9 m character centred on the origin (verified by inspection).
TARGET = Vector((0.0, 0.0, 0.0))
FACE_TARGET = Vector((0.0, 0.0, 0.78))
# Character-left forearm/hand (+X in Blender, screen-right from the front), where the wrist device sits.
WRIST_TARGET = Vector((0.42, 0.0, 0.05))
WRIST_DISTANCE = 0.75
BODY_DISTANCE = 4.2
FACE_DISTANCE = 0.9
BODY_RES = (600, 800)
FACE_RES = (600, 600)

# Blender Z-up after glTF import: glTF +Z forward -> Blender -Y. Front camera sits on -Y.
VIEWS = {
    "front": 270.0,
    "three-quarter": 315.0,
    "side": 0.0,
    "back": 90.0,
}


def setup_scene():
    scene = bpy.context.scene
    world = bpy.data.worlds.new("PreviewWorld")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.55, 0.57, 0.6, 1.0)
    bg.inputs[1].default_value = 0.6
    scene.world = world

    key = bpy.data.lights.new("Key", "SUN")
    key.energy = 3.0
    key_obj = bpy.data.objects.new("Key", key)
    key_obj.rotation_euler = (math.radians(50), 0, math.radians(-30))
    scene.collection.objects.link(key_obj)
    fill = bpy.data.lights.new("Fill", "SUN")
    fill.energy = 1.0
    fill_obj = bpy.data.objects.new("Fill", fill)
    fill_obj.rotation_euler = (math.radians(60), 0, math.radians(150))
    scene.collection.objects.link(fill_obj)

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    scene.view_settings.view_transform = "Standard"
    scene.render.image_settings.file_format = "PNG"
    return scene, cam


def place_camera(cam, target, distance, azimuth_deg, elevation_deg=5.0):
    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)
    offset = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))) * distance
    cam.location = target + offset
    direction = target - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def render(scene, path, res):
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    src, out_dir, label = argv
    out_dir = os.path.abspath(out_dir)  # Blender resolves relative render paths unpredictably
    os.makedirs(out_dir, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    scene, cam = setup_scene()

    shots = [(f"{label}_{name}", TARGET, BODY_DISTANCE, az, 5.0, BODY_RES) for name, az in VIEWS.items()]
    shots.append((f"{label}_face", FACE_TARGET, FACE_DISTANCE, VIEWS["front"], 0.0, FACE_RES))
    shots.append((f"{label}_face-three-quarter", FACE_TARGET, FACE_DISTANCE, VIEWS["three-quarter"], 0.0, FACE_RES))
    shots.append((f"{label}_wrist", WRIST_TARGET, WRIST_DISTANCE, VIEWS["front"], 0.0, FACE_RES))

    # Textured
    scene.render.engine = "BLENDER_EEVEE"
    for name, target, dist, az, el, res in shots:
        place_camera(cam, target, dist, az, el)
        render(scene, os.path.join(out_dir, "textured", f"{name}.png"), res)

    # Clay (geometry only)
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "SINGLE"
    shading.single_color = (0.7, 0.7, 0.7)
    shading.show_cavity = True
    for name, target, dist, az, el, res in shots:
        if name.endswith(("_side", "_back")):
            continue
        place_camera(cam, target, dist, az, el)
        render(scene, os.path.join(out_dir, "clay", f"{name}.png"), res)

    print("RENDER_OK", label)


if __name__ == "__main__":
    main()
