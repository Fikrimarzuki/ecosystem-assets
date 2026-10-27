"""M8.9b.1a.2 — Blender Academy Globe (Learning planet), run inside the live Blender through Blender MCP.

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
SCENE_NAME = "LEARNING"
R = 4.2                      # 14 h
H, RAD = 0.30, 0.05          # astronaut capsule height / radius (local)
KERB, EMBED, TERRACE_SINK, PAVING_LIFT, DESIGN_SLOPE = 0.015, 0.05, 0.01, 0.008, 12.0
PRIMARY, SECONDARY, LANDING_CLEAR = 8 * RAD, 6 * RAD, 6 * RAD
LOOP_LAT = 34.0
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
    "shrubs-south": (330, -40, None), "garden-front": (8, 6, None), "rocks-front": (70, -14, None),
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

# ----------------------------------------------------------------------------- layout
def build():
    report = {"skipped": [], "notes": []}
    if bpy.data.scenes.get(SCENE_NAME):
        raise RuntimeError(f"Scene {SCENE_NAME} already exists in this Blender session; stop (not overwriting).")
    scene = bpy.data.scenes.new(SCENE_NAME)
    cols = {}
    for name in ["LEARNING_VISUAL", "LEARNING_BUILDINGS", "LEARNING_PATHS", "LEARNING_DECORATIONS", "LEARNING_ACCENTS",
                 "LEARNING_ANCHORS", "LEARNING_NAVIGATION_REFERENCE"]:
        col = bpy.data.collections.new(name); scene.collection.children.link(col); cols[name] = col
    mat = diorama_material("LearningDiorama")
    mat_accent = diorama_material("LearningAccent", emissive="#fff1d6")

    site_dir = {k: direction(v[0], v[1]) for k, v in SITES.items()}
    def site_frame(k, radius=R):
        lon, lat, tw = SITES[k]
        n = site_dir[k]
        return Frame(n, radius, site_dir[tw] if tw else south(n))

    # ---- buildings (Gateway-local parts; base at y = 0; footprint centre at the origin)
    def hall_parts(b, w):
        b.box((0, .32, 0), (1.2, .64, .7), PALETTE["wall"], world=w)
        b.box((0, .675, 0), (1.27, .07, .77), PALETTE["hallRoof"], world=w)
        # Heights follow the production hall (roof apex ≈ 1.09 above the base, cupola to ≈ 1.36).
        b.cone((0, .84, 0), (1.5, .5, 1.05), PALETTE["hallRoofTop"], rot=(0, math.pi / 4, 0), segments=4, world=w)
        b.box((0, 1.13, 0), (.17, .16, .17), PALETTE["ivory"], world=w)
        b.cone((0, 1.285, 0), (.24, .15, .24), PALETTE["terracotta"], segments=6, world=w)
        for x in (-.43, 0, .43):
            b.cylinder((x, .32, .44), (.095, .64, .095), PALETTE["column"], world=w)
        b.box((0, .69, .44), (1.0, .06, .13), PALETTE["ivory"], world=w)
        b.box((0, .42, .353), (.84, .16, .025), PALETTE["window"], world=w)
        b.box((0, .16, .355), (.18, .3, .02), PALETTE["door"], world=w)
        for x in (-.54, .54):
            b.box((x, .36, .358), (.09, .3, .015), PALETTE["banner"], world=w)
        for i in range(3):
            b.box((0, .04 + i * .055, .6 - i * .1), (.65, .08, .14), PALETTE["ivory"], world=w)
    def tower_parts(b, w):
        b.box((0, .62, 0), (.37, 1.24, .4), PALETTE["towerWall"], world=w)
        b.box((0, .7, 0), (.43, .04, .46), PALETTE["ivory"], world=w)
        # Heights follow the production tower (roof apex ≈ 1.68 above the base; finial to ≈ 1.735).
        b.box((0, 1.27, 0), (.44, .09, .47), PALETTE["towerRoof"], world=w)
        b.cone((0, 1.43, 0), (.6, .5, .6), PALETTE["towerRoofTop"], segments=8, world=w)
        b.sphere((0, 1.7, 0), (.07, .07, .07), PALETTE["ivory"], world=w)
        b.box((0, .9, .206), (.26, .26, .025), PALETTE["window"], world=w)
        b.box((0, .15, .205), (.14, .3, .02), PALETTE["door"], world=w)
        b.ring((0, 1.14, .206), (.16, .16, .16), PALETTE["ivory"], rot=(math.pi / 2, 0, 0), world=w)
        b.box((0, 1.14, .21), (.04, .04, .01), PALETTE["hand"], world=w)
    def monument_parts(b, w):
        b.cylinder((0, .13, 0), (.4, .26, .4), PALETTE["pedestal"], world=w)
        b.box((-.11, .32, 0), (.23, .045, .3), PALETTE["book"], rot=(0, 0, -.22), world=w)
        b.box((.11, .32, 0), (.23, .045, .3), PALETTE["book"], rot=(0, 0, .22), world=w)

    def measure(parts_fn):
        b = Builder(); parts_fn(b, Matrix.Identity(4))
        xs = [v.co.x for v in b.bm.verts]; ys = [v.co.z for v in b.bm.verts]; zs = [-v.co.y for v in b.bm.verts]
        b.bm.free()
        cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
        return dict(cx=cx, cz=cz, footprint=math.hypot((max(xs) - min(xs)) / 2, (max(zs) - min(zs)) / 2), height=max(ys), base=min(ys))
    hall_m, tower_m, monument_m = measure(hall_parts), measure(tower_parts), measure(monument_parts)
    for m in (hall_m, tower_m, monument_m):
        assert abs(m["base"]) < 1e-6, m

    # ---- terraces (cut-and-fill platforms; the only steps are 0.015 kerbs)
    def make_terrace(key, radius):
        drop = R - math.sqrt(R * R - radius * radius); top = -0.35 * drop
        rim = max(0.0, plane_height(top, radius / R) - KERB)
        blend = max(0.45, 1.5 * rim / math.tan(math.radians(DESIGN_SLOPE)))
        return dict(id=f"terrace-{key}", radius=radius, top=top, blend=blend, rim=rim, frame=site_frame(key, R + top), drop=drop)
    hall_fp, tower_fp = hall_m["footprint"] + 0.06, tower_m["footprint"] + 0.06
    terraces = [make_terrace("hall", hall_fp + 0.08), make_terrace("tower", tower_fp + 0.3)]
    hall_t, tower_t = terraces
    terrace_centres = [t["frame"].up for t in terraces]

    def base(d):
        height = 0.0
        for t in terraces:
            theta = angle(d, t["frame"].up); s = R * theta
            if s <= t["radius"]:
                top = plane_height(t["top"], theta)
                return top, top - KERB - TERRACE_SINK, t["id"]
            if s < t["radius"] + t["blend"]:
                height = max(height, t["rim"] * (1 - smooth((s - t["radius"]) / t["blend"])))
        return height, height, None
    nav_h = lambda d: base(d)[0]

    # ---- plaza, monument, routes
    plaza_f = site_frame("plaza"); plaza_r = 0.95; plaza_c = plaza_f.up
    monument_dir = plaza_f.offset_dir(-0.15, -0.66)
    monument_f = Frame(monument_dir, R + PAVING_LIFT, plaza_c - monument_dir)

    routes = []
    n_loop = max(48, math.ceil(2 * math.pi * R * math.cos(math.radians(LOOP_LAT)) / 0.12))
    routes.append(dict(id="loop", width=PRIMARY, dirs=[direction(i / n_loop * 360, LOOP_LAT) for i in range(n_loop + 1)]))
    def spur(id_, lon, target, end):
        frm = direction(lon, LOOP_LAT)
        start = toward(frm, target, PRIMARY / 2 - 0.03); finish = toward(target, frm, end)
        length = R * angle(start, finish); steps = max(2, math.ceil(length / 0.1))
        routes.append(dict(id=id_, width=SECONDARY, dirs=[toward(start, finish, length * i / steps) for i in range(steps + 1)]))
    spur("spur-hall", SITES["hall"][0], hall_t["frame"].up, hall_t["radius"] - 0.02)
    spur("spur-tower", SITES["tower"][0], tower_t["frame"].up, tower_t["radius"] - 0.02)
    marker_r, pond_r = 0.42, 0.6
    spur("spur-marker", SITES["marker"][0], site_dir["marker"], marker_r + 0.04)
    spur("spur-pond", SITES["pond"][0], site_dir["pond"], pond_r)

    flats = [("pond", site_dir["pond"], pond_r + 0.05), ("marker", site_dir["marker"], marker_r + 0.05)]
    zones = [(d, rt["width"] / 2 + 0.03) for rt in routes for d in rt["dirs"]] + [(plaza_c, plaza_r)] \
        + [(t["frame"].up, t["radius"] + t["blend"]) for t in terraces] + [(d, r_) for _, d, r_ in flats]
    hills = [(direction(a, b), h, s) for a, b, h, s in HILLS]
    JITTER = 0.014
    def decorative(d):
        dist = min(arc(d, c) - r_ for c, r_ in zones)
        mask = smooth((dist - 0.12) / 0.45)
        if mask <= 0: return 0.0
        v = sum(h * math.exp(-((arc(d, c) / s) ** 2)) for c, h, s in hills)
        hsh = abs(math.sin(d.x * 127.1 + d.y * 311.7 + d.z * 74.7) * 43758.5453) % 1
        return (v + JITTER * (hsh * 2 - 1)) * mask
    ground = lambda d: base(d)[1] + decorative(d)

    # ---- terrain (Gateway-space verts, then BVH for facet sampling)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=TERRAIN_SUBDIV, radius=1.0)
    g_verts, faces = [], []
    for v in bm.verts:
        d = Vector((v.co.x, v.co.z, -v.co.y)).normalized()   # bmesh Z-up -> Gateway Y-up
        g_verts.append(d * (R + ground(d)))
    for f in bm.faces:
        faces.append(tuple(l.vert.index for l in f.loops))
    bm.free()
    bvh = BVHTree.FromPolygons([tuple(v) for v in g_verts], faces)
    def height_at(d):
        hit = bvh.ray_cast(Vector((0, 0, 0)), d, R * 2)
        return hit[0].length if hit and hit[0] else R + ground(d)

    colour = {k: hex_lin(PALETTE[k]) for k in ("lawn", "meadow", "meadowLight", "meadowDeep", "grove", "heath", "earth", "rockGround", "sand")}
    districts = [(hall_t["frame"].up, hall_t["radius"] + hall_t["blend"]), (plaza_c, plaza_r), (tower_t["frame"].up, tower_t["radius"] + tower_t["blend"])]
    groves = [site_dir[k] for k in ("grove-far", "orchard", "meadow-north")]
    def patches(n):
        return (math.sin(n.x * 3.1 + n.y * 1.7 + 0.6) + math.sin(n.z * 2.6 - n.x * 1.9 + 1.4) + math.sin(n.y * 3.7 + n.z * 1.3 - 0.4)) / 3
    terrain = Builder()
    tverts = [terrain.bm.verts.new(C @ v) for v in g_verts]
    for fi, f in enumerate(faces):
        face = terrain.bm.faces.new([tverts[i] for i in f]); face.smooth = False
        cen = sum((g_verts[i] for i in f), Vector()) / 3
        height = cen.length - R; n = cen.normalized(); lat = math.degrees(math.asin(max(-1, min(1, n.y))))
        hsh = abs(math.sin(fi * 3 * 12.9898) * 43758.5453) % 1; patch = patches(n)
        c = lerp(colour["meadow"], colour["meadowDeep"] if patch < 0 else colour["meadowLight"], min(1, abs(patch) * 1.6) * 0.75)
        c = lerp(c, colour["meadowLight"], max(0, height) * 2.2)
        c = lerp(c, colour["lawn"], max(1 - smooth((arc(n, dd) - rr) / 0.9) for dd, rr in districts) * 0.7)
        c = lerp(c, colour["grove"], max(1 - smooth((arc(n, g) - 0.3) / 0.7) for g in groves) * 0.6)
        c = lerp(c, colour["sand"], (1 - smooth((arc(n, site_dir["pond"]) - 0.62) / 0.35)) * 0.8)
        c = lerp(c, colour["heath"], smooth((-lat - 4 + patch * 12) / 18) * 0.8)
        c = lerp(c, colour["earth"], smooth((-lat - 32 + patch * 10) / 18) * 0.65 + max(0, -height) * 3)
        c = lerp(c, colour["rockGround"], smooth((-lat - 58) / 18) * 0.8)
        c = offset_l(c, (hsh - 0.5) * 0.04)
        for loop in face.loops:
            loop[terrain.col] = (c[0], c[1], c[2], 1.0)
    terrain_ob = terrain.to_object("LEARNING_TERRAIN", cols["LEARNING_VISUAL"], mat)

    # ---- paths (ribbons on the facets) + plaza + pond paving: one batch
    paths = Builder()
    surf = [hex_lin(PALETTE["path"]), hex_lin(PALETTE["pathAlt"])]; kerb = hex_lin(PALETTE["kerb"])
    for rt in routes:
        dirs = rt["dirs"]; lift = PAVING_LIFT if rt["id"] == "loop" else PAVING_LIFT - 0.002
        across = [(-rt["width"] / 2 - 0.03, -0.004), (-rt["width"] / 2, 0.006), (rt["width"] / 2, 0.006), (rt["width"] / 2 + 0.03, -0.004)]
        rows = []
        for i, d in enumerate(dirs):
            prev, nxt = dirs[max(0, i - 1)], dirs[min(len(dirs) - 1, i + 1)]
            side = d.cross(nxt - prev).normalized()
            row = []
            for off, raise_ in across:
                p = (d * R + side * off).normalized()
                row.append(p * (height_at(p) + lift + raise_))
            rows.append(row)
        for i in range(1, len(rows)):
            if arc(dirs[i], plaza_c) < plaza_r - 0.04 and arc(dirs[i - 1], plaza_c) < plaza_r - 0.04:
                continue
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
    pc = {k: hex_lin(PALETTE[k]) for k in ("plaza", "inlay", "landing", "kerb")}
    cap(plaza_f, pr, lambda ring, s: pc["landing"] if ring == 4 else pc["kerb"] if ring == len(pr) - 1 else pc["inlay"] if ring in (6, 7) and s % 3 == 0 else pc["plaza"], PAVING_LIFT + 0.004)
    pond_f = site_frame("pond"); water = hex_lin(PALETTE["water"]); deep = offset_l(water, -0.04); sand = hex_lin(PALETTE["sand"])
    cap(pond_f, [0, 0.22, 0.4, pond_r * 0.8, pond_r], lambda ring, s: deep if ring <= 2 else water if ring == 3 else sand, PAVING_LIFT, 18)
    paths_ob = paths.to_object("LEARNING_PATHS_PAVING", cols["LEARNING_PATHS"], mat)

    # ---- buildings as separate objects (origin at the base, orientation = surface frame)
    buildings = []
    def place_building(name, parts_fn, m, frame, structure_id, landmark_hint):
        b = Builder()
        parts_fn(b, Matrix.Translation(Vector((-m["cx"], 0, -m["cz"]))))
        mw = C4 @ frame.world() @ C4i
        ob = b.to_object(name, cols["LEARNING_BUILDINGS"], mat, mw)
        ob["structure_id"] = structure_id          # the production structure id only (public geometry identity)
        ob["footprint_radius"] = m["footprint"]
        buildings.append(dict(id=structure_id, name=name, frame=frame, footprint=m["footprint"], height=m["height"], landmark=landmark_hint, ob=ob))
        return ob
    place_building("ACADEMY_HALL", hall_parts, hall_m, hall_t["frame"], "academy-hall", "landmark-javascriptia")
    place_building("ACADEMY_TOWER", tower_parts, tower_m, tower_t["frame"], "academy-tower", "landmark-kodestep")
    place_building("BOOK_MONUMENT", monument_parts, monument_m, monument_f, "book-monument", None)
    hall_fp_eff, tower_fp_eff = hall_fp, tower_fp
    obstacles = [dict(id="academy-hall", kind="structure", dir=hall_t["frame"].up, radius=hall_fp, height=hall_m["height"]),
                 dict(id="academy-tower", kind="structure", dir=tower_t["frame"].up, radius=tower_fp, height=tower_m["height"]),
                 dict(id="book-monument", kind="structure", dir=monument_dir, radius=monument_m["footprint"], height=monument_m["height"])]

    # ---- decorations (merged) and accents (merged, emissive)
    decor, accents = Builder(), Builder()
    for t in terraces:   # terrace slabs: decagon capstone over a darker base, in the terrace frame
        outer = t["radius"] / math.cos(math.pi / 10) * 2; depth = KERB + EMBED + 0.03; w = t["frame"].world()
        decor.cylinder((0, -depth / 2 - 0.006, 0), (outer, depth - 0.012, outer), PALETTE["sandstoneDark"], world=w)
        decor.cylinder((0, -0.006, 0), (outer, 0.012, outer), PALETTE["sandstone"], world=w)

    def fits(d, radius, kind="scenery"):
        for rt in routes:
            for p in rt["dirs"]:
                if arc(d, p) - rt["width"] / 2 - radius < 0.4: return False
        if arc(d, plaza_c) - plaza_r - radius < 0.1: return False
        for t in terraces:
            if arc(d, t["frame"].up) - t["radius"] - radius < 0.05: return False
        for o in obstacles:
            need = PRIMARY if o["kind"] == "structure" else (SECONDARY if (o["kind"] == "decor" or kind == "decor") else 0)
            if arc(d, o["dir"]) - o["radius"] - radius < need: return False
        return True
    def cone_tree(b, w, h, color, width=0.36):
        b.cylinder((0, .1, 0), (.07, .2, .07), PALETTE["trunk"], world=w); b.cone((0, .17 + h / 2, 0), (width, h, width), color, world=w)
    def round_tree(b, w, s, color):
        b.cylinder((0, .11, 0), (.07, .22, .07), PALETTE["trunk"], world=w); b.rock((0, .2 + s * .42, 0), (s, s * .9, s), color, world=w)
    def shrub(b, w, s, color): b.rock((0, s * .28, 0), (s, s * .62, s), color, world=w)
    def stone(b, w, size, color): b.rock((0, size[1] * .32, 0), size, color, world=w)
    def reed(b, w, h): b.cone((0, h / 2, 0), (.055, h, .055), PALETTE["reed"], world=w)
    def item_radius(fn, *args):
        b = Builder(); fn(b, Matrix.Identity(4), *args)
        rr = max(math.hypot(v.co.x, v.co.y) for v in b.bm.verts); hh = max(v.co.z for v in b.bm.verts); b.bm.free()
        return rr, hh
    def cluster(id_, frame, items):
        hint = frame.forward
        for idx, (x, z, fn, args) in enumerate(items):
            item_id = f"{id_}-{idx + 1}" if len(items) > 1 else id_
            d = frame.offset_dir(x, z); rr, hh = item_radius(fn, *args)
            if not fits(d, rr):
                report["skipped"].append(item_id); continue
            f = Frame(d, R + ground(d) - 0.02, hint)
            fn(decor, f.world(), *args)
            obstacles.append(dict(id=item_id, kind="scenery", dir=d, radius=rr, height=hh))
    def frame_off(frame, x, z, hint=None):
        d = frame.offset_dir(x, z)
        return Frame(d, R, hint if hint is not None else frame.forward)
    hf, tf = hall_t["frame"], tower_t["frame"]
    cluster("academy-cypresses", frame_off(hf, 0, -(hall_t["radius"] + 0.55)), [(-.62, .06, cone_tree, (.62, PALETTE["foliage"], .26)), (0, -.06, cone_tree, (.74, PALETTE["grove"], .28)), (.6, .08, cone_tree, (.56, PALETTE["foliage"], .26))])
    cluster("academy-shrubs-left", frame_off(hf, -(hall_t["radius"] + 0.5), .25), [(0, 0, shrub, (.22, PALETTE["foliageWarm"]))])
    cluster("academy-shrubs-right", frame_off(hf, hall_t["radius"] + 0.5, .25), [(0, 0, shrub, (.2, PALETTE["foliageOlive"]))])
    cluster("tower-trees", frame_off(tf, .1, -(tower_t["radius"] + 0.42)), [(-.24, 0, round_tree, (.36, PALETTE["foliage"])), (.26, .08, round_tree, (.3, PALETTE["foliageWarm"]))])
    pond_reeds = frame_off(pond_f, .45, .5)
    cluster("pond-reeds", pond_reeds, [(0, 0, reed, (.2,)), (.09, .05, reed, (.16,)), (-.07, .08, reed, (.18,))])
    cluster("grove-far", site_frame("grove-far"), [(-.24, 0, cone_tree, (.6, PALETTE["foliage"])), (.2, .16, cone_tree, (.48, PALETTE["foliageOlive"])), (.06, -.26, round_tree, (.34, PALETTE["grove"]))])
    cluster("orchard", site_frame("orchard"), [(-.25, -.15, round_tree, (.32, PALETTE["foliageWarm"])), (.22, -.2, round_tree, (.3, PALETTE["foliage"])), (-.18, .25, round_tree, (.3, PALETTE["foliage"])), (.27, .2, round_tree, (.34, PALETTE["foliageOlive"]))])
    cluster("meadow-north", site_frame("meadow-north"), [(-.15, 0, cone_tree, (.5, PALETTE["grove"])), (.22, .12, shrub, (.22, PALETTE["foliageWarm"]))])
    cluster("rocks-south", site_frame("rocks-south"), [(0, 0, stone, ((.42, .34, .36), PALETTE["rock"])), (.32, .12, stone, ((.24, .2, .22), PALETTE["rockDark"])), (-.28, .18, shrub, (.2, PALETTE["foliageOlive"]))])
    cluster("heath-south", site_frame("heath-south"), [(-.15, 0, shrub, (.24, PALETTE["foliageOlive"])), (.16, .1, shrub, (.18, PALETTE["foliageWarm"])), (.05, -.22, stone, ((.22, .18, .2), PALETTE["rock"]))])
    cluster("rocks-west", site_frame("rocks-west"), [(0, 0, stone, ((.36, .3, .32), PALETTE["rockDark"])), (.34, -.1, stone, ((.2, .16, .18), PALETTE["rock"]))])
    cluster("shrubs-south", site_frame("shrubs-south"), [(-.12, 0, shrub, (.22, PALETTE["foliage"])), (.18, .06, round_tree, (.3, PALETTE["foliageOlive"]))])
    cluster("garden-front", site_frame("garden-front"), [(-.2, 0, round_tree, (.34, PALETTE["foliage"])), (.2, .1, round_tree, (.28, PALETTE["foliageWarm"])), (.02, .3, shrub, (.2, PALETTE["foliageOlive"]))])
    cluster("rocks-front", site_frame("rocks-front"), [(0, 0, stone, ((.3, .24, .26), PALETTE["rock"])), (.3, .08, shrub, (.2, PALETTE["foliageWarm"]))])

    accent_list = []
    def accent(id_, district, d, radius, height, decor_fn, glow_fn, lift=-0.01, hint=None, on_plaza=False):
        # Plaza-rim accents sit on the paving by design; they must still clear the landing circle (measured below).
        ok = (arc(d, plaza_c) - radius >= LANDING_CLEAR + 0.1 and arc(d, plaza_c) + radius <= plaza_r) if on_plaza else fits(d, radius, "decor")
        if not ok:
            report["skipped"].append(id_); return
        f = Frame(d, R + ground(d) + lift, hint if hint is not None else south(d))
        decor_fn(decor, f.world()); glow_fn(accents, f.world())
        obstacles.append(dict(id=id_, kind="decor", dir=d, radius=radius, height=height))
        accent_list.append(dict(id=id_, district=district, origin=list(f.origin), up=list(f.up)))
    book_d = hf.offset_dir(-0.78, hall_t["radius"] + 0.42)
    accent("accent-floating-book", "academy", book_d, 0.13, 0.38,
           lambda b, w: (b.cylinder((0, .09, 0), (.15, .18, .15), PALETTE["sandstoneDark"], world=w), b.box((0, .19, 0), (.2, .03, .16), PALETTE["sandstone"], world=w), b.box((0, .335, 0), (.25, .012, .17), PALETTE["cover"], rot=(.18, 0, 0), world=w)),
           lambda b, w: (b.box((-.058, .352, 0), (.11, .012, .15), PALETTE["page"], rot=(.18, 0, -.22), world=w), b.box((.058, .352, 0), (.11, .012, .15), PALETTE["page"], rot=(.18, 0, .22), world=w)),
           hint=hf.up - book_d)
    crystal_d = tf.offset_dir(-(tower_t["radius"] + 0.24), -0.2)
    accent("accent-knowledge-crystal", "tower", crystal_d, 0.09, 0.36,
           lambda b, w: b.cylinder((0, .03, 0), (.17, .08, .17), PALETTE["sandstoneDark"], world=w),
           lambda b, w: (b.rock((0, .21, 0), (.11, .3, .11), PALETTE["crystal"], world=w), b.rock((.05, .12, .03), (.055, .13, .055), PALETTE["crystal"], rot=(0, 0, -.35), world=w)),
           hint=tf.forward)
    term_d = plaza_f.offset_dir(0.35, 0.62)
    accent("accent-learning-terminal", "landing", term_d, 0.12, 0.32,
           lambda b, w: (b.box((0, .11, 0), (.12, .22, .08), PALETTE["slate"], world=w), b.box((0, .245, -.012), (.2, .14, .02), PALETTE["screenBack"], rot=(-.6, 0, 0), world=w)),
           lambda b, w: b.box((0, .25, -.003), (.17, .11, .012), PALETTE["screen"], rot=(-.6, 0, 0), world=w),
           lift=PAVING_LIFT - (ground(term_d)), hint=plaza_c - term_d, on_plaza=True)
    # Discovery marker (far district): standing stones around an engraved disc; environment only, no glow.
    mk = site_frame("marker"); mkf = Frame(mk.up, R + ground(mk.up) - 0.005, mk.forward); w = mkf.world()
    decor.cylinder((0, .006, 0), (.34, .012, .34), PALETTE["sandstone"], world=w)
    decor.ring((0, .014, 0), (.22, .22, .22), PALETTE["kerb"], rot=(math.pi / 2, 0, 0), world=w)
    for i in range(5):
        a = i / 5 * 2 * math.pi
        decor.box((math.sin(a) * .32, .1, math.cos(a) * .32), (.07, .24, .05), PALETTE["rock"], rot=(0, a, 0), world=w)
    obstacles.append(dict(id="discovery-marker", kind="decor", dir=mk.up, radius=marker_r, height=0.24))
    obstacles.append(dict(id="pond", kind="scenery", dir=pond_f.up, radius=pond_r, height=0.02))
    accent_list.append(dict(id="accent-discovery-marker", district="far", origin=list(mkf.origin), up=list(mkf.up)))
    decor_ob = decor.to_object("LEARNING_DECORATIONS_STATIC", cols["LEARNING_DECORATIONS"], mat)
    accents_ob = accents.to_object("LEARNING_ACCENTS_GLOW", cols["LEARNING_ACCENTS"], mat_accent)

    # ---- anchors (empties; names and roles only)
    def on_nav(d):
        d = d.normalized(); return d * (R + nav_h(d))
    def empty(name, frame_or_point, role, radius=None, display="PLAIN_AXES", size=0.15, hint=None):
        ob = bpy.data.objects.new(name, None)
        ob.empty_display_type = display; ob.empty_display_size = size
        if isinstance(frame_or_point, Frame):
            ob.matrix_world = C4 @ frame_or_point.world() @ C4i
        else:
            p = Vector(frame_or_point); f = Frame(p, p.length, hint if hint is not None else south(p.normalized()))
            ob.matrix_world = C4 @ f.world() @ C4i
        ob["role"] = role
        if radius is not None: ob["radius"] = float(radius)
        cols["LEARNING_ANCHORS"].objects.link(ob)
        return ob
    def terrace_door(t, depth): return t["frame"].origin + t["frame"].forward * depth
    hall_door = on_nav(terrace_door(hall_t, hall_m["footprint"] + 0.12))
    tower_door = on_nav(terrace_door(tower_t, tower_m["footprint"] + 0.12))
    monument_point = on_nav(monument_f.origin + monument_f.forward * (monument_m["footprint"] + 0.08))
    spawn_d = toward(plaza_c, hf.up, -0.12)
    spawn_f = Frame(spawn_d, R + PAVING_LIFT, hf.up - spawn_d)
    anchors = {
        "ANCHOR_interaction_academy_hall": empty("ANCHOR_interaction_academy_hall", hall_door, "interaction:academy-hall", hint=hf.up - hall_door.normalized()),
        "ANCHOR_interaction_academy_tower": empty("ANCHOR_interaction_academy_tower", tower_door, "interaction:academy-tower", hint=tf.up - tower_door.normalized()),
        "ANCHOR_interaction_book_monument": empty("ANCHOR_interaction_book_monument", monument_point, "interaction:book-monument", hint=monument_dir - monument_point.normalized()),
        "ANCHOR_landing": empty("ANCHOR_landing", Frame(plaza_c, R + PAVING_LIFT, south(plaza_c)), "landing", LANDING_CLEAR, "CIRCLE", LANDING_CLEAR),
        "ANCHOR_spawn": empty("ANCHOR_spawn", spawn_f, "spawn", display="ARROWS", size=0.12),
        "ANCHOR_lander_arrival": empty("ANCHOR_lander_arrival", Frame(plaza_c, R + 1.5 * H, south(plaza_c)), "lander-arrival", LANDING_CLEAR, "SPHERE", 0.2),
        "ANCHOR_minigame_candidate": empty("ANCHOR_minigame_candidate", Frame(monument_dir, R + PAVING_LIFT, plaza_c - monument_dir), "minigame-candidate", 0.35, "CIRCLE", 0.35),
    }
    for ob in anchors.values():
        ob.empty_display_type = ob.empty_display_type  # keep; circles are drawn in local XY (tangent plane)

    # ---- navigation reference (kept in the .blend; not exported)
    nav = Builder()
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=NAV_SUBDIV, radius=1.0)
    nv = []
    for v in bm.verts:
        d = Vector((v.co.x, v.co.z, -v.co.y)).normalized(); nv.append(nav.bm.verts.new(C @ (d * (R + nav_h(d)))))
    grey = (0.35, 0.4, 0.5)
    for f in bm.faces:
        face = nav.bm.faces.new([nv[l.vert.index] for l in f.loops]); face.smooth = False
        for loop in face.loops: loop[nav.col] = (grey[0], grey[1], grey[2], 1.0)
    bm.free()
    nav_mat = diorama_material("LearningNavigationReference")
    nav_ob = nav.to_object("NAV_SURFACE", cols["LEARNING_NAVIGATION_REFERENCE"], nav_mat); nav_ob.display_type = 'WIRE'; nav_ob.hide_render = True
    def polyline(name, points_g, closed=False):
        me = bpy.data.meshes.new(name); verts = [C @ p for p in points_g]
        edges = [(i, i + 1) for i in range(len(verts) - 1)] + ([(len(verts) - 1, 0)] if closed else [])
        me.from_pydata(verts, edges, []); ob = bpy.data.objects.new(name, me); cols["LEARNING_NAVIGATION_REFERENCE"].objects.link(ob); ob.hide_render = True
        return ob
    path_data = []
    for rt in routes:
        pts = [on_nav(d) for d in rt["dirs"]]
        ob = polyline(f"NAV_route_{rt['id']}", pts); ob["width"] = rt["width"]
        path_data.append(dict(id=rt["id"], width=rt["width"], points=[list(p) for p in pts]))
    for o in obstacles:
        f = Frame(o["dir"], R + nav_h(o["dir"]), south(o["dir"]))
        pts = [f.origin + (f.right * math.cos(a) + f.forward * math.sin(a)) * o["radius"] for a in [i / 24 * 2 * math.pi for i in range(24)]]
        polyline(f"NAV_footprint_{o['id']}", pts, True)
    lf = Frame(plaza_c, R + PAVING_LIFT, south(plaza_c))
    polyline("NAV_landing_clear", [lf.origin + (lf.right * math.cos(a) + lf.forward * math.sin(a)) * LANDING_CLEAR for a in [i / 32 * 2 * math.pi for i in range(32)]], True)

    # ---- measurements (same definitions as the procedural prototype)
    samples = [(rt["id"], rt["width"], d) for rt in routes for d in rt["dirs"]]
    path_clear, path_at = 1e9, ""
    for rid, w_, d in samples:
        if arc(d, plaza_c) < plaza_r: continue
        for o in obstacles:
            if (rid, o["id"]) in (("spur-hall", "academy-hall"), ("spur-tower", "academy-tower"), ("spur-pond", "pond"), ("spur-marker", "discovery-marker")): continue
            gap = arc(d, o["dir"]) - o["radius"] - w_ / 2
            if gap < path_clear: path_clear, path_at = gap, f"{rid} ↔ {o['id']}"
    bgap, bat, sgap, sat, ogap, oat = 1e9, "", 1e9, "", 1e9, ""
    for i in range(len(obstacles)):
        for j in range(i + 1, len(obstacles)):
            a, b_ = obstacles[i], obstacles[j]
            if a["kind"] == "scenery" and b_["kind"] == "scenery": continue
            gap = arc(a["dir"], b_["dir"]) - a["radius"] - b_["radius"]; at = f"{a['id']} ↔ {b_['id']}"
            if a["kind"] == "structure" and b_["kind"] == "structure":
                if gap < bgap: bgap, bat = gap, at
            elif (a["kind"] == "structure" or b_["kind"] == "structure") and gap < sgap: sgap, sat = gap, at
            if gap < ogap: ogap, oat = gap, at
    landing_clear = min(arc(plaza_c, o["dir"]) - o["radius"] for o in obstacles)
    def walkable(p):
        return min(min(arc(p, d) - w_ / 2 for _, w_, d in samples), arc(p, plaza_c) - plaza_r, min(arc(p, t["frame"].up) - t["radius"] for t in terraces))
    reach = {k: max(0.0, walkable(v)) for k, v in (("hall", hall_door), ("tower", tower_door), ("monument", monument_point))}
    max_slope, slope_at, max_step = 0.0, "", 0.0
    for rt in routes:
        dirs = rt["dirs"]
        for i in range(1, len(dirs)):
            steps = max(1, math.ceil(arc(dirs[i - 1], dirs[i]) / 0.01))
            for k in range(1, steps + 1):
                a = dirs[i - 1].lerp(dirs[i], (k - 1) / steps).normalized(); b_ = dirs[i - 1].lerp(dirs[i], k / steps).normalized()
                ha, hb = base(a), base(b_); run = arc(a, b_)
                if ha[2] != hb[2]: max_step = max(max_step, abs(hb[0] - ha[0]))
                elif run > 0:
                    sl = math.degrees(math.atan(abs(hb[0] - ha[0]) / run))
                    if sl > max_slope: max_slope, slope_at = sl, rt["id"]
    landing_drop = R - math.sqrt(R * R - LANDING_CLEAR ** 2)
    # visual extent for calibration (bounding sphere about the origin, in Gateway space)
    extent = 0.0
    for ob in list(cols["LEARNING_VISUAL"].objects) + list(cols["LEARNING_PATHS"].objects) + list(cols["LEARNING_BUILDINGS"].objects) + list(cols["LEARNING_DECORATIONS"].objects) + list(cols["LEARNING_ACCENTS"].objects):
        for v in ob.data.vertices:
            extent = max(extent, (ob.matrix_world @ v.co).length)
    measurements = dict(
        radius=R, radiusInH=R / H, scaleHint=None, extent=extent,
        hallFootprint=hall_m["footprint"], towerFootprint=tower_m["footprint"], monumentFootprint=monument_m["footprint"],
        hallHeight=hall_m["height"], towerHeight=tower_m["height"],
        terraces=[dict(id=t["id"], radius=t["radius"], top=t["top"], blend=t["blend"], rimBerm=t["rim"], curvatureDrop=t["drop"], kerb=KERB) for t in terraces],
        pathWidths={rt["id"]: rt["width"] for rt in routes},
        pathClearance=path_clear, pathClearanceAt=path_at, buildingGap=bgap, buildingGapAt=bat, structureGap=sgap, structureGapAt=sat,
        obstacleGap=ogap, obstacleGapAt=oat, landingClear=landing_clear, landingFlatness=landing_drop,
        maxRouteSlopeDegrees=max_slope, maxRouteSlopeAt=slope_at, maxRouteStep=max_step, anchorReach=reach,
        hallToTowerArc=arc(hf.up, tf.up), skippedDecor=report["skipped"], obstacleCount=len(obstacles),
        decorativeReliefOnPaths=max(abs(decorative(d)) for _, _, d in samples),
    )
    layout = dict(
        structures=[dict(id=b_["id"], object=b_["name"], landmarkHint=b_["landmark"], origin=list(b_["frame"].origin), up=list(b_["frame"].up), forward=list(b_["frame"].forward), footprintRadius=b_["footprint"], height=b_["height"]) for b_ in buildings],
        anchors={k: dict(origin=list(C4i @ v.matrix_world.translation), role=v["role"], radius=v.get("radius")) for k, v in anchors.items()},
        obstacles=[dict(id=o["id"], kind=o["kind"], center=list(o["dir"] * R), radius=o["radius"], height=o["height"]) for o in obstacles],
        paths=path_data, plaza=dict(center=list(plaza_c * R), radius=plaza_r), accents=accent_list,
        terraces=measurements["terraces"], collision=dict(kind="sphere-terraces", radius=R),
    )
    with open(os.path.join(ROOT, "references", "layout.json"), "w", encoding="utf-8") as fh: json.dump(layout, fh, indent=2)
    with open(os.path.join(ROOT, "references", "clearance-report.json"), "w", encoding="utf-8") as fh: json.dump(measurements, fh, indent=2)

    # scene stats
    stats = {}
    for col in cols.values():
        tris = sum(sum(len(p.vertices) - 2 for p in ob.data.polygons) for ob in col.objects if ob.type == 'MESH')
        stats[col.name] = dict(objects=len(col.objects), triangles=tris)
    report["stats"] = stats; report["measurements"] = {k: v for k, v in measurements.items() if k not in ("terraces", "pathWidths")}
    scene["gateway_asset"] = "learning-globe-blender"
    return scene, report

try:
    scene, report = build()
    print("BUILD OK")
    print(json.dumps(report["stats"]))
    print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in report["measurements"].items()}))
except Exception:
    print("BUILD FAILED"); print(traceback.format_exc())
