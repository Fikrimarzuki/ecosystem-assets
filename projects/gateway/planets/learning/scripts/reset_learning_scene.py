"""Remove the LEARNING scene and every datablock it created from the live Blender session, so the build can be
re-run. Only data named for this asset is touched; the user's own scene and objects are never affected."""
import bpy

SCENE = globals().get("RESET_SCENE", "LEARNING")
PREFIXES = ("LEARNING_", "ACADEMY_", "BOOK_MONUMENT", "LIBRARY", "STUDY_PAVILION", "GARDEN_CLASSROOM", "ANCHOR_", "NAV_")
MATERIALS = ("LearningDiorama", "LearningAccent", "LearningNavigationReference")

scene = bpy.data.scenes.get(SCENE)
if scene is not None:
    if bpy.context.window.scene == scene:
        bpy.context.window.scene = next(s for s in bpy.data.scenes if s != scene)
    bpy.data.scenes.remove(scene)
for ob in [o for o in bpy.data.objects if o.name.startswith(PREFIXES)]:
    bpy.data.objects.remove(ob, do_unlink=True)
for me in [m for m in bpy.data.meshes if m.name.startswith(PREFIXES)]:
    bpy.data.meshes.remove(me)
for col in [c for c in bpy.data.collections if c.name.startswith("LEARNING_")]:
    bpy.data.collections.remove(col)
for mat in [m for m in bpy.data.materials if m.name.startswith(MATERIALS)]:
    bpy.data.materials.remove(mat)
print("reset done | scenes:", [s.name for s in bpy.data.scenes], "| objects:", sorted(o.name for o in bpy.data.objects))
