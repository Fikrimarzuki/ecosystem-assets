"""M8.9b.1a.3 — Blender Academy Town v2 (Learning planet), run inside the live Blender through Blender MCP.

Builds a dedicated scene "LEARNING" (never touching the user's own scene), authored in Gateway's local
space: Y up, radius 4.2 local units (14 astronaut heights), longitude from +Z toward +X. Vertices are
converted to Blender's Z-up at creation, and the glTF exporter (+Y up) converts them back, so the GLB
loads in Gateway coordinates with the planet centre at the origin.

Layers (separate collections):
  LEARNING_VISUAL                 terrain (relief sphere), path ribbons, plaza and pond paving
  LEARNING_BUILDINGS              academy hall, academy tower, book monument (one object each, origin at the base)
  LEARNING_PATHS                  (ribbons/paving are part of VISUAL as one batch; the walkable widths live in NAVIGATION)
  LEARNING_DECORATIONS            merged static scenery (trees, shrubs, rocks, reeds, terraces, accent bases)
  LEARNING_ACCENTS                merged restrained glowing accents (book pages, crystal, terminal screen)
  LEARNING_ANCHORS                empties: interactions, landing, spawn, lander arrival, mini-game candidate
  LEARNING_NAVIGATION_REFERENCE   navigation surface (terraces + berms, no decoration), route centrelines,
                                  obstacle footprints, landing circle — kept in the .blend, not exported

No walking, gravity, motion or mini-game is implemented. No private project data is stored.
"""
import bpy, bmesh, math, json, os, colorsys, traceback
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = r"D:\Code\porto-projects\gateway-assets\planets\learning"
SCENE_NAME = "LEARNING_V2"
R = 4.2                      # 14 h
H, RAD = 0.30, 0.05          # astronaut capsule height / radius (local)
KERB, EMBED, TERRACE_SINK, PAVING_LIFT, DESIGN_SLOPE = 0.015, 0.05, 0.01, 0.008, 12.0
PRIMARY, SECONDARY, LANDING_CLEAR = 8 * RAD, 6 * RAD, 6 * RAD
TERRAIN_SUBDIV = 5           # bmesh icosphere: 20 × 4^(n−1) faces → 5,120
NAV_SUBDIV = 4               # 1,280 faces (reference only)

# Gateway (x, y, z; Y up) -> Blender (x, -z, y; Z up). The glTF +Y-up export inverts this exactly.
C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
C4 = C.to_4x4()
C4i = C4.inverted()

PALETTE = dict(
    meadow="#7b8f5c", meadowLight="#99a266", meadowDeep="#687d4f", lawn="#a2a766", grove="#62774b", heath="#ad9862",
    earth="#8e7553", rockGround="#887d6c", sand="#cdb98a", path="#cdbd93", pathAlt="#c4b389", kerb="#9d8a66",
    plaza="#d6c69d", inlay="#b49e72", landing="#c2ab7e", sandstone="#c7a571", sandstoneDark="#a3845a", water="#6f9fad",
    trunk="#74614b", foliage="#6f8456", foliageWarm="#8e9a5c", foliageOlive="#a4a067", rock="#9a9180", rockDark="#857d70",
    reed="#8c9a5a", page="#f5e8c8", crystal="#8fd1c7", screen="#a6dccf", banner="#3f5e7a", cover="#87493a", slate="#58666c",
    ivory="#efe2c4", terracotta="#a5583f", wall="#e1d5b6", hallRoof="#9f6653", hallRoofTop="#b98165", column="#f0e2c4",
    window="#665b51", towerWall="#d2bd99", towerRoof="#945746", towerRoofTop="#a96c52", pedestal="#887857", book="#f0e2bf",
    door="#5a4636", screenBack="#46545a", hand="#5d4a3e",
)

SITES = {
    "hall": (22, 66, None), "plaza": (72, 34, None), "tower": (124, 60, "plaza"), "marker": (206, 49, None),
    "pond": (236, 12, None), "grove-far": (170, 16, None), "orchard": (300, 18, None), "meadow-north": (318, 54, None),
    "rocks-south": (150, -24, None), "heath-south": (40, -30, None), "rocks-west": (266, -22, None),
    "shrubs-south": (330, -40, None), "garden-front": (8, 6, None), "rocks-front": (56, -16, None),
}
HILLS = [(176, -16, .24, 1.0), (296, -24, .2, .9), (52, -40, .2, .9), (330, 64, .12, .6), (200, 76, .1, .55),
         (104, -8, .14, .75), (345, -2, .12, .7), (20, -64, -.07, .8)]

# ----------------------------------------------------------------------------- maths helpers (Gateway space)
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_lin(h):
    h = h.lstrip("#")
    return [srgb_to_linear(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)]

def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return [a[i] + (b[i] - a[i]) * t for i in range(3)]

def offset_l(c, dl):
    h, l, s = colorsys.rgb_to_hls(*[max(0.0, min(1.0, x)) for x in c])
    return list(colorsys.hls_to_rgb(h, max(0.0, min(1.0, l + dl)), s))

def smooth(x):
    t = max(0.0, min(1.0, x))
    return t * t * (3 - 2 * t)

def direction(lon, lat):
    a, b = math.radians(lon), math.radians(lat)
    return Vector((math.cos(b) * math.sin(a), math.sin(b), math.cos(b) * math.cos(a)))

def plane_height(top, theta):
    return (R + top) / math.cos(theta) - R

def angle(a, b):
    d = max(-1.0, min(1.0, a.normalized().dot(b.normalized())))
    return math.acos(d)

def arc(a, b):
    return R * angle(a, b)

def south(n):
    return -(Vector((0, 1, 0)) - n * n.y)

class Frame:
    def __init__(self, up, radius, hint):
        n = up.normalized()
        f = hint - n * hint.dot(n)
        if f.length_squared < 1e-10:
            f = Vector((0, 0, 1)) - n * n.z
        f.normalize()
        self.up, self.forward, self.right = n, f, n.cross(f).normalized()
        self.origin = n * radius
    def offset_dir(self, x, z):
        return (self.up * R + self.right * x + self.forward * z).normalized()
    def basis(self):   # columns right, up, forward (as three's makeBasis)
        m = Matrix.Identity(4)
        for i in range(3):
            m[i][0], m[i][1], m[i][2] = self.right[i], self.up[i], self.forward[i]
        return m
    def world(self):   # Gateway-space transform of a local part set
        return Matrix.Translation(self.origin) @ self.basis()

def toward(frm, to, distance):
    axis = frm.cross(to)
    if axis.length < 1e-9:
        return frm.normalized()
    axis.normalize()
    return (Matrix.Rotation(distance / R, 3, axis) @ frm).normalized()

def three_euler(rot):   # three.js XYZ order == Blender 'ZYX' order
    from mathutils import Euler
    return Euler(rot, 'ZYX').to_matrix().to_4x4()

def part_matrix(pos, size, rot=(0, 0, 0)):
    return Matrix.Translation(Vector(pos)) @ three_euler(rot) @ Matrix.Diagonal(Vector(size)).to_4x4()

# ----------------------------------------------------------------------------- mesh building (vertex coloured)
def octahedron_verts_faces():
    v = [(0.5, 0, 0), (-0.5, 0, 0), (0, 0.5, 0), (0, -0.5, 0), (0, 0, 0.5), (0, 0, -0.5)]
    f = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
    return v, f

def torus_verts_faces(radius=0.5, tube=0.035, radial=5, tubular=24):   # in the XY plane (three TorusGeometry)
    verts, faces = [], []
    for j in range(radial):
        for i in range(tubular):
            u, v = i / tubular * 2 * math.pi, j / radial * 2 * math.pi
            verts.append(((radius + tube * math.cos(v)) * math.cos(u), (radius + tube * math.cos(v)) * math.sin(u), tube * math.sin(v)))
    for j in range(radial):
        for i in range(tubular):
            a = j * tubular + i; b = j * tubular + (i + 1) % tubular
            c = ((j + 1) % radial) * tubular + (i + 1) % tubular; d = ((j + 1) % radial) * tubular + i
            faces.append((a, b, c, d))
    return verts, faces

