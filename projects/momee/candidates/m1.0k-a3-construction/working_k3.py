# M1.0k-A3 non-destructive Krita working source for the Mom master candidate v2 (stage-4 candidate, flat).
# Imports pixels only. Every layer is either the placed master candidate, an unresampled original
# (whole-pixel translation), or hidden guide lines. Nothing is painted, redrawn or enlarged.
# Canvas = the Mom master spec: 800×1248, feet anchor (400, 1216), soles on row 1215.
import sys

sys.path.insert(0, "/Users/mfm/code/porto-projects/ecosystem-assets/projects/momee/candidates/m1.0j-construction")
from working_kra import _canvas_image, add  # noqa: E402

from krita import Krita  # noqa: E402
from PyQt5.QtCore import Qt  # noqa: E402
from PyQt5.QtGui import QColor, QImage, QPainter, QPen  # noqa: E402

W, H, AX, AY = 800, 1248, 400, 1216


def build(F, title):
    k = Krita.instance()
    d = k.createDocument(W, H, title, "RGBA", "U8", "sRGB-elle-V2-srgbtrc.icc", 300)
    k.activeWindow().addView(d)
    root = d.rootNode()
    for n in list(root.childNodes()):
        n.remove()

    g1 = d.createNode("1 · Reference (hidden, locked, read-only)", "grouplayer")
    root.addChildNode(g1, None)
    add(d, g1, "accepted Mom v1.2 extraction — native 514 px, NOT scaled, feet on the anchor (side reference only)",
        _canvas_image(W, H, QImage(F["accepted"]), F["accepted_dx"], F["accepted_dy"]), visible=False, locked=True)
    add(d, g1, "original candidate v2 — native pixels, unresampled, translated (%d, %d); canvas window only — "
               "source of truth: candidates/m1.0k-a/mom-three-quarter-master-candidate-v2.png" % (F["orig_dx"], F["orig_dy"]),
        _canvas_image(W, H, QImage(F["original"]), F["orig_dx"], F["orig_dy"]), visible=False, locked=True)
    g1.setVisible(False)

    g2 = d.createNode("2 · Master candidate v2 (candidate — not accepted, not approved)", "grouplayer")
    root.addChildNode(g2, None)
    add(d, g2, "shadow — empty (contact shadow belongs on this layer; none is baked into the art)")
    add(d, g2, "character — master candidate v2 (alpha-only glow trim, uniform downscale ×0.9683)", QImage(F["master"]))
    add(d, g2, "cleanup — empty (alpha-only edge fixes; never redraw)")

    g3 = d.createNode("3 · Guides (hidden)", "grouplayer")
    root.addChildNode(g3, None)
    gi = QImage(W, H, QImage.Format_ARGB32_Premultiplied)
    gi.fill(0)
    p = QPainter(gi)
    p.setPen(QPen(QColor("#d48658"), 1))
    p.drawLine(0, AY, W, AY)                      # ground line = top edge of row 1216
    p.drawLine(AX, AY - 12, AX, AY + 8)           # feet anchor
    p.setPen(QPen(QColor("#6986a2"), 1, Qt.DashLine))
    p.drawLine(0, 56, W, 56)                      # hair top: 290 u (1160 px) above the ground; 14 u headroom
    p.drawLine(0, F["chin"], W, F["chin"])        # chin landmark (head count 1160 / (chin − 56))
    p.setPen(QPen(QColor("#a6a19b"), 1, Qt.DotLine))
    for heads in (3.2, 3.5):                      # D13 range: chin row for 3.2 and 3.5 heads
        y = round(56 + 1160 / heads)
        p.drawLine(0, y, 60, y)
        p.drawLine(W - 60, y, W, y)
    p.end()
    add(d, g3, "ground line y=1216, feet anchor (400,1216), hair-top y=56, chin y=%d, D13 3.2/3.5-head ticks" % F["chin"], gi)
    g3.setVisible(False)
    d.refreshProjection()
    d.waitForDone()
    return d
