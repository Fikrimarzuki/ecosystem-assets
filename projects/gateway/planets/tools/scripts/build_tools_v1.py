"""M8.9b.4a — Tools world v1, "The Mechanical Workshop" (Floating Industrial Fantasy). Run inside the live Blender via Blender MCP.

Not a planet: an asymmetric cluster of interconnected floating mechanical platforms (decks on riveted hulls with exposed gears, pipes and
rotors underneath), joined by truss bridges and catwalks. Built in a dedicated scene TOOLS_V1 (the user's own scenes are never touched;
rerunning rebuilds it), authored in Gateway's local space: Y up, the cluster roughly centred on the origin, +Z = the front (toward the
default inspection camera), the −X side kept low and open for the parked rocket. Vertices are converted to Blender's Z-up at creation and the
glTF (+Y up) exporter converts them back. Deterministic: no random module, fixed layout tables and a tiny LCG for rivets and crates.

Collections (layers):
  TOOLS_TERRAIN        the platforms: decks, hulls, rivets, railings (one mesh; "TERRAIN" so the staging contract finds the ground)
  TOOLS_PATHS          bridges and catwalks (TOOLS_BRIDGE_*, TOOLS_CATWALK_*)
  TOOLS_BUILDINGS      WORKSHOP_HALL, FORGE_STATION, REPLICATOR_BAY (structure_id) and CONTROL_TOWER (environment, hub-entrance candidate)
  TOOLS_DECORATIONS    merged static machinery: gears, tanks, cranes, pipes, crates, the power core housing
  TOOLS_ACCENTS        merged emissive accents: cyan energy (core, conduits, coils), warm windows and lamps
  TOOLS_ANCHORS        empties TOOLS_ANCHOR_* (prefixed: object names are global in a Blender session that also holds the Games/Learning scenes):
                       interactions, focus points, hub entrance, landing, spawn, lander arrival, mini-game candidate
  TOOLS_NAVIGATION_REFERENCE  the landing circle (kept in the .blend, not exported)
Project publication, landmark identity and permissions stay in Gateway; the asset carries only structure ids and anchor roles.
"""
import bpy, bmesh, math, json, os, colorsys
from mathutils import Vector, Matrix

ROOT = r"D:\Code\porto-projects\gateway-assets\planets\tools"
SCENE = "TOOLS_V1"
COLLECTIONS = ["TOOLS_TERRAIN", "TOOLS_PATHS", "TOOLS_BUILDINGS", "TOOLS_DECORATIONS", "TOOLS_ACCENTS", "TOOLS_ANCHORS", "TOOLS_NAVIGATION_REFERENCE"]
C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))     # Gateway (x, y, z; Y up) -> Blender (x, -z, y; Z up)
C4 = C.to_4x4(); C4i = C4.inverted()

P = dict(steel="#7f8a99", steelLight="#9aa5b3", steelDark="#4b5564", deck="#66707f", deckLine="#55606f", hull="#5a6474", hullDark="#3f4856",
         copper="#b87333", copperDark="#8a4f22", brass="#c9a24b", brassDark="#8c6d2a", rust="#8a5a3c", iron="#2f3640", plank="#9a734f", wood="#7a5a40",
         glass="#9fd8e8", cyan="#5fe3ff", cyanDeep="#2bb8d9", cyanPale="#bff3ff", warm="#ffd98a", ember="#ff8c42", red="#c2374a", concrete="#a7a9ab",
         canvas="#d9c9a3", green="#5f9a6a", lens="#dff6ff", slate="#596673", cable="#262b33", crateA="#b08a5e", crateB="#8fa3b5", crateC="#c9a24b")