class Builder:
    """Accumulates vertex-coloured parts into one bmesh. Part coordinates are Gateway space (unit shapes as in
    three.js: boxes 1³, cylinders/cones along +Y, spheres/octahedra radius 0.5, torus in XZ)."""
    def __init__(self):
        self.bm = bmesh.new()
        self.col = self.bm.loops.layers.float_color.new("Col")
    def _add(self, verts, faces, matrix_g, color):
        # matrix_g: Gateway world transform of the unit shape (given in Gateway axes, Y up).
        m = C4 @ matrix_g
        lin = hex_lin(color) if isinstance(color, str) else list(color)
        start = len(self.bm.verts)
        bverts = [self.bm.verts.new(m @ Vector(v)) for v in verts]
        self.bm.verts.ensure_lookup_table()
        for f in faces:
            try:
                face = self.bm.faces.new([bverts[i] for i in f])
            except ValueError:
                continue
            face.smooth = False
            for loop in face.loops:
                loop[self.col] = (lin[0], lin[1], lin[2], 1.0)
        # Fix winding for negative-determinant transforms (none expected) and recalc normals at the end.
    def box(self, pos, size, color, rot=(0, 0, 0), world=Matrix.Identity(4)):
        v = [(x, y, z) for x in (-.5, .5) for y in (-.5, .5) for z in (-.5, .5)]
        f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        self._add(v, f, world @ part_matrix(pos, size, rot), color)
    def cylinder(self, pos, size, color, rot=(0, 0, 0), segments=10, top=0.5, world=Matrix.Identity(4)):
        # Cylinder/cone along +Y with radius 0.5 at the base and `top` at the top (0 = cone).
        v, f = [], []
        for i in range(segments):
            a = i / segments * 2 * math.pi
            v.append((0.5 * math.cos(a), -0.5, 0.5 * math.sin(a)))
        if top > 0:
            for i in range(segments):
                a = i / segments * 2 * math.pi
                v.append((top * math.cos(a), 0.5, top * math.sin(a)))
            for i in range(segments):
                f.append((i, (i + 1) % segments, segments + (i + 1) % segments, segments + i))
            f.append(tuple(reversed(range(segments))))            # bottom cap
            f.append(tuple(range(segments, 2 * segments)))        # top cap
        else:
            v.append((0, 0.5, 0))
            for i in range(segments):
                f.append((i, (i + 1) % segments, segments))
            f.append(tuple(reversed(range(segments))))
        self._add(v, f, world @ part_matrix(pos, size, rot), color)
    def cone(self, pos, size, color, rot=(0, 0, 0), segments=7, world=Matrix.Identity(4)):
        self.cylinder(pos, size, color, rot, segments, 0.0, world)
    def rock(self, pos, size, color, rot=(0, 0, 0), world=Matrix.Identity(4)):
        v, f = octahedron_verts_faces()
        self._add(v, f, world @ part_matrix(pos, size, rot), color)
    def sphere(self, pos, size, color, world=Matrix.Identity(4)):
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.5)
        v = [tuple(x.co) for x in bm.verts]; f = [tuple(l.vert.index for l in face.loops) for face in bm.faces]
        bm.free()
        # bmesh uv sphere is Z-up; rotate so the poles sit on Y (Gateway up).
        self._add(v, f, world @ part_matrix(pos, size) @ Matrix.Rotation(-math.pi / 2, 4, 'X'), color)
    def ring(self, pos, size, color, rot=(0, 0, 0), world=Matrix.Identity(4)):
        v, f = torus_verts_faces()
        self._add(v, f, world @ part_matrix(pos, size, rot), color)
    def quads(self, quads, lift_normal=True):
        # quads: list of ([p0, p1, p2, p3] Gateway world points, color-linear)
        for pts, color in quads:
            bverts = [self.bm.verts.new(C @ p) for p in pts]
            try:
                face = self.bm.faces.new(bverts)
            except ValueError:
                continue
            face.smooth = False
            for loop in face.loops:
                loop[self.col] = (color[0], color[1], color[2], 1.0)
    def to_object(self, name, collection, material, matrix_world=None):
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-6)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me); self.bm.free()
        for p in me.polygons:
            p.use_smooth = False
        me.color_attributes.active_color_index = 0
        me.color_attributes.render_color_index = 0
        me.materials.append(material)
        ob = bpy.data.objects.new(name, me)
        if matrix_world is not None:
            ob.matrix_world = matrix_world
        collection.objects.link(ob)
        return ob

def diorama_material(name, emissive=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    attr = nodes.new("ShaderNodeVertexColor"); attr.layer_name = "Col"; attr.location = (-300, 0)
    links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.82
    bsdf.inputs["Metallic"].default_value = 0.08
    if emissive:
        c = hex_lin(emissive)
        bsdf.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1.0)
        bsdf.inputs["Emission Strength"].default_value = 0.28
    return mat

# ----------------------------------------------------------------------------- v2 layout: Hybrid Academy Town
PALETTE.update(cobble="#bfa77e", cobbleDark="#a48c64", wood="#8a6a48", stoneWall="#9e9080", wallWarm="#e6d6b4",
               flowerA="#d2a94f", flowerB="#c06d60", flowerC="#e8d7a6", hedge="#5f7a4a", lantern="#f6e3b0",
               highland="#8f8c70", olive="#8e955c", coolGreen="#6f8d5e")
PLATEAU, PLATEAU_BLEND = 0.03, 0.35       # courtyards follow the sphere: a low raise with a soft berm (no cut, no kerb, no step)
SITES = {
    "hall": (16, 66, None), "plaza": (72, 34, None), "tower": (124, 58, "plaza"),
    "library": (38, 20, "plaza"), "pavilion": (75, 6, "plaza"), "classroom": (148, 38, "tower"),
    "marker": (206, 49, None), "pond": (236, 12, None), "highland": (176, 26, None), "ruin": (200, 67, None),
    "grove-far": (160, 8, None), "orchard": (300, 15, None), "meadow-north": (280, 72, None),
    "rocks-south": (150, -24, None), "heath-south": (40, -30, None), "rocks-west": (266, -22, None),
    "shrubs-south": (330, -40, None), "garden-front": (8, 8, None), "rocks-front": (56, -16, None), "glade-west": (284, 48, None),
}
HILLS = [(176, 26, .34, 1.1), (296, -22, .22, .95), (52, -40, .2, .9), (330, 66, .14, .6), (200, 78, .12, .55),
         (104, -8, .16, .75), (345, -2, .14, .7), (20, -64, -.08, .8), (255, 40, .12, .6), (130, 10, .1, .6)]
# Routes as waypoint polylines (lon, lat) smoothed on the sphere. `serves` lists the obstacles each route ends at.
ROUTES = [
    dict(id="town-road", width=PRIMARY, serves=["academy-hall", "academy-tower"],
         points=[(18, 50), (30, 44), (44, 38), (58, 35), (72, 34), (86, 35), (100, 40), (112, 46), (124, 50)]),
    dict(id="scenic-trail", width=SECONDARY, serves=["academy-tower", "discovery-marker", "pond", "academy-hall"],
         points=[(132, 52), (148, 54), (166, 54), (184, 53), (206, 49), (218, 36), (230, 22), (248, 18), (268, 22), (290, 30), (312, 40), (336, 46), (356, 50), (10, 50)]),
    dict(id="library-lane", width=SECONDARY, serves=["library"], points=[(44, 38), (42, 33), (40.5, 28.5)]),
    dict(id="pavilion-lane", width=SECONDARY, serves=["pavilion"], points=[(72, 34), (74, 24), (75, 16)]),
    dict(id="classroom-lane", width=SECONDARY, serves=["classroom", "academy-tower"], points=[(124, 50), (134, 45), (141, 42)]),
]

def chaikin_sphere(points, iterations=3):
    pts = [direction(a, b) for a, b in points]
    for _ in range(iterations):
        out = [pts[0]]
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            out.append((a * 0.75 + b * 0.25).normalized()); out.append((a * 0.25 + b * 0.75).normalized())
        out.append(pts[-1]); pts = out
    return pts

def resample(dirs, spacing=0.1):
    out = [dirs[0]]; carry = 0.0
    for i in range(1, len(dirs)):
        a, b = dirs[i - 1], dirs[i]; seg = arc(a, b)
        if seg < 1e-9: continue
        t = spacing - carry
        while t <= seg:
            out.append(toward(a, b, t)); t += spacing
        carry = seg - (t - spacing)
    if arc(out[-1], dirs[-1]) > spacing * 0.3: out.append(dirs[-1])
    return out

