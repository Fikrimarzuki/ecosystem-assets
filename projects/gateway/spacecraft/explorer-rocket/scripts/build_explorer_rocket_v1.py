"""Explorer Rocket Mk II (M8.9b.2f.1): a handcrafted low-poly Blender model, run through Blender MCP.

Visual foundation: Gateway's procedural Explorer Rocket (components/universe/rocket.tsx), kept inside its envelope so the GLB can
later replace it in place:
  Gateway axes (Y up): y -0.64..0.80, |x|,|z| <= 0.356, enclosing radius ~0.765; nozzle exit at y = -0.59 (the procedural flame
  cone hangs from there; the engine glow sits at y = -0.60); origin at the rocket's own origin (body centre line).
Blender is Z up; the glTF exporter converts (+Y up) on export, so Blender z == Gateway y and Blender (x, y) == Gateway (x, -z).
Everything is built into its own scene, EXPLORER_ROCKET; the user's open scenes are never touched. Rerunning rebuilds it.
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

SCENE = "EXPLORER_ROCKET"
COLLECTIONS = ["ROCKET_BODY", "ROCKET_NOSE", "ROCKET_FINS", "ROCKET_COCKPIT", "ROCKET_ENGINE", "ROCKET_ACCENTS", "ROCKET_ANCHORS"]

# Material palette (sRGB hex from the procedural rocket, with emission for the lit accents).
PALETTE = {
    "RocketHull":    dict(color="#dde5df", roughness=0.62, metallic=0.05),
    "RocketTeal":    dict(color="#3a9aa5", roughness=0.55, metallic=0.10),
    "RocketTealFin": dict(color="#2f8f9a", roughness=0.55, metallic=0.10),
    "RocketCollar":  dict(color="#c9d5d0", roughness=0.60, metallic=0.15),
    "RocketEngine":  dict(color="#3b4d5c", roughness=0.45, metallic=0.55),
    "RocketNozzle":  dict(color="#2a3646", roughness=0.40, metallic=0.70),
    "RocketGlass":   dict(color="#86e4ee", roughness=0.20, metallic=0.00, emission="#86e4ee", strength=1.2),
    "RocketAccent":  dict(color="#e0b25f", roughness=0.50, metallic=0.20),
    "RocketGlow":    dict(color="#8ff0f4", roughness=0.30, metallic=0.00, emission="#8ff0f4", strength=2.5),
}

def srgb(hex_color):
    h = hex_color.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c]

def material(name):
    mat = bpy.data.materials.get(name)
    if mat is None:
        spec = PALETTE[name]
        mat = bpy.data.materials.new(name); mat.use_nodes = True
        bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Base Color"].default_value = (*srgb(spec["color"]), 1)
        bsdf.inputs["Roughness"].default_value = spec["roughness"]
        bsdf.inputs["Metallic"].default_value = spec["metallic"]
        if "emission" in spec:
            bsdf.inputs["Emission Color"].default_value = (*srgb(spec["emission"]), 1)
            bsdf.inputs["Emission Strength"].default_value = spec["strength"]
        mat.diffuse_color = (*srgb(spec["color"]), 1)
    return mat

def reset_scene():
    old = bpy.data.scenes.get(SCENE)
    if old:
        for ob in list(old.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        for name in COLLECTIONS:
            col = bpy.data.collections.get(name)
            if col: bpy.data.collections.remove(col)
        bpy.data.scenes.remove(old)
    for mesh in [m for m in bpy.data.meshes if m.users == 0]: bpy.data.meshes.remove(mesh)
    scene = bpy.data.scenes.new(SCENE)
    cols = {}
    for name in COLLECTIONS:
        col = bpy.data.collections.new(name); scene.collection.children.link(col); cols[name] = col
    return scene, cols

def mesh_object(name, bm, collection, mat, smooth=False):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    for p in me.polygons: p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me); collection.objects.link(ob)
    return ob

# --- Profile-based lathe (Blender Z up). profile = [(radius, z), ...] bottom to top; segments around.
def lathe(name, profile, segments, collection, mat, cap_bottom=True, cap_top=True):
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r <= 1e-6:
            v = bm.verts.new((0, 0, z)); rings.append([v] * segments)
        else:
            ring = [bm.verts.new((r * math.cos(2 * math.pi * i / segments), r * math.sin(2 * math.pi * i / segments), z)) for i in range(segments)]
            rings.append(ring)
    bm.verts.ensure_lookup_table()
    for a, b in zip(rings, rings[1:]):
        for i in range(segments):
            quad = [a[i], a[(i + 1) % segments], b[(i + 1) % segments], b[i]]
            uniq = []
            for v in quad:
                if v not in uniq: uniq.append(v)
            if len(uniq) >= 3:
                try: bm.faces.new(uniq)
                except ValueError: pass
    if cap_bottom and len(set(rings[0])) > 1: bm.faces.new(list(reversed(rings[0])))
    if cap_top and len(set(rings[-1])) > 1: bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_object(name, bm, collection, mat)

def fin(name, angle_deg, collection, mat):
    """A swept stabilizer fin: a thin plate in the local XZ plane, rotated about Z to its station. Blender z = Gateway y.
    Outline (radial, z): root along the hull/engine, leading edge sweeping back, tip at (0.355, -0.52), trailing edge at the nozzle."""
    outline = [(0.17, -0.30), (0.33, -0.44), (0.355, -0.58), (0.30, -0.64), (0.215, -0.60), (0.155, -0.52)]
    bm = bmesh.new()
    t = 0.022
    front = [bm.verts.new((x, -t / 2, z)) for x, z in outline]
    back = [bm.verts.new((x, t / 2, z)) for x, z in outline]
    bm.faces.new(front); bm.faces.new(list(reversed(back)))
    n = len(outline)
    for i in range(n):
        bm.faces.new([front[i], back[i], back[(i + 1) % n], front[(i + 1) % n]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = mesh_object(name, bm, collection, mat)
    ob.rotation_euler = (0, 0, math.radians(angle_deg))
    return ob

def build():
    scene, cols = reset_scene()
    # BODY: a slightly tapered fuselage with a waist, 12 segments. Gateway y range of the hull: -0.30..0.46.
    lathe("ROCKET_HULL", [(0.14, -0.30), (0.165, -0.26), (0.17, -0.10), (0.17, 0.30), (0.16, 0.40), (0.15, 0.46)], 12, cols["ROCKET_BODY"], material("RocketHull"))
    lathe("ROCKET_BAND_UPPER", [(0.172, 0.165), (0.182, 0.175), (0.182, 0.235), (0.172, 0.245)], 12, cols["ROCKET_ACCENTS"], material("RocketTeal"))
    lathe("ROCKET_BAND_LOWER", [(0.172, -0.21), (0.182, -0.20), (0.182, -0.15), (0.172, -0.14)], 12, cols["ROCKET_ACCENTS"], material("RocketTeal"))
    lathe("ROCKET_COLLAR", [(0.15, 0.46), (0.158, 0.47), (0.158, 0.50), (0.14, 0.52)], 12, cols["ROCKET_BODY"], material("RocketCollar"))
    # NOSE: an ogive-ish cone to the tip at Gateway y 0.80.
    lathe("ROCKET_NOSE_CONE", [(0.14, 0.52), (0.125, 0.60), (0.095, 0.68), (0.055, 0.75), (0.0, 0.80)], 12, cols["ROCKET_NOSE"], material("RocketTeal"), cap_top=False)
    lathe("ROCKET_NOSE_TIP", [(0.0, 0.80), (0.012, 0.78)], 8, cols["ROCKET_NOSE"], material("RocketCollar"), cap_bottom=False, cap_top=False)
    # COCKPIT: a rimmed round window on the -Y (Blender) side, which is Gateway +z (the side the inspection camera sees).
    rim = lathe("ROCKET_COCKPIT_RIM", [(0.0, 0.0), (0.075, 0.0), (0.075, 0.03), (0.0, 0.03)], 10, cols["ROCKET_COCKPIT"], material("RocketEngine"))
    rim.rotation_euler = (math.radians(90), 0, 0); rim.location = (0, -0.158, 0.115)
    glass = lathe("ROCKET_COCKPIT_GLASS", [(0.0, 0.0), (0.05, 0.0), (0.05, 0.02), (0.0, 0.02)], 10, cols["ROCKET_COCKPIT"], material("RocketGlass"))
    glass.rotation_euler = (math.radians(90), 0, 0); glass.location = (0, -0.172, 0.115)
    # ACCENTS: a warm dorsal strip on the far side, and two small lit markers on the fins' stations.
    strip = lathe("ROCKET_DORSAL_STRIP", [(0, 0), (0.016, 0), (0.016, 0.34), (0, 0.34)], 6, cols["ROCKET_ACCENTS"], material("RocketAccent"))
    strip.location = (0, 0.168, -0.17)
    for i, ang in enumerate((45, 225)):
        m = lathe(f"ROCKET_MARKER_{i+1}", [(0, 0), (0.014, 0), (0.014, 0.012), (0, 0.012)], 6, cols["ROCKET_ACCENTS"], material("RocketGlow"))
        m.rotation_euler = (0, math.radians(90), math.radians(ang)); m.location = (0.17 * math.cos(math.radians(ang)), 0.17 * math.sin(math.radians(ang)), 0.33)
    # ENGINE: housing, bell nozzle (exit at Gateway y -0.59) and the glowing core ring just inside the bell.
    lathe("ROCKET_ENGINE_HOUSING", [(0.14, -0.30), (0.135, -0.33), (0.135, -0.42), (0.12, -0.45)], 12, cols["ROCKET_ENGINE"], material("RocketEngine"), cap_top=False)
    lathe("ROCKET_NOZZLE", [(0.12, -0.45), (0.10, -0.47), (0.105, -0.52), (0.13, -0.57), (0.14, -0.59), (0.125, -0.59), (0.095, -0.55), (0.09, -0.49), (0.0, -0.49)], 12, cols["ROCKET_ENGINE"], material("RocketNozzle"), cap_bottom=False, cap_top=False)
    lathe("ROCKET_CORE_RING", [(0.07, -0.555), (0.095, -0.555), (0.095, -0.545), (0.07, -0.545)], 12, cols["ROCKET_ENGINE"], material("RocketGlow"))
    # FINS: four swept fins at 0/90/180/270 (Gateway ±x and ±z), matching the procedural fins' stations.
    for i, ang in enumerate((0, 90, 180, 270)):
        fin(f"ROCKET_FIN_{i+1}", ang, cols["ROCKET_FINS"], material("RocketTealFin"))
    # ANCHORS: empties exported as named nodes with extras. The engine anchor is the flame/glow attachment point (y -0.59).
    def anchor(name, loc, role, **extra):
        e = bpy.data.objects.new(name, None); e.empty_display_type = "PLAIN_AXES"; e.empty_display_size = 0.05
        e.location = loc; e["role"] = role
        for k, v in extra.items(): e[k] = v
        cols["ROCKET_ANCHORS"].objects.link(e); return e
    anchor("ANCHOR_engine", (0, 0, -0.59), "engine", attachment="flame-and-glow", direction="-y")
    anchor("ANCHOR_nose", (0, 0, 0.80), "nose")
    anchor("ANCHOR_cockpit", (0, -0.172, 0.115), "cockpit")
    for ob in scene.objects:
        if ob.type == "MESH": ob["rocket_part"] = ob.users_collection[0].name
    return scene

scene = build()
# Report the Gateway-space envelope (Blender z -> Gateway y; Blender y -> Gateway -z).
pts = []
for ob in scene.objects:
    if ob.type == "MESH":
        pts += [ob.matrix_world @ v.co for v in ob.data.vertices]
xs = [p.x for p in pts]; ys = [p.z for p in pts]; zs = [-p.y for p in pts]
reach = max(p.length for p in pts)
tris = sum(sum(len(poly.vertices) - 2 for poly in ob.data.polygons) for ob in scene.objects if ob.type == "MESH")
print({"meshes": sum(1 for o in scene.objects if o.type == "MESH"), "anchors": sum(1 for o in scene.objects if o.type == "EMPTY"),
       "triangles": tris, "materials": len({m.name for o in scene.objects if o.type == "MESH" for m in o.data.materials}),
       "gateway_y": (round(min(ys), 4), round(max(ys), 4)), "gateway_x": (round(min(xs), 4), round(max(xs), 4)), "gateway_z": (round(min(zs), 4), round(max(zs), 4)), "reach": round(reach, 4)})
