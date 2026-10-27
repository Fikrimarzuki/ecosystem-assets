"""Second stage of the v3 derivation: a feature's own approach lane is exempt from the decoration fit rule (as a building's
is), cluster kinds are explicit, the reading-garden wall is a per-piece cluster with its gate facing the lane, and the
path-clearance exemption matches served cluster ids by prefix. Run after make_v3_script.py."""
import os
here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, "build_learning_town_v3.py")
out = open(p, encoding="utf-8").read()

def rep(a, b):
    global out
    assert a in out, a[:90]
    out = out.replace(a, b, 1)

rep('''    def fits(d, radius, kind="scenery", item_id=None):
        reasons = []
        for rt in routes:
            m = min(arc(d, p) - rt["width"] / 2 * 1.6 - radius for p in rt["dirs"])''',
'''    def fits(d, radius, kind="scenery", item_id=None, skip_route=None):
        reasons = []
        for rt in routes:
            if rt["id"] == skip_route: continue   # a feature's own approach lane
            m = min(arc(d, p) - rt["width"] / 2 * 1.6 - radius for p in rt["dirs"])''')
rep('''    def cluster(id_, frame, items):
        hint = frame.forward
        for idx, (x, z, fn, args) in enumerate(items):
            item_id = f"{id_}-{idx + 1}" if len(items) > 1 else id_
            d = frame.offset_dir(x, z); rr, hh = item_radius(fn, *args)
            if not fits(d, rr, "scenery", item_id): report["skipped"].append(item_id); continue
            f = Frame(d, R + ground(d) - 0.02, hint); fn(decor, f.world(), *args)
            obstacles.append(dict(id=item_id, kind="scenery", dir=d, radius=rr, height=hh))''',
'''    def cluster(id_, frame, items, kind="scenery", served_by=None):
        hint = frame.forward
        for idx, (x, z, fn, args) in enumerate(items):
            item_id = f"{id_}-{idx + 1}" if len(items) > 1 else id_
            d = frame.offset_dir(x, z); rr, hh = item_radius(fn, *args)
            if not fits(d, rr, kind, item_id, served_by): report["skipped"].append(item_id); continue
            f = Frame(d, R + ground(d) - 0.02, hint); fn(decor, f.world(), *args)
            obstacles.append(dict(id=item_id, kind=kind, dir=d, radius=rr, height=hh))''')
rep('''    cluster("lookout", lookout_frame, [(0, 0, lookout, ())])
    obstacles[-1]["kind"] = "decor"''',
'''    cluster("lookout", lookout_frame, [(0, 0, lookout, ())], kind="decor", served_by="lookout-lane")''')
rep('''                                         (-.36, -.12, bench, ()), (.36, -.12, bench, ()), (0, .5, round_tree, (.3, P["foliageWarm"]))])
    for i in range(8):
        a = i / 8 * 2 * math.pi
        if i == 2: continue   # gate toward the lane
        d = garden_f.offset_dir(math.sin(a) * .62, math.cos(a) * .62)
        decor.box((0, .05, 0), (.3, .1, .07), P["stoneWall"], rot=(0, a, 0), world=Frame(d, R + ground(d) - 0.01, garden_f.forward).world())''',
'''                                         (-.36, -.12, bench, ()), (.36, -.12, bench, ()), (0, .5, round_tree, (.3, P["foliageWarm"]))], served_by="garden-lane")
    def wall_seg(b, w, a): b.box((0, .05, 0), (.3, .1, .07), P["stoneWall"], rot=(0, a, 0), world=w)
    # Low wall ring with its gate on the north side (−forward), where the garden lane arrives.
    cluster("reading-garden-wall", garden_f, [(math.sin(i / 8 * 2 * math.pi) * .62, math.cos(i / 8 * 2 * math.pi) * .62, wall_seg, (i / 8 * 2 * math.pi,)) for i in range(8) if i != 4], served_by="garden-lane")''')
rep('''(.05, -.5, round_tree, (.3, P["foliageWarm"])), (.3, .32, stone, ((.22, .16, .2), P["rock"]))])''',
    '''(.05, -.5, round_tree, (.3, P["foliageWarm"])), (.3, .32, stone, ((.22, .16, .2), P["rock"]))], served_by="grove-lane")''')
rep('''    obstacles.append(dict(id="reading-garden-wall", kind="scenery", dir=site_dir["reading-garden"], radius=0.7, height=0.1))
    def accent(''', '''    def accent(''')
rep('''            if o["id"] in rt["serves"] and arc(d, o["dir"]) < o["radius"] + 0.8: continue''',
    '''            if any(o["id"] == sv or o["id"].startswith(sv + "-") for sv in rt["serves"]) and arc(d, o["dir"]) < o["radius"] + 0.8: continue''')
open(p, "w", encoding="utf-8").write(out)
print("v3 extra stage applied")

# --- composition fixes after the first measured build
out = open(p, encoding="utf-8").read()
rep('''    for i, a in enumerate((160, 205)):
        d = plaza_f.offset_dir(math.sin(math.radians(a)) * 0.8, math.cos(math.radians(a)) * 0.8)
        w = Frame(d, R + PAVING_LIFT, plaza_c - d).world()
        for k in (-1, 0, 1):
            decor.box((k * .11, .05, abs(k) * .012), (.12, .035, .07), P["sandstone"], rot=(0, -k * .22, 0), world=w)
            decor.box((k * .11, .018, abs(k) * .012), (.08, .036, .05), P["sandstoneDark"], rot=(0, -k * .22, 0), world=w)
        obstacles.append(dict(id=f"plaza-bench-{i + 1}", kind="decor", dir=d, radius=0.18, height=0.07))''',
'''    for i, a in enumerate((183,)):   # one curved stone bench at the north apex, between the two road exits
        d = plaza_f.offset_dir(math.sin(math.radians(a)) * 0.8, math.cos(math.radians(a)) * 0.8)
        w = Frame(d, R + PAVING_LIFT, plaza_c - d).world()
        for k in (-2, -1, 0, 1, 2):
            decor.box((k * .11, .05, abs(k) * abs(k) * .009), (.12, .035, .07), P["sandstone"], rot=(0, -k * .2, 0), world=w)
            decor.box((k * .11, .018, abs(k) * abs(k) * .009), (.08, .036, .05), P["sandstoneDark"], rot=(0, -k * .2, 0), world=w)
        obstacles.append(dict(id=f"plaza-bench-{i + 1}", kind="decor", dir=d, radius=0.3, height=0.07))''')
