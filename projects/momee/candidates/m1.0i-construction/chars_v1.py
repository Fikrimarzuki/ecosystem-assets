# M1.0i character candidates v1 (placeholder-grade, below master fidelity by owner
# decision). Boy and Mom, front and ¾ (facing right), three expressions each.
# World units with the feet anchor at (0, 0), y up negative; sources at 4 px/u.
import math

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QImage, QPainter, QPainterPath, QPen

import kpaint2 as K
from kpaint2 import C, smooth, ellipse, rrect, lin, rad, rpoly
from charpaint import path_kinds, tapered

PPU = 4.0                     # source texels per world unit (asset-pipeline §9: masters ≥ 2.5)
LIGHT_SHADOW = (0.3, 0.35)    # key light from the upper left (as in the master): heavier line lower right

CHARS = {
    "boy": {"canvas": (160, 224), "anchor": (80, 216), "height": 200, "head": 80},
    "mom": {"canvas": (200, 312), "anchor": (100, 304), "height": 290, "head": 94},
}

# ---- palettes (sampled from the master, see the M1.0i record) ----------------------
SKIN = {"base": "#fdc99a", "top": "#fcc08e", "low": "#fdcfa4", "shade": "#f2a47c", "line": "#a35a3c"}
BOY = {
    "hair": "#3d2c2b", "hair_dk": "#251a19", "hair_top": "#46332f", "hair_hi": "#7d5a49", "hair_line": "#1c1312", "lock": "#4a3631",
    "tee": "#fdd653", "tee_sh": "#f2b43a", "tee_li": "#feeb98", "tee_line": "#b66a1c",
    "shorts": "#2b6190", "shorts_sh": "#1f4a73", "shorts_li": "#4c82b4", "shorts_line": "#173452",
    "sock": "#fbf5ee", "sock_sh": "#ddd3ca", "sock_line": "#a2948a",
    "shoe": "#3d78bd", "shoe_sh": "#2b5a92", "shoe_li": "#7aa7dc", "shoe_line": "#1d3f6c", "sole": "#f8f3ec",
}
MOM = {
    "hair": "#5e3426", "hair_dk": "#43231a", "hair_top": "#6a3b2b", "hair_hi": "#a8704f", "hair_line": "#341a12", "lock": "#6b3c2c",
    "blouse": "#fdb299", "blouse_sh": "#ef8f78", "blouse_li": "#fed3c4", "blouse_line": "#b95a47",
    "trouser": "#f1d5b8", "trouser_sh": "#d6b391", "trouser_li": "#fbebd8", "trouser_line": "#a2826a",
    "shoe": "#f7eee4", "shoe_sh": "#dccfc1", "shoe_line": "#a3958a",
}
EYE = {"iris": "#130b09", "iris_lo": "#5a3626", "deep": "#030101", "white": "#fffaf4", "hi": "#fffdf9", "lash": "#1c1312"}
BLUSH, MOUTH, TONGUE, MOUTH_LINE = "#fda882", "#c8432f", "#f08a78", "#8e3324"
LW_OUT, LW_IN = 1.3, 0.8      # silhouette / interior line weights (world units)


# ---- painting -----------------------------------------------------------------------
def find(d, path):
    return K.find(d, path)


def _render(d, fn, anchor):
    w, h = d.width(), d.height()
    img = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
    img.fill(0)
    qp = QPainter(img)
    qp.setRenderHint(QPainter.Antialiasing, True)
    qp.scale(PPU, PPU)
    qp.translate(*anchor)
    fn(K.Pen(qp))
    qp.end()
    img = img.convertToFormat(QImage.Format_ARGB32)
    ptr = img.constBits()
    ptr.setsize(img.byteCount())
    return bytes(ptr)


def paint(d, node, fn, anchor):
    node.setPixelData(_render(d, fn, anchor), 0, 0, d.width(), d.height())


def child(d, parent, name, kind="paintlayer", inherit=False, visible=True):
    node = d.createNode(name, kind)
    parent.addChildNode(node, None)
    node = next(c for c in parent.childNodes() if c.name() == name)
    node.setInheritAlpha(inherit)
    node.setVisible(visible)
    return node


def part(d, view, name, anchor, base, shade=None, light=None, detail=None, line=None, shade_blur=7, light_blur=6):
    g = child(d, view, name, "grouplayer")
    paint(d, child(d, g, f"{name} — base"), base, anchor)
    for label, fn, blur in (("shade (clipped)", shade, shade_blur), ("light (clipped)", light, light_blur),
                            ("details (clipped)", detail, 0)):
        if fn:
            n = child(d, g, f"{name} — {label}", inherit=True)
            paint(d, n, fn, anchor)
            if blur:
                blur_node(d, n, blur)
    if line:
        paint(d, child(d, g, f"{name} — line"), line, anchor)
    return g


def blur_node(d, node, r):
    f = K.Krita.instance().filter("gaussian blur")
    cfg = f.configuration()
    cfg.setProperty("horizRadius", r)
    cfg.setProperty("vertRadius", r)
    f.setConfiguration(cfg)
    f.apply(node, 0, 0, d.width(), d.height())
    d.waitForDone()


def outline(p, path, color, w=LW_OUT):
    K.wline(p, path, color, w, LIGHT_SHADOW)


# ---- ¾ turn: features rotate on the head sphere ------------------------------------
def warp(x, phi, R=48.0):
    if phi == 0:
        return x
    if abs(x) <= R:
        th = math.asin(max(-1.0, min(1.0, x / R))) + phi
        return R * math.sin(max(-math.pi / 2, min(math.pi / 2, th)))
    edge = warp(math.copysign(R, x), phi, R)
    return edge + (x - math.copysign(R, x)) * 0.55


