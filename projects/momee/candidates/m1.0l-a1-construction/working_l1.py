# M1.0l-A1 head-pilot Krita working copy for Mom v2. Imports the extracted layer PNGs unchanged (every master
# pixel lives in exactly one layer) plus the untouched master as a hidden, locked reference. Placeholders for
# artwork that does not exist yet are EMPTY hidden layers named "… — TO PAINT"; nothing is painted or generated.
import sys

sys.path.insert(0, "/Users/mfm/code/porto-projects/ecosystem-assets/projects/momee/candidates/m1.0j-construction")
from working_kra import add  # noqa: E402

from krita import Krita  # noqa: E402
from PyQt5.QtCore import Qt  # noqa: E402
from PyQt5.QtGui import QColor, QFont, QImage, QPainter, QPen  # noqa: E402

W, H = 800, 1248


def group(d, parent, name, visible=True):
    g = d.createNode(name, "grouplayer")
    parent.addChildNode(g, None)
    g.setVisible(visible)
    return g


def build(F, title, pivots):
    k = Krita.instance()
    d = k.createDocument(W, H, title, "RGBA", "U8", "sRGB-elle-V2-srgbtrc.icc", 300)
    k.activeWindow().addView(d)
    root = d.rootNode()
    for n in list(root.childNodes()):
        n.remove()
    L = lambda n: QImage(F["layers"] + n + ".png")  # noqa: E731

    g = group(d, root, "00 reference (hidden, locked) — accepted Mom v2 master, untouched", visible=False)
    add(d, g, "mom-three-quarter-master-candidate.v2.master.png (pixel-identical import)", QImage(F["master"]), visible=False, locked=True)

    # back → front, character-master-spec §6 order (only the slots this pilot touches)
    group(d, root, "shadow")
    hb = group(d, root, "hair-back", visible=True)
    add(d, hb, "hair-back/long — TO PAINT (does not exist in the flat art; empty)", visible=False)
    gb = group(d, root, "base (unseparated)")
    add(d, gb, "base/unseparated — all hair (front + back), body, outfit, near brow, face rim", L("base"))
    bs = group(d, root, "body-skin")
    add(d, bs, "body-skin/neck-visible", L("body-skin__neck-visible"))
    add(d, bs, "body-skin/neck-extension — TO PAINT (≥ 24 px up under the chin; empty)", visible=False)
    hs = group(d, root, "head-skin")
    add(d, hs, "head-skin/base — face, ear, nose, blush (holes under the face attachments)", L("head-skin__base"))
    add(d, hs, "head-skin/under-features — TO PAINT (skin beneath eyes, far brow, mouth; empty)", visible=False)
    fe = group(d, root, "face-eyes")
    op = group(d, fe, "face-eyes/open")
    add(d, op, "eye-near (viewer's left)", L("face-eyes__open__eye-near"))
    add(d, op, "eye-far (viewer's right)", L("face-eyes__open__eye-far"))
    for a in ("half", "closed", "happy"):
        add(d, fe, f"face-eyes/{a} — TO PAINT (empty)", visible=False)
    fb = group(d, root, "face-brows")
    add(d, fb, "face-brows/neutral — far brow only (near brow is inside the hair sweep, not separable)", L("face-brows__neutral__brow-far"))
    add(d, fb, "face-brows/raised — TO PAINT (empty)", visible=False)
    fm = group(d, root, "face-mouth")
    add(d, fm, "face-mouth/neutral — closed gentle smile", L("face-mouth__neutral"))
    for a in ("talking-a (small open)", "talking-b (wider open)", "happy (open smile)"):
        add(d, fm, f"face-mouth/{a} — TO PAINT (empty)", visible=False)
    hf = group(d, root, "hair-front")
    add(d, hf, "hair-front/side-part — NOT SEPARATED (still in base; extraction planned for M1.0l-A2; empty)", visible=False)

    gg = group(d, root, "99 guides (hidden) — pivots and anchors", visible=False)
    gi = QImage(W, H, QImage.Format_ARGB32_Premultiplied)
    gi.fill(0)
    p = QPainter(gi)
    p.setRenderHint(QPainter.Antialiasing, True)
    f = QFont("Helvetica")
    f.setPixelSize(11)
    p.setFont(f)
    for name, (x, y) in pivots.items():
        p.setPen(QPen(QColor("#d43a3a"), 1))
        p.drawLine(x - 6, y, x + 6, y)
        p.drawLine(x, y - 6, x, y + 6)
        p.drawText(x + 8, y - 4, name)
    p.setPen(QPen(QColor("#d48658"), 1))
    p.drawLine(0, 1216, W, 1216)
    p.setPen(QPen(QColor("#6986a2"), 1, Qt.DashLine))
    p.drawLine(0, 56, W, 56)
    p.end()
    add(d, gg, "pivots, anchors, ground line y=1216, hair top y=56", gi)
    d.refreshProjection()
    d.waitForDone()
    return d
