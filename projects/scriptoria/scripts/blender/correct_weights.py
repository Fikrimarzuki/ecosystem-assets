"""M7.5c.2a — targeted weight corrections on the auto-weighted Explorer rig (v1 -> v2).

Usage:
  blender -b --factory-startup --python scripts/blender/correct_weights.py -- \
      <rig-v1.blend> <out.glb> <out.blend> <report.json>

Fixes found by test_deformation.py on v1 (both measured, not guessed):
  1. Clavicle bleed. Bone-heat gave shoulder.L/R dominance over z 0.15–0.71 —
     the whole jacket front panel down to the hem and up into the hood collar —
     so arm motion dragged the jacket and hip motion tore the hem. Clavicle
     weight is kept only near the shoulder (within CLAVICLE_RADIUS of the
     clavicle segment and above CLAVICLE_MIN_Z); the removed weight goes to the
     nearest torso bone (hips/spine/chest/neck).
  2. Joint pinching (linear-blend skinning volume loss at knees/elbows,
     sleeve kink at the shoulder). Weights are smoothed only across those
     transitions, then normalised and limited to 4 influences again.
Geometry, UVs, materials and textures are not touched.
"""
import json
import os
import sys

import bpy
from mathutils import Vector
from mathutils.geometry import intersect_point_line

CLAVICLE_RADIUS = 0.11
CLAVICLE_MIN_Z = 0.36
TORSO = ("hips", "spine", "chest", "neck")
SMOOTH_SETS = [
    ("thigh.L", "shin.L"), ("thigh.R", "shin.R"),
    ("upper_arm.L", "forearm.L"), ("upper_arm.R", "forearm.R"),
    ("shoulder.L", "upper_arm.L"), ("shoulder.R", "upper_arm.R"),
]
SMOOTH_FACTOR = 0.5
SMOOTH_REPEAT = 4


def seg_distance(p, a, b):
    closest, t = intersect_point_line(p, a, b)
    if t < 0:
        closest = a
    elif t > 1:
        closest = b
    return (p - closest).length


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    src_blend, out_glb, out_blend, report_path = argv
    bpy.ops.wm.open_mainfile(filepath=src_blend)
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    mesh = next(o for o in bpy.data.objects if o.type == "MESH")
    bones = {b.name: (arm.matrix_world @ b.head_local, arm.matrix_world @ b.tail_local) for b in arm.data.bones}
    vg = mesh.vertex_groups
    moved = 0

    # 1. Clamp clavicle influence to the shoulder region.
    for side in ("L", "R"):
        g = vg[f"shoulder.{side}"]
        a, b = bones[f"shoulder.{side}"]
        for v in mesh.data.vertices:
            w = next((x.weight for x in v.groups if x.group == g.index), 0.0)
            if w <= 0:
                continue
            p = mesh.matrix_world @ v.co
            if p.z >= CLAVICLE_MIN_Z and seg_distance(p, a, b) <= CLAVICLE_RADIUS:
                continue
            target = min(TORSO, key=lambda n: seg_distance(p, *bones[n]))
            g.remove([v.index])
            vg[target].add([v.index], w, "ADD")
            moved += 1

    # 2. Smooth only across the problem transitions.
    bpy.context.view_layer.objects.active = mesh
    for pair in SMOOTH_SETS:
        for name in pair:
            vg.active_index = vg[name].index
            with bpy.context.temp_override(object=mesh, active_object=mesh, selected_objects=[mesh]):
                bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
                bpy.ops.object.vertex_group_smooth(group_select_mode="ACTIVE", factor=SMOOTH_FACTOR,
                                                   repeat=SMOOTH_REPEAT, expand=0.0)
                bpy.ops.object.mode_set(mode="OBJECT")

    with bpy.context.temp_override(object=mesh, active_object=mesh, selected_objects=[mesh]):
        bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
        bpy.ops.object.vertex_group_clean(group_select_mode="ALL", limit=0.001)
        bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)

    names = {g.index: g.name for g in vg}
    reach, unweighted, hist = {}, 0, {}
    for v in mesh.data.vertices:
        ws = [(names[g.group], g.weight) for g in v.groups if g.weight > 0]
        hist[len(ws)] = hist.get(len(ws), 0) + 1
        if not ws:
            unweighted += 1
        z = (mesh.matrix_world @ v.co).z
        for n, w in ws:
            if w > 0.3:
                lo, hi = reach.get(n, (z, z))
                reach[n] = (min(lo, z), max(hi, z))

    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    arm.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=out_glb, export_format="GLB", use_selection=True, export_yup=True,
        export_apply=False, export_texcoords=True, export_normals=True, export_tangents=False,
        export_materials="EXPORT", export_image_format="AUTO", export_animations=False,
        export_skins=True, export_morph=False, export_draco_mesh_compression_enable=False,
    )
    bpy.ops.wm.save_as_mainfile(filepath=out_blend, compress=True)
    report = {
        "clavicleWeightsMoved": moved,
        "unweightedVertices": unweighted,
        "influencesPerVertex": dict(sorted(hist.items())),
        "zReachWeightOver0.3": {k: [round(lo, 3), round(hi, 3)] for k, (lo, hi) in sorted(reach.items())},
        "glbSizeBytes": os.path.getsize(out_glb),
    }
    with open(report_path, "w") as f:
        json.dump(report, f, indent=1)
    print("CORRECT_OK", json.dumps({k: report[k] for k in ("clavicleWeightsMoved", "unweightedVertices", "influencesPerVertex")}))
    print("REACH", report["zReachWeightOver0.3"])


main()
