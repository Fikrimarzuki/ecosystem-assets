"""Export the LEARNING_V2 scene (M8.9b.1a.3): GLB (visual layers + anchors only), the .blend (written as a separate file, never
saving over the live session), and a Workbench check render. Run through Blender MCP after build_learning_town_v2.py."""
import bpy, os, json, math, traceback
from mathutils import Vector, Matrix

ROOT = r"D:\Code\porto-projects\gateway-assets\planets\learning"
GLB = os.path.join(ROOT, "exports", "learning-v2.glb")
BLEND = os.path.join(ROOT, "learning-v2.blend")
RENDER = os.path.join(ROOT, "references", "blender-workbench-front-v2.png")
EXPORT_COLLECTIONS = ("LEARNING_VISUAL", "LEARNING_PATHS", "LEARNING_BUILDINGS", "LEARNING_DECORATIONS", "LEARNING_ACCENTS", "LEARNING_ANCHORS")

def main():
    scene = bpy.data.scenes["LEARNING_V2"]
    user_scene = bpy.context.window.scene
    out = {}
    try:
        bpy.context.window.scene = scene
        view_layer = bpy.context.view_layer
        for ob in scene.objects:
            ob.select_set(False)
        selected = []
        for name in EXPORT_COLLECTIONS:
            for ob in bpy.data.collections[name].objects:
                ob.select_set(True); selected.append(ob.name)
        # Only pass exporter options that exist in this Blender's glTF add-on.
        props = bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
        wanted = dict(filepath=GLB, export_format='GLB', use_selection=True, use_active_scene=True, export_apply=True, export_yup=True,
                      export_extras=True, export_cameras=False, export_lights=False, export_animations=False, export_skins=False,
                      export_morph=False, export_texcoords=False, export_normals=True, export_materials='EXPORT',
                      export_vertex_color='ACTIVE', export_all_vertex_colors=False, export_active_vertex_color_when_no_material=True,
                      export_image_format='NONE', export_draco_mesh_compression_enable=False, export_hierarchy_full_collections=False)
        kwargs = {k: v for k, v in wanted.items() if k in props}
        out["exporter_args"] = sorted(kwargs)
        out["exporter_skipped_args"] = sorted(set(wanted) - set(kwargs))
        enum = [i.identifier for i in bpy.ops.export_scene.gltf.get_rna_type().properties["export_vertex_color"].enum_items] if "export_vertex_color" in props else []
        out["vertex_color_modes"] = enum
        if "export_vertex_color" in kwargs and kwargs["export_vertex_color"] not in enum:
            kwargs["export_vertex_color"] = enum[0]
        result = bpy.ops.export_scene.gltf(**kwargs)
        out["export"] = str(result); out["selected"] = selected
        out["glb_bytes"] = os.path.getsize(GLB) if os.path.exists(GLB) else None
        for ob in scene.objects:
            ob.select_set(False)

        # Check render (Workbench, studio light): a front-ish view at Gateway lon 26°, lat 26°.
        cam_data = bpy.data.cameras.new("LEARNING_REVIEW_CAMERA"); cam = bpy.data.objects.new("LEARNING_REVIEW_CAMERA", cam_data)
        scene.collection.objects.link(cam)
        a, b = math.radians(26), math.radians(26)
        d_g = Vector((math.cos(b) * math.sin(a), math.sin(b), math.cos(b) * math.cos(a)))
        C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
        pos = C @ (d_g * 16.0)
        cam.location = pos
        cam.rotation_euler = (-pos).to_track_quat('-Z', 'Y').to_euler()
        cam_data.lens = 50
        scene.camera = cam
        engines = [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
        try:
            scene.render.engine = 'BLENDER_WORKBENCH'
        except TypeError as e:
            out["engine_error"] = str(e)[:200]
        scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'VERTEX'
        scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1280, 800, 100
        scene.render.image_settings.file_format = 'PNG'; scene.render.filepath = RENDER
        scene.render.film_transparent = False
        bpy.ops.render.render(write_still=True)
        out["render"] = os.path.exists(RENDER); out["engines"] = engines
        bpy.data.objects.remove(cam, do_unlink=True); bpy.data.cameras.remove(cam_data)
        scene.camera = None

        # Save the asset project as its own file. The live session keeps its own (unsaved) file and scene.
        if os.path.exists(BLEND):
            out["blend"] = "EXISTS - not overwritten"
        else:
            bpy.data.libraries.write(BLEND, {scene}, fake_user=True, compress=True)
            out["blend"] = os.path.getsize(BLEND)
            with bpy.data.libraries.load(BLEND, link=False) as (src, dst):
                out["blend_contents"] = dict(scenes=list(src.scenes), objects=len(src.objects), meshes=len(src.meshes), materials=list(src.materials), collections=list(src.collections))
                dst.scenes = []  # read-only listing; load nothing
    finally:
        bpy.context.window.scene = user_scene
    out["session_file"] = bpy.data.filepath; out["active_scene"] = bpy.context.window.scene.name
    print(json.dumps(out, indent=1))

try:
    main()
except Exception:
    print("EXPORT FAILED"); print(traceback.format_exc())