def wscale(x, phi, R=48.0):
    """Horizontal foreshortening of a feature centred at head-local x."""
    if phi == 0:
        return 1.0
    th = math.asin(max(-1.0, min(1.0, x / R))) + phi
    return max(0.35, math.cos(th) / max(0.35, math.cos(math.asin(max(-1.0, min(1.0, x / R))))))


def W(pts, phi):
    return [(warp(x, phi), y) + tuple(rest) for x, y, *rest in pts]


# ---- shared face features -------------------------------------------------------------
def eye(p, cx, cy, mode, sx=1.0, size=1.0, flick=False):
    w, h = 6.8 * size * sx, 10 * size
    if mode == "open":
        op = smooth([(cx - w, cy - 2 * size), (cx - w * 0.68, cy - h * 0.86), (cx, cy - h), (cx + w * 0.68, cy - h * 0.86),
                     (cx + w, cy - 2 * size), (cx + w * 0.88, cy + 5.5 * size), (cx, cy + 9.4 * size), (cx - w * 0.88, cy + 5.5 * size)], t=0.5)
        p.fill(op, C(EYE["white"]))
        p.p.save()
        p.p.setClipPath(op)
        p.fill(ellipse(cx - 6.2 * size * sx, cy - 9.6 * size, 12.4 * size * sx, 19.4 * size),
               lin(cx, cy - 9 * size, cx, cy + 9 * size, [(0, "#0b0605"), (0.55, EYE["iris"]), (1, EYE["iris_lo"])]))
        p.fill(ellipse(cx - 3.6 * size * sx, cy - 6 * size, 7.2 * size * sx, 10.4 * size), C(EYE["deep"], 210))
        p.fill(smooth([(cx - 4.6 * size * sx, cy + 4.6 * size), (cx, cy + 7.8 * size), (cx + 4.6 * size * sx, cy + 4.6 * size),
                       (cx, cy + 6.4 * size)], t=0.5), C("#9a6248", 170))
        p.p.restore()
        p.fill(ellipse(cx - 5.2 * size * sx, cy - 7.4 * size, 5.8 * size * max(sx, 0.7), 6.2 * size), C(EYE["hi"]))
        p.fill(ellipse(cx + 2.0 * size * sx, cy + 2.4 * size, 2.4 * size, 2.4 * size), C(EYE["hi"], 235))
        lash = [(cx - w * 1.2, cy - 1.2 * size), (cx - w * 0.82, cy - 9.2 * size), (cx + 0.4, cy - 11 * size),
                (cx + w * 0.94, cy - 8.4 * size), (cx + w * 1.26, cy - 3 * size)]
        tapered(p, lash, EYE["lash"], 0.8 * size, 3.0 * size, 1.6 * size)
        if flick:   # Mom: small outer lash flick on each eye's outer corner
            side = 1 if cx > 0 else -1
            ox = cx + side * w * 1.2
            tapered(p, [(ox - side * 1.2, cy - 3.6 * size), (ox + side * 1.6, cy - 6.2 * size)], EYE["lash"], 1.4 * size, 1.0 * size, 0.2)
        p.line([(cx - 3.8 * size * sx, cy + 9.6 * size), (cx + 3 * size * sx, cy + 10 * size)], C(SKIN["line"], 120), 0.5)
    else:   # happy: closed arcs
        tapered(p, [(cx - w * 1.03, cy + 1.5), (cx - w * 0.5, cy - 4.5), (cx + w * 0.5, cy - 4.5), (cx + w * 1.03, cy + 1.5)],
                EYE["lash"], 0.7, 2.6 * size, 0.7)


def mouth(p, mode, cx, cy, s=1.0):
    if mode == "neutral":
        tapered(p, [(cx - 4.8 * s, cy), (cx - 1.5 * s, cy + 2), (cx + 1.5 * s, cy + 2), (cx + 4.8 * s, cy)], SKIN["line"], 0.5, 1.3, 0.5)
    elif mode == "happy":
        m = smooth([(cx - 6.5 * s, cy - 1), (cx, cy + 0.2), (cx + 6.5 * s, cy - 1), (cx + 4.5 * s, cy + 5),
                    (cx, cy + 6.9), (cx - 4.5 * s, cy + 5)], t=0.5)
        p.fill(m, C(MOUTH))
        p.fill(smooth([(cx - 3.4 * s, cy + 4.5), (cx, cy + 3.1), (cx + 3.4 * s, cy + 4.5), (cx, cy + 6.5)], t=0.5), C(TONGUE))
        K.wline(p, m, MOUTH_LINE, 0.8)
    else:   # talking
        m = smooth([(cx - 3.8 * s, cy + 0.2), (cx, cy - 1), (cx + 3.8 * s, cy + 0.2), (cx + 3.4 * s, cy + 5),
                    (cx, cy + 6.4), (cx - 3.4 * s, cy + 5)], t=0.5)
        p.fill(m, C(MOUTH))
        p.fill(ellipse(cx - 2.4 * s, cy + 3.2, 4.8 * s, 2.8), C(TONGUE))
        K.wline(p, m, MOUTH_LINE, 0.8)


def brows(p, xs, y, lift, color, s=1.0, arch=1.0):
    for cx, sx in xs:
        tapered(p, [(cx - 6.5 * sx * s, y + 1.2 * s - lift), (cx, y - 1 * arch * s - lift), (cx + 6.5 * sx * s, y + 0.2 * s - lift)],
                color, 0.5, 1.9 * s, 0.5)


# ---- heads -----------------------------------------------------------------------------
BOY_FACE = [(-37, 30), (-38.5, 46), (-36, 62), (-29, 74), (-16, 81.5), (0, 83.5), (16, 81.5), (29, 74),
            (36, 62), (38.5, 46), (37, 30), (26, 20), (0, 16), (-26, 20)]
