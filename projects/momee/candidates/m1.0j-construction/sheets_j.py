# M1.0j-B review artwork: bedroom compatibility study and the review sheet.
# Character pixels are only placed and uniformly scaled (no repainting).
import json

from krita import Krita
from PyQt5.QtCore import QPointF, QRect, QRectF, Qt
from PyQt5.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPen

COCOA, INK2, SAGE, DUSTY, TERRA, GREY = "#59463d", "#7a6558", "#5d7a60", "#3f6488", "#a65a33", "#8a8580"
MASTER = "/Users/mfm/code/porto-projects/app-momee/assets/references/calm-chibi-storybook/characters/character-master-v1.png"
KINDS = {"master": ("APPROVED MASTER REFERENCE", SAGE, False, "#e3ecdf"),
         "accepted": ("OWNER-ACCEPTED VISUAL DIRECTION · not production-approved", DUSTY, False, "#e1e9f1"),
         "extract": ("EXTRACTION CANDIDATE · NOT APPROVED", TERRA, True, "#fbe7dc"),
         "placeholder": ("TECHNICAL PLACEHOLDER (M1.0i, rejected design)", GREY, True, "#ecebea")}


def new_doc(name, w, h):
    k = Krita.instance()
    for d in k.documents():
        if d.name() == name:
            for n in list(d.rootNode().childNodes()):
                n.remove()
            return d
    d = k.createDocument(w, h, name, "RGBA", "U8", "sRGB-elle-V2-srgbtrc.icc", 144)
    k.activeWindow().addView(d)
    for n in list(d.rootNode().childNodes()):
        n.remove()
    return d


def layer(d, name, fn, parent=None, visible=True):
    img = QImage(d.width(), d.height(), QImage.Format_ARGB32_Premultiplied)
    img.fill(0)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)
    fn(p)
    p.end()
    img = img.convertToFormat(QImage.Format_ARGB32)
    n = d.createNode(name, "paintlayer")
    (parent or d.rootNode()).addChildNode(n, None)
    ptr = img.constBits()
    ptr.setsize(img.byteCount())
    n.setPixelData(bytes(ptr), 0, 0, d.width(), d.height())
    n.setVisible(visible)
    return n


def text(p, x, y, s, size=17, color=COCOA, bold=False):
    f = QFont("Helvetica")
    f.setPixelSize(int(size))
    f.setBold(bold)
    p.setFont(f)
    p.setPen(QColor(color))
    p.drawText(QPointF(x, y), s)


def rr(x, y, w, h, r):
    path = QPainterPath()
    path.addRoundedRect(QRectF(x, y, w, h), r, r)
    return path


def badge(p, x, y, kind):
    label, col, dashed, fill = KINDS[kind]
    f = QFont("Helvetica")
    f.setPixelSize(15)
    f.setBold(True)
    p.setFont(f)
    w = p.fontMetrics().horizontalAdvance(label) + 28
    path = rr(x, y, w, 30, 15)
    p.fillPath(path, QColor(fill))
    p.strokePath(path, QPen(QColor(col), 2, Qt.DashLine if dashed else Qt.SolidLine))
    text(p, x + 14, y + 21, label, 15, col, True)
    return w


def frame(p, x, y, w, h, kind, bg="#fffdf8"):
    _, col, dashed, _ = KINDS[kind]
    path = rr(x, y, w, h, 18)
    p.fillPath(path, QColor(bg))
    p.strokePath(path, QPen(QColor(col), 4, Qt.DashLine if dashed else Qt.SolidLine, Qt.RoundCap))


def fit(p, img, src, x, y, w, h):
    s = min(w / src.width(), h / src.height())
    dw, dh = src.width() * s, src.height() * s
    p.drawImage(QRectF(x + (w - dw) / 2, y + (h - dh) / 2, dw, dh), img, QRectF(src))