def srgb_to_linear(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def hex_lin(h): h = h.lstrip("#"); return [srgb_to_linear(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)]
def shade(c, dl):
    h, l, s = colorsys.rgb_to_hls(*[max(0.0, min(1.0, x)) for x in c]); return list(colorsys.hls_to_rgb(h, max(0.0, min(1.0, l + dl)), s))

class LCG:
    def __init__(self, seed): self.s = seed & 0xffffffff
    def next(self): self.s = (1664525 * self.s + 1013904223) & 0xffffffff; return self.s / 0xffffffff
    def range(self, a, b): return a + (b - a) * self.next()

# ----------------------------------------------------------------------------- mesh builder (vertices in Gateway coordinates)
def part_matrix(pos, size, rot=(0, 0, 0)):
    return Matrix.Translation(Vector(pos)) @ Matrix.Rotation(rot[1], 4, 'Y') @ Matrix.Rotation(rot[0], 4, 'X') @ Matrix.Rotation(rot[2], 4, 'Z') @ Matrix.Diagonal((*size, 1))
def yaw(pos, angle, scale=1.0):
    """A placement frame on a flat deck: translation + rotation about +Y (forward = +Z rotated by `angle`)."""
    return Matrix.Translation(Vector(pos)) @ Matrix.Rotation(angle, 4, 'Y') @ Matrix.Diagonal((scale, scale, scale, 1))
def along(a, b):
    """A frame whose local +Y runs from a to b (length 1 = |ab|), centred at the midpoint; local x/z are unit."""
    a, b = Vector(a), Vector(b); d = b - a; n = d.length
    q = Vector((0, 1, 0)).rotation_difference(d.normalized()) if n > 1e-9 else Matrix.Identity(3).to_quaternion()
    return Matrix.Translation((a + b) / 2) @ q.to_matrix().to_4x4() @ Matrix.Diagonal((1, n, 1, 1))
def span(a, b):
    """A frame whose local +Z runs from a to b (length 1 = |ab|), local +Y stays as upright as possible, origin at a."""
    a, b = Vector(a), Vector(b); d = b - a; n = d.length; f = d.normalized()
    r = Vector((0, 1, 0)).cross(f)
    if r.length < 1e-6: r = Vector((1, 0, 0))
    r.normalize(); u = f.cross(r).normalized()
    m = Matrix.Identity(4)
    for i, col in enumerate((r, u, f)): m[0][i], m[1][i], m[2][i] = col.x, col.y, col.z
    m[0][3], m[1][3], m[2][3] = a.x, a.y, a.z
    return m, n

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
    def cylinder(self, pos, size, color, segments=10, rot=(0, 0, 0), world=Matrix.Identity(4), top=1.0, bottom=1.0):
        v, f = [], []
        for i in range(segments):
            a = 2 * math.pi * i / segments
            v.append((.5 * bottom * math.cos(a), -.5, .5 * bottom * math.sin(a))); v.append((.5 * top * math.cos(a), .5, .5 * top * math.sin(a)))
        for i in range(segments):
            j = (i + 1) % segments; f.append((2 * i, 2 * i + 1, 2 * j + 1, 2 * j))
        f.append(tuple(2 * i for i in range(segments))[::-1]); f.append(tuple(2 * i + 1 for i in range(segments)))
        self._add(v, f, world @ part_matrix(pos, size, rot), color)
    def cone(self, pos, size, color, segments=8, rot=(0, 0, 0), world=Matrix.Identity(4)):
        v = [(.5 * math.cos(2 * math.pi * i / segments), -.5, .5 * math.sin(2 * math.pi * i / segments)) for i in range(segments)] + [(0, .5, 0)]
        f = [(i, segments, (i + 1) % segments) for i in range(segments)] + [tuple(range(segments))[::-1]]
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
    def prism(self, points, y_top, thickness, color, world=Matrix.Identity(4)):
        """A flat polygon (x, z) extruded from y_top − thickness to y_top; the polygon is given counter-clockwise seen from above."""
        n = len(points); v = [(x, y_top, z) for x, z in points] + [(x, y_top - thickness, z) for x, z in points]
        f = [tuple(range(n)), tuple(range(n, 2 * n))[::-1]] + [(i, n + i, n + (i + 1) % n, (i + 1) % n) for i in range(n)]
        self._add(v, f, world, color)
    def quad(self, pts, color):
        bv = [self.bm.verts.new(C @ Vector(p)) for p in pts]
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
    bsdf.inputs["Roughness"].default_value = 0.72; bsdf.inputs["Metallic"].default_value = 0.18
    if emissive:
        links.new(attr.outputs["Color"], bsdf.inputs["Emission Color"]); bsdf.inputs["Emission Strength"].default_value = strength
    return mat

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

# ----------------------------------------------------------------------------- the platforms (Gateway space; y = deck top surface)
# id: (centre x, y, z, shape, (width, depth) or radius, deck thickness, hull depth, yaw)
PLATFORMS = {
    "main":    dict(c=(0.0, 0.0, 0.0), shape="octa", size=(4.3, 3.5), thick=0.32, hull=1.5, yaw=0.0),            # the workshop deck
    "forge":   dict(c=(3.35, 0.55, 1.05), shape="round", size=(2.55, 2.55), thick=0.28, hull=1.2, yaw=0.0),     # DevTools' forge, raised
    "bay":     dict(c=(-2.85, -0.5, 1.75), shape="rect", size=(2.5, 2.0), thick=0.28, hull=1.05, yaw=0.18),     # the replicator bay, low
    "dock":    dict(c=(0.9, -0.25, 3.35), shape="round", size=(2.3, 2.3), thick=0.26, hull=0.9, yaw=0.0),       # arrival: landing pad + control tower
    "power":   dict(c=(2.1, 1.75, -2.2), shape="hex", size=(1.6, 1.6), thick=0.22, hull=0.7, yaw=0.3),          # the suspended power station
    "spare":   dict(c=(-1.9, 0.95, -2.35), shape="hex", size=(1.3, 1.3), thick=0.2, hull=0.6, yaw=-0.2),        # a small tank perch
}
def outline(p):
    cx, cy, cz = p["c"]; w, d = p["size"]; a = p["yaw"]
    if p["shape"] == "octa":
        k = 0.28; pts = [(-w / 2 + k * w, -d / 2), (w / 2 - k * w, -d / 2), (w / 2, -d / 2 + k * d), (w / 2, d / 2 - k * d), (w / 2 - k * w, d / 2), (-w / 2 + k * w, d / 2), (-w / 2, d / 2 - k * d), (-w / 2, -d / 2 + k * d)]
    elif p["shape"] == "rect":
        k = 0.12; pts = [(-w / 2 + k * w, -d / 2), (w / 2 - k * w, -d / 2), (w / 2, -d / 2 + k * d), (w / 2, d / 2 - k * d), (w / 2 - k * w, d / 2), (-w / 2 + k * w, d / 2), (-w / 2, d / 2 - k * d), (-w / 2, -d / 2 + k * d)]
    elif p["shape"] == "hex":
        pts = [(w / 2 * math.cos(math.pi / 3 * i), w / 2 * math.sin(math.pi / 3 * i)) for i in range(6)]
    else:
        pts = [(w / 2 * math.cos(2 * math.pi * i / 14), w / 2 * math.sin(2 * math.pi * i / 14)) for i in range(14)]
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + x * ca + z * sa, cz - x * sa + z * ca) for x, z in pts]
def deck_point(pid, lx, lz):
    """A point on a platform's deck surface from local (x, z) offsets (rotated by the platform yaw)."""
    p = PLATFORMS[pid]; cx, cy, cz = p["c"]; a = p["yaw"]; ca, sa = math.cos(a), math.sin(a)
    return Vector((cx + lx * ca + lz * sa, cy, cz - lx * sa + lz * ca))
def edge_point(pid, direction):
    """The deck-edge point in a horizontal direction (x, z) from the platform centre."""
    p = PLATFORMS[pid]; pts = outline(p); cx, cy, cz = p["c"]; d = Vector((direction[0], direction[1])).normalized()
    best, hit = -1, None
    for i in range(len(pts)):
        ax, az = pts[i]; bx, bz = pts[(i + 1) % len(pts)]
        # intersect ray (cx,cz)+t*d with segment a-b
        ex, ez = bx - ax, bz - az; den = d.x * ez - d.y * ex
        if abs(den) < 1e-9: continue
        t = ((ax - cx) * ez - (az - cz) * ex) / den; u = ((ax - cx) * d.y - (az - cz) * d.x) / den
        if t > 0 and 0 <= u <= 1 and t > best: best, hit = t, (cx + d.x * t, cz + d.y * t)
    return Vector((hit[0], cy, hit[1]))