BOY_HAIR_BACK = [(-47, 50), (-46, 28), (-37, 11), (-20, 3), (0, 1), (20, 3), (37, 11), (46, 28), (47, 50),
                 (43, 62), (37, 58), (-37, 58), (-43, 62)]
BOY_FRINGE = [
    (-46, 60, "t"), (-44, 46, "s"), (-41.5, 33, "s"),
    (-38, 39, "s"), (-35, 47, "t"), (-31, 36, "s"), (-27, 28, "s"),
    (-24.5, 35, "s"), (-21, 42, "t"), (-17.5, 32, "s"), (-12, 25, "s"),
    (-9.5, 31, "s"), (-5.5, 38.5, "t"), (-3, 30, "s"), (1, 24.5, "s"),
    (4.5, 31, "s"), (9.5, 40, "t"), (11.5, 30, "s"), (15, 25, "s"),
    (19, 31, "s"), (24.5, 37.5, "t"), (26, 30, "s"), (30, 27, "s"),
    (34, 35, "s"), (37.5, 44, "t"), (39.5, 34, "s"), (42, 30, "s"), (45, 43, "s"), (46.5, 58, "t"),
    (51, 46, "t"), (49, 36, "s"), (50.5, 26, "t"), (46, 20, "s"), (44.5, 9, "t"), (38, 7, "s"),
    (33, 0.5, "t"), (26, 2.5, "s"), (19, -3.5, "t"), (14, 1, "s"), (7, -1, "s"), (2.5, -7.5, "t"), (-1.5, -0.5, "s"),
    (-9, -2.5, "s"), (-14, -8, "t"), (-17, 1.5, "s"), (-25, 2, "s"), (-30, -1.5, "t"), (-33, 6, "s"),
    (-42, 9, "t"), (-43, 16, "s"), (-51, 22, "t"), (-48.5, 30, "s"), (-52, 40, "t"), (-48.5, 46, "s")]
BOY_TUFTS = [
    [(-30, 6, "s"), (-20, 4, "s"), (-12, 14, "s"), (-14.5, 26, "t"), (-22, 16, "s")],
    [(2, 4, "s"), (14, 4, "s"), (20, 14, "s"), (17, 26, "t"), (10, 14, "s")],
    [(-40, 18, "s"), (-33, 16, "s"), (-31, 26, "s"), (-36, 38, "t"), (-40, 28, "s")],
    [(30, 12, "s"), (39, 14, "s"), (41, 24, "s"), (39, 36, "t"), (33, 24, "s")]]

BOY_FACE_Q = [(-33, 30), (-36, 46), (-34, 62), (-27, 73), (-12, 81), (8, 84), (22, 80), (33, 71), (40, 58), (42, 44),
              (39, 30), (24, 19), (0, 16), (-24, 20)]
MOM_FACE_Q = [(-31, 34), (-34, 52), (-32, 70), (-24, 84), (-8, 92), (12, 94.5), (27, 89), (37, 76), (41, 60), (41, 44),
              (35, 30), (20, 22), (-14, 24)]
MOM_FACE = [(-35, 34), (-36.5, 52), (-34.5, 70), (-28, 83), (-15, 91.5), (0, 94), (15, 91.5), (28, 83),
            (34.5, 70), (36.5, 52), (35, 34), (24, 24), (0, 20), (-24, 24)]
MOM_HAIR_BACK = [(0, -3), (22, 0), (39, 11), (48, 32), (50, 62), (53, 84), (50.5, 100), (55, 116), (52, 132), (57.5, 146),
                 (54, 158), (58, 166), (50, 172), (44, 164), (36, 173), (26, 161), (-26, 161), (-36, 173), (-44, 164), (-50, 172),
                 (-58, 166), (-54, 158), (-57.5, 146), (-52, 132), (-55, 116), (-50.5, 100), (-53, 84), (-50, 62), (-48, 32),
                 (-39, 11), (-22, 0)]
MOM_FRINGE = [  # side part at x ≈ 10; long sweep to the viewer's left
    (-41, 64, "t"), (-38, 50, "s"), (-31, 38, "s"), (-18, 31, "s"), (-4, 27.5, "s"), (6, 24, "s"), (10, 21.5, "t"),
    (16, 27, "s"), (27, 33, "s"), (34.5, 44, "s"), (38, 60, "t"),
    (45, 44, "s"), (46, 22, "s"), (35, 6, "s"), (17, -1.5, "s"), (0, -2.5, "s"), (-19, 1, "s"), (-36, 10, "s"),
    (-46, 28, "s"), (-47, 50, "s")]
MOM_LOCKS = [  # front locks falling over the shoulders (in front of the blouse)
    [(-40, 50, "s"), (-47, 78, "s"), (-50, 108, "s"), (-48, 136, "s"), (-42, 154, "t"), (-36, 140, "s"), (-38, 112, "s"),
     (-36, 84, "s"), (-35, 62, "s")],
    [(37, 52, "s"), (44, 80, "s"), (47, 108, "s"), (45, 134, "s"), (40, 148, "t"), (35, 134, "s"), (36, 110, "s"),
     (34, 84, "s"), (34, 64, "s")]]


