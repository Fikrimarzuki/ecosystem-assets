"""M8.9b.3a — Games planet v1, "Hybrid Game Kingdom" (Fantasy Adventure x Playful Arcade). Run inside the live Blender via Blender MCP.

Builds a dedicated scene GAMES_V1 (the user's own scenes are never touched; rerunning rebuilds it), authored in Gateway's local space:
Y up, planet centre at the origin, base radius R = 4.2 local units (14 astronaut heights), squashed to 92 % on Y, longitude measured
from +Z toward +X. Vertices are converted to Blender's Z-up at creation and the glTF (+Y up) exporter converts them back, so the GLB
loads in Gateway coordinates. Deterministic: no random module, fixed noise directions and a tiny LCG for scatter.

Collections (layers):
  GAMES_TERRAIN       the relief spheroid (vertex-coloured), the lake water and the plaza/green paving
  GAMES_PATHS         road and trail ribbons
  GAMES_BUILDINGS     KINGDOM_CASTLE, ARCADE_HALL, SCRIPTORIUM (structure_id) and PORTAL_PLAZA (environment, hub candidate)
  GAMES_DECORATIONS   merged static scenery (trees, mushrooms, rocks, cottages, cabinets, bridge, cliffs, floating rocks)
  GAMES_ACCENTS       merged emissive accents (portal core, screens, lanterns, crystals)
  GAMES_ANCHORS       empties: interactions, hub entrance, landing, spawn, lander arrival, mini-game candidate
  GAMES_NAVIGATION_REFERENCE  route centrelines and the landing circle (kept in the .blend, not exported)
Project publication, landmark identity and permissions stay in Gateway; the asset carries only structure ids and anchor roles.
"""
import bpy, bmesh, math, json, os, colorsys
from mathutils import Vector, Matrix

ROOT = r"D:\Code\porto-projects\gateway-assets\planets\games"
SCENE = "GAMES_V1"
R, SQUASH = 4.2, 0.92
TERRAIN_SUBDIV = 5
COLLECTIONS = ["GAMES_TERRAIN", "GAMES_PATHS", "GAMES_BUILDINGS", "GAMES_DECORATIONS", "GAMES_ACCENTS", "GAMES_ANCHORS", "GAMES_NAVIGATION_REFERENCE"]
C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))     # Gateway (x, y, z; Y up) -> Blender (x, -z, y; Z up)
C4 = C.to_4x4(); C4i = C4.inverted()

P = dict(lawn="#7fbf5f", meadow="#5fa352", deep="#3f8a4e", moss="#4f9a58", highland="#8d82b4", highlandLight="#a79bc9", sand="#e5d29b",
         cobble="#d7bf8c", cobbleDark="#bfa872", lake="#4aa5cc", lakeDeep="#3a86ad", cliff="#9d8d86", cliffDark="#7e6f69", bed="#c9b687",
         ivory="#e3dcc4", castleRoof="#596653", castleRoofLight="#6b7a66", flag="#b1785f", door="#594533", stone="#8f8798", stoneDark="#6f6878",
         coral="#e8735f", teal="#3fb3b0", yellow="#f2c94c", navy="#2f3d55", screen="#7ff0ff", magenta="#ff6fb5", parchment="#e9dcbd",
         indigo="#6f5fa8", ink="#3b2f4f", quill="#f7f1df", trunk="#7a5a40", leaf="#58a84f", leafLight="#7cc566", leafDeep="#3f8f4a", mana="#7d7bd6",
         manaLight="#a39ff0", mushroom="#d9534f", mushroomStem="#efe6cf", rock="#9a8f88", rockDark="#776d68", crystal="#8de8ff", lantern="#ffe3a0",
         cottageA="#f0c2a2", cottageB="#bcd5e8", cottageC="#f6e6a6", cottageRoof="#8b5e4b", wood="#9a734f", plank="#b08a5e", green="#92c86a")

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
# Plateaus under structures: (id, lon, lat, height, flat radius deg, blend deg)
PLATEAUS = {"kingdom-castle": (10, 60, 0.16, 13, 7), "arcade-hall": (62, 16, 0.08, 11, 6), "scriptorium": (308, 20, 0.12, 9, 5),
            "portal-plaza": (0, -6, 0.02, 11, 5), "landing": (330, -2, 0.02, 7, 4), "green": (36, 36, 0.10, 9, 5)}

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
        if p: h = h + (p[0] - h) * p[1] if lon != LAKE[0] else h + (p[0] - h) * p[1]
    for lon, lat, hh, flat, blend in PLATEAUS.values():
        p = plateau(d, lon, lat, hh, flat, blend)
        if p: h = h + (p[0] - h) * p[1]
    return h
