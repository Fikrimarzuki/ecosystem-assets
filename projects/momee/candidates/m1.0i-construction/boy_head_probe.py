# M1.0i fidelity probe: the Boy's front head, drawn as layered vector paint.
# Head coordinates: x -50..50, y 0 (hair top) .. 84 (chin); canvas offset (60, 8).
import kpaint2 as K
from kpaint2 import C, smooth, ellipse, rrect, lin, rad
from charpaint import path_kinds, mirror, tapered

OX, OY = 60, 8
SKIN, SKIN_SH, SKIN_LINE = "#fdc99a", "#f2a47c", "#a35a3c"
HAIR, HAIR_DK, HAIR_HI, HAIR_LINE = "#3d2c2b", "#251a19", "#7d5a49", "#1c1312"
IRIS, IRIS_LO = "#130b09", "#5a3626"
BLUSH, MOUTH, TONGUE = "#fda882", "#c8432f", "#f08a78"


def G(fn):
    def wrapped(p):
        p.p.translate(OX, OY)
        fn(p)
    return wrapped


FACE = smooth([(-37, 30), (-38.5, 46), (-36, 62), (-29, 74), (-16, 81.5), (0, 83.5), (16, 81.5), (29, 74),
               (36, 62), (38.5, 46), (37, 30), (26, 20), (0, 16), (-26, 20)], t=0.5)
HAIR_BACK = smooth([(-47, 50), (-46, 28), (-37, 11), (-20, 3), (0, 1), (20, 3), (37, 11), (46, 28), (47, 50),
                    (43, 62), (37, 58), (-37, 58), (-43, 62)], t=0.5)
FRINGE = path_kinds([
    (-46, 60, "t"), (-44, 46, "s"), (-41.5, 33, "s"),
    (-38, 39, "s"), (-35, 47, "t"), (-31, 36, "s"), (-27, 28, "s"),
    (-24.5, 35, "s"), (-21, 42, "t"), (-17.5, 32, "s"), (-12, 25, "s"),
    (-9.5, 31, "s"), (-5.5, 38.5, "t"), (-3, 30, "s"), (1, 24.5, "s"),
    (4.5, 31, "s"), (9.5, 40, "t"), (11.5, 30, "s"), (15, 25, "s"),
    (19, 31, "s"), (24.5, 37.5, "t"), (26, 30, "s"), (30, 27, "s"),
    (34, 35, "s"), (37.5, 44, "t"), (39.5, 34, "s"), (42, 30, "s"), (45, 43, "s"), (46.5, 58, "t"),
    (51, 46, "t"), (49, 36, "s"), (50.5, 26, "t"), (46, 20, "s"), (44.5, 9, "t"), (38, 7, "s"),
    (33, 0.5, "t"), (26, 2.5, "s"), (19, -3.5, "t"), (14, 1, "s"), (7, -1, "s"), (2.5, -8.5, "t"), (-1.5, -0.5, "s"),
    (-9, -2.5, "s"), (-14, -9, "t"), (-17, 1.5, "s"), (-25, 2, "s"), (-30, -1.5, "t"), (-33, 6, "s"),
    (-42, 9, "t"), (-43, 16, "s"), (-51, 22, "t"), (-48.5, 30, "s"), (-52, 40, "t"), (-48.5, 46, "s")], t=0.62)
INNER_TUFTS = [  # lighter overlapping locks that break up the helmet shape
    path_kinds([(-30, 6, "s"), (-20, 4, "s"), (-12, 14, "s"), (-14.5, 26, "t"), (-22, 16, "s")], t=0.6),
    path_kinds([(2, 4, "s"), (14, 4, "s"), (20, 14, "s"), (17, 26, "t"), (10, 14, "s")], t=0.6),
    path_kinds([(-40, 18, "s"), (-33, 16, "s"), (-31, 26, "s"), (-36, 38, "t"), (-40, 28, "s")], t=0.6),
    path_kinds([(30, 12, "s"), (39, 14, "s"), (41, 24, "s"), (39, 36, "t"), (33, 24, "s")], t=0.6)]


