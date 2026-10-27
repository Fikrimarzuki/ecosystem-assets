"""M8.9b.5a — Products world v1, "Orbital Product City" (Optimistic Futuristic Innovation). Run inside the live Blender via Blender MCP.

A handcrafted low-poly futuristic miniature city on a rounded planet, crowned by the Culinary Spire and circled by a tilted orbital ring
(environmental geometry, not a landmark). Built in a dedicated scene PRODUCTS_V1 (the user's own scenes are never touched; rerunning
rebuilds it), authored in Gateway's local space: Y up, planet centre at the origin, base radius R = 4.2 local units (14 astronaut heights),
squashed to 94 % on Y, longitude measured from +Z toward +X; +Z is the front (toward the default inspection camera). Vertices are
converted to Blender's Z-up at creation and the glTF (+Y up) exporter converts them back. Deterministic: no random module, fixed noise
directions and a tiny LCG for scatter. Object names are prefixed PRODUCTS_ (Blender object names are global in a session that also holds
the other worlds' scenes).

Collections (layers):
  PRODUCTS_TERRAIN        the relief spheroid (one colour per face) and the plaza/landing paving
  PRODUCTS_PATHS          pedestrian paths (PRODUCTS_PATH_*): silver ribbons with a cyan conduit
  PRODUCTS_BUILDINGS      CULINARY_SPIRE, WEDDING_PAVILION, PLANNER_ATRIUM, PROTOTYPE_LAB, CARD_ARENA, INVENTORY_DEPOT (structure_id) and
                          INNOVATION_PLAZA (environment)
  PRODUCTS_ORBIT          ORBITAL_RING (environment:orbital-ring): the tilted ring with six stations and spokes-free clearance
  PRODUCTS_DECORATIONS    merged static scenery: crystal trees, light pylons, observation platforms, rocks, benches
  PRODUCTS_ACCENTS        merged emissive accents: windows, holograms, conduits, the ring's light band, the landing pad ring
  PRODUCTS_ANCHORS        empties PRODUCTS_ANCHOR_*: interactions, focus points, landing, spawn, lander arrival, mini-game candidate
  PRODUCTS_NAVIGATION_REFERENCE  the landing circle (kept in the .blend, not exported)
Project publication, landmark identity and permissions stay in Gateway; the asset carries only structure ids and anchor roles.
"""
import bpy, bmesh, math, json, os, colorsys
from mathutils import Vector, Matrix

ROOT = r"D:\Code\porto-projects\gateway-assets\planets\products"
SCENE = "PRODUCTS_V1"
R, SQUASH = 4.2, 0.94
TERRAIN_SUBDIV = 5
COLLECTIONS = ["PRODUCTS_TERRAIN", "PRODUCTS_PATHS", "PRODUCTS_BUILDINGS", "PRODUCTS_ORBIT", "PRODUCTS_DECORATIONS", "PRODUCTS_ACCENTS", "PRODUCTS_ANCHORS", "PRODUCTS_NAVIGATION_REFERENCE"]
C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))     # Gateway (x, y, z; Y up) -> Blender (x, -z, y; Z up)
C4 = C.to_4x4(); C4i = C4.inverted()
# The orbital ring: major radius, tube radius, tilt about X (front dips down) and about Z (−X side dips down: the rocket's parking side), Gateway space.
RING = dict(radius=6.3, tube=0.12, tilt_x=math.radians(26), tilt_z=math.radians(12), stations=6)

P = dict(ground="#7e8da8", groundLight="#98a6bd", lavender="#a89cd8", lavenderDeep="#8a7fc4", teal="#5fbfb8", tealLight="#8ad9d2", tealDeep="#3f9a94",
         pave="#d8dde6", paveDark="#b9c1cf", path="#cfd6e2", pathDark="#aab3c3", white="#f2f4f8", silver="#b8c0cc", steel="#7c8794", steelDark="#4f5864",
         glass="#9fd8e8", gold="#e0b85a", goldDark="#b08a35", navy="#2f3d55", violet="#b48cff", cyan="#5fe3ff", cyanPale="#bff3ff", warm="#ffd98a",
         coral="#ff8c7a", rock="#8c95a6", rockDark="#6a7383", cliff="#9aa3b4", cliffDark="#7a8395", water="#4aa5cc", ringBase="#c9d0da", ringDark="#8d97a6")
