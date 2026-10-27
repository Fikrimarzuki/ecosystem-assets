"""Export Explorer Rocket Mk II (M8.9b.2f.1): GLB (meshes + anchors only), the .blend (written as a separate file, never saving over
the live session), and three EEVEE renders. Run through Blender MCP after build_explorer_rocket_v1.py."""
import bpy, os, json, math, traceback
from mathutils import Vector

ROOT = r"D:\Code\porto-projects\gateway-assets\spacecraft\explorer-rocket"
GLB = os.path.join(ROOT, "exports", "explorer-rocket-v1.glb")
BLEND = os.path.join(ROOT, "explorer-rocket-v1.blend")
RENDERS = {"front-three-quarter": (1.5, -2.6, 0.9), "side": (3.1, 0.0, 0.1), "engine-rear": (0.9, -1.5, -2.5)}
COLLECTIONS = ["ROCKET_BODY", "ROCKET_NOSE", "ROCKET_FINS", "ROCKET_COCKPIT", "ROCKET_ENGINE", "ROCKET_ACCENTS", "ROCKET_ANCHORS"]

def main():
    scene = bpy.data.scenes["EXPLORER_ROCKET"]
    user_scene = bpy.context.window.scene
    out = {}
    try:
        bpy.context.window.scene = scene
        for ob in scene.objects: ob.select_set(False)
        selected = []
        for name in COLLECTIONS:
            for ob in bpy.data.collections[name].objects:
                ob.select_set(True); selected.append(ob.name)
        props = bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
        wanted = dict(filepath=GLB, export_format='GLB', use_selection=True, use_active_scene=True, export_apply=True, export_yup=True,
                      export_extras=True, export_cameras=False, export_lights=False, export_animations=False, export_skins=False,
                      export_morph=False, export_texcoords=False, export_normals=True, export_materials='EXPORT',
                      export_image_format='NONE', export_draco_mesh_compression_enable=False, export_hierarchy_full_collections=False)
        kwargs = {k: v for k, v in wanted.items() if k in props}
        out["exporter_skipped_args"] = sorted(set(wanted) - set(kwargs))
        out["export"] = str(bpy.ops.export_scene.gltf(**kwargs)); out["selected"] = selected
        out["glb_bytes"] = os.path.getsize(GLB)
        # Renders: a temporary camera and lights, removed again afterwards (never part of the export or the saved scene).
        cam_data = bpy.data.cameras.new("_rocket_render_cam"); cam = bpy.data.objects.new("_rocket_render_cam", cam_data)
        scene.collection.objects.link(cam); scene.camera = cam; cam_data.lens = 50
        lights = []
        for i, (loc, energy) in enumerate(([(2, -2, 3), 600], [(-2.5, 1.5, 1.5), 250], [(0.5, 2.5, -1.5), 180])):
            ld = bpy.data.lights.new(f"_rocket_render_light_{i}", 'POINT'); ld.energy = energy
            lo = bpy.data.objects.new(ld.name, ld); lo.location = loc; scene.collection.objects.link(lo); lights.append(lo)
        try: scene.render.engine = 'BLENDER_EEVEE_NEXT'
        except TypeError: scene.render.engine = 'BLENDER_EEVEE'
        scene.render.resolution_x = 900; scene.render.resolution_y = 900; scene.render.resolution_percentage = 100
        scene.render.film_transparent = False
        world = bpy.data.worlds.get("_rocket_render_world") or bpy.data.worlds.new("_rocket_render_world"); world.use_nodes = True
        bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND"); bg.inputs[0].default_value = (0.04, 0.05, 0.08, 1); bg.inputs[1].default_value = 1.0
        scene.world = world
        for name, loc in RENDERS.items():
            cam.location = loc
            direction = Vector((0, 0, 0.08)) - Vector(loc)
            cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
            scene.render.filepath = os.path.join(ROOT, "references", f"explorer-rocket-v1-{name}.png")
            bpy.ops.render.render(write_still=True)
        for ob in [cam] + lights: bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.cameras.remove(cam_data); scene.camera = None
        for ld in [l for l in bpy.data.lights if l.name.startswith("_rocket_render_light")]: bpy.data.lights.remove(ld)
        # Save the rocket scene (and everything it references) as its own .blend, leaving the live session file untouched.
        bpy.data.libraries.write(BLEND, {scene}, fake_user=True, compress=True)
        out["blend_bytes"] = os.path.getsize(BLEND)
    except Exception:
        out["error"] = traceback.format_exc()
    finally:
        bpy.context.window.scene = user_scene
    print(json.dumps(out))

main()