def head_spec(who):
    if who == "boy":
        return dict(face=BOY_FACE, face_q=BOY_FACE_Q, ear_q=(-26, 57), back=BOY_HAIR_BACK, fringe=BOY_FRINGE, tufts=BOY_TUFTS, locks=[], pal=BOY,
                    eye_y=56, eye_x=15.5, eye_size=1.0, brow_y=42.2, fringe_y=44, nose_y=64.5, mouth_y=69.6, blush_y=66.5,
                    blush_x=24, ears=True, flick=False, scale=80 / 83.5, chin=83.5)
    return dict(face=MOM_FACE, face_q=MOM_FACE_Q, ear_q=None, back=MOM_HAIR_BACK, fringe=MOM_FRINGE, tufts=[], locks=MOM_LOCKS, pal=MOM,
                eye_y=62, eye_x=14, eye_size=0.9, brow_y=48.5, fringe_y=34, nose_y=75, mouth_y=81.5, blush_y=73.5,
                blush_x=22, ears=False, flick=True, scale=1.0, chin=94)


def head_tx(p, who, view):
    c = CHARS[who]
    hs = head_spec(who)["scale"]
    dx = 3 if view == "three-quarter" else 0
    p.p.translate(dx, -c["height"])
    p.p.scale(hs, hs)


def build_hair_back(d, viewnode, who, view, anchor):
    hs = head_spec(who)
    pal = hs["pal"]
    phi = 0.45 if view == "three-quarter" else 0.0
    T = lambda fn: (lambda p: (head_tx(p, who, view), fn(p)))
    head = viewnode
    # hair-back (unchanged silhouette in ¾: the skull outline stays round; the nape shows more on the left)
    back_pts = hs["back"] if phi == 0 else hs["back"] + []
    back = smooth(back_pts, t=0.5)
    if phi and who == "boy":
        back = back.united(smooth([(-47, 40), (-48.5, 54), (-42, 64), (-30, 62), (-32, 44)], t=0.5))
    gb = part(d, head, "hair-back", anchor,
              base=T(lambda p: p.fill(back, lin(0, 0, 0, 160 if who == "mom" else 60, [(0, pal["hair"]), (1, pal["hair_dk"])]))),
              shade=T(lambda p: p.fill(rrect(10, 20, 70, 170, 0), C(pal["hair_dk"], 170))),
              light=T(lambda p: tapered(p, [(-40, 40), (-46, 80), (-48, 120)], C(pal["hair_hi"], 150), 0.5, 3.5, 0.5)) if who == "mom" else None,
              line=T(lambda p: outline(p, back, pal["hair_line"], 1.2)), shade_blur=30)