def ears(p, fill=True):
    for s in (-1, 1):
        e = smooth([(s * 36, 50), (s * 42, 47), (s * 45.5, 53), (s * 44, 62), (s * 39, 66), (s * 35, 63)], t=0.5)
        if fill:
            p.fill(e, C(SKIN))
        else:
            K.wline(p, e, SKIN_LINE, 1.0)
            p.line([(s * 40, 52), (s * 42.5, 56), (s * 40, 61)], C(SKIN_LINE, 170), 0.7)


def eye(p, cx, cy, mode="open", s=1):
    if mode == "open":
        opening = smooth([(cx - 6.8, cy - 2), (cx - 4.6, cy - 8.6), (cx, cy - 10), (cx + 4.6, cy - 8.6), (cx + 6.8, cy - 2),
                          (cx + 6, cy + 5.5), (cx, cy + 9.4), (cx - 6, cy + 5.5)], t=0.5)
        p.fill(opening, C("#fffaf4"))
        p.p.save()
        p.p.setClipPath(opening)
        p.fill(ellipse(cx - 6.2, cy - 9.6, 12.4, 19.4), lin(cx, cy - 9, cx, cy + 9, [(0, "#0b0605"), (0.55, IRIS), (1, IRIS_LO)]))
        p.fill(ellipse(cx - 3.6, cy - 6.0, 7.2, 10.4), C("#030101", 210))
        p.fill(smooth([(cx - 4.6, cy + 4.6), (cx, cy + 7.8), (cx + 4.6, cy + 4.6), (cx, cy + 6.4)], t=0.5), C("#9a6248", 170))
        p.p.restore()
        p.fill(ellipse(cx - 5.2, cy - 7.4, 5.8, 6.2), C("#fffdf9"))               # big highlight, upper left (both eyes)
        p.fill(ellipse(cx + 2.0, cy + 2.4, 2.4, 2.4), C("#fffdf9", 235))
        tapered(p, [(cx - 8.2, cy - 1.2), (cx - 5.6, cy - 9.2), (cx + 0.4, cy - 11.0), (cx + 6.4, cy - 8.4), (cx + 8.6, cy - 3.0)],
                HAIR_LINE, 0.8, 3.0, 1.6)                                          # heavy upper lash wedge
        tapered(p, [(cx + s * 6.4 - (0 if s > 0 else 0), cy - 8.0), (cx + s * 9.0, cy - 9.6)], HAIR_LINE, 1.2, 1.0, 0.3) if False else None
        p.line([(cx - 3.8, cy + 9.6), (cx + 3.0, cy + 10.0)], C(SKIN_LINE, 120), 0.5)
    elif mode == "happy":
        tapered(p, [(cx - 7, cy + 1.5), (cx - 3.5, cy - 4.5), (cx + 3.5, cy - 4.5), (cx + 7, cy + 1.5)], HAIR_LINE, 0.7, 2.6, 0.7)


def brows(p, lift=0.0):
    for s in (-1, 1):
        tapered(p, [(s * 7.5, 43.2 - lift), (s * 13, 41.2 - lift), (s * 20, 42.4 - lift)], HAIR_DK, 0.5, 1.9, 0.5)


def mouth(p, mode="neutral"):
    if mode == "neutral":
        tapered(p, [(-4.8, 69.6), (-1.5, 71.6), (1.5, 71.6), (4.8, 69.6)], SKIN_LINE, 0.5, 1.3, 0.5)
    elif mode == "happy":
        m = smooth([(-6.5, 68.5), (0, 69.8), (6.5, 68.5), (4.5, 74.5), (0, 76.4), (-4.5, 74.5)], t=0.5)
        p.fill(m, C(MOUTH))
        p.fill(smooth([(-3.4, 74), (0, 72.6), (3.4, 74), (0, 76)], t=0.5), C(TONGUE))
        K.wline(p, m, "#8e3324", 0.8)
    elif mode == "talk":
        m = smooth([(-3.8, 69.8), (0, 68.6), (3.8, 69.8), (3.4, 74.6), (0, 76), (-3.4, 74.6)], t=0.5)
        p.fill(m, C(MOUTH))
        p.fill(ellipse(-2.4, 72.8, 4.8, 2.8), C(TONGUE))
        K.wline(p, m, "#8e3324", 0.8)