def build():
    report = {"skipped": [], "notes": []}
    if bpy.data.scenes.get(SCENE_NAME):
        raise RuntimeError(f"Scene {SCENE_NAME} already exists in this Blender session; stop (not overwriting).")
    scene = bpy.data.scenes.new(SCENE_NAME)
    cols = {}
    for name in ["LEARNING_VISUAL", "LEARNING_BUILDINGS", "LEARNING_PATHS", "LEARNING_DECORATIONS", "LEARNING_ACCENTS",
                 "LEARNING_ANCHORS", "LEARNING_NAVIGATION_REFERENCE"]:
        col = bpy.data.collections.new(name); scene.collection.children.link(col); cols[name] = col
    mat = diorama_material("LearningDiorama"); mat_accent = diorama_material("LearningAccent", emissive="#fff1d6")
    site_dir = {k: direction(v[0], v[1]) for k, v in SITES.items()}
    def site_frame(k, radius=R):
        lon, lat, tw = SITES[k]; n = site_dir[k]
        return Frame(n, radius, site_dir[tw] if tw else south(n))
    P = PALETTE

    # ---- building recipes (Gateway-local; base at y = 0 on the courtyard; foundations reach below the ground)
    def hall_parts(b, w):
        b.box((0, -.07, .02), (2.0, .34, .9), P["sandstoneDark"], world=w)                    # foundation (hides curvature)
        b.box((0, .05, 0), (1.26, .1, .76), P["sandstone"], world=w)                           # plinth course
        b.box((0, .42, 0), (1.2, .74, .7), P["wallWarm"], world=w)                             # main body
        for sx in (-1, 1):
            b.box((sx * .78, .27, .04), (.36, .54, .58), P["wall"], world=w)                   # wings
            b.box((sx * .78, .57, .04), (.44, .06, .66), P["hallRoof"], world=w)
            b.cone((sx * .78, .71, .04), (.52, .22, .74), P["hallRoofTop"], rot=(0, math.pi / 4, 0), segments=4, world=w)
            b.box((sx * .78, .3, .335), (.16, .2, .02), P["window"], world=w)
            b.box((sx * .615, .5, 0), (.02, .2, .4), P["window"], world=w)
        b.box((0, .82, 0), (1.3, .07, .8), P["hallRoof"], world=w)                             # main roof
        b.cone((0, 1.06, 0), (1.6, .42, 1.08), P["hallRoofTop"], rot=(0, math.pi / 4, 0), segments=4, world=w)
        b.box((0, 1.0, -.04), (.46, .34, .42), P["wallWarm"], world=w)                         # raised nave
        b.cone((0, 1.29, -.04), (.6, .26, .56), P["hallRoofTop"], rot=(0, math.pi / 4, 0), segments=4, world=w)
        b.box((0, 1.47, -.04), (.14, .14, .14), P["ivory"], world=w)                           # bell cupola
        b.cone((0, 1.61, -.04), (.2, .14, .2), P["terracotta"], segments=6, world=w)
        for x in (-.5, -.18, .18, .5):
            b.cylinder((x, .35, .47), (.09, .6, .09), P["column"], world=w)                    # portico
        b.box((0, .685, .47), (1.04, .07, .18), P["ivory"], world=w)
        b.cone((0, .78, .47), (1.0, .14, .22), P["ivory"], rot=(0, math.pi / 4, 0), segments=4, world=w)   # pediment
        b.ring((0, .76, .585), (.1, .1, .1), P["cobbleDark"], rot=(math.pi / 2, 0, 0), world=w)             # emblem ring
        b.box((0, .2, .355), (.26, .4, .02), P["door"], world=w)                               # arched entrance
        b.cylinder((0, .4, .355), (.26, .02, .26), P["door"], rot=(math.pi / 2, 0, 0), segments=12, world=w)
        for sx in (-1, 1):
            b.box((sx * .62, .4, .36), (.09, .34, .015), P["banner"], world=w)
        b.box((0, -.03, .56), (.92, .16, .32), P["sandstoneDark"], world=w)                   # step base
        for i in range(3):
            b.box((0, .04 + i * .055, .64 - i * .1), (.9, .08, .14), P["ivory"], world=w)
    def tower_parts(b, w):
        b.box((0, -.07, 0), (.56, .3, .58), P["sandstoneDark"], world=w)
        b.box((0, .05, 0), (.46, .1, .48), P["sandstone"], world=w)
        b.box((0, .62, 0), (.38, 1.2, .4), P["towerWall"], world=w)
        b.box((0, .64, 0), (.42, .04, .44), P["ivory"], world=w)
        b.box((0, .2, .205), (.14, .3, .02), P["door"], world=w)
        b.cylinder((0, .35, .205), (.14, .02, .14), P["door"], rot=(math.pi / 2, 0, 0), segments=10, world=w)
        for y in (.5, .85): b.box((0, y, .206), (.12, .18, .02), P["window"], world=w)
        b.ring((0, 1.08, .206), (.18, .18, .18), P["ivory"], rot=(math.pi / 2, 0, 0), world=w)   # clock
        b.box((0, 1.08, .21), (.04, .04, .01), P["hand"], world=w)
        b.box((0, 1.24, 0), (.52, .05, .54), P["ivory"], world=w)                               # balcony
        for sx in (-1, 1):
            for sz in (-1, 1): b.box((sx * .23, 1.32, sz * .24), (.04, .12, .04), P["ivory"], world=w)
        b.cylinder((0, 1.44, 0), (.34, .36, .34), P["wallWarm"], segments=8, world=w)          # observatory lantern
        for a in (0, math.pi / 2, math.pi, -math.pi / 2):
            b.box((math.sin(a) * .165, 1.46, math.cos(a) * .165), (.1, .14, .02), P["window"], rot=(0, a, 0), world=w)
        b.sphere((0, 1.63, 0), (.4, .26, .4), P["towerRoofTop"], world=w)                     # dome
        b.cone((0, 1.84, 0), (.1, .2, .1), P["ivory"], segments=6, world=w)
        b.sphere((0, 1.96, 0), (.05, .05, .05), P["ivory"], world=w)
    def monument_parts(b, w):
        b.cylinder((0, .13, 0), (.4, .26, .4), P["pedestal"], world=w)
        b.box((-.11, .32, 0), (.23, .045, .3), P["book"], rot=(0, 0, -.22), world=w)
        b.box((.11, .32, 0), (.23, .045, .3), P["book"], rot=(0, 0, .22), world=w)
    def library_parts(b, w):
        b.cylinder((0, -.07, 0), (.84, .3, .84), P["sandstoneDark"], segments=8, world=w)
        b.cylinder((0, .3, 0), (.7, .6, .7), P["wall"], segments=8, world=w)
        b.box((0, .6, 0), (.74, .05, .74), P["hallRoof"], rot=(0, math.pi / 8, 0), world=w)
        b.sphere((0, .62, 0), (.74, .46, .74), P["hallRoofTop"], world=w)                    # dome
        b.cylinder((0, .88, 0), (.14, .12, .14), P["ivory"], segments=6, world=w)
        for x in (-.16, .16): b.cylinder((x, .25, .42), (.07, .5, .07), P["column"], world=w)
        b.box((0, .52, .42), (.5, .05, .14), P["ivory"], world=w)
        b.cone((0, .59, .42), (.48, .1, .18), P["ivory"], rot=(0, math.pi / 4, 0), segments=4, world=w)
        b.box((0, .16, .355), (.16, .32, .02), P["door"], world=w)
        for a in (math.pi / 2, math.pi, -math.pi / 2):
            b.box((math.sin(a) * .35, .36, math.cos(a) * .35), (.1, .18, .02), P["window"], rot=(0, a, 0), world=w)
    def pavilion_parts(b, w):
        b.cylinder((0, -.05, 0), (.8, .24, .8), P["sandstoneDark"], segments=8, world=w)
        b.cylinder((0, .03, 0), (.72, .06, .72), P["cobble"], segments=8, world=w)
        for sx in (-1, 1):
            for sz in (-1, 1): b.cylinder((sx * .24, .32, sz * .24), (.08, .58, .08), P["column"], world=w)
        b.box((0, .63, 0), (.66, .05, .66), P["hallRoof"], world=w)
        b.cone((0, .78, 0), (.78, .26, .78), P["hallRoofTop"], rot=(0, math.pi / 4, 0), segments=4, world=w)
        b.sphere((0, .93, 0), (.06, .06, .06), P["ivory"], world=w)
        b.box((0, .2, 0), (.22, .05, .16), P["wood"], world=w)                                  # reading table
        b.box((0, .12, 0), (.04, .12, .04), P["wood"], world=w)
        b.box((0, .235, 0), (.12, .02, .09), P["page"], rot=(0, .3, 0), world=w)
    def classroom_parts(b, w):
        b.box((0, -.07, 0), (.66, .3, .56), P["sandstoneDark"], world=w)
        b.box((0, .26, 0), (.52, .52, .42), P["towerWall"], world=w)
        b.box((0, .6, 0), (.44, .44, .5), P["hallRoofTop"], rot=(0, 0, math.pi / 4), world=w)   # gable roof
        b.box((.16, .8, -.08), (.08, .22, .08), P["sandstoneDark"], world=w)                    # chimney
        b.box((-.08, .16, .215), (.12, .3, .02), P["door"], world=w)
        b.box((.12, .3, .215), (.12, .14, .02), P["window"], world=w)
        b.box((-.265, .3, 0), (.02, .14, .18), P["window"], world=w)

    def measure(parts_fn):
        b = Builder(); parts_fn(b, Matrix.Identity(4))
        xs = [v.co.x for v in b.bm.verts]; ys = [v.co.z for v in b.bm.verts]; zs = [-v.co.y for v in b.bm.verts]
        b.bm.free()
        cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
        return dict(cx=cx, cz=cz, footprint=math.hypot((max(xs) - min(xs)) / 2, (max(zs) - min(zs)) / 2), height=max(ys))
    recipes = {"academy-hall": hall_parts, "academy-tower": tower_parts, "book-monument": monument_parts, "library": lambda b, w: library_parts(b, w @ Matrix.Scale(0.85, 4)), "pavilion": pavilion_parts, "classroom": classroom_parts}
    meas = {k: measure(fn) for k, fn in recipes.items()}

    # ---- courtyard plateaus (navigation): low raises that follow the sphere; no flat cut, no kerb, no step
    terraces = []
    def plateau(structure_id, key, radius):
        terraces.append(dict(id=f"terrace-{structure_id}", structure=structure_id, key=key, dir=site_dir[key], radius=radius, blend=PLATEAU_BLEND, frame=site_frame(key, R + PLATEAU)))
    plateau("academy-hall", "hall", meas["academy-hall"]["footprint"] + 0.26)
    plateau("academy-tower", "tower", meas["academy-tower"]["footprint"] + 0.34)
    plateau("library", "library", meas["library"]["footprint"] + 0.14)
    plateau("classroom", "classroom", meas["classroom"]["footprint"] + 0.14)
    def base(d):
        height = 0.0
        for t in terraces:
            s = arc(d, t["dir"])
            if s <= t["radius"]: return PLATEAU, PLATEAU, t["id"]
            if s < t["radius"] + t["blend"]: height = max(height, PLATEAU * (1 - smooth((s - t["radius"]) / t["blend"])))
        return height, height, None
    nav_h = lambda d: base(d)[0]
    tframe = {t["structure"]: t["frame"] for t in terraces}

    # ---- plaza and routes
    plaza_f = site_frame("plaza"); plaza_r = 0.95; plaza_c = plaza_f.up
    routes = [dict(id=s["id"], width=s["width"], serves=s["serves"], dirs=resample(chaikin_sphere(s["points"]), 0.1)) for s in ROUTES]
    marker_r, pond_r = 0.46, 0.6
    flats = [("pond", site_dir["pond"], pond_r + 0.05), ("marker", site_dir["marker"], marker_r + 0.05)]
    zones = [(d, rt["width"] / 2 + 0.03) for rt in routes for d in rt["dirs"]] + [(plaza_c, plaza_r)] \
        + [(t["dir"], t["radius"] + t["blend"]) for t in terraces] + [(d, r_) for _, d, r_ in flats]
    hills = [(direction(a, b_), h, s) for a, b_, h, s in HILLS]
    JITTER = 0.018
    def decorative(d):
        dist = min(arc(d, c) - r_ for c, r_ in zones)
        mask = smooth((dist - 0.12) / 0.45)
        if mask <= 0: return 0.0
        v = sum(h * math.exp(-((arc(d, c) / s) ** 2)) for c, h, s in hills)
        hsh = abs(math.sin(d.x * 127.1 + d.y * 311.7 + d.z * 74.7) * 43758.5453) % 1
        return (v + JITTER * (hsh * 2 - 1)) * mask
    ground = lambda d: base(d)[1] + decorative(d)

    # ---- terrain
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=TERRAIN_SUBDIV, radius=1.0)
    g_verts, faces = [], []
    for v in bm.verts:
        d = Vector((v.co.x, v.co.z, -v.co.y)).normalized(); g_verts.append(d * (R + ground(d)))
    for f in bm.faces: faces.append(tuple(l.vert.index for l in f.loops))
    bm.free()
    bvh = BVHTree.FromPolygons([tuple(v) for v in g_verts], faces)
    def height_at(d):
        hit = bvh.ray_cast(Vector((0, 0, 0)), d, R * 2)
        return hit[0].length if hit and hit[0] else R + ground(d)
    col = {k: hex_lin(P[k]) for k in ("lawn", "meadow", "meadowLight", "meadowDeep", "grove", "heath", "earth", "rockGround", "sand", "highland", "olive", "coolGreen")}
    districts = [(t["dir"], t["radius"] + t["blend"]) for t in terraces] + [(plaza_c, plaza_r), (site_dir["pavilion"], 0.7)]
    groves = [site_dir[k] for k in ("grove-far", "orchard", "meadow-north", "glade-west")]
    def patches(n): return (math.sin(n.x * 3.1 + n.y * 1.7 + 0.6) + math.sin(n.z * 2.6 - n.x * 1.9 + 1.4) + math.sin(n.y * 3.7 + n.z * 1.3 - 0.4)) / 3
    terrain = Builder()
    tverts = [terrain.bm.verts.new(C @ v) for v in g_verts]
    for fi, f in enumerate(faces):
        face = terrain.bm.faces.new([tverts[i] for i in f]); face.smooth = False
        cen = sum((g_verts[i] for i in f), Vector()) / 3
        height = cen.length - R; n = cen.normalized(); lat = math.degrees(math.asin(max(-1, min(1, n.y)))); lon = math.degrees(math.atan2(n.x, n.z)) % 360
        hsh = abs(math.sin(fi * 3 * 12.9898) * 43758.5453) % 1; patch = patches(n)
        c = lerp(col["meadow"], col["meadowDeep"] if patch < 0 else col["meadowLight"], min(1, abs(patch) * 1.6) * 0.75)
        # Regions: warm olive south-west, cooler green north-east, a highland on the far side, lawn around districts.
        c = lerp(c, col["olive"], smooth((math.cos(math.radians(lon - 330)) * 0.5 + 0.5) * (1 - smooth((lat - 10) / 40))) * 0.55)
        c = lerp(c, col["coolGreen"], smooth((math.cos(math.radians(lon - 120)) * 0.5 + 0.5) * smooth((lat + 10) / 50)) * 0.5)
        c = lerp(c, col["highland"], (1 - smooth((arc(n, site_dir["highland"]) - 0.6) / 1.1)) * 0.75 + max(0, height - 0.08) * 1.5)
        c = lerp(c, col["meadowLight"], max(0, height) * 1.6)
        c = lerp(c, col["lawn"], max(1 - smooth((arc(n, dd) - rr) / 0.8) for dd, rr in districts) * 0.7)
        c = lerp(c, col["grove"], max(1 - smooth((arc(n, g) - 0.3) / 0.7) for g in groves) * 0.6)
        c = lerp(c, col["sand"], (1 - smooth((arc(n, site_dir["pond"]) - 0.62) / 0.35)) * 0.8)
        c = lerp(c, col["heath"], smooth((-lat - 4 + patch * 12) / 18) * 0.8)
        c = lerp(c, col["earth"], smooth((-lat - 32 + patch * 10) / 18) * 0.65 + max(0, -height) * 3)
        c = lerp(c, col["rockGround"], smooth((-lat - 58) / 18) * 0.8)
        c = offset_l(c, (hsh - 0.5) * 0.045)
        for loop in face.loops: loop[terrain.col] = (c[0], c[1], c[2], 1.0)
    terrain.to_object("LEARNING_TERRAIN", cols["LEARNING_VISUAL"], mat)

    # ---- paths (curved ribbons that flare near the plaza and courtyards), plaza paving, courtyards, pond
    paths = Builder()
    surf = [hex_lin(P["path"]), hex_lin(P["pathAlt"])]; kerb = hex_lin(P["kerb"])
    courts = [(t["dir"], meas[t["structure"]]["footprint"] + 0.22) for t in terraces]
    def flare(d):
        near = min([max(0.0, arc(d, plaza_c) - plaza_r)] + [max(0.0, arc(d, c) - r_) for c, r_ in courts])
        return 1 + 0.6 * (1 - smooth(near / 0.5))
    for rt in routes:
        dirs = rt["dirs"]; lift = PAVING_LIFT if rt["width"] == PRIMARY else PAVING_LIFT - 0.002
        rows = []
        for i, d in enumerate(dirs):
            prev, nxt = dirs[max(0, i - 1)], dirs[min(len(dirs) - 1, i + 1)]
            side = d.cross(nxt - prev).normalized(); half = rt["width"] / 2 * flare(d)
            row = []
            for off, raise_ in ((-half - 0.03, -0.004), (-half, 0.006), (half, 0.006), (half + 0.03, -0.004)):
                p = (d * R + side * off).normalized(); row.append(p * (height_at(p) + lift + raise_))
            rows.append(row)
        for i in range(1, len(rows)):
            if arc(dirs[i], plaza_c) < plaza_r - 0.04 and arc(dirs[i - 1], plaza_c) < plaza_r - 0.04: continue
            hsh = abs(math.sin((i + len(rt["id"]) * 31) * 78.233) * 43758.5453) % 1
            tone = offset_l(surf[0] if hsh < 0.5 else surf[1], (hsh - 0.5) * 0.03)
            for k in range(3):
                paths.quads([([rows[i - 1][k], rows[i][k], rows[i][k + 1], rows[i - 1][k + 1]], tone if k == 1 else kerb)])
    def cap(frame, rings, color_of, lift, sectors=24):
        def point(dist, a):
            d = frame.offset_dir(math.sin(a) * dist, math.cos(a) * dist)
            return d * (max(height_at(d), R + nav_h(d)) + lift)
        for ring in range(1, len(rings)):
            for s in range(sectors):
                a0, a1 = s / sectors * 2 * math.pi, (s + 1) / sectors * 2 * math.pi
                c = offset_l(color_of(ring, s), ((s * 7 + ring * 3) % 5 - 2) * 0.004)
                paths.quads([([point(rings[ring - 1], a0), point(rings[ring], a0), point(rings[ring], a1), point(rings[ring - 1], a1)], c)])
    pr = [0, 0.1, 0.22, LANDING_CLEAR - 0.02, LANDING_CLEAR + 0.03, 0.46, 0.62, 0.78, plaza_r - 0.06, plaza_r]
    pc = {k: hex_lin(P[k]) for k in ("plaza", "inlay", "landing", "kerb")}
    cap(plaza_f, pr, lambda ring, s: pc["landing"] if ring == 4 else pc["kerb"] if ring == len(pr) - 1 else pc["inlay"] if ring in (6, 7) and s % 3 == 0 else pc["plaza"], PAVING_LIFT + 0.004)
    cob = {k: hex_lin(P[k]) for k in ("cobble", "cobbleDark", "sandstone")}
    for t in terraces:   # courtyards: cobbles around each building with a darker edging ring
        fp = meas[t["structure"]]["footprint"]
        cap(Frame(t["dir"], R, site_frame(t["key"]).forward), [0, fp * 0.5, fp + 0.02, fp + 0.14, fp + 0.22],
            lambda ring, s: cob["cobbleDark"] if ring == 4 else cob["cobble"] if (ring + s) % 2 else cob["sandstone"], PAVING_LIFT + 0.002, 20)
    pond_f = site_frame("pond"); water = hex_lin(P["water"]); deep = offset_l(water, -0.04); sand = hex_lin(P["sand"])
    cap(pond_f, [0, 0.22, 0.4, pond_r * 0.8, pond_r], lambda ring, s: deep if ring <= 2 else water if ring == 3 else sand, PAVING_LIFT, 18)
    paths.to_object("LEARNING_PATHS_PAVING", cols["LEARNING_PATHS"], mat)

    # ---- buildings (separate objects; origin at the base centre; rotation = surface frame)
    buildings, obstacles = [], []
    def place_building(name, sid, frame, landmark, env=False, radius=None):
        b = Builder(); m = meas[sid]
        recipes[sid](b, Matrix.Translation(Vector((-m["cx"], 0, -m["cz"]))))
        ob = b.to_object(name, cols["LEARNING_BUILDINGS"], mat, C4 @ frame.world() @ C4i)
        if env: ob["role"] = f"environment:{sid}"
        else: ob["structure_id"] = sid
        ob["footprint_radius"] = m["footprint"]
        buildings.append(dict(id=sid, name=name, frame=frame, footprint=m["footprint"], height=m["height"], landmark=landmark, env=env))
        obstacles.append(dict(id=sid, kind="structure", dir=frame.up, radius=radius if radius is not None else m["footprint"] + 0.06, height=m["height"]))
    place_building("ACADEMY_HALL", "academy-hall", tframe["academy-hall"], "landmark-javascriptia")
    place_building("ACADEMY_TOWER", "academy-tower", tframe["academy-tower"], "landmark-kodestep")
    monument_dir = plaza_f.offset_dir(math.sin(math.radians(57)) * 1.45, math.cos(math.radians(57)) * 1.45)
    monument_f = Frame(monument_dir, R + ground(monument_dir) - 0.005, plaza_c - monument_dir)
    place_building("BOOK_MONUMENT", "book-monument", monument_f, None, radius=meas["book-monument"]["footprint"])
    place_building("LIBRARY", "library", tframe["library"], None, env=True)
    place_building("STUDY_PAVILION", "pavilion", Frame(site_dir["pavilion"], R + PAVING_LIFT, site_dir["plaza"] - site_dir["pavilion"]), None, env=True)
    place_building("GARDEN_CLASSROOM", "classroom", tframe["classroom"], None, env=True)
    hf, tf = tframe["academy-hall"], tframe["academy-tower"]
    hall_r = next(t["radius"] for t in terraces if t["structure"] == "academy-hall")
    tower_r = next(t["radius"] for t in terraces if t["structure"] == "academy-tower")

    # ---- decorations (merged) and accents (merged, emissive)
    decor, accents = Builder(), Builder()
    why = {}
    def fits(d, radius, kind="scenery", item_id=None):
        reasons = []
        for rt in routes:
            m = min(arc(d, p) - rt["width"] / 2 * 1.6 - radius for p in rt["dirs"])
            if m < 0.4: reasons.append(f"{rt['id']} {m:.2f}")
        if arc(d, plaza_c) - plaza_r - radius < 0.1: reasons.append(f"plaza {arc(d, plaza_c) - plaza_r - radius:.2f}")
        for t in terraces:
            if arc(d, t["dir"]) - t["radius"] - radius < 0.0: reasons.append(f"{t['id']} {arc(d, t['dir']) - t['radius'] - radius:.2f}")
        for o in obstacles:
            need = PRIMARY if o["kind"] == "structure" else (SECONDARY if (o["kind"] == "decor" or kind == "decor") else 0)
            if arc(d, o["dir"]) - o["radius"] - radius < need: reasons.append(f"{o['id']} {arc(d, o['dir']) - o['radius'] - radius:.2f}<{need:.2f}")
        if reasons and item_id: why[item_id] = reasons
        return not reasons
    def cone_tree(b, w, h, color, width=0.36):
        b.cylinder((0, .1, 0), (.07, .2, .07), P["trunk"], world=w); b.cone((0, .17 + h / 2, 0), (width, h, width), color, world=w)
    def round_tree(b, w, s, color):
        b.cylinder((0, .11, 0), (.07, .22, .07), P["trunk"], world=w); b.rock((0, .2 + s * .42, 0), (s, s * .9, s), color, world=w)
    def big_tree(b, w):
        b.cylinder((0, .2, 0), (.12, .4, .12), P["trunk"], world=w); b.rock((0, .62, 0), (.7, .62, .7), P["grove"], world=w); b.rock((.18, .78, .1), (.42, .36, .42), P["foliageWarm"], world=w)
    def shrub(b, w, s, color): b.rock((0, s * .28, 0), (s, s * .62, s), color, world=w)
    def stone(b, w, size, color): b.rock((0, size[1] * .32, 0), size, color, world=w)
    def reed(b, w, h): b.cone((0, h / 2, 0), (.055, h, .055), P["reed"], world=w)
    def flowers(b, w, color):
        for x, z in ((0, 0), (.07, .04), (-.05, .06), (.03, -.07)): b.rock((x, .03, z), (.06, .04, .06), color, world=w)
    def hedge(b, w, length): b.box((0, .06, 0), (length, .12, .1), P["hedge"], world=w)
    def bench(b, w):
        b.box((0, .07, 0), (.22, .03, .08), P["wood"], world=w); b.box((-.08, .03, 0), (.03, .06, .07), P["wood"], world=w); b.box((.08, .03, 0), (.03, .06, .07), P["wood"], world=w)
    def wall_piece(b, w): b.box((0, .06, 0), (.3, .12, .08), P["stoneWall"], world=w)
    def pier(b, w):
        b.box((0, .04, .3), (.16, .03, .6), P["wood"], world=w)
        for z in (.1, .5): b.box((.06, -.02, z), (.03, .12, .03), P["trunk"], world=w); b.box((-.06, -.02, z), (.03, .12, .03), P["trunk"], world=w)
    def ruin_arch(b, w):
        b.box((-.2, .25, 0), (.1, .5, .12), P["stoneWall"], world=w); b.box((.2, .22, 0), (.1, .44, .12), P["stoneWall"], world=w); b.box((0, .52, 0), (.5, .08, .12), P["stoneWall"], world=w)
    def item_radius(fn, *args):
        b = Builder(); fn(b, Matrix.Identity(4), *args)
        rr = max(math.hypot(v.co.x, v.co.y) for v in b.bm.verts); hh = max(v.co.z for v in b.bm.verts); b.bm.free()
        return rr, hh
    def cluster(id_, frame, items):
        hint = frame.forward
        for idx, (x, z, fn, args) in enumerate(items):
            item_id = f"{id_}-{idx + 1}" if len(items) > 1 else id_
            d = frame.offset_dir(x, z); rr, hh = item_radius(fn, *args)
            if not fits(d, rr, "scenery", item_id): report["skipped"].append(item_id); continue
            f = Frame(d, R + ground(d) - 0.02, hint); fn(decor, f.world(), *args)
            obstacles.append(dict(id=item_id, kind="scenery", dir=d, radius=rr, height=hh))
    def frame_off(frame, x, z, hint=None):
        d = frame.offset_dir(x, z); return Frame(d, R, hint if hint is not None else frame.forward)
    # Low retaining stones on each courtyard rim (visual only; skipped where a route crosses the rim).
    for t in terraces:
        for i in range(28):
            a = i / 28 * 2 * math.pi
            d = Frame(t["dir"], R, south(t["dir"])).offset_dir(math.sin(a) * (t["radius"] + 0.02), math.cos(a) * (t["radius"] + 0.02))
            if any(arc(d, p) < rt["width"] / 2 * 1.6 + 0.1 for rt in routes for p in rt["dirs"]): continue
            if arc(d, plaza_c) < plaza_r + 0.1: continue
            decor.box((0, .025, 0), (.16, .07, .06), P["stoneWall"], world=Frame(d, R + ground(d) - 0.01, t["dir"] - d).world())
    lib_f, cls_f = tframe["library"], tframe["classroom"]
    # Academy district
    cluster("academy-cypresses", frame_off(hf, 0, -(hall_r + 0.4)), [(-.7, .04, cone_tree, (.66, P["foliage"], .26)), (-.25, -.1, cone_tree, (.8, P["grove"], .28)), (.25, -.1, cone_tree, (.76, P["grove"], .28)), (.7, .04, cone_tree, (.6, P["foliage"], .26))])
    cluster("academy-garden-left", frame_off(hf, -(hall_r + 0.45), -.35), [(0, 0, flowers, (P["flowerA"],)), (-.28, .1, flowers, (P["flowerB"],)), (-.1, -.3, shrub, (.18, P["foliageWarm"])), (-.05, -.62, bench, ())])
    cluster("academy-garden-right", frame_off(hf, hall_r + 0.45, -.35), [(0, 0, flowers, (P["flowerC"],)), (.28, .1, flowers, (P["flowerB"],)), (.1, -.3, shrub, (.18, P["foliageOlive"])), (.05, -.62, bench, ())])
    cluster("library-hedges", frame_off(lib_f, 0, -(meas["library"]["footprint"] + 0.72)), [(-.25, 0, hedge, (.4,)), (.25, 0, hedge, (.4,)), (0, -.42, round_tree, (.3, P["foliage"]))])
    # Landing district: four lanterns on the plaza rim (bases here, glow below) and the pavilion garden.
    lantern_dirs = [plaza_f.offset_dir(math.sin(math.radians(a)) * r_, math.cos(math.radians(a)) * r_) for a, r_ in ((330, 1.4), (215, 1.3))]
    for i, d in enumerate(lantern_dirs):
        w = Frame(d, R + ground(d) - 0.01, plaza_c - d).world()
        decor.cylinder((0, .14, 0), (.05, .28, .05), P["slate"], world=w); decor.box((0, .3, 0), (.09, .09, .09), P["slate"], world=w)
        accents.sphere((0, .3, 0), (.06, .06, .06), P["lantern"], world=w)
        obstacles.append(dict(id=f"lantern-{i + 1}", kind="decor", dir=d, radius=0.06, height=0.35))
    pav_f = Frame(site_dir["pavilion"], R, site_dir["plaza"] - site_dir["pavilion"])
    cluster("pavilion-garden", frame_off(pav_f, 0, -1.25), [(-.4, 0, round_tree, (.34, P["foliageWarm"])), (.4, .05, round_tree, (.3, P["foliage"])), (0, -.28, flowers, (P["flowerA"],))])
    # Tower district
    cluster("tower-garden-left", frame_off(tf, -(tower_r + 0.42), .15), [(0, 0, round_tree, (.36, P["foliage"])), (.1, .36, flowers, (P["flowerB"],))])
    cluster("classroom-garden", Frame(site_dir["classroom"], R, south(site_dir["classroom"])).offset_dir(0, 0) and frame_off(Frame(site_dir["classroom"], R, south(site_dir["classroom"])), 0, meas["classroom"]["footprint"] + 0.66), [(0, 0, flowers, (P["flowerC"],)), (0, .22, shrub, (.2, P["foliageOlive"]))])
    # Far hemisphere: highland with a great tree and boulders, a ruin arch, the pond's pier and reeds.
    cluster("highland", site_frame("highland"), [(0, 0, big_tree, ()), (.7, .3, stone, ((.5, .4, .44), P["rockDark"])), (-.6, .4, stone, ((.34, .28, .3), P["rock"])), (.2, -.7, stone, ((.3, .22, .26), P["rock"]))])
    cluster("ruin", site_frame("ruin"), [(0, 0, ruin_arch, ()), (.5, .2, stone, ((.22, .16, .2), P["stoneWall"]))])
    cluster("pond-pier", frame_off(pond_f, -.1, pond_r + .02, pond_f.forward), [(0, 0, pier, ())])
    cluster("pond-reeds", frame_off(pond_f, .75, .3), [(0, 0, reed, (.2,)), (.09, .05, reed, (.16,)), (-.07, .08, reed, (.18,))])
    cluster("grove-far", site_frame("grove-far"), [(-.24, 0, cone_tree, (.6, P["foliage"])), (.2, .16, cone_tree, (.48, P["foliageOlive"])), (.06, -.26, round_tree, (.34, P["grove"]))])
    cluster("orchard", site_frame("orchard"), [(-.25, -.15, round_tree, (.32, P["foliageWarm"])), (.22, -.2, round_tree, (.3, P["foliage"])), (-.18, .25, round_tree, (.3, P["foliage"])), (.27, .2, round_tree, (.34, P["foliageOlive"]))])
    cluster("orchard-wall", frame_off(site_frame("orchard"), 0, .62), [(-.32, 0, wall_piece, ()), (0, 0, wall_piece, ()), (.32, 0, wall_piece, ())])
    cluster("glade-west", site_frame("glade-west"), [(-.2, 0, cone_tree, (.55, P["grove"])), (.22, .1, round_tree, (.3, P["foliageWarm"])), (0, -.3, flowers, (P["flowerA"],))])
    cluster("meadow-north", site_frame("meadow-north"), [(-.15, 0, cone_tree, (.5, P["grove"])), (.22, .12, shrub, (.22, P["foliageWarm"]))])
    cluster("rocks-south", site_frame("rocks-south"), [(0, 0, stone, ((.42, .34, .36), P["rock"])), (.32, .12, stone, ((.24, .2, .22), P["rockDark"])), (-.28, .18, shrub, (.2, P["foliageOlive"]))])
    cluster("heath-south", site_frame("heath-south"), [(-.15, 0, shrub, (.24, P["foliageOlive"])), (.16, .1, shrub, (.18, P["foliageWarm"])), (.05, -.22, stone, ((.22, .18, .2), P["rock"]))])
    cluster("rocks-west", site_frame("rocks-west"), [(0, 0, stone, ((.36, .3, .32), P["rockDark"])), (.34, -.1, stone, ((.2, .16, .18), P["rock"]))])
    cluster("shrubs-south", site_frame("shrubs-south"), [(-.12, 0, shrub, (.22, P["foliage"])), (.18, .06, round_tree, (.3, P["foliageOlive"]))])
    cluster("garden-front", site_frame("garden-front"), [(-.2, 0, round_tree, (.34, P["foliage"])), (.2, .1, round_tree, (.28, P["foliageWarm"])), (.02, .3, flowers, (P["flowerB"],))])
    cluster("rocks-front", site_frame("rocks-front"), [(0, 0, stone, ((.3, .24, .26), P["rock"])), (.3, .08, shrub, (.2, P["foliageWarm"]))])

    accent_list = []
    def accent(id_, district, d, radius, height, decor_fn, glow_fn, lift=-0.01, hint=None, on_plaza=False):
        ok = (arc(d, plaza_c) - radius >= LANDING_CLEAR + 0.1 and arc(d, plaza_c) + radius <= plaza_r) if on_plaza else fits(d, radius, "decor", id_)
        if not ok: report["skipped"].append(id_); return
        f = Frame(d, R + ground(d) + lift, hint if hint is not None else south(d))
        decor_fn(decor, f.world()); glow_fn(accents, f.world())
        obstacles.append(dict(id=id_, kind="decor", dir=d, radius=radius, height=height))
        accent_list.append(dict(id=id_, district=district, origin=list(f.origin), up=list(f.up)))
    book_d = lib_f.offset_dir(-1.26, 0.3)
    accent("accent-floating-book", "academy", book_d, 0.13, 0.38,
           lambda b, w: (b.cylinder((0, .09, 0), (.15, .18, .15), P["sandstoneDark"], world=w), b.box((0, .19, 0), (.2, .03, .16), P["sandstone"], world=w), b.box((0, .335, 0), (.25, .012, .17), P["cover"], rot=(.18, 0, 0), world=w)),
           lambda b, w: (b.box((-.058, .352, 0), (.11, .012, .15), P["page"], rot=(.18, 0, -.22), world=w), b.box((.058, .352, 0), (.11, .012, .15), P["page"], rot=(.18, 0, .22), world=w)),
           hint=lib_f.up - book_d)
    crystal_d = tf.offset_dir(-(tower_r + 0.15), -0.55)
    accent("accent-knowledge-crystal", "tower", crystal_d, 0.1, 0.38,
           lambda b, w: (b.cylinder((0, .03, 0), (.2, .08, .2), P["sandstoneDark"], segments=6, world=w), b.ring((0, .08, 0), (.2, .2, .2), P["cobbleDark"], rot=(math.pi / 2, 0, 0), world=w)),
           lambda b, w: (b.rock((0, .22, 0), (.12, .32, .12), P["crystal"], world=w), b.rock((.055, .12, .03), (.055, .13, .055), P["crystal"], rot=(0, 0, -.35), world=w)),
           hint=tf.forward)
    term_d = plaza_f.offset_dir(-0.55, 0.48)
    accent("accent-learning-terminal", "landing", term_d, 0.12, 0.32,
           lambda b, w: (b.box((0, .11, 0), (.12, .22, .08), P["slate"], world=w), b.box((0, .245, -.012), (.2, .14, .02), P["screenBack"], rot=(-.6, 0, 0), world=w)),
           lambda b, w: b.box((0, .25, -.003), (.17, .11, .012), P["screen"], rot=(-.6, 0, 0), world=w),
           lift=PAVING_LIFT - ground(term_d), hint=plaza_c - term_d, on_plaza=True)
    # Hall emblem gem on the pediment (glow only; part of the hall silhouette, no obstacle).
    accents.sphere((0, .76, .6), (.05, .05, .05), P["crystal"], world=hf.world() @ Matrix.Translation(Vector((-meas["academy-hall"]["cx"], 0, -meas["academy-hall"]["cz"]))))
    accent_list.append(dict(id="accent-hall-emblem", district="academy", origin=list(hf.origin), up=list(hf.up)))
    accent_list.append(dict(id="accent-plaza-lanterns", district="landing", origin=list(plaza_f.origin), up=list(plaza_f.up)))
    # Discovery marker: a stone circle around a faintly glowing rune disc (environment only).
    mk = site_frame("marker"); mkf = Frame(mk.up, R + ground(mk.up) - 0.005, mk.forward); w = mkf.world()
    decor.cylinder((0, .006, 0), (.4, .012, .4), P["sandstone"], segments=12, world=w)
    decor.ring((0, .016, 0), (.26, .26, .26), P["kerb"], rot=(math.pi / 2, 0, 0), world=w)
    for i in range(6):
        a = i / 6 * 2 * math.pi
        decor.box((math.sin(a) * .36, .12, math.cos(a) * .36), (.08, .28, .06), P["rock"], rot=(0, a, 0), world=w)
    accents.cylinder((0, .02, 0), (.12, .012, .12), P["crystal"], segments=8, world=w)
    obstacles.append(dict(id="discovery-marker", kind="decor", dir=mk.up, radius=marker_r, height=0.28))
    obstacles.append(dict(id="pond", kind="scenery", dir=pond_f.up, radius=pond_r, height=0.02))
    accent_list.append(dict(id="accent-discovery-marker", district="far", origin=list(mkf.origin), up=list(mkf.up)))
    decor.to_object("LEARNING_DECORATIONS_STATIC", cols["LEARNING_DECORATIONS"], mat)
    accents.to_object("LEARNING_ACCENTS_GLOW", cols["LEARNING_ACCENTS"], mat_accent)

    # ---- anchors (empties; names, roles and radii only)
    def on_nav(d):
        d = d.normalized(); return d * (R + nav_h(d))
    def empty(name, frame_or_point, role, radius=None, display="PLAIN_AXES", size=0.15, hint=None):
        ob = bpy.data.objects.new(name, None); ob.empty_display_type = display; ob.empty_display_size = size
        if isinstance(frame_or_point, Frame): ob.matrix_world = C4 @ frame_or_point.world() @ C4i
        else:
            p = Vector(frame_or_point); f = Frame(p, p.length, hint if hint is not None else south(p.normalized())); ob.matrix_world = C4 @ f.world() @ C4i
        ob["role"] = role
        if radius is not None: ob["radius"] = float(radius)
        cols["LEARNING_ANCHORS"].objects.link(ob); return ob
    def door(frame, sid): return frame.origin + frame.forward * (meas[sid]["footprint"] + 0.12)
    hall_door = on_nav(door(hf, "academy-hall")); tower_door = on_nav(door(tf, "academy-tower"))
    monument_point = on_nav(monument_f.origin + monument_f.forward * (meas["book-monument"]["footprint"] + 0.08))
    spawn_d = toward(plaza_c, hf.up, -0.12); spawn_f = Frame(spawn_d, R + PAVING_LIFT, hf.up - spawn_d)
    anchors = {
        "ANCHOR_interaction_academy_hall": empty("ANCHOR_interaction_academy_hall", hall_door, "interaction:academy-hall", hint=hf.up - hall_door.normalized()),
        "ANCHOR_interaction_academy_tower": empty("ANCHOR_interaction_academy_tower", tower_door, "interaction:academy-tower", hint=tf.up - tower_door.normalized()),
        "ANCHOR_interaction_book_monument": empty("ANCHOR_interaction_book_monument", monument_point, "interaction:book-monument", hint=monument_dir - monument_point.normalized()),
        "ANCHOR_landing": empty("ANCHOR_landing", Frame(plaza_c, R + PAVING_LIFT, south(plaza_c)), "landing", LANDING_CLEAR, "CIRCLE", LANDING_CLEAR),
        "ANCHOR_spawn": empty("ANCHOR_spawn", spawn_f, "spawn", display="ARROWS", size=0.12),
        "ANCHOR_lander_arrival": empty("ANCHOR_lander_arrival", Frame(plaza_c, R + 1.5 * H, south(plaza_c)), "lander-arrival", LANDING_CLEAR, "SPHERE", 0.2),
        "ANCHOR_minigame_candidate": empty("ANCHOR_minigame_candidate", Frame(monument_dir, R + PAVING_LIFT, plaza_c - monument_dir), "minigame-candidate", 0.35, "CIRCLE", 0.35),
    }

    # ---- navigation reference (kept in the .blend; not exported)
    nav = Builder()
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=NAV_SUBDIV, radius=1.0)
    nv = []
    for v in bm.verts:
        d = Vector((v.co.x, v.co.z, -v.co.y)).normalized(); nv.append(nav.bm.verts.new(C @ (d * (R + nav_h(d)))))
    for f in bm.faces:
        face = nav.bm.faces.new([nv[l.vert.index] for l in f.loops]); face.smooth = False
        for loop in face.loops: loop[nav.col] = (0.35, 0.4, 0.5, 1.0)
    bm.free()
    nav_ob = nav.to_object("NAV_SURFACE", cols["LEARNING_NAVIGATION_REFERENCE"], diorama_material("LearningNavigationReference")); nav_ob.display_type = 'WIRE'; nav_ob.hide_render = True
    def polyline(name, points_g, closed=False):
        me = bpy.data.meshes.new(name); verts = [C @ p for p in points_g]
        edges = [(i, i + 1) for i in range(len(verts) - 1)] + ([(len(verts) - 1, 0)] if closed else [])
        me.from_pydata(verts, edges, []); ob = bpy.data.objects.new(name, me); cols["LEARNING_NAVIGATION_REFERENCE"].objects.link(ob); ob.hide_render = True; return ob
    path_data = []
    for rt in routes:
        pts = [on_nav(d) for d in rt["dirs"]]; ob = polyline(f"NAV_route_{rt['id']}", pts); ob["width"] = rt["width"]
        path_data.append(dict(id=rt["id"], width=rt["width"], serves=rt["serves"], points=[list(p) for p in pts]))
    for o in obstacles:
        f = Frame(o["dir"], R + nav_h(o["dir"]), south(o["dir"]))
        polyline(f"NAV_footprint_{o['id']}", [f.origin + (f.right * math.cos(a) + f.forward * math.sin(a)) * o["radius"] for a in [i / 24 * 2 * math.pi for i in range(24)]], True)
    lf = Frame(plaza_c, R + PAVING_LIFT, south(plaza_c))
    polyline("NAV_landing_clear", [lf.origin + (lf.right * math.cos(a) + lf.forward * math.sin(a)) * LANDING_CLEAR for a in [i / 32 * 2 * math.pi for i in range(32)]], True)

    # ---- measurements (same definitions as before; routes exempt only their own destination near its footprint)
    samples = [(rt, d) for rt in routes for d in rt["dirs"]]
    path_clear, path_at = 1e9, ""
    for rt, d in samples:
        if arc(d, plaza_c) < plaza_r: continue
        for o in obstacles:
            if o["id"] in rt["serves"] and arc(d, o["dir"]) < o["radius"] + 0.8: continue   # the approach to the route's own destination
            gap = arc(d, o["dir"]) - o["radius"] - rt["width"] / 2
            if gap < path_clear: path_clear, path_at = gap, f"{rt['id']} ↔ {o['id']}"
    landmarks = ("academy-hall", "academy-tower", "book-monument")
    lgap, lat_, bgap, bat, sgap, sat, ogap, oat = 1e9, "", 1e9, "", 1e9, "", 1e9, ""
    for i in range(len(obstacles)):
        for j in range(i + 1, len(obstacles)):
            a, b_ = obstacles[i], obstacles[j]
            if a["kind"] == "scenery" and b_["kind"] == "scenery": continue
            gap = arc(a["dir"], b_["dir"]) - a["radius"] - b_["radius"]; at = f"{a['id']} ↔ {b_['id']}"
            if a["kind"] == "structure" and b_["kind"] == "structure":
                if gap < bgap: bgap, bat = gap, at
                if a["id"] in landmarks and b_["id"] in landmarks and gap < lgap: lgap, lat_ = gap, at
            elif (a["kind"] == "structure" or b_["kind"] == "structure") and gap < sgap: sgap, sat = gap, at
            if gap < ogap: ogap, oat = gap, at
    landing_clear = min(arc(plaza_c, o["dir"]) - o["radius"] for o in obstacles)
    spawn_clear = min(arc(spawn_d, o["dir"]) - o["radius"] for o in obstacles)
    def walkable(p):
        return min(min(arc(p, d) - rt["width"] / 2 for rt, d in samples), arc(p, plaza_c) - plaza_r, min(arc(p, t["dir"]) - t["radius"] for t in terraces))
    reach = {k: max(0.0, walkable(v)) for k, v in (("hall", hall_door), ("tower", tower_door), ("monument", monument_point))}
    max_slope, slope_at = 0.0, ""
    for rt in routes:
        dirs = rt["dirs"]
        for i in range(1, len(dirs)):
            steps = max(1, math.ceil(arc(dirs[i - 1], dirs[i]) / 0.01))
            for k in range(1, steps + 1):
                a = dirs[i - 1].lerp(dirs[i], (k - 1) / steps).normalized(); b_ = dirs[i - 1].lerp(dirs[i], k / steps).normalized()
                run = arc(a, b_)
                if run > 0:
                    sl = math.degrees(math.atan(abs(nav_h(b_) - nav_h(a)) / run))
                    if sl > max_slope: max_slope, slope_at = sl, rt["id"]
    min_turn = 180.0
    for rt in routes:
        d = rt["dirs"]
        for i in range(1, len(d) - 1):
            t1 = (d[i] - d[i - 1]).normalized(); t2 = (d[i + 1] - d[i]).normalized()
            min_turn = min(min_turn, 180 - math.degrees(math.acos(max(-1, min(1, t1.dot(t2))))))
    extent = 0.0
    for name in ("LEARNING_VISUAL", "LEARNING_PATHS", "LEARNING_BUILDINGS", "LEARNING_DECORATIONS", "LEARNING_ACCENTS"):
        for ob in cols[name].objects:
            for v in ob.data.vertices: extent = max(extent, (ob.matrix_world @ v.co).length)
    measurements = dict(
        radius=R, radiusInH=R / H, extent=extent, plateau=PLATEAU,
        footprints={k: v["footprint"] for k, v in meas.items()}, heights={k: v["height"] for k, v in meas.items()},
        terraces=[dict(id=t["id"], radius=t["radius"], blend=t["blend"], raise_=PLATEAU) for t in terraces],
        pathWidths={rt["id"]: rt["width"] for rt in routes}, routeLengths={rt["id"]: sum(arc(rt["dirs"][i - 1], rt["dirs"][i]) for i in range(1, len(rt["dirs"]))) for rt in routes},
        pathClearance=path_clear, pathClearanceAt=path_at, landmarkGap=lgap, landmarkGapAt=lat_, buildingGap=bgap, buildingGapAt=bat,
        structureGap=sgap, structureGapAt=sat, obstacleGap=ogap, obstacleGapAt=oat, landingClear=landing_clear, spawnClear=spawn_clear,
        landingFlatness=R - math.sqrt(R * R - LANDING_CLEAR ** 2), maxRouteSlopeDegrees=max_slope, maxRouteSlopeAt=slope_at, maxRouteStep=0.0,
        minRouteInteriorAngle=min_turn, anchorReach=reach, hallToTowerArc=arc(hf.up, tf.up), skippedDecor=report["skipped"], obstacleCount=len(obstacles),
        decorativeReliefOnPaths=max(abs(decorative(d)) for _, d in samples),
    )
    layout = dict(
        structures=[dict(id=b_["id"], object=b_["name"], landmarkHint=b_["landmark"], environment=b_["env"], origin=list(b_["frame"].origin), up=list(b_["frame"].up), forward=list(b_["frame"].forward), footprintRadius=b_["footprint"], height=b_["height"]) for b_ in buildings],
        anchors={k: dict(origin=list(C4i @ v.matrix_world.translation), role=v["role"], radius=v.get("radius")) for k, v in anchors.items()},
        obstacles=[dict(id=o["id"], kind=o["kind"], center=list(o["dir"] * R), radius=o["radius"], height=o["height"]) for o in obstacles],
        paths=path_data, plaza=dict(center=list(plaza_c * R), radius=plaza_r), accents=accent_list,
        terraces=measurements["terraces"], collision=dict(kind="sphere-plateaus", radius=R, plateau=PLATEAU),
    )
    with open(os.path.join(ROOT, "references", "layout-v2.json"), "w", encoding="utf-8") as fh: json.dump(layout, fh, indent=2)
    with open(os.path.join(ROOT, "references", "clearance-report-v2.json"), "w", encoding="utf-8") as fh: json.dump(measurements, fh, indent=2)
    stats = {c.name: dict(objects=len(c.objects), triangles=sum(sum(len(p.vertices) - 2 for p in ob.data.polygons) for ob in c.objects if ob.type == 'MESH')) for c in cols.values()}
    report["stats"] = stats; report["why"] = why
    report["measurements"] = {k: v for k, v in measurements.items() if k not in ("terraces", "pathWidths", "footprints", "heights", "routeLengths")}
    report["footprints"] = measurements["footprints"]; report["heights"] = measurements["heights"]; report["routeLengths"] = measurements["routeLengths"]
    scene["gateway_asset"] = "learning-globe-blender-v2"
    return scene, report

try:
    scene, report = build()
    print("BUILD OK")
    print(json.dumps(report["stats"]))
    print("SKIP", json.dumps(report["why"]))
    print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in report["measurements"].items()}))
    print(json.dumps({k: round(v, 3) for k, v in report["footprints"].items()}), json.dumps({k: round(v, 3) for k, v in report["heights"].items()}), json.dumps({k: round(v, 2) for k, v in report["routeLengths"].items()}))
except Exception:
    print("BUILD FAILED"); print(traceback.format_exc())