def platform(b, pid, rng):
    p = PLATFORMS[pid]; cx, cy, cz = p["c"]; pts = outline(p); n = len(pts)
    deck, line, hull, hullD, steel, iron = hex_lin(P["deck"]), hex_lin(P["deckLine"]), hex_lin(P["hull"]), hex_lin(P["hullDark"]), hex_lin(P["steel"]), hex_lin(P["iron"])
    b.prism(pts, cy, p["thick"], deck)
    # deck plating lines: thin darker strips across the deck
    w, d = p["size"]
    for i in range(1, int(d / 0.45)):
        z = -d / 2 + i * 0.45
        if abs(z) < d / 2 - 0.2: b.box((0, 0.004, z), (w * 0.78, 0.008, 0.03), line, world=yaw((cx, cy, cz), p["yaw"]))
    # rim: a brass/steel edge band and rivets
    inner = [(cx + (x - cx) * 0.94, cz + (z - cz) * 0.94) for x, z in pts]
    for i in range(n):
        ax, az = pts[i]; bx, bz = pts[(i + 1) % n]; mx, mz = (ax + bx) / 2, (az + bz) / 2
        b.box((mx, cy - p["thick"] * 0.5, mz), (0.06, p["thick"] * 1.02, math.hypot(bx - ax, bz - az) * 1.02), hex_lin(P["steelDark"]), rot=(0, math.atan2(bx - ax, bz - az), 0))
        for k in (0.25, 0.5, 0.75):
            rx, rz = ax + (bx - ax) * k, az + (bz - az) * k
            b.box((rx, cy - p["thick"] * 0.3, rz), (0.05, 0.05, 0.05), hex_lin(P["brassDark"]), rot=(0, math.atan2(bx - ax, bz - az), 0))
    # hull: a tapered riveted underbody with a keel ring, a rotor (lift fan) and hanging pipes
    hb = p["hull"]; hw = min(w, d)
    b.cylinder((cx, cy - p["thick"] - hb * 0.42, cz), (hw * 0.86, hb * 0.84, hw * 0.86 * (d / w if p["shape"] in ("rect", "octa") else 1)), hull, 10, bottom=0.45)
    b.cylinder((cx, cy - p["thick"] - hb * 0.1, cz), (hw * 0.92, 0.12, hw * 0.92 * (d / w if p["shape"] in ("rect", "octa") else 1)), hullD, 10)
    b.ring((cx, cy - p["thick"] - hb * 0.55, cz), (hw * 0.62, 1, hw * 0.62), hex_lin(P["copper"]), tube=0.06, tubular=14)
    b.cylinder((cx, cy - p["thick"] - hb * 0.92, cz), (hw * 0.34, 0.14, hw * 0.34), iron, 10)
    for i in range(6):   # rotor blades under the keel
        a = math.pi / 3 * i
        b.box((cx + math.cos(a) * hw * 0.11, cy - p["thick"] - hb * 0.92, cz + math.sin(a) * hw * 0.11), (hw * 0.2, 0.03, 0.08), steel, rot=(0.35, -a, 0))
    for i in range(3):   # hanging pipes with valve wheels
        a = 0.7 + 2.1 * i + rng.range(-0.3, 0.3); r = hw * 0.36
        px, pz = cx + math.cos(a) * r, cz + math.sin(a) * r
        b.cylinder((px, cy - p["thick"] - hb * 0.35, pz), (0.09, hb * 0.6, 0.09), hex_lin(P["copperDark"]), 6)
        b.ring((px, cy - p["thick"] - hb * 0.62, pz), (0.22, 1, 0.22), hex_lin(P["brass"]), tube=0.1, tubular=8, rot=(math.pi / 2, 0, 0))
    # railing posts around most of the rim (gaps are cut by the bridges' landings visually; posts are thin)
    for i in range(n):
        ax, az = inner[i]
        if pid == "dock" and i in (3, 4): continue
        b.box((ax, cy + 0.22, az), (0.035, 0.44, 0.035), steel)
    for i in range(n):
        ax, az = inner[i]; bx, bz = inner[(i + 1) % n]
        if pid == "dock" and i in (2, 3, 4): continue
        b.box(((ax + bx) / 2, cy + 0.42, (az + bz) / 2), (0.025, 0.025, math.hypot(bx - ax, bz - az)), hex_lin(P["brass"]), rot=(0, math.atan2(bx - ax, bz - az), 0))

# ----------------------------------------------------------------------------- machinery pieces (local frame via `world`)
def gear(b, pos, radius, width, teeth, color, rot=(0, 0, 0), world=Matrix.Identity(4), spokes=True):
    m = world @ part_matrix(pos, (1, 1, 1), rot)
    b.cylinder((0, 0, 0), (radius * 2 * 0.86, width, radius * 2 * 0.86), color, max(8, teeth), world=m)
    for i in range(teeth):
        a = 2 * math.pi * i / teeth
        b.box((math.cos(a) * radius * 0.9, 0, math.sin(a) * radius * 0.9), (radius * 0.26, width * 1.02, radius * 0.22), color, rot=(0, -a, 0), world=m)
    b.cylinder((0, 0, 0), (radius * 0.3, width * 1.2, radius * 0.3), shade(color, -0.2), 8, world=m)
    if spokes:
        for i in range(3): b.box((0, 0, 0), (radius * 1.5, width * 0.5, radius * 0.16), shade(color, -0.12), rot=(0, math.pi / 3 * i, 0), world=m)
def pipe(b, a, c, radius, color, elbows=True):
    b.cylinder((0, 0, 0), (radius * 2, 1, radius * 2), color, 6, world=along(a, c))
    if elbows: b.blob(tuple(c), (radius * 2.3,) * 3, color, 0)
def pipe_run(b, points, radius, color):
    for a, c in zip(points, points[1:]): pipe(b, a, c, radius, color)
def strut(b, a, c, radius, color): b.cylinder((0, 0, 0), (radius * 2, 1, radius * 2), color, 5, world=along(a, c))
def chain(b, a, c, color):
    a, c = Vector(a), Vector(c); n = max(2, int((c - a).length / 0.16))
    for i in range(n):
        p = a + (c - a) * ((i + 0.5) / n)
        b.ring((0, 0, 0), (0.1, 1, 0.1), color, tube=0.18, radial=4, tubular=6, rot=(0, 0, math.pi / 2 * (i % 2)), world=along(a, c) @ Matrix.Translation((0, (i + 0.5) / n - 0.5, 0)) @ Matrix.Diagonal((1, 1 / (c - a).length, 1, 1)))
def tank(b, world, radius=0.42, height=0.9, color=None, band=None):
    color = color or hex_lin(P["steelLight"]); band = band or hex_lin(P["copper"])
    b.cylinder((0, height / 2, 0), (radius * 2, height, radius * 2), color, 12, world=world)
    b.blob((0, height, 0), (radius * 2, radius * 0.9, radius * 2), color, 1, world=world)
    for y in (0.25, 0.65): b.ring((0, height * y, 0), (radius * 2.08, 1, radius * 2.08), band, tube=0.025, tubular=12, world=world)
    for i in range(4): b.box((math.cos(math.pi / 2 * i) * radius * 1.05, 0.08, math.sin(math.pi / 2 * i) * radius * 1.05), (0.1, 0.16, 0.1), hex_lin(P["iron"]), world=world)