def build(d, expression="neutral"):
    E = K.ensure
    for n in list(d.rootNode().childNodes()):
        n.remove()
    E(d, "Head", "grouplayer")
    # back → front; each part is its own group so clipped shading stays on that part
    for grp, layers in [("hair-back", ["base", "line"]), ("ears", ["base", "line"]),
                        ("head-skin", ["base", "shade (clipped)", "blush (clipped)", "line"]),
                        ("face-eyes", ["eyes"]), ("face-brows", ["brows"]), ("face-nose", ["nose"]), ("face-mouth", ["mouth"]),
                        ("hair-front", ["base", "shade (clipped)", "highlight and strands (clipped)", "line"])]:
        E(d, f"Head/{grp}", "grouplayer")
        for L in layers:
            E(d, f"Head/{grp}/{grp} — {L}", inherit="clipped" in L)
    P = lambda path, fn: K.paint(d, "Head/" + path, G(fn), scale=6)
    P("hair-back/hair-back — base", lambda p: p.fill(HAIR_BACK, lin(0, 0, 0, 60, [(0, HAIR), (1, HAIR_DK)])))
    P("hair-back/hair-back — line", lambda p: p.stroke(HAIR_BACK, C(HAIR_LINE), 1.2))
    P("ears/ears — base", lambda p: ears(p))
    P("ears/ears — line", lambda p: ears(p, fill=False))
    P("head-skin/head-skin — base", lambda p: p.fill(FACE, lin(0, 20, 0, 84, [(0, "#fcc08e"), (0.35, SKIN), (1, "#fdcfa4")])))
    P("head-skin/head-skin — shade (clipped)", lambda p: (
        p.fill(smooth([(-40, 18), (40, 18), (40, 44), (20, 41), (0, 43), (-20, 41), (-40, 44)], t=0.5), C(SKIN_SH, 150)),
        p.fill(ellipse(-46, 42, 14, 44), C(SKIN_SH, 110))))
    K.blur(d, "Head/head-skin/head-skin — shade (clipped)", 9)
    P("head-skin/head-skin — blush (clipped)", lambda p: [p.fill(ellipse(s * 24 - 8, 62, 16, 9), rad(s * 24, 66.5, 8, [(0, C(BLUSH, 210)), (1, C(BLUSH, 0))])) for s in (-1, 1)])
    P("head-skin/head-skin — line", lambda p: K.wline(p, FACE, SKIN_LINE, 1.1))
    eyes_mode = "happy" if expression == "happy" else "open"
    P("face-eyes/face-eyes — eyes", lambda p: [eye(p, s * 15.5, 56, eyes_mode, s) for s in (-1, 1)])
    P("face-brows/face-brows — brows", lambda p: brows(p, 1.2 if expression != "neutral" else 0))
    P("face-nose/face-nose — nose", lambda p: tapered(p, [(-0.8, 64.5), (0.6, 65.6), (1.6, 64.8)], SKIN_LINE, 0.4, 1.1, 0.4))
    P("face-mouth/face-mouth — mouth", lambda p: mouth(p, {"neutral": "neutral", "happy": "happy", "talking": "talk"}[expression]))
    P("hair-front/hair-front — base", lambda p: (p.fill(FRINGE, lin(-20, -8, 20, 50, [(0, "#46332f"), (1, HAIR)])),
                                                 [p.fill(t, C("#4a3631")) for t in INNER_TUFTS]))
    P("hair-front/hair-front — shade (clipped)", lambda p: p.fill(
        smooth([(-50, 22), (-10, 18), (30, 20), (50, 26), (50, 60), (-50, 60)], t=0.5), C(HAIR_DK, 190)))
    K.blur(d, "Head/hair-front/hair-front — shade (clipped)", 12)

    def hi(p):
        for pts, w in [([(-34, 14), (-26, 8), (-16, 5)], 3.0), ([(-24, 19), (-14, 13), (-4, 11)], 2.2),
                       ([(-8, 8), (2, 5), (12, 7)], 2.0), ([(6, 15), (15, 12), (24, 15)], 1.6)]:
            tapered(p, pts, C(HAIR_HI, 220), 0.4, w, 0.4)
        for pts in [((-30, 26), (-29, 32), (-31, 38)), ((-14, 22), (-15, 28), (-16, 35)), ((6, 21), (9, 27), (10, 32)),
                    ((22, 22), (26, 29), (29, 36)), ((-39, 30), (-41, 40), (-43, 50)), ((39, 30), (41, 40), (43, 50))]:
            tapered(p, list(pts), C(HAIR_LINE, 190), 0.3, 1.0, 0.3)
    P("hair-front/hair-front — highlight and strands (clipped)", hi)
    P("hair-front/hair-front — line", lambda p: (K.wline(p, FRINGE, HAIR_LINE, 1.2),
                                                 [p.stroke(t, C(HAIR_LINE, 150), 0.6) for t in INNER_TUFTS]))
    K.refresh(d)


