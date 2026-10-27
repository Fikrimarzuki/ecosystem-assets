"""M7.5c.2a — build a minimal game humanoid rig for the Explorer and bind it.

Usage:
  blender -b --factory-startup --python scripts/blender/build_rig.py -- \
      <in.glb> <landmarks.json> <out.glb> <out.blend> <report.json>

Reads the approved optimized GLB (never writes to it). Joint positions come
from the measured cross-sections in landmarks.json (measure_landmarks.py);
the few anatomical choices (which section is the elbow, wrist, ...) are the
constants below and are checked visually in the deformation renders.

Skeleton: 1 root + 21 deform bones, no fingers, no twist bones, no face.
Limb bones are rolled so their local Z axis points forward (character −Y):
rotation about local X then bends a limb in its natural plane.
Binding: Blender automatic (bone-heat) weights, then normalised and limited
to 4 influences per vertex (glTF / Babylon skinning limit).
Mesh, UVs, materials and textures are left exactly as imported; the mesh is
only welded along UV seams (in memory) so heat weighting sees one surface.
"""
import json
import os
import sys

import bmesh
import bpy
from mathutils import Vector

FORWARD = Vector((0, -1, 0))  # glTF +Z forward == Blender −Y after import

# Positions along each measured arm axis (0 = axis start near the shoulder, 1 = fingertip).
ARM_T = {
    "shoulder": 0.05,  # just inside the armpit, top of the arm
    "elbow": 0.40,     # sleeve cuff / sharp narrowing, at waist height in A-pose
    "wrist": 0.63,     # end of the forearm narrowing, where glove + wrist device begin
    "hand_end": 0.90,  # mid-fingers (no finger bones)
}
# Heights (Blender Z, metres) on the measured leg centre-lines and the midline.
LEG_Z = {"hip": 0.12, "knee": -0.36, "ankle": -0.84}
FOOT = {"ankle_y": 0.02, "toe_base": (-0.10, -0.92), "toe_tip": (-0.19, -0.93)}  # (y, z)
SPINE = [("hips", 0.12, 0.24), ("spine", 0.24, 0.36), ("chest", 0.36, 0.54),
         ("neck", 0.54, 0.66), ("head", 0.66, 0.95)]
CLAVICLE_HEAD = (0.03, 0.01, 0.50)  # x is mirrored per side


def lerp_axis(arm, t):
    s, e = Vector(arm["axisStart"]), Vector(arm["axisEnd"])
    secs = arm["sections"]
    # Prefer the measured section centre nearest t (the axis is a best fit; the centre is the real limb middle).
    near = min(secs, key=lambda x: abs(x["t"] - t))
    if abs(near["t"] - t) <= 0.0126:
        return Vector(near["centre"])
    return s.lerp(e, t)