def surface(d, lift=0.0):
    d = d.normalized(); p = d * (R + relief(d) + lift); return Vector((p.x, p.y * SQUASH, p.z))
def normal_at(d):
    p = surface(d); n = Vector((p.x, p.y / (SQUASH * SQUASH), p.z)); return n.normalized()

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
        for name in COLLECTIONS:
            col = bpy.data.collections.get(name)
            if col: bpy.data.collections.remove(col)
        bpy.data.scenes.remove(old)
    for me in [m for m in bpy.data.meshes if m.users == 0]: bpy.data.meshes.remove(me)
    scene = bpy.data.scenes.new(SCENE); cols = {}
    for name in COLLECTIONS:
        col = bpy.data.collections.new(name); scene.collection.children.link(col); cols[name] = col
    return scene, cols

# ----------------------------------------------------------------------------- structures (local Gateway frame: base at y = 0, +Z = front)
def castle(b):
    ivory, roof, roofL = hex_lin(P["ivory"]), hex_lin(P["castleRoof"]), hex_lin(P["castleRoofLight"])
    b.box((0, 0.42, 0), (0.95, 0.84, 0.95), ivory); b.box((0, 0.90, 0), (1.04, 0.12, 1.04), roof)
    for x in (-0.42, -0.14, 0.14, 0.42):
        for z in (-0.46, 0.46): b.box((x, 1.02, z), (0.12, 0.12, 0.1), shade(ivory, -0.06))
    for x in (-0.52, 0.52):
        for z in (-0.52, 0.52):
            b.cylinder((x, 0.62, z), (0.34, 1.24, 0.34), ivory, 8); b.cone((x, 1.42, z), (0.44, 0.38, 0.44), roof, 8)
            b.box((x, 1.70, z), (0.02, 0.22, 0.02), shade(ivory, -0.1)); b.box((x + 0.05, 1.76, z), (0.1, 0.07, 0.02), hex_lin(P["flag"]))
    b.cylinder((0, 0.78, -0.08), (0.46, 1.56, 0.46), ivory, 8); b.cylinder((0, 1.58, -0.08), (0.52, 0.08, 0.52), shade(ivory, -0.08), 8)
    b.cone((0, 1.84, -0.08), (0.6, 0.46, 0.46), roofL, 8)
    b.box((0, 2.26, -0.08), (0.025, 0.42, 0.025), shade(ivory, -0.1)); b.box((0.13, 2.38, -0.08), (0.28, 0.16, 0.025), hex_lin(P["flag"]))
    b.box((0, 0.28, 0.48), (0.3, 0.56, 0.05), hex_lin(P["door"])); b.box((0, 0.62, 0.49), (0.42, 0.1, 0.05), shade(ivory, -0.12))
    for i in range(3): b.box((0, 0.04 + i * 0.045, 0.62 + i * 0.1), (0.5, 0.045, 0.12), shade(ivory, -0.14))
    for y in (0.5, 0.72):
        for x in (-0.25, 0.25): b.box((x, y, 0.48), (0.08, 0.1, 0.02), hex_lin(P["ink"]))
    return dict(footprint=0.78, height=2.5)

