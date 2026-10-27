"""M1.0g Krita painting helpers (scratchpad tooling, not shipped).

Draws with QPainter into canvas-sized QImages and writes them to named Krita
paint layers. Coordinates are world units; `SCALE` texels per unit.
"""
from krita import Krita
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import (QBrush, QColor, QImage, QLinearGradient, QPainter,
                         QPainterPath, QPen, QRadialGradient)

SCALE = 2.0
OFFSET = 0.0   # horizontal world-unit offset applied while painting (composition shifts)


def C(hexstr, a=255):
    c = QColor(hexstr)
    c.setAlpha(int(a))
    return c


def smooth(pts, closed=True, t=0.5):
    """Catmull-Rom spline through pts as a cubic QPainterPath."""
    n = len(pts)
    path = QPainterPath(QPointF(*pts[0]))
    segs = n if closed else n - 1
    for i in range(segs):
        p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) * t / 3, p1[1] + (p2[1] - p0[1]) * t / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * t / 3, p2[1] - (p3[1] - p1[1]) * t / 3)
        path.cubicTo(QPointF(*c1), QPointF(*c2), QPointF(*p2))
    if closed:
        path.closeSubpath()
    return path


def rrect(x, y, w, h, r):
    p = QPainterPath()
    p.addRoundedRect(QRectF(x, y, w, h), r, r)
    return p


def ellipse(x, y, w, h):
    p = QPainterPath()
    p.addEllipse(QRectF(x, y, w, h))
    return p


def poly(pts):
    p = QPainterPath(QPointF(*pts[0]))
    for q in pts[1:]:
        p.lineTo(QPointF(*q))
    p.closeSubpath()
    return p


def rpoly(pts, r):
    """Polygon with softly rounded corners (radius r, world units)."""
    n = len(pts)
    path = QPainterPath()
    for i in range(n):
        p, v, q = pts[i - 1], pts[i], pts[(i + 1) % n]

        def toward(a, b):
            dx, dy = b[0] - a[0], b[1] - a[1]
            d = max((dx * dx + dy * dy) ** 0.5, 1e-6)
            k = min(r / d, 0.5)
            return (a[0] + dx * k, a[1] + dy * k)
        A, B = toward(v, p), toward(v, q)
        if i == 0:
            path.moveTo(QPointF(*A))
        else:
            path.lineTo(QPointF(*A))
        path.quadTo(QPointF(*v), QPointF(*B))
    path.closeSubpath()
    return path


VP = (680.0, 60.0)   # one-point vanishing point (world units), high storybook horizon
ZVP = 800.0          # depth at which receding lines meet the vanishing point


def P(x, h, z, y0):
    """Project a point x along the front line, h above the floor, z deep, whose
    front floor line is at screen y0. Gentle one-point perspective."""
    c = z / ZVP
    by = y0 - h
    return (x + (VP[0] - x) * c, by + (VP[1] - by) * c)


def lin(x1, y1, x2, y2, stops):
    g = QLinearGradient(x1, y1, x2, y2)
    for s, c in stops:
        g.setColorAt(s, c if isinstance(c, QColor) else C(c))
    return QBrush(g)


def rad(cx, cy, r, stops):
    g = QRadialGradient(cx, cy, r)
    for s, c in stops:
        g.setColorAt(s, c if isinstance(c, QColor) else C(c))
    return QBrush(g)


class Pen:
    def __init__(self, p):
        self.p = p

    def fill(self, path, brush):
        if isinstance(brush, str):
            brush = C(brush)
        self.p.fillPath(path, QBrush(brush) if isinstance(brush, QColor) else brush)

    def stroke(self, path, color, width, cap=Qt.RoundCap):
        col = C(color) if isinstance(color, str) else color
        pen = QPen(col, width, Qt.SolidLine, cap, Qt.RoundJoin)
        self.p.strokePath(path, pen)

    def line(self, pts, color, width, t=0.5):
        self.stroke(smooth(pts, closed=False, t=t), color, width)


def doc_by_name(name):
    for d in Krita.instance().documents():
        if d.name() == name or d.fileName().endswith(name):
            return d
    raise KeyError(name)


def find(doc, path):
    node = doc.rootNode()
    for part in path.split("/"):
        node = next((c for c in node.childNodes() if c.name() == part), None)
        if node is None:
            return None
    return node


def ensure(doc, path, kind="paintlayer", inherit=False, opacity=255, blend="normal",
           visible=True, below=None, passthrough=False):
    """Create path (parent groups must exist) if missing; returns the node."""
    node = find(doc, path)
    if node is None:
        parent_path, _, name = path.rpartition("/")
        parent = find(doc, parent_path) if parent_path else doc.rootNode()
        node = doc.createNode(name, kind)
        above = None
        if below is not None:
            # insert directly above sibling `below`
            above = find(doc, (parent_path + "/" if parent_path else "") + below)
        parent.addChildNode(node, above)
        node = find(doc, path)  # re-fetch as the typed wrapper (GroupLayer etc.)
    node.setInheritAlpha(inherit)
    node.setOpacity(int(opacity))
    node.setBlendingMode(blend)
    node.setVisible(visible)
    if kind == "grouplayer":
        node.setPassThroughMode(passthrough)
    return node


