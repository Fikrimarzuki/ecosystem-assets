# M1.0h bedroom refinement comparison sheet (2560x3420 px). Reference excerpts
# are drawn scaled from the read-only reference files.
from PyQt5.QtCore import QPointF, QRect, QRectF, Qt
from PyQt5.QtGui import QFont, QImage, QPen

import kpaint2 as K
from kpaint2 import C, rrect, ellipse

E = K.ensure
COCOA, INK2, SAGE_D, TERRA = "#59463d", "#7a6558", "#5d7a60", "#a65a33"
PAPER = "#fefaf1"
REF = "/Users/mfm/code/porto-projects/app-momee/assets/references/"


def text(p, x, y, s, size=17, color=COCOA, bold=False):
    f = QFont("Helvetica")
    f.setPixelSize(int(size))
    f.setBold(bold)
    p.p.setFont(f)
    p.p.setPen(C(color))
    p.p.drawText(QPointF(x, y), s)


def badge(p, x, y, label, approved):
    f = QFont("Helvetica")
    f.setPixelSize(15)
    f.setBold(True)
    p.p.setFont(f)
    w = p.p.fontMetrics().horizontalAdvance(label) + 28
    shape = rrect(x, y, w, 30, 15)
    p.fill(shape, C("#e3ecdf" if approved else "#fbe7dc"))
    if approved:
        p.stroke(shape, C(SAGE_D), 2)
    else:
        p.p.strokePath(shape, QPen(C(TERRA), 2, Qt.DashLine))
    text(p, x + 14, y + 21, label, 15, SAGE_D if approved else TERRA, True)


def frame(p, x, y, w, h, approved):
    fr = rrect(x, y, w, h, 18)
    p.fill(fr, C("#fffdf8"))
    if approved:
        p.stroke(fr, C(SAGE_D), 4)
    else:
        p.p.strokePath(fr, QPen(C(TERRA), 4, Qt.DashLine, Qt.RoundCap))


def image_in(p, img, src, x, y, w, h):
    s = min(w / src.width(), h / src.height())
    dw, dh = src.width() * s, src.height() * s
    p.p.drawImage(QRectF(x + (w - dw) / 2, y + (h - dh) / 2, dw, dh), img, QRectF(src))


def tile(p, x, y, w, h, img, src, title, sub, approved, label=None):
    frame(p, x, y, w, h, approved)
    p.p.save()
    p.p.setClipPath(rrect(x + 12, y + 12, w - 24, h - 120, 12))
    image_in(p, img, src, x + 12, y + 12, w - 24, h - 120)
    p.p.restore()
    badge(p, x + 14, y + h - 104, label or ("APPROVED REFERENCE" if approved else "CANDIDATE · NOT APPROVED"), approved)
    text(p, x + 16, y + h - 48, title, 18, COCOA, True)
    text(p, x + 16, y + h - 22, sub, 14, INK2)


def section(p, y, title, sub):
    text(p, 40, y, title, 30, COCOA, True)
    text(p, 40, y + 30, sub, 17, INK2)