def leg_centre(leg, z):
    pts = sorted(leg, key=lambda x: abs(x["z"] - z))[:2]
    c = (Vector(pts[0]["centre"]) + Vector(pts[1]["centre"])) / 2
    c.z = z
    return c


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    src, landmarks_path, out_glb, out_blend, report_path = argv
    lm = json.load(open(landmarks_path))

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    mesh = next(o for o in bpy.context.scene.objects if o.type == "MESH")
    mesh.name = "explorer_neutral"
    mesh.data.name = "explorer_neutral"
    tris_before = sum(len(p.vertices) - 2 for p in mesh.data.polygons)

    # Weld UV-seam splits so bone heat diffuses across one connected surface.
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(mesh.data)
    bm.free()
    with bpy.context.temp_override(object=mesh, active_object=mesh, selected_objects=[mesh]):
        bpy.ops.mesh.customdata_custom_splitnormals_clear()

    floor_z = lm["bounds"]["min"][2]

    arm_data = bpy.data.armatures.new("explorer_rig")
    arm_obj = bpy.data.objects.new("explorer_rig", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones

    def bone(name, head, tail, parent=None, deform=True, connect=False):
        b = eb.new(name)
        b.head, b.tail = Vector(head), Vector(tail)
        b.align_roll(FORWARD)  # local Z -> character forward
        b.use_deform = deform
        if parent:
            b.parent = eb[parent]
            b.use_connect = connect
        return b

    bone("root", (0, 0, floor_z), (0, 0, floor_z + 0.15), deform=False)
    parent = "root"
    for name, z0, z1 in SPINE:
        bone(name, (0, 0.0, z0), (0, 0.0, z1), parent, connect=parent != "root")
        parent = name

    for side, sign in (("L", 1), ("R", -1)):
        arm = lm["arms"][side]
        sh = lerp_axis(arm, ARM_T["shoulder"])
        el = lerp_axis(arm, ARM_T["elbow"])
        wr = lerp_axis(arm, ARM_T["wrist"])
        he = lerp_axis(arm, ARM_T["hand_end"])
        bone(f"shoulder.{side}", (sign * CLAVICLE_HEAD[0], CLAVICLE_HEAD[1], CLAVICLE_HEAD[2]), sh, "chest")
        bone(f"upper_arm.{side}", sh, el, f"shoulder.{side}", connect=True)
        bone(f"forearm.{side}", el, wr, f"upper_arm.{side}", connect=True)
        bone(f"hand.{side}", wr, he, f"forearm.{side}", connect=True)

        leg = lm["legs"][side]
        hip = leg_centre(leg, LEG_Z["hip"])
        hip.y = 0.0
        knee = leg_centre(leg, LEG_Z["knee"])
        knee.y -= 0.01  # slight forward knee: unambiguous bend direction for future IK
        ankle = leg_centre(leg, LEG_Z["ankle"])
        ankle.y = FOOT["ankle_y"]
        toe_base = Vector((ankle.x, FOOT["toe_base"][0], FOOT["toe_base"][1]))
        toe_tip = Vector((ankle.x, FOOT["toe_tip"][0], FOOT["toe_tip"][1]))
        bone(f"thigh.{side}", hip, knee, "hips")
        bone(f"shin.{side}", knee, ankle, f"thigh.{side}", connect=True)
        bone(f"foot.{side}", ankle, toe_base, f"shin.{side}", connect=True)
        bone(f"toe.{side}", toe_base, toe_tip, f"foot.{side}", connect=True)

    joints = {b.name: {"head": [round(x, 4) for x in b.head], "tail": [round(x, 4) for x in b.tail],
                       "deform": b.use_deform, "parent": b.parent.name if b.parent else None} for b in eb}
    bpy.ops.object.mode_set(mode="OBJECT")

    # Bind with automatic (bone heat) weights. Blender reports heat failure only as a warning,
    # so unweighted vertices are counted explicitly below.
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")

    bpy.context.view_layer.objects.active = mesh
    with bpy.context.temp_override(object=mesh, active_object=mesh, selected_objects=[mesh]):
        bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
        bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)
        bpy.ops.object.vertex_group_clean(group_select_mode="ALL", limit=0.001)
        bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)

    names = {g.index: g.name for g in mesh.vertex_groups}
    unweighted, influence_hist = 0, {}
    head_region_non_head = 0
    for v in mesh.data.vertices:
        ws = [(names[g.group], g.weight) for g in v.groups if g.weight > 0]
        influence_hist[len(ws)] = influence_hist.get(len(ws), 0) + 1
        if not ws:
            unweighted += 1
        world = mesh.matrix_world @ v.co
        if world.z > 0.70 and sum(w for n, w in ws if n in ("head", "neck")) < 0.9:
            head_region_non_head += 1

    bone_vertex_counts = {g.name: 0 for g in mesh.vertex_groups}
    for v in mesh.data.vertices:
        for g in v.groups:
            if g.weight > 0.05:
                bone_vertex_counts[names[g.group]] += 1

    os.makedirs(os.path.dirname(out_glb), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    arm_obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=out_glb, export_format="GLB", use_selection=True, export_yup=True,
        export_apply=False, export_texcoords=True, export_normals=True, export_tangents=False,
        export_materials="EXPORT", export_image_format="AUTO", export_animations=False,
        export_skins=True, export_morph=False, export_draco_mesh_compression_enable=False,
    )
    bpy.ops.wm.save_as_mainfile(filepath=out_blend, compress=True)

    report = {
        "source": os.path.abspath(src),
        "trianglesBefore": tris_before,
        "trianglesAfter": sum(len(p.vertices) - 2 for p in mesh.data.polygons),
        "weldedVertices": len(mesh.data.vertices),
        "bones": len(arm_data.bones),
        "deformBones": sum(1 for b in arm_data.bones if b.use_deform),
        "joints": joints,
        "unweightedVertices": unweighted,
        "influencesPerVertex": dict(sorted(influence_hist.items())),
        "verticesAboveZ0.70NotMostlyHeadNeck": head_region_non_head,
        "verticesPerBone_weightOver0.05": bone_vertex_counts,
        "glb": out_glb, "glbSizeBytes": os.path.getsize(out_glb), "blend": out_blend,
    }
    with open(report_path, "w") as f:
        json.dump(report, f, indent=1)
    print("RIG_OK", json.dumps({k: report[k] for k in ("bones", "deformBones", "unweightedVertices", "influencesPerVertex", "verticesAboveZ0.70NotMostlyHeadNeck", "glbSizeBytes")}))


main()
