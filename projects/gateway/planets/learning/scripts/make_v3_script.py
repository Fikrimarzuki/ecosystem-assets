"""Derive build_learning_town_v3.py from the v2 build script (M8.9b.1a.4 composition polish). v2 stays untouched.
Changes: new scene/file names; three new environmental features (far-side lookout, west reading garden, south-east scholar
grove) each with a short lane; the monument's paved walk and reading courtyard; plaza stone benches, lantern banners and a
compass inlay; terrain-transition rings around the plaza and courtyards; an oriented-rectangle footprint comparison in the
clearance report."""
import re, os
here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "build_learning_town_v2.py"), encoding="utf-8").read()
out = src

def rep(a, b, count=1):
    global out
    assert out.count(a) >= 1, a[:90]
    out = out.replace(a, b, count)

rep('"""M8.9b.1a.3 — Blender Academy Town v2 (Learning planet)', '"""M8.9b.1a.4 — Blender Academy Town v3 (composition polish of v2; Learning planet)')
rep('SCENE_NAME = "LEARNING_V2"', 'SCENE_NAME = "LEARNING_V3"')
rep('"layout-v2.json"', '"layout-v3.json"'); rep('"clearance-report-v2.json"', '"clearance-report-v3.json"')
rep('scene["gateway_asset"] = "learning-globe-blender-v2"', 'scene["gateway_asset"] = "learning-globe-blender-v3"')

# Sites: lookout on the far-side highland shoulder, reading garden on the west slope, scholar grove on the south-east slope.
rep('"marker": (206, 49, None), "pond": (236, 12, None), "highland": (176, 26, None), "ruin": (200, 67, None),',
    '"marker": (206, 49, None), "pond": (236, 12, None), "highland": (176, 20, None), "ruin": (200, 67, None),\n    "lookout": (176, 40, None), "reading-garden": (320, 24, None), "scholar-grove": (118, 10, None),')
# Routes: lanes to the three features and the monument walk (the monument sits at lon 89.3°, lat 22.4° in v2).
rep('    dict(id="classroom-lane", width=SECONDARY, serves=["classroom", "academy-tower"], points=[(124, 50), (134, 45), (141, 42)]),\n]',
    '''    dict(id="classroom-lane", width=SECONDARY, serves=["classroom", "academy-tower"], points=[(124, 50), (134, 45), (141, 42)]),
    dict(id="lookout-lane", width=SECONDARY, serves=["lookout"], points=[(176, 53.5), (176, 50.5), (176, 47.5)]),
    dict(id="garden-lane", width=SECONDARY, serves=["reading-garden"], points=[(322, 43.5), (321, 37), (320, 31)]),
    dict(id="grove-lane", width=SECONDARY, serves=["scholar-grove"], points=[(100, 40), (106, 30), (114, 17)]),
    dict(id="monument-walk", width=SECONDARY, serves=["book-monument"], points=[(72, 34), (79, 29.5), (85, 26)]),
]''')
# Relief flats: keep the monument courtyard and the three features level.
rep('    flats = [("pond", site_dir["pond"], pond_r + 0.05), ("marker", site_dir["marker"], marker_r + 0.05)]',
    '    flats = [("pond", site_dir["pond"], pond_r + 0.05), ("marker", site_dir["marker"], marker_r + 0.05), ("monument", direction(89.3, 22.4), 0.6),\n             ("lookout", site_dir["lookout"], 0.62), ("reading-garden", site_dir["reading-garden"], 0.62), ("scholar-grove", site_dir["scholar-grove"], 0.6)]')
# Building measurement: also keep oriented half-extents for the footprint comparison.
rep('        return dict(cx=cx, cz=cz, footprint=math.hypot((max(xs) - min(xs)) / 2, (max(zs) - min(zs)) / 2), height=max(ys))',
    '        return dict(cx=cx, cz=cz, footprint=math.hypot((max(xs) - min(xs)) / 2, (max(zs) - min(zs)) / 2), height=max(ys), hx=(max(xs) - min(xs)) / 2, hz=(max(zs) - min(zs)) / 2)')
