"""Inspect a GLB in a clean Blender scene and print a JSON report.

Usage:
  blender -b --factory-startup --python scripts/blender/inspect_glb.py -- <in.glb> <out.json>

Read-only: imports into an empty scene, never saves or exports.
Reports both what Blender sees after import and what the raw glTF JSON
chunk declares (so importer conversions can't hide anything).
"""
import json
import os
import struct
import sys

import bmesh
import bpy
from mathutils import Vector


def raw_gltf(path):
    with open(path, "rb") as f:
        magic, version, length = struct.unpack("<4sII", f.read(12))
        chunk_len, chunk_type = struct.unpack("<I4s", f.read(8))
        doc = json.loads(f.read(chunk_len))
    tri_count = 0
    for mesh in doc.get("meshes", []):
        for prim in mesh["primitives"]:
            mode = prim.get("mode", 4)
            if "indices" in prim:
                n = doc["accessors"][prim["indices"]]["count"]
            else:
                n = doc["accessors"][prim["attributes"]["POSITION"]]["count"]
            if mode == 4:
                tri_count += n // 3
    images = []
    for img in doc.get("images", []):
        images.append({"name": img.get("name"), "mimeType": img.get("mimeType"),
                       "bufferView": img.get("bufferView"), "uri": img.get("uri")})
        if "bufferView" in img:
            images[-1]["bytes"] = doc["bufferViews"][img["bufferView"]]["byteLength"]
    return {
        "magic": magic.decode(), "version": version, "declaredLength": length,
        "generator": doc.get("asset", {}).get("generator"),
        "extensionsUsed": doc.get("extensionsUsed", []),
        "extensionsRequired": doc.get("extensionsRequired", []),
        "meshes": len(doc.get("meshes", [])),
        "primitives": sum(len(m["primitives"]) for m in doc.get("meshes", [])),
        "primitiveAttributes": [sorted(p["attributes"].keys()) for m in doc.get("meshes", []) for p in m["primitives"]],
        "nodes": len(doc.get("nodes", [])),
        "skins": len(doc.get("skins", [])),
        "animations": len(doc.get("animations", [])),
        "materials": [
            {
                "name": m.get("name"),
                "pbr": {k: v for k, v in m.get("pbrMetallicRoughness", {}).items()},
                "normalTexture": "normalTexture" in m,
                "emissiveTexture": "emissiveTexture" in m,
                "emissiveFactor": m.get("emissiveFactor"),
                "alphaMode": m.get("alphaMode", "OPAQUE"),
                "doubleSided": m.get("doubleSided", False),
                "extensions": list(m.get("extensions", {}).keys()),
            }
            for m in doc.get("materials", [])
        ],
        "textures": len(doc.get("textures", [])),
        "images": images,
        "trianglesFromIndices": tri_count,
    }


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    src, out = argv[0], argv[1]

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)

    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    armatures = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]

    world_min = Vector((1e9, 1e9, 1e9))
    world_max = Vector((-1e9, -1e9, -1e9))
    mesh_reports = []
    total_tris = total_verts = 0
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in meshes:
        me = obj.data
        me.calc_loop_triangles()
        tris = len(me.loop_triangles)
        total_tris += tris
        total_verts += len(me.vertices)
        for corner in obj.bound_box:
            w = obj.matrix_world @ Vector(corner)
            world_min = Vector(map(min, world_min, w))
            world_max = Vector(map(max, world_max, w))

        bm = bmesh.new()
        bm.from_mesh(me)
        non_manifold_edges = sum(1 for e in bm.edges if not e.is_manifold)
        boundary_edges = sum(1 for e in bm.edges if e.is_boundary)
        loose_verts = sum(1 for v in bm.verts if not v.link_edges)
        ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
        quads = sum(1 for f in bm.faces if len(f.verts) == 4)
        islands = 0
        seen = set()
        for v in bm.verts:
            if v.index in seen:
                continue
            islands += 1
            stack = [v]
            while stack:
                cur = stack.pop()
                if cur.index in seen:
                    continue
                seen.add(cur.index)
                stack.extend(e.other_vert(cur) for e in cur.link_edges if e.other_vert(cur).index not in seen)
        bm.free()

        uv_layers = [uv.name for uv in me.uv_layers]
        uv_out_of_range = 0
        if me.uv_layers:
            for d in me.uv_layers[0].data:
                u, v = d.uv
                if u < -0.001 or u > 1.001 or v < -0.001 or v > 1.001:
                    uv_out_of_range += 1

        mesh_reports.append({
            "name": obj.name,
            "parent": obj.parent.name if obj.parent else None,
            "location": [round(x, 4) for x in obj.matrix_world.translation],
            "rotationEulerDeg": [round(x * 57.29578, 2) for x in obj.matrix_world.to_euler()],
            "scale": [round(x, 4) for x in obj.matrix_world.to_scale()],
            "vertices": len(me.vertices),
            "faces": len(me.polygons),
            "triangles": tris,
            "quads": quads,
            "ngons": ngons,
            "materials": [s.material.name if s.material else None for s in obj.material_slots],
            "uvLayers": uv_layers,
            "uvLoopsOutsideUnitSquare": uv_out_of_range,
            "colorAttributes": [c.name for c in me.color_attributes],
            "shapeKeys": len(me.shape_keys.key_blocks) if me.shape_keys else 0,
            "vertexGroups": len(obj.vertex_groups),
            "modifiers": [m.type for m in obj.modifiers],
            "nonManifoldEdges": non_manifold_edges,
            "boundaryEdges": boundary_edges,
            "looseVertices": loose_verts,
            "connectedIslands": islands,
            "smoothShadedFaces": sum(1 for p in me.polygons if p.use_smooth),
        })

    images = []
    for img in bpy.data.images:
        if img.source in {"FILE", "GENERATED"} and img.size[0] > 0:
            images.append({"name": img.name, "size": list(img.size), "channels": img.channels,
                           "packed": img.packed_file is not None, "colorspace": img.colorspace_settings.name})

    materials = []
    for mat in bpy.data.materials:
        tex_links = []
        if mat.use_nodes:
            bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
            for n in mat.node_tree.nodes:
                if n.type == "TEX_IMAGE" and n.image:
                    targets = [l.to_socket.name for l in n.outputs[0].links] if n.outputs[0].links else []
                    # follow through normal map / separate nodes one hop
                    deep = []
                    for l in n.outputs[0].links:
                        if l.to_node.type != "BSDF_PRINCIPLED":
                            deep += [f"{l.to_node.type}->{ll.to_socket.name}" for o in l.to_node.outputs for ll in o.links]
                    tex_links.append({"image": n.image.name, "to": targets, "via": deep})
            emission = None
            if bsdf:
                es = bsdf.inputs.get("Emission Strength")
                emission = es.default_value if es else None
        materials.append({"name": mat.name, "users": mat.users, "textureLinks": tex_links,
                          "emissionStrength": emission})

    dims = world_max - world_min
    report = {
        "file": os.path.abspath(src),
        "fileSizeBytes": os.path.getsize(src),
        "blender": bpy.app.version_string,
        "raw": raw_gltf(src),
        "blenderScene": {
            "objects": [(o.name, o.type) for o in bpy.context.scene.objects],
            "meshCount": len(meshes),
            "triangles": total_tris,
            "vertices": total_verts,
            "materialCount": len(bpy.data.materials),
            "imageCount": len(images),
            "armatures": [a.name for a in armatures],
            "bones": sum(len(a.data.bones) for a in armatures),
            "actions": [a.name for a in bpy.data.actions],
            "boundsMinBlenderZUp": [round(x, 4) for x in world_min],
            "boundsMaxBlenderZUp": [round(x, 4) for x in world_max],
            "dimensionsXYZ_BlenderZUp": [round(x, 4) for x in dims],
        },
        "meshes": mesh_reports,
        "images": images,
        "materials": materials,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("INSPECT_OK", out)


main()
