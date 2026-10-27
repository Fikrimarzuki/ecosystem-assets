"""M7.5c.1d — build decimated candidates of the Meshy Explorer character.

Usage:
  blender -b --factory-startup --python scripts/blender/optimize_explorer.py -- <source.glb> <out_dir> <metrics.json>

Reads the source GLB (never writes to it). Builds one linked duplicate per
candidate, all sharing the imported mesh data, each with a non-destructive
modifier stack:

  1. Weld (1e-5 m)  — re-joins vertices the GLB split along UV seams.
                      UVs are per-corner in Blender, so seams survive in UV data.
  2. Decimate (Collapse, uniform) — ratio calibrated per candidate to the target.

Modifiers are applied only on export (export_apply=True). The modifier stacks
are also saved to a working .blend so every candidate can be re-tuned later.
"""
import json
import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

TARGETS = [("40k", 40000), ("25k", 25000), ("20k", 20000)]
WELD_DISTANCE = 1e-5
TOLERANCE = 0.015  # accept within ±1.5 % of the target triangle count


def evaluated_mesh_world(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    verts = [obj.matrix_world @ v.co for v in me.vertices]
    tris = [tuple(lt.vertices) for lt in me.loop_triangles]
    uv_ok = len(me.uv_layers) > 0
    ev.to_mesh_clear()
    return verts, tris, uv_ok


def deviation(src_bvh, src_verts, cand_verts, cand_tris):
    """Symmetric surface deviation (metres): source points -> candidate surface and back."""
    cand_bvh = BVHTree.FromPolygons(cand_verts, cand_tris)

    def one_way(points, bvh):
        d = []
        for p in points:
            hit = bvh.find_nearest(p)
            if hit[0] is not None:
                d.append(hit[3])
        d.sort()
        return {
            "mean_mm": round(1000 * sum(d) / len(d), 3),
            "p95_mm": round(1000 * d[int(len(d) * 0.95)], 3),
            "p99_mm": round(1000 * d[int(len(d) * 0.99)], 3),
            "max_mm": round(1000 * d[-1], 3),
        }

    return {"sourceToCandidate": one_way(src_verts, cand_bvh), "candidateToSource": one_way(cand_verts, src_bvh)}


def bounds(verts):
    mn = Vector((min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts)))
    mx = Vector((max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts)))
    return mn, mx


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    src_path, out_dir, metrics_path = argv[:3]
    normal_mode = argv[3] if len(argv) > 3 else "recompute"  # "recompute" | "transfer"
    os.makedirs(out_dir, exist_ok=True)
    src_hash_before = os.path.getsize(src_path), os.path.getmtime(src_path)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src_path)
    base = next(o for o in bpy.context.scene.objects if o.type == "MESH")
    base.name = "explorer_source"
    base.data.name = "explorer_neutral"
    source_tris = sum(len(p.vertices) - 2 for p in base.data.polygons)

    # Reference surface for deviation metrics = the untouched imported geometry.
    src_verts, src_tris, _ = evaluated_mesh_world(base)
    src_bvh = BVHTree.FromPolygons(src_verts, src_tris)
    src_min, src_max = bounds(src_verts)

    # Keep an untouched copy of the source (with its custom normals) as the
    # normal-transfer target, before the shared mesh's normals are cleared.
    normal_source = base.copy()
    normal_source.data = base.data.copy()
    normal_source.name = "explorer_normal_source"
    bpy.context.scene.collection.objects.link(normal_source)
    normal_source.hide_render = True

    # Custom split normals from the GLB would be interpolated (not recomputed)
    # through decimation; clear them on the shared mesh. In "transfer" mode the
    # candidate then re-acquires the source's shading normals via Data Transfer.
    with bpy.context.temp_override(object=base, active_object=base, selected_objects=[base]):
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    for p in base.data.polygons:
        p.use_smooth = True

    metrics = {"sourceTriangles": source_tris, "normalMode": normal_mode, "candidates": {}}
    candidates = []
    for label, target in TARGETS:
        obj = base.copy()  # linked duplicate: shares mesh data and material
        obj.name = f"explorer_neutral_{label}"
        bpy.context.scene.collection.objects.link(obj)
        weld = obj.modifiers.new("Weld seams", "WELD")
        weld.merge_threshold = WELD_DISTANCE
        weld.mode = "ALL"
        dec = obj.modifiers.new("Decimate", "DECIMATE")
        dec.decimate_type = "COLLAPSE"
        dec.use_collapse_triangulate = True
        dec.use_symmetry = False  # wrist device is one-sided
        if normal_mode == "transfer":
            dt = obj.modifiers.new("Transfer source normals", "DATA_TRANSFER")
            dt.object = normal_source
            dt.use_loop_data = True
            dt.data_types_loops = {"CUSTOM_NORMAL"}
            dt.loop_mapping = "POLYINTERP_NEAREST"

        ratio = target / source_tris
        tris = None
        for _ in range(6):
            dec.ratio = ratio
            _, cand_tris, _ = evaluated_mesh_world(obj)
            tris = len(cand_tris)
            if abs(tris - target) / target <= TOLERANCE:
                break
            ratio *= target / tris
        candidates.append((label, target, obj, ratio, tris))

    normal_source.hide_set(True)
    base.hide_set(True)
    base.hide_render = True

    for label, target, obj, ratio, tris in candidates:
        cand_verts, cand_tris, uv_ok = evaluated_mesh_world(obj)
        mn, mx = bounds(cand_verts)
        out_path = os.path.join(out_dir, f"explorer-neutral-{label}.glb")

        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.export_scene.gltf(
            filepath=out_path,
            export_format="GLB",
            use_selection=True,
            export_apply=True,
            export_yup=True,
            export_texcoords=True,
            export_normals=True,
            export_tangents=False,
            export_materials="EXPORT",
            export_image_format="AUTO",
            export_vertex_color="NONE",
            export_animations=False,
            export_skins=False,
            export_morph=False,
            export_draco_mesh_compression_enable=False,
            export_extras=False,
        )

        metrics["candidates"][label] = {
            "file": out_path,
            "fileSizeBytes": os.path.getsize(out_path),
            "targetTriangles": target,
            "triangles": tris,
            "vertices": len(cand_verts),
            "decimateRatio": round(ratio, 5),
            "uvLayerPresent": uv_ok,
            "boundsMin": [round(x, 4) for x in mn],
            "boundsMax": [round(x, 4) for x in mx],
            "boundsDeltaVsSource_mm": [round(1000 * (a - b), 2) for a, b in zip(list(mn) + list(mx), list(src_min) + list(src_max))],
            "deviation": deviation(src_bvh, src_verts, cand_verts, cand_tris),
        }
        print("CANDIDATE", label, tris, os.path.getsize(out_path))

    blend_path = os.path.join(out_dir, "explorer-neutral-optimization.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path, compress=True)
    metrics["workingBlend"] = blend_path
    metrics["sourceUnchanged"] = (os.path.getsize(src_path), os.path.getmtime(src_path)) == src_hash_before
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print("OPTIMIZE_OK")


main()