EXPRESSIONS = {"neutral": ("open", "neutral", "neutral"), "happy": ("happy", "raised", "happy"),
               "talking": ("open", "raised", "talking")}


def _paint_child(d, group_path, name, fn):
    """Create a paint layer literally named `name` (may contain '/') inside a group and paint it."""
    from PyQt5.QtGui import QImage, QPainter
    parent = K.find(d, group_path)
    node = d.createNode(name, "paintlayer")
    parent.addChildNode(node, None)
    w, h = d.width(), d.height()
    img = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
    img.fill(0)
    qp = QPainter(img)
    qp.setRenderHint(QPainter.Antialiasing, True)
    qp.scale(6, 6)
    qp.translate(OX, OY)
    fn(K.Pen(qp))
    qp.end()
    img = img.convertToFormat(QImage.Format_ARGB32)
    ptr = img.constBits()
    ptr.setsize(img.byteCount())
    node.setPixelData(bytes(ptr), 0, 0, w, h)


def build_all(d):
    """One layered head: every expression part is its own layer, named slot/attachment
    as in asset-pipeline §4; show_expression() toggles them."""
    build(d, "neutral")
    for grp in ("face-eyes", "face-brows", "face-mouth"):
        for n in list(K.find(d, f"Head/{grp}").childNodes()):
            n.remove()
    for att in ("open", "happy"):
        _paint_child(d, "Head/face-eyes", f"face-eyes/{att}", lambda p, a=att: [eye(p, s * 15.5, 56, a, s) for s in (-1, 1)])
    for att, lift in (("neutral", 0.0), ("raised", 1.2)):
        _paint_child(d, "Head/face-brows", f"face-brows/{att}", lambda p, l=lift: brows(p, l))
    for att, mode in (("neutral", "neutral"), ("happy", "happy"), ("talking", "talk")):
        _paint_child(d, "Head/face-mouth", f"face-mouth/{att}", lambda p, m=mode: mouth(p, m))
    show_expression(d, "neutral")


def show_expression(d, expression):
    eyes, brows_, mouth_ = EXPRESSIONS[expression]
    for grp, keep in (("face-eyes", eyes), ("face-brows", brows_), ("face-mouth", mouth_)):
        for n in K.find(d, f"Head/{grp}").childNodes():
            n.setVisible(n.name() == f"{grp}/{keep}")
    K.refresh(d)