def build_head(d, viewnode, who, view, anchor):
    hs = head_spec(who)
    pal = hs["pal"]
    phi = 0.45 if view == "three-quarter" else 0.0
    T = lambda fn: (lambda p: (head_tx(p, who, view), fn(p)))
    head = child(d, viewnode, "head", "grouplayer")

    if hs["ears"] and not phi:
        ex = -40.5
        ear_pts = lambda s, cx: smooth([(cx + s * -4.5, 50), (cx + s * 1.5, 47), (cx + s * 5, 53), (cx + s * 3.5, 62), (cx - s * 1.5, 66), (cx - s * 5.5, 63)], t=0.5)
        ears = [ear_pts(-1, ex)] + ([] if phi else [ear_pts(1, 40.5)])
        part(d, head, "ears", anchor, base=T(lambda p: [p.fill(e, C(SKIN["base"])) for e in ears]),
             shade=T(lambda p: [p.fill(ellipse(ex - 2, 52, 4, 10), C(SKIN["shade"], 160))] + ([] if phi else [p.fill(ellipse(38.5, 52, 4, 10), C(SKIN["shade"], 160))])),
             line=T(lambda p: [K.wline(p, e, SKIN["line"], 1.0, LIGHT_SHADOW) for e in ears]), shade_blur=3)

    face_path = smooth(hs["face_q"] if phi else hs["face"], t=0.5)
    sk = child(d, head, "head-skin", "grouplayer")
    paint(d, child(d, sk, "head-skin — base"), T(lambda p: p.fill(face_path, lin(0, 20, 0, hs["chin"], [(0, SKIN["top"]), (0.35, SKIN["base"]), (1, SKIN["low"])]))), anchor)
    n = child(d, sk, "head-skin — shade (clipped)", inherit=True)
    paint(d, n, T(lambda p: (p.fill(smooth([(-44, 18), (44, 18), (44, hs["fringe_y"]), (0, hs["fringe_y"] - 1), (-44, hs["fringe_y"])], t=0.5), C(SKIN["shade"], 150)),
                             p.fill(ellipse(30 if phi == 0 else 34, 40, 18, 50), C(SKIN["shade"], 120)))), anchor)
    blur_node(d, n, 9)
    n = child(d, sk, "face-blush (clipped)", inherit=True)
    bx = [(warp(-hs["blush_x"], phi), wscale(-hs["blush_x"], phi)), (warp(hs["blush_x"], phi), wscale(hs["blush_x"], phi))]
    paint(d, n, T(lambda p: [p.fill(ellipse(x - 8 * s, hs["blush_y"] - 4.5, 16 * s, 9), rad(x, hs["blush_y"], 8, [(0, C(BLUSH, 210)), (1, C(BLUSH, 0))])) for x, s in bx]), anchor)
    paint(d, child(d, sk, "head-skin — line"), T(lambda p: outline(p, face_path, SKIN["line"], 1.1)), anchor)
    if phi and hs["ear_q"]:
        ex, ey = hs["ear_q"]
        ear = smooth([(ex - 4, ey - 7), (ex + 2.5, ey - 9), (ex + 5.5, ey - 2), (ex + 4, ey + 6), (ex - 1, ey + 8.5), (ex - 5.5, ey + 3)], t=0.5)
        part(d, head, "ears", anchor, base=T(lambda p: p.fill(ear, C(SKIN["base"]))),
             shade=T(lambda p: p.fill(ellipse(ex - 3, ey - 5, 5, 10), C(SKIN["shade"], 170))),
             line=T(lambda p: (K.wline(p, ear, SKIN["line"], 1.0, LIGHT_SHADOW),
                               p.line([(ex - 1, ey - 4), (ex + 1.8, ey), (ex - 0.5, ey + 4)], C(SKIN["line"], 170), 0.7))), shade_blur=3)

    exs = [(warp(-hs["eye_x"], phi), wscale(-hs["eye_x"], phi)), (warp(hs["eye_x"], phi), wscale(hs["eye_x"], phi))]
    fe = child(d, head, "face-eyes", "grouplayer")
    for att in ("open", "happy"):
        paint(d, child(d, fe, f"face-eyes/{att}"), T(lambda p, a=att: [eye(p, x, hs["eye_y"], a, s, hs["eye_size"], hs["flick"]) for x, s in exs]), anchor)
    fb = child(d, head, "face-brows", "grouplayer")
    for att, lift in (("neutral", 0.0), ("raised", 1.3)):
        paint(d, child(d, fb, f"face-brows/{att}"), T(lambda p, l=lift: brows(p, exs, hs["brow_y"], l, pal["hair_dk"], 1.0, 1.3 if who == "mom" else 1.0)), anchor)
    mx = warp(0, phi)
    ms = wscale(0, phi)
    fm = child(d, head, "face-mouth", "grouplayer")
    for att in ("neutral", "happy", "talking"):
        paint(d, child(d, fm, f"face-mouth/{att}"), T(lambda p, a=att: mouth(p, a, mx, hs["mouth_y"], ms * (0.9 if who == "mom" else 1.0))), anchor)
    nx = mx + (2.5 if phi else 0)
    paint(d, child(d, child(d, head, "face-nose", "grouplayer"), "face-nose — nose"),
          T(lambda p: tapered(p, [(nx - 0.8, hs["nose_y"]), (nx + 0.6, hs["nose_y"] + 1.1), (nx + 1.6, hs["nose_y"] + 0.3)], SKIN["line"], 0.4, 1.1, 0.4)), anchor)

    fr = path_kinds(W(hs["fringe"], phi), t=0.62 if who == "boy" else 0.55)
    tufts = [path_kinds(W(t, phi), t=0.6) for t in hs["tufts"]]
    locks = [path_kinds(W(l, phi), t=0.55) for l in hs["locks"]]
    if phi and locks:
        locks = locks[:1]   # the far lock falls behind the shoulder in ¾
    hair_all = fr
    for l in locks:
        hair_all = hair_all.united(l)

    def hi(p):
        if who == "boy":
            for pts, w in [([(-34, 14), (-26, 8), (-16, 5)], 3.0), ([(-24, 19), (-14, 13), (-4, 11)], 2.2),
                           ([(-8, 8), (2, 5), (12, 7)], 2.0), ([(6, 15), (15, 12), (24, 15)], 1.6)]:
                tapered(p, W(pts, phi), C(pal["hair_hi"], 220), 0.4, w, 0.4)
            for pts in [((-30, 26), (-29, 32), (-31, 38)), ((-14, 22), (-15, 28), (-16, 35)), ((6, 21), (9, 27), (10, 32)),
                        ((22, 22), (26, 29), (29, 36)), ((-39, 30), (-41, 40), (-43, 50)), ((39, 30), (41, 40), (43, 50))]:
                tapered(p, W(list(pts), phi), C(pal["hair_line"], 190), 0.3, 1.0, 0.3)
        else:
            for pts, w in [([(-30, 14), (-18, 7), (-4, 4)], 3.4), ([(14, 6), (26, 10), (36, 20)], 2.4),
                           ([(-40, 60), (-43, 90), (-44, 120)], 2.6), ([(36, 64), (39, 92), (40, 120)], 2.0)]:
                tapered(p, W(pts, phi), C(pal["hair_hi"], 200), 0.4, w, 0.4)
            for pts in [((-22, 30), (-30, 40), (-36, 56)), ((22, 30), (30, 40), (34, 54)), ((-40, 100), (-38, 124), (-40, 146)),
                        ((-8, 6), (-20, 14), (-30, 26))]:
                tapered(p, W(list(pts), phi), C(pal["hair_line"], 170), 0.3, 1.0, 0.3)
    part(d, head, "hair-front", anchor,
         base=T(lambda p: (p.fill(hair_all, lin(-20, -8, 20, 60, [(0, pal["hair_top"]), (1, pal["hair"])])),
                           [p.fill(t, C(pal["lock"])) for t in tufts])),
         shade=T(lambda p: p.fill(smooth([(-50, 22), (-10, 18), (30, 20), (50, 26), (50, 70), (-50, 70)], t=0.5), C(pal["hair_dk"], 170))),
         detail=T(hi),
         line=T(lambda p: (outline(p, hair_all, pal["hair_line"], 1.2), [p.stroke(t, C(pal["hair_line"], 150), 0.6) for t in tufts])),
         shade_blur=12)
    return head