def crane(b, world, reach=1.6, height=1.5, color=None):
    color = color or hex_lin(P["brass"]); dark = hex_lin(P["iron"])
    b.cylinder((0, 0.08, 0), (0.6, 0.16, 0.6), dark, 10, world=world); b.box((0, height / 2, 0), (0.18, height, 0.18), color, world=world)
    b.box((0, height + 0.08, 0), (0.3, 0.2, 0.3), dark, world=world)
    b.box((0, height + 0.05, reach / 2 - 0.1), (0.12, 0.1, reach + 0.2), color, world=world)
    b.box((0, height + 0.05, -0.42), (0.26, 0.26, 0.5), dark, world=world)   # counterweight
    for i in range(1, 4): b.box((0, height - 0.05 - i * 0.05, reach * i / 4), (0.03, 0.03, reach / 4), shade(color, -0.1), rot=(0.25, 0, 0), world=world)
    hook = (0, height - 0.75, reach - 0.2)
    strut(b, (0, height, reach - 0.2), hook, 0.012, hex_lin(P["cable"]))
    b.box(hook, (0.12, 0.08, 0.06), dark, world=world)
    b.box((hook[0], hook[1] - 0.22, hook[2]), (0.32, 0.3, 0.3), hex_lin(P["crateA"]), rot=(0, 0.3, 0), world=world)   # the lifted crate
def crate(b, world, s=0.32, color=None):
    color = color or hex_lin(P["crateA"]); b.box((0, s / 2, 0), (s, s, s), color, world=world)
    for i in (-1, 1): b.box((0, s / 2, i * s * 0.5), (s * 1.02, s * 0.12, s * 0.06), hex_lin(P["wood"]), world=world); b.box((i * s * 0.5, s / 2, 0), (s * 0.06, s * 0.12, s * 1.02), hex_lin(P["wood"]), world=world)
def lamp(b, acc, world, h=0.7):
    b.box((0, h / 2, 0), (0.035, h, 0.035), hex_lin(P["iron"]), world=world); b.box((0, h + 0.04, 0), (0.12, 0.08, 0.12), hex_lin(P["brassDark"]), world=world)
    acc.box((0, h + 0.03, 0), (0.09, 0.06, 0.09), hex_lin(P["warm"]), world=world)
def coil(b, acc, world, radius=0.26, turns=5, height=0.9):
    b.cylinder((0, height / 2, 0), (radius * 0.9, height, radius * 0.9), hex_lin(P["copperDark"]), 8, world=world)
    for i in range(turns): acc.ring((0, height * (i + 0.5) / turns, 0), (radius * 2.1, 1, radius * 2.1), hex_lin(P["cyanDeep"]), tube=0.04, tubular=10, world=world)
    acc.blob((0, height + 0.2, 0), (0.26, 0.26, 0.26), hex_lin(P["cyan"]), 1, world=world)

# ----------------------------------------------------------------------------- structures (local frame: base at y = 0, +Z = front)
def workshop_hall(b):
    """CareerLens: the central mechanical workshop with a great brass lens turret on the roof, a big side flywheel and a wide door."""
    wall, trim, roof = hex_lin(P["concrete"]), hex_lin(P["copper"]), hex_lin(P["slate"]); brass, iron = hex_lin(P["brass"]), hex_lin(P["iron"])
    b.box((0, 0.5, 0), (1.9, 1.0, 1.4), wall); b.box((0, 1.05, 0), (2.02, 0.12, 1.52), trim)
    for z in (-0.72, 0.72): b.box((0, 1.28, z * 0.98), (2.0, 0.34, 0.08), shade(wall, -0.06))      # roof parapets
    b.cylinder((0, 1.1, 0), (1.38, 2.0, 1.38), roof, 12, rot=(0, 0, math.pi / 2))                     # barrel roof (axis X)
    for i in range(5): b.box((-0.8 + i * 0.4, 1.78, 0), (0.06, 0.05, 1.3), shade(roof, 0.12))          # roof ribs
    # lens turret: a brass ring frame holding a great lens, on a geared mount
    b.cylinder((0.35, 1.98, -0.1), (0.7, 0.3, 0.7), hex_lin(P["brassDark"]), 10)
    gear(b, (0.35, 2.17, -0.1), 0.42, 0.08, 12, brass, spokes=False)
    b.box((0.35, 2.55, -0.1), (0.12, 0.7, 0.12), iron)
    b.ring((0.35, 2.95, -0.1), (0.95, 1, 0.95), brass, tube=0.09, tubular=16, rot=(0.6, 0, 0))
    b.cylinder((0.35, 2.95, -0.1), (0.76, 0.05, 0.76), hex_lin(P["lens"]), 16, rot=(0.6, 0, 0))
    b.box((0.35, 2.95, -0.1), (0.05, 1.12, 0.05), iron, rot=(0.6, 0, 0)); b.box((0.35, 2.95, -0.1), (1.12, 0.05, 0.05), iron, rot=(0.6, 0, 0))
    # side flywheel and drive
    gear(b, (-1.05, 0.62, 0.2), 0.5, 0.1, 14, hex_lin(P["brass"]), rot=(0, 0, math.pi / 2))
    b.cylinder((-1.0, 0.62, 0.2), (0.14, 0.3, 0.14), iron, 8, rot=(0, 0, math.pi / 2))
    b.box((-1.05, 0.25, 0.2), (0.14, 0.5, 0.26), iron)
    gear(b, (-1.08, 0.2, -0.45), 0.24, 0.08, 9, hex_lin(P["copper"]), rot=(0, 0, math.pi / 2))
    # chimney with cap, pipes along the back wall
    b.cylinder((-0.6, 1.6, -0.45), (0.28, 1.1, 0.28), hex_lin(P["rust"]), 8); b.cylinder((-0.6, 2.18, -0.45), (0.4, 0.08, 0.4), iron, 8)
    pipe_run(b, [(0.8, 0.3, -0.72), (0.8, 0.9, -0.72), (0.4, 0.9, -0.72), (0.4, 1.0, -0.4)], 0.045, hex_lin(P["copper"]))
    # the wide workshop door with a brass lintel and a step, windows
    b.box((0, 0.36, 0.71), (0.7, 0.72, 0.03), iron); b.box((0, 0.36, 0.72), (0.03, 0.72, 0.02), brass); b.box((0, 0.74, 0.72), (0.8, 0.06, 0.05), brass)
    b.box((0, 0.025, 0.86), (0.9, 0.05, 0.28), hex_lin(P["steelDark"]))
    for x in (-0.65, 0.65): b.box((x, 0.6, 0.71), (0.26, 0.28, 0.03), iron)
    for z in (-1, 1): b.box((0.96, 0.55, 0.0), (0.03, 0.3, 0.5), iron)
    b.box((0, 1.14, 0.78), (1.1, 0.16, 0.03), hex_lin(P["canvas"]))                                   # sign board
    return dict(footprint=1.25, height=3.5)
