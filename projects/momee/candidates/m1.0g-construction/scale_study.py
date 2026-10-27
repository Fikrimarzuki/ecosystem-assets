# M1.0g character scale study v1 (2560x1600 px). Uses the existing Boy
# candidate unmodified, a labelled Mom placeholder and the bedroom study.
import json

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QFont, QImage, QPen

import kpaint as K
from kpaint import C, rrect, ellipse, smooth, rpoly
from bedroom_layout_data import INTERACTABLES, CHILD_START, MOM_SPOT, SLEEPER_HEAD

E = K.ensure
COCOA, INK2, DUSTY, TERRA, SAGE_D = "#59463d", "#7a6558", "#4f6a84", "#94502d", "#667d67"
PAPER = "#fefaf1"
BOY_BOX = (330, 28, 864, 1206)        # refined cutout alpha bbox (px)
BOY_CHIN_Y, BOY_CX = 496, 597
CHILD_U, ADULT_U = 200, 290           # asset-pipeline §9 working heights (≈1.45×)
PLACEHOLDER = {"child": 168, "adult": 246}   # current Phaser stand-ins (CHILD_EXTENT, Mom 52/150 build)


def text(p, x, y, s, size=18, color=COCOA, bold=False, align="left"):
    f = QFont("Helvetica")
    f.setPixelSize(int(size))
    f.setBold(bold)
    p.p.setFont(f)
    p.p.setPen(C(color))
    if align == "center":
        w = p.p.fontMetrics().horizontalAdvance(s)
        x -= w / 2
    p.p.drawText(QPointF(x, y), s)


def dashed(p, path, color, w=2.0, style=Qt.DashLine):
    p.p.strokePath(path, QPen(C(color), w, style, Qt.RoundCap, Qt.RoundJoin))


def boy(p, feet_x, feet_y, ppu, boy_png):
    """Draw the unmodified Boy cutout so its soles sit at feet and it is 200 u tall."""
    src = QImage(boy_png)
    s = CHILD_U * ppu / (BOY_BOX[3] - BOY_BOX[1])
    p.p.drawImage(QRectF(feet_x - BOY_CX * s, feet_y - BOY_BOX[3] * s, 1254 * s, 1254 * s), src)
    return s


def mom(p, feet_x, feet_y, ppu, alpha=190):
    """Labelled placeholder: 290 u, ≈3.1 heads, flat fill + dashed edge (not art)."""
    u = ppu
    def X(v): return feet_x + (v - 840) * u
    def Y(v): return feet_y + (v - 560) * u
    sil = (ellipse(X(796), Y(270), 88 * u, 94 * u)
           .united(smooth([(X(792), Y(300)), (X(788), Y(360)), (X(800), Y(404)), (X(872), Y(404)), (X(884), Y(360)), (X(880), Y(300))]))
           .united(rpoly([(X(806), Y(362)), (X(868), Y(362)), (X(874), Y(452)), (X(800), Y(452))], 14 * u))
           .united(rpoly([(X(800), Y(448)), (X(874), Y(448)), (X(886), Y(548)), (X(848), Y(548)), (X(838), Y(470)), (X(828), Y(548)), (X(792), Y(548))], 10 * u))
           .united(ellipse(X(786), Y(542), 44 * u, 18 * u)).united(ellipse(X(842), Y(542), 46 * u, 18 * u))
           .united(rpoly([(X(800), Y(370)), (X(788), Y(372)), (X(778), Y(446)), (X(792), Y(450))], 8 * u)))
    p.fill(sil, C("#e9d3c6", alpha))
    dashed(p, sil, "#b07f6a", max(1.5, 1.2 * u))


def panel(p, x, y, w, h, title, sub=""):
    p.fill(rrect(x, y, w, h, 22), C("#fffdf8"))
    p.stroke(rrect(x, y, w, h, 22), C("#e6d5c0"), 2)
    text(p, x + 28, y + 44, title, 26, COCOA, True)
    if sub:
        text(p, x + 28, y + 74, sub, 17, INK2)