# ---- bodies -------------------------------------------------------------------------
def boy_body(d, vn, view, anchor):
    q = view == "three-quarter"
    P = BOY
    # far-side x is compressed and the body leans slightly to the right in ¾
    def X(x):
        if not q:
            return x
        return x * (0.82 if x > 0 else 0.95) + 3

    def pts(lst):
        return [(X(x), y) for x, y in lst]
    arm_r = pts([(26.5, -97), (28.5, -84), (29.5, -70), (40, -69.5), (40.5, -85), (37.5, -99)])
    arm_l = pts([(-37.5, -99), (-40.5, -85), (-40, -69.5), (-29.5, -70), (-28.5, -84), (-26.5, -97)])
    hand = lambda cx, cy, toward: smooth([(cx - 4.6, cy - 4), (cx, cy - 5.6), (cx + 4.6, cy - 4), (cx + 5, cy + 1.5), (cx + 1.8, cy + 5.4),
                                          (cx - 2.6, cy + 5), (cx - 5, cy + 0.8)], t=0.5).united(ellipse(cx + toward * 3.6 - 1.8, cy - 4.4, 3.6, 5))
    hr, hl = hand(X(35), -64, -1), hand(X(-35), -64, 1)
    legs = {"right": pts([(7, -47), (20, -47), (19, -22), (7, -22)]), "left": pts([(-20, -47), (-6, -47), (-7, -22), (-19, -22)])}
    sock = lambda x0: rpoly(pts([(x0, -24), (x0 + 14, -24), (x0 + 14, -13), (x0, -13)]), 3)
    if q:
        shoe_paths = {"right": (smooth([(4, -8), (6, -15), (14, -18), (22, -16), (29, -11), (31, -5), (28, -2), (5, -2)], t=0.5), (20, -9, 11, 7), 3.0),
                      "left": (smooth([(-23, -6), (-22, -14), (-14, -17), (-5, -16), (3, -10), (5, -4), (2, -0.5), (-22, -0.5)], t=0.5), (-6, -8, 11, 7), 0.0)}
    else:
        shoe_paths = {"right": (smooth([(1.5, -6), (3, -14), (11, -17), (21, -16), (27, -10), (27.5, -3), (2, -3)], t=0.5), (6, -9, 19, 6.5), 0.0),
                      "left": (smooth([(-1.5, -6), (-3, -14), (-11, -17), (-21, -16), (-27, -10), (-27.5, -3), (-2, -3)], t=0.5), (-25, -9, 19, 6.5), 0.0)}
    far, near = ("right", "left")
    shadow = child(d, vn, "shadow (contact; not exported)", visible=False)
    paint(d, shadow, lambda p: p.fill(ellipse(-38, -5, 76, 10), C("#59463d", 90)), anchor)

    def arm(name, ap, hp, sh_x):
        part(d, vn, name, anchor, base=lambda p: (p.fill(smooth(ap, t=0.4), C(SKIN["base"])), p.fill(hp, C(SKIN["base"]))),
             shade=lambda p: p.fill(rrect(sh_x, -100, 6, 45, 0), C(SKIN["shade"], 170)),
             line=lambda p: (outline(p, smooth(ap, t=0.4), SKIN["line"]), outline(p, hp, SKIN["line"], 1.0),
                             p.line([(hp.boundingRect().center().x() - 1, -63), (hp.boundingRect().center().x() + 1, -59)], C(SKIN["line"], 140), 0.5)),
             shade_blur=4)
    arm("arm-back" if q else "arm-right", arm_r, hr, X(36))
    arm("arm-front" if q else "arm-left", arm_l, hl, X(-33))
    for side in (far, near):
        nm = ("leg-back" if side == far else "leg-front") if q else f"leg-{side}"
        lp = rpoly(legs[side], 5)
        dy = -3 if (q and side == far) else 0
        x0 = X(7) if side == "right" else X(-20)
        part(d, vn, nm, anchor, base=lambda p, lp=lp, x0=x0: (p.p.translate(0, dy), p.fill(lp, C(SKIN["base"])), p.fill(sock(x0 if not q else (7 if side == 'right' else -20)), C(P["sock"]))),
             shade=lambda p, lp=lp: (p.p.translate(0, dy), p.fill(rrect(-40, -47, 80, 8, 0), C(SKIN["shade"], 150))),
             line=lambda p, lp=lp, x0=x0: (p.p.translate(0, dy), outline(p, lp, SKIN["line"], 1.0),
                                          outline(p, sock(x0 if not q else (7 if side == 'right' else -20)), P["sock_line"], 0.9)),
             shade_blur=4)
        sp, cap, ddy = shoe_paths[side]
        part(d, vn, ("shoe-back" if side == far else "shoe-front") if q else f"shoe-{side}", anchor,
             base=lambda p, sp=sp, cap=cap, ddy=ddy: (p.p.translate(0, -ddy), p.fill(sp, C(P["shoe"])),
                                                     p.fill(rrect(sp.boundingRect().x(), -5, sp.boundingRect().width(), 4.5, 2), C(P["sole"])),
                                                     p.fill(ellipse(*cap), C(P["sole"]))),
             shade=lambda p, sp=sp, ddy=ddy: (p.p.translate(0, -ddy), p.fill(rrect(sp.boundingRect().x(), -9, sp.boundingRect().width(), 4, 0), C(P["shoe_sh"], 200))),
             light=lambda p, sp=sp, ddy=ddy: (p.p.translate(0, -ddy), p.fill(ellipse(sp.boundingRect().x() + 4, -17, 10, 5), C(P["shoe_li"], 220))),
             detail=lambda p, sp=sp, ddy=ddy: (p.p.translate(0, -ddy), [p.line([(sp.boundingRect().center().x() - 3.5, -15.5 + i * 2.6), (sp.boundingRect().center().x() + 3.5, -14.5 + i * 2.6)], C(P["sole"]), 1.1) for i in range(3)]),
             line=lambda p, sp=sp, ddy=ddy: (p.p.translate(0, -ddy), outline(p, sp, P["shoe_line"], 1.1), p.line([(sp.boundingRect().x() + 1, -5), (sp.boundingRect().right() - 1, -5)], C(P["shoe_line"], 160), 0.6)),
             shade_blur=3, light_blur=3)
    neck = rpoly(pts([(-7, -126), (7, -126), (7, -110), (-7, -110)]), 3)
    part(d, vn, "body-skin", anchor, base=lambda p: p.fill(neck, C(SKIN["base"])),
         shade=lambda p: p.fill(rrect(X(-10), -126, 22, 8, 0), C(SKIN["shade"], 200)), line=lambda p: p.stroke(neck, C(SKIN["line"], 160), 0.8), shade_blur=3)
    shorts = smooth(pts([(-25, -73), (25, -73), (27, -62), (28.5, -45), (3, -44), (0, -54), (-3, -44), (-28.5, -45), (-27, -62)]), t=0.3)
    part(d, vn, "outfit-bottom", anchor, base=lambda p: p.fill(shorts, C(P["shorts"])),
         shade=lambda p: (p.fill(rrect(-40, -73, 80, 6, 0), C(P["shorts_sh"], 220)), p.fill(rrect(X(-4), -56, 8, 14, 0), C(P["shorts_sh"], 200)),
                          p.fill(rrect(X(16), -70, 14, 28, 0), C(P["shorts_sh"], 150))),
         light=lambda p: p.fill(ellipse(X(-24), -64, 12, 16), C(P["shorts_li"], 200)),
         detail=lambda p: (p.line(pts([(-24, -67), (-18, -63), (-17, -58)]), C(P["shorts_line"], 170), 0.6),
                           p.line(pts([(24, -67), (18, -63), (17, -58)]), C(P["shorts_line"], 170), 0.6),
                           p.line(pts([(-27, -55), (-27.5, -47)]), C(P["shorts_line"], 120), 0.5)),
         line=lambda p: outline(p, shorts, P["shorts_line"]), shade_blur=18, light_blur=12)
    tee = smooth(pts([(-9, -116), (-22, -114.5), (-31, -110), (-38, -101), (-37.5, -94.5), (-27, -93), (-26, -84), (-27.5, -70),
                      (0, -68.5), (27.5, -70), (26, -84), (27, -93), (37.5, -94.5), (38, -101), (31, -110), (22, -114.5), (9, -116), (0, -111)]), t=0.4)
    collar = smooth(pts([(-9.5, -116.5), (0, -112.5), (9.5, -116.5), (8.5, -114), (0, -109.5), (-8.5, -114)]), t=0.5)
    part(d, vn, "outfit-top", anchor, base=lambda p: (p.fill(tee, C(P["tee"])), p.fill(collar, C(P["tee_sh"]))),
         shade=lambda p: (p.fill(rrect(X(14), -112, 30, 44, 0), C(P["tee_sh"], 190)), p.fill(rrect(-44, -97, 88, 5, 0), C(P["tee_sh"], 200)),
                          p.fill(rrect(-30, -75, 60, 6, 0), C(P["tee_sh"], 170))),
         light=lambda p: p.fill(ellipse(X(-24), -112, 24, 20), C(P["tee_li"], 150)),
         detail=lambda p: (p.line(pts([(-27, -94), (-26, -98)]), C(P["tee_line"], 140), 0.6), p.line(pts([(27, -94), (26, -98)]), C(P["tee_line"], 140), 0.6),
                           p.line(pts([(-22, -71.5), (22, -71.5)]), C(P["tee_line"], 110), 0.5)),
         line=lambda p: (outline(p, tee, P["tee_line"]), p.stroke(collar, C(P["tee_line"], 200), 0.7)), shade_blur=22, light_blur=14)