# Plaza paving: transition ring into the lawn, and a compass inlay toward the hall, tower, library and pavilion.
rep('''    pr = [0, 0.1, 0.22, LANDING_CLEAR - 0.02, LANDING_CLEAR + 0.03, 0.46, 0.62, 0.78, plaza_r - 0.06, plaza_r]
    pc = {k: hex_lin(P[k]) for k in ("plaza", "inlay", "landing", "kerb")}
    cap(plaza_f, pr, lambda ring, s: pc["landing"] if ring == 4 else pc["kerb"] if ring == len(pr) - 1 else pc["inlay"] if ring in (6, 7) and s % 3 == 0 else pc["plaza"], PAVING_LIFT + 0.004)''',
'''    pr = [0, 0.1, 0.22, LANDING_CLEAR - 0.02, LANDING_CLEAR + 0.03, 0.46, 0.62, 0.78, plaza_r - 0.06, plaza_r, plaza_r + 0.08, plaza_r + 0.17]
    pc = {k: hex_lin(P[k]) for k in ("plaza", "inlay", "landing", "kerb", "lawn", "cobble")}
    def plaza_colour(ring, s):
        if ring == 4: return pc["landing"]
        if ring == 9: return pc["kerb"]
        if ring == 10: return lerp(pc["cobble"], pc["lawn"], 0.35 if s % 2 else 0.6)   # stepping-stone transition
        if ring == 11: return lerp(pc["cobble"], pc["lawn"], 0.8 if s % 2 else 0.9)
        return pc["inlay"] if ring in (6, 7) and s % 3 == 0 else pc["plaza"]
    cap(plaza_f, pr, plaza_colour, PAVING_LIFT + 0.004)
    # Compass inlay: four flat arrows at r 0.5 pointing to the hall, tower, library and pavilion (visual only).
    def bearing_to(target):
        t = target - plaza_c * target.dot(plaza_c)
        return math.atan2(t.dot(plaza_f.right), t.dot(plaza_f.forward))
    for target in (site_dir["hall"], site_dir["tower"], site_dir["library"], site_dir["pavilion"]):
        a = bearing_to(target)
        def pt(dist, ang):
            d = plaza_f.offset_dir(math.sin(ang) * dist, math.cos(ang) * dist); return d * (max(height_at(d), R + nav_h(d)) + PAVING_LIFT + 0.009)
        paths.quads([([pt(0.5, a - 0.09), pt(0.64, a - 0.015), pt(0.64, a + 0.015), pt(0.5, a + 0.09)], hex_lin(P["cobbleDark"]))])''')
# Courtyards: transition ring into the lawn beyond the dark edging.
rep('''        cap(Frame(t["dir"], R, site_frame(t["key"]).forward), [0, fp * 0.5, fp + 0.02, fp + 0.14, fp + 0.22],
            lambda ring, s: cob["cobbleDark"] if ring == 4 else cob["cobble"] if (ring + s) % 2 else cob["sandstone"], PAVING_LIFT + 0.002, 20)''',
'''        cap(Frame(t["dir"], R, site_frame(t["key"]).forward), [0, fp * 0.5, fp + 0.02, fp + 0.14, fp + 0.22, fp + 0.3, fp + 0.38],
            lambda ring, s: cob["cobbleDark"] if ring == 4 else lerp(cob["cobble"], hex_lin(P["lawn"]), 0.4 if s % 2 else 0.65) if ring == 5
            else lerp(cob["cobble"], hex_lin(P["lawn"]), 0.85 if s % 2 else 0.92) if ring == 6 else cob["cobble"] if (ring + s) % 2 else cob["sandstone"], PAVING_LIFT + 0.002, 20)
    # Monument reading courtyard: cobbles around the pedestal, fading into the lawn; the monument walk arrives from the plaza.
    mon_dir = direction(89.3, 22.4); mon_fp = meas["book-monument"]["footprint"]
    cap(Frame(mon_dir, R, plaza_c - mon_dir), [0, mon_fp + 0.04, mon_fp + 0.16, mon_fp + 0.26, mon_fp + 0.34],
        lambda ring, s: cob["cobbleDark"] if ring == 3 else lerp(cob["cobble"], hex_lin(P["lawn"]), 0.7) if ring == 4 else cob["cobble"] if (ring + s) % 2 else cob["sandstone"], PAVING_LIFT + 0.002, 16)''')