def srgb_to_linear(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def hex_lin(h): h = h.lstrip("#"); return [srgb_to_linear(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)]
def lerp(a, b, t): t = max(0.0, min(1.0, t)); return [a[i] + (b[i] - a[i]) * t for i in range(3)]
def shade(c, dl):
    h, l, s = colorsys.rgb_to_hls(*[max(0.0, min(1.0, x)) for x in c]); return list(colorsys.hls_to_rgb(h, max(0.0, min(1.0, l + dl)), s))
def smooth(x): t = max(0.0, min(1.0, x)); return t * t * (3 - 2 * t)
def direction(lon, lat):
    a, b = math.radians(lon), math.radians(lat); return Vector((math.cos(b) * math.sin(a), math.sin(b), math.cos(b) * math.cos(a)))
def angle(a, b): return math.acos(max(-1.0, min(1.0, a.normalized().dot(b.normalized()))))
def slerp(a, b, t):
    om = angle(a, b)
    if om < 1e-6: return a.normalized()
    return (a * math.sin((1 - t) * om) + b * math.sin(t * om)) / math.sin(om)

class LCG:
    def __init__(self, seed): self.s = seed & 0xffffffff
    def next(self): self.s = (1664525 * self.s + 1013904223) & 0xffffffff; return self.s / 0xffffffff
    def range(self, a, b): return a + (b - a) * self.next()

# ----------------------------------------------------------------------------- terrain relief (height above the base sphere, local units)
NOISE = [(direction(37, 21), 3.1, 0.095, 0.4), (direction(142, -33), 4.3, 0.075, 1.7), (direction(256, 58), 5.7, 0.050, 2.9),
         (direction(311, -12), 9.5, 0.028, 0.8), (direction(88, 67), 13.0, 0.016, 2.2)]
HILLS = [(176, 18, 0.36, 24), (118, -22, 0.28, 20), (262, 44, 0.26, 18), (30, -46, 0.22, 22), (212, -40, 0.24, 20), (95, 48, 0.18, 16), (200, 72, 0.2, 18)]
MESAS = [(150, 54, 0.58, 11, 3.5), (236, 30, 0.48, 9, 3.5)]                    # (lon, lat, height, flat radius deg, blend deg): cliffs
GULLY = (34, 6, -0.18, 5.5, 4)                                                  # the road crosses this by bridge
LAKE = (116, -30, -0.26, 12, 6)
# Plateaus: (lon, lat, height, flat radius deg, blend deg). v2 adds the far-side glade (no structure id, no landmark).
PLATEAUS = {"kingdom-castle": (10, 60, 0.16, 13, 7), "arcade-hall": (62, 16, 0.08, 11, 6), "scriptorium": (308, 20, 0.12, 9, 5),
            "portal-plaza": (0, -6, 0.02, 11, 5), "landing": (330, -2, 0.02, 7, 4), "green": (36, 36, 0.10, 9, 5), "glade": (192, 8, 0.05, 8, 5)}

def hill(d, lon, lat, h, sigma):
    a = math.degrees(angle(d, direction(lon, lat))); return h * math.exp(-(a * a) / (2 * sigma * sigma))
def plateau(d, lon, lat, h, flat, blend):
    a = math.degrees(angle(d, direction(lon, lat)))
    return None if a > flat + blend else (h, smooth(1 - (a - flat) / blend) if a > flat else 1.0)
def relief(d):
    h = sum(a * math.sin(f * d.dot(n) * 2.1 + ph) for n, f, a, ph in NOISE)
    h += sum(hill(d, *x) for x in HILLS) + hill(d, GULLY[0], GULLY[1], GULLY[2], GULLY[3])
    for lon, lat, hh, flat, blend in MESAS + [LAKE]:
        p = plateau(d, lon, lat, hh, flat, blend)
        if p: h = h + (p[0] - h) * p[1]
    for lon, lat, hh, flat, blend in PLATEAUS.values():
        p = plateau(d, lon, lat, hh, flat, blend)
        if p: h = h + (p[0] - h) * p[1]
    return h
def surface(d, lift=0.0):
    d = d.normalized(); p = d * (R + relief(d) + lift); return Vector((p.x, p.y * SQUASH, p.z))
def normal_at(d):
    p = surface(d); n = Vector((p.x, p.y / (SQUASH * SQUASH), p.z)); return n.normalized()
def slope(d):
    t1 = d.cross(Vector((0, 1, 0)))
    if t1.length < 1e-3: t1 = d.cross(Vector((1, 0, 0)))
    t1.normalize(); t2 = d.cross(t1).normalized(); e = 0.03; h0 = relief(d)
    gx = (relief((d + t1 * e).normalized()) - h0) / (R * e); gy = (relief((d + t2 * e).normalized()) - h0) / (R * e)
    return math.hypot(gx, gy)

class Frame:
    """Surface frame in Gateway space: columns right, up (surface normal), forward (toward `hint`, tangent)."""
    def __init__(self, d, hint=None, lift=0.0):
        self.origin = surface(d, lift); self.up = normal_at(d)
        h = (hint if hint is not None else Vector((0, 0, 1))).normalized()
        fwd = h - self.up * h.dot(self.up)
        if fwd.length < 1e-4: fwd = Vector((1, 0, 0)) - self.up * self.up.x
        self.forward = fwd.normalized(); self.right = self.up.cross(self.forward).normalized()
    def world(self):
        m = Matrix.Identity(4)
        for i, col in enumerate((self.right, self.up, self.forward)):
            m[0][i], m[1][i], m[2][i] = col.x, col.y, col.z
        m[0][3], m[1][3], m[2][3] = self.origin.x, self.origin.y, self.origin.z
        return m
    def blender(self): return C4 @ self.world() @ C4i

# ----------------------------------------------------------------------------- mesh builder (vertices in Gateway coordinates)
def part_matrix(pos, size, rot=(0, 0, 0)):
    return Matrix.Translation(Vector(pos)) @ Matrix.Rotation(rot[1], 4, 'Y') @ Matrix.Rotation(rot[0], 4, 'X') @ Matrix.Rotation(rot[2], 4, 'Z') @ Matrix.Diagonal((*size, 1))

class Builder:
    def __init__(self): self.bm = bmesh.new(); self.col = self.bm.loops.layers.color.new("Col"); self.tris = 0
    def _add(self, verts, faces, matrix, color):
        bv = [self.bm.verts.new(C @ (matrix @ Vector(v))) for v in verts]
        for f in faces:
            try: face = self.bm.faces.new([bv[i] for i in f])
            except ValueError: continue
            face.smooth = False; self.tris += len(f) - 2
            for loop in face.loops: loop[self.col] = (color[0], color[1], color[2], 1.0)
    def box(self, pos, size, color, rot=(0, 0, 0), world=Matrix.Identity(4)):
        v = [(x, y, z) for x in (-.5, .5) for y in (-.5, .5) for z in (-.5, .5)]
        f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        self._add(v, f, world @ part_matrix(pos, size, rot), color)
    def cylinder(self, pos, size, color, segments=10, rot=(0, 0, 0), world=Matrix.Identity(4), top=1.0):
        v, f = [], []
        for i in range(segments):
            a = 2 * math.pi * i / segments; v.append((.5 * math.cos(a), -.5, .5 * math.sin(a))); v.append((.5 * top * math.cos(a), .5, .5 * top * math.sin(a)))
        for i in range(segments):
            j = (i + 1) % segments; f.append((2 * i, 2 * i + 1, 2 * j + 1, 2 * j))
        f.append(tuple(2 * i for i in range(segments))[::-1]); f.append(tuple(2 * i + 1 for i in range(segments)))
        self._add(v, f, world @ part_matrix(pos, size, rot), color)
    def cone(self, pos, size, color, segments=8, rot=(0, 0, 0), world=Matrix.Identity(4)):
        v = [(.5 * math.cos(2 * math.pi * i / segments), -.5, .5 * math.sin(2 * math.pi * i / segments)) for i in range(segments)] + [(0, .5, 0)]
        f = [(i, segments, (i + 1) % segments) for i in range(segments)] + [tuple(range(segments))[::-1]]
        self._add(v, f, world @ part_matrix(pos, size, rot), color)
    def rock(self, pos, size, color, rot=(0, 0, 0), world=Matrix.Identity(4)):
        v = [(.5, 0, 0), (-.5, 0, 0), (0, .5, 0), (0, -.5, 0), (0, 0, .5), (0, 0, -.5)]
        f = [(0, 2, 4), (4, 2, 1), (1, 2, 5), (5, 2, 0), (4, 3, 0), (1, 3, 4), (5, 3, 1), (0, 3, 5)]
        self._add(v, f, world @ part_matrix(pos, size, rot), color)
    def blob(self, pos, size, color, subdiv=1, world=Matrix.Identity(4)):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=0.5)
        v = [tuple(x.co) for x in bm.verts]; f = [tuple(l.vert.index for l in face.loops) for face in bm.faces]; bm.free()
        self._add(v, f, world @ part_matrix(pos, size), color)
    def ring(self, pos, size, color, radial=6, tubular=20, tube=0.09, rot=(0, 0, 0), world=Matrix.Identity(4)):
        v, f = [], []
        for i in range(tubular):
            a = 2 * math.pi * i / tubular
            for j in range(radial):
                b = 2 * math.pi * j / radial; r = .5 + tube * math.cos(b)
                v.append((r * math.cos(a), tube * math.sin(b), r * math.sin(a)))
        for i in range(tubular):
            for j in range(radial):
                f.append((i * radial + j, ((i + 1) % tubular) * radial + j, ((i + 1) % tubular) * radial + (j + 1) % radial, i * radial + (j + 1) % radial))
        self._add(v, f, world @ part_matrix(pos, size, rot), color)
    def quad(self, pts, color):
        bv = [self.bm.verts.new(C @ p) for p in pts]
        try: face = self.bm.faces.new(bv)
        except ValueError: return
        face.smooth = False; self.tris += 2
        for loop in face.loops: loop[self.col] = (color[0], color[1], color[2], 1.0)
    def to_object(self, name, collection, material, matrix_world=None):
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-6)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        me = bpy.data.meshes.new(name); self.bm.to_mesh(me); self.bm.free()
        for p in me.polygons: p.use_smooth = False
        me.color_attributes.active_color_index = 0; me.color_attributes.render_color_index = 0
        me.materials.append(material)
        ob = bpy.data.objects.new(name, me)
        if matrix_world is not None: ob.matrix_world = matrix_world
        collection.objects.link(ob); return ob

