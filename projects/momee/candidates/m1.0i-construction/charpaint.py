# M1.0i character drawing helpers (extends kpaint2). World units; the canvas
# origin is the character's feet anchor shifted by (AX, AY).
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainterPath

import kpaint2 as K
from kpaint2 import C


def path_kinds(seq, closed=True, t=0.5):
    """Catmull-Rom path where points marked 't' are sharp tips (zero tangent)."""
    n = len(seq)
    pts = [(x, y) for x, y, _ in seq]
    kinds = [k for _, _, k in seq]
    path = QPainterPath(QPointF(*pts[0]))
    segs = n if closed else n - 1
    for i in range(segs):
        i0, i1, i2, i3 = (i - 1) % n, i, (i + 1) % n, (i + 2) % n
        p0, p1, p2, p3 = pts[i0], pts[i1], pts[i2], pts[i3]
        if not closed:
            if i == 0:
                p0 = p1
            if i + 2 >= n:
                p3 = p2
        if kinds[i1] == "t":
            c1 = (p1[0] + (p2[0] - p1[0]) * 0.12, p1[1] + (p2[1] - p1[1]) * 0.12)
        else:
            c1 = (p1[0] + (p2[0] - p0[0]) * t / 3, p1[1] + (p2[1] - p0[1]) * t / 3)
        if kinds[i2 % n] == "t":
            c2 = (p2[0] - (p2[0] - p1[0]) * 0.12, p2[1] - (p2[1] - p1[1]) * 0.12)
        else:
            c2 = (p2[0] - (p3[0] - p1[0]) * t / 3, p2[1] - (p3[1] - p1[1]) * t / 3)
        path.cubicTo(QPointF(*c1), QPointF(*c2), QPointF(*p2))
    if closed:
        path.closeSubpath()
    return path


def mirror(pts):
    """Mirror a left-half outline (x < 0, top → bottom) to a closed symmetric list."""
    right = [(-x, y, k) for x, y, k in reversed(pts)]
    return pts + right


def tapered(p, pts, color, w0, w1, w2=None, t=0.5):
    """A brush-like tapered stroke: thin ends, fuller middle (polygon ribbon)."""
    import math
    from kpaint2 import smooth
    path = smooth(pts, closed=False, t=t)
    n = 40
    samples = [path.pointAtPercent(i / n) for i in range(n + 1)]
    left, right = [], []
    w2 = w0 if w2 is None else w2
    for i, s in enumerate(samples):
        u = i / n
        w = (w0 * (1 - u) * (1 - u) + 2 * w1 * u * (1 - u) + w2 * u * u) / 2
        a = samples[min(i + 1, n)]
        b = samples[max(i - 1, 0)]
        dx, dy = a.x() - b.x(), a.y() - b.y()
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        left.append((s.x() + nx * w, s.y() + ny * w))
        right.append((s.x() - nx * w, s.y() - ny * w))
    ribbon = QPainterPath(QPointF(*left[0]))
    for q in left[1:] + list(reversed(right)):
        ribbon.lineTo(QPointF(*q))
    ribbon.closeSubpath()
    p.fill(ribbon, C(color) if isinstance(color, str) else color)
