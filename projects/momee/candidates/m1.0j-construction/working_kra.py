# M1.0j-B layered working source (stage 3). Imports pixels only; nothing is painted or
# redrawn except hidden guide lines. Canvas = the native extraction canvas.
import json

from krita import Krita
from PyQt5.QtCore import QPoint, QRectF, Qt
from PyQt5.QtGui import QColor, QImage, QPainter, QPen


def _set(node, img, w, h):
    img = img.convertToFormat(QImage.Format_ARGB32)
    ptr = img.constBits()
    ptr.setsize(img.byteCount())
    node.setPixelData(bytes(ptr), 0, 0, w, h)


def _canvas_image(w, h, src, dx, dy):
    out = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
    out.fill(0)
    p = QPainter(out)
    p.setCompositionMode(QPainter.CompositionMode_Source)
    p.drawImage(QPoint(dx, dy), src)     # whole-pixel translation only (no resampling)
    p.end()
    return out


def add(d, parent, name, img=None, visible=True, locked=False, opacity=255):
    n = d.createNode(name, "paintlayer")
    parent.addChildNode(n, None)
    if img is not None:
        _set(n, img, d.width(), d.height())
    n.setVisible(visible)
    n.setOpacity(opacity)
    n.setLocked(locked)
    return n


def build(title, native_png, source_crop_png, shadow_png, info_json, tier_info_json, label):
    info = json.loads(open(info_json).read())
    tiers = json.loads(open(tier_info_json).read())
    native = QImage(native_png)
    W, H = native.width(), native.height()
    nAx, nAy = tiers["files"][0]["anchorPx"]
    ax, ay = info["feetAnchorPx"]
    dx, dy = nAx - ax, nAy - ay                  # extraction-crop → native-canvas offset
    k = Krita.instance()
    d = k.createDocument(W, H, title, "RGBA", "U8", "sRGB-elle-V2-srgbtrc.icc", 300)
    k.activeWindow().addView(d)
    root = d.rootNode()
    for n in list(root.childNodes()):
        n.remove()
    g = d.createNode("1 · Reference — original sheet crop (locked, read-only)", "grouplayer")
    root.addChildNode(g, None)
    add(d, g, f"sheet crop {info['crop']} of {label} (flattened over panel colour)",
        _canvas_image(W, H, QImage(source_crop_png), dx, dy), visible=False, locked=True)
    g.setVisible(False)
    g2 = d.createNode("2 · Extracted character (unmodified pixels; candidate)", "grouplayer")
    root.addChildNode(g2, None)
    add(d, g2, "ground shadow — separated from the sheet", _canvas_image(W, H, QImage(shadow_png), dx, dy), opacity=255)
    add(d, g2, "character — extracted full figure", native)
    add(d, g2, "cleanup — empty (manual edge fixes only, never redraw)")
    g3 = d.createNode("3 · Guides (hidden)", "grouplayer")
    root.addChildNode(g3, None)
    gi = QImage(W, H, QImage.Format_ARGB32_Premultiplied)
    gi.fill(0)
    p = QPainter(gi)
    p.setPen(QPen(QColor("#d48658"), 1))
    p.drawLine(0, nAy + 1, W, nAy + 1)
    p.drawLine(nAx, nAy - 10, nAx, nAy + 6)
    p.setPen(QPen(QColor("#6986a2"), 1, Qt.DashLine))
    p.drawLine(0, nAy - info["figureHeightPx"] + 1, W, nAy - info["figureHeightPx"] + 1)
    p.end()
    add(d, g3, f"ground line y={nAy + 1}, feet anchor ({nAx},{nAy}), hair-top line", gi)
    g3.setVisible(False)
    d.refreshProjection()
    d.waitForDone()
    return d