def checker(p, x, y, w, h, c=10):
    for j in range(int(h // c) + 1):
        for i in range(int(w // c) + 1):
            p.fillRect(QRectF(x + i * c, y + j * c, min(c, w - i * c), min(c, h - j * c)),
                       QColor("#d9d6d2" if (i + j) % 2 else "#f4f2ef"))


def place(p, img, anchor, feet, scale):
    ax, ay = anchor
    p.drawImage(QRectF(feet[0] - ax * scale, feet[1] - (ay + 1) * scale, img.width() * scale, img.height() * scale), img)


# ---- bedroom compatibility study ------------------------------------------------------
def bedroom(F):
    d = new_doc("Momee bedroom accepted-characters study v1", 2560, 1440)
    room = QImage(F["room"])
    boy, mom = QImage(F["boy_native"]), QImage(F["mom_native"])
    bsh, msh = QImage(F["boy_shadow_native"]), QImage(F["mom_shadow_native"])
    B, Mo = F["boy_anchor"], F["mom_anchor"]
    bs, ms = 2 * 200 / F["boy_h"], 2 * 290 / F["mom_h"]          # to 2 px per world unit
    child, momspot = (1040, 1260), (1680, 1120)                  # CHILD_START, MOM_SPOT ×2
    layer(d, "Room — M1.0h bedroom study v2, room-only render (layout unchanged)", lambda p: p.drawImage(QRectF(0, 0, 2560, 1440), room))
    g = d.createNode("Characters — owner-accepted designs, extraction candidates", "grouplayer")
    d.rootNode().addChildNode(g, None)
    layer(d, "ground shadows — separated from the sheets (original pixels, scaled)", lambda p: (
        place(p, bsh, B, child, bs), place(p, msh, Mo, momspot, ms)), g)
    layer(d, "Boy — extraction candidate (2 px/u, downscaled ×%.3f)" % bs, lambda p: place(p, boy, B, child, bs), g)
    layer(d, "Mom — extraction candidate (study-only enlargement ×%.3f; no @2x export)" % ms, lambda p: place(p, mom, Mo, momspot, ms), g)
    layer(d, "Labels", lambda p: (
        text(p, 860, 1306, "BOY — owner-accepted design · extraction candidate (not approved) · 200 u", 16),
        text(p, 1500, 1166, "MOM v1.2 — owner-accepted design · extraction candidate (not approved) · 290 u", 16)))
    d.refreshProjection()
    d.waitForDone()
    return d


# ---- review sheet -------------------------------------------------------------------------
def sheet(F):
    d = new_doc("Momee accepted characters review sheet v1", 2560, 4160)
    m = QImage(MASTER)
    bsheet, msheet = QImage(F["boy_sheet"]), QImage(F["mom_sheet"])
    bn, mn = QImage(F["boy_native"]), QImage(F["mom_native"])
    bcrop, mcrop = QImage(F["boy_crop"]), QImage(F["mom_crop"])
    bex, mex = QImage(F["boy_extracted"]), QImage(F["mom_extracted"])
    study = QImage(F["study"])
    old = QImage(F["m1i_study"])
    ph = {k: QImage(v) for k, v in F["placeholders"].items()}
    tiers = {k: QImage(v) for k, v in F["tiers"].items()}
    layer(d, "Paper", lambda p: p.fillRect(0, 0, 2560, 4160, QColor("#fefaf1")))

    def head(p):
        text(p, 40, 62, "MOMEE · M1.0j-B · ACCEPTED CHARACTER REFERENCES → NON-DESTRUCTIVE EXTRACTION", 36, COCOA, True)
        text(p, 40, 98, "Owner review. Extracted pixels are the accepted artwork, unrepainted; only the panel background and ground shadow were "
             "separated. Nothing here is production-approved; rights are unverified.", 18, INK2)
        x = 40
        for k in ("master", "accepted", "extract", "placeholder"):
            x += badge(p, x, 118, k) + 16
    layer(d, "Header and legend", head)

    def row1(p):
        text(p, 40, 210, "1 · Identity authorities — approved master v1 and the owner-accepted reference sheets", 28, COCOA, True)
        tiles = [(QRect(18, 140, 170, 370), "Boy hero"), (QRect(255, 320, 100, 175), "Boy ¾"),
                 (QRect(683, 125, 160, 375), "Mom hero"), (QRect(905, 315, 75, 185), "Mom ¾")]
        x = 40
        for r, lab in tiles:
            frame(p, x, 236, 200, 520, "master")
            fit(p, m, r, x + 10, 246, 180, 420)
            text(p, x + 12, 690, "master v1 · " + lab, 15, COCOA, True)
            x += 212
        for img, lab in ((bsheet, "candidates/m1.0j/character-reference-v1.png — Boy sheet (titled “v1.1”)"),
                         (msheet, "candidates/m1.0j/mom-character-reference-v1.2.png — Mom v1.2 sheet")):
            frame(p, x, 236, 820, 600, "accepted")
            fit(p, img, QRect(0, 0, 1536, 1024), x + 12, 248, 796, 531)
            text(p, x + 14, 808, lab, 14, COCOA, True)
            x += 832
        badge(p, 40, 712, "master")
        badge(p, 888, 848, "accepted")
        badge(p, 1720, 848, "accepted")
    layer(d, "1 — Master and accepted references", row1)

    def row2(p):
        text(p, 40, 950, "2 · Extraction candidates (native resolution, unresampled) on three backgrounds — and the M1.0i placeholders", 28, COCOA, True)
        x = 40
        bi, mi = F["boy_info"], F["mom_info"]
        for img, lab in ((bn, f"Boy · {bn.width()}×{bn.height()} native · figure {bi['figureHeightPx']} px = {bi['figureHeightPx'] / 200:.2f} px/u"),
                         (mn, f"Mom v1.2 · {mn.width()}×{mn.height()} native · figure {mi['figureHeightPx']} px = {mi['figureHeightPx'] / 290:.2f} px/u")):
            frame(p, x, 976, 3 * (img.width() + 14) + 26, 640, "extract")
            for i, bg in enumerate(("checker", "#2a2523", "#96b5c3")):
                bx = x + 14 + i * (img.width() + 14)
                if bg == "checker":
                    checker(p, bx, 990, img.width(), img.height())
                else:
                    p.fillRect(QRectF(bx, 990, img.width(), img.height()), QColor(bg))
                p.drawImage(QPointF(bx, 990), img)
            text(p, x + 16, 1560, lab, 15, COCOA, True)
            badge(p, x + 14, 1572, "extract")
            x += 3 * (img.width() + 14) + 40
        frame(p, x, 976, 2520 - x, 640, "placeholder")
        for i, k in enumerate(("boy", "mom")):
            im = ph[k]
            fit(p, im, QRect(0, 0, im.width(), im.height()), x + 20 + i * 210, 996, 200, 540)
        text(p, x + 16, 1560, "M1.0i ¾ neutral placeholders (procedural)", 15, COCOA, True)
        badge(p, x + 14, 1572, "placeholder")
    layer(d, "2 — Extraction candidates and placeholders", row2)

    def row3(p):
        text(p, 40, 1700, "3 · Fidelity check — sheet crop (left of each pair) vs extraction on dark (right), 3× nearest-neighbour", 28, COCOA, True)
        bi, mi = F["boy_info"], F["mom_info"]
        regions = [("Boy hair edge", bcrop, bex, QRect(20, 0, 120, 90)), ("Boy hand", bcrop, bex, QRect(52, 332, 58, 58)),
                   ("Boy shoes", bcrop, bex, QRect(70, 440, 200, 82)), ("Mom hair locks", mcrop, mex, QRect(20, 140, 90, 88)),
                   ("Mom clasped hands", mcrop, mex, QRect(130, 270, 80, 60)), ("Mom shoes", mcrop, mex, QRect(60, 470, 180, 52))]
        x, y = 40, 1730
        for lab, src, ex, r in regions:
            w, h = r.width() * 3, r.height() * 3
            if x + 2 * w + 40 > 2520:
                x, y = 40, y + 380
            frame(p, x - 8, y - 8, 2 * w + 34, h + 52, "extract")
            p.drawImage(QRectF(x, y, w, h), src, QRectF(r))
            p.fillRect(QRectF(x + w + 12, y, w, h), QColor("#2a2523"))
            p.drawImage(QRectF(x + w + 12, y, w, h), ex, QRectF(r))
            text(p, x, y + h + 30, lab, 15, COCOA, True)
            x += 2 * w + 60
        text(p, 40, 2490, f"Opaque pixels changed: Boy {bi['opaqueChanged']} of {bi['opaquePixels']:,} · Mom {mi['opaqueChanged']} of {mi['opaquePixels']:,}. "
             "Only the 2 px edge band was unmixed; reviewed enclosed gaps were cleared by explicit seeds; residual: a few 1 px light flecks at Boy tuft tips.", 17, INK2)
    layer(d, "3 — Fidelity check", row3)

    def row4(p):
        text(p, 40, 2560, "4 · Bedroom compatibility — M1.0h room, unchanged coordinates (Boy at CHILD_START 200 u, Mom at MOM_SPOT 290 u)", 28, COCOA, True)
        for i, (im, lab, kind) in enumerate(((old, "BEFORE — M1.0i procedural placeholders", "placeholder"),
                                              (study, "AFTER — owner-accepted designs, extraction candidates", "extract"))):
            x = 40 + i * 1246
            frame(p, x, 2586, 1234, 760, kind)
            p.drawImage(QRectF(x + 12, 2598, 1210, 680), im, QRectF(0, 0, 2560, 1440))
            badge(p, x + 14, 3296, kind)
            text(p, x + 14 + 470, 3318, lab, 16, COCOA, True)
    layer(d, "4 — Bedroom compatibility", row4)

    def row5(p):
        text(p, 40, 3410, "5 · Mobile scale (1:1 CSS px on a 1× screen) and runtime tiers", 28, COCOA, True)
        crops = [("390×844 · child-and-mom · 1.17", 1.172, (623, 200, 333, 520)), ("844×390 · overview · 0.85", 0.85, (193, 245, 993, 459))]
        x = 40
        for lab, z, (wx, wy, ww, wh) in crops:
            w, h = ww * z, wh * z
            p.drawImage(QRectF(x, 3440, w, h), study, QRectF(wx * 2, wy * 2, ww * 2, wh * 2))
            p.strokePath(rr(x, 3440, w, h, 0), QPen(QColor(TERRA), 2, Qt.DashLine))
            text(p, x, 3440 + h + 24, lab, 16, COCOA, True)
            x += w + 40
        text(p, 40, 3440 + 520 * 1.172 + 52, "child-and-mom frames the beat where the child has walked to Mom's approach point (730, 590); "
             "this study keeps him at CHILD_START, so only Mom is in frame.", 15, INK2)
        for k, im in tiers.items():
            checker(p, x, 3440, im.width(), im.height())
            p.drawImage(QPointF(x, 3440), im)
            text(p, x, 3440 + im.height() + 22, k, 14, COCOA, True)
            x += im.width() + 24
        badge(p, x - 520, 3440 + 470, "extract")
    layer(d, "5 — Mobile scale and tiers", row5)
    d.refreshProjection()
    d.waitForDone()
    return d
