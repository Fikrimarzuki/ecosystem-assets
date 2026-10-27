# M1.0l-A1 Mom head-pilot review sheet. All character images are shown 1:1 (head crop 340×330 of the master canvas).
import sys

from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QColor, QImage

sys.path.insert(0, "/Users/mfm/code/porto-projects/ecosystem-assets/projects/momee/candidates/m1.0j-construction")
import sheets_j  # noqa: E402
from sheets_j import new_doc, layer, text, badge, frame, checker, COCOA, INK2, TERRA, SAGE  # noqa: E402

sheets_j.KINDS.setdefault("pilot", ("HEAD PILOT · EXTRACTION ONLY · NOT ANIMATION-READY · NOT APPROVED", TERRA, True, "#fbe7dc"))
CROP = QRectF(240, 150, 340, 330)
SECTIONS = {"head-closeup": (0, 130, 800, 560), "layer-inventory": (800, 130, 2560, 560), "extracted-layers": (0, 580, 2560, 1090),
            "neutral-reconstruction": (0, 1110, 2560, 1590), "missing-artwork-map": (0, 1610, 2560, 2110), "facial-animation-requirements": (0, 2130, 2560, 2930)}


def tile(p, img, x, y, dark=False):
    if dark:
        p.fillRect(QRectF(x, y, 340, 330), QColor("#1d1a18"))
    else:
        checker(p, x, y, 340, 330)
    p.drawImage(QRectF(x, y, 340, 330), img, CROP)