def workshop_accents(a, world):
    for x in (-0.65, 0.65): a.box((x, 0.6, 0.725), (0.2, 0.22, 0.01), hex_lin(P["warm"]), world=world)
    a.box((0.96, 0.55, 0.0), (0.01, 0.24, 0.44), hex_lin(P["warm"]), world=world)
    a.cylinder((0.35, 2.95, -0.1), (0.5, 0.06, 0.5), hex_lin(P["cyanPale"]), 12, rot=(0.6, 0, 0), world=world)   # the lens glow
    a.box((0, 1.14, 0.795), (0.98, 0.08, 0.01), hex_lin(P["cyan"]), world=world)                                     # sign light

def forge_station(b):
    """DevTools: a tool forge: a brick furnace with a tall chimney, bellows, an anvil under a mechanical hammer arm, a tool rack."""
    brick, iron, brass, copper = hex_lin(P["rust"]), hex_lin(P["iron"]), hex_lin(P["brass"]), hex_lin(P["copper"])
    b.box((-0.35, 0.45, -0.2), (1.1, 0.9, 0.9), brick); b.box((-0.35, 0.93, -0.2), (1.2, 0.08, 1.0), hex_lin(P["steelDark"]))
    b.box((-0.35, 0.3, 0.26), (0.5, 0.36, 0.04), iron)                                                    # furnace mouth
    b.cylinder((-0.55, 1.5, -0.35), (0.34, 1.1, 0.34), hex_lin(P["steelDark"]), 8); b.cylinder((-0.55, 2.1, -0.35), (0.46, 0.1, 0.46), iron, 8)
    b.cone((-0.55, 2.26, -0.35), (0.3, 0.24, 0.3), iron, 8)
    # bellows
    b.box((-1.05, 0.5, -0.2), (0.4, 0.3, 0.5), hex_lin(P["wood"])); b.box((-1.0, 0.72, -0.2), (0.45, 0.14, 0.52), hex_lin(P["canvas"]))
    # anvil and hammer arm
    b.box((0.55, 0.22, 0.25), (0.3, 0.44, 0.3), hex_lin(P["steelDark"])); b.box((0.55, 0.5, 0.25), (0.62, 0.14, 0.3), iron)
    b.box((0.95, 0.9, -0.1), (0.14, 1.8, 0.14), iron); b.box((0.95, 1.82, 0.08), (0.12, 0.12, 0.6), brass)
    b.box((0.72, 1.4, 0.3), (0.1, 0.9, 0.1), brass, rot=(0.35, 0, 0)); b.box((0.58, 0.88, 0.3), (0.3, 0.3, 0.26), iron)   # hammer head
    gear(b, (0.95, 1.5, -0.28), 0.3, 0.08, 10, copper, rot=(math.pi / 2, 0, 0))
    # tool rack
    b.box((0.2, 0.65, -0.62), (1.3, 0.9, 0.06), hex_lin(P["wood"]))
    for i in range(5): b.box((-0.3 + i * 0.25, 0.65, -0.57), (0.05, 0.5 + 0.1 * (i % 2), 0.04), hex_lin(P["steelLight"]))
    for i in range(5): b.box((-0.3 + i * 0.25, 0.95, -0.57), (0.14, 0.1, 0.06), hex_lin(P["crateA"]))
    # quench barrel and a pile of coal
    b.cylinder((0.1, 0.22, 0.55), (0.4, 0.44, 0.4), hex_lin(P["wood"]), 8); b.cylinder((0.1, 0.44, 0.55), (0.34, 0.02, 0.34), hex_lin(P["cyanDeep"]), 8)
    for (x, z, s) in ((-0.9, 0.5, 0.2), (-0.72, 0.6, 0.16), (-0.8, 0.36, 0.14)): b.blob((x, s * 0.4, z), (s, s * 0.7, s), hex_lin(P["cable"]), 0)
    return dict(footprint=1.15, height=2.4)
def forge_accents(a, world):
    a.box((-0.35, 0.3, 0.275), (0.42, 0.28, 0.01), hex_lin(P["ember"]), world=world)
    a.blob((0.55, 0.6, 0.25), (0.1, 0.06, 0.1), hex_lin(P["ember"]), 0, world=world)
    a.cylinder((-0.55, 2.4, -0.35), (0.16, 0.2, 0.16), hex_lin(P["ember"]), 6, world=world)

def replicator_bay(b):
    """Multiple Git Clone: a duplication machine: a brass scanner arch feeds one crate in and identical crates roll out on a conveyor."""
    brass, iron, copper, steel = hex_lin(P["brass"]), hex_lin(P["iron"]), hex_lin(P["copper"]), hex_lin(P["steel"])
    b.box((0, 0.2, 0), (2.2, 0.12, 0.8), hex_lin(P["steelDark"]))                                          # conveyor bed
    for i in range(9): b.cylinder((-1.0 + i * 0.25, 0.28, 0), (0.1, 0.78, 0.1), steel, 6, rot=(math.pi / 2, 0, 0))
    for x in (-1.0, 1.0): b.box((x, 0.1, 0), (0.2, 0.2, 0.8), iron)
    # scanner arch (the "clone" gate)
    b.box((-0.25, 0.75, -0.45), (0.16, 1.1, 0.16), brass); b.box((-0.25, 0.75, 0.45), (0.16, 1.1, 0.16), brass); b.box((-0.25, 1.33, 0), (0.2, 0.18, 1.1), brass)
    b.box((-0.25, 1.5, 0), (0.5, 0.2, 0.5), iron); gear(b, (-0.25, 1.68, 0), 0.26, 0.06, 10, copper, spokes=False)
    # the source crate (left) and three identical copies (right)
    crate(b, yaw((-0.75, 0.34, 0), 0.0), 0.34, hex_lin(P["crateB"]))
    for i in range(3): crate(b, yaw((0.1 + i * 0.4, 0.34, 0), 0.0), 0.3, hex_lin(P["crateB"]))
    # control cabinet and dials
    b.box((0.4, 0.5, -0.75), (0.9, 1.0, 0.4), hex_lin(P["steelDark"])); b.box((0.4, 0.8, -0.54), (0.7, 0.3, 0.03), iron)
    for i in range(3): b.cylinder((0.1 + i * 0.3, 0.42, -0.54), (0.14, 0.04, 0.14), brass, 8, rot=(math.pi / 2, 0, 0))
    b.cylinder((1.0, 0.95, -0.75), (0.3, 1.9, 0.3), hex_lin(P["copperDark"]), 8)                           # exhaust stack
    return dict(footprint=1.25, height=1.9)
def replicator_accents(a, world):
    a.box((-0.25, 0.75, 0), (0.04, 1.04, 0.86), hex_lin(P["cyan"]), world=world)                            # the scanning sheet
    a.box((0.4, 0.8, -0.535), (0.62, 0.22, 0.01), hex_lin(P["cyanPale"]), world=world)

