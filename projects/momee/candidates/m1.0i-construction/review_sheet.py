# M1.0i character review sheet (2560x3900 px): identity comparison, height line-up,
# expression comparison, bedroom before/after and mobile gameplay-scale framing.
from PyQt5.QtCore import QPointF, QRect, QRectF, Qt
from PyQt5.QtGui import QFont, QImage, QPen

import kpaint2 as K
from kpaint2 import C, rrect, ellipse
from fidelity_sheet import text, badge, frame, fit, head_at

E = K.ensure
COCOA, INK2, SAGE_D, TERRA, DUSTY = "#59463d", "#7a6558", "#5d7a60", "#a65a33", "#4f6a84"
REF = "/Users/mfm/code/porto-projects/app-momee/assets/references/calm-chibi-storybook/characters/character-master-v1.png"
AN = {"boy": (320, 864), "mom": (400, 1216)}       # feet anchors in the 4 px/u master renders


def figure(p, img, who, feet_x, feet_y, ppu, mirror=False):
    ax, ay = AN[who]
    s = ppu / 4.0
    p.p.save()
    p.p.translate(feet_x, feet_y)
    if mirror:
        p.p.scale(-1, 1)
    p.p.drawImage(QRectF(-ax * s, -ay * s, img.width() * s, img.height() * s), img)
    p.p.restore()