rep('"highland": (176, 20, None)', '"highland": (176, 16, None)')
rep('"lookout": (176, 40, None), "reading-garden": (320, 24, None),', '"lookout": (176, 37, None), "reading-garden": (320, 22, None),')
rep('points=[(176, 53.5), (176, 50.5), (176, 47.5)]', 'points=[(176, 53.5), (176, 49), (176, 44.5)]')
rep('points=[(322, 43.5), (321, 37), (320, 31)]', 'points=[(322, 43.5), (321, 36), (320, 29.5)]')
rep('(-.6, .4, stone, ((.34, .28, .3), P["rock"])), (.2, -.7, stone, ((.3, .22, .26), P["rock"]))])', '(-.6, .4, stone, ((.34, .28, .3), P["rock"])), (.5, -.4, stone, ((.3, .22, .26), P["rock"]))])')
rep('(-.36, -.12, bench, ()), (.36, -.12, bench, ()), (0, .5, round_tree, (.3, P["foliageWarm"]))], served_by="garden-lane")', '(-.36, -.12, bench, ()), (.36, -.12, bench, ()), (-.2, .25, round_tree, (.3, P["foliageWarm"]))], served_by="garden-lane")')
open(p, "w", encoding="utf-8").write(out)
print("v3 composition fixes applied")

# --- second measured build: keep v2's landing clearance (bench at the plaza edge) and relieve the garden
out = open(p, encoding="utf-8").read()
rep('''        d = plaza_f.offset_dir(math.sin(math.radians(a)) * 0.8, math.cos(math.radians(a)) * 0.8)
        w = Frame(d, R + PAVING_LIFT, plaza_c - d).world()
        for k in (-2, -1, 0, 1, 2):
            decor.box((k * .11, .05, abs(k) * abs(k) * .009), (.12, .035, .07), P["sandstone"], rot=(0, -k * .2, 0), world=w)
            decor.box((k * .11, .018, abs(k) * abs(k) * .009), (.08, .036, .05), P["sandstoneDark"], rot=(0, -k * .2, 0), world=w)
        obstacles.append(dict(id=f"plaza-bench-{i + 1}", kind="decor", dir=d, radius=0.3, height=0.07))''',
'''        d = plaza_f.offset_dir(math.sin(math.radians(a)) * 0.9, math.cos(math.radians(a)) * 0.9)   # on the plaza's edge ring
        w = Frame(d, R + PAVING_LIFT, plaza_c - d).world()
        for k in (-1.5, -.5, .5, 1.5):
            decor.box((k * .11, .05, k * k * .012), (.12, .035, .07), P["sandstone"], rot=(0, -k * .2, 0), world=w)
            decor.box((k * .11, .018, k * k * .012), (.08, .036, .05), P["sandstoneDark"], rot=(0, -k * .2, 0), world=w)
        obstacles.append(dict(id=f"plaza-bench-{i + 1}", kind="decor", dir=d, radius=0.27, height=0.07))''')
rep('''(-.36, -.12, bench, ()), (.36, -.12, bench, ()), (-.2, .25, round_tree, (.3, P["foliageWarm"]))], served_by="garden-lane")''',
    '''(-.36, -.12, bench, ()), (.36, -.12, bench, ())], served_by="garden-lane")''')
open(p, "w", encoding="utf-8").write(out)
print("v3 landing/garden fixes applied")

# --- third measured build: the bench rotates 11° away from the hall's garden bed (obstacle gap ≥ 6 r)
out = open(p, encoding="utf-8").read()
rep('''    for i, a in enumerate((183,)):   # one curved stone bench at the north apex, between the two road exits''',
    '''    for i, a in enumerate((172,)):   # one curved stone bench on the north arc, between the two road exits''')
open(p, "w", encoding="utf-8").write(out)
print("v3 bench angle applied")

# --- fourth measured build: a shorter bench (three segments) keeps 6 r from the hall's garden bed
out = open(p, encoding="utf-8").read()
rep('''        for k in (-1.5, -.5, .5, 1.5):
            decor.box((k * .11, .05, k * k * .012), (.12, .035, .07), P["sandstone"], rot=(0, -k * .2, 0), world=w)
            decor.box((k * .11, .018, k * k * .012), (.08, .036, .05), P["sandstoneDark"], rot=(0, -k * .2, 0), world=w)
        obstacles.append(dict(id=f"plaza-bench-{i + 1}", kind="decor", dir=d, radius=0.27, height=0.07))''',
'''        for k in (-1, 0, 1):
            decor.box((k * .11, .05, k * k * .012), (.12, .035, .07), P["sandstone"], rot=(0, -k * .2, 0), world=w)
            decor.box((k * .11, .018, k * k * .012), (.08, .036, .05), P["sandstoneDark"], rot=(0, -k * .2, 0), world=w)
        obstacles.append(dict(id=f"plaza-bench-{i + 1}", kind="decor", dir=d, radius=0.2, height=0.07))''')
open(p, "w", encoding="utf-8").write(out)
print("v3 bench length applied")
