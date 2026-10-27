"""Local-only Blender inspection utilities. Never saves or changes source files."""
import hashlib
import json
import pathlib

import bpy
import numpy as np
from mathutils import Vector

HERE = pathlib.Path(__file__).resolve().parent
ASSETS = HERE.parents[2] / 'astronaut'
SOURCE = ASSETS / 'animated/m7.2/astronaut-assembled.blend'
OUTPUT = ASSETS / 'animated/m7.2/astronaut-animated-candidate.glb'
INPUTS = [SOURCE, ASSETS / 'animated/m7.2/astronaut-working.blend',
          ASSETS / 'animated/m7.2/astronaut-idle.fbx', ASSETS / 'animated/m7.2/astronaut-walk.fbx',
          ASSETS / 'prepared/m7.1/astronaut-meshy-textures-1024.glb']


def hashes():
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS}


def open_source():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    rigs = [o for o in scene.objects if o.type == 'ARMATURE']
    meshes = [o for o in scene.objects if o.type == 'MESH']
    assert len(scene.objects) == 2 and len(rigs) == len(meshes) == 1
    assert sorted(a.name for a in bpy.data.actions) == ['Idle', 'Walk']
    assert bpy.app.version[:3] == (5, 2, 2)
    return scene, rigs[0], meshes[0]


def activate(rig, action, frame):
    rig.animation_data_create()
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    # Imported glTF NLA tracks are muted to inspect one action at a time.
    for track in rig.animation_data.nla_tracks:
        track.mute = True
    bpy.context.scene.frame_set(int(frame), subframe=float(frame) % 1)
    bpy.context.view_layer.update()


def positions(mesh):
    evaluated = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    data = evaluated.to_mesh()
    try:
        co = np.empty(len(data.vertices) * 3, dtype=np.float64)
        data.vertices.foreach_get('co', co)
        matrix = np.asarray(evaluated.matrix_world, dtype=np.float64)
        return co.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]
    finally:
        evaluated.to_mesh_clear()


def bones(rig):
    return np.asarray([rig.matrix_world @ b.matrix for b in rig.pose.bones], dtype=np.float64)


def skin_matrices(rig):
    return np.asarray([rig.matrix_world @ b.matrix @ b.bone.matrix_local.inverted()
                       @ rig.matrix_world.inverted() for b in rig.pose.bones], dtype=np.float64)


def limit_weights(mesh):
    affected = []
    dropped = []
    for vertex in mesh.data.vertices:
        groups = sorted([(g.group, g.weight) for g in vertex.groups if g.weight > 0], key=lambda g: (-g[1], g[0]))
        if len(groups) <= 4:
            continue
        affected.append(vertex.index)
        dropped.append(sum(w for _, w in groups[4:]))
        for group, _ in groups[4:]:
            mesh.vertex_groups[group].remove([vertex.index])
        total = sum(w for _, w in groups[:4])
        for group, weight in groups[:4]:
            mesh.vertex_groups[group].add([vertex.index], weight / total, 'REPLACE')
    bpy.context.view_layer.update()
    return affected, dropped


def stats(values):
    values = np.asarray(values)
    return {'max': float(values.max()), 'mean': float(values.mean()),
            'p95': float(np.percentile(values, 95)), 'p99': float(np.percentile(values, 99))}


def render_setup():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 384
    scene.render.resolution_y = 480
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    if scene.world is None:
        scene.world = bpy.data.worlds.new('InspectionWorld')
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get('Background')
    background.inputs['Color'].default_value = (.18, .21, .28, 1)
    background.inputs['Strength'].default_value = .35
    data = bpy.data.cameras.new('InspectionCamera')
    camera = bpy.data.objects.new('InspectionCamera', data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    data.lens = 55
    for name, location, power, size in [('Key', (3,-4,5),550,4), ('Fill',(-3,-2,3),350,3), ('Rim',(1,3,4),450,3)]:
        data = bpy.data.lights.new(name, 'AREA')
        data.energy = power
        data.shape = 'DISK'
        data.size = size
        light = bpy.data.objects.new(name, data)
        scene.collection.objects.link(light)
        light.location = location
        light.rotation_euler = (Vector((0,0,1)) - light.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.ops.mesh.primitive_plane_add(size=200)
    floor = bpy.context.object
    ground = bpy.data.materials.new('InspectionFloor')
    ground.diffuse_color = (.12,.15,.19,1)
    floor.data.materials.append(ground)
    return camera


def render(camera, path, view):
    camera.location = (2.5,-4,2.1) if view == 'front' else (-2.5,4,2.1)
    camera.rotation_euler = (Vector((0,0,.9)) - camera.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