def diorama_material(name, emissive=None, strength=0.9):
    mat = bpy.data.materials.get(name)
    if mat: return mat
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    attr = nodes.new("ShaderNodeVertexColor"); attr.layer_name = "Col"; attr.location = (-300, 0)
    links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.82; bsdf.inputs["Metallic"].default_value = 0.08
    if emissive:
        links.new(attr.outputs["Color"], bsdf.inputs["Emission Color"]); bsdf.inputs["Emission Strength"].default_value = strength
    return mat

# ----------------------------------------------------------------------------- scene
def reset_scene():
    old = bpy.data.scenes.get(SCENE)
    if old:
        for ob in list(old.objects): bpy.data.objects.remove(ob, do_unlink=True)
        for cname in COLLECTIONS:
            col = bpy.data.collections.get(cname)
            if col: bpy.data.collections.remove(col)
        bpy.data.scenes.remove(old)
    for me in [m for m in bpy.data.meshes if m.users == 0]: bpy.data.meshes.remove(me)
    scene = bpy.data.scenes.new(SCENE); cols = {}
    for name in COLLECTIONS:
        col = bpy.data.collections.new(name); scene.collection.children.link(col); cols[name] = col
    return scene, cols

# ----------------------------------------------------------------------------- structures (local Gateway frame: base at y = 0, +Z = front)
def culinary_spire(b):
    """Foodie Map (Culinary Discovery): the signature spire: a slender silver tower with three ring terraces and a floating culinary globe
    carrying map-pin markers; the city's beacon at the crown."""
    silver, white, teal, gold = hex_lin(P["silver"]), hex_lin(P["white"]), hex_lin(P["teal"]), hex_lin(P["gold"]); lav = hex_lin(P["lavender"])
    b.cylinder((0, 0.08, 0), (1.2, 0.16, 1.2), hex_lin(P["pave"]), 12); b.cylinder((0, 0.2, 0), (0.9, 0.08, 0.9), silver, 8)
    b.cylinder((0, 0.85, 0), (0.46, 1.3, 0.46), white, 8, top=0.62)
    for y, s in ((0.5, 0.95), (0.9, 0.8), (1.25, 0.66)):
        b.cylinder((0, y, 0), (s, 0.06, s), silver, 8); b.ring((0, y + 0.06, 0), (s * 0.96, 1, s * 0.96), gold, tube=0.03, tubular=12)
    b.cylinder((0, 1.6, 0), (0.22, 0.3, 0.22), silver, 6); b.box((0, 1.8, 0), (0.06, 0.4, 0.06), hex_lin(P["steel"]))
    b.blob((0, 2.12, 0), (0.56, 0.56, 0.56), teal, 1)                                                   # the culinary globe
    b.ring((0, 2.12, 0), (0.66, 1, 0.66), gold, tube=0.035, tubular=16, rot=(0.5, 0, 0))               # an orbit of flavour
    for (a, el) in ((0.3, 0.5), (2.2, 0.2), (4.1, 0.7), (5.4, -0.1)):                                  # map pins
        x, y, z = 0.3 * math.cos(el) * math.cos(a), 2.12 + 0.3 * math.sin(el), 0.3 * math.cos(el) * math.sin(a)
        b.cone((x * 1.25, y + 0.1 * math.sin(el), z * 1.25), (0.07, 0.14, 0.07), hex_lin(P["coral"]), 5)
        b.blob((x * 1.42, y + 0.14 * math.sin(el), z * 1.42), (0.08, 0.08, 0.08), hex_lin(P["coral"]), 0)
    b.box((0, 0.33, 0.44), (0.3, 0.42, 0.04), hex_lin(P["glass"])); b.box((0, 0.56, 0.45), (0.38, 0.05, 0.06), gold)
    for i in range(3): b.box((0, 0.03 - i * 0.0, 0.62 + i * 0.1), (0.5 + i * 0.05, 0.03, 0.1), lav)
    return dict(footprint=0.62, height=2.45)
def spire_accents(a, world):
    a.box((0, 0.33, 0.465), (0.24, 0.34, 0.01), hex_lin(P["cyanPale"]), world=world)
    for y in (0.5, 0.9, 1.25): a.ring((0, y + 0.03, 0), (0.98 - (y - 0.5) * 0.36, 1, 0.98 - (y - 0.5) * 0.36), hex_lin(P["cyan"]), tube=0.012, tubular=12, world=world)
    a.blob((0, 2.12, 0), (0.2, 0.2, 0.2), hex_lin(P["cyanPale"]), 0, world=world)

def wedding_pavilion(b):
    """Nikah Yuk (Wedding Marketplace): a white colonnaded pavilion under a lavender dome with a gold rim, an arch gate, garden rings and two
    showcase wings: the marketplace where vendors meet couples."""
    white, lav, gold, pave = hex_lin(P["white"]), hex_lin(P["lavender"]), hex_lin(P["gold"]), hex_lin(P["pave"]); glass = hex_lin(P["glass"])
    b.cylinder((0, 0.05, 0), (1.9, 0.1, 1.9), pave, 12); b.cylinder((0, 0.14, 0), (1.3, 0.08, 1.3), white, 10)
    for i in range(8):
        a = 2 * math.pi * i / 8; b.cylinder((0.55 * math.cos(a), 0.5, 0.55 * math.sin(a)), (0.09, 0.64, 0.09), white, 6)
    b.cylinder((0, 0.85, 0), (1.3, 0.08, 1.3), white, 10); b.ring((0, 0.9, 0), (1.26, 1, 1.26), gold, tube=0.03, tubular=14)
    b.blob((0, 0.9, 0), (1.1, 0.9, 1.1), lav, 1)                                                         # the dome (lower half hidden)
    b.box((0, 0.6, 0), (0.6, 0.8, 0.6), glass); b.blob((0, 1.42, 0), (0.12, 0.12, 0.12), gold, 0)
    for sx in (-1, 1):                                                                                  # showcase wings
        b.box((0.95 * sx, 0.28, -0.2), (0.6, 0.56, 0.7), white); b.box((0.95 * sx, 0.58, -0.2), (0.66, 0.06, 0.76), gold)
        b.box((0.95 * sx, 0.3, 0.16), (0.42, 0.36, 0.03), glass)
    # the arch gate at the front and garden rings
    for sx in (-1, 1): b.box((0.36 * sx, 0.36, 0.95), (0.08, 0.72, 0.08), white)
    b.ring((0, 0.72, 0.95), (0.8, 1, 0.8), gold, tube=0.05, tubular=12, rot=(math.pi / 2, 0, 0))
    for sx in (-1, 1): b.ring((0.62 * sx, 0.11, 0.62), (0.4, 1, 0.4), hex_lin(P["teal"]), tube=0.09, tubular=10)
    return dict(footprint=0.95, height=1.5)
def pavilion_accents(a, world):
    a.box((0, 0.6, 0.31), (0.4, 0.5, 0.01), hex_lin(P["warm"]), world=world)
    for sx in (-1, 1): a.box((0.95 * sx, 0.3, 0.175), (0.36, 0.3, 0.01), hex_lin(P["cyanPale"]), world=world)
    a.ring((0, 0.72, 0.95), (0.66, 1, 0.66), hex_lin(P["violet"]), tube=0.02, tubular=12, rot=(math.pi / 2, 0, 0), world=world)