def mom_body(d, vn, view, anchor):
    q = view == "three-quarter"
    P = MOM

    def X(x):
        if not q:
            return x
        return x * (0.82 if x > 0 else 0.95) + 3

    def pts(lst):
        return [(X(x), y) for x, y in lst]
    shadow = child(d, vn, "shadow (contact; not exported)", visible=False)
    paint(d, shadow, lambda p: p.fill(ellipse(-44, -5, 88, 11), C("#59463d", 90)), anchor)
    forearm = lambda s: pts([(s * 31, -150), (s * 41, -151), (s * 43, -122), (s * 36, -119)])
    hand = lambda cx: smooth([(cx - 5, -121), (cx, -123), (cx + 5, -121), (cx + 5.5, -115), (cx + 2, -109.5), (cx - 3, -110), (cx - 5.5, -115)], t=0.5)
    for s, nm in ((1, "arm-back" if q else "arm-right"), (-1, "arm-front" if q else "arm-left")):
        fa = smooth(forearm(s), t=0.4)
        hp = hand(X(s * 40))
        part(d, vn, nm, anchor, base=lambda p, fa=fa, hp=hp: (p.fill(fa, C(SKIN["base"])), p.fill(hp, C(SKIN["base"]))),
             shade=lambda p, s=s: p.fill(rrect(X(s * 38) - 3, -152, 6, 40, 0), C(SKIN["shade"], 170)),
             line=lambda p, fa=fa, hp=hp: (outline(p, fa, SKIN["line"]), outline(p, hp, SKIN["line"], 1.0)), shade_blur=4)
    shoes = {"right": (ellipse(X(4), -10 - (3 if q else 0), 26 if q else 24, 10)), "left": ellipse(X(-28), -10, 26 if q else 24, 10)}
    for side in ("right", "left"):
        nm = (("shoe-back" if side == "right" else "shoe-front") if q else f"shoe-{side}")
        sp = shoes[side]
        part(d, vn, nm, anchor, base=lambda p, sp=sp: p.fill(sp, C(P["shoe"])),
             shade=lambda p, sp=sp: p.fill(rrect(sp.boundingRect().x(), sp.boundingRect().bottom() - 3, sp.boundingRect().width(), 3, 0), C(P["shoe_sh"])),
             line=lambda p, sp=sp: outline(p, sp, P["shoe_line"], 1.0), shade_blur=2)
    neck = rpoly(pts([(-6.5, -200), (6.5, -200), (6.5, -184), (-6.5, -184)]), 3)
    part(d, vn, "body-skin", anchor, base=lambda p: (p.fill(neck, C(SKIN["base"])), p.fill(smooth(pts([(-9, -189), (0, -178), (9, -189)]), t=0.5), C(SKIN["base"]))),
         shade=lambda p: p.fill(rrect(X(-9), -200, 20, 8, 0), C(SKIN["shade"], 200)), line=lambda p: p.stroke(neck, C(SKIN["line"], 160), 0.8), shade_blur=3)
    trousers = smooth(pts([(-24, -127), (24, -127), (28.5, -110), (31, -60), (33, -10), (3, -10), (1.5, -78), (0, -82), (-1.5, -78),
                           (-3, -10), (-33, -10), (-31, -60), (-28.5, -110)]), t=0.25)
    part(d, vn, "outfit-bottom", anchor, base=lambda p: p.fill(trousers, C(P["trouser"])),
         shade=lambda p: (p.fill(rrect(-40, -127, 80, 7, 0), C(P["trouser_sh"], 200)), p.fill(rrect(X(-5), -82, 10, 74, 0), C(P["trouser_sh"], 170)),
                          p.fill(rrect(X(20), -110, 16, 100, 0), C(P["trouser_sh"], 150))),
         light=lambda p: p.fill(rrect(X(-26), -110, 10, 96, 0), C(P["trouser_li"], 200)),
         detail=lambda p: (p.line(pts([(-15, -112), (-16, -60), (-17, -12)]), C(P["trouser_line"], 120), 0.6),
                           p.line(pts([(15, -112), (16, -60), (17, -12)]), C(P["trouser_line"], 120), 0.6),
                           p.line(pts([(-24, -121.5), (24, -121.5)]), C(P["trouser_line"], 150), 0.6)),
         line=lambda p: outline(p, trousers, P["trouser_line"], 1.4), shade_blur=20, light_blur=12)
    blouse = smooth(pts([(-9, -189), (-25, -187), (-33, -181), (-39, -168), (-42, -152), (-30, -149), (-28, -140), (-29, -122),
                         (0, -118.5), (29, -122), (28, -140), (30, -149), (42, -152), (39, -168), (33, -181), (25, -187), (9, -189), (0, -178)]), t=0.35)
    cuffs = [rpoly(pts([(-43, -157), (-29, -155), (-29.5, -148), (-43.5, -149.5)]), 2), rpoly(pts([(43, -157), (29, -155), (29.5, -148), (43.5, -149.5)]), 2)]
    part(d, vn, "outfit-top", anchor, base=lambda p: (p.fill(blouse, C(P["blouse"])), [p.fill(c, C(P["blouse_li"])) for c in cuffs]),
         shade=lambda p: (p.fill(rrect(X(16), -186, 30, 66, 0), C(P["blouse_sh"], 170)), p.fill(rrect(-44, -152, 88, 4, 0), C(P["blouse_sh"], 200)),
                          p.fill(rrect(-30, -127, 60, 6, 0), C(P["blouse_sh"], 160))),
         light=lambda p: p.fill(ellipse(X(-28), -188, 26, 28), C(P["blouse_li"], 150)),
         detail=lambda p: (p.line(pts([(0, -178), (0, -121)]), C(P["blouse_line"], 150), 0.6),
                           [p.fill(ellipse(X(1.6) - 1.2, y - 1.2, 2.4, 2.4), C(P["blouse_li"])) for y in (-170, -156, -142, -128)],
                           [p.stroke(c, C(P["blouse_line"], 170), 0.6) for c in cuffs]),
         line=lambda p: outline(p, blouse, P["blouse_line"], 1.4), shade_blur=22, light_blur=14)