def build(F, inv, data, spec):
    d = new_doc("Momee Mom head pilot v1 review sheet", 2560, 2930)
    master = QImage(F["master"])
    Lp = lambda n: QImage(F["layers"] + n + ".png")  # noqa: E731
    layer(d, "Paper", lambda p: p.fillRect(0, 0, 2560, 2930, QColor("#fefaf1")))
    layer(d, "Header", lambda p: (
        text(p, 40, 56, "MOMEE · M1.0l-A1 · MOM HEAD LAYER EXTRACTION & FIDELITY — accepted Mom v2 master (visual authority)", 34, COCOA, True),
        text(p, 40, 90, "Existing pixels only: every master pixel sits in exactly one layer, unchanged. Nothing painted, generated, resampled or mirrored. "
             "Head crop shown 1:1 (master x 240–580, y 150–480).", 17, INK2),
        badge(p, 40, 102, "pilot")))

    def s1(p):
        text(p, 40, 170, "1 · Head close-up (accepted v2 master, 1:1)", 26, COCOA, True)
        frame(p, 40, 186, 380, 360, "extract")
        tile(p, master, 60, 200)
        text(p, 440, 230, "Visual authority: Mom v2", 18, COCOA, True)
        for i, s in enumerate(["visually accepted (M1.0k-A4)", "production approval: pending", "rights: unverified",
                               "native facing: left ¾ (kept)", "≈ 3.42 heads · 4 px/u", "canvas 800×1248, feet (400, 1216)"]):
            text(p, 440, 262 + i * 30, s, 16, INK2)
        text(p, 840, 170, "2 · Layer inventory (Krita: source/characters/mom/mom-head-pilot-v1-working.kra)", 26, COCOA, True)
        frame(p, 840, 186, 1680, 360, "extract")
        cols = (860, 1290, 1400, 1640, 1990)
        for c, h in zip(cols, ("layer (slot/attachment)", "pixels", "bbox (master px)", "pivot / centroid", "extraction")):
            text(p, c, 216, h, 15, COCOA, True)
        for i, r in enumerate(inv):
            col = {"safe": SAGE, "partial": TERRA, "base": INK2}[r[5]]
            for c, s in zip(cols, r[:5]):
                text(p, c, 246 + i * 30, s, 14, col if c == 1990 else INK2, c == 860)
        text(p, 860, 246 + len(inv) * 30 + 14, "Not separated (stay in base): near brow (inside the hair sweep) · hair-front vs hair-back · face rim and cheek contour. "
             "Blush stays in head-skin.", 14, TERRA, True)
    layer(d, "1–2 — Close-up and inventory", s1)

    def s2(p):
        text(p, 40, 620, "3 · Extracted layers (each alone, 1:1; checker = transparent)", 26, COCOA, True)
        tiles = [("base/unseparated (hair, body, near brow, rim)", "base", False), ("head-skin/base (holes under attachments)", "head-skin__base", False),
                 ("body-skin/neck-visible", "body-skin__neck-visible", False), ("face-eyes/open (eye-near + eye-far)", ["face-eyes__open__eye-near", "face-eyes__open__eye-far"], True),
                 ("face-brows/neutral (far brow only)", "face-brows__neutral__brow-far", True), ("face-mouth/neutral", "face-mouth__neutral", True)]
        for i, (lab, names, dark) in enumerate(tiles):
            x = 40 + i * 415
            frame(p, x, 640, 380, 420, "extract")
            if isinstance(names, list):
                p.fillRect(QRectF(x + 20, 654, 340, 330), QColor("#1d1a18"))
                for n in names:
                    p.drawImage(QRectF(x + 20, 654, 340, 330), Lp(n), CROP)
            else:
                tile(p, Lp(names), x + 20, 654, dark)
            text(p, x + 20, 1010, lab, 14, COCOA, True)
    layer(d, "3 — Extracted layers", s2)

    def s3(p):
        text(p, 40, 1150, "4 · Neutral reconstruction (Krita's own composite of the visible layers vs the master)", 26, COCOA, True)
        for i, (lab, img) in enumerate((("accepted master", master), ("reconstruction (Krita projection)", QImage(F["projection"])), ("|difference| × 64, visible pixels (black = identical)", QImage(F["diff"])))):
            x = 40 + i * 415
            frame(p, x, 1170, 380, 400, "extract")
            if i < 2:
                tile(p, img, x + 20, 1184)
            else:
                p.drawImage(QRectF(x + 20, 1184, 340, 330), img)
            text(p, x + 20, 1540, lab, 14, COCOA, True)
        x0 = 1300
        lines = [("PASS", "canvas 800×1248 · placement identical (same canvas, no offsets)"),
                 ("PASS", f"full canvas: {data['projectionVsMasterDifferingPixels']} differing visible pixels (RGBA, alpha > 0); alpha identical everywhere ({data['alphaDifferences']} diffs)"),
                 ("NOTE", f"{data['alphaZeroPixelsWithHiddenRgbNotCarried']:,} fully transparent master pixels hold leftover RGB that layers store as 0 — never rendered"),
                 ("PASS", "partition: 0 overlapping pixels, 0 unassigned pixels"),
                 ("PASS", "every imported layer equals its extracted PNG after reopening (0 px)"),
                 ("PASS", "no seams, no missing pixels, no colour change (exact)"),
                 ("NOTE", "exact only in the neutral state; swapping any attachment exposes the holes in §5")]
        for i, (lvl, s) in enumerate(lines):
            text(p, x0, 1210 + i * 40, f"{lvl}  {s}", 17, SAGE if lvl == "PASS" else TERRA, True)
    layer(d, "4 — Reconstruction", s3)

    def s4(p):
        text(p, 40, 1650, "5 · Missing-artwork map (existing pixels never fill these; they need painting or a later extraction)", 26, COCOA, True)
        for i, (lab, lab2, n) in enumerate((("red: skin/eyelid beneath swappable attachments", "hatched: neck under the chin", "missing-1-attachment-footprints"),
                                             ("hatched red: neck extension ≥ 24 px (6 u)", "under the chin (hidden today)", "missing-2-neck-extension"),
                                             ("orange near brow · yellow face rim", "purple hair (front/back not separable)", "missing-3-not-separable"))):
            x = 40 + i * 415
            frame(p, x, 1670, 380, 420, "extract")
            p.drawImage(QRectF(x + 20, 1684, 340, 330), QImage(F["review"] + n + ".png"))
            text(p, x + 20, 2040, lab, 13, COCOA, True)
            text(p, x + 20, 2058, lab2, 13, COCOA, True)
        a = data["areaPx"]
        rows = [f"under eye-near {a['attachmentFootprints']['eye-near']:,} px · eye-far {a['attachmentFootprints']['eye-far']:,} px",
                f"under brow-far {a['attachmentFootprints']['brow-far']:,} px · mouth {a['attachmentFootprints']['mouth']:,} px",
                f"neck extension band {a['neckExtensionBand']:,} px (minimum; spec §5 overlap)",
                f"near brow region {a['nearBrowRegion']:,} px — repaint as its own face-brows attachment",
                f"face rim kept in base {a['faceRimInBase']:,} px — repaint with head-skin if tinted separately",
                f"hair in the head area {a['hairInHeadArea']:,} px — split by painting hair-back",
                "hair-back mass behind head and body: not in the image at all (size set by the illustrator)",
                "skull/forehead under the fringe: only needed if hair moves relative to the face"]
        for i, s in enumerate(rows):
            text(p, 1300, 1700 + i * 44, s, 17, INK2)
    layer(d, "5 — Missing artwork", s4)

    def s5(p):
        text(p, 40, 2170, "6 · Facial animation requirements (specification only — no frames generated)", 26, COCOA, True)
        frame(p, 40, 2190, 2480, 710, "extract")
        y = 2236
        for title, rows in spec:
            text(p, 70, y, title, 20, COCOA, True)
            y += 32
            for r in rows:
                text(p, 100, y, r, 15, INK2)
                y += 26
            y += 14
    layer(d, "6 — Animation requirements", s5)
    d.refreshProjection()
    d.waitForDone()
    return d, SECTIONS