def planner_atrium(b):
    """Nikah Kuy (Wedding Planning): a glass atrium in a white frame with a gold roof band, a planning wall of boards and a stepped entrance."""
    white, glass, gold, steel = hex_lin(P["white"]), hex_lin(P["glass"]), hex_lin(P["gold"]), hex_lin(P["steel"])
    b.cylinder((0, 0.05, 0), (1.7, 0.1, 1.7), hex_lin(P["pave"]), 10)
    b.box((0, 0.5, 0), (1.1, 0.9, 0.9), glass)
    for x in (-0.56, 0, 0.56): b.box((x, 0.5, 0.46), (0.06, 0.92, 0.06), white); b.box((x, 0.5, -0.46), (0.06, 0.92, 0.06), white)
    for z in (-0.46, 0.46): b.box((0, 0.95, z), (1.14, 0.06, 0.06), white)
    b.box((0, 0.98, 0), (1.18, 0.08, 0.98), white); b.box((0, 1.05, 0), (1.2, 0.05, 1.0), gold)
    b.cone((0, 1.3, 0), (0.8, 0.42, 0.7), hex_lin(P["lavender"]), 4, rot=(0, math.pi / 4, 0))
    b.box((-0.9, 0.42, 0), (0.5, 0.84, 0.6), white); b.box((-0.9, 0.86, 0), (0.56, 0.05, 0.66), gold)   # the planning wall / office
    for i in range(3): b.box((-0.65, 0.3 + i * 0.22, 0.0), (0.02, 0.14, 0.4), steel)
    for i in range(3): b.box((0, 0.015 + i * 0.0, 0.55 + i * 0.12), (0.7 - i * 0.05, 0.03, 0.12), hex_lin(P["silver"]))
    b.box((0, 0.32, 0.46), (0.32, 0.6, 0.03), hex_lin(P["steelDark"]))
    return dict(footprint=0.85, height=1.5)
def atrium_accents(a, world):
    for i in range(3): a.box((-0.64, 0.3 + i * 0.22, 0.0), (0.01, 0.1, 0.34), hex_lin(P["cyanPale"]) if i != 1 else hex_lin(P["warm"]), world=world)
    a.box((0, 0.5, 0), (0.5, 0.1, 0.5), hex_lin(P["violet"]), world=world)   # a glowing planning table inside the atrium

def prototype_lab(b):
    """Nikah Yuk Prototype: a small innovation laboratory: a cube lab on stilts, a scaffold frame around a half-built model, an antenna."""
    white, steel, teal, gold = hex_lin(P["white"]), hex_lin(P["steel"]), hex_lin(P["teal"]), hex_lin(P["gold"])
    b.cylinder((0, 0.04, 0), (1.3, 0.08, 1.3), hex_lin(P["pave"]), 8)
    for sx in (-1, 1):
        for sz in (-1, 1): b.box((0.28 * sx, 0.2, 0.28 * sz), (0.07, 0.4, 0.07), steel)
    b.box((0, 0.62, 0), (0.76, 0.5, 0.76), white); b.box((0, 0.9, 0), (0.82, 0.06, 0.82), teal)
    b.box((0, 0.6, 0.39), (0.4, 0.3, 0.02), hex_lin(P["glass"]))
    b.box((0.2, 1.1, 0.2), (0.03, 0.4, 0.03), steel); b.blob((0.2, 1.32, 0.2), (0.08, 0.08, 0.08), gold, 0)
    # the scaffold and the half-built prototype beside the lab
    for sx in (-1, 1):
        for sz in (-1, 1): b.box((0.9 + 0.22 * sx, 0.35, 0.22 * sz), (0.03, 0.7, 0.03), gold)
    for y in (0.35, 0.7): b.box((0.9, y, 0), (0.5, 0.025, 0.025), gold); b.box((0.9, y, 0), (0.025, 0.025, 0.5), gold)
    b.box((0.9, 0.2, 0), (0.28, 0.26, 0.28), hex_lin(P["lavender"])); b.box((0.9, 0.46, 0), (0.18, 0.2, 0.18), white)
    b.box((0, 0.1, 0.62), (0.44, 0.04, 0.3), hex_lin(P["silver"]))
    return dict(footprint=0.7, height=1.4)
def lab_accents(a, world):
    a.box((0, 0.6, 0.4), (0.34, 0.24, 0.01), hex_lin(P["cyanPale"]), world=world)
    a.blob((0.9, 0.62, 0), (0.1, 0.1, 0.1), hex_lin(P["cyan"]), 0, world=world)

def card_arena(b):
    """TCG Hub (TCG Tournaments): a hexagonal tournament arena with tiered seating and a holographic card rising from the centre."""
    white, silver, navy, gold = hex_lin(P["white"]), hex_lin(P["silver"]), hex_lin(P["navy"]), hex_lin(P["gold"])
    b.cylinder((0, 0.1, 0), (1.9, 0.2, 1.9), hex_lin(P["pave"]), 6); b.cylinder((0, 0.27, 0), (1.6, 0.14, 1.6), white, 6)
    b.cylinder((0, 0.41, 0), (1.3, 0.14, 1.3), silver, 6); b.cylinder((0, 0.55, 0), (1.0, 0.14, 1.0), white, 6)
    b.cylinder((0, 0.64, 0), (0.7, 0.06, 0.7), navy, 6)
    for i in range(6):                                                                                  # canopy masts and a light frame
        a = math.pi / 3 * i + math.pi / 6; b.box((0.85 * math.cos(a), 0.95, 0.85 * math.sin(a)), (0.05, 0.6, 0.05), silver)
    b.ring((0, 1.25, 0), (1.7, 1, 1.7), gold, tube=0.025, tubular=6)
    b.box((0, 0.9, 0), (0.36, 0.5, 0.04), hex_lin(P["violet"]), rot=(0, 0.4, 0))                       # the holographic card
    b.box((0, 0.9, 0), (0.3, 0.42, 0.045), hex_lin(P["lavender"]), rot=(0, 0.4, 0))
    b.box((0, 0.2, 1.0), (0.5, 0.2, 0.3), white); b.box((0, 0.33, 1.0), (0.56, 0.05, 0.36), gold)      # entrance booth
    return dict(footprint=0.95, height=1.35)
def arena_accents(a, world):
    a.box((0, 0.9, 0), (0.24, 0.34, 0.05), hex_lin(P["cyanPale"]), rot=(0, 0.4, 0), world=world)
    a.ring((0, 0.65, 0), (0.62, 1, 0.62), hex_lin(P["cyan"]), tube=0.02, tubular=6, world=world)

