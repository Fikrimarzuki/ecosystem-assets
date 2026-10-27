"""M7.5c.2a — pose the rigged Explorer, measure distortion, render comparisons.

Usage:
  blender -b --factory-startup --python scripts/blender/test_deformation.py -- \
      <rigged.glb> <previews_dir> <metrics.json>

Loads the *exported* rigged GLB into a clean scene (so the deliverable itself
is tested, not the authoring session), applies static test poses, and for
each pose:
  * measures distortion against the rest pose (edge strain, collapsed /
    over-stretched triangles, faces whose normal flipped relative to their
    dominant bone's rotation);
  * renders textured (EEVEE) and clay (Workbench) views with fixed cameras,
    plus close-ups of the tested joint.
Poses are applied as world-space rotations about each joint with a sign check
on where the bone tip moved, so "forward"/"down" mean what they say regardless
of bone roll. Nothing is keyframed; no animation is produced.
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_previews import place_camera, render, setup_scene  # noqa: E402

FORWARD = Vector((0, -1, 0))
BODY_RES = (600, 800)
CLOSE_RES = (600, 600)

# (bone, axis kind, degrees, expected tip motion)
#   axis kind: "bend" = perpendicular to the bone in its forward plane, "lateral" = about the forward axis,
#              "roll" = about the bone's own length (twist)
#   expected: fwd | back | down | up | in (towards the midline) | any (twists: no tip motion to check)
ARMS_DOWN = [("upper_arm.L", "lateral", 40, "down"), ("upper_arm.R", "lateral", 40, "down")]
POSES = {
    "rest": {"ops": [], "focus": None},
    "shoulder-down-40": {"ops": ARMS_DOWN, "focus": "upper_arm.L"},
    "shoulder-up-45": {"ops": [("upper_arm.L", "lateral", 45, "up"), ("upper_arm.R", "lateral", 45, "up")], "focus": "upper_arm.L"},
    "shoulder-swing": {"ops": ARMS_DOWN + [("upper_arm.L", "bend", 50, "fwd"), ("upper_arm.R", "bend", 40, "back")], "focus": "upper_arm.L"},
    "elbow-90": {"ops": ARMS_DOWN + [("forearm.L", "bend", 90, "fwd"), ("forearm.R", "bend", 90, "fwd")], "focus": "forearm.L"},
    "wrist-45": {"ops": ARMS_DOWN + [("hand.L", "bend", 45, "fwd"), ("hand.R", "bend", 45, "back")], "focus": "hand.L"},
    "hip-flex": {"ops": [("thigh.L", "bend", 60, "fwd"), ("thigh.R", "bend", 30, "back")], "focus": "thigh.L"},
    "knee-100": {"ops": [("thigh.L", "bend", 45, "fwd"), ("shin.L", "bend", 100, "back"), ("shin.R", "bend", 60, "back")], "focus": "shin.L"},
    "ankle": {"ops": [("foot.L", "bend", 30, "down"), ("foot.R", "bend", 20, "up")], "focus": "foot.L"},
    "idle": {"ops": ARMS_DOWN + [("forearm.L", "bend", 10, "fwd"), ("forearm.R", "bend", 10, "fwd")], "focus": None},
    "walk-contact": {"ops": ARMS_DOWN + [
        ("upper_arm.R", "bend", 20, "fwd"), ("upper_arm.L", "bend", 20, "back"),
        ("forearm.L", "bend", 15, "fwd"), ("forearm.R", "bend", 15, "fwd"),
        ("thigh.L", "bend", 25, "fwd"), ("shin.L", "bend", 5, "back"),
        ("thigh.R", "bend", 20, "back"), ("shin.R", "bend", 15, "back"), ("foot.R", "bend", 10, "down")], "focus": None},
    # Added in M7.5c.2a.1
    "stand-natural": {"ops": ARMS_DOWN + [("forearm.L", "bend", 10, "fwd"), ("forearm.R", "bend", 10, "fwd"),
                                          ("thigh.L", "lateral", 6, "in"), ("thigh.R", "lateral", 6, "in")], "focus": "thigh.L"},
    "spine-twist-25": {"ops": [("spine", "roll", 12, "any"), ("chest", "roll", 13, "any")], "focus": "chest"},
    "spine-side-15": {"ops": [("spine", "lateral", 8, "any"), ("chest", "lateral", 7, "any")], "focus": "chest"},
    "head-turn-45": {"ops": [("neck", "roll", 15, "any"), ("head", "roll", 30, "any")], "focus": "head"},
    "head-nod-20": {"ops": [("neck", "bend", 8, "fwd"), ("head", "bend", 12, "fwd")], "focus": "head"},
    "wrist-twist-60": {"ops": ARMS_DOWN + [("hand.L", "roll", 60, "any"), ("hand.R", "roll", -60, "any")], "focus": "hand.L"},
    "forearm-twist-60": {"ops": ARMS_DOWN + [("forearm.L", "roll", 60, "any"), ("forearm.R", "roll", -60, "any")], "focus": "forearm.L"},
    "run-stride": {"ops": [
        ("spine", "bend", 8, "fwd"), ("chest", "bend", 4, "fwd"),
        ("upper_arm.L", "lateral", 35, "down"), ("upper_arm.R", "lateral", 35, "down"),
        ("upper_arm.R", "bend", 45, "fwd"), ("upper_arm.L", "bend", 35, "back"),
        ("forearm.L", "bend", 90, "fwd"), ("forearm.R", "bend", 90, "fwd"),
        ("thigh.L", "bend", 55, "fwd"), ("shin.L", "bend", 60, "back"),
        ("thigh.R", "bend", 30, "back"), ("shin.R", "bend", 100, "back"), ("foot.R", "bend", 20, "down")], "focus": None},
}
BODY_VIEWS = {"front": 270.0, "side": 0.0, "three-quarter": 315.0}


def pose_bone_axis(pb, kind):
    head, tail = pb.head.copy(), pb.tail.copy()  # armature space == world (armature at identity)
    d = (tail - head).normalized()
    if kind == "lateral":
        return FORWARD.copy()
    if kind == "roll":
        return d
    axis = d.cross(FORWARD)
    if axis.length < 1e-4:  # bone already points forward/back (feet): bend about world X
        axis = Vector((1, 0, 0))
    return axis.normalized()


def moved_as_expected(before, after, expected):
    delta = after - before
    return {"fwd": delta.y < 0, "back": delta.y > 0, "down": delta.z < 0, "up": delta.z > 0,
            "in": abs(after.x) < abs(before.x), "any": True}[expected]


def apply_op(arm, name, kind, degrees, expected):
    pb = arm.pose.bones[name]
    head = pb.head.copy()
    axis = pose_bone_axis(pb, kind)
    before_tail = pb.tail.copy()
    original = pb.matrix.copy()
    for sign in (1, -1):
        rot = Matrix.Translation(head) @ Matrix.Rotation(math.radians(sign * degrees), 4, axis) @ Matrix.Translation(-head)
        pb.matrix = rot @ original
        bpy.context.view_layer.update()
        if moved_as_expected(before_tail, pb.tail, expected):
            return
    raise RuntimeError(f"could not move {name} {expected} with a {kind} rotation")


def evaluated(mesh):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    co = np.array([tuple(mesh.matrix_world @ v.co) for v in me.vertices])
    tris = np.array([tuple(t.vertices) for t in me.loop_triangles])
    ev.to_mesh_clear()
    return co, tris


def tri_normals_areas(co, tris):
    a, b, c = co[tris[:, 0]], co[tris[:, 1]], co[tris[:, 2]]
    n = np.cross(b - a, c - a)
    area = np.linalg.norm(n, axis=1) / 2
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12), area


def self_intersections(co, tris, keys):
    """Pairs of non-adjacent triangles that intersect (adjacency by welded position, so UV-seam splits don't count)."""
    bvh = BVHTree.FromPolygons([tuple(x) for x in co], [tuple(t) for t in tris])
    kt = keys[tris]
    out = []
    for i, j in bvh.overlap(bvh):
        if i < j and not (set(kt[i]) & set(kt[j])):
            out.append((i, j))
    return out


def distortion(arm, mesh, rest_co, rest_tris, dominant, groups_names, keys=None, rest_pairs=None):
    co, tris = evaluated(mesh)
    assert np.array_equal(tris, rest_tris)
    n0, a0 = tri_normals_areas(rest_co, rest_tris)
    n1, a1 = tri_normals_areas(co, tris)
    # Expected normal = rest normal rotated by the dominant bone of the triangle's first vertex.
    rots = {}
    for pb in arm.pose.bones:
        rest = (arm.matrix_world @ pb.bone.matrix_local).to_3x3()
        posed = (arm.matrix_world @ pb.matrix).to_3x3()
        rots[pb.name] = np.array(posed @ rest.inverted())
    dom_bone = [groups_names[dominant[t[0]]] for t in rest_tris]
    expected = np.array([rots[b] @ n for b, n in zip(dom_bone, n0)])
    flipped = (np.einsum("ij,ij->i", expected, n1) < 0) & (a0 > 1e-9)
    ratio = a1 / np.maximum(a0, 1e-12)
    edges = np.concatenate([rest_tris[:, [0, 1]], rest_tris[:, [1, 2]], rest_tris[:, [2, 0]]])
    l0 = np.linalg.norm(rest_co[edges[:, 0]] - rest_co[edges[:, 1]], axis=1)
    l1 = np.linalg.norm(co[edges[:, 0]] - co[edges[:, 1]], axis=1)
    strain = np.abs(l1 / np.maximum(l0, 1e-9) - 1)
    worst = {}
    bad = (ratio < 0.25) | (ratio > 3.0) | flipped
    for b, is_bad in zip(dom_bone, bad):
        if is_bad:
            worst[b] = worst.get(b, 0) + 1
    clip = {}
    new_pairs = 0
    if keys is not None:
        pairs = set(self_intersections(co, tris, keys)) - rest_pairs
        new_pairs = len(pairs)
        for i, _ in pairs:
            b = dom_bone[i]
            clip[b] = clip.get(b, 0) + 1
    return {
        "newSelfIntersections": new_pairs,
        "newSelfIntersectionsByDominantBone": dict(sorted(clip.items(), key=lambda x: -x[1])),
        "flippedFaces": int(flipped.sum()),
        "collapsedTris_areaUnder25pct": int((ratio < 0.25).sum()),
        "stretchedTris_areaOver300pct": int((ratio > 3.0).sum()),
        "edgeStrain_p99": round(float(np.percentile(strain, 99)), 3),
        "edgeStrain_max": round(float(strain.max()), 3),
        "edgesOver50pctStrain": int((strain > 0.5).sum()),
        "problemTrisByDominantBone": dict(sorted(worst.items(), key=lambda x: -x[1])),
    }, co


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    src, out_dir, metrics_path = argv
    out_dir = os.path.abspath(out_dir)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    arm = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
    mesh = next(o for o in bpy.context.scene.objects if o.type == "MESH")
    scene, cam = setup_scene()

    # Importer may leave a non-rest pose; force rest for the baseline.
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    rest_co, rest_tris = evaluated(mesh)
    names = {g.index: g.name for g in mesh.vertex_groups}
    dominant = []
    for v in mesh.data.vertices:
        dominant.append(max(v.groups, key=lambda g: g.weight).group if v.groups else 0)
    # Welded-position keys: seam-split duplicates share a key, so they count as adjacent.
    _, inv = np.unique(np.round(rest_co, 5), axis=0, return_inverse=True)
    keys = inv.reshape(-1)
    rest_pairs = set(self_intersections(rest_co, rest_tris, keys))

    results = {"file": os.path.abspath(src), "triangles": int(len(rest_tris)),
               "restSelfIntersections": len(rest_pairs), "poses": {}}
    for pose_name, spec in POSES.items():
        for pb in arm.pose.bones:
            pb.matrix_basis = Matrix.Identity(4)
        bpy.context.view_layer.update()
        for op in spec["ops"]:
            apply_op(arm, *op)
        metrics, co = distortion(arm, mesh, rest_co, rest_tris, dominant, names, keys, rest_pairs)
        results["poses"][pose_name] = metrics
        print("POSE", pose_name, json.dumps({k: v for k, v in metrics.items() if not k.endswith("ByDominantBone")}))

        for look in ("textured", "clay"):
            if look == "textured":
                scene.render.engine = "BLENDER_EEVEE"
            else:
                scene.render.engine = "BLENDER_WORKBENCH"
                sh = scene.display.shading
                sh.light, sh.color_type, sh.single_color, sh.show_cavity = "STUDIO", "SINGLE", (0.7, 0.7, 0.7), True
            for view, az in BODY_VIEWS.items():
                place_camera(cam, Vector((0, 0, 0)), 4.2, az, 5.0)
                render(scene, os.path.join(out_dir, look, f"{pose_name}_{view}.png"), BODY_RES)
            if spec["focus"]:
                joint = arm.pose.bones[spec["focus"]].head.copy()
                for view, az in (("front", 270.0), ("side", 0.0)):
                    place_camera(cam, joint, 0.85, az, 5.0)
                    render(scene, os.path.join(out_dir, look, f"{pose_name}_close-{view}.png"), CLOSE_RES)

    with open(metrics_path, "w") as f:
        json.dump(results, f, indent=1)
    print("DEFORM_OK")


if __name__ == "__main__":
    main()
