# M1.0i character fidelity assessment sheet (2560x2400 px).
from PyQt5.QtCore import QPointF, QRect, QRectF, Qt
from PyQt5.QtGui import QFont, QImage, QPen

import kpaint2 as K
from kpaint2 import C, rrect

E = K.ensure
COCOA, INK2, SAGE_D, TERRA = "#59463d", "#7a6558", "#5d7a60", "#a65a33"
REF = "/Users/mfm/code/porto-projects/app-momee/assets/references/calm-chibi-storybook/characters/character-master-v1.png"


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


def fit(p, img, src, x, y, w, h):
    s = min(w / src.width(), h / src.height())
    dw, dh = src.width() * s, src.height() * s
    p.p.drawImage(QRectF(x + (w - dw) / 2, y + (h - dh) / 2, dw, dh), img, QRectF(src))


def head_at(p, img, box, head_top, chin, x, y_chin, head_px):
    """Draw `box` of img scaled so the head (hair top → chin) is head_px tall, chin at y_chin."""
    s = head_px / (chin - head_top)
    bx, by, bw, bh = box
    p.p.drawImage(QRectF(x - bw * s / 2, y_chin - (chin - by) * s, bw * s, bh * s), img, QRectF(bx, by, bw, bh))


def run(d, f):
    m = QImage(REF)
    cand = QImage(f["candidate"])
    probe = {e: QImage(f[e]) for e in ("neutral", "happy", "talking")}
    E(d, "Paper")
    K.paint(d, "Paper", lambda p: p.fill(rrect(0, 0, d.width(), d.height(), 0), C("#fefaf1")), scale=1)
    E(d, "Header and legend")
    K.paint(d, "Header and legend", lambda p: (
        text(p, 40, 62, "MOMEE · M1.0i · CHARACTER FIDELITY ASSESSMENT — Boy head probe vs approved master", 36, COCOA, True),
        text(p, 40, 98, "Owner review. The probe is the only character art made in M1.0i: expansion to bodies, ¾ view and Mom was stopped "
             "because fidelity is below the master (brief §11).", 18, INK2),
        badge(p, 40, 118, "APPROVED REFERENCE", True), text(p, 260, 140, "solid sage frame · unmodified excerpts", 16, INK2),
        badge(p, 560, 118, "CANDIDATE · NOT APPROVED", False), text(p, 824, 140, "dashed terracotta frame · rights unverified", 16, INK2)),
        scale=1)

    E(d, "1 — Master Boy excerpts")

    def row1(p):
        text(p, 40, 210, "1 · Approved master — Boy (identity authority)", 28, COCOA, True)
        tiles = [(QRect(18, 140, 170, 370), "hero"), (QRect(180, 140, 85, 160), "front"), (QRect(255, 320, 100, 175), "¾"),
                 (QRect(18, 560, 160, 80), "neutral · happy · talking")]
        x = 40
        for (r, lab), w in zip(tiles, (330, 260, 260, 520)):
            frame(p, x, 236, w, 470, True)
            fit(p, m, r, x + 12, 248, w - 24, 380)
            text(p, x + 16, 660, "master v1 · " + lab, 16, COCOA, True)
            badge(p, x + 14, 668, "APPROVED REFERENCE", True)
            x += w + 14
        frame(p, x, 236, 2520 - x, 470, False)
        fit(p, cand, QRect(300, 0, 600, 1254), x + 12, 248, 2520 - x - 24, 380)
        text(p, x + 16, 660, "Existing Boy candidate (M0.3c.1)", 16, COCOA, True)
        badge(p, x + 14, 668, "CANDIDATE · NOT APPROVED", False)
    K.paint(d, "1 — Master Boy excerpts", row1, scale=1)

    E(d, "2 — M1.0i probe expressions")

    def row2(p):
        text(p, 40, 770, "2 · M1.0i Krita probe v1 — Boy front head, three expressions from one layered head", 28, COCOA, True)
        for i, e in enumerate(("neutral", "happy", "talking")):
            x = 40 + i * 830
            frame(p, x, 796, 816, 640, False)
            p.p.drawImage(QRectF(x + 48, 812, 720, 600), probe[e])
            badge(p, x + 14, 1392, "CANDIDATE · NOT APPROVED", False)
            text(p, x + 300, 1414, "probe v1 · " + e, 18, COCOA, True)
    K.paint(d, "2 — M1.0i probe expressions", row2, scale=1)

    E(d, "3 — Equal head height and gameplay scale")

    def row3(p):
        text(p, 40, 1500, "3 · Same head height: review size (300 px) and gameplay size (68 px at 0.85 CSS px/u, 94 px at 1.17)", 28, COCOA, True)
        srcs = [("master hero", m, (20, 150, 160, 160), 163, 297, True),
                ("existing candidate", cand, (300, 10, 600, 500), 28, 497, False),
                ("M1.0i probe", probe["neutral"], (0, 0, 720, 600), 0, 552, False)]
        frame(p, 40, 1526, 1560, 420, False)
        for i, (lab, img, box, top, chin, appr) in enumerate(srcs):
            cx = 300 + i * 500
            if appr:
                p.fill(rrect(cx - 200, 1540, 400, 396, 14), C("#fffdf8"))
                p.stroke(rrect(cx - 200, 1540, 400, 396, 14), C(SAGE_D), 4)
            p.p.save()
            p.p.setClipPath(rrect(cx - 196, 1544, 392, 388, 12))
            head_at(p, img, box, top, chin, cx, 1880, 300)
            p.p.restore()
            if appr:
                badge(p, cx - 186, 1896, "APPROVED REFERENCE", True)
            else:
                text(p, cx - 120, 1922, lab, 17, TERRA, True)
        frame(p, 1620, 1526, 900, 420, False)
        for j, hp in enumerate((68, 94)):
            for i, (lab, img, box, top, chin, appr) in enumerate(srcs):
                cx = 1720 + i * 140 + j * 420
                if appr:
                    p.stroke(rrect(cx - hp * 0.75, 1760 - hp * 1.15, hp * 1.5, hp * 1.3, 8), C(SAGE_D), 3)
                head_at(p, img, box, top, chin, cx, 1760, hp)
            text(p, 1660 + j * 420, 1800, f"{hp} px head · master · cand. · probe", 15, INK2)
        text(p, 1640, 1840, "Sage box = approved master excerpt; the other two in each trio are candidates.", 15, INK2)
        badge(p, 1640, 1880, "Rows 2–3 candidate art: NOT APPROVED", False)
    K.paint(d, "3 — Equal head height and gameplay scale", row3, scale=1)

    E(d, "4 — Master Mom excerpts (not attempted)")

    def row4(p):
        text(p, 40, 2010, "4 · Approved master — Mom (no Mom art produced in M1.0i)", 28, COCOA, True)
        tiles = [(QRect(683, 125, 160, 375), 300), (QRect(835, 135, 145, 365), 300), (QRect(775, 555, 368, 85), 900)]
        x = 40
        for r, w in tiles:
            frame(p, x, 2036, w, 330, True)
            fit(p, m, r, x + 12, 2048, w - 24, 260)
            badge(p, x + 14, 2322, "APPROVED REFERENCE", True)
            x += w + 14
        notes = ["Why expansion stopped:",
                 "• Hair: master = soft, sweeping locks with tan sheen; probe = stiff spiky silhouette (different idiom).",
                 "• Eyes: closer after pass 2, still generic; master's glossy iris and lash wedge read richer.",
                 "• Rendering: master is painted (soft gradients, colour-varied lines); probe is flat vector.",
                 "• At 68–94 px the probe's hair silhouette still reads as a different boy.",
                 "• Expressions do stay aligned: one head, swapped eye/brow/mouth layers."]
        for i, n in enumerate(notes):
            text(p, x + 10, 2066 + i * 44, n, 18 if i else 20, COCOA if i == 0 else INK2, i == 0)
    K.paint(d, "4 — Master Mom excerpts (not attempted)", row4, scale=1)
    K.refresh(d)