def paint(doc, path, fn, scale=SCALE, clear=True):
    """Render fn(Pen) (world units) into the paint layer at path."""
    w, h = doc.width(), doc.height()
    img = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
    img.fill(0)
    qp = QPainter(img)
    qp.setRenderHint(QPainter.Antialiasing, True)
    qp.setRenderHint(QPainter.SmoothPixmapTransform, True)
    qp.scale(scale, scale)
    qp.translate(OFFSET, 0)
    fn(Pen(qp))
    qp.end()
    node = find(doc, path)
    if not clear:
        old = node.pixelData(0, 0, w, h)
        base = QImage(old, w, h, QImage.Format_ARGB32).convertToFormat(QImage.Format_ARGB32_Premultiplied)
        qp = QPainter(base)
        qp.drawImage(0, 0, img)
        qp.end()
        img = base
    img = img.convertToFormat(QImage.Format_ARGB32)
    ptr = img.constBits()
    ptr.setsize(img.byteCount())
    node.setPixelData(bytes(ptr), 0, 0, w, h)
    return node


def blur(doc, path, radius):
    node = find(doc, path)
    f = Krita.instance().filter("gaussian blur")
    cfg = f.configuration()
    cfg.setProperty("horizRadius", radius)
    cfg.setProperty("vertRadius", radius)
    cfg.setProperty("lockAspect", True)
    f.setConfiguration(cfg)
    f.apply(node, 0, 0, doc.width(), doc.height())
    doc.waitForDone()


def place_image(doc, path, file, x, y, w, h):
    """Paste an image file scaled into a box (world units) on a layer."""
    src = QImage(file)

    def fn(pen):
        pen.p.drawImage(QRectF(x, y, w, h), src, QRectF(0, 0, src.width(), src.height()))
    return paint(doc, path, fn)


def refresh(doc):
    doc.refreshProjection()
    doc.waitForDone()


# ---- M1.0h additions ---------------------------------------------------------
import random as _random
from PyQt5.QtGui import QTransform

_TILES = {}


def noise_tile(seed=3, size=192, sigma=34, cell=1):
    """Grey noise tile (mean 128) for clipped overlay/soft-light texture layers."""
    key = (seed, size, sigma, cell)
    if key in _TILES:
        return _TILES[key]
    rnd = _random.Random(seed)
    n = size // cell
    small = QImage(n, n, QImage.Format_ARGB32)
    for y in range(n):
        for x in range(n):
            v = max(0, min(255, int(128 + rnd.gauss(0, sigma))))
            small.setPixel(x, y, (255 << 24) | (v << 16) | (v << 8) | v)
    img = small.scaled(size, size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation) if cell > 1 else small
    _TILES[key] = img
    return img


def texture(pen, path, tile, texel=0.5):
    """Fill `path` (world units) with a tiled texture at `texel` world units per tile pixel."""
    b = QBrush(tile)
    b.setTransform(QTransform().scale(texel, texel))
    pen.p.fillPath(path, b)


def streaks(pen, path, rect, color, n, length, angle_deg=0.0, seed=5, width=0.5):
    """Sparse grain streaks (wood/fabric direction) clipped to `path`."""
    import math
    rnd = _random.Random(seed)
    pen.p.save()
    pen.p.setClipPath(path)
    x, y, w, h = rect
    a = math.radians(angle_deg)
    for _ in range(n):
        sx, sy = x + rnd.uniform(0, w), y + rnd.uniform(0, h)
        L = rnd.uniform(length * 0.5, length)
        ex, ey = sx + L * math.cos(a), sy + L * math.sin(a)
        mid = ((sx + ex) / 2 + rnd.uniform(-1, 1), (sy + ey) / 2 + rnd.uniform(-0.6, 0.6))
        pen.line([(sx, sy), mid, (ex, ey)], color, width * rnd.uniform(0.6, 1.2))
    pen.p.restore()


def wline(pen, path, color, width, shadow=(-0.3, 0.35), extra=0.55):
    """Warm outline with slightly heavier weight on the shadow side (lower left by
    default, away from the window): the base stroke plus an offset partial stroke."""
    pen.stroke(path, color, width)
    pen.p.save()
    pen.p.translate(*shadow)
    c = C(color) if isinstance(color, str) else QColor(color)
    c.setAlpha(int(c.alpha() * extra))
    pen.stroke(path, c, width * 0.9)
    pen.p.restore()