def inventory_depot(b):
    """Inventory: a logistics depot: a silver warehouse with a flat roof, stacked containers in three colours, a loading dock, a conveyor
    and a small sorting arm."""
    silver, white, steel, gold = hex_lin(P["silver"]), hex_lin(P["white"]), hex_lin(P["steel"]), hex_lin(P["gold"])
    b.cylinder((0, 0.05, 0), (1.8, 0.1, 1.8), hex_lin(P["pave"]), 10)
    b.box((-0.2, 0.42, -0.1), (1.2, 0.74, 0.9), silver); b.box((-0.2, 0.82, -0.1), (1.26, 0.06, 0.96), white)
    b.box((-0.2, 0.86, -0.1), (0.5, 0.08, 0.5), steel)
    b.box((-0.2, 0.3, 0.36), (0.5, 0.5, 0.02), hex_lin(P["steelDark"]))                                 # the loading door
    for i, (x, z, c) in enumerate(((0.7, -0.35, P["teal"]), (0.7, 0.05, P["lavender"]), (0.7, 0.45, P["gold"]), (0.7, -0.15, P["coral"]))):
        y = 0.16 if i < 3 else 0.48; b.box((x, y, z), (0.36, 0.3, 0.34), hex_lin(c))
    b.box((0.25, 0.12, 0.72), (1.0, 0.06, 0.26), steel)                                                 # conveyor
    for i in range(6): b.cylinder((-0.2 + i * 0.18, 0.16, 0.72), (0.05, 0.24, 0.05), silver, 5, rot=(math.pi / 2, 0, 0))
    b.box((-0.75, 0.5, 0.72), (0.06, 1.0, 0.06), gold); b.box((-0.55, 1.0, 0.72), (0.5, 0.05, 0.05), gold); b.box((-0.35, 0.86, 0.72), (0.12, 0.2, 0.12), steel)
    return dict(footprint=0.9, height=1.1)
def depot_accents(a, world):
    a.box((-0.2, 0.3, 0.37), (0.42, 0.42, 0.01), hex_lin(P["warm"]), world=world)
    a.box((0.25, 0.155, 0.72), (0.96, 0.005, 0.2), hex_lin(P["cyan"]), world=world)

def innovation_plaza(b):
    """The central plaza (environment): paved disc with a holographic fountain, four light pylons and benches; the city's meeting point."""
    pave, white, silver, gold = hex_lin(P["pave"]), hex_lin(P["white"]), hex_lin(P["silver"]), hex_lin(P["gold"])
    b.cylinder((0, 0.015, 0), (2.1, 0.03, 2.1), pave, 16); b.ring((0, 0.03, 0), (1.7, 1, 1.7), white, tube=0.02, tubular=16)
    b.cylinder((0, 0.08, 0), (0.7, 0.1, 0.7), silver, 10); b.cone((0, 0.45, 0), (0.34, 0.64, 0.34), hex_lin(P["glass"]), 8)
    for a_ in (0.8, 2.35, 3.95, 5.5):
        x, z = 0.78 * math.cos(a_), 0.78 * math.sin(a_)
        b.box((x, 0.4, z), (0.06, 0.8, 0.06), white); b.box((x, 0.82, z), (0.16, 0.06, 0.16), gold)
        b.box((x * 1.25, 0.1, z * 1.25), (0.3, 0.06, 0.12), silver, rot=(0, -a_, 0))
    return dict(footprint=1.0, height=0.9)
def plaza_accents(a, world):
    a.cone((0, 0.45, 0), (0.2, 0.5, 0.2), hex_lin(P["cyanPale"]), 8, world=world)
    for a_ in (0.8, 2.35, 3.95, 5.5): a.box((0.78 * math.cos(a_), 0.82, 0.78 * math.sin(a_)), (0.12, 0.04, 0.12), hex_lin(P["warm"]), world=world)

# ----------------------------------------------------------------------------- decoration pieces (world Gateway frame via `world`)
def crystal_tree(b, world, s=1.0, kind="teal"):
    """Futuristic vegetation: a slim white stem with stacked translucent canopy discs (teal) or a violet bulb."""
    stem = hex_lin(P["white"])
    b.cylinder((0, 0.18 * s, 0), (0.05 * s, 0.36 * s, 0.05 * s), stem, 5, world=world)
    if kind == "teal":
        for i, w in enumerate((0.42, 0.32, 0.2)): b.cylinder((0, (0.3 + 0.12 * i) * s, 0), (w * s, 0.05 * s, w * s), hex_lin(P["teal"] if i != 1 else P["tealLight"]), 6, world=world)
    else:
        b.blob((0, 0.46 * s, 0), (0.3 * s, 0.36 * s, 0.3 * s), hex_lin(P["violet"]), 1, world=world); b.blob((0, 0.62 * s, 0), (0.14 * s, 0.14 * s, 0.14 * s), hex_lin(P["lavender"]), 0, world=world)
def light_pylon(b, acc, world, h=0.8):
    b.box((0, h / 2, 0), (0.04, h, 0.04), hex_lin(P["white"]), world=world); b.box((0, h + 0.05, 0), (0.14, 0.1, 0.05), hex_lin(P["silver"]), world=world)
    acc.box((0, h + 0.05, 0.03), (0.1, 0.06, 0.01), hex_lin(P["cyanPale"]), world=world)
def observation_platform(b, acc, world):
    b.cylinder((0, 0.3, 0), (0.12, 0.6, 0.12), hex_lin(P["silver"]), 6, world=world); b.cylinder((0, 0.63, 0), (0.9, 0.06, 0.9), hex_lin(P["white"]), 10, world=world)
    b.ring((0, 0.84, 0), (0.84, 1, 0.84), hex_lin(P["silver"]), tube=0.02, tubular=10, world=world)
    for i in range(5): b.box((0.4 * math.cos(1.26 * i), 0.75, 0.4 * math.sin(1.26 * i)), (0.025, 0.24, 0.025), hex_lin(P["silver"]), world=world)
    acc.ring((0, 0.67, 0), (0.8, 1, 0.8), hex_lin(P["cyan"]), tube=0.012, tubular=10, world=world)
def rock(b, world, s=1.0):
    b.rock((0, 0.1 * s, 0), (0.4 * s, 0.26 * s, 0.32 * s), hex_lin(P["rock"]), rot=(0.2, 0.5, 0.1), world=world)
def bench(b, world):
    b.box((0, 0.12, 0), (0.36, 0.04, 0.14), hex_lin(P["white"]), world=world); b.box((0, 0.06, 0), (0.3, 0.08, 0.06), hex_lin(P["silver"]), world=world)
# ----------------------------------------------------------------------------- Products relief tables (override the shared defaults above)
NOISE = [(direction(48, 18), 3.3, 0.07, 0.6), (direction(150, -28), 4.6, 0.055, 1.4), (direction(262, 55), 6.1, 0.035, 2.6), (direction(318, -14), 9.8, 0.02, 0.9)]
HILLS = [(180, 20, 0.26, 22), (124, -24, 0.2, 18), (255, 46, 0.22, 18), (40, -48, 0.16, 20), (210, -40, 0.18, 20), (90, 50, 0.14, 16)]
MESAS = [(165, 58, 0.42, 10, 3.5)]
GULLY = (200, 2, -0.12, 5.0, 4)
LAKE = (140, -34, -0.2, 10, 5)
# Plateaus under structures: (lon, lat, height, flat radius deg, blend deg)
PLATEAUS = {"culinary-spire": (10, 62, 0.14, 11, 6), "wedding-pavilion": (58, 18, 0.1, 11, 6), "planner-atrium": (305, 22, 0.1, 10, 5),
            "prototype-lab": (340, -30, 0.08, 8, 5), "card-arena": (125, 32, 0.1, 11, 6), "inventory-depot": (235, 18, 0.08, 10, 5),
            "innovation-plaza": (0, -4, 0.03, 11, 5), "landing": (28, -24, 0.03, 7, 4), "obs-a": (180, 52, 0.06, 5, 4), "obs-b": (270, -22, 0.06, 5, 4)}