def arcade_hall(b):
    coral, teal, yellow, navy = hex_lin(P["coral"]), hex_lin(P["teal"]), hex_lin(P["yellow"]), hex_lin(P["navy"])
    b.box((0, 0.34, 0), (1.2, 0.68, 0.9), coral)
    b.cylinder((0, 0.68, 0), (0.9, 1.26, 0.9), teal, 12, rot=(0, 0, math.pi / 2))    # barrel roof (axis along X)
    b.box((0, 0.74, 0.48), (1.0, 0.24, 0.06), yellow); b.box((0, 0.74, 0.46), (1.08, 0.3, 0.02), shade(yellow, -0.15))
    for i, c in enumerate((P["magenta"], P["screen"], P["yellow"])): b.box((-0.3 + i * 0.3, 0.74, 0.52), (0.16, 0.12, 0.03), hex_lin(c))
    b.box((0, 0.22, 0.47), (0.34, 0.44, 0.03), navy); b.box((0, 0.5, 0.5), (0.6, 0.04, 0.16), shade(coral, 0.12))
    for x in (-0.76, 0.76):
        b.box((x, 0.3, 0.32), (0.3, 0.6, 0.28), navy); b.box((x, 0.42, 0.47), (0.22, 0.2, 0.02), shade(navy, 0.1))
        b.box((x, 0.62, 0.3), (0.3, 0.06, 0.3), hex_lin(P["magenta"]))
    for z in (-0.3, 0.3): b.box((-0.62, 0.3, z), (0.04, 0.3, 0.2), shade(teal, 0.1))
    return dict(footprint=0.95, height=1.35)

def scriptorium(b):
    parch, indigo, ink = hex_lin(P["parchment"]), hex_lin(P["indigo"]), hex_lin(P["ink"])
    b.cylinder((0, 0.62, 0), (0.8, 1.24, 0.8), parch, 6); b.cylinder((0, 0.68, 0), (0.86, 0.06, 0.86), ink, 6)
    b.cylinder((0, 1.26, 0), (0.9, 0.08, 0.9), shade(parch, -0.1), 6); b.cone((0, 1.6, 0), (0.92, 0.6, 0.92), indigo, 6)
    b.box((0.08, 2.05, 0), (0.03, 0.55, 0.03), hex_lin(P["quill"]), rot=(0, 0, -0.35)); b.box((0.2, 2.2, 0), (0.08, 0.3, 0.02), hex_lin(P["quill"]), rot=(0, 0, -0.35))
    for y in (0.5, 0.9): b.box((0, y, 0.39), (0.1, 0.14, 0.03), ink)
    b.box((0, 0.2, 0.39), (0.22, 0.4, 0.04), hex_lin(P["door"]))
    b.cylinder((0.58, 0.13, 0.25), (0.24, 0.7, 0.24), parch, 8, rot=(0, 0, math.pi / 2)); b.cylinder((0.58, 0.13, 0.25), (0.28, 0.12, 0.28), ink, 8, rot=(0, 0, math.pi / 2))
    b.ring((0, 0.03, 0.78), (0.8, 1, 0.8), shade(parch, -0.2), tube=0.05); b.cylinder((0, 0.01, 0.78), (0.7, 0.02, 0.7), hex_lin(P["sand"]), 10)
    return dict(footprint=0.85, height=2.4)

def portal_plaza(b):
    stone, dark = hex_lin(P["stone"]), hex_lin(P["stoneDark"])
    b.cylinder((0, 0.015, 0), (1.9, 0.03, 1.9), hex_lin(P["cobble"]), 14); b.ring((0, 0.03, 0), (1.5, 1, 1.5), hex_lin(P["cobbleDark"]), tube=0.03, tubular=14)
    b.ring((0, 0.62, 0), (1.0, 1, 1.0), stone, tube=0.07, rot=(math.pi / 2, 0, 0)); b.box((0, 0.1, 0), (0.5, 0.2, 0.2), dark)
    for a in (0.6, 2.3, 3.9, 5.6):
        x, z = 0.75 * math.cos(a), 0.75 * math.sin(a); b.cylinder((x, 0.28, z), (0.12, 0.56, 0.12), stone, 6); b.box((x, 0.58, z), (0.16, 0.06, 0.16), dark)
    return dict(footprint=0.95, height=1.15)

def portal_accents(b, world):
    b.cylinder((0, 0.62, 0), (0.78, 0.02, 0.78), hex_lin("#b48cff"), 14, rot=(math.pi / 2, 0, 0), world=world)
    for a in (0.6, 2.3, 3.9, 5.6): b.box((0.75 * math.cos(a), 0.64, 0.75 * math.sin(a)), (0.1, 0.08, 0.1), hex_lin(P["lantern"]), world=world)