def run(d, f):
    v1, v2 = QImage(f["v1"]), QImage(f["v2"])
    v1r, v2r = QImage(f["v1_room"]), QImage(f["v2_room"])
    p2u, p2m, p3u, p3m = (QImage(f[k]) for k in ("p2u", "p2m", "p3u", "p3m"))
    sb = QImage(REF + "concepts/morning-routine-storyboard.png")
    gp = QImage(REF + "concepts/morning-routine-gameplay.png")
    fc = QImage(REF + "concepts/feature-concepts.png")
    full = QRect(0, 0, 2560, 1440)

    E(d, "Paper")
    K.paint(d, "Paper", lambda p: p.fill(rrect(0, 0, d.width(), d.height(), 0), C(PAPER)), scale=1)
    E(d, "Header and legend")
    K.paint(d, "Header and legend", lambda p: (
        text(p, 40, 62, "MOMEE · M1.0h · BEDROOM REFINEMENT — before and after", 38, COCOA, True),
        text(p, 40, 98, "Owner review. M1.0g and M1.0h bedrooms and both pillow revisions are candidates; references are "
             "unmodified excerpts scaled for layout. Layout and gameplay coordinates are identical in both.", 18, INK2),
        badge(p, 40, 118, "APPROVED REFERENCE", True), text(p, 260, 140, "solid sage frame", 16, INK2),
        badge(p, 440, 118, "CANDIDATE · NOT APPROVED", False), text(p, 704, 140, "dashed terracotta frame · rights unverified", 16, INK2)),
        scale=1)

    E(d, "1 — Before and after (full room)")
    K.paint(d, "1 — Before and after (full room)", lambda p: (
        section(p, 210, "1 · Before → after", "Same room, same coordinates. Boy = existing candidate, unmodified; Mom = labelled placeholder."),
        tile(p, 40, 260, 1234, 820, v1, full, "BEFORE — M1.0g bedroom composition study v1", "uniform paper grain · heavier lines · flat light", False),
        tile(p, 1286, 260, 1234, 820, v2, full, "AFTER — M1.0h bedroom composition study v2", "window daylight · lower mattress · pillow v3 · selective texture", False)),
        scale=1)

    E(d, "2 — Approved bedroom references")
    refs = [(sb, QRect(1138, 790, 192, 100), "Storyboard — bedroom style", "morning-routine-storyboard.png · 1138,790"),
            (sb, QRect(0, 0, 505, 405), "Storyboard — wake up", "morning-routine-storyboard.png · 0,0"),
            (gp, QRect(15, 425, 385, 280), "Gameplay — make the bed", "morning-routine-gameplay.png · 15,425"),
            (fc, QRect(513, 855, 190, 145), "Features — connected bedroom", "feature-concepts.png · 513,855")]
    K.paint(d, "2 — Approved bedroom references", lambda p: (
        section(p, 1150, "2 · Approved bedroom references", "Visual authority for light, bedding, wood and line."),
        [tile(p, 40 + i * 623, 1200, 607, 500, img, r, t, s, True) for i, (img, r, t, s) in enumerate(refs)]),
        scale=1)

    E(d, "3 — Bed detail 1:1")
    crop = QRect(120, 560, 960, 640)   # world x 60–540, y 280–600 at 2 px/u

    def bed(p):
        section(p, 1770, "3 · Bed detail at 2× (1 world unit = 2 px)", "Mattress 92 u → 80 u high and 36 u thick; fuller duvet with fold ridges; carved bevels; contact shadows.")
        for i, (img, lab) in enumerate([(v1r, "BEFORE — M1.0g (pillow v2)"), (v2r, "AFTER — M1.0h (pillow v3)")]):
            x = 40 + i * 1246
            frame(p, x, 1820, 1234, 720, False)
            p.p.drawImage(QRectF(x + 137, 1832, 960, 640), img, QRectF(crop))
            badge(p, x + 14, 2486, "CANDIDATE · NOT APPROVED", False)
            text(p, x + 330, 2508, lab, 18, COCOA, True)
    K.paint(d, "3 — Bed detail 1:1", bed, scale=1)

    E(d, "4 — Pillow v2 versus v3")

    def pillows(p):
        section(p, 2610, "4 · Pillow v2 → v3 (candidates, true relative scale @2x)", "v3 is 1.24× larger (≈ 131 u, ≈ 1.5× the Boy's head width); deeper shading, bounce light, fold ridges, softer contact shadow.")
        frame(p, 40, 2660, 1520, 400, False)
        cells = [("v2 unmade", p2u, (32, 16)), ("v2 made", p2m, (32, 16)), ("v3 unmade", p3u, (0, 0)), ("v3 made", p3m, (0, 0))]
        for i, (lab, img, (ox, oy)) in enumerate(cells):
            x = 64 + i * 370
            p.fill(rrect(x, 2684, 340, 240, 12), C("#9dbbc8" if i % 2 == 0 else "#f9eddc"))
            p.p.drawImage(QRectF(x + 10 + ox, 2692 + oy, img.width(), img.height()), img)
            dashed = QPen(C("#4f6a84"), 1.5, Qt.DashLine)
            p.p.strokePath(ellipse(x + 10 + 160 - 86, 2692 + 112 - 70, 172, 160), dashed) if i >= 2 else None
            text(p, x, 2950, lab + (" · head 86 u dashed" if i >= 2 else ""), 16, COCOA, True)
        badge(p, 64, 2990, "CANDIDATE · NOT APPROVED", False)
        text(p, 360, 3012, "v2: 128×96 @1x canvas · v3: 160×112 @1x canvas, centre anchor (160, 112) @2x", 15, INK2)
        # gameplay-scale strip: both revisions at the 0.85 CSS px/u camera floor and @1x
        frame(p, 1580, 2660, 940, 400, False)
        text(p, 1604, 2700, "Gameplay scale (shown 1:1 on a 1× screen)", 18, COCOA, True)
        p.fill(rrect(1604, 2716, 892, 150, 10), C("#f9eddc"))
        k = 0.85 / 2
        for i, (img, ox) in enumerate([(p2u, 16), (p2m, 16), (p3u, 0), (p3m, 0)]):
            p.p.drawImage(QRectF(1620 + i * 220 + ox * 0.85, 2730, img.width() * k, img.height() * k), img)
        text(p, 1604, 2890, "v2 unmade · v2 made · v3 unmade · v3 made — at 0.85 CSS px/u", 15, INK2)
        text(p, 1604, 2920, "v3 width ≈ 111 CSS px at the camera floor (v2 ≈ 90); both states stay distinct.", 15, INK2)
        badge(p, 1604, 2990, "CANDIDATE · NOT APPROVED", False)
    K.paint(d, "4 — Pillow v2 versus v3", pillows, scale=1)

    E(d, "5 — Gameplay-scale framing")

    def framing(p):
        section(p, 3130, "5 · Gameplay-scale framing at the camera floor (0.85 CSS px/u, 1:1 on a 1× screen)", "Phone portrait bed view (world x 62–478) and phone landscape overview (world x 193–1186), before and after.")
        badge(p, 2250, 3104, "CANDIDATE · NOT APPROVED", False)
        k = 0.85 / 2
        portrait = QRect(124, 500, 832, 800)     # world x 62–478, y 250–650
        landscape = QRect(386, 490, 1986, 918)   # world x 193–1186, y 245–704
        x = 40
        for lab, img in [("M1.0g", v1), ("M1.0h", v2)]:
            p.p.drawImage(QRectF(x, 3180, portrait.width() * k, portrait.height() * k), img, QRectF(portrait))
            text(p, x, 3180 + portrait.height() * k + 22, lab + " candidate · 390×844 bed", 15, COCOA, True)
            x += portrait.width() * k + 24
        for lab, img in [("M1.0g", v1), ("M1.0h", v2)]:
            p.p.drawImage(QRectF(x, 3180, landscape.width() * k, landscape.height() * k), img, QRectF(landscape))
            text(p, x, 3180 + landscape.height() * k + 22, lab + " candidate · 844×390 overview", 15, COCOA, True)
            x += landscape.width() * k + 24
    K.paint(d, "5 — Gameplay-scale framing", framing, scale=1)
    K.refresh(d)
