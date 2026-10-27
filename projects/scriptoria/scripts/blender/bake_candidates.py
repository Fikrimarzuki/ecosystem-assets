"""M7.5c.1d — re-bake the source's textures onto each decimated candidate.

Usage:
  blender -b --factory-startup --python scripts/blender/bake_candidates.py -- \
      <source.glb> <decimated.glb> <out.glb> [<decimated.glb> <out.glb> ...]

Why: decimation keeps UVs by interpolation, so painted details that sat inside
removed triangles drift ("texture swimming") — measured on this asset as a
smeared chest light, a flattened mouth and a jagged hood rim. Baking samples
the untouched source surface through each candidate's own UVs, so the texture
lines up with the reduced geometry again. The normal bake also carries the
source's surface detail (its geometry + normal map) onto the lower mesh.

Per candidate, three 2048² maps, same layout and roles as the source material:
  base color          (EMIT pass of the source base-color texture, sRGB)
  metallic-roughness  (EMIT pass of the source MR texture, non-color)
  normal              (tangent-space NORMAL bake, non-color)
Exported as JPEG (quality 92), matching the source's JPEG textures.
Never writes to the source or to the decimated inputs.
"""
import os
import sys
import time

import bpy

RES = 2048
CAGE_EXTRUSION = 0.01   # m — p99 surface deviation of the candidates is ≤1.1 mm
MAX_RAY_DISTANCE = 0.03
MARGIN = 64  # px — wide dilation so distant mip levels never sample black background


def configure_cycles():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 1
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for backend in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = backend
            prefs.get_devices()
            gpus = [d for d in prefs.devices if d.type == backend]
            if gpus:
                for d in prefs.devices:
                    d.use = d.type == backend
                scene.cycles.device = "GPU"
                return backend
        except TypeError:
            continue
    scene.cycles.device = "CPU"
    return "CPU"


def import_single_mesh(path, name):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.context.scene.objects if o not in before and o.type == "MESH"]
    assert len(new) == 1, f"expected one mesh in {path}, got {len(new)}"
    new[0].name = name
    return new[0]


def texture_feeding(material, socket_name):
    """Image node that (directly or through one hop) feeds the BSDF input `socket_name`."""
    nt = material.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    link = bsdf.inputs[socket_name].links[0]
    node = link.from_node
    while node.type != "TEX_IMAGE":
        node = node.inputs[0].links[0].from_node if node.type != "NORMAL_MAP" else node.inputs["Color"].links[0].from_node
    return node


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    src_path, pairs = argv[0], list(zip(argv[1::2], argv[2::2]))

    bpy.ops.wm.read_factory_settings(use_empty=True)
    device = configure_cycles()
    print("BAKE_DEVICE", device)

    hi = import_single_mesh(src_path, "source_high")
    hi_mat = hi.active_material
    hi_nt = hi_mat.node_tree
    hi_out = next(n for n in hi_nt.nodes if n.type == "OUTPUT_MATERIAL")
    hi_bsdf = next(n for n in hi_nt.nodes if n.type == "BSDF_PRINCIPLED")
    hi_base = texture_feeding(hi_mat, "Base Color")
    hi_mr = texture_feeding(hi_mat, "Roughness")
    hi_emit = hi_nt.nodes.new("ShaderNodeEmission")

    def hi_emit_from(tex_node):
        hi_nt.links.new(tex_node.outputs[0], hi_emit.inputs["Color"])
        hi_nt.links.new(hi_emit.outputs[0], hi_out.inputs["Surface"])

    def hi_restore_bsdf():
        hi_nt.links.new(hi_bsdf.outputs[0], hi_out.inputs["Surface"])

    bake = bpy.context.scene.render.bake
    bake.use_selected_to_active = True
    bake.cage_extrusion = CAGE_EXTRUSION
    bake.max_ray_distance = MAX_RAY_DISTANCE
    bake.margin = MARGIN
    bake.normal_space = "TANGENT"

    for in_path, out_path in pairs:
        label = os.path.splitext(os.path.basename(out_path))[0]
        lo = import_single_mesh(in_path, f"{label}_low")
        lo_mat = lo.active_material.copy()
        lo_mat.name = "explorer_neutral"
        lo.active_material = lo_mat
        nt = lo_mat.node_tree
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        # Reuse the imported node graph (BaseColor -> BSDF, MR -> Separate Color, Normal Map),
        # but point each texture node at a freshly baked image.
        lo_base = texture_feeding(lo_mat, "Base Color")
        lo_mr = texture_feeding(lo_mat, "Roughness")
        lo_nrm = texture_feeding(lo_mat, "Normal")

        def target(name, non_color):
            img = bpy.data.images.new(f"{label}_{name}", RES, RES, alpha=False)
            if non_color:
                img.colorspace_settings.name = "Non-Color"
            img.file_format = "JPEG"
            return img

        images = {
            "basecolor": (lo_base, target("basecolor", False), "EMIT", lambda: hi_emit_from(hi_base)),
            "metallicroughness": (lo_mr, target("metallicroughness", True), "EMIT", lambda: hi_emit_from(hi_mr)),
            "normal": (lo_nrm, target("normal", True), "NORMAL", hi_restore_bsdf),
        }

        bpy.ops.object.select_all(action="DESELECT")
        hi.select_set(True)
        lo.select_set(True)
        bpy.context.view_layer.objects.active = lo
        timings = {}
        for key, (node, img, bake_type, prepare_hi) in images.items():
            prepare_hi()
            node.image = img
            for n in nt.nodes:
                n.select = False
            node.select = True
            nt.nodes.active = node
            t0 = time.time()
            bpy.ops.object.bake(type=bake_type)
            timings[key] = round(time.time() - t0, 1)
        hi_restore_bsdf()

        bpy.ops.object.select_all(action="DESELECT")
        lo.select_set(True)
        bpy.context.view_layer.objects.active = lo
        lo.data.name = "explorer_neutral"
        lo.name = "explorer_neutral"
        bpy.ops.export_scene.gltf(
            filepath=out_path,
            export_format="GLB",
            use_selection=True,
            export_apply=False,
            export_yup=True,
            export_texcoords=True,
            export_normals=True,
            export_tangents=False,
            export_materials="EXPORT",
            export_image_format="JPEG",
            export_jpeg_quality=92,
            export_vertex_color="NONE",
            export_animations=False,
            export_skins=False,
            export_morph=False,
            export_draco_mesh_compression_enable=False,
            export_extras=False,
        )
        print("BAKED", label, timings, os.path.getsize(out_path))
        bpy.data.objects.remove(lo, do_unlink=True)

    print("BAKE_ALL_OK")


main()