def arcade_accents(b, world):
    for x in (-0.76, 0.76): b.box((x, 0.42, 0.485), (0.2, 0.18, 0.01), hex_lin(P["screen"]), world=world)
    b.box((0, 0.74, 0.54), (0.9, 0.06, 0.005), hex_lin(P["magenta"]), world=world)
def scriptorium_accents(b, world):
    for y in (0.5, 0.9): b.box((0, y, 0.41), (0.08, 0.1, 0.01), hex_lin("#ffd98a"), world=world)

# ----------------------------------------------------------------------------- decoration pieces (world Gateway frame via `world`)
def tree(b, world, kind, s=1.0):
    trunk, leaf, light = hex_lin(P["trunk"]), hex_lin(P["leaf"] if kind != "mana" else P["mana"]), hex_lin(P["leafLight"] if kind != "mana" else P["manaLight"])
    if kind == "deep": leaf, light = hex_lin(P["leafDeep"]), hex_lin(P["leaf"])
    b.cylinder((0, 0.14 * s, 0), (0.09 * s, 0.28 * s, 0.09 * s), trunk, 6, world=world)
    b.blob((0, 0.42 * s, 0), (0.46 * s, 0.4 * s, 0.46 * s), leaf, 1, world=world); b.blob((0, 0.62 * s, 0.02), (0.3 * s, 0.26 * s, 0.3 * s), light, 0, world=world)
def mushroom(b, world, s=1.0):
    b.cylinder((0, 0.08 * s, 0), (0.07 * s, 0.16 * s, 0.07 * s), hex_lin(P["mushroomStem"]), 6, world=world)
    b.blob((0, 0.18 * s, 0), (0.24 * s, 0.14 * s, 0.24 * s), hex_lin(P["mushroom"]), 0, world=world)
def rock(b, world, s=1.0, dark=False):
    b.rock((0, 0.1 * s, 0), (0.42 * s, 0.3 * s, 0.34 * s), hex_lin(P["rockDark"] if dark else P["rock"]), rot=(0.2, 0.5, 0.1), world=world)
def crystal(b, world, s=1.0):
    b.rock((0, 0.22 * s, 0), (0.12 * s, 0.5 * s, 0.12 * s), hex_lin(P["crystal"]), rot=(0.1, 0.3, 0.08), world=world)
def cottage(b, world, color):
    wall, roof = hex_lin(color), hex_lin(P["cottageRoof"])
    b.box((0, 0.2, 0), (0.42, 0.4, 0.38), wall); b.cone((0, 0.52, 0), (0.6, 0.3, 0.56), roof, 4, rot=(0, math.pi / 4, 0))
    b.box((0, 0.13, 0.2), (0.12, 0.26, 0.02), hex_lin(P["door"])); b.box((0.14, 0.26, 0.2), (0.08, 0.08, 0.015), hex_lin(P["ink"]))
def cabinet(b, world):
    b.box((0, 0.3, 0), (0.28, 0.6, 0.26), hex_lin(P["navy"]), world=world); b.box((0, 0.6, 0), (0.28, 0.06, 0.28), hex_lin(P["coral"]), world=world)
def lantern(b, world):
    b.box((0, 0.3, 0), (0.03, 0.6, 0.03), hex_lin(P["ink"]), world=world); b.box((0, 0.64, 0), (0.1, 0.1, 0.1), hex_lin(P["stoneDark"]), world=world)

