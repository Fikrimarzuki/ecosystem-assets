# M1.0g visual calibration sheet v1 (2560x2640 px). Reference excerpts are
# copied pixels (scaled for layout only); the reference files are never written.
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QFont, QImage, QPen

import kpaint as K
from kpaint import C, rrect

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
    if approved:
        p.fill(shape, C("#e3ecdf"))
        p.stroke(shape, C(SAGE_D), 2)
    else:
        p.fill(shape, C("#fbe7dc"))
        p.p.strokePath(shape, QPen(C(TERRA), 2, Qt.DashLine))
    text(p, x + 14, y + 21, label, 15, SAGE_D if approved else TERRA, True)


def tile(p, x, y, w, h, img, src, title, sub, approved, bg="#fffdf8", fit=True, label=None):
    frame = rrect(x, y, w, h, 18)
    p.fill(frame, C(bg))
    iw, ih = w - 24, h - 120
    s = min(iw / src.width(), ih / src.height()) if fit else 1
    dw, dh = src.width() * s, src.height() * s
    p.p.save()
    p.p.setClipPath(rrect(x + 12, y + 12, iw, ih, 12))
    p.p.drawImage(QRectF(x + 12 + (iw - dw) / 2, y + 12 + (ih - dh) / 2, dw, dh), img, QRectF(src))
    p.p.restore()
    if approved:
        p.stroke(frame, C(SAGE_D), 4)
    else:
        p.p.strokePath(frame, QPen(C(TERRA), 4, Qt.DashLine, Qt.RoundCap))
    badge(p, x + 14, y + h - 104, label or ("APPROVED REFERENCE" if approved else "CANDIDATE · NOT APPROVED"), approved)
    text(p, x + 16, y + h - 48, title, 18, COCOA, True)
    text(p, x + 16, y + h - 22, sub, 14, INK2)


def section(p, y, title, sub):
    text(p, 40, y, title, 30, COCOA, True)
    text(p, 40, y + 30, sub, 17, INK2)


