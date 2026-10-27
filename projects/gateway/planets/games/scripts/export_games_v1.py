"""Export Games v1 (M8.9b.3a): GLB (visual layers + anchors only; the navigation reference stays in the .blend), the .blend (written
as a separate file, never saving over the live session) and three EEVEE renders. Run through Blender MCP after build_games_v1.py."""
import bpy, os, json, math, traceback
from mathutils import Vector, Matrix

ROOT = r"D:\Code\porto-projects\gateway-assets\planets\games"
GLB = os.path.join(ROOT, "exports", "games-v1.glb")
BLEND = os.path.join(ROOT, "games-v1.blend")
EXPORT_COLLECTIONS = ("GAMES_TERRAIN", "GAMES_PATHS", "GAMES_BUILDINGS", "GAMES_DECORATIONS", "GAMES_ACCENTS", "GAMES_ANCHORS")
C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
def gdir(lon, lat):
    a, b = math.radians(lon), math.radians(lat); return Vector((math.cos(b) * math.sin(a), math.sin(b), math.cos(b) * math.cos(a)))
# (name, Gateway camera direction, distance, look-at point in Gateway space, lens)
VIEWS = [("three-quarter", gdir(26, 26), 19.0, Vector((0, 0.45, 0)), 50), ("opposite", gdir(168, -12), 19.0, Vector((0, 0.1, 0)), 50),
         ("landmark-castle", gdir(16, 40), 10.2, gdir(10, 60) * 4.95, 50)]

def main():
    scene = bpy.data.scenes["GAMES_V1"]; user_scene = bpy.context.window.scene; out = {}
    try:
        bpy.context.window.scene = scene
        for ob in scene.objects: ob.select_set(False)
        selected = []
        for name in EXPORT_COLLECTIONS:
            for ob in bpy.data.collections[name].objects: ob.select_set(True); selected.append(ob.name)
        props = bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
        wanted = dict(filepath=GLB, export_format='GLB', use_selection=True, use_active_scene=True, export_apply=True, export_yup=True,
                      export_extras=True, export_cameras=False, export_lights=False, export_animations=False, export_skins=False,
                      export_morph=False, export_texcoords=False, export_normals=True, export_materials='EXPORT',
                      export_vertex_color='ACTIVE', export_all_vertex_colors=False, export_active_vertex_color_when_no_material=True,
                      export_image_format='NONE', export_draco_mesh_compression_enable=False, export_hierarchy_full_collections=False)
        kwargs = {k: v for k, v in wanted.items() if k in props}
        enum = [i.identifier for i in bpy.ops.export_scene.gltf.get_rna_type().properties["export_vertex_color"].enum_items] if "export_vertex_color" in props else []
        if "export_vertex_color" in kwargs and kwargs["export_vertex_color"] not in enum: kwargs["export_vertex_color"] = enum[0]
        out["export"] = str(bpy.ops.export_scene.gltf(**kwargs)); out["selected"] = len(selected); out["glb_bytes"] = os.path.getsize(GLB)
        for ob in scene.objects: ob.select_set(False)
        # Renders: temporary camera, lights and world, removed afterwards (never exported, never saved).
        cam_data = bpy.data.cameras.new("_games_cam"); cam = bpy.data.objects.new("_games_cam", cam_data); scene.collection.objects.link(cam); scene.camera = cam
        lights = []
        for i, (loc, energy) in enumerate(([(9, -12, 14), 13000], [(-12, 6, 8), 5200], [(4, 12, -9), 4200], [(-6, 14, -12), 3600])):
            ld = bpy.data.lights.new(f"_games_light_{i}", 'POINT'); ld.energy = energy; ld.shadow_soft_size = 2.5
            lo = bpy.data.objects.new(ld.name, ld); lo.location = loc; scene.collection.objects.link(lo); lights.append(lo)
        try: scene.render.engine = 'BLENDER_EEVEE_NEXT'
        except TypeError: scene.render.engine = 'BLENDER_EEVEE'
        scene.render.resolution_x = 1280; scene.render.resolution_y = 900; scene.render.resolution_percentage = 100; scene.render.film_transparent = False
        world = bpy.data.worlds.get("_games_world") or bpy.data.worlds.new("_games_world"); world.use_nodes = True
        bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND"); bg.inputs[0].default_value = (0.035, 0.045, 0.075, 1); bg.inputs[1].default_value = 1.0
        scene.world = world
        for name, d, dist, look, lens in VIEWS:
            pos = C @ (d.normalized() * dist); target = C @ look
            cam.location = pos; cam.rotation_euler = (target - pos).to_track_quat('-Z', 'Y').to_euler(); cam_data.lens = lens
            scene.render.filepath = os.path.join(ROOT, "references", f"games-v1-{name}.png"); bpy.ops.render.render(write_still=True)
        for ob in [cam] + lights: bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.cameras.remove(cam_data); scene.camera = None
        for ld in [l for l in bpy.data.lights if l.name.startswith("_games_light")]: bpy.data.lights.remove(ld)
        bpy.data.worlds.remove(world); scene.world = None
        bpy.data.libraries.write(BLEND, {scene}, fake_user=True, compress=True); out["blend_bytes"] = os.path.getsize(BLEND)
    except Exception:
        out["error"] = traceback.format_exc()
    finally:
        bpy.context.window.scene = user_scene
    print(json.dumps(out))

main()