def control_tower(b):
    """The Tools hub's dock: a control tower with a brass dish, a signal mast and the landing pad markings (environment, not a landmark)."""
    steel, iron, brass = hex_lin(P["steelLight"]), hex_lin(P["iron"]), hex_lin(P["brass"])
    b.cylinder((0, 0.75, 0), (0.6, 1.5, 0.6), steel, 8, top=0.8); b.cylinder((0, 1.62, 0), (0.9, 0.3, 0.9), hex_lin(P["slate"]), 8)
    b.cylinder((0, 1.95, 0), (0.72, 0.36, 0.72), hex_lin(P["glass"]), 8); b.cone((0, 2.25, 0), (0.86, 0.26, 0.86), hex_lin(P["copper"]), 8)
    b.box((0, 2.7, 0), (0.05, 0.7, 0.05), iron)
    b.cylinder((0.32, 1.95, 0.0), (0.5, 0.06, 0.5), brass, 10, rot=(0, 0, -1.1))                         # dish
    b.box((0, 0.05, 0.05), (0.42, 0.1, 0.9), iron)                                                        # entrance step
    return dict(footprint=0.6, height=3.05)
def tower_accents(a, world):
    a.cylinder((0, 1.95, 0), (0.6, 0.26, 0.6), hex_lin(P["warm"]), 8, world=world)
    a.blob((0, 3.07, 0), (0.1, 0.1, 0.1), hex_lin(P["red"]), 0, world=world)

# ----------------------------------------------------------------------------- bridges and catwalks
def bridge(b, acc, name, a, c, width, cols, mat, truss=True):
    m, n = span(a, c); rb = Builder(); plank, rail, iron = hex_lin(P["plank"]), hex_lin(P["brass"]), hex_lin(P["iron"])
    steps = max(2, int(n / 0.36))
    for i in range(steps):
        rb.box((0, -0.03, (i + 0.5) / steps * n), (width, 0.06, n / steps * 0.9), plank if i % 2 else shade(plank, -0.06), world=m)
    for sx in (-1, 1):
        rb.box((sx * width / 2, -0.09, n / 2), (0.08, 0.12, n), iron, world=m)                             # side girders
        rb.box((sx * width / 2, 0.42, n / 2), (0.025, 0.025, n), rail, world=m)                           # handrails
        for i in range(int(n / 0.6) + 1):
            z = min(n - 0.05, 0.05 + i * 0.6); rb.box((sx * width / 2, 0.21, z), (0.03, 0.42, 0.03), hex_lin(P["steel"]), world=m)
        if truss:
            for i in range(int(n / 0.7)):
                z = (i + 0.5) * 0.7
                rb.box((sx * width / 2, -0.28, z), (0.04, 0.04, 0.7 * 1.2), iron, rot=(0.9, 0, 0), world=m)
                rb.box((sx * width / 2, -0.28, z), (0.04, 0.04, 0.7 * 1.2), iron, rot=(-0.9, 0, 0), world=m)
            rb.box((0, -0.42, n / 2), (width * 1.04, 0.05, n), iron, world=m)
    if truss:   # energy conduit along the underside
        acc.box((0, -0.5, n / 2), (0.05, 0.05, n * 0.98), hex_lin(P["cyanDeep"]), world=m)
    rb.to_object(name, cols["TOOLS_PATHS"], mat)
    return n