# Plaza furniture and lantern banners (after the lanterns); new feature clusters (after the highland cluster).
rep('''    pav_f = Frame(site_dir["pavilion"], R, site_dir["plaza"] - site_dir["pavilion"])''',
'''        decor.box((0, .2, 0), (.014, .18, .11), P["banner"], world=w)                               # lantern banner
    # Two curved stone benches on the plaza's north arc (between the road exits); the centre stays open.
    for i, a in enumerate((160, 205)):
        d = plaza_f.offset_dir(math.sin(math.radians(a)) * 0.8, math.cos(math.radians(a)) * 0.8)
        w = Frame(d, R + PAVING_LIFT, plaza_c - d).world()
        for k in (-1, 0, 1):
            decor.box((k * .11, .05, abs(k) * .012), (.12, .035, .07), P["sandstone"], rot=(0, -k * .22, 0), world=w)
            decor.box((k * .11, .018, abs(k) * .012), (.08, .036, .05), P["sandstoneDark"], rot=(0, -k * .22, 0), world=w)
        obstacles.append(dict(id=f"plaza-bench-{i + 1}", kind="decor", dir=d, radius=0.18, height=0.07))
    pav_f = Frame(site_dir["pavilion"], R, site_dir["plaza"] - site_dir["pavilion"])''')
rep('''    cluster("ruin", site_frame("ruin"), [(0, 0, ruin_arch, ()), (.5, .2, stone, ((.22, .16, .2), P["stoneWall"]))])''',
'''    cluster("ruin", site_frame("ruin"), [(0, 0, ruin_arch, ()), (.5, .2, stone, ((.22, .16, .2), P["stoneWall"]))])
    # Far-side lookout: a stone observation terrace with parapet, telescope and a small knowledge obelisk (environment only).
    def lookout(b, w):
        b.cylinder((0, .03, 0), (.84, .06, .84), P["sandstone"], segments=12, world=w)
        b.cylinder((0, -.06, 0), (.9, .14, .9), P["sandstoneDark"], segments=12, world=w)
        for i in range(10):
            a = i / 10 * 2 * math.pi
            if 2 <= i <= 3: continue   # opening toward the lane (north)
            b.box((math.sin(a) * .39, .11, math.cos(a) * .39), (.12, .1, .05), P["stoneWall"], rot=(0, a, 0), world=w)
        b.cylinder((.12, .19, -.1), (.05, .26, .05), P["wood"], world=w)                                  # telescope post
        b.cylinder((.12, .36, -.1), (.07, .3, .07), P["cobbleDark"], rot=(-.9, 0, 0), world=w)            # telescope tube
        b.box((-.2, .33, .12), (.09, .6, .09), P["sandstone"], world=w)                                   # obelisk
        b.cone((-.2, .68, .12), (.1, .1, .1), P["sandstone"], segments=4, world=w)
    lookout_frame = Frame(site_dir["lookout"], R, -south(site_dir["lookout"]))   # faces north, toward the lane
    cluster("lookout", lookout_frame, [(0, 0, lookout, ())])
    obstacles[-1]["kind"] = "decor"
    accents.rock((-.2, .77, .12), (.07, .1, .07), P["crystal"], world=Frame(site_dir["lookout"], R + ground(site_dir["lookout"]) - 0.02, lookout_frame.forward).world())
    accent_list.append(dict(id="accent-lookout-crystal", district="far", origin=list(lookout_frame.origin), up=list(lookout_frame.up)))
    # West reading garden: a low wall ring, flower beds, a sundial and benches (environment only).
    def sundial(b, w):
        b.cylinder((0, .07, 0), (.22, .14, .22), P["sandstoneDark"], segments=8, world=w); b.cylinder((0, .15, 0), (.26, .02, .26), P["sandstone"], segments=8, world=w)
        b.box((0, .2, 0), (.02, .1, .1), P["cobbleDark"], rot=(.6, 0, 0), world=w)
    garden_f = site_frame("reading-garden")
    cluster("reading-garden", garden_f, [(0, 0, sundial, ()), (-.3, .18, flowers, (P["flowerA"],)), (.3, .18, flowers, (P["flowerB"],)), (0, -.32, flowers, (P["flowerC"],)),
                                         (-.36, -.12, bench, ()), (.36, -.12, bench, ()), (0, .5, round_tree, (.3, P["foliageWarm"]))])
    for i in range(8):
        a = i / 8 * 2 * math.pi
        if i == 2: continue   # gate toward the lane
        d = garden_f.offset_dir(math.sin(a) * .62, math.cos(a) * .62)
        decor.box((0, .05, 0), (.3, .1, .07), P["stoneWall"], rot=(0, a, 0), world=Frame(d, R + ground(d) - 0.01, garden_f.forward).world())
    # South-east scholar grove: three round trees around a stele with a ring finial (environment only).
    def stele(b, w):
        b.box((0, -.02, 0), (.24, .08, .24), P["sandstoneDark"], world=w); b.box((0, .36, 0), (.12, .72, .1), P["sandstone"], world=w)
        b.ring((0, .78, 0), (.14, .14, .14), P["cobbleDark"], rot=(math.pi / 2, 0, 0), world=w)
    cluster("scholar-grove", site_frame("scholar-grove"), [(0, 0, stele, ()), (-.42, -.1, round_tree, (.36, P["foliage"])), (.4, -.14, round_tree, (.32, P["grove"])), (.05, -.5, round_tree, (.3, P["foliageWarm"])), (.3, .32, stone, ((.22, .16, .2), P["rock"]))])''')