# ----------------------------------------------------------------------------- build
def build():
    scene, cols = reset_scene()
    mat, accent = diorama_material("GamesDiorama"), diorama_material("GamesAccent", emissive=True)
    layout = dict(planet=dict(radius=R, squash=SQUASH, up="+Y", longitude="from +Z toward +X"), structures=[], anchors={}, routes=[], decorations={})

    # --- terrain: icosphere, displaced by relief, squashed, vertex-coloured by region
    b = Builder(); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=TERRAIN_SUBDIV, radius=1.0)
    verts = [Vector((v.co.x, v.co.z, -v.co.y)).normalized() for v in bm.verts]     # Blender icosphere -> Gateway directions
    faces = [tuple(l.vert.index for l in f.loops) for f in bm.faces]; bm.free()
    lake_dir = direction(LAKE[0], LAKE[1]); crown = direction(PLATEAUS["kingdom-castle"][0], PLATEAUS["kingdom-castle"][1])
    def terrain_color(d):
        h = relief(d); lat = math.degrees(math.asin(max(-1, min(1, d.y))))
        n = 0.5 + 0.5 * math.sin(d.dot(direction(63, 14)) * 9.3) * math.sin(d.dot(direction(201, -40)) * 7.1)
        c = lerp(hex_lin(P["meadow"]), hex_lin(P["lawn"]), n)
        if h > 0.30: c = lerp(c, hex_lin(P["cliff"]), smooth((h - 0.30) / 0.08))
        if h > 0.44: c = lerp(c, hex_lin(P["cliffDark"]), smooth((h - 0.44) / 0.1) * 0.6)
        if h < -0.04: c = lerp(c, hex_lin(P["bed"]), smooth((-h - 0.04) / 0.08))
        a = math.degrees(angle(d, crown))
        if a < 27: c = lerp(c, hex_lin(P["highland"]), smooth((27 - a) / 12))
        if a < 14: c = lerp(c, hex_lin(P["highlandLight"]), smooth((14 - a) / 8) * 0.5)
        if math.degrees(angle(d, direction(176, 18))) < 26: c = lerp(c, hex_lin(P["deep"]), 0.5)
        for lon, lat_, hh, flat, blend in (PLATEAUS["portal-plaza"], PLATEAUS["landing"], PLATEAUS["green"]):
            ad = math.degrees(angle(d, direction(lon, lat_)))
            if ad < flat: c = lerp(c, hex_lin(P["sand"] if lon != PLATEAUS["green"][0] else P["green"]), 0.8 if ad < flat - 2 else 0.4)
        return c
    pts = [surface(d) for d in verts]; colors = [terrain_color(d) for d in verts]
    bverts = [b.bm.verts.new(C @ p) for p in pts]
    for f in faces:
        face = b.bm.faces.new([bverts[i] for i in f]); face.smooth = False; b.tris += 1
        for loop in face.loops:
            c = colors[loop.vert.index]; loop[b.col] = (c[0], c[1], c[2], 1.0)
    bmesh.ops.recalc_face_normals(b.bm, faces=b.bm.faces)
    terrain = b.to_object("GAMES_TERRAIN", cols["GAMES_TERRAIN"], mat); terrain_tris = b.tris
    # lake water: a flat disc at the basin's rim level
    w = Builder(); lf = Frame(lake_dir, Vector((0, 1, 0)))
    water_r = R * math.sin(math.radians(LAKE[3] + 1.5))
    wf = Frame(lake_dir); level = surface(lake_dir) + wf.up * 0.11
    wm = Matrix.Translation(level) @ Matrix.Identity(4)
    m = Frame(lake_dir).world(); m[0][3], m[1][3], m[2][3] = level.x, level.y, level.z
    w.cylinder((0, 0, 0), (2 * water_r, 0.02, 2 * water_r), hex_lin(P["lake"]), 16, world=m)
    w.to_object("GAMES_LAKE_WATER", cols["GAMES_TERRAIN"], mat)

    # --- roads and trails: ribbon strips along smoothed great-circle polylines
    def route(name, waypoints, width, color_a, color_b):
        dirs = [direction(*wp) for wp in waypoints]
        for _ in range(3):   # Chaikin smoothing on the sphere
            out = [dirs[0]]
            for a_, b_ in zip(dirs, dirs[1:]): out += [slerp(a_, b_, 0.25), slerp(a_, b_, 0.75)]
            dirs = out + [dirs[-1]]
        samples = [dirs[0]]
        for a_, b_ in zip(dirs, dirs[1:]):
            n = max(1, int(angle(a_, b_) * R / 0.11))
            samples += [slerp(a_, b_, (i + 1) / n) for i in range(n)]
        rb = Builder()
        for i in range(len(samples) - 1):
            d0, d1 = samples[i], samples[i + 1]
            p0, p1 = surface(d0, 0.012), surface(d1, 0.012); t = (p1 - p0).normalized()
            s0, s1 = normal_at(d0).cross(t).normalized() * width / 2, normal_at(d1).cross(t).normalized() * width / 2
            rb.quad([p0 - s0, p1 - s1, p1 + s1, p0 + s0], color_a if i % 2 else color_b)
        rb.to_object(name, cols["GAMES_PATHS"], mat)
        layout["routes"].append(dict(id=name, waypoints=waypoints, width=width))
        return samples
    cob, cobD = hex_lin(P["cobble"]), hex_lin(P["cobbleDark"])
    route("GAMES_ROAD_PLAZA_VILLAGE", [(0, -2), (16, 0), (30, 4), (40, 8), (52, 12), (60, 14)], 0.3, cob, cobD)
    route("GAMES_ROAD_VILLAGE_CASTLE", [(66, 20), (72, 30), (60, 40), (44, 46), (30, 52), (14, 55)], 0.28, cob, cobD)
    route("GAMES_ROAD_PLAZA_SCRIPTORIUM", [(356, -4), (342, 2), (330, 10), (316, 16)], 0.24, cob, cobD)
    route("GAMES_TRAIL_CASTLE_GREEN", [(18, 54), (28, 46), (36, 40)], 0.2, hex_lin(P["sand"]), shade(hex_lin(P["sand"]), -0.05))
    route("GAMES_TRAIL_LANDING", [(340, -1), (334, -1)], 0.2, hex_lin(P["sand"]), shade(hex_lin(P["sand"]), -0.05))

    # --- buildings (separate objects; origin at the base centre on the plateau; forward toward the plaza / front)
    front = direction(0, -6)
    def place(name, sid, recipe, hint, env=False, lift=0.0, scale=1.0):
        lon, lat = PLATEAUS[sid][0], PLATEAUS[sid][1]
        fr = Frame(direction(lon, lat), hint, lift); bb = Builder(); meas = recipe(bb)
        meas = dict(footprint=meas["footprint"] * scale, height=meas["height"] * scale)
        ob = bb.to_object(name, cols["GAMES_BUILDINGS"], mat, C4 @ (fr.world() @ Matrix.Diagonal((scale, scale, scale, 1))) @ C4i)
        if env: ob["role"] = f"environment:{sid}"
        else: ob["structure_id"] = sid
        ob["footprint_radius"] = meas["footprint"]
        layout["structures"].append(dict(node=name, structure_id=sid, environment=env, lon=lon, lat=lat, footprint=meas["footprint"], height=meas["height"], triangles=bb.tris))
        return fr
    castle_f = place("KINGDOM_CASTLE", "kingdom-castle", castle, front, scale=1.15)
    arcade_f = place("ARCADE_HALL", "arcade-hall", arcade_hall, front)
    script_f = place("SCRIPTORIUM", "scriptorium", scriptorium, direction(20, 10))
    portal_f = place("PORTAL_PLAZA", "portal-plaza", portal_plaza, direction(0, 40), env=True)

    # --- accents (one merged emissive object) and decorations (one merged object)
    ab = Builder(); portal_accents(ab, portal_f.world()); arcade_accents(ab, arcade_f.world()); scriptorium_accents(ab, script_f.world())
    dec = Builder(); rng = LCG(20261023); counts = dict(trees=0, mushrooms=0, rocks=0, crystals=0, cottages=0, cabinets=0, lanterns=0, floating=0)
    occupied = [(direction(lon, lat), flat + 1.5) for lon, lat, _, flat, _ in PLATEAUS.values()] + [(lake_dir, LAKE[3] + 2)]
    def free(d, margin=0.0): return all(math.degrees(angle(d, o)) > r + margin for o, r in occupied)
    def scatter(center_lon, center_lat, spread, n, fn, margin=2.0):
        c = direction(center_lon, center_lat); placed = 0; tries = 0
        while placed < n and tries < n * 12:
            tries += 1
            d = (c + (direction(rng.range(0, 360), rng.range(-70, 70)) * math.radians(spread) * rng.range(0.25, 1.0))).normalized()
            if not free(d, margin): continue
            if fn(d): placed += 1; occupied.append((d, margin))
    def put_tree(kind, s_lo=0.85, s_hi=1.25):
        def fn(d):
            fr = Frame(d, direction(rng.range(0, 360), 0)); tree(dec, fr.world(), kind, rng.range(s_lo, s_hi)); counts["trees"] += 1; return True
        return fn
    scatter(176, 18, 22, 11, put_tree("deep"), 3.2)        # far-side forest
    scatter(126, 28, 14, 6, put_tree("leaf"), 3.0)          # east woods
    scatter(286, 2, 14, 6, put_tree("leaf"), 3.0)           # west woods
    scatter(222, -28, 12, 5, put_tree("mana"), 3.0)         # mana grove (violet)
    scatter(44, 28, 10, 4, put_tree("leaf", 0.7, 1.0), 2.6)  # near the green
    scatter(340, 30, 10, 3, put_tree("leaf", 0.7, 1.0), 2.6)
    def put_mushroom(d):
        fr = Frame(d, direction(0, 0)); mushroom(dec, fr.world(), rng.range(0.8, 1.3)); counts["mushrooms"] += 1; return True
    scatter(200, -4, 14, 6, put_mushroom, 2.2); scatter(300, 40, 10, 4, put_mushroom, 2.2)
    def put_rock(dark):
        def fn(d):
            fr = Frame(d, direction(rng.range(0, 360), 0)); rock(dec, fr.world(), rng.range(0.7, 1.6), dark); counts["rocks"] += 1; return True
        return fn
    scatter(150, 54, 10, 5, put_rock(True), 2.4); scatter(236, 30, 8, 4, put_rock(True), 2.4); scatter(30, -46, 12, 5, put_rock(False), 2.4)
    def put_crystal(d):
        fr = Frame(d, direction(0, 0)); crystal(ab, fr.world(), rng.range(0.8, 1.4)); counts["crystals"] += 1; return True
    scatter(350, 8, 7, 3, put_crystal, 2.0); scatter(316, 28, 6, 3, put_crystal, 2.0)
    for i, (lon, lat, col) in enumerate(((78, 8, P["cottageA"]), (56, 2, P["cottageB"]), (84, 22, P["cottageC"]))):
        d = direction(lon, lat); fr = Frame(d, direction(62, 16)); cb = Builder(); cottage(cb, fr.world(), col)
        # cottages are small separate structures; merged into the decoration batch via the same builder for a single draw call
        cottage(dec, fr.world(), col); counts["cottages"] += 1; occupied.append((d, 3.0)); cb.bm.free()
    for lon, lat in ((70, 6), (52, 22)):
        fr = Frame(direction(lon, lat), direction(62, 16)); cabinet(dec, fr.world()); counts["cabinets"] += 1; occupied.append((direction(lon, lat), 2.0))
    for lon, lat in ((8, 4), (352, 4), (48, 16), (14, 46), (322, 12), (28, 40)):
        fr = Frame(direction(lon, lat)); lantern(dec, fr.world()); counts["lanterns"] += 1
        ab.box((0, 0.64, 0), (0.08, 0.08, 0.08), hex_lin(P["lantern"]), world=fr.world())
    # bridge over the gully (the plaza-village road crosses it at ~lon 34, lat 6)
    gd = direction(GULLY[0], GULLY[1]); bf = Frame(gd, direction(60, 14)); level = R + 0.03 + relief(direction(24, 3))
    bm_ = bf.world(); bm_[0][3], bm_[1][3], bm_[2][3] = (gd * level).x, (gd * level).y * SQUASH, (gd * level).z
    dec.box((0, 0, 0), (0.42, 0.05, 0.95), hex_lin(P["plank"]), world=bm_)
    for x in (-0.19, 0.19):
        dec.box((x, 0.1, 0), (0.03, 0.2, 0.95), hex_lin(P["wood"]), world=bm_)
        for z in (-0.4, 0, 0.4): dec.box((x, 0.1, z), (0.04, 0.22, 0.04), hex_lin(P["wood"]), world=bm_)
    # floating rocks (+x / +z sides only, away from the rocket's parking side)
    for lon, lat, h, s in ((118, 42, 0.95, 1.0), (44, -52, 0.8, 0.8), (168, 66, 1.05, 1.2)):
        d = direction(lon, lat); fr = Frame(d); o = surface(d) + fr.up * h
        mm = fr.world(); mm[0][3], mm[1][3], mm[2][3] = o.x, o.y, o.z
        dec.rock((0, 0, 0), (0.6 * s, 0.42 * s, 0.5 * s), hex_lin(P["rockDark"]), rot=(0.3, 0.2, 0.1), world=mm)
        dec.blob((0, 0.2 * s, 0), (0.5 * s, 0.14 * s, 0.42 * s), hex_lin(P["lawn"]), 0, world=mm); counts["floating"] += 1
    dec.to_object("GAMES_DECORATIONS_STATIC", cols["GAMES_DECORATIONS"], mat); ab.to_object("GAMES_ACCENTS_GLOW", cols["GAMES_ACCENTS"], accent)
    layout["decorations"] = counts

    # --- anchors (empties; names, roles and radii only)
    def empty(name, point, role, radius=None, forward=None):
        ob = bpy.data.objects.new(name, None); ob.empty_display_type = "PLAIN_AXES"; ob.empty_display_size = 0.15
        fr = Frame(point.normalized(), forward); m = fr.world(); m[0][3], m[1][3], m[2][3] = point.x, point.y, point.z
        ob.matrix_world = C4 @ m @ C4i; ob["role"] = role
        if radius is not None: ob["radius"] = float(radius)
        cols["GAMES_ANCHORS"].objects.link(ob)
        layout["anchors"][name] = dict(origin=[round(v, 4) for v in point], role=role, radius=radius)
    def door(fr, dist): return fr.origin + fr.forward * dist
    empty("ANCHOR_interaction_kingdom_castle", door(castle_f, 1.02), "interaction:kingdom-castle")
    empty("ANCHOR_interaction_arcade_hall", door(arcade_f, 0.72), "interaction:arcade-hall")
    empty("ANCHOR_interaction_scriptorium", door(script_f, 1.1), "interaction:scriptorium")
    empty("ANCHOR_hub_portal_plaza", door(portal_f, 0.2), "hub-entrance:portal-plaza")
    land = direction(PLATEAUS["landing"][0], PLATEAUS["landing"][1]); lf = Frame(land, direction(0, -6))
    empty("ANCHOR_landing", lf.origin, "landing", radius=0.3); empty("ANCHOR_spawn", lf.origin + lf.forward * 0.28, "spawn", forward=direction(0, -6))
    empty("ANCHOR_lander_arrival", lf.origin + lf.up * 0.55, "lander-arrival", radius=0.3)
    g = direction(PLATEAUS["green"][0], PLATEAUS["green"][1]); empty("ANCHOR_minigame_candidate", surface(g), "minigame-candidate", radius=0.35)
    # --- navigation reference (not exported): landing circle and route centrelines
    nb = Builder()
    for i in range(24):
        a0, a1 = 2 * math.pi * i / 24, 2 * math.pi * (i + 1) / 24
        p = lambda a: lf.origin + (lf.right * math.cos(a) + lf.forward * math.sin(a)) * 0.3 + lf.up * 0.01
        nb.quad([p(a0), p(a1), p(a1) + lf.up * 0.02, p(a0) + lf.up * 0.02], hex_lin("#ff5a5a"))
    nb.to_object("NAV_landing_circle", cols["GAMES_NAVIGATION_REFERENCE"], mat)
    for ob in scene.objects:
        if ob.type == "MESH": ob["games_layer"] = ob.users_collection[0].name
    # --- statistics (Gateway space)
    pts_all, tris = [], 0
    for ob in scene.objects:
        if ob.type != "MESH" or ob.users_collection[0].name == "GAMES_NAVIGATION_REFERENCE": continue
        pts_all += [C4i @ (ob.matrix_world @ v.co) for v in ob.data.vertices]; tris += sum(len(p.vertices) - 2 for p in ob.data.polygons)
    ext = max(p.length for p in pts_all)
    layout["stats"] = dict(triangles=tris, terrain_triangles=terrain_tris, meshes=sum(1 for o in scene.objects if o.type == "MESH" and o.users_collection[0].name != "GAMES_NAVIGATION_REFERENCE"),
        anchors=len(layout["anchors"]), extent=round(ext, 4), bounds=[[round(min(p[i] for p in pts_all), 4) for i in range(3)], [round(max(p[i] for p in pts_all), 4) for i in range(3)]])
    os.makedirs(os.path.join(ROOT, "references"), exist_ok=True)
    with open(os.path.join(ROOT, "references", "layout-v1.json"), "w") as f: json.dump(layout, f, indent=1)
    print(json.dumps(layout["stats"]), json.dumps(counts))
    return scene

build()