# ----------------------------------------------------------------------------- build
def build():
    scene, cols = reset_scene()
    mat, accent = diorama_material("ToolsDiorama"), diorama_material("ToolsAccent", emissive=True)
    rng = LCG(20261023)
    layout = dict(version=1, world="tools", up="+Y", front="+Z", platforms={k: dict(centre=list(v["c"]), shape=v["shape"], size=list(v["size"]), yaw=v["yaw"]) for k, v in PLATFORMS.items()},
                  structures=[], anchors={}, bridges=[], decorations={})

    # --- platforms (one mesh)
    tb = Builder()
    for pid in PLATFORMS: platform(tb, pid, rng)
    tb.to_object("TOOLS_TERRAIN", cols["TOOLS_TERRAIN"], mat); terrain_tris = tb.tris

    # --- structures (separate objects; origin at the base centre on the deck; forward toward the front / the bridge)
    def place(name, sid, recipe, pid, lx, lz, facing, env=False, scale=1.0):
        pos = deck_point(pid, lx, lz); bb = Builder(); meas = recipe(bb)
        m = yaw(pos, facing, scale); ob = bb.to_object(name, cols["TOOLS_BUILDINGS"], mat, C4 @ m @ C4i)
        if env: ob["role"] = f"environment:{sid}"
        else: ob["structure_id"] = sid
        ob["footprint_radius"] = meas["footprint"] * scale
        layout["structures"].append(dict(node=name, structure_id=sid, environment=env, platform=pid, origin=[round(v, 4) for v in pos], facing=facing, footprint=meas["footprint"] * scale, height=meas["height"] * scale, triangles=bb.tris))
        return m
    hall_m = place("WORKSHOP_HALL", "workshop-hall", workshop_hall, "main", -0.55, -0.35, 0.0)
    forge_m = place("FORGE_STATION", "forge-station", forge_station, "forge", 0.1, -0.1, -0.5)
    bay_m = place("REPLICATOR_BAY", "replicator-bay", replicator_bay, "bay", 0.0, -0.1, 0.18)
    tower_m = place("CONTROL_TOWER", "control-tower", control_tower, "dock", -0.65, -0.55, 0.0, env=True)

    # --- bridges and catwalks between deck edges
    ab = Builder()
    def link(name, pa, pb, width, truss=True):
        da = PLATFORMS[pb]["c"]; ca = PLATFORMS[pa]["c"]; d = (da[0] - ca[0], da[2] - ca[2])
        a = edge_point(pa, d); c = edge_point(pb, (-d[0], -d[1]))
        n = bridge(None, ab, name, a + Vector((0, 0.0, 0)), c, width, cols, mat, truss)
        layout["bridges"].append(dict(id=name, from_=pa, to=pb, start=[round(v, 4) for v in a], end=[round(v, 4) for v in c], length=round(n, 4), width=width))
    link("TOOLS_BRIDGE_MAIN_FORGE", "main", "forge", 0.62)
    link("TOOLS_BRIDGE_MAIN_BAY", "main", "bay", 0.62)
    link("TOOLS_BRIDGE_MAIN_DOCK", "main", "dock", 0.7)
    link("TOOLS_CATWALK_MAIN_POWER", "main", "power", 0.42)
    link("TOOLS_CATWALK_MAIN_SPARE", "main", "spare", 0.42, truss=False)

    # --- decorations (one merged object) and accents (one merged emissive object)
    dec = Builder(); counts = dict(gears=0, tanks=0, cranes=0, crates=0, lamps=0, coils=0, pipes=0, struts=0)
    # main deck: a big drive gear train beside the hall, a crane, crates, the assembly station (mini-game candidate), lamps
    gear(dec, deck_point("main", 1.25, -0.95) + Vector((0, 0.42, 0)), 0.42, 0.1, 12, hex_lin(P["brass"]), rot=(0, 0, math.pi / 2)); counts["gears"] += 1
    gear(dec, deck_point("main", 1.25, -0.25) + Vector((0, 0.3, 0)), 0.3, 0.1, 9, hex_lin(P["copper"]), rot=(0, 0, math.pi / 2)); counts["gears"] += 1
    dec.box(tuple(deck_point("main", 1.25, -0.6) + Vector((0, 0.15, 0))), (0.16, 0.3, 1.0), hex_lin(P["iron"]))
    crane(dec, yaw(tuple(deck_point("main", 1.55, 0.95)), 2.3)); counts["cranes"] += 1
    for (lx, lz, s, c) in ((-1.55, 1.05, 0.3, P["crateA"]), (-1.25, 1.15, 0.26, P["crateC"]), (-1.45, 0.72, 0.24, P["crateA"])):
        crate(dec, yaw(tuple(deck_point("main", lx, lz)), rng.range(0, 1.2)), s, hex_lin(c)); counts["crates"] += 1
    # the machine-assembly station: a round work table with parts and a small arm (the mini-game candidate spot)
    st = deck_point("main", 0.35, 1.05)
    dec.cylinder(tuple(st + Vector((0, 0.3, 0))), (0.9, 0.08, 0.9), hex_lin(P["steelDark"]), 12); dec.cylinder(tuple(st + Vector((0, 0.13, 0))), (0.3, 0.26, 0.3), hex_lin(P["iron"]), 8)
    for i in range(4): dec.box(tuple(st + Vector((math.cos(1.6 * i) * 0.28, 0.38, math.sin(1.6 * i) * 0.28))), (0.12, 0.08, 0.1), hex_lin(P["brass"]), rot=(0, i * 0.7, 0))
    dec.box(tuple(st + Vector((0.5, 0.55, 0))), (0.06, 0.5, 0.06), hex_lin(P["copper"])); dec.box(tuple(st + Vector((0.3, 0.8, 0))), (0.45, 0.05, 0.05), hex_lin(P["copper"]))
    for (lx, lz) in ((-1.9, 0.2), (1.95, -1.1), (-0.2, 1.5), (0.9, -1.55)):
        lamp(dec, ab, yaw(tuple(deck_point("main", lx, lz)), 0.0)); counts["lamps"] += 1
    # forge platform: a water tank and a coal bunker
    tank(dec, yaw(tuple(deck_point("forge", -0.85, 0.55)), 0.0), 0.3, 0.75); counts["tanks"] += 1
    dec.box(tuple(deck_point("forge", 0.75, 0.7) + Vector((0, 0.2, 0))), (0.6, 0.4, 0.5), hex_lin(P["wood"]))
    # bay platform: crates waiting, a small crane
    for i, (lx, lz) in enumerate(((0.95, 0.65), (0.7, 0.72), (0.95, 0.35))): crate(dec, yaw(tuple(deck_point("bay", lx, lz)), 0.2 * i), 0.26, hex_lin(P["crateB"])); counts["crates"] += 1
    crane(dec, yaw(tuple(deck_point("bay", -0.9, 0.6)), -2.2), reach=1.1, height=1.2, color=hex_lin(P["copper"])); counts["cranes"] += 1
    # dock platform: landing pad markings and tie-down bollards
    pad = deck_point("dock", 0.35, 0.35)
    dec.ring(tuple(pad + Vector((0, 0.012, 0))), (1.3, 1, 1.3), hex_lin(P["brass"]), tube=0.02, tubular=16)
    dec.ring(tuple(pad + Vector((0, 0.012, 0))), (0.5, 1, 0.5), hex_lin(P["brass"]), tube=0.03, tubular=12)
    for i in range(4): dec.box(tuple(pad + Vector((math.cos(math.pi / 2 * i + 0.785) * 0.78, 0.07, math.sin(math.pi / 2 * i + 0.785) * 0.78))), (0.1, 0.14, 0.1), hex_lin(P["iron"]))
    # power platform: the energy core (a cyan sphere in a brass cage) and two coils; the spare perch: a big tank and pipes
    core = deck_point("power", 0.0, 0.0)
    dec.cylinder(tuple(core + Vector((0, 0.12, 0))), (0.9, 0.24, 0.9), hex_lin(P["iron"]), 10)
    dec.ring(tuple(core + Vector((0, 0.78, 0))), (1.0, 1, 1.0), hex_lin(P["brass"]), tube=0.05, tubular=16, rot=(math.pi / 2, 0, 0))
    dec.ring(tuple(core + Vector((0, 0.78, 0))), (1.0, 1, 1.0), hex_lin(P["brass"]), tube=0.05, tubular=16, rot=(0, 0, math.pi / 2))
    for lx, lz in ((0.55, 0.4), (-0.55, 0.4)): coil(dec, ab, yaw(tuple(deck_point("power", lx, lz)), 0.0), 0.16, 4, 0.6); counts["coils"] += 1
    tank(dec, yaw(tuple(deck_point("spare", 0.0, 0.0)), 0.0), 0.42, 0.95, hex_lin(P["copper"]), hex_lin(P["brassDark"])); counts["tanks"] += 1
    # pipes and energy conduits between platforms (under the catwalks and down to the hulls), chains holding the power platform
    cp = hex_lin(P["copperDark"])
    pipe_run(dec, [tuple(deck_point("main", 1.2, -1.6) + Vector((0, -0.2, 0))), tuple(deck_point("main", 1.2, -1.6) + Vector((0, -0.8, 0))), tuple(deck_point("power", -0.5, 0.5) + Vector((0, -0.9, 0))), tuple(deck_point("power", -0.5, 0.5) + Vector((0, -0.2, 0)))], 0.06, cp); counts["pipes"] += 1
    pipe_run(dec, [tuple(deck_point("main", -1.6, -0.9) + Vector((0, -0.3, 0))), tuple(deck_point("main", -1.6, -0.9) + Vector((0, -0.9, 0))), tuple(deck_point("spare", 0.3, 0.5) + Vector((0, -0.8, 0))), tuple(deck_point("spare", 0.3, 0.5) + Vector((0, -0.2, 0)))], 0.06, cp); counts["pipes"] += 1
    pipe_run(dec, [tuple(deck_point("main", 1.9, 0.6) + Vector((0, -0.4, 0))), tuple(deck_point("forge", -1.0, -0.3) + Vector((0, -0.6, 0))), tuple(deck_point("forge", -0.6, -0.3) + Vector((0, -0.25, 0)))], 0.05, cp); counts["pipes"] += 1
    for (lx, lz) in ((0.5, -0.5), (-0.5, -0.5), (0.0, 0.6)):
        top = deck_point("main", 1.35 + lx * 0.4, -1.55); top.y += 2.3
        chain(dec, tuple(top), tuple(deck_point("power", lx, lz) + Vector((0, 0.05, 0))), hex_lin(P["steelDark"])); counts["struts"] += 1
    gm = deck_point("main", 1.35, -1.55)
    dec.box(tuple(gm + Vector((0, 1.15, 0))), (0.12, 2.3, 0.12), hex_lin(P["iron"])); dec.box(tuple(gm + Vector((0.4, 2.3, -0.3))), (1.2, 0.1, 0.1), hex_lin(P["brass"]), rot=(0, -0.6, 0))   # the gantry mast
    strut(dec, tuple(deck_point("bay", 1.1, -0.6) + Vector((0, -0.3, 0))), tuple(deck_point("main", -1.7, 0.9) + Vector((0, -0.6, 0))), 0.04, hex_lin(P["steelDark"])); counts["struts"] += 1
    strut(dec, tuple(deck_point("dock", -0.8, -0.9) + Vector((0, -0.25, 0))), tuple(deck_point("main", 0.4, 1.5) + Vector((0, -0.6, 0))), 0.04, hex_lin(P["steelDark"])); counts["struts"] += 1
    dec.to_object("TOOLS_DECORATIONS_STATIC", cols["TOOLS_DECORATIONS"], mat)

    workshop_accents(ab, hall_m); forge_accents(ab, forge_m); replicator_accents(ab, bay_m); tower_accents(ab, tower_m)
    ab.blob(tuple(core + Vector((0, 0.78, 0))), (0.62, 0.62, 0.62), hex_lin(P["cyan"]), 1)                 # the power core
    for i in range(4): ab.box(tuple(pad + Vector((math.cos(math.pi / 2 * i + 0.785) * 0.78, 0.15, math.sin(math.pi / 2 * i + 0.785) * 0.78))), (0.06, 0.03, 0.06), hex_lin(P["cyan"]))
    ab.to_object("TOOLS_ACCENTS_GLOW", cols["TOOLS_ACCENTS"], accent)
    layout["decorations"] = counts

    # --- anchors (empties; names, roles and radii only). Up = +Y on every deck; forward = the structure's facing.
    def empty(name, point, role, radius=None, facing=0.0):
        ob = bpy.data.objects.new(name, None); ob.empty_display_type = "PLAIN_AXES"; ob.empty_display_size = 0.15
        ob.matrix_world = C4 @ yaw(tuple(point), facing) @ C4i; ob["role"] = role
        if radius is not None: ob["radius"] = float(radius)
        cols["TOOLS_ANCHORS"].objects.link(ob)
        layout["anchors"][name] = dict(origin=[round(v, 4) for v in point], role=role, radius=radius)
    def door(m, dist, up=0.0): return (m @ Vector((0, up, dist))).to_3d()
    empty("TOOLS_ANCHOR_interaction_workshop_hall", door(hall_m, 1.1), "interaction:workshop-hall")
    empty("TOOLS_ANCHOR_interaction_forge_station", door(forge_m, 0.95), "interaction:forge-station", facing=-0.5)
    empty("TOOLS_ANCHOR_interaction_replicator_bay", door(bay_m, 1.05), "interaction:replicator-bay", facing=0.18)
    empty("TOOLS_ANCHOR_hub_control_tower", door(tower_m, 0.75), "hub-entrance:control-tower")
    # camera focus points: the visual centre of each structure (the lens, the hammer, the scanner arch, the tower cabin)
    empty("TOOLS_ANCHOR_focus_workshop_hall", door(hall_m, -0.1, 1.9), "focus:workshop-hall")
    empty("TOOLS_ANCHOR_focus_forge_station", door(forge_m, 0.0, 1.0), "focus:forge-station")
    empty("TOOLS_ANCHOR_focus_replicator_bay", door(bay_m, 0.0, 0.8), "focus:replicator-bay")
    empty("TOOLS_ANCHOR_focus_control_tower", door(tower_m, 0.0, 1.9), "focus:control-tower")
    empty("TOOLS_ANCHOR_landing", pad, "landing", radius=0.3)
    empty("TOOLS_ANCHOR_spawn", pad + Vector((-0.35, 0, -0.3)), "spawn", facing=0.0)
    empty("TOOLS_ANCHOR_lander_arrival", pad + Vector((0, 0.55, 0)), "lander-arrival", radius=0.3)
    empty("TOOLS_ANCHOR_minigame_candidate", st, "minigame-candidate", radius=0.35)
    # --- navigation reference (not exported): the landing circle
    nb = Builder()
    for i in range(24):
        a0, a1 = 2 * math.pi * i / 24, 2 * math.pi * (i + 1) / 24
        p = lambda a: pad + Vector((math.cos(a) * 0.3, 0.01, math.sin(a) * 0.3))
        nb.quad([tuple(p(a0)), tuple(p(a1)), tuple(p(a1) + Vector((0, 0.02, 0))), tuple(p(a0) + Vector((0, 0.02, 0)))], hex_lin("#ff5a5a"))
    nb.to_object("TOOLS_NAV_landing_circle", cols["TOOLS_NAVIGATION_REFERENCE"], mat)
    for ob in scene.objects:
        if ob.type == "MESH": ob["tools_layer"] = ob.users_collection[0].name
    # --- statistics (Gateway space)
    pts_all, tris = [], 0
    for ob in scene.objects:
        if ob.type != "MESH" or ob.users_collection[0].name == "TOOLS_NAVIGATION_REFERENCE": continue
        pts_all += [C4i @ (ob.matrix_world @ v.co) for v in ob.data.vertices]; tris += sum(len(p.vertices) - 2 for p in ob.data.polygons)
    ext = max(p.length for p in pts_all)
    mn = [round(min(p[i] for p in pts_all), 4) for i in range(3)]; mx = [round(max(p[i] for p in pts_all), 4) for i in range(3)]
    layout["stats"] = dict(triangles=tris, terrain_triangles=terrain_tris, meshes=sum(1 for o in scene.objects if o.type == "MESH" and o.users_collection[0].name != "TOOLS_NAVIGATION_REFERENCE"),
        anchors=len(layout["anchors"]), extent=round(ext, 4), bounds=[mn, mx], centre=[round((mn[i] + mx[i]) / 2, 4) for i in range(3)])
    os.makedirs(os.path.join(ROOT, "references"), exist_ok=True)
    with open(os.path.join(ROOT, "references", "layout-v1.json"), "w") as f: json.dump(layout, f, indent=1)
    print(json.dumps(layout["stats"]), json.dumps(counts))
    return scene

build()