# ---- build and expressions ---------------------------------------------------------
EXPRESSIONS = {"neutral": ("open", "neutral", "neutral"), "happy": ("happy", "raised", "happy"),
               "talking": ("open", "raised", "talking")}


def build(d, who):
    for n in list(d.rootNode().childNodes()):
        n.remove()
    anchor = CHARS[who]["anchor"]
    guides = child(d, d.rootNode(), "Guides — ground line, anchor, height (hidden)", "grouplayer", visible=False)
    c = CHARS[who]
    paint(d, child(d, guides, "ground line and anchor"), lambda p: (
        p.line([(-90, 0), (90, 0)], C("#d48658"), 0.4), p.line([(0, -6), (0, 6)], C("#d48658"), 0.4),
        p.line([(-70, -c["height"]), (70, -c["height"])], C("#6986a2"), 0.3),
        p.line([(-70, -c["height"] + c["head"]), (70, -c["height"] + c["head"])], C("#9eb49f"), 0.3)), anchor)
    for view in ("three-quarter", "front"):
        vn = child(d, d.rootNode(), f"view: {view}", "grouplayer", visible=(view == "front"))
        build_hair_back(d, vn, who, view, anchor)
        (boy_body if who == "boy" else mom_body)(d, vn, view, anchor)
        build_head(d, vn, who, view, anchor)
    show(d, "front", "neutral")


def show(d, view, expression):
    eyes, brows_, mouth_ = EXPRESSIONS[expression]
    for vname in ("front", "three-quarter"):
        vn = K.find(d, f"view: {vname}")
        vn.setVisible(vname == view)
        head = next(c for c in vn.childNodes() if c.name() == "head")
        for grp, keep in (("face-eyes", eyes), ("face-brows", brows_), ("face-mouth", mouth_)):
            g = next(c for c in head.childNodes() if c.name() == grp)
            for n in g.childNodes():
                n.setVisible(n.name() == f"{grp}/{keep}")
    d.refreshProjection()
    d.waitForDone()