def field(d, a, b, ka, kb): return 0.5 + 0.5 * math.sin(d.dot(a) * ka) * math.sin(d.dot(b) * kb)
F_BASE = (direction(63, 14), direction(201, -40), 8.3, 6.1); F_LAV = (direction(300, 25), direction(110, -10), 5.1, 7.3); F_TEAL = (direction(20, -35), direction(250, 30), 6.7, 5.4)

def ring_frame():
    """The orbital ring's frame in Gateway space: a circle in local XZ, tilted about X then Z, centred on the planet."""
    return Matrix.Rotation(RING["tilt_z"], 4, 'Z') @ Matrix.Rotation(RING["tilt_x"], 4, 'X')
def ring_point(a, radial=0.0):
    m = ring_frame(); r = RING["radius"] + radial
    return (m @ Vector((r * math.cos(a), 0, r * math.sin(a)))).to_3d()

# ----------------------------------------------------------------------------- build
def build():
    scene, cols = reset_scene()
    mat, accent = diorama_material("ProductsDiorama"), diorama_material("ProductsAccent", emissive=True)
    rng = LCG(20261023)
    layout = dict(version=1, world="products", planet=dict(radius=R, squash=SQUASH, up="+Y", longitude="from +Z toward +X"),
                  ring=dict(radius=RING["radius"], tube=RING["tube"], tilt_x_deg=round(math.degrees(RING["tilt_x"]), 2), tilt_z_deg=round(math.degrees(RING["tilt_z"]), 2), stations=RING["stations"]),
                  structures=[], anchors={}, routes=[], decorations={})

    # --- terrain: icosphere displaced by relief, squashed, one colour per face from region + patch fields
    b = Builder(); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=TERRAIN_SUBDIV, radius=1.0)
    verts = [Vector((v.co.x, v.co.z, -v.co.y)).normalized() for v in bm.verts]
    faces = [tuple(l.vert.index for l in f.loops) for f in bm.faces]; bm.free()
    lake_dir = direction(LAKE[0], LAKE[1]); crown = direction(PLATEAUS["culinary-spire"][0], PLATEAUS["culinary-spire"][1])
    def terrain_color(d):
        h = relief(d)
        c = lerp(hex_lin(P["ground"]), hex_lin(P["groundLight"]), field(d, *F_BASE))
        c = lerp(c, hex_lin(P["lavender"]), smooth((field(d, *F_LAV) - 0.56) / 0.2) * 0.55)
        c = lerp(c, hex_lin(P["tealDeep"]), smooth((field(d, *F_TEAL) - 0.6) / 0.16) * 0.45)
        sl = slope(d)
        if sl > 0.28: c = lerp(c, hex_lin(P["cliff"]), smooth((sl - 0.28) / 0.22) * 0.7)
        if h > 0.26: c = lerp(c, hex_lin(P["cliffDark"]), smooth((h - 0.26) / 0.1) * 0.6)
        if h < -0.03: c = lerp(c, hex_lin(P["rockDark"]), smooth((-h - 0.03) / 0.08))
        a = math.degrees(angle(d, crown))
        if a < 24: c = lerp(c, hex_lin(P["paveDark"]), smooth((24 - a) / 12) * 0.55)
        for key, colour in (("innovation-plaza", P["pave"]), ("landing", P["paveDark"]), ("culinary-spire", P["pave"]), ("wedding-pavilion", P["paveDark"]), ("planner-atrium", P["paveDark"]), ("card-arena", P["paveDark"]), ("inventory-depot", P["paveDark"]), ("prototype-lab", P["paveDark"])):
            lon, lat_, hh, flat, blend = PLATEAUS[key]; ad = math.degrees(angle(d, direction(lon, lat_)))
            if ad < flat: c = lerp(c, hex_lin(colour), 0.85 if ad < flat - 2 else 0.4)
        return c
    face_colors = []
    for fi, f in enumerate(faces):
        centroid = (verts[f[0]] + verts[f[1]] + verts[f[2]]).normalized()
        jitter = (((fi * 2654435761) & 0xffff) / 0xffff - 0.5) * 0.03
        face_colors.append(shade(terrain_color(centroid), jitter))
    pts = [surface(d) for d in verts]
    bverts = [b.bm.verts.new(C @ p) for p in pts]
    for fi, f in enumerate(faces):
        face = b.bm.faces.new([bverts[i] for i in f]); face.smooth = False; b.tris += 1
        c = face_colors[fi]
        for loop in face.loops: loop[b.col] = (c[0], c[1], c[2], 1.0)
    bmesh.ops.recalc_face_normals(b.bm, faces=b.bm.faces)
    b.to_object("PRODUCTS_TERRAIN", cols["PRODUCTS_TERRAIN"], mat); terrain_tris = b.tris
    w = Builder(); water_r = R * math.sin(math.radians(LAKE[3] + 1.5)); wf = Frame(lake_dir); level = surface(lake_dir) + wf.up * 0.1
    m = Frame(lake_dir).world(); m[0][3], m[1][3], m[2][3] = level.x, level.y, level.z
    w.cylinder((0, 0, 0), (2 * water_r, 0.02, 2 * water_r), hex_lin(P["water"]), 14, world=m)
    w.to_object("PRODUCTS_LAKE_WATER", cols["PRODUCTS_TERRAIN"], mat)

    # --- pedestrian paths: silver ribbons along smoothed great circles (a cyan conduit strip is added in the accents)
    ab = Builder(); route_dirs = []
    def route(name, waypoints, width, color_a, color_b):
        dirs = [direction(*wp) for wp in waypoints]
        for _ in range(3):
            out = [dirs[0]]
            for a_, b_ in zip(dirs, dirs[1:]): out += [slerp(a_, b_, 0.25), slerp(a_, b_, 0.75)]
            dirs = out + [dirs[-1]]
        samples = [dirs[0]]
        for a_, b_ in zip(dirs, dirs[1:]):
            n = max(1, int(angle(a_, b_) * R / 0.11)); samples += [slerp(a_, b_, (i + 1) / n) for i in range(n)]
        rb = Builder()
        for i in range(len(samples) - 1):
            d0, d1 = samples[i], samples[i + 1]; p0, p1 = surface(d0, 0.012), surface(d1, 0.012); t = (p1 - p0).normalized()
            s0, s1 = normal_at(d0).cross(t).normalized() * width / 2, normal_at(d1).cross(t).normalized() * width / 2
            rb.quad([p0 - s0, p1 - s1, p1 + s1, p0 + s0], color_a if i % 2 else color_b)
            if i % 2 == 0: ab.quad([surface(d0, 0.016) - s0 * 0.12, surface(d1, 0.016) - s1 * 0.12, surface(d1, 0.016) + s1 * 0.12, surface(d0, 0.016) + s0 * 0.12], hex_lin(P["cyan"]))
        rb.to_object(name, cols["PRODUCTS_PATHS"], mat)
        layout["routes"].append(dict(id=name, waypoints=waypoints, width=width)); route_dirs.extend(samples[::4])
    pa, pb = hex_lin(P["path"]), hex_lin(P["pathDark"])
    route("PRODUCTS_PATH_PLAZA_PAVILION", [(0, 2), (18, 6), (34, 10), (48, 14)], 0.26, pa, pb)
    route("PRODUCTS_PATH_PLAZA_ATRIUM", [(356, 2), (340, 8), (322, 14), (312, 18)], 0.26, pa, pb)
    route("PRODUCTS_PATH_PAVILION_SPIRE", [(62, 26), (54, 38), (40, 50), (22, 58)], 0.22, pa, pb)
    route("PRODUCTS_PATH_ATRIUM_SPIRE", [(306, 30), (318, 42), (338, 52), (358, 58)], 0.22, pa, pb)
    route("PRODUCTS_PATH_PAVILION_ARENA", [(70, 18), (88, 22), (104, 28), (116, 32)], 0.22, pa, pb)
    route("PRODUCTS_PATH_ARENA_DEPOT", [(136, 34), (160, 30), (190, 24), (215, 20), (228, 18)], 0.22, pa, pb)
    route("PRODUCTS_PATH_ATRIUM_DEPOT", [(298, 18), (278, 10), (258, 12), (242, 16)], 0.22, pa, pb)
    route("PRODUCTS_PATH_PLAZA_LANDING", [(6, -8), (14, -14), (22, -20)], 0.22, pa, pb)
    route("PRODUCTS_PATH_PLAZA_LAB", [(352, -8), (346, -16), (342, -24)], 0.2, pa, pb)

    # --- buildings
    front = direction(0, -4)
    def place(name, sid, recipe, hint, env=False, scale=1.0):
        lon, lat = PLATEAUS[sid][0], PLATEAUS[sid][1]
        fr = Frame(direction(lon, lat), hint); bb = Builder(); meas = recipe(bb)
        ob = bb.to_object(name, cols["PRODUCTS_BUILDINGS"], mat, C4 @ (fr.world() @ Matrix.Diagonal((scale, scale, scale, 1))) @ C4i)
        if env: ob["role"] = f"environment:{sid}"
        else: ob["structure_id"] = sid
        ob["footprint_radius"] = meas["footprint"] * scale
        layout["structures"].append(dict(node=name, structure_id=sid, environment=env, lon=lon, lat=lat, footprint=meas["footprint"] * scale, height=meas["height"] * scale, triangles=bb.tris))
        return fr
    spire_f = place("CULINARY_SPIRE", "culinary-spire", culinary_spire, front)
    pav_f = place("WEDDING_PAVILION", "wedding-pavilion", wedding_pavilion, front, scale=1.15)
    atr_f = place("PLANNER_ATRIUM", "planner-atrium", planner_atrium, front, scale=1.15)
    lab_f = place("PROTOTYPE_LAB", "prototype-lab", prototype_lab, direction(0, -4), scale=1.15)
    arena_f = place("CARD_ARENA", "card-arena", card_arena, direction(60, 18), scale=1.15)
    depot_f = place("INVENTORY_DEPOT", "inventory-depot", inventory_depot, direction(305, 22), scale=1.15)
    plaza_f = place("INNOVATION_PLAZA", "innovation-plaza", innovation_plaza, direction(0, 40), env=True)
    S115 = Matrix.Diagonal((1.15, 1.15, 1.15, 1))
    spire_accents(ab, spire_f.world()); pavilion_accents(ab, pav_f.world() @ S115); atrium_accents(ab, atr_f.world() @ S115); lab_accents(ab, lab_f.world() @ S115)
    arena_accents(ab, arena_f.world() @ S115); depot_accents(ab, depot_f.world() @ S115); plaza_accents(ab, plaza_f.world())

    # --- the orbital ring (environment): a tilted torus with six small stations; its light band goes to the accents
    rb = Builder(); rm = ring_frame()
    rb.ring((0, 0, 0), (RING["radius"] * 2, 1, RING["radius"] * 2), hex_lin(P["ringBase"]), radial=8, tubular=56, tube=RING["tube"] / (RING["radius"] * 2), world=rm)
    for i in range(RING["stations"]):
        a = 2 * math.pi * i / RING["stations"] + 0.35
        sm = rm @ Matrix.Translation((RING["radius"] * math.cos(a), 0, RING["radius"] * math.sin(a))) @ Matrix.Rotation(-a, 4, 'Y')
        rb.box((0, 0, 0), (0.34, 0.3, 0.34), hex_lin(P["white"]), world=sm); rb.box((0, 0, 0), (0.42, 0.14, 0.42), hex_lin(P["ringDark"]), world=sm)
        rb.box((0, 0.26, 0), (0.05, 0.22, 0.05), hex_lin(P["silver"]), world=sm); rb.blob((0, 0.4, 0), (0.09, 0.09, 0.09), hex_lin(P["gold"]), 0, world=sm)
        rb.box((0, 0, 0), (0.7, 0.04, 0.12), hex_lin(P["silver"]), world=sm)
        ab.box((0, 0, 0.22), (0.26, 0.08, 0.01), hex_lin(P["cyanPale"]), world=sm)
    ring_ob = rb.to_object("ORBITAL_RING", cols["PRODUCTS_ORBIT"], mat); ring_ob["role"] = "environment:orbital-ring"; ring_ob["footprint_radius"] = float(RING["radius"] + 0.4)
    ab.ring((0, 0, 0), (RING["radius"] * 2, 1, RING["radius"] * 2), hex_lin(P["cyan"]), radial=4, tubular=56, tube=0.028 / (RING["radius"] * 2), world=rm @ Matrix.Translation((0, 0.13, 0)))
    layout["ring_object"] = "ORBITAL_RING"

    # --- decorations (one merged object)
    dec = Builder(); counts = dict(trees=0, pylons=0, platforms=0, rocks=0, benches=0, pad=1)
    occupied = [(direction(lon, lat), flat + 1.5) for lon, lat, _, flat, _ in PLATEAUS.values()] + [(lake_dir, LAKE[3] + 2)] + [(d, 1.8) for d in route_dirs]
    def free(d, margin=0.0): return all(math.degrees(angle(d, o)) > r + margin for o, r in occupied)
    def scatter(center_lon, center_lat, spread, n, fn, margin=2.0):
        c = direction(center_lon, center_lat); placed = 0; tries = 0
        while placed < n and tries < n * 14:
            tries += 1
            d = (c + (direction(rng.range(0, 360), rng.range(-70, 70)) * math.radians(spread) * rng.range(0.25, 1.0))).normalized()
            if not free(d, margin): continue
            if fn(d): placed += 1; occupied.append((d, margin))
    def put_tree(kind):
        def fn(d):
            fr = Frame(d, direction(rng.range(0, 360), 0)); crystal_tree(dec, fr.world(), rng.range(0.8, 1.25), kind); counts["trees"] += 1; return True
        return fn
    scatter(40, 32, 12, 5, put_tree("teal"), 2.6); scatter(330, 36, 12, 5, put_tree("teal"), 2.6); scatter(88, 6, 12, 4, put_tree("violet"), 2.6)
    scatter(170, 10, 18, 7, put_tree("teal"), 2.8); scatter(260, 40, 14, 4, put_tree("violet"), 2.6); scatter(300, -14, 12, 4, put_tree("teal"), 2.6); scatter(205, -30, 14, 5, put_tree("violet"), 2.6)
    def put_rock(d):
        fr = Frame(d, direction(rng.range(0, 360), 0)); rock(dec, fr.world(), rng.range(0.7, 1.4)); counts["rocks"] += 1; return True
    scatter(165, 58, 9, 4, put_rock, 2.2); scatter(40, -48, 10, 4, put_rock, 2.2); scatter(120, -24, 10, 3, put_rock, 2.2)
    for lon, lat in ((8, 12), (352, 12), (44, 24), (316, 26), (24, 56), (100, 24), (240, 10), (14, -16)):
        fr = Frame(direction(lon, lat), direction(0, -4)); light_pylon(dec, ab, fr.world()); counts["pylons"] += 1
    for key in ("obs-a", "obs-b"):
        lon, lat, *_ = PLATEAUS[key]; fr = Frame(direction(lon, lat), direction(0, 40)); observation_platform(dec, ab, fr.world()); counts["platforms"] += 1
    for lon, lat in ((4, 4), (356, -1), (6, -10)):
        fr = Frame(direction(lon, lat), direction(0, -4)); bench(dec, fr.world()); counts["benches"] += 1
    # the landing pad: a paved disc with a cyan ring and four beacons
    land = direction(PLATEAUS["landing"][0], PLATEAUS["landing"][1]); lf = Frame(land, direction(0, -4))
    dec.cylinder((0, 0.012, 0), (1.5, 0.024, 1.5), hex_lin(P["pave"]), 14, world=lf.world()); dec.ring((0, 0.03, 0), (1.3, 1, 1.3), hex_lin(P["silver"]), tube=0.02, tubular=14, world=lf.world())
    for i in range(4): dec.box((0.62 * math.cos(math.pi / 2 * i + 0.785), 0.06, 0.62 * math.sin(math.pi / 2 * i + 0.785)), (0.08, 0.12, 0.08), hex_lin(P["steel"]), world=lf.world())
    ab.ring((0, 0.035, 0), (0.64, 1, 0.64), hex_lin(P["cyan"]), tube=0.03, tubular=14, world=lf.world())
    for i in range(4): ab.box((0.62 * math.cos(math.pi / 2 * i + 0.785), 0.13, 0.62 * math.sin(math.pi / 2 * i + 0.785)), (0.06, 0.03, 0.06), hex_lin(P["cyan"]), world=lf.world())
    dec.to_object("PRODUCTS_DECORATIONS_STATIC", cols["PRODUCTS_DECORATIONS"], mat); ab.to_object("PRODUCTS_ACCENTS_GLOW", cols["PRODUCTS_ACCENTS"], accent)
    layout["decorations"] = counts

    # --- anchors (empties; names, roles and radii only)
    def empty(name, point, role, radius=None, forward=None):
        ob = bpy.data.objects.new(name, None); ob.empty_display_type = "PLAIN_AXES"; ob.empty_display_size = 0.15
        fr = Frame(point.normalized(), forward); m = fr.world(); m[0][3], m[1][3], m[2][3] = point.x, point.y, point.z
        ob.matrix_world = C4 @ m @ C4i; ob["role"] = role
        if radius is not None: ob["radius"] = float(radius)
        cols["PRODUCTS_ANCHORS"].objects.link(ob)
        layout["anchors"][name] = dict(origin=[round(v, 4) for v in point], role=role, radius=radius)
    def door(fr, dist, up=0.0): return fr.origin + fr.forward * dist + fr.up * up
    for sid, fr, dist, focus_up in (("culinary-spire", spire_f, 0.9, 2.1), ("wedding-pavilion", pav_f, 1.38, 1.0), ("planner-atrium", atr_f, 1.15, 0.8), ("prototype-lab", lab_f, 0.98, 0.75), ("card-arena", arena_f, 1.38, 0.92), ("inventory-depot", depot_f, 1.2, 0.58)):
        empty(f"PRODUCTS_ANCHOR_interaction_{sid.replace('-', '_')}", door(fr, dist), f"interaction:{sid}", forward=fr.forward)
        empty(f"PRODUCTS_ANCHOR_focus_{sid.replace('-', '_')}", door(fr, 0.0, focus_up), f"focus:{sid}", forward=fr.forward)
    empty("PRODUCTS_ANCHOR_landing", lf.origin, "landing", radius=0.3); empty("PRODUCTS_ANCHOR_spawn", lf.origin + lf.forward * 0.3, "spawn", forward=direction(0, -4))
    empty("PRODUCTS_ANCHOR_lander_arrival", lf.origin + lf.up * 0.55, "lander-arrival", radius=0.3)
    empty("PRODUCTS_ANCHOR_minigame_candidate", plaza_f.origin + plaza_f.forward * 0.6, "minigame-candidate", radius=0.35)   # the delivery hub beside the plaza fountain
    nb = Builder()
    for i in range(24):
        a0, a1 = 2 * math.pi * i / 24, 2 * math.pi * (i + 1) / 24
        p = lambda a: lf.origin + (lf.right * math.cos(a) + lf.forward * math.sin(a)) * 0.3 + lf.up * 0.01
        nb.quad([p(a0), p(a1), p(a1) + lf.up * 0.02, p(a0) + lf.up * 0.02], hex_lin("#ff5a5a"))
    nb.to_object("PRODUCTS_NAV_landing_circle", cols["PRODUCTS_NAVIGATION_REFERENCE"], mat)
    for ob in scene.objects:
        if ob.type == "MESH": ob["products_layer"] = ob.users_collection[0].name
    # --- statistics (Gateway space) and ring clearance
    pts_all, tris = [], 0
    for ob in scene.objects:
        if ob.type != "MESH" or ob.users_collection[0].name == "PRODUCTS_NAVIGATION_REFERENCE": continue
        pts_all += [C4i @ (ob.matrix_world @ v.co) for v in ob.data.vertices]; tris += sum(len(p.vertices) - 2 for p in ob.data.polygons)
    ext = max(p.length for p in pts_all)
    surf_pts = [C4i @ (scene.objects["PRODUCTS_TERRAIN"].matrix_world @ v.co) for v in scene.objects["PRODUCTS_TERRAIN"].data.vertices]
    ring_pts = [C4i @ (ring_ob.matrix_world @ v.co) for v in ring_ob.data.vertices]
    gap = min(min((rp - sp).length for sp in surf_pts[::4]) for rp in ring_pts[::6])
    build_pts = [C4i @ (o.matrix_world @ v.co) for o in scene.objects if o.type == "MESH" and o.users_collection[0].name == "PRODUCTS_BUILDINGS" for v in o.data.vertices]
    gap_buildings = min(min((rp - bp).length for bp in build_pts[::3]) for rp in ring_pts[::6])
    mn = [round(min(p[i] for p in pts_all), 4) for i in range(3)]; mx = [round(max(p[i] for p in pts_all), 4) for i in range(3)]
    layout["ring"].update(surface_clearance=round(gap, 4), building_clearance=round(gap_buildings, 4), extent=round(max(p.length for p in ring_pts), 4),
        minus_x_point=[round(v, 4) for v in ring_point(math.pi)], plus_x_point=[round(v, 4) for v in ring_point(0)], front_point=[round(v, 4) for v in ring_point(math.pi / 2)])
    layout["stats"] = dict(triangles=tris, terrain_triangles=terrain_tris, meshes=sum(1 for o in scene.objects if o.type == "MESH" and o.users_collection[0].name != "PRODUCTS_NAVIGATION_REFERENCE"),
        anchors=len(layout["anchors"]), extent=round(ext, 4), bounds=[mn, mx])
    os.makedirs(os.path.join(ROOT, "references"), exist_ok=True)
    with open(os.path.join(ROOT, "references", "layout-v1.json"), "w") as f: json.dump(layout, f, indent=1)
    print(json.dumps(layout["stats"]), json.dumps(counts), json.dumps(layout["ring"]))
    return scene

build()