def run(d, files):
    master = QImage(REF + "calm-chibi-storybook/characters/character-master-v1.png")
    sb = QImage(REF + "concepts/morning-routine-storyboard.png")
    gp = QImage(REF + "concepts/morning-routine-gameplay.png")
    fc = QImage(REF + "concepts/feature-concepts.png")
    boy = QImage(files["boy"])
    study = QImage(files["study"])
    ph = QImage(files["placeholder"])
    from PyQt5.QtCore import QRect

    E(d, "Paper")
    K.paint(d, "Paper", lambda p: p.fill(rrect(0, 0, d.width(), d.height(), 0), C(PAPER)), scale=1)
    E(d, "Header and legend")
    K.paint(d, "Header and legend", lambda p: (
        text(p, 40, 62, "MOMEE · M1.0g · VISUAL CALIBRATION SHEET v1 — Calm Chibi Storybook", 38, COCOA, True),
        text(p, 40, 98, "For owner art review. Approved references are unmodified excerpts (scaled for layout). "
             "Everything else is candidate or placeholder work: nothing generated here is approved.", 18, INK2),
        badge(p, 40, 118, "APPROVED REFERENCE", True), text(p, 260, 140, "solid sage frame", 16, INK2),
        badge(p, 440, 118, "CANDIDATE · NOT APPROVED", False), text(p, 704, 140, "dashed terracotta frame · rights unverified", 16, INK2)),
        scale=1)

    E(d, "1 — Approved reference excerpts")
    refs = [(master, QRect(20, 100, 332, 412), "Character master v1 — Boy", "character-master-v1.png · crop 20,100 332×412"),
            (master, QRect(683, 100, 297, 412), "Character master v1 — Mom", "character-master-v1.png · crop 683,100 297×412"),
            (master, QRect(1278, 220, 244, 104), "Master palette swatches", "character-master-v1.png · crop 1278,220 244×104"),
            (sb, QRect(1138, 790, 192, 100), "Storyboard — bedroom style", "morning-routine-storyboard.png · 1138,790"),
            (gp, QRect(15, 425, 385, 280), "Gameplay — Make the Bed", "morning-routine-gameplay.png · 15,425"),
            (fc, QRect(513, 855, 190, 145), "Features — connected bedroom", "feature-concepts.png · 513,855")]

    def row1(p):
        section(p, 210, "1 · Approved references", "Visual authorities. Character master wins over concept boards for characters; concept boards guide rooms.")
        x, w = 40, 400
        for img, r, t, s in refs:
            tile(p, x, 260, w, 560, img, r, t, s, True)
            x += w + 13
    K.paint(d, "1 — Approved reference excerpts", row1, scale=1)

    E(d, "2 — Candidates and placeholder")

    def row2(p):
        section(p, 890, "2 · Candidate artwork in the current pipeline", "Compared against row 1. None of these is approved.")
        tile(p, 40, 940, 470, 720, boy, QRect(300, 0, 600, 1254), "Boy candidate (M0.3c.1)",
             "existing, unmodified · rights unverified", False)
        tile(p, 530, 940, 1290, 720, study, QRect(0, 0, study.width(), study.height()),
             "Bedroom composition study v1 (M1.0g)", "Krita layered study · Boy = existing candidate · Mom = placeholder", False)
        tile(p, 1840, 940, 680, 720, ph, QRect(0, 40, 1280, 680),
             "Current Phaser bedroom (geometric placeholder)", "/dev/free-play screenshot · technical stand-in, never art", False,
             bg="#f6efe6", label="PLACEHOLDER · NOT ART")
    K.paint(d, "2 — Candidates and placeholder", row2, scale=1)

    E(d, "3 — Pillow revision v1 → v2")
    v = {k: QImage(files[k]) for k in ("v1u", "v1m", "v2u", "v2m", "v2u1", "v2m1")}

    def row3(p):
        section(p, 1740, "3 · Pillow revision: M1.0f v1 → M1.0g v2 (both candidates)", "Same 256×192 @2x / 128×96 @1x canvas and centre anchor (128, 96). v1 files untouched.")
        y = 1790
        frame = rrect(40, y, 2480, 400, 18)
        p.fill(frame, C("#fffdf8"))
        p.p.strokePath(frame, QPen(C(TERRA), 4, Qt.DashLine, Qt.RoundCap))
        x = 70
        for lab, key, bg in [("v1 unmade", "v1u", "#f9eddc"), ("v1 made", "v1m", "#f9eddc"),
                             ("v2 unmade", "v2u", "#f9eddc"), ("v2 made", "v2m", "#f9eddc"),
                             ("v2 unmade on duvet", "v2u", "#9dbbc8"), ("v2 made on duvet", "v2m", "#9dbbc8")]:
            p.fill(rrect(x, y + 30, 270, 206, 12), C(bg))
            p.p.drawImage(QRectF(x + 7, y + 37, 256, 192), v[key])
            text(p, x + 6, y + 262, lab + " · @2x", 16, COCOA, True)
            x += 290
        # actual gameplay scale strip
        gx = x + 10
        text(p, gx, y + 50, "Gameplay scale", 18, COCOA, True)
        p.fill(rrect(gx, y + 64, 250, 110, 10), C("#f9eddc"))
        p.p.drawImage(QRectF(gx + 4, y + 70, 109, 82), v["v2u"])
        p.p.drawImage(QRectF(gx + 124, y + 70, 109, 82), v["v2m"])
        text(p, gx, y + 196, "0.85 CSS px/u (camera floor)", 14, INK2)
        p.fill(rrect(gx, y + 210, 250, 100, 10), C("#f9eddc"))
        p.p.drawImage(QRectF(gx + 4, y + 212, 128, 96), v["v2u1"])
        p.p.drawImage(QRectF(gx + 122, y + 212, 128, 96), v["v2m1"])
        text(p, gx, y + 330, "@1x export, 1:1", 14, INK2)
        notes = ["v1: cool slate line #6d7880 ≈ 2.5 u, flat sky-mist fill, faceted polygon edge, hard shade bands.",
                 "v2: cream body + warm taupe line #a28c80 at 1.25 u, one soft cool shade, warm highlight from the upper right.",
                 "v2 unmade: flatter, head dent, folded corner, soft creases.  v2 made: taller, symmetric, piping seam, brighter top.",
                 "Colour no longer carries the state change; silhouette does. Optional low contrast shadow sits inside the canvas."]
        ty = y + 296
        for n in notes:
            text(p, 76, ty, n, 17, INK2)
            ty += 26
    K.paint(d, "3 — Pillow revision v1 → v2", row3, scale=1)

    E(d, "4 — Calibration notes")

    def row4(p):
        section(p, 2250, "4 · Calibration rules proposed by this study", "Proposed for owner review; the Visual Style Bible is unchanged.")
        cols = [
            ("Palette", ["Wall cream #f9eddc; honey wood #e8c69e;", "floor #efd8b6 → #e2c299.", "Duvet sky mist #9dbbc8; pillow and sheet",
                         "cream #fbf3e6 with cool shade #c9d2de,", "as on the concept boards.", "No pure black or white; v1 slate is off-palette."]),
            ("Outline", ["Warm, darker local colour, never black.", "Interactables 1.25 u · furniture 1.0 u ·", "wall decor 0.75 u · far view no line.",
                         "Master small figures ≈ 1.4 u at child scale;", "Boy candidate ≈ 0.6 u at 200 u (too thin);", "pillow v1 ≈ 2.5 u (too heavy)."]),
            ("Shading", ["Warm key light from the upper right", "(window side), same for every object.", "One soft cool shade + one warm light,",
                         "blurred edges, gentle gradients.", "No hard cel bands (v1 had them).", "Backgrounds quieter than interactables."]),
            ("Proportions", ["Boy measured 2.52 heads (≈ 2.5 ✓).", "Mom placeholder 3.1 heads; 290/200 = 1.45×.", "Mattress 92 u = 46% of the child.",
                             "Pillow 106 u ≈ 1.2× head width;", "concepts ≈ 1.6–2× → owner decision.", "Height line-up still in review (D2)."]),
            ("Perspective", ["Gentle one-point: vanishing point (680, 60),", "receding lines meet it at 800 u depth.", "Floor seams horizontal; furniture shows",
                             "top + front faces; no converging verticals.", "Characters: feet origin, y-sorted depth.", "Bed long axis left→right (layout)."]),
            ("Readability", ["Camera floor 0.85 CSS px/u: child 170 px,", "pillow ≈ 90 px, pillow target 106×77 px.", "States read by silhouette, not colour.",
                             "Calm wall above the bed and beside", "Mom keeps room for dialogue UI.", "@2x needed on phones (≈ 1.9 texels/u)."]),
        ]
        x, w = 40, 400
        for title, lines in cols:
            fr = rrect(x, 2300, w, 300, 18)
            p.fill(fr, C("#fffdf8"))
            p.stroke(fr, C("#e6d5c0"), 2)
            text(p, x + 20, 2340, title, 22, COCOA, True)
            yy = 2376
            for ln in lines:
                text(p, x + 20, yy, ln, 16, INK2)
                yy += 36
            x += w + 13
        sw = [("#f9eddc", "cream"), ("#e8c69e", "honey"), ("#9dbbc8", "duvet"), ("#fbf3e6", "pillow"), ("#c9d2de", "cool shade"),
              ("#a28c80", "line: fabric"), ("#a57b5a", "line: wood"), ("#5f7489", "line: duvet"), ("#59463d", "cocoa (darkest)")]
        sx = 40
        for col, lab in sw:
            p.fill(rrect(sx, 2614, 26, 18, 4), C(col))
            p.stroke(rrect(sx, 2614, 26, 18, 4), C("#cdb9a6"), 1)
            text(p, sx + 32, 2629, lab, 14, INK2)
            sx += 150
    K.paint(d, "4 — Calibration notes", row4, scale=1)
    K.refresh(d)