# Scenery cluster items may sit on their own flats: the garden wall pieces are placed directly (visual) — add them as one obstacle ring.
rep('''    accent_list = []
    def accent(id_, district, d, radius, height, decor_fn, glow_fn, lift=-0.01, hint=None, on_plaza=False):''',
'''    obstacles.append(dict(id="reading-garden-wall", kind="scenery", dir=site_dir["reading-garden"], radius=0.7, height=0.1))
    def accent(id_, district, d, radius, height, decor_fn, glow_fn, lift=-0.01, hint=None, on_plaza=False):''')
rep('''    decor, accents = Builder(), Builder()
    why = {}''', '''    decor, accents = Builder(), Builder()
    accent_list = []
    why = {}''')
# Oriented-rectangle footprint comparison (documentation only; the circle checks stay the tested reference).
rep('''    measurements = dict(
        radius=R, radiusInH=R / H, extent=extent, plateau=PLATEAU,''',
'''    # Oriented rectangles: distance from another obstacle's centre to the building's bounding rectangle in its tangent
    # frame (small-angle projection), minus that obstacle's radius. Compared with the circle gap for every building pair.
    def rect_gap(bld, other):
        f = bld["frame"]; p = other["dir"]
        x = R * math.asin(max(-1, min(1, p.dot(f.right)))); z = R * math.asin(max(-1, min(1, p.dot(f.forward))))
        m = meas[bld["id"]]; dx = max(0.0, abs(x) - m["hx"] - 0.06); dz = max(0.0, abs(z) - m["hz"] - 0.06)
        return math.hypot(dx, dz) - other["radius"]
    obb = []
    bl = {b_["id"]: b_ for b_ in buildings}
    for i in range(len(obstacles)):
        for j in range(len(obstacles)):
            a, b_ = obstacles[i], obstacles[j]
            if i == j or a["id"] not in bl or b_["kind"] == "scenery" and a["kind"] == "scenery": continue
            circle = arc(a["dir"], b_["dir"]) - a["radius"] - b_["radius"]
            if circle < 1.0:
                obb.append(dict(building=a["id"], other=b_["id"], circleGap=round(circle, 3), rectGap=round(rect_gap(bl[a["id"]], b_), 3), halfExtents=[round(meas[a["id"]]["hx"], 3), round(meas[a["id"]]["hz"], 3)]))
    measurements = dict(
        radius=R, radiusInH=R / H, extent=extent, plateau=PLATEAU, orientedFootprintComparison=obb,''')
rep('''    report["measurements"] = {k: v for k, v in measurements.items() if k not in ("terraces", "pathWidths", "footprints", "heights", "routeLengths")}''',
    '''    report["measurements"] = {k: v for k, v in measurements.items() if k not in ("terraces", "pathWidths", "footprints", "heights", "routeLengths", "orientedFootprintComparison")}
    report["obb"] = measurements["orientedFootprintComparison"]''')
rep('''    print(json.dumps({k: round(v, 3) for k, v in report["footprints"].items()}), json.dumps({k: round(v, 3) for k, v in report["heights"].items()}), json.dumps({k: round(v, 2) for k, v in report["routeLengths"].items()}))''',
    '''    print(json.dumps({k: round(v, 3) for k, v in report["footprints"].items()}), json.dumps({k: round(v, 3) for k, v in report["heights"].items()}), json.dumps({k: round(v, 2) for k, v in report["routeLengths"].items()}))
    print("OBB", json.dumps(report["obb"]))''')
open(os.path.join(here, "build_learning_town_v3.py"), "w", encoding="utf-8").write(out)
print("build_learning_town_v3.py written", len(out.splitlines()), "lines")