def run(d, boy_png, room_png, full_png, made_png, unmade_png):
    E(d, "Paper", "paintlayer")
    K.paint(d, "Paper", lambda p: p.fill(rrect(0, 0, d.width(), d.height(), 0), C(PAPER)), scale=1)
    E(d, "Title — candidate study, not approval")
    K.paint(d, "Title — candidate study, not approval", lambda p: (
        text(p, 40, 58, "MOMEE · M1.0g · CHARACTER SCALE STUDY v1", 34, COCOA, True),
        text(p, 40, 92, "Candidate study for owner review — not character approval. Boy = existing candidate (unmodified). "
             "Mom = labelled placeholder. Heights = asset-pipeline §9 working values (child 200 u, adult 290 u).", 18, INK2)), scale=1)

    # Panel A — line-up --------------------------------------------------------
    A = "A — Height line-up"
    E(d, A, "grouplayer")
    for n in ["Panel", "Grid (20 u)", "Current Phaser placeholders (dashed)", "Mom — PLACEHOLDER (not art)",
              "Boy — existing candidate (unmodified)", "Measurements"]:
        E(d, f"{A}/{n}")
    ax, ay, aw, ah, ppu, gy = 40, 120, 880, 960, 2.0, 880

    K.paint(d, f"{A}/Panel", lambda p: panel(p, ax, ay, aw, ah, "A · Adult-to-child scale",
                                             "One ground line · 2 px per world unit"), scale=1)

    def grid(p):
        for i in range(0, 301, 20):
            yy = gy - i * ppu
            p.line([(ax + 30, yy), (ax + aw - 30, yy)], C("#e9dccb" if i % 100 else "#d9c4aa"), 1.2 if i % 100 else 2)
            if i % 100 == 0:
                text(p, ax + 34, yy - 6, f"{i} u", 15, INK2)
    K.paint(d, f"{A}/Grid (20 u)", grid, scale=1)
    bx, mx = ax + 300, ax + 640

    def placeholders(p):
        dashed(p, rrect(bx - 46 * ppu, gy - PLACEHOLDER["child"] * ppu, 92 * ppu, PLACEHOLDER["child"] * ppu, 30), "#8fb8e0", 2, Qt.DotLine)
        dashed(p, rrect(mx - 55 * ppu, gy - PLACEHOLDER["adult"] * ppu, 110 * ppu, PLACEHOLDER["adult"] * ppu, 40), "#9ed49a", 2, Qt.DotLine)
    K.paint(d, f"{A}/Current Phaser placeholders (dashed)", placeholders, scale=1)
    K.paint(d, f"{A}/Mom — PLACEHOLDER (not art)", lambda p: mom(p, mx, gy, ppu), scale=1)
    K.paint(d, f"{A}/Boy — existing candidate (unmodified)", lambda p: boy(p, bx, gy, ppu, boy_png), scale=1)

    def meas(p):
        head_u = (BOY_CHIN_Y - BOY_BOX[1]) / (BOY_BOX[3] - BOY_BOX[1]) * CHILD_U
        for x, top, h, lab in [(bx + 120, gy - CHILD_U * ppu, CHILD_U, "200 u"), (mx + 130, gy - ADULT_U * ppu, ADULT_U, "290 u")]:
            p.line([(x, top), (x, gy)], C(TERRA), 2)
            p.line([(x - 8, top), (x + 8, top)], C(TERRA), 2)
            text(p, x + 10, top + 22, lab, 18, TERRA, True)
        p.line([(bx - 150, gy - CHILD_U * ppu), (bx - 150, gy - CHILD_U * ppu + head_u * ppu)], C(DUSTY), 3)
        text(p, bx - 270, gy - CHILD_U * ppu + 40, f"head {head_u:.0f} u", 16, DUSTY)
        text(p, bx - 270, gy - CHILD_U * ppu + 60, "≈ 2.5 heads", 16, DUSTY)
        text(p, mx + 150, gy - ADULT_U * ppu + 50, "≈ 3.1 heads", 16, DUSTY)
        text(p, mx + 150, gy - ADULT_U * ppu + 70, "(placeholder)", 16, DUSTY)
        text(p, bx, gy + 34, "BOY — existing candidate", 17, COCOA, True, "center")
        text(p, bx, gy + 56, "unmodified · 200 u", 15, INK2, False, "center")
        text(p, mx, gy + 34, "MOM — PLACEHOLDER", 17, COCOA, True, "center")
        text(p, mx, gy + 56, "not character art · 290 u", 15, INK2, False, "center")
        y = ay + ah - 90
        for line in ["Ratio 290 / 200 = 1.45× (bible D2: 1.4–1.5×).",
                     "Dotted outlines: current Phaser stand-ins, child 168 u and Mom ≈246 u (1.46×).",
                     "Final heights still need the approved height line-up (D2); ref.height-lineup-v1 is in review."]:
            text(p, ax + 30, y, line, 16, INK2)
            y += 26
    K.paint(d, f"{A}/Measurements", meas, scale=1)

    # Panel B — bed, pillow and child ------------------------------------------
    B = "B — Bed, pillow and child"
    E(d, B, "grouplayer")
    for n in ["Panel", "Bedroom study crop (room only)", "Boy — at the bed front line (unmodified)",
              "Pillow states at scale", "Measurements"]:
        E(d, f"{B}/{n}")
    bx0, by0, bw, bh = 960, 120, 1560, 960
    K.paint(d, f"{B}/Panel", lambda p: panel(p, bx0, by0, bw, bh, "B · Bed-to-child scale, pillow size, floor position",
                                             "Bedroom study crop at 2 px/u; Boy placed with soles on the bed's front floor line (y 578)"), scale=1)
    room = QImage(room_png)
    cx0, cy0 = 40, 280        # world crop origin
    ox, oy = bx0 + 40, by0 + 110

    def W(x, y):
        return (ox + (x - cx0) * 2, oy + (y - cy0) * 2)
    K.paint(d, f"{B}/Bedroom study crop (room only)", lambda p: p.p.drawImage(
        QRectF(ox, oy, 560 * 2, 340 * 2), room, QRectF(cx0 * 2, cy0 * 2, 560 * 2, 340 * 2)), scale=1)
    K.paint(d, f"{B}/Boy — at the bed front line (unmodified)", lambda p: boy(p, W(560, 578)[0], W(560, 578)[1], 2.0, boy_png), scale=1)

    def states(p):
        mimg, uimg = QImage(made_png), QImage(unmade_png)
        # @1x review at 1 px/u: actual pixel tiers side by side, under the crop
        x, y = W(560, 0)[0] + 140, oy + 40
        text(p, x, y, "Pillow v2 at its export tiers", 17, COCOA, True)
        p.p.drawImage(QRectF(x, y + 14, 128, 96), uimg, QRectF(0, 0, 256, 192))
        p.p.drawImage(QRectF(x + 140, y + 14, 128, 96), mimg, QRectF(0, 0, 256, 192))
        text(p, x, y + 128, "@1x  128×96 (1 px/u)", 14, INK2)
        p.p.drawImage(QRectF(x, y + 140, 256, 192), uimg)
        text(p, x, y + 350, "@2x  256×192 (2 px/u)", 14, INK2)
        p.p.drawImage(QRectF(x, y + 360, 256 * 0.425, 192 * 0.425), mimg)
        p.p.drawImage(QRectF(x + 130, y + 360, 256 * 0.425, 192 * 0.425), uimg)
        text(p, x, y + 460, "at 0.85 CSS px/u (camera floor),", 14, INK2)
        text(p, x, y + 478, "shown 1:1 on a 1× screen", 14, INK2)
    K.paint(d, f"{B}/Pillow states at scale", states, scale=1)

    def bmeas(p):
        # mattress height vs child height at the same depth
        fx, fy = W(500, 578)
        top = W(500, 578 - 92)[1]
        p.line([(fx, fy), (fx, top)], C(TERRA), 3)
        p.line([(fx - 10, top), (fx + 10, top)], C(TERRA), 3)
        text(p, fx - 250, top - 10, "mattress top 92 u = 46% of child", 17, TERRA, True)
        # head-size circle on the pillow at SLEEPER_HEAD
        hx, hy = W(*SLEEPER_HEAD)
        dashed(p, ellipse(hx - 43 * 2, hy - 40 * 2, 86 * 2, 80 * 2), DUSTY, 2.5)
        text(p, hx - 80, hy - 92, "Boy head 86×80 u at SLEEPER_HEAD", 16, DUSTY, True)
        pl, pr = W(117, 512), W(223, 512)
        p.line([pl, pr], C(DUSTY), 2)
        p.line([(pl[0], pl[1] - 8), (pl[0], pl[1] + 8)], C(DUSTY), 2)
        p.line([(pr[0], pr[1] - 8), (pr[0], pr[1] + 8)], C(DUSTY), 2)
        text(p, pl[0], pl[1] + 26, "pillow 106 u ≈ 1.23× head width", 16, DUSTY, True)
        # pillow hit area
        for iid, (x, y, w, h), _ in INTERACTABLES:
            if iid in ("pillow", "blanket"):
                a = W(x, y)
                dashed(p, rrect(a[0], a[1], w * 2, h * 2, 0), "#4f6a84", 1.5, Qt.DotLine)
        y = by0 + bh - 140
        for line in ["Bed 400×240 u reads child-sized: frame length ≈ 1.9× the child's height, mattress at mid-thigh/hip.",
                     "A slightly lower mattress (≈ 75–80 u, ~38%) would let the child climb in and reach the pillow more naturally.",
                     "Pillow v2 keeps v1 bounds (128×96 @1x). At 106 u it is only ≈ 1.2× the head; concept boards show ≈ 1.6–2×.",
                     "A larger pillow needs a v3 canvas (e.g. 160×112 @1x) and a matching pillow hit area: owner decision."]:
            text(p, bx0 + 30, y, line, 16, INK2)
            y += 26
    K.paint(d, f"{B}/Measurements", bmeas, scale=1)

    # Panel C — reach and camera framing ----------------------------------------
    Cg = "C — Reach and camera framing"
    E(d, Cg, "grouplayer")
    for n in ["Panel", "Bedroom study (with position guides)", "Reach radii", "Camera frames", "Notes"]:
        E(d, f"{Cg}/{n}")
    c0x, c0y, cw, ch = 40, 1110, 2480, 760
    K.paint(d, f"{Cg}/Panel", lambda p: panel(p, c0x, c0y, cw, ch, "C · Interaction reach and camera framing",
                                              "Bedroom study at 0.9 px/u · frames are the visible world from frameCamera() (camera-framing.ts)"), scale=1)
    sx, sy, k = c0x + 30, c0y + 100, 0.9
    room_full = QImage(full_png)

    def V(x, y):
        return (sx + x * k, sy + y * k)
    K.paint(d, f"{Cg}/Bedroom study (with position guides)", lambda p: p.p.drawImage(
        QRectF(sx, sy, 1280 * k, 720 * k), room_full), scale=1)

    def reach(p):
        # child arm reach ≈ 0.3 × height from the shoulder; adult ≈ 0.33 × height
        for (fx, fy), h, r, col, lab, below in [(CHILD_START, CHILD_U, 60, TERRA, "child reach ≈ 60 u (at start)", True),
                                                ((470, 620), CHILD_U, 60, TERRA, "child at bed approach", False),
                                                (MOM_SPOT, ADULT_U, 95, SAGE_D, "Mom reach ≈ 95 u (standing)", False)]:
            shoulder = V(fx, fy - h * 0.66)
            dashed(p, ellipse(shoulder[0] - r * k, shoulder[1] - r * k, 2 * r * k, 2 * r * k), col, 2)
            ly = shoulder[1] + r * k + 22 if below else shoulder[1] - r * k - 8
            text(p, shoulder[0] - 80, ly, lab, 14, col, True)
        a, b = V(470, 560), V(170, 463)
        p.line([a, b], C(DUSTY), 2)
        text(p, (a[0] + b[0]) / 2 - 110, (a[1] + b[1]) / 2 - 10, "bed approach → pillow ≈ 315 u", 14, DUSTY, True)
    K.paint(d, f"{Cg}/Reach radii", reach, scale=1)
    frames = json.load(open(K.__file__.replace("kpaint.py", "frames.json")))

    def cams(p):
        cols = {"390x844:bed": TERRA, "844x390:overview": DUSTY, "1280x800:overview": SAGE_D, "390x844:child-and-mom": "#b0607a"}
        for i, (key, col) in enumerate(cols.items()):
            f = frames[key]
            x0, y0 = f["cx"] - f["visW"] / 2, f["cy"] - f["visH"] / 2
            a = V(max(-40, x0), max(-20, y0))
            b = V(min(1320, x0 + f["visW"]), min(740, y0 + f["visH"]))
            dashed(p, rrect(a[0], a[1], b[0] - a[0], b[1] - a[1], 0), col, 3, Qt.DashLine)
            text(p, a[0] + 8, a[1] + 22 + i * 20, f"{key.replace(':', ' · ')}  zoom {f['zoom']}", 14, col, True)
    K.paint(d, f"{Cg}/Camera frames", cams, scale=1)

    def notes(p):
        x, y = sx + 1280 * k + 40, c0y + 130
        rows = [("Viewport · target", "zoom", "child", "Mom", "pillow hit"),
                ("320×568 · bed", "0.85", "170", "247", "106×77"),
                ("390×844 · bed", "0.94", "188", "272", "117×84"),
                ("390×844 · child-and-mom", "1.17", "234", "340", "147×106"),
                ("844×390 · overview", "0.85", "170", "247", "106×77"),
                ("1280×800 · overview", "1.10", "220", "319", "138×99")]
        for i, r in enumerate(rows):
            for j, cell in enumerate(r):
                text(p, x + [0, 300, 380, 460, 540][j], y + i * 28, cell, 16, COCOA if i else INK2, i == 0)
        text(p, x, y + 6 * 28 + 4, "CSS px, from frameZoom(); 0.65 compact floor applies under overlays.", 14, INK2)
        y += 6 * 28 + 50
        for line in ["• Every viewport keeps the pillow and blanket targets ≥ 64 CSS px.",
                     "• Phone portrait (bed) shows x≈62–478: the whole bed, the child at the",
                     "  approach point, and the pillow at ≈ 90–100 CSS px wide.",
                     "• Render scale caps at 2×: phones need ≈ 1.7–1.9 texels/u, so @2x is",
                     "  the working tier and @1x is below need on phones.",
                     "• The bed approach (470, 620) is ≈ 5× the child's reach from the pillow.",
                     "  Visible fluffing would need a pillow-side stand point (≈ 250, 600) —",
                     "  a layout change for a later milestone, not part of this study.",
                     "• Mom (290 u) at MOM_SPOT reaches a child at her approach point (730, 590);",
                     "  standing, her hands hang near the child's chest (≈ 130 u), so the",
                     "  bible's kneel-to-the-child's-level pose is needed for face-to-face beats."]:
            text(p, x, y, line, 16, INK2)
            y += 26
    K.paint(d, f"{Cg}/Notes", notes, scale=1)
    K.refresh(d)