def run(d, f):
    m = QImage(REF)
    R = {k: QImage(v) for k, v in f["renders"].items()}
    cand = QImage(f["candidate"])
    E(d, "Paper")
    K.paint(d, "Paper", lambda p: p.fill(rrect(0, 0, d.width(), d.height(), 0), C("#fefaf1")), scale=1)
    E(d, "Header and legend")
    K.paint(d, "Header and legend", lambda p: (
        text(p, 40, 62, "MOMEE · M1.0i · BOY & MOM CHARACTER CANDIDATES v1 — review sheet", 38, COCOA, True),
        text(p, 40, 98, "Placeholder-grade candidates drawn in Krita by code, produced by owner decision despite fidelity below the "
             "approved master. Layout, scale and identity study — not on-model production art.", 18, INK2),
        badge(p, 40, 118, "APPROVED REFERENCE", True), text(p, 260, 140, "solid sage frame · unmodified excerpts", 16, INK2),
        badge(p, 560, 118, "CANDIDATE · NOT APPROVED · BELOW MASTER FIDELITY", False), text(p, 1030, 140, "dashed terracotta frame · rights unverified", 16, INK2)),
        scale=1)

    E(d, "1 — Identity comparison")

    def row1(p):
        text(p, 40, 210, "1 · Identity comparison — approved master, existing Boy candidate, M1.0i v1", 28, COCOA, True)
        refs = [(QRect(180, 140, 85, 160), "Boy front"), (QRect(255, 320, 100, 175), "Boy ¾"),
                (QRect(835, 135, 72, 180), "Mom front"), (QRect(905, 315, 75, 185), "Mom ¾")]
        x = 40
        for r, lab in refs:
            frame(p, x, 236, 230, 470, True)
            fit(p, m, r, x + 12, 248, 206, 380)
            text(p, x + 14, 660, "master · " + lab, 15, COCOA, True)
            badge(p, x + 12, 668, "APPROVED REFERENCE", True)
            x += 244
        frame(p, x, 236, 230, 470, False)
        fit(p, cand, QRect(300, 0, 600, 1254), x + 12, 248, 206, 380)
        text(p, x + 14, 660, "existing Boy ¾ (M0.3c.1)", 15, COCOA, True)
        badge(p, x + 12, 668, "CANDIDATE", False)
        x += 244
        frame(p, x, 236, 2520 - x, 470, False)
        for i, k in enumerate(("boy-front-neutral", "boy-three-quarter-neutral", "mom-front-neutral", "mom-three-quarter-neutral")):
            im = R[k]
            fit(p, im, QRect(0, 0, im.width(), im.height()), x + 14 + i * 255, 248, 240, 400)
        text(p, x + 14, 680, "M1.0i v1 · Boy front · Boy ¾ · Mom front · Mom ¾", 16, COCOA, True)
        badge(p, x + 560, 662, "CANDIDATE · NOT APPROVED", False)
    K.paint(d, "1 — Identity comparison", row1, scale=1)

    E(d, "2 — Height line-up (common ground line)")

    def row2(p):
        text(p, 40, 770, "2 · Height line-up on one ground line — 2 px per world unit · Boy 200 u, Mom 290 u (1.45×)", 28, COCOA, True)
        frame(p, 40, 796, 2480, 780, False)
        gy, ppu = 1500, 2.0
        for u in range(0, 321, 20):
            yy = gy - u * ppu
            p.line([(70, yy), (2490, yy)], C("#d9c4aa" if u % 100 == 0 else "#efe3d3"), 1.6 if u % 100 == 0 else 1)
            if u % 100 == 0:
                text(p, 74, yy - 6, f"{u} u", 15, INK2)
        for u, col, lab in ((200, TERRA, "Boy 200 u"), (290, TERRA, "Mom 290 u"), (120, DUSTY, "Boy chin (head 80 u)"), (196, DUSTY, "Mom chin (head 94 u)")):
            yy = gy - u * ppu
            p.p.strokePath(rrect(140, yy, 2340, 0.1, 0), QPen(C(col), 1.5, Qt.DashLine))
            text(p, 2300 if "Mom chin" not in lab else 1960, yy - 6 if "Mom chin" not in lab else yy + 18, lab, 15, col, True)
        xs = [300, 560, 860, 1180]
        for x, k, who in zip(xs, ("boy-front-neutral", "boy-three-quarter-neutral", "mom-front-neutral", "mom-three-quarter-neutral"),
                             ("boy", "boy", "mom", "mom")):
            figure(p, R[k], who, x, gy, ppu)
        # existing candidate at 200 u for comparison
        s = 200 * ppu / (1206 - 28)
        p.p.drawImage(QRectF(1440 - 597 * s, gy - 1206 * s, 1254 * s, 1254 * s), cand)
        text(p, 1370, gy + 34, "existing Boy ¾", 16, TERRA, True)
        # together: Boy ¾ facing Mom (Mom mirrored, as in the room)
        figure(p, R["boy-three-quarter-happy"], "boy", 1800, gy, ppu)
        figure(p, R["mom-three-quarter-talking"], "mom", 2080, gy, ppu, mirror=True)
        for x, lab in zip(xs + [1940], ("Boy front", "Boy ¾", "Mom front", "Mom ¾", "together (Mom mirrored)")):
            text(p, x - 60, gy + 34, lab, 16, COCOA, True)
        text(p, 140, gy + 66, "Measured on v1: Boy 2.5 heads, eyes 67% down the head (master 69%); Mom 3.09 heads, eyes 66% (master 68%). "
             "Feet on the anchor line; Boy ¾ far shoe raised 3 u for depth.", 16, INK2)
    K.paint(d, "2 — Height line-up (common ground line)", row2, scale=1)

    E(d, "3 — Expression comparison")

    def row3(p):
        text(p, 40, 1650, "3 · Expressions — neutral · happy · talking (one head per view; only eye/brow/mouth layers change)", 28, COCOA, True)
        frame(p, 40, 1676, 2480, 700, False)
        keys = [("boy", "front"), ("boy", "three-quarter"), ("mom", "front"), ("mom", "three-quarter")]
        for r, (who, v) in enumerate(keys):
            for j, e in enumerate(("neutral", "happy", "talking")):
                im = R[f"{who}-{v}-{e}"]
                ax, ay = AN[who]
                h = 200 if who == "boy" else 290
                hd = 80 if who == "boy" else 94
                top = ay - (h + 10) * 4
                side = (hd + 26) * 4
                x = 70 + (r % 2) * 1230 + j * 400
                y = 1700 + (r // 2) * 340
                p.p.drawImage(QRectF(x, y, 300, 300), im, QRectF(ax - side / 2, top, side, side))
                text(p, x + 40, y + 320, f"{who} · {v} · {e}", 15, COCOA, True)
    K.paint(d, "3 — Expression comparison", row3, scale=1)

    E(d, "4 — Bedroom before and after")
    before, after = QImage(f["before"]), QImage(f["after"])

    def row4(p):
        text(p, 40, 2450, "4 · Bedroom integration — M1.0h placeholder composition → M1.0i candidates (same room, same positions)", 28, COCOA, True)
        for i, (im, lab) in enumerate(((before, "BEFORE — Boy candidate + Mom placeholder (M1.0h)"), (after, "AFTER — Boy + Mom candidates v1 (M1.0i)"))):
            x = 40 + i * 1246
            frame(p, x, 2476, 1234, 760, False)
            p.p.drawImage(QRectF(x + 12, 2488, 1210, 680), im, QRectF(0, 0, 2560, 1440))
            badge(p, x + 14, 3190, "CANDIDATE · NOT APPROVED", False)
            text(p, x + 360, 3212, lab, 17, COCOA, True)
    K.paint(d, "4 — Bedroom before and after", row4, scale=1)

    E(d, "5 — Mobile gameplay-scale framing")

    def row5(p):
        text(p, 40, 3300, "5 · Mobile framing at real CSS size (1:1 on a 1× screen) — frames from camera-framing.ts", 28, COCOA, True)
        # child-and-mom target on a 390×844 phone (zoom 1.17, world x 622–955) and overview on 844×390 (zoom 0.85)
        crops = [("390×844 · child-and-mom · 1.17", 1.172, (623, 200, 333, 520)), ("844×390 · overview · 0.85", 0.85, (193, 245, 993, 459)),
                 ("390×844 · bed · 0.94", 0.938, (62, 250, 416, 450))]
        x = 40
        for lab, z, (wx, wy, ww, wh) in crops:
            w, h = ww * z, wh * z
            p.p.drawImage(QRectF(x, 3330, w, h), after, QRectF(wx * 2, wy * 2, ww * 2, wh * 2))
            p.p.strokePath(rrect(x, 3330, w, h, 0), QPen(C(TERRA), 2, Qt.DashLine))
            text(p, x, 3330 + h + 24, lab, 16, COCOA, True)
            x += w + 40
        text(p, x, 3360, "At the 0.85 camera floor: Boy ≈ 170 CSS px tall, Mom ≈ 247.", 16, INK2)
        text(p, x, 3388, "Faces stay readable: eyes ≈ 15–16 CSS px tall at 0.85; expressions", 16, INK2)
        text(p, x, 3416, "remain distinct (open vs closed eyes, mouth shapes).", 16, INK2)
        text(p, x, 3452, "child-and-mom frames the story beat where the child walks to Mom's", 16, INK2)
        text(p, x, 3480, "approach point (730, 590); this study keeps him at CHILD_START, so he is off-frame.", 16, INK2)
        badge(p, x, 3500, "CANDIDATE · NOT APPROVED", False)
    K.paint(d, "5 — Mobile gameplay-scale framing", row5, scale=1)
    K.refresh(d)
