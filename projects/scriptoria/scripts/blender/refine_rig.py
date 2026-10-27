"""M7.5c.2a.1 — final weight refinement of the Explorer rig (v2 -> v3).

Usage:
  blender -b --factory-startup --python scripts/blender/refine_rig.py -- \
      <rig-v2.blend> <out.glb> <out.blend> <report.json>

Starts from the v2 working .blend — verified identical (max weight diff 0.0)
to the approved explorer-neutral-25k-rigged-v2.glb — because it holds the
welded mesh; smoothing weights on the seam-split GLB could open seams.

Weight-only corrections (no new bones, geometry/UVs/materials untouched):
  1. Elbow: replaces the ~1 cm upper_arm -> forearm transition with a smooth
     (smoothstep) blend across the sleeve cuff, so the inner side of the bend
     folds into the cuff instead of the forearm knifing through it.
  2. Knee:  same treatment for thigh -> shin, to spread the back-of-knee pinch.
     The blend only redistributes the weight a vertex already gives the two
     bones; any third bone's share is preserved.
  3. Groin: Laplacian weight smoothing restricted to the inner-thigh/crotch
     region (masked by position and by thigh/hips dominance), so the jacket
     and trouser silhouette elsewhere keep their v2 weights.
Then: 4 influences max, clean, normalise (glTF/Babylon limit unchanged).
"""
import json
import os
import sys

import bmesh
import bpy
from mathutils import Vector

# (parent, child, window start, window end) — signed distance from the joint
# along the parent (negative) / child (positive) bone direction, metres.
JOINT_BLENDS = [
    ("upper_arm.L", "forearm.L", -0.06, 0.05),
    ("upper_arm.R", "forearm.R", -0.06, 0.05),
    ("thigh.L", "shin.L", -0.07, 0.06),
    ("thigh.R", "shin.R", -0.07, 0.06),
]
GROIN = {"max_abs_x": 0.13, "z_min": -0.08, "z_max": 0.16, "iterations": 6, "factor": 0.5,
         "groups": ("hips", "thigh.L", "thigh.R")}


def smoothstep(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def get_weights(mesh):
    names = {g.index: g.name for g in mesh.vertex_groups}
    return [{names[g.group]: g.weight for g in v.groups if g.weight > 0} for v in mesh.data.vertices]


def set_weights(mesh, weights, indices):
    vg = mesh.vertex_groups
    for i in indices:
        for g in vg:
            g.remove([i])
        for name, w in weights[i].items():
            if w > 1e-4:
                vg[name].add([i], w, "REPLACE")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    src_blend, out_glb, out_blend, report_path = argv[:4]
    # Optional override of the elbow window, "a0,a1" (used to compare blend placements).
    if len(argv) > 4:
        e0, e1 = (float(x) for x in argv[4].split(","))
        for k, jb in enumerate(JOINT_BLENDS):
            if jb[0].startswith("upper_arm"):
                JOINT_BLENDS[k] = (jb[0], jb[1], e0, e1)
    bpy.ops.wm.open_mainfile(filepath=src_blend)
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    mesh = next(o for o in bpy.data.objects if o.type == "MESH")
    bones = {b.name: (arm.matrix_world @ b.head_local, arm.matrix_world @ b.tail_local) for b in arm.data.bones}
    pos = [mesh.matrix_world @ v.co for v in mesh.data.vertices]
    weights = get_weights(mesh)
    changed = set()
    report = {"jointBlends": {}, "groin": {}}

    # 1–2. Smooth joint blends.
    for parent, child, a0, a1 in JOINT_BLENDS:
        joint = bones[child][0]
        pdir = (bones[parent][1] - bones[parent][0]).normalized()
        cdir = (bones[child][1] - bones[child][0]).normalized()
        n = 0
        for i, p in enumerate(pos):
            w = weights[i]
            pc = w.get(parent, 0.0) + w.get(child, 0.0)
            if pc < 0.05:
                continue
            d = p - joint
            a = d.dot(cdir) if d.dot(cdir) > 0 else d.dot(pdir)
            if not (a0 - 0.02 <= a <= a1 + 0.02):
                continue
            s = smoothstep(a0, a1, a)
            w[child], w[parent] = pc * s, pc * (1 - s)
            changed.add(i)
            n += 1
        report["jointBlends"][f"{parent}->{child}"] = {"window_m": [a0, a1], "vertices": n}

    # 3. Masked Laplacian smoothing at the groin.
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    bm.verts.ensure_lookup_table()
    nbrs = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
    bm.free()

    def dominant(w):
        return max(w, key=w.get) if w else None

    mask = [i for i, p in enumerate(pos)
            if abs(p.x) <= GROIN["max_abs_x"] and GROIN["z_min"] <= p.z <= GROIN["z_max"]
            and dominant(weights[i]) in GROIN["groups"]]
    mask_set = set(mask)
    for _ in range(GROIN["iterations"]):
        new = {}
        for i in mask:
            acc = {}
            for j in nbrs[i]:
                for k, w in weights[j].items():
                    acc[k] = acc.get(k, 0.0) + w / len(nbrs[i])
            keys = set(acc) | set(weights[i])
            blended = {k: (1 - GROIN["factor"]) * weights[i].get(k, 0.0) + GROIN["factor"] * acc.get(k, 0.0) for k in keys}
            new[i] = blended
        for i, w in new.items():
            weights[i] = w
    changed |= mask_set
    report["groin"] = {**{k: v for k, v in GROIN.items() if k != "groups"}, "groups": list(GROIN["groups"]), "vertices": len(mask)}

    # Keep top 4 influences and renormalise per vertex before writing back.
    for i in changed:
        top = sorted(weights[i].items(), key=lambda x: -x[1])[:4]
        total = sum(w for _, w in top) or 1.0
        weights[i] = {k: w / total for k, w in top if w / total > 0.001}
    set_weights(mesh, weights, sorted(changed))
    bpy.context.view_layer.objects.active = mesh
    with bpy.context.temp_override(object=mesh, active_object=mesh, selected_objects=[mesh]):
        bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
        bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)

    final = get_weights(mesh)
    hist, unweighted = {}, 0
    for w in final:
        hist[len(w)] = hist.get(len(w), 0) + 1
        unweighted += not w
    report.update({"verticesChanged": len(changed), "unweightedVertices": unweighted,
                   "influencesPerVertex": dict(sorted(hist.items())), "bones": len(arm.data.bones),
                   "deformBones": sum(1 for b in arm.data.bones if b.use_deform)})

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
    report["glbSizeBytes"] = os.path.getsize(out_glb)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=1)
    print("REFINE_OK", json.dumps(report))


main()
